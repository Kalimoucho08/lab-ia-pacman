#!/usr/bin/env python3
"""
Visualisation graphique de Pac-Man avec Pygame.
Affiche une fenêtre avec la grille, Pac-Man (jaune), le fantôme (rouge) et les points (blancs).
"""
import pygame
import sys
import time
from src.pacman_env.duel_env import PacManDuelEnv
from src.agents.random_agent import RandomAgent

# Couleurs
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 120, 255)
GRAY = (40, 40, 40)

# Paramètres de la fenêtre
CELL_SIZE = 60
GRID_SIZE = 10
WINDOW_SIZE = CELL_SIZE * GRID_SIZE
FPS = 10

def draw_grid(screen, env):
    """Dessine la grille, les points, Pac-Man et le fantôme."""
    screen.fill(BLACK)
    
    # Dessiner les points
    for y in range(env.size):
        for x in range(env.size):
            if env.dots[y, x] == 1:
                center = (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2)
                pygame.draw.circle(screen, WHITE, center, CELL_SIZE // 10)
    
    # Dessiner Pac-Man (cercle jaune)
    px, py = env.pacman_pos
    pac_rect = pygame.Rect(px * CELL_SIZE, py * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.circle(screen, YELLOW, pac_rect.center, CELL_SIZE // 2 - 5)
    
    # Dessiner le fantôme (cercle rouge avec yeux)
    gx, gy = env.ghost_pos
    ghost_rect = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.circle(screen, RED, ghost_rect.center, CELL_SIZE // 2 - 5)
    # Yeux
    eye_offset = CELL_SIZE // 6
    pygame.draw.circle(screen, WHITE, (ghost_rect.centerx - eye_offset, ghost_rect.centery - eye_offset), CELL_SIZE // 8)
    pygame.draw.circle(screen, WHITE, (ghost_rect.centerx + eye_offset, ghost_rect.centery - eye_offset), CELL_SIZE // 8)
    pygame.draw.circle(screen, BLACK, (ghost_rect.centerx - eye_offset, ghost_rect.centery - eye_offset), CELL_SIZE // 16)
    pygame.draw.circle(screen, BLACK, (ghost_rect.centerx + eye_offset, ghost_rect.centery - eye_offset), CELL_SIZE // 16)
    
    # Dessiner la grille
    for x in range(GRID_SIZE + 1):
        pygame.draw.line(screen, GRAY, (x * CELL_SIZE, 0), (x * CELL_SIZE, WINDOW_SIZE), 2)
    for y in range(GRID_SIZE + 1):
        pygame.draw.line(screen, GRAY, (0, y * CELL_SIZE), (WINDOW_SIZE, y * CELL_SIZE), 2)
    
    # Afficher les informations
    font = pygame.font.SysFont(None, 24)
    dist = ((px - gx) ** 2 + (py - gy) ** 2) ** 0.5
    info_text = f"Step: {env.current_step}  Reward: {env._get_obs()[0]:.2f}  Distance: {dist:.1f}"
    text_surface = font.render(info_text, True, WHITE)
    screen.blit(text_surface, (10, WINDOW_SIZE - 30))
    
    pygame.display.flip()

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Pac-Man Visualisation")
    clock = pygame.time.Clock()
    
    env = PacManDuelEnv(size=GRID_SIZE)
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
            action = agent.act(obs)
            obs, reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                print(f"Épisode terminé. Reward total: {reward}")
                obs, _ = env.reset()
        
        draw_grid(screen, env)
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()