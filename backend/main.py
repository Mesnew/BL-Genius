from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
from pathlib import Path
import uuid
import asyncio
import threading
from typing import Optional
import torch
import warnings
from pydantic import BaseModel
import yt_dlp

# Patch PyTorch 2.6+ weights_only issue
_original_torch_load = torch.load
def patched_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = patched_torch_load
warnings.filterwarnings('ignore', message='.*weights_only.*', category=UserWarning)

# Import des modules du template
import sys
sys.path.append(str(Path(__file__).parent))
from trackers import Tracker
from team_assigner import TeamAssigner
from player_ball_assigner import PlayerBallAssigner
from camera_movement_estimator import CameraMovementEstimator
from view_transformer import ViewTransformer
from speed_and_distance_estimator import SpeedAndDistance_Estimator
from utils import read_video, save_video

app = FastAPI(title="BL Genius - Football Analysis API")

# CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dossiers
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
MODELS_DIR = Path("models")
STUBS_DIR = Path("stubs")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
STUBS_DIR.mkdir(exist_ok=True)

# Stockage des tâches (en mémoire pour l'instant)
tasks = {}

class YouTubeRequest(BaseModel):
    url: str

@app.get("/")
async def root():
    return {"message": "BL Genius API", "version": "0.2.0"}

@app.post("/youtube")
async def download_youtube(request: YouTubeRequest):
    """Télécharger une vidéo YouTube pour analyse"""
    try:
        task_id = str(uuid.uuid4())
        output_template = str(UPLOAD_DIR / f"{task_id}_youtube")

        # Options yt-dlp - télécharge en MP4 pour compatibilité OpenCV
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': f"{output_template}.mp4",
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            title = info.get('title', 'youtube_video')

        final_file = f"{output_template}.mp4"

        tasks[task_id] = {
            "id": task_id,
            "status": "uploaded",
            "input_path": final_file,
            "output_path": None,
            "progress": 0,
            "source": "youtube",
            "title": title
        }

        return {
            "task_id": task_id,
            "status": "uploaded",
            "message": f"Vidéo YouTube téléchargée: {title}",
            "title": title
        }

    except Exception as e:
        raise HTTPException(400, f"Erreur téléchargement YouTube: {str(e)}")

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload une vidéo pour analyse"""
    if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(400, "Format non supporté. Utilisez MP4, AVI, MOV ou MKV")

    task_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{task_id}_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    tasks[task_id] = {
        "id": task_id,
        "status": "uploaded",
        "input_path": str(file_path),
        "output_path": None,
        "progress": 0
    }

    return {
        "task_id": task_id,
        "status": "uploaded",
        "message": "Vidéo uploadée avec succès"
    }

def process_video_async(task_id: str, input_path: str, output_path: str):
    """Traiter la vidéo avec tous les modules du template"""
    try:
        task = tasks[task_id]
        task["status"] = "processing"
        task["progress"] = 10
        print(f"🎬 Traitement de la vidéo: {input_path}")

        # Lire la vidéo
        video_frames = read_video(input_path)
        print(f"✅ {len(video_frames)} frames lues")
        task["progress"] = 20

        # Initialize Tracker
        model_path = str(MODELS_DIR / "best.pt") if (MODELS_DIR / "best.pt").exists() else "yolov8m.pt"
        tracker = Tracker(model_path)
        print(f"🤖 Modèle chargé: {model_path}")

        # Get object tracks
        stub_path = str(STUBS_DIR / f"{task_id}_track_stubs.pkl")
        tracks = tracker.get_object_tracks(video_frames, read_from_stub=False, stub_path=stub_path)
        print("✅ Tracking terminé")
        task["progress"] = 40

        # Add positions
        tracker.add_position_to_tracks(tracks)

        # Camera movement estimator
        camera_movement_estimator = CameraMovementEstimator(video_frames[0])
        camera_movement_stub = str(STUBS_DIR / f"{task_id}_camera_movement_stub.pkl")
        camera_movement_per_frame = camera_movement_estimator.get_camera_movement(
            video_frames, read_from_stub=False, stub_path=camera_movement_stub
        )
        camera_movement_estimator.add_adjust_positions_to_tracks(tracks, camera_movement_per_frame)
        print("✅ Mouvement de caméra estimé")
        task["progress"] = 50

        # View Transformer
        view_transformer = ViewTransformer()
        view_transformer.add_transformed_position_to_tracks(tracks)
        print("✅ Transformation de perspective appliquée")
        task["progress"] = 60

        # Interpolate Ball Positions
        tracks["ball"] = tracker.interpolate_ball_positions(tracks["ball"])
        print("✅ Interpolation du ballon terminée")

        # Speed and distance estimator
        speed_and_distance_estimator = SpeedAndDistance_Estimator()
        speed_and_distance_estimator.add_speed_and_distance_to_tracks(tracks)
        print("✅ Vitesse et distance calculées")
        task["progress"] = 70

        # Assign Player Teams
        team_assigner = TeamAssigner()
        team_assigner.assign_team_color(video_frames[0], tracks['players'][0])

        for frame_num, player_track in enumerate(tracks['players']):
            for player_id, track in player_track.items():
                team = team_assigner.get_player_team(video_frames[frame_num], track['bbox'], player_id)
                tracks['players'][frame_num][player_id]['team'] = team
                tracks['players'][frame_num][player_id]['team_color'] = team_assigner.team_colors[team]
        print("✅ Équipes assignées")
        task["progress"] = 80

        # Assign Ball Acquisition
        player_assigner = PlayerBallAssigner()
        team_ball_control = []
        for frame_num, player_track in enumerate(tracks['players']):
            ball_bbox = tracks['ball'][frame_num][1]['bbox']
            assigned_player = player_assigner.assign_ball_to_player(player_track, ball_bbox)

            if assigned_player != -1:
                tracks['players'][frame_num][assigned_player]['has_ball'] = True
                team_ball_control.append(tracks['players'][frame_num][assigned_player]['team'])
            else:
                if team_ball_control:
                    team_ball_control.append(team_ball_control[-1])
                else:
                    team_ball_control.append(1)
        import numpy as np
        team_ball_control = np.array(team_ball_control)
        print("✅ Contrôle du ballon assigné")
        task["progress"] = 90

        # Draw output
        output_video_frames = tracker.draw_annotations(video_frames, tracks, team_ball_control)
        output_video_frames = camera_movement_estimator.draw_camera_movement(output_video_frames, camera_movement_per_frame)
        speed_and_distance_estimator.draw_speed_and_distance(output_video_frames, tracks)
        print("✅ Annotations dessinées")

        # Save video
        save_video(output_video_frames, output_path)
        print(f"💾 Vidéo sauvegardée: {output_path}")

        task["status"] = "completed"
        task["output_path"] = output_path
        task["progress"] = 100

    except Exception as e:
        task["status"] = "error"
        task["error"] = str(e)
        print(f"❌ Erreur analyse {task_id}: {e}")
        import traceback
        traceback.print_exc()

@app.post("/analyze/{task_id}")
async def analyze_video(task_id: str, background_tasks: BackgroundTasks):
    """Lancer l'analyse de la vidéo en arrière-plan"""
    if task_id not in tasks:
        raise HTTPException(404, "Tâche non trouvée")

    task = tasks[task_id]

    if task["status"] == "processing":
        return {"task_id": task_id, "status": "processing", "message": "Analyse déjà en cours"}

    if task["status"] == "completed":
        return {"task_id": task_id, "status": "completed", "message": "Analyse déjà terminée"}

    # Lancer l'analyse en arrière-plan
    output_path = str(OUTPUT_DIR / f"{task_id}_analyzed.avi")
    task["status"] = "processing"
    task["progress"] = 10

    # Lancer dans un thread séparé
    thread = threading.Thread(
        target=process_video_async,
        args=(task_id, task["input_path"], output_path)
    )
    thread.start()

    return {
        "task_id": task_id,
        "status": "processing",
        "message": "Analyse lancée en arrière-plan"
    }

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """Récupérer le statut d'une analyse"""
    if task_id not in tasks:
        raise HTTPException(404, "Tâche non trouvée")

    return tasks[task_id]

@app.get("/download/{task_id}")
async def download_video(task_id: str):
    """Télécharger la vidéo analysée"""
    if task_id not in tasks:
        raise HTTPException(404, "Tâche non trouvée")

    task = tasks[task_id]

    if task["status"] != "completed":
        raise HTTPException(400, "Analyse non terminée")

    if not task["output_path"] or not os.path.exists(task["output_path"]):
        raise HTTPException(404, "Fichier de sortie non trouvé")

    return FileResponse(
        task["output_path"],
        media_type="video/x-msvideo",
        filename=f"bl_genius_analysis_{task_id}.avi"
    )

@app.get("/tasks")
async def list_tasks():
    """Lister toutes les tâches"""
    return list(tasks.values())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
