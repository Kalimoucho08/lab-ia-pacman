# Méthodologie de Mesure d'Intelligence IA Pac-Man

## Introduction

Ce document décrit la méthodologie complète pour mesurer l'intelligence des agents IA dans le laboratoire scientifique Pac-Man. Le système produit un score composite de 0 à 100 qui évalue les performances globales de l'agent selon plusieurs dimensions.

## Architecture du Système

```
intelligence/
├── intelligence_calculator.py    # Calculateur de score composite
├── metrics_analyzer.py           # Analyseur de métriques détaillées
├── baseline_comparator.py        # Comparateur avec baselines
├── difficulty_adjuster.py        # Ajusteur de difficulté
├── recommendations_generator.py  # Générateur de recommandations
└── visualization_generator.py    # Générateur de visualisations
```

## Formule de Score d'Intelligence

### Score Composite

```
Intelligence = 45% × Winrate + 30% × Reward moyen + 25% × Survie moyenne
```

### Composantes Détaillées

1. **Winrate normalisée** (45%)
   ```
   winrate_norm = (winrate_agent - winrate_baseline) / (1 - winrate_baseline)
   ```

2. **Reward normalisé** (30%)
   ```
   reward_norm = (reward_agent - reward_min) / (reward_max - reward_min)
   ```

3. **Survie normalisée** (25%)
   ```
   survival_norm = steps_agent / steps_max
   ```

4. **Métriques secondaires** (pour analyse)
   - **Efficacité** : Pellets collectés / Pellets totaux
   - **Consistance** : 1 - (écart-type des performances / moyenne)
   - **Apprentissage** : Pente de la régression linéaire des scores

## Normalisation et Ajustement

### Normalisation par Baseline

Chaque métrique est normalisée par rapport à des baselines prédéfinies :

| Baseline | Winrate | Reward moyen | Survie moyenne |
|----------|---------|--------------|----------------|
| Agent aléatoire | 10% | -100 | 20% |
| Heuristique simple | 30% | 50 | 40% |
| Rule-based | 60% | 150 | 70% |
| State-of-the-art | 85% | 300 | 90% |

### Ajustement de Difficulté

Le score est ajusté selon la difficulté de l'environnement :

```
score_ajusté = score_brut × facteur_difficulté
```

**Facteurs de difficulté** :
- Taille de grille : 1.0 (petite) à 1.5 (grande)
- Nombre de fantômes : 1.0 (1 fantôme) à 2.0 (8 fantômes)
- Densité de pellets : 1.0 (haute) à 1.3 (basse)
- Vitesse des fantômes : 1.0 (lente) à 1.4 (rapide)

## Analyse des Métriques

### Métriques de Base

1. **Winrate** : Pourcentage de victoires
2. **Reward moyen** : Récompense moyenne par épisode
3. **Survie moyenne** : Nombre moyen de steps avant mort
4. **Efficacité** : Ratio de pellets collectés
5. **Consistance** : Stabilité des performances
6. **Taux d'apprentissage** : Amélioration au cours du temps

### Analyse de Tendances

- **Régression linéaire** sur les 20 derniers épisodes
- **Moyenne mobile** sur 10 épisodes
- **Détection de plateaux** et de régressions
- **Analyse de variance** pour la consistance

### Détection de Patterns

- **Cycles de victoires/défaites**
- **Comportements répétitifs**
- **Stratégies émergentes**
- **Faiblesses systématiques**

## Comparaison avec Baselines

### Ratios d'Amélioration

```
ratio = métrique_agent / métrique_baseline
```

### Percentiles

Position de l'agent par rapport aux baselines prédéfinies.

### Interprétation

| Percentile | Niveau | Description |
|------------|--------|-------------|
| 0-20 | Débutant | Performances inférieures à l'agent aléatoire |
| 20-40 | Novice | Légèrement meilleur que l'agent aléatoire |
| 40-60 | Intermédiaire | Comparable à l'heuristique simple |
| 60-80 | Avancé | Meilleur que le rule-based |
| 80-100 | Expert | Approche le state-of-the-art |

## Génération de Recommandations

### Priorisation

