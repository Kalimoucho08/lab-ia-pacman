import BarChartIcon from '@mui/icons-material/BarChart'
import ShowChartIcon from '@mui/icons-material/ShowChart'
import TimelineIcon from '@mui/icons-material/Timeline'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import { Box, Paper, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material'
import {
    BarController,
    BarElement,
    CategoryScale,
    Chart as ChartJS,
    Filler,
    Legend,
    LinearScale,
    LineController,
    LineElement,
    PointElement,
    Title,
    Tooltip,
} from 'chart.js'
import React, { useEffect, useRef } from 'react'

// Enregistrer les composants Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  LineController,
  BarController
)

const Charts: React.FC = () => {
  const scoreChartRef = useRef<HTMLCanvasElement>(null)
  const rewardChartRef = useRef<HTMLCanvasElement>(null)
  const lossChartRef = useRef<HTMLCanvasElement>(null)
  const efficiencyChartRef = useRef<HTMLCanvasElement>(null)
  const [chartType, setChartType] = React.useState<'line' | 'bar'>('line')

  // Générer des données de démonstration
  const generateData = (count: number, min: number, max: number, trend: number = 0) => {
    const data = []
    let value = (min + max) / 2
    for (let i = 0; i < count; i++) {
      value += (Math.random() - 0.5) * (max - min) * 0.1 + trend
      value = Math.max(min, Math.min(max, value))
      data.push(value)
    }
    return data
  }

  const labels = Array.from({ length: 50 }, (_, i) => `Ép. ${i * 20}`)

  useEffect(() => {
    if (!scoreChartRef.current || !rewardChartRef.current || !lossChartRef.current || !efficiencyChartRef.current) {
      return
    }

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          mode: 'index' as const,
          intersect: false,
        },
      },
      scales: {
        x: {
          display: false,
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(255, 255, 255, 0.1)',
          },
          ticks: {
            color: 'rgba(255, 255, 255, 0.7)',
          },
        },
      },
      elements: {
        line: {
          tension: 0.4,
        },
        point: {
          radius: 0,
        },
      },
    }

    // Chart 1: Score par épisode
    const scoreChart = new ChartJS(scoreChartRef.current, {
      type: chartType,
      data: {
        labels,
        datasets: [
          {
            label: 'Score',
            data: generateData(50, 0, 2000, 5),
            borderColor: '#4caf50',
            backgroundColor: chartType === 'bar' ? 'rgba(76, 175, 80, 0.5)' : 'rgba(76, 175, 80, 0.1)',
            fill: chartType === 'line',
          },
        ],
      },
      options: chartOptions,
    })

    // Chart 2: Récompense moyenne
    const rewardChart = new ChartJS(rewardChartRef.current, {
      type: chartType,
      data: {
        labels,
        datasets: [
          {
            label: 'Récompense',
            data: generateData(50, -10, 30, 0.2),
            borderColor: '#2196f3',
            backgroundColor: chartType === 'bar' ? 'rgba(33, 150, 243, 0.5)' : 'rgba(33, 150, 243, 0.1)',
            fill: chartType === 'line',
          },
        ],
      },
      options: chartOptions,
    })

    // Chart 3: Perte d'entraînement
    const lossChart = new ChartJS(lossChartRef.current, {
      type: chartType,
      data: {
        labels,
        datasets: [
          {
            label: 'Perte',
            data: generateData(50, 0, 5, -0.02),
            borderColor: '#f44336',
            backgroundColor: chartType === 'bar' ? 'rgba(244, 67, 54, 0.5)' : 'rgba(244, 67, 54, 0.1)',
            fill: chartType === 'line',
          },
        ],
      },
      options: chartOptions,
    })

    // Chart 4: Efficacité
    const efficiencyChart = new ChartJS(efficiencyChartRef.current, {
      type: chartType,
      data: {
        labels,
        datasets: [
          {
            label: 'Efficacité',
            data: generateData(50, 0, 100, 0.5),
            borderColor: '#9c27b0',
            backgroundColor: chartType === 'bar' ? 'rgba(156, 39, 176, 0.5)' : 'rgba(156, 39, 176, 0.1)',
            fill: chartType === 'line',
          },
        ],
      },
      options: chartOptions,
    })

    return () => {
      scoreChart.destroy()
      rewardChart.destroy()
      lossChart.destroy()
      efficiencyChart.destroy()
    }
  }, [chartType])

  const handleChartTypeChange = (_event: React.MouseEvent<HTMLElement>, newType: 'line' | 'bar') => {
    if (newType !== null) {
      setChartType(newType)
    }
  }

  const charts = [
    {
      title: 'Score par épisode',
      description: 'Évolution du score total par épisode d\'entraînement',
      icon: <TrendingUpIcon />,
      color: '#4caf50',
      ref: scoreChartRef,
    },
    {
      title: 'Récompense moyenne',
      description: 'Récompense moyenne par étape (moyenne glissante)',
      icon: <ShowChartIcon />,
      color: '#2196f3',
      ref: rewardChartRef,
    },
    {
      title: 'Perte d\'entraînement',
      description: 'Valeur de la fonction de perte pendant l\'entraînement',
      icon: <TimelineIcon />,
      color: '#f44336',
      ref: lossChartRef,
    },
    {
      title: 'Efficacité',
      description: 'Pourcentage de pac-gommes collectées par épisode',
      icon: <BarChartIcon />,
      color: '#9c27b0',
      ref: efficiencyChartRef,
    },
  ]

  return (
    <Box>
      {/* Contrôles des graphiques */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            4 Graphiques Temps Réel
          </Typography>
          <ToggleButtonGroup
            value={chartType}
            exclusive
            onChange={handleChartTypeChange}
            size="small"
          >
            <ToggleButton value="line">
              <ShowChartIcon sx={{ mr: 1 }} /> Ligne
            </ToggleButton>
            <ToggleButton value="bar">
              <BarChartIcon sx={{ mr: 1 }} /> Barres
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Données mises à jour en temps réel via WebSocket. Cliquez sur un graphique pour plus de détails.
        </Typography>
      </Paper>

      {/* Grille de graphiques */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
        {charts.map((chart) => (
          <Paper key={chart.title} sx={{ p: 2, height: 250 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Box sx={{ color: chart.color, mr: 1 }}>
                {chart.icon}
              </Box>
              <Typography variant="subtitle1" fontWeight={600}>
                {chart.title}
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
              {chart.description}
            </Typography>
            <Box sx={{ position: 'relative', height: 'calc(100% - 60px)' }}>
              <canvas ref={chart.ref} />
            </Box>
          </Paper>
        ))}
      </Box>

      {/* Légende et informations */}
      <Paper sx={{ p: 2, mt: 2 }}>
        <Typography variant="body2" color="text.secondary">
          <strong>Légende:</strong> 
          <Box component="span" sx={{ color: '#4caf50', mx: 1 }}>● Score</Box> • 
          <Box component="span" sx={{ color: '#2196f3', mx: 1 }}>● Récompense</Box> • 
          <Box component="span" sx={{ color: '#f44336', mx: 1 }}>● Perte</Box> • 
          <Box component="span" sx={{ color: '#9c27b0', mx: 1 }}>● Efficacité</Box>
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          Données mises à jour toutes les 100ms • Dernière mise à jour: {new Date().toLocaleTimeString()}
        </Typography>
      </Paper>
    </Box>
  )
}

export default Charts