import { Box, Container, Typography, Grid, Paper } from '@mui/material'
import Dashboard from './components/Dashboard/Dashboard'
import ParameterSliders from './components/ParameterSliders/ParameterSliders'
import GameVisualizer from './components/GameVisualizer/GameVisualizer'
import Charts from './components/Charts/Charts'
import SessionManager from './components/SessionManager/SessionManager'
import './App.css'

function App() {
  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h1" component="h1" gutterBottom>
          Laboratoire Scientifique IA Pac-Man
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Interface web pour l'expérimentation d'intelligence artificielle sur Pac-Man
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Colonne gauche : Paramètres et Dashboard */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, mb: 3, height: '100%' }}>
            <Typography variant="h4" gutterBottom>
              Configuration
            </Typography>
            <ParameterSliders />
          </Paper>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h4" gutterBottom>
              Dashboard
            </Typography>
            <Dashboard />
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
              Gestion des Sessions
            </Typography>
            <SessionManager />
          </Paper>
        </Grid>

        {/* Colonne centrale : Visualisation du jeu */}
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h4" gutterBottom>
              Visualisation du Jeu
            </Typography>
            <GameVisualizer />
          </Paper>
        </Grid>

        {/* Colonne droite : Graphiques */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h4" gutterBottom>
              Métriques Temps Réel
            </Typography>
            <Charts />
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Laboratoire IA Pac-Man v0.1.0 • Interface scientifique pour l'expérimentation RL
        </Typography>
      </Box>
    </Container>
  )
}

export default App