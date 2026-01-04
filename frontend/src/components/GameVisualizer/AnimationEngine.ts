/**
 * Moteur d'animations 60 FPS pour Pac-Man
 * 
 * Fonctionnalités :
 * - Gestion d'animations fluides à 60 FPS
 * - Système de particules pour effets visuels
 * - Transitions et easing
 * - Synchronisation avec le rendu Canvas
 * - Gestion des ressources d'animation
 */

import { GameState } from '../../types/pacman';
import { CanvasRenderer } from './CanvasRenderer';

export interface AnimationConfig {
  fps: number;
  enableParticles: boolean;
  particleCount: number;
  enableScreenShake: boolean;
  enableTrails: boolean;
  trailLength: number;
  enableBloom: boolean;
  bloomIntensity: number;
}

export interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  maxLife: number;
  color: string;
  size: number;
  type: 'score' | 'pellet' | 'power' | 'ghost' | 'generic';
}

export interface Animation {
  id: string;
  type: string;
  startTime: number;
  duration: number;
  from: any;
  to: any;
  easing: (t: number) => number;
  onUpdate: (value: any, progress: number) => void;
  onComplete: () => void;
}

export class AnimationEngine {
  private config: AnimationConfig;
  private particles: Particle[] = [];
  private activeAnimations: Animation[] = [];
  private lastFrameTime = 0;
  private frameCount = 0;
  private isRunning = false;
  private animationFrameId: number | null = null;
  private renderer: CanvasRenderer | null = null;
  private screenShakeEffect = { x: 0, y: 0, intensity: 0, decay: 0.9 };
  private trails: Array<{ x: number; y: number; alpha: number }> = [];

  // Callbacks
  private onFrameCallbacks: ((deltaTime: number) => void)[] = [];
  private onParticleCreatedCallbacks: ((particle: Particle) => void)[] = [];
  private onAnimationCompleteCallbacks: ((animationId: string) => void)[] = [];

  constructor(config: Partial<AnimationConfig> = {}) {
    this.config = {
      fps: 60,
      enableParticles: true,
      particleCount: 100,
      enableScreenShake: false,
      enableTrails: false,
      trailLength: 10,
      enableBloom: false,
      bloomIntensity: 0.1,
      ...config
    };
  }

  /**
   * Définit le renderer Canvas
   */
  public setRenderer(renderer: CanvasRenderer): void {
    this.renderer = renderer;
  }

  /**
   * Démarre le moteur d'animations
   */
  public start(): void {
    if (this.isRunning) return;
    
    this.isRunning = true;
    this.lastFrameTime = performance.now();
    
    const animate = (timestamp: number) => {
      if (!this.isRunning) return;
      
      const deltaTime = timestamp - this.lastFrameTime;
      const targetFrameTime = 1000 / this.config.fps;
      
      if (deltaTime >= targetFrameTime) {
        this.lastFrameTime = timestamp - (deltaTime % targetFrameTime);
        this.frameCount++;
        
        // Mettre à jour les animations
        this.updateAnimations(deltaTime);
        
        // Mettre à jour les particules
        this.updateParticles(deltaTime);
        
        // Mettre à jour les effets d'écran
        this.updateScreenEffects(deltaTime);
        
        // Appeler les callbacks de frame
        this.onFrameCallbacks.forEach(callback => {
          try {
            callback(deltaTime);
          } catch (error) {
            console.error('AnimationEngine: Erreur dans le callback onFrame', error);
          }
        });
        
        // Rendu des effets si un renderer est disponible
        if (this.renderer) {
          this.renderEffects();
        }
      }
      
      this.animationFrameId = requestAnimationFrame(animate);
    };
    
    this.animationFrameId = requestAnimationFrame(animate);
  }

