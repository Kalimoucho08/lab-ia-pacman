#!/usr/bin/env python3
"""
Service d'archivage pour le backend FastAPI.

Intègre le système d'archivage intelligent avec l'API REST.
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from backend.config import settings
from experiments.archive_service import IntelligentArchiveService, ArchiveConfig
from experiments.metadata_generator import IntelligentMetadataGenerator
from experiments.session_resumer import SessionResumer
from experiments.version_manager import VersionManager
from experiments.compression_optimizer import CompressionOptimizer
from experiments.archive_validator import ArchiveValidator

class ArchiveService:
    """
    Service d'archivage pour le backend FastAPI.
    
    Fournit une interface unifiée pour toutes les opérations d'archivage.
    """
    
    def __init__(self):
        self.base_dir = settings.ARCHIVE_DIR if hasattr(settings, 'ARCHIVE_DIR') else "experiments/archives"
        self.logs_dir = settings.LOGS_DIR if hasattr(settings, 'LOGS_DIR') else "logs"
        
        # Créer la configuration pour le service d'archivage
        archive_config = ArchiveConfig(
            archive_dir=self.base_dir,
            max_archives=100,
            auto_save_interval=1000,
            save_on_improvement=True,
            improvement_threshold=0.05,
            compression_level=9,
            include_model=True,
            include_logs=True,
            include_metrics=True,
            include_config=True,
            backup_to_cloud=False,
            cloud_endpoint=None
        )
        
        # Initialiser les composants
        self.archive_service = IntelligentArchiveService(config=archive_config)
        self.metadata_generator = IntelligentMetadataGenerator()
        self.session_resumer = SessionResumer()
        self.version_manager = VersionManager()
        self.compression_optimizer = CompressionOptimizer()
        self.archive_validator = ArchiveValidator()
        
        # Créer les répertoires nécessaires
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def create_archive(self, 
                      experiment_id: str,
                      model_path: Optional[str] = None,
                      metrics: Optional[Dict[str, Any]] = None,
                      config: Optional[Dict[str, Any]] = None,
                      tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Crée une archive pour une expérience.
        
        Args:
            experiment_id: ID de l'expérience
            model_path: Chemin vers le fichier de modèle (optionnel)
            metrics: Métriques de l'expérience (optionnel)
            config: Configuration de l'expérience (optionnel)
            tags: Tags pour l'archive (optionnel)
            
        Returns:
            Informations sur l'archive créée
        """
        try:
            # Préparer les métadonnées
            metadata = {
                "experiment_id": experiment_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics or {},
                "config": config or {},
                "tags": tags or []
            }
            
            # Créer l'archive
            archive_info = self.archive_service.create_archive(
                model_path=model_path,
                metadata=metadata,
                tags=tags
            )
            
            # Enregistrer la version
            version_info = self.version_manager.register_new_version(
                archive_path=archive_info["archive_path"],
                metadata=metadata,
                tags=tags
            )
            
            # Optimiser la compression
            optimized_info = self.compression_optimizer.optimize_archive(
                archive_info["archive_path"]
            )
            
            # Valider l'archive
            validation_result = self.archive_validator.validate_archive(
                archive_info["archive_path"]
            )
            
            return {
                "success": True,
                "archive_path": archive_info["archive_path"],
                "archive_name": archive_info["archive_name"],
                "version_id": version_info.get("version_id"),
                "compression_ratio": optimized_info.get("compression_ratio"),
                "validation_result": validation_result.is_valid,
                "message": f"Archive créée avec succès: {archive_info['archive_name']}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la création de l'archive: {e}"
            }
    
    def list_archives(self, 
                     filter_tags: Optional[List[str]] = None,
                     min_version: Optional[int] = None,
                     max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Liste les archives disponibles.
        
        Args:
            filter_tags: Tags pour filtrer les archives
            min_version: Numéro de version minimum
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste des archives
        """
        try:
            # Utiliser le gestionnaire de versions pour la recherche
            versions = self.version_manager.search_versions(
                tags=filter_tags,
                min_version=min_version,
                limit=max_results
            )
            
            archives = []
            for version in versions:
                archive_path = version["archive_path"]
                
                # Obtenir des informations supplémentaires
                archive_info = self.archive_service.get_archive_info(archive_path)
                
                archives.append({
                    "archive_path": archive_path,
                    "archive_name": os.path.basename(archive_path),
                    "version_id": version.get("version_id"),
                    "tags": version.get("tags", []),
                    "created_at": version.get("created_at"),
                    "metadata": version.get("metadata", {}),
                    "size_mb": archive_info.get("size_mb", 0),
                    "file_count": archive_info.get("file_count", 0)
                })
            
            return archives
            
        except Exception as e:
            return []
    
    def get_archive_info(self, archive_path: str) -> Dict[str, Any]:
        """
        Récupère des informations détaillées sur une archive.
        
        Args:
            archive_path: Chemin vers l'archive
            
        Returns:
            Informations sur l'archive
        """
        try:
            # Obtenir les informations de base
            archive_info = self.archive_service.get_archive_info(archive_path)
            
            # Valider l'archive
            validation_result = self.archive_validator.validate_archive(archive_path)
            
            # Obtenir les informations de version
            version_info = self.version_manager.get_version_info(archive_path)
            
            # Extraire les métadonnées
            metadata = self.archive_service.extract_metadata(archive_path)
            
            return {
                "archive_path": archive_path,
                "archive_name": os.path.basename(archive_path),
                "size_mb": archive_info.get("size_mb", 0),
                "file_count": archive_info.get("file_count", 0),
                "created_at": archive_info.get("created_at"),
                "validation_result": {
                    "is_valid": validation_result.is_valid,
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings
                },
                "version_info": version_info,
                "metadata": metadata,
                "structure": archive_info.get("structure", {})
            }
            
        except Exception as e:
            return {
                "archive_path": archive_path,
                "error": str(e),
                "message": f"Erreur lors de la récupération des informations: {e}"
            }
    
    def restore_session(self, archive_path: str, target_dir: str) -> Dict[str, Any]:
        """
        Restaure une session à partir d'une archive.
        
        Args:
            archive_path: Chemin vers l'archive
            target_dir: Répertoire cible pour la restauration
            
        Returns:
            Informations sur la restauration
        """
        try:
            # Utiliser le système de reprise de sessions
            resume_info = self.session_resumer.load_archive(
                archive_path=archive_path,
                target_dir=target_dir
            )
            
            return {
                "success": True,
                "target_dir": target_dir,
                "extracted_files": resume_info.get("extracted_files", []),
                "metadata": resume_info.get("metadata", {}),
                "message": f"Session restaurée avec succès dans {target_dir}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la restauration de la session: {e}"
            }
    
    def compare_sessions(self, archive_path1: str, archive_path2: str) -> Dict[str, Any]:
        """
        Compare deux sessions.
        
        Args:
            archive_path1: Chemin vers la première archive
            archive_path2: Chemin vers la deuxième archive
            
        Returns:
            Résultat de la comparaison
        """
        try:
            comparison = self.session_resumer.compare_sessions(
                archive_path1, archive_path2
            )
            
            return {
                "success": True,
                "comparison": comparison,
                "message": "Sessions comparées avec succès"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la comparaison des sessions: {e}"
            }
    
    def auto_save(self, 
                 experiment_id: str,
                 model_path: Optional[str] = None,
                 metrics: Optional[Dict[str, Any]] = None,
                 config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sauvegarde automatique basée sur les métriques.
        
        Args:
            experiment_id: ID de l'expérience
            model_path: Chemin vers le fichier de modèle
            metrics: Métriques de l'expérience
            config: Configuration de l'expérience
            
        Returns:
            Informations sur la sauvegarde
        """
        try:
            # Déterminer si une sauvegarde est nécessaire
            should_save = self._should_auto_save(metrics)
            
            if not should_save:
                return {
                    "success": True,
                    "saved": False,
                    "message": "Sauvegarde automatique non déclenchée"
                }
            
            # Créer l'archive
            return self.create_archive(
                experiment_id=experiment_id,
                model_path=model_path,
                metrics=metrics,
                config=config,
                tags=["auto_save"]
            )
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la sauvegarde automatique: {e}"
            }
    
    def _should_auto_save(self, metrics: Optional[Dict[str, Any]]) -> bool:
        """
        Détermine si une sauvegarde automatique est nécessaire.
        
        Args:
            metrics: Métriques de l'expérience
            
        Returns:
            True si une sauvegarde est nécessaire
        """
        if not metrics:
            return False
        
        # Logique de décision basée sur les métriques
        # Exemple: sauvegarder si le win_rate a augmenté de plus de 5%
        # ou si le nombre d'épisodes est un multiple de 1000
        
        win_rate = metrics.get("win_rate", 0)
        total_episodes = metrics.get("total_episodes", 0)
        
        # Sauvegarder tous les 1000 épisodes
        if total_episodes % 1000 == 0:
            return True
        
        # Sauvegarder si le win_rate a augmenté significativement
        # (nécessite de connaître le win_rate précédent)
        
        return False
    
    def cleanup_old_archives(self, max_age_days: int = 30, keep_best: int = 5) -> Dict[str, Any]:
        """
        Nettoie les anciennes archives.
        
        Args:
            max_age_days: Âge maximum en jours
            keep_best: Nombre de meilleures archives à conserver
            
        Returns:
            Informations sur le nettoyage
        """
        try:
            # Obtenir les archives
            archives = self.list_archives(max_results=1000)
            
            # Filtrer par âge
            old_archives = []
            for archive in archives:
                created_at = archive.get("created_at")
                if not created_at:
                    continue
                
                # Convertir la date
                try:
                    if isinstance(created_at, str):
                        archive_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        continue
                    
                    age_days = (datetime.now() - archive_date).days
                    
                    if age_days > max_age_days:
                        old_archives.append(archive)
                        
                except Exception:
                    continue
            
            # Conserver les meilleures archives
            best_archives = self.version_manager.get_best_versions(limit=keep_best)
            best_paths = [arch["archive_path"] for arch in best_archives]
            
            # Supprimer les anciennes archives (sauf les meilleures)
            deleted = []
            for archive in old_archives:
                archive_path = archive["archive_path"]
                
                # Ne pas supprimer les meilleures archives
                if archive_path in best_paths:
                    continue
                
                try:
                    os.remove(archive_path)
                    deleted.append(archive_path)
                except Exception as e:
                    pass
            
            return {
                "success": True,
                "deleted_count": len(deleted),
                "deleted_archives": deleted,
                "kept_best": best_paths,
                "message": f"{len(deleted)} anciennes archives supprimées"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors du nettoyage des archives: {e}"
            }

# Instance globale du service
archive_service = ArchiveService()