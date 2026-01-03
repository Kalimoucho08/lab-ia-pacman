# Système de Visualisation Web pour le Laboratoire IA

## Objectifs
Remplacer Pygame par une visualisation web moderne avec :
1. Canvas HTML5 pour le rendu du jeu
2. Contrôles interactifs (play/pause/step/rewind)
3. Performances élevées (60 FPS)
4. Support multi-navigateurs
5. Intégration avec l'API backend

## Architecture de Visualisation

### Composants Frontend
1. **GameCanvas** : Composant React avec Canvas 2D/WebGL
2. **GameControls** : Barre de contrôle avec boutons et sliders
3. **GameInfoPanel** : Panneau d'informations en temps réel
4. **ComparisonView** : Vue comparative côte à côte

### Backend Services
1. **RendererService** : Génération d'images côté serveur (fallback)
2. **StateStreamingService** : Streaming d'états via WebSocket
3. **AnimationService** : Génération d'animations (GIF/MP4)

## Approches Techniques

### Option 1 : Rendu Client Pur (Recommandé)
- Le frontend reçoit l'état du jeu via WebSocket
- Dessine directement sur Canvas HTML5
- Avantages : Latence minimale, scalable
- Inconvénients : Logique de rendu dupliquée

### Option 2 : Rendu Serveur + Streaming
- Le backend génère des images/frames
- Stream vers le frontend via WebSocket/MJPEG
- Avantages : Code de rendu unique
- Inconvénients : Latence, bande passante

### Option Hybride (Choix Retenu)
- **Mode normal** : Rendu client pour performance
- **Mode fallback** : Rendu serveur si WebGL indisponible
- **Export** : Génération serveur pour qualité maximale

## Implémentation du Rendu Client

### Composant GameCanvas
```typescript
// frontend/src/components/GameCanvas/GameCanvas.tsx
interface GameCanvasProps {
    gameState: GameState;
    config: RenderConfig;
    onInteraction?: (action: Interaction) => void;
}

const GameCanvas: React.FC<GameCanvasProps> = ({ gameState, config }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        
        // Dessiner la grille
        drawGrid(ctx, gameState, config);
        
        // Dessiner les murs
        drawWalls(ctx, gameState.walls, config);
        
        // Dessiner les points
        drawDots(ctx, gameState.dots, config);
        
        // Dessiner Pac-Man
        drawPacman(ctx, gameState.pacmanPos, config);
        
        // Dessiner les fantômes
        drawGhosts(ctx, gameState.ghostPositions, config);
        
        // Dessiner les informations
        drawInfo(ctx, gameState, config);
    }, [gameState, config]);
    
    return <canvas ref={canvasRef} width={config.width} height={config.height} />;
};
```

### Système de Dessin
```typescript
// frontend/src/utils/drawing.ts
export const drawGrid = (
    ctx: CanvasRenderingContext2D,
    gameState: GameState,
    config: RenderConfig
) => {
    const { size, cellSize } = config;
    
    // Fond
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, size * cellSize, size * cellSize);
    
    // Grille
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 1;
    
    for (let i = 0; i <= size; i++) {
        // Lignes verticales
        ctx.beginPath();
        ctx.moveTo(i * cellSize, 0);
        ctx.lineTo(i * cellSize, size * cellSize);
        ctx.stroke();
        
        // Lignes horizontales
        ctx.beginPath();
        ctx.moveTo(0, i * cellSize);
        ctx.lineTo(size * cellSize, i * cellSize);
        ctx.stroke();
    }
};

export const drawPacman = (
    ctx: CanvasRenderingContext2D,
    position: [number, number],
    config: RenderConfig
) => {
    const [x, y] = position;
    const { cellSize } = config;
    
    const centerX = x * cellSize + cellSize / 2;
    const centerY = y * cellSize + cellSize / 2;
    const radius = cellSize * 0.4;
    
    // Corps jaune
    ctx.fillStyle = '#FFFF00';
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    ctx.fill();
    
    // Bouche (animation)
    const mouthAngle = (Date.now() / 200) % 1 * Math.PI * 0.5;
    ctx.fillStyle = '#000000';
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.arc(centerX, centerY, radius, -mouthAngle, mouthAngle);
    ctx.closePath();
    ctx.fill();
    
    // Œil
    ctx.fillStyle = '#000000';
    ctx.beginPath();
    ctx.arc(centerX - radius * 0.3, centerY - radius * 0.4, radius * 0.15, 0, Math.PI * 2);
    ctx.fill();
};
```

## Adaptation du Code Pygame Existant

### Extrait de `visual_pacman_advanced.py` à Adapter
```python
# Code Pygame original
def draw_grid(screen, env, cell_size):
    screen.fill(BLACK)
    size = env.size
    
    # Dessiner les murs
    for (r, c) in env.walls:
        x1 = c * cell_size
        y1 = r * cell_size
        x2 = x1 + cell_size
        y2 = y1 + cell_size
        pygame.draw.rect(screen, WALL_COLOR, (x1, y1, cell_size, cell_size))
    
    # ... reste du code
```

