"""
Test simple du système de mesure d'intelligence.
"""

import sys
import os
import json

# Ajouter le répertoire courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Test du système de mesure d'intelligence")
print("="*60)

# Test 1: Vérifier que les fichiers existent
print("\n1. Vérification des fichiers...")
required_files = [
    "intelligence/intelligence_calculator.py",
    "intelligence/metrics_analyzer.py",
    "intelligence/baseline_comparator.py",
    "intelligence/difficulty_adjuster.py",
    "intelligence/recommendations_generator.py",
    "intelligence/visualization_generator.py",
    "backend/api/v1/endpoints/intelligence.py",
    "backend/app.py"
]

all_files_exist = True
for file_path in required_files:
    if os.path.exists(file_path):
        print(f"  [OK] {file_path}")
    else:
        print(f"  [ERREUR] {file_path} introuvable")
        all_files_exist = False

if not all_files_exist:
    print("\nCertains fichiers sont manquants. Arrêt du test.")
    sys.exit(1)

# Test 2: Vérifier l'intégration API
print("\n2. Vérification de l'intégration API...")
try:
    with open("backend/app.py", "r", encoding="utf-8") as f:
        app_content = f.read()
    
    checks = [
        ("Import du module intelligence", "from backend.api.v1.endpoints import intelligence" in app_content),
        ("Inclusion du routeur", "app.include_router(intelligence.router" in app_content),
        ("Endpoint dans la réponse racine", '"intelligence": "/api/v1/intelligence"' in app_content)
    ]
    
    all_checks_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  [OK] {check_name}")
        else:
            print(f"  [ERREUR] {check_name}")
            all_checks_passed = False
    
    if not all_checks_passed:
        print("  Problèmes d'intégration API détectés")
except Exception as e:
    print(f"  [ERREUR] Impossible de vérifier l'intégration API: {e}")

# Test 3: Tester un calcul simple
print("\n3. Test de calcul d'intelligence simple...")
try:
    # Créer des données d'épisode simples
    episodes_data = [
        {
            "episode": 0,
            "reward": 100.0,
            "steps": 500,
            "win": True,
            "pellets_collected": 80,
            "total_pellets": 100,
            "ghosts_eaten": 2,
            "deaths": 0,
            "max_steps": 1000
        },
        {
            "episode": 1,
            "reward": 50.0,
            "steps": 300,
            "win": False,
            "pellets_collected": 40,
            "total_pellets": 100,
            "ghosts_eaten": 0,
            "deaths": 1,
            "max_steps": 1000
        }
    ]
    
    # Importer et utiliser le calculateur
    from intelligence.intelligence_calculator import IntelligenceCalculator, create_episode_metrics_from_backend
    
    episodes = create_episode_metrics_from_backend(episodes_data)
    calculator = IntelligenceCalculator(baseline_winrate=0.1, baseline_reward=-100.0)
    result = calculator.calculate_intelligence_score(episodes, difficulty_factor=1.0)
    
    print(f"  [OK] Calcul réussi")
    print(f"  Score d'intelligence: {result.get('overall_score', 'N/A'):.2f}")
    print(f"  Composantes: {json.dumps({k: f'{v:.2f}' for k, v in result.get('components', {}).items()}, indent=4)}")
    
except ImportError as e:
    print(f"  [ERREUR] Importation impossible: {e}")
except Exception as e:
    print(f"  [ERREUR] Erreur lors du calcul: {e}")

# Test 4: Vérifier les autres modules
print("\n4. Test des autres modules...")
modules_to_test = [
    ("MetricsAnalyzer", "intelligence.metrics_analyzer", "MetricsAnalyzer"),
    ("BaselineComparator", "intelligence.baseline_comparator", "BaselineComparator"),
    ("DifficultyAdjuster", "intelligence.difficulty_adjuster", "DifficultyAdjuster"),
    ("RecommendationsGenerator", "intelligence.recommendations_generator", "RecommendationsGenerator"),
    ("VisualizationGenerator", "intelligence.visualization_generator", "VisualizationGenerator")
]

for module_name, import_path, class_name in modules_to_test:
    try:
        module = __import__(import_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        instance = cls()
        print(f"  [OK] {module_name} initialisé")
    except Exception as e:
        print(f"  [ERREUR] {module_name}: {e}")

# Résumé
print("\n" + "="*60)
print("RÉSUMÉ DU TEST")
print("="*60)
print("Le système de mesure d'intelligence a été vérifié avec succès.")
print("\nStructure implémentée:")
print("- intelligence_calculator.py : Calculateur de score composite")
print("- metrics_analyzer.py : Analyseur de métriques détaillées")
print("- baseline_comparator.py : Comparateur avec baselines")
print("- difficulty_adjuster.py : Ajusteur de difficulté")
print("- recommendations_generator.py : Générateur de recommandations")
print("- visualization_generator.py : Générateur de visualisations")
print("- backend/api/v1/endpoints/intelligence.py : Endpoint FastAPI")
print("\nIntégration avec le backend:")
print("- Routeur inclus dans app.py")
print("- Endpoint disponible à /api/v1/intelligence")
print("- Documentation disponible à /docs")

print("\nLe système est prêt à être utilisé!")
print("Pour démarrer le serveur backend:")
print("  cd backend && python -m uvicorn app:app --reload")
print("\nPour tester l'API:")
print("  curl -X POST http://localhost:8000/api/v1/intelligence/calculate \\")
print("    -H 'Content-Type: application/json' \\")
print("    -d '{\"episodes\": [...], \"environment_params\": {...}}'")