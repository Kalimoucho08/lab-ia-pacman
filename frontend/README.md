# Laboratoire Scientifique IA Pac-Man - Interface Web

Interface React moderne pour l'expérimentation d'intelligence artificielle sur Pac-Man.

## 🚀 Fonctionnalités

- **20 curseurs paramétrables** organisés en 4 catégories (Entraînement, Jeu, Intelligence, Visualisation)
- **Visualisation temps réel** du jeu avec Canvas HTML5
- **4 graphiques interactifs** (Chart.js) pour le suivi des métriques
- **Système de sessions** complet avec sauvegarde automatique
- **Dashboard scientifique** avec métriques en temps réel
- **Communication WebSocket** pour les mises à jour live
- **Design responsive** Material-UI avec thème sombre

## 📁 Structure du projet

```
frontend/
├── public/              # Assets statiques
├── src/
│   ├── components/      # Composants React
│   │   ├── Dashboard/   # Dashboard principal
│   │   ├── ParameterSliders/ # 20 curseurs paramétrables
│   │   ├── GameVisualizer/   # Canvas de visualisation
│   │   ├── Charts/      # 4 graphiques temps réel
│   │   └── SessionManager/   # Gestion des sessions
│   ├── pages/          # Pages de l'application
│   ├── services/       # API et WebSocket
│   ├── types/          # Types TypeScript
│   └── utils/          # Utilitaires
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 🛠 Installation

### Prérequis
- Node.js 18+ et npm/yarn/pnpm

### Installation des dépendances
```bash
cd frontend
npm install
```

### Configuration
Copier le fichier d'environnement d'exemple :
```bash
cp .env.example .env
```

### Démarrage en mode développement
```bash
npm run dev
```

L'application sera accessible à l'adresse : [http://localhost:3000](http://localhost:3000)

### Construction pour la production
```bash
npm run build
npm run preview
```

## 🔧 Configuration

### Variables d'environnement
| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `VITE_API_URL` | URL de l'API backend | `http://localhost:8000/api` |
| `VITE_WS_URL` | URL du WebSocket | `ws://localhost:8000/ws` |
| `VITE_DEBUG` | Mode debug | `true` |

### Paramètres configurables (20 curseurs)

#### 1. Entraînement
- `learning_rate` : Taux d'apprentissage (0.0001 - 0.01)
- `gamma` : Facteur de discount (0.5 - 0.99)
- `episodes` : Nombre d'épisodes (100 - 10000)
- `batch_size` : Taille du batch (16 - 512)
- `buffer_size` : Taille du buffer (1000 - 100000)

#### 2. Jeu
- `grid_size` : Taille de la grille (10 - 30)
- `num_ghosts` : Nombre de fantômes (1 - 8)
- `power_pellets` : Super pac-gommes (0 - 8)
- `lives` : Vies de Pac-Man (1 - 10)
- `pellet_density` : Densité des pac-gommes (10% - 90%)

#### 3. Intelligence
- `exploration_rate` : Taux d'exploration (1% - 100%)
- `target_update` : Fréquence de mise à jour cible (100 - 10000)
- `learning_starts` : Début de l'apprentissage (100 - 10000)
- `train_freq` : Fréquence d'entraînement (1 - 100)

#### 4. Visualisation
- `fps` : Images par seconde (1 - 60)
- `render_scale` : Échelle de rendu (1x - 5x)
- `show_grid` : Afficher la grille (oui/non)
- `show_stats` : Afficher les statistiques (oui/non)
- `highlight_path` : Surligner le chemin (oui/non)

## 📊 Composants principaux

### 1. ParameterSliders
Composant contenant les 20 curseurs organisés en accordéons avec :
- Tooltips explicatifs pour chaque paramètre
- Valeurs par défaut scientifiques
- Mise à jour en temps réel

### 2. GameVisualizer
Visualisation interactive du jeu Pac-Man avec :
- Canvas HTML5 60 FPS
- Contrôles de lecture (play/pause/step)
- Zoom et grille ajustables
- État du jeu en temps réel

### 3. Charts
4 graphiques temps réel avec Chart.js :
- Score par épisode
- Récompense moyenne
- Perte d'entraînement
- Efficacité

### 4. SessionManager
Gestion complète des sessions d'expérimentation :
- Création/suppression de sessions
- Suivi de l'état (en cours, en pause, terminé)
- Export des résultats
- Comparaison entre sessions

### 5. Dashboard
Tableau de bord principal avec :
- Boutons d'action (Entraîner Pac-Man, Entraîner Fantômes, etc.)
- Métriques en temps réel
- Contrôles de simulation
- Statut système

## 🔌 Intégration avec le backend

### API REST
L'interface communique avec le backend FastAPI via :
- `GET /api/parameters` : Récupérer les paramètres actuels
- `PUT /api/parameters` : Mettre à jour les paramètres
- `GET /api/sessions` : Lister les sessions
- `POST /api/sessions` : Créer une nouvelle session
- `POST /api/training/pacman` : Démarrer l'entraînement de Pac-Man

### WebSocket
Connexion temps réel pour :
- Mises à jour de l'état du jeu
- Métriques d'entraînement en direct
- Notifications de session

## 🎨 Design et UX

- **Thème Material-UI** avec palette sombre scientifique
- **Design responsive** adapté à tous les écrans
- **Animations subtiles** pour une expérience fluide
- **Feedback visuel** immédiat pour toutes les actions
- **Explications contextuelles** pour chaque paramètre

## 🧪 Tests

```bash
# Tests unitaires
npm test

# Vérification TypeScript
npm run type-check

# Linting
npm run lint
```

## 📚 Documentation des composants

Chaque composant inclut :
- Documentation TypeScript complète
- Exemples d'utilisation
- Props documentées
- États gérés

## 🔄 Déploiement

### Build de production
```bash
npm run build
```

Les fichiers statiques sont générés dans le dossier `dist/`.

### Serveur de prévisualisation
```bash
npm run preview
```

### Déploiement sur Vercel/Netlify
Le projet est pré-configuré pour le déploiement sur les plateformes modernes.

## 🤝 Contribution

1. Fork du projet
2. Création d'une branche (`git checkout -b feature/amazing-feature`)
3. Commit des changements (`git commit -m 'Add amazing feature'`)
4. Push vers la branche (`git push origin feature/amazing-feature`)
5. Ouverture d'une Pull Request

## 📄 Licence

Ce projet fait partie du Laboratoire Scientifique IA Pac-Man - Licence MIT.

## 🙏 Remerciements

- **React** et **TypeScript** pour la base frontend
- **Material-UI** pour le système de design
- **Chart.js** pour les visualisations
- **Vite** pour le build ultra-rapide