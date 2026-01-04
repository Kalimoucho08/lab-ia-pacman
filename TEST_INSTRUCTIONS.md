# Instructions pour tester l'interface minimale Pac-Man

Cette version minimale permet de voir une interface fonctionnelle avec des données mockées, sans erreurs critiques.

## Prérequis

- Python 3.11.9 (environnement virtuel `venv311` activé)
- Node.js (pour le frontend React)
- Dépendances Python installées (fastapi, uvicorn, websockets)

## Étapes de test

### 1. Démarrer le backend FastAPI

Ouvrez un terminal dans le répertoire `lab-ia-pacman` et exécutez :

```bash
cd backend
python app_simple.py
```

Le serveur démarrera sur `http://localhost:8000`. Vous devriez voir les logs :

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 2. Démarrer le frontend React

Dans un **second terminal** (le backend doit rester en cours d'exécution), exécutez :

```bash
cd frontend
npm run dev
```

Le frontend démarrera sur `http://localhost:3000`. Vous devriez voir un message indiquant que le serveur de développement est prêt.

### 3. Ouvrir l'interface dans le navigateur

Ouvrez votre navigateur à l'adresse : [http://localhost:3000](http://localhost:3000)

## Ce que vous devriez voir

1. **Une interface avec un thème bleu** (Material-UI) au lieu d'une page bleue vide.
2. **Un titre "Laboratoire Pac‑Man"** en haut de la page.
3. **Un canvas de jeu** affichant une grille avec :
   - Pac‑Man (cercle jaune) qui se déplace lentement
   - Quatre fantômes (cercles colorés) qui se déplacent aléatoirement
   - Des pellets (petits points blancs) et des power pellets (points plus grands)
4. **Des métriques en temps réel** (score, FPS, mémoire utilisée) mises à jour chaque seconde.
5. **Des graphiques** (score et mémoire) qui tracent l'évolution des données mockées.
6. **Des contrôles** (boutons "Pause", "Reset", "Vitesse") qui ne plantent pas.

## Données utilisées

Le backend génère des données mockées réalistes :

- Positions de Pac‑Man et des fantômes qui évoluent à chaque tick
- Score qui augmente progressivement
- Métriques système simulées (FPS ~60, mémoire ~200‑300 Mo)
- État du jeu (nombre de pellets restants, vies, etc.)

Le frontend se connecte automatiquement au WebSocket (`ws://localhost:8000/ws/game_state`) et reçoit les données toutes les 500 ms.

## Résolution des problèmes courants

### Erreur "ModuleNotFoundError: No module named 'fastapi'"

Assurez-vous que l'environnement virtuel `venv311` est activé et que les dépendances sont installées :

```bash
pip install -r backend/requirements_minimal.txt
```

### Erreur Chart.js "line is not a registered controller"

Cette erreur a été corrigée en enregistrant explicitement les contrôleurs dans `frontend/src/components/Charts/Charts.tsx`. Si elle persiste, vérifiez que le fichier a bien été mis à jour.

### Page bleue sans contenu

Vérifiez que le backend est bien en cours d'exécution et que le frontend peut se connecter au WebSocket. Ouvrez la console du navigateur (F12) pour voir les erreurs éventuelles.

### Le canvas reste vide

Les données mockées sont envoyées toutes les 500 ms. Attendez quelques secondes. Si rien n'apparaît, vérifiez les logs du backend (des messages "WebSocket connected" et "Sending game state" doivent apparaître).

## Arrêt propre

1. Dans le terminal du backend, appuyez sur `Ctrl+C` pour arrêter le serveur.
2. Dans le terminal du frontend, appuyez sur `Ctrl+C` pour arrêter le serveur de développement.

## Fichiers créés/modifiés

- `backend/app_simple.py` : backend minimal avec WebSocket et données mockées
- `frontend/src/components/Charts/Charts.tsx` : correction des erreurs Chart.js
- `frontend/src/App.tsx` : structure de l'interface
- `backend/requirements_minimal.txt` : dépendances minimales pour le backend

## Prochaines étapes possibles

- Intégrer l'environnement Pac‑Man réel (`src/pacman_env/`)
- Remplacer les données mockées par un vrai jeu
- Ajouter des contrôles d'entraînement (boutons "Train Pac‑Man", "Train Ghosts")
- Connecter l'interface à l'API d'archivage et d'intelligence

---

**Version testée le :** 2026‑01‑04  
**État :** Fonctionnel (interface visible, données mockées, pas d'erreurs critiques)
