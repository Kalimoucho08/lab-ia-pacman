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
        
        normalized = (mean_reward - baseline) / (max_theoretical - baseline)
        
        # Appliquer une fonction sigmoïde pour pénaliser la variance
        if std_reward > 0:
            penalty = 1.0 / (1.0 + np.exp((std_reward - 50) / 20))  # Pénalise les fortes variances
            normalized *= penalty
        
        return max(0.0, min(1.0, normalized))
    
    def _normalize_survival(self, episodes: List[EpisodeMetrics]) -> float:
        """
        Normalise la survie moyenne.
        
        Survie = steps / max_possible_steps, moyenné sur tous les épisodes.
        """
        survival_ratios = []
        for episode in episodes:
            if episode.max_possible_steps > 0:
                ratio = episode.steps / episode.max_possible_steps
                survival_ratios.append(ratio)
        
        if not survival_ratios:
            return 0.0
        
        avg_survival = np.mean(survival_ratios)
        return max(0.0, min(1.0, avg_survival))
    
    def _calculate_efficiency(self, episodes: List[EpisodeMetrics]) -> float:
        """Calcule l'efficacité de collecte des pellets."""
        efficiencies = []
        for episode in episodes:
            if episode.total_pellets > 0:
                efficiency = episode.pellets_collected / episode.total_pellets
                efficiencies.append(efficiency)
        
        if not efficiencies:
            return 0.0
        
        return np.mean(efficiencies)
    
    def _calculate_consistency(self, rewards: List[float]) -> float:
        """Calcule la consistance (1 - coefficient de variation)."""
        if len(rewards) < 2 or np.mean(rewards) == 0:
            return 0.5  # Valeur par défaut
        
        cv = np.std(rewards) / np.mean(rewards)  # Coefficient de variation
        consistency = 1.0 / (1.0 + cv)  # Transforme en score 0-1
        return max(0.0, min(1.0, consistency))
    
    def _calculate_learning_trend(self, rewards: List[float]) -> float:
        """Calcule la tendance d'apprentissage (pente de régression linéaire)."""
        if len(rewards) < 3:
            return 0.0
        
        # Utiliser une régression linéaire simple
        x = np.arange(len(rewards))
        y = np.array(rewards)
        
        # Calculer la pente
        A = np.vstack([x, np.ones(len(x))]).T
        slope, _ = np.linalg.lstsq(A, y, rcond=None)[0]
        
        # Normaliser la pente
        max_slope = np.std(y) * 2  # Pente maximale attendue
        if max_slope == 0:
            return 0.0
        
        normalized_slope = slope / max_slope
        return max(-1.0, min(1.0, normalized_slope))
    
    def _adjust_for_difficulty(self, score: float, difficulty_factor: float) -> float:
        """
        Ajuste le score selon la difficulté de l'environnement.
        
        Args:
            score: Score original (0-100)
            difficulty_factor: Facteur de difficulté (>1 = plus difficile)
            
        Returns:
            Score ajusté (0-100)
        """
        if difficulty_factor <= 1.0:
            return score
        
        # Formule d'ajustement: score * (1 + log(difficulty_factor))
        # Cela récompense les performances dans des environnements difficiles
        adjustment = 1.0 + np.log(difficulty_factor) / 10.0
        adjusted = score * adjustment
        
        return min(100.0, adjusted)
    
    def _generate_explanation(self, components: IntelligenceComponents, 
                            score: float, difficulty_factor: float) -> str:
        """Génère une explication textuelle du score."""
        explanations = []
        
        # Évaluation globale
        if score >= 80:
            explanations.append("Performance exceptionnelle ! L'agent démontre une intelligence avancée.")
        elif score >= 60:
            explanations.append("Bonne performance. L'agent montre une compréhension solide du jeu.")
        elif score >= 40:
            explanations.append("Performance moyenne. L'agent a des bases mais peut s'améliorer.")
        elif score >= 20:
            explanations.append("Performance faible. L'agent a du mal avec les mécaniques de base.")
        else:
            explanations.append("Performance très faible. L'agent ne comprend pas le jeu.")
        
        # Points forts
        strengths = []
        if components.winrate >= 0.7:
            strengths.append("taux de victoire élevé")
        if components.reward_normalized >= 0.7:
            strengths.append("récompenses importantes")
        if components.survival_normalized >= 0.7:
            strengths.append("bonne survie")
        if components.efficiency >= 0.7:
            strengths.append("efficacité de collecte")
        
        if strengths:
            explanations.append(f"Points forts: {', '.join(strengths)}.")
        
        # Points faibles
        weaknesses = []
        if components.winrate <= 0.3:
            weaknesses.append("taux de victoire bas")
        if components.reward_normalized <= 0.3:
            weaknesses.append("récompenses faibles")
        if components.survival_normalized <= 0.3:
            weaknesses.append("survie limitée")
        if components.consistency <= 0.3:
            weaknesses.append("inconsistance")
        
        if weaknesses:
            explanations.append(f"Points à améliorer: {', '.join(weaknesses)}.")
        
        # Tendance d'apprentissage
        if components.learning_trend > 0.1:
            explanations.append("L'agent montre une nette amélioration au fil du temps.")
        elif components.learning_trend < -0.1:
            explanations.append("Attention: l'agent régresse au lieu de s'améliorer.")
        
        # Difficulté
        if difficulty_factor > 1.5:
            explanations.append(f"Performance remarquable compte tenu de la difficulté élevée (facteur: {difficulty_factor:.1f}x).")
        
        return " ".join(explanations)
    
    def _generate_recommendations(self, components: IntelligenceComponents) -> List[str]:
        """Génère des recommandations pour améliorer l'agent."""
        recommendations = []
        
        if components.winrate < 0.5:
            recommendations.append("Augmenter l'exploration pour découvrir de meilleures stratégies.")
        
        if components.reward_normalized < 0.5:
            recommendations.append("Ajuster la fonction de récompense pour mieux guider l'apprentissage.")
        
        if components.survival_normalized < 0.5:
            recommendations.append("Renforcer l'apprentissage de l'évitement des fantômes.")
        
        if components.efficiency < 0.5:
            recommendations.append("Améliorer la planification du chemin pour collecter plus de pellets.")
        
        if components.consistency < 0.5:
            recommendations.append("Stabiliser l'apprentissage avec un taux d'apprentissage plus faible.")
        
        if components.learning_trend < 0:
            recommendations.append("Réviser les hyperparamètres, l'agent régresse au lieu de progresser.")
        
        if not recommendations:
            recommendations.append("Continuer l'entraînement actuel, l'agent progresse bien.")
        
        return recommendations
    
    def _empty_score(self) -> Dict[str, Any]:
        """Retourne un score vide lorsque aucune donnée n'est disponible."""
        return {
            'overall_score': 0.0,
            'detailed_score': 0.0,
            'components': {
                'winrate': 0.0,
                'reward_normalized': 0.0,
                'survival_normalized': 0.0,
                'efficiency': 0.0,
                'consistency': 0.0,
                'learning_trend': 0.0
            },
            'raw_metrics': {
                'total_episodes': 0,
                'wins': 0,
                'avg_reward': 0.0,
                'avg_steps': 0.0,
                'avg_pellets_collected': 0.0
            },
            'explanation': "Aucune donnée disponible pour calculer le score d'intelligence.",
            'recommendations': ["Collecter des données d'entraînement pour évaluer l'agent."],
            'difficulty_factor': 1.0,
            'calculated_at': datetime.now().isoformat()
        }


