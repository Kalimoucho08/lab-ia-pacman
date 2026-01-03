"""
Visualisation de l'environnement multi‑agent avec power pellets.
Permet de charger des modèles pour Pac‑Man et/ou les fantômes.
"""
import sys
sys.path.insert(0, '.')

import pygame
import numpy as np
import argparse
from src.pacman_env.multiagent_env import PacManMultiAgentEnv
from stable_baselines3 import DQN, PPO, A2C, SAC, TD3
import time


# Couleurs
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 120, 255)
PINK = (255, 182, 193)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)

GHOST_COLORS = [RED, PINK, CYAN, ORANGE]


def load_model(algorithm, path, env):
    """Charge un modèle Stable‑Baselines3."""
    if algorithm == "DQN":
        return DQN.load(path, env=env)
    elif algorithm == "PPO":
        return PPO.load(path, env=env)
    elif algorithm == "A2C":
        return A2C.load(path, env=env)
    elif algorithm == "SAC":
        return SAC.load(path, env=env)
    elif algorithm == "TD3":
        return TD3.load(path, env=env)
    else:
        raise ValueError(f"Algorithme inconnu: {algorithm}")


def main():
    parser = argparse.ArgumentParser(description="Visualisation multi‑agent Pac‑Man")
    parser.add_argument("--size", type=int, default=10, help="Taille de la grille")
    parser.add_argument("--num_ghosts", type=int, default=2, help="Nombre de fantômes")
    parser.add_argument("--num_dots", type=int, default=None, help="Nombre de points (None = remplissage)")
    parser.add_argument("--num_walls", type=int, default=0, help="Nombre de murs aléatoires")
    parser.add_argument("--lives", type=int, default=3, help="Vies de Pac‑Man")
    parser.add_argument("--fps", type=int, default=10, help="Images par seconde")
    parser.add_argument("--power_duration", type=int, default=10, help="Durée des power pellets")
    parser.add_argument("--num_power", type=int, default=2, help="Nombre de power pellets")
    parser.add_argument("--pacman_model", type=str, default=None, help="Chemin du modèle pour Pac‑Man")
    parser.add_argument("--ghost_model", type=str, default=None, help="Chemin du modèle pour les fantômes")
    parser.add_argument("--pacman_algorithm", default="DQN", help="Algorithme du modèle Pac‑Man")
    parser.add_argument("--ghost_algorithm", default="PPO", help="Algorithme du modèle fantômes")
    args = parser.parse_args()

    # Générer des murs aléatoires
    walls = []
    if args.num_walls > 0:
        import random
        possible = [(r, c) for r in range(args.size) for c in range(args.size)
                    if (r, c) != (1, 1)]  # éviter Pac‑Man
        walls = random.sample(possible, min(args.num_walls, len(possible)))

    # Créer l'environnement
    env = PacManMultiAgentEnv(
        size=args.size,
        walls=walls,
        num_ghosts=args.num_ghosts,
        num_dots=args.num_dots,
        num_power=args.num_power,
        power_duration=args.power_duration,
        reward_structure={
            "pacman": {"dot": 10.0, "ghost_vulnerable": 50.0, "death": -100.0, "step": -0.1},
            "ghost": {"eat_pacman": 100.0, "avoid_pacman": -20.0, "step": -0.1}
        }
    )

    # Charger les modèles si fournis
    pacman_model = None
    ghost_model = None
    if args.pacman_model:
        print(f"Chargement du modèle Pac‑Man depuis {args.pacman_model}")
        # Créer un environnement factice pour le chargement (non utilisé)
        from stable_baselines3.common.env_util import make_vec_env
        dummy_env = make_vec_env(lambda: env, n_envs=1)
        pacman_model = load_model(args.pacman_algorithm, args.pacman_model, dummy_env)
    if args.ghost_model:
        print(f"Chargement du modèle fantômes depuis {args.ghost_model}")
        dummy_env = make_vec_env(lambda: env, n_envs=1)
        ghost_model = load_model(args.ghost_algorithm, args.ghost_model, dummy_env)

    # Initialisation Pygame
    pygame.init()
    cell_size = 40
    width = args.size * cell_size
    height = args.size * cell_size
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Pac‑Man Multi‑Agent avec Power Pellets")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    # Boucle principale
    obs_dict, _ = env.reset()
    running = True
    total_rewards = {agent: 0.0 for agent in env.possible_agents}
    steps = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    obs_dict, _ = env.reset()
                    total_rewards = {agent: 0.0 for agent in env.possible_agents}
                    steps = 0
                    print("Environnement réinitialisé.")

        # Déterminer les actions
        actions = {}
        for agent in env.possible_agents:
            if agent == "pacman":
                if pacman_model:
                    # Utiliser le modèle pour Pac‑Man
                    action, _ = pacman_model.predict(obs_dict[agent], deterministic=True)
                    actions[agent] = action
                else:
                    # Contrôle manuel avec les flèches
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_UP]:
                        actions[agent] = 0
                    elif keys[pygame.K_RIGHT]:
                        actions[agent] = 1
                    elif keys[pygame.K_DOWN]:
                        actions[agent] = 2
                    elif keys[pygame.K_LEFT]:
                        actions[agent] = 3
                    else:
                        actions[agent] = 4  # ne rien faire
            else:  # fantôme
                if ghost_model:
                    # Utiliser le même modèle pour tous les fantômes (partage de poids)
                    action, _ = ghost_model.predict(obs_dict[agent], deterministic=True)
                    actions[agent] = action
                else:
                    # Comportement aléatoire
                    actions[agent] = env.action_space(agent).sample()

        # Exécuter l'étape
        obs_dict, rewards, terminations, truncations, infos = env.step(actions)
        for agent in env.possible_agents:
            total_rewards[agent] += rewards[agent]
        steps += 1

        # Vérifier si l'épisode est terminé
        if any(terminations.values()) or any(truncations.values()):
            print(f"Épisode terminé après {steps} steps.")
            print("Récompenses totales:", total_rewards)
            time.sleep(1)
            obs_dict, _ = env.reset()
            total_rewards = {agent: 0.0 for agent in env.possible_agents}
            steps = 0

        # Rendu
        screen.fill(BLACK)
        # Dessiner la grille
        for r in range(args.size):
            for c in range(args.size):
                rect = pygame.Rect(c * cell_size, r * cell_size, cell_size, cell_size)
                pygame.draw.rect(screen, WHITE, rect, 1)
        # Dessiner les murs
        for (r, c) in walls:
            pygame.draw.rect(screen, (100, 100, 100),
                             (c * cell_size, r * cell_size, cell_size, cell_size))
        # Dessiner les points
        grid = env.grid
        for r in range(args.size):
            for c in range(args.size):
                if grid[r, c] == 1:  # point
                    pygame.draw.circle(screen, WHITE,
                                       (c * cell_size + cell_size // 2, r * cell_size + cell_size // 2),
                                       3)
                elif grid[r, c] == 2:  # power pellet
                    pygame.draw.circle(screen, GREEN,
                                       (c * cell_size + cell_size // 2, r * cell_size + cell_size // 2),
                                       6)
        # Dessiner Pac‑Man
        pacman_pos = env.pacman_position
        pygame.draw.circle(screen, YELLOW,
                           (pacman_pos[1] * cell_size + cell_size // 2,
                            pacman_pos[0] * cell_size + cell_size // 2),
                           cell_size // 2 - 2)
        # Dessiner les fantômes
        for idx, ghost_pos in enumerate(env.ghost_positions):
            color = GHOST_COLORS[idx % len(GHOST_COLORS)]
            if env.vulnerable_ghosts[idx]:
                color = BLUE  # fantôme vulnérable
            pygame.draw.circle(screen, color,
                               (ghost_pos[1] * cell_size + cell_size // 2,
                                ghost_pos[0] * cell_size + cell_size // 2),
                               cell_size // 2 - 2)
        # Afficher les statistiques
        stats = f"Steps: {steps} | Pac‑Man reward: {total_rewards.get('pacman', 0):.1f}"
        if env.power_active:
            stats += f" | Power: {env.power_timer}"
        text = font.render(stats, True, WHITE)
        screen.blit(text, (10, 10))
        # Afficher les vies
        lives_text = font.render(f"Vies: {env.lives}", True, WHITE)
        screen.blit(lives_text, (width - 100, 10))

        pygame.display.flip()
        clock.tick(args.fps)

    pygame.quit()
    env.close()


if __name__ == "__main__":
    main()