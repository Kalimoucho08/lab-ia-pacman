#!/usr/bin/env python3
"""Test rapide de l'environnement multi‑agent parallèle."""
import sys
sys.path.insert(0, '.')
from src.pacman_env.multiagent_env import PacManMultiAgentEnv

def test_env():
    env = PacManMultiAgentEnv(size=8, num_ghosts=2, power_pellets=2, ghost_behavior='random')
    print("Agents:", env.agents)
    obs, info = env.reset()
    print("Observation shape pour pacman:", obs["pacman"].shape)
    
    # Jouer quelques steps
    for step in range(5):
        print(f"\n--- Step {step} ---")
        actions = {agent: env.action_spaces[agent].sample() for agent in env.agents}
        print("Actions:", actions)
        obs, rewards, terminations, truncations, infos = env.step(actions)
        print("Rewards:", rewards)
        print("Terminations:", terminations)
        print("Truncations:", truncations)
        print("Grille:")
        print(env.render(mode='ansi'))
        if any(terminations.values()) or any(truncations.values()):
            print("Épisode terminé.")
            break
    print("Test terminé.")

if __name__ == "__main__":
    test_env()