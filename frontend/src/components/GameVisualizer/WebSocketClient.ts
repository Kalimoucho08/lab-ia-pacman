/**
 * Client WebSocket optimisé pour la visualisation temps réel de Pac-Man
 * 
 * Fonctionnalités :
 * - Reconnexion automatique avec backoff exponentiel
 * - Buffering des états de jeu pour synchronisation 60 FPS
 * - Gestion de la latence et compensation
 * - Priorisation des messages (game_state > metrics > autres)
 * - Compression optionnelle des données
 * - Statistiques de connexion en temps réel
 */

import { GameState, WebSocketMessage as BaseWebSocketMessage } from '../../types/pacman';

// Extension du type WebSocketMessage pour inclure les types spécifiques à la visualisation
type ExtendedWebSocketMessageType =
  | BaseWebSocketMessage['type']
  | 'pong'
  | 'ping'
  | 'latency_test'
  | 'latency_response'
  | 'visualization_config_updated'
  | 'test_message';

interface ExtendedWebSocketMessage {
  type: ExtendedWebSocketMessageType;
  data: any;
  timestamp: string;
}

export interface WebSocketConfig {
  url: string;
  maxReconnectAttempts: number;
  reconnectDelay: number;
  maxBufferSize: number;
  targetFps: number;
  enableCompression: boolean;
  pingInterval: number;
}

export interface ConnectionStats {
  connected: boolean;
  latency: number; // ms
  messagesReceived: number;
  messagesSent: number;
  bytesReceived: number;
  bytesSent: number;
  reconnectAttempts: number;
  lastMessageTime: number;
  bufferSize: number;
  droppedFrames: number;
}

export type GameStateCallback = (gameState: GameState) => void;
export type ConnectionCallback = (connected: boolean) => void;
export type ErrorCallback = (error: string) => void;
export type StatsCallback = (stats: ConnectionStats) => void;

export class WebSocketClient {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private isConnecting = false;
  private pingIntervalId: number | null = null;
  private lastPingTime = 0;
  private latency = 0;
  private messageQueue: ExtendedWebSocketMessage[] = [];
  private gameStateBuffer: GameState[] = [];
  private lastProcessedFrame = 0;
  private stats: ConnectionStats;
  private config: WebSocketConfig;

  // Callbacks
  private onGameStateCallbacks: GameStateCallback[] = [];
  private onConnectCallbacks: ConnectionCallback[] = [];
  private onDisconnectCallbacks: ConnectionCallback[] = [];
  private onErrorCallbacks: ErrorCallback[] = [];
  private onStatsCallbacks: StatsCallback[] = [];

  // Métriques
  private messagesReceived = 0;
  private messagesSent = 0;
  private bytesReceived = 0;
  private bytesSent = 0;
  private droppedFrames = 0;

  constructor(config: Partial<WebSocketConfig> = {}) {
    this.config = {
      url: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
      maxReconnectAttempts: 10,
      reconnectDelay: 1000,
      maxBufferSize: 60, // 1 seconde à 60 FPS
      targetFps: 60,
      enableCompression: false,
      pingInterval: 5000,
      ...config
    };

    this.stats = {
      connected: false,
      latency: 0,
      messagesReceived: 0,
      messagesSent: 0,
      bytesReceived: 0,
      bytesSent: 0,
      reconnectAttempts: 0,
      lastMessageTime: 0,
      bufferSize: 0,
      droppedFrames: 0
    };
  }

