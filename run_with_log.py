#!/usr/bin/env python3
"""
Script pour exécuter un programme Python avec journalisation en temps réel.
Capture stdout/stderr et les écrit dans un fichier log texte, puis compresse en gzip à la fin.
"""
import sys
import subprocess
import threading
import time
import os
import gzip
import shutil
from datetime import datetime

def tee_output(pipe, log_file, prefix=""):
    """Lit les lignes depuis pipe et les écrit à la fois dans log_file (texte) et stdout/stderr."""
    with open(log_file, 'a', encoding='utf-8') as f:
        for line in iter(pipe.readline, ''):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            output_line = f"[{timestamp}] {prefix}{line}"
            sys.stdout.write(output_line)
            sys.stdout.flush()
            f.write(output_line)
            f.flush()
        pipe.close()

def compress_log(text_log_path, compressed_log_path):
    """Compresse un fichier log texte en gzip."""
    try:
        with open(text_log_path, 'rb') as f_in:
            with gzip.open(compressed_log_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(text_log_path)
        return True
    except Exception as e:
        print(f"Erreur lors de la compression: {e}", file=sys.stderr)
        # Ne pas supprimer le fichier texte en cas d'erreur
        if os.path.exists(text_log_path):
            print(f"Le fichier texte original est conservé : {text_log_path}", file=sys.stderr)
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_with_log.py <script.py> [args...]")
        sys.exit(1)
    
    script = sys.argv[1]
    args = sys.argv[1:]
    
    # Créer le répertoire logs s'il n'existe pas
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Nom du fichier log texte temporaire (sans compression)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    script_name = os.path.basename(script).replace('.py', '')
    text_log = os.path.join(log_dir, f"{script_name}_{timestamp}.log")
    compressed_log = text_log + '.gz'
    
    print(f"Lancement de {' '.join(args)}")
    print(f"Log en temps réel : {compressed_log}")
    
    # Ouvrir le processus
    proc = subprocess.Popen(
        [sys.executable] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )
    
    # Démarrer les threads pour lire stdout et stderr
    stdout_thread = threading.Thread(target=tee_output, args=(proc.stdout, text_log, ""))
    stderr_thread = threading.Thread(target=tee_output, args=(proc.stderr, text_log, "ERROR: "))
    
    stdout_thread.start()
    stderr_thread.start()
    
    # Attendre la fin du processus
    proc.wait()
    
    # Attendre que les threads de lecture terminent
    stdout_thread.join()
    stderr_thread.join()
    
    # Compresser le fichier log texte
    if os.path.exists(text_log):
        compress_log(text_log, compressed_log)
        print(f"\nProcessus terminé avec code de sortie {proc.returncode}")
        print(f"Log complet disponible dans {compressed_log}")
    else:
        print(f"\nProcessus terminé avec code de sortie {proc.returncode}")
        print("Aucun log texte généré.")

if __name__ == '__main__':
    main()