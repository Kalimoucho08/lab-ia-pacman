import React, { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Button,
  Chip,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Divider,
  Tooltip,
} from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import PauseIcon from '@mui/icons-material/Pause'
import StopIcon from '@mui/icons-material/Stop'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import AddIcon from '@mui/icons-material/Add'
import FolderIcon from '@mui/icons-material/Folder'
import DownloadIcon from '@mui/icons-material/Download'
import CompareIcon from '@mui/icons-material/Compare'
import { Session } from '../../types/pacman'

const mockSessions: Session[] = [
  {
    id: '1',
    name: 'Entraînement DQN - Grid 20x20',
    createdAt: '2026-01-03T10:30:00',
    parameters: {
      training: {
        learning_rate: 0.001,
        gamma: 0.95,
        episodes: 1000,
        batch_size: 64,
        buffer_size: 10000,
      },
      game: {
        grid_size: 20,
        num_ghosts: 4,
        power_pellets: 4,
        lives: 3,
        pellet_density: 0.7,
      },
      intelligence: {
        exploration_rate: 0.1,
        target_update: 1000,
        learning_starts: 1000,
        train_freq: 4,
      },
      visualization: {
        fps: 30,
        render_scale: 2,
        show_grid: 1,
        show_stats: 1,
        highlight_path: 1,
      },
    },
    status: 'completed',
    metrics: {
      score: 1245,
      steps: 8500,
      efficiency: 78,
      survival: 92,
      intelligence: 85,
    },
  },
  {
    id: '2',
    name: 'PPO Multi-Agent - 8 Fantômes',
    createdAt: '2026-01-03T09:15:00',
    parameters: {
      training: {
        learning_rate: 0.0003,
        gamma: 0.99,
        episodes: 5000,
        batch_size: 128,
        buffer_size: 50000,
      },
      game: {
        grid_size: 25,
        num_ghosts: 8,
        power_pellets: 6,
        lives: 5,
        pellet_density: 0.8,
      },
      intelligence: {
        exploration_rate: 0.05,
        target_update: 500,
        learning_starts: 5000,
        train_freq: 8,
      },
      visualization: {
        fps: 60,
        render_scale: 1.5,
        show_grid: 0,
        show_stats: 1,
        highlight_path: 0,
      },
    },
    status: 'running',
    metrics: {
      score: 856,
      steps: 3200,
      efficiency: 65,
      survival: 78,
      intelligence: 72,
    },
  },
  {
    id: '3',
    name: 'Test Random Agent - Baseline',
    createdAt: '2026-01-02T16:45:00',
    parameters: {
      training: {
        learning_rate: 0.01,
        gamma: 0.9,
        episodes: 100,
        batch_size: 32,
        buffer_size: 1000,
      },
      game: {
        grid_size: 15,
        num_ghosts: 2,
        power_pellets: 2,
        lives: 3,
        pellet_density: 0.5,
      },
      intelligence: {
        exploration_rate: 1.0,
        target_update: 100,
        learning_starts: 100,
        train_freq: 1,
      },
      visualization: {
        fps: 10,
        render_scale: 1,
        show_grid: 1,
        show_stats: 1,
        highlight_path: 1,
      },
    },
    status: 'paused',
    metrics: {
      score: 120,
      steps: 500,
      efficiency: 15,
      survival: 30,
      intelligence: 25,
    },
  },
  {
    id: '4',
    name: 'Optimisation Hyperparamètres',
    createdAt: '2026-01-01T14:20:00',
    parameters: {
      training: {
        learning_rate: 0.0005,
        gamma: 0.97,
        episodes: 2000,
        batch_size: 256,
        buffer_size: 20000,
      },
      game: {
        grid_size: 20,
        num_ghosts: 4,
        power_pellets: 4,
        lives: 3,
        pellet_density: 0.7,
      },
      intelligence: {
        exploration_rate: 0.2,
        target_update: 2000,
        learning_starts: 2000,
        train_freq: 2,
      },
      visualization: {
        fps: 30,
        render_scale: 2,
        show_grid: 1,
        show_stats: 1,
        highlight_path: 1,
      },
    },
    status: 'error',
    metrics: {
      score: 0,
      steps: 100,
      efficiency: 0,
      survival: 0,
      intelligence: 0,
    },
  },
]

