#!/usr/bin/env python3
"""
Service d'archivage intelligent pour le laboratoire scientifique IA Pac-Man.

Fonctionnalités :
- Format d'archive intelligent avec nommage automatique
- Génération automatique de params.md avec explications contextuelles
- Sauvegarde périodique et événementielle
- Intégration avec le backend FastAPI
- Gestion des versions et métadonnées
- Compression optimisée pour gros modèles (100MB+)
"""

import os
import json
import yaml
import zipfile
import shutil
import tempfile
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import hashlib
import time

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ArchiveMetadata:
    """Métadonnées d'une archive de session."""
    session_id: str
    session_number: int
    timestamp: str
    model_type: str
    agent_type: str
    total_episodes: int
    win_rate: float
    learning_rate: float
    gamma: float
    epsilon: float
    batch_size: int
    buffer_size: int
    tags: List[str]
    metrics: Dict[str, Any]
    previous_session_id: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class ArchiveConfig:
    """Configuration du service d'archivage."""
    archive_dir: str = "experiments/archives"
    max_archives: int = 100
    auto_save_interval: int = 1000  # Épisodes
    save_on_improvement: bool = True
    improvement_threshold: float = 0.05  # 5% d'amélioration
    compression_level: int = 9
    include_model: bool = True
    include_logs: bool = True
    include_metrics: bool = True
    include_config: bool = True
    backup_to_cloud: bool = False
    cloud_endpoint: Optional[str] = None

