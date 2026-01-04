"""
Générateur de recommandations pour l'amélioration des agents IA.

Analyse les performances de l'agent et génère des recommandations
spécifiques pour améliorer son intelligence, basées sur les métriques,
les patterns détectés et les meilleures pratiques RL.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class RecommendationPriority(Enum):
    """Priorité des recommandations."""
    CRITICAL = 1  # Doit être adressé immédiatement
    HIGH = 2      # Important pour l'amélioration
    MEDIUM = 3    # Amélioration significative possible
    LOW = 4       # Affinage optionnel

class RecommendationCategory(Enum):
    """Catégories de recommandations."""
    HYPERPARAMETERS = "hyperparameters"
    ARCHITECTURE = "architecture"
    TRAINING = "training"
    ENVIRONMENT = "environment"
    EXPLORATION = "exploration"
    REWARD = "reward_function"
    STABILITY = "stability"

@dataclass
class Recommendation:
    """Recommandation spécifique pour l'amélioration."""
    id: str
    title: str
    description: str
    category: RecommendationCategory
    priority: RecommendationPriority
    rationale: str
    action_items: List[str]
    expected_impact: float  # 0-1, impact attendu sur le score
    difficulty: str  # 'easy', 'medium', 'hard'
    dependencies: List[str]  # IDs des recommandations prérequises

