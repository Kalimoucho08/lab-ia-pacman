#!/usr/bin/env python3
"""
Test d'import spécifique pour les modules backend.
"""
import sys
import importlib

MODULES = [
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
]

def test():
    errors = []
    for module in MODULES:
        try:
            importlib.import_module(module)
            print(f"OK: {module}")
        except Exception as e:
            print(f"ERREUR: {module} - {type(e).__name__}: {e}")
            errors.append((module, e))
    
    print(f"\nTotal: {len(MODULES)}, Réussis: {len(MODULES)-len(errors)}, Échecs: {len(errors)}")
    return len(errors) == 0

if __name__ == "__main__":
    success = test()
    sys.exit(0 if success else 1)