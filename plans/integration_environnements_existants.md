# Plan d'Intégration des Environnements Existants

## Analyse des Composants Existants

### Environnements Disponibles
1. **`PacManConfigurableEnv`** (`src/pacman_env/configurable_env.py`)
   - Grille configurable (taille, murs, fantômes, points)
   - Comportements fantômes (random, chase, scatter)
   - Système de vies et récompenses configurables
   - Observation shape: (size, size, 4)

2. **`PacManMultiAgentEnv`** (`src/pacman_env/multiagent_env.py`)
   - Environnement PettingZoo ParallelEnv
   - Support power pellets et vulnérabilité
   - Multi-agent avec agents distincts (pacman, ghost_0, ghost_1...)
   - Observation shape: (size, size, 6)

3. **`SingleAgentWrapper`** (`src/pacman_env/multiagent_wrappers.py`)
   - Wrapper pour isoler un agent dans un environnement multi-agent
   - Permet d'entraîner un agent spécifique

4. **`PacManDuelEnv`** (`src/pacman_env/duel_env.py`)
   - Environnement simplifié (obsolète, à déprécier)

### Agents Disponibles
1. **`RandomAgent`** (`src/agents/random_agent.py`)
   - Agent aléatoire de base

### Outils de Visualisation
1. **`visual_pacman_advanced.py`**
   - Visualisation Pygame avec paramètres configurables
   - Support des modèles Stable-Baselines3

2. **`main_advanced.py`**
   - Interface Tkinter avec 5 onglets
   - Configuration, entraînement, visualisation, multi-agent, analyse

## Stratégie d'Intégration

### Principe : Adapter sans Réécrire
- Conserver 70% du code existant
- Créer des wrappers d'adaptation pour l'API web
- Exposer les fonctionnalités via services

### 1. Service d'Environnement
```python
# backend/app/services/environment_service.py
class EnvironmentService:
    def create_env(self, config: EnvironmentConfig) -> gym.Env:
        """Crée un environnement basé sur la configuration"""
        if config.type == "configurable":
            return PacManConfigurableEnv(**config.params)
        elif config.type == "multiagent":
            return PacManMultiAgentEnv(**config.params)
    
    def get_env_state(self, env) -> Dict:
        """Extrait l'état de l'environnement pour sérialisation"""
        return {
            "pacman_pos": env.pacman_pos,
            "ghost_positions": env.ghost_positions,
            "dots": env.dots.tolist(),
            "current_step": env.current_step,
            "current_lives": env.current_lives
        }
    
    def render_to_image(self, env, mode="rgb_array") -> bytes:
        """Rend l'environnement en image PNG"""
        # Utiliser le rendu existant adapté
        pass
```

### 2. Adapter les Environnements pour l'API

#### Modifications Minimales à `PacManConfigurableEnv`
1. Ajouter une méthode `to_dict()` pour sérialisation
2. Ajouter une méthode `from_dict(cls, data)` pour désérialisation
3. Standardiser les paramètres de configuration

```python
# Modification proposée
def to_dict(self):
    return {
        "type": "configurable",
        "params": {
            "size": self.size,
            "walls": self.walls,
            "num_ghosts": self.num_ghosts,
            "num_dots": self.num_dots,
            "pacman_start_position": self.pacman_start_position,
            "lives": self.lives,
            "max_steps": self.max_steps,
            "ghost_behavior": self.ghost_behavior,
            "reward_structure": self.reward_structure
        }
    }

@classmethod
def from_dict(cls, data):
    return cls(**data["params"])
```

#### Adapter `PacManMultiAgentEnv`
1. Même approche avec sérialisation
2. Gérer la conversion PettingZoo → Gymnasium pour compatibilité

### 3. Service d'Agents

```python
# backend/app/services/agent_service.py
class AgentService:
    def create_agent(self, config: AgentConfig) -> BaseAgent:
        """Crée un agent basé sur la configuration"""
        if config.type == "random":
            return RandomAgent(action_space=config.action_space)
        elif config.type == "sb3":
            return SB3AgentWrapper(
                algorithm=config.algorithm,
                policy=config.policy,
                env=config.env,
                **config.hyperparams
            )
    
    def load_agent(self, path: str) -> BaseAgent:
        """Charge un agent depuis un fichier"""
        # Support des formats .zip (SB3), .pth (PyTorch), .h5 (Keras)
        pass
```

### 4. Wrapper Stable-Baselines3

```python
# src/agents/sb3_agent.py
class SB3AgentWrapper:
    """Wrapper unifié pour les agents Stable-Baselines3"""
    
    def __init__(self, algorithm="DQN", policy="MlpPolicy", env=None, **hyperparams):
        self.algorithm = algorithm
        self.policy = policy
        self.hyperparams = hyperparams
        
        if algorithm == "DQN":
            self.model = DQN(policy, env, **hyperparams)
        elif algorithm == "PPO":
            self.model = PPO(policy, env, **hyperparams)
        # ... autres algorithmes
    
    def act(self, observation, deterministic=True):
        return self.model.predict(observation, deterministic=deterministic)
    
    def learn(self, total_timesteps, callback=None):
        self.model.learn(total_timesteps, callback=callback)
    
    def save(self, path):
        self.model.save(path)
    
    @classmethod
    def load(cls, path, env=None):
        # Détection automatique de l'algorithme
        pass
```

