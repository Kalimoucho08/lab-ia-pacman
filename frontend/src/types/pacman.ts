export interface Parameter {
  id: string
  name: string
  category: 'training' | 'game' | 'intelligence' | 'visualization'
  description: string
  min: number
  max: number
  step: number
  defaultValue: number
  unit?: string
}

export interface TrainingParameters {
  learning_rate: number
  gamma: number
  episodes: number
  batch_size: number
  buffer_size: number
}

export interface GameParameters {
  grid_size: number
  num_ghosts: number
  power_pellets: number
  lives: number
  pellet_density: number
}

export interface IntelligenceParameters {
  exploration_rate: number
  target_update: number
  learning_starts: number
  train_freq: number
}

export interface VisualizationParameters {
  fps: number
  render_scale: number
  show_grid: number
  show_stats: number
  highlight_path: number
}

export interface AllParameters {
  training: TrainingParameters
  game: GameParameters
  intelligence: IntelligenceParameters
  visualization: VisualizationParameters
}

export interface Session {
  id: string
  name: string
  createdAt: string
  parameters: AllParameters
  status: 'running' | 'paused' | 'completed' | 'error'
  metrics: {
    score: number
    steps: number
    efficiency: number
    survival: number
    intelligence: number
  }
}

export interface ChartDataPoint {
  timestamp: number
  value: number
  label: string
}

export interface ChartDataset {
  label: string
  data: ChartDataPoint[]
  color: string
}

export interface GameState {
  grid: number[][]
  pacman: { x: number; y: number; direction: string }
  ghosts: Array<{ x: number; y: number; color: string; mode: string }>
  pellets: Array<{ x: number; y: number }>
  powerPellets: Array<{ x: number; y: number }>
  score: number
  lives: number
  step: number
}

export interface WebSocketMessage {
  type: 'game_state' | 'metrics' | 'session_update' | 'error' | 'subscribe' | 'unsubscribe'
  data: any
  timestamp: string
}