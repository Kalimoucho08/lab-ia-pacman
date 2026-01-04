"""
Script de test pour le système de mesure d'intelligence.

Valide le calcul du score d'intelligence, l'analyse des métriques,
la comparaison avec baselines, l'ajustement de difficulté,
la génération de recommandations et les visualisations.
"""

import sys
import os
import json
import logging
from typing import Dict, List, Any

# Ajouter le répertoire courant au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importer les modules d'intelligence
try:
    from intelligence.intelligence_calculator import IntelligenceCalculator, create_episode_metrics_from_backend
    from intelligence.metrics_analyzer import MetricsAnalyzer
    from intelligence.baseline_comparator import BaselineComparator
    from intelligence.difficulty_adjuster import DifficultyAdjuster, EnvironmentDifficulty
    from intelligence.recommendations_generator import RecommendationsGenerator
    from intelligence.visualization_generator import VisualizationGenerator
    print("[OK] Modules d'intelligence importés avec succès")
except ImportError as e:
    print(f"[ERREUR] Erreur d'importation des modules d'intelligence: {e}")
    sys.exit(1)

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_test_episodes(num_episodes: int = 50) -> List[Dict[str, Any]]:
    """
    Génère des données d'épisodes de test réalistes.
    
    Args:
        num_episodes: Nombre d'épisodes à générer
        
    Returns:
        Liste de dictionnaires représentant les épisodes
    """
    episodes = []
    
    for i in range(num_episodes):
        # Générer des données réalistes avec une tendance d'amélioration
        improvement_factor = min(1.0, i / num_episodes * 2)  # Amélioration linéaire
        
        # Winrate augmente avec le temps
        win_probability = 0.1 + improvement_factor * 0.6  # De 10% à 70%
        win = (i % 10) < (win_probability * 10)  # Simulation aléatoire
        
        # Reward augmente avec le temps
        base_reward = -50.0 + improvement_factor * 200.0  # De -50 à 150
        reward_variation = (i % 20) * 5.0  # Variation
        reward = base_reward + reward_variation
        
        # Steps augmentent avec le temps (meilleure survie)
        max_steps = 1000
        steps = int(200 + improvement_factor * 600 + (i % 10) * 20)
        steps = min(steps, max_steps)
        
        # Pellets collectés
        total_pellets = 100
        pellets_collected = int(30 + improvement_factor * 50 + (i % 10) * 2)
        pellets_collected = min(pellets_collected, total_pellets)
        
        # Fantômes mangés
        ghosts_eaten = int(improvement_factor * 5)
        
        # Morts
        deaths = 0 if win else 1
        
        episodes.append({
            "episode": i,
            "reward": reward,
            "steps": steps,
            "win": win,
            "pellets_collected": pellets_collected,
            "total_pellets": total_pellets,
            "ghosts_eaten": ghosts_eaten,
            "deaths": deaths,
            "max_steps": max_steps
        })
    
    return episodes

def test_intelligence_calculator() -> bool:
    """Teste le calculateur de score d'intelligence."""
    print("\n" + "="*60)
    print("Test du calculateur de score d'intelligence")
    print("="*60)
    
    try:
        # Générer des épisodes de test
        episodes_data = generate_test_episodes(30)
        episodes = create_episode_metrics_from_backend(episodes_data)
        
        # Initialiser le calculateur
        calculator = IntelligenceCalculator(
            baseline_winrate=0.1,
            baseline_reward=-100.0
        )
        
        # Calculer le score d'intelligence
        result = calculator.calculate_intelligence_score(episodes, difficulty_factor=1.0)
        
        # Vérifier les résultats
        assert 'overall_score' in result, "Score global manquant"
        assert 0 <= result['overall_score'] <= 100, f"Score hors limites: {result['overall_score']}"
        assert 'components' in result, "Composantes manquantes"
        assert 'explanations' in result, "Explications manquantes"
        
        print(f"[OK] Score d'intelligence calculé: {result['overall_score']:.2f}")
        print(f"  Composantes: {json.dumps({k: f'{v:.2f}' for k, v in result['components'].items()}, indent=2)}")
        
        return True
    except Exception as e:
        logger.error(f"[ERREUR] Erreur dans le calculateur d'intelligence: {e}", exc_info=True)
        return False

def test_metrics_analyzer() -> bool:
    """Teste l'analyseur de métriques."""
    print("\n" + "="*60)
    print("Test de l'analyseur de métriques")
    print("="*60)
    
    try:
        # Générer des épisodes de test
        episodes_data = generate_test_episodes(40)
        
        # Initialiser l'analyseur
        analyzer = MetricsAnalyzer()
        
        # Analyser les performances
        result = analyzer.analyze_performance(episodes_data, agent_type="pacman")
        
        # Vérifier les résultats
        required_keys = ['basic_statistics', 'trend_analysis', 'pattern_detection', 'diagnostics']
        for key in required_keys:
            assert key in result, f"Clé manquante: {key}"
        
        print(f"[OK] Analyse des métriques réussie")
        print(f"  Statistiques de base: {result['basic_statistics'].get('winrate', 0):.2%} winrate")
        print(f"  Tendances: {len(result['trend_analysis'].get('trends', []))} tendances détectées")
        print(f"  Patterns: {len(result['pattern_detection'].get('patterns', []))} patterns détectés")
        
        return True
    except Exception as e:
        logger.error(f"[ERREUR] Erreur dans l'analyseur de métriques: {e}", exc_info=True)
        return False

