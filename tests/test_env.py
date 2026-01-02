import pytest
import numpy as np
from src.pacman_env.duel_env import PacManDuelEnv
from src.agents.random_agent import RandomAgent


def test_duel_env_reset():
    """Teste la réinitialisation de PacManDuelEnv."""
    env = PacManDuelEnv(size=10)
    obs, info = env.reset()
    assert isinstance(obs, np.ndarray)
    assert obs.shape == (4,)
    assert info == {}
    # Vérifie que les valeurs sont dans [0,1]
    assert np.all(obs >= 0) and np.all(obs <= 1)


def test_duel_env_step():
    """Teste un step de PacManDuelEnv."""
    env = PacManDuelEnv(size=10)
    obs, _ = env.reset()
    action = 0  # up
    obs2, reward, terminated, truncated, info = env.step(action)
    assert isinstance(obs2, np.ndarray)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)
    # La récompense peut être négative ou positive
    assert True


def test_duel_env_observation_space():
    """Vérifie que l'observation space est correct."""
    env = PacManDuelEnv(size=10)
    obs, _ = env.reset()
    assert env.observation_space.contains(obs)


def test_duel_env_action_space():
    """Vérifie que l'action space est correct."""
    env = PacManDuelEnv(size=10)
    assert env.action_space.n == 4
    for action in range(4):
        env.reset()
        obs, reward, terminated, truncated, info = env.step(action)
        assert not np.isnan(reward)


def test_random_agent():
    """Teste l'agent aléatoire."""
    agent = RandomAgent(action_space=4)
    obs = np.zeros(4)
    action = agent.act(obs)
    assert isinstance(action, int)
    assert 0 <= action < 4
    # Test avec un dict observation
    obs_dict = {'pos': np.array([1,1])}
    action2 = agent.act(obs_dict)
    assert 0 <= action2 < 4


def test_random_agent_reset():
    """Teste la méthode reset de RandomAgent (ne fait rien)."""
    agent = RandomAgent(action_space=4)
    agent.reset()  # Ne devrait pas lever d'exception
    assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
