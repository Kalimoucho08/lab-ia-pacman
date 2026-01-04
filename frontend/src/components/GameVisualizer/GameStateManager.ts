/**
 * Gestionnaire d'état de jeu pour Pac-Man
 * 
 * Fonctionnalités :
 * - Réception des états de jeu via WebSocket
 * - Buffering et synchronisation frame-by-frame
 * - Interpolation pour animations fluides
 * - Prédiction de mouvement pour compensation de latence
 * - Gestion des collisions et règles de jeu
 * - Historique des états pour rewind/debug
 */

import { GameState } from '../../types/pacman';
import { webSocketClient, ConnectionStats } from './WebSocketClient';

export interface GameStateManagerConfig {
  interpolation: boolean;
  prediction: boolean;
  maxHistorySize: number;
  targetFps: number;
  bufferTarget: number; // Nombre d'états à garder en buffer
}

export interface GameStateWithMetadata {
  state: GameState;
  receivedAt: number;
  processed: boolean;
  interpolated?: boolean;
}

export class GameStateManager {
  private config: GameStateManagerConfig;
  private gameStates: GameStateWithMetadata[] = [];
  private currentState: GameState | null = null;
  private lastRenderTime = 0;
  private frameCount = 0;
  private isRunning = false;
  private animationFrameId: number | null = null;
  private onStateUpdateCallbacks: ((state: GameState) => void)[] = [];
  private onStatsUpdateCallbacks: ((stats: any) => void)[] = [];

  // Statistiques
  private stats = {
    totalStatesReceived: 0,
    statesDropped: 0,
    averageLatency: 0,
    bufferSize: 0,
    interpolationCount: 0,
    predictionCount: 0,
    lastUpdateTime: 0
  };

  constructor(config: Partial<GameStateManagerConfig> = {}) {
    this.config = {
      interpolation: true,
      prediction: false,
      maxHistorySize: 100,
      targetFps: 60,
      bufferTarget: 3,
      ...config
    };

    this.setupWebSocketListeners();
  }

  /**
   * Configuration des écouteurs WebSocket
   */
  private setupWebSocketListeners(): void {
    webSocketClient.onGameState((gameState: GameState) => {
      this.handleNewGameState(gameState);
    });

    webSocketClient.onStats((connectionStats: ConnectionStats) => {
      this.updateConnectionStats(connectionStats);
    });
  }

  /**
   * Traitement d'un nouvel état de jeu
   */
  private handleNewGameState(gameState: GameState): void {
    this.stats.totalStatesReceived++;
    
    const stateWithMetadata: GameStateWithMetadata = {
      state: gameState,
      receivedAt: Date.now(),
      processed: false
    };

    // Ajouter à l'historique
    this.gameStates.push(stateWithMetadata);
    
    // Maintenir la taille de l'historique
    if (this.gameStates.length > this.config.maxHistorySize) {
      const removed = this.gameStates.shift();
      if (removed && !removed.processed) {
        this.stats.statesDropped++;
      }
    }

    // Mettre à jour les statistiques
    this.stats.bufferSize = this.gameStates.length;
    this.stats.lastUpdateTime = Date.now();
    
    this.notifyStatsUpdate();
    
    // Si c'est le premier état, le définir comme état courant
    if (!this.currentState) {
      this.currentState = gameState;
      this.notifyStateUpdate();
    }
  }

  /**
   * Récupère l'état de jeu à afficher pour le temps courant
   */
  public getCurrentState(targetTime?: number): GameState | null {
    if (this.gameStates.length === 0) {
      return this.currentState;
    }

    const now = targetTime || Date.now();
    
    // Si l'interpolation est désactivée, retourner l'état le plus récent
    if (!this.config.interpolation || this.gameStates.length < 2) {
      const latestState = this.gameStates[this.gameStates.length - 1];
      this.currentState = latestState.state;
      latestState.processed = true;
      return this.currentState;
    }

    // Trouver les deux états entre lesquels interpoler
    let previousState: GameStateWithMetadata | null = null;
    let nextState: GameStateWithMetadata | null = null;

    for (let i = this.gameStates.length - 1; i >= 0; i--) {
      const state = this.gameStates[i];
      if (state.receivedAt <= now) {
        previousState = state;
        if (i < this.gameStates.length - 1) {
          nextState = this.gameStates[i + 1];
        }
        break;
      }
    }

    // Si on n'a pas d'état précédent, prendre le premier
    if (!previousState && this.gameStates.length > 0) {
      previousState = this.gameStates[0];
    }

    // Si on n'a pas d'état suivant, pas d'interpolation possible
    if (!previousState) {
      return this.currentState;
    }

    if (!nextState) {
      this.currentState = previousState.state;
      previousState.processed = true;
      return this.currentState;
    }

    // Calculer le facteur d'interpolation (0 à 1)
    const timeRange = nextState.receivedAt - previousState.receivedAt;
    if (timeRange <= 0) {
      this.currentState = previousState.state;
      return this.currentState;
    }

    const alpha = (now - previousState.receivedAt) / timeRange;
    const clampedAlpha = Math.max(0, Math.min(1, alpha));

    // Interpoler les positions
    this.currentState = this.interpolateStates(
      previousState.state,
      nextState.state,
      clampedAlpha
    );

    // Marquer les états comme traités
    previousState.processed = true;
    nextState.processed = true;
    
    this.stats.interpolationCount++;
    
    return this.currentState;
  }

