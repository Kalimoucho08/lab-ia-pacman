"""
Service d'entraînement RL avec Stable-Baselines3.

Gère l'entraînement asynchrone de Pac-Man et des fantômes,
avec callbacks pour les métriques temps réel et sauvegarde des modèles.
"""
import asyncio
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor

try:
    import stable_baselines3 as sb3
    from stable_baselines3.common.callbacks import BaseCallback
    from stable_baselines3.common.vec_env import DummyVecEnv
    SB3_AVAILABLE = True
except ImportError:
    logging.warning("Stable-Baselines3 non disponible. L'entraînement RL ne fonctionnera pas.")
    sb3 = None
    BaseCallback = object
    DummyVecEnv = None
    SB3_AVAILABLE = False

from backend.config import AllParameters
from backend.models.experiment import Session, TrainingMetrics
from backend.services.environment_service import environment_service
from backend.services.websocket_service import websocket_manager

logger = logging.getLogger(__name__)

class TrainingCallback(BaseCallback):
    """Callback personnalisé pour collecter les métriques et les envoyer via WebSocket."""
    
    def __init__(self, session_id: str, websocket_manager, verbose=0):
        super().__init__(verbose)
        self.session_id = session_id
        self.websocket_manager = websocket_manager
        self.episode_rewards = []
        self.episode_lengths = []
        self.current_episode = 0
    
    def _on_step(self) -> bool:
        """Appelé à chaque step de l'environnement."""
        return True
    
    def _on_rollout_end(self) -> None:
        """Appelé à la fin de chaque rollout."""
        # Récupérer les métriques depuis le modèle
        if hasattr(self.model, 'logger'):
            for key, value in self.model.logger.name_to_value.items():
                if 'reward' in key.lower():
                    self.episode_rewards.append(value)
        
        # Envoyer les métriques via WebSocket
        metrics_data = {
            "session_id": self.session_id,
            "episode": self.current_episode,
            "reward": self.episode_rewards[-1] if self.episode_rewards else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        asyncio.run_coroutine_threadsafe(
            self.websocket_manager.broadcast_metrics(metrics_data),
            asyncio.get_event_loop()
        )
        
        self.current_episode += 1
    
    def _on_training_end(self) -> None:
        """Appelé à la fin de l'entraînement."""
        logger.info(f"Entraînement terminé pour la session {self.session_id}")

class TrainingService:
    """Service pour l'entraînement RL asynchrone."""
    
    def __init__(self, max_workers: int = 2):
        """Initialise le service avec un pool de threads pour l'entraînement."""
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_trainings: Dict[str, threading.Thread] = {}
        self.training_results: Dict[str, Any] = {}
        
        # Vérifier la disponibilité de Stable-Baselines3
        if not SB3_AVAILABLE:
            logger.warning("Stable-Baselines3 n'est pas disponible. "
                          "L'entraînement RL sera simulé.")
    
    def train_pacman(self, session: Session, parameters: AllParameters, 
                    callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Entraîne Pac-Man avec l'algorithme spécifié."""
        logger.info(f"Début de l'entraînement de Pac-Man pour la session {session.id}")
        
        # Créer l'environnement
        env = environment_service.create_configurable_env(parameters.game)
        if env is None:
            return {"success": False, "error": "Impossible de créer l'environnement"}
        
        # Envelopper pour Stable-Baselines3
        if SB3_AVAILABLE:
            vec_env = DummyVecEnv([lambda: env])
            
            # Sélectionner l'algorithme
            algorithm_class = getattr(sb3, session.algorithm_pacman, sb3.DQN)
            
            # Configurer les hyperparamètres
            model_kwargs = {
                "learning_rate": parameters.training.learning_rate,
                "gamma": parameters.training.gamma,
                "buffer_size": parameters.training.buffer_size,
                "batch_size": parameters.training.batch_size,
                "exploration_fraction": 0.1,
                "exploration_final_eps": parameters.intelligence.exploration_rate,
                "target_update_interval": parameters.intelligence.target_update,
                "learning_starts": parameters.intelligence.learning_starts,
                "train_freq": parameters.intelligence.train_freq,
                "verbose": 1
            }
            
            # Créer le modèle
            model = algorithm_class("MlpPolicy", vec_env, **model_kwargs)
            
            # Callback personnalisé
            training_callback = TrainingCallback(
                session_id=session.id,
                websocket_manager=websocket_manager
            )
            
            # Entraînement
            try:
                model.learn(
                    total_timesteps=parameters.training.episodes * 200,  # Estimation
                    callback=training_callback,
                    log_interval=10
                )
                
                # Sauvegarder le modèle
                model_path = self._save_model(model, session, "pacman")
                
                return {
                    "success": True,
                    "model_path": model_path,
                    "episodes": parameters.training.episodes,
                    "final_reward": training_callback.episode_rewards[-1] if training_callback.episode_rewards else 0
                }
                
            except Exception as e:
                logger.error(f"Erreur lors de l'entraînement de Pac-Man: {e}")
                return {"success": False, "error": str(e)}
        else:
            # Simulation d'entraînement (pour le développement)
            logger.warning("Stable-Baselines3 non disponible, simulation de l'entraînement")
            time.sleep(2)  # Simulation
            return {
                "success": True,
                "model_path": f"logs/models/pacman_simulated_{session.id}.zip",
                "episodes": 10,
                "final_reward": 100.0
            }
    
    def train_ghosts(self, session: Session, parameters: AllParameters,
                    ghost_indices: List[int] = None) -> Dict[str, Any]:
        """Entraîne les fantômes avec l'algorithme spécifié."""
        logger.info(f"Début de l'entraînement des fantômes pour la session {session.id}")
        
        if ghost_indices is None:
            ghost_indices = list(range(parameters.game.num_ghosts))
        
        results = {}
        for ghost_idx in ghost_indices:
            # Créer un environnement multi-agent avec wrapper single-agent
            env = environment_service.create_multiagent_env(parameters.game)
            if env is None:
                results[ghost_idx] = {"success": False, "error": "Environnement non disponible"}
                continue
            
            wrapper = environment_service.create_single_agent_wrapper(
                env, f"ghost_{ghost_idx}"
            )
            if wrapper is None:
                results[ghost_idx] = {"success": False, "error": "Wrapper non disponible"}
                continue
            
            if SB3_AVAILABLE:
                vec_env = DummyVecEnv([lambda: wrapper])
                algorithm_class = getattr(sb3, session.algorithm_ghosts, sb3.DQN)
                
                model_kwargs = {
                    "learning_rate": parameters.training.learning_rate,
                    "gamma": parameters.training.gamma,
                    "buffer_size": parameters.training.buffer_size,
                    "batch_size": parameters.training.batch_size,
                    "verbose": 1
                }
                
                model = algorithm_class("MlpPolicy", vec_env, **model_kwargs)
                
                try:
                    model.learn(total_timesteps=parameters.training.episodes * 100)
                    model_path = self._save_model(model, session, f"ghost_{ghost_idx}")
                    results[ghost_idx] = {
                        "success": True,
                        "model_path": model_path
                    }
                except Exception as e:
                    logger.error(f"Erreur lors de l'entraînement du fantôme {ghost_idx}: {e}")
                    results[ghost_idx] = {"success": False, "error": str(e)}
            else:
                # Simulation
                time.sleep(1)
                results[ghost_idx] = {
                    "success": True,
                    "model_path": f"logs/models/ghost_{ghost_idx}_simulated_{session.id}.zip"
                }
        
        return results
    
    def start_training_async(self, session: Session, parameters: AllParameters) -> str:
        """Démarre l'entraînement asynchrone dans un thread séparé."""
        training_id = f"training_{session.id}_{int(time.time())}"
        
        def training_task():
            """Tâche d'entraînement exécutée dans un thread."""
            try:
                # Notifier le début
                asyncio.run_coroutine_threadsafe(
                    websocket_manager.broadcast_session_update({
                        "session_id": session.id,
                        "status": "running",
                        "message": "Début de l'entraînement"
                    }),
                    asyncio.get_event_loop()
                )
                
                # Entraîner Pac-Man
                pacman_result = self.train_pacman(session, parameters)
                
                # Entraîner les fantômes (si configuré)
                ghosts_result = self.train_ghosts(session, parameters)
                
                # Stocker les résultats
                self.training_results[training_id] = {
                    "pacman": pacman_result,
                    "ghosts": ghosts_result,
                    "completed_at": datetime.now().isoformat()
                }
                
                # Notifier la fin
                asyncio.run_coroutine_threadsafe(
                    websocket_manager.broadcast_session_update({
                        "session_id": session.id,
                        "status": "completed",
                        "message": "Entraînement terminé",
                        "results": {
                            "pacman_success": pacman_result.get("success", False),
                            "ghosts_success": all(r.get("success", False) for r in ghosts_result.values())
                        }
                    }),
                    asyncio.get_event_loop()
                )
                
                logger.info(f"Entraînement {training_id} terminé avec succès")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'entraînement {training_id}: {e}")
                asyncio.run_coroutine_threadsafe(
                    websocket_manager.broadcast_session_update({
                        "session_id": session.id,
                        "status": "error",
                        "message": f"Erreur: {str(e)}"
                    }),
                    asyncio.get_event_loop()
                )
        
        # Démarrer le thread d'entraînement
        thread = threading.Thread(target=training_task, name=f"Training-{training_id}")
        thread.daemon = True
        thread.start()
        
        self.active_trainings[training_id] = thread
        
        logger.info(f"Entraînement asynchrone démarré: {training_id}")
        return training_id
    
    def stop_training(self, training_id: str) -> bool:
        """Arrête un entraînement en cours."""
        if training_id in self.active_trainings:
            # Dans une implémentation réelle, on interromprait le modèle
            # Pour l'instant, on marque simplement comme arrêté
            del self.active_trainings[training_id]
            logger.info(f"Entraînement {training_id} arrêté")
            return True
        return False
    
    def get_training_status(self, training_id: str) -> Dict[str, Any]:
        """Récupère le statut d'un entraînement."""
        if training_id in self.active_trainings:
            thread = self.active_trainings[training_id]
            return {
                "status": "running",
                "thread_alive": thread.is_alive(),
                "training_id": training_id
            }
        elif training_id in self.training_results:
            return {
                "status": "completed",
                "results": self.training_results[training_id]
            }
        else:
            return {"status": "unknown", "training_id": training_id}
    
    def _save_model(self, model, session: Session, agent_type: str) -> str:
        """Sauvegarde un modèle entraîné dans le dossier logs/."""
        models_dir = Path("logs/models")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{agent_type}_{session.algorithm_pacman}_{session.id}_{timestamp}.zip"
        model_path = models_dir / filename
        
        if hasattr(model, 'save'):
            model.save(str(model_path))
            logger.info(f"Modèle sauvegardé: {model_path}")
        else:
            # Créer un fichier factice pour la simulation
            with open(model_path, 'w') as f:
                f.write(f"Simulated model for {agent_type}")
        
        return str(model_path)
    
    def cleanup(self):
        """Nettoie les ressources du service."""
        self.executor.shutdown(wait=False)
        logger.info("Service d'entraînement nettoyé")

# Instance singleton du service
training_service = TrainingService()