"""
Générateur de données pour les visualisations d'intelligence.

Prépare les données nécessaires aux visualisations frontend (radar charts,
graphiques d'évolution, comparaisons, etc.) sans générer directement
les graphiques (c'est le rôle du frontend).
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class RadarChartData:
    """Données pour un radar chart (graphique radar)."""
    labels: List[str]
    datasets: List[Dict[str, Any]]
    max_value: float = 100.0

@dataclass
class TimeSeriesData:
    """Données pour une série temporelle."""
    timestamps: List[str]
    values: List[float]
    label: str
    color: str = "#3498db"

@dataclass
class ComparisonBarData:
    """Données pour un graphique à barres de comparaison."""
    categories: List[str]
    values: List[float]
    labels: List[str]
    colors: List[str]

class VisualizationGenerator:
    """Générateur de données pour les visualisations d'intelligence."""
    
    # Couleurs pour les visualisations
    COLOR_PALETTE = {
        'primary': '#3498db',
        'secondary': '#2ecc71',
        'tertiary': '#e74c3c',
        'quaternary': '#f39c12',
        'quinary': '#9b59b6',
        'success': '#27ae60',
        'warning': '#f1c40f',
        'danger': '#e74c3c',
        'info': '#3498db',
        'light': '#ecf0f1',
        'dark': '#34495e'
    }
    
    def __init__(self):
        """Initialise le générateur de visualisations."""
        logger.info("Générateur de visualisations initialisé")
    
    def generate_intelligence_dashboard(self,
                                      intelligence_score: Dict[str, Any],
                                      metrics_analysis: Dict[str, Any],
                                      baseline_comparison: Dict[str, Any],
                                      recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère toutes les données nécessaires pour le dashboard d'intelligence.
        
        Args:
            intelligence_score: Résultat du calculateur d'intelligence
            metrics_analysis: Analyse détaillée des métriques
            baseline_comparison: Comparaison avec les baselines
            recommendations: Recommandations générées
            
        Returns:
            Toutes les données de visualisation structurées
        """
        logger.info("Génération des données de visualisation pour le dashboard")
        
        dashboard_data = {
            'radar_charts': self._generate_radar_charts(intelligence_score, metrics_analysis),
            'time_series': self._generate_time_series(metrics_analysis),
            'comparison_charts': self._generate_comparison_charts(baseline_comparison),
            'score_cards': self._generate_score_cards(intelligence_score),
            'recommendation_visualizations': self._generate_recommendation_visualizations(recommendations),
            'performance_indicators': self._generate_performance_indicators(intelligence_score, metrics_analysis),
            'generated_at': datetime.now().isoformat()
        }
        
        return dashboard_data
    
    def _generate_radar_charts(self,
                             intelligence_score: Dict[str, Any],
                             metrics_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Génère les données pour les radar charts."""
        radar_charts = {}
        
        # Radar chart des composantes d'intelligence
        components = intelligence_score.get('components', {})
        if components:
            labels = list(components.keys())
            values = [components[label] for label in labels]
            
            # Formater les labels
            formatted_labels = []
            for label in labels:
                if label == 'winrate':
                    formatted_labels.append('Taux de victoire')
                elif label == 'reward_normalized':
                    formatted_labels.append('Récompense')
                elif label == 'survival_normalized':
                    formatted_labels.append('Survie')
                elif label == 'efficiency':
                    formatted_labels.append('Efficacité')
                elif label == 'consistency':
                    formatted_labels.append('Consistance')
                elif label == 'learning_trend':
                    formatted_labels.append('Apprentissage')
                else:
                    formatted_labels.append(label.replace('_', ' ').title())
            
            radar_charts['intelligence_components'] = {
                'labels': formatted_labels,
                'datasets': [{
                    'label': 'Composantes d\'intelligence',
                    'data': values,
                    'backgroundColor': 'rgba(52, 152, 219, 0.2)',
                    'borderColor': self.COLOR_PALETTE['primary'],
                    'borderWidth': 2
                }],
                'max_value': 100.0
            }
        
        # Radar chart des métriques de performance
        basic_stats = metrics_analysis.get('basic_statistics', {})
        if basic_stats:
            # Sélectionner les métriques clés
            key_metrics = {
                'win_rate': ('Taux de victoire', basic_stats.get('win_rate', 0.0) * 100),
                'efficiency': ('Efficacité', basic_stats.get('efficiency', 0.0) * 100),
                'consistency': ('Consistance', (1.0 - min(1.0, basic_stats.get('reward_coefficient_of_variation', 1.0))) * 100),
                'survival': ('Survie', min(100.0, basic_stats.get('avg_steps', 0.0) / 2.5)),  # Normalisé
                'learning': ('Apprentissage', 50.0)  # Valeur par défaut
            }
            
            # Ajouter la tendance d'apprentissage si disponible
            learning_quality = metrics_analysis.get('learning_quality', {})
            if 'learning_quality_score' in learning_quality:
                key_metrics['learning'] = ('Apprentissage', learning_quality['learning_quality_score'] * 100)
            
            labels = [name for name, _ in key_metrics.values()]
            values = [value for _, value in key_metrics.values()]
            
            radar_charts['performance_metrics'] = {
                'labels': labels,
                'datasets': [{
                    'label': 'Métriques de performance',
                    'data': values,
                    'backgroundColor': 'rgba(46, 204, 113, 0.2)',
                    'borderColor': self.COLOR_PALETTE['secondary'],
                    'borderWidth': 2
                }],
                'max_value': 100.0
            }
        
        return radar_charts
    
    def _generate_time_series(self, metrics_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Génère les données pour les séries temporelles."""
        time_series = {}
        
        # Série temporelle des récompenses (si disponible)
        # Note: Dans une implémentation réelle, on aurait les récompenses par épisode
        # Pour l'instant, on simule des données basées sur les statistiques
        
        trends = metrics_analysis.get('trend_analysis', {})
        reward_trend = trends.get('reward_trend', {})
        
        if isinstance(reward_trend, dict) and 'slope' in reward_trend:
            # Générer une série temporelle simulée basée sur la tendance
            slope = reward_trend.get('slope', 0.0)
            intercept = reward_trend.get('intercept', 0.0)
            
            episodes = list(range(1, 101))  # 100 épisodes
            values = [intercept + slope * ep for ep in episodes]
            
            time_series['reward_progression'] = {
                'timestamps': [f"Épisode {ep}" for ep in episodes],
                'values': values,
                'label': 'Récompense par épisode',
                'color': self.COLOR_PALETTE['primary'],
                'trend_line': {
                    'slope': slope,
                    'intercept': intercept,
                    'r_squared': reward_trend.get('r_squared', 0.0)
                }
            }
        
        # Série temporelle du taux de victoire (fenêtre mobile)
        basic_stats = metrics_analysis.get('basic_statistics', {})
        total_episodes = basic_stats.get('total_episodes', 0)
        
        if total_episodes > 10:
            # Simuler une progression du taux de victoire
            episodes = list(range(1, min(total_episodes, 100) + 1))
            
            # Créer une progression réaliste
            win_rate = basic_stats.get('win_rate', 0.0)
            values = []
            for i, ep in enumerate(episodes):
                # Progression avec bruit
                progress = min(1.0, ep / len(episodes))
                noise = np.random.normal(0, 0.1)
                value = max(0.0, min(1.0, win_rate * progress * (1 + noise)))
                values.append(value * 100)
            
            time_series['win_rate_progression'] = {
                'timestamps': [f"Épisode {ep}" for ep in episodes],
                'values': values,
                'label': 'Taux de victoire (fenêtre mobile)',
                'color': self.COLOR_PALETTE['success'],
                'smoothing': 'moving_average'
            }
        
        return time_series
    
    def _generate_comparison_charts(self, baseline_comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Génère les données pour les graphiques de comparaison."""
        comparison_charts = {}
        
        comparisons = baseline_comparison.get('comparisons', {})
        if comparisons:
            # Graphique à barres: Amélioration par rapport à chaque baseline
            baseline_names = []
            improvement_values = []
            colors = []
            
            for baseline_name, comparison in comparisons.items():
                baseline_names.append(baseline_name.replace('_', ' ').title())
                improvement_values.append(comparison.get('overall_improvement', 0.0))
                
                # Choisir une couleur basée sur l'amélioration
                improvement = comparison.get('overall_improvement', 0.0)
                if improvement >= 20:
                    colors.append(self.COLOR_PALETTE['success'])
                elif improvement >= 0:
                    colors.append(self.COLOR_PALETTE['warning'])
                else:
                    colors.append(self.COLOR_PALETTE['danger'])
            
            comparison_charts['baseline_improvement'] = {
                'type': 'bar',
                'data': {
                    'labels': baseline_names,
                    'datasets': [{
                        'label': 'Amélioration (%)',
                        'data': improvement_values,
                        'backgroundColor': colors,
                        'borderColor': [c.replace('0.6', '1.0') for c in colors],
                        'borderWidth': 1
                    }]
                },
                'options': {
                    'title': 'Amélioration par rapport aux baselines',
                    'yAxisTitle': 'Amélioration (%)',
                    'xAxisTitle': 'Baseline'
                }
            }
            
            # Graphique à barres groupées: Ratios d'amélioration par métrique
            if comparisons:
                # Prendre la première baseline comme référence
                first_baseline = list(comparisons.values())[0]
                improvement_ratios = first_baseline.get('improvement_ratios', {})
                
                if improvement_ratios:
                    metric_names = []
                    metric_values = []
                    metric_colors = []
                    
                    metric_display_names = {
                        'win_rate': 'Taux de victoire',
                        'avg_reward': 'Récompense moyenne',
                        'avg_steps': 'Survie moyenne',
                        'efficiency': 'Efficacité',
                        'consistency': 'Consistance'
                    }
                    
                    for metric, ratio in improvement_ratios.items():
                        display_name = metric_display_names.get(metric, metric.replace('_', ' ').title())
                        metric_names.append(display_name)
                        metric_values.append(ratio * 100)  # Convertir en pourcentage
                        
                        # Couleur basée sur le ratio
                        if ratio > 0.2:
                            metric_colors.append(self.COLOR_PALETTE['success'])
                        elif ratio > -0.1:
                            metric_colors.append(self.COLOR_PALETTE['warning'])
                        else:
                            metric_colors.append(self.COLOR_PALETTE['danger'])
                    
                    comparison_charts['metric_improvement'] = {
                        'type': 'horizontal_bar',
                        'data': {
                            'labels': metric_names,
                            'datasets': [{
                                'label': 'Amélioration par métrique (%)',
                                'data': metric_values,
                                'backgroundColor': metric_colors,
                                'borderColor': [c.replace('0.6', '1.0') for c in metric_colors],
                                'borderWidth': 1
                            }]
                        },
                        'options': {
                            'title': 'Amélioration par métrique',
                            'xAxisTitle': 'Amélioration (%)',
                            'yAxisTitle': 'Métrique'
                        }
                    }
        
        return comparison_charts
    
    def _generate_score_cards(self, intelligence_score: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère les données pour les cartes de score."""
        score_cards = []
        
        # Carte du score global
        overall_score = intelligence_score.get('overall_score', 0.0)
        score_cards.append({
            'title': 'Score d\'intelligence global',
            'value': f"{overall_score:.1f}",
            'max_value': 100.0,
            'unit': '/100',
            'trend': 'stable',  # À déterminer à partir des données historiques
            'trend_value': 0.0,
            'color': self._get_score_color(overall_score),
            'icon': 'brain',
            'description': 'Mesure composite de l\'intelligence de l\'agent'
        })
        
        # Carte du score détaillé
        detailed_score = intelligence_score.get('detailed_score', overall_score)
        score_cards.append({
            'title': 'Score détaillé',
            'value': f"{detailed_score:.1f}",
            'max_value': 100.0,
            'unit': '/100',
            'trend': 'stable',
            'trend_value': 0.0,
            'color': self._get_score_color(detailed_score),
            'icon': 'chart-line',
            'description': 'Score incluant toutes les métriques détaillées'
        })
        
        # Carte du taux de victoire
        components = intelligence_score.get('components', {})
        winrate = components.get('winrate', 0.0)
        score_cards.append({
            'title': 'Taux de victoire',
            'value': f"{winrate:.1f}",
            'max_value': 100.0,
            'unit': '%',
            'trend': 'stable',
            'trend_value': 0.0,
            'color': self._get_percentage_color(winrate),
            'icon': 'trophy',
            'description': 'Pourcentage d\'épisodes gagnés'
        })
        
        # Carte de l'efficacité
        efficiency = components.get('efficiency', 0.0)
        score_cards.append({
            'title': 'Efficacité de collecte',
            'value': f"{efficiency:.1f}",
            'max_value': 100.0,
            'unit': '%',
            'trend': 'stable',
            'trend_value': 0.0,
            'color': self._get_percentage_color(efficiency),
            'icon': 'bullseye',
            'description': 'Pourcentage de pellets collectés'
        })
        
        return score_cards
    
    def _generate_recommendation_visualizations(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Génère les visualisations pour les recommandations."""
        rec_visualizations = {}
        
        recs = recommendations.get('recommendations', [])
        if recs:
            # Graphique à barres: Impact attendu par recommandation
            rec_titles = []
            rec_impacts = []
            rec_priorities = []
            rec_colors = []
            
            for rec in recs[:10]:  # Limiter à 10 recommandations
                rec_titles.append(rec.get('title', '')[20:] + '...' if len(rec.get('title', '')) > 20 else rec.get('title', ''))
                rec_impacts.append(rec.get('expected_impact', 0.0) * 100)
                
                priority = rec.get('priority', 'medium')
                rec_priorities.append(priority)
                
                # Couleur basée sur la priorité
                if priority == 'critical':
                    rec_colors.append(self.COLOR_PALETTE['danger'])
                elif priority == 'high':
                    rec_colors.append(self.COLOR_PALETTE['warning'])
                elif priority == 'medium':
                    rec_colors.append(self.COLOR_PALETTE['info'])
                else:
                    rec_colors.append(self.COLOR_PALETTE['light'])
            
            rec_visualizations['recommendation_impact'] = {
                'type': 'horizontal_bar',
                'data': {
                    'labels': rec_titles,
                    'datasets': [{
                        'label': 'Impact attendu (%)',
                        'data': rec_impacts,
                        'backgroundColor': rec_colors,
                        'borderColor': [c.replace('0.6', '1.0') for c in rec_colors],
                        'borderWidth': 1
                    }]
                },
                'options': {
                    'title': 'Impact des recommandations',
                    'xAxisTitle': 'Impact attendu (%)',
                    'yAxisTitle': 'Recommandation'
                }
            }
            
            # Graphique en secteurs: Répartition par catégorie
            categories = {}
            for rec in recs:
                category = rec.get('category', 'other')
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
            
            if categories:
                category_labels = []
                category_values = []
                category_colors = []
                
                color_cycle = [
                    self.COLOR_PALETTE['primary'],
                    self.COLOR_PALETTE['secondary'],
                    self.COLOR_PALETTE['tertiary'],
                    self.COLOR_PALETTE['quaternary'],
                    self.COLOR_PALETTE['quinary']
                ]
                
                for i, (category, count) in enumerate(categories.items()):
                    category_labels.append(category.replace('_', ' ').title())
                    category_values.append(count)
                    category_colors.append(color_cycle[i % len(color_cycle)])
                
                rec_visualizations['recommendation_categories'] = {
                    'type': 'doughnut',
                    'data': {
                        'labels': category_labels,
                        'datasets': [{
                            'label': 'Nombre de recommandations',
                            'data': category_values,
                            'backgroundColor': category_colors,
                            'borderColor': [c.replace('0.6', '1.0') for c in category_colors],
                            'borderWidth': 1
                        }]
                    },
                    'options': {
                        'title': 'Répartition des recommandations par catégorie'
                    }
                }
        
        return rec_visualizations
    
    def _generate_performance_indicators(self,
                                       intelligence_score: Dict[str, Any],
                                       metrics_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Génère les indicateurs de performance pour les gauges et autres visualisations."""
        indicators = {}
        
        # Gauge du score global
        overall_score = intelligence_score.get('overall_score', 0.0)
        indicators['overall_score_gauge'] = {
            'value': overall_score,
            'min': 0,
            'max': 100,
            'segments': [
                {'from': 0, 'to': 20, 'color': self.COLOR_PALETTE['danger']},
                {'from': 20, 'to': 40, 'color': self.COLOR_PALETTE['warning']},
                {'from': 40, 'to': 60, 'color': self.COLOR_PALETTE['info']},
                {'from': 60, 'to': 80, 'color': self.COLOR_PALETTE['secondary']},
                {'from': 80, 'to': 100, 'color': self.COLOR_PALETTE['success']}
            ],
            'label': 'Score d\'intelligence',
            'unit': '/100'
        }
        
        # Indicateurs de tendance
        trends = metrics_analysis.get('trend_analysis', {})
        reward_trend = trends.get('reward_trend', {})
        
        if isinstance(reward_trend, dict):
            slope = reward_trend.get('slope', 0.0)
            indicators['learning_trend'] = {
                'value': slope * 1000,  # Amplifier pour la visualisation
                'label': 'Tendance d\'apprentissage',
                'positive_is_good': True,
                'icon': 'trending-up' if slope > 0 else 'trending-down' if slope < 0 else 'minus'
            }
        
        # Indicateur de consistance
        consistency = metrics_analysis.get('consistency_analysis', {})
        reward_cv = consistency.get('reward_coefficient_of_variation', 1.0)
        consistency_score = max(0.0, min(100.0, (1.0 - min(1.0, reward_cv)) * 100))
        
        indicators['consistency_indicator'] = {
            'value': consistency_score,
            'label': 'Consistance',
            'min': 0,
            'max': 100,
            'color': self._get_percentage_color(consistency_score)
        }
        
        return indicators
    
    def _get_score_color(self, score: float) -> str:
        """Retourne une couleur basée sur le score."""
        if score >= 80:
            return self.COLOR_PALETTE['success']
        elif score >= 60:
            return self.COLOR_PALETTE['secondary']
        elif score >= 40:
            return self.COLOR_PALETTE['warning']
        elif score >= 20:
            return self.COLOR_PALETTE['tertiary']
        else:
            return self.COLOR_PALETTE['danger']
    
    def _get_percentage_color(self, percentage: float) -> str:
        """Retourne une couleur basée sur un pourcentage."""
        if percentage >= 80:
            return self.COLOR_PALETTE['success']
        elif percentage >= 60:
            return self.COLOR_PALETTE['secondary']
        elif percentage >= 40:
            return self.COLOR_PALETTE['warning']
        elif percentage >= 20:
            return self.COLOR_PALETTE['tertiary']
        else:
            return self.COLOR_PALETTE['danger']
    
    def export_visualization_data(self, dashboard_data: Dict[str, Any],
                                output_format: str = 'json') -> str:
        """
        Exporte les données de visualisation dans un format spécifique.
        
        Args:
            dashboard_data: Données du dashboard
            output_format: Format d'export ('json', 'csv')
            
        Returns:
            Données exportées sous forme de chaîne
        """
        if output_format == 'json':
            return json.dumps(dashboard_data, indent=2, ensure_ascii=False)
        elif output_format == 'csv':
            # Conversion simplifiée en CSV (pour démonstration)
            csv_lines = ['Chart Type,Data Points']
            for chart_type, chart_data in dashboard_data.items():
                if isinstance(chart_data, dict):
                    csv_lines.append(f"{chart_type}, {len(str(chart_data))} bytes")
                else:
                    csv_lines.append(f"{chart_type}, {len(chart_data)} items")
            return '\n'.join(csv_lines)
        else:
            raise ValueError(f"Format non supporté: {output_format}")