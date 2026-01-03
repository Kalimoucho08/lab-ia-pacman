"""
Interface graphique avancée pour le laboratoire IA Pac-Man avec environnement configurable,
visualisation intégrée, et contrôles de paramètres.
"""
import gymnasium as gym
import numpy as np
from stable_baselines3 import DQN, PPO, A2C, SAC, TD3
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import os
import json
import sys
import subprocess
from collections import deque
from pathlib import Path

from src.pacman_env.configurable_env import PacManConfigurableEnv
from src.pacman_env.multiagent_env import PacManMultiAgentEnv
from src.pacman_env.multiagent_wrappers import SingleAgentWrapper
import log_archiver


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


class IALabAdvanced:
    """Interface graphique principale avec onglets."""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("IA LAB PAC-MAN - Laboratoire Avancé")
        self.root.geometry("1400x900")

        # Modèle et environnement
        self.model = None
        self.env = None
        self.callback = None
        self.training_thread = None
        self.stop_training = False
        self.config = self._default_config()

        # Données pour les graphiques
        self.episode_rewards = deque(maxlen=500)
        self.episode_lengths = deque(maxlen=500)
        self.recent_rewards = deque(maxlen=100)

        # Interface utilisateur
        self.setup_ui()
        self.load_environment()
        self.update_visualization_config_label()

    def _default_config(self):
        """Retourne la configuration par défaut de l'environnement."""
        return {
            'size': 10,
            'walls': [],
            'num_walls': 0,
            'num_ghosts': 1,
            'num_dots': None,  # None = remplissage par défaut
            'ghost_start_positions': None,
            'pacman_start_position': (1, 1),
            'lives': 3,
            'max_steps': 200,
            'ghost_behavior': 'random',
            'reward_dot': 10.0,
            'reward_ghost_caught': -50.0,
            'reward_death': -100.0,
            'reward_step': -0.1,
        }

    def setup_ui(self):
        """Crée l'interface avec onglets."""
        # Notebook (onglets)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Onglet 1 : Configuration de l'environnement
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text='Configuration')
        self.setup_config_tab()

        # Onglet 2 : Entraînement
        self.training_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.training_frame, text='Entraînement')
        self.setup_training_tab()

        # Onglet 3 : Visualisation
        self.visualization_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.visualization_frame, text='Visualisation')
        self.setup_visualization_tab()

        # Onglet 4 : Multi‑Agent
        self.multiagent_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.multiagent_frame, text='Multi‑Agent')
        self.setup_multiagent_tab()

        # Onglet 5 : Analyse
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text='Analyse')
        self.setup_analysis_tab()

        # Barre de statut
        self.status_var = tk.StringVar(value="Prêt")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_config_tab(self):
        """Configure l'onglet de configuration de l'environnement."""
        # Panneau gauche : paramètres numériques
        left_frame = ttk.Frame(self.config_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        ttk.Label(left_frame, text="Configuration de l'environnement", font=('Arial', 14)).pack(pady=10)

        # Taille de la grille
        ttk.Label(left_frame, text="Taille de la grille").pack()
        self.size_var = tk.IntVar(value=self.config['size'])
        size_spin = ttk.Spinbox(left_frame, from_=5, to=20, textvariable=self.size_var, width=10)
        size_spin.pack(pady=2)

        # Nombre de fantômes
        ttk.Label(left_frame, text="Nombre de fantômes").pack()
        self.num_ghosts_var = tk.IntVar(value=self.config['num_ghosts'])
        ghosts_spin = ttk.Spinbox(left_frame, from_=1, to=4, textvariable=self.num_ghosts_var, width=10)
        ghosts_spin.pack(pady=2)

        # Nombre de points (optionnel)
        ttk.Label(left_frame, text="Nombre de points (laisser vide pour remplissage)").pack()
        self.num_dots_var = tk.StringVar(value='')
        dots_entry = ttk.Entry(left_frame, textvariable=self.num_dots_var, width=10)
        dots_entry.pack(pady=2)

        # Nombre de murs aléatoires
        ttk.Label(left_frame, text="Nombre de murs aléatoires").pack()
        self.num_walls_var = tk.IntVar(value=self.config['num_walls'])
        walls_spin = ttk.Spinbox(left_frame, from_=0, to=50, textvariable=self.num_walls_var, width=10)
        walls_spin.pack(pady=2)

        # Vies de Pac-Man
        ttk.Label(left_frame, text="Vies de Pac-Man").pack()
        self.lives_var = tk.IntVar(value=self.config['lives'])
        lives_spin = ttk.Spinbox(left_frame, from_=1, to=10, textvariable=self.lives_var, width=10)
        lives_spin.pack(pady=2)

        # Comportement des fantômes
        ttk.Label(left_frame, text="Comportement des fantômes").pack()
        self.ghost_behavior_var = tk.StringVar(value=self.config['ghost_behavior'])
        behavior_combo = ttk.Combobox(left_frame, textvariable=self.ghost_behavior_var,
                                      values=['random', 'chase', 'scatter'], state='readonly')
        behavior_combo.pack(pady=2)

        # Boutons d'action
        ttk.Button(left_frame, text="Appliquer la configuration", command=self.apply_config).pack(pady=10)
        ttk.Button(left_frame, text="Réinitialiser à la configuration par défaut",
                   command=self.reset_config).pack(pady=5)

        # Panneau droit : éditeur de murs (grille cliquable)
        right_frame = ttk.Frame(self.config_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        ttk.Label(right_frame, text="Éditeur de murs (cliquez pour ajouter/enlever)", font=('Arial', 12)).pack(pady=5)
        self.wall_canvas = tk.Canvas(right_frame, width=400, height=400, bg='white')
        self.wall_canvas.pack()
        self.wall_canvas.bind('<Button-1>', self.toggle_wall)
        self.walls = set(self.config['walls'])
        self.draw_grid()

    def draw_grid(self):
        """Dessine la grille de l'éditeur de murs."""
        self.wall_canvas.delete('all')
        size = self.size_var.get()
        cell_size = 400 // size
        for r in range(size):
            for c in range(size):
                x1 = c * cell_size
                y1 = r * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                color = 'black' if (r, c) in self.walls else 'white'
                self.wall_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='gray')
                # Marquer Pac-Man et fantômes
                if (r, c) == self.config['pacman_start_position']:
                    self.wall_canvas.create_text(x1 + cell_size//2, y1 + cell_size//2, text='P', fill='yellow')
                # Les fantômes ne sont pas affichés pour simplifier

    def toggle_wall(self, event):
        """Ajoute ou enlève un mur au clic."""
        size = self.size_var.get()
        cell_size = 400 // size
        c = event.x // cell_size
        r = event.y // cell_size
        if 0 <= r < size and 0 <= c < size:
            if (r, c) == self.config['pacman_start_position']:
                messagebox.showwarning("Position invalide", "Impossible de placer un mur sur Pac-Man.")
                return
            if (r, c) in self.walls:
                self.walls.remove((r, c))
            else:
                self.walls.add((r, c))
            self.draw_grid()

    def generate_random_walls(self, size, num_walls, exclude_positions):
        """Génère une liste de positions de murs aléatoires, en évitant les positions exclues."""
        import random
        walls = []
        possible = [(r, c) for r in range(size) for c in range(size) if (r, c) not in exclude_positions]
        if num_walls > len(possible):
            num_walls = len(possible)
        chosen = random.sample(possible, num_walls)
        return chosen

    def apply_config(self):
        """Applique la configuration et recharge l'environnement."""
        try:
            size = self.size_var.get()
            num_ghosts = self.num_ghosts_var.get()
            num_dots = self.num_dots_var.get()
            num_dots = int(num_dots) if num_dots.strip() else None
            num_walls = self.num_walls_var.get()
            lives = self.lives_var.get()
            ghost_behavior = self.ghost_behavior_var.get()

            # Générer les murs aléatoires
            random_walls = []
            if num_walls > 0:
                exclude = [self.config['pacman_start_position']]
                # Exclure aussi les positions des fantômes (inconnues) et les murs manuels
                # On génère les murs aléatoires en excluant les positions déjà occupées par des murs manuels
                exclude.extend(self.walls)
                random_walls = self.generate_random_walls(size, num_walls, exclude)
            
            # Union des murs manuels et aléatoires
            all_walls = list(set(self.walls) | set(random_walls))

            # Mettre à jour la configuration
            self.config.update({
                'size': size,
                'walls': all_walls,
                'num_walls': num_walls,
                'num_ghosts': num_ghosts,
                'num_dots': num_dots,
                'lives': lives,
                'ghost_behavior': ghost_behavior,
            })

            # Recharger l'environnement
            self.load_environment()
            self.draw_grid()
            self.status_var.set("Configuration appliquée avec succès.")
            self.update_visualization_config_label()
        except Exception as e:
            messagebox.showerror("Erreur de configuration", str(e))

    def reset_config(self):
        """Réinitialise la configuration aux valeurs par défaut."""
        self.config = self._default_config()
        self.size_var.set(self.config['size'])
        self.num_ghosts_var.set(self.config['num_ghosts'])
        self.num_dots_var.set('')
        self.num_walls_var.set(self.config['num_walls'])
        self.lives_var.set(self.config['lives'])
        self.ghost_behavior_var.set(self.config['ghost_behavior'])
        self.walls = set(self.config['walls'])
        self.draw_grid()
        self.status_var.set("Configuration réinitialisée.")
        self.update_visualization_config_label()

    def setup_training_tab(self):
        """Configure l'onglet d'entraînement (similaire à l'ancienne interface)."""
        # Panneau de contrôle gauche
        control_frame = ttk.Frame(self.training_frame)
        control_frame.pack(side="left", fill="y", padx=10, pady=10)

        ttk.Label(control_frame, text="Entraînement RL", font=("Arial", 16)).pack(pady=10)

        # Boutons d'action
        ttk.Button(control_frame, text="🚀 Entraîner", command=self.start_training).pack(pady=5, fill="x")
        ttk.Button(control_frame, text="⏸ Pause", command=self.pause_training).pack(pady=5, fill="x")
        ttk.Button(control_frame, text="▶️ Tester", command=self.test_model).pack(pady=5, fill="x")
        ttk.Button(control_frame, text="💾 Sauvegarder", command=self.save_model).pack(pady=5, fill="x")
        ttk.Button(control_frame, text="📂 Charger", command=self.load_model).pack(pady=5, fill="x")
        ttk.Button(control_frame, text="🔄 Réinitialiser", command=self.reset_model).pack(pady=5, fill="x")
        ttk.Button(control_frame, text="🗜️ Archiver les logs", command=self.archive_logs).pack(pady=5, fill="x")

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
        self.canvas = FigureCanvasTkAgg(fig, self.training_frame)
        self.canvas.get_tk_widget().pack(side="right", fill="both", expand=True, padx=10, pady=10)

    def setup_visualization_tab(self):
        """Configure l'onglet de visualisation (intégration Pygame)."""
        frame = ttk.Frame(self.visualization_frame)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Visualisation des parties", font=('Arial', 14)).pack(pady=10)

        # Description
        ttk.Label(frame, text="Visualisez l'environnement Pac-Man avec les paramètres actuels.").pack(pady=5)
        ttk.Label(frame, text="Vous pouvez lancer une visualisation avec un agent aléatoire ou visualiser l'entraînement en temps réel.").pack(pady=5)

        # Boutons d'action
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="🎮 Visualiser avec paramètres actuels (agent aléatoire)",
                   command=self.launch_visualization_with_config).pack(pady=5, fill='x')
        ttk.Button(button_frame, text="🤖 Visualiser l'entraînement en temps réel (expérimental)",
                   command=self.launch_training_visualization).pack(pady=5, fill='x')
        ttk.Button(button_frame, text="🔄 Visualiser avec modèle entraîné",
                   command=self.launch_model_visualization).pack(pady=5, fill='x')

        # Paramètres de visualisation
        control_frame = ttk.Frame(frame)
        control_frame.pack(pady=10)
        ttk.Label(control_frame, text="FPS:").pack(side='left')
        self.fps_var = tk.IntVar(value=10)
        fps_spin = ttk.Spinbox(control_frame, from_=1, to=60, textvariable=self.fps_var, width=5)
        fps_spin.pack(side='left', padx=5)
        ttk.Button(control_frame, text="Pause", command=self.pause_visualization).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Reprendre", command=self.resume_visualization).pack(side='left', padx=5)

        # Informations de configuration
        info_frame = ttk.LabelFrame(frame, text="Configuration actuelle")
        info_frame.pack(pady=10, fill='x', padx=20)
        self.vis_config_label = ttk.Label(info_frame, text="", justify='left')
        self.vis_config_label.pack(pady=5, padx=5)
        self.update_visualization_config_label()

    def setup_multiagent_tab(self):
        """Configure l'onglet multi‑agent avec power pellets et sélection de modèles."""
        frame = ttk.Frame(self.multiagent_frame)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Apprentissage Multi‑Agent avec Power Pellets", font=('Arial', 14)).pack(pady=10)

        # Description
        ttk.Label(frame, text="Chaque agent (Pac‑Man et fantômes) peut être contrôlé par un modèle RL distinct.").pack(pady=5)
        ttk.Label(frame, text="Les power pellets rendent les fantômes vulnérables pendant une durée configurable.").pack(pady=5)

        # Panneau gauche : configuration
        left_frame = ttk.Frame(frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        # Power pellets
        ttk.Label(left_frame, text="Power Pellets", font=('Arial', 12)).pack(pady=5)
        ttk.Label(left_frame, text="Durée d'effet (steps)").pack()
        self.power_duration_var = tk.IntVar(value=10)
        power_spin = ttk.Spinbox(left_frame, from_=5, to=30, textvariable=self.power_duration_var, width=10)
        power_spin.pack(pady=2)

        # Nombre de power pellets
        ttk.Label(left_frame, text="Nombre de power pellets").pack()
        self.num_power_var = tk.IntVar(value=2)
        num_power_spin = ttk.Spinbox(left_frame, from_=0, to=5, textvariable=self.num_power_var, width=10)
        num_power_spin.pack(pady=2)

        # Récompenses configurables
        ttk.Label(left_frame, text="Récompenses Pac‑Man", font=('Arial', 12)).pack(pady=(10,0))
        ttk.Label(left_frame, text="Point").pack()
        self.reward_dot_var = tk.DoubleVar(value=10.0)
        ttk.Entry(left_frame, textvariable=self.reward_dot_var, width=10).pack(pady=2)
        ttk.Label(left_frame, text="Fantôme vulnérable").pack()
        self.reward_ghost_vuln_var = tk.DoubleVar(value=50.0)
        ttk.Entry(left_frame, textvariable=self.reward_ghost_vuln_var, width=10).pack(pady=2)
        ttk.Label(left_frame, text="Mort").pack()
        self.reward_death_var = tk.DoubleVar(value=-100.0)
        ttk.Entry(left_frame, textvariable=self.reward_death_var, width=10).pack(pady=2)

        ttk.Label(left_frame, text="Récompenses Fantôme", font=('Arial', 12)).pack(pady=(10,0))
        ttk.Label(left_frame, text="Manger Pac‑Man").pack()
        self.reward_ghost_eat_var = tk.DoubleVar(value=100.0)
        ttk.Entry(left_frame, textvariable=self.reward_ghost_eat_var, width=10).pack(pady=2)
        ttk.Label(left_frame, text="Éviter Pac‑Man (vulnérable)").pack()
        self.reward_ghost_avoid_var = tk.DoubleVar(value=-20.0)
        ttk.Entry(left_frame, textvariable=self.reward_ghost_avoid_var, width=10).pack(pady=2)

        # Bouton appliquer
        ttk.Button(left_frame, text="Appliquer les paramètres multi‑agent", command=self.apply_multiagent_config).pack(pady=20)

        # Panneau droit : sélection des modèles
        right_frame = ttk.Frame(frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # Pac‑Man
        ttk.Label(right_frame, text="Pac‑Man", font=('Arial', 12)).pack(pady=5)
        self.pacman_algorithm_var = tk.StringVar(value="DQN")
        ttk.Combobox(right_frame, textvariable=self.pacman_algorithm_var,
                     values=["DQN", "PPO", "A2C", "SAC", "TD3"], state="readonly").pack(pady=2)
        ttk.Button(right_frame, text="Entraîner Pac‑Man", command=self.train_pacman).pack(pady=5)
        ttk.Button(right_frame, text="Charger modèle Pac‑Man", command=self.load_pacman_model).pack(pady=2)

        # Fantômes
        ttk.Label(right_frame, text="Fantômes", font=('Arial', 12)).pack(pady=(10,0))
        self.ghost_algorithm_var = tk.StringVar(value="PPO")
        ttk.Combobox(right_frame, textvariable=self.ghost_algorithm_var,
                     values=["DQN", "PPO", "A2C", "SAC", "TD3"], state="readonly").pack(pady=2)
        ttk.Label(right_frame, text="Partage de poids entre fantômes").pack()
        self.share_weights_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, variable=self.share_weights_var).pack()
        ttk.Button(right_frame, text="Entraîner les fantômes", command=self.train_ghosts).pack(pady=5)
        ttk.Button(right_frame, text="Charger modèle fantômes", command=self.load_ghost_model).pack(pady=2)

        # Boutons communs
        ttk.Button(right_frame, text="Lancer une simulation multi‑agent", command=self.launch_multiagent_simulation).pack(pady=20)

        # Statistiques par agent
        stats_frame = ttk.LabelFrame(frame, text="Statistiques par agent")
        stats_frame.pack(fill='x', padx=20, pady=10)
        self.stats_text = tk.Text(stats_frame, height=8, wrap='word')
        self.stats_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.update_multiagent_stats()

    def apply_multiagent_config(self):
        """Applique les paramètres multi‑agent (power pellets, récompenses)."""
        try:
            self.config['power_duration'] = self.power_duration_var.get()
            self.config['num_power'] = self.num_power_var.get()
            self.config['reward_dot'] = self.reward_dot_var.get()
            self.config['reward_ghost_vuln'] = self.reward_ghost_vuln_var.get()
            self.config['reward_death'] = self.reward_death_var.get()
            self.config['reward_ghost_eat'] = self.reward_ghost_eat_var.get()
            self.config['reward_ghost_avoid'] = self.reward_ghost_avoid_var.get()
            self.log("Paramètres multi‑agent appliqués.")
            self.update_multiagent_stats()
        except Exception as e:
            self.log(f"Erreur lors de l'application des paramètres multi‑agent: {e}")

    def train_pacman(self):
        """Entraîne Pac‑Man avec l'algorithme sélectionné."""
        self.log("Démarrage de l'entraînement de Pac‑Man...")
        # Créer un environnement multi‑agent avec les paramètres actuels
        try:
            reward_config = {
                "pacman": {
                    "dot": self.config.get('reward_dot', 10.0),
                    "ghost_eaten": self.config.get('reward_ghost_vuln', 50.0),
                    "death": self.config.get('reward_death', -100.0),
                    "step": self.config.get('reward_step', -0.1),
                    "power_pellet_eaten": 20.0
                },
                "ghost": {
                    "eat_pacman": self.config.get('reward_ghost_eat', 100.0),
                    "eaten": self.config.get('reward_ghost_avoid', -20.0),
                    "step": -0.1,
                    "distance_reward": 0.0
                }
            }
            multi_env = PacManMultiAgentEnv(
                size=self.config['size'],
                walls=self.config['walls'],
                num_ghosts=self.config['num_ghosts'],
                num_dots=self.config['num_dots'],
                pacman_start_position=self.config['pacman_start_position'],
                lives=self.config['lives'],
                max_steps=self.config['max_steps'],
                ghost_behavior=self.config['ghost_behavior'],
                power_pellets=self.config.get('num_power', 2),
                power_duration=self.config.get('power_duration', 10),
                reward_config=reward_config
            )
            # Wrapper pour Pac‑Man (les fantômes en comportement prédéfini)
            pacman_env = SingleAgentWrapper(multi_env, agent_id="pacman", other_agent_policy="random")
            # Vectoriser l'environnement pour Stable-Baselines3
            vec_env = DummyVecEnv([lambda: Monitor(pacman_env)])
            # Sélectionner l'algorithme
            algorithm = self.pacman_algorithm_var.get()
            lr = self.lr_var.get()
            gamma = self.gamma_var.get()
            if algorithm == "DQN":
                model = DQN("MlpPolicy", vec_env, learning_rate=lr, gamma=gamma,
                            verbose=0, tensorboard_log="./logs/")
            elif algorithm == "PPO":
                model = PPO("MlpPolicy", vec_env, learning_rate=lr, gamma=gamma,
                            verbose=0, tensorboard_log="./logs/")
            elif algorithm == "A2C":
                model = A2C("MlpPolicy", vec_env, learning_rate=lr, gamma=gamma,
                            verbose=0, tensorboard_log="./logs/")
            elif algorithm == "SAC":
                model = SAC("MlpPolicy", vec_env, learning_rate=lr, gamma=gamma,
                            verbose=0, tensorboard_log="./logs/")
            elif algorithm == "TD3":
                model = TD3("MlpPolicy", vec_env, learning_rate=lr, gamma=gamma,
                            verbose=0, tensorboard_log="./logs/")
            else:
                self.log(f"Algorithme {algorithm} non supporté.")
                return
            # Entraînement dans un thread séparé
            self.stop_training = False
            self.training_thread = threading.Thread(target=self._train_pacman_loop,
                                                    args=(model, vec_env),
                                                    daemon=True)
            self.training_thread.start()
            self.log(f"Entraînement de Pac‑Man avec {algorithm} démarré.")
        except Exception as e:
            self.log(f"Erreur lors de la création de l'environnement multi‑agent: {e}")

    def _train_pacman_loop(self, model, vec_env):
        """Boucle d'entraînement pour Pac‑Man."""
        total_episodes = self.episodes_var.get()
        self.log(f"Entraînement de Pac‑Man sur {total_episodes} épisodes...")
        callback = TrainingCallback()
        for episode in range(total_episodes):
            if self.stop_training:
                self.log("Entraînement de Pac‑Man interrompu.")
                break
            model.learn(total_timesteps=10, reset_num_timesteps=False, callback=callback)
            if callback.episode_rewards:
                reward = callback.episode_rewards[-1]
                length = callback.episode_lengths[-1]
                self.episode_rewards.append(reward)
                self.episode_lengths.append(length)
                self.recent_rewards.append(reward)
            else:
                self.episode_rewards.append(0.0)
                self.episode_lengths.append(0)
                self.recent_rewards.append(0.0)
            if episode % 10 == 0:
                self.root.after(0, self.update_ui)
            time.sleep(0.01)
        self.log("✅ Entraînement de Pac‑Man terminé !")
        # Sauvegarder le modèle dans un fichier par défaut
        model.save(f"logs/pacman_{self.pacman_algorithm_var.get()}_{int(time.time())}.zip")
        self.log("Modèle Pac‑Man sauvegardé.")

    def train_ghosts(self):
        """Entraîne les fantômes avec l'algorithme sélectionné."""
        self.log("Démarrage de l'entraînement des fantômes...")
        try:
            reward_config = {
                "pacman": {
                    "dot": self.config.get('reward_dot', 10.0),
                    "ghost_eaten": self.config.get('reward_ghost_vuln', 50.0),
                    "death": self.config.get('reward_death', -100.0),
                    "step": self.config.get('reward_step', -0.1),
                    "power_pellet_eaten": 20.0
                },
                "ghost": {
                    "eat_pacman": self.config.get('reward_ghost_eat', 100.0),
                    "eaten": self.config.get('reward_ghost_avoid', -20.0),
                    "step": -0.1,
                    "distance_reward": 0.0
                }
            }
            multi_env = PacManMultiAgentEnv(
                size=self.config['size'],
                walls=self.config['walls'],
                num_ghosts=self.config['num_ghosts'],
                num_dots=self.config['num_dots'],
                pacman_start_position=self.config['pacman_start_position'],
                lives=self.config['lives'],
                max_steps=self.config['max_steps'],
                ghost_behavior=self.config['ghost_behavior'],
                power_pellets=self.config.get('num_power', 2),
                power_duration=self.config.get('power_duration', 10),
                reward_config=reward_config
            )
            # Wrapper pour un fantôme (agent_id "ghost_0") avec Pac‑Man en comportement prédéfini
            ghost_env = SingleAgentWrapper(multi_env, agent_id="ghost_0", other_agent_policy="random")
            vec_env = DummyVecEnv([lambda: Monitor(ghost_env)])
            algorithm = self.ghost_algorithm_var.get()
            lr = self.lr_var.get()
            gamma = self.gamma_var.get()
            if algorithm == "DQN":
                model = DQN("MlpPolicy", vec_env, learning_rate=lr, gamma=gamma,
                            verbose=0, tensorboard_log="./logs/")
            elif algorithm == "PPO":
                model = PPO("MlpPolicy", vec_env, learning_rate=lr, gamma=gamma,
                            verbose=0, tensorboard_log="./logs/")
            elif algorithm == "A2C":
                model = A2C("MlpPolicy", vec_env, learning_rate=lr, gamma=gamma,
                            verbose=0, tensorboard_log="./logs/")
            elif algorithm == "SAC":
                model = SAC("MlpPolicy", vec_env, learning_rate=lr, gamma=gamma,
                            verbose=0, tensorboard_log="./logs/")
            elif algorithm == "TD3":
                model = TD3("MlpPolicy", vec_env, learning_rate=lr, gamma=gamma,
                            verbose=0, tensorboard_log="./logs/")
            else:
                self.log(f"Algorithme {algorithm} non supporté.")
                return
            self.stop_training = False
            self.training_thread = threading.Thread(target=self._train_ghosts_loop,
                                                    args=(model, vec_env),
                                                    daemon=True)
            self.training_thread.start()
            self.log(f"Entraînement des fantômes avec {algorithm} démarré.")
        except Exception as e:
            self.log(f"Erreur lors de la création de l'environnement pour les fantômes: {e}")

    def _train_ghosts_loop(self, model, vec_env):
        """Boucle d'entraînement pour les fantômes."""
        total_episodes = self.episodes_var.get()
        self.log(f"Entraînement des fantômes sur {total_episodes} épisodes...")
        callback = TrainingCallback()
        for episode in range(total_episodes):
            if self.stop_training:
                self.log("Entraînement des fantômes interrompu.")
                break
            model.learn(total_timesteps=10, reset_num_timesteps=False, callback=callback)
            if callback.episode_rewards:
                reward = callback.episode_rewards[-1]
                length = callback.episode_lengths[-1]
                self.episode_rewards.append(reward)
                self.episode_lengths.append(length)
                self.recent_rewards.append(reward)
            else:
                self.episode_rewards.append(0.0)
                self.episode_lengths.append(0)
                self.recent_rewards.append(0.0)
            if episode % 10 == 0:
                self.root.after(0, self.update_ui)
            time.sleep(0.01)
        self.log("✅ Entraînement des fantômes terminé !")
        model.save(f"logs/ghosts_{self.ghost_algorithm_var.get()}_{int(time.time())}.zip")
        self.log("Modèle fantômes sauvegardé.")

    def load_pacman_model(self):
        """Charge un modèle pour Pac‑Man."""
        filename = filedialog.askopenfilename(filetypes=[("Fichier ZIP", "*.zip"), ("Tous fichiers", "*.*")])
        if filename:
            self.log(f"Chargement du modèle Pac‑Man depuis {filename}")
            # TODO: charger le modèle

    def load_ghost_model(self):
        """Charge un modèle pour les fantômes."""
        filename = filedialog.askopenfilename(filetypes=[("Fichier ZIP", "*.zip"), ("Tous fichiers", "*.*")])
        if filename:
            self.log(f"Chargement du modèle fantômes depuis {filename}")
            # TODO: charger le modèle

    def launch_multiagent_simulation(self):
        """Lance une simulation multi‑agent avec visualisation."""
        self.log("Lancement de la simulation multi‑agent...")
        try:
            # Construire la commande pour lancer un script de simulation multi‑agent
            args = [
                sys.executable, "visual_pacman_advanced.py",
                "--size", str(self.config['size']),
                "--num_ghosts", str(self.config['num_ghosts']),
                "--lives", str(self.config['lives']),
                "--ghost_behavior", self.config['ghost_behavior'],
                "--num_walls", str(self.config['num_walls']),
                "--fps", str(self.fps_var.get()),
                "--multiagent", "1",
                "--power_duration", str(self.config.get('power_duration', 10)),
                "--num_power", str(self.config.get('num_power', 2))
            ]
            if self.config['num_dots'] is not None:
                args.extend(["--num_dots", str(self.config['num_dots'])])
            self.log(f"Exécution: {' '.join(args)}")
            import subprocess
            subprocess.Popen(args)
        except Exception as e:
            self.log(f"Erreur lors du lancement de la simulation multi‑agent: {e}")

    def update_multiagent_stats(self):
        """Met à jour les statistiques affichées dans l'onglet multi‑agent."""
        text = f"Power pellets: {self.config.get('num_power', 2)} (durée {self.config.get('power_duration', 10)} steps)\n"
        text += f"Récompenses Pac‑Man: point={self.config.get('reward_dot', 10.0)}, fantôme vulnérable={self.config.get('reward_ghost_vuln', 50.0)}, mort={self.config.get('reward_death', -100.0)}\n"
        text += f"Récompenses Fantôme: manger Pac‑Man={self.config.get('reward_ghost_eat', 100.0)}, éviter Pac‑Man={self.config.get('reward_ghost_avoid', -20.0)}\n"
        text += f"Algorithme Pac‑Man: {self.pacman_algorithm_var.get()}\n"
        text += f"Algorithme Fantômes: {self.ghost_algorithm_var.get()}\n"
        text += f"Partage de poids: {'Oui' if self.share_weights_var.get() else 'Non'}\n"
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert('1.0', text)
        self.stats_text.config(state='disabled')

    def setup_analysis_tab(self):
        """Configure l'onglet d'analyse (explications, métriques)."""
        frame = ttk.Frame(self.analysis_frame)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Analyse et Explications", font=('Arial', 14)).pack(pady=10)

        # Notebook interne pour sous-onglets
        sub_notebook = ttk.Notebook(frame)
        sub_notebook.pack(fill='both', expand=True)

        # Sous-onglet 1 : Explications des paramètres
        explain_frame = ttk.Frame(sub_notebook)
        sub_notebook.add(explain_frame, text='Paramètres')
        text = tk.Text(explain_frame, wrap='word', height=15)
        text.pack(fill='both', expand=True, padx=5, pady=5)
        explanation = """
        Taille de la grille : Nombre de cases par côté (5 à 20).
        Murs : Cases infranchissables, placées via l'éditeur graphique.
        Nombre de fantômes : De 1 à 4. Chaque fantôme peut avoir un comportement distinct.
        Nombre de points : Si vide, toutes les cases non occupées contiennent un point.
        Vies de Pac-Man : Nombre de vies avant fin de l'épisode.
        Comportement des fantômes :
          - random : Déplacement aléatoire.
          - chase : Poursuite de Pac-Man (distance de Manhattan).
          - scatter : Dispersion vers les coins.
        Récompenses :
          - Point : +10
          - Fantôme attrapé : -50
          - Mort : -100
          - Step : -0.1
        """
        text.insert('1.0', explanation)
        text.config(state='disabled')

        # Sous-onglet 2 : Métriques
        metrics_frame = ttk.Frame(sub_notebook)
        sub_notebook.add(metrics_frame, text='Métriques')
        ttk.Label(metrics_frame, text="Métriques de performance").pack(pady=5)
        self.metrics_text = tk.Text(metrics_frame, wrap='word', height=10)
        self.metrics_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.update_metrics()

        # Sous-onglet 3 : Paramètres des modèles
        model_params_frame = ttk.Frame(sub_notebook)
        sub_notebook.add(model_params_frame, text='Paramètres des modèles')
        model_text = tk.Text(model_params_frame, wrap='word', height=15)
        model_text.pack(fill='both', expand=True, padx=5, pady=5)
        model_explanation = """
        Paramètres des algorithmes d'apprentissage par renforcement :

        Learning Rate (taux d'apprentissage) :
          - Plage typique : 0.0001 à 0.01
          - Plus élevé → apprentissage plus rapide mais risque d'instabilité.
          - Plus bas → apprentissage plus stable mais plus lent.
          - Valeur par défaut : 0.001

        Gamma (facteur de discount) :
          - Plage : 0.9 à 0.999
          - Détermine l'importance des récompenses futures.
          - Proche de 1 → l'agent prend en compte les récompenses lointaines.
          - Proche de 0 → l'agent est myope, ne considère que les récompenses immédiates.
          - Valeur par défaut : 0.99

        Algorithmes disponibles :
          - DQN (Deep Q-Network) :
            * Utilise une Q‑Network pour estimer la valeur des actions.
            * Convient pour des espaces d'actions discrets.
            * Mémoire de replay pour stabiliser l'apprentissage.
            * Paramètres supplémentaires : taille du replay buffer, fréquence de mise à jour de la target network.

          - PPO (Proximal Policy Optimization) :
            * Optimisation de politique avec contrainte de proximité.
            * Plus stable et robuste que DQN pour des politiques continues.
            * Convient aussi aux actions discrètes.
            * Paramètres supplémentaires : clip range, nombre d'étapes par mise à jour.

        Effets des variations :
          - Augmenter le learning rate peut accélérer la convergence mais risque de diverger.
          - Diminuer gamma rend l'agent plus court‑termiste, peut améliorer les performances si les récompenses lointaines sont bruitées.
          - DQN est plus sensible à l'hyperparamétrisation, PPO est plus robuste mais plus lent.
          - Pour Pac‑Man, DQN fonctionne bien avec une grille petite, PPO peut mieux gérer des environnements plus complexes.

        Recommandations pour Pac‑Man :
          - Commencer avec DQN, learning rate 0.001, gamma 0.99.
          - Si l'apprentissage est instable, réduire le learning rate.
          - Si l'agent ne planifie pas assez, augmenter gamma.
          - Ajouter plus de fantômes ou de murs peut nécessiter un apprentissage plus long.
        """
        model_text.insert('1.0', model_explanation)
        model_text.config(state='disabled')

        # Sous-onglet 4 : À propos
        about_frame = ttk.Frame(sub_notebook)
        sub_notebook.add(about_frame, text='À propos')
        about_text = tk.Text(about_frame, wrap='word', height=10)
        about_text.pack(fill='both', expand=True, padx=5, pady=5)
        about_content = """
        Laboratoire IA Pac-Man - Version avancée
        Développé pour l'expérimentation d'algorithmes d'apprentissage par renforcement.
        Environnement configurable avec Gymnasium.
        Intégration de Stable-Baselines3 (DQN, PPO).
        Interface graphique Tkinter avec visualisation Pygame.
        """
        about_text.insert('1.0', about_content)
        about_text.config(state='disabled')

    def update_metrics(self):
        """Met à jour les métriques affichées."""
        if self.episode_rewards:
            avg_reward = np.mean(list(self.episode_rewards)[-50:])
            avg_length = np.mean(list(self.episode_lengths)[-50:])
            text = f"Reward moyen (50 derniers épisodes) : {avg_reward:.2f}\n"
            text += f"Longueur moyenne (50 derniers épisodes) : {avg_length:.2f}\n"
            text += f"Nombre total d'épisodes enregistrés : {len(self.episode_rewards)}\n"
            if self.model:
                text += f"Modèle actuel : {self.algorithm_var.get()}\n"
            else:
                text += "Aucun modèle chargé.\n"
            self.metrics_text.delete('1.0', tk.END)
            self.metrics_text.insert('1.0', text)
        self.metrics_text.config(state='disabled')

    def log(self, message):
        """Ajoute un message aux logs avec timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def load_environment(self):
        """Charge l'environnement Pac-Man configurable."""
        try:
            reward_structure = {
                'dot': self.config['reward_dot'],
                'ghost_caught': self.config['reward_ghost_caught'],
                'death': self.config['reward_death'],
                'step': self.config['reward_step']
            }
            env = PacManConfigurableEnv(
                size=self.config['size'],
                walls=self.config['walls'],
                num_ghosts=self.config['num_ghosts'],
                num_dots=self.config['num_dots'],
                ghost_start_positions=self.config['ghost_start_positions'],
                pacman_start_position=self.config['pacman_start_position'],
                lives=self.config['lives'],
                max_steps=self.config['max_steps'],
                ghost_behavior=self.config['ghost_behavior'],
                reward_structure=reward_structure
            )
            self.env = DummyVecEnv([lambda: Monitor(env)])
            self.log("Environnement Pac-Man configurable chargé.")
        except Exception as e:
            self.log(f"Erreur lors du chargement de l'environnement: {e}")

    def create_model(self):
        """Crée un nouveau modèle avec les paramètres actuels."""
        algorithm = self.algorithm_var.get()
        lr = self.lr_var.get()
        gamma = self.gamma_var.get()
        # Détecter si l'observation est une image (shape 3D avec canaux en premier)
        obs_shape = self.env.observation_space.shape
        # Stable-Baselines3 attend des images avec canaux en premier (C, H, W)
        # Notre environnement Pac-Man retourne (H, W, C) -> considérer comme MLP
        # Pour simplifier, on utilise toujours MlpPolicy car l'observation est une grille discrète
        policy = "MlpPolicy"
        if algorithm == "DQN":
            model = DQN(policy, self.env, learning_rate=lr, gamma=gamma,
                        verbose=0, tensorboard_log="./logs/")
        else:  # PPO
            model = PPO(policy, self.env, learning_rate=lr, gamma=gamma,
                        verbose=0, tensorboard_log="./logs/")
        self.log(f"Modèle {algorithm} créé (LR={lr}, gamma={gamma}, policy={policy})")
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
            else:
                # Aucun épisode terminé, on ajoute une valeur par défaut pour éviter les listes vides
                self.episode_rewards.append(0.0)
                self.episode_lengths.append(0)
                self.recent_rewards.append(0.0)
            # Mettre à jour l'interface toutes les 10 épisodes
            if episode % 10 == 0:
                self.root.after(0, self.update_ui)
            # Petit délai pour éviter de surcharger le CPU
            time.sleep(0.01)
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
        obs = self.env.reset()
        total_reward = 0.0
        done = False
        steps = 0
        while not done and steps < 500:
            action, _ = self.model.predict(obs, deterministic=True)
            obs, reward, done, info = self.env.step(action)
            # reward peut être un tableau numpy (pour VecEnv), extraire la valeur scalaire
            total_reward += float(reward[0] if isinstance(reward, np.ndarray) else reward)
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

    def archive_logs(self):
        """Archive les logs de la simulation actuelle (texte compressé + fusion TensorBoard)."""
        try:
            self.log("Archivage des logs en cours...")
            # Chemin du répertoire logs
            log_dir = "logs"
            if not os.path.exists(log_dir):
                self.log("Aucun répertoire logs trouvé.")
                return
            
            # Trouver le sous-répertoire le plus récent (par date de modification)
            subdirs = [d for d in os.listdir(log_dir) if os.path.isdir(os.path.join(log_dir, d))]
            if not subdirs:
                self.log("Aucun sous-répertoire de simulation trouvé.")
                return
            
            # Sélectionner le répertoire avec la date de modification la plus récente
            latest_sim = max(subdirs, key=lambda d: os.path.getmtime(os.path.join(log_dir, d)))
            sim_path = os.path.join(log_dir, latest_sim)
            
            # Fusionner les logs TensorBoard
            self.log(f"Fusion des logs TensorBoard dans {sim_path}...")
            merged = log_archiver.merge_tensorboard_logs(sim_path)
            if merged:
                self.log(f"Logs TensorBoard fusionnés : {merged}")
            
            # Compresser les logs texte uniquement dans le répertoire de simulation
            for root, dirs, files in os.walk(sim_path):
                for file in files:
                    if file.endswith('.log') and not file.endswith('.log.gz'):
                        log_path = os.path.join(root, file)
                        self.log(f"Compression de {log_path}...")
                        compressed = log_archiver.compress_text_log(log_path, keep_original=False)
                        if compressed:
                            self.log(f"Compressé en {compressed}")
            
            # Créer une archive ZIP de la simulation
            archive_path = log_archiver.archive_simulation_logs(latest_sim, log_dir)
            if archive_path:
                self.log(f"Archive créée : {archive_path}")
                self.status_var.set(f"Logs archivés dans {archive_path}")
            else:
                self.log("Échec de la création de l'archive.")
        except Exception as e:
            self.log(f"Erreur lors de l'archivage : {e}")

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
        self.update_metrics()

    def launch_visualization(self):
        """Lance une fenêtre de visualisation Pygame (placeholder)."""
        self.log("Lancement de la visualisation...")
        # Pour l'instant, on utilise le script existant
        import subprocess
        subprocess.Popen([sys.executable, "visual_pacman.py"])

    def pause_visualization(self):
        """Met en pause la visualisation."""
        self.log("Visualisation en pause (non implémenté).")

    def resume_visualization(self):
        """Reprend la visualisation."""
        self.log("Visualisation reprise (non implémenté).")

    def update_visualization_config_label(self):
        """Met à jour le label de configuration dans l'onglet Visualisation."""
        config = self.config
        text = f"Taille: {config['size']}x{config['size']} | Fantômes: {config['num_ghosts']} | Points: {config['num_dots'] if config['num_dots'] else 'remplissage'} | Murs: {len(config['walls'])} ({config['num_walls']} aléatoires) | Vies: {config['lives']} | Comportement: {config['ghost_behavior']}"
        self.vis_config_label.config(text=text)

    def launch_visualization_with_config(self):
        """Lance une visualisation avec les paramètres actuels de configuration."""
        self.log("Lancement de la visualisation avec paramètres actuels...")
        try:
            # Construire la commande pour lancer visual_pacman_advanced.py avec les arguments
            args = [
                sys.executable, "visual_pacman_advanced.py",
                "--size", str(self.config['size']),
                "--num_ghosts", str(self.config['num_ghosts']),
                "--lives", str(self.config['lives']),
                "--ghost_behavior", self.config['ghost_behavior'],
                "--num_walls", str(self.config['num_walls']),
                "--fps", str(self.fps_var.get())
            ]
            if self.config['num_dots'] is not None:
                args.extend(["--num_dots", str(self.config['num_dots'])])
            self.log(f"Exécution: {' '.join(args)}")
            import subprocess
            subprocess.Popen(args)
        except Exception as e:
            self.log(f"Erreur lors du lancement de la visualisation: {e}")

    def launch_training_visualization(self):
        """Lance une visualisation en temps réel de l'entraînement (expérimental)."""
        self.log("Visualisation de l'entraînement en temps réel (expérimental) - non implémenté.")
        # Pour l'instant, on lance une visualisation normale avec un agent aléatoire
        self.launch_visualization_with_config()

    def launch_model_visualization(self):
        """Lance une visualisation avec le modèle entraîné (si disponible)."""
        if self.model is None:
            self.log("Aucun modèle entraîné chargé. Veuillez d'abord entraîner ou charger un modèle.")
            return
        self.log("Lancement de la visualisation avec modèle entraîné...")
        try:
            # Sauvegarder le modèle dans un fichier temporaire
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
                temp_path = f.name
            self.model.save(temp_path)
            self.log(f"Modèle sauvegardé temporairement sous {temp_path}")
            # Construire la commande
            args = [
                sys.executable, "visual_pacman_advanced.py",
                "--size", str(self.config['size']),
                "--num_ghosts", str(self.config['num_ghosts']),
                "--lives", str(self.config['lives']),
                "--ghost_behavior", self.config['ghost_behavior'],
                "--num_walls", str(self.config['num_walls']),
                "--fps", str(self.fps_var.get()),
                "--model_path", temp_path
            ]
            if self.config['num_dots'] is not None:
                args.extend(["--num_dots", str(self.config['num_dots'])])
            self.log(f"Exécution: {' '.join(args)}")
            import subprocess
            # Lancer le processus; le fichier temporaire sera supprimé après ? On laisse le script le supprimer après chargement.
            # Pour l'instant, on ne supprime pas (risque de corruption). On pourrait ajouter un nettoyage après fermeture.
            subprocess.Popen(args)
        except Exception as e:
            self.log(f"Erreur lors du lancement de la visualisation avec modèle: {e}")

    def run(self):
        """Lance la boucle principale de l'interface."""
        self.root.mainloop()


def main():
    lab = IALabAdvanced()
    lab.run()


if __name__ == '__main__':
    main()