class RecommendationsGenerator:
    """Générateur de recommandations pour l'amélioration des agents."""
    
    def __init__(self):
        """Initialise le générateur avec une base de connaissances."""
        self.recommendation_templates = self._load_recommendation_templates()
        logger.info("Générateur de recommandations initialisé")
    
    def generate_recommendations(self,
                               intelligence_score: Dict[str, Any],
                               metrics_analysis: Dict[str, Any],
                               baseline_comparison: Dict[str, Any],
                               difficulty_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère des recommandations personnalisées basées sur l'analyse complète.
        
        Args:
            intelligence_score: Résultat du calculateur d'intelligence
            metrics_analysis: Analyse détaillée des métriques
            baseline_comparison: Comparaison avec les baselines
            difficulty_profile: Profil de difficulté de l'environnement
            
        Returns:
            Ensemble de recommandations personnalisées
        """
        logger.info("Génération des recommandations personnalisées")
        
        # Collecter les signaux de performance
        performance_signals = self._extract_performance_signals(
            intelligence_score, metrics_analysis, baseline_comparison
        )
        
        # Identifier les problèmes prioritaires
        problems = self._identify_problems(performance_signals)
        
        # Générer les recommandations pour chaque problème
        recommendations = []
        for problem in problems:
            problem_recommendations = self._generate_recommendations_for_problem(
                problem, performance_signals, difficulty_profile
            )
            recommendations.extend(problem_recommendations)
        
        # Trier par priorité et impact
        recommendations.sort(key=lambda r: (r.priority.value, -r.expected_impact))
        
        # Grouper par catégorie
        grouped_recommendations = self._group_recommendations_by_category(recommendations)
        
        # Générer un plan d'action
        action_plan = self._generate_action_plan(recommendations)
        
        # Calculer l'impact total potentiel
        total_impact = self._calculate_total_impact(recommendations)
        
        return {
            'recommendations': [self._recommendation_to_dict(r) for r in recommendations],
            'grouped_recommendations': grouped_recommendations,
            'action_plan': action_plan,
            'performance_summary': performance_signals,
            'identified_problems': problems,
            'total_potential_impact': total_impact,
            'generation_timestamp': datetime.now().isoformat()
        }
    
    def _extract_performance_signals(self,
                                   intelligence_score: Dict[str, Any],
                                   metrics_analysis: Dict[str, Any],
                                   baseline_comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les signaux de performance clés des différentes analyses."""
        signals = {}
        
        # Signaux du score d'intelligence
        if intelligence_score:
            signals['overall_score'] = intelligence_score.get('overall_score', 0.0)
            signals['components'] = intelligence_score.get('components', {})
            signals['raw_metrics'] = intelligence_score.get('raw_metrics', {})
        
        # Signaux de l'analyse des métriques
        if metrics_analysis:
            signals['basic_stats'] = metrics_analysis.get('basic_statistics', {})
            signals['trends'] = metrics_analysis.get('trend_analysis', {})
            signals['patterns'] = metrics_analysis.get('detected_patterns', [])
            signals['weaknesses'] = metrics_analysis.get('weakness_diagnosis', [])
            signals['consistency'] = metrics_analysis.get('consistency_analysis', {})
            signals['learning_quality'] = metrics_analysis.get('learning_quality', {})
        
        # Signaux de comparaison avec baseline
        if baseline_comparison:
            signals['comparisons'] = baseline_comparison.get('comparisons', {})
            signals['overall_stats'] = baseline_comparison.get('overall_statistics', {})
            signals['summary'] = baseline_comparison.get('summary', {})
        
        # Calculer des signaux dérivés
        signals['derived'] = self._calculate_derived_signals(signals)
        
        return signals
    
    def _calculate_derived_signals(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule des signaux dérivés à partir des signaux bruts."""
        derived = {}
        
        # Score global
        overall_score = signals.get('overall_score', 0.0)
        derived['performance_level'] = self._classify_performance_level(overall_score)
        
        # Consistance
        consistency_data = signals.get('consistency', {})
        reward_cv = consistency_data.get('reward_coefficient_of_variation', 1.0)
        derived['consistency_level'] = 'high' if reward_cv < 0.5 else 'medium' if reward_cv < 1.0 else 'low'
        
        # Tendance d'apprentissage
        learning_data = signals.get('learning_quality', {})
        learning_slope = learning_data.get('learning_slope', 0.0)
        derived['learning_trend'] = 'positive' if learning_slope > 0.01 else 'negative' if learning_slope < -0.01 else 'stable'
        
        # Efficacité
        basic_stats = signals.get('basic_stats', {})
        efficiency = basic_stats.get('efficiency', 0.0)
        derived['efficiency_level'] = 'high' if efficiency > 0.7 else 'medium' if efficiency > 0.4 else 'low'
        
        # Survie
        avg_steps = basic_stats.get('avg_steps', 0.0)
        derived['survival_level'] = 'high' if avg_steps > 150 else 'medium' if avg_steps > 80 else 'low'
        
        return derived
    
    def _classify_performance_level(self, score: float) -> str:
        """Classe le niveau de performance."""
        if score >= 80:
            return 'excellent'
        elif score >= 60:
            return 'good'
        elif score >= 40:
            return 'average'
        elif score >= 20:
            return 'poor'
        else:
            return 'very_poor'
    
    def _identify_problems(self, signals: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identifie les problèmes de performance à partir des signaux."""
        problems = []
        
        # Problème: Score global faible
        overall_score = signals.get('overall_score', 0.0)
        if overall_score < 40:
            problems.append({
                'id': 'low_overall_score',
                'description': f'Score d\'intelligence faible ({overall_score:.1f}/100)',
                'severity': 'high',
                'metrics': ['overall_score']
            })
        
        # Problème: Inconsistance
        derived = signals.get('derived', {})
        if derived.get('consistency_level') == 'low':
            problems.append({
                'id': 'high_variability',
                'description': 'Performances très variables d\'un épisode à l\'autre',
                'severity': 'medium',
                'metrics': ['reward_coefficient_of_variation']
            })
        
        # Problème: Tendance d'apprentissage négative
        if derived.get('learning_trend') == 'negative':
            problems.append({
                'id': 'negative_learning',
                'description': 'L\'agent régresse au lieu de progresser',
                'severity': 'high',
                'metrics': ['learning_slope']
            })
        
        # Problème: Efficacité faible
        if derived.get('efficiency_level') == 'low':
            problems.append({
                'id': 'low_efficiency',
                'description': 'Faible efficacité de collecte des pellets',
                'severity': 'medium',
                'metrics': ['efficiency']
            })
        
        # Problème: Survie courte
        if derived.get('survival_level') == 'low':
            problems.append({
                'id': 'short_survival',
                'description': 'Survie moyenne très courte',
                'severity': 'high',
                'metrics': ['avg_steps']
            })
        
        # Problème: Plateau d'apprentissage
        patterns = signals.get('patterns', [])
        for pattern in patterns:
            if pattern.get('name') == 'learning_plateau':
                problems.append({
                    'id': 'learning_plateau',
                    'description': 'L\'agent a atteint un plateau d\'apprentissage',
                    'severity': 'medium',
                    'metrics': ['learning_trend']
                })
                break
        
        # Problème: Instabilité élevée
        for pattern in patterns:
            if pattern.get('name') == 'high_instability':
                problems.append({
                    'id': 'high_instability',
                    'description': 'Instabilité élevée des performances',
                    'severity': 'medium',
                    'metrics': ['reward_std']
                })
                break
        
        # Problème: Comparaison défavorable avec baseline
        summary = signals.get('summary', {})
        avg_improvement = summary.get('average_improvement', 0.0)
        if avg_improvement < -10:
            problems.append({
                'id': 'poor_baseline_comparison',
                'description': f'Performance inférieure aux baselines ({avg_improvement:.1f}%)',
                'severity': 'high',
                'metrics': ['average_improvement']
            })
        
        return problems
    
    def _generate_recommendations_for_problem(self,
                                            problem: Dict[str, Any],
                                            signals: Dict[str, Any],
                                            difficulty_profile: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations spécifiques pour un problème identifié."""
        problem_id = problem.get('id', '')
        recommendations = []
        
        # Mapping des problèmes aux recommandations
        problem_recommendations_map = {
            'low_overall_score': self._generate_low_score_recommendations,
            'high_variability': self._generate_variability_recommendations,
            'negative_learning': self._generate_negative_learning_recommendations,
            'low_efficiency': self._generate_efficiency_recommendations,
            'short_survival': self._generate_survival_recommendations,
            'learning_plateau': self._generate_plateau_recommendations,
            'high_instability': self._generate_instability_recommendations,
            'poor_baseline_comparison': self._generate_baseline_recommendations
        }
        
        generator = problem_recommendations_map.get(problem_id)
        if generator:
            recommendations = generator(signals, difficulty_profile)
        
        return recommendations
    
    def _generate_low_score_recommendations(self,
                                          signals: Dict[str, Any],
                                          difficulty_profile: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations pour un score global faible."""
        recommendations = []
        
        # Analyser les composantes faibles
        components = signals.get('components', {})
        weak_components = []
        
        for component, value in components.items():
            if value < 40:  # Composante faible
                weak_components.append((component, value))
        
        # Recommandations spécifiques par composante faible
        for component, value in weak_components:
            if component == 'winrate':
                recommendations.append(Recommendation(
                    id='rec_winrate_01',
                    title='Améliorer le taux de victoire',
                    description='Le taux de victoire est faible. Focus sur la stratégie de fin de partie.',
                    category=RecommendationCategory.STRATEGY,
                    priority=RecommendationPriority.HIGH,
                    rationale=f'Taux de victoire actuel: {value:.1f}%',
                    action_items=[
                        'Ajouter des récompenses pour la collecte de tous les pellets',
                        'Renforcer l\'apprentissage des états de fin de partie',
                        'Augmenter l\'exploration en fin d\'épisode'
                    ],
                    expected_impact=0.3,
                    difficulty='medium',
                    dependencies=[]
                ))
            elif component == 'reward_normalized':
                recommendations.append(Recommendation(
                    id='rec_reward_01',
                    title='Optimiser la fonction de récompense',
                    description='Les récompenses sont faibles. La fonction de récompense pourrait être mal calibrée.',
                    category=RecommendationCategory.REWARD,
                    priority=RecommendationPriority.HIGH,
                    rationale=f'Récompense normalisée: {value:.1f}%',
                    action_items=[
                        'Réviser les poids des différentes récompenses',
                        'Ajouter des récompenses intermédiaires',
                        'Ajuster les pénalités pour les morts'
                    ],
                    expected_impact=0.4,
                    difficulty='medium',
                    dependencies=[]
                ))
        
        # Recommandation générale si plusieurs composantes sont faibles
        if len(weak_components) >= 2:
            recommendations.append(Recommendation(
                id='rec_general_01',
                title='Réviser la stratégie d\'apprentissage globale',
                description='Plusieurs aspects des performances sont faibles. Une approche globale est nécessaire.',
                category=RecommendationCategory.TRAINING,
                priority=RecommendationPriority.CRITICAL,
                rationale=f'{len(weak_components)} composantes sous 40%',
                action_items=[
                    'Augmenter le nombre total d\'épisodes d\'entraînement',
                    'Réviser l\'architecture du réseau de neurones',
                    'Expérimenter avec différents algorithmes RL'
                ],
                expected_impact=0.5,
                difficulty='hard',
                dependencies=[]
            ))
        
        return recommendations
    
    def _generate_variability_recommendations(self,
                                            signals: Dict[str, Any],
                                            difficulty_profile: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations pour une variabilité élevée."""
        recommendations = []
        
        recommendations.append(Recommendation(
            id='rec_variability_01',
            title='Stabiliser les performances',
            description='Les performances sont très variables d\'un épisode à l\'autre.',
            category=RecommendationCategory.STABILITY,
            priority=RecommendationPriority.HIGH,
            rationale='Coefficient de variation élevé des récompenses',
            action_items=[
                'Réduire le taux d\'apprentissage (learning rate)',
                'Augmenter la taille du buffer de replay',
                'Utiliser un target network plus stable',
                'Augmenter la fréquence de mise à jour du target network'
            ],
            expected_impact=0.35,
            difficulty='medium',
            dependencies=[]
        ))
        
        return recommendations
    
    def _generate_negative_learning_recommendations(self,
                                                  signals: Dict[str, Any],
                                                  difficulty_profile: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations pour une tendance d'apprentissage négative."""
        recommendations = []
        
        recommendations.append(Recommendation(
            id='rec_negative_learning_01',
            title='Inverser la tendance d\'apprentissage',
            description='L\'agent régresse au lieu de progresser au fil du temps.',
            category=RecommendationCategory.TRAINING,
            priority=RecommendationPriority.CRITICAL,
            rationale='Pente négative de la régression des récompenses',
            action_items=[
                'Réinitialiser les poids du réseau avec une initialisation différente',
                'Réduire drastiquement le taux d\'apprentissage',
                'Augmenter l\'exploration (epsilon) temporairement',
                'Vérifier la stabilité des gradients'
            ],
            expected_impact=0.4,
            difficulty='hard',
            dependencies=[]
        ))
        
        return recommendations
    
    def _generate_efficiency_recommendations(self,
                                           signals: Dict[str, Any],
                                           difficulty_profile: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations pour une faible efficacité."""
        recommendations = []
        
        recommendations.append(Recommendation(
            id='rec_efficiency_01',
            title='Améliorer l\'efficacité de collecte',
            description='L\'agent collecte peu de pellets par rapport au total disponible.',
            category=RecommendationCategory.STRATEGY,
            priority=RecommendationPriority.MEDIUM,
            rationale='Efficacité de collecte faible',
            action_items=[
                'Améliorer l\'exploration pour découvrir tous les pellets',
                'Ajouter des récompenses pour la collecte de pellets',
                'Optimiser la planification de chemin',
                'Réduire les mouvements circulaires inutiles'
            ],
            expected_impact=0.25,
            difficulty='medium',
            dependencies=[]
        ))
        
        return recommendations
    
    def _generate_survival_recommendations(self,
                                         signals: Dict[str, Any],
                                         difficulty_profile: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations pour une survie courte."""
        recommendations = []
        
        recommendations.append(Recommendation(
            id='rec_survival_01',
            title='Améliorer la survie',
            description='L\'agent meurt trop rapidement dans les épisodes.',
            category=RecommendationCategory.STRATEGY,
            priority=RecommendationPriority.HIGH,
            rationale='Survie moyenne très courte',
            action_items=[
                'Renforcer l\'apprentissage de l\'évitement des fantômes',
                'Ajouter des pénalités pour les morts précoces',
                'Apprendre à utiliser les power pellets efficacement',
                'Améliorer la détection des fantômes proches'
            ],
            expected_impact=0.35,
            difficulty='medium',
            dependencies=[]
        ))
        
        return recommendations
    
    def _generate_plateau_recommendations(self,
                                        signals: Dict[str, Any],
                                        difficulty_profile: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations pour un plateau d'apprentissage."""
        recommendations = []
        
        recommendations.append(Recommendation(
            id='rec_plateau_01',
            title='Sortir du plateau d\'apprentissage',
            description='L\'agent a atteint un plateau et ne progresse plus.',
            category=RecommendationCategory.TRAINING,
            priority=RecommendationPriority.MEDIUM,
            rationale='Plateau d\'apprentissage détecté',
            action_items=[
                'Augmenter l\'exploration (epsilon) temporairement',
                'Expérimenter avec un taux d\'apprentissage adaptatif',
                'Introduire de la noise dans les actions',
                'Essayer un algorithme RL différent'
            ],
            expected_impact=0.3,
            difficulty='hard',
            dependencies=[]
        ))
        
        return recommendations
    
    def _generate_instability_recommendations(self,
                                            signals: Dict[str, Any],
                                            difficulty_profile: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations pour une instabilité élevée."""
        recommendations = []
        
        recommendations.append(Recommendation(
            id='rec_instability_01',
            title='Réduire l\'instabilité',
            description='Les performances sont très instables.',
            category=RecommendationCategory.STABILITY,
            priority=RecommendationPriority.MEDIUM,
            rationale='Instabilité élevée détectée',
            action_items=[
                'Réduire le taux d\'apprentissage',
                'Augmenter la taille du batch',
                'Utiliser la normalisation des gradients',
                'Implémenter un clipping des gradients'
            ],
            expected_impact=0.25,
            difficulty='medium',
            dependencies=[]
        ))
        
        return recommendations
    
    def _generate_baseline_recommendations(self,
                                         signals: Dict[str, Any],
                                         difficulty_profile: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations pour une comparaison défavorable avec baseline."""
        recommendations = []
        
        recommendations.append(Recommendation(
            id='rec_baseline_01',
            title='Améliorer par rapport aux baselines',
            description='L\'agent performe moins bien que les agents de référence.',
            category=RecommendationCategory.TRAINING,
            priority=RecommendationPriority.HIGH,
            rationale='Performance inférieure aux baselines établies',
            action_items=[
                'Analyser les stratégies des baselines performantes',
                'Adapter les hyperparamètres pour correspondre aux baselines',
                'Implémenter des techniques éprouvées des baselines',
                'Augmenter la durée d\'entraînement'
            ],
            expected_impact=0.4,
            difficulty='hard',
            dependencies=[]
        ))
        
        return recommendations
    
    def _load_recommendation_templates(self) -> Dict[str, Any]:
        """Charge les templates de recommandations depuis une base de connaissances."""
        # Pour l'instant, retourner un dictionnaire vide
        # Dans une implémentation réelle, on chargerait depuis un fichier JSON ou une base de données
        return {}
    
    def _group_recommendations_by_category(self, recommendations: List[Recommendation]) -> Dict[str, List[Dict[str, Any]]]:
        """Groupe les recommandations par catégorie."""
        grouped = {}
        
        for recommendation in recommendations:
            category = recommendation.category.value
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(self._recommendation_to_dict(recommendation))
        
        return grouped
    
    def _generate_action_plan(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Génère un plan d'action à partir des recommandations."""
        # Trier par priorité
        critical = [r for r in recommendations if r.priority == RecommendationPriority.CRITICAL]
        high = [r for r in recommendations if r.priority == RecommendationPriority.HIGH]
        medium = [r for r in recommendations if r.priority == RecommendationPriority.MEDIUM]
        low = [r for r in recommendations if r.priority == RecommendationPriority.LOW]
        
        # Estimer le temps total
        time_estimates = {
            'easy': 1,
            'medium': 3,
            'hard': 8
        }
        
        total_time = sum(time_estimates.get(r.difficulty, 2) for r in recommendations)
        
        # Créer une roadmap
        roadmap = []
        current_week = 1
        
        # Semaine 1: Recommandations critiques
        if critical:
            roadmap.append({
                'week': current_week,
                'focus': 'Problèmes critiques',
                'recommendations': [r.id for r in critical],
                'estimated_hours': sum(time_estimates.get(r.difficulty, 2) for r in critical)
            })
            current_week += 1
        
        # Semaine 2: Recommandations haute priorité
        if high:
            roadmap.append({
                'week': current_week,
                'focus': 'Améliorations importantes',
                'recommendations': [r.id for r in high],
                'estimated_hours': sum(time_estimates.get(r.difficulty, 2) for r in high)
            })
            current_week += 1
        
        # Semaines suivantes: Recommandations moyenne et basse priorité
        if medium or low:
            roadmap.append({
                'week': current_week,
                'focus': 'Affinages et optimisations',
                'recommendations': [r.id for r in medium + low],
                'estimated_hours': sum(time_estimates.get(r.difficulty, 2) for r in medium + low)
            })
        
        return {
            'total_recommendations': len(recommendations),
            'by_priority': {
                'critical': len(critical),
                'high': len(high),
                'medium': len(medium),
                'low': len(low)
            },
            'total_estimated_time_hours': total_time,
            'roadmap': roadmap,
            'next_steps': self._get_next_steps(recommendations)
        }
    
    def _get_next_steps(self, recommendations: List[Recommendation]) -> List[str]:
        """Retourne les prochaines étapes immédiates."""
        if not recommendations:
            return ["Aucune recommandation disponible. Continuer l'entraînement actuel."]
        
        # Trouver les recommandations les plus prioritaires sans dépendances
        immediate_recommendations = [
            r for r in recommendations
            if r.priority in [RecommendationPriority.CRITICAL, RecommendationPriority.HIGH]
            and not r.dependencies
        ]
        
        if not immediate_recommendations:
            immediate_recommendations = recommendations[:2]
        
        next_steps = []
        for rec in immediate_recommendations[:3]:  # Limiter à 3 étapes
            next_steps.append(f"{rec.title}: {rec.action_items[0]}")
        
        return next_steps
    
    def _calculate_total_impact(self, recommendations: List[Recommendation]) -> float:
        """Calcule l'impact total potentiel des recommandations."""
        if not recommendations:
            return 0.0
        
        # Pondérer par la priorité
        priority_weights = {
            RecommendationPriority.CRITICAL: 1.0,
            RecommendationPriority.HIGH: 0.8,
            RecommendationPriority.MEDIUM: 0.5,
            RecommendationPriority.LOW: 0.2
        }
        
        total_impact = 0.0
        total_weight = 0.0
        
        for recommendation in recommendations:
            weight = priority_weights.get(recommendation.priority, 0.5)
            total_impact += recommendation.expected_impact * weight
            total_weight += weight
        
        if total_weight > 0:
            return min(1.0, total_impact / total_weight * 2)  # Normaliser
        else:
            return 0.0
    
    def _recommendation_to_dict(self, recommendation: Recommendation) -> Dict[str, Any]:
        """Convertit une recommandation en dictionnaire."""
        return {
            'id': recommendation.id,
            'title': recommendation.title,
            'description': recommendation.description,
            'category': recommendation.category.value,
            'priority': recommendation.priority.name.lower(),
            'rationale': recommendation.rationale,
            'action_items': recommendation.action_items,
            'expected_impact': recommendation.expected_impact,
            'difficulty': recommendation.difficulty,
            'dependencies': recommendation.dependencies
        }
