#!/usr/bin/env python3
"""
Test des imports critiques dans l'environnement venv311.
"""
import sys

print("Python executable:", sys.executable)
print("Python version:", sys.version)
print()

modules = [
    "numpy",
    "matplotlib",
    "gymnasium",
    "torch",
    "pygame",
    "onnxruntime",
    "sqlalchemy",
    "fastapi",
    "pydantic",
    "tensorflow",
    "stable_baselines3",
    "pettingzoo",
    "supersuit",
    "tkinter",
]

for mod in modules:
    try:
        __import__(mod)
        print(f"[OK] {mod}")
    except ImportError as e:
        print(f"[FAIL] {mod}: {e}")
    except Exception as e:
        print(f"[ERROR] {mod}: {e}")

print("\n--- Liste des packages installés ---")
try:
    import pkg_resources
    installed = sorted([pkg.key for pkg in pkg_resources.working_set])
    print(f"Total: {len(installed)} packages")
    for pkg in installed[:20]:
        print(f"  {pkg}")
    if len(installed) > 20:
        print(f"  ... et {len(installed)-20} autres")
except:
    print("Impossible de récupérer la liste des packages.")