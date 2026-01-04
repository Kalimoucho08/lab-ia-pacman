"""
Endpoints API REST pour le système de mesure d'intelligence.

Fournit les opérations pour calculer, analyser et visualiser
les scores d'intelligence des agents IA Pac-Man.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Query, Body
from pydantic import BaseModel, Field

# Import des modules d'intelligence
import sys
import os

# Ajouter le répertoire intelligence au path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

try:
    from intelligence.intelligence_calculator import IntelligenceCalculator, create_episode_metrics_from_backend
    from intelligence.metrics_analyzer import MetricsAnalyzer
    from intelligence.baseline_comparator import BaselineComparator
    from intelligence.difficulty_adjuster import DifficultyAdjuster, EnvironmentDifficulty
    from intelligence.recommendations_generator import RecommendationsGenerator
    from intelligence.visualization_generator import VisualizationGenerator
    INTELLIGENCE_MODULES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Modules d'intelligence non disponibles: {e}")
    INTELLIGENCE_MODULES_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger(__name__)

# Modèles Pydantic pour les requêtes
class EpisodeData(BaseModel):
    """Données d'un épisode pour le calcul d'intelligence."""
    episode: int = Field(..., ge=0, description="Numéro de l'épisode")
    reward: float = Field(..., description="Récompense totale")
    steps: int = Field(..., ge=0, description="Nombre de steps")
    win: bool = Field(..., description="Victoire (True) ou défaite (False)")
    pellets_collected: int = Field(..., ge=0, description="Pellets collectés")
    total_pellets: int = Field(..., ge=1, description="Pellets totaux disponibles")
    ghosts_eaten: int = Field(0, ge=0, description="Fantômes mangés")
    deaths: int = Field(0, ge=0, description="Nombre de morts")
    max_steps: int = Field(1000, ge=1, description="Steps maximum possibles")

class IntelligenceCalculationRequest(BaseModel):
    """Requête pour le calcul d'intelligence."""
    episodes: List[EpisodeData] = Field(..., description="Liste des données d'épisodes")
    environment_params: Dict[str, Any] = Field(
        default_factory=lambda: {
            "grid_size": 10,
            "num_ghosts": 2,
            "power_pellets": 2,
            "pellet_density": 0.7
        },
        description="Paramètres de l'environnement"
    )
    agent_type: str = Field("pacman", description="Type d'agent ('pacman' ou 'ghost')")
    baseline_winrate: float = Field(0.1, ge=0, le=1, description="Taux de victoire de baseline")
    baseline_reward: float = Field(-100.0, description="Récompense de baseline")

class EnvironmentParams(BaseModel):
    """Paramètres d'environnement pour l'ajustement de difficulté."""
    grid_size: int = Field(10, ge=5, le=30, description="Taille de la grille")
    num_ghosts: int = Field(2, ge=1, le=8, description="Nombre de fantômes")
    power_pellets: int = Field(2, ge=0, le=8, description="Nombre de power pellets")
    pellet_density: float = Field(0.7, ge=0.1, le=1.0, description="Densité de pellets")
    ghost_speed: float = Field(1.0, ge=0.5, le=2.0, description="Vitesse des fantômes")
    pacman_speed: float = Field(1.0, ge=0.5, le=2.0, description="Vitesse de Pac-Man")
    episode_time_limit: int = Field(1000, ge=500, le=2000, description="Limite de temps par épisode")

@router.get("/health")
async def intelligence_health_check():
    """Vérifie que le système d'intelligence est opérationnel."""
    if not INTELLIGENCE_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modules d'intelligence non disponibles"
        )
    
    return {
        "status": "healthy",
        "modules_available": True,
        "message": "Système de mesure d'intelligence opérationnel"
    }

