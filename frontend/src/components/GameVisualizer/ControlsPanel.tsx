/**
 * Panneau de contrôles interactifs pour la visualisation Pac-Man
 * 
 * Fonctionnalités :
 * - Contrôles de zoom (in/out, reset)
 * - Réglage de la vitesse de simulation (0.5x à 10x)
 * - Affichage/masquage d'éléments (grille, stats, chemins)
 * - Mode pas à pas
 * - Export d'images/vidéos
 * - Réinitialisation de la visualisation
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Slider,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Stack,
  Chip,
  Divider,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  ZoomOutMap as ZoomResetIcon,
  PlayArrow as PlayArrowIcon,
  Pause as PauseIcon,
  SkipNext as SkipNextIcon,
  SkipPrevious as SkipPreviousIcon,
  RestartAlt as RestartAltIcon,
  Speed as SpeedIcon,
  GridOn as GridOnIcon,
  GridOff as GridOffIcon,
  Info as InfoIcon,
  Timeline as TimelineIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';

export interface ControlsPanelProps {
  // État
  isPlaying: boolean;
  isConnected?: boolean; // Connexion WebSocket
  speed: number; // 0.5 à 10
  zoom: number; // 0.5 à 3
  showGrid: boolean;
  showStats: boolean;
  showPaths: boolean;
  showHeatmap: boolean;
  showAgentLabels?: boolean;
  currentStep?: number;
  totalSteps?: number;
  
  // Callbacks
  onPlayPause: (playing: boolean) => void;
  onSpeedChange: (speed: number) => void;
  onZoomChange?: (zoom: number) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onZoomReset?: () => void;
  onToggleGrid: (show: boolean) => void;
  onToggleStats: (show: boolean) => void;
  onTogglePaths: (show: boolean) => void;
  onToggleHeatmap: (show: boolean) => void;
  onToggleAgentLabels?: (show: boolean) => void;
  onStepForward: () => void;
  onStepBackward: () => void;
  onReset: () => void;
  onExportImage?: () => void;
  onExportVideo?: () => void;
  onSettingsOpen?: () => void;
  
  // Options supplémentaires
  enableExport?: boolean;
  enableStepMode?: boolean;
  enableSpeedControl?: boolean;
  enableZoomControl?: boolean;
  enableDisplayControls?: boolean;
  
  // Statistiques de performance
  performanceStats?: {
    fps: number;
    latency: number;
    memoryUsage: number;
    bufferSize: number;
    lastUpdate: number;
  };
}

const ControlsPanel: React.FC<ControlsPanelProps> = ({
  // État
  isPlaying,
  speed,
  zoom,
  showGrid,
  showStats,
  showPaths,
  showHeatmap,
  currentStep,
  totalSteps,
  
  // Callbacks
  onPlayPause,
  onSpeedChange,
  onZoomChange,
  onZoomIn,
  onZoomOut,
  onZoomReset,
  onToggleGrid,
  onToggleStats,
  onTogglePaths,
  onToggleHeatmap,
  onStepForward,
  onStepBackward,
  onReset,
  onExportImage,
  onExportVideo,
  onSettingsOpen,
  
  // Options
  enableExport = true,
  enableStepMode = true,
  enableSpeedControl = true,
  enableZoomControl = true,
  enableDisplayControls = true,
}) => {
  const [speedAnchorEl, setSpeedAnchorEl] = useState<null | HTMLElement>(null);
  const [displayAnchorEl, setDisplayAnchorEl] = useState<null | HTMLElement>(null);
  const [exportAnchorEl, setExportAnchorEl] = useState<null | HTMLElement>(null);
  
  const speedOpen = Boolean(speedAnchorEl);
  const displayOpen = Boolean(displayAnchorEl);
  const exportOpen = Boolean(exportAnchorEl);
  
  // Pré-définir les vitesses
  const speedPresets = [
    { label: '0.5x', value: 0.5 },
    { label: '1x', value: 1 },
    { label: '2x', value: 2 },
    { label: '5x', value: 5 },
    { label: '10x', value: 10 },
  ];
  
  // Gestion des menus
  const handleSpeedClick = (event: React.MouseEvent<HTMLElement>) => {
    setSpeedAnchorEl(event.currentTarget);
  };
  
  const handleDisplayClick = (event: React.MouseEvent<HTMLElement>) => {
    setDisplayAnchorEl(event.currentTarget);
  };
  
  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportAnchorEl(event.currentTarget);
  };
  
  const handleClose = () => {
    setSpeedAnchorEl(null);
    setDisplayAnchorEl(null);
    setExportAnchorEl(null);
  };
  
  // Gestion des presets de vitesse
  const handleSpeedPreset = (presetSpeed: number) => {
    onSpeedChange(presetSpeed);
    handleClose();
  };
  
  // Gestion de l'export
  const handleExportImage = () => {
    if (onExportImage) onExportImage();
    handleClose();
  };
  
  const handleExportVideo = () => {
    if (onExportVideo) onExportVideo();
    handleClose();
  };
  
  // Formatage de la vitesse
  const formatSpeed = (value: number) => {
    return `${value.toFixed(1)}x`;
  };
  
  // Formatage du zoom
  const formatZoom = (value: number) => {
    return `${value.toFixed(1)}x`;
  };
  
  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      {/* En-tête */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" component="h2">
          Contrôles de visualisation
        </Typography>
        
        <Stack direction="row" spacing={1}>
          {/* Indicateur d'état */}
          <Chip
            label={isPlaying ? 'En cours' : 'En pause'}
            color={isPlaying ? 'success' : 'warning'}
            size="small"
            variant="outlined"
          />
          
          {/* Indicateur d'étape */}
          {totalSteps && (
            <Chip
              label={`Étape: ${currentStep} / ${totalSteps}`}
              color="info"
              size="small"
              variant="outlined"
            />
          )}
        </Stack>
      </Box>
      
      <Divider sx={{ mb: 2 }} />
      
      {/* Contrôles principaux */}
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
        {/* Contrôles de lecture */}
        <Stack direction="row" spacing={1}>
          <Tooltip title="Étape précédente">
            <IconButton onClick={onStepBackward} disabled={!enableStepMode}>
              <SkipPreviousIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title={isPlaying ? 'Pause' : 'Lecture'}>
            <IconButton
              color={isPlaying ? 'warning' : 'success'}
              onClick={() => onPlayPause(!isPlaying)}
              sx={{ width: 56, height: 56 }}
            >
              {isPlaying ? <PauseIcon /> : <PlayArrowIcon />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Étape suivante">
            <IconButton onClick={onStepForward} disabled={!enableStepMode}>
              <SkipNextIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Réinitialiser">
            <IconButton onClick={onReset}>
              <RestartAltIcon />
            </IconButton>
          </Tooltip>
        </Stack>
        
        <Divider orientation="vertical" flexItem />
        
        {/* Contrôles de vitesse */}
        {enableSpeedControl && (
          <>
            <Tooltip title="Vitesse de simulation">
              <IconButton onClick={handleSpeedClick}>
                <SpeedIcon />
              </IconButton>
            </Tooltip>
            
            <Box sx={{ minWidth: 120 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Vitesse: {formatSpeed(speed)}
              </Typography>
              <Slider
                value={speed}
                onChange={(_, value) => onSpeedChange(value as number)}
                min={0.1}
                max={10}
                step={0.1}
                valueLabelDisplay="auto"
                valueLabelFormat={formatSpeed}
                size="small"
              />
            </Box>
            
            <Menu
              anchorEl={speedAnchorEl}
              open={speedOpen}
              onClose={handleClose}
            >
              <Typography variant="subtitle2" sx={{ px: 2, py: 1 }}>
                Vitesses prédéfinies
              </Typography>
              {speedPresets.map((preset) => (
                <MenuItem
                  key={preset.value}
                  onClick={() => handleSpeedPreset(preset.value)}
                  selected={Math.abs(speed - preset.value) < 0.1}
                >
                  <ListItemIcon>
                    <SpeedIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={preset.label} />
                </MenuItem>
              ))}
            </Menu>
          </>
        )}
        
        <Divider orientation="vertical" flexItem />
        
        {/* Contrôles de zoom */}
        {enableZoomControl && (
          <>
            <Stack direction="row" spacing={1}>
              <Tooltip title="Zoom avant">
                <IconButton onClick={onZoomIn}>
                  <ZoomInIcon />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Zoom arrière">
                <IconButton onClick={onZoomOut}>
                  <ZoomOutIcon />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Réinitialiser le zoom">
                <IconButton onClick={onZoomReset}>
                  <ZoomResetIcon />
                </IconButton>
              </Tooltip>
            </Stack>
            
            <Box sx={{ minWidth: 100 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Zoom: {formatZoom(zoom)}
              </Typography>
              <Slider
                value={zoom}
                onChange={(_, value) => onZoomChange?.(value as number)}
                min={0.5}
                max={3}
                step={0.1}
                valueLabelDisplay="auto"
                valueLabelFormat={formatZoom}
                size="small"
              />
            </Box>
          </>
        )}
      </Stack>
      
      {/* Contrôles d'affichage */}
      {enableDisplayControls && (
        <>
          <Divider sx={{ mb: 2 }} />
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Affichage
            </Typography>
            
            <Stack direction="row" spacing={2} alignItems="center">
              <Tooltip title="Paramètres d'affichage">
                <IconButton onClick={handleDisplayClick}>
                  <VisibilityIcon />
                </IconButton>
              </Tooltip>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={showGrid}
                    onChange={(e) => onToggleGrid(e.target.checked)}
                    size="small"
                  />
                }
                label="Grille"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={showStats}
                    onChange={(e) => onToggleStats(e.target.checked)}
                    size="small"
                  />
                }
                label="Statistiques"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={showPaths}
                    onChange={(e) => onTogglePaths(e.target.checked)}
                    size="small"
                  />
                }
                label="Chemins"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={showHeatmap}
                    onChange={(e) => onToggleHeatmap(e.target.checked)}
                    size="small"
                  />
                }
                label="Heatmap"
              />
            </Stack>
            
            <Menu
              anchorEl={displayAnchorEl}
              open={displayOpen}
              onClose={handleClose}
            >
              <Typography variant="subtitle2" sx={{ px: 2, py: 1 }}>
                Affichage des éléments
              </Typography>
              <MenuItem onClick={() => onToggleGrid(!showGrid)}>
                <ListItemIcon>
                  {showGrid ? <GridOnIcon fontSize="small" /> : <GridOffIcon fontSize="small" />}
                </ListItemIcon>
                <ListItemText primary="Grille" />
              </MenuItem>
              <MenuItem onClick={() => onToggleStats(!showStats)}>
                <ListItemIcon>
                  {showStats ? <InfoIcon fontSize="small" /> : <VisibilityOffIcon fontSize="small" />}
                </ListItemIcon>
                <ListItemText primary="Statistiques" />
              </MenuItem>
              <MenuItem onClick={() => onTogglePaths(!showPaths)}>
                <ListItemIcon>
                  <TimelineIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText primary="Chemins des agents" />
              </MenuItem>
              <MenuItem onClick={() => onToggleHeatmap(!showHeatmap)}>
                <ListItemIcon>
                  <TimelineIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText primary="Heatmap des positions" />
              </MenuItem>
            </Menu>
          </Box>
        </>
      )}
      
      {/* Contrôles d'export et paramètres avancés */}
      <Divider sx={{ mb: 2 }} />
      
      <Stack direction="row" spacing={2} justifyContent="space-between">
        <Stack direction="row" spacing={1}>
          {/* Export */}
          {enableExport && (
            <>
              <Tooltip title="Exporter">
                <IconButton onClick={handleExportClick}>
                  <DownloadIcon />
                </IconButton>
              </Tooltip>
              
              <Menu
                anchorEl={exportAnchorEl}
                open={exportOpen}
                onClose={handleClose}
              >
                <Typography variant="subtitle2" sx={{ px: 2, py: 1 }}>
                  Exporter la visualisation
                </Typography>
                <MenuItem onClick={handleExportImage}>
                  <ListItemIcon>
                    <DownloadIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Image (PNG)" />
                </MenuItem>
                <MenuItem onClick={handleExportVideo} disabled={!onExportVideo}>
                  <ListItemIcon>
                    <DownloadIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Vidéo (MP4)" />
                </MenuItem>
              </Menu>
            </>
          )}
          
          {/* Paramètres avancés */}
          {onSettingsOpen && (
            <Tooltip title="Paramètres avancés">
              <IconButton onClick={onSettingsOpen}>
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          )}
        </Stack>
        
        {/* Indicateurs rapides */}
        <Stack direction="row" spacing={1}>
          <Chip
            icon={<GridOnIcon />}
            label="Grille"
            size="small"
            color={showGrid ? 'primary' : 'default'}
            variant={showGrid ? 'filled' : 'outlined'}
            onClick={() => onToggleGrid(!showGrid)}
          />
          <Chip
            icon={<InfoIcon />}
            label="Stats"
            size="small"
            color={showStats ? 'primary' : 'default'}
            variant={showStats ? 'filled' : 'outlined'}
            onClick={() => onToggleStats(!showStats)}
          />
          <Chip
            icon={<TimelineIcon />}
            label="Chemins"
            size="small"
            color={showPaths ? 'primary' : 'default'}
            variant={showPaths ? 'filled' : 'outlined'}
            onClick={() => onTogglePaths(!showPaths)}
          />
        </Stack>
      </Stack>
      
      {/* Informations supplémentaires */}
      <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Typography variant="caption" color="text.secondary">
          Utilisez la molette de la souris pour zoomer, cliquez-glissez pour déplacer la vue.
          Espace pour play/pause, flèches pour naviguer.
        </Typography>
      </Box>
    </Paper>
  );
};

export default ControlsPanel;