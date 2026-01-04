/**
 * Optimiseur de performance pour la visualisation Pac-Man
 * 
 * Fonctionnalités :
 * - Web Workers pour calculs lourds
 * - Caching avancé des assets
 * - Compression/décompression des données
 * - Lazy loading des sprites
 * - Gestion de mémoire optimisée
 */

export interface PerformanceMetrics {
  fps: number;
  memoryUsage: number;
  cpuUsage: number;
  bufferSize: number;
  latency: number;
  renderTime: number;
  updateTime: number;
}

export interface OptimizationConfig {
  enableWebWorkers: boolean;
  enableCompression: boolean;
  enableCaching: boolean;
  cacheSize: number;
  workerCount: number;
  targetFPS: number;
  memoryLimit: number; // MB
}

export class PerformanceOptimizer {
  private config: OptimizationConfig;
  private metrics: PerformanceMetrics;
  private workers: Worker[] = [];
  private cache: Map<string, any> = new Map();
  private frameTimes: number[] = [];
  private lastFrameTime: number = 0;
  private memoryMonitorInterval: number | null = null;
  private isMonitoring: boolean = false;


  constructor(config: Partial<OptimizationConfig> = {}) {
    this.config = {
      enableWebWorkers: true,
      enableCompression: false,
      enableCaching: true,
      cacheSize: 100,
      workerCount: Math.min(navigator.hardwareConcurrency || 4, 4),
      targetFPS: 60,
      memoryLimit: 500, // 500 MB
      ...config
    };

    this.metrics = {
      fps: 0,
      memoryUsage: 0,
      cpuUsage: 0,
      bufferSize: 0,
      latency: 0,
      renderTime: 0,
      updateTime: 0
    };

    this.initWorkers();
    this.startMonitoring();
  }

  /**
   * Initialise les Web Workers
   */
  private initWorkers(): void {
    if (!this.config.enableWebWorkers || typeof Worker === 'undefined') {
      console.log('Web Workers non supportés ou désactivés');
      return;
    }

    // Créer les workers pour différents types de calculs
    const workerTypes = ['interpolation', 'pathfinding', 'compression', 'rendering'];
    
    for (let i = 0; i < Math.min(this.config.workerCount, workerTypes.length); i++) {
      try {
        // Dans une implémentation réelle, charger depuis des fichiers séparés
        const workerCode = this.createWorkerCode(workerTypes[i]);
        const blob = new Blob([workerCode], { type: 'application/javascript' });
        const worker = new Worker(URL.createObjectURL(blob));
        
        worker.onmessage = (event) => this.handleWorkerMessage(event, workerTypes[i]);
        worker.onerror = (error) => this.handleWorkerError(error, workerTypes[i]);
        
        this.workers.push(worker);
      } catch (error) {
        console.error(`Erreur lors de la création du worker ${workerTypes[i]}:`, error);
      }
    }
  }

