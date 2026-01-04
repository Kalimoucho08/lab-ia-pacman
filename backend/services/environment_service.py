"""
Service d'intégration des environnements Pac-Man existants.

Adapte les environnements configurable_env.py et multiagent_env.py
pour l'API backend avec validation des paramètres.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Ajout du chemin src pour importer les environnements existants
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from pacman_env.configurable_env import PacManConfigurableEnv
    from pacman_env.multiagent_env import PacManMultiAgentEnv
    from pacman_env.multiagent_wrappers import SingleAgentWrapper
    IMPORT_SUCCESS = True
except ImportError as e:
    logging.warning(f"Impossible d'importer les environnements Pac-Man: {e}")
    PacManConfigurableEnv = None
    PacManMultiAgentEnv = None
    SingleAgentWrapper = None
    IMPORT_SUCCESS = False

from backend.config import AllParameters, GameParameters
from backend.models.experiment import GameState

logger = logging.getLogger(__name__)

class EnvironmentService:
    """Service pour la gestion des environnements de jeu."""
    
    def __init__(self):
        """Initialise le service avec les environnements disponibles."""
        self.environments = {}
        self.active_sessions = {}
        
        if not IMPORT_SUCCESS:
            logger.error("Les environnements Pac-Man ne sont pas disponibles. "
                        "Vérifiez que le code source est dans src/pacman_env/")
    
    def create_configurable_env(self, game_params: GameParameters, **kwargs) -> Optional[PacManConfigurableEnv]:
        """Crée un environnement Pac-Man configurable à partir des paramètres."""
        if PacManConfigurableEnv is None:
            return None
        
        # Conversion des paramètres de jeu vers les arguments de l'environnement
        # Calcul du nombre de points basé sur la densité
        total_cells = game_params.grid_size * game_params.grid_size
        # Estimation: on suppose 10% de murs par défaut
        estimated_walls = int(total_cells * 0.1)
        free_cells = total_cells - estimated_walls - 1 - game_params.num_ghosts  # Pac-Man + fantômes
        num_dots = int(free_cells * game_params.pellet_density)
        
        # Création de l'environnement
        env = PacManConfigurableEnv(
            size=game_params.grid_size,
            walls=[],  # À générer aléatoirement ou via configuration
            num_ghosts=game_params.num_ghosts,
            num_dots=num_dots,
            lives=game_params.lives,
            max_steps=200,  # Par défaut
            ghost_behavior='random',  # Par défaut
            reward_structure={
                'dot': 10.0,
                'ghost_caught': -50.0,
                'death': -100.0,
                'step': -0.1
            },
            **kwargs
        )
        
        logger.info(f"Environnement configurable créé: grille {game_params.grid_size}x{game_params.grid_size}, "
                   f"{game_params.num_ghosts} fantômes, {num_dots} points")
        return env
    
    def create_multiagent_env(self, game_params: GameParameters, **kwargs) -> Optional[PacManMultiAgentEnv]:
        """Crée un environnement Pac-Man multi-agent à partir des paramètres."""
        if PacManMultiAgentEnv is None:
            return None
        
        # Calcul du nombre de points
        total_cells = game_params.grid_size * game_params.grid_size
        estimated_walls = int(total_cells * 0.1)
        free_cells = total_cells - estimated_walls - 1 - game_params.num_ghosts - game_params.power_pellets
        num_dots = int(free_cells * game_params.pellet_density)
        
        # Création de l'environnement
        env = PacManMultiAgentEnv(
            size=game_params.grid_size,
            walls=[],
            num_ghosts=game_params.num_ghosts,
            num_dots=num_dots,
            lives=game_params.lives,
            power_pellets=game_params.power_pellets,
            power_duration=15,  # Par défaut
            ghost_behavior='random',  # Par défaut
            reward_config={
                "pacman": {
                    "dot": 10.0,
                    "ghost_eaten": 50.0,
                    "death": -100.0,
                    "step": -0.1,
                    "power_pellet_eaten": 20.0
                },
                "ghost": {
                    "eat_pacman": 100.0,
                    "eaten": -50.0,
                    "step": -0.1,
                    "distance_reward": 0.0
                }
            },
            **kwargs
        )
        
        logger.info(f"Environnement multi-agent créé: grille {game_params.grid_size}x{game_params.grid_size}, "
                   f"{game_params.num_ghosts} fantômes, {game_params.power_pellets} power pellets")
        return env
    
    def create_single_agent_wrapper(self, multiagent_env: PacManMultiAgentEnv, agent_id: str):
        """Crée un wrapper single-agent pour un environnement multi-agent."""
        if SingleAgentWrapper is None or multiagent_env is None:
            return None
        
        return SingleAgentWrapper(multiagent_env, agent_id)
    
    def get_game_state(self, env, env_type: str = "configurable") -> Optional[GameState]:
        """Extrait l'état du jeu depuis un environnement pour la visualisation."""
        if env is None:
            return None
        
        try:
            if env_type == "configurable" and hasattr(env, 'dots'):
                # Pour PacManConfigurableEnv
                grid_size = env.size
                grid = []
                for r in range(grid_size):
                    row = []
                    for c in range(grid_size):
                        if (r, c) in env.walls:
                            row.append(-1)  # Mur
                        elif env.dots[r, c] == 1:
                            row.append(1)   # Point
                        else:
                            row.append(0)   # Vide
                    grid.append(row)
                
                pacman = {
                    "x": env.pacman_pos[1],
                    "y": env.pacman_pos[0],
                    "direction": "right"  # À déterminer
                }
                
                ghosts = []
                for i, (r, c) in enumerate(env.ghost_positions):
                    ghosts.append({
                        "x": c,
                        "y": r,
                        "color": f"ghost_{i}",
                        "mode": "normal"
                    })
                
                # Points restants
                pellets = []
                for r in range(grid_size):
                    for c in range(grid_size):
                        if env.dots[r, c] == 1:
                            pellets.append({"x": c, "y": r})
                
                return GameState(
                    grid=grid,
                    pacman=pacman,
                    ghosts=ghosts,
                    pellets=pellets,
                    power_pellets=[],  # Pas de power pellets dans configurable
                    score=0,  # À calculer
                    lives=env.current_lives,
                    step=env.current_step,
                    episode=0
                )
                
            elif env_type == "multiagent" and hasattr(env, 'dots'):
                # Pour PacManMultiAgentEnv
                grid_size = env.size
                grid = []
                for r in range(grid_size):
                    row = []
                    for c in range(grid_size):
                        if (r, c) in env.walls:
                            row.append(-1)
                        elif env.dots[r, c] == 1:
                            row.append(1)
                        elif env.dots[r, c] == 2:
                            row.append(2)  # Power pellet
                        else:
                            row.append(0)
                    grid.append(row)
                
                pacman = {
                    "x": env.pacman_pos[1],
                    "y": env.pacman_pos[0],
                    "direction": "right"
                }
                
                ghosts = []
                for i, (r, c) in enumerate(env.ghost_positions):
                    mode = "vulnerable" if i in getattr(env, 'vulnerable_ghosts', set()) else "normal"
                    ghosts.append({
                        "x": c,
                        "y": r,
                        "color": f"ghost_{i}",
                        "mode": mode
                    })
                
                pellets = []
                for r in range(grid_size):
                    for c in range(grid_size):
                        if env.dots[r, c] == 1:
                            pellets.append({"x": c, "y": r})
                
                power_pellets = []
                for (r, c) in getattr(env, 'power_pellet_positions', []):
                    power_pellets.append({"x": c, "y": r})
                
                return GameState(
                    grid=grid,
                    pacman=pacman,
                    ghosts=ghosts,
                    pellets=pellets,
                    power_pellets=power_pellets,
                    score=0,
                    lives=env.current_lives,
                    step=env.current_step,
                    episode=0
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de l'état du jeu: {e}")
        
        return None
    
    def validate_parameters(self, parameters: AllParameters) -> Tuple[bool, str]:
        """Valide les paramètres de jeu pour s'assurer qu'ils sont cohérents."""
        game = parameters.game
        
        # Vérification de la taille de la grille
        if game.grid_size < 5:
            return False, "La taille de la grille doit être d'au moins 5"
        
        # Vérification du nombre de fantômes
        if game.num_ghosts < 1 or game.num_ghosts > 4:
            return False, "Le nombre de fantômes doit être entre 1 et 4"
        
        # Vérification des power pellets
        if game.power_pellets < 0 or game.power_pellets > 10:
            return False, "Le nombre de power pellets doit être entre 0 et 10"
        
        # Vérification de la densité des points
        if game.pellet_density < 0.1 or game.pellet_density > 1.0:
            return False, "La densité des points doit être entre 0.1 et 1.0"
        
        # Vérification de la cohérence: assez de place pour les points
        total_cells = game.grid_size * game.grid_size
        min_occupied = 1 + game.num_ghosts + game.power_pellets  # Pac-Man + fantômes + power pellets
        if min_occupied >= total_cells:
            return False, "La grille est trop petite pour le nombre d'éléments"
        
        max_dots = total_cells - min_occupied
        estimated_dots = int(max_dots * game.pellet_density)
        if estimated_dots < 1:
            return False, "Pas assez de points dans la grille avec cette densité"
        
        return True, "Paramètres valides"
    
    def get_default_config(self) -> Dict[str, Any]:
        """Retourne la configuration par défaut pour l'environnement."""
        return {
            "grid_size": 10,
            "num_ghosts": 2,
            "power_pellets": 2,
            "lives": 3,
            "pellet_density": 0.7,
            "ghost_behavior": "random",
            "max_steps": 200,
            "power_duration": 15
        }

# Instance singleton du service
environment_service = EnvironmentService()