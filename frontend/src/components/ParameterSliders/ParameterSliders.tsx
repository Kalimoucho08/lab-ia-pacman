import React, { useState } from 'react'
import {
  Box,
  Typography,
  Slider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  IconButton,
  Divider,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import InfoIcon from '@mui/icons-material/Info'
import { Parameter } from '../../types/pacman'

const parameters: Parameter[] = [
  // Entraînement
  {
    id: 'learning_rate',
    name: 'Taux d\'apprentissage',
    category: 'training',
    description: 'Vitesse à laquelle l\'agent ajuste ses poids pendant l\'entraînement. Valeur typique entre 0.0001 et 0.01.',
    min: 0.0001,
    max: 0.01,
    step: 0.0001,
    defaultValue: 0.001,
  },
  {
    id: 'gamma',
    name: 'Facteur de discount',
    category: 'training',
    description: 'Importance des récompenses futures (0 = myope, 1 = vision à long terme).',
    min: 0.5,
    max: 0.99,
    step: 0.01,
    defaultValue: 0.95,
  },
  {
    id: 'episodes',
    name: 'Nombre d\'épisodes',
    category: 'training',
    description: 'Nombre total de parties d\'entraînement à exécuter.',
    min: 100,
    max: 10000,
    step: 100,
    defaultValue: 1000,
  },
  {
    id: 'batch_size',
    name: 'Taille du batch',
    category: 'training',
    description: 'Nombre d\'expériences utilisées pour chaque mise à jour du réseau.',
    min: 16,
    max: 512,
    step: 16,
    defaultValue: 64,
  },
  {
    id: 'buffer_size',
    name: 'Taille du buffer',
    category: 'training',
    description: 'Nombre maximum d\'expériences stockées dans la mémoire de replay.',
    min: 1000,
    max: 100000,
    step: 1000,
    defaultValue: 10000,
  },
  // Jeu
  {
    id: 'grid_size',
    name: 'Taille de la grille',
    category: 'game',
    description: 'Nombre de cellules en largeur et hauteur du labyrinthe.',
    min: 10,
    max: 30,
    step: 1,
    defaultValue: 20,
  },
  {
    id: 'num_ghosts',
    name: 'Nombre de fantômes',
    category: 'game',
    description: 'Nombre de fantômes actifs dans le jeu.',
    min: 1,
    max: 8,
    step: 1,
    defaultValue: 4,
  },
  {
    id: 'power_pellets',
    name: 'Super pac-gommes',
    category: 'game',
    description: 'Nombre de super pac-gommes qui rendent Pac-Man invincible.',
    min: 0,
    max: 8,
    step: 1,
    defaultValue: 4,
  },
  {
    id: 'lives',
    name: 'Vies de Pac-Man',
    category: 'game',
    description: 'Nombre de vies initiales de Pac-Man.',
    min: 1,
    max: 10,
    step: 1,
    defaultValue: 3,
  },
  {
    id: 'pellet_density',
    name: 'Densité des pac-gommes',
    category: 'game',
    description: 'Pourcentage de cellules contenant une pac-gomme.',
    min: 0.1,
    max: 0.9,
    step: 0.05,
    defaultValue: 0.7,
    unit: '%',
  },
  // Intelligence
  {
    id: 'exploration_rate',
    name: 'Taux d\'exploration',
    category: 'intelligence',
    description: 'Probabilité que l\'agent choisisse une action aléatoire plutôt que la meilleure action connue.',
    min: 0.01,
    max: 1.0,
    step: 0.01,
    defaultValue: 0.1,
  },
  {
    id: 'target_update',
    name: 'Fréquence de mise à jour cible',
    category: 'intelligence',
    description: 'Nombre d\'étapes entre chaque mise à jour du réseau cible.',
    min: 100,
    max: 10000,
    step: 100,
    defaultValue: 1000,
  },
  {
    id: 'learning_starts',
    name: 'Début de l\'apprentissage',
    category: 'intelligence',
    description: 'Nombre d\'étapes avant le début de l\'apprentissage (remplissage du buffer).',
    min: 100,
    max: 10000,
    step: 100,
    defaultValue: 1000,
  },
  {
    id: 'train_freq',
    name: 'Fréquence d\'entraînement',
    category: 'intelligence',
    description: 'Nombre d\'étapes entre chaque session d\'entraînement.',
    min: 1,
    max: 100,
    step: 1,
    defaultValue: 4,
  },
  // Visualisation
  {
    id: 'fps',
    name: 'Images par seconde',
    category: 'visualization',
    description: 'Vitesse de rafraîchissement de la visualisation.',
    min: 1,
    max: 60,
    step: 1,
    defaultValue: 30,
    unit: 'FPS',
  },
  {
    id: 'render_scale',
    name: 'Échelle de rendu',
    category: 'visualization',
    description: 'Facteur d\'agrandissement de la visualisation.',
    min: 1,
    max: 5,
    step: 0.5,
    defaultValue: 2,
  },
  {
    id: 'show_grid',
    name: 'Afficher la grille',
    category: 'visualization',
    description: 'Afficher les lignes de la grille (0 = non, 1 = oui).',
    min: 0,
    max: 1,
    step: 1,
    defaultValue: 1,
  },
  {
    id: 'show_stats',
    name: 'Afficher les statistiques',
    category: 'visualization',
    description: 'Afficher les métriques en temps réel (0 = non, 1 = oui).',
    min: 0,
    max: 1,
    step: 1,
    defaultValue: 1,
  },
  {
    id: 'highlight_path',
    name: 'Surligner le chemin',
    category: 'visualization',
    description: 'Mettre en évidence le chemin parcouru par Pac-Man (0 = non, 1 = oui).',
    min: 0,
    max: 1,
    step: 1,
    defaultValue: 1,
  },
]

const categoryLabels = {
  training: 'Entraînement',
  game: 'Jeu',
  intelligence: 'Intelligence',
  visualization: 'Visualisation',
}

const ParameterSliders: React.FC = () => {
  const [values, setValues] = useState<Record<string, number>>(
    parameters.reduce((acc, param) => {
      acc[param.id] = param.defaultValue
      return acc
    }, {} as Record<string, number>)
  )

  const handleSliderChange = (id: string) => (_event: Event, newValue: number | number[]) => {
    setValues({ ...values, [id]: newValue as number })
  }

  const formatValue = (param: Parameter, value: number): string => {
    if (param.unit === '%') {
      return `${(value * 100).toFixed(0)}%`
    }
    if (param.id === 'learning_rate') {
      return value.toFixed(4)
    }
    if (value < 1) {
      return value.toFixed(2)
    }
    return value.toString()
  }

  const categories = ['training', 'game', 'intelligence', 'visualization'] as const

  return (
    <Box>
      {categories.map((category) => (
        <Accordion key={category} defaultExpanded={category === 'training'} sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {categoryLabels[category]}
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {parameters
                .filter((param) => param.category === category)
                .map((param) => (
                  <Box key={param.id} className="slider-container">
                    <Box className="slider-label">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1" fontWeight={500}>
                          {param.name}
                        </Typography>
                        <Tooltip title={param.description} arrow>
                          <IconButton size="small">
                            <InfoIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                      <Typography variant="body2" className="slider-value">
                        {formatValue(param, values[param.id])}
                      </Typography>
                    </Box>
                    <Slider
                      value={values[param.id]}
                      onChange={handleSliderChange(param.id)}
                      min={param.min}
                      max={param.max}
                      step={param.step}
                      valueLabelDisplay="auto"
                      valueLabelFormat={(value) => formatValue(param, value)}
                      sx={{ mt: 1 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      Min: {param.min} • Max: {param.max} • Défaut: {param.defaultValue}
                    </Typography>
                  </Box>
                ))}
            </Box>
          </AccordionDetails>
        </Accordion>
      ))}
      <Divider sx={{ my: 2 }} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          {Object.keys(values).length} paramètres configurés
        </Typography>
        <Typography variant="body2" color="primary">
          Valeurs actuelles sauvegardées automatiquement
        </Typography>
      </Box>
    </Box>
  )
}

export default ParameterSliders