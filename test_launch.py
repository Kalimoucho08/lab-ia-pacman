#!/usr/bin/env python3
"""
Test de lancement rapide de l'interface.
"""
import sys
import os
import threading
import time

# Ajouter le répertoire courant au PYTHONPATH
sys.path.insert(0, '.')

def test_interface():
    """Test que l'interface peut être créée sans erreur."""
    try:
        from main_advanced import IALabAdvanced
        lab = IALabAdvanced()
        print("Interface créée avec succès.")
        # Fermer après 2 secondes
        lab.root.after(2000, lab.root.destroy)
        lab.run()
        print("Interface fermée.")
    except Exception as e:
        print(f"Erreur lors du lancement: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_interface()