const SessionManager: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>(mockSessions)
  const [openDialog, setOpenDialog] = useState(false)
  const [newSessionName, setNewSessionName] = useState('')
  const [selectedSession, setSelectedSession] = useState<Session | null>(null)

  const handleStartSession = (sessionId: string) => {
    setSessions(sessions.map(session => 
      session.id === sessionId 
        ? { ...session, status: 'running' as const }
        : session
    ))
  }

  const handlePauseSession = (sessionId: string) => {
    setSessions(sessions.map(session => 
      session.id === sessionId 
        ? { ...session, status: 'paused' as const }
        : session
    ))
  }

  const handleStopSession = (sessionId: string) => {
    setSessions(sessions.map(session => 
      session.id === sessionId 
        ? { ...session, status: 'completed' as const }
        : session
    ))
  }

  const handleDeleteSession = (sessionId: string) => {
    setSessions(sessions.filter(session => session.id !== sessionId))
  }

  const handleCreateSession = () => {
    if (!newSessionName.trim()) return

    const newSession: Session = {
      id: Date.now().toString(),
      name: newSessionName,
      createdAt: new Date().toISOString(),
      parameters: mockSessions[0].parameters, // Utiliser les paramètres par défaut
      status: 'paused',
      metrics: {
        score: 0,
        steps: 0,
        efficiency: 0,
        survival: 0,
        intelligence: 0,
      },
    }

    setSessions([newSession, ...sessions])
    setNewSessionName('')
    setOpenDialog(false)
  }

  const handleCompareSessions = () => {
    // Logique de comparaison
    alert('Fonctionnalité de comparaison à implémenter')
  }

  const getStatusColor = (status: Session['status']) => {
    switch (status) {
      case 'running': return 'success'
      case 'paused': return 'warning'
      case 'completed': return 'info'
      case 'error': return 'error'
      default: return 'default'
    }
  }

  const getStatusLabel = (status: Session['status']) => {
    switch (status) {
      case 'running': return 'En cours'
      case 'paused': return 'En pause'
      case 'completed': return 'Terminé'
      case 'error': return 'Erreur'
      default: return 'Inconnu'
    }
  }

  return (
    <Box>
      {/* En-tête avec actions */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Sessions d'expérimentation
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<CompareIcon />}
            onClick={handleCompareSessions}
            sx={{ mr: 1 }}
          >
            Comparer
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenDialog(true)}
          >
            Nouvelle session
          </Button>
        </Box>
      </Box>

      {/* Liste des sessions */}
      <List sx={{ maxHeight: 400, overflow: 'auto' }}>
        {sessions.map((session) => (
          <React.Fragment key={session.id}>
            <ListItem
              sx={{
                bgcolor: 'background.paper',
                mb: 1,
                borderRadius: 1,
                borderLeft: `4px solid ${
                  session.status === 'running' ? '#4caf50' :
                  session.status === 'paused' ? '#ff9800' :
                  session.status === 'completed' ? '#2196f3' : '#f44336'
                }`,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
                <FolderIcon sx={{ color: 'text.secondary', mr: 1 }} />
              </Box>
              <ListItemText
                primary={
                  <Typography variant="subtitle1" fontWeight={600}>
                    {session.name}
                  </Typography>
                }
                secondary={
                  <>
                    <Typography variant="caption" component="span" display="block">
                      Créée le {new Date(session.createdAt).toLocaleString()}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                      <Chip
                        label={getStatusLabel(session.status)}
                        color={getStatusColor(session.status)}
                        size="small"
                      />
                      <Chip
                        label={`Score: ${session.metrics.score}`}
                        variant="outlined"
                        size="small"
                      />
                      <Chip
                        label={`Intelligence: ${session.metrics.intelligence}/100`}
                        variant="outlined"
                        size="small"
                      />
                    </Box>
                  </>
                }
              />
              <ListItemSecondaryAction>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {session.status === 'running' ? (
                    <Tooltip title="Mettre en pause">
                      <IconButton size="small" onClick={() => handlePauseSession(session.id)}>
                        <PauseIcon />
                      </IconButton>
                    </Tooltip>
                  ) : (
                    <Tooltip title="Démarrer">
                      <IconButton size="small" onClick={() => handleStartSession(session.id)}>
                        <PlayArrowIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                  <Tooltip title="Arrêter">
                    <IconButton size="small" onClick={() => handleStopSession(session.id)}>
                      <StopIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Éditer">
                    <IconButton size="small">
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Supprimer">
                    <IconButton size="small" onClick={() => handleDeleteSession(session.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Télécharger">
                    <IconButton size="small">
                      <DownloadIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </ListItemSecondaryAction>
            </ListItem>
            <Divider variant="inset" component="li" />
          </React.Fragment>
        ))}
      </List>

      {/* Statistiques */}
      <Paper sx={{ p: 2, mt: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Résumé des sessions
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h5">{sessions.length}</Typography>
            <Typography variant="caption">Sessions totales</Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h5" color="success.main">
              {sessions.filter(s => s.status === 'running').length}
            </Typography>
            <Typography variant="caption">Actives</Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h5" color="info.main">
              {sessions.filter(s => s.status === 'completed').length}
            </Typography>
            <Typography variant="caption">Terminées</Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h5">
              {Math.max(...sessions.map(s => s.metrics.score))}
            </Typography>
            <Typography variant="caption">Meilleur score</Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h5">
              {Math.round(sessions.reduce((acc, s) => acc + s.metrics.intelligence, 0) / sessions.length)}
            </Typography>
            <Typography variant="caption">Intelligence moyenne</Typography>
          </Box>
        </Box>
      </Paper>

      {/* Dialogue de création de session */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Créer une nouvelle session</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Nom de la session"
            fullWidth
            value={newSessionName}
            onChange={(e) => setNewSessionName(e.target.value)}
            placeholder="Ex: Entraînement DQN avec exploration 0.2"
            sx={{ mt: 2 }}
          />
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Modèle de configuration</InputLabel>
            <Select
              value="default"
              label="Modèle de configuration"
            >
              <MenuItem value="default">Configuration par défaut</MenuItem>
              <MenuItem value="dqn">DQN standard</MenuItem>
              <MenuItem value="ppo">PPO multi-agent</MenuItem>
              <MenuItem value="random">Agent aléatoire (baseline)</MenuItem>
            </Select>
          </FormControl>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            La session sera créée avec les paramètres actuels du dashboard.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Annuler</Button>
          <Button 
            onClick={handleCreateSession} 
            variant="contained"
            disabled={!newSessionName.trim()}
          >
            Créer
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default SessionManager