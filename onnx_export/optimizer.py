"""
Optimiseur ONNX pour la performance et la taille.

Ce module implémente:
- Quantisation (FP32 → FP16/INT8)
- Fusion d'opérations pour accélération
- Compression pour taille réduite
- Validation de l'exactitude post-optimisation
"""

import os
import json
import tempfile
import shutil
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import onnx
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, quantize_static, QuantType
from onnxruntime.transformers import optimizer as ort_optimizer


class ONNXOptimizer:
    """
    Optimiseur pour les modèles ONNX.
    
    Supporte:
    - Quantisation dynamique et statique
    - Fusion d'opérations
    - Simplification de graphe
    - Compression
    """
    
    def __init__(self, onnx_model_path: str):
        """
        Initialise l'optimiseur avec un modèle ONNX.
        
        Args:
            onnx_model_path: Chemin vers le fichier ONNX
        """
        self.onnx_model_path = onnx_model_path
        self.model = onnx.load(onnx_model_path)
        self.baseline_metrics = self._compute_baseline_metrics()
        
    def _compute_baseline_metrics(self) -> Dict[str, Any]:
        """
        Calcule les métriques de base du modèle.
        
        Returns:
            Dictionnaire avec métriques (taille, nombre d'opérations, etc.)
        """
        model_size = os.path.getsize(self.onnx_model_path)
        
        # Compter les opérations
        op_counts = {}
        for node in self.model.graph.node:
            op_type = node.op_type
            op_counts[op_type] = op_counts.get(op_type, 0) + 1
        
        return {
            "model_size_bytes": model_size,
            "model_size_mb": model_size / (1024 * 1024),
            "operation_counts": op_counts,
            "total_operations": len(self.model.graph.node),
            "input_count": len(self.model.graph.input),
            "output_count": len(self.model.graph.output)
        }
    
    def quantize(
        self,
        output_path: str,
        quantization_type: str = "dynamic_int8",
        calibrate_data: Optional[List[np.ndarray]] = None,
        per_channel: bool = False
    ) -> Dict[str, Any]:
        """
        Quantise le modèle ONNX.
        
        Args:
            output_path: Chemin de sortie
            quantization_type: Type de quantisation (dynamic_int8, static_int8, fp16)
            calibrate_data: Données de calibration pour la quantisation statique
            per_channel: Quantisation par canal (meilleure précision)
            
        Returns:
            Dictionnaire avec résultats de quantisation
        """
        if quantization_type == "dynamic_int8":
            return self._quantize_dynamic_int8(output_path, per_channel)
        elif quantization_type == "static_int8":
            return self._quantize_static_int8(output_path, calibrate_data, per_channel)
        elif quantization_type == "fp16":
            return self._quantize_fp16(output_path)
        else:
            raise ValueError(f"Type de quantisation non supporté: {quantization_type}")
    
    def _quantize_dynamic_int8(
        self,
        output_path: str,
        per_channel: bool = False
    ) -> Dict[str, Any]:
        """
        Quantisation dynamique INT8.
        
        Args:
            output_path: Chemin de sortie
            per_channel: Quantisation par canal
            
        Returns:
            Dictionnaire avec résultats
        """
        print(f"Quantisation dynamique INT8 du modèle...")
        
        # Quantisation dynamique
        quantize_dynamic(
            self.onnx_model_path,
            output_path,
            weight_type=QuantType.QInt8,
            per_channel=per_channel,
            optimize_model=True
        )
        
        # Calculer les métriques post-quantisation
        quantized_metrics = self._compute_model_metrics(output_path)
        
        results = {
            "quantization_type": "dynamic_int8",
            "per_channel": per_channel,
            "original_size_mb": self.baseline_metrics["model_size_mb"],
            "quantized_size_mb": quantized_metrics["model_size_mb"],
            "compression_ratio": self.baseline_metrics["model_size_mb"] / quantized_metrics["model_size_mb"],
            "output_path": output_path
        }
        
        print(f"Quantisation dynamique terminée: {output_path}")
        print(f"  Taille originale: {results['original_size_mb']:.2f} MB")
        print(f"  Taille quantifiée: {results['quantized_size_mb']:.2f} MB")
        print(f"  Ratio de compression: {results['compression_ratio']:.2f}x")
        
        return results
    
    def _quantize_static_int8(
        self,
        output_path: str,
        calibrate_data: Optional[List[np.ndarray]],
        per_channel: bool = False
    ) -> Dict[str, Any]:
        """
        Quantisation statique INT8 avec données de calibration.
        
        Args:
            output_path: Chemin de sortie
            calibrate_data: Données de calibration
            per_channel: Quantisation par canal
            
        Returns:
            Dictionnaire avec résultats
        """
        print(f"Quantisation statique INT8 du modèle...")
        
        if calibrate_data is None:
            print("Avertissement: Pas de données de calibration, utilisation de la quantisation dynamique")
            return self._quantize_dynamic_int8(output_path, per_channel)
        
        # Pour la quantisation statique, nous aurions besoin d'un calibrateur
        # Pour l'instant, utiliser la quantisation dynamique comme fallback
        print("Quantisation statique nécessite un calibrateur - utilisation de la dynamique")
        return self._quantize_dynamic_int8(output_path, per_channel)
    
    def _quantize_fp16(self, output_path: str) -> Dict[str, Any]:
        """
        Quantisation FP16 (demi-précision).
        
        Args:
            output_path: Chemin de sortie
            
        Returns:
            Dictionnaire avec résultats
        """
        print(f"Quantisation FP16 du modèle...")
        
        # Charger le modèle
        model = onnx.load(self.onnx_model_path)
        
        # Convertir les poids FP32 en FP16
        from onnxconverter_common import float16
        
        try:
            model_fp16 = float16.convert_float_to_float16(model)
            onnx.save(model_fp16, output_path)
            
            # Calculer les métriques
            quantized_metrics = self._compute_model_metrics(output_path)
            
            results = {
                "quantization_type": "fp16",
                "original_size_mb": self.baseline_metrics["model_size_mb"],
                "quantized_size_mb": quantized_metrics["model_size_mb"],
                "compression_ratio": self.baseline_metrics["model_size_mb"] / quantized_metrics["model_size_mb"],
                "output_path": output_path
            }
            
            print(f"Quantisation FP16 terminée: {output_path}")
            print(f"  Taille originale: {results['original_size_mb']:.2f} MB")
            print(f"  Taille quantifiée: {results['quantized_size_mb']:.2f} MB")
            print(f"  Ratio de compression: {results['compression_ratio']:.2f}x")
            
            return results
            
        except ImportError:
            print("Avertissement: onnxconverter-common non installé")
            print("Installation: pip install onnxconverter-common")
            
            # Fallback: copier le modèle original
            shutil.copy2(self.onnx_model_path, output_path)
            return {
                "quantization_type": "fp16",
                "error": "onnxconverter-common non installé",
                "output_path": output_path
            }
    
    def fuse_operations(
        self,
        output_path: str,
        fusion_patterns: List[str] = None
    ) -> Dict[str, Any]:
        """
        Fusionne les opérations pour améliorer les performances.
        
        Args:
            output_path: Chemin de sortie
            fusion_patterns: Modèles de fusion à appliquer
            
        Returns:
            Dictionnaire avec résultats
        """
        print(f"Fusion d'opérations du modèle...")
        
        if fusion_patterns is None:
            fusion_patterns = ["SkipLayerNormalization", "EmbedLayerNormalization", "Attention", "Gelu", "BiasGelu"]
        
        try:
            # Utiliser l'optimiseur ONNX Runtime Transformer
            optimized_model = ort_optimizer.optimize_model(
                self.onnx_model_path,
                model_type='bert',  # Type générique
                num_heads=0,
                hidden_size=0,
                optimization_options=None
            )
            
            # Sauvegarder le modèle optimisé
            optimized_model.save_model_to_file(output_path)
            
            # Calculer les métriques
            fused_metrics = self._compute_model_metrics(output_path)
            
            results = {
                "fusion_applied": True,
                "fusion_patterns": fusion_patterns,
                "original_ops": self.baseline_metrics["total_operations"],
                "fused_ops": fused_metrics["total_operations"],
                "reduction_percent": (1 - fused_metrics["total_operations"] / self.baseline_metrics["total_operations"]) * 100,
                "output_path": output_path
            }
            
            print(f"Fusion d'opérations terminée: {output_path}")
            print(f"  Opérations originales: {results['original_ops']}")
            print(f"  Opérations après fusion: {results['fused_ops']}")
            print(f"  Réduction: {results['reduction_percent']:.1f}%")
            
            return results
            
        except Exception as e:
            print(f"Erreur lors de la fusion: {e}")
            print("Utilisation du modèle original")
            
            shutil.copy2(self.onnx_model_path, output_path)
            return {
                "fusion_applied": False,
                "error": str(e),
                "output_path": output_path
            }
    
    def simplify_graph(
        self,
        output_path: str,
        skip_shape_inference: bool = False
    ) -> Dict[str, Any]:
        """
        Simplifie le graphe ONNX (fusion de constantes, élimination de nœuds morts).
        
        Args:
            output_path: Chemin de sortie
            skip_shape_inference: Ignorer l'inférence de shape
            
        Returns:
            Dictionnaire avec résultats
        """
        print(f"Simplification du graphe ONNX...")
        
        try:
            import onnxsim
            
            # Simplifier le modèle
            model_simp, check = onnxsim.simplify(
                self.model,
                skip_shape_inference=skip_shape_inference
            )
            
            if check:
                onnx.save(model_simp, output_path)
                
                # Calculer les métriques
                simplified_metrics = self._compute_model_metrics(output_path)
                
                results = {
                    "simplification_applied": True,
                    "check_passed": check,
                    "original_size_mb": self.baseline_metrics["model_size_mb"],
                    "simplified_size_mb": simplified_metrics["model_size_mb"],
                    "output_path": output_path
                }
                
                print(f"Simplification du graphe terminée: {output_path}")
                print(f"  Vérification passée: {check}")
                print(f"  Taille originale: {results['original_size_mb']:.2f} MB")
                print(f"  Taille simplifiée: {results['simplified_size_mb']:.2f} MB")
                
                return results
            else:
                print("Avertissement: La vérification de simplification a échoué")
                shutil.copy2(self.onnx_model_path, output_path)
                return {
                    "simplification_applied": False,
                    "check_passed": check,
                    "output_path": output_path
                }
                
        except ImportError:
            print("Avertissement: onnxsim non installé")
            print("Installation: pip install onnxsim")
            
            shutil.copy2(self.onnx_model_path, output_path)
            return {
                "simplification_applied": False,
                "error": "onnxsim non installé",
                "output_path": output_path
            }
    
    def compress(
        self,
        output_path: str,
        compression_level: int = 9
    ) -> Dict[str, Any]:
        """
        Compresse le modèle ONNX (gzip).
        
        Args:
            output_path: Chemin de sortie (.onnx.gz)
            compression_level: Niveau de compression (1-9)
            
        Returns:
            Dictionnaire avec résultats
        """
        import gzip
        
        print(f"Compression GZIP du modèle (niveau {compression_level})...")
        
        # Lire le modèle
        with open(self.onnx_model_path, 'rb') as f:
            model_data = f.read()
        
        # Compresser
        with gzip.open(output_path, 'wb', compresslevel=compression_level) as f:
            f.write(model_data)
        
        # Calculer les métriques
        compressed_size = os.path.getsize(output_path)
        
        results = {
            "compression_type": "gzip",
            "compression_level": compression_level,
            "original_size_mb": self.baseline_metrics["model_size_mb"],
            "compressed_size_mb": compressed_size / (1024 * 1024),
            "compression_ratio": self.baseline_metrics["model_size_bytes"] / compressed_size,
            "output_path": output_path
        }
        
        print(f"Compression terminée: {output_path}")
        print(f"  Taille originale: {results['original_size_mb']:.2f} MB")
        print(f"  Taille compressée: {results['compressed_size_mb']:.2f} MB")
        print(f"  Ratio de compression: {results['compression_ratio']:.2f}x")
        
        return results
    
    def validate_accuracy(
        self,
        optimized_model_path: str,
        test_data: List[Tuple[np.ndarray, np.ndarray]] = None,
        num_samples: int = 10,
        tolerance: float = 1e-3
    ) -> Dict[str, Any]:
        """
        Valide l'exactitude du modèle optimisé par rapport à l'original.
        
        Args:
            optimized_model_path: Chemin vers le modèle optimisé
            test_data: Données de test (entrées, sorties attendues)
            num_samples: Nombre d'échantillons de test à générer
            tolerance: Tolérance numérique pour la validation
            
        Returns:
            Dictionnaire avec résultats de validation
        """
        print(f"Validation de l'exactitude...")
        
        # Charger les modèles
        orig_session = ort.InferenceSession(self.onnx_model_path)
        opt_session = ort.InferenceSession(optimized_model_path)
        
        # Générer des données de test si non fournies
        if test_data is None:
            test_data = self._generate_test_data(num_samples)
        
        # Comparer les prédictions
        differences = []
        max_diff = 0.0
        
        for input_data, _ in test_data:
            # Inférence avec le modèle original
            orig_input_name = orig_session.get_inputs()[0].name
            orig_output_name = orig_session.get_outputs()[0].name
            orig_output = orig_session.run([orig_output_name], {orig_input_name: input_data})[0]
            
            # Inférence avec le modèle optimisé
            opt_input_name = opt_session.get_inputs()[0].name
            opt_output_name = opt_session.get_outputs()[0].name
            opt_output = opt_session.run([opt_output_name], {opt_input_name: input_data})[0]
            
            # Calculer la différence
            diff = np.abs(orig_output - opt_output).max()
            differences.append(diff)
            max_diff = max(max_diff, diff)
        
        mean_diff = np.mean(differences)
        std_diff = np.std(differences)
        
        results = {
            "samples_tested": len(test_data),
            "max_difference": float(max_diff),
            "mean_difference": float(mean_diff),
            "std_difference": float(std_diff),
            "within_tolerance": max_diff <= tolerance,
            "tolerance": tolerance,
            "differences": differences
        }
        
        print(f"Validation terminée:")
        print(f"  Échantillons testés: {results['samples_tested']}")
        print(f"  Différence max: {results['max_difference']:.6f}")
        print(f"  Différence moyenne: {results['mean_difference']:.6f}")
        print(f"  Dans la tolérance ({tolerance}): {results['within_tolerance']}")
        
        return results
    
    def _generate_test_data(
        self,
        num_samples: int
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Génère des données de test aléatoires.
        
        Args:
            num_samples: Nombre d'échantillons
            
        Returns:
            Liste de tuples (entrée, sortie)
        """
        test_data = []
        
        # Obtenir la shape d'entrée
        input_shape = None
        for input in self.model.graph.input:
            # Extraire la shape de l'entrée
            dims = []
            for dim in input.type.tensor_type.shape.dim:
                if dim.dim_value > 0:
                    dims.append(dim.dim_value)
                else:
                    dims.append(1)  # Dimension inconnue, utiliser 1
            
            if dims:
                input_shape = tuple(dims)
                break
        
        if input_shape is None:
            # Shape par défaut si non trouvée
            input_shape = (1, 100)  # Shape typique pour Pac-Man
        
        # Générer des échantillons
        for _ in range(num_samples):
            # Générer des données d'entrée aléatoires
            input_data = np.random.randn(*input_shape).astype(np.float32)
            
            # Pour la sortie, nous utiliserons l'inférence du modèle original
            # (sera calculée lors de la validation)
            test_data.append((input_data, None))
        
        return test_data
    
    def _compute_model_metrics(self, model_path: str) -> Dict[str, Any]:
        """
        Calcule les métriques d'un modèle ONNX.
        
        Args:
            model_path: Chemin vers le modèle
            
        Returns:
            Dictionnaire avec métriques
        """
        model = onnx.load(model_path)
        model_size = os.path.getsize(model_path)
        
        # Compter les opérations
        op_counts = {}
        for node in model.graph.node:
            op_type = node.op_type
            op_counts[op_type] = op_counts.get(op_type, 0) + 1
        
        return {
            "model_size_bytes": model_size,
            "model_size_mb": model_size / (1024 * 1024),
            "operation_counts": op_counts,
            "total_operations": len(model.graph.node)
        }
    
    def apply_all_optimizations(
        self,
        output_dir: str,
        optimizations: List[str] = None,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Applique toutes les optimisations disponibles.
        
        Args:
            output_dir: Répertoire de sortie
            optimizations: Liste des optimisations à appliquer
            validate: Valider l'exactitude après optimisation
            
        Returns:
            Dictionnaire avec résultats de toutes les optimisations
        """
        os.makedirs(output_dir, exist_ok=True)
        
        if optimizations is None:
            optimizations = ["simplify", "fuse", "quantize", "compress"]
        
        results = {}
        current_model = self.onnx_model_path
        
        for opt in optimizations:
            opt_output = os.path.join(output_dir, f"optimized_{opt}.onnx")
            
            try:
                if opt == "simplify":
                    opt_result = self.simplify_graph(opt_output)
                elif opt == "fuse":
                    opt_result = self.fuse_operations(opt_output)
                elif opt == "quantize":
                    opt_result = self.quantize(opt_output, "dynamic_int8")
                elif opt == "compress":
                    opt_result = self.compress(opt_output + ".gz")
                else:
                    print(f"Optimisation inconnue ignorée: {opt}")
                    continue
                
                results[opt] = opt_result
                
                # Mettre à jour le modèle courant pour les optimisations suivantes
                if "output_path" in opt_result and os.path.exists(opt_result["output_path"]):
                    current_model = opt_result["output_path"]
                    # Recharger l'optimiseur avec le nouveau modèle
                    self.__init__(current_model)
                
            except Exception as e:
                print(f"Erreur lors de l'optimisation {opt}: {e}")
                results[opt] = {"error": str(e)}
        
        # Validation finale
        if validate and "quantize" in results and "output_path" in results["quantize"]:
            validation_result = self.validate_accuracy(
                results["quantize"]["output_path"],
                num_samples=5
            )
            results["validation"] = validation_result
        
        # Sauvegarder les résultats
        report_path = os.path.join(output_dir, "optimization_report.json")
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Rapport d'optimisation généré: {report_path}")
        return results


def optimize_model_cli():
    """Interface en ligne de commande pour l'optimisation de modèles."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Optimiser un modèle ONNX")
    parser.add_argument("onnx_model", help="Chemin vers le modèle ONNX")
    parser.add_argument("--output_dir", default="./optimized_models", help="Répertoire de sortie")
    parser.add_argument("--optimizations", nargs="+",
                       choices=["simplify", "fuse", "quantize", "compress", "all"],
                       default=["all"], help="Optimisations à appliquer")
    parser.add_argument("--no_validate", action="store_true", help="Désactiver la validation")
    
    args = parser.parse_args()
    
    # Convertir "all" en liste de toutes les optimisations
    if "all" in args.optimizations:
        args.optimizations = ["simplify", "fuse", "quantize", "compress"]
    
    optimizer = ONNXOptimizer(args.onnx_model)
    
    # Appliquer les optimisations
    results = optimizer.apply_all_optimizations(
        args.output_dir,
        args.optimizations,
        validate=not args.no_validate
    )
    
    print("\n" + "="*50)
    print("Optimisation terminée!")
    
    # Afficher un résumé
    for opt, result in results.items():
        if "error" in result:
            print(f"  {opt}: ÉCHEC - {result['error']}")
        else:
            if "compression_ratio" in result:
                print(f"  {opt}: SUCCÈS - Ratio: {result['compression_ratio']:.2f}x")
            elif "reduction_percent" in result:
                print(f"  {opt}: SUCCÈS - Réduction: {result['reduction_percent']:.1f}%")
            else:
                print(f"  {opt}: SUCCÈS")
    
    print("="*50)


if __name__ == "__main__":
    optimize_model_cli()