def test_baseline_comparator() -> bool:
    """Teste le comparateur de baselines."""
    print("\n" + "="*60)
    print("Test du comparateur de baselines")
    print("="*60)
    
    try:
        # Générer des métriques d'agent
        agent_metrics = {
            "winrate": 0.65,
            "avg_reward": 120.5,
            "avg_survival": 0.75,
            "efficiency": 0.82,
            "consistency": 0.68,
            "learning_rate": 0.15
        }
        
        environment_params = {
            "grid_size": 10,
            "num_ghosts": 2,
            "power_pellets": 2,
            "pellet_density": 0.7
        }
        
        # Initialiser le comparateur
        comparator = BaselineComparator()
        
        # Comparer avec les baselines
        result = comparator.compare_with_baselines(agent_metrics, environment_params)
        
        # Vérifier les résultats
        assert 'improvement_ratios' in result, "Ratios d'amélioration manquants"
        assert 'percentiles' in result, "Percentiles manquants"
        assert 'interpretation' in result, "Interprétation manquante"
        
        print(f"[OK] Comparaison avec baselines réussie")
        print(f"  Ratios d'amélioration: {json.dumps(result['improvement_ratios'], indent=2)}")
        print(f"  Percentiles: {json.dumps(result['percentiles'], indent=2)}")
        
        return True
    except Exception as e:
        logger.error(f"[ERREUR] Erreur dans le comparateur de baselines: {e}", exc_info=True)
        return False

def test_difficulty_adjuster() -> bool:
    """Teste l'ajusteur de difficulté."""
    print("\n" + "="*60)
    print("Test de l'ajusteur de difficulté")
    print("="*60)
    
    try:
        # Initialiser l'ajusteur
        adjuster = DifficultyAdjuster()
        
        # Créer un environnement difficile
        env_difficult = EnvironmentDifficulty(
            grid_size=20,
            num_ghosts=4,
            power_pellets=1,
            pellet_density=0.5,
            ghost_speed=1.5,
            pacman_speed=1.0,
            episode_time_limit=800
        )
        
        # Créer un environnement facile
        env_easy = EnvironmentDifficulty(
            grid_size=8,
            num_ghosts=1,
            power_pellets=3,
            pellet_density=0.9,
            ghost_speed=0.8,
            pacman_speed=1.2,
            episode_time_limit=1200
        )
        
        # Calculer les facteurs de difficulté
        factor_difficult = adjuster.calculate_difficulty_factor(env_difficult)
        factor_easy = adjuster.calculate_difficulty_factor(env_easy)
        
        # Ajuster un score
        raw_score = 70.0
        adjusted_difficult = adjuster.adjust_intelligence_score(raw_score, env_difficult, "multiplicative")
        adjusted_easy = adjuster.adjust_intelligence_score(raw_score, env_easy, "multiplicative")
        
        print(f"[OK] Ajusteur de difficulté testé")
        print(f"  Facteur difficulté (difficile): {factor_difficult:.2f}")
        print(f"  Facteur difficulté (facile): {factor_easy:.2f}")
        print(f"  Score ajusté (difficile): {adjusted_difficult['adjusted_score']:.2f}")
        print(f"  Score ajusté (facile): {adjusted_easy['adjusted_score']:.2f}")
        
        # Vérifier que le score ajusté est plus élevé pour l'environnement difficile
        assert adjusted_difficult['adjusted_score'] > adjusted_easy['adjusted_score'], \
            "Le score ajusté devrait être plus élevé pour l'environnement difficile"
        
        return True
    except Exception as e:
        logger.error(f"[ERREUR] Erreur dans l'ajusteur de difficulté: {e}", exc_info=True)
        return False

