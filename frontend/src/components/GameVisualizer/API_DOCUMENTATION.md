# API de Visualisation Pac-Man - Documentation

## Vue d'ensemble

Le système de visualisation Pac-Man est une architecture modulaire qui remplace Pygame par une visualisation Canvas HTML5 avec WebSocket pour les mises à jour temps réel. Il est conçu pour offrir des performances à 60 FPS avec des animations fluides et une interface interactive.

## Architecture

```
frontend/src/components/GameVisualizer/
├── GameVisualizer.tsx          # Composant principal React
├── CanvasRenderer.ts           # Moteur de rendu Canvas optimisé
├── WebSocketClient.ts          # Client WebSocket temps réel
├── GameStateManager.ts         # Gestionnaire d'état de jeu
├── AnimationEngine.ts          # Moteur d'animations 60 FPS
├── ControlsPanel.tsx           # Panneau de contrôles interactifs
├── InfoOverlay.tsx             # Overlay d'informations
├── PerformanceOptimizer.ts     # Optimisations de performance
└── IntegrationTest.ts          # Tests d'intégration
```

## Composants Principaux

### 1. GameVisualizer.tsx

**Description** : Composant React principal qui intègre tous les sous-systèmes.

**Props** : Aucune (utilise le contexte interne)

**État** :
- `isConnected` : État de connexion WebSocket
- `isPlaying` : Lecture/pause de la simulation
- `gameState` : État courant du jeu
- `renderConfig` : Configuration du rendu
- `performanceStats` : Statistiques de performance

**Méthodes principales** :
- `handlePlayPause()` : Basculer lecture/pause
- `handleStepForward()` : Avancer d'une étape
- `handleStepBackward()` : Reculer d'une étape
- `handleZoomIn()` / `handleZoomOut()` : Contrôles de zoom
- `handleSpeedChange(speed)` : Ajuster la vitesse
- `handleExportImage()` : Exporter l'image du canvas

**Utilisation** :
```tsx
import GameVisualizer from './GameVisualizer';

function App() {
  return (
    <div style={{ width: '100%', height: '600px' }}>
      <GameVisualizer />
    </div>
  );
}
```

### 2. CanvasRenderer.ts

**Description** : Moteur de rendu Canvas HTML5 optimisé avec double buffering, sprite sheet préchargée et animations fluides.

**Configuration** :
```typescript
interface RenderConfig {
  cellSize: number;      // Taille d'une cellule en pixels
  zoom: number;          // Niveau de zoom
  showGrid: boolean;     // Afficher la grille
  showStats: boolean;    // Afficher les statistiques
  highlightPaths: boolean; // Mettre en évidence les chemins
  fps: number;           // FPS cible
  renderScale: number;   // Échelle de rendu (DPI)
}
```

**Méthodes publiques** :
- `constructor(canvas: HTMLCanvasElement, config?: Partial<RenderConfig>)`
- `updateConfig(config: Partial<RenderConfig>)` : Mettre à jour la configuration
- `startRendering()` : Démarrer le rendu continu
- `stopRendering()` : Arrêter le rendu
- `cacheGrid(gridWidth, gridHeight)` : Pré-rendre la grille pour optimisation
- `renderPacman(x, y, direction, frame)` : Rendre Pac-Man
- `renderGhost(x, y, color, mode, frame)` : Rendre un fantôme
- `renderPellet(x, y, frame)` : Rendre une pac-gomme
- `renderPowerPellet(x, y, frame)` : Rendre une super pac-gomme
- `renderWall(x, y)` : Rendre un mur
- `renderGameInfo(score, lives, step, fps)` : Rendre les informations
- `dispose()` : Nettoyer les ressources

**Exemple** :
```typescript
const canvas = document.getElementById('game-canvas') as HTMLCanvasElement;
const renderer = new CanvasRenderer(canvas, { cellSize: 24, zoom: 1.5 });
renderer.startRendering();
renderer.renderPacman(5, 10, 'right', 0);
```

