"""
Application FastAPI principale pour le système d'expérimentation IA Pac-Man.

Fournit une API REST pour configurer, lancer et suivre les expériences
d'entraînement RL, ainsi qu'un serveur WebSocket pour les mises à jour
temps réel.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.api.v1.endpoints import experiments, training, environment, visualization
from backend.services.websocket_service import WebSocketManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log', encoding='cp1252'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Gestionnaire de WebSocket global
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    # Démarrage
    logger.info("Démarrage de l'application FastAPI")
    # Initialiser les services
    # ...
    yield
    # Arrêt
    logger.info("Arrêt de l'application FastAPI")
    await websocket_manager.disconnect_all()

# Création de l'application FastAPI
app = FastAPI(
    title="Laboratoire Scientifique IA Pac-Man",
    description="API backend pour le système d'expérimentation RL Pac-Man",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routeurs
app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["experiments"])
app.include_router(training.router, prefix="/api/v1/training", tags=["training"])
app.include_router(environment.router, prefix="/api/v1/environment", tags=["environment"])
app.include_router(visualization.router, prefix="/api/v1/visualization", tags=["visualization"])

@app.get("/")
async def root():
    """Endpoint racine pour vérifier que l'API fonctionne."""
    return {
        "message": "Bienvenue dans le Laboratoire Scientifique IA Pac-Man",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "experiments": "/api/v1/experiments",
            "training": "/api/v1/training",
            "environment": "/api/v1/environment",
            "visualization": "/api/v1/visualization"
        }
    }

@app.get("/health")
async def health_check():
    """Endpoint de santé pour les vérifications de l'infrastructure."""
    return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket pour les mises à jour temps réel."""
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Traitement des messages entrants (abonnements, etc.)
            await websocket_manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}")
        websocket_manager.disconnect(websocket)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Gestionnaire global d'exceptions."""
    logger.error(f"Exception non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur interne est survenue", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )