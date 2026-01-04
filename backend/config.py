"""
Configuration de l'application backend.

Contient les paramètres de l'application, les schémas Pydantic pour les
20 paramètres configurables, et les valeurs par défaut scientifiques.
"""
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, confloat, conint
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Paramètres de l'application chargés depuis les variables d'environnement."""
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Base de données SQLite
    DATABASE_URL: str = "sqlite:///./experiments.db"
    
    # Répertoires
    LOGS_DIR: str = "logs"
    MODELS_DIR: str = "logs/models"
    EXPERIMENTS_DIR: str = "experiments"
    
    # Stable-Baselines3
    SB3_ALGORITHMS: List[str] = ["DQN", "PPO", "A2C", "SAC", "TD3"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# ============================================================================
# Schémas Pydantic pour les 20 paramètres configurables
# ============================================================================

class TrainingParameters(BaseModel):
    """Paramètres d'entraînement RL."""
    learning_rate: confloat(ge=1e-5, le=0.1) = Field(
        0.001,
        description="Taux d'apprentissage de l'optimiseur (plus petit = apprentissage stable mais lent)"
    )
    gamma: confloat(ge=0.5, le=0.9999) = Field(
        0.99,
        description="Facteur de discount des récompenses futures (0 = myope, 1 = vision à long terme)"
    )
    episodes: conint(ge=1, le=100000) = Field(
        1000,
        description="Nombre d'épisodes d'entraînement (chaque épisode = une partie complète)"
    )
    batch_size: conint(ge=8, le=2048) = Field(
        64,
        description="Taille du batch pour l'apprentissage par gradient (plus grand = stable mais gourmand en mémoire)"
    )
    buffer_size: conint(ge=1000, le=1000000) = Field(
        10000,
        description="Taille du replay buffer (mémoire d'expériences pour l'apprentissage hors politique)"
    )

class GameParameters(BaseModel):
    """Paramètres du jeu Pac-Man."""
    grid_size: conint(ge=5, le=30) = Field(
        10,
        description="Taille de la grille (N x N). Plus grand = plus complexe."
    )
    num_ghosts: conint(ge=1, le=4) = Field(
        2,
        description="Nombre de fantômes (1-4). Plus il y a de fantômes, plus le jeu est difficile."
    )
    power_pellets: conint(ge=0, le=10) = Field(
        2,
        description="Nombre de power pellets qui rendent les fantômes vulnérables."
    )
    lives: conint(ge=1, le=10) = Field(
        3,
        description="Nombre de vies de Pac-Man. Plus de vies = plus de tolérance aux erreurs."
    )
    pellet_density: confloat(ge=0.1, le=1.0) = Field(
        0.7,
        description="Densité des points dans la grille (1.0 = toutes les cases libres ont un point)."
    )

class IntelligenceParameters(BaseModel):
    """Paramètres d'exploration et d'apprentissage."""
    exploration_rate: confloat(ge=0.01, le=1.0) = Field(
        0.1,
        description="Taux d'exploration (epsilon) pour les politiques ε-greedy (1.0 = toujours explorer)"
    )
    target_update: conint(ge=1, le=10000) = Field(
        100,
        description="Fréquence de mise à jour du réseau cible (en steps). Plus petit = apprentissage plus instable."
    )
    learning_starts: conint(ge=0, le=10000) = Field(
        1000,
        description="Nombre de steps avant de commencer l'apprentissage (pour remplir le buffer)"
    )
    train_freq: conint(ge=1, le=100) = Field(
        4,
        description="Fréquence d'entraînement (entraîner tous les N steps)."
    )

class VisualizationParameters(BaseModel):
    """Paramètres de visualisation."""
    fps: conint(ge=1, le=120) = Field(
        10,
        description="Images par seconde pour la visualisation en temps réel."
    )
    render_scale: conint(ge=10, le=200) = Field(
        50,
        description="Échelle de rendu (taille en pixels d'une cellule)."
    )
    show_grid: conint(ge=0, le=1) = Field(
        1,
        description="Afficher la grille (1 = oui, 0 = non)."
    )
    show_stats: conint(ge=0, le=1) = Field(
        1,
        description="Afficher les statistiques en superposition (1 = oui, 0 = non)."
    )
    highlight_path: conint(ge=0, le=1) = Field(
        0,
        description="Mettre en évidence le chemin de Pac-Man (1 = oui, 0 = non)."
    )

