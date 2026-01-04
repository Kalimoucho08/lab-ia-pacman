#!/usr/bin/env python3
"""
Système de reprise de sessions pour le laboratoire scientifique IA Pac-Man.

Fonctionnalités :
- Chargement d'archives existantes
- Continuation d'entraînement à partir d'un point de sauvegarde
- Comparaison de sessions (diff de paramètres)
- Fusion de sessions pour méta-analyse
- Migration depuis l'ancien système
"""

import os
import json
import yaml
import zipfile
import shutil
import tempfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ResumeConfig:
    """Configuration pour la reprise de session."""
    target_dir: str = "experiments/resumed"
    overwrite_existing: bool = False
    validate_integrity: bool = True
    extract_model: bool = True
    extract_logs: bool = True
    extract_config: bool = True
    merge_with_current: bool = False
    continuation_prefix: str = "resumed_"

@dataclass 
class SessionComparison:
    """Résultat de la comparaison entre deux sessions."""
    session_a_id: str
    session_b_id: str
    parameter_diffs: Dict[str, Dict[str, Any]]
    metric_diffs: Dict[str, Dict[str, Any]]
    compatibility_score: float
    recommendations: List[str]

class SessionResumer:
    """
    Système de reprise de sessions.
    
    Permet de charger des archives existantes et de reprendre l'entraînement
    à partir d'un point de sauvegarde.
    """
    
    def __init__(self, config: Optional[ResumeConfig] = None):
        self.config = config or ResumeConfig()
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Crée les répertoires nécessaires."""
        os.makedirs(self.config.target_dir, exist_ok=True)
        os.makedirs("experiments/comparisons", exist_ok=True)
        os.makedirs("experiments/merged", exist_ok=True)
    
    def load_archive(self, archive_path: str) -> Optional[Dict[str, Any]]:
        """
        Charge une archive et extrait ses métadonnées.
        
        Args:
            archive_path: Chemin vers l'archive ZIP
            
        Returns:
            Dictionnaire contenant les métadonnées et chemins des fichiers extraits
        """
        if not os.path.exists(archive_path):
            logger.error(f"Archive non trouvée: {archive_path}")
            return None
        
        try:
            # Vérifier l'intégrité
            if self.config.validate_integrity:
                if not self._validate_archive_integrity(archive_path):
                    logger.warning(f"Intégrité de l'archive non vérifiée: {archive_path}")
            
            # Créer un répertoire temporaire pour l'extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extraire l'archive
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Charger les métadonnées
                metadata = self._load_metadata(temp_dir)
                if not metadata:
                    logger.error(f"Métadonnées non trouvées dans l'archive: {archive_path}")
                    return None
                
                # Préparer la structure de retour
                result = {
                    'metadata': metadata,
                    'extracted_dir': temp_dir,
                    'archive_path': archive_path,
                    'files': {}
                }
                
                # Identifier les fichiers importants
                important_files = self._identify_important_files(temp_dir)
                result['files'] = important_files
                
                # Copier les fichiers vers le répertoire cible si demandé
                if self.config.extract_model or self.config.extract_logs or self.config.extract_config:
                    target_subdir = self._copy_to_target(temp_dir, metadata.get('session_id', 'unknown'))
                    result['target_dir'] = target_subdir
                
                logger.info(f"Archive chargée: {archive_path} (session: {metadata.get('session_id', 'unknown')})")
                return result
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'archive: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _validate_archive_integrity(self, archive_path: str) -> bool:
        """Valide l'intégrité de l'archive via son hash MD5."""
        hash_file = archive_path + ".md5"
        
        if not os.path.exists(hash_file):
            logger.warning(f"Fichier de hash non trouvé: {hash_file}")
            return True  # Continuer sans validation
        
        try:
            with open(hash_file, 'r') as f:
                expected_hash = f.read().strip().split()[0]
            
            # Calculer le hash actuel
            hash_md5 = hashlib.md5()
            with open(archive_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            actual_hash = hash_md5.hexdigest()
            
            if expected_hash == actual_hash:
                logger.info(f"Vérification d'intégrité OK: {archive_path}")
                return True
            else:
                logger.error(f"Échec de vérification d'intégrité: {archive_path}")
                logger.error(f"  Attendu: {expected_hash}")
                logger.error(f"  Obtenu:  {actual_hash}")
                return False
                
        except Exception as e:
            logger.warning(f"Erreur lors de la validation d'intégrité: {e}")
            return True  # Continuer malgré l'erreur
    
    def _load_metadata(self, extracted_dir: str) -> Optional[Dict[str, Any]]:
        """Charge les métadonnées depuis le répertoire extrait."""
        metadata_files = [
            os.path.join(extracted_dir, "metadata.json"),
            os.path.join(extracted_dir, "config.yaml"),
            os.path.join(extracted_dir, "params.md")
        ]
        
        metadata = {}
        
        # Charger metadata.json
        metadata_json_path = metadata_files[0]
        if os.path.exists(metadata_json_path):
            try:
                with open(metadata_json_path, 'r') as f:
                    metadata.update(json.load(f))
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de metadata.json: {e}")
        
        # Charger config.yaml
        config_yaml_path = metadata_files[1]
        if os.path.exists(config_yaml_path):
            try:
                with open(config_yaml_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    metadata['config'] = config_data
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de config.yaml: {e}")
        
        # Extraire des informations de params.md
        params_md_path = metadata_files[2]
        if os.path.exists(params_md_path):
            try:
                with open(params_md_path, 'r', encoding='utf-8') as f:
                    params_content = f.read()
                    # Extraire des informations basiques
                    metadata['params_preview'] = params_content[:500]
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de params.md: {e}")
        
        # Ajouter des informations sur les fichiers
        model_files = []
        log_files = []
        
        for root, dirs, files in os.walk(extracted_dir):
            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, extracted_dir)
                
                if 'model' in rel_path.lower():
                    model_files.append(rel_path)
                elif 'log' in rel_path.lower():
                    log_files.append(rel_path)
        
        metadata['model_files'] = model_files
        metadata['log_files'] = log_files
        
        return metadata if metadata else None
    
    def _identify_important_files(self, extracted_dir: str) -> Dict[str, List[str]]:
        """Identifie les fichiers importants dans le répertoire extrait."""
        important = {
            'model_files': [],
            'config_files': [],
            'log_files': [],
            'data_files': [],
            'other_files': []
        }
        
        for root, dirs, files in os.walk(extracted_dir):
            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, extracted_dir)
                
                # Catégoriser le fichier
                if any(keyword in rel_path.lower() for keyword in ['model', 'checkpoint', 'weights', '.pth', '.pt', '.h5']):
                    important['model_files'].append(rel_path)
                elif any(keyword in rel_path.lower() for keyword in ['config', 'params', 'settings', '.yaml', '.yml', '.json']):
                    important['config_files'].append(rel_path)
                elif any(keyword in rel_path.lower() for keyword in ['log', 'metric', 'history', '.log', '.csv', '.txt']):
                    important['log_files'].append(rel_path)
                elif any(keyword in rel_path.lower() for keyword in ['data', 'dataset', 'buffer', '.npz', '.npy']):
                    important['data_files'].append(rel_path)
                else:
                    important['other_files'].append(rel_path)
        
        return important
    
    def _copy_to_target(self, extracted_dir: str, session_id: str) -> str:
        """Copie les fichiers extraits vers le répertoire cible."""
        # Créer un sous-répertoire pour cette session
        safe_session_id = "".join(c for c in session_id if c.isalnum() or c in '_-')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        target_subdir = os.path.join(self.config.target_dir, f"{self.config.continuation_prefix}{safe_session_id}_{timestamp}")
        
        os.makedirs(target_subdir, exist_ok=True)
        
        # Copier les fichiers selon la configuration
        files_copied = 0
        
        for root, dirs, files in os.walk(extracted_dir):
            for file in files:
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, extracted_dir)
                dst_path = os.path.join(target_subdir, rel_path)
                
                # Vérifier si on doit copier ce type de fichier
                should_copy = False
                
                if self.config.extract_model and any(keyword in rel_path.lower() for keyword in ['model', 'checkpoint', 'weights']):
                    should_copy = True
                elif self.config.extract_config and any(keyword in rel_path.lower() for keyword in ['config', 'params', 'metadata']):
                    should_copy = True
                elif self.config.extract_logs and any(keyword in rel_path.lower() for keyword in ['log', 'metric', 'history']):
                    should_copy = True
                else:
                    # Copier les autres fichiers importants
                    should_copy = True
                
                if should_copy:
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    shutil.copy2(src_path, dst_path)
                    files_copied += 1
        
        logger.info(f"{files_copied} fichiers copiés vers {target_subdir}")
        return target_subdir
    
    def resume_training(self, archive_path: str, new_session_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Reprend l'entraînement à partir d'une archive.
        
        Args:
            archive_path: Chemin vers l'archive à reprendre
            new_session_config: Configuration pour la nouvelle session
            
        Returns:
            Informations sur la session reprise ou None en cas d'erreur
        """
        # Charger l'archive
        archive_data = self.load_archive(archive_path)
        if not archive_data:
            return None
        
        try:
            metadata = archive_data['metadata']
            target_dir = archive_data.get('target_dir')
            
            # Préparer la configuration de continuation
            continuation_config = {
                'resumed_from': {
                    'archive_path': archive_path,
                    'session_id': metadata.get('session_id'),
                    'session_number': metadata.get('session_number'),
                    'timestamp': metadata.get('timestamp')
                },
                'new_session': new_session_config,
                'resume_timestamp': datetime.now().isoformat(),
                'model_files': archive_data['files'].get('model_files', [])
            }
            
            # Sauvegarder la configuration de continuation
            config_path = os.path.join(target_dir, "continuation_config.json")
            with open(config_path, 'w') as f:
                json.dump(continuation_config, f, indent=2)
            
            # Générer un script de reprise
            resume_script = self._generate_resume_script(continuation_config, target_dir)
            script_path = os.path.join(target_dir, "resume_training.py")
            with open(script_path, 'w') as f:
                f.write(resume_script)
            
            logger.info(f"Session reprise depuis {archive_path}")
            logger.info(f"Configuration de continuation sauvegardée: {config_path}")
            logger.info(f"Script de reprise généré: {script_path}")
            
            return {
                'success': True,
                'resumed_from': archive_path,
                'target_directory': target_dir,
                'continuation_config': continuation_config,
                'resume_script': script_path
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la reprise de l'entraînement: {e}")
            return None
    
    def _generate_resume_script(self, continuation_config: Dict[str, Any], target_dir: str) -> str:
        """Génère un script Python pour reprendre l'entraînement."""
        script = '''#!/usr/bin/env python3
"""
Script de reprise d'entraînement généré automatiquement.
Reprend l'entraînement à partir d'une session sauvegardée.
"""

import os
import sys
import json
import torch
import numpy as np
from datetime import datetime

# Configuration de continuation
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "continuation_config.json")

def load_continuation_config():
    """Charge la configuration de continuation."""
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def find_model_file(target_dir):
    """Trouve le fichier de modèle dans le répertoire cible."""
    model_extensions = ['.pth', '.pt', '.h5', '.zip', '.model']
    
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if any(file.endswith(ext) for ext in model_extensions):
                return os.path.join(root, file)
    
    return None

def resume_training():
    """Fonction principale de reprise d'entraînement."""
    print("=== Reprise d'entraînement ===")
    
    # Charger la configuration
    config = load_continuation_config()
    print(f"Reprise depuis: {config['resumed_from']['session_id']}")
    print(f"Session originale: #{config['resumed_from']['session_number']}")
    
    # Trouver le modèle
    target_dir = os.path.dirname(CONFIG_PATH)
    model_path = find_model_file(target_dir)
    
    if model_path:
        print(f"Modèle trouvé: {model_path}")
        
        # Charger le modèle (exemple pour PyTorch)
        try:
            # Cette partie dépend du framework utilisé
            # Exemple pour PyTorch:
            # model = torch.load(model_path)
            # print(f"Modèle chargé avec succès")
            pass
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
    else:
        print("Avertissement: Aucun fichier de modèle trouvé")
    
    # Appliquer la nouvelle configuration
    new_config = config['new_session']
    print(f"Nouvelle configuration:")
    print(f"  Learning rate: {new_config.get('learning_rate', 'N/A')}")
    print(f"  Gamma: {new_config.get('gamma', 'N/A')}")
    print(f"  Batch size: {new_config.get('batch_size', 'N/A')}")
    
    # Ici, vous intégreriez le code pour reprendre l'entraînement
    # avec votre framework RL spécifique
    
    print("\\n=== Instructions pour reprendre l'entraînement ===")
    print("1. Adapter ce script à votre framework RL (Stable-Baselines3, etc.)")
    print("2. Charger le modèle depuis le fichier identifié")
    print("3. Configurer l'environnement avec les paramètres de la session originale")
    print("4. Reprendre l'entraînement avec les nouveaux hyperparamètres")
    print("5. Sauvegarder régulièrement avec le système d'archivage intelligent")
    
    return True

if __name__ == "__main__":
    success = resume_training()
    sys.exit(0 if success else 1)
'''
        return script
    
    def compare_sessions(self, archive_path_a: str, archive_path_b: str) -> Optional[SessionComparison]:
        """
        Compare deux sessions archivées.
        
        Args:
            archive_path_a: Chemin vers la première archive
            archive_path_b: Chemin vers la deuxième archive
            
        Returns:
            Ob
