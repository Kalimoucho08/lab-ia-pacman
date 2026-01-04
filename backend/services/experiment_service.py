"""
Service de gestion des expériences.

Gère le CRUD des expériences, la persistance dans SQLite,
et la coordination avec les autres services.
"""
import json
import logging
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from backend.config import AllParameters, PRESET_CONFIGS
from backend.models.experiment import Experiment, ExperimentCreate, ExperimentUpdate

logger = logging.getLogger(__name__)

class ExperimentService:
    """Service pour la gestion des expériences."""
    
    def __init__(self, db_path: str = "experiments.db"):
        """Initialise le service avec la connexion à la base de données."""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialise la base de données SQLite avec les tables nécessaires."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Table des expériences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    tags TEXT,
                    preset TEXT,
                    parameters TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    created_by TEXT
                )
            """)
            # Table des sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    algorithm_pacman TEXT NOT NULL,
                    algorithm_ghosts TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    current_episode INTEGER NOT NULL,
                    total_episodes INTEGER NOT NULL,
                    metrics TEXT,
                    FOREIGN KEY (experiment_id) REFERENCES experiments (id)
                )
            """)
            conn.commit()
        logger.info("Base de données initialisée")
    
    def create_experiment(self, experiment_data: ExperimentCreate) -> Experiment:
        """Crée une nouvelle expérience."""
        experiment = Experiment(
            **experiment_data.dict(),
            status="pending"
        )
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO experiments 
                (id, name, description, tags, preset, parameters, created_at, updated_at, status, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment.id,
                experiment.name,
                experiment.description,
                json.dumps(experiment.tags),
                experiment.preset,
                experiment.parameters.json(),
                experiment.created_at.isoformat(),
                experiment.updated_at.isoformat(),
                experiment.status,
                experiment.created_by
            ))
            conn.commit()
        
        logger.info(f"Expérience créée: {experiment.id} - {experiment.name}")
        return experiment
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Récupère une expérience par son ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
            row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_experiment(row)
    
    def list_experiments(self, limit: int = 100, offset: int = 0) -> List[Experiment]:
        """Liste toutes les expériences."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM experiments 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = cursor.fetchall()
        
        return [self._row_to_experiment(row) for row in rows]
    
    def update_experiment(self, experiment_id: str, update_data: ExperimentUpdate) -> Optional[Experiment]:
        """Met à jour une expérience existante."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return None
        
        # Mise à jour des champs
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            if key == "tags" and value is not None:
                setattr(experiment, key, value)
            elif value is not None:
                setattr(experiment, key, value)
        
        experiment.updated_at = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE experiments 
                SET name = ?, description = ?, tags = ?, status = ?, updated_at = ?
                WHERE id = ?
            """, (
                experiment.name,
                experiment.description,
                json.dumps(experiment.tags),
                experiment.status,
                experiment.updated_at.isoformat(),
                experiment.id
            ))
            conn.commit()
        
        logger.info(f"Expérience mise à jour: {experiment_id}")
        return experiment
    
    def delete_experiment(self, experiment_id: str) -> bool:
        """Supprime une expérience et ses sessions associées."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Supprimer d'abord les sessions
            cursor.execute("DELETE FROM sessions WHERE experiment_id = ?", (experiment_id,))
            # Puis l'expérience
            cursor.execute("DELETE FROM experiments WHERE id = ?", (experiment_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
        
        if deleted:
            logger.info(f"Expérience supprimée: {experiment_id}")
        else:
            logger.warning(f"Expérience non trouvée pour suppression: {experiment_id}")
        
        return deleted
    
    def get_preset_config(self, preset_name: str) -> Optional[AllParameters]:
        """Récupère une configuration prédéfinie."""
        return PRESET_CONFIGS.get(preset_name)
    
    def list_presets(self) -> Dict[str, Dict[str, Any]]:
        """Liste toutes les configurations prédéfinies disponibles."""
        presets = {}
        for name, config in PRESET_CONFIGS.items():
            presets[name] = {
                "description": f"Configuration {name} pour l'entraînement RL",
                "parameters": config.dict()
            }
        return presets
    
    def _row_to_experiment(self, row: sqlite3.Row) -> Experiment:
        """Convertit une ligne SQLite en objet Experiment."""
        parameters = AllParameters.parse_raw(row["parameters"])
        tags = json.loads(row["tags"]) if row["tags"] else []
        
        return Experiment(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            tags=tags,
            preset=row["preset"],
            parameters=parameters,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            status=row["status"],
            created_by=row["created_by"]
        )

# Instance singleton du service
experiment_service = ExperimentService()