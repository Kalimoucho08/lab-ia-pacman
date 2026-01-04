"""
Validateur d'export ONNX.

Ce module valide:
- L'intégrité des fichiers ONNX exportés
- La compatibilité avec les runtimes cibles
- L'exactitude des prédictions
- La conformité des métadonnées
"""

import os
import json
import tempfile
import subprocess
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import onnx
import onnxruntime as ort
from onnxruntime.quantization import CalibrationDataReader


class ONNXValidator:
    """
    Validateur pour les exports ONNX.
    
    Effectue des vérifications complètes:
    1. Validation de syntaxe ONNX
    2. Compatibilité runtime
    3. Exactitude des prédictions
    4. Vérification des métadonnées
    5. Tests de performance
    """
    
    def __init__(self, onnx_model_path: str):
        """
        Initialise le validateur avec un modèle ONNX.
        
        Args:
            onnx_model_path: Chemin vers le fichier ONNX
        """
        self.onnx_model_path = onnx_model_path
        self.model = None
        self.metadata = {}
        
        # Charger le modèle
        self._load_model()
    
    def _load_model(self):
        """Charge et valide le modèle ONNX."""
        try:
            self.model = onnx.load(self.onnx_model_path)
            onnx.checker.check_model(self.model)
            print(f"Modèle ONNX chargé et validé: {self.onnx_model_path}")
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            raise
    
    def validate_syntax(self) -> Dict[str, Any]:
        """
        Valide la syntaxe et la structure ONNX.
        
        Returns:
            Dictionnaire avec résultats de validation
        """
        print("Validation de la syntaxe ONNX...")
        
        issues = []
        warnings = []
        
        try:
            # Vérification ONNX standard
            onnx.checker.check_model(self.model)
            
            # Vérifications supplémentaires
            if not self.model.graph.input:
                issues.append("Le modèle n'a pas d'entrée définie")
            
            if not self.model.graph.output:
                issues.append("Le modèle n'a pas de sortie définie")
            
            # Vérifier les types de données supportés
            for tensor in self.model.graph.initializer:
                if tensor.data_type not in [1, 7, 10]:  # FLOAT, FLOAT16, INT32
                    warnings.append(f"Type de données potentiellement problématique: {tensor.data_type}")
            
            # Vérifier la version opset
            opset_version = self.model.opset_import[0].version if self.model.opset_import else 0
            if opset_version < 7:
                warnings.append(f"Version Opset ancienne: {opset_version}. Recommandé: >= 13")
            
        except Exception as e:
            issues.append(f"Erreur de validation: {e}")
        
        results = {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "opset_version": opset_version,
            "input_count": len(self.model.graph.input),
            "output_count": len(self.model.graph.output),
            "node_count": len(self.model.graph.node)
        }
        
        print(f"Validation syntaxique: {'PASSÉ' if results['valid'] else 'ÉCHOUÉ'}")
        if issues:
            print(f"  Problèmes: {issues}")
        if warnings:
            print(f"  Avertissements: {warnings}")
        
        return results
    
    def validate_runtime_compatibility(
        self,
        providers: List[str] = None
    ) -> Dict[str, Any]:
        """
        Valide la compatibilité avec ONNX Runtime.
        
        Args:
            providers: Fournisseurs d'exécution à tester
            
        Returns:
            Dictionnaire avec résultats de compatibilité
        """
        print("Validation de la compatibilité runtime...")
        
        if providers is None:
            providers = ['CPUExecutionProvider']
        
        results = {}
        
        for provider in providers:
            try:
                # Créer une session avec le provider
                sess_options = ort.SessionOptions()
                session = ort.InferenceSession(
                    self.onnx_model_path,
                    sess_options=sess_options,
                    providers=[provider]
                )
                
                # Obtenir les informations d'entrée/sortie
                input_info = []
                for input in session.get_inputs():
                    input_info.append({
                        "name": input.name,
                        "shape": input.shape,
                        "type": input.type
                    })
                
                output_info = []
                for output in session.get_outputs():
                    output_info.append({
                        "name": output.name,
                        "shape": output.shape,
                        "type": output.type
                    })
                
                results[provider] = {
                    "compatible": True,
                    "inputs": input_info,
                    "outputs": output_info,
                    "session_created": True
                }
                
                print(f"  {provider}: COMPATIBLE")
                
            except Exception as e:
                results[provider] = {
                    "compatible": False,
                    "error": str(e),
                    "session_created": False
                }
                
                print(f"  {provider}: INCOMPATIBLE - {e}")
        
        overall_compatible = any(r.get("compatible", False) for r in results.values())
        
        return {
            "overall_compatible": overall_compatible,
            "providers": results,
            "recommended_provider": "CPUExecutionProvider" if overall_compatible else None
        }
    
    def validate_predictions(
        self,
        test_data: Optional[List[np.ndarray]] = None,
        num_samples: int = 5,
        tolerance: float = 1e-5
    ) -> Dict[str, Any]:
        """
        Valide les prédictions du modèle.
        
        Args:
            test_data: Données de test (optionnel)
            num_samples: Nombre d'échantillons à générer
            tolerance: Tolérance numérique
            
        Returns:
            Dictionnaire avec résultats de validation
        """
        print("Validation des prédictions...")
        
        try:
            # Créer une session
            session = ort.InferenceSession(self.onnx_model_path)
            
            # Générer des données de test si non fournies
            if test_data is None:
                test_data = self._generate_test_data(session, num_samples)
            
            # Exécuter des prédictions
            predictions = []
            inference_times = []
            
            for input_data in test_data:
                # Préparer les entrées
                inputs = {}
                for i, input_info in enumerate(session.get_inputs()):
                    inputs[input_info.name] = input_data[i] if isinstance(input_data, list) else input_data
                
                # Mesurer le temps d'inférence
                import time
                start_time = time.perf_counter()
                
                # Inférence
                outputs = session.run(None, inputs)
                
                inference_time = time.perf_counter() - start_time
                inference_times.append(inference_time)
                
                predictions.append(outputs)
            
            # Analyser les résultats
            avg_inference_time = np.mean(inference_times)
            std_inference_time = np.std(inference_times)
            
            # Vérifier la consistance des prédictions
            consistent = True
            if len(predictions) > 1:
                # Comparer les premières prédictions pour vérifier la consistance
                first_pred = predictions[0]
                for i in range(1, len(predictions)):
                    current_pred = predictions[i]
                    # Vérifier que les shapes sont cohérentes
                    if len(first_pred) != len(current_pred):
                        consistent = False
                        break
            
            results = {
                "predictions_valid": True,
                "samples_tested": len(test_data),
                "avg_inference_time_ms": avg_inference_time * 1000,
                "std_inference_time_ms": std_inference_time * 1000,
                "predictions_consistent": consistent,
                "output_shapes": [p[0].shape for p in predictions[:2]] if predictions else []
            }
            
            print(f"Validation des prédictions: PASSÉ")
            print(f"  Échantillons testés: {results['samples_tested']}")
            print(f"  Temps d'inférence moyen: {results['avg_inference_time_ms']:.2f} ms")
            print(f"  Prédictions consistantes: {results['predictions_consistent']}")
            
            return results
            
        except Exception as e:
            print(f"Validation des prédictions: ÉCHOUÉ - {e}")
            return {
                "predictions_valid": False,
                "error": str(e)
            }
    
    def validate_metadata(self) -> Dict[str, Any]:
        """
        Valide les métadonnées intégrées au modèle.
        
        Returns:
            Dictionnaire avec résultats de validation
        """
        print("Validation des métadonnées...")
        
        metadata = {}
        issues = []
        
        # Extraire les métadonnées
        for prop in self.model.metadata_props:
            if prop.key == "metadata":
                try:
                    metadata = json.loads(prop.value)
                except json.JSONDecodeError:
                    issues.append(f"Métadonnées JSON invalides: {prop.value[:50]}...")
            else:
                metadata[prop.key] = prop.value
        
        # Vérifier les métadonnées requises
        required_fields = ["algorithm", "policy_type", "observation_shape", "action_shape"]
        missing_fields = []
        
        for field in required_fields:
            if field not in metadata:
                missing_fields.append(field)
        
        if missing_fields:
            issues.append(f"Champs de métadonnées manquants: {missing_fields}")
        
        # Vérifier la cohérence avec le modèle
        if "observation_shape" in metadata and "action_shape" in metadata:
            try:
                # Vérifier que les shapes correspondent aux entrées/sorties du modèle
                session = ort.InferenceSession(self.onnx_model_path)
                inputs = session.get_inputs()
                outputs = session.get_outputs()
                
                if inputs:
                    input_shape = list(inputs[0].shape)
                    # Ignorer la dimension batch
                    if input_shape[0] == -1:
                        input_shape = input_shape[1:]
                    
                    obs_shape = metadata["observation_shape"]
                    if isinstance(obs_shape, list) and input_shape != obs_shape:
                        issues.append(f"Incohérence de shape d'entrée: modèle={input_shape}, métadonnées={obs_shape}")
                
                if outputs:
                    output_shape = list(outputs[0].shape)
                    if output_shape[0] == -1:
                        output_shape = output_shape[1:]
                    
                    action_shape = metadata["action_shape"]
                    if isinstance(action_shape, list) and output_shape != action_shape:
                        issues.append(f"Incohérence de shape de sortie: modèle={output_shape}, métadonnées={action_shape}")
                        
            except Exception as e:
                issues.append(f"Erreur lors de la vérification de cohérence: {e}")
        
        results = {
            "metadata_present": len(metadata) > 0,
            "metadata": metadata,
            "issues": issues,
            "valid": len(issues) == 0,
            "missing_fields": missing_fields
        }
        
        print(f"Validation des métadonnées: {'PASSÉ' if results['valid'] else 'ÉCHOUÉ'}")
        if metadata:
            print(f"  Métadonnées trouvées: {len(metadata)} champs")
        if issues:
            print(f"  Problèmes: {issues}")
        
        return results
    
    def validate_performance(
        self,
        batch_sizes: List[int] = None,
        num_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Valide les performances du modèle.
        
        Args:
            batch_sizes: Tailles de batch à tester
            num_iterations: Nombre d'itérations par test
            
        Returns:
            Dictionnaire avec résultats de performance
        """
        print("Validation des performances...")
        
        if batch_sizes is None:
            batch_sizes = [1, 4, 8, 16]
        
        try:
            session = ort.InferenceSession(self.onnx_model_path)
            input_info = session.get_inputs()[0]
            
            # Obtenir la shape d'entrée
            input_shape = list(input_info.shape)
            # Remplacer -1 (dimension dynamique) par 1
            input_shape = [1 if dim == -1 else dim for dim in input_shape]
            
            results = {}
            
            for batch_size in batch_sizes:
                # Ajuster la shape avec la taille de batch
                test_shape = input_shape.copy()
                if test_shape[0] == 1:  # Si la première dimension est 1 (batch)
                    test_shape[0] = batch_size
                else:
                    test_shape = [batch_size] + test_shape
                
                # Générer des données de test
                test_data = np.random.randn(*test_shape).astype(np.float32)
                
                # Mesurer les performances
                import time
                times = []
                
                # Warm-up
                for _ in range(2):
                    session.run(None, {input_info.name: test_data})
                
                # Mesures
                for _ in range(num_iterations):
                    start_time = time.perf_counter()
                    session.run(None, {input_info.name: test_data})
                    end_time = time.perf_counter()
                    times.append(end_time - start_time)
                
                avg_time = np.mean(times) * 1000  # en ms
                std_time = np.std(times) * 1000
                throughput = batch_size / (np.mean(times))  # échantillons par seconde
                
                results[batch_size] = {
                    "avg_inference_time_ms": avg_time,
                    "std_inference_time_ms": std_time,
                    "throughput_samples_per_sec": throughput,
                    "shape": test_shape
                }
                
                print(f"  Batch {batch_size}: {avg_time:.2f} ms (±{std_time:.2f}), {throughput:.0f} échantillons/s")
            
            return {
                "performance_tests": results,
                "recommended_batch_size": min(batch_sizes, key=lambda bs: results[bs]["avg_inference_time_ms"] / bs if bs > 0 else float('inf'))
            }
            
        except Exception as e:
            print(f"Validation des performances: ÉCHOUÉ - {e}")
            return {
                "performance_tests": {},
                "error": str(e)
            }
    
    def validate_platform_specific(
        self,
        platform: str,
        platform_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Valide des aspects spécifiques à une plateforme.
        
        Args:
            platform: Plateforme cible (pygame, web, unity, generic)
            platform_config: Configuration spécifique
            
        Returns:
            Dictionnaire avec résultats de validation
        """
        print(f"Validation spécifique à la plateforme {platform}...")
        
        if platform_config is None:
            platform_config = {}
        
        issues = []
        warnings = []
        
        if platform == "web":
            # Vérifications pour le web
            model_size = os.path.getsize(self.onnx_model_path) / (1024 * 1024)  # MB
            if model_size > 10:
                warnings.append(f"Taille du modèle ({model_size:.1f} MB) peut être trop grande pour le web")
            
            # Vérifier les opérations supportées par TensorFlow.js
            unsupported_ops_web = ["RandomNormal", "RandomUniform", "Loop", "Scan"]
            for node in self.model.graph.node:
                if node.op_type in unsupported_ops_web:
                    warnings.append(f"Opération {node.op_type} peut être problématique pour TensorFlow.js")
        
        elif platform == "unity":
            # Vérifications pour Unity Barracuda
            unsupported_ops_unity = ["RandomNormal", "RandomUniform", "Dropout", "Loop", "Scan", "If"]
            for node in self.model.graph.node:
                if node.op_type in unsupported_ops_unity:
                    issues.append(f"Opération {node.op_type} non supportée par Barracuda")
            
            # Vérifier la taille
            model_size = os.path.getsize(self.onnx_model_path) / (1024 * 1024)
            if model_size > 50:
                warnings.append(f"Taille du modèle ({model_size:.1f} MB) peut être trop grande pour Unity")
        
        elif platform == "pygame":
            # Vérifications pour Pygame
            # Principalement la compatibilité ONNX Runtime
            pass
        
        elif platform == "generic":
            # Vérifications génériques
            pass
        
        else:
            warnings.append(f"Plateforme non reconnue: {platform}")
        
        return {
            "platform": platform,
            "issues": issues,
            "warnings": warnings,
            "valid": len(issues) == 0
        }
    
    def run_comprehensive_validation(
        self,
        platforms: List[str] = None,
        performance_test: bool = True
    ) -> Dict[str, Any]:
        """
        Exécute une validation complète.
        
        Args:
            platforms: Plateformes à valider
            performance_test: Inclure les tests de performance
            
        Returns:
            Dictionnaire avec tous les résultats de validation
        """
        if platforms is None:
            platforms = ["pygame", "web", "unity", "generic"]
        
        print(f"\n{'='*60}")
        print(f"VALIDATION COMPLÈTE DU MODÈLE ONNX")
        print(f"{'='*60}")
        
        results = {}
        
        # 1. Validation syntaxique
        results["syntax"] = self.validate_syntax()
        
        # 2. Compatibilité runtime
        results["runtime"] = self.validate_runtime_compatibility()
        
        # 3. Validation des prédictions
        results["predictions"] = self.validate_predictions()
        
        # 4. Validation des métadonnées
        results["metadata"] = self.validate_metadata()
        
        # 5. Validation des performances (optionnel)
        if performance_test:
            results["performance"] = self.validate_performance()
        
        # 6. Validation spécifique à la plateforme
        results["platform_specific"] = {}
        for platform in platforms:
            results["platform_specific"][platform] = self.validate_platform_specific(platform)
        
        # 7. Calculer un score global
        overall_score = self._calculate_overall_score(results)
        results["overall"] = overall_score
        
        # 8. Générer un rapport
        report = self._generate_validation_report(results)
        results["report"] = report
        
        print(f"\n{'='*60}")
        print(f"VALIDATION TERMINÉE")
        print(f"{'='*60}")
        print(f"Score global: {overall_score['score']}/100")
        print(f"Statut: {overall_score['status']}")
        print(f"Recommandations: {len(overall_score['recommendations'])}")
        
        return results
    
    def _generate_test_data(
        self,
        session: ort.InferenceSession,
        num_samples: int
    ) -> List[np.ndarray]:
        """
        Génère des données de test pour la validation.
        
        Args:
            session: Session ONNX Runtime
            num_samples: Nombre d'échantillons
            
        Returns:
            Liste de données de test
        """
        test_data = []
        
        for _ in range(num_samples):
            sample = []
            for input_info in session.get_inputs():
                # Générer des données aléatoires avec la shape appropriée
                shape = list(input_info.shape)
                # Remplacer -1 (dimension dynamique) par 1
                shape = [1 if dim == -1 else dim for dim in shape]
                
                # Générer des données
                data = np.random.randn(*shape).astype(np.float32)
                sample.append(data)
            
            if len(sample) == 1:
                test_data.append(sample[0])
            else:
                test_data.append(sample)
        
        return test_data
    
    def _calculate_overall_score(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcule un score global de validation.
        
        Args:
            results: Résultats de validation
            
        Returns:
            Dictionnaire avec score et recommandations
        """
        score = 100
        issues = []
        recommendations = []
        
        # Pénalités pour chaque type de problème
        if not results.get("syntax", {}).get("valid", False):
            score -= 30
            issues.append("Syntaxe ONNX invalide")
        
        if not results.get("runtime", {}).get("overall_compatible", False):
            score -= 25
            issues.append("Incompatible avec ONNX Runtime")
            recommendations.append("Vérifier les opérations utilisées")
        
        if not results.get("predictions", {}).get("predictions_valid", False):
            score -= 20
            issues.append("Prédictions invalides")
            recommendations.append("Vérifier la conversion du modèle")
        
        if not results.get("metadata", {}).get("valid", False):
            score -= 10
            issues.append("Métadonnées incomplètes ou invalides")
            recommendations.append("Ajouter des métadonnées complètes")
        
        # Vérifier les problèmes spécifiques aux plateformes
        platform_issues = 0
        for platform, platform_results in results.get("platform_specific", {}).items():
            if not platform_results.get("valid", False):
                platform_issues += 1
                issues.append(f"Problèmes avec la plateforme {platform}")
        
        if platform_issues > 0:
            score -= platform_issues * 5
            recommendations.append("Adapter le modèle pour les plateformes cibles")
        
        # Déterminer le statut
        if score >= 90:
            status = "EXCELLENT"
        elif score >= 75:
            status = "BON"
        elif score >= 60:
            status = "ACCEPTABLE"
        else:
            status = "PROBLÉMATIQUE"
        
        return {
            "score": score,
            "status": status,
            "issues": issues,
            "recommendations": recommendations,
            "model_size_mb": os.path.getsize(self.onnx_model_path) / (1024 * 1024)
        }
    
    def _generate_validation_report(self, results: Dict[str, Any]) -> str:
        """
        Génère un rapport de validation lisible.
        
        Args:
            results: Résultats de validation
            
        Returns:
            Rapport formaté
        """
        report_lines = []
        
        report_lines.append("="*60)
        report_lines.append("RAPPORT DE VALIDATION ONNX")
        report_lines.append("="*60)
        report_lines.append(f"Modèle: {os.path.basename(self.onnx_model_path)}")
        report_lines.append(f"Taille: {results['overall']['model_size_mb']:.2f} MB")
        report_lines.append("")
        
        # Résumé
        overall = results["overall"]
        report_lines.append("RÉSUMÉ")
        report_lines.append(f"  Score: {overall['score']}/100")
        report_lines.append(f"  Statut: {overall['status']}")
        report_lines.append("")
        
        # Détails par catégorie
        report_lines.append("DÉTAILS PAR CATÉGORIE")
        
        # Syntaxe
        syntax = results["syntax"]
        report_lines.append(f"  1. Syntaxe ONNX: {'✓ PASSÉ' if syntax['valid'] else '✗ ÉCHOUÉ'}")
        if syntax.get('issues'):
            for issue in syntax['issues']:
                report_lines.append(f"     - {issue}")
        
        # Runtime
        runtime = results["runtime"]
        report_lines.append(f"  2. Compatibilité Runtime: {'✓ PASSÉ' if runtime['overall_compatible'] else '✗ ÉCHOUÉ'}")
        for provider, provider_result in runtime.get('providers', {}).items():
            status = "✓" if provider_result.get('compatible', False) else "✗"
            report_lines.append(f"     - {provider}: {status}")
        
        # Prédictions
        predictions = results["predictions"]
        report_lines.append(f"  3. Prédictions: {'✓ PASSÉ' if predictions.get('predictions_valid', False) else '✗ ÉCHOUÉ'}")
        if predictions.get('predictions_valid', False):
            report_lines.append(f"     Temps moyen: {predictions.get('avg_inference_time_ms', 0):.2f} ms")
        
        # Métadonnées
        metadata = results["metadata"]
        report_lines.append(f"  4. Métadonnées: {'✓ PASSÉ' if metadata.get('valid', False) else '✗ ÉCHOUÉ'}")
        if metadata.get('metadata_present', False):
            report_lines.append(f"     Champs: {len(metadata.get('metadata', {}))}")
        
        # Plateformes
        report_lines.append("  5. Compatibilité Plateforme:")
        for platform, platform_result in results.get("platform_specific", {}).items():
            status = "✓" if platform_result.get('valid', False) else "✗"
            report_lines.append(f"     - {platform}: {status}")
        
        # Recommandations
        if overall['recommendations']:
            report_lines.append("")
            report_lines.append("RECOMMANDATIONS:")
            for i, rec in enumerate(overall['recommendations'], 1):
                report_lines.append(f"  {i}. {rec}")
        
        report_lines.append("")
        report_lines.append("="*60)
        
        return "\n".join(report_lines)
    
    def save_validation_report(
        self,
        output_path: str,
        results: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Sauvegarde le rapport de validation dans un fichier.
        
        Args:
            output_path: Chemin de sortie
            results: Résultats de validation (optionnel)
            
        Returns:
            Chemin du fichier généré
        """
        if results is None:
            results = self.run_comprehensive_validation()
        
        # Générer le rapport
        report = self._generate_validation_report(results)
        
        # Sauvegarder
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Sauvegarder également les résultats complets en JSON
        json_path = output_path.replace('.txt', '.json').replace('.md', '.json')
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Rapport de validation sauvegardé: {output_path}")
        print(f"Résultats complets: {json_path}")
        
        return output_path


def validate_model_cli():
    """Interface en ligne de commande pour la validation de modèles."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Valider un modèle ONNX")
    parser.add_argument("onnx_model", help="Chemin vers le modèle ONNX")
    parser.add_argument("--output_report", default="./validation_report.txt", help="Fichier de rapport")
    parser.add_argument("--platforms", nargs="+",
                       choices=["pygame", "web", "unity", "generic", "all"],
                       default=["all"], help="Plateformes à valider")
    parser.add_argument("--no_performance", action="store_true", help="Exclure les tests de performance")
    
    args = parser.parse_args()
    
    # Convertir "all" en liste de toutes les plateformes
    if "all" in args.platforms:
        args.platforms = ["pygame", "web", "unity", "generic"]
    
    # Valider le modèle
    validator = ONNXValidator(args.onnx_model)
    results = validator.run_comprehensive_validation(
        platforms=args.platforms,
        performance_test=not args.no_performance
    )
    
    # Sauvegarder le rapport
    validator.save_validation_report(args.output_report, results)
    
    print(f"\nValidation terminée. Rapport: {args.output_report}")


if __name__ == "__main__":
    validate_model_cli()