#!/usr/bin/env python3
"""
Test d'import des modules principaux après installation.
"""
import sys
print("Python version:", sys.version)

modules = [
    ("numpy", "numpy"),
    ("matplotlib", "matplotlib"),
    ("gymnasium", "gymnasium"),
    ("stable_baselines3", "stable_baselines3"),
    ("torch", "torch"),
    ("pygame", "pygame"),
    ("pettingzoo", "pettingzoo"),
    ("supersuit", "supersuit"),
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("psutil", "psutil"),
    ("yaml", "yaml"),
    ("httpx", "httpx"),
    ("onnx", "onnx"),
    ("sqlalchemy", "sqlalchemy"),
]

failed = []
for name, mod in modules:
    try:
        __import__(mod)
        print(f"[OK] {name} importe")
    except Exception as e:
        print(f"[FAIL] {name} echec: {e}")
        failed.append((name, e))

print("\n--- Résultat ---")
if failed:
    print(f"{len(failed)} modules ont échoué:")
    for name, err in failed:
        print(f"  - {name}: {err}")
else:
    print("Tous les imports ont réussi.")

# Test des modules spécifiques au projet
try:
    from src.pacman_env import multiagent_env
    print("[OK] src.pacman_env.multiagent_env importe")
except Exception as e:
    print(f"[FAIL] src.pacman_env.multiagent_env: {e}")

try:
    from src.pacman_env import multiagent_wrappers
    print("[OK] src.pacman_env.multiagent_wrappers importe")
except Exception as e:
    print(f"[FAIL] src.pacman_env.multiagent_wrappers: {e}")

sys.exit(0 if len(failed) == 0 else 1)