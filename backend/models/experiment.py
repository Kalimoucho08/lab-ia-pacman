"""
Modèles Pydantic pour les expériences, sessions et métriques.

Ces modèles sont utilisés pour la validation des données entrantes
et la sérialisation des réponses API.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field, validator

from backend.config import AllParameters

class ExperimentBase(BaseModel):
    """Base commune pour une expérience."""
    name: str = Field(..., description="Nom de l'expérience", max_length=100)
    description: Optional[str] = Field(None, description="Description détaillée", max_length=500)
    tags: List[str] = Field(default_factory=list, description="Tags pour catégoriser l'expérience")
    preset: Optional[str] = Field(None, description="Préréglage utilisé (débutant, avancé, expert)")

class ExperimentCreate(ExperimentBase):
    """Données requises pour créer une nouvelle expérience."""
    parameters: AllParameters = Field(default_factory=AllParameters)

class ExperimentUpdate(BaseModel):
    """Données pour mettre à jour une expérience existante."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(pending|running|paused|completed|error)$")

class Experiment(ExperimentBase):
    """Expérience complète avec identifiant et métadonnées."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    parameters: AllParameters
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: str = Field("pending", pattern="^(pending|running|paused|completed|error)$")
    created_by: Optional[str] = Field(None, description="Identifiant de l'utilisateur")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SessionBase(BaseModel):
    """Base commune pour une session d'entraînement."""
    experiment_id: str = Field(..., description="ID de l'expérience parente")
    name: str = Field(..., description="Nom de la session", max_length=100)
    algorithm_pacman: str = Field("DQN", description="Algorithme RL pour Pac-Man")
    algorithm_ghosts: str = Field("DQN", description="Algorithme RL pour les fantômes")

class SessionCreate(SessionBase):
    """Données requises pour créer une nouvelle session."""
    pass

class SessionUpdate(BaseModel):
    """Données pour mettre à jour une session existante."""
    name: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, pattern="^(pending|running|paused|completed|error)$")
    current_episode: Optional[int] = Field(None, ge=0)

class Session(SessionBase):
    """Session complète avec identifiant et métadonnées."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: str = Field("pending", pattern="^(pending|running|paused|completed|error)$")
    current_episode: int = Field(0, ge=0)
    total_episodes: int = Field(1000, ge=1)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MetricPoint(BaseModel):
    """Point de métrique pour un épisode donné."""
    episode: int = Field(..., ge=0)
    timestamp: datetime = Field(default_factory=datetime.now)
    value: float = Field(...)
    metric_type: str = Field(..., description="Type de métrique (reward, loss, score, etc.)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TrainingMetrics(BaseModel):
    """Métriques d'entraînement agrégées."""
    session_id: str
    episode_rewards: List[MetricPoint] = Field(default_factory=list)
    episode_lengths: List[MetricPoint] = Field(default_factory=list)
    losses: List[MetricPoint] = Field(default_factory=list)
    exploration_rates: List[MetricPoint] = Field(default_factory=list)
    intelligence_scores: List[MetricPoint] = Field(default_factory=list)
    
    def add_point(self, metric_type: str, episode: int, value: float):
        """Ajoute un point de métrique."""
        point = MetricPoint(
            episode=episode,
            value=value,
            metric_type=metric_type
        )
        if metric_type == "reward":
            self.episode_rewards.append(point)
        elif metric_type == "length":
            self.episode_lengths.append(point)
        elif metric_type == "loss":
            self.losses.append(point)
        elif metric_type == "exploration_rate":
            self.exploration_rates.append(point)
        elif metric_type == "intelligence_score":
            self.intelligence_scores.append(point)
        else:
            raise ValueError(f"Type de métrique inconnu: {metric_type}")

class IntelligenceScore(BaseModel):
    """Score d'intelligence calculé (0-100)."""
    session_id: str
    episode: int
    overall: float = Field(..., ge=0, le=100)
    components: Dict[str, float] = Field(
        description="Scores des composantes (efficacité, survie, évitement, planification, adaptabilité)"
    )
    explanation: Optional[str] = Field(None, description="Explication textuelle du score")

class GameState(BaseModel):
    """État du jeu pour la visualisation."""
    grid: List[List[int]] = Field(..., description="Grille 2D (0: vide, 1: point, 2: power pellet, -1: mur)")
    pacman: Dict[str, Any] = Field(..., description="Position et direction de Pac-Man")
    ghosts: List[Dict[str, Any]] = Field(..., description="Liste des fantômes avec positions et états")
    pellets: List[Dict[str, int]] = Field(..., description="Positions des points restants")
    power_pellets: List[Dict[str, int]] = Field(..., description="Positions des power pellets restants")
    score: int = Field(0, description="Score actuel")
    lives: int = Field(3, description="Vies restantes")
    step: int = Field(0, description="Step actuel dans l'épisode")
    episode: int = Field(0, description="Épisode actuel")

class WebSocketMessage(BaseModel):
    """Message WebSocket standardisé."""
    type: str = Field(..., description="Type de message (game_state, metrics, session_update, error)")
    data: Dict[str, Any] = Field(...)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }