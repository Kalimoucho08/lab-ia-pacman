"""
Ajusteur de difficulté pour la normalisation des scores d'intelligence.

Ajuste les scores d'intelligence selon la difficulté de l'environnement,
en tenant compte de paramètres comme la taille de la grille, le nombre
de fantômes, la densité de pellets, etc.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import math

logger = logging.getLogger(__name__)

@dataclass
class EnvironmentDifficulty:
    """Caractéristiques de difficulté d'un environnement."""
    grid_size: int
    num_ghosts: int
    power_pellets: int
    pellet_density: float
    ghost_speed: float = 1.0
    pacman_speed: float = 1.0
    episode_time_limit: int = 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            'grid_size': self.grid_size,
            'num_ghosts': self.num_ghosts,
            'power_pellets': self.power_pellets,
            'pellet_density': self.pellet_density,
            'ghost_speed': self.ghost_speed,
            'pacman_speed': self.pacman_speed,
            'episode_time_limit': self.episode_time_limit
        }

class DifficultyAdjuster:
    """Ajuste les scores selon la difficulté de l'environnement."""
    
    # Paramètres de référence pour la difficulté "normale" (facteur = 1.0)
    REFERENCE_ENVIRONMENT = EnvironmentDifficulty(
        grid_size=10,
        num_ghosts=2,
        power_pellets=2,
        pellet_density=0.7,
        ghost_speed=1.0,
        pacman_speed=1.0,
        episode_time_limit=1000
    )
    
    # Poids des différents facteurs de difficulté
    DIFFICULTY_WEIGHTS = {
        'grid_size': 0.15,
        'num_ghosts': 0.35,
        'power_pellets': 0.10,
        'pellet_density': 0.10,
        'ghost_speed': 0.15,
        'pacman_speed': 0.10,
        'episode_time_limit': 0.05
    }
    
    # Plages de valeurs pour la normalisation
    VALUE_RANGES = {
        'grid_size': (5, 30),
        'num_ghosts': (1, 8),
        'power_pellets': (0, 8),
        'pellet_density': (0.1, 1.0),
        'ghost_speed': (0.5, 2.0),
        'pacman_speed': (0.5, 2.0),
        'episode_time_limit': (500, 2000)
    }
    
    def __init__(self, reference_env: Optional[EnvironmentDifficulty] = None):
        """
        Initialise l'ajusteur de difficulté.
        
        Args:
            reference_env: Environnement de référence (difficulté normale)
        """
        self.reference_env = reference_env or self.REFERENCE_ENVIRONMENT
        logger.info(f"Ajusteur de difficulté initialisé avec référence: {self.reference_env}")
    
    def calculate_difficulty_factor(self, env: EnvironmentDifficulty) -> float:
        """
        Calcule un facteur de difficulté pour un environnement donné.
        
        Args:
            env: Environnement à évaluer
            
        Returns:
            Facteur de difficulté (>1.0 = plus difficile, <1.0 = plus facile)
        """
        # Calculer les scores de difficulté individuels
        difficulty_scores = {}
        
        # Taille de la grille (plus grande = plus difficile)
        grid_score = self._calculate_grid_difficulty(env.grid_size)
        difficulty_scores['grid_size'] = grid_score
        
        # Nombre de fantômes (plus nombreux = plus difficile)
        ghosts_score = self._calculate_ghosts_difficulty(env.num_ghosts)
        difficulty_scores['num_ghosts'] = ghosts_score
        
        # Power pellets (moins nombreux = plus difficile)
        pellets_score = self._calculate_power_pellets_difficulty(env.power_pellets)
        difficulty_scores['power_pellets'] = pellets_score
        
        # Densité de pellets (plus faible = plus difficile)
        density_score = self._calculate_pellet_density_difficulty(env.pellet_density)
        difficulty_scores['pellet_density'] = density_score
        
        # Vitesse des fantômes (plus rapide = plus difficile)
        ghost_speed_score = self._calculate_speed_difficulty(
            env.ghost_speed, is_ghost=True
        )
        difficulty_scores['ghost_speed'] = ghost_speed_score
        
        # Vitesse de Pac-Man (plus lente = plus difficile)
        pacman_speed_score = self._calculate_speed_difficulty(
            env.pacman_speed, is_ghost=False
        )
        difficulty_scores['pacman_speed'] = pacman_speed_score
        
        # Limite de temps (plus courte = plus difficile)
        time_score = self._calculate_time_limit_difficulty(env.episode_time_limit)
        difficulty_scores['episode_time_limit'] = time_score
        
        # Calculer le facteur de difficulté global
        total_weight = sum(self.DIFFICULTY_WEIGHTS.values())
        weighted_sum = 0.0
        
        for factor, weight in self.DIFFICULTY_WEIGHTS.items():
            if factor in difficulty_scores:
                weighted_sum += difficulty_scores[factor] * weight
        
        difficulty_factor = weighted_sum / total_weight if total_weight > 0 else 1.0
        
        # Ajuster pour que 1.0 soit la référence
        reference_factor = self.calculate_difficulty_factor(self.reference_env)
        if reference_factor != 0:
            difficulty_factor = difficulty_factor / reference_factor
        
        logger.debug(f"Facteur de difficulté calculé: {difficulty_factor:.2f}")
        return max(0.5, min(3.0, difficulty_factor))  # Limiter à une plage raisonnable
    
    def adjust_intelligence_score(self,
                                raw_score: float,
                                env: EnvironmentDifficulty,
                                adjustment_type: str = "multiplicative") -> Dict[str, Any]:
        """
        Ajuste un score d'intelligence brut selon la difficulté.
        
        Args:
            raw_score: Score brut (0-100)
            env: Environnement dans lequel le score a été obtenu
            adjustment_type: Type d'ajustement ('multiplicative', 'additive', 'exponential')
            
        Returns:
            Dictionnaire avec le score ajusté et les détails de l'ajustement
        """
        difficulty_factor = self.calculate_difficulty_factor(env)
        
        # Appliquer l'ajustement
        if adjustment_type == "multiplicative":
            adjusted_score = raw_score * difficulty_factor
        elif adjustment_type == "additive":
            # Ajustement additif basé sur l'écart à la référence
            adjustment = (difficulty_factor - 1.0) * 20  # 20 points max d'ajustement
            adjusted_score = raw_score + adjustment
        elif adjustment_type == "exponential":
            # Ajustement exponentiel (plus sensible aux hautes difficultés)
            adjustment = math.exp(difficulty_factor - 1.0)
            adjusted_score = raw_score * adjustment
        else:
            logger.warning(f"Type d'ajustement inconnu: {adjustment_type}, utilisation de multiplicative")
            adjusted_score = raw_score * difficulty_factor
        
        # Limiter le score à 0-100
        adjusted_score = max(0.0, min(100.0, adjusted_score))
        
        # Calculer le bonus/malus
        bonus = adjusted_score - raw_score
        
        # Générer une explication
        explanation = self._generate_adjustment_explanation(
            raw_score, adjusted_score, difficulty_factor, env
        )
        
        return {
            'raw_score': round(raw_score, 2),
            'adjusted_score': round(adjusted_score, 2),
            'difficulty_factor': round(difficulty_factor, 3),
            'adjustment_type': adjustment_type,
            'bonus_malus': round(bonus, 2),
            'environment_difficulty': env.to_dict(),
            'explanation': explanation,
            'adjustment_timestamp': datetime.now().isoformat()
        }
    
    def compare_environments(self,
                           env1: EnvironmentDifficulty,
                           env2: EnvironmentDifficulty) -> Dict[str, Any]:
        """
        Compare la difficulté de deux environnements.
        
        Args:
            env1: Premier environnement
            env2: Deuxième environnement
            
        Returns:
            Comparaison détaillée des difficultés
        """
        factor1 = self.calculate_difficulty_factor(env1)
        factor2 = self.calculate_difficulty_factor(env2)
        
        ratio = factor2 / factor1 if factor1 != 0 else 0.0
        
        # Déterminer la relation
        if ratio > 1.5:
            relation = "beaucoup plus difficile"
        elif ratio > 1.1:
            relation = "plus difficile"
        elif ratio > 0.9:
            relation = "similaire en difficulté"
        elif ratio > 0.67:
            relation = "plus facile"
        else:
            relation = "beaucoup plus facile"
        
        # Analyser les différences par facteur
        differences = []
        for factor_name in self.DIFFICULTY_WEIGHTS.keys():
            val1 = getattr(env1, factor_name, 0)
            val2 = getattr(env2, factor_name, 0)
            
            if val1 != val2:
                diff_pct = (val2 - val1) / max(abs(val1), 1) * 100
                differences.append({
                    'factor': factor_name,
                    'env1_value': val1,
                    'env2_value': val2,
                    'difference_pct': round(diff_pct, 1)
                })
        
        return {
            'env1_difficulty_factor': round(factor1, 3),
            'env2_difficulty_factor': round(factor2, 3),
            'difficulty_ratio': round(ratio, 3),
            'relation': relation,
            'differences': differences,
            'comparison_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_grid_difficulty(self, grid_size: int) -> float:
        """Calcule la difficulté liée à la taille de la grille."""
        min_size, max_size = self.VALUE_RANGES['grid_size']
        
        # Normaliser entre 0 et 1
        normalized = (grid_size - min_size) / (max_size - min_size)
        
        # Plus la grille est grande, plus c'est difficile (fonction quadratique)
        difficulty = 0.5 + normalized * 0.5  # 0.5 à 1.0
        
        return max(0.5, min(2.0, difficulty))
    
    def _calculate_ghosts_difficulty(self, num_ghosts: int) -> float:
        """Calcule la difficulté liée au nombre de fantômes."""
        min_ghosts, max_ghosts = self.VALUE_RANGES['num_ghosts']
        
        # Normaliser entre 0 et 1
        normalized = (num_ghosts - min_ghosts) / (max_ghosts - min_ghosts)
        
        # Les fantômes ajoutent une difficulté exponentielle
        difficulty = 0.5 + math.exp(normalized * 1.5) / math.exp(1.5) * 0.5
        
        return max(0.5, min(2.5, difficulty))
    
    def _calculate_power_pellets_difficulty(self, power_pellets: int) -> float:
        """Calcule la difficulté liée aux power pellets."""
        min_pellets, max_pellets = self.VALUE_RANGES['power_pellets']
        
        if max_pellets == min_pellets:
            return 1.0
        
        # Normaliser entre 0 et 1 (inversé: moins de pellets = plus difficile)
        normalized = (max_pellets - power_pellets) / (max_pellets - min_pellets)
        
        # Difficulté linéaire inversée
        difficulty = 0.7 + normalized * 0.6  # 0.7 à 1.3
        
        return max(0.5, min(2.0, difficulty))
    
    def _calculate_pellet_density_difficulty(self, density: float) -> float:
        """Calcule la difficulté liée à la densité de pellets."""
        min_density, max_density = self.VALUE_RANGES['pellet_density']
        
        if max_density == min_density:
            return 1.0
        
        # Normaliser entre 0 et 1 (inversé: moins dense = plus difficile)
        normalized = (max_density - density) / (max_density - min_density)
        
        # Difficulté quadratique inversée
        difficulty = 0.8 + normalized * 0.7  # 0.8 à 1.5
        
        return max(0.5, min(2.0, difficulty))
    
    def _calculate_speed_difficulty(self, speed: float, is_ghost: bool) -> float:
        """Calcule la difficulté liée à la vitesse."""
        min_speed, max_speed = self.VALUE_RANGES['ghost_speed' if is_ghost else 'pacman_speed']
        
        if max_speed == min_speed:
            return 1.0
        
        # Normaliser entre 0 et 1
        normalized = (speed - min_speed) / (max_speed - min_speed)
        
        if is_ghost:
            # Fantômes plus rapides = plus difficile
            difficulty = 0.6 + normalized * 0.8  # 0.6 à 1.4
        else:
            # Pac-Man plus lent = plus difficile (inversé)
            difficulty = 0.8 + (1 - normalized) * 0.6  # 0.8 à 1.4
        
        return max(0.5, min(2.0, difficulty))
    
    def _calculate_time_limit_difficulty(self, time_limit: int) -> float:
        """Calcule la difficulté liée à la limite de temps."""
        min_time, max_time = self.VALUE_RANGES['episode_time_limit']
        
        if max_time == min_time:
            return 1.0
        
        # Normaliser entre 0 et 1 (inversé: moins de temps = plus difficile)
        normalized = (max_time - time_limit) / (max_time - min_time)
        
        # Difficulté linéaire inversée
        difficulty = 0.9 + normalized * 0.4  # 0.9 à 1.3
        
        return max(0.5, min(2.0, difficulty))
    
    def _generate_adjustment_explanation(self,
                                       raw_score: float,
                                       adjusted_score: float,
                                       difficulty_factor: float,
                                       env: EnvironmentDifficulty) -> str:
        """Génère une explication de l'ajustement."""
        explanation_parts = []
        
        # Description de la difficulté
        if difficulty_factor > 1.5:
            explanation_parts.append("Environnement très difficile")
        elif difficulty_factor > 1.2:
            explanation_parts.append("Environnement difficile")
        elif difficulty_factor > 0.9:
            explanation_parts.append("Environnement de difficulté normale")
        elif difficulty_factor > 0.7:
            explanation_parts.append("Environnement assez facile")
        else:
            explanation_parts.append("Environnement très facile")
        
        # Facteurs contributifs
        factors = []
        if env.grid_size > self.reference_env.grid_size:
            factors.append(f"grille plus grande ({env.grid_size})")
        if env.num_ghosts > self.reference_env.num_ghosts:
            factors.append(f"plus de fantômes ({env.num_ghosts})")
        if env.power_pellets < self.reference_env.power_pellets:
            factors.append(f"moins de power pellets ({env.power_pellets})")
        if env.pellet_density < self.reference_env.pellet_density:
            factors.append(f"densité de pellets plus faible ({env.pellet_density:.2f})")
        
        if factors:
            explanation_parts.append(f"en raison de: {', '.join(factors)}.")
        else:
            explanation_parts.append(".")
        
        # Effet de l'ajustement
        bonus = adjusted_score - raw_score
        if bonus > 5:
            explanation_parts.append(f"Un bonus de {bonus:.1f} points a été appliqué pour récompenser la performance dans des conditions difficiles.")
        elif bonus < -5:
            explanation_parts.append(f"Un malus de {abs(bonus):.1f} points a été appliqué car l'environnement est plus facile que la référence.")
        else:
            explanation_parts.append("L'ajustement de difficulté est mineur.")
        
        # Score final
        explanation_parts.append(f"Score final ajusté: {adjusted_score:.1f}/100 (score brut: {raw_score:.1f}).")
        
        return " ".join(explanation_parts)
    
    def create_difficulty_profile(self, env: EnvironmentDifficulty) -> Dict[str, Any]:
        """
        Crée un profil de difficulté détaillé pour un environnement.
        
        Args:
            env: Environnement à analyser
            
        Returns:
            Profil de difficulté avec scores par facteur
        """
        profile = {}
        
        # Calculer les scores individuels
        for factor_name in self.DIFFICULTY_WEIGHTS.keys():
            value = getattr(env, factor_name, 0)
            reference_value = getattr(self.reference_env, factor_name, 0)
            
            # Calculer le score de difficulté
            if factor_name == 'grid_size':
                score = self._calculate_grid_difficulty(value)
            elif factor_name == 'num_ghosts':
                score = self._calculate_ghosts_difficulty(value)
            elif factor_name == 'power_pellets':
                score = self._calculate_power_pellets_difficulty(value)
            elif factor_name == 'pellet_density':
                score = self._calculate_pellet_density_difficulty(value)
            elif factor_name == 'ghost_speed':
                score = self._calculate_speed_difficulty(value, is_ghost=True)
            elif factor_name == 'pacman_speed':
                score = self._calculate_speed_difficulty(value, is_ghost=False)
            elif factor_name == 'episode_time_limit':
                score = self._calculate_time_limit_difficulty(value)
            else:
                score = 1.0
            
            profile[factor_name] = {
                'value': value,
                'reference_value': reference_value,
                'difficulty_score': round(score, 3),
                'contribution': round(score * self.DIFFICULTY_WEIGHTS.get(factor_name, 0.0), 3)
            }
        
        # Calculer le facteur global
        difficulty_factor = self.calculate_difficulty_factor(env)
        
        # Classification
        if difficulty_factor >= 1.8:
            classification = 'extreme'
        elif difficulty_factor >= 1.4:
            classification = 'hard'
        elif difficulty_factor >= 1.1:
            classification = 'challenging'
        elif difficulty_factor >= 0.9:
            classification = 'normal'
        elif difficulty_factor >= 0.7:
            classification = 'easy'
        else:
            classification = 'very_easy'
        
        profile['overall'] = {
            'difficulty_factor': round(difficulty_factor, 3),
            'classification': classification,
            'description': self._get_difficulty_description(classification)
        }
        
        return profile
    
    def _get_difficulty_description(self, classification: str) -> str:
        """Retourne une description textuelle de la classification."""
        descriptions = {
            'extreme': 'Difficulté extrême - Environnement très exigeant nécessitant des stratégies avancées',
            'hard': 'Difficulté élevée - Défi significatif même pour des agents expérimentés',
            'challenging': 'Difficile - Environnement stimulant avec des obstacles notables',
            'normal': 'Difficulté normale - Équilibre entre challenge et accessibilité',
            'easy': 'Facile - Environnement accessible pour les débutants',
            'very_easy': 'Très facile - Environnement simplifié pour l\'apprentissage de base'
        }
        return descriptions.get(classification, 'Difficulté non classée')
    
    def recommend_difficulty_adjustment(self,
                                      current_env: EnvironmentDifficulty,
                                      target_performance: float = 70.0,
                                      current_performance: Optional[float] = None) -> Dict[str, Any]:
        """
        Recommande des ajustements de difficulté pour atteindre une performance cible.
        
        Args:
            current_env: Environnement actuel
            target_performance: Performance cible (0-100)
            current_performance: Performance actuelle (si connue)
            
        Returns:
            Recommandations d'ajustement
        """
        current_factor = self.calculate_difficulty_factor(current_env)
        
        recommendations = []
        
        # Si la performance actuelle est fournie, calculer l'ajustement nécessaire
        if current_performance is not None:
            performance_ratio = target_performance / current_performance if current_performance > 0 else 1.0
            
            # Ajuster la difficulté en fonction du ratio de performance
            if performance_ratio > 1.2:
                # Performance trop faible, réduire la difficulté
                recommendations.append("Réduire la difficulté pour permettre à l'agent d'atteindre la performance cible.")
                target_factor = current_factor / performance_ratio
            elif performance_ratio < 0.8:
                # Performance trop élevée, augmenter la difficulté
                recommendations.append("Augmenter la difficulté pour maintenir un défi approprié.")
                target_factor = current_factor / performance_ratio
            else:
                recommendations.append("La difficulté actuelle est appropriée pour la performance cible.")
                target_factor = current_factor
        else:
            # Pas de performance connue, utiliser des recommandations générales
            if current_factor > 1.5:
                recommendations.append("L'environnement est très difficile. Considérer réduire le nombre de fantômes ou la taille de la grille.")
            elif current_factor < 0.8:
                recommendations.append("L'environnement est très facile. Considérer augmenter le nombre de fantômes ou réduire les power pellets.")
            else:
                recommendations.append("La difficulté actuelle est bien équilibrée.")
            
            target_factor = current_factor
        
        # Recommandations spécifiques par facteur
        specific_recommendations = []
        
        if current_env.num_ghosts > 4:
            specific_recommendations.append(f"Réduire le nombre de fantômes de {current_env.num_ghosts} à {max(2, current_env.num_ghosts - 2)}")
        
        if current_env.grid_size > 15:
            specific_recommendations.append(f"Réduire la taille de la grille de {current_env.grid_size} à {max(10, current_env.grid_size - 5)}")
        
        if current_env.power_pellets < 1:
            specific_recommendations.append(f"Augmenter le nombre de power pellets de {current_env.power_pellets} à {current_env.power_pellets + 2}")
        
        if specific_recommendations:
            recommendations.extend(specific_recommendations)
        
        return {
            'current_difficulty_factor': round(current_factor, 3),
            'target_difficulty_factor': round(target_factor, 3) if 'target_factor' in locals() else None,
            'recommendations': recommendations,
            'current_environment': current_env.to_dict(),
            'target_performance': target_performance,
            'current_performance': current_performance,
            'recommendation_timestamp': datetime.now().isoformat()
        }