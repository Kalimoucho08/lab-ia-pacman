#!/usr/bin/env python3
"""
Endpoints API REST pour la gestion des archives.

Fournit les opérations CRUD sur les archives,
ainsi que la sauvegarde automatique et la reprise de sessions.
"""

import os
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query, Body, File, UploadFile
from pydantic import BaseModel, Field

from backend.services.archive_service import archive_service
from backend.services.websocket_service import websocket_manager

router = APIRouter()

# Modèles Pydantic
class ArchiveCreate(BaseModel):
    """Modèle pour la création d'archive."""
    experiment_id: str = Field(..., description="ID de l'expérience")
    model_path: Optional[str] = Field(None, description="Chemin vers le fichier de modèle")
    metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Métriques de l'expérience")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Configuration de l'expérience")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags pour l'archive")

class ArchiveRestore(BaseModel):
    """Modèle pour la restauration d'archive."""
    archive_path: str = Field(..., description="Chemin vers l'archive")
    target_dir: str = Field(..., description="Répertoire cible pour la restauration")

class ArchiveCompare(BaseModel):
    """Modèle pour la comparaison d'archives."""
    archive_path1: str = Field(..., description="Chemin vers la première archive")
    archive_path2: str = Field(..., description="Chemin vers la deuxième archive")

class CleanupConfig(BaseModel):
    """Modèle pour la configuration du nettoyage."""
    max_age_days: int = Field(30, ge=1, le=365, description="Âge maximum en jours")
    keep_best: int = Field(5, ge=1, le=100, description="Nombre de meilleures archives à conserver")

@router.get("/", response_model=List[Dict[str, Any]])
async def list_archives(
    filter_tags: Optional[List[str]] = Query(None, description="Tags pour filtrer les archives"),
    min_version: Optional[int] = Query(None, ge=1, description="Numéro de version minimum"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'archives à retourner")
):
    """
    Liste toutes les archives disponibles.
    
    Args:
        filter_tags: Tags pour filtrer les archives
        min_version: Numéro de version minimum
        limit: Nombre maximum de résultats
        
    Returns:
        Liste des archives avec leurs métadonnées
    """
    try:
        archives = archive_service.list_archives(
            filter_tags=filter_tags,
            min_version=min_version,
            max_results=limit
        )
        
        return archives
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la liste des archives: {e}"
        )

@router.post("/", response_model=Dict[str, Any])
async def create_archive(archive_data: ArchiveCreate):
    """
    Crée une nouvelle archive.
    
    Args:
        archive_data: Données pour la création de l'archive
        
    Returns:
        Informations sur l'archive créée
    """
    try:
        result = archive_service.create_archive(
            experiment_id=archive_data.experiment_id,
            model_path=archive_data.model_path,
            metrics=archive_data.metrics,
            config=archive_data.config,
            tags=archive_data.tags
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Erreur inconnue lors de la création de l'archive")
            )
        
        # Notifier via WebSocket
        await websocket_manager.broadcast_experiment_update({
            "type": "archive_created",
            "experiment_id": archive_data.experiment_id,
            "archive_name": result.get("archive_name"),
            "archive_path": result.get("archive_path")
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de l'archive: {e}"
        )

@router.get("/{archive_path:path}", response_model=Dict[str, Any])
async def get_archive_info(archive_path: str):
    """
    Récupère des informations détaillées sur une archive.
    
    Args:
        archive_path: Chemin vers l'archive
        
    Returns:
        Informations détaillées sur l'archive
    """
    try:
        # Vérifier que l'archive existe
        if not os.path.exists(archive_path):
            # Essayer de trouver l'archive dans le répertoire par défaut
            base_dir = archive_service.base_dir
            full_path = os.path.join(base_dir, archive_path)
            
            if not os.path.exists(full_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Archive {archive_path} non trouvée"
                )
            
            archive_path = full_path
        
        info = archive_service.get_archive_info(archive_path)
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des informations de l'archive: {e}"
        )

