"""
Comparateur de baseline pour l'évaluation d'intelligence.

Compare les performances de l'agent avec des baselines prédéfinies
(agent aléatoire, agent simple, état de l'art) et calcule des scores
relatifs d'amélioration.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class BaselineMetrics:
    """Métriques de référence pour une baseline."""
    name: str
    description: str
    win_rate: float
    avg_reward: float
    avg_steps: float
    avg_pellets: float
    efficiency: float
    consistency: float
    difficulty_level: str  # 'easy', 'medium', 'hard'
    environment_params: Dict[str, Any]

@dataclass
class ComparisonResult:
    """Résultat de comparaison avec une baseline."""
    baseline_name: str
    improvement_ratios: Dict[str, float]  # Ratios d'amélioration par métrique
    overall_improvement: float  # Amélioration globale (0-100)
    percentile: float  # Percentile par rapport à la baseline (0-100)
    interpretation: str

class BaselineComparator:
    """Compare les performances de l'agent avec différentes baselines."""
    
    # Baselines prédéfinies
    DEFAULT_BASELINES = {
        'random_agent': BaselineMetrics(
            name='random_agent',
            description='Agent aléatoire (baseline minimale)',
            win_rate=0.05,  # 5% de victoires
            avg_reward=-50.0,
            avg_steps=30.0,
            avg_pellets=5.0,
            efficiency=0.1,
            consistency=0.3,
            difficulty_level='easy',
            environment_params={'grid_size': 10, 'num_ghosts': 2}
        ),
        'simple_heuristic': BaselineMetrics(
            name='simple_heuristic',
            description='Agent avec heuristiques simples (évitement basique)',
            win_rate=0.15,
            avg_reward=20.0,
            avg_steps=80.0,
            avg_pellets=15.0,
            efficiency=0.3,
            consistency=0.5,
            difficulty_level='medium',
            environment_params={'grid_size': 10, 'num_ghosts': 2}
        ),
        'rule_based': BaselineMetrics(
            name='rule_based',
            description='Agent basé sur règles (stratégie déterministe)',
            win_rate=0.35,
            avg_reward=80.0,
            avg_steps=150.0,
            avg_pellets=25.0,
            efficiency=0.5,
            consistency=0.7,
            difficulty_level='medium',
            environment_params={'grid_size': 10, 'num_ghosts': 2}
        ),
        'state_of_the_art': BaselineMetrics(
            name='state_of_the_art',
            description='Meilleures performances rapportées dans la littérature',
            win_rate=0.85,
            avg_reward=300.0,
            avg_steps=250.0,
            avg_pellets=40.0,
            efficiency=0.9,
            consistency=0.9,
            difficulty_level='hard',
            environment_params={'grid_size': 10, 'num_ghosts': 4}
        )
    }
    
    def __init__(self, baseline_data_path: Optional[str] = None):
        """
        Initialise le comparateur avec les baselines.
        
        Args:
            baseline_data_path: Chemin vers un fichier JSON de baselines personnalisées
        """
        self.baselines = self.DEFAULT_BASELINES.copy()
        
        if baseline_data_path and Path(baseline_data_path).exists():
            self._load_custom_baselines(baseline_data_path)
        
        logger.info(f"Comparateur initialisé avec {len(self.baselines)} baselines")
    
    def compare_with_baselines(self,
                             agent_metrics: Dict[str, Any],
                             environment_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare les métriques de l'agent avec toutes les baselines appropriées.
        
        Args:
            agent_metrics: Métriques de l'agent (doit contenir les mêmes champs que BaselineMetrics)
            environment_params: Paramètres de l'environnement pour sélectionner les baselines appropriées
            
        Returns:
            Résultats de comparaison détaillés
        """
        # Sélectionner les baselines pertinentes
        relevant_baselines = self._select_relevant_baselines(environment_params)
        
        if not relevant_baselines:
            logger.warning("Aucune baseline pertinente trouvée")
            return self._empty_comparison()
        
        # Comparer avec chaque baseline
        comparisons = {}
        for baseline_name in relevant_baselines:
            baseline = self.baselines[baseline_name]
            comparison = self._compare_single_baseline(agent_metrics, baseline)
            comparisons[baseline_name] = comparison
        
        # Calculer les statistiques globales
        overall_stats = self._calculate_overall_statistics(comparisons, agent_metrics)
        
        # Générer un rapport synthétique
        summary = self._generate_summary_report(comparisons, overall_stats)
        
        return {
            'agent_metrics': agent_metrics,
            'environment_params': environment_params,
            'comparisons': comparisons,
            'overall_statistics': overall_stats,
            'summary': summary,
            'comparison_timestamp': datetime.now().isoformat()
        }
    
    def _select_relevant_baselines(self, 
                                 environment_params: Dict[str, Any]) -> List[str]:
        """
        Sélectionne les baselines pertinentes selon les paramètres d'environnement.
        
        Priorise les baselines avec des paramètres similaires.
        """
        relevant = []
        
        # Extraire les caractéristiques clés
        grid_size = environment_params.get('grid_size', 10)
        num_ghosts = environment_params.get('num_ghosts', 2)
        difficulty = self._estimate_difficulty_level(grid_size, num_ghosts)
        
        for name, baseline in self.baselines.items():
            # Vérifier la similarité des paramètres
            baseline_grid = baseline.environment_params.get('grid_size', 10)
            baseline_ghosts = baseline.environment_params.get('num_ghosts', 2)
            
            # Calculer un score de similarité
            grid_diff = abs(grid_size - baseline_grid) / max(grid_size, baseline_grid)
            ghosts_diff = abs(num_ghosts - baseline_ghosts) / max(num_ghosts, baseline_ghosts)
            similarity_score = 1.0 - (grid_diff + ghosts_diff) / 2.0
            
            if similarity_score > 0.6:  # Seuil de similarité
                relevant.append(name)
        
        # Si aucune baseline n'est suffisamment similaire, retourner toutes
        if not relevant:
            relevant = list(self.baselines.keys())
        
        # Trier par pertinence (d'abord les plus similaires)
        relevant.sort(key=lambda x: self._calculate_similarity_score(
            environment_params, self.baselines[x].environment_params
        ), reverse=True)
        
        return relevant[:3]  # Limiter à 3 baselines les plus pertinentes
    
    def _compare_single_baseline(self,
                               agent_metrics: Dict[str, Any],
                               baseline: BaselineMetrics) -> ComparisonResult:
        """Compare les métriques de l'agent avec une baseline spécifique."""
        # Calculer les ratios d'amélioration pour chaque métrique
        improvement_ratios = {}
        
        # Win rate (plus c'est haut, mieux c'est)
        agent_win_rate = agent_metrics.get('win_rate', 0.0)
        improvement_ratios['win_rate'] = self._calculate_improvement_ratio(
            agent_win_rate, baseline.win_rate, higher_is_better=True
        )
        
        # Average reward
        agent_reward = agent_metrics.get('avg_reward', 0.0)
        improvement_ratios['avg_reward'] = self._calculate_improvement_ratio(
            agent_reward, baseline.avg_reward, higher_is_better=True
        )
        
        # Average steps (survie)
        agent_steps = agent_metrics.get('avg_steps', 0.0)
        improvement_ratios['avg_steps'] = self._calculate_improvement_ratio(
            agent_steps, baseline.avg_steps, higher_is_better=True
        )
        
        # Efficiency (pellets collectés)
        agent_efficiency = agent_metrics.get('efficiency', 0.0)
        improvement_ratios['efficiency'] = self._calculate_improvement_ratio(
            agent_efficiency, baseline.efficiency, higher_is_better=True
        )
        
        # Consistency
        agent_consistency = agent_metrics.get('consistency', 0.5)
        improvement_ratios['consistency'] = self._calculate_improvement_ratio(
            agent_consistency, baseline.consistency, higher_is_better=True
        )
        
        # Calculer l'amélioration globale (moyenne pondérée)
        weights = {
            'win_rate': 0.3,
            'avg_reward': 0.25,
            'avg_steps': 0.2,
            'efficiency': 0.15,
            'consistency': 0.1
        }
        
        overall_improvement = 0.0
        for metric, ratio in improvement_ratios.items():
            overall_improvement += ratio * weights.get(metric, 0.0)
        
        # Calculer le percentile
        percentile = self._calculate_percentile(overall_improvement, baseline.name)
        
        # Générer l'interprétation
        interpretation = self._generate_interpretation(
            overall_improvement, baseline, improvement_ratios
        )
        
        return ComparisonResult(
            baseline_name=baseline.name,
            improvement_ratios=improvement_ratios,
            overall_improvement=overall_improvement * 100,  # Convertir en pourcentage
            percentile=percentile,
            interpretation=interpretation
        )
    
    def _calculate_improvement_ratio(self,
                                   agent_value: float,
                                   baseline_value: float,
                                   higher_is_better: bool = True) -> float:
        """
        Calcule le ratio d'amélioration par rapport à la baseline.
        
        Retourne 0.0 si égal à la baseline, >0.0 si meilleur, <0.0 si pire.
        Normalisé entre -1.0 et 1.0.
        """
        if baseline_value == 0:
            # Éviter la division par zéro
            if agent_value == 0:
                return 0.0
            elif higher_is_better:
                return 1.0 if agent_value > 0 else -1.0
            else:
                return -1.0 if agent_value > 0 else 1.0
        
        if higher_is_better:
            ratio = (agent_value - baseline_value) / abs(baseline_value)
        else:
            ratio = (baseline_value - agent_value) / abs(baseline_value)
        
        # Limiter le ratio à [-1, 1] pour éviter les valeurs extrêmes
        return max(-1.0, min(1.0, ratio))
    
    def _calculate_percentile(self, improvement_ratio: float, baseline_name: str) -> float:
        """
        Calcule le percentile de l'agent par rapport à la distribution attendue.
        
        Pour l'instant, utilise une fonction sigmoïde pour estimer le percentile.
        Dans une implémentation réelle, on utiliserait des données historiques.
        """
        # Mapping des baselines aux distributions attendues
        baseline_percentiles = {
            'random_agent': (0.0, 0.3),  # (moyenne, écart-type) de la distribution
            'simple_heuristic': (0.2, 0.25),
            'rule_based': (0.5, 0.2),
            'state_of_the_art': (0.8, 0.15)
        }
        
        if baseline_name in baseline_percentiles:
            mean, std = baseline_percentiles[baseline_name]
            # Utiliser la fonction de répartition normale
            z_score = (improvement_ratio - mean) / (std + 1e-6)
            percentile = 1.0 / (1.0 + np.exp(-z_score))  # Approximation sigmoïde
        else:
            # Approximation par défaut
            percentile = (improvement_ratio + 1.0) / 2.0  # Convertir [-1,1] en [0,1]
        
        return max(0.0, min(100.0, percentile * 100))
    
    def _generate_interpretation(self,
                               overall_improvement: float,
                               baseline: BaselineMetrics,
                               improvement_ratios: Dict[str, float]) -> str:
        """Génère une interprétation textuelle de la comparaison."""
        improvement_percent = overall_improvement * 100
        
        # Phrases d'introduction
        if improvement_percent >= 50:
            intro = f"Performance exceptionnelle ! L'agent surpasse significativement "
        elif improvement_percent >= 20:
            intro = f"Bonne performance. L'agent est meilleur que "
        elif improvement_percent >= 0:
            intro = f"Performance similaire à "
        elif improvement_percent >= -20:
            intro = f"Performance légèrement inférieure à "
        else:
            intro = f"Performance nettement inférieure à "
        
        intro += f"la baseline '{baseline.description}'."
        
        # Détails des points forts
        strengths = []
        for metric, ratio in improvement_ratios.items():
            if ratio > 0.3:  # Amélioration significative
                metric_names = {
                    'win_rate': 'taux de victoire',
                    'avg_reward': 'récompenses',
                    'avg_steps': 'survie',
                    'efficiency': 'efficacité de collecte',
                    'consistency': 'consistance'
                }
                strengths.append(f"{metric_names.get(metric, metric)} (+{ratio*100:.0f}%)")
        
        if strengths:
            intro += f" Points forts: {', '.join(strengths)}."
        
        # Détails des points faibles
        weaknesses = []
        for metric, ratio in improvement_ratios.items():
            if ratio < -0.2:  # Dégradation significative
                metric_names = {
                    'win_rate': 'taux de victoire',
                    'avg_reward': 'récompenses',
                    'avg_steps': 'survie',
                    'efficiency': 'efficacité de collecte',
                    'consistency': 'consistance'
                }
                weaknesses.append(f"{metric_names.get(metric, metric)} ({ratio*100:.0f}%)")
        
        if weaknesses:
            intro += f" Points à améliorer: {', '.join(weaknesses)}."
        
        # Recommandation finale
        if improvement_percent >= 30:
            intro += " Continuez sur cette voie, l'agent progresse très bien."
        elif improvement_percent >= 0:
            intro += " Des ajustements mineurs pourraient encore améliorer les performances."
        else:
            intro += " Une révision de la stratégie d'apprentissage est recommandée."
        
        return intro
    
    def _calculate_overall_statistics(self,
                                    comparisons: Dict[str, ComparisonResult],
                                    agent_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule les statistiques globales de comparaison."""
        if not comparisons:
            return {}
        
        # Extraire les améliorations globales
        improvements = [c.overall_improvement for c in comparisons.values()]
        percentiles = [c.percentile for c in comparisons.values()]
        
        # Trouver la meilleure et pire baseline
        best_baseline = max(comparisons.items(), key=lambda x: x[1].overall_improvement)
        worst_baseline = min(comparisons.items(), key=lambda x: x[1].overall_improvement)
        
        # Calculer la distance à l'état de l'art
        state_of_art = comparisons.get('state_of_the_art')
        distance_to_sota = None
        if state_of_art:
            distance_to_sota = 100.0 - state_of_art.percentile
        
        return {
            'avg_improvement': float(np.mean(improvements)),
            'median_improvement': float(np.median(improvements)),
            'std_improvement': float(np.std(improvements)) if len(improvements) > 1 else 0.0,
            'avg_percentile': float(np.mean(percentiles)),
            'best_baseline': {
                'name': best_baseline[0],
                'improvement': float(best_baseline[1].overall_improvement),
                'percentile': float(best_baseline[1].percentile)
            },
            'worst_baseline': {
                'name': worst_baseline[0],
                'improvement': float(worst_baseline[1].overall_improvement),
                'percentile': float(worst_baseline[1].percentile)
            },
            'distance_to_state_of_the_art': distance_to_sota,
            'num_baselines_compared': len(comparisons)
        }
    
    def _generate_summary_report(self,
                               comparisons: Dict[str, ComparisonResult],
                               overall_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un rapport synthétique des comparaisons."""
        if not comparisons:
            return {'error': 'No comparisons available'}
        
        # Classification de performance
        avg_improvement = overall_stats.get('avg_improvement', 0.0)
        
        if avg_improvement >= 40:
            performance_class = 'excellent'
            performance_description = 'Performance exceptionnelle'
        elif avg_improvement >= 20:
            performance_class = 'good'
            performance_description = 'Bonne performance'
        elif avg_improvement >= 0:
            performance_class = 'average'
            performance_description = 'Performance moyenne'
        elif avg_improvement >= -10:
            performance_class = 'below_average'
            performance_description = 'Performance légèrement inférieure à la moyenne'
        else:
            performance_class = 'poor'
            performance_description = 'Performance faible'
        
        # Recommandations basées sur la comparaison
        recommendations = self._generate_recommendations(comparisons, overall_stats)
        
        return {
            'performance_classification': performance_class,
            'performance_description': performance_description,
            'average_improvement': float(avg_improvement),
            'distance_to_state_of_the_art': overall_stats.get('distance_to_state_of_the_art'),
            'best_baseline': overall_stats.get('best_baseline', {}),
            'key_insights': self._extract_key_insights(comparisons),
            'recommendations': recommendations
        }
    
    def _estimate_difficulty_level(self, grid_size: int, num_ghosts: int) -> str:
        """Estime le niveau de difficulté basé sur les paramètres."""
        if grid_size <= 10 and num_ghosts <= 2:
            return 'easy'
        elif grid_size <= 15 and num_ghosts <= 3:
            return 'medium'
        else:
            return 'hard'
    
    def _calculate_similarity_score(self, params1: Dict[str, Any], params2: Dict[str, Any]) -> float:
        """Calcule un score de similarité entre deux ensembles de paramètres."""
        score = 0.0
        total_weight = 0.0
        
        # Comparer les paramètres clés
        key_params = ['grid_size', 'num_ghosts', 'power_pellets', 'pellet_density']
        weights = {'grid_size': 0.3, 'num_ghosts': 0.4, 'power_pellets': 0.2, 'pellet_density': 0.1}
        
        for param in key_params:
            if param in params1 and param in params2:
                val1 = params1[param]
                val2 = params2[param]
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    # Normaliser la différence
                    max_val = max(abs(val1), abs(val2), 1)
                    diff = abs(val1 - val2) / max_val
                    similarity = 1.0 - diff
                    score += similarity * weights.get(param, 0.0)
                    total_weight += weights.get(param, 0.0)
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _load_custom_baselines(self, data_path: str):
        """Charge des baselines personnalisées depuis un fichier JSON."""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for baseline_data in data.get('baselines', []):
                baseline = BaselineMetrics(**baseline_data)
                self.baselines[baseline.name] = baseline
            
            logger.info(f"Baselines personnalisées chargées depuis {data_path}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des baselines personnalisées: {e}")
    
    def _empty_comparison(self) -> Dict[str, Any]:
        """Retourne un résultat de comparaison vide."""
        return {
            'agent_metrics': {},
            'environment_params': {},
            'comparisons': {},
            'overall_statistics': {},
            'summary': {
                'performance_classification': 'unknown',
                'performance_description': 'Données insuffisantes pour la comparaison',
                'average_improvement': 0.0,
                'distance_to_state_of_the_art': None,
                'best_baseline': None,
                'key_insights': [],
                'recommendations': ['Collecter plus de données pour permettre la comparaison']
            },
            'comparison_timestamp': datetime.now().isoformat()
        }
    
    def _extract_key_insights(self, comparisons: Dict[str, ComparisonResult]) -> List[str]:
        """Extrait les insights clés des comparaisons."""
        insights = []
        
        if not comparisons:
            return insights
        
        # Insight sur la performance relative
        improvements = [c.overall_improvement for c in comparisons.values()]
        avg_improvement = np.mean(improvements)
        
        if avg_improvement > 30:
            insights.append("L'agent surpasse significativement la plupart des baselines.")
        elif avg_improvement > 10:
            insights.append("L'agent est compétitif par rapport aux baselines établies.")
        elif avg_improvement < -10:
            insights.append("L'agent a des difficultés à atteindre le niveau des baselines.")
        
        # Insight sur les points forts/faibles
        all_ratios = {}
        for comparison in comparisons.values():
            for metric, ratio in comparison.improvement_ratios.items():
                if metric not in all_ratios:
                    all_ratios[metric] = []
                all_ratios[metric].append(ratio)
        
        # Identifier les métriques les plus fortes et faibles
        avg_ratios = {metric: np.mean(ratios) for metric, ratios in all_ratios.items()}
        strongest = max(avg_ratios.items(), key=lambda x: x[1]) if avg_ratios else None
        weakest = min(avg_ratios.items(), key=lambda x: x[1]) if avg_ratios else None
        
        if strongest and strongest[1] > 0.2:
            metric_names = {
                'win_rate': 'taux de victoire',
                'avg_reward': 'récompenses',
                'avg_steps': 'survie',
                'efficiency': 'efficacité',
                'consistency': 'consistance'
            }
            insights.append(f"Point fort: excellente performance en {metric_names.get(strongest[0], strongest[0])}.")
        
        if weakest and weakest[1] < -0.1:
            metric_names = {
                'win_rate': 'taux de victoire',
                'avg_reward': 'récompenses',
                'avg_steps': 'survie',
                'efficiency': 'efficacité',
                'consistency': 'consistance'
            }
            insights.append(f"Point à améliorer: faible performance en {metric_names.get(weakest[0], weakest[0])}.")
        
        return insights
    
    def _generate_recommendations(self,
                                comparisons: Dict[str, ComparisonResult],
                                overall_stats: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur les résultats de comparaison."""
        recommendations = []
        
        if not comparisons:
            return ["Collecter plus de données avant de faire des recommandations spécifiques."]
        
        # Recommandation basée sur la distance à l'état de l'art
        distance_to_sota = overall_stats.get('distance_to_state_of_the_art')
        if distance_to_sota is not None:
            if distance_to_sota > 50:
                recommendations.append("L'agent est très loin de l'état de l'art. Considérer une approche radicalement différente.")
            elif distance_to_sota > 20:
                recommendations.append("Il reste une marge significative d'amélioration pour atteindre l'état de l'art.")
            elif distance_to_sota <= 10:
                recommendations.append("L'agent est proche de l'état de l'art. Affiner les hyperparamètres pour des gains marginaux.")
        
        # Recommandation basée sur la consistance
        for comparison in comparisons.values():
            consistency_ratio = comparison.improvement_ratios.get('consistency', 0.0)
            if consistency_ratio < -0.1:
                recommendations.append("Améliorer la consistance des performances avec un taux d'apprentissage plus faible.")
                break
        
        # Recommandation basée sur l'efficacité
        for comparison in comparisons.values():
            efficiency_ratio = comparison.improvement_ratios.get('efficiency', 0.0)
            if efficiency_ratio < -0.1:
                recommendations.append("Améliorer l'efficacité de collecte en explorant mieux l'environnement.")
                break
        
        if not recommendations:
            recommendations.append("Continuer l'entraînement actuel, l'agent progresse bien par rapport aux baselines.")
        
        return recommendations[:3]  # Limiter à 3 recommandations principales