#!/bin/bash

echo "🚀 BL Genius - Lancement du serveur"
echo "=================================="

# Vérifier si on est dans le bon dossier
if [ ! -f "requirements.txt" ]; then
    echo "❌ Erreur: Lancez ce script depuis le dossier bl-genius"
    exit 1
fi

# Créer l'environnement virtuel si nécessaire
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer les dépendances
echo "📥 Installation des dépendances..."
pip install -q -r requirements.txt

# Télécharger le modèle YOLO si nécessaire
if [ ! -f "backend/models/yolov8m.pt" ]; then
    echo "🤖 Téléchargement du modèle YOLOv8..."
    mkdir -p backend/models
    python3 -c "from ultralytics import YOLO; YOLO('yolov8m.pt')" 2>/dev/null || true
    if [ -f "yolov8m.pt" ]; then
        mv yolov8m.pt backend/models/
    fi
fi

# Créer les dossiers nécessaires
mkdir -p backend/uploads backend/outputs

# Lancer le serveur
echo ""
echo "✅ Serveur prêt!"
echo ""
echo "🌐 API Backend: http://localhost:8000"
echo "📱 Frontend:    http://localhost:8000 (ou ouvrez frontend/index.html)"
echo ""
echo "📚 Documentation API: http://localhost:8000/docs"
echo ""
echo "⚠️  Gardez ce terminal ouvert pour garder le serveur actif"
echo ""

cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
