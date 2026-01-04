#!/usr/bin/env python3
"""
Script de test pour le système de sauvegarde automatique intelligente.

Teste toutes les fonctionnalités du système d'archivage.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Ajouter le répertoire courant au chemin Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_archive_service():
    """Teste le service d'archivage principal."""
    print("=== Test du service d'archivage ===")
    
    try:
        from experiments.archive_service import IntelligentArchiveService, ArchiveConfig
        
        # Créer un répertoire temporaire pour les tests
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_dir = os.path.join(temp_dir, "archives")
            
            # Initialiser le service
            config = ArchiveConfig(
                archive_dir=archive_dir,
                auto_save_interval=100,
                compression_level=6
            )
            service = IntelligentArchiveService(config=config)
            
            # Créer un fichier de modèle fictif
            model_path = os.path.join(temp_dir, "model.zip")
            with open(model_path, "wb") as f:
                f.write(b"fake model data")
            
            # Créer des métadonnées de test
            metadata = {
                "experiment_id": "test_001",
                "algorithm": "DQN",
                "agent_type": "pacman",
                "hyperparameters": {
                    "learning_rate": 0.001,
                    "gamma": 0.99,
                    "epsilon": 0.1
                },
                "metrics": {
                    "win_rate": 0.75,
                    "total_episodes": 1000,
                    "average_score": 1500
                }
            }
            
            # Créer une archive
            print("  Création d'une archive...")
            archive_info = service.create_archive(
                model_path=model_path,
                metadata=metadata,
                tags=["test", "dqn", "pacman"]
            )
            
            print(f"  Archive créée: {archive_info['archive_name']}")
            print(f"  Chemin: {archive_info['archive_path']}")
            print(f"  Taille: {archive_info['size_mb']:.2f} MB")
            
            # Vérifier que l'archive existe
            assert os.path.exists(archive_info["archive_path"]), "L'archive n'a pas été créée"
            
            # Obtenir des informations sur l'archive
            print("  Récupération des informations de l'archive...")
            archive_info2 = service.get_archive_info(archive_info["archive_path"])
            print(f"  Nombre de fichiers: {archive_info2['file_count']}")
            print(f"  Structure: {list(archive_info2['structure'].keys())}")
            
            # Extraire les métadonnées
            print("  Extraction des métadonnées...")
            extracted_metadata = service.extract_metadata(archive_info["archive_path"])
            print(f"  ID d'expérience: {extracted_metadata.get('experiment_id')}")
            print(f"  Algorithm: {extracted_metadata.get('algorithm')}")
            
            # Lister les archives
            print("  Liste des archives...")
            archives = service.list_archives()
            print(f"  Nombre d'archives: {len(archives)}")
            
            print("[OK] Test du service d'archivage réussi")
            return True
            
    except Exception as e:
        print(f"[ERREUR] Erreur lors du test du service d'archivage: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_generator():
    """Teste le générateur de métadonnées intelligent."""
    print("\n=== Test du générateur de métadonnées ===")
    
    try:
        from experiments.metadata_generator import IntelligentMetadataGenerator, TrainingMetrics
        
        # Initialiser le générateur
        generator = IntelligentMetadataGenerator()
        
        # Créer des métriques de test
        metrics = TrainingMetrics(
            win_rate=0.77,
            total_episodes=5000,
            average_score=1800,
            best_score=2500,
            episodes_since_improvement=200,
            training_time_hours=2.5
        )
        
        # Créer des métadonnées de session
        session_metadata = {
            "session_id": 47,
            "algorithm": "DQN",
            "agent_type": "pacman",
            "hyperparameters": {
                "learning_rate": 0.001,
                "gamma": 0.99,
                "epsilon": 0.1,
                "batch_size": 64,
                "buffer_size": 10000
            },
            "previous_session_id": 46,
            "previous_win_rate": 0.65
        }
        
        # Générer le fichier params.md
        print("  Génération de params.md...")
        params_md = generator.generate_params_md(session_metadata, metrics)
        
        print("  Contenu généré:")
        print("-" * 50)
        print(params_md[:500] + "..." if len(params_md) > 500 else params_md)
        print("-" * 50)
        
        # Vérifier que le contenu contient les informations attendues
        assert "Session 47" in params_md, "Le numéro de session n'est pas présent"
        assert "Learning Rate" in params_md, "Le learning rate n'est pas présent"
        assert "Winrate" in params_md, "Le winrate n'est pas présent"
        
        # Générer le fichier config.yaml
        print("  Génération de config.yaml...")
        config_yaml = generator.generate_config_yaml(session_metadata)
        
        # Générer le fichier metadata.json
        print("  Génération de metadata.json...")
        metadata_json = generator.generate_metadata_json(session_metadata, metrics)
        
        print(f"  Taille de params.md: {len(params_md)} caractères")
        print(f"  Taille de config.yaml: {len(config_yaml)} caractères")
        print(f"  Taille de metadata.json: {len(metadata_json)} caractères")
        
        print("[OK] Test du générateur de métadonnées réussi")
        return True
        
    except Exception as e:
        print(f"[ERREUR] Erreur lors du test du générateur de métadonnées: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_session_resumer():
    """Teste le système de reprise de sessions."""
    print("\n=== Test du système de reprise de sessions ===")
    
    try:
        from experiments.session_resumer import SessionResumer
        
        # Créer un répertoire temporaire pour les tests
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialiser le système de reprise
            resumer = SessionResumer()
            
            # Créer deux archives fictives pour la comparaison
            archive1 = os.path.join(temp_dir, "archive1.zip")
            archive2 = os.path.join(temp_dir, "archive2.zip")
            
            # Créer des fichiers ZIP simples
            import zipfile
            with zipfile.ZipFile(archive1, 'w') as zf:
                zf.writestr("params.md", "# Session 46\nLearning Rate: 0.001")
                zf.writestr("metadata.json", json.dumps({"win_rate": 0.65, "episodes": 3000}))
            
            with zipfile.ZipFile(archive2, 'w') as zf:
                zf.writestr("params.md", "# Session 47\nLearning Rate: 0.0005")
                zf.writestr("metadata.json", json.dumps({"win_rate": 0.77, "episodes": 5000}))
            
            # Comparer les sessions
            print("  Comparaison de sessions...")
            comparison = resumer.compare_sessions(archive1, archive2)
            
            print(f"  Différences trouvées: {len(comparison.get('differences', []))}")
            print(f"  Similarité: {comparison.get('similarity_score', 0):.2f}")
            
            # Vérifier que la comparaison contient les informations attendues
            assert "differences" in comparison, "La comparaison ne contient pas de différences"
            assert "similarity_score" in comparison, "La comparaison ne contient pas de score de similarité"
            
            # Tester la fusion de sessions
            print("  Fusion de sessions...")
            merge_result = resumer.merge_sessions([archive1, archive2], os.path.join(temp_dir, "merged"))
            
            print(f"  Fusion réussie: {merge_result.get('success', False)}")
            print(f"  Fichiers fusionnés: {len(merge_result.get('merged_files', []))}")
            
            print("[OK] Test du système de reprise de sessions réussi")
            return True
            
    except Exception as e:
        print(f"[ERREUR] Erreur lors du test du système de reprise de sessions: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_version_manager():
    """Teste le gestionnaire de versions."""
    print("\n=== Test du gestionnaire de versions ===")
    
    try:
        from experiments.version_manager import VersionManager
        
        # Créer un répertoire temporaire pour les tests
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialiser le gestionnaire
            manager = VersionManager(base_dir=temp_dir)
            
            # Enregistrer quelques versions
            print("  Enregistrement de versions...")
            
            for i in range(3):
                archive_path = os.path.join(temp_dir, f"archive_{i}.zip")
                
                # Créer un fichier ZIP fictif
                import zipfile
                with zipfile.ZipFile(archive_path, 'w') as zf:
                    zf.writestr("test.txt", f"Contenu de l'archive {i}")
                
                metadata = {
                    "experiment_id": f"test_{i}",
                    "win_rate": 0.6 + i * 0.1,
                    "episodes": 1000 * (i + 1)
                }
                
                tags = ["test"]
                if i == 2:
                    tags.append("best")
                
                version_info = manager.register_new_version(
                    archive_path=archive_path,
                    metadata=metadata,
                    tags=tags
                )
                
                print(f"  Version {i} enregistrée: {version_info.get('version_id')}")
            
            # Rechercher des versions
            print("  Recherche de versions...")
            versions = manager.search_versions(tags=["test"])
            print(f"  Versions trouvées: {len(versions)}")
            
            # Obtenir les meilleures versions
            print("  Récupération des meilleures versions...")
            best_versions = manager.get_best_versions(limit=2)
            print(f"  Meilleures versions: {len(best_versions)}")
            
            # Exporter les versions
            print("  Export des versions...")
            export_path = os.path.join(temp_dir, "versions_export.json")
            manager.export_versions(export_path)
            
            print(f"  Export créé: {export_path}")
            assert os.path.exists(export_path), "L'export n'a pas été créé"
            
            print("[OK] Test du gestionnaire de versions réussi")
            return True
            
    except Exception as e:
        print(f"[ERREUR] Erreur lors du test du gestionnaire de versions: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backend_integration():
    """Teste l'intégration avec le backend."""
    print("\n=== Test de l'intégration backend ===")
    
    try:
        # Vérifier que les fichiers backend existent
        backend_files = [
            "backend/services/archive_service.py",
            "backend/api/v1/endpoints/archives.py",
            "backend/app.py"
        ]
        
        for file_path in backend_files:
            if not os.path.exists(file_path):
                print(f"[ERREUR] Fichier manquant: {file_path}")
                return False
        
        print("  Fichiers backend vérifiés:")
        for file_path in backend_files:
            print(f"    [OK] {file_path}")
        
        # Vérifier que le service d'archivage peut être importé
        print("  Import du service d'archivage...")
        try:
            from backend.services.archive_service import ArchiveService
            print("    [OK] ArchiveService importé avec succès")
        except ImportError as e:
            print(f"    [ERREUR] Erreur d'import: {e}")
            return False
        
        # Vérifier que les endpoints peuvent être importés
        print("  Import des endpoints...")
        try:
            from backend.api.v1.endpoints.archives import router
            print("    [OK] Router des archives importé avec succès")
        except ImportError as e:
            print(f"    [ERREUR] Erreur d'import: {e}")
            return False
        
        # Vérifier que l'application FastAPI inclut les archives
        print("  Vérification de l'application FastAPI...")
        with open("backend/app.py", "r", encoding="utf-8") as f:
            app_content = f.read()
        
        if "archives" in app_content and "api/v1/archives" in app_content:
            print("    [OK] Archives intégrées dans l'application FastAPI")
        else:
            print("    [ERREUR] Archives non intégrées dans l'application FastAPI")
            return False
        
        print("[OK] Test de l'intégration backend réussi")
        return True
        
    except Exception as e:
        print(f"[ERREUR] Erreur lors du test de l'intégration backend: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale de test."""
    print("=" * 60)
    print("Test du système de sauvegarde automatique intelligente")
    print("=" * 60)
    
    # Exécuter tous les tests
    tests = [
        ("Service d'archivage", test_archive_service),
        ("Générateur de métadonnées", test_metadata_generator),
        ("Système de reprise", test_session_resumer),
        ("Gestionnaire de versions", test_version_manager),
        ("Intégration backend", test_backend_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"[ERREUR] Exception non geree dans {test_name}: {e}")
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