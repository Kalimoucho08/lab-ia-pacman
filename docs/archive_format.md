# Format d'archive intelligent - Laboratoire Scientifique IA Pac-Man

## Introduction

Ce document décrit le format d'archive intelligent utilisé par le système de sauvegarde automatique du laboratoire scientifique IA Pac-Man. Ce format est conçu pour stocker de manière organisée et intelligible les sessions d'entraînement, les modèles RL, les métadonnées et les configurations.

## Structure d'archive

### Nommage des archives

Les archives suivent un format de nommage intelligent permettant une identification rapide :

```
pacman_run_{session_number:03d}_{timestamp}_{model_type}_{agent_type}.zip
```

**Exemple :**
```
pacman_run_047_20260103_1632_DQN_pacman.zip
```

**Composants :**
- `pacman_run_` : Préfixe identifiant le type d'archive
- `047` : Numéro de session sur 3 chiffres
- `20260103_1632` : Timestamp (AAAAMMJJ_HHMM)
- `DQN` : Type de modèle (abréviation)
- `pacman` : Type d'agent
- `.zip` : Extension d'archive

### Structure interne

```
archive.zip/
├── params.md                    # Documentation des paramètres avec explications
├── metadata.json                # Métadonnées structurées au format JSON
├── config.yaml                  # Configuration au format YAML
├── model/                       # Répertoire des fichiers de modèle (optionnel)
│   ├── model.zip                # Modèle RL (format Stable-Baselines3)
│   ├── model_architecture.json  # Architecture du modèle
│   └── model_weights.h5         # Poids du modèle (si applicable)
├── logs/                        # Répertoire des logs (optionnel)
│   ├── training.log             # Logs d'entraînement
│   ├── metrics.json             # Métriques détaillées
│   └── events.out.tfevents      # Événements TensorBoard (si applicable)
└── checksum.md5                 # Hash MD5 pour vérification d'intégrité
```

## Fichiers détaillés

### 1. params.md

Fichier Markdown contenant une documentation intelligente des paramètres avec explications contextuelles.

**Format :**
```markdown
# Session 47 - Lancée 03/01/26 16h32

## Paramètres d'entraînement

- **Learning Rate**: 0.001 (moyen → stable, bon compromis)
- **Gamma**: 0.99 (fort → planifie loin dans le futur)
- **Epsilon**: 0.1 (modéré → équilibre exploration/exploitation)
- **Batch Size**: 64
- **Buffer Size**: 10000

## Métriques de performance

- **Épisodes totaux**: 5000
- **Taux de victoire**: 77.00%

## Comparaison avec session précédente

- **Épisodes**: +2000 vs session 46
- **Taux de victoire**: +12.00% (65.00% → 77.00%)

## Observation

Amélioration significative ! La configuration actuelle semble très efficace.

## Tags

`DQN`, `pacman`, `best_performance`, `auto_save`

## Notes

Convergence observée après 3000 épisodes. Winrate stable depuis 1000 épisodes.
```

### 2. metadata.json

Fichier JSON contenant les métadonnées structurées de la session.

**Format :**
```json
{
  "session_id": "pacman_run_047",
  "session_number": 47,
  "timestamp": "2026-01-03T16:32:00Z",
  "model_type": "DQN",
  "agent_type": "pacman",
  "hyperparameters": {
    "learning_rate": 0.001,
    "gamma": 0.99,
    "epsilon": 0.1,
    "batch_size": 64,
    "buffer_size": 10000
  },
  "metrics": {
    "win_rate": 0.77,
    "total_episodes": 5000,
    "average_score": 1800,
    "best_score": 2500,
    "training_time_hours": 2.5
  },
  "tags": ["DQN", "pacman", "best_performance", "auto_save"],
  "previous_session_id": "pacman_run_046",
  "notes": "Convergence observée après 3000 épisodes"
}
```

### 3. config.yaml

