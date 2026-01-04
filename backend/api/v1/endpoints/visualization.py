"""
Endpoints API REST pour la visualisation du jeu.

Fournit les opérations pour générer des frames de visualisation,
récupérer des états de jeu, et gérer les paramètres de rendu.
"""
import base64
import io
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import Response

from backend.config import VisualizationParameters
from backend.services.websocket_service import websocket_manager

router = APIRouter()

@router.get("/frame", responses={
    200: {
        "content": {"image/png": {}},
        "description": "Retourne une image PNG de la frame de visualisation"
    }
})
async def get_visualization_frame(
    width: int = Query(400, ge=100, le=1920, description="Largeur de l'image"),
    height: int = Query(400, ge=100, le=1080, description="Hauteur de l'image"),
    grid_size: int = Query(10, ge=5, le=30, description="Taille de la grille"),
    show_grid: bool = Query(True, description="Afficher la grille"),
    show_stats: bool = Query(True, description="Afficher les statistiques")
):
    """Génère une frame de visualisation du jeu Pac-Man."""
    try:
        # Dans une implémentation réelle, on utiliserait un moteur de rendu
        # Pour l'instant, on génère une image simple avec Pillow ou on retourne une image factice
        
        # Vérifier si Pillow est disponible
        try:
            from PIL import Image, ImageDraw, ImageFont
            HAS_PILLOW = True
        except ImportError:
            HAS_PILLOW = False
        
        if HAS_PILLOW:
            # Créer une image avec Pillow
            image = Image.new('RGB', (width, height), color='black')
            draw = ImageDraw.Draw(image)
            
            # Dessiner une grille simple
            cell_size = min(width, height) // grid_size
            
            if show_grid:
                # Lignes verticales
                for x in range(0, width, cell_size):
                    draw.line([(x, 0), (x, height)], fill='gray', width=1)
                # Lignes horizontales
                for y in range(0, height, cell_size):
                    draw.line([(0, y), (width, y)], fill='gray', width=1)
            
            # Dessiner Pac-Man (cercle jaune)
            pacman_x = width // 2
            pacman_y = height // 2
            pacman_radius = cell_size // 2 - 2
            draw.ellipse(
                [(pacman_x - pacman_radius, pacman_y - pacman_radius),
                 (pacman_x + pacman_radius, pacman_y + pacman_radius)],
                fill='yellow'
            )
            
            # Dessiner des fantômes (cercles colorés)
            ghost_colors = ['red', 'pink', 'cyan', 'orange']
            for i, color in enumerate(ghost_colors[:3]):
                ghost_x = pacman_x + (i - 1) * cell_size * 2
                ghost_y = pacman_y
                draw.ellipse(
                    [(ghost_x - pacman_radius, ghost_y - pacman_radius),
                     (ghost_x + pacman_radius, ghost_y + pacman_radius)],
                    fill=color
                )
            
            if show_stats:
                # Ajouter du texte de statistiques
                try:
                    font = ImageFont.load_default()
                    stats_text = f"Grid: {grid_size}x{grid_size} | Score: 0 | Lives: 3"
                    draw.text((10, 10), stats_text, fill='white', font=font)
                except:
                    pass
            
            # Convertir en PNG
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            return Response(content=img_byte_arr.getvalue(), media_type="image/png")
        else:
            # Retourner une image PNG factice (1x1 pixel noir)
            fake_image = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
            return Response(content=fake_image, media_type="image/png")
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération de la frame: {str(e)}"
        )

@router.post("/config", response_model=VisualizationParameters)
async def update_visualization_config(config: VisualizationParameters):
    """Met à jour la configuration de visualisation."""
    # Dans une implémentation réelle, on sauvegarderait la configuration
    # Pour l'instant, on la retourne simplement
    
    # Notifier les clients via WebSocket
    await websocket_manager.broadcast({
        "type": "visualization_config_updated",
        "config": config.dict(),
        "timestamp": "2026-01-03T17:14:00Z"
    })
    
    return config

@router.get("/config", response_model=VisualizationParameters)
async def get_visualization_config():
    """Récupère la configuration de visualisation actuelle."""
    return VisualizationParameters()

@router.get("/websocket/info", response_model=Dict[str, Any])
async def get_websocket_info():
    """Récupère des informations sur les connexions WebSocket actives."""
    stats = websocket_manager.get_connection_stats()
    
    return {
        "websocket_endpoint": "ws://localhost:8000/ws",
        "available_channels": list(stats["subscriptions"].keys()),
        "connection_stats": stats,
        "subscription_instructions": {
            "connect": "Utiliser WebSocket sur /ws",
            "subscribe": 'Envoyer {"type": "subscribe", "channel": "metrics"}',
            "channels": ["metrics", "game_state", "session_updates", "experiment_updates", "errors"]
        }
    }

@router.post("/broadcast/test")
async def broadcast_test_message(message: str = "Test message from API"):
    """Envoie un message de test à tous les clients WebSocket connectés."""
    await websocket_manager.broadcast({
        "type": "test_message",
        "message": message,
        "timestamp": "2026-01-03T17:14:00Z"
    })
    
    return {
        "broadcasted": True,
        "message": message,
        "clients_count": len(websocket_manager.active_connections)
    }

@router.get("/performance", response_model=Dict[str, Any])
async def get_visualization_performance():
    """Récupère des métriques de performance de visualisation."""
    import time
    import psutil
    import os
    
    try:
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent(interval=0.1)
    except:
        memory_mb = 0
        cpu_percent = 0
    
    return {
        "performance": {
            "frame_generation_time_ms": 16.7,  # 60 FPS
            "memory_usage_mb": round(memory_mb, 2),
            "cpu_usage_percent": round(cpu_percent, 1),
            "active_websocket_connections": len(websocket_manager.active_connections)
        },
        "limits": {
            "max_frame_size": "1920x1080",
            "supported_formats": ["PNG", "JPEG"],
            "max_fps": 60
        }
    }

@router.get("/export/frame", responses={
    200: {
        "content": {"application/json": {}},
        "description": "Retourne une frame encodée en base64"
    }
})
async def export_frame_as_base64(
    width: int = Query(200, ge=50, le=800),
    height: int = Query(200, ge=50, le=800)
):
    """Exporte une frame de visualisation encodée en base64."""
    try:
        # Générer une image simple
        from PIL import Image, ImageDraw
        image = Image.new('RGB', (width, height), color='navy')
        draw = ImageDraw.Draw(image)
        
        # Dessiner un Pac-Man simple
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 4
        draw.ellipse(
            [(center_x - radius, center_y - radius),
             (center_x + radius, center_y + radius)],
            fill='yellow'
        )
        
        # Convertir en base64
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        
        return {
            "format": "png",
            "width": width,
            "height": height,
            "data": f"data:image/png;base64,{img_base64}",
            "size_bytes": len(img_byte_arr.getvalue())
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'export de la frame: {str(e)}"
        )