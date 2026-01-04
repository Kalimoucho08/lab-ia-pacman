#!/usr/bin/env python3
"""
Validation d'archives pour le système d'archivage intelligent.

Fonctionnalités :
- Vérification d'intégrité (hash MD5, SHA256)
- Validation de structure et de contenu
- Détection d'anomalies et de corruption
- Signature numérique et vérification
- Rapports de validation détaillés
"""

import os
import json
import yaml
import zipfile
import tarfile
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Résultat de la validation d'une archive."""
    archive_path: str
    is_valid: bool
    validation_time: str
    checks_performed: List[str]
    errors: List[str]
    warnings: List[str]
    statistics: Dict[str, Any]
    integrity_hash: Optional[str] = None
    signature_valid: Optional[bool] = None

@dataclass
class ArchiveStructure:
    """Structure attendue d'une archive."""
    required_files: List[str]
    optional_files: List[str]
    file_patterns: Dict[str, str]  # pattern -> description
    max_size_mb: int
    allowed_formats: List[str]

class ArchiveValidator:
    """
    Validateur d'archives pour le système d'archivage.
    
    Vérifie l'intégrité, la structure et la validité des archives.
    """
    
    # Structure standard pour les archives Pac-Man
    PACMAN_ARCHIVE_STRUCTURE = ArchiveStructure(
        required_files=[
            "metadata.json",
            "params.md",
            "config.yaml"
        ],
        optional_files=[
            "model.zip",
            "metrics.json",
            "logs/",
            "checkpoints/",
            "visualizations/"
        ],
        file_patterns={
            r"model_.*\.(zip|pth|h5)$": "Fichier de modèle",
            r"logs/.*\.(log|txt|json)$": "Fichiers de logs",
            r"checkpoints/.*\.(pth|pt|h5)$": "Checkpoints",
            r"visualizations/.*\.(png|jpg|gif)$": "Visualisations"
        },
        max_size_mb=500,  # 500MB maximum
        allowed_formats=[".zip", ".tar.gz", ".tgz", ".tar"]
    )
    
    def __init__(self, work_dir: str = "experiments/validation"):
        self.work_dir = work_dir
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Crée les répertoires nécessaires."""
        os.makedirs(self.work_dir, exist_ok=True)
        os.makedirs(os.path.join(self.work_dir, "reports"), exist_ok=True)
        os.makedirs(os.path.join(self.work_dir, "quarantine"), exist_ok=True)
    
    def validate_archive(self, archive_path: str, 
                        structure: Optional[ArchiveStructure] = None,
                        check_integrity: bool = True,
                        check_structure: bool = True,
                        check_content: bool = True) -> ValidationResult:
        """
        Valide une archive selon plusieurs critères.
        
        Args:
            archive_path: Chemin vers l'archive à valider
            structure: Structure attendue (None pour la structure par défaut)
            check_integrity: Vérifier l'intégrité du fichier
            check_structure: Vérifier la structure de l'archive
            check_content: Vérifier le contenu des fichiers
            
        Returns:
            Résultat de la validation
        """
        if not os.path.exists(archive_path):
            return ValidationResult(
                archive_path=archive_path,
                is_valid=False,
                validation_time=datetime.now().isoformat(),
                checks_performed=[],
                errors=["Archive non trouvée"],
                warnings=[],
                statistics={}
            )
        
        start_time = datetime.now()
        checks_performed = []
        errors = []
        warnings = []
        statistics = {}
        
        try:
            # Vérifier l'intégrité du fichier
            if check_integrity:
                checks_performed.append("integrity_check")
                integrity_result = self._check_integrity(archive_path)
                
                if not integrity_result["is_valid"]:
                    errors.extend(integrity_result["errors"])
                else:
                    statistics["integrity_hash"] = integrity_result["hash"]
                
                warnings.extend(integrity_result["warnings"])
            
            # Vérifier la structure de l'archive
            if check_structure and not errors:
                checks_performed.append("structure_check")
                structure_to_use = structure or self.PACMAN_ARCHIVE_STRUCTURE
                structure_result = self._check_structure(archive_path, structure_to_use)
                
                if not structure_result["is_valid"]:
                    errors.extend(structure_result["errors"])
                
                warnings.extend(structure_result["warnings"])
                statistics.update(structure_result["statistics"])
            
            # Vérifier le contenu des fichiers
            if check_content and not errors:
                checks_performed.append("content_check")
                content_result = self._check_content(archive_path)
                
                if not content_result["is_valid"]:
                    errors.extend(content_result["errors"])
                
                warnings.extend(content_result["warnings"])
                statistics.update(content_result["statistics"])
            
            # Vérifier la signature numérique si présente
            signature_result = self._check_digital_signature(archive_path)
            if signature_result["checked"]:
                checks_performed.append("signature_check")
                statistics["signature_valid"] = signature_result["is_valid"]
                
                if not signature_result["is_valid"]:
                    warnings.append("Signature numérique invalide ou absente")
            
            # Calculer le temps de validation
            validation_time = (datetime.now() - start_time).total_seconds()
            statistics["validation_time_seconds"] = validation_time
            
            # Déterminer si l'archive est valide
            is_valid = len(errors) == 0
            
            # Créer le résultat
            result = ValidationResult(
                archive_path=archive_path,
                is_valid=is_valid,
                validation_time=datetime.now().isoformat(),
                checks_performed=checks_performed,
                errors=errors,
                warnings=warnings,
                statistics=statistics,
                integrity_hash=statistics.get("integrity_hash"),
                signature_valid=statistics.get("signature_valid")
            )
            
            # Sauvegarder le rapport
            self._save_validation_report(result)
            
            # Mettre en quarantaine si invalide
            if not is_valid:
                self._quarantine_archive(archive_path, result)
            
            logger.info(f"Validation terminée: {archive_path} - {'VALIDE' if is_valid else 'INVALIDE'}")
            if errors:
                logger.error(f"  Erreurs: {len(errors)}")
            if warnings:
                logger.warning(f"  Avertissements: {len(warnings)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation de l'archive: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return ValidationResult(
                archive_path=archive_path,
                is_valid=False,
                validation_time=datetime.now().isoformat(),
                checks_performed=checks_performed,
                errors=[f"Erreur lors de la validation: {str(e)}"],
                warnings=warnings,
                statistics=statistics
            )
    
    def _check_integrity(self, archive_path: str) -> Dict[str, Any]:
        """Vérifie l'intégrité du fichier d'archive."""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "hash": None
        }
        
        try:
            # Vérifier que le fichier n'est pas corrompu
            file_size = os.path.getsize(archive_path)
            
            if file_size == 0:
                result["is_valid"] = False
                result["errors"].append("Fichier vide")
                return result
            
            # Calculer le hash MD5
            md5_hash = self._compute_file_hash(archive_path, "md5")
            result["hash"] = md5_hash
            
            # Vérifier si un fichier de hash existe
            hash_file = archive_path + ".md5"
            if os.path.exists(hash_file):
                with open(hash_file, 'r') as f:
                    expected_hash = f.read().strip().split()[0]
                
                if expected_hash != md5_hash:
                    result["is_valid"] = False
                    result["errors"].append("Hash MD5 ne correspond pas")
                else:
                    result["warnings"].append("Hash MD5 vérifié avec succès")
            else:
                result["warnings"].append("Aucun fichier de hash trouvé")
            
            # Vérifier que l'archive peut être ouverte
            if not self._can_open_archive(archive_path):
                result["is_valid"] = False
                result["errors"].append("Archive corrompue ou format invalide")
            
        except Exception as e:
            result["is_valid"] = False
            result["errors"].append(f"Erreur lors de la vérification d'intégrité: {e}")
        
        return result
    
    def _compute_file_hash(self, file_path: str, algorithm: str) -> str:
        """Calcule le hash d'un fichier."""
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def _can_open_archive(self, archive_path: str) -> bool:
        """Vérifie si une archive peut être ouverte."""
        try:
            if archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    # Tester la liste des fichiers
                    _ = zipf.namelist()
                    return True
            
            elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
                with tarfile.open(archive_path, 'r:gz') as tarf:
                    _ = tarf.getnames()
                    return True
            
            elif archive_path.endswith('.tar'):
                with tarfile.open(archive_path, 'r') as tarf:
                    _ = tarf.getnames()
                    return True
            
            else:
                return False
                
        except Exception:
            return False
    
    def _check_structure(self, archive_path: str, structure: ArchiveStructure) -> Dict[str, Any]:
        """Vérifie la structure de l'archive."""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        try:
            # Vérifier le format
            file_ext = os.path.splitext(archive_path)[1].lower()
            if file_ext not in structure.allowed_formats:
                result["is_valid"] = False
                result["errors"].append(f"Format non autorisé: {file_ext}")
            
            # Vérifier la taille
            file_size_mb = os.path.getsize(archive_path) / (1024 * 1024)
            result["statistics"]["file_size_mb"] = file_size_mb
            
            if file_size_mb > structure.max_size_mb:
                result["is_valid"] = False
                result["errors"].append(f"Taille excessive: {file_size_mb:.1f}MB > {structure.max_size_mb}MB")
            
            # Extraire et analyser la structure
            with tempfile.TemporaryDirectory() as temp_dir:
                extracted_files = self._extract_archive(archive_path, temp_dir)
                
                if not extracted_files:
                    result["is_valid"] = False
                    result["errors"].append("Impossible d'extraire l'archive")
                    return result
                
                result["statistics"]["file_count"] = len(extracted_files)
                
                # Vérifier les fichiers requis
                missing_required = []
                for required_file in structure.required_files:
                    if not any(f.endswith(required_file) or required_file in f for f in extracted_files):
                        missing_required.append(required_file)
                
                if missing_required:
                    result["is_valid"] = False
                    result["errors"].append(f"Fichiers requis manquants: {missing_required}")
                
                # Vérifier les patterns de fichiers
                for pattern, description in structure.file_patterns.items():
                    import re
                    matching_files = [f for f in extracted_files if re.match(pattern, f)]
                    
                    if matching_files:
                        result["statistics"][f"files_{description.replace(' ', '_').lower()}"] = len(matching_files)
                
                # Vérifier la hiérarchie des répertoires
                dir_structure = self._analyze_directory_structure(extracted_files)
                result["statistics"]["directory_depth"] = dir_structure.get("max_depth", 0)
                result["statistics"]["directory_count"] = dir_structure.get("dir_count", 0)
                
                if dir_structure.get("max_depth", 0) > 5:
                    result["warnings"].append("Structure de répertoires trop profonde")
                
        except Exception as e:
            result["is_valid"] = False
            result["errors"].append(f"Erreur lors de la vérification de structure: {e}")
        
        return result
    
    def _extract_archive(self, archive_path: str, extract_dir: str) -> List[str]:
        """Extrait une archive et retourne la liste des fichiers."""
        try:
            if archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(extract_dir)
                    return zipf.namelist()
            
            elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
                with tarfile.open(archive_path, 'r:gz') as tarf:
                    tarf.extractall(extract_dir)
                    return tarf.getnames()
            
            elif archive_path.endswith('.tar'):
                with tarfile.open(archive_path, 'r') as tarf:
                    tarf.extractall(extract_dir)
                    return tarf.getnames()
            
            else:
                return []
                
        except Exception:
            return []
    
    def _analyze_directory_structure(self, file_list: List[str]) -> Dict[str, Any]:
        """Analyse la structure des répertoires d'une liste de fichiers."""
        dirs = set()
        max_depth = 0
        
        for file_path in file_list:
            # Compter les séparateurs de répertoire
            depth = file_path.count('/') + file_path.count('\\')
            max_depth = max(max_depth, depth)
            
            # Extraire les répertoires
            dir_path = os.path.dirname(file_path)
            while dir_path:
                dirs.add(dir_path)
                dir_path = os.path.dirname(dir_path)
        
        return {
            "dir_count": len(dirs),
            "max_depth": max_depth,
            "all_dirs": list(dirs)
        }
    
    def _check_content(self, archive_path: str) -> Dict[str, Any]:
        """Vérifie le contenu des fichiers de l'archive."""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                extracted_files = self._extract_archive(archive_path, temp_dir)
                
                if not extracted_files:
                    result["is_valid"] = False
                    result["errors"].append("Impossible d'extraire l'archive pour vérification du contenu")
                    return result
                
                # Vérifier les fichiers de métadonnées
                metadata_errors = self._check_metadata_files(temp_dir, extracted_files)
                if metadata_errors:
                    result["is_valid"] = False
                    result["errors"].extend(metadata_errors)
                
                # Vérifier les fichiers de modèle
                model_warnings = self._check_model_files(temp_dir, extracted_files)
                result["warnings"].extend(model_warnings)
                
                # Vérifier les fichiers de logs
                log_stats = self._check_log_files(temp_dir, extracted_files)
                result["statistics"].update(log_stats)
                
                # Détecter les anomalies
                anomalies = self._detect_anomalies(temp_dir, extracted_files)
                if anomalies:
                    result["warnings"].extend(anomalies)
                
        except Exception as e:
            result["is_valid"] = False
            result["errors"].append(f"Erreur lors de la vérification du contenu: {e}")
        
        return result
    
    def _check_metadata_files(self, extract_dir: str, file_list: List[str]) -> List[str]:
        """Vérifie les fichiers de métadonnées."""
        errors = []
        
        # Chercher metadata.json
        metadata_files = [f for f in file_list if f.endswith('metadata.json')]
        
        for metadata_file in metadata_files:
            try:
                metadata_path = os.path.join(extract_dir, metadata_file)
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Vérifier les champs requis
                required_fields = ['session_id', 'timestamp', 'model_type']
                for field in required_fields:
                    if field not in metadata:
                        errors.append(f"Champ '{field}' manquant dans {metadata_file}")
                
                # Vérifier les types de données
                if 'total_episodes'