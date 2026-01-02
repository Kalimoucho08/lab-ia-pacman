from src.pacman_env.duel_env import PacManDuelEnv
from src.agents.random_agent import RandomAgent


def main(steps: int = 200):
    env = PacManDuelEnv(size=10)
    agent = RandomAgent(action_space=env.action_space.n)
    obs, _ = env.reset()
    try:
        env.render()
    except Exception:
        pass
    total_reward = 0.0
    for t in range(steps):
        action = agent.act(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        try:
            env.render()
        except Exception:
            pass
        if terminated or truncated:
            print(f"Episode terminé en {t+1} steps, reward total: {total_reward:.1f}")
            break
    else:
        print(f"Terminé après {steps} steps, reward total: {total_reward:.1f}")


if __name__ == '__main__':
    main()
