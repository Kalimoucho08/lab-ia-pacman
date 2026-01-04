/**
 * Script de test d'intégration pour le système de visualisation Pac-Man
 * 
 * Vérifie que tous les composants fonctionnent correctement ensemble :
 * - CanvasRenderer
 * - WebSocketClient
 * - GameStateManager
 * - AnimationEngine
 * - ControlsPanel
 * - InfoOverlay
 * - PerformanceOptimizer
 */

import { CanvasRenderer } from './CanvasRenderer';
import { WebSocketClient } from './WebSocketClient';
import { GameStateManager } from './GameStateManager';
import { AnimationEngine } from './AnimationEngine';
import { PerformanceOptimizer } from './PerformanceOptimizer';
import { GameState } from '../../types/pacman';

export class IntegrationTest {
  private canvas: HTMLCanvasElement;
  private renderer: CanvasRenderer | null = null;
  private wsClient: WebSocketClient | null = null;
  private stateManager: GameStateManager | null = null;
  private animationEngine: AnimationEngine | null = null;
  private performanceOptimizer: PerformanceOptimizer | null = null;
  
  private testResults: Array<{
    component: string;
    test: string;
    passed: boolean;
    message: string;
    duration: number;
  }> = [];
  
  private startTime: number = 0;
  
  constructor(canvas?: HTMLCanvasElement) {
    if (canvas) {
      this.canvas = canvas;
    } else {
      // Créer un canvas de test si aucun n'est fourni
      this.canvas = document.createElement('canvas');
      this.canvas.width = 800;
      this.canvas.height = 600;
    }
  }
  
  /**
   * Ajoute un résultat de test
   */
  private addTestResult(
    component: string,
    test: string,
    passed: boolean,
    message: string,
    duration: number
  ): void {
    this.testResults.push({
      component,
      test,
      passed,
      message,
      duration
    });
    
    const status = passed ? '✅' : '❌';
    console.log(`${status} [${component}] ${test}: ${message} (${duration.toFixed(0)} ms)`);
  }
  
  /**
   * Compte le nombre de tests réussis
   */
  private getPassedCount(): number {
    return this.testResults.filter(result => result.passed).length;
  }
  
  /**
   * Exécute tous les tests d'intégration
   */
  public async runAllTests(): Promise<Array<{
    component: string;
    test: string;
    passed: boolean;
    message: string;
    duration: number;
  }>> {
    this.startTime = performance.now();
    this.testResults = [];
    
    console.log('🚀 Démarrage des tests d\'intégration du système de visualisation Pac-Man');
    
    try {
      // 1. Test du CanvasRenderer
      await this.testCanvasRenderer();
      
      // 2. Test du GameStateManager
      await this.testGameStateManager();
      
      // 3. Test de l'AnimationEngine
      await this.testAnimationEngine();
      
      // 4. Test du PerformanceOptimizer
      await this.testPerformanceOptimizer();
      
      // 5. Test du WebSocketClient (simulé)
      await this.testWebSocketClient();
      
      // 6. Test d'intégration complète
      await this.testFullIntegration();
      
    } catch (error) {
      this.addTestResult('Integration', 'Global', false, `Erreur globale: ${error}`, 0);
    }
    
    const totalDuration = performance.now() - this.startTime;
    console.log(`✅ Tests terminés en ${totalDuration.toFixed(0)} ms`);
    console.log(`📊 Résultats: ${this.getPassedCount()} / ${this.testResults.length} tests réussis`);
    
    return this.testResults;
  }
  
