#!/usr/bin/env python3
"""
Script de test pour vérifier la compression des logs.
"""
import sys
import time

print("Début du test de compression des logs")
print("Ce message devrait être capturé et compressé.")
print("Erreur simulée", file=sys.stderr)
time.sleep(0.5)
print("Fin du test.")