### 3. WebSocketClient.ts

**Description** : Client WebSocket optimisé avec reconnexion automatique, buffering des états et gestion de latence.

**Configuration** :
```typescript
interface WebSocketConfig {
  url: string;                    // URL du serveur WebSocket
  reconnectAttempts: number;      // Tentatives de reconnexion
  reconnectDelay: number;         // Délai entre reconnexions (ms)
  bufferSize: number;             // Taille du buffer d'états
  pingInterval: number;           // Intervalle de ping (ms)
}
```

**Méthodes publiques** :
- `constructor(config: Partial<WebSocketConfig>)`
- `connect()` : Établir la connexion
- `disconnect()` : Fermer la connexion
- `send(message)` : Envoyer un message
- `subscribeToGameState(sessionId?)` : S'abonner aux états de jeu
- `getNextGameState()` : Récupérer le prochain état du buffer
- `getLatestGameState()` : Récupérer le dernier état
- `getStats()` : Obtenir les statistiques de connexion
- `isConnected()` : Vérifier si connecté
- `dispose()` : Nettoyer les ressources

**Callbacks** :
- `onGameState(callback)` : État de jeu reçu
- `onConnect(callback)` : Connexion établie
- `onDisconnect(callback)` : Déconnexion
- `onError(callback)` : Erreur
- `onStats(callback)` : Statistiques mises à jour

**Exemple** :
```typescript
const wsClient = new WebSocketClient({
  url: 'ws://localhost:8000/ws/game_state',
  reconnectAttempts: 5
});

wsClient.onGameState((gameState) => {
  console.log('État reçu:', gameState);
});

wsClient.connect();
```

### 4. GameStateManager.ts

**Description** : Gestionnaire d'état avec interpolation, prédiction, buffering et synchronisation frame-by-frame.

**Configuration** :
```typescript
interface GameStateManagerConfig {
  interpolation: boolean;    // Activer l'interpolation
  prediction: boolean;       // Activer la prédiction
  maxHistorySize: number;    // Taille maximale de l'historique
  targetFps: number;         // FPS cible
  bufferTarget: number;      // Nombre d'états en buffer
}
```

**Méthodes publiques** :
- `constructor(config?: Partial<GameStateManagerConfig>)`
- `start()` : Démarrer la boucle de mise à jour
- `stop()` : Arrêter la boucle
- `getCurrentState(targetTime?)` : Obtenir l'état courant (interpolé)
- `predictNextState(deltaTime)` : Prédire le prochain état
- `getHistory()` : Obtenir l'historique des états
- `getCurrentGameState()` : Obtenir l'état courant (non interpolé)
- `getStats()` : Obtenir les statistiques
- `reset()` : Réinitialiser le gestionnaire
- `onStateUpdate(callback)` : Callback sur mise à jour d'état
- `onStatsUpdate(callback)` : Callback sur mise à jour de stats
- `dispose()` : Nettoyer les ressources

**Exemple** :
```typescript
const stateManager = new GameStateManager({
  interpolation: true,
  prediction: true,
  targetFps: 60
});

stateManager.onStateUpdate((gameState) => {
  console.log('État mis à jour:', gameState.step);
});

stateManager.start();
```

### 5. AnimationEngine.ts

**Description** : Moteur d'animations 60 FPS avec système de particules, effets d'écran et transitions.

**Configuration** :
```typescript
interface AnimationConfig {
  fps: number;                // FPS cible
  enableParticles: boolean;   // Activer les particules
  particleCount: number;      // Nombre max de particules
  enableScreenShake: boolean; // Activer le tremblement d'écran
  enableTrails: boolean;      // Activer les traînées
  trailLength: number;        // Longueur des traînées
  enableBloom: boolean;       // Activer l'effet bloom
  bloomIntensity: number;     // Intensité du bloom
}
```

