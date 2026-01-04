"""
Adaptateur multi-plateforme pour les modèles ONNX.

Ce module adapte les modèles ONNX pour différentes plateformes:
- Pygame classique (ONNX Runtime Python)
- Web (TensorFlow.js via onnx2tf)
- Unity (Barracuda)
- Autres labyrinthes (interface générique)
"""

import os
import subprocess
import json
import tempfile
import shutil
from typing import Dict, Any, Optional, Tuple, List
import onnx
import onnxruntime as ort
import numpy as np


class PlatformAdapter:
    """
    Adapte les modèles ONNX pour différentes plateformes cibles.
    """
    
    def __init__(self, onnx_model_path: str):
        """
        Initialise l'adaptateur avec un modèle ONNX.
        
        Args:
            onnx_model_path: Chemin vers le fichier ONNX
        """
        self.onnx_model_path = onnx_model_path
        self.model = onnx.load(onnx_model_path)
        self.metadata = self._extract_metadata()
        
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extrait les métadonnées du modèle ONNX."""
        metadata = {}
        
        for prop in self.model.metadata_props:
            if prop.key == "metadata":
                try:
                    metadata = json.loads(prop.value)
                except json.JSONDecodeError:
                    pass
        
        return metadata
    
    def adapt_for_pygame(
        self,
        output_dir: str,
        include_wrapper: bool = True,
        optimize: bool = True
    ) -> Dict[str, str]:
        """
        Adapte le modèle pour Pygame avec ONNX Runtime Python.
        
        Args:
            output_dir: Répertoire de sortie
            include_wrapper: Inclure un wrapper Python pour l'inférence
            optimize: Optimiser le modèle pour l'inférence
            
        Returns:
            Dictionnaire avec chemins des fichiers générés
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Copier le modèle ONNX
        model_name = os.path.splitext(os.path.basename(self.onnx_model_path))[0]
        pygame_model_path = os.path.join(output_dir, f"{model_name}_pygame.onnx")
        shutil.copy2(self.onnx_model_path, pygame_model_path)
        
        # Optimiser le modèle si demandé
        if optimize:
            pygame_model_path = self._optimize_for_inference(
                pygame_model_path,
                output_dir,
                target="cpu"
            )
        
        results = {
            "onnx_model": pygame_model_path,
            "platform": "pygame",
            "runtime": "onnxruntime"
        }
        
        # Générer un wrapper Python
        if include_wrapper:
            wrapper_path = os.path.join(output_dir, "pygame_inference_wrapper.py")
            self._generate_pygame_wrapper(wrapper_path, pygame_model_path)
            results["wrapper"] = wrapper_path
        
        print(f"Adaptation Pygame terminée: {pygame_model_path}")
        return results
    
    def adapt_for_web(
        self,
        output_dir: str,
        framework: str = "tensorflowjs",
        optimize: bool = True
    ) -> Dict[str, str]:
        """
        Adapte le modèle pour le web (TensorFlow.js).
        
        Args:
            output_dir: Répertoire de sortie
            framework: Framework cible (tensorflowjs, onnxjs)
            optimize: Optimiser le modèle
            
        Returns:
            Dictionnaire avec chemins des fichiers générés
        """
        os.makedirs(output_dir, exist_ok=True)
        
        if framework == "tensorflowjs":
            return self._convert_to_tensorflowjs(output_dir, optimize)
        elif framework == "onnxjs":
            return self._prepare_for_onnxjs(output_dir)
        else:
            raise ValueError(f"Framework web non supporté: {framework}")
    
    def _convert_to_tensorflowjs(
        self,
        output_dir: str,
        optimize: bool
    ) -> Dict[str, str]:
        """
        Convertit le modèle ONNX en TensorFlow.js via onnx2tf.
        
        Args:
            output_dir: Répertoire de sortie
            optimize: Optimiser le modèle
            
        Returns:
            Dictionnaire avec chemins des fichiers générés
        """
        # Vérifier si onnx2tf est disponible
        try:
            import onnx2tf
            onnx2tf_available = True
        except ImportError:
            onnx2tf_available = False
            print("Avertissement: onnx2tf non installé. Installation recommandée:")
            print("pip install onnx2tf")
        
        # Créer un modèle optimisé pour la conversion
        if optimize:
            optimized_path = os.path.join(output_dir, "optimized_for_tfjs.onnx")
            self._optimize_for_web(self.onnx_model_path, optimized_path)
            source_model = optimized_path
        else:
            source_model = self.onnx_model_path
        
        # Chemin de sortie TensorFlow.js
        tfjs_dir = os.path.join(output_dir, "tfjs_model")
        
        # Commande de conversion
        conversion_cmd = [
            "onnx2tf", "-i", source_model, "-o", tfjs_dir,
            "--output_signature_defs", "true"
        ]
        
        results = {
            "platform": "web",
            "framework": "tensorflowjs",
            "source_onnx": source_model,
            "target_dir": tfjs_dir,
            "conversion_command": " ".join(conversion_cmd)
        }
        
        print(f"Adaptation Web (TensorFlow.js) préparée: {tfjs_dir}")
        print(f"Exécutez la commande: {' '.join(conversion_cmd)}")
        
        return results
    
    def _prepare_for_onnxjs(self, output_dir: str) -> Dict[str, str]:
        """
        Prépare le modèle pour ONNX.js (runtime ONNX dans le navigateur).
        
        Args:
            output_dir: Répertoire de sortie
            
        Returns:
            Dictionnaire avec chemins des fichiers générés
        """
        # Optimiser pour le web
        optimized_path = os.path.join(output_dir, "optimized_for_onnxjs.onnx")
        self._optimize_for_web(self.onnx_model_path, optimized_path)
        
        results = {
            "platform": "web",
            "framework": "onnxjs",
            "onnx_model": optimized_path
        }
        
        print(f"Adaptation Web (ONNX.js) terminée: {optimized_path}")
        return results
    
    def adapt_for_unity(
        self,
        output_dir: str,
        barracuda_compatible: bool = True
    ) -> Dict[str, str]:
        """
        Adapte le modèle pour Unity avec Barracuda.
        
        Args:
            output_dir: Répertoire de sortie
            barracuda_compatible: Assurer la compatibilité Barracuda
            
        Returns:
            Dictionnaire avec chemins des fichiers générés
        """
        os.makedirs(output_dir, exist_ok=True)
        
        model_name = os.path.splitext(os.path.basename(self.onnx_model_path))[0]
        unity_model_path = os.path.join(output_dir, f"{model_name}_unity.onnx")
        
        # Vérifier la compatibilité Barracuda
        if barracuda_compatible:
            compatibility = self._check_barracuda_compatibility()
            if not compatibility["compatible"]:
                print(f"Avertissement: Modèle potentiellement incompatible avec Barracuda")
                print(f"Problèmes: {compatibility['issues']}")
            
            # Appliquer des transformations pour Barracuda si nécessaire
            unity_model_path = self._make_barracuda_compatible(
                self.onnx_model_path,
                unity_model_path
            )
        else:
            shutil.copy2(self.onnx_model_path, unity_model_path)
        
        results = {
            "platform": "unity",
            "framework": "barracuda",
            "onnx_model": unity_model_path,
            "compatibility_check": self._check_barracuda_compatibility() if barracuda_compatible else None
        }
        
        print(f"Adaptation Unity terminée: {unity_model_path}")
        return results
    
    def adapt_for_generic(
        self,
        output_dir: str,
        interface_type: str = "rest"
    ) -> Dict[str, str]:
        """
        Adapte le modèle pour une interface générique (REST, gRPC, etc.).
        
        Args:
            output_dir: Répertoire de sortie
            interface_type: Type d'interface (rest, grpc, socket)
            
        Returns:
            Dictionnaire avec chemins des fichiers générés
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Copier le modèle
        model_name = os.path.splitext(os.path.basename(self.onnx_model_path))[0]
        generic_model_path = os.path.join(output_dir, f"{model_name}_generic.onnx")
        shutil.copy2(self.onnx_model_path, generic_model_path)
        
        results = {
            "platform": "generic",
            "interface_type": interface_type,
            "onnx_model": generic_model_path
        }
        
        print(f"Adaptation générique ({interface_type}) terminée: {generic_model_path}")
        return results
    
    def _optimize_for_inference(
        self,
        model_path: str,
        output_dir: str,
        target: str = "cpu"
    ) -> str:
        """
        Optimise le modèle ONNX pour l'inférence.
        
        Args:
            model_path: Chemin du modèle
            output_dir: Répertoire de sortie
            target: Cible d'optimisation (cpu, gpu)
            
        Returns:
            Chemin du modèle optimisé
        """
        optimized_path = os.path.join(
            output_dir,
            f"optimized_{target}_{os.path.basename(model_path)}"
        )
        
        # Pour l'instant, simplement copier le modèle
        # Dans une implémentation réelle, utiliser ONNX Runtime Optimizer
        shutil.copy2(model_path, optimized_path)
        
        print(f"Modèle optimisé pour {target}: {optimized_path}")
        return optimized_path
    
    def _optimize_for_web(self, input_path: str, output_path: str):
        """
        Optimise le modèle pour le web (réduction de taille, compatibilité).
        
        Args:
            input_path: Chemin d'entrée
            output_path: Chemin de sortie
        """
        model = onnx.load(input_path)
        
        # Simplifier le modèle si onnxsim est disponible
        try:
            import onnxsim
            model_simp, check = onnxsim.simplify(model)
            if check:
                onnx.save(model_simp, output_path)
                print(f"Modèle simplifié pour le web: {output_path}")
                return
        except ImportError:
            pass
        
        # Fallback: copier le modèle original
        shutil.copy2(input_path, output_path)
    
    def _check_barracuda_compatibility(self) -> Dict[str, Any]:
        """
        Vérifie la compatibilité du modèle avec Barracuda.
        
        Returns:
            Dictionnaire avec résultats de compatibilité
        """
        issues = []
        
        # Vérifier les opérations supportées par Barracuda
        problematic_ops = [
            "RandomNormal", "RandomUniform", "Dropout",
            "Loop", "Scan", "If", "Sequence"
        ]
        
        for node in self.model.graph.node:
            if node.op_type in problematic_ops:
                issues.append(f"Opération {node.op_type} peut être incompatible")
        
        # Vérifier les types de données
        for tensor in self.model.graph.initializer:
            if tensor.data_type not in [1, 7]:  # FLOAT, FLOAT16
            from onnxruntime.transformers import optimizer
            from onnxruntime.transformers.fusion_options import FusionOptions
            
            # Options d'optimisation
            opt_options = FusionOptions(target.device)
            
            # Optimiser le modèle
            optimized_model = optimizer.optimize_model(
                model_path,
                model_type='bert',  # Type générique
                num_heads=0,  # Non applicable
                hidden_size=0,
                optimization_options=opt_options
            )
            
            optimized_model.save_model_to_file(optimized_path)
            print(f"Modèle optimisé pour {target}: {optimized_path}")
            
        except ImportError:
            print("Avertissement: ONNX Runtime Transformer Optimizer non disponible")
            print("Utilisation du modèle original")
            shutil.copy2(model_path, optimized_path)
        
        return optimized_path
    
    def _optimize_for_web(self, input_path: str, output_path: str):
        """
        Optimise le modèle pour le web (réduction de taille, compatibilité).
        
        Args:
            input_path: Chemin d'entrée
            output_path: Chemin de sortie
        """
        model = onnx.load(input_path)
        
        # Simplifier le modèle (fusion d'opérations, etc.)
        try:
            import onnxsim
            model_simp, check = onnxsim.simplify(model)
            if check:
                onnx.save(model_simp, output_path)
                print(f"Modèle simplifié pour le web: {output_path}")
                return
        except ImportError:
            pass
        
        # Fallback: copier le modèle original
        shutil.copy2(input_path, output_path)
    
    def _check_barracuda_compatibility(self) -> Dict[str, Any]:
        """
        Vérifie la compatibilité du modèle avec Barracuda.
        
        Returns:
            Dictionnaire avec résultats de compatibilité
        """
        issues = []
        
        # Vérifier les opérations supportées par Barracuda
        # Liste des opérations potentiellement problématiques
        problematic_ops = [
            "RandomNormal", "RandomUniform", "Dropout",
            "Loop", "Scan", "If", "Sequence"
        ]
        
        for node in self.model.graph.node:
            if node.op_type in problematic_ops:
                issues.append(f"Opération {node.op_type} peut être incompatible")
        
        # Vérifier les types de données
        for tensor in self.model.graph.initializer:
            if tensor.data_type not in [1, 7]:  # FLOAT, FLOAT16
                issues.append(f"Type de données non supporté: {tensor.data_type}")
        
        return {
            "compatible": len(issues) == 0,
            "issues": issues,
            "op_count": len(self.model.graph.node),
            "model_size_mb": os.path.getsize(self.onnx_model_path) / (1024 * 1024)
        }
    
    def _make_barracuda_compatible(self, input_path: str, output_path: str) -> str:
        """
        Rend le modèle compatible avec Barracuda.
        
        Args:
            input_path: Chemin d'entrée
            output_path: Chemin de sortie
            
        Returns:
            Chemin du modèle compatible
        """
        # Pour l'instant, simplement copier le modèle
        # Dans une implémentation réelle, appliquer des transformations
        shutil.copy2(input_path, output_path)
        return output_path
    
    # Méthodes de génération de wrappers (implémentations simplifiées)
    
    def _generate_pygame_wrapper(self, output_path: str, model_path: str):
        """Génère un wrapper Python pour Pygame."""
        wrapper_code = '''"""