Fichier YAML contenant la configuration de la session.

**Format :**
```yaml
session:
  id: "pacman_run_047"
  number: 47
  timestamp: "2026-01-03T16:32:00Z"
  algorithm: "DQN"
  agent_type: "pacman"

hyperparameters:
  learning_rate: 0.001
  gamma: 0.99
  epsilon: 0.1
  batch_size: 64
  buffer_size: 10000

environment:
  grid_size: 15
  num_ghosts: 4
  power_pellets: 4
  pellet_density: 0.8

training:
  total_episodes: 5000
  max_steps_per_episode: 1000
  save_interval: 1000
  evaluation_interval: 100

tags:
  - DQN
  - pacman
  - best_performance
  - auto_save
```

### 4. Modèles RL

Les modèles sont stockés dans le format natif de Stable-Baselines3 :

- **Format principal** : `.zip` (format par défaut de Stable-Baselines3)
- **Architecture** : `model_architecture.json` (si applicable)
- **Poids** : `model_weights.h5` (pour les modèles Keras/TensorFlow)

**Compatibilité :**
- Stable-Baselines3 `.zip` format
- TensorFlow SavedModel (optionnel)
- PyTorch `.pt` (optionnel)

### 5. Logs et métriques

**Fichiers de logs :**
- `training.log` : Logs textuels de l'entraînement
- `metrics.json` : Métriques structurées au format JSON
- `events.out.tfevents` : Événements TensorBoard (pour visualisation)

**Métriques standard :**
```json
{
  "episode_rewards": [1500, 1600, 1800, ...],
  "episode_lengths": [200, 210, 195, ...],
  "win_rates": [0.5, 0.55, 0.6, ...],
  "losses": [0.1, 0.08, 0.06, ...],
  "exploration_rate": [0.1, 0.095, 0.09, ...]
}
```

## Système de sauvegarde automatique

### Conditions de sauvegarde

Le système effectue des sauvegardes automatiques dans les cas suivants :

1. **Périodique** : Tous les N épisodes (configurable, par défaut 1000)
2. **Sur amélioration** : Lorsque le winrate s'améliore de plus de 5%
3. **À la fin** : À la fin de chaque session d'entraînement
4. **Manuelle** : Via l'interface utilisateur ou l'API

### Gestion des versions

Chaque archive reçoit automatiquement :
- Un numéro de version incrémental
- Des tags basés sur les performances
- Une catégorie (best, experimental, baseline)
- Un score de performance calculé

### Compression intelligente

Le système utilise une compression optimisée :
- **Niveau de compression** : Configurable (1-9, par défaut 6)
- **Déduplication** : Suppression des doublons entre sessions
- **Différentielle** : Stockage des différences avec sessions précédentes
- **Gzip pour logs** : Compression spécifique pour les fichiers texte

## Reprise de sessions

### Format de reprise

Les archives peuvent être reprises pour :
1. **Continuer l'entraînement** : Reprendre à partir du dernier point de sauvegarde
2. **Analyse comparative** : Comparer différentes sessions
3. **Fusion** : Combiner les meilleurs aspects de plusieurs sessions

### Script de reprise automatique

Chaque archive contient un script de reprise généré automatiquement :

```python
# resume_session.py
import json
import yaml
from stable_baselines3 import DQN

# Charger la configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Charger le modèle
model = DQN.load('model/model.zip')

# Reprendre l'entraînement
print(f"Reprise de la session {config['session']['number']}")
print(f"Hyperparamètres: {config['hyperparameters']}")
```

## Intégration avec le système existant

### Backend FastAPI

Le système d'archivage s'intègre avec le backend existant via :

1. **API REST** : Endpoints pour la gestion des archives
2. **WebSocket** : Notifications en temps réel des sauvegardes
3. **Base de données** : Métadonnées stockées dans la base de données

