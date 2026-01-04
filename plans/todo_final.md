# TODO LIST FINALE - Application Laboratoire Pac-Man

## État actuel

- Backend FastAPI minimal fonctionnel (app_simple.py) - données mockées
- Frontend React/TypeScript avec interface de base
- Composants créés mais non connectés aux vrais services
- Système d'archivage avancé implémenté mais non intégré
- Services d'intelligence et ONNX créés mais non utilisés

## Tâches prioritaires (à faire maintenant)

### 1. Intégration Backend Réel

- [ ] Remplacer `backend/app_simple.py` par `backend/app.py` avec vraie intégration
- [ ] Connecter les endpoints API aux services existants
- [ ] Implémenter WebSocket pour vraies données de jeu
- [ ] Intégrer les environnements Pac-Man existants (`src/pacman_env/`)

### 2. Frontend - Connexion aux APIs

- [ ] Mettre à jour `frontend/src/services/api.ts` pour utiliser les vraies endpoints
- [ ] Connecter `GameVisualizer` au WebSocket backend
- [ ] Remplacer les données mockées par des données réelles
- [ ] Implémenter les contrôles de jeu (play/pause/step)

### 3. Système d'Archivage

- [ ] Connecter le service d'archivage au backend
- [ ] Ajouter bouton "Sauvegarder session" dans l'interface
- [ ] Afficher la liste des archives sauvegardées
- [ ] Implémenter la restauration de sessions

### 4. Intelligence et Métriques

- [ ] Connecter le calculateur d'intelligence au backend
- [ ] Afficher le score d'intelligence en temps réel
- [ ] Générer des graphiques avec vraies données
- [ ] Implémenter les comparaisons entre sessions

### 5. Export ONNX

- [ ] Connecter le service d'export ONNX
- [ ] Ajouter bouton "Exporter modèle" dans l'interface
- [ ] Générer et télécharger les fichiers ONNX
- [ ] Valider les modèles exportés

### 6. Interface Utilisateur

- [ ] Finaliser les curseurs de paramètres avec vraies valeurs
- [ ] Implémenter les tooltips explicatifs
- [ ] Ajouter les présélections (débutant/avancé/expert)
- [ ] Améliorer la responsivité mobile

### 7. Tests et Validation

- [ ] Tester la connexion frontend/backend
- [ ] Valider le système d'archivage
- [ ] Tester l'export ONNX
- [ ] Vérifier les performances avec vrai jeu

## Fichiers clés à modifier

### Backend

- `backend/app.py` - API principale
- `backend/services/` - Services à connecter
- `backend/api/v1/endpoints/` - Endpoints REST

### Frontend

- `frontend/src/services/api.ts` - Client API
- `frontend/src/services/websocket.ts` - Client WebSocket
- `frontend/src/components/GameVisualizer/` - Visualisation jeu
- `frontend/src/components/Charts/` - Graphiques

## Scripts de lancement

Créer `start.bat` et `start.sh` pour:

1. Activer l'environnement virtuel Python 3.11
2. Lancer le backend FastAPI
3. Lancer le frontend React

## Documentation

- Créer `README.md` avec instructions d'installation
- Documenter l'API avec OpenAPI/Swagger
- Ajouter captures d'écran de l'interface

## Délais

Priorité 1: Tâches 1-2 (intégration de base) - À faire immédiatement
Priorité 2: Tâches 3-5 (fonctionnalités avancées) - Après intégration
Priorité 3: Tâches 6-7 (polissage) - Finalisation
