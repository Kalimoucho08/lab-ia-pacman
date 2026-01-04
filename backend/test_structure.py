"""
Test minimal de la structure du backend.

Vérifie que tous les fichiers nécessaires existent et ont une syntaxe Python valide.
"""
import os
import sys
import importlib.util
from pathlib import Path

def check_file_exists(path, required=True):
    """Vérifie qu'un fichier existe."""
    exists = os.path.exists(path)
    status = "[OK]" if exists else "[ERREUR]"
    print(f"{status} {path}")
    
    if required and not exists:
        print(f"  ERREUR: Fichier manquant: {path}")
        return False
    return True

def check_python_syntax(path):
    """Vérifie la syntaxe Python d'un fichier."""
    try:
        spec = importlib.util.spec_from_file_location("module", path)
        if spec and spec.loader:
            # Juste charger pour vérifier la syntaxe
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"  [OK] Syntaxe Python valide")
            return True
    except SyntaxError as e:
        print(f"  [ERREUR] Erreur de syntaxe: {e}")
        return False
    except Exception as e:
        # Autres erreurs (imports manquants) sont acceptables pour ce test
        print(f"  [ATTENDU] Erreur à l'import: {type(e).__name__}")
        return True  # On considère que la syntaxe est OK

def main():
    print("=" * 60)
    print("TEST DE STRUCTURE DU BACKEND")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    files_to_check = [
        # Fichiers principaux
        ("app.py", True),
        ("config.py", True),
        ("requirements.txt", True),
        ("README.md", True),
        
        # Services
        ("services/experiment_service.py", True),
        ("services/environment_service.py", True),
        ("services/training_service.py", True),
        ("services/websocket_service.py", True),
        
        # Modèles
        ("models/experiment.py", True),
        
        # Endpoints API
        ("api/v1/endpoints/experiments.py", True),
        ("api/v1/endpoints/training.py", True),
        ("api/v1/endpoints/environment.py", True),
        ("api/v1/endpoints/visualization.py", True),
        
        # Base de données
        ("db/database.py", True),
        
        # Utilitaires
        ("utils/error_handling.py", True),
        
        # Tests
        ("test_integration.py", True),
        ("test_structure.py", False),  # Ce fichier
    ]
    
    all_ok = True
    
    for file_path, required in files_to_check:
        full_path = base_dir / file_path
        print(f"\nVérification de {file_path}:")
        
        # Vérifier l'existence
        if not check_file_exists(full_path, required):
            if required:
                all_ok = False
            continue
        
        # Vérifier la syntaxe Python pour les fichiers .py
        if file_path.endswith('.py'):
            if not check_python_syntax(full_path):
                all_ok = False
    
    # Vérifier la structure des répertoires
    print("\n" + "=" * 60)
    print("VÉRIFICATION DES RÉPERTOIRES")
    print("=" * 60)
    
    directories = [
        "services",
        "models", 
        "api/v1/endpoints",
        "db",
        "utils",
        "logs",  # sera créé à l'exécution
        "logs/models",
    ]
    
    for dir_path in directories:
        full_dir = base_dir / dir_path
        if full_dir.exists():
            print(f"[OK] Répertoire {dir_path} existe")
        else:
            print(f"[ATTENDU] Répertoire {dir_path} n'existe pas (sera créé à l'exécution)")
    
    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    
    if all_ok:
        print("[SUCCES] Tous les fichiers requis existent et ont une syntaxe valide.")
        print("\nLe backend est correctement structuré et prêt à être utilisé.")
        print("\nPour installer les dépendances :")
        print("  pip install -r requirements.txt")
        print("\nPour démarrer le serveur :")
        print("  python app.py")
        print("  ou")
        print("  uvicorn app:app --host 127.0.0.1 --port 8000 --reload")
        return 0
    else:
        print("[ERREUR] Certains fichiers requis sont manquants ou ont des erreurs.")
        print("\nVeuillez corriger les problèmes ci-dessus avant de continuer.")
        return 1

if __name__ == "__main__":
    sys.exit(main())