  /**
   * Arrête le moteur d'animations
   */
  public stop(): void {
    this.isRunning = false;
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  /**
   * Met à jour les animations actives
   */
  private updateAnimations(_deltaTime: number): void {
    const now = performance.now();
    const completedAnimations: string[] = [];
    
    for (let i = this.activeAnimations.length - 1; i >= 0; i--) {
      const animation = this.activeAnimations[i];
      const elapsed = now - animation.startTime;
      const progress = Math.min(elapsed / animation.duration, 1);
      const easedProgress = animation.easing(progress);
      
      // Mettre à jour la valeur de l'animation
      if (animation.onUpdate) {
        const value = this.interpolate(animation.from, animation.to, easedProgress);
        animation.onUpdate(value, easedProgress);
      }
      
      // Si l'animation est terminée
      if (progress >= 1) {
        if (animation.onComplete) {
          try {
            animation.onComplete();
          } catch (error) {
            console.error('AnimationEngine: Erreur dans onComplete', error);
          }
        }
        
        completedAnimations.push(animation.id);
        this.activeAnimations.splice(i, 1);
      }
    }
    
    // Notifier les animations terminées
    completedAnimations.forEach(animationId => {
      this.onAnimationCompleteCallbacks.forEach(callback => {
        try {
          callback(animationId);
        } catch (error) {
          console.error('AnimationEngine: Erreur dans le callback onAnimationComplete', error);
        }
      });
    });
  }

  /**
   * Interpolation entre deux valeurs
   */
  private interpolate(from: any, to: any, progress: number): any {
    if (typeof from === 'number' && typeof to === 'number') {
      return from + (to - from) * progress;
    }
    
    if (typeof from === 'object' && typeof to === 'object') {
      const result: any = {};
      for (const key in from) {
        if (typeof from[key] === 'number' && typeof to[key] === 'number') {
          result[key] = from[key] + (to[key] - from[key]) * progress;
        } else {
          result[key] = progress > 0.5 ? to[key] : from[key];
        }
      }
      return result;
    }
    
    return progress > 0.5 ? to : from;
  }

  /**
   * Met à jour les particules
   */
  private updateParticles(deltaTime: number): void {
    if (!this.config.enableParticles) return;
    
    const deltaSeconds = deltaTime / 1000;
    
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const particle = this.particles[i];
      
      // Mettre à jour la position
      particle.x += particle.vx * deltaSeconds;
      particle.y += particle.vy * deltaSeconds;
      
      // Appliquer la gravité (pour certains types)
      if (particle.type === 'score' || particle.type === 'generic') {
        particle.vy += 98 * deltaSeconds; // Gravité approximative
      }
      
      // Réduire la vie
      particle.life -= deltaSeconds;
      
      // Supprimer les particules mortes
      if (particle.life <= 0) {
        this.particles.splice(i, 1);
      }
    }
    
    // Limiter le nombre de particules
    if (this.particles.length > this.config.particleCount) {
      this.particles = this.particles.slice(-this.config.particleCount);
    }
  }

  /**
   * Met à jour les effets d'écran (tremblement, etc.)
   */
  private updateScreenEffects(_deltaTime: number): void {
    // Tremblement d'écran
    if (this.config.enableScreenShake && this.screenShakeEffect.intensity > 0) {
      this.screenShakeEffect.x = (Math.random() - 0.5) * this.screenShakeEffect.intensity;
      this.screenShakeEffect.y = (Math.random() - 0.5) * this.screenShakeEffect.intensity;
      this.screenShakeEffect.intensity *= this.screenShakeEffect.decay;
      
      if (this.screenShakeEffect.intensity < 0.1) {
        this.screenShakeEffect.intensity = 0;
        this.screenShakeEffect.x = 0;
        this.screenShakeEffect.y = 0;
      }
    }
    
    // Traînées
    if (this.config.enableTrails) {
      // Les traînées sont mises à jour lors du rendu
    }
  }

