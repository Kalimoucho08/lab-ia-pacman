#!/usr/bin/env python3
"""
Script de test d'import pour vérifier que tous les modules Python du projet
s'importent correctement sans erreur.
"""
import sys
import traceback
import importlib

# Liste des modules à tester (chemins relatifs)
MODULES_TO_TEST = [
    # Core
    "src.__main__",
    "src.main_gui",
    "src.run_pacman",
    "src.agents.random_agent",
    "src.pacman_env.__init__",
    "src.pacman_env.configurable_env",
    "src.pacman_env.duel_env",
    "src.pacman_env.multiagent_env",
    "src.pacman_env.multiagent_wrappers",
    "src.utils.helpers",
    # Backend
    "backend.app",
    "backend.config",
    "backend.db.database",
    "backend.api.v1.endpoints.experiments",
    "backend.api.v1.endpoints.training",
    "backend.api.v1.endpoints.environment",
    "backend.api.v1.endpoints.visualization",
    "backend.api.v1.endpoints.archives",
    "backend.api.v1.endpoints.intelligence",
    "backend.api.v1.endpoints.onnx",
    "backend.services.archive_service",
    "backend.services.environment_service",
    "backend.services.experiment_service",
    "backend.services.onnx_export_service",
    "backend.services.training_service",
    "backend.services.websocket_service",
    "backend.utils.error_handling",
    # Intelligence
    "intelligence.baseline_comparator",
    "intelligence.difficulty_adjuster",
    "intelligence.intelligence_calculator",
    "intelligence.metrics_analyzer",
    "intelligence.recommendations_generator",
    "intelligence.visualization_generator",
    # ONNX Export
    "onnx_export.compatibility_checker",
    "onnx_export.metadata_embedder",
    "onnx_export.onnx_converter",
    "onnx_export.optimizer",
    "onnx_export.platform_adapter",
    "onnx_export.validator",
    # Experiments
    "experiments.archive_service",
    "experiments.archive_validator",
    "experiments.compression_optimizer",
    "experiments.metadata_generator",
    "experiments.session_resumer",
    "experiments.version_manager",
]

def test_import(module_name):
    """Tente d'importer un module et retourne le résultat."""
    try:
        module = importlib.import_module(module_name)
        return True, f"OK: {module_name}"
    except Exception as e:
        return False, f"ERREUR: {module_name} - {type(e).__name__}: {e}"

def main():
    print("=== Test d'import des modules Python ===\n")
    results = []
    errors = []
    
    for module_name in MODULES_TO_TEST:
        success, message = test_import(module_name)
        results.append((success, message))
        if not success:
            errors.append(message)
        print(message)
    
    print("\n=== Résumé ===")
    total = len(results)
    passed = sum(1 for success, _ in results if success)
    failed = total - passed
    
    print(f"Modules testés: {total}")
    print(f"Modules importés avec succès: {passed}")
    print(f"Modules en échec: {failed}")
    
    if errors:
        print("\n=== Détails des erreurs ===")
        for error in errors:
            print(f"  - {error}")
        
        # Afficher les traces pour les premières erreurs
        print("\n=== Traces d'erreur détaillées (premières 3) ===")
        for i, module_name in enumerate(MODULES_TO_TEST):
            if i >= 3:
                break
            try:
                importlib.import_module(module_name)
            except Exception as e:
                print(f"\n--- Trace pour {module_name} ---")
                traceback.print_exc()
    
    sys.exit(1 if failed > 0 else 0)

if __name__ == "__main__":
    main()