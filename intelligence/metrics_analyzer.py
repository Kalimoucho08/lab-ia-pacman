"""
Analyseur de métriques détaillées pour l'évaluation d'intelligence.

Fournit des analyses statistiques avancées sur les performances de l'agent,
incluant la détection de patterns, l'analyse de tendances et le diagnostic
des faiblesses.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from scipy import stats
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)
logger = logging.getLogger(__name__)

@dataclass
class PerformancePattern:
    """Pattern de performance détecté."""
    name: str
    description: str
    confidence: float  # 0-1
    impact: str  # 'positive', 'negative', 'neutral'

@dataclass
class TrendAnalysis:
    """Analyse de tendance temporelle."""
    slope: float
    intercept: float
    r_squared: float
    significance: float  # p-value
    direction: str  # 'improving', 'declining', 'stable'

@dataclass
class WeaknessDiagnosis:
    """Diagnostic de faiblesse spécifique."""
    category: str
    severity: float  # 0-1
    symptoms: List[str]
    recommendations: List[str]

class MetricsAnalyzer:
    """Analyseur de métriques pour l'évaluation d'intelligence."""
    
    def __init__(self, window_size: int = 50):
        """
        Initialise l'analyseur.
        
        Args:
            window_size: Taille de la fenêtre pour les analyses mobiles
        """
        self.window_size = window_size
    
    def analyze_performance(self, 
                          episodes: List[Dict[str, Any]],
                          agent_type: str = "pacman") -> Dict[str, Any]:
        """
        Analyse complète des performances de l'agent.
        
        Args:
            episodes: Liste des données d'épisodes
            agent_type: Type d'agent ('pacman' ou 'ghost')
            
        Returns:
            Analyse détaillée des performances
        """
        if not episodes:
            return self._empty_analysis()
        
        # Extraire les séries temporelles
        rewards = [e.get('reward', 0.0) for e in episodes]
        steps = [e.get('steps', 0) for e in episodes]
        wins = [e.get('win', False) for e in episodes]
        pellets = [e.get('pellets_collected', 0) for e in episodes]
        total_pellets = episodes[0].get('total_pellets', 1) if episodes else 1
        
        # Analyses de base
        basic_stats = self._calculate_basic_stats(rewards, steps, wins, pellets, total_pellets)
        
        # Analyses avancées
        trend_analysis = self._analyze_trends(rewards, steps, wins)
        patterns = self._detect_patterns(rewards, steps, wins, pellets)
        weaknesses = self._diagnose_weaknesses(rewards, steps, wins, pellets, agent_type)
        consistency = self._analyze_consistency(rewards, steps)
        learning_quality = self._assess_learning_quality(rewards, wins)
        
        # Score de qualité globale
        quality_score = self._calculate_quality_score(
            basic_stats, trend_analysis, consistency, learning_quality
        )
        
        return {
            'basic_statistics': basic_stats,
            'trend_analysis': trend_analysis,
            'detected_patterns': patterns,
            'weakness_diagnosis': weaknesses,
            'consistency_analysis': consistency,
            'learning_quality': learning_quality,
            'overall_quality_score': quality_score,
            'agent_type': agent_type,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_basic_stats(self, 
                              rewards: List[float],
                              steps: List[int],
                              wins: List[bool],
                              pellets: List[int],
                              total_pellets: int) -> Dict[str, Any]:
        """Calcule les statistiques de base."""
        win_rate = np.mean(wins) if wins else 0.0
        avg_reward = np.mean(rewards) if rewards else 0.0
        avg_steps = np.mean(steps) if steps else 0.0
        avg_pellets = np.mean(pellets) if pellets else 0.0
        
        # Efficacité
        efficiency = avg_pellets / total_pellets if total_pellets > 0 else 0.0
        
        # Distribution des récompenses
        reward_std = np.std(rewards) if len(rewards) > 1 else 0.0
        reward_cv = reward_std / avg_reward if avg_reward != 0 else 0.0
        
        # Distribution des steps
        steps_std = np.std(steps) if len(steps) > 1 else 0.0
        
        return {
            'win_rate': float(win_rate),
            'avg_reward': float(avg_reward),
            'avg_steps': float(avg_steps),
            'avg_pellets_collected': float(avg_pellets),
            'efficiency': float(efficiency),
            'reward_std': float(reward_std),
            'reward_coefficient_of_variation': float(reward_cv),
            'steps_std': float(steps_std),
            'total_episodes': len(rewards)
        }
    
    def _analyze_trends(self, 
                       rewards: List[float],
                       steps: List[int],
                       wins: List[bool]) -> Dict[str, Any]:
        """Analyse les tendances temporelles."""
        if len(rewards) < 3:
            return {'error': 'Insufficient data for trend analysis'}
        
        x = np.arange(len(rewards))
        
        # Tendance des récompenses
        reward_trend = self._linear_trend_analysis(x, rewards, 'reward')
        
        # Tendance des steps
        steps_trend = self._linear_trend_analysis(x, steps, 'steps')
        
        # Tendance des victoires (fenêtre mobile)
        if len(wins) >= self.window_size:
            win_rates = self._moving_average([1.0 if w else 0.0 for w in wins], self.window_size)
            win_trend = self._linear_trend_analysis(
                x[:len(win_rates)], win_rates, 'win_rate'
            )
        else:
            win_trend = {'error': f'Need at least {self.window_size} episodes for win trend analysis'}
        
        # Détection de points d'inflexion
        inflection_points = self._detect_inflection_points(rewards)
        
        return {
            'reward_trend': reward_trend,
            'steps_trend': steps_trend,
            'win_trend': win_trend,
            'inflection_points': inflection_points,
            'window_size': self.window_size
        }
    
    def _linear_trend_analysis(self, x: np.ndarray, y: List[float], metric_name: str) -> Dict[str, Any]:
        """Analyse de tendance linéaire."""
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Déterminer la direction
            if abs(slope) < 0.001:
                direction = 'stable'
            elif slope > 0:
                direction = 'improving'
            else:
                direction = 'declining'
            
            # Significativité
            significant = p_value < 0.05
            
            return {
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(r_value ** 2),
                'p_value': float(p_value),
                'significant': significant,
                'direction': direction,
                'metric': metric_name
            }
        except Exception as e:
            logger.warning(f"Erreur dans l'analyse de tendance pour {metric_name}: {e}")
            return {'error': str(e), 'metric': metric_name}
    
    def _detect_inflection_points(self, values: List[float]) -> List[Dict[str, Any]]:
        """Détecte les points d'inflexion dans une série temporelle."""
        if len(values) < 10:
            return []
        
        points = []
        
        # Utiliser une dérivée seconde approchée
        smoothed = self._moving_average(values, 5)
        if len(smoothed) < 3:
            return []
        
        # Calculer la dérivée seconde discrète
        second_deriv = []
        for i in range(1, len(smoothed) - 1):
            deriv2 = smoothed[i+1] - 2*smoothed[i] + smoothed[i-1]
            second_deriv.append(deriv2)
        
        # Détecter les changements de signe
        for i in range(1, len(second_deriv)):
            if second_deriv[i-1] * second_deriv[i] < 0:  # Changement de signe
                points.append({
                    'episode': i + 2,  # Ajuster l'index
                    'value': values[i+2] if i+2 < len(values) else 0.0,
                    'type': 'inflection',
                    'confidence': 0.7
                })
        
        # Détecter les pics et creux locaux
        for i in range(2, len(values) - 2):
            if (values[i] > values[i-1] and values[i] > values[i+1] and
                values[i] > np.mean(values[max(0, i-5):min(len(values), i+5)])):
                points.append({
                    'episode': i,
                    'value': values[i],
                    'type': 'peak',
                    'confidence': 0.8
                })
            elif (values[i] < values[i-1] and values[i] < values[i+1] and
                  values[i] < np.mean(values[max(0, i-5):min(len(values), i+5)])):
                points.append({
                    'episode': i,
                    'value': values[i],
                    'type': 'trough',
                    'confidence': 0.8
                })
        
        return points
    
    def _detect_patterns(self,
                        rewards: List[float],
                        steps: List[int],
                        wins: List[bool],
                        pellets: List[int]) -> List[Dict[str, Any]]:
        """Détecte les patterns de performance intéressants."""
        patterns = []
        
        # Pattern: Plateau d'apprentissage
        if len(rewards) >= 30:
            last_10 = rewards[-10:]
            first_10 = rewards[:10]
            if (np.mean(last_10) - np.mean(first_10)) / (np.std(rewards) + 1e-6) < 0.5:
                patterns.append({
                    'name': 'learning_plateau',
                    'description': 'L\'agent semble avoir atteint un plateau d\'apprentissage',
                    'confidence': 0.6,
                    'impact': 'negative'
                })
        
        # Pattern: Instabilité
        reward_std = np.std(rewards) if rewards else 0.0
        avg_reward = np.mean(rewards) if rewards else 1.0
        if reward_std > abs(avg_reward) * 2:
            patterns.append({
                'name': 'high_instability',
                'description': 'Performances très instables d\'un épisode à l\'autre',
                'confidence': 0.7,
                'impact': 'negative'
            })
        
        # Pattern: Amélioration constante
        if len(rewards) >= 20:
            first_half = rewards[:len(rewards)//2]
            second_half = rewards[len(rewards)//2:]
            if np.mean(second_half) > np.mean(first_half) * 1.5:
                patterns.append({
                    'name': 'consistent_improvement',
                    'description': 'Amélioration constante des performances au fil du temps',
                    'confidence': 0.8,
                    'impact': 'positive'
                })
        
        # Pattern: Mort précoce systématique
        avg_steps = np.mean(steps) if steps else 0.0
        if avg_steps < 50 and len(steps) > 10:
            patterns.append({
                'name': 'early_death_pattern',
                'description': 'L\'agent meurt systématiquement très tôt dans les épisodes',
                'confidence': 0.9,
                'impact': 'negative'
            })
        
        # Pattern: Efficacité de collecte
        if pellets:
            avg_pellets = np.mean(pellets)
            if avg_pellets > 0:
                efficiency_variance = np.std(pellets) / avg_pellets
                if efficiency_variance < 0.1:
                    patterns.append({
                        'name': 'consistent_efficiency',
                        'description': 'Efficacité de collecte très constante',
                        'confidence': 0.7,
                        'impact': 'positive'
                    })
        
        return patterns
    
    def _diagnose_weaknesses(self,
                            rewards: List[float],
                            steps: List[int],
                            wins: List[bool],
                            pellets: List[int],
                            agent_type: str) -> List[Dict[str, Any]]:
        """Diagnostique les faiblesses spécifiques de l'agent."""
        weaknesses = []
        
        # Faiblesse: Taux de victoire bas
        win_rate = np.mean(wins) if wins else 0.0
        if win_rate < 0.2:
            weaknesses.append({
                'category': 'winning_ability',
                'severity': 1.0 - win_rate,
                'symptoms': [
                    f'Taux de victoire très bas ({win_rate*100:.1f}%)',
                    'Stratégie de victoire inefficace'
                ],
                'recommendations': [
                    'Augmenter l\'exploration pour découvrir de meilleures stratégies',
                    'Réviser la fonction de récompense pour mieux récompenser les victoires'
                ]
            })
        
        # Faiblesse: Survie courte
        avg_steps = np.mean(steps) if steps else 0.0
        if avg_steps < 100:
            weaknesses.append({
                'category': 'survival',
                'severity': min(1.0, (100 - avg_steps) / 100),
                'symptoms': [
                    f'Survie moyenne très courte ({avg_steps:.1f} steps)',
                    'Évitement des fantômes inefficace'
                ],
                'recommendations': [
                    'Renforcer l\'apprentissage de l\'évitement',
                    'Ajouter des récompenses négatives pour les morts précoces'
                ]
            })
        
        # Faiblesse: Inconsistance
        if len(rewards) > 5:
            reward_cv = np.std(rewards) / np.mean(rewards) if np.mean(rewards) != 0 else 0.0
            if reward_cv > 1.0:
                weaknesses.append({
                    'category': 'consistency',
                    'severity': min(1.0, reward_cv / 2.0),
                    'symptoms': [
                        f'Variabilité élevée des récompenses (CV={reward_cv:.2f})',
                        'Performances imprévisibles'
                    ],
                    'recommendations': [
                        'Réduire le taux d\'apprentissage',
                        'Augmenter la taille du buffer de replay',
                        'Utiliser un target network plus stable'
                    ]
                })
        
        # Faiblesse: Efficacité de collecte
        if pellets and len(pellets) > 5:
            avg_pellets = np.mean(pellets)
            if avg_pellets < 10:
                weaknesses.append({
                    'category': 'efficiency',
                    'severity': min(1.0, (10 - avg_pellets) / 10),
                    'symptoms': [
                        f'Collecte moyenne faible ({avg_pellets:.1f} pellets)',
                        'Planification de chemin inefficace'
                    ],
                    'recommendations': [
                        'Améliorer l\'exploration pour découvrir tous les pellets',
                        'Ajouter des récompenses pour la collecte de pellets'
                    ]
                })
        
        # Faiblesse spécifique aux fantômes
        if agent_type == 'ghost':
            # Analyser la capacité à capturer Pac-Man
            # (À implémenter avec des métriques spécifiques aux fantômes)
            pass
        
        return weaknesses
    
    def _analyze_consistency(self, rewards: List[float], steps: List[int]) -> Dict[str, Any]:
        """Analyse la consistance des performances."""
        if len(rewards) < 2:
            return {'error': 'Insufficient data for consistency analysis'}
        
        # Coefficient de variation
        reward_cv = np.std(rewards) / np.mean(rewards) if np.mean(rewards) != 0 else 0.0
        steps_cv = np.std(steps) / np.mean(steps) if np.mean(steps) != 0 else 0.0
        
        # Autocorrélation (persistance)
        reward_acf = self._autocorrelation(rewards, lag=1) if len(rewards) > 10 else 0.0
        steps_acf = self._autocorrelation(steps, lag=1) if len(steps) > 10 else 0.0
        
        # Test de stationnarité (approximatif)
        stationarity = self._check_stationarity(rewards)
        
        return {
            'reward_coefficient_of_variation': float(reward_cv),
            'steps_coefficient_of_variation': float(steps_cv),
            'reward_autocorrelation_lag1': float(reward_acf),
            'steps_autocorrelation_lag1': float(steps_acf),
            'stationarity': stationarity
        }
    
    def _assess_learning_quality(self, rewards: List[float], wins: List[bool]) -> Dict[str, Any]:
        """Évalue la qualité de l'apprentissage."""
        if len(rewards) < 10:
            return {'error': 'Insufficient data for learning quality assessment'}
        
        # Tendance d'apprentissage
        x = np.arange(len(rewards))
        slope, _, r_value, p_value, _ = stats.linregress(x, rewards)
        
        # Amélioration relative
        first_quarter = rewards[:len(rewards)//4]
        last_quarter = rewards[-len(rewards)//4:]
        improvement_ratio = np.mean(last_quarter) / np.mean(first_quarter) if np.mean(first_quarter) != 0 else 0.0
        
        # Consistance de l'amélioration
        window_size = max(10, len(rewards) // 10)
        moving_avg = self._moving_average(rewards, window_size)
        if len(moving_avg) > 1:
            moving_slope, _, _, _, _ = stats.linregress(np.arange(len(moving_avg)), moving_avg)
        else:
            moving_slope = 0.0
        
        # Stabilité des victoires
        if len(wins) >= 20:
            win_stability = self._calculate_stability([1.0 if w else 0.0 for w in wins])
        else:
            win_stability = 0.0
        
        return {
            'learning_slope': float(slope),
            'learning_r_squared': float(r_value ** 2),
            'learning_significant': p_value < 0.05,
            'improvement_ratio': float(improvement_ratio),
            'moving_slope': float(moving_slope),
            'win_stability': float(win_stability),
            'learning_quality_score': self._calculate_learning_score(slope, improvement_ratio, win_stability)
        }
    
    def _calculate_quality_score(self, basic_stats: Dict[str, Any],
                               trend_analysis: Dict[str, Any],
                               consistency: Dict[str, Any],
                               learning_quality: Dict[str, Any]) -> float:
        """Calcule un score de qualité globale."""
        scores = []
        
        # Score de performance de base
        win_rate = basic_stats.get('win_rate', 0.0)
        efficiency = basic_stats.get('efficiency', 0.0)
        scores.append(win_rate * 0.4 + efficiency * 0.3)
        
        # Score de tendance
        reward_trend = trend_analysis.get('reward_trend', {})
        if isinstance(reward_trend, dict) and 'direction' in reward_trend:
            if reward_trend['direction'] == 'improving':
                scores.append(0.8)
            elif reward_trend['direction'] == 'stable':
                scores.append(0.5)
            else:
                scores.append(0.2)
        
        # Score de consistance
        reward_cv = consistency.get('reward_coefficient_of_variation', 1.0)
        consistency_score = 1.0 / (1.0 + reward_cv)
        scores.append(consistency_score * 0.5)
        
        # Score d'apprentissage
        learning_score = learning_quality.get('learning_quality_score', 0.5)
        scores.append(learning_score * 0.3)
        
        # Moyenne pondérée
        return float(np.mean(scores) * 100) if scores else 0.0
    
    def _moving_average(self, values: List[float], window: int) -> List[float]:
        """Calcule la moyenne mobile."""
        if len(values) < window:
            return values
        
        result = []
        for i in range(len(values) - window + 1):
            result.append(np.mean(values[i:i+window]))
        return result
    
    def _autocorrelation(self, values: List[float], lag: int = 1) -> float:
        """Calcule l'autocorrélation pour un lag donné."""
        if len(values) <= lag:
            return 0.0
        
        x = np.array(values[:-lag])
        y = np.array(values[lag:])
        
        if len(x) < 2 or len(y) < 2:
            return 0.0
        
        correlation = np.corrcoef(x, y)[0, 1]
        return 0.0 if np.isnan(correlation) else correlation
    
    def _check_stationarity(self, values: List[float]) -> Dict[str, Any]:
        """Vérifie la stationnarité de la série (approximation simple)."""
        if len(values) < 20:
            return {'stationary': False, 'confidence': 0.0}
        
        # Test de stationnarité simplifié
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        mean_diff = abs(np.mean(first_half) - np.mean(second_half))
        std_diff = abs(np.std(first_half) - np.std(second_half))
        
        # Si les différences sont petites, considérer comme stationnaire
        threshold = np.std(values) * 0.5
        stationary = mean_diff < threshold and std_diff < threshold
        
        return {
            'stationary': bool(stationary),
            'confidence': 1.0 - min(1.0, (mean_diff + std_diff) / (threshold * 2)),
            'mean_difference': float(mean_diff),
            'std_difference': float(std_diff)
        }
    
    def _calculate_stability(self, values: List[float]) -> float:
        """Calcule un score de stabilité (0-1)."""
        if len(values) < 2:
            return 0.5
        
        # Utiliser l'inverse du coefficient de variation
        cv = np.std(values) / np.mean(values) if np.mean(values) != 0 else 1.0
        stability = 1.0 / (1.0 + cv)
        return max(0.0, min(1.0, stability))
    
    def _calculate_learning_score(self, slope: float, improvement_ratio: float,
                                win_stability: float) -> float:
        """Calcule un score de qualité d'apprentissage."""
        # Normaliser la pente
        slope_score = min(1.0, max(0.0, slope * 100 + 0.5))
        
        # Score d'amélioration
        improvement_score = min(1.0, improvement_ratio / 2.0)
        
        # Score composite
        return (slope_score * 0.4 + improvement_score * 0.4 + win_stability * 0.2)
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Retourne une analyse vide lorsque aucune donnée n'est disponible."""
        return {
            'basic_statistics': {
                'win_rate': 0.0,
                'avg_reward': 0.0,
                'avg_steps': 0.0,
                'avg_pellets_collected': 0.0,
                'efficiency': 0.0,
                'reward_std': 0.0,
                'reward_coefficient_of_variation': 0.0,
                'steps_std': 0.0,
                'total_episodes': 0
            },
            'trend_analysis': {'error': 'No data available'},
            'detected_patterns': [],
            'weakness_diagnosis': [],
            'consistency_analysis': {'error': 'No data available'},
            'learning_quality': {'error': 'No data available'},
            'overall_quality_score': 0.0,
            'agent_type': 'unknown',
            'analysis_timestamp': datetime.now().isoformat()
        }