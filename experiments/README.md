# Système de Sauvegarde Automatique Intelligente

## Vue d'ensemble

Ce module implémente un système de sauvegarde automatique intelligente pour le laboratoire scientifique IA Pac-Man. Il permet la création, la gestion et la reprise d'archives de sessions d'entraînement RL avec métadonnées enrichies, documentation intelligente et compression optimisée.

## Architecture

```
experiments/
├── archive_service.py          # Service principal d'archivage
├── metadata_generator.py       # Générateur de métadonnées intelligentes
├── session_resumer.py          # Système de reprise de sessions
├── version_manager.py          # Gestionnaire de versions
├── compression_optimizer.py    # Optimisation de compression
├── archive_validator.py        # Validation d'archives
├── README.md                   # Cette documentation
└── archives/                   # Répertoire des archives (créé automatiquement)
```

## Fonctionnalités

### 1. Archivage Intelligent
- **Nommage automatique** : `pacman_run_047_20260103_1632_DQN_pacman.zip`
- **Structure organisée** : Modèle, params.md, metadata.json, config.yaml
- **Documentation contextuelle** : Explications intelligentes des paramètres
- **Compression optimisée** : Gestion efficace de l'espace

### 2. Sauvegarde Automatique
- **Périodique** : Tous les N épisodes (configurable)
- **Sur amélioration** : Lorsque les métriques s'améliorent significativement
- **Événementielle** : À la fin de l'entraînement, manuellement via interface
- **Intelligente** : Détection d'anomalies et sauvegarde préventive

### 3. Reprise de Sessions
- **Chargement d'archives** : Restauration complète des sessions
- **Comparaison** : Analyse des différences entre sessions
- **Fusion** : Combinaison de plusieurs sessions pour méta-analyse
- **Continuation** : Reprise de l'entraînement à partir d'un point de sauvegarde

### 4. Gestion des Versions
- **Numérotation automatique** : Incrémentation des numéros de session
- **Tags et catégories** : Classification automatique (best, experimental, baseline)
- **Recherche avancée** : Filtrage par métriques, tags, dates
- **Migration** : Compatibilité avec l'ancien système

### 5. Validation et Intégrité
- **Vérification d'intégrité** : Hash MD5 pour détection de corruption
- **Validation de structure** : Vérification des fichiers requis
- **Validation de contenu** : Vérification des formats JSON/YAML
- **Rapports détaillés** : Diagnostics complets des archives

## Utilisation

### Installation

Aucune installation supplémentaire requise. Les dépendances sont incluses dans le projet principal.

### Création d'une archive

```python
from experiments.archive_service import IntelligentArchiveService, ArchiveMetadata

# Initialiser le service
service = IntelligentArchiveService()

# Préparer les métadonnées
metadata = ArchiveMetadata(
    session_id="my_session_001",
    session_number=0,  # Sera auto-incrémenté
    model_type="DQN",
    agent_type="pacman",
    total_episodes=5000,
    win_rate=0.77,
    learning_rate=0.001,
    gamma=0.99,
    epsilon=0.1,
    batch_size=64,
    buffer_size=10000,
    tags=['DQN', 'pacman', 'baseline'],
    metrics={'avg_score': 1800, 'best_score': 2500},
    notes="Session de test avec configuration baseline"
)

# Créer l'archive
archive_path = service.create_archive(
    metadata=metadata,
    model_path="path/to/model.zip",  # Optionnel
    log_patterns=["logs/*.log", "logs/*.json"]  # Optionnel
)

print(f"Archive créée: {archive_path}")
```

### Sauvegarde automatique

```python
# Dans une boucle d'entraînement
for episode in range(total_episodes):
    # ... entraînement ...
    
    # Sauvegarde automatique tous les 1000 épisodes
    if episode % 1000 == 0:
        metrics = {
            'win_rate': current_win_rate,
            'total_episodes': episode,
            'learning_rate': current_lr,
            'gamma': current_gamma
        }
        
        archive_path = service.auto_save(
            episode=episode,
            metrics=metrics,
            model_path="path/to/current_model.zip",
            force=False  # True pour forcer la sauvegarde
        )
        
        if archive_path:
            print(f"Sauvegarde automatique: {archive_path}")
```

### Reprise d'une session

```python
from experiments.session_resumer import SessionResumer

# Initialiser le système de reprise
resumer = SessionResumer()

# Charger une archive
session_info = resumer.load_archive(
    archive_path="experiments/archives/pacman_run_047_20260103_1632_DQN_pacman.zip",
    target_dir="experiments/resumed_session_047"
)

print(f"Session restaurée: {session_info['session_id']}")
print(f"Fichiers extraits: {len(session_info['extracted_files'])}")

# Comparer deux sessions
comparison = resumer.compare_sessions(
    "archive1.zip",
    "archive2.zip"
)

print(f"Similarité: {comparison.similarity_score:.2f}")
print(f"Différences: {len(comparison.differences)}")
```

### Gestion des versions

