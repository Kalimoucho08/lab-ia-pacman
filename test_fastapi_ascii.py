#!/usr/bin/env python3
"""
Test du backend FastAPI (version ASCII pour Windows CP1252).
"""
import sys
import subprocess
import time
import requests

def test_fastapi():
    # Démarrer le serveur en arrière-plan
    print("Demarrage du serveur FastAPI...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Attendre que le serveur démarre
    time.sleep(5)
    
    try:
        # Tester l'endpoint racine
        print("Test de l'endpoint racine...")
        response = requests.get("http://127.0.0.1:8000/")
        if response.status_code == 200:
            data = response.json()
            print(f"OK Endpoint racine: {data}")
        else:
            print(f"ECHEC Endpoint racine: {response.status_code}")
            return False
        
        # Tester l'endpoint health
        print("Test de l'endpoint health...")
        response = requests.get("http://127.0.0.1:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"OK Health: {data}")
        else:
            print(f"ECHEC Health: {response.status_code}")
            return False
        
        # Tester l'endpoint docs
        print("Test de l'endpoint docs...")
        response = requests.get("http://127.0.0.1:8000/docs")
        if response.status_code == 200:
            print("OK Docs")
        else:
            print(f"ECHEC Docs: {response.status_code}")
            return False
        
        print("Tous les tests FastAPI ont reussi !")
        return True
        
    except Exception as e:
        print(f"Erreur lors du test FastAPI: {e}")
        return False
    finally:
        # Arrêter le serveur
        print("Arret du serveur...")
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    success = test_fastapi()
    sys.exit(0 if success else 1)