def test_recommendations_generator() -> bool:
    """Teste le générateur de recommandations."""
    print("\n" + "="*60)
    print("Test du générateur de recommandations")
    print("="*60)
    
    try:
        # Données d'entrée simulées
        intelligence_score = {
            "overall_score": 65.5,
            "components": {
                "winrate": 70.0,
                "reward_normalized": 60.0,
                "survival_normalized": 55.0,
                "efficiency": 75.0,
                "consistency": 50.0,
                "learning": 80.0
            },
            "explanations": {
                "winrate": "Bon taux de victoire",
                "reward_normalized": "Récompenses moyennes",
                "survival_normalized": "Survie à améliorer"
            }
        }
        
        metrics_analysis = {
            "basic_statistics": {
                "winrate": 0.7,
                "avg_reward": 120.0,
                "avg_survival": 0.55,
                "efficiency": 0.75,
                "consistency": 0.5
            },
            "diagnostics": {
                "weaknesses": ["Survie courte", "Inconsistance"],
                "strengths": ["Efficacité de collecte", "Apprentissage rapide"]
            }
        }
        
        baseline_comparison = {
            "improvement_ratios": {
                "random": 3.5,
                "simple_heuristic": 1.8,
                "rule_based": 1.2
            },
            "percentiles": {
                "winrate": 75,
                "reward": 60,
                "survival": 40
            }
        }
        
        difficulty_profile = {
            "difficulty_level": "medium",
            "challenge_factors": {
                "ghost_threat": 0.7,
                "navigation_complexity": 0.5,
                "resource_scarcity": 0.3
            }
        }
        
        # Initialiser le générateur
        generator = RecommendationsGenerator()
        
        # Générer des recommandations
        result = generator.generate_recommendations(
            intelligence_score=intelligence_score,
            metrics_analysis=metrics_analysis,
            baseline_comparison=baseline_comparison,
            difficulty_profile=difficulty_profile
        )
        
        # Vérifier les résultats
        assert 'recommendations' in result, "Recommandations manquantes"
        assert 'priority_ranking' in result, "Classement par priorité manquant"
        assert 'action_plan' in result, "Plan d'action manquant"
        
        print(f"[OK] Générateur de recommandations testé")
        print(f"  Nombre de recommandations: {len(result['recommendations'])}")
        print(f"  Priorité la plus élevée: {result['priority_ranking'][0] if result['priority_ranking'] else 'Aucune'}")
        
        return True
    except Exception as e:
        logger.error(f"[ERREUR] Erreur dans le générateur de recommandations: {e}", exc_info=True)
        return False

def test_visualization_generator() -> bool:
    """Teste le générateur de visualisations."""
    print("\n" + "="*60)
    print("Test du générateur de visualisations")
    print("="*60)
    
    try:
        # Données d'entrée simulées
        intelligence_score = {
            "overall_score": 65.5,
            "components": {
                "winrate": 70.0,
                "reward_normalized": 60.0,
                "survival_normalized": 55.0,
                "efficiency": 75.0,
                "consistency": 50.0,
                "learning": 80.0
            }
        }
        
        metrics_analysis = {
            "basic_statistics": {
                "winrate": 0.7,
                "avg_reward": 120.0,
                "avg_survival": 0.55,
                "efficiency": 0.75,
                "consistency": 0.5
            },
            "trend_analysis": {
                "trends": [
                    {"metric": "winrate", "slope": 0.05, "strength": "moderate"},
                    {"metric": "reward", "slope": 2.5, "strength": "strong"}
                ]
            }
        }
        
        baseline_comparison = {
            "improvement_ratios": {
                "random": 3.5,
                "simple_heuristic": 1.8,
                "rule_based": 1.2
            }
        }
        
        recommendations = {
            "recommendations": [
                {"id": "rec1", "title": "Améliorer la survie", "priority": "high"},
                {"id": "rec2", "title": "Réduire l'inconsistance", "priority": "medium"}
            ]
        }
        
        # Initialiser le générateur
        generator = VisualizationGenerator()
        
        # Générer les visualisations
        result = generator.generate_intelligence_dashboard(
            intelligence_score=intelligence_score,
            metrics_analysis=metrics_analysis,
            baseline_comparison=baseline_comparison,
            recommendations=recommendations
        )
        
        # Vérifier les résultats
        assert 'radar_chart_data' in result, "Données radar chart manquantes"
        assert 'time_series_data' in result, "Données séries temporelles manquantes"
        assert 'comparison_charts' in result, "Données comparaison manquantes"
        
        print(f"[OK] Générateur de visualisations testé")
        print(f"  Radar chart: {len(result['radar_chart_data'].get('datasets', []))} datasets")
        print(f"  Séries temporelles: {len(result['time_series_data'])} séries")
        print(f"  Charts de comparaison: {len(result['comparison_charts'])} charts")
        
        return True
    except Exception as e:
        logger.error(f"[ERREUR] Erreur dans le générateur de visualisations: {e}", exc_info=True)
        return False

def test_api_integration() -> bool:
    """Teste l'intégration avec l'API FastAPI."""
    print("\n" + "="*60)
    print("Test de l'intégration API")
    print("="*60)
    
    try:
        # Vérifier que le fichier d'endpoint existe
        endpoint_path = os.path.join("backend", "api", "v1", "endpoints", "intelligence.py")
        if not os.path.exists(endpoint_path):
            print(f"[ERREUR] Fichier d'endpoint introuvable:
