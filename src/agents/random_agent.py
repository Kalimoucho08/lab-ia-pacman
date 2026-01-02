import random
from typing import Any

class RandomAgent:
    """Agent qui choisit des actions aléatoires.
    
    Peut être utilisé avec n'importe quel environnement ayant un action_space discret.
    """
    def __init__(self, action_space: int = 4):
        self.action_space = action_space

    def act(self, observation: Any) -> int:
        """Retourne une action aléatoire indépendamment de l'observation."""
        return random.randint(0, self.action_space - 1)

    def reset(self):
        """Réinitialise l'agent (rien à faire pour random)."""
        pass