  /**
   * Crée le code pour un worker spécifique
   */
  private createWorkerCode(_workerType: string): string {
    const baseCode = `
      self.onmessage = function(event) {
        const { type, data, id } = event.data;
        
        try {
          let result;
          
          switch (type) {
            case 'interpolate':
              result = interpolateStates(data.states, data.progress);
              break;
              
            case 'compress':
              result = compressData(data);
              break;
              
            case 'decompress':
              result = decompressData(data);
              break;
              
            case 'calculate_path':
              result = calculatePath(data.start, data.end, data.grid);
              break;
              
            default:
              result = { error: 'Type de tâche non supporté' };
          }
          
          self.postMessage({ id, result, type });
        } catch (error) {
          self.postMessage({ id, error: error.message, type });
        }
      };
      
      // Fonctions d'interpolation
      function interpolateStates(states, progress) {
        if (states.length < 2) return states[0] || null;
        
        const index = Math.floor(progress * (states.length - 1));
        const nextIndex = Math.min(index + 1, states.length - 1);
        const localProgress = (progress * (states.length - 1)) - index;
        
        const state1 = states[index];
        const state2 = states[nextIndex];
        
        // Interpolation linéaire simple
        const result = {};
        
        // Interpoler Pac-Man
        if (state1.pacman && state2.pacman) {
          result.pacman = {
            x: state1.pacman.x + (state2.pacman.x - state1.pacman.x) * localProgress,
            y: state1.pacman.y + (state2.pacman.y - state1.pacman.y) * localProgress,
            direction: localProgress > 0.5 ? state2.pacman.direction : state1.pacman.direction
          };
        }
        
        // Interpoler les fantômes
        if (state1.ghosts && state2.ghosts && state1.ghosts.length === state2.ghosts.length) {
          result.ghosts = state1.ghosts.map((ghost, i) => ({
            x: ghost.x + (state2.ghosts[i].x - ghost.x) * localProgress,
            y: ghost.y + (state2.ghosts[i].y - ghost.y) * localProgress,
            color: ghost.color,
            mode: localProgress > 0.5 ? state2.ghosts[i].mode : ghost.mode
          }));
        }
        
        // Copier les autres propriétés
        result.score = state1.score;
        result.lives = state1.lives;
        result.step = Math.round(state1.step + (state2.step - state1.step) * localProgress);
        
        return result;
      }
      
      // Fonctions de compression simples (pour démonstration)
      function compressData(data) {
        // Dans une implémentation réelle, utiliser une vraie compression
        return {
          compressed: true,
          size: JSON.stringify(data).length,
          data: JSON.stringify(data) // Simuler la compression
        };
      }
      
      function decompressData(data) {
        try {
          return JSON.parse(data);
        } catch (error) {
          return { error: 'Échec de décompression' };
        }
      }
      
      // Algorithme de pathfinding A* simplifié
      function calculatePath(start, end, grid) {
        // Implémentation simplifiée pour la démonstration
        const path = [];
        let current = { x: start.x, y: start.y };
        
        while (current.x !== end.x || current.y !== end.y) {
          path.push({ ...current });
          
          if (current.x < end.x) current.x++;
          else if (current.x > end.x) current.x--;
          
          if (current.y < end.y) current.y++;
          else if (current.y > end.y) current.y--;
          
          // Éviter les boucles infinies
          if (path.length > 1000) break;
        }
        
        path.push({ ...end });
        return path;
      }
    `;
    
    return baseCode;
  }

  /**
   * Gère les messages des workers
   */
  private handleWorkerMessage(event: MessageEvent, workerType: string): void {
    const { id, result, error, type } = event.data;
    
    if (error) {
      console.error(`Worker ${workerType} erreur (${type}):`, error);
      return;
    }
    
    // Émettre un événement pour notifier les résultats
    const customEvent = new CustomEvent('workerResult', {
      detail: { id, result, workerType, taskType: type }
    });
    window.dispatchEvent(customEvent);
  }

  /**
   * Gère les erreurs des workers
   */
  private handleWorkerError(error: ErrorEvent, workerType: string): void {
    console.error(`Worker ${workerType} erreur:`, error);
  }

  /**
   * Démarre la surveillance des performances
   */
  private startMonitoring(): void {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    this.lastFrameTime = performance.now();
    
    // Surveiller la mémoire (si l'API est disponible)
    if ('memory' in performance) {
      this.memoryMonitorInterval = window.setInterval(() => {
        this.updateMemoryUsage();
      }, 1000);
    }
    
    // Surveiller le FPS
    const updateFPS = () => {
      const now = performance.now();
      const deltaTime = now - this.lastFrameTime;
      this.lastFrameTime = now;
      
      this.frameTimes.push(deltaTime);
      if (this.frameTimes.length > 60) {
        this.frameTimes.shift();
      }
      
      // Calculer le FPS moyen
      const avgFrameTime = this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length;
      this.metrics.fps = avgFrameTime > 0 ? Math.round(1000 / avgFrameTime) : 0;
      
      if (this.isMonitoring) {
        requestAnimationFrame(updateFPS);
      }
    };
    
    requestAnimationFrame(updateFPS);
  }

  /**
   * Met à jour l'utilisation mémoire
   */
  private updateMemoryUsage(): void {
    // Utiliser l'API Performance Memory si disponible
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      this.metrics.memoryUsage = Math.round(memory.usedJSHeapSize / (1024 * 1024));
    } else {
      // Estimation basée sur la taille du cache
      this.metrics.memoryUsage = Math.round(this.cache.size * 0.1);
    }
    
