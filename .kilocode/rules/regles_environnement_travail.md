# regles_environnement_travail.md

Règles spécifiques au projet lab-ia-pacman et à son environnement de travail (Windows, Python 3.14, VS Code).

## Lignes directrices

- Le répertoire racine est `g:/Drive/bogny/projet ia & co/lab-ia-pacman`. Utiliser des chemins relatifs à partir de là.
- La console Windows utilise CP1252 : interdiction d'utiliser des caractères Unicode dans les `print` et logs de l'interface.
- Les environnements multi‑agent sont définis dans `src/pacman_env/multiagent_env.py` et `src/pacman_env/multiagent_wrappers.py`.
- Les boutons "Entraîner Pac‑Man" et "Entraîner les fantômes" doivent lancer un thread séparé pour ne pas bloquer l'interface Tkinter.
- Les modèles sauvegardés doivent être placés dans `logs/` avec un nom explicite (ex: `pacman_DQN_<timestamp>.zip`).
- Le script `visual_pacman_advanced.py` accepte des arguments en ligne de commande pour la configuration ; utiliser `subprocess.Popen` pour le lancer.
- Ne pas supposer que `env.ghosts` est une liste (c'est un entier `num_ghosts`). `env.power_pellets` est également un entier.
- Les récompenses (`reward_config`) doivent être des dictionnaires avec les clés `pacman` et `ghost`.
- Le wrapper `SingleAgentWrapper` attend un `agent_id` comme `"pacman"` ou `"ghost_0"`.
- Tester les imports avec un petit script avant de lancer l'interface graphique.
- Suivre le style PEP 8 et écrire les docstrings en français.