**Endpoints disponibles :**
- `GET /api/v1/archives/` : Lister les archives
- `POST /api/v1/archives/` : Créer une nouvelle archive
- `GET /api/v1/archives/{archive_path}` : Obtenir des informations
- `POST /api/v1/archives/restore` : Restaurer une session
- `POST /api/v1/archives/compare` : Comparer deux sessions

### Frontend React

L'interface utilisateur permet :
- Visualisation des archives disponibles
- Restauration de sessions en un clic
- Comparaison graphique des performances
- Gestion des tags et catégories

## Validation et intégrité

### Vérifications automatiques

Chaque archive est validée automatiquement :

1. **Intégrité** : Vérification du hash MD5
2. **Structure** : Vérification des fichiers requis
3. **Contenu** : Validation des formats JSON/YAML
4. **Compatibilité** : Vérification de la compatibilité des modèles

### Rapport de validation

```json
{
  "archive": "pacman_run_047_20260103_1632_DQN_pacman.zip",
  "validation_result": {
    "is_valid": true,
    "errors": [],
    "warnings": ["Fichier de hash manquant"],
    "structure_score": 0.95,
    "content_score": 0.98
  },
  "files": {
    "present": ["params.md", "metadata.json", "config.yaml", "model/model.zip"],
    "missing": [],
    "corrupted": []
  }
}
```

## Migration depuis l'ancien système

### Compatibilité ascendante

Le nouveau format est compatible avec :
- Archives existantes au format ZIP simple
- Modèles Stable-Baselines3 existants
- Logs au format texte/JSON existants

### Outil de migration

Un script de migration automatique est fourni :

```bash
python -m experiments.migration_tool --input old_archive.zip --output new_archive.zip
```

## Bonnes pratiques

### Organisation des archives

1. **Nommage cohérent** : Suivre le format standard
2. **Tags descriptifs** : Utiliser des tags significatifs
3. **Documentation complète** : Remplir tous les champs de params.md
4. **Compression appropriée** : Adapter le niveau de compression à l'usage

### Gestion de l'espace

1. **Nettoyage automatique** : Configurer la rétention des archives
2. **Compression différentielle** : Pour les sessions similaires
3. **Archivage distant** : Sauvegarde vers cloud/local secondaire

### Sécurité

1. **Vérification d'intégrité** : Toujours vérifier les hashs
2. **Signature numérique** : Optionnelle pour les archives critiques
3. **Accès contrôlé** : Via l'API avec authentification

## Exemples d'utilisation

### Création d'archive via Python

```python
from experiments.archive_service import IntelligentArchiveService, ArchiveMetadata

service = IntelligentArchiveService()

metadata = ArchiveMetadata(
    session_id="my_session",
    session_number=1,
    model_type="DQN",
    agent_type="pacman",
    total_episodes=1000,
    win_rate=0.75,
    learning_rate=0.001,
    gamma=0.99,
    epsilon=0.1,
    batch_size=32,
    buffer_size=10000,
    tags=['test', 'DQN'],
    metrics={'avg_score': 1500}
)

archive_path = service.create_archive(metadata, "path/to/model.zip")
```

### Reprise via API REST

```bash
# Lister les archives
curl -X GET "http://localhost:8000/api/v1/archives/"

# Restaurer une session
curl -X POST "http://localhost:8000/api/v1/archives/restore" \
  -H "Content-Type: application/json" \
  -d '{
    "archive_path": "experiments/archives/pacman_run_047_20260103_1632_DQN_pacman.zip",
    "target_dir": "experiments/resumed_session_047"
  }'
```

## Conclusion

Le format d'archive intelligent fournit une solution robuste et organisée pour la sauvegarde des sessions d'entraînement RL. Il combine documentation intelligente, métadonnées structurées, compression optimisée et intégration transparente avec l'écosystème existant du laboratoire scientifique IA Pac-Man.

Ce format évoluera avec les besoins du projet, tout en maintenant la compatibilité avec les archives existantes.