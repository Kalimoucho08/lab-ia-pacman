import { WebSocketMessage, GameState, Session } from '../types/pacman'

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

type WebSocketCallback = (message: WebSocketMessage) => void
type GameStateCallback = (gameState: GameState) => void
type MetricsCallback = (metrics: any) => void
type SessionCallback = (session: Session) => void
type ErrorCallback = (error: string) => void

class WebSocketService {
  private socket: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private isConnecting = false

  // Callbacks
  private onMessageCallbacks: WebSocketCallback[] = []
  private onGameStateCallbacks: GameStateCallback[] = []
  private onMetricsCallbacks: MetricsCallback[] = []
  private onSessionCallbacks: SessionCallback[] = []
  private onErrorCallbacks: ErrorCallback[] = []
  private onConnectCallbacks: (() => void)[] = []
  private onDisconnectCallbacks: (() => void)[] = []

  constructor(private url: string = WS_BASE_URL) {}

  // Connexion au WebSocket
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      if (this.isConnecting) {
        reject(new Error('Already connecting'))
        return
      }

      this.isConnecting = true

      try {
        this.socket = new WebSocket(this.url)

        this.socket.onopen = () => {
          console.log('WebSocket connected')
          this.isConnecting = false
          this.reconnectAttempts = 0
          this.onConnectCallbacks.forEach(callback => callback())
          resolve()
        }

        this.socket.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.socket.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.onErrorCallbacks.forEach(callback => callback('WebSocket error'))
          this.isConnecting = false
          reject(error)
        }

        this.socket.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason)
          this.isConnecting = false
          this.onDisconnectCallbacks.forEach(callback => callback())
          this.attemptReconnect()
        }
      } catch (error) {
        this.isConnecting = false
        reject(error)
      }
    })
  }

  // Tentative de reconnexion
  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    setTimeout(() => {
      if (this.socket?.readyState !== WebSocket.OPEN) {
        this.connect().catch(() => {
          // La reconnexion échouera silencieusement et réessaiera au prochain intervalle
        })
      }
    }, delay)
  }

  // Gestion des messages
  private handleMessage(message: WebSocketMessage) {
    // Appeler les callbacks généraux
    this.onMessageCallbacks.forEach(callback => callback(message))

    // Appeler les callbacks spécifiques au type
    switch (message.type) {
      case 'game_state':
        this.onGameStateCallbacks.forEach(callback => callback(message.data))
        break
      case 'metrics':
        this.onMetricsCallbacks.forEach(callback => callback(message.data))
        break
      case 'session_update':
        this.onSessionCallbacks.forEach(callback => callback(message.data))
        break
      case 'error':
        this.onErrorCallbacks.forEach(callback => callback(message.data))
        break
    }
  }

  // Envoyer un message
  send(message: WebSocketMessage): boolean {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message))
      return true
    }
    console.warn('WebSocket not connected, message not sent:', message)
    return false
  }

  // S'abonner à un type de message
  subscribeToGameState(sessionId: string): boolean {
    return this.send({
      type: 'subscribe',
      data: { channel: 'game_state', sessionId },
      timestamp: new Date().toISOString(),
    })
  }

  subscribeToMetrics(sessionId: string): boolean {
    return this.send({
      type: 'subscribe',
      data: { channel: 'metrics', sessionId },
      timestamp: new Date().toISOString(),
    })
  }

  subscribeToSession(sessionId: string): boolean {
    return this.send({
      type: 'subscribe',
      data: { channel: 'session', sessionId },
      timestamp: new Date().toISOString(),
    })
  }

  // Se désabonner
  unsubscribe(channel: string, sessionId: string): boolean {
    return this.send({
      type: 'unsubscribe',
      data: { channel, sessionId },
      timestamp: new Date().toISOString(),
    })
  }

  // Déconnexion
  disconnect(): void {
    if (this.socket) {
      this.socket.close(1000, 'Client disconnected')
      this.socket = null
    }
    this.reconnectAttempts = this.maxReconnectAttempts // Empêcher la reconnexion automatique
  }

  // État de la connexion
  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN
  }

  // Getters pour l'état
  get readyState(): number {
    return this.socket?.readyState || WebSocket.CLOSED
  }

  // Méthodes pour enregistrer les callbacks
  onMessage(callback: WebSocketCallback): void {
    this.onMessageCallbacks.push(callback)
  }

  onGameState(callback: GameStateCallback): void {
    this.onGameStateCallbacks.push(callback)
  }

  onMetrics(callback: MetricsCallback): void {
    this.onMetricsCallbacks.push(callback)
  }

  onSession(callback: SessionCallback): void {
    this.onSessionCallbacks.push(callback)
  }

  onError(callback: ErrorCallback): void {
    this.onErrorCallbacks.push(callback)
  }

  onConnect(callback: () => void): void {
    this.onConnectCallbacks.push(callback)
  }

  onDisconnect(callback: () => void): void {
    this.onDisconnectCallbacks.push(callback)
  }

  // Supprimer les callbacks
  removeMessageCallback(callback: WebSocketCallback): void {
    this.onMessageCallbacks = this.onMessageCallbacks.filter(cb => cb !== callback)
  }

  removeGameStateCallback(callback: GameStateCallback): void {
    this.onGameStateCallbacks = this.onGameStateCallbacks.filter(cb => cb !== callback)
  }

  removeMetricsCallback(callback: MetricsCallback): void {
    this.onMetricsCallbacks = this.onMetricsCallbacks.filter(cb => cb !== callback)
  }

  removeSessionCallback(callback: SessionCallback): void {
    this.onSessionCallbacks = this.onSessionCallbacks.filter(cb => cb !== callback)
  }

  removeErrorCallback(callback: ErrorCallback): void {
    this.onErrorCallbacks = this.onErrorCallbacks.filter(cb => cb !== callback)
  }
}

// Instance singleton
const webSocketService = new WebSocketService()

export default webSocketService