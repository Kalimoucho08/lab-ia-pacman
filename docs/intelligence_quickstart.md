# Guide de Démarrage Rapide - Mesure d'Intelligence

## Installation

1. **Vérifier les dépendances** :
   ```bash
   pip install scipy numpy
   ```

2. **Vérifier la structure** :
   ```bash
   python test_intelligence_simple.py
   ```

## Utilisation Basique

### 1. Calculer un score d'intelligence

```python
from intelligence.intelligence_calculator import IntelligenceCalculator, create_episode_metrics_from_backend

# Données d'épisodes
episodes_data = [
    {
        "episode": 0,
        "reward": 100.0,
        "steps": 500,
        "win": True,
        "pellets_collected": 80,
        "total_pellets": 100,
        "ghosts_eaten": 2,
        "deaths": 0,
        "max_steps": 1000
    }
]

# Convertir et calculer
episodes = create_episode_metrics_from_backend(episodes_data)
calculator = IntelligenceCalculator(baseline_winrate=0.1, baseline_reward=-100.0)
result = calculator.calculate_intelligence_score(episodes, difficulty_factor=1.0)

print(f"Score d'intelligence: {result['overall_score']:.2f}")
```

### 2. Utiliser l'API REST

**Démarrer le serveur** :
```bash
cd backend
python -m uvicorn app:app --reload
```

**Envoyer une requête** :
```bash
curl -X POST http://localhost:8000/api/v1/intelligence/calculate \
  -H "Content-Type: application/json" \
  -d '{
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
    "agent_type": "pacman"
  }'
```

## Exemples Complets

### Exemple 1 : Analyse complète

```python
import json
from intelligence.metrics_analyzer import MetricsAnalyzer
from intelligence.baseline_comparator import BaselineComparator
from intelligence.recommendations_generator import RecommendationsGenerator

# Analyser les métriques
analyzer = MetricsAnalyzer()
metrics_result = analyzer.analyze_performance(episodes_data, "pacman")

# Comparer avec baselines
comparator = BaselineComparator()
baseline_result = comparator.compare_with_baselines(
    metrics_result['basic_statistics'],
    {"grid_size": 10, "num_ghosts": 2}
)

# Générer des recommandations
generator = RecommendationsGenerator()
recommendations = generator.generate_recommendations(
    intelligence_score=result,
    metrics_analysis=metrics_result,
    baseline_comparison=baseline_result,
    difficulty_profile={"difficulty_level": "medium"}
)

print(json.dumps(recommendations, indent=2))
```

### Exemple 2 : Ajustement de difficulté

```python
from intelligence.difficulty_adjuster import DifficultyAdjuster, EnvironmentDifficulty

adjuster = DifficultyAdjuster()

# Environnement difficile
env_difficult = EnvironmentDifficulty(
    grid_size=20,
    num_ghosts=4,
    power_pellets=1,
    pellet_density=0.5,
    ghost_speed=1.5,
    pacman_speed=1.0,
    episode_time_limit=800
)

# Ajuster un score
adjusted = adjuster.adjust_intelligence_score(
    raw_score=70.0,
    env=env_difficult,
    adjustment_type="multiplicative"
)

print(f"Score ajusté: {adjusted['adjusted_score']:.2f}")
print(f"Facteur de difficulté: {adjusted['difficulty_factor']:.2f}")
```

## Intégration avec le Système Existant

### 1. Intégration avec l'entraînement RL

```python
# Dans votre boucle d'entraînement
def after_episode_callback(episode_data):
    from intelligence.intelligence_calculator import IntelligenceCalculator
    
    calculator = IntelligenceCalculator()
    episodes = create_episode_metrics_from_backend([episode_data])
    score = calculator.calculate_intelligence_score(episodes)
    
    # Enregistrer le score
    log_intelligence_score(score)
    
    # Envoyer au frontend via WebSocket
    send_to_frontend({
        "type": "intelligence_update",
        "score": score['overall_score'],
        "components": score['components']
    })
```

### 2. Intégration avec le Dashboard

```javascript
// Frontend React
import { useIntelligenceAPI } from '../services/api';

function IntelligenceDashboard() {
  const { calculateIntelligence } = useIntelligenceAPI();
  
  const handleCalculate = async (episodes) => {
    const result = await calculateIntelligence(episodes);
    
    // Afficher les résultats
    setScore(result.intelligence_score.overall_score);
    setComponents(result.intelligence_score.components);
    setRecommendations(result.recommendations);
  };
  
  return (
    <div>
      <IntelligenceRadarChart data={result.visualizations.radar_chart_data} />
      <RecommendationsList recommendations={result.recommendations.recommendations} />
    </div>
  );
}
```

## Tests et Validation

### Tests unitaires

```bash
python -m pytest tests/test_intelligence.py -v
```

### Tests d'intégration

```bash
python test_intelligence_simple.py
```

### Test manuel de l'API

```bash
# Vérifier que le serveur fonctionne
curl http://localhost:8000/api/v1/intelligence/health

# Tester le calcul
python scripts/test_intelligence_api.py
```

## Dépannage

### Problèmes courants

1. **Module scipy non trouvé** :
   ```bash
   pip install scipy
   ```

2. **Erreur d'import** :
   ```bash
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   ```

3. **API non accessible** :
   - Vérifier que le serveur est démarré
   - Vérifier les logs d'erreur
   - Vérifier les permissions CORS

### Logs et Debug

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Utiliser le calculateur avec debug
calculator = IntelligenceCalculator(debug=True)
```

## Ressources

- **Documentation complète** : `docs/intelligence_measurement_methodology.md`
- **Exemples de code** : `examples/intelligence_examples.py`
- **Tests** : `tests/test_intelligence.py`
- **API Reference** : http://localhost:8000/docs

## Support

Pour toute question ou problème :
1. Consulter la documentation
2. Vérifier les tests d'intégration
3. Ouvrir une issue sur le repository
4. Contacter l'équipe de développement