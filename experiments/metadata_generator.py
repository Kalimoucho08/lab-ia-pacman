#!/usr/bin/env python3
"""
Générateur de métadonnées intelligent pour les archives Pac-Man.

Fonctionnalités :
- Génération automatique de params.md avec explications contextuelles
- Analyse comparative avec sessions précédentes
- Observations automatiques basées sur les métriques
- Évaluation intelligente des hyperparamètres
- Génération de tags et catégories
"""

import json
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import statistics
from pathlib import Path

@dataclass
class TrainingMetrics:
    """Métriques d'entraînement pour une session."""
    total_episodes: int
    win_rate: float
    avg_score: float
    max_score: float
    min_score: float
    avg_steps: float
    exploration_rate: float
    learning_rate: float
    gamma: float
    epsilon: float
    batch_size: int
    buffer_size: int
    training_time_hours: float
    memory_usage_mb: float

@dataclass
class SessionMetadata:
    """Métadonnées complètes d'une session."""
    session_id: str
    session_number: int
    timestamp: str
    model_type: str
    agent_type: str
    environment: str
    metrics: TrainingMetrics
    tags: List[str]
    previous_session_id: Optional[str] = None
    notes: Optional[str] = None
    config_hash: Optional[str] = None

class IntelligentMetadataGenerator:
    """
    Générateur de métadonnées intelligent.
    
    Produit des descriptions contextuelles, des comparaisons et des observations
    automatiques basées sur les données d'entraînement.
    """
    
    def __init__(self, history_file: Optional[str] = None):
        """
        Initialise le générateur avec un fichier d'historique optionnel.
        
        Args:
            history_file: Chemin vers un fichier JSON contenant l'historique des sessions
        """
        self.history_file = history_file
        self.session_history: List[Dict] = []
        
        if history_file and Path(history_file).exists():
            self._load_history()
    
    def _load_history(self) -> None:
        """Charge l'historique des sessions depuis le fichier."""
        try:
            with open(self.history_file, 'r') as f:
                self.session_history = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load history file: {e}")
            self.session_history = []
    
    def _save_history(self) -> None:
        """Sauvegarde l'historique des sessions dans le fichier."""
        if not self.history_file:
            return
        
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.session_history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save history file: {e}")
    
    def generate_params_md(self, current_session: SessionMetadata, 
                          previous_session: Optional[SessionMetadata] = None) -> str:
        """
        Génère le contenu du fichier params.md avec explications contextuelles.
        
        Args:
            current_session: Métadonnées de la session actuelle
            previous_session: Métadonnées de la session précédente (optionnel)
            
        Returns:
            Contenu Markdown formaté
        """
        lines = []
        
        # En-tête
        lines.append(f"# Session {current_session.session_number} - {current_session.timestamp}")
        lines.append("")
        lines.append(f"**Modèle**: {current_session.model_type}  ")
        lines.append(f"**Agent**: {current_session.agent_type}  ")
        lines.append(f"**Environnement**: {current_session.environment}")
        lines.append("")
        
        # Section 1: Résumé exécutif
        lines.append("## 📊 Résumé exécutif")
        lines.append("")
        
        summary = self._generate_executive_summary(current_session.metrics, previous_session.metrics if previous_session else None)
        lines.append(summary)
        lines.append("")
        
        # Section 2: Paramètres d'entraînement avec évaluation
        lines.append("## ⚙️ Paramètres d'entraînement")
        lines.append("")
        
        params_evaluation = self._evaluate_hyperparameters(current_session.metrics)
        for param, (value, evaluation) in params_evaluation.items():
            lines.append(f"- **{param}**: `{value}` – {evaluation}")
        lines.append("")
        
        # Section 3: Métriques de performance détaillées
        lines.append("## 📈 Métriques de performance")
        lines.append("")
        
        metrics_table = self._format_metrics_table(current_session.metrics)
        lines.append(metrics_table)
        lines.append("")
        
        # Section 4: Analyse comparative (si session précédente disponible)
        if previous_session:
            lines.append("## 🔄 Comparaison avec session précédente")
            lines.append("")
            
            comparison = self._generate_comparison_analysis(current_session, previous_session)
            lines.append(comparison)
            lines.append("")
            
            # Graphique ASCII simple pour visualiser l'amélioration
            improvement_chart = self._generate_improvement_chart(
                current_session.metrics.win_rate,
                previous_session.metrics.win_rate
            )
            if improvement_chart:
                lines.append("### Tendance du taux de victoire")
                lines.append("```")
                lines.append(improvement_chart)
                lines.append("```")
                lines.append("")
        
        # Section 5: Observations et recommandations
        lines.append("## 💡 Observations et recommandations")
        lines.append("")
        
        observations = self._generate_observations(current_session, previous_session)
        lines.append(observations)
        lines.append("")
        
        # Section 6: Tags et catégories
        lines.append("## 🏷️ Tags et catégories")
        lines.append("")
        
        tags_with_icons = self._categorize_session(current_session)
        lines.append(", ".join(tags_with_icons))
        lines.append("")
        
        # Section 7: Notes techniques
        lines.append("## 📝 Notes techniques")
        lines.append("")
        
        if current_session.notes:
            lines.append(current_session.notes)
        else:
            lines.append("*Aucune note supplémentaire.*")
        lines.append("")
        
        # Pied de page
        lines.append("---")
        lines.append(f"*Généré automatiquement le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("*Système d'archivage intelligent - Laboratoire IA Pac-Man*")
        
        return "\n".join(lines)
    
    def _generate_executive_summary(self, metrics: TrainingMetrics, 
                                   previous_metrics: Optional[TrainingMetrics] = None) -> str:
        """Génère un résumé exécutif des performances."""
        summary_parts = []
        
        # Évaluation du taux de victoire
        if metrics.win_rate >= 0.8:
            winrate_eval = "excellente"
        elif metrics.win_rate >= 0.6:
            winrate_eval = "bonne"
        elif metrics.win_rate >= 0.4:
            winrate_eval = "moyenne"
        else:
            winrate_eval = "faible"
        
        summary_parts.append(f"Performance **{winrate_eval}** avec un taux de victoire de **{metrics.win_rate:.1%}**.")
        
        # Comparaison avec session précédente
        if previous_metrics:
            winrate_diff = metrics.win_rate - previous_metrics.win_rate
            if abs(winrate_diff) < 0.01:
                diff_text = "stable"
            elif winrate_diff > 0:
                diff_text = f"en amélioration de **+{winrate_diff:.1%}**"
            else:
                diff_text = f"en régression de **{winrate_diff:.1%}**"
            
            summary_parts.append(f"Performance {diff_text} par rapport à la session précédente.")
        
        # Évaluation de l'efficacité d'entraînement
        episodes_per_hour = metrics.total_episodes / max(metrics.training_time_hours, 0.1)
        if episodes_per_hour > 1000:
            efficiency = "très efficace"
        elif episodes_per_hour > 500:
            efficiency = "efficace"
        elif episodes_per_hour > 100:
            efficiency = "modérément efficace"
        else:
            efficiency = "peu efficace"
        
        summary_parts.append(f"Entraînement **{efficiency}** ({episodes_per_hour:.0f} épisodes/heure).")
        
        # Recommandation globale
        if metrics.win_rate >= 0.7 and metrics.avg_score > 1000:
            recommendation = "La configuration actuelle est optimale. Poursuivre l'entraînement."
        elif metrics.win_rate < 0.3:
            recommendation = "Revoir les hyperparamètres ou augmenter l'exploration."
        else:
            recommendation = "Continuer l'entraînement avec ajustements mineurs si nécessaire."
        
        summary_parts.append(f"**Recommandation**: {recommendation}")
        
        return " ".join(summary_parts)
    
    def _evaluate_hyperparameters(self, metrics: TrainingMetrics) -> Dict[str, Tuple[Any, str]]:
        """Évalue les hyperparamètres et retourne des descriptions contextuelles."""
        evaluations = {}
        
        # Learning Rate
        lr = metrics.learning_rate
        if lr > 0.01:
            lr_eval = "élevé → apprentissage rapide mais risque d'instabilité"
        elif lr > 0.001:
            lr_eval = "optimal → bon compromis stabilité/vitesse"
        elif lr > 0.0001:
            lr_eval = "faible → convergence lente mais stable"
        else:
            lr_eval = "très faible → risque de sous-apprentissage"
        evaluations["Learning Rate"] = (lr, lr_eval)
        
        # Gamma (facteur de discount)
        gamma = metrics.gamma
        if gamma > 0.95:
            gamma_eval = "élevé → forte importance des récompenses futures"
        elif gamma > 0.85:
            gamma_eval = "modéré → équilibre court/long terme"
        else:
            gamma_eval = "faible → focus sur récompenses immédiates"
        evaluations["Gamma"] = (gamma, gamma_eval)
        
        # Epsilon (exploration)
        epsilon = metrics.epsilon
        if epsilon > 0.3:
            epsilon_eval = "élevé → forte exploration, bonne découverte"
        elif epsilon > 0.1:
            epsilon_eval = "modéré → bon équilibre exploration/exploitation"
        else:
            epsilon_eval = "faible → forte exploitation, risque de stagnation"
        evaluations["Epsilon"] = (epsilon, epsilon_eval)
        
        # Batch Size
        batch = metrics.batch_size
        if batch > 128:
            batch_eval = "grand → mise à jour stable mais coûteuse"
        elif batch > 32:
            batch_eval = "moyen → bon compromis"
        else:
            batch_eval = "petit → mise à jour fréquente mais bruyante"
        evaluations["Batch Size"] = (batch, batch_eval)
        
        return evaluations
    
    def _format_metrics_table(self, metrics: TrainingMetrics) -> str:
        """Formate les métriques dans un tableau Markdown."""
        table = [
            "| Métrique | Valeur | Évaluation |",
            "|----------|--------|------------|"
        ]
        
        # Taux de victoire
        winrate_eval = self._evaluate_metric(metrics.win_rate, "win_rate")
        table.append(f"| Taux de victoire | {metrics.win_rate:.2%} | {winrate_eval} |")
        
        # Score moyen
        score_eval = self._evaluate_metric(metrics.avg_score, "avg_score")
        table.append(f"| Score moyen | {metrics.avg_score:.0f} | {score_eval} |")
        
        # Épisodes
        table.append(f"| Épisodes totaux | {metrics.total_episodes} | - |")
        
        # Temps d'entraînement
        table.append(f"| Durée d'entraînement | {metrics.training_time_hours:.1f}h | - |")
        
        # Utilisation mémoire
        mem_eval = self._evaluate_metric(metrics.memory_usage_mb, "memory")
        table.append(f"| Mémoire utilisée | {metrics.memory_usage_mb:.0f} MB | {mem_eval} |")
        
        return "\n".join(table)
    
    def _evaluate_metric(self, value: float, metric_type: str) -> str:
        """Évalue une métrique spécifique."""
        if metric_type == "win_rate":
            if value >= 0.8:
                return "⭐ Excellente"
            elif value >= 0.6:
                return "✅ Bonne"
            elif value >= 0.4:
                return "⚠️ Moyenne"
            else:
                return "❌ À améliorer"
        
        elif metric_type == "avg_score":
            if value >= 2000:
                return "⭐ Exceptionnel"
            elif value >= 1000:
                return "✅ Bon"
            elif value >= 500:
                return "⚠️ Acceptable"
            else:
                return "❌ Faible"
        
        elif metric_type == "memory":
            if value > 2000:
                return "⚠️ Élevée"
            elif value > 1000:
                return "✅ Normale"
            else:
                return "✅ Optimale"
        
        return "-"
    
    def _generate_comparison_analysis(self, current: SessionMetadata, 
                                     previous: SessionMetadata) -> str:
        """Génère une analyse comparative entre deux sessions."""
        analysis = []
        
        # Différences de métriques
        winrate_diff = current.metrics.win_rate - previous.metrics.win_rate
        score_diff = current.metrics.avg_score - previous.metrics.avg_score
        episodes_diff = current.metrics.total_episodes - previous.metrics.total_episodes
        
        # Analyse du taux de victoire
        if abs(winrate_diff) < 0.01:
            winrate_analysis = "**Stabilité** du taux de victoire."
        elif winrate_diff > 0.15:
            winrate_analysis = f"**Amélioration significative** (+{winrate_diff:.1%}) !"
        elif winrate_diff > 0.05:
            winrate_analysis = f"**Amélioration modérée** (+{winrate_diff:.1%})."
        elif winrate_diff > -0.05:
            winrate_analysis = "**Légère variation** dans la marge d'erreur."
        elif winrate_diff > -0.15:
            winrate_analysis = f"**Légère régression** ({winrate_diff:.1%})."
        else:
            winrate_analysis = f"**Régression significative** ({winrate_diff:.1%}) !"
        
        analysis.append(f"- **Taux de victoire**: {winrate_analysis}")
        
        # Analyse du score
        if abs(score_diff) < 50:
            score_analysis = "Score stable."
        elif score_diff > 200:
            score_analysis = f"Score **fortement amélioré** (+{score_diff:.0f})."
        elif score_diff > 0:
            score_analysis = f"Score **légèrement amélioré** (+{score_diff:.0f})."
        else:
            score_analysis = f"Score **en baisse** ({score_diff:.0f})."
        
        analysis.append(f"- **Score moyen**: {score_analysis}")
        
        # Analyse des épisodes
        if episodes_diff > 0:
            episodes_analysis = f"**+{episodes_diff} épisodes** d'entraînement supplémentaires."
        else:
            episodes_analysis = f"**{episodes_diff} épisodes** de moins."
        
        analysis.append(f"- **Volume d'entraînement**: {episodes_analysis}")
        
        # Conclusion comparative
        if winrate_diff > 0.1 and score_diff > 100:
            conclusion = "**Progression nette** dans toutes les métriques. La configuration actuelle est supérieure."
        elif winrate_diff > 0 and score_diff > 0:
            conclusion = "**Progression positive**. L'entraînement porte ses fruits."
        elif abs(winrate_diff) < 0.05 and abs(score_diff) < 100:
            conclusion = "**Stabilité générale**. Possible plateau d'apprentissage."
        else:
            conclusion = "**Performance en baisse**. Revoir la stratégie d'entraînement."
        
        analysis.append(f"\n**Conclusion**: {conclusion}")
        
        return "\n".join(analysis)
    def _generate_improvement_chart(self, current_winrate: float,
                                   previous_winrate: float) -> str:
        """Génère un graphique ASCII simple pour visualiser l'amélioration."""
        if previous_winrate <= 0:
            return ""
        
        # Normaliser les valeurs pour un graphique de 20 caractères
        max_value = max(current_winrate, previous_winrate, 0.01)
        scale = 20 / max_value
        
        prev_bars = int(previous_winrate * scale)
        curr_bars = int(current_winrate * scale)
        
        # Créer les barres
        prev_bar = "█" * prev_bars + "░" * (20 - prev_bars)
        curr_bar = "█" * curr_bars + "░" * (20 - curr_bars)
        
        chart = [
            f"Précédent [{previous_winrate:.1%}]: {prev_bar}",
            f"Actuel    [{current_winrate:.1%}]: {curr_bar}",
            "",
            f"Évolution: {'↑' if current_winrate > previous_winrate else '↓'} {abs(current_winrate - previous_winrate):.1%}"
        ]
        
        return "\n".join(chart)
    
    def _generate_observations(self, current: SessionMetadata,
                              previous: Optional[SessionMetadata] = None) -> str:
        """Génère des observations et recommandations automatiques."""
        observations = []
        
        # Observation basée sur le taux de victoire
        if current.metrics.win_rate >= 0.8:
            observations.append("✅ **Performance excellente** – Le modèle maîtrise bien l'environnement.")
        elif current.metrics.win_rate >= 0.6:
            observations.append("✅ **Performance satisfaisante** – Bon équilibre exploration/exploitation.")
        elif current.metrics.win_rate >= 0.4:
            observations.append("⚠️ **Performance moyenne** – Possibilité d'amélioration avec ajustement des hyperparamètres.")
        else:
            observations.append("❌ **Performance faible** – Revoir la stratégie d'entraînement.")
        
        # Observation basée sur la stabilité du score
        score_range = current.metrics.max_score - current.metrics.min_score
        if score_range > 2000:
            observations.append("⚠️ **Grande variabilité des scores** – L'entraînement est instable. Essayer de réduire le learning rate.")
        elif score_range < 500:
            observations.append("✅ **Scores stables** – L'entraînement converge bien.")
        
        # Observation basée sur l'exploration
        if current.metrics.exploration_rate > 0.3:
            observations.append("🔍 **Exploration élevée** – Le modèle explore activement. Bon pour découvrir de nouvelles stratégies.")
        elif current.metrics.exploration_rate < 0.05:
            observations.append("🎯 **Exploitation élevée** – Le modèle exploite ses connaissances. Risque de stagnation.")
        
        # Recommandations basées sur la comparaison
        if previous:
            winrate_diff = current.metrics.win_rate - previous.metrics.win_rate
            
            if winrate_diff > 0.1:
                observations.append("🚀 **Progression rapide** – Maintenir la configuration actuelle.")
            elif winrate_diff < -0.1:
                observations.append("🔧 **Régression détectée** – Revenir aux hyperparamètres précédents ou augmenter l'exploration.")
            elif abs(winrate_diff) < 0.02:
                observations.append("⏸️ **Plateau détecté** – Essayer de nouvelles stratégies d'exploration ou ajuster le learning rate.")
        
        # Recommandation finale
        if current.metrics.win_rate < 0.3:
            observations.append("\n**🎯 Recommandation prioritaire**: Augmenter le taux d'exploration (epsilon) et réduire le learning rate.")
        elif current.metrics.win_rate > 0.7:
            observations.append("\n**🎯 Recommandation**: Poursuivre l'entraînement pour consolider les performances.")
        else:
            observations.append("\n**🎯 Recommandation**: Ajuster progressivement les hyperparamètres pour améliorer les performances.")
        
        return "\n\n".join(observations)
    
    def _categorize_session(self, session: SessionMetadata) -> List[str]:
        """Catégorise la session et génère des tags avec icônes."""
        tags = []
        
        # Basé sur le taux de victoire
        if session.metrics.win_rate >= 0.8:
            tags.append("🏆 excellence")
        elif session.metrics.win_rate >= 0.6:
            tags.append("✅ bonne_performance")
        elif session.metrics.win_rate >= 0.4:
            tags.append("⚠️ performance_moyenne")
        else:
            tags.append("🔧 besoin_amélioration")
        
        # Basé sur le type de modèle
        if "dqn" in session.model_type.lower():
            tags.append("🧠 DQN")
        elif "ppo" in session.model_type.lower():
            tags.append("🔄 PPO")
        elif "a2c" in session.model_type.lower():
            tags.append("⚡ A2C")
        else:
            tags.append(f"🤖 {session.model_type}")
        
        # Basé sur l'agent
        if "pacman" in session.agent_type.lower():
            tags.append("👻 PacMan")
        elif "ghost" in session.agent_type.lower():
            tags.append("👻 Fantôme")
        else:
            tags.append(f"🎮 {session.agent_type}")
        
        # Basé sur la durée d'entraînement
        if session.metrics.training_time_hours > 10:
            tags.append("⏳ long_entraînement")
        elif session.metrics.training_time_hours > 1:
            tags.append("⏱️ entraînement_moyen")
        else:
            tags.append("⚡ entraînement_court")
        
        # Tags personnalisés de la session
        tags.extend(session.tags)
        
        return tags
    
    def generate_config_yaml(self, session: SessionMetadata) -> str:
        """Génère un fichier de configuration YAML pour la session."""
        config = {
            'session': {
                'id': session.session_id,
                'number': session.session_number,
                'timestamp': session.timestamp,
                'model_type': session.model_type,
                'agent_type': session.agent_type,
                'environment': session.environment
            },
            'hyperparameters': {
                'learning_rate': session.metrics.learning_rate,
                'gamma': session.metrics.gamma,
                'epsilon': session.metrics.epsilon,
                'batch_size': session.metrics.batch_size,
                'buffer_size': session.metrics.buffer_size
            },
            'performance': {
                'win_rate': session.metrics.win_rate,
                'avg_score': session.metrics.avg_score,
                'total_episodes': session.metrics.total_episodes,
                'training_time_hours': session.metrics.training_time_hours
            },
            'tags': session.tags,
            'notes': session.notes or ""
        }
        
        return yaml.dump(config, default_flow_style=False, allow_unicode=True)
    
    def generate_metadata_json(self, session: SessionMetadata) -> Dict[str, Any]:
        """Génère un dictionnaire de métadonnées au format JSON."""
        return {
            'session': asdict(session),
            'generated_at': datetime.now().isoformat(),
            'generator_version': '1.0.0',
            'analysis': {
                'performance_category': self._categorize_session(session)[0].replace("️", "").strip(),
                'recommendations': self._generate_observations(session, None).split("\n\n")[:3]
            }
        }


# Exemple d'utilisation
if __name__ == "__main__":
    print("=== Test du générateur de métadonnées intelligent ===")
    
    # Créer des métriques de test
    test_metrics = TrainingMetrics(
        total_episodes=5000,
        win_rate=0.77,
        avg_score=1520.5,
        max_score=2450,
        min_score=620,
        avg_steps=850,
        exploration_rate=0.15,
        learning_rate=0.001,
        gamma=0.99,
        epsilon=0.1,
        batch_size=32,
        buffer_size=10000,
        training_time_hours=2.5,
        memory_usage_mb=1240
    )
    
    # Créer une session de test
    test_session = SessionMetadata(
        session_id="test_session_001",
        session_number=47,
        timestamp="2026-01-03T16:32:00",
        model_type="DQN",
        agent_type="PacMan",
        environment="PacMan-v0",
        metrics=test_metrics,
        tags=['baseline', 'DQN', 'test_run'],
        notes="Session de test pour validation du générateur de métadonnées."
    )
    
    # Créer une session précédente pour comparaison
    prev_metrics = TrainingMetrics(
        total_episodes=3000,
        win_rate=0.65,
        avg_score=1380,
        max_score=2100,
        min_score=580,
        avg_steps=790,
        exploration_rate=0.2,
        learning_rate=0.0015,
        gamma=0.95,
        epsilon=0.15,
        batch_size=32,
        buffer_size=10000,
        training_time_hours=1.8,
        memory_usage_mb=1180
    )
    
    prev_session = SessionMetadata(
        session_id="test_session_046",
        session_number=46,
        timestamp="2026-01-02T14:20:00",
        model_type="DQN",
        agent_type="PacMan",
        environment="PacMan-v0",
        metrics=prev_metrics,
        tags=['baseline', 'DQN']
    )
    
    # Initialiser le générateur
    generator = IntelligentMetadataGenerator()
    
    # Générer le params.md
    params_content = generator.generate_params_md(test_session, prev_session)
    
    print("\n=== Contenu généré (extrait) ===")
    print(params_content[:500] + "...")
    
    # Générer la configuration YAML
    yaml_content = generator.generate_config_yaml(test_session)
    print("\n=== Configuration YAML ===")
    print(yaml_content)
    
    # Générer les métadonnées JSON
    json_metadata = generator.generate_metadata_json(test_session)
    print("\n=== Métadonnées JSON (extrait) ===")
    print(json.dumps(json_metadata, indent=2)[:500] + "...")
    
    print("\n=== Test terminé avec succès ===")
        