1. **Haute priorité** : Faiblesses critiques (>20% d'amélioration possible)
2. **Moyenne priorité** : Améliorations significatives (10-20%)
3. **Basse priorité** : Optimisations mineures (<10%)

### Types de Recommandations

1. **Stratégiques** : Changer de stratégie globale
2. **Tactiques** : Améliorer des actions spécifiques
3. **Paramétriques** : Ajuster les hyperparamètres
4. **Architecturales** : Modifier l'architecture du modèle

## Visualisations

### Radar Chart des 6 Métriques

Affiche les performances sur 6 dimensions :
1. Winrate
2. Reward
3. Survie
4. Efficacité
5. Consistance
6. Apprentissage

### Séries Temporelles

- Évolution du score d'intelligence
- Tendances des métriques individuelles
- Comparaison avec les sessions précédentes

### Charts de Comparaison

- Bar charts vs baselines
- Heatmaps de performance par difficulté
- Scatter plots des métriques corrélées

## Intégration avec le Système

### Backend FastAPI

**Endpoints disponibles** :

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/intelligence/calculate` | POST | Calcule le score d'intelligence |
| `/api/v1/intelligence/analyze-metrics` | POST | Analyse détaillée des métriques |
| `/api/v1/intelligence/compare-baselines` | POST | Compare avec les baselines |
| `/api/v1/intelligence/adjust-difficulty` | POST | Ajuste le score selon la difficulté |
| `/api/v1/intelligence/generate-recommendations` | POST | Génère des recommandations |
| `/api/v1/intelligence/generate-visualizations` | POST | Génère les données de visualisation |
| `/api/v1/intelligence/baselines` | GET | Liste les baselines disponibles |
| `/api/v1/intelligence/health` | GET | Vérifie l'état du service |

### Format des Données

```json
{
  "episodes": [
    {
      "episode": 0,
      "reward": 100.0,
      "steps": 500,
      "win": true,
      "pellets_collected": 80,
      "total_pellets": 100,
      "ghosts_eaten": 2,
      "deaths": 0,
      "max_steps": 1000
    }
  ],
  "environment_params": {
    "grid_size": 10,
    "num_ghosts": 2,
    "power_pellets": 2,
    "pellet_density": 0.7
  },
  "agent_type": "pacman",
  "baseline_winrate": 0.1,
  "baseline_reward": -100.0
}
```

### Réponse Type

```json
{
  "intelligence_score": {
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
  },
  "metrics_analysis": {
    "basic_statistics": { ... },
    "trend_analysis": { ... },
    "pattern_detection": { ... },
    "diagnostics": { ... }
  },
  "baseline_comparison": {
    "improvement_ratios": { ... },
    "percentiles": { ... },
    "interpretation": "Niveau intermédiaire"
  },
  "recommendations": {
    "recommendations": [ ... ],
    "priority_ranking": [ ... ],
    "action_plan": [ ... ]
  },
  "visualizations": {
    "radar_chart_data": { ... },
    "time_series_data": [ ... ],
    "comparison_charts": [ ... ]
  }
}
```

## Certification des Niveaux d'Intelligence

| Score | Niveau | Description |
|-------|--------|-------------|
| 0-20 | Débutant | Comprend les règles de base |
| 20-40 | Novice | Survit quelques steps |
| 40-60 | Intermédiaire | Collecte des pellets régulièrement |
| 60-80 | Avancé | Évite les fantômes efficacement |
| 80-90 | Expert | Gagne régulièrement |
| 90-100 | Maître | Performance optimale |

## Optimisation des Calculs

### Techniques d'Optimisation

1. **Pré-calcul des baselines**
2. **Mise en cache des résultats intermédiaires**
3. **Calcul incrémental** pour les séries temporelles
4. **Parallélisation** des analyses statistiques

### Performance

- **Temps de calcul** : < 100ms pour 1000 épisodes
- **Mémoire** : < 10MB pour l'analyse complète
- **Scalabilité** : Linéaire avec le nombre d'épisodes

## Validation et Tests

### Tests Unitaires

- Validation des formules de normalisation
- Vérification des limites (0-100)
- Tests de consistance statistique

### Tests d'Intégration

- Intégration avec le backend FastAPI
- Compatibilité avec le frontend React
- Tests de charge et performance

### Tests de Validation

- Comparaison avec évaluations humaines
- Validation sur données de référence
- Tests A/B avec différentes configurations

## Utilisation Pratique

### Pour les Chercheurs

1. **Évaluation comparative** : Comparez différents algorithmes
2. **Analyse diagnostique** : Identifiez les points faibles
3. **Suivi d'apprentissage** : Visualisez la progression

### Pour les Développeurs

1. **Intégration simple** : API REST standard
2. **Documentation complète** : Exemples et tutoriels
3. **Extensibilité** : Ajoutez vos propres métriques

### Pour les Enseignants

1. **Évaluation objective** : Scores reproductibles
2. **Visualisations pédagogiques** : Graphiques explicatifs
3. **Benchmarks** : Comparaisons avec l'état de l'art

## Limitations et Améliorations Futures

### Limitations Actuelles

1. **Biais de difficulté** : Certains environnements sont plus difficiles à évaluer
2. **Métriques subjectives** : Certains aspects de l'intelligence ne sont pas capturés
3. **Dépendance aux baselines** : Qualité des baselines de référence

### Améliorations Planifiées

1. **Apprentissage par renforcement multi-objectif**
2. **Analyse comportementale avancée**
3. **Intégration de métriques cognitives**
4. **Benchmarking distribué**

## Conclusion

Le système de mesure d'intelligence fournit une évaluation complète et objective des performances des agents IA Pac-Man. En combinant des métriques quantitatives, des analyses statistiques et des visualisations intuitives, il offre aux chercheurs, développeurs et enseignants un outil puissant pour évaluer, comparer et améliorer les agents d'intelligence artificielle.

## Références

1. Pac-Man Reinforcement Learning Benchmark (2024)
2. Multi-Agent Intelligence Evaluation Framework
3. Reinforcement Learning Performance Metrics Survey
4. Game AI Evaluation Methodologies