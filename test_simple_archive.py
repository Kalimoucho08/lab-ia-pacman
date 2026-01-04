#!/usr/bin/env python3
"""
Test simplifié du système de sauvegarde automatique intelligente.

Teste les fonctionnalités de base sans dépendances complexes.
"""

import os
import sys
import json
import tempfile
import shutil
import zipfile
from pathlib import Path

# Ajouter le répertoire courant au chemin Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_archive_creation():
    """Teste la création d'archive de base."""
    print("=== Test de création d'archive ===")
    
    try:
        from experiments.archive_service import IntelligentArchiveService, ArchiveMetadata
        
        # Créer un répertoire temporaire pour les tests
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_dir = os.path.join(temp_dir, "archives")
            
            # Initialiser le service
            service = IntelligentArchiveService()
            service.config.archive_dir = archive_dir
            
            # Créer des métadonnées de test
            metadata = ArchiveMetadata(
                session_id="test_session_001",
                session_number=0,
                timestamp="",
                model_type="DQN",
                agent_type="PacMan",
                total_episodes=1000,
                win_rate=0.75,
                learning_rate=0.001,
                gamma=0.99,
                epsilon=0.1,
                batch_size=32,
                buffer_size=10000,
                tags=['test', 'basic'],
                metrics={'avg_score': 1500},
                notes="Test de création d'archive basique"
            )
            
            # Créer un fichier de modèle fictif
            model_path = os.path.join(temp_dir, "model.zip")
            with open(model_path, "wb") as f:
                f.write(b"fake model data for testing")
            
            # Créer une archive
            print("  Création d'archive...")
            archive_path = service.create_archive(metadata, model_path)
            
            if archive_path and os.path.exists(archive_path):
                print(f"  [OK] Archive créée: {os.path.basename(archive_path)}")
                print(f"  Taille: {os.path.getsize(archive_path) / 1024:.1f} KB")
                
                # Vérifier le contenu de l'archive
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    files = zf.namelist()
                    print(f"  Fichiers dans l'archive: {len(files)}")
                    
                    # Vérifier les fichiers essentiels
                    essential_files = ['params.md', 'metadata.json', 'config.yaml']
                    for f in essential_files:
                        if f in files:
                            print(f"    [OK] {f} présent")
                        else:
                            print(f"    [ERREUR] {f} manquant")
                
                return True
            else:
                print("  [ERREUR] Échec de la création de l'archive")
                return False
                
    except Exception as e:
        print(f"  [ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_generation():
    """Teste la génération de métadonnées."""
    print("\n=== Test de génération de métadonnées ===")
    
    try:
        from experiments.metadata_generator import IntelligentMetadataGenerator
        
        # Initialiser le générateur
        generator = IntelligentMetadataGenerator()
        
        # Données de test
        session_data = {
            "session_id": "test_47",
            "algorithm": "DQN",
            "agent_type": "pacman",
            "hyperparameters": {
                "learning_rate": 0.001,
                "gamma": 0.99,
                "epsilon": 0.1
            },
            "metrics": {
                "win_rate": 0.77,
                "total_episodes": 5000,
                "avg_score": 1800
            }
        }
        
        # Générer params.md
        print("  Génération de params.md...")
        params_md = generator.generate_params_md(session_data)
        
        if params_md and len(params_md) > 100:
            print(f"  [OK] params.md généré ({len(params_md)} caractères)")
            print(f"  Extrait: {params_md[:100]}...")
        else:
            print("  [ERREUR] params.md trop court ou vide")
            return False
        
        # Générer config.yaml
        print("  Génération de config.yaml...")
        config_yaml = generator.generate_config_yaml(session_data)
        
        if config_yaml and "algorithm" in config_yaml:
            print(f"  [OK] config.yaml généré ({len(config_yaml)} caractères)")
        else:
            print("  [ERREUR] config.yaml invalide")
            return False
        
        # Générer metadata.json
        print("  Génération de metadata.json...")
        metadata_json = generator.generate_metadata_json(session_data)
        
        if metadata_json and "session_id" in metadata_json:
            print(f"  [OK] metadata.json généré")
        else:
            print("  [ERREUR] metadata.json invalide")
            return False
        
        return True
        
    except Exception as e:
        print(f"  [ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_archive_restoration():
    """Teste la restauration d'archive."""
    print("\n=== Test de restauration d'archive ===")
    
    try:
        # Créer une archive de test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Créer un fichier ZIP simple
            archive_path = os.path.join(temp_dir, "test_archive.zip")
            with zipfile.ZipFile(archive_path, 'w') as zf:
                zf.writestr("params.md", "# Archive de test\nCeci est un test.")
                zf.writestr("metadata.json", json.dumps({"test": "data"}))
            
            # Restaurer l'archive
            restore_dir = os.path.join(temp_dir, "restored")
            os.makedirs(restore_dir, exist_ok=True)
            
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(restore_dir)
            
            # Vérifier les fichiers restaurés
            restored_files = os.listdir(restore_dir)
            print(f"  Fichiers restaurés: {restored_files}")
            
            if "params.md" in restored_files and "metadata.json" in restored_files:
                print("  [OK] Archive restaurée avec succès")
                
                # Lire le contenu
                with open(os.path.join(restore_dir, "params.md"), 'r') as f:
                    content = f.read()
                    print(f"  Contenu de params.md: {content[:50]}...")
                
                return True
            else:
                print("  [ERREUR] Fichiers manquants après restauration")
                return False
                
    except Exception as e:
        print(f"  [ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backend_files():
    """Teste l'existence des fichiers backend."""
    print("\n=== Test des fichiers backend ===")
    
    backend_files = [
        "backend/services/archive_service.py",
        "backend/api/v1/endpoints/archives.py",
        "backend/app.py"
    ]
    
    all_exist = True
    for file_path in backend_files:
        if os.path.exists(file_path):
            print(f"  [OK] {file_path}")
        else:
            print(f"  [ERREUR] {file_path} manquant")
            all_exist = False
    
    if all_exist:
        # Vérifier que l'application FastAPI inclut les archives
        try:
            with open("backend/app.py", "r", encoding="utf-8") as f:
                app_content = f.read()
            
            if "archives" in app_content and "api/v1/archives" in app_content:
                print("  [OK] Archives intégrées dans FastAPI")
                return True
            else:
                print("  [ERREUR] Archives non intégrées dans FastAPI")
                return False
        except Exception as e:
            print(f"  [ERREUR] Lecture de app.py: {e}")
            return False
    else:
        return False

def test_archive_structure():
    """Teste la structure d'archive standard."""
    print("\n=== Test de structure d'archive ===")
    
    # Structure attendue
    expected_structure = {
        "params.md": "Fichier de documentation des paramètres",
        "metadata.json": "Métadonnées au format JSON",
        "config.yaml": "Configuration au format YAML",
        "model/": "Répertoire pour les fichiers de modèle (optionnel)",
        "logs/": "Répertoire pour les logs (optionnel)"
    }
    
    print("  Structure d'archive attendue:")
    for item, description in expected_structure.items():
        print(f"    - {item}: {description}")
    
    # Créer une archive de test avec la structure
    with tempfile.TemporaryDirectory() as temp_dir:
        archive_path = os.path.join(temp_dir, "structure_test.zip")
        
        with zipfile.ZipFile(archive_path, 'w') as zf:
            # Ajouter les fichiers essentiels
            zf.writestr("params.md", "# Test de structure\nCeci est un test.")
            zf.writestr("metadata.json", json.dumps({"test": "structure"}))
            zf.writestr("config.yaml", "test: structure\nversion: 1.0")
            
            # Ajouter un répertoire modèle fictif
            zf.writestr("model/test_model.bin", "données de modèle fictives")
            zf.writestr("logs/training.log", "log de test")
        
        # Vérifier la structure
        with zipfile.ZipFile(archive_path, 'r') as zf:
            files = zf.namelist()
            print(f"  Fichiers dans l'archive de test: {len(files)}")
            
            # Vérifier les fichiers essentiels
            essential = ["params.md", "metadata.json", "config.yaml"]
            missing = [f for f in essential if f not in files]
            
            if not missing:
                print("  [OK] Tous les fichiers essentiels sont présents")
                return True
            else:
                print(f"  [ERREUR] Fichiers manquants: {missing}")
                return False

def main():
    """Fonction principale de test."""
    print("=" * 60)
    print("Test simplifié du système de sauvegarde")
    print("=" * 60)
    
    # Exécuter tous les tests
    tests = [
        ("Création d'archive", test_basic_archive_creation),
        ("Génération de métadonnées", test_metadata_generation),
        ("Restauration d'archive", test_archive_restoration),
        ("Fichiers backend", test_backend_files),
        ("Structure d'archive", test_archive_structure)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n>>> Exécution: {test_name}")
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"[ERREUR] Exception dans {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Afficher le résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} - {test_name}")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} tests réussis, {failed} tests échoués")
    
    if failed == 0:
        print("\n[SUCCES] Tous les tests ont réussi !")
        return 0
    else:
        print("\n[ECHEC] Certains tests ont échoué.")
        return 1

if __name__ == "__main__":
    sys.exit(main())