  /**
   * Rend les effets visuels
   */
  private renderEffects(): void {
    if (!this.renderer) return;
    
    // Rendu des particules
    this.particles.forEach(particle => {
      const alpha = particle.life / particle.maxLife;
      // const _size = particle.size * alpha; // Variable non utilisée, commentée
      
      // Dans une implémentation réelle, on utiliserait le renderer
      // Pour l'instant, on se contente de log
    });
    
    // Rendu des traînées
    if (this.config.enableTrails && this.trails.length > 0) {
      // Rendu des traînées
    }
  }

  /**
   * Crée une animation
   */
  public createAnimation(
    type: string,
    from: any,
    to: any,
    duration: number,
    easing: (t: number) => number = this.easeOutCubic,
    onUpdate?: (value: any, progress: number) => void,
    onComplete?: () => void
  ): string {
    const animationId = `anim_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const animation: Animation = {
      id: animationId,
      type,
      startTime: performance.now(),
      duration,
      from,
      to,
      easing,
      onUpdate: onUpdate || (() => {}),
      onComplete: onComplete || (() => {})
    };
    
    this.activeAnimations.push(animation);
    return animationId;
  }

  /**
   * Crée des particules pour un effet
   */
  public createParticles(
    x: number,
    y: number,
    count: number,
    type: Particle['type'] = 'generic',
    color: string = '#FFFFFF',
    size: number = 2
  ): void {
    if (!this.config.enableParticles) return;
    
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 50 + Math.random() * 100;
      const life = 0.5 + Math.random() * 1.5;
      
      const particle: Particle = {
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life,
        maxLife: life,
        color,
        size: size * (0.5 + Math.random()),
        type
      };
      
      this.particles.push(particle);
      
      // Notifier la création
      this.onParticleCreatedCallbacks.forEach(callback => {
        try {
          callback(particle);
        } catch (error) {
          console.error('AnimationEngine: Erreur dans le callback onParticleCreated', error);
        }
      });
    }
  }

  /**
   * Déclenche un tremblement d'écran
   */
  public triggerScreenShake(intensity: number = 10, decay: number = 0.9): void {
    if (!this.config.enableScreenShake) return;
    
    this.screenShakeEffect.intensity = intensity;
    this.screenShakeEffect.decay = decay;
  }

  /**
   * Ajoute une traînée
   */
  public addTrail(x: number, y: number): void {
    if (!this.config.enableTrails) return;
    
    this.trails.push({ x, y, alpha: 1.0 });
    
    // Limiter la longueur des traînées
    if (this.trails.length > this.config.trailLength) {
      this.trails.shift();
    }
  }

  /**
   * Met à jour les traînées
   */
  public updateTrails(): void {
    for (let i = 0; i < this.trails.length; i++) {
      this.trails[i].alpha -= 0.1;
    }
    
    // Supprimer les traînées transparentes
    this.trails = this.trails.filter(trail => trail.alpha > 0);
  }

  /**
   * Fonctions d'easing prédéfinies
   */
  public easeLinear(t: number): number {
    return t;
  }

  public easeInQuad(t: number): number {
    return t * t;
  }

  public easeOutQuad(t: number): number {
    return t * (2 - t);
  }

  public easeInOutQuad(t: number): number {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
  }

  public easeInCubic(t: number): number {
    return t * t * t;
  }

  public easeOutCubic(t: number): number {
    return (--t) * t * t + 1;
  }

  public easeInOutCubic(t: number): number {
    return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
  }

  public easeInSine(t: number): number {
    return 1 - Math.cos((t * Math.PI) / 2);
  }

  public easeOutSine(t: number): number {
    return Math.sin((t * Math.PI) / 2);
  }

  /**
   * Anime Pac-Man (bouche qui s'ouvre et se ferme)
   */
  public animatePacman(pacman: GameState['pacman'], frame: number): { angle: number; rotation: number } {
    // Animation de la bouche (0 à 1)
    const mouthOpen = 0.3 + 0.3 * Math.sin(frame * 0.2);
    const angle = mouthOpen * Math.PI * 0.5;
    
    // Rotation selon la direction
    let rotation = 0;
    switch (pacman.direction) {
      case 'right': rotation = 0; break;
      case 'left': rotation = Math.PI; break;
      case 'up': rotation = -Math.PI / 2; break;
      case 'down': rotation = Math.PI / 2; break;
    }
    
    return { angle, rotation };
  }

  /**
   * Anime les fantômes (ondulation, yeux)
   */
  public animateGhost(_ghost: GameState['ghosts'][0], frame: number): { waveAmplitude: number; eyeOffset: number } {
    // Ondulation du bas du fantôme
    const waveAmplitude = 2 + 2 * Math.sin(frame * 0.3);
    
    // Animation des yeux (suivi de direction)
    const eyeOffset = Math.sin(frame * 0.5) * 0.5;
    
    return { waveAmplitude, eyeOffset };
  }

  /**
   * Anime les pac-gommes (scintillement)
   */
  public animatePellet(frame: number): { alpha: number; scale: number } {
    const alpha = 0.7 + 0.3 * Math.sin(frame * 0.5);
    const scale = 0.8 + 0.2 * Math.sin(frame * 0.3);
    return { alpha, scale };
  }

  /**
   * Anime les super pac-gommes (pulsation)
   */
  public animatePowerPellet(frame: number): { scale: number; glow: number } {
    const scale = 0.7 + 0.3 * Math.sin(frame * 0.2);
    const glow = 0.5 + 0.5 * Math.sin(frame * 0.4);
    return { scale, glow };
  }

  /**
   * Met à jour le moteur d'animation (pour compatibilité avec GameVisualizer)
   */
  public update(deltaTime: number): void {
    // Mettre à jour les animations
    this.updateAnimations(deltaTime);
    
    // Mettre à jour les particules
    this.updateParticles(deltaTime);
    
    // Mettre à jour les effets d'écran
    this.updateScreenEffects(deltaTime);
  }

  /**
   * Applique les effets d'écran (pour compatibilité avec GameVisualizer)
   */
  public applyScreenEffects(): void {
    // Dans une implémentation complète, appliquer les effets au renderer
    // Pour l'instant, on ne fait rien
  }

  /**
   * Réinitialise le moteur d'animation (pour compatibilité avec GameVisualizer)
   */
  public reset(): void {
    this.stop();
    this.particles = [];
    this.activeAnimations = [];
    this.trails = [];
    this.screenShakeEffect = { x: 0, y: 0, intensity: 0, decay: 0.9 };
  }

  /**
   * Getters
   */
  public getParticles(): Particle[] {
    return [...this.particles];
  }

  public getActiveAnimations(): Animation[] {
    return [...this.activeAnimations];
  }

  public getScreenShake(): { x: number; y: number } {
    return { x: this.screenShakeEffect.x, y: this.screenShakeEffect.y };
  }

  public getTrails(): Array<{ x: number; y: number; alpha: number }> {
    return [...this.trails];
  }

  public isAnimating(): boolean {
    return this.activeAnimations.length > 0;
  }

  /**
   * Méthodes d'enregistrement des callbacks
   */
  public onFrame(callback: (deltaTime: number) => void): void {
    this.onFrameCallbacks.push(callback);
  }

  public onParticleCreated(callback: (particle: Particle) => void): void {
    this.onParticleCreatedCallbacks.push(callback);
  }

  public onAnimationComplete(callback: (animationId: string) => void): void {
    this.onAnimationCompleteCallbacks.push(callback);
  }

  /**
   * Nettoyage
   */
  public dispose(): void {
    this.stop();
    this.particles = [];
    this.activeAnimations = [];
    this.trails = [];
    this.onFrameCallbacks = [];
    this.onParticleCreatedCallbacks = [];
    this.onAnimationCompleteCallbacks = [];
  }
}
