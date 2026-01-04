/**
 * Overlay d'informations pour la visualisation Pac-Man
 * 
 * Fonctionnalités :
 * - Affichage des scores, vies, temps restant
 * - Positions des agents avec labels
 * - Chemins prévus des fantômes
 * - Heatmap des positions fréquentes
 * - Statistiques de performance
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Stack,
  Tooltip,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  Info as InfoIcon,
  LocationOn as LocationIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';

import { GameState } from '../../types/pacman';

export interface InfoOverlayProps {
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

const InfoOverlay: React.FC<InfoOverlayProps> = ({
  gameState,
  showStats,
  showPaths,
  showHeatmap,
  showAgentLabels,
  fps,
  latency,
  memoryUsage,
  bufferSize,
  onToggleStats,
  onTogglePaths,
  onToggleHeatmap,
  onToggleAgentLabels,
}) => {
  const [expanded, setExpanded] = React.useState(true);
  
  if (!gameState) {
    return (
      <Paper
        sx={{
          position: 'absolute',
          top: 16,
          left: 16,
          p: 2,
          bgcolor: 'background.paper',
          opacity: 0.9,
          zIndex: 1000,
        }}
      >
        <Typography variant="body2" color="text.secondary">
          En attente de données...
        </Typography>
      </Paper>
    );
  }
  
  const { pacman, ghosts, score, lives, step } = gameState;
  
  // Calculer des statistiques dérivées
  const remainingPellets = gameState.pellets.length;
  const remainingPowerPellets = gameState.powerPellets.length;
  const activeGhosts = ghosts.filter(g => g.mode !== 'eaten').length;
  
  return (
    <>
      {/* Overlay principal (coin supérieur gauche) */}
      <Paper
        sx={{
          position: 'absolute',
          top: 16,
          left: 16,
          p: 2,
          bgcolor: 'background.paper',
          opacity: 0.9,
          zIndex: 1000,
          maxWidth: 300,
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h6" component="h3">
            État du jeu
          </Typography>
          <IconButton size="small" onClick={() => setExpanded(!expanded)}>
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>
        
        <Collapse in={expanded}>
          {/* Informations essentielles */}
          <Stack spacing={1} sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Score:
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {score}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Vies:
              </Typography>
              <Typography variant="body2" fontWeight="bold" color={lives > 1 ? 'success.main' : 'error.main'}>
                {lives} {lives === 1 ? '❤️' : '❤️'.repeat(Math.min(lives, 3))}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Étape:
              </Typography>
              <Typography variant="body2">
                {step}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Pac-gommes:
              </Typography>
              <Typography variant="body2">
                {remainingPellets} ({remainingPowerPellets} super)
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Fantômes actifs:
              </Typography>
              <Typography variant="body2">
                {activeGhosts} / {ghosts.length}
              </Typography>
            </Box>
          </Stack>
          
          {/* Position de Pac-Man */}
          <Paper variant="outlined" sx={{ p: 1, mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <LocationIcon fontSize="small" sx={{ mr: 1 }} />
              Pac-Man
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              <Chip
                label={`(${pacman.x}, ${pacman.y})`}
                size="small"
                color="warning"
                variant="outlined"
              />
              <Chip
                label={pacman.direction}
                size="small"
                color="info"
                variant="outlined"
              />
            </Stack>
          </Paper>
          
          {/* Positions des fantômes */}
          <Paper variant="outlined" sx={{ p: 1, mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <LocationIcon fontSize="small" sx={{ mr: 1 }} />
              Fantômes
            </Typography>
            <Stack spacing={0.5}>
              {ghosts.map((ghost, index) => (
                <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Chip
                    label={`Fantôme ${index + 1}`}
                    size="small"
                    sx={{ bgcolor: ghost.color, color: 'white', mr: 1 }}
                  />
                  <Typography variant="caption">
                    ({ghost.x}, {ghost.y}) • {ghost.mode}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Paper>
          
          {/* Statistiques de performance */}
          {(fps !== undefined || latency !== undefined || memoryUsage !== undefined) && (
            <Paper variant="outlined" sx={{ p: 1 }}>
              <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <SpeedIcon fontSize="small" sx={{ mr: 1 }} />
                Performance
              </Typography>
              <Stack spacing={0.5}>
                {fps !== undefined && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      FPS:
                    </Typography>
                    <Typography variant="caption" color={fps >= 50 ? 'success.main' : fps >= 30 ? 'warning.main' : 'error.main'}>
                      {fps.toFixed(0)}
                    </Typography>
                  </Box>
                )}
                
                {latency !== undefined && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Latence:
                    </Typography>
                    <Typography variant="caption" color={latency < 50 ? 'success.main' : latency < 100 ? 'warning.main' : 'error.main'}>
                      {latency.toFixed(0)} ms
                    </Typography>
                  </Box>
                )}
                
                {memoryUsage !== undefined && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Mémoire:
                    </Typography>
                    <Typography variant="caption">
                      {memoryUsage.toFixed(1)} MB
                    </Typography>
                  </Box>
                )}
                
                {bufferSize !== undefined && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Buffer:
                    </Typography>
                    <Typography variant="caption" color={bufferSize > 5 ? 'success.main' : bufferSize > 2 ? 'warning.main' : 'error.main'}>
                      {bufferSize} états
                    </Typography>
                  </Box>
                )}
              </Stack>
            </Paper>
          )}
        </Collapse>
      </Paper>
      
      {/* Contrôles d'affichage (coin supérieur droit) */}
      <Paper
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          p: 1,
          bgcolor: 'background.paper',
          opacity: 0.9,
          zIndex: 1000,
        }}
      >
        <Stack direction="row" spacing={0.5}>
          <Tooltip title="Statistiques">
            <IconButton
              size="small"
              color={showStats ? 'primary' : 'default'}
              onClick={onToggleStats}
            >
              <InfoIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Chemins">
            <IconButton
              size="small"
              color={showPaths ? 'primary' : 'default'}
              onClick={onTogglePaths}
            >
              <TimelineIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Heatmap">
            <IconButton
              size="small"
              color={showHeatmap ? 'primary' : 'default'}
              onClick={onToggleHeatmap}
            >
              <MemoryIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Labels agents">
            <IconButton
              size="small"
              color={showAgentLabels ? 'primary' : 'default'}
              onClick={onToggleAgentLabels}
            >
              <LocationIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Stack>
      </Paper>
      
      {/* Indicateurs en bas à gauche */}
      <Paper
        sx={{
          position: 'absolute',
          bottom: 16,
          left: 16,
          p: 1,
          bgcolor: 'background.paper',
          opacity: 0.9,
          zIndex: 1000,
        }}
      >
        <Stack direction="row" spacing={1}>
          <Chip
            label={`Score: ${score}`}
            size="small"
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`Vies: ${lives}`}
            size="small"
            color={lives > 1 ? 'success' : 'error'}
            variant="outlined"
          />
          <Chip
            label={`Étape: ${step}`}
            size="small"
            color="info"
            variant="outlined"
          />
        </Stack>
      </Paper>
      
      {/* Légende des fantômes (en bas à droite) */}
      <Paper
        sx={{
          position: 'absolute',
          bottom: 16,
          right: 16,
          p: 1,
          bgcolor: 'background.paper',
          opacity: 0.9,
          zIndex: 1000,
          maxWidth: 200,
        }}
      >
        <Typography variant="caption" color="text.secondary" gutterBottom>
          Légende fantômes
        </Typography>
        <Stack spacing={0.5}>
          {ghosts.slice(0, 4).map((ghost, index) => (
            <Box key={index} sx={{ display: 'flex', alignItems: 'center' }}>
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  bgcolor: ghost.color,
                  mr: 1,
                }}
              />
              <Typography variant="caption">
                Fantôme {index + 1}: {ghost.mode}
              </Typography>
            </Box>
          ))}
        </Stack>
      </Paper>
    </>
  );
};

export default InfoOverlay;