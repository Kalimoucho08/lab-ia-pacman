# Système d'Expérimentation Backend - Laboratoire Scientifique IA Pac-Man

Backend FastAPI pour le système d'expérimentation RL Pac-Man, fournissant une API REST complète, des WebSockets temps réel, et l'intégration des environnements existants.

## Architecture

```
backend/
├── app.py                    # Application FastAPI principale
├── config.py                 # Configuration et schémas Pydantic (20 paramètres)
├── requirements.txt          # Dépendances Python
├── test_integration.py       # Tests d'intégration
├── services/                 # Services métier
│   ├── experiment_service.py # Gestion des expériences
│   ├── training_service.py   # Entraînement RL avec Stable-Baselines3
│   ├── environment_service.py # Intégration des environnements Pac-Man
│   └── websocket_service.py  # Communication WebSocket temps réel
├── models/                   # Modèles Pydantic
│   ├── experiment.py         # Expériences, sessions, métriques
│   └── (autres modèles)
├── api/v1/endpoints/         # Endpoints API REST
│   ├── experiments.py        # Gestion des expériences
│   ├── training.py           # Entraînement RL
│   ├── environment.py        # Environnements de jeu
│   └── visualization.py      # Visualisation
├── db/                       # Base de données
│   └── database.py           # Gestionnaire SQLite
└── utils/                    # Utilitaires
    └── error_handling.py     # Gestion des erreurs
```

## Fonctionnalités

### 1. API REST Complète
- **Expériences** : CRUD des expériences avec 20 paramètres configurables
- **Entraînement** : Démarrage/arrêt/pause des sessions RL
- **Environnements** : Configuration et création des environnements Pac-Man
- **Visualisation** : Génération de frames et états de jeu

### 2. 20 Paramètres Configurables
Organisés en 4 catégories :
- **Entraînement** : learning_rate, gamma, episodes, batch_size, buffer_size
- **Jeu** : grid_size, num_ghosts, power_pellets, lives, pellet_density
- **Intelligence** : exploration_rate, target_update, learning_starts, train_freq
- **Visualisation** : fps, render_scale, show_grid, show_stats, highlight_path

### 3. Intégration des Environnements Existants
- Réutilisation de 70% du code existant (`src/pacman_env/`)
- Support des environnements configurable et multi-agent
- Validation des paramètres et génération d'états de jeu

### 4. Système d'Entraînement RL
- Support de Stable-Baselines3 (DQN, PPO, A2C, SAC, TD3)
- Entraînement asynchrone avec threads séparés
- Callbacks pour métriques temps réel
- Sauvegarde automatique des modèles

### 5. Communication Temps Réel
- WebSocket pour mises à jour live (métriques, état du jeu)
- Abonnements par canal (metrics, game_state, session_updates)
- Diffusion efficace aux clients connectés

### 6. Base de Données SQLite
- Stockage des expériences, sessions et métriques
- Sauvegarde et restauration automatiques
- Requêtes optimisées avec index

## Installation

### Prérequis
- Python 3.14
- pip (gestionnaire de paquets Python)

### Installation des dépendances
```bash
cd backend
pip install -r requirements.txt
```

### Configuration
Les paramètres par défaut sont dans `config.py`. Pour personnaliser :
1. Créer un fichier `.env` dans le dossier backend
2. Définir les variables d'environnement (voir `config.py`)

## Utilisation

### Démarrer le serveur
```bash
cd backend
python app.py
```

Ou avec uvicorn directement :
```bash
cd backend
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### Accéder à l'API
- **API Documentation** : http://127.0.0.1:8000/docs (Swagger UI)
- **Alternative Docs** : http://127.0.0.1:8000/redoc (ReDoc)
- **Health Check** : http://127.0.0.1:8000/health
- **WebSocket** : ws://127.0.0.1:8000/ws

### Exemples d'utilisation

#### Créer une expérience
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/experiments/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ma première expérience",
    "description": "Test des paramètres par défaut",
    "tags": ["test", "débutant"],
    "preset": "débutant",
    "parameters": {
      "training": {
        "learning_rate": 0.001,
        "gamma": 0.99,
        "episodes": 1000,
        "batch_size": 64,
        "buffer_size": 10000
      },
      "game": {
        "grid_size": 10,
        "num_ghosts": 2,
        "power_pellets": 2,
        "lives": 3,
        "pellet_density": 0.7
      },
      "intelligence": {
        "exploration_rate": 0.1,
        "target_update": 100,
        "learning_starts": 1000,
        "train_freq": 4
      },
      "visualization": {
        "fps": 10,
        "render_scale": 50,
        "show_grid": 1,
        "show_stats": 1,
        "highlight_path": 0
      }
    }
  }'
```

#### Démarrer un entraînement
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/training/sessions/{session_id}/start"
```

#### Se connecter via WebSocket
```javascript
// Exemple JavaScript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connecté au WebSocket');
  // S'abonner aux métriques
  ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'metrics'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Message reçu:', data);
};
```

## Tests

### Exécuter les tests d'intégration
```bash
cd backend
python test_integration.py
```

### Tests unitaires (à développer)
```bash
pytest tests/ -v
```

## Intégration avec le Frontend

Le backend est conçu pour fonctionner avec le frontend React existant :
1. **CORS** configuré pour http://localhost:5173 (Vite dev server)
2. **Endpoints** correspondant aux types TypeScript du frontend
3. **WebSocket** pour les mises à jour temps réel des graphiques

## Déploiement

### Production
Pour le déploiement en production :
1. Désactiver le mode debug : `DEBUG=False`
2. Configurer un serveur ASGI (Uvicorn avec Gunicorn)
3. Mettre en place un reverse proxy (Nginx, Apache)
4. Configurer HTTPS avec certificat SSL

### Docker (optionnel)
Un Dockerfile peut être ajouté pour le conteneurisation :
```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Dépannage

### Problèmes courants

1. **ImportError: cannot import name 'PacManConfigurableEnv'**
   - Vérifier que le chemin `src/pacman_env/` existe
   - Ajouter `sys.path.insert(0, '..')` si nécessaire

2. **Stable-Baselines3 non disponible**
   - L'entraînement RL fonctionnera en mode simulation
   - Installer avec `pip install stable-baselines3`

3. **Erreurs de connexion WebSocket**
   - Vérifier que le serveur est en cours d'exécution
   - Vérifier les paramètres CORS

4. **Problèmes de base de données**
   - Vérifier les permissions d'écriture sur `experiments.db`
   - Exécuter `python -c "from backend.db.database import db_manager; db_manager._init_database()"`

## Contribution

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet fait partie du Laboratoire Scientifique IA Pac-Man. Voir le fichier LICENSE principal pour plus de détails.

## Contact

Pour toute question ou problème, ouvrir une issue sur le dépôt du projet.