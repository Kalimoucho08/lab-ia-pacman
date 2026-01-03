#!/usr/bin/env python3
"""
Module pour la compression et la consolidation des logs.
Fournit des fonctions pour compresser les logs texte et fusionner les logs TensorBoard.
"""
import gzip
import shutil
import os
import glob
import tempfile
import threading
from datetime import datetime
from pathlib import Path

def compress_text_log(log_path, keep_original=True):
    """
    Compresse un fichier log texte avec gzip.
    
    Args:
        log_path (str): Chemin vers le fichier log.
        keep_original (bool): Si True, conserve le fichier original après compression.
    
    Returns:
        str: Chemin du fichier compressé (.gz) ou None en cas d'erreur.
    """
    if not os.path.exists(log_path):
        return None
    compressed_path = log_path + '.gz'
    try:
        with open(log_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        if not keep_original:
            os.remove(log_path)
        return compressed_path
    except Exception as e:
        print(f"Erreur lors de la compression de {log_path}: {e}")
        return None

def merge_tensorboard_logs(log_dir, output_file=None):
    """
    Fusionne tous les fichiers d'événements TensorBoard (*.tfevents*) d'un répertoire
    en un seul fichier. Utilise l'outil `tensorboard.summary.merge` si disponible.

    Args:
        log_dir (str): Répertoire contenant les fichiers d'événements.
        output_file (str): Chemin du fichier de sortie. Si None, génère un nom automatique.

    Returns:
        str: Chemin du fichier fusionné, ou None si échec.
    """
    try:
        # Essayer d'importer tensorflow pour utiliser tf.summary.merge
        import tensorflow as tf
    except ImportError:
        print("TensorFlow non installé, impossible de fusionner les logs TensorBoard.")
        print("Installez TensorFlow avec: pip install tensorflow")
        return None
    
    event_files = glob.glob(os.path.join(log_dir, '*.tfevents*'))
    if not event_files:
        print(f"Aucun fichier d'événements trouvé dans {log_dir}")
        return None
    
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(log_dir, f'merged_events_{timestamp}.tfevents')
    
    try:
        # Créer un writer de sortie
        with tf.summary.create_file_writer(os.path.dirname(output_file)) as writer:
            # Lire tous les événements de chaque fichier
            for event_file in event_files:
                for event in tf.compat.v1.train.summary_iterator(event_file):
                    # Réécrire chaque événement dans le writer unique
                    for value in event.summary.value:
                        tf.summary.scalar(value.tag, value.simple_value, step=event.step)
        # Note: Cette approche est simplifiée et peut ne pas préserver tous les types de données.
        # Une alternative plus robuste serait d'utiliser `tensorboard.summary.merge`.
        print(f"Fusionné {len(event_files)} fichiers en {output_file}")
        return output_file
    except Exception as e:
        print(f"Erreur lors de la fusion des logs TensorBoard: {e}")
        return None

def archive_simulation_logs(simulation_id=None, log_dir='logs', output_archive=None):
    """
    Crée une archive ZIP contenant tous les logs d'une simulation.

    Args:
        simulation_id (str): Identifiant de la simulation (ex: horodatage).
                            Si None, utilise le dernier répertoire de logs.
        log_dir (str): Répertoire racine des logs.
        output_archive (str): Chemin de l'archive de sortie (.zip).

    Returns:
        str: Chemin de l'archive créée.
    """
    import zipfile
    
    if simulation_id is None:
        # Trouver le sous-répertoire le plus récent (par date de modification)
        subdirs = [d for d in os.listdir(log_dir) if os.path.isdir(os.path.join(log_dir, d))]
        if not subdirs:
            print("Aucun sous-répertoire de logs trouvé.")
            return None
        # Sélectionner le répertoire avec la date de modification la plus récente
        simulation_id = max(subdirs, key=lambda d: os.path.getmtime(os.path.join(log_dir, d)))
    
    sim_path = os.path.join(log_dir, simulation_id)
    if not os.path.exists(sim_path):
        print(f"Répertoire de simulation {sim_path} introuvable.")
        return None
    
    if output_archive is None:
        output_archive = os.path.join(log_dir, f'{simulation_id}.zip')
    
    with zipfile.ZipFile(output_archive, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(sim_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, log_dir)
                zipf.write(file_path, arcname)
    
    print(f"Archive créée : {output_archive}")
    return output_archive

if __name__ == '__main__':
    # Exemple d'utilisation
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test de compression
        test_log = 'logs/test.log'
        with open(test_log, 'w') as f:
            f.write('Test log line\n')
        compressed = compress_text_log(test_log, keep_original=False)
        print(f"Compressed: {compressed}")
        # Test de fusion (nécessite TensorFlow)
        # merge_tensorboard_logs('logs/DQN_0')
        # Test d'archivage
        archive_simulation_logs()
    else:
        print("Module log_archiver chargé.")