Wrapper d'inférence ONNX pour Pygame Pac-Man.
"""

import numpy as np
import onnxruntime as ort


class PacManONNXInference:
    """Classe pour l'inférence ONNX dans Pygame."""
    
    def __init__(self, model_path):
        """
        Initialise le runtime ONNX.
        
        Args:
            model_path: Chemin vers le modèle ONNX
        """
        self.session = ort.InferenceSession(model_path)
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        
        # Métadonnées d'environnement (à adapter)
        self.grid_size = 10
        self.num_actions = 4  # Haut, Bas, Gauche, Droite
        
    def preprocess_observation(self, observation):
        """
        Prétraite l'observation pour l'inférence.
        
        Args:
            observation: Observation brute du jeu
            
        Returns:
            Observation prétraitée
        """
        # Convertir en tableau numpy et ajouter une dimension batch
        obs_array = np.array(observation, dtype=np.float32)
        if len(obs_array.shape) == 1:
            obs_array = obs_array.reshape(1, -1)
        elif len(obs_array.shape) == 3:
            # Image: (H, W, C) -> (1, C, H, W)
            obs_array = np.transpose(obs_array, (2, 0, 1))
            obs_array = np.expand_dims(obs_array, axis=0)
        
        return obs_array
    
    def predict(self, observation):
        """
        Prédit l'action à partir d'une observation.
        
        Args:
            observation: Observation du jeu
            
        Returns:
            Action prédite (indice)
        """
        # Pr