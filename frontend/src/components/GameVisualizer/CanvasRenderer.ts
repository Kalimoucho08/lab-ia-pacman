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
  private _gridSize: { width: number; height: number } = { width: 0, height: 0 };

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
      const y = this.config.cellSize / 2 + bodyHeight * 0.3;
      ctx.quadraticCurveTo(
        x + bodyWidth / 6,
        y + waveAmplitude,
        x + bodyWidth / 3,
        y
      );
    }
    ctx.closePath();
    ctx.fill();
    
    // Yeux
    ctx.fillStyle = '#FFFFFF';
    const eyeRadius = this.config.cellSize * 0.12;
    const leftEyeX = this.config.cellSize / 2 - eyeRadius;
    const rightEyeX = this.config.cellSize / 2 + eyeRadius;
    const eyeY = this.config.cellSize / 2 - bodyHeight * 0.1;
    
    ctx.beginPath();
    ctx.arc(leftEyeX, eyeY, eyeRadius, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.beginPath();
    ctx.arc(rightEyeX, eyeY, eyeRadius, 0, Math.PI * 2);
    ctx.fill();
    
    // Pupilles
    ctx.fillStyle = '#0000FF';
    const pupilOffset = frame === 0 ? 0 : eyeRadius * 0.3;
    ctx.beginPath();
    ctx.arc(leftEyeX + pupilOffset, eyeY, eyeRadius * 0.5, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.beginPath();
    ctx.arc(rightEyeX + pupilOffset, eyeY, eyeRadius * 0.5, 0, Math.PI * 2);
    ctx.fill();
    
    const img = new Image();
    img.src = canvas.toDataURL();
    return img;
  }

  private createPelletSprite(): HTMLImageElement {
    const canvas = document.createElement('canvas');
    canvas.width = this.config.cellSize;
    canvas.height = this.config.cellSize;
    const ctx = canvas.getContext('2d')!;
    
    // Pac-gomme scintillante
    const gradient = ctx.createRadialGradient(
      this.config.cellSize / 2,
      this.config.cellSize / 2,
      0,
      this.config.cellSize / 2,
      this.config.cellSize / 2,
      this.config.cellSize * 0.2
    );
    gradient.addColorStop(0, '#FFFFFF');
    gradient.addColorStop(1, '#CCCCCC');
    
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(
      this.config.cellSize / 2,
      this.config.cellSize / 2,
      this.config.cellSize * 0.15,
      0,
      Math.PI * 2
    );
    ctx.fill();
    
    const img = new Image();
    img.src = canvas.toDataURL();
    return img;
  }

  private createPowerPelletSprite(): HTMLImageElement {
    const canvas = document.createElement('canvas');
    canvas.width = this.config.cellSize;
    canvas.height = this.config.cellSize;
    const ctx = canvas.getContext('2d')!;
    
    // Power pellet pulsante
    const gradient = ctx.createRadialGradient(
      this.config.cellSize / 2,
      this.config.cellSize / 2,
      0,
      this.config.cellSize / 2,
      this.config.cellSize / 2,
      this.config.cellSize * 0.3
    );
    gradient.addColorStop(0, '#FFFF00');
    gradient.addColorStop(0.7, '#FFAA00');
    gradient.addColorStop(1, '#FF5500');
    
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(
      this.config.cellSize / 2,
      this.config.cellSize / 2,
      this.config.cellSize * 0.25,
      0,
      Math.PI * 2
    );
    ctx.fill();
    
    // Effet de brillance
    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.beginPath();
    ctx.arc(
      this.config.cellSize / 2 - this.config.cellSize * 0.1,
      this.config.cellSize / 2 - this.config.cellSize * 0.1,
      this.config.cellSize * 0.1,
      0,
      Math.PI * 2
    );
    ctx.fill();
    
    const img = new Image();
    img.src = canvas.toDataURL();
    return img;
  }

  private createWallSprite(): HTMLImageElement {
    const canvas = document.createElement('canvas');
    canvas.width = this.config.cellSize;
    canvas.height = this.config.cellSize;
    const ctx = canvas.getContext('2d')!;
    
    // Mur avec texture
    ctx.fillStyle = '#1E3A8A';
    ctx.fillRect(0, 0, this.config.cellSize, this.config.cellSize);
    
    // Bordure intérieure
    ctx.strokeStyle = '#3B82F6';
    ctx.lineWidth = 2;
    ctx.strokeRect(2, 2, this.config.cellSize - 4, this.config.cellSize - 4);
    
    // Texture de points
    ctx.fillStyle = '#60A5FA';
    for (let i = 0; i < 4; i++) {
      for (let j = 0; j < 4; j++) {
        if ((i + j) % 2 === 0) {
          ctx.beginPath();
          ctx.arc(
            4 + i * (this.config.cellSize - 8) / 3,
            4 + j * (this.config.cellSize - 8) / 3,
            1,
            0,
            Math.PI * 2
          );
          ctx.fill();
        }
      }
    }
    
    const img = new Image();
    img.src = canvas.toDataURL();
    return img;
  }

  private createScoreEffectSprite(): HTMLImageElement {
    const canvas = document.createElement('canvas');
    canvas.width = this.config.cellSize * 2;
    canvas.height = this.config.cellSize;
    const ctx = canvas.getContext('2d')!;
    
    // Effet de score (étoile)
    const gradient = ctx.createRadialGradient(
      this.config.cellSize,
      this.config.cellSize / 2,
      0,
      this.config.cellSize,
      this.config.cellSize / 2,
      this.config.cellSize * 0.8
    );
    gradient.addColorStop(0, '#FFFFFF');
    gradient.addColorStop(1, '#FFFF00');
    
    ctx.fillStyle = gradient;
    ctx.beginPath();
    for (let i = 0; i < 5; i++) {
      const angle = (i * Math.PI * 2) / 5;
      const outerRadius = this.config.cellSize * 0.4;
      const innerRadius = this.config.cellSize * 0.2;
      
      const x1 = this.config.cellSize + Math.cos(angle) * outerRadius;
      const y1 = this.config.cellSize / 2 + Math.sin(angle) * outerRadius;
      
      const x2 = this.config.cellSize + Math.cos(angle + Math.PI / 5) * innerRadius;
      const y2 = this.config.cellSize / 2 + Math.sin(angle + Math.PI / 5) * innerRadius;
      
      if (i === 0) {
        ctx.moveTo(x1, y1);
      } else {
        ctx.lineTo(x1, y1);
      }
      ctx.lineTo(x2, y2);
    }
    ctx.closePath();
    ctx.fill();
    
    const img = new Image();
    img.src = canvas.toDataURL();
    return img;
  }

  private createParticleSprite(): HTMLImageElement {
    const canvas = document.createElement('canvas');
    canvas.width = this.config.cellSize;
    canvas.height = this.config.cellSize;
    const ctx = canvas.getContext('2d')!;
    
    // Particule circulaire avec gradient
    const gradient = ctx.createRadialGradient(
      this.config.cellSize / 2,
      this.config.cellSize / 2,
      0,
      this.config.cellSize / 2,
      this.config.cellSize / 2,
      this.config.cellSize * 0.3
    );
    gradient.addColorStop(0, '#FFFFFF');
    gradient.addColorStop(0.5, '#FFAA00');
    gradient.addColorStop(1, 'rgba(255, 100, 0, 0)');
    
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(
      this.config.cellSize / 2,
      this.config.cellSize / 2,
      this.config.cellSize * 0.25,
      0,
      Math.PI * 2
    );
    ctx.fill();
    
    const img = new Image();
    img.src = canvas.toDataURL();
    return img;
  }

  /**
   * Met à jour la configuration de rendu
   */
  public updateConfig(config: Partial<RenderConfig>): void {
    this.config = { ...this.config, ...config };
    this.setupCanvas();
  }

  /**
   * Démarre le rendu continu
   */
  public startRendering(): void {
    if (this.isRendering) return;
    
    this.isRendering = true;
    this.lastFrameTime = performance.now();
    
    const renderLoop = (timestamp: number) => {
      if (!this.isRendering) return;
      
      // Calculer le FPS
      this.frameCount++;
      const deltaTime = timestamp - this.lastFrameTime;
      if (deltaTime >= 1000) {
        this.fps = Math.round((this.frameCount * 1000) / deltaTime);
        this.frameCount = 0;
        this.lastFrameTime = timestamp;
      }
      
      // Rendu sur le canvas hors écran
      this.renderToOffscreen();
      
      // Copier le canvas hors écran vers le canvas principal
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      this.ctx.drawImage(this.offscreenCanvas, 0, 0);
      
      this.animationFrameId = requestAnimationFrame(renderLoop);
    };
    
    this.animationFrameId = requestAnimationFrame(renderLoop);
  }

  /**
   * Arrête le rendu
   */
  public stopRendering(): void {
    this.isRendering = false;
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  /**
   * Rend un état de jeu sur le canvas hors écran
   */
  private renderToOffscreen(): void {
    const ctx = this.offscreenCtx;
    const { cellSize: _cellSize, zoom: _zoom, showGrid } = this.config;
    
    // Effacer le canvas
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, this.offscreenCanvas.width, this.offscreenCanvas.height);
    
    // Rendu de la grille (si activé)
    if (showGrid && this.cachedGrid) {
      ctx.drawImage(this.cachedGrid, 0, 0);
    }
    
    // Note: Le rendu des éléments de jeu nécessite un GameState
    // Cette méthode sera complétée dans GameStateManager
  }

  /**
   * Prerend la grille pour optimisation
   */
  public cacheGrid(gridWidth: number, gridHeight: number): void {
    this._gridSize = { width: gridWidth, height: gridHeight };
    
    const canvas = document.createElement('canvas');
    const cellSize = this.config.cellSize * this.config.zoom;
    canvas.width = gridWidth * cellSize;
    canvas.height = gridHeight * cellSize;
    const ctx = canvas.getContext('2d')!;
    
    // Dessiner la grille
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    
    // Lignes verticales
    for (let x = 0; x <= gridWidth; x++) {
      ctx.beginPath();
      ctx.moveTo(x * cellSize, 0);
      ctx.lineTo(x * cellSize, canvas.height);
      ctx.stroke();
    }
    
    // Lignes horizontales
    for (let y = 0; y <= gridHeight; y++) {
      ctx.beginPath();
      ctx.moveTo(0, y * cellSize);
      ctx.lineTo(canvas.width, y * cellSize);
      ctx.stroke();
    }
    
    // Convertir en ImageBitmap pour performance
    createImageBitmap(canvas).then(bitmap => {
      this.cachedGrid = bitmap;
    });
  }

  /**
   * Rend Pac-Man
   */
  public renderPacman(x: number, y: number, direction: string, frame: number = 0): void {
    if (!this.sprites) return;
    
    const ctx = this.offscreenCtx;
    const { cellSize, zoom } = this.config;
    const sprites = this.sprites.pacman[direction];
    
    if (sprites && sprites[frame % sprites.length]) {
      const sprite = sprites[frame % sprites.length];
      const drawX = x * cellSize * zoom;
      const drawY = y * cellSize * zoom;
      
      ctx.drawImage(
        sprite,
        drawX,
        drawY,
        cellSize * zoom,
        cellSize * zoom
      );
    }
  }

  /**
   * Rend un fantôme
   */
  public renderGhost(x: number, y: number, color: string, mode: string, frame: number = 0): void {
    if (!this.sprites) return;
    
    const ctx = this.offscreenCtx;
    const { cellSize, zoom } = this.config;
    
    // Déterminer la couleur en fonction du mode
    let spriteColor = color;
    if (mode === 'frightened') {
      spriteColor = (Math.floor(frame / 10) % 2 === 0) ? 'blue' : 'white';
    }
    
    const sprites = this.sprites.ghosts[spriteColor];
    if (sprites && sprites[frame % sprites.length]) {
      const sprite = sprites[frame % sprites.length];
      const drawX = x * cellSize * zoom;
      const drawY = y * cellSize * zoom;
      
      ctx.drawImage(
        sprite,
        drawX,
        drawY,
        cellSize * zoom,
        cellSize * zoom
      );
    }
  }

  /**
   * Rend une pac-gomme
   */
  public renderPellet(x: number, y: number, frame: number = 0): void {
    if (!this.sprites) return;
    
    const ctx = this.offscreenCtx;
    const { cellSize, zoom } = this.config;
    const sprite = this.sprites.pellets;
    
    // Animation de scintillement
    const alpha = 0.7 + 0.3 * Math.sin(frame * 0.2);
    ctx.globalAlpha = alpha;
    
    const drawX = x * cellSize * zoom + (cellSize * zoom * 0.5) - (cellSize * zoom * 0.15);
    const drawY = y * cellSize * zoom + (cellSize * zoom * 0.5) - (cellSize * zoom * 0.15);
    const size = cellSize * zoom * 0.3;
    
    ctx.drawImage(sprite, drawX, drawY, size, size);
    ctx.globalAlpha = 1.0;
  }

  /**
   * Rend une super pac-gomme
   */
  public renderPowerPellet(x: number, y: number, frame: number = 0): void {
    if (!this.sprites) return;
    
    const ctx = this.offscreenCtx;
    const { cellSize, zoom } = this.config;
    const sprite = this.sprites.powerPellets;
    
    // Animation de pulsation
    const scale = 0.8 + 0.2 * Math.sin(frame * 0.3);
    const drawX = x * cellSize * zoom + (cellSize * zoom * 0.5) - (cellSize * zoom * 0.25 * scale);
    const drawY = y * cellSize * zoom + (cellSize * zoom * 0.5) - (cellSize * zoom * 0.25 * scale);
    const size = cellSize * zoom * 0.5 * scale;
    
    ctx.drawImage(sprite, drawX, drawY, size, size);
  }

  /**
   * Rend un mur
   */
  public renderWall(x: number, y: number): void {
    if (!this.sprites) return;
    
    const ctx = this.offscreenCtx;
    const { cellSize, zoom } = this.config;
    const sprite = this.sprites.walls;
    
    const drawX = x * cellSize * zoom;
    const drawY = y * cellSize * zoom;
    
    ctx.drawImage(sprite, drawX, drawY, cellSize * zoom, cellSize * zoom);
  }

  /**
   * Rend un effet de score
   */
  public renderScoreEffect(x: number, y: number, score: number, frame: number = 0): void {
    if (!this.sprites) return;
    
    const ctx = this.offscreenCtx;
    const { cellSize, zoom } = this.config;
    const sprite = this.sprites.effects.score;
    
    // Animation de montée
    const offsetY = -frame * 2;
    const alpha = 1.0 - frame * 0.1;
    
    ctx.globalAlpha = Math.max(0, alpha);
    const drawX = x * cellSize * zoom;
    const drawY = y * cellSize * zoom + offsetY;
    
    ctx.drawImage(sprite, drawX, drawY, cellSize * zoom * 2, cellSize * zoom);
    
    // Afficher le score
    ctx.fillStyle = '#FFFFFF';
    ctx.font = `${12 * zoom}px Arial`;
    ctx.textAlign = 'center';
    ctx.fillText(
      `+${score}`,
      drawX + cellSize * zoom,
      drawY + cellSize * zoom * 0.7
    );
    
    ctx.globalAlpha = 1.0;
    ctx.textAlign = 'left';
  }

  /**
   * Rend des particules
   */
  public renderParticles(x: number, y: number, count: number, frame: number = 0): void {
    if (!this.sprites) return;
    
    const ctx = this.offscreenCtx;
    const { cellSize, zoom } = this.config;
    const sprite = this.sprites.effects.particles;
    
    for (let i = 0; i < count; i++) {
      const angle = (i * Math.PI * 2) / count + frame * 0.1;
      const distance = (frame % 10) * 2;
      const particleX = x * cellSize * zoom + Math.cos(angle) * distance;
      const particleY = y * cellSize * zoom + Math.sin(angle) * distance;
      const size = cellSize * zoom * 0.2 * (1 - (frame % 20) / 20);
      
      ctx.globalAlpha = 0.7 * (1 - (frame % 20) / 20);
      ctx.drawImage(sprite, particleX, particleY, size, size);
    }
    
    ctx.globalAlpha = 1.0;
  }

  /**
   * Rend les informations de jeu (score, vies, etc.)
   */
  public renderGameInfo(score: number, lives: number, step: number, fps?: number): void {
    if (!this.config.showStats) return;
    
    const ctx = this.offscreenCtx;
    const { zoom } = this.config;
    
    ctx.fillStyle = '#FFFFFF';
    ctx.font = `${14 * zoom}px Arial`;
    ctx.textAlign = 'left';
    
    // Score
    ctx.fillText(`Score: ${score}`, 10 * zoom, 20 * zoom);
    
    // Vies
    ctx.fillText(`Vies: ${lives}`, 10 * zoom, 40 * zoom);
    
    // Étape
    ctx.fillText(`Étape: ${step}`, 10 * zoom, 60 * zoom);
    
    // FPS (si disponible)
    if (fps !== undefined) {
      ctx.fillText(`FPS: ${fps}`, 10 * zoom, 80 * zoom);
    }
  }

  /**
   * Rend un état de jeu complet (pour compatibilité avec GameVisualizer)
   */
  public render(gameState: GameState, config: any): void {
    // Mettre à jour la configuration si nécessaire
    if (config) {
      this.updateConfig(config);
    }
    
    // Rendu sur le canvas hors écran
    this.renderToOffscreen();
    
    // Rendu des éléments de jeu
    this.renderGameState(gameState);
    
    // Copier le canvas hors écran vers le canvas principal
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.ctx.drawImage(this.offscreenCanvas, 0, 0);
  }

  /**
   * Rend un état de jeu spécifique
   */
  private renderGameState(gameState: GameState): void {
    const { grid, pacman, ghosts, pellets, powerPellets, score, lives, step } = gameState;
    const frame = Math.floor(step / 2); // Utiliser l'étape pour l'animation
    
    // Rendu de la grille
    if (this.config.showGrid && grid) {
      this.renderGrid(grid);
    }
    
    // Rendu des pac-gommes
    pellets.forEach(pellet => {
      this.renderPellet(pellet.x, pellet.y, frame);
    });
    
    // Rendu des super pac-gommes
    powerPellets.forEach(powerPellet => {
      this.renderPowerPellet(powerPellet.x, powerPellet.y, frame);
    });
    
    // Rendu des fantômes
    ghosts.forEach(ghost => {
      this.renderGhost(ghost.x, ghost.y, ghost.color, ghost.mode, frame);
    });
    
    // Rendu de Pac-Man
    this.renderPacman(pacman.x, pacman.y, pacman.direction, frame);
    
    // Rendu des informations de jeu
    this.renderGameInfo(score, lives, step, this.fps);
  }

  /**
   * Rend la grille
   */
  private renderGrid(grid: number[][]): void {
    // Si la grille est déjà en cache, on l'utilise
    if (!this.cachedGrid) {
      this.cacheGrid(grid[0].length, grid.length);
    }
    
    // Dessiner la grille
    if (this.cachedGrid) {
      this.offscreenCtx.drawImage(this.cachedGrid, 0, 0);
    }
  }

  /**
   * Nettoie les ressources (alias de dispose pour compatibilité)
   */
  public cleanup(): void {
    this.dispose();
  }

  /**
   * Nettoie les ressources
   */
  public dispose(): void {
    this.stopRendering();
    if (this.cachedGrid) {
      this.cachedGrid.close();
      this.cachedGrid = null;
    }
  }
}