**Méthodes publiques** :
- `constructor(config?: Partial<AnimationConfig>)`
- `setRenderer(renderer)` : Associer un renderer Canvas
- `start()` : Démarrer le moteur d'animations
- `stop()` : Arrêter le moteur
- `createAnimation(type, from, to, duration, easing, onUpdate, onComplete)` : Créer une animation
- `createParticles(x, y, count, type, color, size)` : Créer des particules
- `triggerScreenShake(intensity, decay)` : Déclencher un tremblement d'écran
- `addTrail(x, y)` : Ajouter une traînée
- `animatePacman(pacman, frame)` : Animer Pac-Man
- `animateGhost(ghost, frame)` : Animer un fantôme
- `animatePellet(frame)` : Animer une pac-gomme
- `animatePowerPellet(frame)` : Animer une super pac-gomme
- `onFrame(callback)` : Callback à chaque frame
- `onParticleCreated(callback)` : Callback sur création de particule
- `onAnimationComplete(callback)` : Callback sur fin d'animation
- `dispose()` : Nettoyer les ressources

**Fonctions d'easing intégrées** :
- `easeLinear(t)`, `easeInQuad(t)`, `easeOutQuad(t)`, `easeInOutQuad(t)`
- `easeInCubic(t)`, `easeOutCubic(t)`, `easeInOutCubic(t)`
- `easeInSine(t)`, `easeOutSine(t)`

**Exemple** :
```typescript
const animationEngine = new AnimationEngine({
  enableParticles: true,
  particleCount: 100
});

animationEngine.createAnimation(
  'move',
  { x: 0, y: 0 },
  { x: 100, y: 100 },
  1000,
  animationEngine.easeOutCubic,
  (value) => { /* mise à jour */ },
  () => { /* complétion */ }
);

animationEngine.start();
```

### 6. ControlsPanel.tsx

**Description** : Panneau de contrôles React avec Material-UI pour la gestion interactive de la visualisation.

**Props** :
```typescript
interface ControlsPanelProps {
  isPlaying: boolean;
  zoom: number;
  speed: number;
  showGrid: boolean;
  showPaths: boolean;
  showHeatmap: boolean;
  showAgentLabels: boolean;
  showStats: boolean;
  onPlayPause: () => void;
  onStepForward: () => void;
  onStepBackward: () => void;
  onReset: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onSpeedChange: (speed: number) => void;
  onToggleGrid: () => void;
  onTogglePaths: () => void;
  onToggleHeatmap: () => void;
  onToggleAgentLabels: () => void;
  onToggleStats: () => void;
  onExportImage: () => void;
  onExportVideo: () => void;
  performanceStats?: {
    fps: number;
    latency: number;
    memoryUsage: number;
    bufferSize: number;
  };
}
```

**Utilisation** :
```tsx
<ControlsPanel
  isPlaying={isPlaying}
  zoom={zoom}
  speed={speed}
  showGrid={showGrid}
  onPlayPause={handlePlayPause}
  onZoomIn={handleZoomIn}
  // ... autres props
/>
```

### 7. InfoOverlay.tsx

**Description** : Overlay d'informations React affichant score, vies, positions, chemins et statistiques.

**Props** :
```typescript
interface InfoOverlayProps {
  gameState: GameState | null;
  showStats: boolean;
  showPaths: boolean;
  showHeatmap: boolean;
  showAgentLabels: boolean;
  fps?: number;
  latency?: number;
  memoryUsage?: number;
  bufferSize?: number;
  onToggleStats?: () => void;
  onTogglePaths?: () => void;
  onToggleHeatmap?: () => void;
  onToggleAgentLabels?: () => void;
}
```

### 8. PerformanceOptimizer.ts

**Description** : Optimiseur de performance avec Web Workers, caching, compression et lazy loading.

**Configuration** :
```typescript
interface OptimizationConfig {
  enableWebWorkers: boolean;   // Activer les Web Workers
  enableCompression: boolean;  // Activer la compression
  enableCaching: boolean;      // Activer le caching
  cacheSize: number;           // Taille du cache
  workerCount: number;         // Nombre de workers
  targetFPS: number;           // FPS cible
  memoryLimit: number;         // Limite mémoire (MB)
}
```

