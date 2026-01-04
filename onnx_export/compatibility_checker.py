"""
Vérificateur de compatibilité ONNX multi-plateforme.

Ce module vérifie la compatibilité des modèles ONNX avec:
- Pygame (ONNX Runtime Python)
- Web (TensorFlow.js, ONNX.js)
- Unity (Barracuda)
- Autres runtimes (ONNX Runtime mobile, etc.)
"""

import os
import json
import subprocess
from typing import Dict, Any, List, Optional, Set
import onnx
import onnxruntime as ort


class CompatibilityChecker:
    """
    Vérificateur de compatibilité multi-plateforme.
    
    Analyse les modèles ONNX pour identifier les problèmes potentiels
    de compatibilité avec différentes plateformes cibles.
    """
    
    def __init__(self, onnx_model_path: str):
        """
        Initialise le vérificateur avec un modèle ONNX.
        
        Args:
            onnx_model_path: Chemin vers le fichier ONNX
        """
        self.onnx_model_path = onnx_model_path
        self.model = onnx.load(onnx_model_path)
        self.operations = self._extract_operations()
        
    def _extract_operations(self) -> Dict[str, List[str]]:
        """
        Extrait toutes les opérations du modèle.
        
        Returns:
            Dictionnaire avec opérations par type
        """
        operations = {}
        
        for node in self.model.graph.node:
            op_type = node.op_type
            if op_type not in operations:
                operations[op_type] = []
            operations[op_type].append(node.name)
        
        return operations
    
    def check_pygame_compatibility(self) -> Dict[str, Any]:
        """
        Vérifie la compatibilité avec Pygame (ONNX Runtime Python).
        
        Returns:
            Dictionnaire avec résultats de compatibilité
        """
        print("Vérification de compatibilité Pygame...")
        
        issues = []
        warnings = []
        
        # Pygame utilise ONNX Runtime Python standard
        # Vérifications générales
        try:
            session = ort.InferenceSession(self.onnx_model_path)
            
            # Vérifier la disponibilité des providers
            available_providers = ort.get_available_providers()
            if 'CPUExecutionProvider' not in available_providers:
                warnings.append("CPUExecutionProvider non disponible")
            
            # Vérifier la mémoire requise
            model_size_mb = os.path.getsize(self.onnx_model_path) / (1024 * 1024)
            if model_size_mb > 100:
                warnings.append(f"Taille du modèle importante ({model_size_mb:.1f} MB) peut affecter les performances")
            
        except Exception as e:
            issues.append(f"Erreur ONNX Runtime: {e}")
        
        # Vérifier les opérations problématiques
        problematic_ops = self._get_problematic_operations("pygame")
        for op in problematic_ops:
            if op in self.operations:
                warnings.append(f"Opération {op} peut nécessiter une attention particulière")
        
        return {
            "platform": "pygame",
            "compatible": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommended_action": "Aucune action requise" if len(issues) == 0 else "Vérifier les erreurs ci-dessus"
        }
    
    def check_web_compatibility(
        self,
        framework: str = "tensorflowjs"
    ) -> Dict[str, Any]:
        """
        Vérifie la compatibilité avec le web.
        
        Args:
            framework: Framework cible (tensorflowjs, onnxjs)
            
        Returns:
            Dictionnaire avec résultats de compatibilité
        """
        print(f"Vérification de compatibilité Web ({framework})...")
        
        issues = []
        warnings = []
        
        # Vérifications communes pour le web
        model_size_mb = os.path.getsize(self.onnx_model_path) / (1024 * 1024)
        if model_size_mb > 10:
            warnings.append(f"Taille du modèle ({model_size_mb:.1f} MB) peut être trop grande pour le web")
        
        if framework == "tensorflowjs":
            # Vérifications spécifiques à TensorFlow.js
            tfjs_unsupported_ops = [
                "RandomNormal", "RandomUniform", "Loop", "Scan", 
                "If", "SequenceInsert", "SequenceErase", "SequenceLength"
            ]
            
            for op in tfjs_unsupported_ops:
                if op in self.operations:
                    issues.append(f"Opération {op} non supportée par TensorFlow.js")
            
            # Vérifier les types de données
            for tensor in self.model.graph.initializer:
                if tensor.data_type not in [1, 7, 10]:  # FLOAT, FLOAT16, INT32
                    warnings.append(f"Type de données {tensor.data_type} peut nécessiter une conversion")
            
            # Recommandations pour TensorFlow.js
            if not issues:
                recommendations = [
                    "Utiliser onnx2tf pour la conversion",
                    "Vérifier la compatibilité des opérations après conversion",
                    "Tester avec TensorFlow.js runtime"
                ]
            else:
                recommendations = [
                    "Considérer l'utilisation d'ONNX.js comme alternative",
                    "Modifier le modèle pour éviter les opérations non supportées"
                ]
                
        elif framework == "onnxjs":
            # Vérifications spécifiques à ONNX.js
            onnxjs_unsupported_ops = [
                "RandomNormal", "RandomUniform", "Loop", "Scan"
            ]
            
            for op in onnxjs_unsupported_ops:
                if op in self.operations:
                    warnings.append(f"Opération {op} peut être problématique pour ONNX.js")
            
            # ONNX.js a des limitations de taille
            if model_size_mb > 5:
                warnings.append(f"Taille du modèle ({model_size_mb:.1f} MB) peut affecter les performances dans le navigateur")
            
            recommendations = [
                "Utiliser ONNX Runtime Web (WASM) pour de meilleures performances",
                "Considérer la quantisation pour réduire la taille"
            ]
        
        else:
            issues.append(f"Framework web non supporté: {framework}")
            recommendations = []
        
        return {
            "platform": "web",
            "framework": framework,
            "compatible": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "model_size_mb": model_size_mb
        }
    
    def check_unity_compatibility(self) -> Dict[str, Any]:
        """
        Vérifie la compatibilité avec Unity Barracuda.
        
        Returns:
            Dictionnaire avec résultats de compatibilité
        """
        print("Vérification de compatibilité Unity (Barracuda)...")
        
        issues = []
        warnings = []
        
        # Opérations non supportées par Barracuda
        barracuda_unsupported_ops = [
            "RandomNormal", "RandomUniform", "Dropout", "Loop", 
            "Scan", "If", "Sequence", "Resize", "Upsample"
        ]
        
        for op in barracuda_unsupported_ops:
            if op in self.operations:
                issues.append(f"Opération {op} non supportée par Barracuda")
        
        # Vérifier les types de données
        for tensor in self.model.graph.initializer:
            if tensor.data_type not in [1, 7]:  # FLOAT, FLOAT16
                issues.append(f"Type de données {tensor.data_type} non supporté par Barracuda")
        
        # Vérifier la taille du modèle
        model_size_mb = os.path.getsize(self.onnx_model_path) / (1024 * 1024)
        if model_size_mb > 50:
            warnings.append(f"Taille du modèle ({model_size_mb:.1f} MB) peut affecter les performances Unity")
        
        # Vérifier la complexité du modèle
        total_nodes = len(self.model.graph.node)
        if total_nodes > 1000:
            warnings.append(f"Modèle complexe ({total_nodes} nœuds) peut affecter les performances")
        
        recommendations = []
        if issues:
            recommendations = [
                "Utiliser ONNX Simplifier pour simplifier le modèle",
                "Remplacer les opérations non supportées par des équivalents",
                "Considérer l'export vers un format alternatif"
            ]
        else:
            recommendations = [
                "Le modèle semble compatible avec Barracuda",
                "Tester avec l'importateur Barracuda dans Unity"
            ]
        
        return {
            "platform": "unity",
            "framework": "barracuda",
            "compatible": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "model_size_mb": model_size_mb,
            "total_nodes": total_nodes
        }
    
    def check_generic_compatibility(
        self,
        runtime: str = "onnxruntime"
    ) -> Dict[str, Any]:
        """
        Vérifie la compatibilité avec un runtime générique.
        
        Args:
            runtime: Runtime cible (onnxruntime, ncnn, tflite, etc.)
            
        Returns:
            Dictionnaire avec résultats de compatibilité
        """
        print(f"Vérification de compatibilité générique ({runtime})...")
        
        issues = []
        warnings = []
        
        if runtime == "onnxruntime":
            # Vérifications pour ONNX Runtime général
            try:
                # Tester avec différentes versions d'opset
                opset_version = self.model.opset_import[0].version if self.model.opset_import else 0
                if opset_version < 7:
                    warnings.append(f"Version Opset ancienne ({opset_version}), mise à jour recommandée")
                
                # Vérifier la compatibilité avec différents providers
                available_providers = ort.get_available_providers()
                
                recommendations = [
                    f"Version Opset: {opset_version}",
                    f"Providers disponibles: {available_providers}"
                ]
                
            except Exception as e:
                issues.append(f"Erreur lors de la vérification: {e}")
                recommendations = ["Vérifier la configuration d'ONNX Runtime"]
        
        elif runtime == "tflite":
            # Vérifications pour TensorFlow Lite
            tflite_unsupported_ops = [
                "RandomNormal", "RandomUniform", "Loop", "Scan"
            ]
            
            for op in tflite_unsupported_ops:
                if op in self.operations:
                    warnings.append(f"Opération {op} peut être problématique pour TensorFlow Lite")
            
            recommendations = [
                "Utiliser tf2onnx ou onnx-tf pour la conversion",
                "Vérifier la compatibilité après conversion"
            ]
        
        else:
            warnings.append(f"Runtime {runtime} non spécifiquement supporté")
            recommendations = ["Vérifier la documentation du runtime cible"]
        
        return {
            "platform": "generic",
            "runtime": runtime,
            "compatible": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations
        }
    
    def check_all_platforms(
        self,
        platforms: List[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Vérifie la compatibilité avec toutes les plateformes.
        
        Args:
            platforms: Liste des plateformes à vérifier
            
        Returns:
            Dictionnaire avec résultats par plateforme
        """
        if platforms is None:
            platforms = ["pygame", "web_tensorflowjs", "web_onnxjs", "unity", "generic_onnxruntime"]
        
        results = {}
        
        for platform in platforms:
            if platform == "pygame":
                results["pygame"] = self.check_pygame_compatibility()
            elif platform == "web_tensorflowjs":
                results["web_tensorflowjs"] = self.check_web_compatibility("tensorflowjs")
            elif platform == "web_onnxjs":
                results["web_onnxjs"] = self.check_web_compatibility("onnxjs")
            elif platform == "unity":
                results["unity"] = self.check_unity_compatibility()
            elif platform == "generic_onnxruntime":
                results["generic_onnxruntime"] = self.check_generic_compatibility("onnxruntime")
            elif platform == "generic_tflite":
                results["generic_tflite"] = self.check_generic_compatibility("tflite")
            else:
                print(f"Plateforme non reconnue ignorée: {platform}")
        
        # Générer un rapport global
        global_report = self._generate_global_compatibility_report(results)
        results["global"] = global_report
        
        return results
    
    def _get_problematic_operations(self, platform: str) -> List[str]:
        """
        Retourne la liste des opérations potentiellement problématiques pour une plateforme.
        
        Args:
            platform: Plateforme cible
            
        Returns:
            Liste des opérations problématiques
        """
        # Définitions des opérations problématiques par plateforme
        problematic_ops = {
            "pygame": [
                "RandomNormal", "RandomUniform",  # Aléatoire non déterministe
                "Loop", "Scan",  # Boucles complexes
            ],
            "web": [
                "RandomNormal", "RandomUniform",
                "Loop", "Scan", "If", "Sequence",
            ],
            "unity": [
                "RandomNormal", "RandomUniform", "Dropout",
                "Loop", "Scan", "If", "Sequence", "Resize",
            ]
        }
        
        return problematic_ops.get(platform, [])
    
    def _generate_global_compatibility_report(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Génère un rapport global de compatibilité.
        
        Args:
            results: Résultats par plateforme
            
        Returns:
            Rapport global
        """
        compatible_platforms = []
        partially_compatible_platforms = []
        incompatible_platforms = []
        
        for platform_name, platform_result in results.items():
            if platform_name == "global":
                continue
            
            if platform_result.get("compatible", False):
                if platform_result.get("warnings", []):
                    partially_compatible_platforms.append(platform_name)
                else:
                    compatible_platforms.append(platform_name)
            else:
                incompatible_platforms.append(platform_name)
        
        # Calculer un score de compatibilité
        total_platforms = len(results) - 1  # Exclure "global"
        if total_platforms > 0:
            compatibility_score = (len(compatible_platforms) / total_platforms) * 100
        else:
            compatibility_score = 0
        
        # Recommandations globales
        global_recommendations = []
        
        if incompatible_platforms:
            global_recommendations.append(
                f"Modifier le modèle pour la compatibilité avec: {', '.join(incompatible_platforms)}"
            )
        
        if partially_compatible_platforms:
            global_recommendations.append(
                f"Vérifier les avertissements pour: {', '.join(partially_compatible_platforms)}"
            )
        
        if compatible_platforms:
            global_recommendations.append(
                f"Plateformes entièrement compatibles: {', '.join(compatible_platforms)}"
            )
        
        return {
            "compatible_platforms": compatible_platforms,
            "partially_compatible_platforms": partially_compatible_platforms,
            "incompatible_platforms": incompatible_platforms,
            "compatibility_score": compatibility_score,
            "total_platforms_tested": total_platforms,
            "recommendations": global_recommendations,
            "overall_status": "EXCELLENT" if compatibility_score >= 90 else
                            "BON" if compatibility_score >= 70 else
                            "MODÉRÉ" if compatibility_score >= 50 else
                            "LIMITÉ"
        }
    
    def generate_compatibility_matrix(self) -> str:
        """
        Génère une matrice de compatibilité au format markdown.
        
        Returns:
            Matrice de compatibilité formatée
        """
        # Vérifier toutes les plateformes
        results = self.check_all_platforms()
        
        # Construire la matrice
        matrix_lines = []
        
        matrix_lines.append("# Matrice de Compatibilité ONNX")
        matrix_lines.append("")
        matrix_lines.append(f"**Modèle:** {os.path.basename(self.onnx_model_path)}")
        matrix_lines.append(f"**Taille:** {os.path.getsize(self.onnx_model_path) / (1024 * 1024):.2f} MB")
        matrix_lines.append(f"**Opérations:** {len(self.operations)} types")
        matrix_lines.append("")
        
        # En-tête du tableau
        matrix_lines.append("| Plateforme | Compatible | Problèmes | Avertissements |")
        matrix_lines.append("|------------|------------|-----------|----------------|")
        
        for platform_name, platform_result in results.items():
            if platform_name == "global":
                continue
            
            compatible = "✅" if platform_result.get("compatible", False) else "❌"
            issues_count = len(platform_result.get("issues", []))
            warnings_count = len(platform_result.get("warnings", []))
            
            issues_display = f"{issues_count}" if issues_count > 0 else "-"
            warnings_display = f"{warnings_count}" if warnings_count > 0 else "-"
            
            matrix_lines.append(f"| {platform_name} | {compatible} | {issues_display} | {warnings_display} |")
        
        # Résumé global
        global_result = results["global"]
        matrix_lines.append("")
        matrix_lines.append("## Résumé Global")
        matrix_lines.append(f"- **Score de compatibilité:** {global_result['compatibility_score']:.1f}%")
        matrix_lines.append(f"- **Statut:** {global_result['overall_status']}")
        matrix_lines.append(f"- **Plateformes compatibles:** {len(global_result['compatible_platforms'])}/{global_result['total_platforms_tested']}")
        
        if global_result['compatible_platforms']:
            matrix_lines.append(f"- **Liste des plateformes compatibles:** {', '.join(global_result['compatible_platforms'])}")
        
        if global_result['incompatible_platforms']:
            matrix_lines.append(f"- **Plateformes incompatibles:** {', '.join(global_result['incompatible_platforms'])}")
        
        # Recommandations
        if global_result['recommendations']:
            matrix_lines.append("")
            matrix_lines.append("## Recommandations")
            for i, rec in enumerate(global_result['recommendations'], 1):
                matrix_lines.append(f"{i}. {rec}")
        
        return "\n".join(matrix_lines)
    
    def save_compatibility_report(
        self,
        output_path: str,
        platforms: List[str] = None
    ) -> str:
        """
        Sauvegarde un rapport de compatibilité complet.
        
        Args:
            output_path: Chemin de sortie
            platforms: Plateformes à inclure
            
        Returns:
            Chemin du fichier généré
        """
        # Vérifier la compatibilité
        results = self.check_all_platforms(platforms)
        
        # Générer la matrice
        matrix = self.generate_compatibility_matrix()
        
        # Sauvegarder le rapport
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(matrix)
        
        # Sauvegarder également les résultats détaillés en JSON
        json_path = output_path.replace('.txt', '.json').replace('.md', '.json')
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Rapport de compatibilité sauvegardé: {output_path}")
        print(f"Résultats détaillés: {json_path}")
        
        return output_path


def check_compatibility_cli():
    """Interface en ligne de commande pour la vérification de compatibilité."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vérifier la compatibilité d'un modèle ONNX")
    parser.add_argument("onnx_model", help="Chemin vers le modèle ONNX")
    parser.add_argument("--output_report", default="./compatibility_report.md", help="Fichier de rapport")
    parser.add_argument("--platforms", nargs="+",
                       choices=["pygame", "web_tensorflowjs", "web_onnxjs", "unity",
                               "generic_onnxruntime", "generic_tflite", "all"],
                       default=["all"], help="Plateformes à vérifier")
    
    args = parser.parse_args()
    
    # Convertir "all" en liste de toutes les plateformes
    if "all" in args.platforms:
        args.platforms = ["pygame", "web_tensorflowjs", "web_onnxjs", "unity", "generic_onnxruntime"]
    
    # Vérifier la compatibilité
    checker = CompatibilityChecker(args.onnx_model)
    checker.save_compatibility_report(args.output_report, args.platforms)
    
    print(f"\nVérification de compatibilité terminée. Rapport: {args.output_report}")


if __name__ == "__main__":
    check_compatibility_cli()