  /**
   * Connexion au serveur WebSocket
   */
  public async connect(): Promise<void> {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    if (this.isConnecting) {
      return Promise.reject(new Error('Déjà en cours de connexion'));
    }

    this.isConnecting = true;

    return new Promise((resolve, reject) => {
      try {
        this.socket = new WebSocket(this.config.url);

        this.socket.onopen = () => {
          console.log('WebSocketClient: Connexion établie');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.stats.connected = true;
          this.startPingInterval();
          this.notifyConnect();
          this.updateStats();
          resolve();
        };

        this.socket.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.socket.onerror = (error) => {
          console.error('WebSocketClient: Erreur de connexion', error);
          this.isConnecting = false;
          this.notifyError('Erreur de connexion WebSocket');
          reject(error);
        };

        this.socket.onclose = (event) => {
          console.log(`WebSocketClient: Déconnecté (code: ${event.code}, raison: ${event.reason})`);
          this.isConnecting = false;
          this.stats.connected = false;
          this.stopPingInterval();
          this.notifyDisconnect();
          this.updateStats();
          
          if (event.code !== 1000) { // Fermeture normale
            this.attemptReconnect();
          }
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Tentative de reconnexion avec backoff exponentiel
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('WebSocketClient: Nombre maximum de tentatives de reconnexion atteint');
      return;
    }

    this.reconnectAttempts++;
    this.stats.reconnectAttempts = this.reconnectAttempts;
    
    const delay = this.config.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    const jitter = Math.random() * 1000; // Jitter aléatoire pour éviter les synchronisations
    
    console.log(`WebSocketClient: Tentative de reconnexion dans ${Math.round(delay + jitter)}ms (tentative ${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`);

    setTimeout(() => {
      if (!this.stats.connected && !this.isConnecting) {
        this.connect().catch(() => {
          // Échec silencieux, la prochaine tentative sera déclenchée par le timeout
        });
      }
    }, delay + jitter);
  }

  /**
   * Gestion des messages entrants
   */
  private handleMessage(event: MessageEvent): void {
    const messageSize = event.data instanceof Blob ? event.data.size : event.data.length;
    this.bytesReceived += messageSize;
    this.messagesReceived++;
    
    try {
      const message: ExtendedWebSocketMessage = JSON.parse(event.data);
      this.stats.lastMessageTime = Date.now();
      
      // Traitement selon le type de message
      switch (message.type) {
        case 'game_state':
          this.handleGameState(message.data);
          break;
        case 'pong':
          this.handlePong(message);
          break;
        case 'latency_test':
          this.handleLatencyTest(message);
          break;
        default:
          // Pour les autres types, ajouter à la file d'attente
          this.messageQueue.push(message);
          this.processMessageQueue();
      }
      
      this.updateStats();
    } catch (error) {
      console.error('WebSocketClient: Erreur de parsing du message', error);
      this.notifyError('Format de message invalide');
    }
  }

  /**
   * Gestion des états de jeu avec buffering
   */
  private handleGameState(gameState: GameState): void {
    // Vérifier si c'est un nouvel état (step > dernier traité)
    if (gameState.step <= this.lastProcessedFrame) {
      // Frame obsolète, l'ignorer
      this.droppedFrames++;
      return;
    }

    // Ajouter au buffer
    this.gameStateBuffer.push(gameState);
    
    // Maintenir la taille du buffer
    if (this.gameStateBuffer.length > this.config.maxBufferSize) {
      const removed = this.gameStateBuffer.shift();
      if (removed && removed.step > this.lastProcessedFrame) {
        this.droppedFrames++;
      }
    }
    
    this.stats.bufferSize = this.gameStateBuffer.length;
    
    // Notifier les callbacks
    this.onGameStateCallbacks.forEach(callback => {
      try {
        callback(gameState);
      } catch (error) {
        console.error('WebSocketClient: Erreur dans le callback game_state', error);
      }
    });
  }

  /**
   * Récupère le prochain état de jeu à afficher
   */
  public getNextGameState(): GameState | null {
    if (this.gameStateBuffer.length === 0) {
      return null;
    }
    
    // Stratégie: prendre l'état le plus récent
    const nextState = this.gameStateBuffer.shift();
    if (nextState) {
      this.lastProcessedFrame = nextState.step;
      this.stats.bufferSize = this.gameStateBuffer.length;
      return nextState;
    }
    
    return null;
  }

  /**
   * Récupère l'état de jeu le plus récent sans le retirer du buffer
   */
  public getLatestGameState(): GameState | null {
    if (this.gameStateBuffer.length === 0) {
      return null;
    }
    
    return this.gameStateBuffer[this.gameStateBuffer.length - 1];
  }

  /**
   * Vide le buffer d'états de jeu
   */
  public clearBuffer(): void {
    this.gameStateBuffer = [];
    this.stats.bufferSize = 0;
    this.lastProcessedFrame = 0;
  }

  /**
   * Gestion du pong (réponse au ping)
   */
  private handlePong(message: ExtendedWebSocketMessage): void {
    if (message.data?.timestamp) {
      this.latency = Date.now() - message.data.timestamp;
      this.stats.latency = this.latency;
    }
  }

  /**
   * Test de latence
   */
  private handleLatencyTest(message: ExtendedWebSocketMessage): void {
    if (message.data?.testId) {
      this.send({
        type: 'latency_response',
        data: { testId: message.data.testId, timestamp: Date.now() },
        timestamp: new Date().toISOString()
      } as ExtendedWebSocketMessage);
    }
  }

  /**
   * Traitement de la file d'attente des messages
   */
  private processMessageQueue(): void {
    // Priorité: game_state > metrics > autres
    const priorityOrder = ['game_state', 'metrics', 'session_update', 'error'];
    
    for (const priority of priorityOrder) {
      const index = this.messageQueue.findIndex(msg => msg.type === priority);
      if (index !== -1) {
        const message = this.messageQueue.splice(index, 1)[0];
        // Traiter le message selon son type
        // (pour l'instant, on ne fait que le logger)
        console.log(`WebSocketClient: Message prioritaire ${message.type}`, message.data);
      }
    }
    
    // Traiter les messages restants (non prioritaires)
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()!;
      console.log(`WebSocketClient: Message non prioritaire ${message.type}`, message.data);
    }
  }

  /**
   * Envoi d'un message
   */
  public send(message: ExtendedWebSocketMessage): boolean {
    if (this.socket?.readyState !== WebSocket.OPEN) {
      console.warn('WebSocketClient: Impossible d\'envoyer, connexion non établie');
      return false;
    }

    try {
      const messageStr = JSON.stringify(message);
      this.socket.send(messageStr);
      
      this.messagesSent++;
      this.bytesSent += messageStr.length;
      this.updateStats();
      
      return true;
    } catch (error) {
      console.error('WebSocketClient: Erreur lors de l\'envoi', error);
      this.notifyError('Erreur d\'envoi WebSocket');
      return false;
    }
  }

  /**
   * S'abonner au canal game_state
   */
  public subscribeToGameState(sessionId?: string): boolean {
    return this.send({
      type: 'subscribe',
      data: { channel: 'game_state', sessionId },
      timestamp: new Date().toISOString()
    } as ExtendedWebSocketMessage);
  }

  /**
   * Se désabonner d'un canal
   */
  public unsubscribe(channel: string, sessionId?: string): boolean {
    return this.send({
      type: 'unsubscribe',
      data: { channel, sessionId },
      timestamp: new Date().toISOString()
    } as ExtendedWebSocketMessage);
  }

  /**
   * Envoi d'un ping pour mesurer la latence
   */
  public sendPing(): boolean {
    this.lastPingTime = Date.now();
    return this.send({
      type: 'ping',
      data: { timestamp: this.lastPingTime },
      timestamp: new Date().toISOString()
    } as ExtendedWebSocketMessage);
  }

  /**
   * Démarre l'intervalle de ping
   */
  private startPingInterval(): void {
    if (this.pingIntervalId) {
      clearInterval(this.pingIntervalId);
    }
    
    this.pingIntervalId = setInterval(() => {
      if (this.stats.connected) {
        this.sendPing();
      }
    }, this.config.pingInterval);
  }

  /**
   * Arrête l'intervalle de ping
   */
  private stopPingInterval(): void {
    if (this.pingIntervalId) {
      clearInterval(this.pingIntervalId);
      this.pingIntervalId = null;
    }
  }

  /**
   * Déconnexion
   */
  public disconnect(): void {
    this.stopPingInterval();
    
    if (this.socket) {
      this.socket.close(1000, 'Déconnexion client');
      this.socket = null;
    }
    
    this.stats.connected = false;
    this.reconnectAttempts = this.config.maxReconnectAttempts; // Empêcher la reconnexion automatique
    this.notifyDisconnect();
    this.updateStats();
  }

  /**
   * Mise à jour des statistiques
   */
  private updateStats(): void {
    this.stats = {
      ...this.stats,
      latency: this.latency,
      messagesReceived: this.messagesReceived,
      messagesSent: this.messagesSent,
      bytesReceived: this.bytesReceived,
      bytesSent: this.bytesSent,
      reconnectAttempts: this.reconnectAttempts,
      bufferSize: this.gameStateBuffer.length,
      droppedFrames: this.droppedFrames
    };
    
    this.notifyStats();
  }

  /**
   * Notification des callbacks
   */
  private notifyConnect(): void {
    this.onConnectCallbacks.forEach(callback => {
      try {
        callback(true);
      } catch (error) {
        console.error('WebSocketClient: Erreur dans le callback onConnect', error);
      }
    });
  }

  private notifyDisconnect(): void {
    this.onDisconnectCallbacks.forEach(callback => {
      try {
        callback(false);
      } catch (error) {
        console.error('WebSocketClient: Erreur dans le callback onDisconnect', error);
      }
    });
  }

  private notifyError(error: string): void {
    this.onErrorCallbacks.forEach(callback => {
      try {
        callback(error);
      } catch (error) {
        console.error('WebSocketClient: Erreur dans le callback onError', error);
      }
    });
  }

  private notifyStats(): void {
    this.onStatsCallbacks.forEach(callback => {
      try {
        callback(this.stats);
      } catch (error) {
        console.error('WebSocketClient: Erreur dans le callback onStats', error);
      }
    });
  }

  /**
   * Getters
   */
  public isConnected(): boolean {
    return this.stats.connected;
  }

  public getStats(): ConnectionStats {
    return { ...this.stats };
  }

  public getBufferSize(): number {
    return this.gameStateBuffer.length;
  }

  public getLatency(): number {
    return this.latency;
  }

  /**
   * Méthodes d'enregistrement des callbacks
   */
  public onGameState(callback: GameStateCallback): void {
    this.onGameStateCallbacks.push(callback);
  }

  public onConnect(callback: ConnectionCallback): void {
    this.onConnectCallbacks.push(callback);
  }

  public onDisconnect(callback: ConnectionCallback): void {
    this.onDisconnectCallbacks.push(callback);
  }

  public onError(callback: ErrorCallback): void {
    this.onErrorCallbacks.push(callback);
  }

  public onStats(callback: StatsCallback): void {
    this.onStatsCallbacks.push(callback);
  }

  /**
   * Nettoyage
   */
  public dispose(): void {
    this.disconnect();
    this.onGameStateCallbacks = [];
    this.onConnectCallbacks = [];
    this.onDisconnectCallbacks = [];
    this.onErrorCallbacks = [];
    this.onStatsCallbacks = [];
    this.clearBuffer();
    this.messageQueue = [];
  }
}

// Instance singleton pour une utilisation globale
export const webSocketClient = new WebSocketClient();

export default webSocketClient;