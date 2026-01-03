#!/usr/bin/env python3
"""Test rapide de l'environnement multi‑agent."""
import sys
sys.path.insert(0, '.')
from src.pacman_env.multiagent_env import PacManMultiAgentEnv

def test_env():
    env = PacManMultiAgentEnv(size=8, num_ghosts=2, power_pellets=2, ghost_behavior='random')
    print("Agents:", env.agents)
    obs = env.reset()
    print("Observation shape pour pacman:", obs["pacman"].shape)
    
    # Jouer quelques steps
    for step in range(5):
        print(f"\n--- Step {step} ---")
        for agent in env.agents:
            action = env.action_space(agent).sample()
            env.step(action)
            print(f"Agent {agent} a joué action {action}")
            if env.terminations[agent] or env.truncations[agent]:
                print(f"Agent {agent} terminé")
        print("Grille:")
        print(env.render(mode='ansi'))
        if all(env.terminations[agent] for agent in env.agents):
            break
    print("Test terminé.")

if __name__ == "__main__":
    test_env()