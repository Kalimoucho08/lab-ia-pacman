"""
Calculateur de score d'intelligence pour les agents IA Pac-Man.

Fournit un score composite 0-100 basé sur les performances de l'agent,
avec normalisation et ajustement selon la difficulté de l'environnement.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class EpisodeMetrics:
    """Métriques collectées pour un épisode."""
    episode: int
    reward: float
    steps: int
    win: bool
    pellets_collected: int
    total_pellets: int
    ghosts_eaten: int
    deaths: int
    max_possible_steps: int = 1000  # Valeur par défaut

@dataclass
class IntelligenceComponents:
    """Composantes du score d'intelligence."""
    winrate: float  # 0-1
    reward_normalized: float  # 0-1
    survival_normalized: float  # 0-1
    efficiency: float  # 0-1 (pellets collectés)
    consistency: float  # 0-1 (1 - coefficient de variation)
    learning_trend: float  # -1 à 1 (pente de régression)

class IntelligenceCalculator:
    """Calcule le score d'intelligence à partir des métriques d'épisodes."""
    
    # Poids pour le score composite
    WEIGHTS = {
        'winrate': 0.45,
        'reward': 0.30,
        'survival': 0.25
    }
    
    # Poids pour le score détaillé (radar chart)
    DETAILED_WEIGHTS = {
        'winrate': 0.25,
        'reward': 0.20,
        'survival': 0.15,
        'efficiency': 0.15,
        'consistency': 0.15,
        'learning': 0.10
    }
    
    def __init__(self, baseline_winrate: float = 0.1, baseline_reward: float = -100.0):
        """
        Initialise le calculateur avec les valeurs de baseline.
        
        Args:
            baseline_winrate: Taux de victoire de l'agent aléatoire (0-1)
            baseline_reward: Récompense moyenne de l'agent aléatoire
        """
        self.baseline_winrate = baseline_winrate
        self.baseline_reward = baseline_reward
        
    def calculate_intelligence_score(self, 
                                   episodes: List[EpisodeMetrics],
                                   difficulty_factor: float = 1.0) -> Dict[str, Any]:
        """
        Calcule le score d'intelligence global et ses composantes.
        
        Args:
            episodes: Liste des métriques d'épisodes
            difficulty_factor: Facteur de difficulté (1.0 = normal, >1.0 = plus difficile)
            
        Returns:
            Dictionnaire avec le score global, les composantes et les explications
        """
        if not episodes:
            return self._empty_score()
        
        # Calculer les composantes
        components = self._calculate_components(episodes)
        
        # Calculer le score composite
        composite_score = (
            self.WEIGHTS['winrate'] * components.winrate +
            self.WEIGHTS['reward'] * components.reward_normalized +
            self.WEIGHTS['survival'] * components.survival_normalized
        ) * 100  # Convertir en 0-100
        
        # Calculer le score détaillé (pour radar chart)
        detailed_score = (
            self.DETAILED_WEIGHTS['winrate'] * components.winrate +
            self.DETAILED_WEIGHTS['reward'] * components.reward_normalized +
            self.DETAILED_WEIGHTS['survival'] * components.survival_normalized +
            self.DETAILED_WEIGHTS['efficiency'] * components.efficiency +
            self.DETAILED_WEIGHTS['consistency'] * components.consistency +
            self.DETAILED_WEIGHTS['learning'] * max(0, components.learning_trend)  # Ignorer les tendances négatives
        ) * 100
        
        # Ajuster selon la difficulté
        adjusted_score = self._adjust_for_difficulty(composite_score, difficulty_factor)
        adjusted_detailed = self._adjust_for_difficulty(detailed_score, difficulty_factor)
        
        # Générer l'explication
        explanation = self._generate_explanation(components, adjusted_score, difficulty_factor)
        
        # Recommandations
        recommendations = self._generate_recommendations(components)
        
        return {
            'overall_score': round(adjusted_score, 2),
            'detailed_score': round(adjusted_detailed, 2),
            'components': {
                'winrate': round(components.winrate * 100, 2),
                'reward_normalized': round(components.reward_normalized * 100, 2),
                'survival_normalized': round(components.survival_normalized * 100, 2),
                'efficiency': round(components.efficiency * 100, 2),
                'consistency': round(components.consistency * 100, 2),
                'learning_trend': round(components.learning_trend, 3)
            },
            'raw_metrics': {
                'total_episodes': len(episodes),
                'wins': sum(1 for e in episodes if e.win),
                'avg_reward': np.mean([e.reward for e in episodes]),
                'avg_steps': np.mean([e.steps for e in episodes]),
                'avg_pellets_collected': np.mean([e.pellets_collected for e in episodes])
            },
            'explanation': explanation,
            'recommendations': recommendations,
            'difficulty_factor': difficulty_factor,
            'calculated_at': datetime.now().isoformat()
        }
    
    def _calculate_components(self, episodes: List[EpisodeMetrics]) -> IntelligenceComponents:
        """Calcule toutes les composantes du score d'intelligence."""
        # Winrate
        winrate = sum(1 for e in episodes if e.win) / len(episodes)
        winrate_norm = self._normalize_winrate(winrate)
        
        # Reward normalisé
        rewards = [e.reward for e in episodes]
        reward_norm = self._normalize_reward(np.mean(rewards), np.std(rewards))
        
        # Survie normalisée
        survival_norm = self._normalize_survival(episodes)
        
        # Efficacité (pellets collectés)
        efficiency = self._calculate_efficiency(episodes)
        
        # Consistance (1 - coefficient de variation)
        consistency = self._calculate_consistency(rewards)
        
        # Tendance d'apprentissage
        learning_trend = self._calculate_learning_trend(rewards)
        
        return IntelligenceComponents(
            winrate=winrate_norm,
            reward_normalized=reward_norm,
            survival_normalized=survival_norm,
            efficiency=efficiency,
            consistency=consistency,
            learning_trend=learning_trend
        )
    
    def _normalize_winrate(self, winrate: float) -> float:
        """
        Normalise le winrate par rapport à la baseline.
        
        Formule: (winrate - baseline) / (1 - baseline)
        Résultat clampé entre 0 et 1.
        """
        if winrate <= self.baseline_winrate:
            return 0.0
        
        normalized = (winrate - self.baseline_winrate) / (1 - self.baseline_winrate)
        return max(0.0, min(1.0, normalized))
    
    def _normalize_reward(self, mean_reward: float, std_reward: float) -> float:
        """
        Normalise la récompense moyenne.
        
        Utilise une fonction sigmoïde pour transformer en score 0-1.
        """
        # Récompense de référence (baseline = 0, maximum théorique = 1000)
        baseline = self.baseline_reward
        max_theoretical = 1000.0  # Valeur arbitraire, à ajuster selon l'environnement
        
        # Normalisation linéaire avec clamp
        if mean_reward <= baseline:
            return 0.0
        