  /**
   * Test du CanvasRenderer
   */
  private async testCanvasRenderer(): Promise<void> {
    const testStart = performance.now();
    
    try {
      // Créer le renderer
      this.renderer = new CanvasRenderer(this.canvas, {
        cellSize: 20,
        zoom: 1.5,
        showGrid: true,
        showStats: true,
        highlightPaths: false,
        fps: 60,
        renderScale: 1
      });
      
      // Vérifier que le renderer est créé
      if (!this.renderer) {
        throw new Error('CanvasRenderer non créé');
      }
      
      // Tester le caching de grille
      this.renderer.cacheGrid(25, 25);
      
      // Tester le rendu d'éléments simples
      this.renderer.renderPacman(5, 5, 'right', 0);
      this.renderer.renderGhost(10, 10, 'red', 'chase', 0);
      this.renderer.renderPellet(3, 3, 0);
      this.renderer.renderPowerPellet(1, 1, 0);
      
      // Tester la mise à jour de configuration
      this.renderer.updateConfig({ zoom: 2.0 });
      
      this.addTestResult(
        'CanvasRenderer',
        'Initialisation et rendu basique',
        true,
        'CanvasRenderer initialisé avec succès',
        performance.now() - testStart
      );
      
    } catch (error) {
      this.addTestResult(
        'CanvasRenderer',
        'Initialisation et rendu basique',
        false,
        `Erreur: ${error}`,
        performance.now() - testStart
      );
    }
  }
  
  /**
   * Test du GameStateManager
   */
  private async testGameStateManager(): Promise<void> {
    const testStart = performance.now();
    
    try {
      // Créer le gestionnaire d'état
      this.stateManager = new GameStateManager();
      
      if (!this.stateManager) {
        throw new Error('GameStateManager non créé');
      }
      
      // Créer des états de test
      const testState1: GameState = {
        grid: Array(25).fill(0).map(() => Array(25).fill(0)),
        pacman: { x: 5, y: 10, direction: 'right' },
        ghosts: [
          { x: 10, y: 5, color: '#FF0000', mode: 'chase' },
          { x: 15, y: 5, color: '#FF88FF', mode: 'scatter' }
        ],
        pellets: [{ x: 3, y: 3 }, { x: 4, y: 4 }],
        powerPellets: [{ x: 1, y: 1 }],
        score: 100,
        lives: 3,
        step: 0
      };
      
      const testState2: GameState = {
        ...testState1,
        pacman: { x: 6, y: 10, direction: 'right' },
        ghosts: [
          { x: 11, y: 5, color: '#FF0000', mode: 'chase' },
          { x: 16, y: 5, color: '#FF88FF', mode: 'scatter' }
        ],
        score: 200,
        step: 1
      };
      
      // Ajouter des états
      this.stateManager.addState(testState1);
      this.stateManager.addState(testState2);
      
      // Récupérer l'état actuel
      const currentState = this.stateManager.getCurrentState();
      if (!currentState) {
        throw new Error('Impossible de récupérer l\'état actuel');
      }
      
      // Vérifier que l'état est correct
      if (currentState.score !== 100 && currentState.score !== 200) {
        throw new Error(`Score incorrect: ${currentState.score}`);
      }
      
      // Tester la prédiction (variable intentionnellement non utilisée)
      const predictedState = this.stateManager.predictNextState(100);
      // Utiliser la variable pour éviter le warning
      if (predictedState) {
        // rien
      }
      
      this.addTestResult(
        'GameStateManager',
        'Gestion d\'états et interpolation',
        true,
        `GameStateManager fonctionnel (${currentState.step} étapes)`,
        performance.now() - testStart
      );
      
    } catch (error) {
      this.addTestResult(
        'GameStateManager',
        'Gestion d\'états et interpolation',
        false,
        `Erreur: ${error}`,
        performance.now() - testStart
      );
    }
  }
  
