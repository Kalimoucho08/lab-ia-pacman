/**
 * Moteur de rendu Canvas HTML5 optimisé pour Pac-Man
 * 
 * Fonctionnalités :
 * - Rendu 60 FPS avec double buffering
 * - Sprite sheet préchargée
 * - Animations fluides (Pac-Man, fantômes, effets)
 * - Optimisations de performance (caching, requestAnimationFrame)
 * - Support zoom/pan
 * - Effets visuels (scintillement, particules, transitions)
 */

import { GameState } from '../../types/pacman';

export interface RenderConfig {
  cellSize: number;
  zoom: number;
  showGrid: boolean;
  showStats: boolean;
  highlightPaths: boolean;
  fps: number;
  renderScale: number;
}

export interface SpriteSheet {
  pacman: {
    [direction: string]: HTMLImageElement[];
  };
  ghosts: {
    [color: string]: HTMLImageElement[];
  };
  pellets: HTMLImageElement;
  powerPellets: HTMLImageElement;
  walls: HTMLImageElement;
  effects: {
    score: HTMLImageElement;
    particles: HTMLImageElement;
  };
}

export class CanvasRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private offscreenCanvas: HTMLCanvasElement;
  private offscreenCtx: CanvasRenderingContext2D;
  private config: RenderConfig;
  private sprites: SpriteSheet | null = null;
  private lastFrameTime: number = 0;
  private frameCount: number = 0;
  private fps: number = 0;
  private animationFrameId: number | null = null;
  private isRendering: boolean = false;
  private cachedGrid: ImageBitmap | null = null;
  private gridSize: { width: number; height: number } = { width: 0, height: 0 };

  // Couleurs standard pour les fantômes
  private static readonly GHOST_COLORS: Record<string, string> = {
    red: '#FF0000',
    pink: '#FFB8FF',
    cyan: '#00FFFF',
    orange: '#FFB852',
    blue: '#0000FF', // mode peur
    white: '#FFFFFF' // mode peur clignotant
  };

  constructor(canvas: HTMLCanvasElement, config: Partial<RenderConfig> = {}) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Impossible d\'obtenir le contexte 2D du canvas');
    }
    this.ctx = ctx;

    // Créer un canvas hors écran pour le double buffering
    this.offscreenCanvas = document.createElement('canvas');
    this.offscreenCanvas.width = canvas.width;
    this.offscreenCanvas.height = canvas.height;
    const offscreenCtx = this.offscreenCanvas.getContext('2d');
    if (!offscreenCtx) {
      throw new Error('Impossible d\'obtenir le contexte 2D du canvas hors écran');
    }
    this.offscreenCtx = offscreenCtx;

    // Configuration par défaut
    this.config = {
      cellSize: 20,
      zoom: 1.5,
      showGrid: true,
      showStats: true,
      highlightPaths: false,
      fps: 60,
      renderScale: window.devicePixelRatio || 1,
      ...config
    };

    this.setupCanvas();
    this.preloadSprites();
  }

  /**
   * Configure le canvas avec les dimensions correctes et le DPI scaling
   */
  private setupCanvas(): void {
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    
    // Ajuster la taille du canvas pour le DPI
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.canvas.style.width = `${rect.width}px`;
    this.canvas.style.height = `${rect.height}px`;
    
    // Configurer le contexte
    this.ctx.scale(dpr, dpr);
    this.ctx.imageSmoothingEnabled = true;
    this.ctx.imageSmoothingQuality = 'high';
    
    // Synchroniser le canvas hors écran
    this.offscreenCanvas.width = this.canvas.width;
    this.offscreenCanvas.height = this.canvas.height;
    this.offscreenCtx.scale(dpr, dpr);
    this.offscreenCtx.imageSmoothingEnabled = true;
    this.offscreenCtx.imageSmoothingQuality = 'high';
  }

  /**
   * Préchage les sprites (dans une implémentation réelle, charger depuis des fichiers)
   */
  private preloadSprites(): void {
    // Pour l'instant, créer des sprites programmatiquement
    // Dans une version complète, on chargerait des images réelles
    this.sprites = {
      pacman: {
        right: [this.createPacmanSprite('right', 0), this.createPacmanSprite('right', 1)],
        left: [this.createPacmanSprite('left', 0), this.createPacmanSprite('left', 1)],
        up: [this.createPacmanSprite('up', 0), this.createPacmanSprite('up', 1)],
        down: [this.createPacmanSprite('down', 0), this.createPacmanSprite('down', 1)],
      },
      ghosts: {
        red: [this.createGhostSprite('red', 0), this.createGhostSprite('red', 1)],
        pink: [this.createGhostSprite('pink', 0), this.createGhostSprite('pink', 1)],
        cyan: [this.createGhostSprite('cyan', 0), this.createGhostSprite('cyan', 1)],
        orange: [this.createGhostSprite('orange', 0), this.createGhostSprite('orange', 1)],
        blue: [this.createGhostSprite('blue', 0), this.createGhostSprite('blue', 1)],
        white: [this.createGhostSprite('white', 0), this.createGhostSprite('white', 1)],
      },
      pellets: this.createPelletSprite(),
      powerPellets: this.createPowerPelletSprite(),
      walls: this.createWallSprite(),
      effects: {
        score: this.createScoreEffectSprite(),
        particles: this.createParticleSprite(),
      }
    };
  }

  /**
   * Crée un sprite Pac-Man programmatiquement
   */
  private createPacmanSprite(direction: string, frame: number): HTMLImageElement {
    const canvas = document.createElement('canvas');
    canvas.width = this.config.cellSize;
    canvas.height = this.config.cellSize;
    const ctx = canvas.getContext('2d')!;
    
    // Dessiner Pac-Man
    ctx.fillStyle = '#FFFF00';
    const angle = frame === 0 ? Math.PI / 4 : Math.PI / 6;
    const startAngle = this.getPacmanStartAngle(direction);
    
    ctx.beginPath();
    ctx.arc(
      this.config.cellSize / 2,
      this.config.cellSize / 2,
      this.config.cellSize * 0.4,
      startAngle + angle,
      startAngle + Math.PI * 2 - angle
    );
    ctx.lineTo(this.config.cellSize / 2, this.config.cellSize / 2);
    ctx.fill();
    
    // Ajouter un œil
    ctx.fillStyle = '#000000';
    const eyePos = this.getPacmanEyePosition(direction);
    ctx.beginPath();
    ctx.arc(
      this.config.cellSize / 2 + eyePos.x,
      this.config.cellSize / 2 + eyePos.y,
      this.config.cellSize * 0.1,
      0,
      Math.PI * 2
    );
    ctx.fill();
    
    const img = new Image();
    img.src = canvas.toDataURL();
    return img;
  }

  private getPacmanStartAngle(direction: string): number {
    switch (direction) {
      case 'right': return Math.PI / 4;
      case 'left': return Math.PI * 5/4;
      case 'up': return Math.PI * 7/4;
      case 'down': return Math.PI * 3/4;
      default: return Math.PI / 4;
    }
  }

  private getPacmanEyePosition(direction: string): { x: number; y: number } {
    const offset = this.config.cellSize * 0.15;
    switch (direction) {
      case 'right': return { x: offset, y: -offset };
      case 'left': return { x: -offset, y: -offset };
      case 'up': return { x: 0, y: -offset * 1.5 };
      case 'down': return { x: 0, y: offset * 0.5 };
      default: return { x: offset, y: -offset };
    }
  }

  /**
   * Crée un sprite de fantôme programmatiquement
   */
  private createGhostSprite(color: string, frame: number): HTMLImageElement {
    const canvas = document.createElement('canvas');
    canvas.width = this.config.cellSize;
    canvas.height = this.config.cellSize;
    const ctx = canvas.getContext('2d')!;
    
    // Corps du fantôme
    ctx.fillStyle = CanvasRenderer.GHOST_COLORS[color] || color;
    const bodyHeight = this.config.cellSize * 0.7;
    const bodyWidth = this.config.cellSize * 0.8;
    
    // Forme de fantôme avec vague en bas
    ctx.beginPath();
    ctx.arc(
      this.config.cellSize / 2,
      this.config.cellSize / 2 - bodyHeight * 0.2,
      bodyWidth / 2,
      Math.PI,
      Math.PI * 2
    );
    
    // Bas ondulé
    const waveAmplitude = frame === 0 ? 2 : 4;
    for (let i = 0; i < 3; i++) {
      const x = this.config.cellSize / 2 - bodyWidth / 2 + (bodyWidth / 3) * i;
