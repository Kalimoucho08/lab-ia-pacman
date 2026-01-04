/**
 * Composant principal de visualisation Pac-Man
 *
 * Intègre tous les sous-systèmes :
 * - CanvasRenderer : rendu optimisé Canvas HTML5
 * - WebSocketClient : communication temps réel avec backend
 * - GameStateManager : gestion et interpolation des états
 * - AnimationEngine : animations fluides 60 FPS
 * - ControlsPanel : contrôles interactifs
 * - InfoOverlay : overlay d'informations
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Box, Paper, Typography, Alert, CircularProgress } from '@mui/material';

// Import des sous-systèmes
import { CanvasRenderer } from './CanvasRenderer';
import { WebSocketClient } from './WebSocketClient';
import { GameStateManager } from './GameStateManager';
import { AnimationEngine } from './AnimationEngine';
import ControlsPanel from './ControlsPanel';
import InfoOverlay from './InfoOverlay';

// Types
import { GameState, RenderConfig } from '../../types/pacman';

// Configuration par défaut
const DEFAULT_CONFIG: RenderConfig = {
  cellSize: 24,
  zoom: 1.5,
  showGrid: true,
  showPaths: false,
  showHeatmap: false,
  showAgentLabels: true,
  showStats: true,
  animationSpeed: 1.0,
  backgroundColor: '#000000',
  gridColor: 'rgba(255, 255, 255, 0.1)',
  pelletColor: '#FFFFFF',
  powerPelletColor: '#FFFF00',
  pacmanColor: '#FFFF00',
  ghostColors: ['#FF0000', '#FF88FF', '#00FFFF', '#FFAA00'],
};

const GameVisualizer: React.FC = () => {
  // Références aux sous-systèmes
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rendererRef = useRef<CanvasRenderer | null>(null);
  const wsClientRef = useRef<WebSocketClient | null>(null);
  const stateManagerRef = useRef<GameStateManager | null>(null);
  const animationEngineRef = useRef<AnimationEngine | null>(null);
  
  // États
  const [isConnected, setIsConnected] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [renderConfig, setRenderConfig] = useState<RenderConfig>(DEFAULT_CONFIG);
  const [performanceStats, setPerformanceStats] = useState({
    fps: 0,
    latency: 0,
    memoryUsage: 0,
    bufferSize: 0,
    lastUpdate: Date.now(),
  });
  
  // Initialisation des sous-systèmes
  useEffect(() => {
    if (!canvasRef.current) return;
    
    // Initialiser le moteur de rendu
    const canvas = canvasRef.current;
    const renderer = new CanvasRenderer(canvas, renderConfig);
    rendererRef.current = renderer;
    
    // Initialiser le gestionnaire d'état
    const stateManager = new GameStateManager();
    stateManagerRef.current = stateManager;
    
    // Initialiser le moteur d'animations
    const animationEngine = new AnimationEngine();
    animationEngine.setRenderer(renderer);
    animationEngineRef.current = animationEngine;
    
    // Initialiser le client WebSocket
    const wsClient = new WebSocketClient({
      url: 'ws://localhost:8000/ws/game_state',
    });
    wsClientRef.current = wsClient;
    
    // Enregistrer les callbacks
    wsClient.onGameState((gameState: GameState) => {
      stateManager.addState(gameState);
    });
    
    wsClient.onConnect(() => {
      setIsConnected(true);
      console.log('WebSocket connecté');
    });
    
    wsClient.onDisconnect(() => {
      setIsConnected(false);
      console.log('WebSocket déconnecté');
    });
    
    wsClient.onError((error: string) => {
      console.error('Erreur WebSocket:', error);
    });
    
    // Gérer les autres types de messages
    // Note: WebSocketClient n'a pas de callback générique onMessage,
    // donc pour performance_stats, il faudrait soit l'ajouter soit utiliser un autre mécanisme
    // Pour l'instant, on ignore performance_stats
    
    // Démarrer la boucle de rendu
    let animationFrameId: number;
    let lastTime = 0;
    
    const renderLoop = (timestamp: number) => {
      const deltaTime = timestamp - lastTime;
      lastTime = timestamp;
      
      // Calculer le FPS
      const fps = deltaTime > 0 ? 1000 / deltaTime : 0;
      
      // Mettre à jour les statistiques de performance
      setPerformanceStats(prev => ({
        ...prev,
        fps: Math.round(fps),
        lastUpdate: timestamp,
      }));
      
      // Obtenir l'état actuel interpolé
      const currentState = stateManager.getCurrentState();
      if (currentState) {
        setGameState(currentState);
        
        // Mettre à jour le moteur d'animations
        if (animationEngineRef.current) {
          animationEngineRef.current.update(deltaTime);
        }
        
        // Rendu
        if (rendererRef.current) {
          rendererRef.current.render(currentState, renderConfig);
          
          // Appliquer les effets d'écran
          if (animationEngineRef.current) {
            animationEngineRef.current.applyScreenEffects();
          }
        }
      }
      
      animationFrameId = requestAnimationFrame(renderLoop);
    };
    
    animationFrameId = requestAnimationFrame(renderLoop);
    
    // Nettoyage
    return () => {
      cancelAnimationFrame(animationFrameId);
      wsClient.disconnect();
      renderer.cleanup();
    };
  }, []);
  
  // Gestion de la lecture/pause
  useEffect(() => {
    if (stateManagerRef.current) {
      stateManagerRef.current.setPaused(!isPlaying);
    }
  }, [isPlaying]);
  
  // Mise à jour de la configuration de rendu
  useEffect(() => {
    if (rendererRef.current) {
      rendererRef.current.updateConfig(renderConfig);
    }
  }, [renderConfig]);
  
  // Gestionnaires d'événements
  const handlePlayPause = useCallback(() => {
    setIsPlaying(prev => !prev);
  }, []);
  
  const handleStepForward = useCallback(() => {
    if (stateManagerRef.current) {
      stateManagerRef.current.stepForward();
    }
  }, []);
  
  const handleStepBackward = useCallback(() => {
    if (stateManagerRef.current) {
      stateManagerRef.current.stepBackward();
    }
  }, []);
  
  const handleReset = useCallback(() => {
    setIsPlaying(false);
    if (stateManagerRef.current) {
      stateManagerRef.current.reset();
    }
    if (animationEngineRef.current) {
      animationEngineRef.current.reset();
    }
  }, []);
  
  const handleZoomIn = useCallback(() => {
    setRenderConfig(prev => ({
      ...prev,
      zoom: Math.min(3.0, prev.zoom + 0.25),
    }));
  }, []);
  
  const handleZoomOut = useCallback(() => {
    setRenderConfig(prev => ({
      ...prev,
      zoom: Math.max(0.5, prev.zoom - 0.25),
    }));
  }, []);
  
  const handleSpeedChange = useCallback((speed: number) => {
    setRenderConfig(prev => ({
      ...prev,
      animationSpeed: speed,
    }));
    if (stateManagerRef.current) {
      stateManagerRef.current.setSpeed(speed);
    }
  }, []);
  
  const handleToggleGrid = useCallback(() => {
    setRenderConfig(prev => ({
      ...prev,
      showGrid: !prev.showGrid,
    }));
  }, []);
  
  const handleTogglePaths = useCallback(() => {
    setRenderConfig(prev => ({
      ...prev,
      showPaths: !prev.showPaths,
    }));
  }, []);
  
  const handleToggleHeatmap = useCallback(() => {
    setRenderConfig(prev => ({
      ...prev,
      showHeatmap: !prev.showHeatmap,
    }));
  }, []);
  
  const handleToggleAgentLabels = useCallback(() => {
    setRenderConfig(prev => ({
      ...prev,
      showAgentLabels: !prev.showAgentLabels,
    }));
  }, []);
  
  const handleToggleStats = useCallback(() => {
    setRenderConfig(prev => ({
      ...prev,
      showStats: !prev.showStats,
    }));
  }, []);
  
  const handleExportImage = useCallback(() => {
    if (rendererRef.current && canvasRef.current) {
      const dataUrl = canvasRef.current.toDataURL('image/png');
      const link = document.createElement('a');
      link.download = `pacman_${Date.now()}.png`;
      link.href = dataUrl;
      link.click();
    }
  }, []);
  
  const handleExportVideo = useCallback(() => {
    // Implémentation simplifiée - utiliser MediaRecorder API
    alert('Export vidéo - fonctionnalité avancée à implémenter');
  }, []);
  
  // Calculer la taille du canvas
  const canvasWidth = 800;
  const canvasHeight = 600;
  
  return (
    <Box sx={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* Indicateur de connexion */}
      {!isConnected && (
        <Alert 
          severity="warning" 
          sx={{ 
            position: 'absolute', 
            top: 16, 
            left: '50%', 
            transform: 'translateX(-50%)',
            zIndex: 1100,
            width: 'auto',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CircularProgress size={16} sx={{ mr: 1 }} />
            Connexion au serveur en cours...
          </Box>
        </Alert>
      )}
      
      {/* Canvas de jeu */}
      <Paper 
        sx={{ 
          p: 2, 
          mb: 2, 
          display: 'flex', 
          justifyContent: 'center',
          alignItems: 'center',
          bgcolor: 'black',
          position: 'relative',
          overflow: 'hidden',
          minHeight: canvasHeight + 40,
        }}
      >
        <canvas
          ref={canvasRef}
          width={canvasWidth}
          height={canvasHeight}
          className="game-canvas"
          style={{
            borderRadius: '8px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
            backgroundColor: '#000',
          }}
        />
        
        {/* Overlay d'informations */}
        {gameState && (
          <InfoOverlay
            gameState={gameState}
            showStats={renderConfig.showStats}
            showPaths={renderConfig.showPaths}
            showHeatmap={renderConfig.showHeatmap}
            showAgentLabels={renderConfig.showAgentLabels}
            fps={performanceStats.fps}
            latency={performanceStats.latency}
            memoryUsage={performanceStats.memoryUsage}
            bufferSize={performanceStats.bufferSize}
            onToggleStats={handleToggleStats}
            onTogglePaths={handleTogglePaths}
            onToggleHeatmap={handleToggleHeatmap}
            onToggleAgentLabels={handleToggleAgentLabels}
          />
        )}
      </Paper>
      
      {/* Panneau de contrôles */}
      <ControlsPanel
        isPlaying={isPlaying}
        isConnected={isConnected}
        zoom={renderConfig.zoom}
        speed={renderConfig.animationSpeed}
        showGrid={renderConfig.showGrid}
        showPaths={renderConfig.showPaths}
        showHeatmap={renderConfig.showHeatmap}
        showAgentLabels={renderConfig.showAgentLabels}
        showStats={renderConfig.showStats}
        onPlayPause={handlePlayPause}
        onStepForward={handleStepForward}
        onStepBackward={handleStepBackward}
        onReset={handleReset}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onSpeedChange={handleSpeedChange}
        onToggleGrid={handleToggleGrid}
        onTogglePaths={handleTogglePaths}
        onToggleHeatmap={handleToggleHeatmap}
        onToggleAgentLabels={handleToggleAgentLabels}
        onToggleStats={handleToggleStats}
        onExportImage={handleExportImage}
        onExportVideo={handleExportVideo}
        performanceStats={performanceStats}
      />
      
      {/* Informations de débogage (optionnel) */}
      {import.meta.env.DEV && (
        <Paper sx={{ p: 2, mt: 2, bgcolor: 'grey.900' }}>
          <Typography variant="caption" color="text.secondary">
            Débogage: {gameState ? `Étape ${gameState.step}` : 'Aucun état'} •
            FPS: {performanceStats.fps} •
            Buffer: {performanceStats.bufferSize} •
            Latence: {performanceStats.latency}ms
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default GameVisualizer;