  /**
   * Interpolation linéaire entre deux états
   */
  private interpolateStates(
    stateA: GameState,
    stateB: GameState,
    alpha: number
  ): GameState {
    // Pour des raisons de simplicité, on interpole seulement Pac-Man et les fantômes
    // Dans une implémentation complète, il faudrait interpoler tous les éléments
    
    const interpolatedPacman = {
      x: stateA.pacman.x + (stateB.pacman.x - stateA.pacman.x) * alpha,
      y: stateA.pacman.y + (stateB.pacman.y - stateA.pacman.y) * alpha,
      direction: alpha > 0.5 ? stateB.pacman.direction : stateA.pacman.direction
    };

    const interpolatedGhosts = stateA.ghosts.map((ghostA, index) => {
      const ghostB = stateB.ghosts[index] || ghostA;
      return {
        x: ghostA.x + (ghostB.x - ghostA.x) * alpha,
        y: ghostA.y + (ghostB.y - ghostA.y) * alpha,
        color: ghostA.color,
        mode: ghostA.mode
      };
    });

    // Pour les autres éléments, on prend l'état le plus récent ou on fait un mélange
    return {
      ...stateB, // On garde la plupart des propriétés de l'état B
      pacman: interpolatedPacman,
      ghosts: interpolatedGhosts,
      step: Math.round(stateA.step + (stateB.step - stateA.step) * alpha)
    };
  }

  /**
   * Prédiction de l'état suivant basée sur la vélocité
   */
  public predictNextState(deltaTime: number): GameState | null {
    if (!this.config.prediction || this.gameStates.length < 2) {
      return null;
    }

    const latestState = this.gameStates[this.gameStates.length - 1].state;
    const previousState = this.gameStates[this.gameStates.length - 2].state;
    
    const timeDiff = this.gameStates[this.gameStates.length - 1].receivedAt - 
                     this.gameStates[this.gameStates.length - 2].receivedAt;
    
    if (timeDiff <= 0) {
      return null;
    }

    // Calculer les vitesses
    const pacmanVelocity = {
      x: (latestState.pacman.x - previousState.pacman.x) / timeDiff,
      y: (latestState.pacman.y - previousState.pacman.y) / timeDiff
    };

    // Prédire la position suivante
    const predictedPacman = {
      x: latestState.pacman.x + pacmanVelocity.x * deltaTime,
      y: latestState.pacman.y + pacmanVelocity.y * deltaTime,
      direction: latestState.pacman.direction
    };

    // Prédire les positions des fantômes
    const predictedGhosts = latestState.ghosts.map((ghost, index) => {
      const previousGhost = previousState.ghosts[index];
      if (!previousGhost) return ghost;
      
      const ghostVelocity = {
        x: (ghost.x - previousGhost.x) / timeDiff,
        y: (ghost.y - previousGhost.y) / timeDiff
      };
      
      return {
        x: ghost.x + ghostVelocity.x * deltaTime,
        y: ghost.y + ghostVelocity.y * deltaTime,
        color: ghost.color,
        mode: ghost.mode
      };
    });

    this.stats.predictionCount++;

    return {
      ...latestState,
      pacman: predictedPacman,
      ghosts: predictedGhosts,
      step: latestState.step + 1
    };
  }

  /**
   * Démarre la boucle de mise à jour
   */
  public start(): void {
    if (this.isRunning) return;
    
    this.isRunning = true;
    this.lastRenderTime = performance.now();
    
    const updateLoop = (timestamp: number) => {
      if (!this.isRunning) return;
      
      const deltaTime = timestamp - this.lastRenderTime;
      const targetFrameTime = 1000 / this.config.targetFps;
      
      if (deltaTime >= targetFrameTime) {
        this.lastRenderTime = timestamp - (deltaTime % targetFrameTime);
        this.frameCount++;
        
        // Obtenir l'état courant (avec interpolation si activée)
        const currentState = this.getCurrentState();
        
        // Si pas d'état courant et que la prédiction est activée, essayer de prédire
        if (!currentState && this.config.prediction) {
          const predictedState = this.predictNextState(deltaTime);
          if (predictedState) {
            this.currentState = predictedState;
          }
        }
        
        // Notifier les callbacks si on a un état
        if (this.currentState) {
          this.notifyStateUpdate();
        }
        
        // Nettoyer les états anciens
        this.cleanupOldStates();
      }
      
      this.animationFrameId = requestAnimationFrame(updateLoop);
    };
    
    this.animationFrameId = requestAnimationFrame(updateLoop);
  }

