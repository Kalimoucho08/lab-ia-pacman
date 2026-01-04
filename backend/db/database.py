"""
Configuration de la base de données SQLite.

Fournit une interface pour interagir avec la base de données
des expériences, sessions et métriques.
"""
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

from backend.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestionnaire de base de données SQLite."""
    
    def __init__(self, db_path: str = None):
        """Initialise le gestionnaire avec le chemin de la base de données."""
        self.db_path = db_path or settings.DATABASE_URL.replace("sqlite:///", "")
        self._init_database()
    
    def _init_database(self):
        """Initialise la base de données avec les tables nécessaires."""
        with self.get_connection() as conn:
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
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_by TEXT,
                    metadata TEXT
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
                    status TEXT NOT NULL DEFAULT 'pending',
                    current_episode INTEGER NOT NULL DEFAULT 0,
                    total_episodes INTEGER NOT NULL DEFAULT 1000,
                    metrics TEXT,
                    model_paths TEXT,
                    FOREIGN KEY (experiment_id) REFERENCES experiments (id) ON DELETE CASCADE
                )
            """)
            
            # Table des métriques
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    episode INTEGER NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            """)
            
            # Index pour améliorer les performances
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_experiment_id ON sessions(experiment_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_session_id ON metrics(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
            
            conn.commit()
        
        logger.info(f"Base de données initialisée: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Contexte pour obtenir une connexion à la base de données."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Exécute une requête SELECT et retourne les résultats."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """Exécute une requête UPDATE/INSERT/DELETE et retourne le nombre de lignes affectées."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def insert_experiment(self, experiment_data: Dict[str, Any]) -> str:
        """Insère une nouvelle expérience dans la base de données."""
        experiment_id = experiment_data.get("id")
        if not experiment_id:
            import uuid
            experiment_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO experiments 
            (id, name, description, tags, preset, parameters, created_at, updated_at, status, created_by, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            experiment_id,
            experiment_data.get("name", ""),
            experiment_data.get("description"),
            json.dumps(experiment_data.get("tags", [])),
            experiment_data.get("preset"),
            json.dumps(experiment_data.get("parameters", {})),
            experiment_data.get("created_at", datetime.now().isoformat()),
            experiment_data.get("updated_at", datetime.now().isoformat()),
            experiment_data.get("status", "pending"),
            experiment_data.get("created_by"),
            json.dumps(experiment_data.get("metadata", {}))
        )
        
        self.execute_update(query, params)
        return experiment_id
    
    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une expérience par son ID."""
        query = "SELECT * FROM experiments WHERE id = ?"
        results = self.execute_query(query, (experiment_id,))
        
        if not results:
            return None
        
        experiment = results[0]
        # Décoder les champs JSON
        experiment["tags"] = json.loads(experiment["tags"]) if experiment["tags"] else []
        experiment["parameters"] = json.loads(experiment["parameters"]) if experiment["parameters"] else {}
        experiment["metadata"] = json.loads(experiment["metadata"]) if experiment["metadata"] else {}
        
        return experiment
    
    def update_experiment_status(self, experiment_id: str, status: str) -> bool:
        """Met à jour le statut d'une expérience."""
        query = """
            UPDATE experiments 
            SET status = ?, updated_at = ?
            WHERE id = ?
        """
        
        rows_affected = self.execute_update(
            query, 
            (status, datetime.now().isoformat(), experiment_id)
        )
        
        return rows_affected > 0
    
    def insert_metric(self, session_id: str, episode: int, metric_type: str, value: float) -> int:
        """Insère une métrique dans la base de données."""
        query = """
            INSERT INTO metrics (session_id, episode, metric_type, value, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """
        
        metric_id = self.execute_update(
            query,
            (session_id, episode, metric_type, value, datetime.now().isoformat())
        )
        
        return metric_id
    
    def get_session_metrics(self, session_id: str, metric_type: str = None, 
                           limit: int = 1000) -> List[Dict[str, Any]]:
        """Récupère les métriques d'une session."""
        if metric_type:
            query = """
                SELECT * FROM metrics 
                WHERE session_id = ? AND metric_type = ?
                ORDER BY episode ASC
                LIMIT ?
            """
            params = (session_id, metric_type, limit)
        else:
            query = """
                SELECT * FROM metrics 
                WHERE session_id = ?
                ORDER BY episode ASC
                LIMIT ?
            """
            params = (session_id, limit)
        
        return self.execute_query(query, params)
    
    def get_recent_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Récupère les métriques des dernières heures."""
        from datetime import datetime, timedelta
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        query = """
            SELECT m.*, s.name as session_name, e.name as experiment_name
            FROM metrics m
            JOIN sessions s ON m.session_id = s.id
            JOIN experiments e ON s.experiment_id = e.id
            WHERE m.timestamp > ?
            ORDER BY m.timestamp DESC
            LIMIT 1000
        """
        
        return self.execute_query(query, (cutoff_time,))
    
    def backup_database(self, backup_path: str = None) -> str:
        """Crée une sauvegarde de la base de données."""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backups/experiments_backup_{timestamp}.db"
        
        Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(self.db_path, backup_path)
        
        logger.info(f"Sauvegarde créée: {backup_path}")
        return backup_path
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Récupère des statistiques sur la base de données."""
        stats = {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Nombre d'expériences
            cursor.execute("SELECT COUNT(*) as count FROM experiments")
            stats["experiments_count"] = cursor.fetchone()[0]
            
            # Nombre de sessions
            cursor.execute("SELECT COUNT(*) as count FROM sessions")
            stats["sessions_count"] = cursor.fetchone()[0]
            
            # Nombre de métriques
            cursor.execute("SELECT COUNT(*) as count FROM metrics")
            stats["metrics_count"] = cursor.fetchone()[0]
            
            # Taille de la base de données
            db_file = Path(self.db_path)
            if db_file.exists():
                stats["database_size_mb"] = db_file.stat().st_size / (1024 * 1024)
            else:
                stats["database_size_mb"] = 0
            
            # Dernière mise à jour
            cursor.execute("SELECT MAX(updated_at) as last_update FROM experiments")
            stats["last_update"] = cursor.fetchone()[0]
        
        return stats

# Instance singleton du gestionnaire de base de données
db_manager = DatabaseManager()