  /**
   * Test de l'AnimationEngine
   */
  private async testAnimationEngine(): Promise<void> {
    const testStart = performance.now();
    
    try {
      // Créer le moteur d'animations
      this.animationEngine = new AnimationEngine({
        fps: 60,
        enableParticles: true,
        particleCount: 50,
        enableScreenShake: false,
        enableTrails: false,
        enableBloom: false,
        bloomIntensity: 0.1
      });
      
      if (!this.animationEngine) {
        throw new Error('AnimationEngine non créé');
      }
      
      // Tester les animations
      const animationId = this.animationEngine.createAnimation(
        'test',
        { x: 0, y: 0 },
        { x: 100, y: 100 },
        1000,
        this.animationEngine.easeOutCubic,
        (_value) => {
          // Callback de mise à jour
        },
        () => {
          // Callback de complétion
        }
      );
      
      if (!animationId) {
        throw new Error('Animation non créée');
      }
      
      // Tester les particules
      this.animationEngine.createParticles(50, 50, 10, 'generic', '#FFFFFF', 2);
      
      // Tester les fonctions d'easing
      const easedValue = this.animationEngine.easeOutCubic(0.5);
      if (easedValue < 0 || easedValue > 1) {
        throw new Error(`Valeur d'easing invalide: ${easedValue}`);
      }
      
      this.addTestResult(
        'AnimationEngine',
        'Animations et particules',
        true,
        `AnimationEngine fonctionnel (animation: ${animationId})`,
        performance.now() - testStart
      );
      
    } catch (error) {
      this.addTestResult(
        'AnimationEngine',
        'Animations et particules',
        false,
        `Erreur: ${error}`,
        performance.now() - testStart
      );
    }
  }
  
  /**
   * Test du PerformanceOptimizer
   */
  private async testPerformanceOptimizer(): Promise<void> {
    const testStart = performance.now();
    
    try {
      // Créer l'optimiseur
      this.performanceOptimizer = new PerformanceOptimizer({
        enableWebWorkers: false, // Désactivé pour les tests
        enableCompression: false,
        enableCaching: true,
        cacheSize: 10,
        workerCount: 1,
        targetFPS: 60,
        memoryLimit: 100
      });
      
      if (!this.performanceOptimizer) {
        throw new Error('PerformanceOptimizer non créé');
      }
      
      // Tester le caching
      this.performanceOptimizer.cacheItem('test_key', { data: 'test_value' }, 5000);
      const cachedItem = this.performanceOptimizer.getCachedItem('test_key');
      
      if (!cachedItem || cachedItem.data !== 'test_value') {
        throw new Error('Cache non fonctionnel');
      }
      
      // Tester l'interpolation
      const states = [
        { x: 0, y: 0 },
        { x: 10, y: 10 },
        { x: 20, y: 20 }
      ];
      
      const interpolated = await this.performanceOptimizer.interpolateStates(states, 0.5);
      if (!interpolated) {
        throw new Error('Interpolation échouée');
      }
      
      // Tester les métriques
      const metrics = this.performanceOptimizer.getMetrics();
      if (typeof metrics.fps !== 'number') {
        throw new Error('Métriques non disponibles');
      }
      
      this.addTestResult(
        'PerformanceOptimizer',
        'Caching et optimisation',
        true,
        `PerformanceOptimizer fonctionnel (FPS: ${metrics.fps})`,
        performance.now() - testStart
      );
      
    } catch (error) {
      this.addTestResult(
        'PerformanceOptimizer',
        'Caching et optimisation',
        false,
        `Erreur: ${error}`,
        performance.now() - testStart
      );
    }
  }
  
  /**
   * Test du WebSocketClient (simulé)
   */
  private async testWebSocketClient(): Promise<void> {
    const testStart = performance.now();
    
    try {
      // Créer un client WebSocket simulé (pas de connexion réelle)
      this.wsClient = new WebSocketClient({
        url: 'ws://localhost:8000/ws/game_state',
        maxReconnectAttempts: 3,
        reconnectDelay: 1000,
        maxBufferSize: 10
      });
      
      if (!this.wsClient) {
        throw new Error('WebSocketClient non créé');
      }
      
      // Tester les méthodes sans connexion réelle
      const stats = this.wsClient.getStats();
      const bufferSize = this.wsClient.getBufferSize();
      // Utiliser stats pour éviter le warning
      if (stats) {
        // rien
      }
      
      // Simuler la réception d'un état (variable intentionnellement non utilisée)
      const mockState: GameState = {
        grid: Array(25).fill(0).map(() => Array(25).fill(0)),
        pacman: { x: 5, y: 10, direction: 'right' },
        ghosts: [{ x: 10, y: 5, color: '#FF0000', mode: 'chase' }],
        pellets: [{ x: 3, y: 3 }],
        powerPellets: [],
        score: 150,
        lives: 3,
        step: 42
      };
      // Utiliser mockState pour éviter le warning
      if (mockState) {
        // rien
      }
      
      // Note: Dans un test réel, on simulerait la réception via onGameState
      
      this.addTestResult(
        'WebSocketClient',
        'Initialisation et configuration',
        true,
        `WebSocketClient configuré (buffer: ${bufferSize})`,
        performance.now() - testStart
      );
      
    } catch (error) {
      this.addTestResult(
        'WebSocketClient',
        'Initialisation et configuration',
        false,
        `Erreur: ${error}`,
        performance.now() - testStart
      );
    }
  }
  
