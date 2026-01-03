#!/usr/bin/env python3
"""
Visualisation graphique de Pac-Man avec Pygame, utilisant l'environnement configurable.
Affiche une fenêtre avec la grille, Pac-Man, plusieurs fantômes, points et murs.
Accepte des paramètres en ligne de commande pour personnaliser l'environnement.
Peut utiliser un modèle entraîné (Stable-Baselines3) ou un agent aléatoire.
"""
import pygame
import sys
import time
import argparse
import numpy as np
import random
from src.pacman_env.configurable_env import PacManConfigurableEnv
from src.agents.random_agent import RandomAgent

# Couleurs
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 120, 255)
GREEN = (0, 255, 0)
PURPLE = (180, 0, 255)
GRAY = (40, 40, 40)
WALL_COLOR = (80, 80, 80)

# Couleurs pour les fantômes (différentes)
GHOST_COLORS = [RED, BLUE, GREEN, PURPLE]

def draw_grid(screen, env, cell_size):
    """Dessine la grille, les points, Pac-Man, les fantômes et les murs."""
    screen.fill(BLACK)
    size = env.size
    
    # Dessiner les murs
    for (r, c) in env.walls:
        x1 = c * cell_size
        y1 = r * cell_size
        x2 = x1 + cell_size
        y2 = y1 + cell_size
        pygame.draw.rect(screen, WALL_COLOR, (x1, y1, cell_size, cell_size))
    
    # Dessiner les points
    for y in range(size):
        for x in range(size):
            if env.dots[y, x] == 1:
                center = (x * cell_size + cell_size // 2, y * cell_size + cell_size // 2)
                pygame.draw.circle(screen, WHITE, center, cell_size // 10)
    
    # Dessiner Pac-Man (cercle jaune)
    px, py = env.pacman_pos
    pac_rect = pygame.Rect(px * cell_size, py * cell_size, cell_size, cell_size)
    pygame.draw.circle(screen, YELLOW, pac_rect.center, cell_size // 2 - 5)
    
    # Dessiner les fantômes
    for i, (gx, gy) in enumerate(env.ghost_positions):
        ghost_rect = pygame.Rect(gx * cell_size, gy * cell_size, cell_size, cell_size)
        color = GHOST_COLORS[i % len(GHOST_COLORS)]
        pygame.draw.circle(screen, color, ghost_rect.center, cell_size // 2 - 5)
        # Yeux
        eye_offset = cell_size // 6
        pygame.draw.circle(screen, WHITE, (ghost_rect.centerx - eye_offset, ghost_rect.centery - eye_offset), cell_size // 8)
        pygame.draw.circle(screen, WHITE, (ghost_rect.centerx + eye_offset, ghost_rect.centery - eye_offset), cell_size // 8)
        pygame.draw.circle(screen, BLACK, (ghost_rect.centerx - eye_offset, ghost_rect.centery - eye_offset), cell_size // 16)
        pygame.draw.circle(screen, BLACK, (ghost_rect.centerx + eye_offset, ghost_rect.centery - eye_offset), cell_size // 16)
    
    # Dessiner la grille
    for x in range(size + 1):
        pygame.draw.line(screen, GRAY, (x * cell_size, 0), (x * cell_size, size * cell_size), 2)
    for y in range(size + 1):
        pygame.draw.line(screen, GRAY, (0, y * cell_size), (size * cell_size, y * cell_size), 2)
    
    # Afficher les informations
    font = pygame.font.SysFont(None, 24)
    info_text = f"Step: {env.current_step}  Lives: {env.current_lives}  Dots left: {np.sum(env.dots == 1)}"
    text_surface = font.render(info_text, True, WHITE)
    screen.blit(text_surface, (10, size * cell_size - 30))
    
    pygame.display.flip()

def generate_random_walls(size, num_walls, exclude_positions):
    """Génère une liste de positions de murs aléatoires, en évitant les positions exclues."""
    walls = []
    possible = [(r, c) for r in range(size) for c in range(size) if (r, c) not in exclude_positions]
    if num_walls > len(possible):
        num_walls = len(possible)
    chosen = random.sample(possible, num_walls)
    return chosen

def main():
    parser = argparse.ArgumentParser(description='Visualisation Pac-Man configurable')
    parser.add_argument('--size', type=int, default=10, help='Taille de la grille')
    parser.add_argument('--num_ghosts', type=int, default=1, help='Nombre de fantômes')
    parser.add_argument('--num_dots', type=int, default=None, help='Nombre de points (None pour remplissage)')
    parser.add_argument('--num_walls', type=int, default=0, help='Nombre de murs (placés aléatoirement)')
    parser.add_argument('--lives', type=int, default=3, help='Vies de Pac-Man')
    parser.add_argument('--ghost_behavior', type=str, default='random', choices=['random', 'chase', 'scatter'], help='Comportement des fantômes')
    parser.add_argument('--cell_size', type=int, default=60, help='Taille d\'une cellule en pixels')
    parser.add_argument('--fps', type=int, default=10, help='Images par seconde')
    parser.add_argument('--model_path', type=str, default=None, help='Chemin vers un modèle entraîné (ZIP)')
    args = parser.parse_args()
    
    # Générer les murs aléatoires
    walls = []
    if args.num_walls > 0:
        # Positions à exclure : Pac-Man start (1,1) et positions des fantômes (inconnues pour l'instant)
        # On génère les murs après création de l'environnement ? On va générer des murs qui évitent les positions initiales connues.
        # Pour simplifier, on génère d'abord les murs, puis on ajuste l'environnement.
        exclude = [(1, 1)]  # Pac-Man start
        # On ne connaît pas encore les positions des fantômes, donc on les exclura après.
        walls = generate_random_walls(args.size, args.num_walls, exclude)
    
    # Créer l'environnement configurable
    env = PacManConfigurableEnv(
        size=args.size,
        walls=walls,
        num_ghosts=args.num_ghosts,
        num_dots=args.num_dots,
        pacman_start_position=(1, 1),
        lives=args.lives,
        ghost_behavior=args.ghost_behavior
    )
    
    # Initialisation Pygame
    pygame.init()
    window_size = args.size * args.cell_size
    screen = pygame.display.set_mode((window_size, window_size))
    pygame.display.set_caption(f"Pac-Man Visualisation (size={args.size}, ghosts={args.num_ghosts}, dots={args.num_dots})")
    clock = pygame.time.Clock()
    
    # Charger le modèle ou utiliser un agent aléatoire
    if args.model_path:
        try:
            from stable_baselines3 import DQN, PPO
            # Détecter l'algorithme basé sur le nom du fichier ou utiliser DQN par défaut
            if "PPO" in args.model_path:
                model = PPO.load(args.model_path, env=env)
            else:
                model = DQN.load(args.model_path, env=env)
            print(f"Modèle chargé depuis {args.model_path}")
            use_model = True
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            print("Utilisation d'un agent aléatoire.")
            use_model = False
            agent = RandomAgent(action_space=env.action_space.n)
    else:
        use_model = False
        agent = RandomAgent(action_space=env.action_space.n)
    
    obs, _ = env.reset()
    
    running = True
    paused = False
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    obs, _ = env.reset()
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        if not paused:
            if use_model:
                action, _ = model.predict(obs, deterministic=True)
            else:
                action = agent.act(obs)
            obs, reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                print(f"Épisode terminé. Reward total: {reward}")
                obs, _ = env.reset()
        
        draw_grid(screen, env, args.cell_size)
        clock.tick(args.fps)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()