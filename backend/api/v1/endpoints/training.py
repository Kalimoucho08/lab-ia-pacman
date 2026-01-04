"""
Endpoints API REST pour la gestion de l'entraînement RL.

Fournit les opérations pour démarrer, arrêter, mettre en pause
et suivre les sessions d'entraînement.
"""
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, BackgroundTasks

from backend.models.experiment import Session, SessionCreate, SessionUpdate
from backend.services.experiment_service import experiment_service
from backend.services.training_service import training_service
from backend.services.websocket_service import websocket_manager

router = APIRouter()

@router.post("/sessions/", response_model=Session, status_code=status.HTTP_201_CREATED)
async def create_session(session_data: SessionCreate):
    """Crée une nouvelle session d'entraînement."""
    # Vérifier que l'expérience existe
    experiment = experiment_service.get_experiment(session_data.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expérience {session_data.experiment_id} non trouvée"
        )
    
    # Créer la session
    session = Session(
        **session_data.dict(),
        total_episodes=experiment.parameters.training.episodes
    )
    
    # Sauvegarder dans la base de données (simplifié)
    # Dans une implémentation complète, on utiliserait experiment_service
    
    # Notifier via WebSocket
    await websocket_manager.broadcast_session_update({
        "type": "session_created",
        "session_id": session.id,
        "experiment_id": session.experiment_id,
        "name": session.name
    })
    
    return session

@router.post("/sessions/{session_id}/start")
async def start_training(session_id: str, background_tasks: BackgroundTasks):
    """Démarre l'entraînement pour une session."""
    # Récupérer la session (simulée)
    # Dans une implémentation réelle, on récupérerait depuis la base de données
    session = Session(
        id=session_id,
        experiment_id="exp_123",
        name="Session de test",
        algorithm_pacman="DQN",
        algorithm_ghosts="DQN"
    )
    
    # Récupérer les paramètres de l'expérience
    experiment = experiment_service.get_experiment(session.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expérience {session.experiment_id} non trouvée"
        )
    
    # Démarrer l'entraînement asynchrone
    training_id = training_service.start_training_async(session, experiment.parameters)
    
    # Mettre à jour le statut de la session
    session.status = "running"
    
    # Notifier via WebSocket
    await websocket_manager.broadcast_session_update({
        "type": "training_started",
        "session_id": session_id,
        "training_id": training_id,
        "status": "running"
    })
    
    return {
        "session_id": session_id,
        "training_id": training_id,
        "status": "started",
        "message": "Entraînement démarré en arrière-plan"
    }

@router.post("/sessions/{session_id}/pause")
async def pause_training(session_id: str):
    """Met en pause l'entraînement d'une session."""
    # Dans une implémentation réelle, on interromprait le modèle
    # Pour l'instant, on simule
    
    # Notifier via WebSocket
    await websocket_manager.broadcast_session_update({
        "type": "training_paused",
        "session_id": session_id,
        "status": "paused"
    })
    
    return {
        "session_id": session_id,
        "status": "paused",
        "message": "Entraînement mis en pause"
    }

@router.post("/sessions/{session_id}/resume")
async def resume_training(session_id: str):
    """Reprend l'entraînement d'une session mise en pause."""
    # Notifier via WebSocket
    await websocket_manager.broadcast_session_update({
        "type": "training_resumed",
        "session_id": session_id,
        "status": "running"
    })
    
    return {
        "session_id": session_id,
        "status": "running",
        "message": "Entraînement repris"
    }

@router.post("/sessions/{session_id}/stop")
async def stop_training(session_id: str):
    """Arrête l'entraînement d'une session."""
    # Dans une implémentation réelle, on arrêterait le thread d'entraînement
    # Pour l'instant, on simule
    
    # Notifier via WebSocket
    await websocket_manager.broadcast_session_update({
        "type": "training_stopped",
        "session_id": session_id,
        "status": "stopped"
    })
    
    return {
        "session_id": session_id,
        "status": "stopped",
        "message": "Entraînement arrêté"
    }

@router.get("/sessions/{session_id}/status")
async def get_training_status(session_id: str):
    """Récupère le statut d'entraînement d'une session."""
    # Dans une implémentation réelle, on récupérerait depuis training_service
    # Pour l'instant, on retourne un statut simulé
    
    return {
        "session_id": session_id,
        "status": "running",
        "current_episode": 42,
        "total_episodes": 1000,
        "metrics": {
            "reward": 150.5,
            "loss": 0.05,
            "exploration_rate": 0.1
        }
    }

@router.get("/training/{training_id}/status")
async def get_training_job_status(training_id: str):
    """Récupère le statut d'un job d'entraînement spécifique."""
    status_info = training_service.get_training_status(training_id)
    
    return {
        "training_id": training_id,
        **status_info
    }

@router.post("/training/{training_id}/stop")
async def stop_training_job(training_id: str):
    """Arrête un job d'entraînement spécifique."""
    stopped = training_service.stop_training(training_id)
    
    if not stopped:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job d'entraînement {training_id} non trouvé"
        )
    
    # Notifier via WebSocket
    await websocket_manager.broadcast_session_update({
        "type": "training_job_stopped",
        "training_id": training_id,
        "status": "stopped"
    })
    
    return {
        "training_id": training_id,
        "stopped": True,
        "message": "Job d'entraînement arrêté"
    }

@router.get("/metrics/{session_id}")
async def get_training_metrics(session_id: str, limit: int = 100):
    """Récupère les métriques d'entraînement d'une session."""
    # Dans une implémentation réelle, on récupérerait depuis la base de données
    # Pour l'instant, on retourne des métriques simulées
    
    import random
    from datetime import datetime, timedelta
    
    metrics = []
    base_time = datetime.now()
    
    for i in range(limit):
        metrics.append({
            "timestamp": (base_time - timedelta(seconds=i*10)).isoformat(),
            "episode": i,
            "reward": random.uniform(0, 200),
            "loss": random.uniform(0, 0.1),
            "exploration_rate": max(0.1, 1.0 - i/1000)
        })
    
    return {
        "session_id": session_id,
        "metrics": metrics,
        "count": len(metrics)
    }

@router.get("/models/")
async def list_saved_models():
    """Liste tous les modèles sauvegardés."""
    import os
    from pathlib import Path
    
    models_dir = Path("logs/models")
    models = []
    
    if models_dir.exists():
        for model_file in models_dir.glob("*.zip"):
            models.append({
                "name": model_file.name,
                "path": str(model_file),
                "size": model_file.stat().st_size,
                "modified": model_file.stat().st_mtime
            })
    
    return {
        "models": models,
        "count": len(models)
    }

@router.post("/export/{session_id}")
async def export_model(session_id: str, format: str = "onnx"):
    """Exporte un modèle entraîné dans un format spécifique (ONNX, etc.)."""
    # Dans une implémentation réelle, on convertirait le modèle
    # Pour l'instant, on simule
    
    return {
        "session_id": session_id,
        "format": format,
        "exported": True,
        "message": f"Modèle exporté au format {format}",
        "download_url": f"/api/v1/training/models/{session_id}.{format}"
    }