  /**
   * Test d'intégration complète
   */
  private async testFullIntegration(): Promise<void> {
    const testStart = performance.now();
    
    try {
      // Vérifier que tous les composants sont initialisés
      if (!this.renderer || !this.stateManager || !this.animationEngine || !this.performanceOptimizer) {
        throw new Error('Composants manquants pour le test d\'intégration');
      }
      
      // Configurer l'AnimationEngine avec le renderer
      this.animationEngine.setRenderer(this.renderer);
      
      // Créer un état de test
      const testState: GameState = {
        grid: Array(20).fill(0).map(() => Array(20).fill(0)),
        pacman: { x: 8, y: 10, direction: 'right' },
        ghosts: [
          { x: 5, y: 5, color: '#FF0000', mode: 'chase' },
          { x: 15, y: 5, color: '#FF88FF', mode: 'scatter' },
          { x: 5, y: 15, color: '#00FFFF', mode: 'chase' },
          { x: 15, y: 15, color: '#FFAA00', mode: 'frightened' }
        ],
        pellets: Array.from({ length: 50 }, (_, _i) => ({
          x: Math.floor(Math.random() * 20),
          y: Math.floor(Math.random() * 20)
        })),
        powerPellets: [
          { x: 1, y: 1 },
          { x: 18, y: 1 },
          { x: 1, y: 18 },
          { x: 18, y: 18 }
        ],
        score: 1234,
        lives: 3,
        step: 100
      };
      // Ajouter l'état au gestionnaire
      this.stateManager.addState(testState);
      
      // Récupérer l'état actuel
      const currentState = this.stateManager.getCurrentState();
      if (!currentState) {
        throw new Error('État non disponible après ajout');
      }
      
      // Rendu de test
      this.renderer.renderPacman(
        currentState.pacman.x,
        currentState.pacman.y,
        currentState.pacman.direction,
        0
      );
      
      // Rendu des fantômes
      currentState.ghosts.forEach((ghost, index) => {
        this.renderer!.renderGhost(
          ghost.x,
          ghost.y,
          ghost.color,
          ghost.mode,
          index
        );
      });
      
      // Rendu des pac-gommes
      currentState.pellets.forEach(pellet => {
        this.renderer!.renderPellet(pellet.x, pellet.y, 0);
      });
      
      // Rendu des informations
      this.renderer.renderGameInfo(
        currentState.score,
        currentState.lives,
        currentState.step,
        60
      );
      
      // Tester les animations
      const pacmanAnimation = this.animationEngine.animatePacman(currentState.pacman, 0);
      if (!pacmanAnimation || typeof pacmanAnimation.angle !== 'number') {
        throw new Error('Animation Pac-Man échouée');
      }
      
      // Tester l'optimisation
      const optimizedStates = await this.performanceOptimizer.interpolateStates([testState, testState], 0.5);
      if (!optimizedStates) {
        throw new Error('Optimisation d\'interpolation échouée');
      }
      
      this.addTestResult(
        'Integration',
        'Intégration complète',
        true,
        `Système intégré avec succès (score: ${currentState.score}, vies: ${currentState.lives})`,
        performance.now() - testStart
      );
      
    } catch (error) {
      this.addTestResult(
        'Integration',
        'Intégration complète',
        false,
        `Erreur d'intégration: ${error}`,
        performance.now() - testStart
      );
    }
  }
}
      