@router.post("/calculate", response_model=Dict[str, Any])
async def calculate_intelligence_score(
    request: IntelligenceCalculationRequest = Body(...)
):
    """
    Calcule le score d'intelligence à partir des données d'épisodes.
    
    Retourne le score composite, les composantes détaillées et les explications.
    """
    if not INTELLIGENCE_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modules d'intelligence non disponibles"
        )
    
    try:
        # Convertir les données d'épisodes
        episode_dicts = [episode.dict() for episode in request.episodes]
        episodes = create_episode_metrics_from_backend(episode_dicts)
        
        # Initialiser le calculateur
        calculator = IntelligenceCalculator(
            baseline_winrate=request.baseline_winrate,
            baseline_reward=request.baseline_reward
        )
        
        # Calculer le facteur de difficulté
        env_params = request.environment_params
        difficulty_adjuster = DifficultyAdjuster()
        env_difficulty = EnvironmentDifficulty(
            grid_size=env_params.get("grid_size", 10),
            num_ghosts=env_params.get("num_ghosts", 2),
            power_pellets=env_params.get("power_pellets", 2),
            pellet_density=env_params.get("pellet_density", 0.7),
            ghost_speed=env_params.get("ghost_speed", 1.0),
            pacman_speed=env_params.get("pacman_speed", 1.0),
            episode_time_limit=env_params.get("episode_time_limit", 1000)
        )
        
        difficulty_factor = difficulty_adjuster.calculate_difficulty_factor(env_difficulty)
        
        # Calculer le score d'intelligence
        intelligence_result = calculator.calculate_intelligence_score(
            episodes=episodes,
            difficulty_factor=difficulty_factor
        )
        
        # Analyser les métriques
        analyzer = MetricsAnalyzer()
        metrics_result = analyzer.analyze_performance(
            episodes=episode_dicts,
            agent_type=request.agent_type
        )
        
        # Comparer avec les baselines
        baseline_comparator = BaselineComparator()
        baseline_result = baseline_comparator.compare_with_baselines(
            agent_metrics=metrics_result['basic_statistics'],
            environment_params=env_params
        )
        
        # Générer des recommandations
        recommendations_generator = RecommendationsGenerator()
        recommendations_result = recommendations_generator.generate_recommendations(
            intelligence_score=intelligence_result,
            metrics_analysis=metrics_result,
            baseline_comparison=baseline_result,
            difficulty_profile=difficulty_adjuster.create_difficulty_profile(env_difficulty)
        )
        
        # Générer les visualisations
        visualization_generator = VisualizationGenerator()
        visualizations_result = visualization_generator.generate_intelligence_dashboard(
            intelligence_score=intelligence_result,
            metrics_analysis=metrics_result,
            baseline_comparison=baseline_result,
            recommendations=recommendations_result
        )
        
        return {
            "intelligence_score": intelligence_result,
            "metrics_analysis": metrics_result,
            "baseline_comparison": baseline_result,
            "recommendations": recommendations_result,
            "visualizations": visualizations_result,
            "summary": {
                "overall_score": intelligence_result['overall_score'],
                "performance_level": _classify_performance_level(intelligence_result['overall_score']),
                "key_strengths": _extract_key_strengths(intelligence_result),
                "key_weaknesses": _extract_key_weaknesses(intelligence_result),
                "improvement_potential": recommendations_result.get('total_potential_impact', 0.0)
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul d'intelligence: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul d'intelligence: {str(e)}"
        )

@router.post("/analyze-metrics", response_model=Dict[str, Any])
async def analyze_metrics(
    episodes: List[Dict[str, Any]] = Body(..., description="Données d'épisodes"),
    agent_type: str = Body("pacman", description="Type d'agent")
):
    """
    Analyse détaillée des métriques de performance.
    
    Retourne des statistiques, tendances, patterns et diagnostics.
    """
    if not INTELLIGENCE_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modules d'intelligence non disponibles"
        )
    
    try:
        analyzer = MetricsAnalyzer()
        result = analyzer.analyze_performance(episodes, agent_type)
        return result
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse des métriques: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse des métriques: {str(e)}"
        )

@router.post("/compare-baselines", response_model=Dict[str, Any])
async def compare_with_baselines(
    agent_metrics: Dict[str, Any] = Body(..., description="Métriques de l'agent"),
    environment_params: Dict[str, Any] = Body(..., description="Paramètres d'environnement")
):
    """
    Compare les performances de l'agent avec des baselines prédéfinies.
    
    Retourne des ratios d'amélioration, percentiles et interprétations.
    """
    if not INTELLIGENCE_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modules d'intelligence non disponibles"
        )
    
    try:
        comparator = BaselineComparator()
        result = comparator.compare_with_baselines(agent_metrics, environment_params)
        return result
    except Exception as e:
        logger.error(f"Erreur lors de la comparaison avec baselines: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la comparaison avec baselines: {str(e)}"
        )

@router.post("/adjust-difficulty", response_model=Dict[str, Any])
async def adjust_difficulty_score(
    raw_score: float = Body(..., ge=0, le=100, description="Score brut (0-100)"),
    environment_params: EnvironmentParams = Body(...),
    adjustment_type: str = Body("multiplicative", description="Type d'ajustement")
):
    """
    Ajuste un score d'intelligence selon la difficulté de l'environnement.
    
    Retourne le score ajusté, le facteur de difficulté et une explication.
    """
    if not INTELLIGENCE_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modules d'intelligence non disponibles"
        )
    
    try:
        adjuster = DifficultyAdjuster()
        env_difficulty = EnvironmentDifficulty(
            grid_size=environment_params.grid_size,
            num_ghosts=environment_params.num_ghosts,
            power_pellets=environment_params.power_pellets,
            pellet_density=environment_params.pellet_density,
            ghost_speed=environment_params.ghost_speed,
            pacman_speed=environment_params.pacman_speed,
            episode_time_limit=environment_params.episode_time_limit
        )
        
        result = adjuster.adjust_intelligence_score(
            raw_score=raw_score,
            env=env_difficulty,
            adjustment_type=adjustment_type
        )
        return result
    except Exception as e:
        logger.error(f"Erreur lors de l'ajustement de difficulté: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'ajustement de difficulté: {str(e)}"
        )

