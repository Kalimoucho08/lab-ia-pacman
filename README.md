# Lab IA Pacman

Un laboratoire d'intelligence artificielle centré sur Pacman, conçu pour l'expérimentation d'algorithmes d'apprentissage par renforcement (RL) dans un environnement simplifié.

## Fonctionnalités

- **Environnement Pacman** :
  - `PacManDuelEnv` : Environnement Gymnasium avec Pac-Man et un fantôme, grille 10x10, points à collecter, pénalités de collision. Idéal pour l'apprentissage par renforcement.
- **Agents** :
  - Agent aléatoire (`RandomAgent`) comme baseline.
  - Intégration avec Stable-Baselines3 (DQN, PPO) pour l'entraînement RL.
- **Interface graphique** :
  - Dashboard Tkinter avec contrôles d'entraînement, graphiques en temps réel, logs.
  - Possibilité de sauvegarder/charger des modèles, ajuster les hyperparamètres.
- **Tests unitaires** :
  - Couverture des environnements et agents.
- **Notebooks pédagogiques** :
  - Exemples d'utilisation dans Jupyter (à compléter).

## Installation

### Prérequis
- Python 3.9 ou supérieur (testé avec 3.14)
- pip

### Étapes

1. Cloner le dépôt (ou extraire l'archive)
2. Créer un environnement virtuel (recommandé) :
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # Windows PowerShell
   # ou sur Linux/Mac :
   # source .venv/bin/activate
   ```
3. Installer les dépendances :
   ```powershell
   pip install -r requirements.txt
   ```
   Les dépendances incluent `gymnasium`, `stable-baselines3`, `torch`, `pygame-ce`, `matplotlib`, `tkinter` (inclus avec Python).

## Utilisation

### Interface graphique (recommandée)
Lancez l'application principale :
```bash
python main.py
```
Ou depuis le module :
```bash
python -m src.main_gui
```

**Fonctionnalités de la GUI** :
- **Entraîner** : Lance l'entraînement d'un modèle DQN ou PPO avec les paramètres choisis.
- **Pause** : Interrompt l'entraînement.
- **Tester** : Exécute un épisode avec le modèle actuel et affiche le score.
- **Sauvegarder/Charger** : Persistance des modèles.
- **Graphiques** : Visualisation en temps réel des récompenses et longueurs d'épisode.
- **Logs** : Messages d'information et d'erreur.

### Exécution en ligne de commande
Pour un runner minimal avec un agent aléatoire :
```bash
python -m src.run_pacman
```
Vous pouvez modifier le script `src/run_pacman.py` pour changer l'agent ou l'environnement.

### Tests
Exécutez la suite de tests unitaires :
```bash
pytest tests/ -v
```

## Structure du projet

```
.
├── main.py                    # Point d'entrée de l'interface graphique
├── src/
│   ├── main_gui.py           # GUI (identique à main.py)
│   ├── run_pacman.py         # Runner minimal avec agent aléatoire
│   ├── pacman_env/
│   │   └── duel_env.py       # Environnement Pac-Man vs fantôme (duel)
│   ├── agents/
│   │   └── random_agent.py   # Agent aléatoire
│   └── utils/
│       └── helpers.py        # Fonctions utilitaires
├── tests/
│   └── test_env.py           # Tests unitaires
├── notebooks/
│   └── intro.ipynb           # Notebook pédagogique (à compléter)
├── requirements.txt          # Dépendances Python
├── pyproject.toml            # Configuration du projet
└── README.md                 # Ce fichier
```

## Développement

### Ajouter un nouvel agent
Créez un fichier dans `src/agents/` qui implémente une classe avec une méthode `act(observation)` et optionnellement `reset()`. Voir `random_agent.py` pour un exemple.

### Ajouter un nouvel environnement
Créez une classe héritant de `gymnasium.Env` dans `src/pacman_env/`. Implémentez `reset()`, `step()`, `render()` et définissez `action_space` et `observation_space`. Référez-vous à `duel_env.py`.

### Améliorer la GUI
La classe `IALab` dans `main.py` peut être étendue pour ajouter de nouvelles fonctionnalités (ex : visualisation de la grille, comparaison d'algorithmes).

## Problèmes connus

- L'entraînement peut être lent sur CPU (pas de GPU requis).
- L'environnement `PacManDuelEnv` est simplifié et peut ne pas être suffisamment complexe pour des algorithmes RL avancés.
- La GUI peut geler pendant l'entraînement long (l'entraînement s'exécute dans un thread séparé, mais les mises à jour de l'interface sont limitées à toutes les 10 épisodes).

## Contribuer

Les contributions sont les bienvenues ! Ouvrez une issue pour discuter des changements proposés, ou soumettez une pull request.

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` (à créer) pour plus de détails.

## Remerciements

- Basé sur [Gymnasium](https://gymnasium.farama.org/) et [Stable-Baselines3](https://stable-baselines3.readthedocs.io/).
- Inspiré par le classique jeu Pac-Man de Namco.
