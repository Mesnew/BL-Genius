#!/usr/bin/env python3
"""
Script d'entraînement YOLOv8 pour la détection de joueurs de football
Basé sur le tutoriel: https://github.com/abdullahtarek/football_analysis
"""

import os
import sys
from pathlib import Path

# Ajouter le parent au path pour importer les modules
sys.path.append(str(Path(__file__).parent.parent))

def train_model():
    """Entraîne le modèle YOLOv8 sur le dataset football"""

    print("🚀 Démarrage de l'entraînement YOLOv8")
    print("=" * 50)

    # Vérifier que le dataset existe
    dataset_path = Path("football-players-detection/data.yaml")
    if not dataset_path.exists():
        print("❌ Dataset non trouvé!")
        print("Lancez d'abord: python download_dataset.py")
        return False

    print(f"✅ Dataset trouvé: {dataset_path}")

    # Importer ultralytics
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Installation d'ultralytics...")
        os.system("pip install ultralytics -q")
        from ultralytics import YOLO

    # Créer le dossier models
    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(exist_ok=True)

    # Charger le modèle pré-entraîné YOLOv8
    print("\n📥 Chargement du modèle YOLOv8x...")
    model = YOLO("yolov8x.pt")  # Version extra-large pour meilleure précision

    # Entraînement
    print("\n🔥 Début de l'entraînement...")
    print("Paramètres:")
    print("  - Epochs: 100")
    print("  - Image size: 640")
    print("  - Batch: 16")
    print("  - Device: GPU si disponible, sinon CPU")
    print()

    results = model.train(
        data=str(dataset_path),
        epochs=100,
        imgsz=640,
        batch=16,
        device=0 if os.system("nvidia-smi > /dev/null 2>&1") == 0 else "cpu",
        project=str(models_dir),
        name="football_yolov8x",
        exist_ok=True,
        patience=20,  # Early stopping après 20 epochs sans amélioration
        save=True,
        plots=True,
    )

    print("\n" + "=" * 50)
    print("✅ Entraînement terminé!")

    # Copier le meilleur modèle
    best_model = Path(models_dir) / "football_yolov8x" / "weights" / "best.pt"
    final_model = models_dir / "best.pt"

    if best_model.exists():
        import shutil
        shutil.copy(best_model, final_model)
        print(f"🎉 Modèle sauvegardé: {final_model}")
        print(f"   mAP50: {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
        return True
    else:
        print("❌ Modèle non trouvé après entraînement")
        return False

def quick_train():
    """Entraînement rapide pour test (10 epochs)"""

    print("⚡ Mode entraînement rapide (10 epochs)")

    dataset_path = Path("football-players-detection/data.yaml")
    if not dataset_path.exists():
        print("❌ Dataset non trouvé!")
        return False

    try:
        from ultralytics import YOLO
    except ImportError:
        os.system("pip install ultralytics -q")
        from ultralytics import YOLO

    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(exist_ok=True)

    model = YOLO("yolov8n.pt")  # Version nano pour test rapide

    model.train(
        data=str(dataset_path),
        epochs=10,
        imgsz=640,
        batch=8,
        project=str(models_dir),
        name="football_test",
        exist_ok=True,
    )

    print("✅ Test terminé!")
    return True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Entraînement YOLO Football")
    parser.add_argument("--quick", action="store_true", help="Entraînement rapide (10 epochs)")
    args = parser.parse_args()

    if args.quick:
        success = quick_train()
    else:
        success = train_model()

    sys.exit(0 if success else 1)
