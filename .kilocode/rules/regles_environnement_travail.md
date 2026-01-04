# regles_environnement_travail.md

Règles spécifiques au projet lab-ia-pacman et à son environnement de travail (Windows, Python 3.11, VS Code).

## Lignes directrices

- Le répertoire racine est `g:/Drive/bogny/projet-ia-code/lab-ia-pacman`. Utiliser des chemins relatifs à partir de là.
- La console Windows utilise CP1252 : interdiction d'utiliser des caractères Unicode dans les `print` et logs de l'interface. Les fichiers sources doivent être encodés en UTF-8.
- **Utiliser l'environnement virtuel `venv311` (Python 3.11.9) pour le projet lab-ia-pacman.** L'environnement `venv` (Python 3.14.2) est présent mais non utilisé. Vérifier que `venv311` est activé avant d'exécuter des scripts.
- Les environnements multi‑agent sont définis dans `src/pacman_env/multiagent_env.py` et `src/pacman_env/multiagent_wrappers.py`.
- Les boutons "Entraîner Pac‑Man" et "Entraîner les fantômes" doivent lancer un thread séparé pour ne pas bloquer l'interface Tkinter. Vérifier que le thread est `daemon=True` et arrêter proprement l'entraînement si nécessaire.
- Les modèles sauvegardés doivent être placés dans `logs/` avec un nom explicite (ex: `pacman_DQN_<timestamp>.zip`). Inclure les métadonnées (algorithme, paramètres) dans le nom ou un fichier adjacent.
- Le script `visual_pacman_advanced.py` accepte des arguments en ligne de commande pour la configuration ; utiliser `subprocess.Popen` avec `shell=False` pour le lancer. Gérer les chemins avec des chaînes brutes (raw strings) sous Windows.
- Ne pas supposer que `env.ghosts` est une liste (c'est un entier `num_ghosts`). `env.power_pellets` est également un entier. Pour accéder aux positions des fantômes, utiliser `env.ghost_positions` (liste de tuples).
- Les récompenses (`reward_config`) doivent être des dictionnaires avec les clés `pacman` et `ghost`. Chaque sous‑dictionnaire doit contenir au moins les clés suivantes :
  - `pacman` : `dot`, `ghost_eaten`, `death`, `step`, `power_pellet_eaten`
  - `ghost` : `eat_pacman`, `eaten`, `step`, `distance_reward`
- Le wrapper `SingleAgentWrapper` attend un `agent_id` comme `"pacman"` ou `"ghost_0"`. L'argument `other_agent_policy` peut être `"random"`, `"chase"`, `"scatter"` ou `"rl"`.
- Tester les imports avec un petit script avant de lancer l'interface graphique. Utiliser `try/except` pour capturer `ModuleNotFoundError` et afficher un message clair.
- Suivre le style PEP 8 et écrire les docstrings en français. Les noms de variables et de fonctions doivent être en anglais (convention du projet).
- Pour les interactions avec le backend FastAPI, l'URL de base est `http://localhost:8000`. Vérifier que le serveur est en cours d'exécution avant d'envoyer des requêtes.
- Les fichiers temporaires doivent être créés dans le répertoire `temp/` (s'il existe) ou via `tempfile.gettempdir()`. Les supprimer après usage.
- Éviter les chemins absolus dans le code ; utiliser `os.path.join` avec des chemins relatifs au répertoire racine.
- Lors de l'exécution de commandes système, préférer `subprocess.run` pour les commandes synchrones et `subprocess.Popen` pour les asynchrones. Toujours capturer `stdout` et `stderr` pour le débogage.
- Les logs doivent être écrits dans `logs/` avec rotation (voir `logging.handlers.RotatingFileHandler`). Utiliser le niveau `INFO` par défaut.
- Les interfaces graphiques Tkinter doivent être mises à jour via `after()` et non dans des boucles bloquantes.
- Les tests unitaires doivent être placés dans `tests/` et exécutables avec `pytest`. Utiliser des fixtures pour les environnements communs.
- Les dépendances doivent être listées dans `requirements.txt` et `pyproject.toml`. Vérifier la compatibilité avec Python 3.14.
- Les scripts de démarrage (`.bat`) doivent utiliser l'environnement virtuel activé. Vérifier la présence de `venv` avant d'exécuter.
- **Interdiction stricte des caractères Unicode dans les messages `print`, logs, commandes exécutées et noms de fichiers temporaires.** Utiliser uniquement des caractères ASCII pour éviter les erreurs d'encodage CP1252.
