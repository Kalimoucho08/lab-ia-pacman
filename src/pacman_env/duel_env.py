import gymnasium as gym
from gymnasium import spaces
import numpy as np

class PacManDuelEnv(gym.Env):
    """Environnement Pac-Man simplifié multi-agent.
    
    Grille 10x10 avec Pac-Man et un fantôme.
    Pac-Man peut manger des points (dots) pour obtenir des récompenses.
    Le fantôme bouge en opposition à Pac-Man.
    Si Pac-Man est trop proche du fantôme, l'épisode se termine avec pénalité.
    """
    def __init__(self, size=10):
        super().__init__()
        self.size = size
        self.action_space = spaces.Discrete(4)  # HAUT BAS GAUCHE DROITE
        self.observation_space = spaces.Box(low=0, high=1, shape=(4,), dtype=np.float32)

        self.pacman_pos = [1, 1]
        self.ghost_pos = [8, 8]
        self.dots = np.ones((self.size, self.size))
        self.dots[self.pacman_pos[0], self.pacman_pos[1]] = 0
        self.dots[self.ghost_pos[0], self.ghost_pos[1]] = 0

        self.max_steps = 200
        self.current_step = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.pacman_pos = [1, 1]
        self.ghost_pos = [8, 8]
        self.dots = np.ones((self.size, self.size))
        self.dots[1, 1] = self.dots[8, 8] = 0
        self.current_step = 0
        obs = self._get_obs()
        return obs, {}

    def step(self, action):
        # PacMan bouge
        moves = [[-1, 0], [1, 0], [0, -1], [0, 1]]
        new_pac = np.array(self.pacman_pos) + moves[action]
        new_pac = np.clip(new_pac, 0, self.size - 1)
        self.pacman_pos = new_pac.tolist()

        # Ghost bouge opposé (simulé)
        opp_action = (action + 2) % 4
        new_ghost = np.array(self.ghost_pos) + moves[opp_action]
        new_ghost = np.clip(new_ghost, 0, self.size - 1)
        self.ghost_pos = new_ghost.tolist()

        # Reward
        reward = 0.0
        if self.dots[tuple(self.pacman_pos)] == 1:
            reward += 10.0
            self.dots[tuple(self.pacman_pos)] = 0

        dist = np.linalg.norm(np.array(self.pacman_pos) - np.array(self.ghost_pos))
        if dist < 1.5:
            reward -= 50.0
            terminated = True
        else:
            terminated = self.current_step >= self.max_steps

        truncated = False
        self.current_step += 1
        obs = self._get_obs()
        return obs, reward, terminated, truncated, {"dist": dist}

    def _get_obs(self):
        dist = np.linalg.norm(np.array(self.pacman_pos) - np.array(self.ghost_pos))
        dots_left = np.sum(self.dots)
        return np.array([dist / 10, dots_left / 100, self.current_step / 200, 1], dtype=np.float32)

    def render(self):
        """Affiche la grille dans la console."""
        grid = [['.' for _ in range(self.size)] for _ in range(self.size)]
        px, py = self.pacman_pos
        gx, gy = self.ghost_pos
        grid[py][px] = 'P'
        grid[gy][gx] = 'G'
        for y in range(self.size):
            for x in range(self.size):
                if self.dots[y, x] == 1:
                    grid[y][x] = '*'
        print('\n'.join(''.join(row) for row in grid))
        print(f"Step: {self.current_step}, Reward: {self._get_obs()[0]}")
        print()

    def close(self):
        pass