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
        shutil.copy2(input_path, output_path)
        return output_path
    
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
        
    def predict(self, observation):
        """
        Prédit l'action à partir d'une observation.
        
        Args:
            observation: Observation du jeu (tableau numpy)
            
        Returns:
            Action prédite (indice)
        """
        # Ajouter une dimension batch si nécessaire
        if len(observation.shape) == 1:
            observation = observation.reshape(1, -1)
        
        # Inférence
        outputs = self.session.run(
            [self.output_name],
            {self.input_name: observation.astype(np.float32)}
        )
        
        # Extraire l'action (supposer que la sortie est logits)
        action_logits = outputs[0][0]
        action = np.argmax(action_logits)
        
        return action
    
    def predict_batch(self, observations):
        """
        Prédit des actions pour un batch d'observations.
        
        Args:
            observations: Batch d'observations
            
        Returns:
            Actions prédites
        """
        outputs = self.session.run(
            [self.output_name],
            {self.input_name: observations.astype(np.float32)}
        )
        
        actions = np.argmax(outputs[0], axis=1)
        return actions


# Exemple d'utilisation
if __name__ == "__main__":
    # Charger le modèle
    model = PacManONNXInference("model.onnx")
    
    # Exemple d'observation (à adapter selon votre environnement)
    dummy_obs = np.random.randn(1, 100).astype(np.float32)  # Exemple: 100 features
    
    # Prédiction
    action = model.predict(dummy_obs)
    print(f"Action prédite: {action}")
'''
        
        with open(output_path, 'w') as f:
            f.write(wrapper_code)
        
        print(f"Wrapper Pygame généré: {output_path}")
    
    def export_all_platforms(
        self,
        base_output_dir: str,
        platforms: List[str] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        Exporte le modèle pour toutes les plateformes supportées.
        
        Args:
            base_output_dir: Répertoire de base de sortie
            platforms: Liste des plateformes (défaut: toutes)
            
        Returns:
            Dictionnaire avec résultats par plateforme
        """
        if platforms is None:
            platforms = ["pygame", "web", "unity", "generic"]
        
        results = {}
        
        for platform in platforms:
            platform_dir = os.path.join(base_output_dir, platform)
            os.makedirs(platform_dir, exist_ok=True)
            
            try:
                if platform == "pygame":
                    platform_results = self.adapt_for_pygame(platform_dir)
                elif platform == "web":
                    platform_results = self.adapt_for_web(platform_dir)
                elif platform == "unity":
                    platform_results = self.adapt_for_unity(platform_dir)
                elif platform == "generic":
                    platform_results = self.adapt_for_generic(platform_dir)
                else:
                    print(f"Plateforme non supportée ignorée: {platform}")
                    continue
                
                results[platform] = platform_results
                
            except Exception as e:
                print(f"Erreur lors de l'adaptation pour {platform}: {e}")
                results[platform] = {"error": str(e)}
        
        # Générer un rapport d'export
        report_path = os.path.join(base_output_dir, "export_report.json")
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Rapport d'export généré: {report_path}")
        return results


def adapt_model_cli():
    """Interface en ligne de commande pour l'adaptation de modèles."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Adapter un modèle ONNX pour différentes plateformes")
    parser.add_argument("onnx_model", help="Chemin vers le modèle ONNX")
    parser.add_argument("--output_dir", default="./platform_exports", help="Répertoire de sortie")
    parser.add_argument("--platforms", nargs="+",
                       choices=["pygame", "web", "unity", "generic", "all"],
                       default=["all"], help="Plateformes cibles")
    
    args = parser.parse_args()
    
    # Convertir "all" en liste de toutes les plateformes
    if "all" in args.platforms:
        args.platforms = ["pygame", "web", "unity", "generic"]
    
    adapter = PlatformAdapter(args.onnx_model)
    
    # Exporter pour toutes les plateformes demandées
    results = adapter.export_all_platforms(args.output_dir, args.platforms)
    
    print("\n" + "="*50)
    print("Adaptation multi-plateforme terminée!")
    print(f"Résultats sauvegardés dans: {args.output_dir}")
    
    # Afficher un résumé
    for platform, result in results.items():
        if "error" in result:
            print(f"  {platform}: ÉCHEC - {result['error']}")
        else:
            print(f"  {platform}: SUCCÈS - {result.get('onnx_model', 'N/A')}")
    
    print("="*50)


if __name__ == "__main__":
    adapt_model_cli()