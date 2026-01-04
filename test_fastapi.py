#!/usr/bin/env python3
"""
Test du backend FastAPI.
"""
import sys
import subprocess
import time
import requests

def test_fastapi():
    # Démarrer le serveur en arrière-plan
    print("Démarrage du serveur FastAPI...")
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
            print(f"✓ Endpoint racine OK: {data}")
        else:
            print(f"✗ Endpoint racine échoué: {response.status_code}")
            return False
        
        # Tester l'endpoint health
        print("Test de l'endpoint health...")
        response = requests.get("http://127.0.0.1:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health OK: {data}")
        else:
            print(f"✗ Health échoué: {response.status_code}")
            return False
        
        # Tester l'endpoint docs
        print("Test de l'endpoint docs...")
        response = requests.get("http://127.0.0.1:8000/docs")
        if response.status_code == 200:
            print("✓ Docs OK")
        else:
            print(f"✗ Docs échoué: {response.status_code}")
            return False
        
        print("Tous les tests FastAPI ont réussi !")
        return True
        
    except Exception as e:
        print(f"Erreur lors du test FastAPI: {e}")
        return False
    finally:
        # Arrêter le serveur
        print("Arrêt du serveur...")
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    success = test_fastapi()
    sys.exit(0 if success else 1)