"""
Backend FastAPI minimal pour le laboratoire Pac-Man.
Version simplifiée pour fournir des données mock et permettre le test de l'interface.
"""
import asyncio
import json
import random
import time
from typing import Dict, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Pac-Man Lab Backend Minimal", version="0.1.0")

# CORS pour autoriser le frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Données mock pour le jeu Pac-Man
MOCK_GRID = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1],
    [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1],
    [0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0],
    [1, 1, 1, 1, 0, 1, 0, 1, 1, 2, 1, 1, 0, 1, 0, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 1, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1],
    [0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0],
    [1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

# Positions initiales
PACMAN_START = (10, 9)
GHOST_STARTS = [(9, 9), (10, 8), (11, 9), (10, 10)]

def generate_mock_game_state(step: int) -> Dict[str, Any]:
    """Génère un état de jeu mocké."""
    # Déplacer Pac-Man en cercle
    angle = step * 0.1
    pacman_x = PACMAN_START[0] + int(3 * (1 + 0.5 * step % 10))
    pacman_y = PACMAN_START[1] + int(2 * (1 + 0.3 * step % 10))
    pacman_x = max(1, min(pacman_x, len(MOCK_GRID[0]) - 2))
    pacman_y = max(1, min(pacman_y, len(MOCK_GRID) - 2))
    
    # Déplacer les fantômes
    ghosts = []
    for i, (gx, gy) in enumerate(GHOST_STARTS):
        offset = step * (0.2 + i * 0.1)
        ghost_x = gx + int(2 * (1 + 0.4 * offset % 8))
        ghost_y = gy + int(1 * (1 + 0.2 * offset % 6))
        ghost_x = max(1, min(ghost_x, len(MOCK_GRID[0]) - 2))
        ghost_y = max(1, min(ghost_y, len(MOCK_GRID) - 2))
        ghosts.append({
            "id": f"ghost_{i}",
            "position": [ghost_x, ghost_y],
            "color": ["#FF0000", "#FF88FF", "#00FFFF", "#FFAA00"][i],
            "state": "chase" if step % 20 < 10 else "scatter",
            "direction": ["up", "down", "left", "right"][(step + i) % 4]
        })
    
    # Compter les pellets restants
    pellets = []
    power_pellets = []
    for y, row in enumerate(MOCK_GRID):
        for x, cell in enumerate(row):
            if cell == 0:
                pellets.append([x, y])
            elif cell == 2:
                power_pellets.append([x, y])
    
    # Simuler la consommation de pellets
    remaining_pellets = pellets[:max(10, len(pellets) - step % 50)]
    remaining_power_pellets = power_pellets[:max(2, len(power_pellets) - (step // 30))]
    
    # Convertir pellets et power_pellets en objets {x, y}
    pellets_objects = [{"x": p[0], "y": p[1]} for p in remaining_pellets]
    power_pellets_objects = [{"x": p[0], "y": p[1]} for p in remaining_power_pellets]
    
    # Convertir ghosts pour avoir x, y, color, mode
    ghosts_objects = []
    for i, ghost in enumerate(ghosts):
        ghosts_objects.append({
            "x": ghost["position"][0],
            "y": ghost["position"][1],
            "color": ghost["color"],
            "mode": ghost["state"]
        })
    
    # Pac-Man avec x, y, direction
    pacman_obj = {
        "x": pacman_x,
        "y": pacman_y,
        "direction": ["right", "down", "left", "up"][step % 4]
    }
    
    return {
        "step": step,
        "score": step * 10 + 100,
        "lives": 3 - (step // 100),
        "pacman": pacman_obj,
        "ghosts": ghosts_objects,
        "grid": MOCK_GRID,
        "pellets": pellets_objects,
        "powerPellets": power_pellets_objects,
        "game_over": step > 500,
        "victory": len(remaining_pellets) == 0 and len(remaining_power_pellets) == 0,
        "timestamp": time.time(),
        "metrics": {
            "fps": 60,
            "latency": random.randint(5, 30),
            "memory_usage": random.randint(200, 500),
            "buffer_size": random.randint(10, 50)
        }
    }

@app.get("/")
async def root():
    """Endpoint racine."""
    return {"message": "Pac-Man Lab Backend Minimal", "status": "running"}

@app.get("/api/status")
async def get_status():
    """Retourne le statut du backend."""
    return {"status": "ok", "version": "0.1.0", "timestamp": time.time()}

@app.get("/api/game_state")
async def get_game_state():
    """Retourne un état de jeu mocké (pour tests)."""
    return generate_mock_game_state(int(time.time()) % 1000)

@app.websocket("/ws/game_state")
async def websocket_game_state(websocket: WebSocket):
    """WebSocket qui envoie des états de jeu mockés en temps réel."""
    await websocket.accept()
    print("WebSocket client connected")
    
    try:
        step = 0
        while True:
            # Générer un état mocké
            game_state = generate_mock_game_state(step)
            
            # Envoyer l'état au client
            await websocket.send_json({
                "type": "game_state",
                "data": game_state,
                "timestamp": time.time()
            })
            
            # Envoyer également des métriques de performance
            if step % 5 == 0:
                await websocket.send_json({
                    "type": "performance_stats",
                    "data": {
                        "fps": random.randint(55, 65),
                        "latency": random.randint(5, 50),
                        "memory_usage": random.randint(200, 600),
                        "buffer_size": random.randint(5, 30)
                    }
                })
            
            step += 1
            await asyncio.sleep(0.1)  # ~10 FPS pour simuler un jeu
            
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()

if __name__ == "__main__":
    print("Démarrage du backend FastAPI minimal sur http://localhost:8000")
    print("Endpoints disponibles:")
    print("  GET /api/status")
    print("  GET /api/game_state")
    print("  WS  /ws/game_state")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")