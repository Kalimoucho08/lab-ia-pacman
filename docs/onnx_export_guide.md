# Guide d'export ONNX universel

Ce guide décrit le système d'export ONNX universel pour le laboratoire scientifique IA Pac-Man. Ce système permet de convertir les modèles Stable-Baselines3 en format ONNX compatible avec plusieurs plateformes.

## Table des matières

1. [Introduction](#introduction)
2. [Architecture du système](#architecture-du-système)
3. [Installation des dépendances](#installation-des-dépendances)
4. [Utilisation via l'interface en ligne de commande](#utilisation-via-linterface-en-ligne-de-commande)
5. [Utilisation via l'API REST](#utilisation-via-lapi-rest)
6. [Plateformes supportées](#plateformes-supportées)
7. [Optimisations disponibles](#optimisations-disponibles)
8. [Validation et compatibilité](#validation-et-compatibilité)
9. [Exemples pratiques](#exemples-pratiques)
10. [Dépannage](#dépannage)
11. [Référence API](#référence-api)

## Introduction

Le système d'export ONNX universel permet de convertir les modèles d'apprentissage par renforcement (RL) entraînés avec Stable-Baselines3 (DQN, PPO, A2C, SAC, TD3) en format ONNX standard. Cette conversion permet d'exécuter les modèles sur différentes plateformes :

- **Pygame classique** : Runtime ONNX Python
- **Web (TensorFlow.js)** : Conversion vers TensorFlow.js/ONNX.js
- **Unity (Barracuda)** : Compatibilité directe avec Barracuda
- **Interface générique** : Inférence via API REST

## Architecture du système

Le système est organisé en plusieurs modules dans le répertoire `onnx_export/` :

```
onnx_export/
├── onnx_converter.py      # Conversion principale SB3 → ONNX
├── metadata_embedder.py   # Incorporation de métadonnées
├── platform_adapter.py    # Adaptation pour différentes plateformes
├── optimizer.py           # Optimisations (quantisation, fusion)
├── validator.py           # Validation complète des exports
└── compatibility_checker.py # Vérification de compatibilité
```

### Services backend

- `backend/services/onnx_export_service.py` : Service principal d'export
- `backend/api/v1/endpoints/onnx.py` : Endpoints API REST
- Intégration avec `backend/app.py` : Routeur FastAPI

## Installation des dépendances

### Dépendances principales

```bash
pip install onnx onnxruntime onnxconverter-common onnxsim stable-baselines3
```

### Dépendances optionnelles

Pour l'export vers TensorFlow.js :
```bash
pip install onnx2tf tensorflowjs
```

Pour l'export vers Unity (Barracuda) :
```bash
pip install onnx onnxruntime
```

### Vérification de l'installation

```python
import onnx
import onnxruntime
import stable_baselines3
print("Modules installés avec succès")
```

## Utilisation via l'interface en ligne de commande

Chaque module peut être utilisé directement depuis la ligne de commande :

### 1. Conversion d'un modèle SB3 vers ONNX

```bash
python -m onnx_export.onnx_converter --model-path logs/pacman_DQN_20260104.zip --output-dir exports/
```

Options disponibles :
- `--algorithm` : Algorithme RL (auto, DQN, PPO, A2C, SAC, TD3)
- `--include-metadata` : Inclure les métadonnées (défaut: True)
- `--test-conversion` : Tester la conversion (défaut: True)

### 2. Incorporation de métadonnées

```bash
python -m onnx_export.metadata_embedder --onnx-model model.onnx --env-config config.json
```

### 3. Adaptation pour une plateforme spécifique

```bash
python -m onnx_export.platform_adapter --onnx-model model.onnx --platform pygame --output-dir exports/pygame
```

Plateformes disponibles : `pygame`, `web`, `unity`, `generic`

### 4. Optimisation d'un modèle ONNX

```bash
python -m onnx_export.optimizer --onnx-model model.onnx --optimizations quantize,fuse,compress --output-dir exports/optimized
```

### 5. Validation d'un modèle ONNX

```bash
python -m onnx_export.validator --onnx-model model.onnx --platforms pygame,web --performance-test
```

### 6. Vérification de compatibilité

```bash
python -m onnx_export.compatibility_checker --onnx-model model.onnx --platforms all --output-report compatibility.md
```

## Utilisation via l'API REST

Le système expose une API REST complète via FastAPI.

### Démarrer le serveur backend

```bash
cd backend
python app.py
```

L'API sera disponible à l'adresse : `http://localhost:8000`

### Endpoints principaux

#### 1. Informations sur le système

```bash
GET /api/v1/onnx
```

#### 2. Conversion d'un modèle

```bash
POST /api/v1/onnx/convert
Content-Type: multipart/form-data

model_file: fichier .zip
algorithm: DQN
include_metadata: true
```

#### 3. Export pour une plateforme

```bash
POST /api/v1/onnx/export/{platform}
Content-Type: application/x-www-form-urlencoded

onnx_model_path: /path/to/model.onnx
platform_config: {"batch_size": 1}
```

#### 4. Export pour toutes les plateformes

```bash
POST /api/v1/onnx/export-all
Content-Type: application/x-www-form-urlencoded

onnx_model_path: /path/to/model.onnx
platforms: ["pygame", "web", "unity", "generic"]
```

#### 5. Optimisation d'un modèle

```bash
POST /api/v1/onnx/optimize
Content-Type: application/x-www-form-urlencoded

onnx_model_path: /path/to/model.onnx
optimizations: ["quantize", "fuse"]
validate: true
```

#### 6. Validation d'un modèle

```bash
POST /api/v1/onnx/validate
Content-Type: application/x-www-form-urlencoded

onnx_model_path: /path/to/model.onnx
platforms: ["pygame", "web"]
performance_test: true
```

#### 7. Vérification de compatibilité

```bash
POST /api/v1/onnx/check-compatibility
Content-Type: application/x-www-form-urlencoded

onnx_model_path: /path/to/model.onnx
platforms: ["pygame", "web", "unity"]
```

#### 8. Gestion des exports

```bash
GET /api/v1/onnx/exports                    # Liste tous les exports
GET /api/v1/onnx/exports/{export_id}        # Détails d'un export
GET /api/v1/onnx/exports/{export_id}/download # Télécharger un export
DELETE /api/v1/onnx/exports/{export_id}     # Supprimer un export
```

## Plateformes supportées

### 1. Pygame classique

**Description** : Runtime ONNX Python avec interface simple pour l'exécution dans des environnements Pygame.

**Fichiers générés** :
- `model.onnx` : Modèle ONNX original
- `inference.py` : Script d'inférence Python
- `requirements.txt` : Dépendances Python
- `config.json` : Configuration de l'environnement

**Utilisation** :
```python
from inference import ONNXInference
inference = ONNXInference("model.onnx")
action = inference.predict(observation)
```

### 2. Web (TensorFlow.js)

**Description** : Conversion vers TensorFlow.js/ONNX.js pour exécution dans le navigateur.

**Fichiers générés** :
- `model.json` : Modèle TensorFlow.js
- `model.bin` : Poids binaires
- `index.html` : Exemple d'interface web
- `web_inference.js` : Bibliothèque JavaScript d'inférence

**Prérequis** :
```bash
pip install onnx2tf tensorflowjs
```

### 3. Unity (Barracuda)

**Description** : Export direct ONNX compatible avec Barracuda (moteur d'inférence ML d'Unity).

**Fichiers générés** :
- `model.onnx` : Modèle ONNX compatible Barracuda
- `model.bytes` : Modèle au format bytes pour Unity
- `Inference.cs` : Script C# pour l'inférence
- `README_UNITY.md` : Instructions d'intégration Unity

### 4. Interface générique

**Description** : Interface REST pour l'inférence distante.

**Fichiers générés** :
- `model.onnx` : Modèle ONNX
- `api_server.py` : Serveur FastAPI d'inférence
- `client_example.py` : Exemple de client Python
- `docker-compose.yml` : Configuration Docker

## Optimisations disponibles

### 1. Quantisation

Conversion des poids FP32 vers FP16 ou INT8 pour réduire la taille du modèle et améliorer les performances.

```python
from onnx_export.optimizer import ONNXOptimizer
optimizer = ONNXOptimizer("model.onnx")
optimizer.quantize(fp16=True, int8=False)
```

### 2. Fusion d'opérations

Fusion d'opérations ONNX adjacentes pour réduire le nombre de nœuds dans le graphe.

```python
optimizer.fuse_operations()
```

### 3. Simplification du graphe

Suppression des nœuds inutiles et simplification de la structure du graphe.

```python
optimizer.simplify_graph()
```

### 4. Compression

Compression GZIP du modèle ONNX pour réduire la taille du fichier.

```python
optimizer.compress_gzip()
```

### 5. Validation d'exactitude

Vérification que les optimisations n'ont pas altéré la précision du modèle.

```python
accuracy_loss = optimizer.validate_accuracy()
print(f"Perte de précision : {accuracy_loss:.4f}%")
```

## Validation et compatibilité

### Validation complète

Le validateur exécute une série de tests :

1. **Validation syntaxique** : Vérifie que le modèle ONNX est valide
2. **Compatibilité runtime** : Teste l'inférence avec ONNX Runtime
3. **Exactitude des prédictions** : Compare avec le modèle SB3 original
4. **Performances** : Mesure le temps d'inférence et l'utilisation mémoire
5. **Métadonnées** : Vérifie la présence et la validité des métadonnées

### Vérification de compatibilité

Le vérificateur de compatibilité évalue la compatibilité avec chaque plateforme :

```python
from onnx_export.compatibility_checker import CompatibilityChecker
checker = CompatibilityChecker("model.onnx")
report = checker.check_all_platforms()
checker.save_compatibility_report("compatibility.md", report)
```

## Exemples pratiques

### Exemple 1 : Conversion complète d'un modèle DQN

```python
from onnx_export.onnx_converter import convert_sb3_model

# Conversion du modèle
results = convert_sb3_model(
    model_path="logs/pacman_DQN_20260104.zip",
    output_dir="exports/dqn_model",
    algorithm="DQN",
    include_metadata=True,
    test_conversion=True
)

print(f"Modèle converti : {results['onnx_model_path']}")
print(f"Taille originale : {results['original_size_mb']} MB")
print(f"Taille ONNX : {results['onnx_size_mb']} MB")
```

### Exemple 2 : Export multi-plateforme

```python
from onnx_export.platform_adapter import PlatformAdapter

adapter = PlatformAdapter("exports/dqn_model/model.onnx")

# Export pour Pygame
pygame_results = adapter.adapt_for_pygame("exports/pygame")

# Export pour Web
web_results = adapter.adapt_for_web("exports/web")

# Export pour Unity
unity_results = adapter.adapt_for_unity("exports/unity")

print("Export multi-plateforme terminé")
```

### Exemple 3 : Optimisation et validation

```python
from onnx_export.optimizer import ONNXOptimizer
from onnx_export.validator import ONNXValidator

# Optimisation
optimizer = ONNXOptimizer("model.onnx")
optimized_path = optimizer.apply_all_optimizations(
    output_dir="exports/optimized",
    optimizations=["quantize", "fuse", "simplify"],
    validate=True
)

# Validation
validator = ONNXValidator(optimized_path)
validation_results = validator.run_comprehensive_validation(
    platforms=["pygame", "web"],
    performance_test=True
)

if validation_results["overall_status"] == "PASS":
    print("Modèle validé avec succès")
else:
    print(f"Problèmes détectés : {validation_results['issues']}")
```

## Dépannage

### Problèmes courants

#### 1. Erreur "ModuleNotFoundError: No module named 'onnx'"

**Solution** : Installer les dépendances ONNX
```bash
pip install onnx onnxruntime
```

#### 2. Erreur "Unsupported ONNX opset version"

**Solution** : Spécifier une version d'opset compatible
```python
from onnx_export.onnx_converter import ONNXConverter
converter = ONNXConverter(opset_version=13)
```

#### 3. Erreur "Model too large for target platform"

**Solution** : Appliquer la quantisation
```python
optimizer.quantize(fp16=True)
```

#### 4. Erreur "Incompatible with Barracuda"

**Solution** : Vérifier les opérations ONNX supportées par Barracuda
```python
checker.check_barracuda_compatibility()
```

#### 5. Performances médiocres sur Web

**Solution** :
- Appliquer la quantisation INT8
- Réduire la taille du modèle
- Utiliser WebGL acceleration

### Journalisation et débogage

Activez la journalisation détaillée :

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Référence API

### Classe ONNXConverter

```python
class ONNXConverter:
    def __init__(self, opset_version=13):
        """Initialise le convertisseur ONNX."""
    
    def convert_sb3_model(self, model_path, output_dir, algorithm="auto", 
                         include_metadata=True, test_conversion=True):
        """Convertit un modèle SB3 vers ONNX."""
    
    def extract_policy_network(self, model, algorithm):
        """Extrait le réseau de neurones de la politique."""
```

### Classe MetadataEmbedder

```python
class MetadataEmbedder:
    def __init__(self, onnx_model_path):
        """Initialise l'embedder de métadonnées."""
    
    def embed_metadata(self, metadata_dict):
        """Incorpore des métadonnées dans le modèle ONNX."""
    
    def extract_metadata(self):
        """Extrait les métadonnées du modèle ONNX."""
```

### Classe PlatformAdapter

```python
class PlatformAdapter:
    def __init__(self, onnx_model_path):
        """Initialise l'adaptateur de plateforme."""
    
    def adapt_for_pygame(self, output_dir):
        """Adapte le modèle pour Pygame."""
    
    def adapt_for_web(self, output_dir):
        """Adapte le modèle pour le Web (TensorFlow.js)."""
    
    def adapt_for_unity(self, output_dir):
        """Adapte le modèle pour Unity (Barracuda)."""
    
    def adapt_for_generic(self, output_dir):
        """Adapte le modèle pour une interface générique."""
```

### Classe ONNXOptimizer

```python
class ONNXOptimizer:
    def __init__(self, onnx_model_path):
        """Initialise l'optimiseur ONNX."""
    
    def quantize(self, fp16=True, int8=False):
        """Quantise le modèle."""
    
    def fuse_operations(self):
        """Fusionne les opérations."""
    
    def simplify_graph(self):
        """Simplifie le graphe ONNX."""
    
    def compress_gzip(self):
        """Compresse le modèle avec GZIP."""
```

### Classe ONNXValidator

```python
class ONNXValidator:
    def __init__(self, onnx_model_path):
        """Initialise le validateur ONNX."""
    
    def validate_syntax(self):
        """Valide la syntaxe ONNX."""
    
    def validate_runtime(self):
        """Valide l'exécution avec ONNX Runtime."""
    
    def validate_predictions(self, original_model, test_samples=100):
        """Valide l'exactitude des prédictions."""
    
    def validate_performance(self, batch_sizes=[1, 8, 32]):
        """Valide les performances."""
```

### Classe CompatibilityChecker

```python
class CompatibilityChecker:
    def __init__(self, onnx_model_path):
        """Initialise le vérificateur de compatibilité."""
    
    def check_pygame_compatibility(self):
        """Vérifie la compatibilité avec Pygame."""
    
    def check_web_compatibility(self):
        """Vérifie la compatibilité avec le Web."""
    
    def check_unity_compatibility(self):
        """Vérifie la compatibilité avec Unity."""
    
    def check_all_platforms(self, platforms=None):
        """Vérifie la compatibilité avec toutes les plateformes."""
```

## Conclusion

Le système d'export ONNX universel fournit une solution complète pour convertir, optim