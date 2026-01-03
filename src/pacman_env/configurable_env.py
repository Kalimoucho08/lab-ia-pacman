"""
Environnement Pac-Man configurable avec murs, fantômes multiples, points, vies, etc.
Hérite de gymnasium.Env et permet une grande flexibilité pour le laboratoire IA.
"""
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import List, Tuple, Optional, Dict, Any


class PacManConfigurableEnv(gym.Env):
    """Environnement Pac-Man configurable pour le laboratoire IA.

    Paramètres :
    ------------
    size : int
        Taille de la grille (size x size). Par défaut 10.
    walls : List[Tuple[int, int]]
        Liste des positions des murs (bloquants). Chaque mur est un tuple (row, col).
    num_ghosts : int
        Nombre de fantômes (1-4). Par défaut 1.
    num_dots : int
        Nombre de points à collecter. Si None, remplissage par défaut (toutes les cases sauf Pac-Man et fantômes).
    ghost_start_positions : List[Tuple[int, int]]
        Positions initiales des fantômes. Si None, positions aléatoires (évitant Pac-Man).
    pacman_start_position : Tuple[int, int]
        Position initiale de Pac-Man. Par défaut (1,1).
    lives : int
        Nombre de vies de Pac-Man. Par défaut 3.
    max_steps : int
        Nombre maximal de steps par épisode. Par défaut 200.
    ghost_behavior : str
        Comportement des fantômes : 'random' (aléatoire), 'chase' (poursuite), 'scatter' (dispersion).
    reward_structure : Dict[str, float]
        Récompenses personnalisées : dot, ghost_caught, death, step.
    """
    metadata = {'render_modes': ['human', 'ansi', 'rgb_array'], 'render_fps': 10}

    def __init__(self,
                 size: int = 10,
                 walls: Optional[List[Tuple[int, int]]] = None,
                 num_ghosts: int = 1,
                 num_dots: Optional[int] = None,
                 ghost_start_positions: Optional[List[Tuple[int, int]]] = None,
                 pacman_start_position: Tuple[int, int] = (1, 1),
                 lives: int = 3,
                 max_steps: int = 200,
                 ghost_behavior: str = 'random',
                 reward_structure: Optional[Dict[str, float]] = None):
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
        self.reward_structure = reward_structure or {
            'dot': 10.0,
            'ghost_caught': -50.0,
            'death': -100.0,
            'step': -0.1
        }

        # Vérifications
        assert 1 <= self.num_ghosts <= 4, "num_ghosts doit être entre 1 et 4"
        assert 0 <= self.lives <= 10, "lives doit être entre 0 et 10"
        assert self.size >= 5, "size doit être au moins 5"
        for (r, c) in self.walls:
            assert 0 <= r < self.size and 0 <= c < self.size, f"Mur hors grille: ({r},{c})"

        # Espaces d'action et d'observation
        self.action_space = spaces.Discrete(4)  # HAUT, BAS, GAUCHE, DROITE
        # Observation : positions relatives, murs, points restants, vies, step
        obs_shape = (self.size, self.size, 4)  # canaux : Pac-Man, fantômes, points, murs
        self.observation_space = spaces.Box(low=0, high=1, shape=obs_shape, dtype=np.float32)

        # État interne
        self.pacman_pos = list(self.pacman_start_position)
        self.ghost_positions = []
        self.dots = np.ones((self.size, self.size), dtype=np.int8)  # 1 = point présent
        self.current_step = 0
        self.current_lives = self.lives
        self.done = False
        self.info = {}

        # Initialisation
        self._initialize_grid()

    def _initialize_grid(self):
        """Initialise la grille avec les murs, points, et positions des agents."""
        # Marquer les murs
        for (r, c) in self.walls:
            self.dots[r, c] = -1  # -1 signifie mur

        # Positionner Pac-Man
        pr, pc = self.pacman_pos
        if self.dots[pr, pc] == -1:
            raise ValueError("Position de Pac-Man sur un mur")
        self.dots[pr, pc] = 0  # pas de point à cette position

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
            occupied = len(self.walls) + 1 + self.num_ghosts  # murs + Pac-Man + fantômes
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

    def reset(self, seed=None, options=None):
        """Réinitialise l'environnement à l'état initial."""
        super().reset(seed=seed)
        self.pacman_pos = list(self.pacman_start_position)
        self.ghost_positions = list(self.ghost_start_positions)
        self.current_step = 0
        self.current_lives = self.lives
        self.done = False
        self.info = {}
        self._initialize_grid()
        obs = self._get_obs()
        return obs, self.info

    def step(self, action):
        """Exécute une action (0: HAUT, 1: BAS, 2: GAUCHE, 3: DROITE)."""
        if self.done:
            raise RuntimeError("L'épisode est terminé, veuillez appeler reset()")

        reward = self.reward_structure['step']
        terminated = False
        truncated = False

        # Déplacer Pac-Man
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        dr, dc = moves[action]
        new_pr = self.pacman_pos[0] + dr
        new_pc = self.pacman_pos[1] + dc

        # Vérifier les limites et murs
        if 0 <= new_pr < self.size and 0 <= new_pc < self.size and (new_pr, new_pc) not in self.walls:
            self.pacman_pos = [new_pr, new_pc]
        # Sinon, Pac-Man reste sur place (collision avec mur/bord)

        # Collecter un point
        if self.dots[tuple(self.pacman_pos)] == 1:
            reward += self.reward_structure['dot']
            self.dots[tuple(self.pacman_pos)] = 0

        # Déplacer les fantômes
        self._move_ghosts()

        # Vérifier les collisions avec les fantômes
        for ghost_pos in self.ghost_positions:
            if tuple(self.pacman_pos) == ghost_pos:
                reward += self.reward_structure['ghost_caught']
                self.current_lives -= 1
                if self.current_lives <= 0:
                    reward += self.reward_structure['death']
                    terminated = True
                else:
                    # Respawn Pac-Man à sa position initiale
                    self.pacman_pos = list(self.pacman_start_position)
                break

        # Vérifier la fin de l'épisode
        self.current_step += 1
        if self.current_step >= self.max_steps:
            truncated = True
        if np.sum(self.dots == 1) == 0:  # plus de points
            terminated = True

        self.done = terminated or truncated
        obs = self._get_obs()
        self.info = {
            'lives': self.current_lives,
            'dots_left': np.sum(self.dots == 1),
            'step': self.current_step,
            'ghost_positions': self.ghost_positions.copy()
        }
        return obs, reward, terminated, truncated, self.info

    def _move_ghosts(self):
        """Déplace les fantômes selon leur comportement."""
        for i, (gr, gc) in enumerate(self.ghost_positions):
            if self.ghost_behavior == 'random':
                # Mouvement aléatoire (évite les murs)
                possible_moves = []
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = gr + dr, gc + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size and (nr, nc) not in self.walls:
                        possible_moves.append((nr, nc))
                if possible_moves:
                    self.ghost_positions[i] = possible_moves[np.random.randint(len(possible_moves))]
            elif self.ghost_behavior == 'chase':
                # Poursuite de Pac-Man (mouvement vers lui)
                pr, pc = self.pacman_pos
                best_move = None
                best_dist = float('inf')
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = gr + dr, gc + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size and (nr, nc) not in self.walls:
                        dist = abs(nr - pr) + abs(nc - pc)  # distance de Manhattan
                        if dist < best_dist:
                            best_dist = dist
                            best_move = (nr, nc)
                if best_move:
                    self.ghost_positions[i] = best_move
            else:
                # Par défaut, rester sur place
                pass

    def _get_obs(self):
        """Retourne l'observation sous forme de tensor (size, size, 4)."""
        obs = np.zeros((self.size, self.size, 4), dtype=np.float32)
        # Canal 0 : Pac-Man
        obs[self.pacman_pos[0], self.pacman_pos[1], 0] = 1.0
        # Canal 1 : fantômes
        for (r, c) in self.ghost_positions:
            obs[r, c, 1] = 1.0
        # Canal 2 : points
        obs[:, :, 2] = (self.dots == 1).astype(np.float32)
        # Canal 3 : murs
        for (r, c) in self.walls:
            obs[r, c, 3] = 1.0
        return obs

    def render(self, mode='human'):
        """Affiche la grille dans la console (mode 'ansi') ou retourne un array RGB (mode 'rgb_array')."""
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
                        row.append('G')
                    elif self.dots[r, c] == 1:
                        row.append('.')
                    else:
                        row.append(' ')
                grid.append(''.join(row))
            output = '\n'.join(grid)
            output += f"\nStep: {self.current_step}, Lives: {self.current_lives}, Dots left: {np.sum(self.dots == 1)}"
            return output
        elif mode == 'rgb_array':
            # Retourne un array RGB simple (pour visualisation future)
            raise NotImplementedError("Le mode rgb_array sera implémenté avec Pygame")
        else:
            super().render(mode=mode)

    def close(self):
        pass