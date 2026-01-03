"""
Package des environnements Pac‑Man pour le laboratoire IA.
"""

from .duel_env import PacManDuelEnv
from .configurable_env import PacManConfigurableEnv
from .multiagent_env import PacManMultiAgentEnv

__all__ = [
    "PacManDuelEnv",
    "PacManConfigurableEnv",
    "PacManMultiAgentEnv",
]