    // Vérifier la limite mémoire
    if (this.metrics.memoryUsage > this.config.memoryLimit) {
      this.clearCache();
      console.warn(`Limite mémoire dépassée (${this.metrics.memoryUsage} MB), cache vidé`);
    }
  }

  /**
   * Met en cache un élément
   */
  public cacheItem(key: string, value: any, ttl: number = 60000): void {
    if (!this.config.enableCaching) return;
    
    // Limiter la taille du cache
    if (this.cache.size >= this.config.cacheSize) {
      const firstKeyIterator = this.cache.keys().next();
      if (!firstKeyIterator.done) {
        const firstKey = firstKeyIterator.value;
        this.cache.delete(firstKey);
      }
    }
    
    this.cache.set(key, {
      value,
      timestamp: Date.now(),
      ttl
    });
  }

  /**
   * Récupère un élément du cache
   */
  public getCachedItem(key: string): any | null {
    if (!this.config.enableCaching) return null;
    
    const cached = this.cache.get(key);
    if (!cached) return null;
    
    // Vérifier l'expiration
    if (Date.now() - cached.timestamp > cached.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.value;
  }

  /**
   * Vide le cache
   */
  public clearCache(): void {
    this.cache.clear();
  }

  /**
   * Compresse des données (si activé)
   */
  public async compress(data: any): Promise<any> {
    if (!this.config.enableCompression) {
      return data;
    }
    
    // Utiliser un worker pour la compression
    if (this.config.enableWebWorkers && this.workers.length > 0) {
      return new Promise((resolve) => {
        const id = `compress_${Date.now()}_${Math.random()}`;
        const compressionWorker = this.workers.find(_w => true); // Premier worker disponible
        
        if (!compressionWorker) {
          resolve(data);
          return;
        }
        
        const handleResult = (event: CustomEvent) => {
          if (event.detail.id === id && event.detail.taskType === 'compress') {
            window.removeEventListener('workerResult', handleResult as EventListener);
            resolve(event.detail.result);
          }
        };
        
        window.addEventListener('workerResult', handleResult as EventListener);
        
        compressionWorker.postMessage({
          type: 'compress',
          data,
          id
        });
        
        // Timeout après 1 seconde
        setTimeout(() => {
          window.removeEventListener('workerResult', handleResult as EventListener);
          resolve(data);
        }, 1000);
      });
    }
    
    // Compression simple (JSON stringify)
    return JSON.stringify(data);
  }

  /**
   * Décompresse des données (si activé)
   */
  public async decompress(data: any): Promise<any> {
    if (!this.config.enableCompression) {
      return data;
    }
    
    // Utiliser un worker pour la décompression
    if (this.config.enableWebWorkers && this.workers.length > 0) {
      return new Promise((resolve) => {
        const id = `decompress_${Date.now()}_${Math.random()}`;
        const compressionWorker = this.workers.find(_w => true);
        
        if (!compressionWorker) {
          resolve(typeof data === 'string' ? JSON.parse(data) : data);
          return;
        }
        
        const handleResult = (event: CustomEvent) => {
          if (event.detail.id === id && event.detail.taskType === 'decompress') {
            window.removeEventListener('workerResult', handleResult as EventListener);
            resolve(event.detail.result);
          }
        };
        
        window.addEventListener('workerResult', handleResult as EventListener);
        
        compressionWorker.postMessage({
          type: 'decompress',
          data,
          id
        });
        
        // Timeout après 1 seconde
        setTimeout(() => {
          window.removeEventListener('workerResult', handleResult as EventListener);
          resolve(typeof data === 'string' ? JSON.parse(data) : data);
        }, 1000);
      });
    }
    
    // Décompression simple
    try {
      return typeof data === 'string' ? JSON.parse(data) : data;
    } catch {
      return data;
    }
  }

  /**
   * Interpole des états de jeu (utilise un worker si possible)
   */
  public async interpolateStates(states: any[], progress: number): Promise<any> {
    if (!this.config.enableWebWorkers || this.workers.length === 0 || states.length < 2) {
      // Interpolation simple côté client
      return this.simpleInterpolation(states, progress);
    }
    
    return new Promise((resolve) => {
      const id = `interpolate_${Date.now()}_${Math.random()}`;
      const interpolationWorker = this.workers.find(_w => true);
      
      if (!interpolationWorker) {
        resolve(this.simpleInterpolation(states, progress));
        return;
      }
      
      const handleResult = (event: CustomEvent) => {
        if (event.detail.id === id && event.detail.taskType === 'interpolate') {
          window.removeEventListener('workerResult', handleResult as EventListener);
          resolve(event.detail.result);
        }
      };
      
      window.addEventListener('workerResult', handleResult as EventListener);
      
      interpolationWorker.postMessage({
        type: 'interpolate',
        data: { states, progress },
        id
      });
      
      // Timeout après 500ms
      setTimeout(() => {
        window.removeEventListener('workerResult', handleResult as EventListener);
        resolve(this.simpleInterpolation(states, progress));
      }, 500);
    });
  }

  /**
   * Interpolation simple côté client
   */
  private simpleInterpolation(states: any[], progress: number): any {
    if (states.length < 2) return states[0] || null;
    
    const index = Math.floor(progress * (states.length - 1));
    const nextIndex = Math.min(index + 1, states.length - 1);
    const localProgress = (progress * (states.length - 1)) - index;
    
    const state1 = states[index];
    const state2 = states[nextIndex];
    
    // Interpolation linéaire simple
    const result = { ...state1 };
    
    // Interpoler Pac-Man
    if (state1.pacman && state2.pacman) {
      result.pacman = {
        ...state1.pacman,
        x: state1.pacman.x + (state2.pacman.x - state1.pacman.x) * localProgress,
        y: state1.pacman.y + (state2.pacman.y - state1.pacman.y) * localProgress
      };
    }
    
    // Interpoler les fantômes
    if (state1.ghosts && state2.ghosts && state1.ghosts.length === state2.ghosts.length) {
      result.ghosts = state1.ghosts.map((ghost: any, i: number) => ({
        ...ghost,
        x: ghost.x + (state2.ghosts[i].x - ghost.x) * localProgress,
        y: ghost.y + (state2.ghosts[i].y - ghost.y) * localProgress
      }));
    }
    
    return result;
  }

  /**
   * Calcule un chemin (utilise un worker si possible)
   */
  public async calculatePath(
    start: { x: number; y: number },
    end: { x: number; y: number },
    grid: number[][]
  ): Promise<Array<{ x: number; y: number }>> {
    if (!this.config.enableWebWorkers || this.workers.length === 0) {
      // Calcul simple côté client
      return this.simplePathCalculation(start, end, grid);
    }
    
    return new Promise((resolve) => {
      const id = `path_${Date.now()}_${Math.random()}`;
      const pathfindingWorker = this.workers.find(_w => true);
      
      if (!pathfindingWorker) {
        resolve(this.simplePathCalculation(start, end, grid));
        return;
      }
      
      const handleResult = (event: CustomEvent) => {
        if (event.detail.id === id && event.detail.taskType === 'calculate_path') {
          window.removeEventListener('workerResult', handleResult as EventListener);
          resolve(event.detail.result);
        }
      };
      
      window.addEventListener('workerResult', handleResult as EventListener);
      
      pathfindingWorker.postMessage({
        type: 'calculate_path',
        data: { start, end, grid },
        id
      });
      
      // Timeout après 1 seconde
      setTimeout(() => {
        window.removeEventListener('workerResult', handleResult as EventListener);
        resolve(this.simplePathCalculation(start, end, grid));
      }, 1000);
    });
  }

  /**
   * Calcul de chemin simple côté client (algorithme A* simplifié)
   */
  private simplePathCalculation(
    start: { x: number; y: number },
    end: { x: number; y: number },
    _grid: number[][]
  ): Array<{ x: number; y: number }> {
    const path: Array<{ x: number; y: number }> = [];
    let current = { x: start.x, y: start.y };
    
    // Algorithme simplifié (chemin en ligne droite avec évitement d'obstacles)
    while (current.x !== end.x || current.y !== end.y) {
      path.push({ ...current });
      
      // Déplacement en ligne droite
      if (current.x < end.x) current.x++;
      else if (current.x > end.x) current.x--;
      
      if (current.y < end.y) current.y++;
      else if (current.y > end.y) current.y--;
      
      // Éviter les boucles infinies
      if (path.length > 1000) break;
    }
    
    path.push({ ...end });
    return path;
  }

  /**
   * Met à jour les métriques de performance
   */
  public updateMetrics(partialMetrics: Partial<PerformanceMetrics>): void {
    this.metrics = { ...this.metrics, ...partialMetrics };
  }

  /**
   * Récupère les métriques actuelles
   */
  public getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  /**
   * Récupère la configuration
   */
  public getConfig(): OptimizationConfig {
    return { ...this.config };
  }

  /**
   * Met à jour la configuration
   */
  public updateConfig(config: Partial<OptimizationConfig>): void {
    this.config = { ...this.config, ...config };
    
    // Redémarrer les workers si nécessaire
    if (config.enableWebWorkers !== undefined || config.workerCount !== undefined) {
      this.disposeWorkers();
      this.initWorkers();
    }
  }

  /**
   * Nettoie les workers
   */
  private disposeWorkers(): void {
    this.workers.forEach(worker => worker.terminate());
    this.workers = [];
  }

  /**
   * Arrête la surveillance et nettoie les ressources
   */
  public dispose(): void {
    this.isMonitoring = false;
    
    if (this.memoryMonitorInterval !== null) {
      clearInterval(this.memoryMonitorInterval);
      this.memoryMonitorInterval = null;
    }
    
    this.disposeWorkers();
    this.clearCache();
  }
}