```python
from experiments.version_manager import VersionManager

# Initialiser le gestionnaire
manager = VersionManager()

# Enregistrer une nouvelle version
version_info = manager.register_new_version(
    archive_path="path/to/archive.zip",
    metadata={"win_rate": 0.77, "episodes": 5000},
    tags=["best", "DQN", "pacman"]
)

print(f"Version enregistrée: {version_info['version_id']}")

# Rechercher des versions
best_versions = manager.get_best_versions(limit=5)
print(f"Meilleures versions: {len(best_versions)}")

# Exporter les versions
manager.export_versions("versions_export.json")
```

## Intégration avec le Backend

### API REST

Le système s'intègre avec le backend FastAPI via les endpoints :

- `GET /api/v1/archives/` - Lister les archives
- `POST /api/v1/archives/` - Créer une nouvelle archive
- `GET /api/v1/archives/{archive_path}` - Obtenir des informations
- `POST /api/v1/archives/restore` - Restaurer une session
- `POST /api/v1/archives/compare` - Comparer deux sessions
- `POST /api/v1/archives/auto-save` - Sauvegarde automatique
- `POST /api/v1/archives/cleanup` - Nettoyer les anciennes archives
- `POST /api/v1/archives/upload` - Uploader une archive
- `GET /api/v1/archives/best` - Obtenir les meilleures archives

### Exemple d'utilisation via API

```bash
# Lister les archives
curl -X GET "http://localhost:8000/api/v1/archives/?limit=10"

# Créer une archive
curl -X POST "http://localhost:8000/api/v1/archives/" \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "exp_001",
    "model_path": "models/dqn_pacman.zip",
    "metrics": {"win_rate": 0.77, "episodes": 5000},
    "config": {"learning_rate": 0.001, "gamma": 0.99},
    "tags": ["DQN", "pacman", "best"]
  }'

# Restaurer une archive
curl -X POST "http://localhost:8000/api/v1/archives/restore" \
  -H "Content-Type: application/json" \
  -d '{
    "archive_path": "experiments/archives/pacman_run_047.zip",
    "target_dir": "experiments/resumed"
  }'
```

## Configuration

### Service d'archivage

```python
from experiments.archive_service import ArchiveConfig

config = ArchiveConfig(
    archive_dir="experiments/archives",  # Répertoire des archives
    max_archives=100,                    # Nombre maximum d'archives à conserver
    auto_save_interval=1000,             # Intervalle de sauvegarde automatique (épisodes)
    save_on_improvement=True,            # Sauvegarder sur amélioration des métriques
    improvement_threshold=0.05,          # Seuil d'amélioration (5%)
    compression_level=6,                 # Niveau de compression (1-9)
    include_model=True,                  # Inclure les fichiers de modèle
    include_logs=True,                   # Inclure les logs
    include_metrics=True,                # Inclure les métriques
    include_config=True,                 # Inclure la configuration
    backup_to_cloud=False,               # Sauvegarde cloud (optionnel)
    cloud_endpoint=None                  # Endpoint cloud (optionnel)
)

service = IntelligentArchiveService(config=config)
```

## Tests

### Tests unitaires

```bash
# Exécuter les tests simplifiés
python test_simple_archive.py

# Exécuter les tests complets (si disponibles)
python test_archive_system.py
```

### Tests d'intégration

```bash
# Tester l'intégration avec le backend
python -m pytest backend/tests/test_archives.py -v
```

## Format d'archive

Voir la documentation détaillée : [docs/archive_format.md](../docs/archive_format.md)

## Bonnes pratiques

1. **Nommage cohérent** : Utiliser le format standard `pacman_run_XXX_YYYYMMDD_HHMM_ALGO_AGENT.zip`
2. **Documentation complète** : Remplir tous les champs de `params.md`
3. **Tags significatifs** : Utiliser des tags descriptifs pour faciliter la recherche
4. **Validation régulière** : Vérifier l'intégrité des archives périodiquement
5. **Nettoyage automatique** : Configurer la rétention des archives pour éviter l'accumulation

## Dépannage

### Problèmes courants

1. **Erreur "Archive non trouvée"** : Vérifier le chemin et les permissions
2. **Erreur de validation** : Vérifier la structure et le format des fichiers
3. **Espace disque insuffisant** : Configurer `max_archives` ou activer la compression
4. **Problèmes de compatibilité** : Vérifier les versions des bibliothèques

### Logs

Les logs sont disponibles dans :
- `experiments/archive_service.log` - Logs du service d'archivage
- `backend.log` - Logs du backend (intégration API)

## Évolution future

- [ ] Support pour d'autres formats de modèle (PyTorch, JAX)
- [ ] Compression différentielle avancée
- [ ] Intégration avec des services cloud (AWS S3, Google Cloud Storage)
- [ ] Interface graphique dédiée pour la gestion des archives
- [ ] Analyse automatique des tendances et recommandations

## Licence

Ce module fait partie du projet Laboratoire Scientifique IA Pac-Man et est distribué sous la même licence.

## Contact

Pour toute question ou problème, consulter la documentation du projet ou contacter l'équipe de développement.