@router.post("/restore", response_model=Dict[str, Any])
async def restore_archive(restore_data: ArchiveRestore):
    """
    Restaure une session à partir d'une archive.
    
    Args:
        restore_data: Données pour la restauration
        
    Returns:
        Informations sur la restauration
    """
    try:
        # Vérifier que l'archive existe
        if not os.path.exists(restore_data.archive_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archive {restore_data.archive_path} non trouvée"
            )
        
        # Vérifier que le répertoire cible n'existe pas déjà
        if os.path.exists(restore_data.target_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le répertoire cible {restore_data.target_dir} existe déjà"
            )
        
        result = archive_service.restore_session(
            archive_path=restore_data.archive_path,
            target_dir=restore_data.target_dir
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Erreur inconnue lors de la restauration")
            )
        
        # Notifier via WebSocket
        await websocket_manager.broadcast_experiment_update({
            "type": "archive_restored",
            "archive_path": restore_data.archive_path,
            "target_dir": restore_data.target_dir
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la restauration de l'archive: {e}"
        )

@router.post("/compare", response_model=Dict[str, Any])
async def compare_archives(compare_data: ArchiveCompare):
    """
    Compare deux sessions.
    
    Args:
        compare_data: Données pour la comparaison
        
    Returns:
        Résultat de la comparaison
    """
    try:
        # Vérifier que les archives existent
        for archive_path in [compare_data.archive_path1, compare_data.archive_path2]:
            if not os.path.exists(archive_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Archive {archive_path} non trouvée"
                )
        
        result = archive_service.compare_sessions(
            archive_path1=compare_data.archive_path1,
            archive_path2=compare_data.archive_path2
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Erreur inconnue lors de la comparaison")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la comparaison des archives: {e}"
        )

@router.post("/auto-save", response_model=Dict[str, Any])
async def auto_save_archive(
    experiment_id: str = Query(..., description="ID de l'expérience"),
    model_path: Optional[str] = Query(None, description="Chemin vers le fichier de modèle"),
    metrics: Optional[Dict[str, Any]] = Body(None, description="Métriques de l'expérience"),
    config: Optional[Dict[str, Any]] = Body(None, description="Configuration de l'expérience")
):
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
        result = archive_service.auto_save(
            experiment_id=experiment_id,
            model_path=model_path,
            metrics=metrics,
            config=config
        )
        
        if result.get("saved", False):
            # Notifier via WebSocket
            await websocket_manager.broadcast_experiment_update({
                "type": "archive_auto_saved",
                "experiment_id": experiment_id,
                "archive_name": result.get("archive_name")
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la sauvegarde automatique: {e}"
        )

@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_archives(config: CleanupConfig):
    """
    Nettoie les anciennes archives.
    
    Args:
        config: Configuration du nettoyage
        
    Returns:
        Informations sur le nettoyage
    """
    try:
        result = archive_service.cleanup_old_archives(
            max_age_days=config.max_age_days,
            keep_best=config.keep_best
        )
        
        if result.get("success", False):
            # Notifier via WebSocket
            await websocket_manager.broadcast_experiment_update({
                "type": "archives_cleaned",
                "deleted_count": result.get("deleted_count", 0),
                "kept_best": result.get("kept_best", [])
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du nettoyage des archives: {e}"
        )

@router.post("/upload", response_model=Dict[str, Any])
async def upload_archive(
    file: UploadFile = File(..., description="Fichier d'archive à uploader"),
    experiment_id: str = Query(..., description="ID de l'expérience"),
    tags: Optional[List[str]] = Query(None, description="Tags pour l'archive")
):
    """
    Upload une archive existante.
    
    Args:
        file: Fichier d'archive
        experiment_id: ID de l'expérience
        tags: Tags pour l'archive
        
    Returns:
        Informations sur l'archive uploadée
    """
    try:
        # Vérifier l'extension du fichier
        if not file.filename.endswith('.zip'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seuls les fichiers ZIP sont acceptés"
            )
        
        # Créer le répertoire de destination
        base_dir = archive_service.base_dir
        os.makedirs(base_dir, exist_ok=True)
        
        # Générer un nom de fichier unique
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"uploaded_{experiment_id}_{timestamp}_{unique_id}.zip"
        file_path = os.path.join(base_dir, filename)
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Valider l'archive
        validation_result = archive_service.archive_validator.validate_archive(file_path)
        
        if not validation_result.is_valid:
            # Supprimer le fichier invalide
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archive invalide: {validation_result.errors}"
            )
        
        # Extraire les métadonnées
        metadata = archive_service.archive_service.extract_metadata(file_path)
        
        # Enregistrer la version
        version_info = archive_service.version_manager.register_new_version(
            archive_path=file_path,
            metadata=metadata,
            tags=tags or ["uploaded"]
        )
        
        # Notifier via WebSocket
        await websocket_manager.broadcast_experiment_update({
            "type": "archive_uploaded",
            "experiment_id": experiment_id,
            "archive_name": filename,
            "archive_path": file_path
        })
        
        return {
            "success": True,
            "archive_path": file_path,
            "archive_name": filename,
            "version_id": version_info.get("version_id"),
            "validation_result": validation_result.is_valid,
            "message": f"Archive uploadée avec succès: {filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'upload de l'archive: {e}"
        )

@router.get("/best", response_model=List[Dict[str, Any]])
async def get_best_archives(
    limit: int = Query(10, ge=1, le=100, description="Nombre maximum d'archives à retourner")
):
    """
    Récupère les meilleures archives.
    
    Args:
        limit: Nombre maximum de résultats
        
    Returns:
        Liste des meilleures archives
    """
    try:
        # Utiliser le gestionnaire de versions
        best_versions = archive_service.version_manager.get_best_versions(limit=limit)
        
        # Ajouter des informations supplémentaires
        archives = []
        for version in best_versions:
            archive_path = version["archive_path"]
            
            # Obtenir des informations supplémentaires
            archive_info = archive_service.archive_service.get_archive_info(archive_path)
            
            archives.append({
                "archive_path": archive_path,
                "archive_name": os.path.basename(archive_path),
                "version_id": version.get("version_id"),
                "tags": version.get("tags", []),
                "created_at": version.get("created_at"),
                "metadata": version.get("metadata", {}),
                "size_mb": archive_info.get("size_mb", 0),
                "score": version.get("score", 0)
            })
        
        return archives
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des meilleures archives: {e}"
        )

# Import datetime pour la route upload
from datetime import datetime