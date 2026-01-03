"""
Exemple d'entraînement de Pac‑Man dans l'environnement multi‑agent avec power pellets.
Utilise un wrapper single‑agent pour isoler Pac‑Man (les fantômes ont un comportement aléatoire).
"""
import sys
sys.path.insert(0, '.')

from src.pacman_env.multiagent_env import PacManMultiAgentEnv
from src.pacman_env.multiagent_wrappers import SingleAgentWrapper
from stable_baselines3 import DQN, PPO, A2C, SAC, TD3
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
import numpy as np
import argparse


def train_pacman(algorithm="DQN", total_timesteps=10000, power_duration=10, num_power=2):
    """
    Entraîne Pac‑Man avec l'algorithme choisi.
    """
    # Créer l'environnement multi‑agent
    env = PacManMultiAgentEnv(
        size=10,
        walls=[],
        num_ghosts=2,
        num_dots=None,
        num_power=num_power,
        power_duration=power_duration,
        reward_structure={
            "pacman": {"dot": 10.0, "ghost_vulnerable": 50.0, "death": -100.0, "step": -0.1},
            "ghost": {"eat_pacman": 100.0, "avoid_pacman": -20.0, "step": -0.1}
        }
    )
    # Wrapper pour isoler Pac‑Man
    pacman_env = SingleAgentWrapper(env, agent_id="pacman", other_agent_policy="random")
    pacman_env = Monitor(pacman_env)
    pacman_env = DummyVecEnv([lambda: pacman_env])

    # Sélection de l'algorithme
    if algorithm == "DQN":
        model = DQN("MlpPolicy", pacman_env, verbose=1, tensorboard_log="./logs/")
    elif algorithm == "PPO":
        model = PPO("MlpPolicy", pacman_env, verbose=1, tensorboard_log="./logs/")
    elif algorithm == "A2C":
        model = A2C("MlpPolicy", pacman_env, verbose=1, tensorboard_log="./logs/")
    elif algorithm == "SAC":
        model = SAC("MlpPolicy", pacman_env, verbose=1, tensorboard_log="./logs/")
    elif algorithm == "TD3":
        model = TD3("MlpPolicy", pacman_env, verbose=1, tensorboard_log="./logs/")
    else:
        raise ValueError(f"Algorithme inconnu: {algorithm}")

    print(f"Entraînement de Pac‑Man avec {algorithm} sur {total_timesteps} timesteps...")
    model.learn(total_timesteps=total_timesteps)
    model.save(f"logs/pacman_{algorithm}_multiagent")
    print(f"Modèle sauvegardé dans logs/pacman_{algorithm}_multiagent.zip")

    # Test du modèle
    print("Test du modèle entraîné...")
    obs = pacman_env.reset()
    total_reward = 0.0
    for _ in range(200):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, info = pacman_env.step(action)
        total_reward += reward[0]
        if done:
            break
    print(f"Reward total pendant le test: {total_reward}")
    pacman_env.close()
    env.close()


def train_ghosts(algorithm="PPO", total_timesteps=10000, power_duration=10, num_power=2):
    """
    Entraîne les fantômes (un seul modèle partagé) avec l'algorithme choisi.
    """
    env = PacManMultiAgentEnv(
        size=10,
        walls=[],
        num_ghosts=2,
        num_dots=None,
        num_power=num_power,
        power_duration=power_duration,
        reward_structure={
            "pacman": {"dot": 10.0, "ghost_vulnerable": 50.0, "death": -100.0, "step": -0.1},
            "ghost": {"eat_pacman": 100.0, "avoid_pacman": -20.0, "step": -0.1}
        }
    )
    # On entraîne le premier fantôme (ghost_0) et on partage les poids avec les autres
    ghost_env = SingleAgentWrapper(env, agent_id="ghost_0", other_agent_policy="random")
    ghost_env = Monitor(ghost_env)
    ghost_env = DummyVecEnv([lambda: ghost_env])

    if algorithm == "DQN":
        model = DQN("MlpPolicy", ghost_env, verbose=1, tensorboard_log="./logs/")
    elif algorithm == "PPO":
        model = PPO("MlpPolicy", ghost_env, verbose=1, tensorboard_log="./logs/")
    elif algorithm == "A2C":
        model = A2C("MlpPolicy", ghost_env, verbose=1, tensorboard_log="./logs/")
    elif algorithm == "SAC":
        model = SAC("MlpPolicy", ghost_env, verbose=1, tensorboard_log="./logs/")
    elif algorithm == "TD3":
        model = TD3("MlpPolicy", ghost_env, verbose=1, tensorboard_log="./logs/")
    else:
        raise ValueError(f"Algorithme inconnu: {algorithm}")

    print(f"Entraînement des fantômes avec {algorithm} sur {total_timesteps} timesteps...")
    model.learn(total_timesteps=total_timesteps)
    model.save(f"logs/ghosts_{algorithm}_multiagent")
    print(f"Modèle sauvegardé dans logs/ghosts_{algorithm}_multiagent.zip")

    # Test
    obs = ghost_env.reset()
    total_reward = 0.0
    for _ in range(200):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, info = ghost_env.step(action)
        total_reward += reward[0]
        if done:
            break
    print(f"Reward total pendant le test: {total_reward}")
    ghost_env.close()
    env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entraînement multi‑agent Pac‑Man")
    parser.add_argument("--agent", choices=["pacman", "ghosts"], default="pacman", help="Agent à entraîner")
    parser.add_argument("--algorithm", choices=["DQN", "PPO", "A2C", "SAC", "TD3"], default="DQN", help="Algorithme RL")
    parser.add_argument("--timesteps", type=int, default=10000, help="Nombre total de timesteps")
    parser.add_argument("--power_duration", type=int, default=10, help="Durée des power pellets")
    parser.add_argument("--num_power", type=int, default=2, help="Nombre de power pellets")
    args = parser.parse_args()

    if args.agent == "pacman":
        train_pacman(algorithm=args.algorithm, total_timesteps=args.timesteps,
                     power_duration=args.power_duration, num_power=args.num_power)
    else:
        train_ghosts(algorithm=args.algorithm, total_timesteps=args.timesteps,
                     power_duration=args.power_duration, num_power=args.num_power)