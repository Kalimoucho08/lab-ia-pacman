"""
Endpoints API REST pour la gestion des environnements de jeu.

Fournit les opérations pour configurer, réinitialiser
et interagir avec les environnements Pac-Man.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status

from backend.config import AllParameters, GameParameters
from backend.models.experiment import GameState
from backend.services.environment_service import environment_service
from backend.services.websocket_service import websocket_manager

router = APIRouter()

@router.get("/config/default", response_model=Dict[str, Any])
async def get_default_config():
    """Récupère la configuration par défaut de l'environnement."""
    return environment_service.get_default_config()

@router.post("/config/validate", response_model=Dict[str, Any])
async def validate_config(parameters: AllParameters):
    """Valide une configuration d'environnement."""
    is_valid, message = environment_service.validate_parameters(parameters)
    
    return {
        "valid": is_valid,
        "message": message,
        "parameters_summary": {
            "grid_size": parameters.game.grid_size,
            "num_ghosts": parameters.game.num_ghosts,
            "power_pellets": parameters.game.power_pellets,
            "pellet_density": parameters.game.pellet_density,
            "lives": parameters.game.lives
        }
    }

@router.post("/create/configurable", response_model=Dict[str, Any])
async def create_configurable_env(game_params: GameParameters):
    """Crée un environnement Pac-Man configurable."""
    env = environment_service.create_configurable_env(game_params)
    
    if env is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de créer l'environnement configurable"
        )
    
    # Extraire l'état initial
    game_state = environment_service.get_game_state(env, "configurable")
    
    return {
        "environment_type": "configurable",
        "grid_size": env.size,
        "num_ghosts": env.num_ghosts,
        "initial_state": game_state.dict() if game_state else None,
        "message": "Environnement configurable créé avec succès"
    }

@router.post("/create/multiagent", response_model=Dict[str, Any])
async def create_multiagent_env(game_params: GameParameters):
    """Crée un environnement Pac-Man multi-agent."""
    env = environment_service.create_multiagent_env(game_params)
    
    if env is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de créer l'environnement multi-agent"
        )
    
    # Extraire l'état initial
    game_state = environment_service.get_game_state(env, "multiagent")
    
    return {
        "environment_type": "multiagent",
        "grid_size": env.size,
        "num_ghosts": env.num_ghosts,
        "power_pellets": env.power_pellets,
        "initial_state": game_state.dict() if game_state else None,
        "message": "Environnement multi-agent créé avec succès"
    }

@router.post("/simulate/step", response_model=Dict[str, Any])
async def simulate_step(environment_type: str = "configurable", steps: int = 1):
    """Simule un ou plusieurs steps dans un environnement."""
    # Créer un environnement temporaire pour la simulation
    game_params = GameParameters(
        grid_size=10,
        num_ghosts=2,
        power_pellets=2,
        lives=3,
        pellet_density=0.7
    )
    
    if environment_type == "configurable":
        env = environment_service.create_configurable_env(game_params)
    elif environment_type == "multiagent":
        env = environment_service.create_multiagent_env(game_params)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type d'environnement invalide: {environment_type}"
        )
    
    if env is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de créer l'environnement de simulation"
        )
    
    # Réinitialiser l'environnement
    if hasattr(env, 'reset'):
        env.reset()
    
    # Simuler les steps
    states = []
    for step in range(steps):
        # Action aléatoire pour la simulation
        import random
        if environment_type == "configurable":
            action = random.randint(0, 3)
            obs, reward, terminated, truncated, info = env.step(action)
        else:
            # Pour multi-agent, actions pour tous les agents
            actions = {}
            for agent in env.agents:
                actions[agent] = random.randint(0, 3)
            obs, rewards, terminations, truncations, infos = env.step(actions)
        
        # Extraire l'état
        game_state = environment_service.get_game_state(env, environment_type)
        if game_state:
            states.append(game_state.dict())
    
    # Nettoyer
    if hasattr(env, 'close'):
        env.close()
    
    return {
        "environment_type": environment_type,
        "steps_simulated": steps,
        "states": states,
        "final_state": states[-1] if states else None
    }

@router.get("/visualization/state", response_model=GameState)
async def get_visualization_state(environment_type: str = "configurable"):
    """Génère un état de visualisation pour le frontend."""
    # Créer un environnement temporaire
    game_params = GameParameters(
        grid_size=12,
        num_ghosts=3,
        power_pellets=2,
        lives=3,
        pellet_density=0.6
    )
    
    if environment_type == "configurable":
        env = environment_service.create_configurable_env(game_params)
    else:
        env = environment_service.create_multiagent_env(game_params)
    
    if env is None:
        # Retourner un état simulé si l'environnement n'est pas disponible
        import random
        grid_size = game_params.grid_size
        grid = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
        
        # Ajouter quelques murs
        for _ in range(grid_size * 2):
            x, y = random.randint(0, grid_size-1), random.randint(0, grid_size-1)
            grid[y][x] = -1
        
        # Ajouter des points
        for _ in range(int(grid_size * grid_size * 0.3)):
            while True:
                x, y = random.randint(0, grid_size-1), random.randint(0, grid_size-1)
                if grid[y][x] == 0:
                    grid[y][x] = 1
                    break
        
        # Position de Pac-Man
        pacman_x, pacman_y = grid_size//2, grid_size//2
        grid[pacman_y][pacman_x] = 0
        
        # Fantômes
        ghosts = []
        for i in range(game_params.num_ghosts):
            while True:
                x, y = random.randint(0, grid_size-1), random.randint(0, grid_size-1)
                if grid[y][x] == 0 and (x, y) != (pacman_x, pacman_y):
                    ghosts.append({
                        "x": x,
                        "y": y,
                        "color": f"ghost_{i}",
                        "mode": "normal"
                    })
                    break
        
        game_state = GameState(
            grid=grid,
            pacman={"x": pacman_x, "y": pacman_y, "direction": "right"},
            ghosts=ghosts,
            pellets=[{"x": x, "y": y} for y in range(grid_size) for x in range(grid_size) if grid[y][x] == 1],
            power_pellets=[],
            score=0,
            lives=game_params.lives,
            step=0,
            episode=0
        )
    else:
        # Extraire l'état réel
        game_state = environment_service.get_game_state(env, environment_type)
        if hasattr(env, 'close'):
            env.close()
        
        if game_state is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Impossible d'extraire l'état du jeu"
            )
    
    # Diffuser via WebSocket pour les clients abonnés
    await websocket_manager.broadcast_game_state(game_state.dict())
    
    return game_state

@router.get("/capabilities", response_model=Dict[str, Any])
async def get_environment_capabilities():
    """Récupère les capacités des environnements disponibles."""
    capabilities = {
        "configurable_env_available": environment_service.create_configurable_env is not None,
        "multiagent_env_available": environment_service.create_multiagent_env is not None,
        "supported_features": {
            "power_pellets": True,
            "multiple_ghosts": True,
            "custom_walls": True,
            "variable_grid_size": True,
            "reward_customization": True
        },
        "limits": {
            "max_grid_size": 30,
            "max_ghosts": 4,
            "max_power_pellets": 10,
            "max_lives": 10
        }
    }
    
    return capabilities