class AllParameters(BaseModel):
    """Regroupement de tous les paramètres."""
    training: TrainingParameters = Field(default_factory=TrainingParameters)
    game: GameParameters = Field(default_factory=GameParameters)
    intelligence: IntelligenceParameters = Field(default_factory=IntelligenceParameters)
    visualization: VisualizationParameters = Field(default_factory=VisualizationParameters)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit tous les paramètres en dictionnaire plat."""
        flat = {}
        for category in ["training", "game", "intelligence", "visualization"]:
            category_params = getattr(self, category)
            for key, value in category_params.dict().items():
                flat[f"{category}_{key}"] = value
        return flat
    
    @classmethod
    def from_flat_dict(cls, flat_dict: Dict[str, Any]) -> "AllParameters":
        """Reconstruit AllParameters à partir d'un dictionnaire plat."""
        structured = {}
        for category in ["training", "game", "intelligence", "visualization"]:
            prefix = f"{category}_"
            category_dict = {}
            for key, value in flat_dict.items():
                if key.startswith(prefix):
                    category_key = key[len(prefix):]
                    category_dict[category_key] = value
            if category == "training":
                structured[category] = TrainingParameters(**category_dict)
            elif category == "game":
                structured[category] = GameParameters(**category_dict)
            elif category == "intelligence":
                structured[category] = IntelligenceParameters(**category_dict)
            elif category == "visualization":
                structured[category] = VisualizationParameters(**category_dict)
        return cls(**structured)

# Valeurs par défaut scientifiques (configurations prédéfinies)
PRESET_CONFIGS = {
    "debutant": AllParameters(
        training=TrainingParameters(
            learning_rate=0.0005,
            gamma=0.95,
            episodes=500,
            batch_size=32,
            buffer_size=5000
        ),
        game=GameParameters(
            grid_size=8,
            num_ghosts=1,
            power_pellets=1,
            lives=5,
            pellet_density=0.5
        ),
        intelligence=IntelligenceParameters(
            exploration_rate=0.2,
            target_update=200,
            learning_starts=500,
            train_freq=8
        ),
        visualization=VisualizationParameters(
            fps=5,
            render_scale=40,
            show_grid=1,
            show_stats=1,
            highlight_path=1
        )
    ),
    "avance": AllParameters(
        training=TrainingParameters(
            learning_rate=0.001,
            gamma=0.99,
            episodes=2000,
            batch_size=64,
            buffer_size=10000
        ),
        game=GameParameters(
            grid_size=12,
            num_ghosts=2,
            power_pellets=2,
            lives=3,
            pellet_density=0.7
        ),
        intelligence=IntelligenceParameters(
            exploration_rate=0.1,
            target_update=100,
            learning_starts=1000,
            train_freq=4
        ),
        visualization=VisualizationParameters(
            fps=10,
            render_scale=50,
            show_grid=1,
            show_stats=1,
            highlight_path=0
        )
    ),
    "expert": AllParameters(
        training=TrainingParameters(
            learning_rate=0.0001,
            gamma=0.999,
            episodes=10000,
            batch_size=128,
            buffer_size=50000
        ),
        game=GameParameters(
            grid_size=15,
            num_ghosts=3,
            power_pellets=3,
            lives=2,
            pellet_density=0.8
        ),
        intelligence=IntelligenceParameters(
            exploration_rate=0.05,
            target_update=50,
            learning_starts=2000,
            train_freq=2
        ),
        visualization=VisualizationParameters(
            fps=30,
            render_scale=60,
            show_grid=0,
            show_stats=1,
            highlight_path=0
        )
    )
}