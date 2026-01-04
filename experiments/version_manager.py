#!/usr/bin/env python3
"""
Gestionnaire de versions pour le système d'archivage intelligent.

Fonctionnalités :
- Numérotation automatique des runs
- Tags et catégories (best, experimental, baseline)
- Recherche et filtrage par métriques
- Gestion des métadonnées de version
- Migration depuis l'ancien système
"""

import os
import json
import yaml
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict, field
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class VersionMetadata:
    """Métadonnées de version pour une session."""
    session_id: str
    session_number: int
    timestamp: str
    model_type: str
    agent_type: str
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    archive_path: Optional[str] = None
    parent_version: Optional[str] = None
    child_versions: List[str] = field(default_factory=list)
    notes: str = ""

@dataclass
class VersionFilter:
    """Filtre pour la recherche de versions."""
    min_session_number: Optional[int] = None
    max_session_number: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    min_metric_value: Optional[Dict[str, float]] = None
    max_metric_value: Optional[Dict[str, float]] = None
    model_type: Optional[str] = None
    agent_type: Optional[str] = None
    search_text: Optional[str] = None

class VersionManager:
    """
    Gestionnaire de versions pour le système d'archivage intelligent.
    
    Gère la numérotation automatique, les tags, les catégories et la recherche
    de sessions archivées.
    """
    
    def __init__(self, archive_dir: str = "experiments/archives"):
        self.archive_dir = archive_dir
        self.metadata_dir = os.path.join(archive_dir, "metadata")
        self._ensure_directories()
        self._load_version_registry()
    
    def _ensure_directories(self) -> None:
        """Crée les répertoires nécessaires."""
        os.makedirs(self.archive_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs("experiments/tags", exist_ok=True)
        os.makedirs("experiments/categories", exist_ok=True)
    
    def _load_version_registry(self) -> None:
        """Charge ou crée le registre des versions."""
        registry_path = os.path.join(self.metadata_dir, "version_registry.json")
        
        if os.path.exists(registry_path):
            try:
                with open(registry_path, 'r') as f:
                    self.registry = json.load(f)
                logger.info(f"Registre des versions chargé: {len(self.registry.get('versions', {}))} versions")
            except Exception as e:
                logger.warning(f"Erreur lors du chargement du registre: {e}")
                self.registry = self._create_new_registry()
        else:
            self.registry = self._create_new_registry()
    
    def _create_new_registry(self) -> Dict[str, Any]:
        """Crée un nouveau registre des versions."""
        return {
            'next_session_number': 1,
            'versions': {},
            'tags': {},
            'categories': {},
            'statistics': {
                'total_sessions': 0,
                'by_model_type': {},
                'by_agent_type': {},
                'by_tag': {},
                'by_category': {}
            }
        }
    
    def _save_registry(self) -> None:
        """Sauvegarde le registre des versions."""
        registry_path = os.path.join(self.metadata_dir, "version_registry.json")
        
        try:
            with open(registry_path, 'w') as f:
                json.dump(self.registry, f, indent=2)
            logger.debug("Registre des versions sauvegardé")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du registre: {e}")
    
    def register_new_version(self, archive_path: str, metadata: Dict[str, Any]) -> Optional[VersionMetadata]:
        """
        Enregistre une nouvelle version dans le système.
        
        Args:
            archive_path: Chemin vers l'archive
            metadata: Métadonnées de la session
            
        Returns:
            Métadonnées de version enregistrées ou None en cas d'erreur
        """
        try:
            # Générer un numéro de session
            session_number = self.registry['next_session_number']
            self.registry['next_session_number'] += 1
            
            # Créer l'ID de session
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"session_{session_number:03d}_{timestamp}"
            
            # Extraire les informations de base
            model_type = metadata.get('model_type', 'unknown')
            agent_type = metadata.get('agent_type', 'unknown')
            
            # Extraire les métriques
            metrics = metadata.get('metrics', {})
            
            # Extraire les paramètres
            parameters = metadata.get('parameters', {})
            
            # Déterminer les tags automatiques
            tags = self._generate_automatic_tags(metrics, parameters)
            
            # Déterminer les catégories automatiques
            categories = self._generate_automatic_categories(metrics, parameters)
            
            # Créer l'objet VersionMetadata
            version_metadata = VersionMetadata(
                session_id=session_id,
                session_number=session_number,
                timestamp=timestamp,
                model_type=model_type,
                agent_type=agent_type,
                tags=tags,
                categories=categories,
                metrics=metrics,
                parameters=parameters,
                archive_path=archive_path,
                notes=metadata.get('notes', '')
            )
            
            # Mettre à jour le registre
            self._update_registry_with_version(version_metadata)
            
            # Sauvegarder les métadonnées de version
            self._save_version_metadata(version_metadata)
            
            # Mettre à jour les index de tags et catégories
            self._update_tag_index(version_metadata)
            self._update_category_index(version_metadata)
            
            # Sauvegarder le registre
            self._save_registry()
            
            logger.info(f"Nouvelle version enregistrée: {session_id} (#{session_number})")
            logger.info(f"Tags: {tags}")
            logger.info(f"Catégories: {categories}")
            
            return version_metadata
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de la version: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _generate_automatic_tags(self, metrics: Dict[str, Any], parameters: Dict[str, Any]) -> List[str]:
        """Génère des tags automatiques basés sur les métriques et paramètres."""
        tags = []
        
        # Tags basés sur les métriques
        win_rate = metrics.get('win_rate', 0)
        if win_rate > 0.8:
            tags.append('high_performance')
        elif win_rate > 0.6:
            tags.append('good_performance')
        elif win_rate < 0.3:
            tags.append('low_performance')
        
        # Tags basés sur les paramètres
        learning_rate = parameters.get('learning_rate', 0)
        if learning_rate > 0.01:
            tags.append('high_lr')
        elif learning_rate < 0.0001:
            tags.append('low_lr')
        
        gamma = parameters.get('gamma', 0)
        if gamma > 0.99:
            tags.append('long_term')
        elif gamma < 0.9:
            tags.append('short_term')
        
        # Tags basés sur la stabilité
        if 'converged' in metrics.get('observations', '').lower():
            tags.append('converged')
        
        if 'overfitting' in metrics.get('observations', '').lower():
            tags.append('overfitting')
        
        return list(set(tags))  # Supprimer les doublons
    
    def _generate_automatic_categories(self, metrics: Dict[str, Any], parameters: Dict[str, Any]) -> List[str]:
        """Génère des catégories automatiques basées sur les métriques et paramètres."""
        categories = ['all']  # Toujours inclure 'all'
        
        # Catégorie basée sur le type de modèle
        model_type = parameters.get('model_type', '').lower()
        if model_type:
            categories.append(f"model_{model_type}")
        
        # Catégorie basée sur les performances
        win_rate = metrics.get('win_rate', 0)
        if win_rate > 0.7:
            categories.append('best')
        elif win_rate < 0.4:
            categories.append('experimental')
        else:
            categories.append('baseline')
        
        # Catégorie basée sur la taille du modèle
        model_size = metrics.get('model_size_mb', 0)
        if model_size > 100:
            categories.append('large_model')
        elif model_size < 10:
            categories.append('small_model')
        
        return list(set(categories))
    
    def _update_registry_with_version(self, version: VersionMetadata) -> None:
        """Met à jour le registre avec une nouvelle version."""
        # Ajouter la version au registre
        self.registry['versions'][version.session_id] = asdict(version)
        
        # Mettre à jour les statistiques
        stats = self.registry['statistics']
        stats['total_sessions'] += 1
        
        # Statistiques par type de modèle
        model_type = version.model_type
        stats['by_model_type'][model_type] = stats['by_model_type'].get(model_type, 0) + 1
        
        # Statistiques par type d'agent
        agent_type = version.agent_type
        stats['by_agent_type'][agent_type] = stats['by_agent_type'].get(agent_type, 0) + 1
        
        # Statistiques par tag
        for tag in version.tags:
            stats['by_tag'][tag] = stats['by_tag'].get(tag, 0) + 1
        
        # Statistiques par catégorie
        for category in version.categories:
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
    
    def _save_version_metadata(self, version: VersionMetadata) -> None:
        """Sauvegarde les métadonnées de version dans un fichier séparé."""
        version_path = os.path.join(self.metadata_dir, f"{version.session_id}.json")
        
        try:
            with open(version_path, 'w') as f:
                json.dump(asdict(version), f, indent=2)
            logger.debug(f"Métadonnées de version sauvegardées: {version_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des métadonnées de version: {e}")
    
    def _update_tag_index(self, version: VersionMetadata) -> None:
        """Met à jour l'index des tags."""
        for tag in version.tags:
            tag_file = os.path.join("experiments/tags", f"{tag}.json")
            
            # Charger ou créer l'index du tag
            if os.path.exists(tag_file):
                with open(tag_file, 'r') as f:
                    tag_index = json.load(f)
            else:
                tag_index = {'sessions': [], 'description': '', 'created': datetime.now().isoformat()}
            
            # Ajouter la session à l'index
            if version.session_id not in tag_index['sessions']:
                tag_index['sessions'].append(version.session_id)
                
                # Sauvegarder l'index
                with open(tag_file, 'w') as f:
                    json.dump(tag_index, f, indent=2)
    
    def _update_category_index(self, version: VersionMetadata) -> None:
        """Met à jour l'index des catégories."""
        for category in version.categories:
            category_file = os.path.join("experiments/categories", f"{category}.json")
            
            # Charger ou créer l'index de la catégorie
            if os.path.exists(category_file):
                with open(category_file, 'r') as f:
                    category_index = json.load(f)
            else:
                category_index = {'sessions': [], 'description': '', 'created': datetime.now().isoformat()}
            
            # Ajouter la session à l'index
            if version.session_id not in category_index['sessions']:
                category_index['sessions'].append(version.session_id)
                
                # Sauvegarder l'index
                with open(category_file, 'w') as f:
                    json.dump(category_index, f, indent=2)
    
    def search_versions(self, filter_criteria: VersionFilter) -> List[VersionMetadata]:
        """
        Recherche des versions selon des critères de filtrage.
        
        Args:
            filter_criteria: Critères de filtrage
            
        Returns:
            Liste des versions correspondantes
        """
        matching_versions = []
        
        for version_id, version_data in self.registry['versions'].items():
            version = VersionMetadata(**version_data)
            
            # Appliquer les filtres
            if not self._matches_filter(version, filter_criteria):
                continue
            
            matching_versions.append(version)
        
        # Trier par numéro de session (décroissant par défaut)
        matching_versions.sort(key=lambda v: v.session_number, reverse=True)
        
        logger.info(f"Recherche trouvée: {len(matching_versions)} versions correspondantes")
        return matching_versions
    
    def _matches_filter(self, version: VersionMetadata, filter_criteria: VersionFilter) -> bool:
        """Vérifie si une version correspond aux critères de filtrage."""
        # Filtre par numéro de session
        if filter_criteria.min_session_number is not None:
            if version.session_number < filter_criteria.min_session_number:
                return False
        
        if filter_criteria.max_session_number is not None:
            if version.session_number > filter_criteria.max_session_number:
                return False
        
        # Filtre par date
        if filter_criteria.start_date is not None:
            if version.timestamp < filter_criteria.start_date:
                return False
        
        if filter_criteria.end_date is not None:
            if version.timestamp > filter_criteria.end_date:
                return False
        
        # Filtre par tags
        if filter_criteria.tags is not None:
            if not any(tag in version.tags for tag in filter_criteria.tags):
                return False
        
        # Filtre par catégories
        if filter_criteria.categories is not None:
            if not any(category in version.categories for category in filter_criteria.categories):
                return False
        
        # Filtre par métriques
        if filter_criteria.min_metric_value is not None:
            for metric_name, min_value in filter_criteria.min_metric_value.items():
                if metric_name in version.metrics:
                    if version.metrics[metric_name] < min_value:
                        return False
        
        if filter_criteria.max_metric_value is not None:
            for metric_name, max_value in filter_criteria.max_metric_value.items():
                if metric_name in version.metrics:
                    if version.metrics[metric_name] > max_value:
                        return False
        
        # Filtre par type de modèle
        if filter_criteria.model_type is not None:
            if version.model_type != filter_criteria.model_type:
                return False
        
        # Filtre par type d'agent
        if filter_criteria.agent_type is not None:
            if version.agent_type != filter_criteria.agent_type:
                return False
        
        # Filtre par texte de recherche
        if filter_criteria.search_text is not None:
            search_text = filter_criteria.search_text.lower()
            
            # Rechercher dans différents champs
            search_fields = [
                version.session_id.lower(),
                version.notes.lower(),
                str(version.parameters).lower(),
                ' '.join(version.tags).lower(),
                ' '.join(version.categories).lower()
            ]
            
            if not any(search_text in field for field in search_fields):
                return False
        
        return True
    
    def get_version(self, session_id: str) -> Optional[VersionMetadata]:
        """Récupère une version par son ID."""
        version_data = self.registry['versions'].get(session_id)
        
        if version_data:
            return VersionMetadata(**version_data)
        else:
            # Essayer de charger depuis le fichier de métadonnées
            version_path = os.path.join(self.metadata_dir, f"{session_id}.json")
            
            if os.path.exists(version_path):
                try:
                    with open(version_path, 'r') as f:
                        version_data = json.load(f)
                    return VersionMetadata(**version_data)
                except Exception as e:
                    logger.error(f"Erreur lors du chargement de la version {session_id}: {e}")
        
        return None
    
    def add_tag(self, session_id: str, tag: str) -> bool:
        """Ajoute un tag à une version."""
        version = self.get_version(session_id)
        
        if not version:
            logger.error(f"Version non trouvée: {session_id}")
            return False
        
        if tag not in version.tags:
            version.tags.append(tag)
            
            # Mettre à jour le registre
            self.registry['versions'][session_id]['tags'] = version.tags
            
            # Mettre à jour l'index des tags
            self._update_tag_index(version)
            
            # Mettre à jour les statistiques
            self.registry['statistics']['by_tag'][tag] = self.registry['statistics']['by_tag'].get(tag, 0) + 1
            
            # Sauvegarder les métadonnées
            self._save_version_metadata(version)
            self._save_registry()
            
            logger.info(f"Tag '{tag}' ajouté à {session_id}")
            return True
        
        return False  # Tag déjà présent
    
    def remove_tag(self, session_id: str, tag: str) -> bool:
        """Supprime un tag d'une version."""
        version = self.get_version(session_id)
        
        if not version:
            logger.error(f"Version non trouvée: {session_id}")
            return False
        
        if tag in version.tags:
            version.tags.remove(tag)
            
            # Mettre à jour le registre
            self.registry['versions'][session_id]['tags'] = version.tags
            
            # Mettre à jour les statistiques
            if tag in self.registry['statistics']['by_tag']:
                self.registry['statistics']['by_tag'][tag] -= 1
                if self.registry['statistics']['by_tag'][tag] <= 0:
                    del self.registry['statistics']['by_tag'][tag]
            
            # Sauvegarder les métadonnées
            self._save_version_metadata(version)
            self._save_registry()
            
            logger.info(f"Tag '{tag}' supprimé de {session_id}")
            return True
        
        return False  # Tag non présent
    
    def add_category(self, session_id: str, category: str) -> bool:
        """Ajoute une catégorie à une version."""
        version = self.get_version(session_id)
        
        if not version:
            logger.error(f"Version non trouvée: {session_id}")
            return False
        
        if category not in version.categories:
            version.categories.append(category)
            
            # Mettre à jour le registre
            self.registry['versions'][session_id]['categories'] = version.categories
            
            # Mettre à jour l'index des catégories
            self._update_category_index(version)
            
            # Mettre à jour les statistiques
            self.registry['statistics']['by_category'][category] = self.registry['statistics']['by_category'].get(category, 0) + 1
            
            # Sauvegarder les métadonnées
            self._save_version_metadata(version)
            self._save_registry()
            
            logger.info(f"Catégorie '{category}' ajoutée à {session_id}")
            return True
        
        return False  # Catégorie déjà présente
    
    def remove_category(self, session_id: str, category: str) -> bool:
        """Supprime une catégorie d'une version."""
        version = self.get_version(session_id)
        
        if not version:
            logger.error(f"Version non trouvée: {session_id}")
            return False
        
        if category in version.categories:
            version.categories.remove(category)
            
            # Mettre à jour le registre
            self.registry['versions'][session_id]['categories'] = version.categories
            
            # Mettre à jour les statistiques
            if category in self.registry['statistics']['by_category']:
                self.registry['statistics']['by_category'][category] -= 1
                if self.registry['statistics']['by_category'][category] <= 0:
                    del self.registry['statistics']['by_category'][category]
            
            # Sauvegarder les métadonnées
            self._save_version_metadata(version)
            self._save_registry()
            
            logger.info(f"Catégorie '{category}' supprimée de {session_id}")
            return True
        
        return False  # Catégorie non présente
    
    def update_notes(self, session_id: str, notes: str) -> bool:
        """Met à jour les notes d'une version."""
        version = self.get_version(session_id)
        
        if not version:
            logger.error(f"Version non trouvée: {session_id}")
            return False
        
        version.notes = notes
        
        # Mettre à jour le registre
        self.registry['versions'][session_id]['notes'] = notes
        
        # Sauvegarder les métadonnées
        self._save_version_metadata(version)
        self._save_registry()
        
        logger.info(f"Notes mises à jour pour {session_id}")
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques du système de versions."""
        return self.registry['statistics']
    
    def get_best_versions(self, metric: str = 'win_rate', limit: int = 5) -> List[VersionMetadata]:
        """
        Récupère les meilleures versions selon une métrique.
        
        Args:
            metric: Métrique à utiliser pour le classement
            limit: Nombre maximum de versions à retourner
            
        Returns:
            Liste des meilleures versions
        """
        versions_with_metric = []
        
        for version_id, version_data in self.registry['versions'].items():
            version = VersionMetadata(**version_data)
            
            if metric in version.metrics:
                metric_value = version.metrics[metric]
                if isinstance(metric_value, (int, float)):
                    versions_with_metric.append((version, metric_value))
        
        # Trier par métrique (décroissant pour win_rate, croissant pour loss)
        reverse = metric not in ['loss', 'error', 'cost']
        versions_with_metric.sort(key=lambda x: x[1], reverse=reverse)
        
        # Retourner les meilleures versions
        best_versions = [v[0] for v in versions_with_metric[:limit]]
        
        logger.info(f"Meilleures versions par {metric}: {len(best_versions)} trouvées")
        return best_versions
    
    def export_versions(self, output_format: str = 'json', filter_criteria: Optional[VersionFilter] = None) -> str:
        """
        Exporte les versions dans un format spécifique.
        
        Args:
            output_format: Format d'export ('json', 'csv', 'markdown')
            filter_criteria: Critères de filtrage optionnels
            
        Returns:
            Chemin vers le fichier exporté
        """
        # Récupérer les versions
        if filter_criteria:
            versions = self.search_versions(filter_criteria)
        else:
            versions = [VersionMetadata(**v) for v in self.registry['versions'].values()]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format == 'json':
            filename = f"versions_export_{timestamp}.json"
            filepath = os.path.join(self.archive_dir, filename)
            
            export_data = {
                'export_timestamp': timestamp,
                'version_count': len(versions),
                'versions': [asdict(v) for v in versions]
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        elif output_format == 'csv':
            filename = f"versions_export_{timestamp}.csv"
            filepath = os.path.join(self.archive_dir, filename)
            
            import csv
            
            # Définir les colonnes
            fieldnames = ['session_id', 'session_number', 'timestamp', 'model_type', 'agent_type',
                         'win_rate', 'total_episodes', 'tags', 'categories', 'notes']
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for version in versions:
                    row = {
                        'session_id': version.session_id,
                        'session_number': version.session_number,
                        'timestamp': version.timestamp,
                        'model_type': version.model_type,
                        'agent_type': version.agent_type,
                        'win_rate': version.metrics.get('win_rate', 'N/A'),
                        'total_episodes': version.metrics.get('total_episodes', 'N/A'),
                        'tags': ', '.join(version.tags),
                        'categories': ', '.join(version.categories),
                        'notes': version.notes[:100]  # Limiter la longueur
                    }
                    writer.writerow(row)
        
        elif output_format == 'markdown':
            filename = f"versions_export_{timestamp}.md"
            filepath = os.path.join(self.archive_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Export des versions - {timestamp}\n\n")
                f.write(f"**Total**: {len(versions)} versions\n\n")
                
                f.write("## Résumé\n")
                f.write(f"- Sessions: {len(versions)}\n")
                f.write(f"- Période: {versions[0].timestamp if versions else 'N/A'} à {versions[-1].timestamp if versions else 'N/A'}\n")
                f.write(f"- Modèles uniques: {len(set(v.model_type for v in versions))}\n")
                f.write(f"- Agents uniques: {len(set(v.agent_type for v in versions))}\n\n")
                
                f.write("## Versions\n")
                for version in versions:
                    f.write(f"### {version.session_id} (#{version.session_number})\n")
                    f.write(f"- **Date**: {version.timestamp}\n")
                    f.write(f"- **Modèle**: {version.model_type}\n")
                    f.write(f"- **Agent**: {version.agent_type}\n")
                    f.write(f"- **Win Rate**: {version.metrics.get('win_rate', 'N/A')}\n")
                    f.write(f"- **Tags**: {', '.join(version.tags) if version.tags else 'Aucun'}\n")
                    f.write(f"- **Catégories**: {', '.join(version.categories) if version.categories else 'Aucune'}\n")
                    f.write(f"- **Notes**: {version.notes[:200] if version.notes else 'Aucune'}\n\n")
        
        else:
            logger.error(f"Format d'export non supporté: {output_format}")
            return ""
        
        logger.info(f"Versions exportées: {filepath}")
        return filepath
    
    def migrate_old_system(self, old_archive_dir: str) -> int:
        """
        Migre les archives d'un ancien système vers le nouveau.
        
        Args:
            old_archive_dir: Répertoire contenant les anciennes archives
            
        Returns:
            Nombre d'archives migrées
        """
        if not os.path.exists(old_archive_dir):
            logger.error(f"Répertoire d'anciennes archives non trouvé: {old_archive_dir}")
            return 0
        
        migrated_count = 0
        
        # Rechercher les fichiers d'archive
        archive_patterns = ['*.zip', '*.tar', '*.tar.gz']
        
        for pattern in archive_patterns:
            for archive_path in Path(old_archive_dir).glob(pattern):
                try:
                    # Extraire les métadonnées basiques du nom de fichier
                    archive_name = archive_path.name
                    
                    # Essayer de deviner le numéro de session
                    session_number_match = re.search(r'(\d+)', archive_name)
                    session_number = int(session_number_match.group(1)) if session_number_match else 0
                    
                    # Créer des métadonnées minimales
                    metadata = {
                        'session_id': f"migrated_{archive_name.replace('.', '_')}",
                        'model_type': 'unknown',
                        'agent_type': 'unknown',
                        'metrics': {'total_episodes': 0, 'win_rate': 0.0},
                        'parameters': {},
                        'notes': f"Migré depuis l'ancien système: {archive_name}"
                    }
                    
                    # Copier l'archive
                    new_archive_path = os.path.join(self.archive_dir, archive_name)
                    shutil.copy2(archive_path, new_archive_path)
                    
                    # Enregistrer la version
                    version = self.register_new_version(new_archive_path, metadata)
                    
                    if version:
                        migrated_count += 1
                        logger.info(f"Archive migrée: {archive_name} -> {version.session_id}")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la migration de {archive_path}: {e}")
        
        logger.info(f"Migration terminée: {migrated_count} archives migrées")
        return migrated_count
    
    def cleanup_orphaned_metadata(self) -> int:
        """
        Nettoie les métadonnées orphelines (sans archive correspondante).
        
        Returns:
            Nombre de métadonnées nettoyées
        """
        cleaned_count = 0
        
        # Vérifier chaque version dans le registre
        for session_id in list(self.registry['versions'].keys()):
            version_data = self.registry['versions'][session_id]
            archive_path = version_data.get('archive_path')
            
            if archive_path and not os.path.exists(archive_path):
                # Archive manquante, supprimer la métadonnée
                del self.registry['versions'][session_id]
                
                # Supprimer le fichier de métadonnées
                metadata_path = os.path.join(self.metadata_dir, f"{session_id}.json")
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                
                cleaned_count += 1
                logger.info(f"Métadonnées orphelines nettoyées: {session_id}")
        
        if cleaned_count > 0:
            self._save_registry()
        
        return cleaned_count