@router.post("/generate-recommendations", response_model=Dict[str, Any])
async def generate_recommendations(
    intelligence_score: Dict[str, Any] = Body(..., description="Score d'intelligence"),
    metrics_analysis: Dict[str, Any] = Body(..., description="Analyse des métriques"),
    baseline_comparison: Dict[str, Any] = Body(..., description="Comparaison avec baselines"),
    difficulty_profile: Dict[str, Any] = Body(..., description="Profil de difficulté")
):
    """
    Génère des recommandations personnalisées pour améliorer l'agent.
    
    Retourne des recommandations prioritaires avec plans d'action.
    """
    if not INTELLIGENCE_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modules d'intelligence non disponibles"
        )
    
    try:
        generator = RecommendationsGenerator()
        result = generator.generate_recommendations(
            intelligence_score=intelligence_score,
            metrics_analysis=metrics_analysis,
            baseline_comparison=baseline_comparison,
            difficulty_profile=difficulty_profile
        )
        return result
    except Exception as e:
        logger.error(f"Erreur lors de la génération de recommandations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération de recommandations: {str(e)}"
        )

@router.post("/generate-visualizations", response_model=Dict[str, Any])
async def generate_visualizations(
    intelligence_score: Dict[str, Any] = Body(..., description="Score d'intelligence"),
    metrics_analysis: Dict[str, Any] = Body(..., description="Analyse des métriques"),
    baseline_comparison: Dict[str, Any] = Body(..., description="Comparaison avec baselines"),
    recommendations: Dict[str, Any] = Body(..., description="Recommandations générées")
):
    """
    Génère les données pour les visualisations du dashboard d'intelligence.
    
    Retourne les données structurées pour radar charts, séries temporelles, etc.
    """
    if not INTELLIGENCE_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modules d'intelligence non disponibles"
        )
    
    try:
        generator = VisualizationGenerator()
        result = generator.generate_intelligence_dashboard(
            intelligence_score=intelligence_score,
            metrics_analysis=metrics_analysis,
            baseline_comparison=baseline_comparison,
            recommendations=recommendations
        )
        return result
    except Exception as e:
        logger.error(f"Erreur lors de la génération de visualisations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération de visualisations: {str(e)}"
        )

@router.get("/baselines", response_model=Dict[str, Any])
async def list_available_baselines():
    """
    Liste toutes les baselines disponibles pour la comparaison.
    
    Retourne les métriques de référence pour chaque baseline.
    """
    if not INTELLIGENCE_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modules d'intelligence non disponibles"
        )
    
    try:
        comparator = BaselineComparator()
        # Exposer les baselines via une méthode publique si elle existe
        # Pour l'instant, retourner un message
        return {
            "baselines": ["random_agent", "simple_heuristic", "rule_based", "state_of_the_art"],
            "description": "Baselines prédéfinies pour la comparaison de performance",
            "count": 4
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des baselines: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des baselines: {str(e)}"
        )

# Fonctions utilitaires
def _classify_performance_level(score: float) -> str:
    """Classe le niveau de performance."""
    if score >= 80:
        return "excellent"
    elif score >= 60:
        return "good"
    elif score >= 40:
        return "average"
    elif score >= 20:
        return "poor"
    else:
        return "very_poor"

def _extract_key_strengths(intelligence_result: Dict[str, Any]) -> List[str]:
    """Extrait les points forts à partir du résultat d'intelligence."""
    strengths = []
    components = intelligence_result.get('components', {})
    
    for component, value in components.items():
        if value >= 70:  # Seuil pour point fort
            if component == 'winrate':
                strengths.append(f"Taux de victoire élevé ({value:.1f}%)")
            elif component == 'reward_normalized':
                strengths.append(f"Récompenses importantes ({value:.1f}%)")
            elif component == 'survival_normalized':
                strengths.append(f"Bonne survie ({value:.1f}%)")
            elif component == 'efficiency':
                strengths.append(f"Efficacité de collecte élevée ({value:.1f}%)")
            elif component == 'consistency':
                strengths.append(f"Consistance excellente ({value:.1f}%)")
    
    return strengths if strengths else ["Aucun point fort significatif identifié"]

def _extract_key_weaknesses(intelligence_result: Dict[str, Any]) -> List[str]:
    """Extrait les points faibles à partir du résultat d'intelligence."""
    weaknesses = []
    components = intelligence_result.get('components', {})
    
    for component, value in components.items():
        if value <= 30:  # Seuil pour point faible
            if component == 'winrate':
                weaknesses.append(f"Taux de victoire faible ({value:.1f}%)")
            elif component == 'reward_normalized':
                weaknesses.append(f"Récompenses insuffisantes ({value:.1f}%)")
            elif component == 'survival_normalized':
                weaknesses.append(f"Survie courte ({value:.1f}%)")
            elif component == 'efficiency':
                weaknesses.append(f"Efficacité de collecte faible ({value:.1f}%)")
            elif component == 'consistency':
                weaknesses.append(f"Manque de consistance ({value:.1f}%)")
    
    return weaknesses if weaknesses else ["Aucun point faible significatif identifié"]
