"""
Endpoints API REST pour la gestion des expériences.

Fournit les opérations CRUD sur les expériences,
ainsi que la gestion des configurations prédéfinies.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query

from backend.models.experiment import Experiment, ExperimentCreate, ExperimentUpdate
from backend.services.experiment_service import experiment_service
from backend.services.websocket_service import websocket_manager

router = APIRouter()

@router.get("/", response_model=List[Experiment])
async def list_experiments(
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'expériences à retourner"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination")
):
    """Liste toutes les expériences."""
    experiments = experiment_service.list_experiments(limit=limit, offset=offset)
    return experiments

@router.post("/", response_model=Experiment, status_code=status.HTTP_201_CREATED)
async def create_experiment(experiment_data: ExperimentCreate):
    """Crée une nouvelle expérience."""
    # Valider les paramètres
    from backend.services.environment_service import environment_service
    is_valid, message = environment_service.validate_parameters(experiment_data.parameters)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Paramètres invalides: {message}"
        )
    
    experiment = experiment_service.create_experiment(experiment_data)
    
    # Notifier via WebSocket
    await websocket_manager.broadcast_experiment_update({
        "type": "experiment_created",
        "experiment_id": experiment.id,
        "name": experiment.name,
        "status": experiment.status
    })
    
    return experiment

@router.get("/{experiment_id}", response_model=Experiment)
async def get_experiment(experiment_id: str):
    """Récupère une expérience par son ID."""
    experiment = experiment_service.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expérience {experiment_id} non trouvée"
        )
    return experiment

@router.put("/{experiment_id}", response_model=Experiment)
async def update_experiment(experiment_id: str, update_data: ExperimentUpdate):
    """Met à jour une expérience existante."""
    experiment = experiment_service.update_experiment(experiment_id, update_data)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expérience {experiment_id} non trouvée"
        )
    
    # Notifier via WebSocket
    await websocket_manager.broadcast_experiment_update({
        "type": "experiment_updated",
        "experiment_id": experiment.id,
        "status": experiment.status
    })
    
    return experiment

@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(experiment_id: str):
    """Supprime une expérience."""
    deleted = experiment_service.delete_experiment(experiment_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expérience {experiment_id} non trouvée"
        )
    
    # Notifier via WebSocket
    await websocket_manager.broadcast_experiment_update({
        "type": "experiment_deleted",
        "experiment_id": experiment_id
    })

@router.get("/presets/", response_model=dict)
async def list_presets():
    """Liste toutes les configurations prédéfinies disponibles."""
    return experiment_service.list_presets()

@router.get("/presets/{preset_name}", response_model=dict)
async def get_preset(preset_name: str):
    """Récupère une configuration prédéfinie spécifique."""
    config = experiment_service.get_preset_config(preset_name)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Préréglage {preset_name} non trouvé"
        )
    return {
        "preset": preset_name,
        "parameters": config.dict()
    }

@router.post("/{experiment_id}/duplicate", response_model=Experiment)
async def duplicate_experiment(experiment_id: str, new_name: Optional[str] = None):
    """Duplique une expérience existante."""
    original = experiment_service.get_experiment(experiment_id)
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expérience {experiment_id} non trouvée"
        )
    
    # Créer une nouvelle expérience avec les mêmes paramètres
    duplicate_data = ExperimentCreate(
        name=new_name or f"{original.name} (copie)",
        description=original.description,
        tags=original.tags.copy(),
        preset=original.preset,
        parameters=original.parameters
    )
    
    duplicate = experiment_service.create_experiment(duplicate_data)
    
    # Notifier via WebSocket
    await websocket_manager.broadcast_experiment_update({
        "type": "experiment_duplicated",
        "original_id": original.id,
        "new_id": duplicate.id,
        "name": duplicate.name
    })
    
    return duplicate

@router.get("/{experiment_id}/validate", response_model=dict)
async def validate_experiment_parameters(experiment_id: str):
    """Valide les paramètres d'une expérience."""
    experiment = experiment_service.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expérience {experiment_id} non trouvée"
        )
    
    from backend.services.environment_service import environment_service
    is_valid, message = environment_service.validate_parameters(experiment.parameters)
    
    return {
        "experiment_id": experiment_id,
        "valid": is_valid,
        "message": message,
        "parameters_summary": {
            "grid_size": experiment.parameters.game.grid_size,
            "num_ghosts": experiment.parameters.game.num_ghosts,
            "power_pellets": experiment.parameters.game.power_pellets,
            "pellet_density": experiment.parameters.game.pellet_density
        }
    }