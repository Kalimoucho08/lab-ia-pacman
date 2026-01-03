"""
Wrappers pour convertir l'environnement multi‑agent en environnement single‑agent
pour l'entraînement avec Stable‑Baselines3.
"""
import gymnasium as gym
import numpy as np
from gymnasium import spaces
from pettingzoo.utils.wrappers import BaseWrapper


class SingleAgentWrapper(gym.Env):
    """
    Wrapper qui isole un agent spécifique d'un environnement PettingZoo ParallelEnv.
    L'observation, l'action et la récompense sont celles de l'agent sélectionné.
    Les autres agents sont contrôlés par une politique fixe (par exemple aléatoire).
    """
    def __init__(self, env, agent_id, other_agent_policy="random"):
        """
        Args:
            env: instance de PacManMultiAgentEnv (ou autre ParallelEnv)
            agent_id: identifiant de l'agent à isoler (ex: "pacman", "ghost_0")
            other_agent_policy: politique des autres agents ("random", "chase", "scatter")
        """
        self.env = env
        self.agent_id = agent_id
        self.other_agent_policy = other_agent_policy
        # Espaces d'observation et d'action de l'agent cible
        self.observation_space = env.observation_space(agent_id)
        self.action_space = env.action_space(agent_id)
        # Garder une référence aux autres agents
        self.other_agents = [a for a in env.possible_agents if a != agent_id]
        self.metadata = env.metadata

    def reset(self, seed=None, options=None):
        obs_dict, info = self.env.reset(seed=seed, options=options)
        self._last_obs = obs_dict[self.agent_id]
        return self._last_obs, info

    def step(self, action):
        # Construire un dictionnaire d'actions pour tous les agents
        actions = {}
        actions[self.agent_id] = action
        for agent in self.other_agents:
            # Politique fixe pour les autres agents
            if self.other_agent_policy == "random":
                actions[agent] = self.env.action_space(agent).sample()
            elif self.other_agent_policy == "chase":
                # Implémentation simple: se déplacer vers Pac‑Man (si agent est fantôme)
                # Pour simplifier, on utilise random
                actions[agent] = self.env.action_space(agent).sample()
            else:
                actions[agent] = self.env.action_space(agent).sample()
        # Exécuter l'étape dans l'environnement parallèle
        obs_dict, rewards, terminations, truncations, infos = self.env.step(actions)
        # Extraire observation, récompense, terminaison pour l'agent cible
        obs = obs_dict[self.agent_id]
        reward = rewards[self.agent_id]
        terminated = terminations[self.agent_id]
        truncated = truncations[self.agent_id]
        info = infos.get(self.agent_id, {})
        self._last_obs = obs
        return obs, reward, terminated, truncated, info

    def render(self):
        return self.env.render()

    def close(self):
        self.env.close()


class MultiAgentToSingleAgent(BaseWrapper):
    """
    Wrapper PettingZoo qui convertit un environnement parallèle en environnement
    single‑agent en sélectionnant un agent et en fixant les autres.
    """
    def __init__(self, env, agent_id, other_agent_policy="random"):
        super().__init__(env)
        self.agent_id = agent_id
        self.other_agent_policy = other_agent_policy
        self.observation_space = env.observation_space(agent_id)
        self.action_space = env.action_space(agent_id)
        self.other_agents = [a for a in env.possible_agents if a != agent_id]

    def reset(self, seed=None, options=None):
        obs_dict, info = self.env.reset(seed=seed, options=options)
        return obs_dict[self.agent_id], info

    def step(self, action):
        actions = {self.agent_id: action}
        for agent in self.other_agents:
            if self.other_agent_policy == "random":
                actions[agent] = self.env.action_space(agent).sample()
            else:
                actions[agent] = self.env.action_space(agent).sample()
        obs_dict, rewards, terminations, truncations, infos = self.env.step(actions)
        obs = obs_dict[self.agent_id]
        reward = rewards[self.agent_id]
        terminated = terminations[self.agent_id]
        truncated = truncations[self.agent_id]
        info = infos.get(self.agent_id, {})
        return obs, reward, terminated, truncated, info


class MultiAgentTrainingEnv(gym.Env):
    """
    Environnement qui alterne entre les agents pour l'entraînement centralisé.
    (Approche simplifiée: on entraîne un agent à la fois)
    """
    def __init__(self, env, agent_ids):
        self.env = env
        self.agent_ids = agent_ids
        # On suppose que tous les agents ont les mêmes espaces (sinon adapter)
        self.observation_space = env.observation_space(agent_ids[0])
        self.action_space = env.action_space(agent_ids[0])
        self.current_agent_idx = 0

    def reset(self, seed=None, options=None):
        obs_dict, info = self.env.reset(seed=seed, options=options)
        self.current_agent_idx = 0
        agent = self.agent_ids[self.current_agent_idx]
        return obs_dict[agent], info

    def step(self, action):
        agent = self.agent_ids[self.current_agent_idx]
        actions = {a: self.env.action_space(a).sample() for a in self.env.possible_agents}
        actions[agent] = action
        obs_dict, rewards, terminations, truncations, infos = self.env.step(actions)
        obs = obs_dict[agent]
        reward = rewards[agent]
        terminated = terminations[agent]
        truncated = truncations[agent]
        # Passer à l'agent suivant (cyclique)
        self.current_agent_idx = (self.current_agent_idx + 1) % len(self.agent_ids)
        return obs, reward, terminated, truncated, infos.get(agent, {})

    def render(self):
        return self.env.render()

    def close(self):
        self.env.close()