### 5. Service de Visualisation

Adapter `visual_pacman_advanced.py` pour :
1. Générer des frames sans fenêtre Pygame
2. Exporter en PNG/JPEG pour le frontend
3. Support du streaming via WebSocket

```python
# backend/app/services/visualization_service.py
class VisualizationService:
    def __init__(self):
        self.renderer = PygameRenderer(headless=True)
    
    def render_frame(self, env_state: Dict, config: RenderConfig) -> bytes:
        """Rend une frame à partir de l'état de l'environnement"""
        # Créer une surface Pygame en mémoire
        # Dessiner la grille, agents, points
        # Convertir en PNG
        return png_bytes
    
    def create_animation(self, episode_states: List[Dict], fps: int) -> bytes:
        """Crée une animation GIF/MP4 à partir d'une séquence d'états"""
        pass
```

## Points d'Intégration Détaillés

### API REST pour les Environnements
```
POST /api/v1/environments
{
    "type": "configurable",
    "params": {
        "size": 12,
        "num_ghosts": 2,
        "walls": [[3,3], [3,4], [4,3]],
        ...
    }
}

Response:
{
    "env_id": "env_abc123",
    "observation_space": {"shape": [12, 12, 4], "type": "Box"},
    "action_space": {"n": 4, "type": "Discrete"}
}
```

### WebSocket pour les Mises à Jour Temps Réel
```javascript
// Frontend
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'training_progress') {
        updateCharts(data.metrics);
    } else if (data.type === 'game_state') {
        updateVisualizer(data.state);
    }
};
```

### Base de Données pour les Expériences
```sql
-- Table experiments
CREATE TABLE experiments (
    id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    config JSON,
    created_at TIMESTAMP,
    status TEXT,  -- 'pending', 'running', 'completed', 'failed'
    metrics JSON,  -- Métriques finales
    intelligence_score FLOAT
);

-- Table training_runs
CREATE TABLE training_runs (
    id TEXT PRIMARY KEY,
    experiment_id TEXT,
    step INTEGER,
    metrics JSON,
    timestamp TIMESTAMP
);
```

## Migration Progressive

### Étape 1 : Préparer les Environnements
1. Ajouter les méthodes de sérialisation aux environnements existants
2. Créer des tests de validation
3. Documenter les changements d'API

### Étape 2 : Créer les Services de Base
1. Implémenter `EnvironmentService`
2. Implémenter `AgentService`
3. Créer l'API REST de base

### Étape 3 : Intégrer l'Entraînement
1. Adapter `TrainingCallback` pour WebSocket
2. Créer le service d'entraînement asynchrone
3. Implémenter l'arrêt/redémarrage

### Étape 4 : Visualisation Web
1. Adapter le rendu Pygame pour headless
2. Créer le service de visualisation
3. Implémenter le streaming WebSocket

## Tests d'Intégration

### Scénarios à Tester
1. **Création d'environnement** : Config → Environnement fonctionnel
2. **Sérialisation** : Environnement → JSON → Environnement (roundtrip)
3. **Entraînement** : Démarrage, progression, sauvegarde
4. **Visualisation** : Génération de frames, performance
5. **API** : Endpoints REST, erreurs, validation

### Benchmarks de Performance
- Latence création environnement : < 50ms
- Génération frame : < 16ms (60 FPS)
- Transmission WebSocket : < 10ms
- Sauvegarde modèle : < 100ms

## Gestion des Échecs

### Fallbacks en Cas de Problème
1. **Pygame non disponible** : Rendu ASCII via API
2. **Stable-Baselines3 échec** : Retour à RandomAgent avec notification
3. **WebSocket déconnecté** : Fallback polling HTTP
4. **GPU non disponible** : CPU-only avec warning

### Monitoring
- Logs structurés avec JSON
- Métriques de performance
- Alertes sur erreurs critiques
- Dashboard de santé des services

## Documentation à Produire

### Pour les Développeurs
1. Guide d'intégration des nouveaux environnements
2. API Reference (OpenAPI/Swagger)
3. Guide de contribution

### Pour les Utilisateurs
1. Guide des paramètres avec exemples
2. Tutoriel pas à pas
3. FAQ et dépannage

## Calendrier d'Implémentation

### Semaine 1-2 : Fondations
- [ ] Services d'environnement et agents
- [ ] API REST de base
- [ ] Tests d'intégration

### Semaine 3-4 : Entraînement & Visualisation
- [ ] Service d'entraînement asynchrone
- [ ] Adaptation du rendu Pygame
- [ ] WebSocket pour temps réel

### Semaine 5-6 : Interface Utilisateur
- [ ] Composants React de base
- [ ] Connexion à l'API
- [ ] Graphiques et visualiseur

### Semaine 7-8 : Fonctionnalités Avancées
- [ ] Système d'expérimentation
- [ ] Calculateur d'intelligence
- [ ] Export ONNX

### Semaine 9-10 : Polissage
- [ ] Documentation
- [ ] Tests complets
- [ ] Optimisations performance

## Métriques de Réussite

### Technique
- 95% de couverture de code
- 0 regression sur les fonctionnalités existantes
- Latence < 100ms pour les opérations critiques

### Utilisateur
- Interface intuitive (test utilisateur)
- Documentation complète
- Support multi-navigateurs

### Maintenance
- Code modulaire et testable
- Documentation des APIs
- Procédures de déploiement