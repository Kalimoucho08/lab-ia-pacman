import axios from 'axios'
import { AllParameters, Session, GameState } from '../types/pacman'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Gestion des paramètres
export const parametersApi = {
  // Récupérer les paramètres actuels
  getCurrent: async (): Promise<AllParameters> => {
    const response = await api.get<AllParameters>('/parameters')
    return response.data
  },

  // Mettre à jour les paramètres
  update: async (parameters: Partial<AllParameters>): Promise<AllParameters> => {
    const response = await api.put<AllParameters>('/parameters', parameters)
    return response.data
  },

  // Réinitialiser aux valeurs par défaut
  reset: async (): Promise<AllParameters> => {
    const response = await api.post<AllParameters>('/parameters/reset')
    return response.data
  },
}

// Gestion des sessions
export const sessionsApi = {
  // Lister toutes les sessions
  list: async (): Promise<Session[]> => {
    const response = await api.get<Session[]>('/sessions')
    return response.data
  },

  // Créer une nouvelle session
  create: async (name: string, parameters?: AllParameters): Promise<Session> => {
    const response = await api.post<Session>('/sessions', { name, parameters })
    return response.data
  },

  // Récupérer une session spécifique
  get: async (sessionId: string): Promise<Session> => {
    const response = await api.get<Session>(`/sessions/${sessionId}`)
    return response.data
  },

  // Mettre à jour une session
  update: async (sessionId: string, updates: Partial<Session>): Promise<Session> => {
    const response = await api.put<Session>(`/sessions/${sessionId}`, updates)
    return response.data
  },

  // Supprimer une session
  delete: async (sessionId: string): Promise<void> => {
    await api.delete(`/sessions/${sessionId}`)
  },

  // Démarrer/arrêter une session
  start: async (sessionId: string): Promise<Session> => {
    const response = await api.post<Session>(`/sessions/${sessionId}/start`)
    return response.data
  },

  pause: async (sessionId: string): Promise<Session> => {
    const response = await api.post<Session>(`/sessions/${sessionId}/pause`)
    return response.data
  },

  stop: async (sessionId: string): Promise<Session> => {
    const response = await api.post<Session>(`/sessions/${sessionId}/stop`)
    return response.data
  },
}

// Gestion de l'entraînement
export const trainingApi = {
  // Démarrer l'entraînement de Pac-Man
  trainPacman: async (parameters?: AllParameters): Promise<{ sessionId: string }> => {
    const response = await api.post<{ sessionId: string }>('/training/pacman', { parameters })
    return response.data
  },

  // Démarrer l'entraînement des fantômes
  trainGhosts: async (parameters?: AllParameters): Promise<{ sessionId: string }> => {
    const response = await api.post<{ sessionId: string }>('/training/ghosts', { parameters })
    return response.data
  },

  // Continuer une session existante
  continueSession: async (sessionId: string): Promise<Session> => {
    const response = await api.post<Session>(`/training/continue/${sessionId}`)
    return response.data
  },

  // Obtenir l'état actuel de l'entraînement
  getStatus: async (sessionId: string): Promise<{
    status: 'running' | 'paused' | 'completed' | 'error'
    progress: number
    metrics: any
  }> => {
    const response = await api.get(`/training/status/${sessionId}`)
    return response.data
  },
}

// Gestion du jeu
export const gameApi = {
  // Obtenir l'état actuel du jeu
  getState: async (sessionId: string): Promise<GameState> => {
    const response = await api.get<GameState>(`/game/state/${sessionId}`)
    return response.data
  },

  // Exécuter une étape du jeu
  step: async (sessionId: string, action?: string): Promise<GameState> => {
    const response = await api.post<GameState>(`/game/step/${sessionId}`, { action })
    return response.data
  },

  // Réinitialiser le jeu
  reset: async (sessionId: string): Promise<GameState> => {
    const response = await api.post<GameState>(`/game/reset/${sessionId}`)
    return response.data
  },

  // Obtenir les métriques du jeu
  getMetrics: async (sessionId: string): Promise<any> => {
    const response = await api.get(`/game/metrics/${sessionId}`)
    return response.data
  },
}

// Gestion des exports
export const exportApi = {
  // Exporter une session au format ZIP
  exportSession: async (sessionId: string): Promise<Blob> => {
    const response = await api.get(`/export/session/${sessionId}`, {
      responseType: 'blob',
    })
    return response.data
  },

  // Exporter les paramètres au format JSON
  exportParameters: async (parameters: AllParameters): Promise<Blob> => {
    const response = await api.post('/export/parameters', parameters, {
      responseType: 'blob',
    })
    return response.data
  },

  // Exporter les métriques au format CSV
  exportMetrics: async (sessionId: string): Promise<Blob> => {
    const response = await api.get(`/export/metrics/${sessionId}`, {
      responseType: 'blob',
    })
    return response.data
  },
}

// Gestion des erreurs
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    
    // Gestion des erreurs spécifiques
    if (error.response?.status === 401) {
      // Rediriger vers la page de connexion si nécessaire
      console.warn('Authentication required')
    } else if (error.response?.status === 404) {
      console.error('Resource not found')
    } else if (error.response?.status >= 500) {
      console.error('Server error')
    }
    
    return Promise.reject(error)
  }
)

export default api