# Fonction utilitaire pour créer des EpisodeMetrics à partir des données du backend
def create_episode_metrics_from_backend(episode_data: List[Dict[str, Any]]) -> List[EpisodeMetrics]:
    """
    Convertit les données d'épisode du backend en objets EpisodeMetrics.
    
    Args:
        episode_data: Liste de dictionnaires avec les clés:
            - episode: numéro d'épisode
            - reward: récompense totale
            - steps: nombre de steps
            - win: booléen de victoire
            - pellets_collected: pellets collectés
            - total_pellets: pellets totaux
            - ghosts_eaten: fantômes mangés
            - deaths: morts
            - max_steps: steps maximum possibles (optionnel)
            
    Returns:
        Liste d'objets EpisodeMetrics
    """
    episodes = []
    for data in episode_data:
        episode = EpisodeMetrics(
            episode=data.get('episode', 0),
            reward=data.get('reward', 0.0),
            steps=data.get('steps', 0),
            win=data.get('win', False),
            pellets_collected=data.get('pellets_collected', 0),
            total_pellets=data.get('total_pellets', 1),
            ghosts_eaten=data.get('ghosts_eaten', 0),
            deaths=data.get('deaths', 0),
            max_possible_steps=data.get('max_steps', data.get('max_possible_steps', 1000))
        )
        episodes.append(episode)
    
    return episodes