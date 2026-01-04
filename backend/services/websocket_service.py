"""
Service de gestion des connexions WebSocket pour la communication temps réel.

Gère les connexions clients, les abonnements aux canaux,
et la diffusion des mises à jour (métriques, état du jeu, statuts).
"""
import asyncio
import json
import logging
from typing import Dict, List, Set, Any
from datetime import datetime

from fastapi import WebSocket

from backend.models.experiment import WebSocketMessage

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Gestionnaire des connexions WebSocket."""
    
    def __init__(self):
        """Initialise le gestionnaire avec des collections vides."""
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, Set[WebSocket]] = {
            "metrics": set(),
            "game_state": set(),
            "session_updates": set(),
            "experiment_updates": set(),
            "errors": set()
        }
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accepte une nouvelle connexion WebSocket."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = {
            "connected_at": datetime.now(),
            "subscriptions": set(),
            "last_activity": datetime.now()
        }
        logger.info(f"Nouvelle connexion WebSocket (total: {len(self.active_connections)})")
    
    def disconnect(self, websocket: WebSocket):
        """Déconnecte un client WebSocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Retirer de tous les abonnements
        for channel in self.subscriptions.values():
            if websocket in channel:
                channel.remove(websocket)
        
        if websocket in self.connection_info:
            del self.connection_info[websocket]
        
        logger.info(f"Connexion WebSocket fermée (restantes: {len(self.active_connections)})")
    
    async def disconnect_all(self):
        """Déconnecte tous les clients WebSocket."""
        for websocket in self.active_connections.copy():
            await websocket.close()
        self.active_connections.clear()
        self.subscriptions.clear()
        self.connection_info.clear()
        logger.info("Toutes les connexions WebSocket ont été fermées")
    
    async def subscribe(self, websocket: WebSocket, channel: str):
        """Abonne un client à un canal spécifique."""
        if channel not in self.subscriptions:
            logger.warning(f"Tentative d'abonnement à un canal inconnu: {channel}")
            return False
        
        self.subscriptions[channel].add(websocket)
        if websocket in self.connection_info:
            self.connection_info[websocket]["subscriptions"].add(channel)
        
        logger.debug(f"Client abonné au canal {channel}")
        return True
    
    async def unsubscribe(self, websocket: WebSocket, channel: str):
        """Désabonne un client d'un canal spécifique."""
        if channel in self.subscriptions and websocket in self.subscriptions[channel]:
            self.subscriptions[channel].remove(websocket)
            if websocket in self.connection_info:
                self.connection_info[websocket]["subscriptions"].discard(channel)
            logger.debug(f"Client désabonné du canal {channel}")
            return True
        return False
    
    async def handle_message(self, websocket: WebSocket, data: Dict[str, Any]):
        """Traite un message reçu d'un client WebSocket."""
        if websocket not in self.connection_info:
            return
        
        # Mettre à jour la dernière activité
        self.connection_info[websocket]["last_activity"] = datetime.now()
        
        message_type = data.get("type", "")
        
        if message_type == "subscribe":
            channel = data.get("channel", "")
            if channel:
                await self.subscribe(websocket, channel)
                await self.send_personal_message({
                    "type": "subscription_confirmed",
                    "channel": channel,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
        
        elif message_type == "unsubscribe":
            channel = data.get("channel", "")
            if channel:
                await self.unsubscribe(websocket, channel)
                await self.send_personal_message({
                    "type": "unsubscription_confirmed",
                    "channel": channel,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
        
        elif message_type == "ping":
            await self.send_personal_message({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }, websocket)
        
        else:
            logger.debug(f"Message WebSocket non traité: {message_type}")
    
    async def send_personal_message(self, data: Dict[str, Any], websocket: WebSocket):
        """Envoie un message à un client spécifique."""
        try:
            message = WebSocketMessage(
                type=data.get("type", "message"),
                data=data,
                timestamp=datetime.now()
            )
            await websocket.send_json(message.dict())
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi d'un message personnel: {e}")
    
    async def broadcast(self, data: Dict[str, Any]):
        """Diffuse un message à tous les clients connectés."""
        message = WebSocketMessage(
            type=data.get("type", "broadcast"),
            data=data,
            timestamp=datetime.now()
        )
        
        disconnected = []
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message.dict())
            except Exception as e:
                logger.error(f"Erreur lors de la diffusion à un client: {e}")
                disconnected.append(websocket)
        
        # Nettoyer les connexions défaillantes
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_to_channel(self, channel: str, data: Dict[str, Any]):
        """Diffuse un message aux clients abonnés à un canal spécifique."""
        if channel not in self.subscriptions:
            logger.warning(f"Tentative de diffusion sur un canal inconnu: {channel}")
            return
        
        message = WebSocketMessage(
            type=data.get("type", channel),
            data=data,
            timestamp=datetime.now()
        )
        
        disconnected = []
        for websocket in self.subscriptions[channel].copy():
            try:
                await websocket.send_json(message.dict())
            except Exception as e:
                logger.error(f"Erreur lors de la diffusion sur le canal {channel}: {e}")
                disconnected.append(websocket)
        
        # Nettoyer les connexions défaillantes
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_metrics(self, metrics_data: Dict[str, Any]):
        """Diffuse des métriques d'entraînement aux clients abonnés."""
        await self.broadcast_to_channel("metrics", {
            "type": "metrics_update",
            "data": metrics_data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_game_state(self, game_state: Dict[str, Any]):
        """Diffuse l'état du jeu aux clients abonnés."""
        await self.broadcast_to_channel("game_state", {
            "type": "game_state",
            "data": game_state,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_session_update(self, session_data: Dict[str, Any]):
        """Diffuse une mise à jour de session aux clients abonnés."""
        await self.broadcast_to_channel("session_updates", {
            "type": "session_update",
            "data": session_data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_experiment_update(self, experiment_data: Dict[str, Any]):
        """Diffuse une mise à jour d'expérience aux clients abonnés."""
        await self.broadcast_to_channel("experiment_updates", {
            "type": "experiment_update",
            "data": experiment_data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_error(self, error_data: Dict[str, Any]):
        """Diffuse une erreur aux clients abonnés."""
        await self.broadcast_to_channel("errors", {
            "type": "error",
            "data": error_data,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur les connexions WebSocket."""
        return {
            "total_connections": len(self.active_connections),
            "subscriptions": {
                channel: len(subscribers) 
                for channel, subscribers in self.subscriptions.items()
            },
            "connection_info": {
                "oldest": min(
                    (info["connected_at"] for info in self.connection_info.values()),
                    default=None
                ),
                "newest": max(
                    (info["connected_at"] for info in self.connection_info.values()),
                    default=None
                )
            }
        }

# Instance singleton du gestionnaire
websocket_manager = WebSocketManager()