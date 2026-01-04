"""
Service d'export ONNX pour le backend FastAPI.

Ce service fournit des fonctionnalités d'export ONNX via l'API REST.
"""

import os
import json
import tempfile
import shutil
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

# Import des modules d'export ONNX
try:
    from onnx_export.onnx_converter import ONNXConverter, convert_sb3_model
    from onnx_export.metadata_embedder import MetadataEmbedder
    from onnx_export.platform_adapter import PlatformAdapter
    from onnx_export.optimizer import ONNXOptimizer
    from onnx_export.validator import ONNXValidator
    from onnx_export.compatibility_checker import CompatibilityChecker
    ONNX_EXPORT_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Modules d'export ONNX non disponibles: {e}")
    ONNX_EXPORT_AVAILABLE = False


class ONNXExportService:
    """
    Service d'export ONNX pour l'API backend.
    
    Gère:
    - Conversion de modèles Stable-Baselines3 vers ONNX
    - Export multi-plateforme
    - Validation et optimisation
    - Gestion des fichiers exportés
    """
    
    def __init__(self, base_export_dir: str = "./onnx_exports"):
        """
        Initialise le service d'export.
        
        Args:
            base_export_dir: Répertoire de base pour les exports
        """
        self.base_export_dir = Path(base_export_dir)
        self.base_export_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        if not ONNX_EXPORT_AVAILABLE:
            self.logger.warning("Modules d'export ONNX non disponibles. Certaines fonctionnalités seront limitées.")
    
    def convert_model(
        self,
        model_path: str,
        algorithm: str = "auto",
        output_name: Optional[str] = None,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Convertit un modèle Stable-Baselines3 en ONNX.
        
        Args:
            model_path: Chemin vers le modèle .zip
            algorithm: Algorithme RL (auto, DQN, PPO, etc.)
            output_name: Nom personnalisé pour l'export
            include_metadata: Inclure les métadonnées
            
        Returns:
            Dictionnaire avec résultats de conversion
        """
        if not ONNX_EXPORT_AVAILABLE:
            return {
                "success": False,
                "error": "Modules d'export ONNX non disponibles",
                "required_packages": ["onnx", "onnxruntime", "onnxconverter-common", "onnxsim"]
            }
        
        try:
            # Créer un répertoire d'export pour ce modèle
            model_name = Path(model_path).stem
            export_dir = self.base_export_dir / model_name
            export_dir.mkdir(exist_ok=True)
            
            # Convertir le modèle
            results = convert_sb3_model(
                model_path=str(model_path),
                output_dir=str(export_dir),
                algorithm=algorithm,
                include_metadata=include_metadata,
                test_conversion=True
            )
            
            # Ajouter des informations supplémentaires
            results["success"] = True
            results["export_dir"] = str(export_dir)
            results["model_name"] = model_name
            
            self.logger.info(f"Modèle converti avec succès: {model_path}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la conversion: {e}")
            return {
                "success": False,
                "error": str(e),
                "model_path": model_path
            }
    
    def export_for_platform(
        self,
        onnx_model_path: str,
        platform: str,
        platform_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Exporte un modèle ONNX pour une plateforme spécifique.
        
        Args:
            onnx_model_path: Chemin vers le modèle ONNX
            platform: Plateforme cible (pygame, web, unity, generic)
            platform_config: Configuration spécifique à la plateforme
            
        Returns:
            Dictionnaire avec résultats d'export
        """
        if not ONNX_EXPORT_AVAILABLE:
            return {
                "success": False,
                "error": "Modules d'export ONNX non disponibles"
            }
        
        try:
            # Créer un adaptateur pour la plateforme
            adapter = PlatformAdapter(onnx_model_path)
            
            # Créer un répertoire d'export pour cette plateforme
            model_name = Path(onnx_model_path).stem
            platform_dir = self.base_export_dir / model_name / platform
            platform_dir.mkdir(parents=True, exist_ok=True)
            
            # Adapter pour la plateforme
            if platform == "pygame":
                results = adapter.adapt_for_pygame(str(platform_dir))
            elif platform == "web":
                results = adapter.adapt_for_web(str(platform_dir))
            elif platform == "unity":
                results = adapter.adapt_for_unity(str(platform_dir))
            elif platform == "generic":
                results = adapter.adapt_for_generic(str(platform_dir))
            else:
                return {
                    "success": False,
                    "error": f"Plateforme non supportée: {platform}",
                    "supported_platforms": ["pygame", "web", "unity", "generic"]
                }
            
            results["success"] = True
            results["platform_dir"] = str(platform_dir)
            
            self.logger.info(f"Export pour {platform} réussi: {onnx_model_path}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'export pour {platform}: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": platform
            }
    
    def export_for_all_platforms(
        self,
        onnx_model_path: str,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Exporte un modèle ONNX pour toutes les plateformes supportées.
        
        Args:
            onnx_model_path: Chemin vers le modèle ONNX
            platforms: Liste des plateformes (défaut: toutes)
            
        Returns:
            Dictionnaire avec résultats par plateforme
        """
        if not ONNX_EXPORT_AVAILABLE:
            return {
                "success": False,
                "error": "Modules d'export ONNX non disponibles"
            }
        
        if platforms is None:
            platforms = ["pygame", "web", "unity", "generic"]
        
        try:
            adapter = PlatformAdapter(onnx_model_path)
            
            # Créer un répertoire d'export
            model_name = Path(onnx_model_path).stem
            all_platforms_dir = self.base_export_dir / model_name / "all_platforms"
            all_platforms_dir.mkdir(parents=True, exist_ok=True)
            
            # Exporter pour toutes les plateformes
            results = adapter.export_all_platforms(str(all_platforms_dir), platforms)
            
            # Générer un rapport
            report_path = all_platforms_dir / "export_report.json"
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            return {
                "success": True,
                "results": results,
                "export_dir": str(all_platforms_dir),
                "report_path": str(report_path)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'export multi-plateforme: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def optimize_model(
        self,
        onnx_model_path: str,
        optimizations: Optional[List[str]] = None,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Optimise un modèle ONNX.
        
        Args:
            onnx_model_path: Chemin vers le modèle ONNX
            optimizations: Liste des optimisations à appliquer
            validate: Valider l'exactitude après optimisation
            
        Returns:
            Dictionnaire avec résultats d'optimisation
        """
        if not ONNX_EXPORT_AVAILABLE:
            return {
                "success": False,
                "error": "Modules d'export ONNX non disponibles"
            }
        
        try:
            optimizer = ONNXOptimizer(onnx_model_path)
            
            # Créer un répertoire pour les optimisations
            model_name = Path(onnx_model_path).stem
            optim_dir = self.base_export_dir / model_name / "optimized"
            optim_dir.mkdir(parents=True, exist_ok=True)
            
            # Appliquer les optimisations
            results = optimizer.apply_all_optimizations(
                str(optim_dir),
                optimizations,
                validate
            )
            
            return {
                "success": True,
                "results": results,
                "optimization_dir": str(optim_dir)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_model(
        self,
        onnx_model_path: str,
        platforms: Optional[List[str]] = None,
        performance_test: bool = True
    ) -> Dict[str, Any]:
        """
        Valide un modèle ONNX.
        
        Args:
            onnx_model_path: Chemin vers le modèle ONNX
            platforms: Plateformes à valider
            performance_test: Inclure les tests de performance
            
        Returns:
            Dictionnaire avec résultats de validation
        """
        if not ONNX_EXPORT_AVAILABLE:
            return {
                "success": False,
                "error": "Modules d'export ONNX non disponibles"
            }
        
        try:
            validator = ONNXValidator(onnx_model_path)
            
            # Créer un répertoire pour les rapports
            model_name = Path(onnx_model_path).stem
            validation_dir = self.base_export_dir / model_name / "validation"
            validation_dir.mkdir(parents=True, exist_ok=True)
            
            # Exécuter la validation
            results = validator.run_comprehensive_validation(platforms, performance_test)
            
            # Sauvegarder le rapport
            report_path = validation_dir / "validation_report.txt"
            validator.save_validation_report(str(report_path), results)
            
            return {
                "success": True,
                "results": results,
                "validation_dir": str(validation_dir),
                "report_path": str(report_path)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la validation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_compatibility(
        self,
        onnx_model_path: str,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Vérifie la compatibilité d'un modèle ONNX avec différentes plateformes.
        
        Args:
            onnx_model_path: Chemin vers le modèle ONNX
            platforms: Plateformes à vérifier
            
        Returns:
            Dictionnaire avec résultats de compatibilité
        """
        if not ONNX_EXPORT_AVAILABLE:
            return {
                "success": False,
                "error": "Modules d'export ONNX non disponibles"
            }
        
        try:
            checker = CompatibilityChecker(onnx_model_path)
            
            # Créer un répertoire pour les rapports
            model_name = Path(onnx_model_path).stem
            compat_dir = self.base_export_dir / model_name / "compatibility"
            compat_dir.mkdir(parents=True, exist_ok=True)
            
            # Vérifier la compatibilité
            report_path = compat_dir / "compatibility_report.md"
            checker.save_compatibility_report(str(report_path), platforms)
            
            # Lire les résultats
            json_path = report_path.with_suffix('.json')
            with open(json_path, 'r') as f:
                results = json.load(f)
            
            return {
                "success": True,
                "results": results,
                "compatibility_dir": str(compat_dir),
                "report_path": str(report_path)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de compatibilité: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_export_status(self, export_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'un export.
        
        Args:
            export_id: Identifiant de l'export
            
        Returns:
            Dictionnaire avec statut de l'export
        """
        export_dir = self.base_export_dir / export_id
        
        if not export_dir.exists():
            return {
                "success": False,
                "error": f"Export {export_id} non trouvé"
            }
        
        # Lister les fichiers dans le répertoire d'export
        files = []
        for file_path in export_dir.rglob("*"):
            if file_path.is_file():
                files.append({
                    "path": str(file_path.relative_to(export_dir)),
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime
                })
        
        return {
            "success": True,
            "export_id": export_id,
            "export_dir": str(export_dir),
            "files": files,
            "total_size": sum(f["size"] for f in files)
        }
    
    def list_exports(self) -> Dict[str, Any]:
        """
        Liste tous les exports disponibles.
        
        Returns:
            Dictionnaire avec liste des exports
        """
        exports = []
        
        for export_dir in self.base_export_dir.iterdir():
            if export_dir.is_dir():
                # Compter les fichiers
                file_count = sum(1 for _ in export_dir.rglob("*") if _.is_file())
                
                exports.append({
                    "id": export_dir.name,
                    "path": str(export_dir),
                    "file_count": file_count,
                    "size": sum(f.stat().st_size for f in export_dir.rglob("*") if f.is_file())
                })
        
        return {
            "success": True,
            "exports": exports,
            "total_exports": len(exports),
            "base_export_dir": str(self.base_export_dir)
        }


# Instance globale du service
onnx_export_service = ONNXExportService()