import React from 'react'
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Stack,
  IconButton,
  Tooltip,
} from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import PauseIcon from '@mui/icons-material/Pause'
import StopIcon from '@mui/icons-material/Stop'
import RefreshIcon from '@mui/icons-material/Refresh'
import SaveIcon from '@mui/icons-material/Save'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import SpeedIcon from '@mui/icons-material/Speed'
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents'
import PsychologyIcon from '@mui/icons-material/Psychology'

const Dashboard: React.FC = () => {
  const [isTraining, setIsTraining] = React.useState(false)
  const [isGhostTraining, setIsGhostTraining] = React.useState(false)
  const [progress, setProgress] = React.useState(45)

  const handleTrainPacman = () => {
    setIsTraining(true)
    // Simulation de progression
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsTraining(false)
          return 100
        }
        return prev + 1
      })
    }, 100)
  }

  const handleTrainGhosts = () => {
    setIsGhostTraining(true)
    setTimeout(() => setIsGhostTraining(false), 3000)
  }

  const handlePause = () => {
    setIsTraining(false)
    setIsGhostTraining(false)
  }

  const handleStop = () => {
    setIsTraining(false)
    setIsGhostTraining(false)
    setProgress(0)
  }

  const handleReset = () => {
    setProgress(0)
  }

  const metrics = [
    { label: 'Score actuel', value: '1,245', unit: 'points', icon: <EmojiEventsIcon />, color: '#4caf50' },
    { label: 'Vitesse', value: '30', unit: 'FPS', icon: <SpeedIcon />, color: '#2196f3' },
    { label: 'Intelligence', value: '78', unit: '/100', icon: <PsychologyIcon />, color: '#9c27b0' },
    { label: 'Tendance', value: '+12%', unit: 'vs précédent', icon: <TrendingUpIcon />, color: '#ff9800' },
  ]

  const actions = [
    { label: 'Entraîner Pac-Man', color: 'primary', onClick: handleTrainPacman, disabled: isTraining },
    { label: 'Entraîner les Fantômes', color: 'secondary', onClick: handleTrainGhosts, disabled: isGhostTraining },
    { label: 'Continuer session', color: 'success', onClick: () => {}, disabled: false },
    { label: 'Comparer runs', color: 'info', onClick: () => {}, disabled: false },
  ]

  return (
    <Box>
      {/* Boutons d'action */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {actions.map((action) => (
          <Grid item xs={6} key={action.label}>
            <Button
              variant="contained"
              color={action.color as any}
              fullWidth
              onClick={action.onClick}
              disabled={action.disabled}
              startIcon={
                action.label.includes('Pac-Man') ? <PlayArrowIcon /> :
                action.label.includes('Fantômes') ? <PsychologyIcon /> :
                action.label.includes('Continuer') ? <PlayArrowIcon /> :
                <RefreshIcon />
              }
              sx={{ py: 1.5 }}
            >
              {action.label}
            </Button>
          </Grid>
        ))}
      </Grid>

      {/* Contrôles de simulation */}
      <Paper sx={{ p: 2, mb: 3, bgcolor: 'background.default' }}>
        <Typography variant="h6" gutterBottom>
          Contrôles de simulation
        </Typography>
        <Stack direction="row" spacing={1} justifyContent="center" sx={{ mb: 2 }}>
          <Tooltip title="Démarrer l'entraînement">
            <IconButton color="primary" onClick={handleTrainPacman} disabled={isTraining}>
              <PlayArrowIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Mettre en pause">
            <IconButton color="warning" onClick={handlePause}>
              <PauseIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Arrêter">
            <IconButton color="error" onClick={handleStop}>
              <StopIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Réinitialiser">
            <IconButton color="info" onClick={handleReset}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Sauvegarder">
            <IconButton color="success">
              <SaveIcon />
            </IconButton>
          </Tooltip>
        </Stack>
        
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">Progression de l'entraînement</Typography>
            <Typography variant="body2" fontWeight={600}>{progress}%</Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={progress} 
            sx={{ height: 10, borderRadius: 5 }}
          />
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Chip 
            label={isTraining ? "Entraînement en cours" : "Prêt"} 
            color={isTraining ? "warning" : "success"} 
            size="small" 
          />
          <Chip 
            label={isGhostTraining ? "Fantômes en apprentissage" : "Fantômes inactifs"} 
            color={isGhostTraining ? "secondary" : "default"} 
            size="small" 
          />
        </Box>
      </Paper>

      {/* Métriques en temps réel */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Métriques en temps réel
        </Typography>
        <Grid container spacing={2}>
          {metrics.map((metric) => (
            <Grid item xs={6} key={metric.label}>
              <Paper 
                sx={{ 
                  p: 2, 
                  textAlign: 'center',
                  bgcolor: 'background.paper',
                  borderLeft: `4px solid ${metric.color}`,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                  <Box sx={{ color: metric.color, mr: 1 }}>
                    {metric.icon}
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {metric.label}
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight={700}>
                  {metric.value}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {metric.unit}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Statut système */}
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          Système: <Chip label="Connecté" color="success" size="small" /> • 
          API: <Chip label="Disponible" color="success" size="small" /> • 
          WebSocket: <Chip label="Actif" color="success" size="small" />
        </Typography>
        <Button size="small" variant="outlined" startIcon={<SaveIcon />}>
          Exporter configuration
        </Button>
      </Box>
    </Box>
  )
}

export default Dashboard