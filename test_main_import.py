#!/usr/bin/env python3
"""
Test d'import du module main et création de l'environnement.
"""
import sys
import threading
import time

def test():
    try:
        # Import des modules nécessaires
        from src.pacman_env.duel_env import PacManDuelEnv
        from stable_baselines3 import DQN, PPO
        from stable_baselines3.common.monitor import Monitor
        from stable_baselines3.common.vec_env import DummyVecEnv
        import tkinter as tk
        print("[OK] Imports de base réussis")
        
        # Test de création de l'environnement
        env = DummyVecEnv([lambda: Monitor(PacManDuelEnv())])
        print("[OK] Environnement PacManDuelEnv créé")
        
        # Test de création d'un modèle DQN (sans entraînement)
        model = DQN("MlpPolicy", env, learning_rate=0.001, gamma=0.99, verbose=0)
        print("[OK] Modèle DQN créé")
        
        # Test de création d'une fenêtre Tkinter (fermée immédiatement)
        root = tk.Tk()
        root.withdraw()  # cache la fenêtre
        root.after(100, root.destroy)
        root.update()
        print("[OK] Fenêtre Tkinter créée et détruite")
        
        return True
    except Exception as e:
        print(f"[ERREUR] Échec du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test()
    sys.exit(0 if success else 1)