### Version Adaptée pour Canvas HTML5
```typescript
// Conversion des fonctions de dessin
const WALL_COLOR = '#505050';
const GHOST_COLORS = ['#FF0000', '#0078FF', '#00FF00', '#B400FF'];

export const drawWalls = (
    ctx: CanvasRenderingContext2D,
    walls: Array<[number, number]>,
    config: RenderConfig
) => {
    const { cellSize } = config;
    
    ctx.fillStyle = WALL_COLOR;
    walls.forEach(([r, c]) => {
        const x = c * cellSize;
        const y = r * cellSize;
        ctx.fillRect(x, y, cellSize, cellSize);
    });
};
```

## Service de Rendu Serveur (Fallback)

### Pygame Headless
```python
# backend/app/services/pygame_renderer.py
import pygame
import io
from PIL import Image

class PygameRenderer:
    def __init__(self, headless=True):
        if headless:
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
            pygame.display.set_mode((1, 1), pygame.NOFRAME)
        else:
            pygame.init()
    
    def render_to_png(self, game_state: Dict, config: Dict) -> bytes:
        """Rend l'état du jeu en PNG"""
        size = config['size']
        cell_size = config['cell_size']
        
        # Créer une surface Pygame en mémoire
        surface = pygame.Surface((size * cell_size, size * cell_size))
        
        # Utiliser les fonctions de dessin existantes
        self._draw_grid(surface, game_state, config)
        
        # Convertir en PNG
        img_str = pygame.image.tostring(surface, 'RGB')
        img = Image.frombytes('RGB', surface.get_size(), img_str)
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def _draw_grid(self, surface, game_state, config):
        # Réutiliser le code de visual_pacman_advanced.py
        pass
```

### API d'Export d'Images
```
GET /api/v1/visualization/frame
Query Parameters:
- env_id: ID de l'environnement
- format: png|jpeg|webp (default: png)
- quality: 1-100 (default: 90)

Response: Image binary avec Content-Type approprié
```

## Streaming Temps Réel

### WebSocket pour les États de Jeu
```python
# backend/app/api/websocket.py
from fastapi import WebSocket

class GameWebSocket:
    def __init__(self):
        self.connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
    
    async def broadcast_game_state(self, game_state: Dict):
        """Diffuse l'état du jeu à tous les clients connectés"""
        for connection in self.connections:
            try:
                await connection.send_json({
                    "type": "game_state",
                    "state": game_state,
                    "timestamp": time.time()
                })
            except:
                self.connections.remove(connection)
```

### Optimisation des Données
```typescript
// Format optimisé pour le streaming
interface OptimizedGameState {
    // Positions seulement (réduit la taille de 90%)
    p: [number, number];  // Pac-Man position
    g: Array<[number, number]>;  // Ghost positions
    d: number;  // Dots remaining count
    l: number;  // Lives remaining
    s: number;  // Current step
    // ... autres métriques essentielles
}

// Compression delta (envoi seulement des changements)
interface DeltaUpdate {
    type: 'delta';
    changes: {
        pacman?: [number, number];
        ghosts?: Array<{idx: number, pos: [number, number]}>;
        dots?: Array<[number, number]>;  // Dots collected
    };
}
```

## Contrôles Interactifs

### Barre de Contrôle
```typescript
// frontend/src/components/GameControls/GameControls.tsx
const GameControls: React.FC = () => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [speed, setSpeed] = useState(1.0); // 0.25x à 4x
    
    return (
        <div className="game-controls">
            <button onClick={() => setIsPlaying(!isPlaying)}>
                {isPlaying ? '⏸️ Pause' : '▶️ Play'}
            </button>
            
            <button onClick={handleStep}>⏭️ Step</button>
            
            <button onClick={handleRewind}>⏪ Rewind</button>
            
            <button onClick={handleReset}>🔄 Reset</button>
            
            <div className="speed-control">
                <span>Speed:</span>
                <input
                    type="range"
                    min="0.25"
                    max="4"
                    step="0.25"
                    value={speed}
                    onChange={(e) => setSpeed(parseFloat(e.target.value))}
                />
                <span>{speed}x</span>
            </div>
            
            <div className="frame-control">
                <button onClick={() => handleJump(-10)}>« -10</button>
                <button onClick={() => handleJump(-1)}>‹ -1</button>
                <span>Frame: {currentFrame}</span>
                <button onClick={() => handleJump(1)}>+1 ›</button>
                <button onClick={() => handleJump(10)}>+10 »</button>
            </div>
        </div>
    );
};
```