**Méthodes publiques** :
- `constructor(config?: Partial<OptimizationConfig>)`
- `cacheItem(key, value, ttl)` : Mettre en cache un élément
- `getCachedItem(key)` : Récupérer un élément du cache
- `compress(data)` : Compresser des données
- `decompress(data)` : Décompresser des données
- `interpolateStates(states, progress)` : Interpoler des états (via worker)
- `calculatePath(start, end, grid)` : Calculer un chemin (via worker)
- `getMetrics()` : Obtenir les métriques de performance
- `updateConfig(config)` : Mettre à jour la configuration
- `dispose()` : Nettoyer les ressources

## Intégration avec le Backend

### Endpoints WebSocket

Le système de visualisation communique avec le backend via les endpoints suivants :

1. **Connexion WebSocket** : `ws://localhost:8000/ws/game_state`
2. **Messages attendus** :
   - `game_state` : État complet du jeu
   - `performance_stats` : Statistiques de performance
   - `metrics` : Métriques d'entraînement
   - `session_update` : Mise à jour de session

### Format des données

**État de jeu (GameState)** :
```typescript
interface GameState {
  grid: number[][];  // Grille de jeu (0: vide, 1: mur, 2: pac-gomme, etc.)
  pacman: { x: number; y: number; direction: string };
  ghosts: Array<{ x: number; y: number; color: string; mode: string }>;
  pellets: Array<{ x: number; y: number }>;
  powerPellets: Array<{ x: number; y: number }>;
  score: number;
  lives: number;
  step: number;
}
```

**Message WebSocket** :
```typescript
interface WebSocketMessage {
  type: 'game_state' | 'metrics' | 'session_update' | 'error' | 'subscribe' | 'unsubscribe' | 'performance_stats';
  data: any;
  timestamp: string;
}
```

## Configuration Recommandée

### Pour le développement :
```typescript
const devConfig = {
  // CanvasRenderer
  cellSize: 20,
  zoom: 1.5,
  showGrid: true,
  showStats: true,
  
  // GameStateManager
  interpolation: true,
  prediction: false,
  targetFps: 60,
  
  // AnimationEngine
  enableParticles: true,
  particleCount: 50,
  
  // PerformanceOptimizer
  enableWebWorkers: false, // Désactivé en dev pour le débogage
  enableCaching: true,
  cacheSize: 50
};
```

### Pour la production :
```typescript
const prodConfig = {
  // CanvasRenderer
  cellSize: 24,
  zoom: 2.0,
  showGrid: false,
  showStats: true,
  
  // GameStateManager
  interpolation: true,
  prediction: true,
  targetFps: 60,
  
  // AnimationEngine
  enableParticles: true,
  particleCount: 100,
  
  // PerformanceOptimizer
  enableWebWorkers: true,
  enableCompression: true,
  enableCaching: true,
  cacheSize: 100,
  workerCount: Math.min(navigator.hardwareConcurrency || 4, 4)
};
```

## Guide de Démarrage Rapide

1. **Installation des dépendances** :
```bash
cd frontend
npm install
```

2. **Démarrage du backend** (si non déjà démarré) :
```bash
cd backend
uvicorn main:app --reload --port 8000
```

3. **Démarrage du frontend** :
```bash
cd frontend
npm run dev
```

4. **Utilisation du composant** :
```tsx
import React from 'react';
import GameVisualizer from './components/GameVisualizer/GameVisualizer';

function App() {
  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <GameVisualizer />
    </div>
  );
}
```

