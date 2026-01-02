"""GUI principale pour le laboratoire IA Pac-Man.
Contient une interface Tkinter pour entraîner et tester des agents RL.
"""

import gymnasium as gym
import numpy as np
from stable_baselines3 import DQN, PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, filedialog
import threading
import time
import os
from collections import deque

from src.pacman_env.duel_env import PacManDuelEnv


class TrainingCallback(BaseCallback):
    """Callback personnalisé pour collecter les récompenses pendant l'entraînement."""
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.current_episode_reward = 0
        self.episode_lengths = []
        self.current_episode_length = 0

    def _on_step(self) -> bool:
        # Récupérer la récompense du premier environnement (DummyVecEnv)
        reward = self.locals['rewards'][0]
        done = self.locals['dones'][0]
        self.current_episode_reward += reward
        self.current_episode_length += 1
        if done:
            self.episode_rewards.append(self.current_episode_reward)
            self.episode_lengths.append(self.current_episode_length)
            self.current_episode_reward = 0
            self.current_episode_length = 0
        return True


class IALab:
    """Interface graphique principale."""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("IA LAB PAC-MAN - Entraînement RL")
        self.root.geometry("1200x800")

        # Modèle et environnement
        self.model = None
        self.env = None
        self.callback = None
        self.training_thread = None
        self.stop_training = False

        # Données pour les graphiques
        self.episode_rewards = deque(maxlen=500)
        self.episode_lengths = deque(maxlen=500)
        self.recent_rewards = deque(maxlen=100)

        # Interface utilisateur
        self.setup_ui()
        self.load_environment()

    def setup_ui(self):
        # Panneau de contrôle gauche
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side="left", fill="y", padx=10, pady=10)

        # Titre
        ttk.Label(control_frame, text="PAC-MAN RL Lab", font=("Arial", 16)).pack(pady=10)

        # Boutons d'action
        ttk.Button(control_frame, text="🚀 Entraîner", command=self.start_training).pack(pady=5, fill="x")
        ttk.Button(control_frame, text="⏸ Pause", command=self.pause_training).pack(pady=5, fill="x")
        ttk.Button(control_frame, text="▶️ Tester", command=self.test_model).pack(pady=5, fill="x")
        ttk.Button(control_frame, text="💾 Sauvegarder", command=self.save_model).pack(pady=5, fill="x")
        ttk.Button(control_frame, text="📂 Charger", command=self.load_model).pack(pady=5, fill="x")
        ttk.Button(control_frame, text="🔄 Réinitialiser", command=self.reset_model).pack(pady=5, fill="x")

        # Séparateur
        ttk.Separator(control_frame, orient="horizontal").pack(fill="x", pady=10)

        # Paramètres d'entraînement
        ttk.Label(control_frame, text="Paramètres d'entraînement", font=("Arial", 12)).pack(pady=5)

        ttk.Label(control_frame, text="Learning Rate").pack()
        self.lr_var = tk.DoubleVar(value=0.001)
        lr_scale = ttk.Scale(control_frame, from_=0.0001, to=0.01, variable=self.lr_var, orient="horizontal")
        lr_scale.pack(fill="x", pady=2)
        ttk.Label(control_frame, textvariable=tk.StringVar(value="0.001")).pack()

        ttk.Label(control_frame, text="Gamma").pack()
        self.gamma_var = tk.DoubleVar(value=0.99)
        gamma_scale = ttk.Scale(control_frame, from_=0.9, to=0.999, variable=self.gamma_var, orient="horizontal")
        gamma_scale.pack(fill="x", pady=2)
        ttk.Label(control_frame, textvariable=tk.StringVar(value="0.99")).pack()

        ttk.Label(control_frame, text="Nombre d'épisodes").pack()
        self.episodes_var = tk.IntVar(value=1000)
        episodes_entry = ttk.Entry(control_frame, textvariable=self.episodes_var)
        episodes_entry.pack(pady=2)

        ttk.Label(control_frame, text="Algorithme").pack()
        self.algorithm_var = tk.StringVar(value="DQN")
        algorithm_combo = ttk.Combobox(control_frame, textvariable=self.algorithm_var,
                                       values=["DQN", "PPO"], state="readonly")
        algorithm_combo.pack(pady=2)

        # Séparateur
        ttk.Separator(control_frame, orient="horizontal").pack(fill="x", pady=10)

        # Statistiques
        self.stats_label = ttk.Label(control_frame, text="Reward moyen: 0.0\nLongueur moyenne: 0",
                                     justify="left", font=("Courier", 10))
        self.stats_label.pack(pady=10)

        # Zone de logs
        ttk.Label(control_frame, text="Logs").pack()
        self.log_text = tk.Text(control_frame, height=10, width=30)
        self.log_text.pack(fill="both", expand=True, pady=5)

        # Panneau droit : graphiques
        fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8))
        self.fig = fig
        self.ax1.set_title("Récompense par épisode")
        self.ax2.set_title("Longueur d'épisode")
        self.canvas = FigureCanvasTkAgg(fig, self.root)
        self.canvas.get_tk_widget().pack(side="right", fill="both", expand=True, padx=10, pady=10)

    def log(self, message):
        """Ajoute un message aux logs avec timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def load_environment(self):
        """Charge l'environnement Pac-Man."""
        try:
            self.env = DummyVecEnv([lambda: Monitor(PacManDuelEnv())])
            self.log("Environnement Pac-Man chargé.")
        except Exception as e:
            self.log(f"Erreur lors du chargement de l'environnement: {e}")

    def create_model(self):
        """Crée un nouveau modèle avec les paramètres actuels."""
        algorithm = self.algorithm_var.get()
        lr = self.lr_var.get()
        gamma = self.gamma_var.get()
        if algorithm == "DQN":
            model = DQN("MlpPolicy", self.env, learning_rate=lr, gamma=gamma,
                        verbose=0, tensorboard_log="./logs/")
        else:  # PPO
            model = PPO("MlpPolicy", self.env, learning_rate=lr, gamma=gamma,
                        verbose=0, tensorboard_log="./logs/")
        self.log(f"Modèle {algorithm} créé (LR={lr}, gamma={gamma})")
        return model

    def start_training(self):
        """Démarre l'entraînement dans un thread séparé."""
        if self.training_thread and self.training_thread.is_alive():
            self.log("Entraînement déjà en cours.")
            return
        self.stop_training = False
        self.training_thread = threading.Thread(target=self._training_loop, daemon=True)
        self.training_thread.start()
        self.log("Démarrage de l'entraînement...")

    def _training_loop(self):
        """Boucle d'entraînement principale."""
        if self.model is None:
            self.model = self.create_model()
        self.callback = TrainingCallback()
        total_episodes = self.episodes_var.get()
        self.log(f"Entraînement sur {total_episodes} épisodes...")
        for episode in range(total_episodes):
            if self.stop_training:
                self.log("Entraînement interrompu.")
                break
            # Entraînement sur un petit nombre de timesteps pour permettre des mises à jour fréquentes
            self.model.learn(total_timesteps=10, reset_num_timesteps=False, callback=self.callback)
            # Mettre à jour les données
            if self.callback.episode_rewards:
                reward = self.callback.episode_rewards[-1]
                length = self.callback.episode_lengths[-1]
                self.episode_rewards.append(reward)
                self.episode_lengths.append(length)
                self.recent_rewards.append(reward)
            # Mettre à jour l'interface toutes les 10 épisodes
            if episode % 10 == 0:
                self.root.after(0, self.update_ui)
        self.log("✅ Entraînement terminé !")

    def pause_training(self):
        """Met en pause l'entraînement."""
        self.stop_training = True
        self.log("Entraînement en pause.")

    def test_model(self):
        """Teste le modèle actuel sur un épisode."""
        if self.model is None:
            self.log("Aucun modèle chargé. Veuillez en créer un ou en charger un.")
            return
        threading.Thread(target=self._test_loop, daemon=True).start()

    def _test_loop(self):
        """Boucle de test."""
        obs, _ = self.env.reset()
        total_reward = 0
        done = False
        steps = 0
        while not done and steps < 500:
            action, _ = self.model.predict(obs, deterministic=True)
            obs, reward, done, info = self.env.step(action)
            total_reward += reward
            steps += 1
        self.log(f"Test terminé: reward={total_reward:.1f}, steps={steps}")

    def save_model(self):
        """Sauvegarde le modèle dans un fichier."""
        if self.model is None:
            self.log("Aucun modèle à sauvegarder.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".zip",
                                                filetypes=[("Fichier ZIP", "*.zip"), ("Tous fichiers", "*.*")])
        if filename:
            self.model.save(filename)
            self.log(f"Modèle sauvegardé sous {filename}")

    def load_model(self):
        """Charge un modèle depuis un fichier."""
        filename = filedialog.askopenfilename(filetypes=[("Fichier ZIP", "*.zip"), ("Tous fichiers", "*.*")])
        if filename:
            try:
                algorithm = self.algorithm_var.get()
                if algorithm == "DQN":
                    self.model = DQN.load(filename, env=self.env)
                else:
                    self.model = PPO.load(filename, env=self.env)
                self.log(f"Modèle chargé depuis {filename}")
            except Exception as e:
                self.log(f"Erreur lors du chargement: {e}")

    def reset_model(self):
        """Réinitialise le modèle."""
        self.model = None
        self.episode_rewards.clear()
        self.episode_lengths.clear()
        self.recent_rewards.clear()
        self.log("Modèle réinitialisé.")
        self.update_ui()

    def update_ui(self):
        """Met à jour les graphiques et les statistiques."""
        # Statistiques
        if self.episode_rewards:
            avg_reward = np.mean(list(self.episode_rewards)[-50:])
            avg_length = np.mean(list(self.episode_lengths)[-50:])
            self.stats_label.config(text=f"Reward moyen: {avg_reward:.1f}\nLongueur moyenne: {avg_length:.1f}")
        else:
            self.stats_label.config(text="Reward moyen: 0.0\nLongueur moyenne: 0")

        # Graphiques
        self.ax1.clear()
        self.ax2.clear()
        if self.episode_rewards:
            self.ax1.plot(list(self.episode_rewards), 'b-', alpha=0.7)
            self.ax1.set_title("Récompense par épisode")
            self.ax1.set_xlabel("Épisode")
            self.ax1.set_ylabel("Reward")
            self.ax1.grid(True, alpha=0.3)
        if self.episode_lengths:
            self.ax2.plot(list(self.episode_lengths), 'g-', alpha=0.7)
            self.ax2.set_title("Longueur d'épisode")
            self.ax2.set_xlabel("Épisode")
            self.ax2.set_ylabel("Steps")
            self.ax2.grid(True, alpha=0.3)
        self.canvas.draw()

    def run(self):
        """Lance la boucle principale de l'interface."""
        self.root.mainloop()


def main():
    lab = IALab()
    lab.run()


if __name__ == '__main__':
    main()