### Gestion de la Lecture
```typescript
// frontend/src/hooks/useGamePlayback.ts
const useGamePlayback = (initialState: GameState) => {
    const [currentState, setCurrentState] = useState(initialState);
    const [history, setHistory] = useState<GameState[]>([initialState]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    
    // Boucle de lecture
    useEffect(() => {
        if (!isPlaying) return;
        
        const interval = setInterval(() => {
            if (currentIndex < history.length - 1) {
                setCurrentIndex(prev => prev + 1);
                setCurrentState(history[currentIndex + 1]);
            } else {
                setIsPlaying(false); // Fin de l'historique
            }
        }, 1000 / fps);
        
        return () => clearInterval(interval);
    }, [isPlaying, currentIndex, history, fps]);
    
    const stepForward = () => {
        if (currentIndex < history.length - 1) {
            setCurrentIndex(prev => prev + 1);
            setCurrentState(history[currentIndex + 1]);
        }
    };
    
    const stepBackward = () => {
        if (currentIndex > 0) {
            setCurrentIndex(prev => prev - 1);
            setCurrentState(history[currentIndex - 1]);
        }
    };
    
    return {
        currentState,
        isPlaying,
        setIsPlaying,
        stepForward,
        stepBackward,
        jumpToFrame: (index: number) => {
            if (index >= 0 && index < history.length) {
                setCurrentIndex(index);
                setCurrentState(history[index]);
            }
        }
    };
};
```

## Visualisation Comparative

### Vue Côte à Côte
```typescript
// frontend/src/components/ComparisonView/ComparisonView.tsx
const ComparisonView: React.FC = () => {
    const [experiments, setExperiments] = useState<Experiment[]>([]);
    const [selectedExperiments, setSelectedExperiments] = useState<string[]>([]);
    
    return (
        <div className="comparison-view">
            <div className="experiment-selector">
                <h3>Select Experiments to Compare</h3>
                {experiments.map(exp => (
                    <label key={exp.id}>
                        <input
                            type="checkbox"
                            checked={selectedExperiments.includes(exp.id)}
                            onChange={() => toggleExperiment(exp.id)}
                        />
                        {exp.name} (Score: {exp.intelligenceScore})
                    </label>
                ))}
            </div>
            
            <div className="comparison-grid">
                {selectedExperiments.map(expId => {
                    const exp = experiments.find(e => e.id === expId);
                    return (
                        <div key={expId} className="experiment-view">
                            <h4>{exp?.name}</h4>
                            <GameCanvas
                                gameState={exp?.currentState}
                                config={exp?.renderConfig}
                            />
                            <div className="metrics">
                                <div>Reward: {exp?.metrics.reward}</div>
                                <div>Steps: {exp?.metrics.steps}</div>
                                <div>Intelligence: {exp?.intelligenceScore}</div>
                            </div>
                        </div>
                    );
                })}
            </div>
            
            <div className="comparison-charts">
                <LineChart data={comparisonData} />
            </div>
        </div>
    );
};
```

## Performances et Optimisations

### Techniques d'Optimisation
1. **Double Buffering** : Utiliser deux canvas pour éviter le scintillement
2. **Dirty Rectangles** : Ne redessiner que les zones modifiées
3. **Spritesheets** : Précharger les assets graphiques
4. **WebGL** : Utiliser Three.js pour rendu 3D avancé
5. **Worker Threads** : Déplacer le calcul dans Web Workers

### Implémentation WebGL (Optionnel)
```typescript
// frontend/src/components/WebGLRenderer/WebGLRenderer.tsx
const WebGLRenderer: React.FC = () => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        
        const gl = canvas.getContext('webgl2');
        if (!gl) {
            console.warn('WebGL2 not available, falling back to Canvas2D');
            return;
        }
        
        // Initialiser WebGL
        initShaders(gl);
        initBuffers(gl);
        
        // Boucle de rendu
        const render = () => {
            drawScene(gl, gameState);
            requestAnimationFrame(render);
        };
        
        render();
    }, [gameState]);
    
    return <canvas ref={canvasRef} width={800} height={800} />;
};
```

## Tests de Performance

### Benchmarks Cibles
- **Rendu 60 FPS** : Mise à jour complète en < 16ms
- **Latence WebSocket** : < 50ms round-trip
- **Chargement initial** : < 2 secondes
- **Mémoire** : < 100MB pour 1000 frames d'historique

### Outils de Profiling
- Chrome DevTools Performance tab
- React DevTools Profiler
- WebSocket latency monitoring
- Memory usage tracking

## Plan de Migration depuis Pygame

### Étape 1 : Extraction de la Logique de Rendu
1. Isoler les fonctions de dessin de `visual_pacman_advanced.py`
2. Créer un module `rendering.py` indépendant de Pygame
3. Tester avec des mocks

### Étape 2 : Implémentation Canvas2D
1. Porter les fonctions de dessin en TypeScript
2. Implémenter le composant GameCanvas
3. Tester avec des états de jeu statiques

### Étape 3 : Intégration Temps Réel
1. Connecter WebSocket pour les mises à jour
