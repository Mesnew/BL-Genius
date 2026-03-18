# ⚽ BL Genius - Football Analysis System

Système d'analyse de football par IA basé sur YOLO et Computer Vision.

## 🎯 Fonctionnalités

- **Détection & Tracking** : Détecte et suit automatiquement les joueurs, gardiens, arbitres et ballon
- **Modèle Fine-tuné** : Support du modèle Roboflow (ball, goalkeeper, player, referee)
- **Assignation d'équipes** : K-Means clustering sur les couleurs de maillots
- **Interpolation du ballon** : Suivi du ballon même quand il n'est pas détecté
- **Compensation caméra** : Optical flow pour compenser les mouvements de caméra
- **Transformation de perspective** : Vue 2D du terrain avec positions réelles
- **Statistiques** : Vitesse instantanée (km/h), distance totale, vitesse max
- **Interface web** : Next.js avec upload drag & drop et lecteur côte à côte

## 🚀 Démarrage rapide

### Prérequis

- Python 3.9+
- pip
- (Optionnel) GPU NVIDIA pour accélérer l'analyse

### Installation

1. **Cloner et entrer dans le dossier :**
```bash
cd bl-genius
```

2. **Lancer le serveur :**
```bash
./start.sh
```

Le script va :
- Créer un environnement virtuel Python
- Installer les dépendances
- Télécharger le modèle YOLO
- Lancer le serveur FastAPI sur http://localhost:8000

3. **Ouvrir l'interface :**

Ouvrez `frontend/index.html` dans votre navigateur, ou allez sur http://localhost:8000

## 📁 Structure du projet

```
bl-genius/
├── backend/
│   ├── main.py                    # API FastAPI
│   ├── yolo_tracker/
│   │   ├── __init__.py
│   │   ├── tracker.py             # Tracker principal
│   │   ├── team_assigner.py       # K-Means pour équipes
│   │   ├── ball_interpolator.py   # Interpolation ballon
│   │   ├── camera_movement_estimator.py  # Optical flow
│   │   ├── perspective_transformer.py    # Vue terrain 2D
│   │   └── speed_calculator.py    # Vitesse et distance
│   ├── training/
│   │   ├── download_dataset.py    # Télécharger dataset Roboflow
│   │   └── train.py               # Entraînement YOLO
│   ├── models/                    # Modèles YOLO (.pt)
│   ├── uploads/                   # Vidéos uploadées
│   └── outputs/                   # Vidéos analysées
├── frontend/                      # Next.js 15 + Tailwind
│   ├── src/
│   │   ├── app/
│   │   ├── components/            # UploadVideo, VideoPlayer
│   │   └── lib/                   # API client
│   └── next.config.ts
├── requirements.txt
└── start.sh                       # Script de lancement
```

## 🔧 API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Status de l'API |
| `/upload` | POST | Uploader une vidéo |
| `/analyze/{task_id}` | POST | Lancer l'analyse |
| `/status/{task_id}` | GET | Voir le statut |
| `/download/{task_id}` | GET | Télécharger le résultat |
| `/tasks` | GET | Lister toutes les tâches |
| `/docs` | GET | Documentation Swagger |

## 🎮 Utilisation

### Via l'interface web

1. Ouvrez `frontend/index.html`
2. Glissez-déposez une vidéo de football
3. Attendez l'analyse (1-5 minutes selon la durée)
4. Visualisez et téléchargez le résultat

### Via l'API (curl)

```bash
# Upload
curl -X POST -F "file=@match.mp4" http://localhost:8000/upload

# Analyse (remplacez TASK_ID par l'ID reçu)
curl -X POST http://localhost:8000/analyze/TASK_ID

# Vérifier le statut
curl http://localhost:8000/status/TASK_ID

# Télécharger
curl -O http://localhost:8000/download/TASK_ID
```

## 🧪 Test avec une vidéo exemple

Vous pouvez télécharger une vidéo de test depuis :
- [DFL Bundesliga Data Shootout (Kaggle)](https://www.kaggle.com/competitions/dfl-bundesliga-data-shootout)
- Ou utiliser n'importe quelle vidéo de match de football

## 🛠️ Développement

### Ajouter le modèle fine-tuné

Pour utiliser le modèle du tutoriel (meilleure détection du ballon) :

1. Téléchargez le dataset Roboflow : https://universe.roboflow.com/roboflow-jvuqo/football-players-detection-3zvbc
2. Entraînez le modèle avec YOLOv5/v8
3. Placez le fichier `best.pt` dans `backend/models/`
4. Redémarrez le serveur

### Personnaliser les annotations

Modifiez `backend/yolo_tracker/tracker.py` :
- `draw_annotations()` : Style des ellipses/triangles
- `get_object_tracks()` : Logique de tracking

## ✅ Roadmap

- [x] **Étape 1**: Structure Next.js + Upload Vidéo
- [x] **Étape 2**: Intégration du modèle fine-tuné (Roboflow)
- [x] **Étape 3**: Assignation d'équipes par K-Means
- [x] **Étape 4**: Interpolation du ballon
- [x] **Étape 5**: Transformation de perspective + Compensation caméra
- [x] **Étape 6**: Calcul de la vitesse et distance
- [ ] Support du streaming (YouTube)
- [ ] Dockerisation complète
- [ ] Interface de calibration pour la perspective

## 🧠 Modules de Tracking

### TeamAssigner (`team_assigner.py`)
- Extraction de la couleur du maillot (région du torse)
- Clustering K-Means pour identifier 2 équipes
- Assignation automatique avec score de confiance

### BallInterpolator (`ball_interpolator.py`)
- Interpolation linéaire entre détections
- Lissage par moyenne mobile
- Maximum 10 frames interpolées consécutivement

### CameraMovementEstimator (`camera_movement_estimator.py`)
- Détection de features (GoodFeaturesToTrack)
- Optical flow Lucas-Kanade
- Compensation des positions des joueurs

### PerspectiveTransformer (`perspective_transformer.py`)
- Homographie basée sur les coins du terrain
- Conversion pixels → mètres
- Vue 2D du terrain avec positions des joueurs

### SpeedCalculator (`speed_calculator.py`)
- Vitesse instantanée (km/h)
- Distance totale parcourue
- Vitesse maximale et moyenne par joueur
- Rapport de statistiques

## 🎨 Visualisation

| Élément | Style | Couleur |
|---------|-------|---------|
| Joueurs Équipe 1 | Ellipse | Couleur maillot (K-Means) |
| Joueurs Équipe 2 | Ellipse | Couleur maillot (K-Means) |
| Gardiens | Ellipse | Orange |
| Arbitres | Ellipse | Jaune |
| Ballon (détecté) | Triangle | Rouge |
| Ballon (interpolé) | Triangle | Gris |
| Vitesse | Texte | Vert/Jaune/Rouge selon vitesse |

## 🙏 Crédits

Basé sur le tutoriel de [Abdullah Tarek](https://github.com/abdullahtarek/football_analysis) - "Build an AI/ML Football Analysis system with YOLO, OpenCV, and Python"

## 📄 Licence

MIT License
