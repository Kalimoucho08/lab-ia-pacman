"""
Convertisseur ONNX universel pour les modèles Stable-Baselines3.

Ce module convertit les modèles RL (DQN, PPO, A2C, SAC, TD3) en format ONNX
avec support des politiques MlpPolicy et CnnPolicy.
"""

import os
import sys
import warnings
import numpy as np
from typing import Dict, Any, Optional, Tuple, Union
import torch
import onnx
import onnxruntime as ort
from stable_baselines3 import DQN, PPO, A2C, SAC, TD3
from stable_baselines3.common.policies import BasePolicy
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor


class ONNXConverter:
    """
    Convertisseur ONNX pour les modèles Stable-Baselines3.
    
    Attributes:
        model: Modèle Stable-Baselines3 chargé
        policy: Politique du modèle (actor ou critic selon l'algorithme)
        observation_space: Espace d'observation
        action_space: Espace d'action
        metadata: Métadonnées d'environnement
    """
    
    def __init__(self, model_path: str, algorithm: str = "auto"):
        """
        Initialise le convertisseur avec un modèle sauvegardé.
        
        Args:
            model_path: Chemin vers le fichier .zip du modèle
            algorithm: Algorithme utilisé (DQN, PPO, A2C, SAC, TD3) ou "auto" pour détection
        """
        self.model_path = model_path
        self.algorithm = algorithm
        self.model = None
        self.policy = None
        self.observation_space = None
        self.action_space = None
        self.metadata = {}
        
        # Charger le modèle
        self._load_model()
        
    def _load_model(self):
        """Charge le modèle Stable-Baselines3 depuis le fichier."""
        if self.algorithm == "auto":
            # Détection automatique basée sur le nom de fichier
            filename = os.path.basename(self.model_path).lower()
            if "dqn" in filename:
                self.algorithm = "DQN"
            elif "ppo" in filename:
                self.algorithm = "PPO"
            elif "a2c" in filename:
                self.algorithm = "A2C"
            elif "sac" in filename:
                self.algorithm = "SAC"
            elif "td3" in filename:
                self.algorithm = "TD3"
            else:
                raise ValueError("Impossible de détecter l'algorithme. Spécifiez-le explicitement.")
        
        # Mapping algorithme -> classe
        algorithm_map = {
            "DQN": DQN,
            "PPO": PPO,
            "A2C": A2C,
            "SAC": SAC,
            "TD3": TD3
        }
        
        if self.algorithm not in algorithm_map:
            raise ValueError(f"Algorithme non supporté: {self.algorithm}")
        
        print(f"Chargement du modèle {self.algorithm} depuis {self.model_path}")
        self.model = algorithm_map[self.algorithm].load(self.model_path)
        
        # Extraire la politique et les espaces
        self.policy = self.model.policy
        self.observation_space = self.model.observation_space
        self.action_space = self.model.action_space
        
        # Collecter les métadonnées de base
        self.metadata = {
            "algorithm": self.algorithm,
            "policy_type": self.policy.__class__.__name__,
            "observation_shape": self.observation_space.shape,
            "action_shape": self.action_space.shape,
            "model_path": self.model_path,
            "normalize": hasattr(self.model, "normalize") and self.model.normalize is not None
        }
        
    def _get_policy_network(self) -> torch.nn.Module:
        """
        Extrait le réseau de neurones approprié pour la conversion ONNX.
        
        Returns:
            Module PyTorch représentant le réseau de décision
        """
        if self.algorithm in ["DQN", "PPO", "A2C"]:
            # Pour les algorithmes à politique déterministe/stochastique
            # On exporte le réseau acteur (policy)
            if hasattr(self.policy, "mlp_extractor"):
                # Architecture avec extracteur MLP
                return self.policy.mlp_extractor
            elif hasattr(self.policy, "features_extractor"):
                # Architecture avec extracteur de features
                return torch.nn.Sequential(
                    self.policy.features_extractor,
                    self.policy.mlp_extractor if hasattr(self.policy, "mlp_extractor") else self.policy.action_net
                )
            else:
                # Fallback: utiliser le réseau d'action
                return self.policy.action_net
        elif self.algorithm in ["SAC", "TD3"]:
            # Pour SAC/TD3, exporter l'acteur (actor)
            return self.policy.actor
        else:
            raise ValueError(f"Algorithme {self.algorithm} non supporté pour l'extraction de réseau")
    
    def _create_dummy_input(self, batch_size: int = 1) -> torch.Tensor:
        """
        Crée une entrée factice pour le tracing ONNX.
        
        Args:
            batch_size: Taille du batch pour l'inférence
            
        Returns:
            Tensor PyTorch de forme appropriée
        """
        obs_shape = self.observation_space.shape
        dummy_shape = (batch_size,) + obs_shape
        
        # Générer des valeurs dans la plage appropriée
        if hasattr(self.observation_space, "low") and hasattr(self.observation_space, "high"):
            low = self.observation_space.low
            high = self.observation_space.high
            dummy_input = torch.tensor(
                np.random.uniform(low, high, size=dummy_shape).astype(np.float32)
            )
        else:
            # Espace d'observation discret ou autre
            dummy_input = torch.randn(dummy_shape, dtype=torch.float32)
        
        return dummy_input
    
    def convert_to_onnx(
        self,
        output_path: str,
        opset_version: int = 13,
        dynamic_axes: Optional[Dict] = None,
        verbose: bool = False
    ) -> str:
        """
        Convertit le modèle en format ONNX.
        
        Args:
            output_path: Chemin de sortie pour le fichier .onnx
            opset_version: Version Opset ONNX (défaut: 13)
            dynamic_axes: Axes dynamiques pour le batch size
            verbose: Afficher les détails de conversion
            
        Returns:
            Chemin du fichier ONNX généré
        """
        # Extraire le réseau
        policy_net = self._get_policy_network()
        
        # Créer l'entrée factice
        dummy_input = self._create_dummy_input()
        
        # Configurer les axes dynamiques par défaut
        if dynamic_axes is None:
            dynamic_axes = {
                "input": {0: "batch_size"},
                "output": {0: "batch_size"}
            }
        
        # Exporter vers ONNX
        print(f"Conversion du modèle {self.algorithm} vers ONNX...")
        
        torch.onnx.export(
            policy_net,
            dummy_input,
            output_path,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes=dynamic_axes,
            opset_version=opset_version,
            verbose=verbose,
            export_params=True,
            do_constant_folding=True
        )
        
        # Valider le fichier ONNX généré
        onnx_model = onnx.load(output_path)
        onnx.checker.check_model(onnx_model)
        
        print(f"Modèle ONNX sauvegardé: {output_path}")
        print(f"Taille du modèle: {os.path.getsize(output_path) / 1024:.2f} KB")
        
        return output_path
    
    def test_onnx_inference(
        self,
        onnx_path: str,
        test_observations: Optional[np.ndarray] = None,
        num_tests: int = 5
    ) -> Dict[str, Any]:
        """
        Teste l'inférence ONNX et compare avec le modèle original.
        
        Args:
            onnx_path: Chemin vers le fichier ONNX
            test_observations: Observations de test (optionnel)
            num_tests: Nombre de tests à effectuer
            
        Returns:
            Dictionnaire avec résultats de validation
        """
        # Charger le runtime ONNX
        ort_session = ort.InferenceSession(onnx_path)
        
        # Générer des observations de test
        if test_observations is None:
            test_observations = []
            for _ in range(num_tests):
                dummy = self._create_dummy_input(batch_size=1).numpy()
                test_observations.append(dummy)
            test_observations = np.concatenate(test_observations, axis=0)
        
        # Inférence avec le modèle original
        with torch.no_grad():
            original_outputs = []
            for obs in test_observations:
                obs_tensor = torch.tensor(obs[np.newaxis, ...], dtype=torch.float32)
                output = self._get_policy_network()(obs_tensor)
                original_outputs.append(output.numpy())
        
        # Inférence avec ONNX Runtime
        onnx_outputs = []
        for obs in test_observations:
            ort_inputs = {"input": obs[np.newaxis, ...].astype(np.float32)}
            ort_output = ort_session.run(None, ort_inputs)[0]
            onnx_outputs.append(ort_output)
        
        # Calculer la différence
        max_diff = 0.0
        mean_diff = 0.0
        for orig, onnx in zip(original_outputs, onnx_outputs):
            diff = np.abs(orig - onnx).max()
            max_diff = max(max_diff, diff)
            mean_diff += diff
        
        mean_diff /= len(original_outputs)
        
        results = {
            "onnx_path": onnx_path,
            "test_samples": len(test_observations),
            "max_difference": float(max_diff),
            "mean_difference": float(mean_diff),
            "compatible": max_diff < 1e-5,  # Tolérance numérique
            "original_output_shape": original_outputs[0].shape,
            "onnx_output_shape": onnx_outputs[0].shape
        }
        
        print(f"Test d'inférence ONNX:")
        print(f"  Échantillons testés: {results['test_samples']}")
        print(f"  Différence max: {results['max_difference']:.6f}")
        print(f"  Différence moyenne: {results['mean_difference']:.6f}")
        print(f"  Compatible: {results['compatible']}")
        
        return results
    
    def export_complete(
        self,
        output_dir: str,
        model_name: Optional[str] = None,
        include_metadata: bool = True,
        test_conversion: bool = True
    ) -> Dict[str, str]:
        """
        Export complet avec métadonnées et tests.
        
        Args:
            output_dir: Répertoire de sortie
            model_name: Nom du modèle (défaut: basé sur le fichier d'entrée)
            include_metadata: Inclure les métadonnées dans un fichier séparé
            test_conversion: Tester la conversion après export
            
        Returns:
            Dictionnaire avec chemins des fichiers générés
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Générer le nom du modèle
        if model_name is None:
            base_name = os.path.splitext(os.path.basename(self.model_path))[0]
            model_name = f"{base_name}_onnx"
        
        # Chemins de sortie
        onnx_path = os.path.join(output_dir, f"{model_name}.onnx")
        metadata_path = os.path.join(output_dir, f"{model_name}_metadata.json")
        
        # Conversion ONNX
        onnx_file = self.convert_to_onnx(onnx_path)
        
        # Métadonnées
        if include_metadata:
            import json
            full_metadata = {
                **self.metadata,
                "export_timestamp": np.datetime64('now').astype(str),
                "onnx_opset": 13,
                "input_shape": self.observation_space.shape,
                "output_shape": self.action_space.shape,
                "platform_targets": ["pygame", "web", "unity", "generic"],
                "normalization_required": self.metadata.get("normalize", False)
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(full_metadata, f, indent=2)
            
            print(f"Métadonnées sauvegardées: {metadata_path}")
        
        # Test de conversion
        test_results = None
        if test_conversion:
            test_results = self.test_onnx_inference(onnx_file)
        
        # Résultats
        results = {
            "onnx_model": onnx_file,
            "metadata": metadata_path if include_metadata else None,
            "test_results": test_results,
            "model_name": model_name
        }
        
        return results


def convert_sb3_model(
    model_path: str,
    output_dir: str = "./onnx_exports",
    algorithm: str = "auto",
    **kwargs
) -> Dict[str, Any]:
    """
    Fonction utilitaire pour convertir un modèle Stable-Baselines3 en ONNX.
    
    Args:
        model_path: Chemin vers le modèle .zip
        output_dir: Répertoire de sortie
        algorithm: Algorithme RL
        **kwargs: Arguments supplémentaires pour ONNXConverter
        
    Returns:
        Résultats de la conversion
    """
    converter = ONNXConverter(model_path, algorithm)
    results = converter.export_complete(output_dir, **kwargs)
    return results


if __name__ == "__main__":
    # Exemple d'utilisation
    import argparse
    
    parser = argparse.ArgumentParser(description="Convertir un modèle Stable-Baselines3 en ONNX")
    parser.add_argument("model_path", help="Chemin vers le modèle .zip")
    parser.add_argument("--output_dir", default="./onnx_exports", help="Répertoire de sortie")
    parser.add_argument("--algorithm", default="auto", 
                       choices=["auto", "DQN", "PPO", "A2C", "SAC", "TD3"],
                       help="Algorithme RL")
    parser.add_argument("--no_test", action="store_true", help="Désactiver les tests")
    parser.add_argument("--no_metadata", action="store_true", help="Exclure les métadonnées")
    
    args = parser.parse_args()
    
    results = convert_sb3_model(
        args.model_path,
        output_dir=args.output_dir,
        algorithm=args.algorithm,
        include_metadata=not args.no_metadata,
        test_conversion=not args.no_test
    )
    
    print("\n" + "="*50)
    print("Export ONNX terminé avec succès!")
    print(f"Modèle ONNX: {results['onnx_model']}")
    if results['metadata']:
        print(f"Métadonnées: {results['metadata']}")
    print("="*50)