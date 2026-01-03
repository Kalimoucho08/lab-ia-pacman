import React, { useRef, useEffect, useState } from 'react'
import { Box, Paper, Typography, Slider, Stack, IconButton, Tooltip, Chip } from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import PauseIcon from '@mui/icons-material/Pause'
import SkipNextIcon from '@mui/icons-material/SkipNext'
import SkipPreviousIcon from '@mui/icons-material/SkipPrevious'
import RestartAltIcon from '@mui/icons-material/RestartAlt'
import ZoomInIcon from '@mui/icons-material/ZoomIn'
import ZoomOutIcon from '@mui/icons-material/ZoomOut'
import GridOnIcon from '@mui/icons-material/GridOn'
import GridOffIcon from '@mui/icons-material/GridOff'

const GRID_SIZE = 20
const CELL_SIZE = 20
const CANVAS_WIDTH = GRID_SIZE * CELL_SIZE
const CANVAS_HEIGHT = GRID_SIZE * CELL_SIZE

const GameVisualizer: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState(30)
  const [zoom, setZoom] = useState(1.5)
  const [showGrid, setShowGrid] = useState(true)
  const [step, setStep] = useState(0)
  const [gameState, setGameState] = useState({
    pacman: { x: 5, y: 10, direction: 'right' },
    ghosts: [
      { x: 10, y: 5, color: '#ff0000', mode: 'chase' },
      { x: 15, y: 5, color: '#ff88ff', mode: 'scatter' },
      { x: 10, y: 15, color: '#00ffff', mode: 'chase' },
      { x: 15, y: 15, color: '#ffaa00', mode: 'frightened' },
    ],
    pellets: Array.from({ length: 50 }, (_, i) => ({
      x: Math.floor(Math.random() * GRID_SIZE),
      y: Math.floor(Math.random() * GRID_SIZE),
    })),
    powerPellets: [
      { x: 1, y: 1 },
      { x: GRID_SIZE - 2, y: 1 },
      { x: 1, y: GRID_SIZE - 2 },
      { x: GRID_SIZE - 2, y: GRID_SIZE - 2 },
    ],
    score: 1245,
    lives: 3,
  })

  // Dessiner le jeu sur le canvas
  const drawGame = () => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Effacer le canvas
    ctx.fillStyle = '#000'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Dessiner la grille
    if (showGrid) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)'
      ctx.lineWidth = 1
      for (let x = 0; x <= GRID_SIZE; x++) {
        ctx.beginPath()
        ctx.moveTo(x * CELL_SIZE * zoom, 0)
        ctx.lineTo(x * CELL_SIZE * zoom, canvas.height)
        ctx.stroke()
      }
      for (let y = 0; y <= GRID_SIZE; y++) {
        ctx.beginPath()
        ctx.moveTo(0, y * CELL_SIZE * zoom)
        ctx.lineTo(canvas.width, y * CELL_SIZE * zoom)
        ctx.stroke()
      }
    }

    // Dessiner les pac-gommes
    ctx.fillStyle = '#ffffff'
    gameState.pellets.forEach(pellet => {
      ctx.beginPath()
      ctx.arc(
        (pellet.x + 0.5) * CELL_SIZE * zoom,
        (pellet.y + 0.5) * CELL_SIZE * zoom,
        2 * zoom,
        0,
        Math.PI * 2
      )
      ctx.fill()
    })

    // Dessiner les super pac-gommes
    ctx.fillStyle = '#ffff00'
    gameState.powerPellets.forEach(pellet => {
      ctx.beginPath()
      ctx.arc(
        (pellet.x + 0.5) * CELL_SIZE * zoom,
        (pellet.y + 0.5) * CELL_SIZE * zoom,
        5 * zoom,
        0,
        Math.PI * 2
      )
      ctx.fill()
    })

    // Dessiner Pac-Man
    ctx.fillStyle = '#ffff00'
    ctx.beginPath()
    const pacmanAngle = (step % 20) / 20 * Math.PI * 0.5
    ctx.arc(
      (gameState.pacman.x + 0.5) * CELL_SIZE * zoom,
      (gameState.pacman.y + 0.5) * CELL_SIZE * zoom,
      (CELL_SIZE * 0.4) * zoom,
      pacmanAngle,
      Math.PI * 2 - pacmanAngle
    )
    ctx.lineTo(
      (gameState.pacman.x + 0.5) * CELL_SIZE * zoom,
      (gameState.pacman.y + 0.5) * CELL_SIZE * zoom
    )
    ctx.fill()

    // Dessiner les fantômes
    gameState.ghosts.forEach(ghost => {
      ctx.fillStyle = ghost.color
      // Corps
      ctx.beginPath()
      ctx.arc(
        (ghost.x + 0.5) * CELL_SIZE * zoom,
        (ghost.y + 0.5) * CELL_SIZE * zoom,
        (CELL_SIZE * 0.4) * zoom,
        0,
        Math.PI
      )
      ctx.lineTo(
        (ghost.x - 0.3) * CELL_SIZE * zoom,
        (ghost.y + 0.5) * CELL_SIZE * zoom
      )
      ctx.fill()

      // Yeux
      ctx.fillStyle = '#ffffff'
      ctx.beginPath()
      ctx.arc(
        (ghost.x + 0.3) * CELL_SIZE * zoom,
        (ghost.y + 0.3) * CELL_SIZE * zoom,
        3 * zoom,
        0,
        Math.PI * 2
      )
      ctx.fill()
      ctx.beginPath()
      ctx.arc(
        (ghost.x + 0.7) * CELL_SIZE * zoom,
        (ghost.y + 0.3) * CELL_SIZE * zoom,
        3 * zoom,
        0,
        Math.PI * 2
      )
      ctx.fill()

      // Pupilles
      ctx.fillStyle = '#0000ff'
      ctx.beginPath()
      ctx.arc(
        (ghost.x + 0.3) * CELL_SIZE * zoom,
        (ghost.y + 0.3) * CELL_SIZE * zoom,
        1.5 * zoom,
        0,
        Math.PI * 2
      )
      ctx.fill()
      ctx.beginPath()
      ctx.arc(
        (ghost.x + 0.7) * CELL_SIZE * zoom,
        (ghost.y + 0.3) * CELL_SIZE * zoom,
        1.5 * zoom,
        0,
        Math.PI * 2
      )
      ctx.fill()
    })

    // Dessiner les informations
    ctx.fillStyle = '#ffffff'
    ctx.font = `${12 * zoom}px Arial`
    ctx.fillText(`Score: ${gameState.score}`, 10, 20)
    ctx.fillText(`Vies: ${gameState.lives}`, 10, 40)
    ctx.fillText(`Étape: ${step}`, 10, 60)
  }

  // Animation loop
  useEffect(() => {
    let animationFrameId: number
    let lastTime = 0
    const interval = 1000 / speed

    const animate = (time: number) => {
      if (isPlaying && time - lastTime > interval) {
        lastTime = time
        setStep(prev => prev + 1)
        
        // Mettre à jour la position de Pac-Man
        setGameState(prev => {
          const newX = (prev.pacman.x + 1) % GRID_SIZE
          return {
            ...prev,
            pacman: { ...prev.pacman, x: newX },
          }
        })
      }
      drawGame()
      animationFrameId = requestAnimationFrame(animate)
    }

    animationFrameId = requestAnimationFrame(animate)
    return () => {
      cancelAnimationFrame(animationFrameId)
    }
  }, [isPlaying, speed, zoom, showGrid, step])

  // Initial draw
  useEffect(() => {
    drawGame()
  }, [])

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying)
  }

  const handleStepForward = () => {
    setStep(prev => prev + 1)
    drawGame()
  }

  const handleStepBackward = () => {
    setStep(prev => Math.max(0, prev - 1))
    drawGame()
  }

  const handleReset = () => {
    setIsPlaying(false)
    setStep(0)
    setGameState({
      ...gameState,
      pacman: { x: 5, y: 10, direction: 'right' },
    })
  }

  const handleZoomIn = () => {
    setZoom(prev => Math.min(3, prev + 0.25))
  }

  const handleZoomOut = () => {
    setZoom(prev => Math.max(0.5, prev - 0.25))
  }

  const handleSpeedChange = (_event: Event, newValue: number | number[]) => {
    setSpeed(newValue as number)
  }

  return (
    <Box>
      {/* Canvas de jeu */}
      <Paper 
        sx={{ 
          p: 2, 
          mb: 2, 
          display: 'flex', 
          justifyContent: 'center',
          bgcolor: 'black',
        }}
      >
        <canvas
          ref={canvasRef}
          width={CANVAS_WIDTH * zoom}
          height={CANVAS_HEIGHT * zoom}
          className="game-canvas"
          style={{
            borderRadius: '8px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
          }}
        />
      </Paper>

      {/* Contrôles */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack direction="row" spacing={1} justifyContent="center" sx={{ mb: 2 }}>
          <Tooltip title="Étape précédente">
            <IconButton onClick={handleStepBackward}>
              <SkipPreviousIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title={isPlaying ? "Pause" : "Lecture"}>
            <IconButton 
              color={isPlaying ? "warning" : "success"} 
              onClick={handlePlayPause}
              sx={{ width: 56, height: 56 }}
            >
              {isPlaying ? <PauseIcon /> : <PlayArrowIcon />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Étape suivante">
            <IconButton onClick={handleStepForward}>
              <SkipNextIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Réinitialiser">
            <IconButton onClick={handleReset}>
              <RestartAltIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Zoom avant">
            <IconButton onClick={handleZoomIn}>
              <ZoomInIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Zoom arrière">
            <IconButton onClick={handleZoomOut}>
              <ZoomOutIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title={showGrid ? "Masquer la grille" : "Afficher la grille"}>
            <IconButton onClick={() => setShowGrid(!showGrid)}>
              {showGrid ? <GridOnIcon /> : <GridOffIcon />}
            </IconButton>
          </Tooltip>
        </Stack>

        <Box sx={{ px: 2 }}>
          <Typography variant="body2" gutterBottom>
            Vitesse: {speed} FPS
          </Typography>
          <Slider
            value={speed}
            onChange={handleSpeedChange}
            min={1}
            max={60}
            step={1}
            valueLabelDisplay="auto"
            sx={{ mt: 1 }}
          />
        </Box>
      </Paper>

      {/* Informations du jeu */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          État du jeu
        </Typography>
        <Stack direction="row" spacing={2} flexWrap="wrap">
          <Chip 
            label={`Score: ${gameState.score}`} 
            color="primary" 
            variant="outlined" 
          />
          <Chip 
            label={`Vies: ${gameState.lives}`} 
            color={gameState.lives > 1 ? "success" : "error"} 
            variant="outlined" 
          />
          <Chip 
            label={`Étape: ${step}`} 
            color="info" 
            variant="outlined" 
          />
          <Chip 
            label={`Zoom: ${zoom.toFixed(1)}x`} 
            color="secondary" 
            variant="outlined" 
          />
          <Chip 
            label={isPlaying ? "En cours" : "En pause"} 
            color={isPlaying ? "success" : "warning"} 
            variant="outlined" 
          />
        </Stack>
        
        <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>
          Position Pac-Man: ({gameState.pacman.x}, {gameState.pacman.y}) • 
          Fantômes actifs: {gameState.ghosts.length} • 
          Pac-gommes restantes: {gameState.pellets.length}
        </Typography>
      </Paper>
    </Box>
  )
}

export default GameVisualizer