5. **Personnalisation avancée** :
```tsx
import { CanvasRenderer } from './components/GameVisualizer/CanvasRenderer';
import { GameStateManager } from './components/GameVisualizer/GameStateManager';
import { AnimationEngine } from './components/GameVisualizer/AnimationEngine';

// Créer une instance personnalisée
const canvas = document.getElementById('custom-canvas');
const renderer = new CanvasRenderer(canvas, { cellSize: 30, zoom: 2.0 });
const stateManager = new GameStateManager({ interpolation: true });
const animationEngine = new AnimationEngine({ enableParticles: true });

// Connecter les composants
animationEngine.setRenderer(renderer);
stateManager.onStateUpdate((gameState) => {
  // Rendu personnalisé
  renderer.renderPacman(gameState.pacman.x, gameState.pacman.y, gameState.pacman.direction, 0);
});

// Démarrer
renderer.startRendering();
stateManager.start();
animationEngine.start();
```

## Dépannage

### Problèmes courants

1. **Pas de connexion WebSocket** :
   - Vérifier que le backend est démarré sur `localhost:8000`
   - Vérifier les CORS dans la configuration du backend
   - Vérifier les logs du navigateur (F12 > Console)

2. **Performances médiocres** :
   - Activer les Web Workers dans `PerformanceOptimizer`
   - Réduire le nombre de particules dans `AnimationEngine`
   - Désactiver l'interpolation si la latence est faible
   - Utiliser le caching des sprites

3. **Rendu flou ou pixelisé** :
   - Ajuster `renderScale` dans `CanvasRenderer` selon le DPI de l'écran
   - Utiliser `imageSmoothingEnabled = true` dans la configuration Canvas

4. **Animations saccadées** :
   - Vérifier que `requestAnimationFrame` est utilisé (activé par défaut)
   - Ajuster `targetFps` dans `GameStateManager` et `AnimationEngine`
   - Vérifier la taille du buffer dans `WebSocketClient`

### Debugging

Pour activer le mode debug, ajoutez ceci avant d'initialiser les composants :
```typescript
// Dans GameVisualizer.tsx
if (process.env.NODE_ENV === 'development') {
  window.__PACMAN_DEBUG__ = {
    renderer: rendererRef.current,
    stateManager: stateManagerRef.current,
    animationEngine: animationEngineRef.current,
    performanceOptimizer: performanceOptimizerRef.current
  };
  
  console.log('Mode debug activé. Accès via window.__PACMAN_DEBUG__');
}
```

## Performance Monitoring

Le système inclut un monitoring de performance intégré :

```typescript
// Accéder aux métriques
const metrics = performanceOptimizer.getMetrics();
console.log(`FPS: ${metrics.fps}, Mémoire: ${metrics.memoryUsage}MB, Latence: ${metrics.latency}ms`);

// Surveiller les événements de performance
window.addEventListener('performanceMetrics', (event) => {
  const { fps, memoryUsage, renderTime } = event.detail;
  // Loguer ou afficher les métriques
});
```

## Évolution Future

### Améliorations planifiées :
1. **Support WebGL** : Rendu 3D avec Three.js
2. **Replay System** : Enregistrement et relecture des sessions
3. **Multi-view** : Vues multiples (vue globale, vue Pac-Man, vue fantôme)
4. **Analytics** : Analyse des performances des agents IA
5. **Export Video** : Export MP4/WebM des sessions

### Extensibilité :
Le système est conçu pour être extensible. Pour ajouter de nouveaux types d'éléments :
1. Étendre `GameState` avec les nouvelles données
2. Ajouter des méthodes de rendu dans `CanvasRenderer`
3. Ajouter des animations dans `AnimationEngine`
4. Mettre à jour `GameStateManager` pour gérer les nouveaux états

## Conclusion

Le système de visualisation Pac-Man offre une architecture complète et performante pour remplacer Pygame par une solution web moderne. Avec son rendu Canvas optimisé, sa communication WebSocket temps réel, ses animations fluides et ses contrôles interactifs, il constitue une base solide pour le laboratoire scientifique IA Pac-Man.

Pour toute question ou contribution, référez-vous à la documentation du code source et aux tests d'intégration.