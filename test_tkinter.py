#!/usr/bin/env python3
"""
Test rapide de l'interface Tkinter.
"""
import sys
import tkinter as tk
import threading
import time

def test_tkinter():
    try:
        root = tk.Tk()
        root.title("Test Tkinter")
        root.geometry("300x200")
        label = tk.Label(root, text="Interface Tkinter fonctionnelle")
        label.pack(pady=20)
        # Mettre à jour l'interface
        root.update()
        print("[OK] Fenêtre Tkinter créée avec succès")
        # Fermer après 1 seconde
        root.after(1000, root.destroy)
        root.mainloop()
        return True
    except Exception as e:
        print(f"[ERREUR] Échec de création de l'interface Tkinter: {e}")
        return False

if __name__ == "__main__":
    success = test_tkinter()
    sys.exit(0 if success else 1)