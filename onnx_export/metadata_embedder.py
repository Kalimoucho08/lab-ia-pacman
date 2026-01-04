"""
Embedder de métadonnées pour les modèles ONNX.

Ce module permet d'incorporer des métadonnées d'environnement et de configuration
directement dans les fichiers ONNX via des propriétés de modèle et des annotations.
"""

import json
import os
import onnx
from onnx import helper, numpy_helper
from typing import Dict, Any, Optional, List, Union
import numpy as np
from datetime import datetime


class MetadataEmbedder:
    """
    Gère l'incorporation de métadonnées dans les modèles ONNX.
    
    Les métadonnées peuvent inclure:
    - Informations d'environnement (taille grille, actions, observations)
    - Configuration d'inférence (batch size, normalisation)
    - Documentation intégrée
    - Informations de version et de compatibilité
    """
    
    def __init__(self, onnx_model_path: str):
        """
        Initialise l'embedder avec un modèle ONNX.
        
        Args:
            onnx_model_path: Chemin vers le fichier ONNX
        """
        self.onnx_model_path = onnx_model_path
        self.model = onnx.load(onnx_model_path)
        self.metadata = {}
        
    def add_environment_metadata(
        self,
        grid_size: Optional[int] = None,
        num_ghosts: Optional[int] = None,
        num_power_pellets: Optional[int] = None,
        action_space: Optional[Dict] = None,
        observation_space: Optional[Dict] = None,
        reward_config: Optional[Dict] = None
    ):
        """
        Ajoute des métadonnées d'environnement Pac-Man.
        
        Args:
            grid_size: Taille de la grille (ex: 10)
            num_ghosts: Nombre de fantômes
            num_power_pellets: Nombre de power pellets
            action_space: Espace d'action (type, shape, valeurs)
            observation_space: Espace d'observation (type, shape, plages)
            reward_config: Configuration des récompenses
        """
        env_metadata = {
            "environment": "PacManMultiAgentEnv",
            "grid_size": grid_size,
            "num_ghosts": num_ghosts,
            "num_power_pellets": num_power_pellets,
            "action_space": action_space or {},
            "observation_space": observation_space or {},
            "reward_config": reward_config or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.metadata["environment"] = env_metadata
        return self
    
    def add_inference_config(
        self,
        batch_size: int = 1,
        normalize_input: bool = False,
        normalize_params: Optional[Dict] = None,
        deterministic: bool = True,
        device: str = "cpu"
    ):
        """
        Ajoute la configuration d'inférence.
        
        Args:
            batch_size: Taille de batch par défaut
            normalize_input: Si l'entrée doit être normalisée
            normalize_params: Paramètres de normalisation (mean, std)
            deterministic: Mode déterministe ou stochastique
            device: Device cible (cpu, cuda)
        """
        inference_config = {
            "batch_size": batch_size,
            "normalize_input": normalize_input,
            "normalize_params": normalize_params or {},
            "deterministic": deterministic,
            "device": device,
            "recommended_batch_sizes": [1, 4, 8, 16]
        }
        
        self.metadata["inference"] = inference_config
        return self
    
    def add_platform_compatibility(
        self,
        platforms: List[str] = None,
        requirements: Optional[Dict[str, Any]] = None
    ):
        """
        Ajoute des informations de compatibilité plateforme.
        
        Args:
            platforms: Liste des plateformes supportées
            requirements: Exigences spécifiques par plateforme
        """
        if platforms is None:
            platforms = ["pygame", "web", "unity", "generic"]
        
        platform_info = {
            "supported_platforms": platforms,
            "requirements": requirements or {},
            "web": {
                "framework": "TensorFlow.js",
                "conversion_tool": "onnx2tf",
                "recommended_opset": 13
            },
            "unity": {
                "framework": "Barracuda",
                "compatibility": "ONNX 1.7+",
                "limitations": "Certaines opérations peuvent nécessiter des adaptations"
            },
            "pygame": {
                "runtime": "ONNX Runtime Python",
                "version": ">=1.14.0"
            }
        }
        
        self.metadata["platform_compatibility"] = platform_info
        return self
    
    def add_training_info(
        self,
        algorithm: str,
        total_timesteps: int,
        policy_type: str,
        hyperparameters: Optional[Dict] = None,
        training_env: Optional[Dict] = None
    ):
        """
        Ajoute des informations sur l'entraînement.
        
        Args:
            algorithm: Algorithme RL (DQN, PPO, etc.)
            total_timesteps: Nombre total de timesteps d'entraînement
            policy_type: Type de politique (MlpPolicy, CnnPolicy)
            hyperparameters: Hyperparamètres d'entraînement
            training_env: Environnement d'entraînement
        """
        training_info = {
            "algorithm": algorithm,
            "total_timesteps": total_timesteps,
            "policy_type": policy_type,
            "hyperparameters": hyperparameters or {},
            "training_env": training_env or {},
            "framework": "Stable-Baselines3",
            "export_tool": "ONNXConverter"
        }
        
        self.metadata["training"] = training_info
        return self
    
    def add_custom_properties(self, properties: Dict[str, Any]):
        """
        Ajoute des propriétés personnalisées.
        
        Args:
            properties: Dictionnaire de propriétés personnalisées
        """
        if "custom" not in self.metadata:
            self.metadata["custom"] = {}
        
        self.metadata["custom"].update(properties)
        return self
    
    def _create_model_properties(self) -> List[helper.ModelProto]:
        """
        Crée les propriétés de modèle ONNX à partir des métadonnées.
        
        Returns:
            Liste de propriétés de modèle
        """
        properties = []
        
        # Convertir les métadonnées en chaîne JSON
        metadata_str = json.dumps(self.metadata, indent=2)
        
        # Propriété pour les métadonnées complètes
        properties.append(
            helper.make_attribute(
                "metadata",
                metadata_str
            )
        )
        
        # Propriétés individuelles pour un accès facile
        if "environment" in self.metadata:
            env = self.metadata["environment"]
            if env.get("grid_size"):
                properties.append(
                    helper.make_attribute("grid_size", env["grid_size"])
                )
            if env.get("num_ghosts"):
                properties.append(
                    helper.make_attribute("num_ghosts", env["num_ghosts"])
                )
        
        if "training" in self.metadata:
            training = self.metadata["training"]
            properties.append(
                helper.make_attribute("algorithm", training["algorithm"])
            )
            properties.append(
                helper.make_attribute("policy_type", training["policy_type"])
            )
        
        # Propriété de version
        properties.append(
            helper.make_attribute("export_version", "1.0.0")
        )
        properties.append(
            helper.make_attribute("export_timestamp", datetime.now().isoformat())
        )
        
        return properties
    
    def embed_into_model(self, output_path: Optional[str] = None) -> str:
        """
        Incorpore les métadonnées dans le modèle ONNX.
        
        Args:
            output_path: Chemin de sortie (défaut: remplace le fichier d'origine)
            
        Returns:
            Chemin du fichier ONNX modifié
        """
        if output_path is None:
            output_path = self.onnx_model_path
        
        # Créer les propriétés de modèle
        properties = self._create_model_properties()
        
        # Ajouter les propriétés au modèle
        for prop in properties:
            self.model.metadata_props.append(prop)
        
        # Ajouter des informations de documentation
        doc_string = f"Pac-Man RL Model - {self.metadata.get('training', {}).get('algorithm', 'Unknown')}"
        if self.model.doc_string:
            self.model.doc_string += f"\n{doc_string}"
        else:
            self.model.doc_string = doc_string
        
        # Sauvegarder le modèle modifié
        onnx.save(self.model, output_path)
        
        print(f"Métadonnées incorporées dans: {output_path}")
        print(f"Taille des métadonnées: {len(json.dumps(self.metadata))} bytes")
        
        return output_path
    
    def extract_metadata(self) -> Dict[str, Any]:
        """
        Extrait les métadonnées d'un modèle ONNX.
        
        Returns:
            Dictionnaire des métadonnées extraites
        """
        extracted = {}
        
        # Extraire des propriétés de modèle
        for prop in self.model.metadata_props:
            key = prop.key
            value = prop.value
            
            # Essayer de parser JSON pour la propriété 'metadata'
            if key == "metadata":
                try:
                    extracted = json.loads(value)
                except json.JSONDecodeError:
                    extracted["raw_metadata"] = value
            else:
                extracted[key] = value
        
        # Extraire du doc_string
        if self.model.doc_string:
            extracted["doc_string"] = self.model.doc_string
        
        return extracted
    
    def save_metadata_json(self, output_path: str):
        """
        Sauvegarde les métadonnées dans un fichier JSON séparé.
        
        Args:
            output_path: Chemin du fichier JSON de sortie
        """
        with open(output_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        print(f"Métadonnées sauvegardées dans: {output_path}")
        return output_path
    
    @classmethod
    def create_from_sb3_model(
        cls,
        model_path: str,
        onnx_output_path: str,
        env_config: Optional[Dict] = None
    ) -> 'MetadataEmbedder':
        """
        Crée un embedder à partir d'un modèle Stable-Baselines3.
        
        Args:
            model_path: Chemin vers le modèle SB3
            onnx_output_path: Chemin de sortie ONNX
            env_config: Configuration d'environnement
            
        Returns:
            Instance de MetadataEmbedder
        """
        # Simuler la conversion (dépend de onnx_converter)
        from .onnx_converter import ONNXConverter
        
        converter = ONNXConverter(model_path)
        converter.convert_to_onnx(onnx_output_path)
        
        # Créer l'embedder
        embedder = cls(onnx_output_path)
        
        # Ajouter les métadonnées par défaut
        if env_config:
            embedder.add_environment_metadata(**env_config)
        
        # Inférer les informations d'entraînement
        embedder.add_training_info(
            algorithm=converter.metadata.get("algorithm", "Unknown"),
            total_timesteps=10000,  # Par défaut
            policy_type=converter.metadata.get("policy_type", "MlpPolicy"),
            hyperparameters={}
        )
        
        embedder.add_inference_config()
        embedder.add_platform_compatibility()
        
        return embedder


def embed_metadata_cli():
    """Interface en ligne de commande pour l'embedding de métadonnées."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Incorporer des métadonnées dans un modèle ONNX")
    parser.add_argument("onnx_model", help="Chemin vers le modèle ONNX")
    parser.add_argument("--output", help="Chemin de sortie (défaut: remplace l'entrée)")
    parser.add_argument("--metadata_json", help="Fichier JSON de métadonnées à incorporer")
    parser.add_argument("--extract", action="store_true", help="Extraire les métadonnées existantes")
    
    args = parser.parse_args()
    
    embedder = MetadataEmbedder(args.onnx_model)
    
    if args.extract:
        metadata = embedder.extract_metadata()
        print("Métadonnées extraites:")
        print(json.dumps(metadata, indent=2))
        
        # Sauvegarder dans un fichier
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"Métadonnées sauvegardées dans: {args.output}")
    else:
        # Charger les métadonnées depuis JSON
        if args.metadata_json:
            with open(args.metadata_json, 'r') as f:
                metadata = json.load(f)
            
            # Appliquer les métadonnées
            if "environment" in metadata:
                embedder.add_environment_metadata(**metadata["environment"])
            if "training" in metadata:
                embedder.add_training_info(**metadata["training"])
            if "inference" in metadata:
                embedder.add_inference_config(**metadata["inference"])
        
        # Incorporer les métadonnées
        output_path = embedder.embed_into_model(args.output)
        
        # Sauvegarder également en JSON séparé
        json_path = output_path.replace('.onnx', '_metadata.json')
        embedder.save_metadata_json(json_path)


if __name__ == "__main__":
    # Exemple d'utilisation
    embed_metadata_cli()