  /**
   * Arrête la boucle de mise à jour
   */
  public stop(): void {
    this.isRunning = false;
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  /**
   * Nettoie les états anciens de l'historique
   */
  private cleanupOldStates(): void {
    const now = Date.now();
    const maxAge = 5000; // 5 secondes
    
    // Garder au moins 2 états pour l'interpolation
    const minStatesToKeep = Math.max(2, this.config.bufferTarget);
    
    while (this.gameStates.length > minStatesToKeep) {
      const state = this.gameStates[0];
      if (now - state.receivedAt > maxAge) {
        if (!state.processed) {
          this.stats.statesDropped++;
        }
        this.gameStates.shift();
      } else {
        break;
      }
    }
    
    this.stats.bufferSize = this.gameStates.length;
    this.notifyStatsUpdate();
  }

  /**
   * Met à jour les statistiques de connexion
   */
  private updateConnectionStats(connectionStats: ConnectionStats): void {
    this.stats.averageLatency = connectionStats.latency;
    this.notifyStatsUpdate();
  }

  /**
   * Notifie les callbacks de mise à jour d'état
   */
  private notifyStateUpdate(): void {
    if (!this.currentState) return;
    
    this.onStateUpdateCallbacks.forEach(callback => {
      try {
        callback(this.currentState!);
      } catch (error) {
        console.error('GameStateManager: Erreur dans le callback onStateUpdate', error);
      }
    });
  }

  /**
   * Notifie les callbacks de mise à jour des statistiques
   */
  private notifyStatsUpdate(): void {
    const combinedStats = {
      ...this.stats,
      frameCount: this.frameCount,
      isRunning: this.isRunning,
      currentStep: this.currentState?.step || 0
    };
    
    this.onStatsUpdateCallbacks.forEach(callback => {
      try {
        callback(combinedStats);
      } catch (error) {
        console.error('GameStateManager: Erreur dans le callback onStatsUpdate', error);
      }
    });
  }

  /**
   * Ajoute un état de jeu (méthode pour compatibilité avec GameVisualizer)
   */
  public addState(gameState: GameState): void {
    this.handleNewGameState(gameState);
  }

  /**
   * Met en pause ou reprend la lecture
   */
  public setPaused(paused: boolean): void {
    if (paused) {
      this.stop();
    } else {
      this.start();
    }
  }

  /**
   * Avance d'un pas (pour le contrôle manuel)
   */
  public stepForward(): void {
    if (this.gameStates.length > 0) {
      const nextState = this.gameStates.shift();
      if (nextState) {
        this.currentState = nextState.state;
        this.notifyStateUpdate();
      }
    }
  }

  /**
   * Recule d'un pas (pour le contrôle manuel)
   */
  public stepBackward(): void {
    // Dans une implémentation complète, on utiliserait l'historique
    // Pour l'instant, on ne fait rien
    console.log('stepBackward non implémenté');
  }

  /**
   * Définit la vitesse de lecture
   */
  public setSpeed(speed: number): void {
    // Ajuster la vitesse de lecture (modifier targetFps)
    this.config.targetFps = Math.max(1, Math.min(120, speed * 60));
  }

  /**
   * Réinitialise le gestionnaire
   */
  public reset(): void {
    this.stop();
    this.gameStates = [];
    this.currentState = null;
    this.frameCount = 0;
    this.stats = {
      totalStatesReceived: 0,
      statesDropped: 0,
      averageLatency: 0,
      bufferSize: 0,
      interpolationCount: 0,
      predictionCount: 0,
      lastUpdateTime: 0
    };
    this.notifyStatsUpdate();
  }

  /**
   * Récupère l'historique des états
   */
  public getHistory(): GameStateWithMetadata[] {
    return [...this.gameStates];
  }

  /**
   * Récupère l'état courant
   */
  public getCurrentGameState(): GameState | null {
    return this.currentState;
  }

  /**
   * Récupère les statistiques
   */
  public getStats(): any {
    return {
      ...this.stats,
      frameCount: this.frameCount,
      isRunning: this.isRunning,
      currentStep: this.currentState?.step || 0,
      bufferTarget: this.config.bufferTarget,
      interpolationEnabled: this.config.interpolation,
      predictionEnabled: this.config.prediction
    };
  }

  /**
   * Méthodes d'enregistrement des callbacks
   */
  public onStateUpdate(callback: (state: GameState) => void): void {
    this.onStateUpdateCallbacks.push(callback);
  }

  public onStatsUpdate(callback: (stats: any) => void): void {
    this.onStatsUpdateCallbacks.push(callback);
  }

  /**
   * Nettoyage
   */
  public dispose(): void {
    this.stop();
    this.onStateUpdateCallbacks = [];
    this.onStatsUpdateCallbacks = [];
    webSocketClient.dispose();
  }
}

// Instance singleton pour une utilisation globale
export const gameStateManager = new GameStateManager();

export default gameStateManager;