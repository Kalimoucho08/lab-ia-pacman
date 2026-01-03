# Lab IA Pacman

Un laboratoire d'intelligence artificielle centré sur Pacman, conçu pour l'expérimentation d'algorithmes d'apprentissage par renforcement (RL) dans un environnement simplifié.

## Fonctionnalités

- **Environnements Pac‑Man** :
  - `PacManDuelEnv` : Environnement Gymnasium avec Pac‑Man et un fantôme, grille 10x10, points à collecter, pénalités de collision. Idéal pour l'apprentissage par renforcement.
  - `PacManConfigurableEnv` : Environnement mono‑agent configurable (taille, murs, nombre de fantômes, récompenses, comportement des fantômes).
  - `PacManMultiAgentEnv` : Environnement multi‑agent basé sur PettingZoo, avec power pellets, récompenses distinctes par agent, et gestion de la vulnérabilité des fantômes.
- **Power pellets** :
  - Boules spéciales qui rendent les fantômes vulnérables pendant une durée configurable (5‑30 steps).
  - Les fantômes changent de couleur et fuient Pac‑Man.
  - Récompenses ajustées (Pac‑Man gagne des points en mangeant un fantôme vulnérable).
- **Agents** :
  - Agent aléatoire (`RandomAgent`) comme baseline.
  - Intégration avec Stable‑Baselines3 (DQN, PPO, A2C, SAC, TD3) pour l'entraînement RL.
  - Possibilité d'entraîner séparément Pac‑Man et les fantômes (partage de poids entre fantômes).
- **Interface graphique avancée** :
  - Dashboard Tkinter avec onglets (Configuration, Entraînement, Visualisation, Multi‑Agent, Analyse).
  - Contrôles d'entraînement, graphiques en temps réel, logs.
  - Possibilité de sauvegarder/charger des modèles, ajuster les hyperparamètres.
  - Onglet Multi‑Agent : configuration des power pellets, sélection des algorithmes par agent, statistiques par agent.
- **Visualisations** :
  - Visualisation Pygame intégrée pour l'environnement configurable (`visual_pacman_advanced.py`).
  - Visualisation multi‑agent avec chargement de modèles (`visual_pacman_multiagent.py`).
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

### Utilisation avancée : Multi‑Agent et Power Pellets

#### Interface graphique multi‑agent
Lancez l'interface avancée avec l'onglet Multi‑Agent :
```bash
python main_advanced.py
```
Dans l'onglet "Multi‑Agent", vous pouvez :
- Configurer la durée des power pellets (5‑30 steps) et leur nombre (0‑5).
- Définir les récompenses pour Pac‑Man (point, fantôme vulnérable, mort) et pour les fantômes (manger Pac‑Man, éviter Pac‑Man).
- Choisir un algorithme RL pour Pac‑Man et un autre pour les fantômes (DQN, PPO, A2C, SAC, TD3).
- Activer le partage de poids entre fantômes.
- Lancer une simulation multi‑agent avec visualisation Pygame.

#### Entraînement séparé des agents
Pour entraîner Pac‑Man seul (les fantômes ont un comportement aléatoire) :
```bash
python train_pacman_multiagent.py --agent pacman --algorithm DQN --timesteps 10000
```
Pour entraîner les fantômes (partage de poids) :
```bash
python train_pacman_multiagent.py --agent ghosts --algorithm PPO --timesteps 10000
```

#### Visualisation multi‑agent avec modèles chargés
```bash
python visual_pacman_multiagent.py --num_ghosts 2 --power_duration 10 --num_power 2 --pacman_model logs/pacman_DQN_multiagent.zip --ghost_model logs/ghosts_PPO_multiagent.zip
```

### Tests
Exécutez la suite de tests unitaires :
```bash
pytest tests/ -v
```

## Structure du projet

```
.
├── main.py                    # Point d'entrée de l'interface graphique
├── main_advanced.py           # Interface avancée avec onglets (configuration, entraînement, visualisation, multi‑agent, analyse)
├── visual_pacman.py           # Visualisation Pygame de l'environnement duel
├── visual_pacman_advanced.py  # Visualisation avec environnement configurable
├── visual_pacman_multiagent.py # Visualisation multi‑agent avec power pellets
├── train_pacman_multiagent.py # Script d'entraînement multi‑agent
├── src/
│   ├── main_gui.py           # GUI (identique à main.py)
│   ├── run_pacman.py         # Runner minimal avec agent aléatoire
│   ├── pacman_env/
│   │   ├── duel_env.py       # Environnement Pac‑Man vs fantôme (duel)
│   │   ├── configurable_env.py # Environnement mono‑agent configurable
│   │   ├── multiagent_env.py   # Environnement multi‑agent avec power pellets
│   │   ├── multiagent_wrappers.py # Wrappers pour entraînement single‑agent
│   │   └── __init__.py       # Export des environnements
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
├── plans/                    # Plans de développement
│   ├── laboratoire_pacman_avance.md
│   └── multiagent_pacman_plan.md
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
