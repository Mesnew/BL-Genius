#!/usr/bin/env python3
"""
Script pour télécharger le dataset Roboflow Football Player Detection
Dataset: https://universe.roboflow.com/roboflow-jvuqo/football-players-detection-3zvbc
"""

import os
import sys
import shutil

def download_roboflow_dataset():
    """Télécharge le dataset depuis Roboflow"""

    print("📥 Téléchargement du dataset Roboflow...")
    print("Dataset: Football Player Detection")
    print("Classes: ball, goalkeeper, player, referee")
    print()

    # Installation de roboflow si nécessaire
    try:
        import roboflow
    except ImportError:
        print("Installation de roboflow...")
        os.system("pip install roboflow -q")
        import roboflow

    # Téléchargement
    from roboflow import Roboflow

    print("Connexion à Roboflow...")
    # Version publique du dataset (pas besoin de clé API pour télécharger)
    rf = Roboflow(api_key="demo")  # Clé demo pour datasets publics

    print("Téléchargement du dataset...")
    project = rf.workspace("roboflow-jvuqo").project("football-players-detection-3zvbc")
    dataset = project.version(1).download("yolov8")

    print(f"✅ Dataset téléchargé: {dataset.location}")

    # Déplacer le dataset dans le bon dossier
    target_dir = "football-players-detection-1"
    if os.path.exists(target_dir):
        # Structure attendue par YOLO
        os.makedirs("football-players-detection", exist_ok=True)

        # Déplacer train/test/valid
        for split in ["train", "test", "valid"]:
            src = f"{target_dir}/{split}"
            dst = f"football-players-detection/{split}"
            if os.path.exists(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.move(src, dst)

        # Déplacer data.yaml
        if os.path.exists(f"{target_dir}/data.yaml"):
            shutil.move(f"{target_dir}/data.yaml", "football-players-detection/data.yaml")

        # Nettoyer
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

    print("✅ Dataset prêt pour l'entraînement!")
    print("📁 Dossier: football-players-detection/")
    print("📄 Config: football-players-detection/data.yaml")

    return "football-players-detection"

if __name__ == "__main__":
    try:
        dataset_path = download_roboflow_dataset()
        print(f"\n🎉 Dataset prêt dans: {dataset_path}")
        print("\nProchaine étape: Lancer l'entraînement avec train.py")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("\nAlternative: Téléchargez manuellement depuis:")
        print("https://universe.roboflow.com/roboflow-jvuqo/football-players-detection-3zvbc")
        sys.exit(1)
