"""
Environnement Pac‑Man multi‑agent avec power pellets, basé sur PettingZoo ParallelEnv.
Supporte un agent Pac‑Man et N agents fantômes (contrôlables par RL).
Gestion des power pellets avec durée d'effet configurable.
"""
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Union
from pettingzoo import ParallelEnv


class PacManMultiAgentEnv(ParallelEnv):
    """Environnement Pac‑Man multi‑agent pour le laboratoire IA.

    Paramètres :
    ------------
    size : int
        Taille de la grille (size x size). Par défaut 10.
    walls : List[Tuple[int, int]]
        Liste des positions des murs (bloquants).
    num_ghosts : int
        Nombre de fantômes (1‑4). Par défaut 2.
    num_dots : int
        Nombre de points à collecter. Si None, remplissage par défaut.
    ghost_start_positions : List[Tuple[int, int]]
        Positions initiales des fantômes. Si None, positions aléatoires.
    pacman_start_position : Tuple[int, int]
        Position initiale de Pac‑Man. Par défaut (1,1).
    lives : int
        Nombre de vies de Pac‑Man. Par défaut 3.
    max_steps : int
        Nombre maximal de steps par épisode. Par défaut 200.
    ghost_behavior : str
        Comportement des fantômes si non contrôlés par RL : 'random', 'chase', 'scatter'.
    power_pellets : int
        Nombre de power pellets à placer aléatoirement. Par défaut 2.
    power_duration : int
        Durée d'effet d'un power pellet (en steps). Par défaut 10.
    reward_config : Dict[str, Dict[str, float]]
        Récompenses configurables par agent.
        Exemple :
        {
            "pacman": {"dot": 10.0, "ghost_eaten": 50.0, "death": -100.0, "step": -0.1},
            "ghost": {"eat_pacman": 100.0, "eaten": -50.0, "step": -0.1}
        }
    """
    metadata = {'render_modes': ['human', 'ansi', 'rgb_array'], 'render_fps': 10}

    def __init__(self,
                 size: int = 10,
                 walls: Optional[List[Tuple[int, int]]] = None,
                 num_ghosts: int = 2,
                 num_dots: Optional[int] = None,
                 ghost_start_positions: Optional[List[Tuple[int, int]]] = None,
                 pacman_start_position: Tuple[int, int] = (1, 1),
                 lives: int = 3,
                 max_steps: int = 200,
                 ghost_behavior: str = 'random',
                 power_pellets: int = 2,
                 power_duration: int = 10,
                 reward_config: Optional[Dict[str, Dict[str, float]]] = None):
        super().__init__()

        self.size = size
        self.walls = walls if walls is not None else []
        self.num_ghosts = num_ghosts
        self.num_dots = num_dots
        self.ghost_start_positions = ghost_start_positions
        self.pacman_start_position = pacman_start_position
        self.lives = lives
        self.max_steps = max_steps
        self.ghost_behavior = ghost_behavior
        self.power_pellets = power_pellets
        self.power_duration = power_duration

        # Récompenses par défaut
        self.reward_config = reward_config or {
            "pacman": {
                "dot": 10.0,
                "ghost_eaten": 50.0,
                "death": -100.0,
                "step": -0.1,
                "power_pellet_eaten": 20.0
            },
            "ghost": {
                "eat_pacman": 100.0,
                "eaten": -50.0,
                "step": -0.1,
                "distance_reward": 0.0  # peut être positif pour fuir, négatif pour approcher
            }
        }

        # Vérifications
        assert 1 <= self.num_ghosts <= 4, "num_ghosts doit être entre 1 et 4"
        assert 0 <= self.lives <= 10, "lives doit être entre 0 et 10"
        assert self.size >= 5, "size doit être au moins 5"
        assert 0 <= self.power_pellets <= 4, "power_pellets doit être entre 0 et 4"
        assert 1 <= self.power_duration <= 50, "power_duration doit être entre 1 et 50"
        for (r, c) in self.walls:
            assert 0 <= r < self.size and 0 <= c < self.size, f"Mur hors grille: ({r},{c})"

        # Définir les agents
        self.agents = ["pacman"] + [f"ghost_{i}" for i in range(self.num_ghosts)]
        self.possible_agents = self.agents[:]
        self.agent_name_mapping = {name: idx for idx, name in enumerate(self.agents)}

        # Espaces d'action (discret 4 directions pour tous)
        self.action_spaces = {agent: spaces.Discrete(4) for agent in self.agents}
        # Espaces d'observation (identique pour tous : grille size x size x canaux)
        # Canaux : Pac‑Man, fantômes, points, murs, power pellets, état vulnérable
        obs_shape = (self.size, self.size, 6)
        self.observation_spaces = {
            agent: spaces.Box(low=0, high=1, shape=obs_shape, dtype=np.float32)
            for agent in self.agents
        }

        # État interne (sera initialisé dans reset)
        self.pacman_pos = None
        self.ghost_positions = None
        self.dots = None
        self.power_pellet_positions = None
        self.power_active = False
        self.power_timer = 0
        self.current_step = 0
        self.current_lives = None
        self.vulnerable_ghosts = set()  # indices des fantômes vulnérables

    def _initialize_grid(self):
        """Initialise la grille avec murs, points, power pellets et positions des agents."""
        # Réinitialiser les structures
        self.dots = np.ones((self.size, self.size), dtype=np.int8)
        for (r, c) in self.walls:
            self.dots[r, c] = -1  # -1 signifie mur

        # Positionner Pac‑Man
        pr, pc = self.pacman_pos
        if self.dots[pr, pc] == -1:
            raise ValueError("Position de Pac‑Man sur un mur")
        self.dots[pr, pc] = 0

        # Positionner les fantômes
        if self.ghost_start_positions is None:
            self.ghost_start_positions = []
            for _ in range(self.num_ghosts):
                while True:
                    r = np.random.randint(0, self.size)
                    c = np.random.randint(0, self.size)
                    if (r, c) != (pr, pc) and (r, c) not in self.walls and (r, c) not in self.ghost_start_positions:
                        self.ghost_start_positions.append((r, c))
                        break
        else:
            if len(self.ghost_start_positions) != self.num_ghosts:
                raise ValueError("Le nombre de positions fournies ne correspond pas à num_ghosts")
            for (r, c) in self.ghost_start_positions:
                if (r, c) in self.walls:
                    raise ValueError(f"Fantôme placé sur un mur: ({r},{c})")

        self.ghost_positions = list(self.ghost_start_positions)
        for (r, c) in self.ghost_positions:
            self.dots[r, c] = 0

        # Ajuster le nombre de points si spécifié
        if self.num_dots is not None:
            total_cells = self.size * self.size
            occupied = len(self.walls) + 1 + self.num_ghosts + self.power_pellets
            max_dots = total_cells - occupied
            if self.num_dots > max_dots:
                raise ValueError(f"Trop de points demandés (max {max_dots})")
            # Réinitialiser les points
            self.dots = np.ones((self.size, self.size), dtype=np.int8)
            for (r, c) in self.walls:
                self.dots[r, c] = -1
            for (r, c) in [self.pacman_pos] + self.ghost_positions:
                self.dots[r, c] = 0
            # Placer aléatoirement les points
            available = np.argwhere(self.dots == 1)
            chosen = available[np.random.choice(len(available), self.num_dots, replace=False)]
            self.dots[:, :] = 0
            for (r, c) in chosen:
                self.dots[r, c] = 1
            for (r, c) in self.walls:
                self.dots[r, c] = -1
            for (r, c) in [self.pacman_pos] + self.ghost_positions:
                self.dots[r, c] = 0

        # Placer les power pellets
        self.power_pellet_positions = []
        if self.power_pellets > 0:
            available = [(r, c) for r in range(self.size) for c in range(self.size)
                         if self.dots[r, c] == 1 and (r, c) not in self.walls]
            if len(available) < self.power_pellets:
                raise ValueError("Pas assez de cases libres pour placer les power pellets")
            chosen = np.random.choice(len(available), self.power_pellets, replace=False)
            for idx in chosen:
                r, c = available[idx]
                self.power_pellet_positions.append((r, c))
                self.dots[r, c] = 2  # 2 = power pellet

        # Réinitialiser l'état des power pellets
        self.power_active = False
        self.power_timer = 0
        self.vulnerable_ghosts.clear()

    def reset(self, seed=None, options=None):
        """Réinitialise l'environnement à l'état initial."""
        if seed is not None:
            np.random.seed(seed)
        self.pacman_pos = list(self.pacman_start_position)
        self.ghost_positions = list(self.ghost_start_positions) if self.ghost_start_positions else []
        self.current_step = 0
        self.current_lives = self.lives
        self._initialize_grid()

        # Retourner les observations pour tous les agents
        observations = {agent: self._get_obs(agent) for agent in self.agents}
        infos = {agent: {} for agent in self.agents}
        return observations, infos

    def step(self, actions):
        """Exécute les actions pour tous les agents en parallèle."""
        # Si un agent n'a pas d'action (terminé/truncated), on l'ignore
        rewards = {agent: 0.0 for agent in self.agents}
        terminations = {agent: False for agent in self.agents}
        truncations = {agent: False for agent in self.agents}
        infos = {agent: {} for agent in self.agents}

        # Déplacer Pac‑Man
        if "pacman" in actions:
            rewards["pacman"] += self._move_pacman(actions["pacman"])

        # Déplacer les fantômes
        for agent, action in actions.items():
            if agent.startswith("ghost_"):
                ghost_idx = int(agent.split("_")[1])
                rewards[agent] += self._move_ghost(ghost_idx, action)

        # Avancer le timer des power pellets
        self._global_step()

        # Vérifier les collisions après tous les déplacements
        self._check_collisions(rewards)

        # Vérifier les conditions de fin d'épisode
        self._check_episode_end(terminations, truncations)

        # Incrémenter le step
        self.current_step += 1

        # Remplir les infos
        for agent in self.agents:
            infos[agent] = {
                "step": self.current_step,
                "lives": self.current_lives,
                "power_active": self.power_active,
                "power_timer": self.power_timer
            }

        # Observations pour le prochain step
        observations = {agent: self._get_obs(agent) for agent in self.agents}
        return observations, rewards, terminations, truncations, infos

    def _move_pacman(self, action):
        """Déplace Pac‑Man et retourne la récompense obtenue."""
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        dr, dc = moves[action]
        new_pr = self.pacman_pos[0] + dr
        new_pc = self.pacman_pos[1] + dc

        reward = self.reward_config["pacman"]["step"]

        # Vérifier les limites et murs
        if 0 <= new_pr < self.size and 0 <= new_pc < self.size and (new_pr, new_pc) not in self.walls:
            self.pacman_pos = [new_pr, new_pc]
        else:
            # Collision avec mur/bord : reste sur place
            return reward

        # Collecter un point
        cell_value = self.dots[tuple(self.pacman_pos)]
        if cell_value == 1:  # point normal
            reward += self.reward_config["pacman"]["dot"]
            self.dots[tuple(self.pacman_pos)] = 0
        elif cell_value == 2:  # power pellet
            reward += self.reward_config["pacman"]["power_pellet_eaten"]
            self.dots[tuple(self.pacman_pos)] = 0
            self.power_active = True
            self.power_timer = self.power_duration
            self.vulnerable_ghosts = set(range(self.num_ghosts))
            # Retirer de la liste des power pellets
            if tuple(self.pacman_pos) in self.power_pellet_positions:
                self.power_pellet_positions.remove(tuple(self.pacman_pos))

        return reward

    def _move_ghost(self, ghost_idx, action):
        """Déplace un fantôme et retourne la récompense obtenue."""
        # Si le fantôme est contrôlé par RL, utiliser l'action fournie.
        # Sinon, ignorer l'action et utiliser le comportement par défaut.
        if self.ghost_behavior != "rl":
            self._move_ghost_auto(ghost_idx)
            return self.reward_config["ghost"]["step"]
        
        # RL : déplacer selon l'action
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        dr, dc = moves[action]
        gr, gc = self.ghost_positions[ghost_idx]
        new_gr = gr + dr
        new_gc = gc + dc

        reward = self.reward_config["ghost"]["step"]

        # Vérifier les limites et murs
        if 0 <= new_gr < self.size and 0 <= new_gc < self.size and (new_gr, new_gc) not in self.walls:
            self.ghost_positions[ghost_idx] = (new_gr, new_gc)
        else:
            # Collision avec mur/bord : reste sur place
            return reward

        # La collision avec Pac‑Man sera gérée dans _check_collisions
        return reward

    def _move_ghost_auto(self, ghost_idx):
        """Déplace un fantôme selon le comportement prédéfini (random, chase, scatter)."""
        gr, gc = self.ghost_positions[ghost_idx]
        if self.ghost_behavior == 'random':
            possible_moves = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = gr + dr, gc + dc
                if 0 <= nr < self.size and 0 <= nc < self.size and (nr, nc) not in self.walls:
                    possible_moves.append((nr, nc))
            if possible_moves:
                self.ghost_positions[ghost_idx] = possible_moves[np.random.randint(len(possible_moves))]
        elif self.ghost_behavior == 'chase':
            pr, pc = self.pacman_pos
            best_move = None
            best_dist = float('inf')
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = gr + dr, gc + dc
                if 0 <= nr < self.size and 0 <= nc < self.size and (nr, nc) not in self.walls:
                    dist = abs(nr - pr) + abs(nc - pc)
                    if dist < best_dist:
                        best_dist = dist
                        best_move = (nr, nc)
            if best_move:
                self.ghost_positions[ghost_idx] = best_move
        elif self.ghost_behavior == 'scatter':
            # Dispersion vers les coins (simplifié)
            corners = [(0, 0), (0, self.size-1), (self.size-1, 0), (self.size-1, self.size-1)]
            target = corners[ghost_idx % len(corners)]
            best_move = None
            best_dist = float('inf')
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = gr + dr, gc + dc
                if 0 <= nr < self.size and 0 <= nc < self.size and (nr, nc) not in self.walls:
                    dist = abs(nr - target[0]) + abs(nc - target[1])
                    if dist < best_dist:
                        best_dist = dist
                        best_move = (nr, nc)
            if best_move:
                self.ghost_positions[ghost_idx] = best_move

    def _global_step(self):
        """Avance le timer des power pellets."""
        if self.power_active:
            self.power_timer -= 1
            if self.power_timer <= 0:
                self.power_active = False
                self.vulnerable_ghosts.clear()

    def _check_collisions(self, rewards):
        """Vérifie les collisions entre Pac‑Man et les fantômes, met à jour les récompenses."""
        for idx, (gr, gc) in enumerate(self.ghost_positions):
            if (gr, gc) == tuple(self.pacman_pos):
                if idx in self.vulnerable_ghosts:
                    # Pac‑Man mange le fantôme vulnérable
                    rewards["pacman"] += self.reward_config["pacman"]["ghost_eaten"]
                    rewards[f"ghost_{idx}"] += self.reward_config["ghost"]["eaten"]
                    # Respawn du fantôme
                    self._respawn_ghost(idx)
                else:
                    # Fantôme mange Pac‑Man
                    rewards[f"ghost_{idx}"] += self.reward_config["ghost"]["eat_pacman"]
                    rewards["pacman"] += self.reward_config["pacman"]["death"]
                    self.current_lives -= 1
                    if self.current_lives <= 0:
                        # Pac‑Man mort, terminaison plus tard
                        pass
                    else:
                        # Respawn Pac‑Man
                        self.pacman_pos = list(self.pacman_start_position)

    def _respawn_ghost(self, ghost_idx):
        """Replace un fantôme à une position aléatoire libre."""
        while True:
            r = np.random.randint(0, self.size)
            c = np.random.randint(0, self.size)
            if (r, c) not in self.walls and (r, c) != tuple(self.pacman_pos) and (r, c) not in self.ghost_positions:
                self.ghost_positions[ghost_idx] = (r, c)
                break

    def _check_episode_end(self, terminations, truncations):
        """Remplit terminations et truncations selon les conditions de fin."""
        # Truncation par max steps
        if self.current_step >= self.max_steps:
            for agent in self.agents:
                truncations[agent] = True
        # Terminaison si plus de points
        if np.sum(self.dots == 1) == 0 and len(self.power_pellet_positions) == 0:
            terminations["pacman"] = True
            for ghost in self.agents[1:]:
                terminations[ghost] = True
        # Terminaison si Pac‑Man mort
        if self.current_lives <= 0:
            terminations["pacman"] = True
            for ghost in self.agents[1:]:
                terminations[ghost] = True

    def _get_obs(self, agent):
        """Retourne l'observation pour un agent donné."""
        obs = np.zeros((self.size, self.size, 6), dtype=np.float32)
        # Canal 0 : Pac‑Man (visible pour tous)
        obs[self.pacman_pos[0], self.pacman_pos[1], 0] = 1.0
        # Canal 1 : fantômes (tous)
        for (r, c) in self.ghost_positions:
            obs[r, c, 1] = 1.0
        # Canal 2 : points normaux
        obs[:, :, 2] = (self.dots == 1).astype(np.float32)
        # Canal 3 : murs
        for (r, c) in self.walls:
            obs[r, c, 3] = 1.0
        # Canal 4 : power pellets
        for (r, c) in self.power_pellet_positions:
            obs[r, c, 4] = 1.0
        # Canal 5 : état vulnérable (1 si fantôme vulnérable à cette position)
        for idx in self.vulnerable_ghosts:
            r, c = self.ghost_positions[idx]
            obs[r, c, 5] = 1.0
        return obs

    def render(self, mode='human'):
        """Affiche la grille dans la console (mode 'ansi') ou retourne un array RGB."""
        if mode == 'ansi':
            grid = []
            for r in range(self.size):
                row = []
                for c in range(self.size):
                    if (r, c) in self.walls:
                        row.append('#')
                    elif (r, c) == tuple(self.pacman_pos):
                        row.append('P')
                    elif (r, c) in self.ghost_positions:
                        idx = self.ghost_positions.index((r, c))
                        if idx in self.vulnerable_ghosts:
                            row.append('V')
                        else:
                            row.append('G')
                    elif (r, c) in self.power_pellet_positions:
                        row.append('O')
                    elif self.dots[r, c] == 1:
                        row.append('.')
                    else:
                        row.append(' ')
                grid.append(''.join(row))
            output = '\n'.join(grid)
            output += f"\nStep: {self.current_step}, Lives: {self.current_lives}, Power active: {self.power_active}"
            return output
        elif mode == 'rgb_array':
            # À implémenter avec Pygame
            raise NotImplementedError("Le mode rgb_array sera implémenté avec Pygame")
        else:
            super().render(mode=mode)

    def close(self):
        pass