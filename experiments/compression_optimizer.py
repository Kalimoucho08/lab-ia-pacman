#!/usr/bin/env python3
"""
Optimisation de compression pour le système d'archivage intelligent.

Fonctionnalités :
- Compression intelligente (gzip pour logs, stockage brut pour modèles)
- Compression différentielle entre sessions
- Optimisation d'espace avec suppression des doublons
- Export multi-format (ZIP, TAR, dossier décompressé)
- Détection de redondance et déduplication
"""

import os
import json
import gzip
import zipfile
import tarfile
import shutil
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CompressionStats:
    """Statistiques de compression."""
    original_size: int
    compressed_size: int
    compression_ratio: float
    time_taken: float
    algorithm: str
    files_processed: int
    duplicate_files_found: int
    space_saved: int

@dataclass
class FileFingerprint:
    """Empreinte digitale d'un fichier pour la déduplication."""
    file_path: str
    file_size: int
    md5_hash: str
    sha256_hash: str
    last_modified: str
    compression_suitable: bool

class CompressionOptimizer:
    """
    Optimiseur de compression pour le système d'archivage.
    
    Implémente des techniques avancées de compression et de déduplication
    pour réduire l'espace de stockage des archives.
    """
    
    def __init__(self, work_dir: str = "experiments/compression"):
        self.work_dir = work_dir
        self.fingerprint_db = os.path.join(work_dir, "fingerprints.json")
        self._ensure_directories()
        self._load_fingerprint_db()
    
    def _ensure_directories(self) -> None:
        """Crée les répertoires nécessaires."""
        os.makedirs(self.work_dir, exist_ok=True)
        os.makedirs(os.path.join(self.work_dir, "cache"), exist_ok=True)
        os.makedirs(os.path.join(self.work_dir, "differential"), exist_ok=True)
        os.makedirs(os.path.join(self.work_dir, "deduplicated"), exist_ok=True)
    
    def _load_fingerprint_db(self) -> None:
        """Charge ou crée la base de données d'empreintes digitales."""
        if os.path.exists(self.fingerprint_db):
            try:
                with open(self.fingerprint_db, 'r') as f:
                    self.fingerprints = json.load(f)
                logger.info(f"Base d'empreintes chargée: {len(self.fingerprints)} fichiers")
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de la base d'empreintes: {e}")
                self.fingerprints = {}
        else:
            self.fingerprints = {}
    
    def _save_fingerprint_db(self) -> None:
        """Sauvegarde la base de données d'empreintes digitales."""
        try:
            with open(self.fingerprint_db, 'w') as f:
                json.dump(self.fingerprints, f, indent=2)
            logger.debug("Base d'empreintes sauvegardée")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la base d'empreintes: {e}")
    
    def optimize_archive(self, archive_path: str, optimization_level: str = "balanced") -> Optional[CompressionStats]:
        """
        Optimise une archive existante.
        
        Args:
            archive_path: Chemin vers l'archive à optimiser
            optimization_level: Niveau d'optimisation ('minimal', 'balanced', 'aggressive')
            
        Returns:
            Statistiques de compression ou None en cas d'erreur
        """
        if not os.path.exists(archive_path):
            logger.error(f"Archive non trouvée: {archive_path}")
            return None
        
        start_time = datetime.now()
        
        try:
            # Créer un répertoire temporaire pour l'extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extraire l'archive
                extracted_files = self._extract_archive(archive_path, temp_dir)
                if not extracted_files:
                    return None
                
                # Analyser les fichiers
                file_fingerprints = self._analyze_files(temp_dir)
                
                # Appliquer l'optimisation selon le niveau
                if optimization_level == "minimal":
                    optimized_dir = self._apply_minimal_optimization(temp_dir, file_fingerprints)
                elif optimization_level == "aggressive":
                    optimized_dir = self._apply_aggressive_optimization(temp_dir, file_fingerprints)
                else:  # balanced
                    optimized_dir = self._apply_balanced_optimization(temp_dir, file_fingerprints)
                
                # Créer une nouvelle archive optimisée
                original_size = os.path.getsize(archive_path)
                optimized_archive = self._create_optimized_archive(optimized_dir, archive_path)
                
                if not optimized_archive:
                    return None
                
                # Calculer les statistiques
                compressed_size = os.path.getsize(optimized_archive)
                time_taken = (datetime.now() - start_time).total_seconds()
                
                stats = CompressionStats(
                    original_size=original_size,
                    compressed_size=compressed_size,
                    compression_ratio=compressed_size / original_size if original_size > 0 else 0,
                    time_taken=time_taken,
                    algorithm="optimized_zip",
                    files_processed=len(extracted_files),
                    duplicate_files_found=self._count_duplicates(file_fingerprints),
                    space_saved=original_size - compressed_size
                )
                
                logger.info(f"Archive optimisée: {archive_path}")
                logger.info(f"  Taille originale: {original_size / 1024 / 1024:.2f} MB")
                logger.info(f"  Taille optimisée: {compressed_size / 1024 / 1024:.2f} MB")
                logger.info(f"  Ratio: {stats.compression_ratio:.2%}")
                logger.info(f"  Espace économisé: {stats.space_saved / 1024 / 1024:.2f} MB")
                
                return stats
                
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation de l'archive: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _extract_archive(self, archive_path: str, extract_dir: str) -> List[str]:
        """Extrait une archive dans un répertoire temporaire."""
        extracted_files = []
        
        try:
            if archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(extract_dir)
                    extracted_files = zipf.namelist()
            
            elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
                with tarfile.open(archive_path, 'r:gz') as tarf:
                    tarf.extractall(extract_dir)
                    extracted_files = tarf.getnames()
            
            elif archive_path.endswith('.tar'):
                with tarfile.open(archive_path, 'r') as tarf:
                    tarf.extractall(extract_dir)
                    extracted_files = tarf.getnames()
            
            else:
                logger.error(f"Format d'archive non supporté: {archive_path}")
                return []
            
            logger.info(f"Archive extraite: {len(extracted_files)} fichiers")
            return extracted_files
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de l'archive: {e}")
            return []
    
    def _analyze_files(self, directory: str) -> List[FileFingerprint]:
        """Analyse les fichiers et génère leurs empreintes digitales."""
        fingerprints = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, directory)
                
                try:
                    # Obtenir les informations de base
                    file_size = os.path.getsize(file_path)
                    last_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    
                    # Calculer les hashs
                    md5_hash = self._compute_file_hash(file_path, 'md5')
                    sha256_hash = self._compute_file_hash(file_path, 'sha256')
                    
                    # Déterminer si le fichier est adapté à la compression
                    compression_suitable = self._is_compression_suitable(file_path, file_size)
                    
                    fingerprint = FileFingerprint(
                        file_path=rel_path,
                        file_size=file_size,
                        md5_hash=md5_hash,
                        sha256_hash=sha256_hash,
                        last_modified=last_modified,
                        compression_suitable=compression_suitable
                    )
                    
                    fingerprints.append(fingerprint)
                    
                    # Mettre à jour la base de données d'empreintes
                    self._update_fingerprint_db(fingerprint)
                    
                except Exception as e:
                    logger.warning(f"Erreur lors de l'analyse de {file_path}: {e}")
        
        logger.info(f"Fichiers analysés: {len(fingerprints)} empreintes générées")
        return fingerprints
    
    def _compute_file_hash(self, file_path: str, algorithm: str) -> str:
        """Calcule le hash d'un fichier."""
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def _is_compression_suitable(self, file_path: str, file_size: int) -> bool:
        """Détermine si un fichier est adapté à la compression."""
        # Les fichiers déjà compressés ne devraient pas être recompressés
        compressed_extensions = ['.zip', '.gz', '.bz2', '.xz', '.7z', '.rar', '.jpg', '.png', '.mp3', '.mp4']
        
        if any(file_path.lower().endswith(ext) for ext in compressed_extensions):
            return False
        
        # Les petits fichiers ne bénéficient pas beaucoup de la compression
        if file_size < 1024:  # < 1KB
            return False
        
        # Analyser le contenu pour estimer la compressibilité
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(4096)
                
                # Vérifier l'entropie (approximation simple)
                unique_bytes = len(set(sample))
                entropy_ratio = unique_bytes / len(sample) if sample else 0
                
                # Faible entropie = bonne compressibilité
                return entropy_ratio < 0.8
                
        except Exception:
            return True  # Par défaut, essayer la compression
    
    def _update_fingerprint_db(self, fingerprint: FileFingerprint) -> None:
        """Met à jour la base de données d'empreintes digitales."""
        # Utiliser le hash SHA256 comme clé
        key = fingerprint.sha256_hash
        
        if key not in self.fingerprints:
            self.fingerprints[key] = {
                'file_paths': [fingerprint.file_path],
                'file_size': fingerprint.file_size,
                'md5_hash': fingerprint.md5_hash,
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'compression_suitable': fingerprint.compression_suitable
            }
        else:
            # Mettre à jour les informations existantes
            if fingerprint.file_path not in self.fingerprints[key]['file_paths']:
                self.fingerprints[key]['file_paths'].append(fingerprint.file_path)
            self.fingerprints[key]['last_seen'] = datetime.now().isoformat()
    
    def _count_duplicates(self, fingerprints: List[FileFingerprint]) -> int:
        """Compte les fichiers en double basés sur leurs empreintes."""
        hash_count = {}
        
        for fp in fingerprints:
            hash_count[fp.sha256_hash] = hash_count.get(fp.sha256_hash, 0) + 1
        
        # Compter les hashs qui apparaissent plus d'une fois
        duplicates = sum(1 for count in hash_count.values() if count > 1)
        
        return duplicates
    
    def _apply_minimal_optimization(self, directory: str, fingerprints: List[FileFingerprint]) -> str:
        """Applique une optimisation minimale (compression sélective)."""
        optimized_dir = os.path.join(self.work_dir, "optimized_minimal")
        shutil.rmtree(optimized_dir, ignore_errors=True)
        shutil.copytree(directory, optimized_dir)
        
        # Compresser uniquement les fichiers adaptés
        for fp in fingerprints:
            if fp.compression_suitable:
                file_path = os.path.join(optimized_dir, fp.file_path)
                self._compress_file_if_beneficial(file_path)
        
        return optimized_dir
    
    def _apply_balanced_optimization(self, directory: str, fingerprints: List[FileFingerprint]) -> str:
        """Applique une optimisation équilibrée (compression + déduplication)."""
        optimized_dir = os.path.join(self.work_dir, "optimized_balanced")
        shutil.rmtree(optimized_dir, ignore_errors=True)
        
        # Créer une structure optimisée avec déduplication
        os.makedirs(optimized_dir)
        
        # Grouper les fichiers par hash
        files_by_hash = {}
        for fp in fingerprints:
            files_by_hash.setdefault(fp.sha256_hash, []).append(fp)
        
        # Copier un exemplaire de chaque fichier unique
        file_mapping = {}
        for hash_value, fps in files_by_hash.items():
            # Prendre le premier fichier comme référence
            ref_fp = fps[0]
            src_path = os.path.join(directory, ref_fp.file_path)
            
            # Créer un nom de fichier basé sur le hash
            file_ext = os.path.splitext(ref_fp.file_path)[1]
            new_filename = f"{hash_value[:16]}{file_ext}"
            dst_path = os.path.join(optimized_dir, "content", new_filename)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            
            # Copier le fichier
            shutil.copy2(src_path, dst_path)
            
            # Compresser si bénéfique
            if ref_fp.compression_suitable:
                self._compress_file_if_beneficial(dst_path)
            
            # Enregistrer le mapping
            for fp in fps:
                file_mapping[fp.file_path] = new_filename
        
        # Créer un fichier de mapping
        mapping_path = os.path.join(optimized_dir, "file_mapping.json")
        with open(mapping_path, 'w') as f:
            json.dump(file_mapping, f, indent=2)
        
        return optimized_dir
    
    def _apply_aggressive_optimization(self, directory: str, fingerprints: List[FileFingerprint]) -> str:
        """Applique une optimisation agressive (compression maximale + différentielle)."""
        optimized_dir = os.path.join(self.work_dir, "optimized_aggressive")
        shutil.rmtree(optimized_dir, ignore_errors=True)
        shutil.copytree(directory, optimized_dir)
        
        # Compresser tous les fichiers (sauf ceux déjà compressés)
        for fp in fingerprints:
            file_path = os.path.join(optimized_dir, fp.file_path)
            
            # Toujours compresser les fichiers textuels
            if self._is_text_file(file_path):
                self._compress_with_gzip(file_path)
            elif fp.compression_suitable:
                self._compress_file_if_beneficial(file_path)
        
        # Appliquer la compression différentielle si possible
        self._apply_differential_compression(optimized_dir, fingerprints)
        
        return optimized_dir
    
    def _is_text_file(self, file_path: str) -> bool:
        """Détermine si un fichier est textuel."""
        text_extensions = ['.txt', '.log', '.csv', '.json', '.yaml', '.yml', '.md', '.py', '.js', '.ts']
        
        if any(file_path.lower().endswith(ext) for ext in text_extensions):
            return True
        
        # Vérifier le contenu
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(1024)
                # Vérifier la présence de caractères non-ASCII
                return all(byte < 128 or byte == 10 or byte == 13 for byte in sample)
        except Exception:
            return False
    
    def _compress_with_gzip(self, file_path: str) -> bool:
        """Compresse un fichier avec gzip."""
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(file_path + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remplacer le fichier original par la version compressée
            os.remove(file_path)
            os.rename(file_path + '.gz', file_path)
            
            return True
            
        except Exception as e:
            logger.warning(f"Erreur lors de la compression gzip de {file_path}: {e}")
            return False
    
    def _compress_file_if_beneficial(self,