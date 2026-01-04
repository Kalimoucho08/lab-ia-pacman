"""
Endpoints API pour l'export ONNX.

Fournit des endpoints REST pour:
- Convertir des modèles Stable-Baselines3 en ONNX
- Exporter pour différentes plateformes
- Optimiser et valider les modèles ONNX
- Vérifier la compatibilité
- Gérer les exports
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

from backend.services.onnx_export_service import onnx_export_service

router = APIRouter()


@router.get("/")
async def get_onnx_info():
    """
    Informations sur le système d'export ONNX.
    
    Returns:
        Informations sur les fonctionnalités disponibles
    """
    return {
        "system": "Export ONNX universel pour le laboratoire scientifique IA Pac-Man",
        "version": "1.0.0",
        "features": [
            "Conversion de modèles Stable-Baselines3 vers ONNX",
            "Export multi-plateforme (Pygame, Web, Unity, Generic)",
            "Optimisations (quantisation, fusion, compression)",
            "Validation complète des modèles",
            "Vérification de compatibilité",
            "Gestion des exports"
        ],
        "supported_algorithms": ["DQN", "PPO", "A2C", "SAC", "TD3"],
        "supported_platforms": ["pygame", "web", "unity", "generic"],
        "base_export_dir": str(onnx_export_service.base_export_dir)
    }


@router.post("/convert")
async def convert_model(
    background_tasks: BackgroundTasks,
    model_file: UploadFile = File(...),
    algorithm: str = Form("auto"),
    include_metadata: bool = Form(True),
    output_name: Optional[str] = Form(None)
):
    """
    Convertit un modèle Stable-Baselines3 en ONNX.
    
    Args:
        model_file: Fichier .zip du modèle SB3
        algorithm: Algorithme RL (auto, DQN, PPO, etc.)
        include_metadata: Inclure les métadonnées
        output_name: Nom personnalisé pour l'export
        
    Returns:
        Résultats de la conversion
    """
    # Vérifier l'extension du fichier
    if not model_file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être un fichier .zip de modèle Stable-Baselines3"
        )
    
    # Créer un fichier temporaire
    temp_dir = tempfile.mkdtemp()
    temp_model_path = Path(temp_dir) / model_file.filename
    
    try:
        # Sauvegarder le fichier uploadé
        with open(temp_model_path, 'wb') as f:
            content = await model_file.read()
            f.write(content)
        
        # Convertir le modèle
        result = onnx_export_service.convert_model(
            model_path=str(temp_model_path),
            algorithm=algorithm,
            output_name=output_name,
            include_metadata=include_metadata
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la conversion: {result.get('error', 'Erreur inconnue')}"
            )
        
        # Nettoyer le fichier temporaire
        background_tasks.add_task(shutil.rmtree, temp_dir)
        
        return result
        
    except Exception as e:
        # Nettoyer en cas d'erreur
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/{platform}")
async def export_for_platform(
    platform: str,
    onnx_model_path: str = Form(...),
    platform_config: Optional[str] = Form(None)
):
    """
    Exporte un modèle ONNX pour une plateforme spécifique.
    
    Args:
        platform: Plateforme cible (pygame, web, unity, generic)
        onnx_model_path: Chemin vers le modèle ONNX
        platform_config: Configuration JSON pour la plateforme
        
    Returns:
        Résultats de l'export
    """
    # Vérifier que le fichier existe
    if not os.path.exists(onnx_model_path):
        raise HTTPException(
            status_code=404,
            detail=f"Fichier ONNX non trouvé: {onnx_model_path}"
        )
    
    # Parser la configuration si fournie
    config_dict = None
    if platform_config:
        try:
            config_dict = json.loads(platform_config)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Configuration invalide (doit être du JSON)"
            )
    
    # Exporter pour la plateforme
    result = onnx_export_service.export_for_platform(
        onnx_model_path=onnx_model_path,
        platform=platform,
        platform_config=config_dict
    )
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'export: {result.get('error', 'Erreur inconnue')}"
        )
    
    return result


@router.post("/export-all")
async def export_for_all_platforms(
    onnx_model_path: str = Form(...),
    platforms: Optional[str] = Form(None)
):
    """
    Exporte un modèle ONNX pour toutes les plateformes supportées.
    
    Args:
        onnx_model_path: Chemin vers le modèle ONNX
        platforms: Liste JSON des plateformes (défaut: toutes)
        
    Returns:
        Résultats de l'export multi-plateforme
    """
    # Vérifier que le fichier existe
    if not os.path.exists(onnx_model_path):
        raise HTTPException(
            status_code=404,
            detail=f"Fichier ONNX non trouvé: {onnx_model_path}"
        )
    
    # Parser la liste des plateformes si fournie
    platforms_list = None
    if platforms:
        try:
            platforms_list = json.loads(platforms)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Liste de plateformes invalide (doit être du JSON)"
            )
    
    # Exporter pour toutes les plateformes
    result = onnx_export_service.export_for_all_platforms(
        onnx_model_path=onnx_model_path,
        platforms=platforms_list
    )
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'export multi-plateforme: {result.get('error', 'Erreur inconnue')}"
        )
    
    return result


@router.post("/optimize")
async def optimize_model(
    onnx_model_path: str = Form(...),
    optimizations: Optional[str] = Form(None),
    validate: bool = Form(True)
):
    """
    Optimise un modèle ONNX.
    
    Args:
        onnx_model_path: Chemin vers le modèle ONNX
        optimizations: Liste JSON des optimisations à appliquer
        validate: Valider l'exactitude après optimisation
        
    Returns:
        Résultats de l'optimisation
    """
    # Vérifier que le fichier existe
    if not os.path.exists(onnx_model_path):
        raise HTTPException(
            status_code=404,
            detail=f"Fichier ONNX non trouvé: {onnx_model_path}"
        )
    
    # Parser la liste des optimisations si fournie
    optimizations_list = None
    if optimizations:
        try:
            optimizations_list = json.loads(optimizations)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Liste d'optimisations invalide (doit être du JSON)"
            )
    
    # Optimiser le modèle
    result = onnx_export_service.optimize_model(
        onnx_model_path=onnx_model_path,
        optimizations=optimizations_list,
        validate=validate
    )
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'optimisation: {result.get('error', 'Erreur inconnue')}"
        )
    
    return result


@router.post("/validate")
async def validate_model(
    onnx_model_path: str = Form(...),
    platforms: Optional[str] = Form(None),
    performance_test: bool = Form(True)
):
    """
    Valide un modèle ONNX.
    
    Args:
        onnx_model_path: Chemin vers le modèle ONNX
        platforms: Liste JSON des plateformes à valider
        performance_test: Inclure les tests de performance
        
    Returns:
        Résultats de la validation
    """
    # Vérifier que le fichier existe
    if not os.path.exists(onnx_model_path):
        raise HTTPException(
            status_code=404,
            detail=f"Fichier ONNX non trouvé: {onnx_model_path}"
        )
    
    # Parser la liste des plateformes si fournie
    platforms_list = None
    if platforms:
        try:
            platforms_list = json.loads(platforms)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Liste de plateformes invalide (doit être du JSON)"
            )
    
    # Valider le modèle
    result = onnx_export_service.validate_model(
        onnx_model_path=onnx_model_path,
        platforms=platforms_list,
        performance_test=performance_test
    )
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la validation: {result.get('error', 'Erreur inconnue')}"
        )
    
    return result


@router.post("/check-compatibility")
async def check_compatibility(
    onnx_model_path: str = Form(...),
    platforms: Optional[str] = Form(None)
):
    """
    Vérifie la compatibilité d'un modèle ONNX avec différentes plateformes.
    
    Args:
        onnx_model_path: Chemin vers le modèle ONNX
        platforms: Liste JSON des plateformes à vérifier
        
    Returns:
        Résultats de la vérification de compatibilité
    """
    # Vérifier que le fichier existe
    if not os.path.exists(onnx_model_path):
        raise HTTPException(
            status_code=404,
            detail=f"Fichier ONNX non trouvé: {onnx_model_path}"
        )
    
    # Parser la liste des plateformes si fournie
    platforms_list = None
    if platforms:
        try:
            platforms_list = json.loads(platforms)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Liste de plateformes invalide (doit être du JSON)"
            )
    
    # Vérifier la compatibilité
    result = onnx_export_service.check_compatibility(
        onnx_model_path=onnx_model_path,
        platforms=platforms_list
    )
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la vérification de compatibilité: {result.get('error', 'Erreur inconnue')}"
        )
    
    return result


@router.get("/exports")
async def list_exports():
    """
    Liste tous les exports disponibles.
    
    Returns:
        Liste des exports avec informations
    """
    result = onnx_export_service.list_exports()
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des exports: {result.get('error', 'Erreur inconnue')}"
        )
    
    return result


@router.get("/exports/{export_id}")
async def get_export_status(export_id: str):
    """
    Récupère le statut d'un export spécifique.
    
    Args:
        export_id: Identifiant de l'export
        
    Returns:
        Statut de l'export avec liste des fichiers
    """
    result = onnx_export_service.get_export_status(export_id)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=404,
            detail=f"Export non trouvé: {export_id}"
        )
    
    return result


@router.get("/exports/{export_id}/download")
async def download_export(export_id: str):
    """
    Télécharge un export complet sous forme d'archive ZIP.
    
    Args:
        export_id: Identifiant de l'export
        
    Returns:
        Archive ZIP de l'export
    """
    result = onnx_export_service.get_export_status(export_id)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=404,
            detail=f"Export non trouvé: {export_id}"
        )
    
    export_dir = result["export_dir"]
    
    # Créer une archive ZIP temporaire
    import zipfile
    temp_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
    
    try:
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(export_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, export_dir)
                    zipf.write(file_path, arcname)
        
        # Retourner le fichier ZIP
        return FileResponse(
            path=temp_zip.name,
            filename=f"{export_id}.zip",
            media_type='application/zip'
        )
        
    except Exception as e:
        os.unlink(temp_zip.name)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exports/{export_id}/files/{file_path:path}")
async def download_export_file(export_id: str, file_path: str):
    """
    Télécharge un fichier spécifique d'un export.
    
    Args:
        export_id: Identifiant de l'export
        file_path: Chemin relatif du fichier dans l'export
        
    Returns:
        Fichier demandé
    """
    result = onnx_export_service.get_export_status(export_id)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=404,
            detail=f"Export non trouvé: {export_id}"
        )
    
    export_dir = result["export_dir"]
    full_path = os.path.join(export_dir, file_path)
    
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=404,
            detail=f"Fichier non trouvé: {file_path}"
        )
    
    if not os.path.isfile(full_path):
        raise HTTPException(
            status_code=400,
            detail=f"Le chemin ne correspond pas à un fichier: {file_path}"
        )
    
    # Vérifier que le fichier est dans le répertoire d'export
    try:
        os.path.commonpath([export_dir, full_path]) == export_dir
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Accès non autorisé à ce fichier"
        )
    
    return FileResponse(full_path)


@router.delete("/exports/{export_id}")
async def delete_export(export_id: str):
    """
    Supprime un export et tous ses fichiers.
    
    Args:
        export_id: Identifiant de l'export
        
    Returns:
        Confirmation de suppression
    """
    result = onnx_export_service.get_export_status(export_id)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=404,
            detail=f"Export non trouvé: {export_id}"
        )
    
    export_dir = result["export_dir"]
    
    try:
        shutil.rmtree(export_dir)
        return {
            "success": True,
            "message": f"Export {export_id} supprimé avec succès",
            "export_id": export_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


@router.get("/platforms")
async def get_supported_platforms():
    """
    Retourne la liste des plateformes supportées avec leurs caractéristiques.
    
    Returns:
        Liste des plateformes supportées
    """
    return {
        "platforms": [
            {
                "id": "pygame",
                "name": "Pygame classique",
                "description": "Runtime ONNX Python avec interface simple",
                "requirements": ["onnxruntime", "numpy"],
                "export_formats": [".onnx", ".py", ".json"]
            },
            {
                "id": "web",
                "name": "Web (TensorFlow.js)",
                "description": "Conversion via onnx2tf ou ONNX.js",
                "requirements": ["onnx2tf", "tensorflowjs"],
                "export_formats": [".json", ".bin", ".html"]
            },
            {
                "id": "unity",
                "name": "Unity (Barracuda)",
                "description": "Export direct ONNX compatible Barracuda",
                "requirements": ["onnx", "onnxruntime"],
                "export_formats": [".onnx", ".bytes", ".cs"]
            },
            {
                "id": "generic",
                "name": "Interface générique",
                "description": "Interface REST pour inférence distante",
                "requirements": ["fastapi", "onnxruntime"],
                "export_formats": [".onnx", ".json", ".yaml", ".txt"]
            }
        ]
    }