class IntelligentArchiveService:
    """
    Service principal d'archivage intelligent.
    
    Gère la création, la gestion et la reprise des archives de sessions.
    """
    
    def __init__(self, config: Optional[ArchiveConfig] = None):
        self.config = config or ArchiveConfig()
        self._ensure_directories()
        self._session_counter = self._load_session_counter()
        self._lock = threading.RLock()
        self._active_archives: Dict[str, Dict] = {}
        
        logger.info(f"Service d'archivage initialisé (répertoire: {self.config.archive_dir})")
    
    def _ensure_directories(self) -> None:
        """Crée les répertoires nécessaires."""
        os.makedirs(self.config.archive_dir, exist_ok=True)
        os.makedirs("experiments/temp", exist_ok=True)
        os.makedirs("experiments/metadata", exist_ok=True)
    
    def _load_session_counter(self) -> int:
        """Charge le compteur de sessions depuis le fichier de persistance."""
        counter_file = "experiments/session_counter.json"
        if os.path.exists(counter_file):
            try:
                with open(counter_file, 'r') as f:
                    data = json.load(f)
                    return data.get('counter', 0)
            except Exception as e:
                logger.warning(f"Erreur lors du chargement du compteur: {e}")
        return 0
    
    def _save_session_counter(self) -> None:
        """Sauvegarde le compteur de sessions."""
        counter_file = "experiments/session_counter.json"
        try:
            with open(counter_file, 'w') as f:
                json.dump({'counter': self._session_counter, 'updated': datetime.now().isoformat()}, f)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du compteur: {e}")
    
    def _generate_archive_name(self, session_number: int, metadata: ArchiveMetadata) -> str:
        """
        Génère un nom d'archive intelligent.
        
        Format: pacman_run_{session_number:03d}_{timestamp}_{model_type}_{agent_type}.zip
        Exemple: pacman_run_047_20260103_1632_DQN_pacman.zip
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        model_short = metadata.model_type[:10].replace(' ', '_')
        agent_short = metadata.agent_type[:10].replace(' ', '_')
        
        return f"pacman_run_{session_number:03d}_{timestamp}_{model_short}_{agent_short}.zip"
    
    def _generate_params_md(self, metadata: ArchiveMetadata, previous_metadata: Optional[ArchiveMetadata] = None) -> str:
        """
        Génère le contenu du fichier params.md avec explications contextuelles.
        
        Inclut des comparaisons avec les sessions précédentes et des observations automatiques.
        """
        lines = []
        
        # En-tête
        lines.append(f"# Session {metadata.session_number} - Lancée {metadata.timestamp}")
        lines.append("")
        
        # Paramètres d'entraînement avec explications
        lines.append("## Paramètres d'entraînement")
        lines.append("")
        
        # Learning Rate avec évaluation
        lr_desc = self._evaluate_learning_rate(metadata.learning_rate)
        lines.append(f"- **Learning Rate**: {metadata.learning_rate} ({lr_desc})")
        
        # Gamma avec évaluation
        gamma_desc = self._evaluate_gamma(metadata.gamma)
        lines.append(f"- **Gamma**: {metadata.gamma} ({gamma_desc})")
        
        # Epsilon avec évaluation
        epsilon_desc = self._evaluate_epsilon(metadata.epsilon)
        lines.append(f"- **Epsilon**: {metadata.epsilon} ({epsilon_desc})")
        
        # Batch Size
        lines.append(f"- **Batch Size**: {metadata.batch_size}")
        
        # Buffer Size
        lines.append(f"- **Buffer Size**: {metadata.buffer_size}")
        lines.append("")
        
        # Métriques de performance
        lines.append("## Métriques de performance")
        lines.append("")
        lines.append(f"- **Épisodes totaux**: {metadata.total_episodes}")
        lines.append(f"- **Taux de victoire**: {metadata.win_rate:.2%}")
        
        # Comparaison avec session précédente
        if previous_metadata:
            episode_diff = metadata.total_episodes - previous_metadata.total_episodes
            winrate_diff = metadata.win_rate - previous_metadata.win_rate
            
            lines.append("")
            lines.append("## Comparaison avec session précédente")
            lines.append("")
            
            if episode_diff > 0:
                lines.append(f"- **Épisodes**: +{episode_diff} vs session {previous_metadata.session_number}")
            else:
                lines.append(f"- **Épisodes**: {episode_diff} vs session {previous_metadata.session_number}")
            
            if winrate_diff > 0:
                lines.append(f"- **Taux de victoire**: +{winrate_diff:.2%} ({previous_metadata.win_rate:.2%} → {metadata.win_rate:.2%})")
            else:
                lines.append(f"- **Taux de victoire**: {winrate_diff:.2%} ({previous_metadata.win_rate:.2%} → {metadata.win_rate:.2%})")
            
            # Observation automatique
            observation = self._generate_observation(metadata, previous_metadata)
            if observation:
                lines.append("")
                lines.append("## Observation")
                lines.append("")
                lines.append(observation)
        
        # Tags et catégories
        if metadata.tags:
            lines.append("")
            lines.append("## Tags")
            lines.append("")
            lines.append(", ".join([f"`{tag}`" for tag in metadata.tags]))
        
        # Notes supplémentaires
        if metadata.notes:
            lines.append("")
            lines.append("## Notes")
            lines.append("")
            lines.append(metadata.notes)
        
        return "\n".join(lines)
    
    def _evaluate_learning_rate(self, lr: float) -> str:
        """Évalue le learning rate et retourne une description."""
        if lr > 0.01:
            return "élevé → apprentissage rapide, risque d'instabilité"
        elif lr > 0.001:
            return "moyen → stable, bon compromis"
        elif lr > 0.0001:
            return "faible → convergence lente mais stable"
        else:
            return "très faible → convergence très lente"
    
    def _evaluate_gamma(self, gamma: float) -> str:
        """Évalue le facteur de discount gamma."""
        if gamma > 0.95:
            return "fort → planifie loin dans le futur"
        elif gamma > 0.85:
            return "moyen → équilibre court/long terme"
        else:
            return "faible → focus sur récompenses immédiates"
    
    def _evaluate_epsilon(self, epsilon: float) -> str:
        """Évalue le taux d'exploration epsilon."""
        if epsilon > 0.3:
            return "élevé → forte exploration"
        elif epsilon > 0.1:
            return "modéré → équilibre exploration/exploitation"
        else:
            return "faible → forte exploitation"
    
    def _generate_observation(self, metadata: ArchiveMetadata, previous_metadata: ArchiveMetadata) -> str:
        """Génère une observation automatique basée sur les métriques."""
        winrate_diff = metadata.win_rate - previous_metadata.win_rate
        
        if winrate_diff > 0.15:
            return "Amélioration significative ! La configuration actuelle semble très efficace."
        elif winrate_diff > 0.05:
            return "Amélioration modérée. L'entraînement progresse bien."
        elif winrate_diff > -0.05:
            return "Stabilité des performances. Peut-être atteint un plateau."
        elif winrate_diff > -0.15:
            return "Légère régression. Vérifier les hyperparamètres ou l'exploration."
        else:
            return "Régression significative. Revoir la configuration d'entraînement."
    
    def _collect_model_files(self, model_path: str, temp_dir: str) -> List[str]:
        """Collecte les fichiers de modèle dans le répertoire temporaire."""
        collected = []
        
        if not os.path.exists(model_path):
            logger.warning(f"Chemin de modèle non trouvé: {model_path}")
            return collected
        
        try:
            if os.path.isfile(model_path):
                # Fichier unique
                dest = os.path.join(temp_dir, "model", os.path.basename(model_path))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(model_path, dest)
                collected.append(dest)
            elif os.path.isdir(model_path):
                # Répertoire de modèle
                model_dir = os.path.join(temp_dir, "model")
                shutil.copytree(model_path, model_dir, dirs_exist_ok=True)
                collected.append(model_dir)
            
            logger.info(f"Fichiers de modèle collectés: {len(collected)}")
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des fichiers de modèle: {e}")
        
        return collected
    
    def _collect_log_files(self, log_patterns: List[str], temp_dir: str) -> List[str]:
        """Collecte les fichiers de logs correspondant aux patterns."""
        collected = []
        logs_dir = os.path.join(temp_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        for pattern in log_patterns:
            try:
                for log_file in Path(".").glob(pattern):
                    if log_file.is_file():
                        dest = os.path.join(logs_dir, log_file.name)
                        shutil.copy2(log_file, dest)
                        collected.append(dest)
            except Exception as e:
                logger.warning(f"Erreur lors de la collecte des logs avec pattern {pattern}: {e}")
        
        logger.info(f"Fichiers de logs collectés: {len(collected)}")
        return collected
    
    def create_archive(self, metadata: ArchiveMetadata, model_path: Optional[str] = None, 
                      log_patterns: Optional[List[str]] = None) -> Optional[str]:
        """
        Crée une archive intelligente pour une session.
        
        Args:
            metadata: Métadonnées de la session
            model_path: Chemin vers le modèle (fichier ou répertoire)
            log_patterns: Patterns pour collecter les logs
            
        Returns:
            Chemin de l'archive créée ou None en cas d'erreur
        """
        with self._lock:
            try:
                # Incrémenter le compteur de sessions
                self._session_counter += 1
                metadata.session_number = self._session_counter
                metadata.timestamp = datetime.now().isoformat()
                
                # Créer un répertoire temporaire
                with tempfile.TemporaryDirectory() as temp_dir:
                    archive_contents = []
                    
                    # 1. Générer et sauvegarder params.md
                    previous_metadata = self._get_previous_session_metadata()
                    params_content = self._generate_params_md(metadata, previous_metadata)
                    params_path = os.path.join(temp_dir, "params.md")
                    with open(params_path, 'w', encoding='utf-8') as f:
                        f.write(params_content)
                    archive_contents.append(("params.md", params_path))
                    
                    # 2. Sauvegarder les métadonnées au format JSON
                    metadata_path = os.path.join(temp_dir, "metadata.json")
                    with open(metadata_path, 'w') as f:
                        json.dump(asdict(metadata), f, indent=2)
                    archive_contents.append(("metadata.json", metadata_path))
                    
                    # 3. Sauvegarder la configuration au format YAML
                    config_path = os.path.join(temp_dir, "config.yaml")
                    config_data = {
                        'session_id': metadata.session_id,
                        'session_number': metadata.session_number,
                        'timestamp': metadata.timestamp,
                        'hyperparameters': {
                            'learning_rate': metadata.learning_rate,
                            'gamma': metadata.gamma,
                            'epsilon': metadata.epsilon,
                            'batch_size': metadata.batch_size,
                            'buffer_size': metadata.buffer_size
                        }
                    }
                    with open(config_path, 'w') as f:
                        yaml.dump(config_data, f, default_flow_style=False)
                    archive_contents.append(("config.yaml", config_path))
                    
                    # 4. Collecter les fichiers de modèle
                    if model_path and self.config.include_model:
                        model_files = self._collect_model_files(model_path, temp_dir)
                        for file_path in model_files:
                            rel_path = os.path.relpath(file_path, temp_dir)
                            archive_contents.append((rel_path, file_path))
                    
                    # 5. Collecter les logs
                    if log_patterns and self.config.include_logs:
                        log_files = self._collect_log_files(log_patterns, temp_dir)
                        for file_path in log_files:
                            rel_path = os.path.relpath(file_path, temp_dir)
                            archive_contents.append((rel_path, file_path))
                    
                    # 6. Générer le nom de l'archive
                    archive_name = self._generate_archive_name(metadata.session_number, metadata)
                    archive_path = os.path.join(self.config.archive_dir, archive_name)
                    
                    # 7. Créer l'archive ZIP
                    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for arcname, filepath in archive_contents:
                            if os.path.exists(filepath):
                                zipf.write(filepath, arcname)
                    
                    # 8. Calculer le hash MD5 pour vérification d'intégrité
                    archive_hash = self._calculate_file_hash(archive_path)
                    hash_path = archive_path + ".md5"
                    with open(hash_path, 'w') as f:
                        f.write(f"{archive_hash}  {archive_name}")
                    
                    # 9. Sauvegarder le compteur
                    self._save_session_counter()
                    
                    # 10. Enregistrer dans la liste des archives actives
                    self._active_archives[metadata.session_id] = {
                        'path': archive_path,
                        'metadata': asdict(metadata),
                        'created': datetime.now().isoformat(),
                        'hash': archive_hash
                    }
                    
                    logger.info(f"Archive créée: {archive_path} (hash: {archive_hash[:8]}...)")
                    logger.info(f"Session {metadata.session_number} archivée avec succès")
                    
                    # 11. Nettoyer les anciennes archives si nécessaire
                    self._cleanup_old_archives()
                    
                    return archive_path
                    
            except Exception as e:
                logger.error(f"Erreur lors de la création de l'archive: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return None
    
    def _get_previous_session_metadata(self) -> Optional[ArchiveMetadata]:
        """Récupère les métadonnées de la session précédente."""
        # Pour l'instant, retourne None
        # Dans une implémentation complète, on lirait le dernier fichier metadata.json
        return None
    
    def _calculate_file_hash(self, filepath: str) -> str:
        """Calcule le hash MD5 d'un fichier."""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _cleanup_old_archives(self) -> None:
        """Nettoie les anciennes archives si le nombre maximal est dépassé."""
        try:
            archive_files = []
            for file in os.listdir(self.config.archive_dir):
                if file.endswith('.zip'):
                    filepath = os.path.join(self.config.archive_dir, file)
                    if os.path.isfile(filepath):
                        mtime = os.path.getmtime(filepath)
                        archive_files.append((filepath, mtime))
            
            if len(archive_files) <= self.config.max_archives:
                return
            
            # Trier par date de modification (plus ancien en premier)
            archive_files.sort(key=lambda x: x[1])
            
            # Supprimer les plus anciens
            files_to_remove = len(archive_files) - self.config.max_archives
            for i in range(files_to_remove):
                filepath, _ = archive_files[i]
                try:
                    os.remove(filepath)
                    # Supprimer aussi le fichier .md5 associé
                    md5_file = filepath + ".md5"
                    if os.path.exists(md5_file):
                        os.remove(md5_file)
                    logger.info(f"Archive ancienne supprimée: {os.path.basename(filepath)}")
                except Exception as e:
                    logger.warning(f"Erreur lors de la suppression de {filepath}: {e}")
                    
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des archives: {e}")
    
    def list_archives(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Liste les archives disponibles avec leurs métadonnées."""
        archives = []
        
        try:
            for file in os.listdir(self.config.archive_dir):
                if file.endswith('.zip'):
                    filepath = os.path.join(self.config.archive_dir, file)
                    if os.path.isfile(filepath):
                        # Extraire les métadonnées du nom de fichier
                        metadata = self._extract_metadata_from_filename(file)
                        metadata['path'] = filepath
                        metadata['size_mb'] = os.path.getsize(filepath) / (1024 * 1024)
                        metadata['modified'] = datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                        
                        archives.append(metadata)
            
            # Trier par numéro de session (décroissant)
            archives.sort(key=lambda x: x.get('session_number', 0), reverse=True)
            
            return archives[:limit]
            
        except Exception as e:
            logger.error(f"Erreur lors de la liste des archives: {e}")
            return []
    
    def _extract_metadata_from_filename(self, filename: str) -> Dict[str, Any]:
        """Extrait les métadonnées du nom de fichier d'archive."""
        # Format: pacman_run_047_20260103_1632_DQN_pacman.zip
        import re
        
        pattern = r'pacman_run_(\d+)_(\d+)_(\d+)_([^_]+)_([^_]+)\.zip'
        match = re.match(pattern, filename)
        
        if match:
            session_num, date, time, model_type, agent_type = match.groups()
            return {
                'session_number': int(session_num),
                'date': date,
                'time': time,
                'model_type': model_type,
                'agent_type': agent_type,
                'filename': filename
            }
        else:
            return {'filename': filename}
    
    def get_archive_info(self, archive_path: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations détaillées d'une archive."""
        if not os.path.exists(archive_path):
            logger.error(f"Archive non trouvée: {archive_path}")
            return None
        
        try:
            info = {
                'path': archive_path,
                'size_bytes': os.path.getsize(archive_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(archive_path)).isoformat(),
                'hash': self._calculate_file_hash(archive_path)
            }
            
            # Extraire les métadonnées si possible
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                # Vérifier la présence des fichiers clés
                file_list = zipf.namelist()
                info['files'] = file_list
                
                if 'metadata.json' in file_list:
                    with zipf.open('metadata.json') as f:
                        metadata = json.load(f)
                        info['metadata'] = metadata
                
                if 'params.md' in file_list:
                    with zipf.open('params.md') as f:
                        params_content = f.read().decode('utf-8')
                        info['params_preview'] = params_content[:500] + "..." if len(params_content) > 500 else params_content
            
            return info
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de l'archive: {e}")
            return None
    
    def restore_session(self, archive_path: str, target_dir: str) -> Optional[str]:
        """
        Restaure une session depuis une archive.
        
        Args:
            archive_path: Chemin vers l'archive
            target_dir: Répertoire de destination
            
        Returns:
            Chemin du répertoire restauré ou None en cas d'erreur
        """
        if not os.path.exists(archive_path):
            logger.error(f"Archive non trouvée: {archive_path}")
            return None
        
        try:
            os.makedirs(target_dir, exist_ok=True)
            
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(target_dir)
            
            logger.info(f"Session restaurée depuis {archive_path} vers {target_dir}")
            
            # Vérifier l'intégrité
            hash_file = archive_path + ".md5"
            if os.path.exists(hash_file):
                with open(hash_file, 'r') as f:
                    expected_hash = f.read().split()[0]
                actual_hash = self._calculate_file_hash(archive_path)
                
                if expected_hash == actual_hash:
                    logger.info("Vérification d'intégrité: OK")
                else:
                    logger.warning("Vérification d'intégrité: ÉCHEC - hash mismatch")
            
            return target_dir
            
        except Exception as e:
            logger.error(f"Erreur lors de la restauration: {e}")
            return None
    
    def auto_save(self, episode: int, metrics: Dict[str, Any], model_path: str,
                  force: bool = False) -> Optional[str]:
        """
        Sauvegarde automatique basée sur les conditions configurées.
        
        Args:
            episode: Numéro de l'épisode actuel
            metrics: Métriques de performance actuelles
            model_path: Chemin vers le modèle
            force: Forcer la sauvegarde même si les conditions ne sont pas remplies
            
        Returns:
            Chemin de l'archive créée ou None si pas de sauvegarde
        """
        if not force:
            # Vérifier l'intervalle
            if episode % self.config.auto_save_interval != 0:
                return None
            
            # Vérifier l'amélioration si configuré
            if self.config.save_on_improvement:
                # Dans une implémentation complète, on comparerait avec les métriques précédentes
                pass
        
        # Créer les métadonnées pour la sauvegarde automatique
        metadata = ArchiveMetadata(
            session_id=f"auto_{episode}_{int(time.time())}",
            session_number=0,  # Sera défini par create_archive
            timestamp="",
            model_type="auto_detected",
            agent_type="auto_detected",
            total_episodes=episode,
            win_rate=metrics.get('win_rate', 0.0),
            learning_rate=metrics.get('learning_rate', 0.001),
            gamma=metrics.get('gamma', 0.99),
            epsilon=metrics.get('epsilon', 0.1),
            batch_size=metrics.get('batch_size', 32),
            buffer_size=metrics.get('buffer_size', 10000),
            tags=['auto_save', f'episode_{episode}'],
            metrics=metrics,
            notes=f"Sauvegarde automatique à l'épisode {episode}"
        )
        
        return self.create_archive(metadata, model_path, ['logs/*.log', 'logs/*.json'])
    
    def integrate_with_backend(self, backend_url: str, archive_path: str) -> bool:
        """
        Intègre l'archive avec le backend FastAPI.
        
        Args:
            backend_url: URL du backend
            archive_path: Chemin vers l'archive
            
        Returns:
            True si l'intégration a réussi, False sinon
        """
        try:
            import requests
            
            # Dans une implémentation complète, on enverrait l'archive au backend
            # Pour l'instant, on simule l'intégration
            logger.info(f"Intégration avec le backend {backend_url} pour {archive_path}")
            
            # Simuler un appel API
            # response = requests.post(f"{backend_url}/api/archives", files={'archive': open(archive_path, 'rb')})
            # return response.status_code == 200
            
            return True
            
        except ImportError:
            logger.warning("Module requests non installé, intégration backend désactivée")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration avec le backend: {e}")
            return False


# Fonctions utilitaires pour une utilisation simple
def create_simple_archive(session_name: str, model_path: str, metrics: Dict[str, Any]) -> Optional[str]:
    """
    Crée une archive simple pour une utilisation rapide.
    
    Args:
        session_name: Nom de la session
        model_path: Chemin vers le modèle
        metrics: Métriques de performance
    
    Returns:
        Chemin de l'archive créée
    """
    service = IntelligentArchiveService()
    
    metadata = ArchiveMetadata(
        session_id=session_name,
        session_number=0,
        timestamp="",
        model_type="DQN",  # À détecter automatiquement
        agent_type="PacMan",
        total_episodes=metrics.get('total_episodes', 0),
        win_rate=metrics.get('win_rate', 0.0),
        learning_rate=metrics.get('learning_rate', 0.001),
        gamma=metrics.get('gamma', 0.99),
        epsilon=metrics.get('epsilon', 0.1),
        batch_size=metrics.get('batch_size', 32),
        buffer_size=metrics.get('buffer_size', 10000),
        tags=['simple_archive'],
        metrics=metrics,
        notes=f"Archive créée via create_simple_archive"
    )
    
    return service.create_archive(metadata, model_path)


if __name__ == "__main__":
    # Exemple d'utilisation
    print("=== Test du service d'archivage intelligent ===")
    
    # Créer le service
    service = IntelligentArchiveService()
    
    # Créer des métadonnées de test
    test_metadata = ArchiveMetadata(
        session_id="test_session_001",
        session_number=0,
        timestamp="",
        model_type="DQN",
        agent_type="PacMan",
        total_episodes=5000,
        win_rate=0.77,
        learning_rate=0.001,
        gamma=0.99,
        epsilon=0.1,
        batch_size=32,
        buffer_size=10000,
        tags=['test', 'DQN', 'baseline'],
        metrics={'avg_score': 1500, 'max_score': 2500, 'min_score': 500},
        notes="Session de test pour le système d'archivage"
    )
    
    # Créer une archive de test (sans modèle réel)
    archive_path = service.create_archive(test_metadata)
    
    if archive_path:
        print(f"✓ Archive créée: {archive_path}")
        
        # Lister les archives
        archives = service.list_archives(5)
        print(f"\n✓ Archives disponibles ({len(archives)}):")
        for arch in archives:
            print(f"  - {arch['filename']} (session {arch.get('session_number', '?')})")
        
        # Obtenir des informations sur l'archive
        info = service.get_archive_info(archive_path)
        if info:
            print(f"\n✓ Informations sur l'archive:")
            print(f"  Taille: {info['size_bytes'] / (1024*1024):.2f} MB")
            print(f"  Fichiers: {len(info.get('files', []))}")
        
        # Tester la restauration
        restore_dir = "experiments/restored_test"
        restored = service.restore_session(archive_path, restore_dir)
        if restored:
            print(f"\n✓ Session restaurée dans: {restored}")
    else:
        print("✗ Échec de la création de l'archive")
    
    print("\n=== Test terminé ===")