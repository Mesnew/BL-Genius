# ============================================
# BL GENIUS - MAIN API (Version Sécurisée)
# Avec authentification JWT, rate limiting, validation
# ============================================

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import torch
import warnings
import re
import uuid
import logging
import yt_dlp

# Configuration du logging sécurisé
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Patch PyTorch
_original_torch_load = torch.load
def patched_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = patched_torch_load
warnings.filterwarnings('ignore', message='.*weights_only.*', category=UserWarning)

# Imports des modèles et base de données
from app.database import get_db, init_db, check_db_connection
from app.models.video import Video, User
from app.workers import celery_app, process_video

# Imports sécurité
from app.auth import (
    get_current_user, get_current_active_user, get_password_hash,
    verify_password, create_access_token, Token,
    get_current_user_from_token_or_header
)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ============================================
# CONFIGURATION
# ============================================

# Validation UUID
UUID_REGEX = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# Création de l'application FastAPI
app = FastAPI(
    title="BL Genius - Football Analysis API",
    description="API sécurisée pour l'analyse de matchs de football",
    version="1.0.0",
    docs_url="/docs" if os.getenv("DEBUG") == "true" else None,
    redoc_url="/redoc" if os.getenv("DEBUG") == "true" else None
)

# Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS sécurisé
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
# Ajouter localhost et 127.0.0.1 si pas déjà présents
for origin in ["http://localhost:3000", "http://127.0.0.1:3000"]:
    if origin not in ALLOWED_ORIGINS:
        ALLOWED_ORIGINS.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# Configuration des répertoires
VIDEO_OUTPUT_DIR = Path(os.getenv('VIDEO_OUTPUT_DIR', '/app/data/videos'))
VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(VIDEO_OUTPUT_DIR / 'uploads').mkdir(exist_ok=True)
(VIDEO_OUTPUT_DIR / 'processed').mkdir(exist_ok=True)

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "500")) * 1024 * 1024  # 500 MB

# ============================================
# MODÈLES PYDANTIC
# ============================================

class YouTubeRequest(BaseModel):
    url: str = Field(..., min_length=10, max_length=1000)

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    password: str = Field(..., min_length=8, max_length=100)

class UserLogin(BaseModel):
    username: str
    password: str

class StatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    message: Optional[str] = None

# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def validate_uuid(task_id: str) -> bool:
    """Valide le format UUID"""
    return bool(UUID_REGEX.match(task_id))

def sanitize_filename(filename: str) -> str:
    """Nettoie un nom de fichier"""
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = filename.lstrip('.')
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext
    return filename

# ============================================
# GESTION DES ERREURS GLOBALE
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Masque les erreurs internes"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Log les erreurs HTTP"""
    if exc.status_code >= 400:
        logger.warning(f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# ============================================
# AUTHENTIFICATION
# ============================================

@app.post("/auth/register", response_model=Token)
@limiter.limit("100/hour" if os.getenv("DEBUG") == "true" else "5/hour")
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Inscription d'un nouvel utilisateur"""
    # Vérifier si l'email existe
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(400, "Email already registered")

    # Vérifier si le username existe
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(400, "Username already taken")

    # Créer l'utilisateur
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"User registered: {user.username}")

    # Créer le token
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/login", response_model=Token)
@limiter.limit("100/minute" if os.getenv("DEBUG") == "true" else "10/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Connexion utilisateur"""
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"Failed login attempt: {credentials.username} from {request.client.host}")
        raise HTTPException(401, "Incorrect username or password")

    if not user.is_active:
        raise HTTPException(403, "Account is disabled")

    # Mettre à jour la date de dernière connexion
    user.last_login = datetime.utcnow()
    db.commit()

    logger.info(f"User logged in: {user.username}")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Récupère les infos de l'utilisateur connecté"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }


# ============================================
# API PRINCIPALE (Protégée)
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialisation"""
    logger.info("🚀 Starting BL Genius API (Secure)")
    init_db()
    if check_db_connection():
        logger.info("✅ Database connected")
    else:
        logger.error("❌ Database connection failed")


@app.get("/")
async def root():
    return {"message": "BL Genius API", "version": "1.0.0", "secure": True}


@app.get("/health")
async def health_check():
    """Health check pour monitoring"""
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/upload", response_model=StatusResponse)
@limiter.limit("5/minute")
async def upload_video(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload sécurisé d'une vidéo"""
    try:
        # Validation du fichier
        if not file.filename:
            raise HTTPException(400, "No file provided")

        # Vérification de l'extension
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(400, f"Format not supported. Use: {', '.join(allowed_extensions)}")

        # Lecture et vérification taille
        contents = await file.read()
        file_size = len(contents)

        if file_size == 0:
            raise HTTPException(400, "Empty file")

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(413, f"File too large. Max: {MAX_FILE_SIZE / 1024 / 1024}MB")

        # Génération nom sécurisé
        task_id = str(uuid.uuid4())
        safe_filename = f"{task_id}{file_ext}"
        file_path = VIDEO_OUTPUT_DIR / 'uploads' / safe_filename

        # Sauvegarde
        with open(file_path, "wb") as f:
            f.write(contents)

        file_size_mb = file_size / (1024 * 1024)

        # Création en BDD
        video = Video(
            task_id=task_id,
            original_name=sanitize_filename(file.filename),
            storage_path=str(file_path),
            status='uploaded',
            file_size_mb=file_size_mb,
            user_id=current_user.id
        )
        db.add(video)
        db.commit()

        logger.info(f"Video uploaded: {task_id} by user {current_user.username}")

        return {
            "task_id": task_id,
            "status": "uploaded",
            "progress": 0,
            "message": "Video uploaded successfully"
        }

    except Exception as e:
        logger.error(f"Upload error: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(500, "Upload failed")


@app.post("/youtube", response_model=StatusResponse)
@limiter.limit("5/minute")
async def download_youtube(
    request: Request,
    youtube_req: YouTubeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Téléchargement YouTube sécurisé"""
    # Validation URL simple
    youtube_pattern = re.compile(r'(https?://)?(www\.)?(youtube|youtu)\.')
    if not youtube_pattern.match(youtube_req.url):
        raise HTTPException(400, "Invalid YouTube URL")

    try:
        task_id = str(uuid.uuid4())
        output_template = VIDEO_OUTPUT_DIR / 'uploads' / f"{task_id}_youtube"

        ydl_opts = {
            'format': 'best[vcodec^=avc1][ext=mp4]/best[ext=mp4]/best',
            'outtmpl': str(output_template) + '.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'max_filesize': MAX_FILE_SIZE,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_req.url, download=True)
            title = info.get('title', 'youtube_video')
            ext = info.get('ext', 'mp4')

        final_file = VIDEO_OUTPUT_DIR / 'uploads' / f"{task_id}_youtube.{ext}"

        if not final_file.exists():
            raise Exception("Download failed")

        file_size = final_file.stat().st_size / (1024 * 1024)

        video = Video(
            task_id=task_id,
            original_name=f"{sanitize_filename(title)}.{ext}",
            storage_path=str(final_file),
            status='uploaded',
            source='youtube',
            youtube_url=youtube_req.url,
            file_size_mb=file_size,
            user_id=current_user.id
        )
        db.add(video)
        db.commit()

        logger.info(f"YouTube downloaded: {task_id} by user {current_user.username}")

        return {
            "task_id": task_id,
            "status": "uploaded",
            "progress": 0,
            "message": f"YouTube video downloaded: {title}"
        }

    except Exception as e:
        logger.error(f"YouTube download error: {e}")
        raise HTTPException(400, f"Download failed: {str(e)}")


@app.post("/analyze/{task_id}", response_model=StatusResponse)
@limiter.limit("100/hour" if os.getenv("DEBUG") == "true" else "10/hour")
async def analyze_video(
    request: Request,
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Lance l'analyse d'une vidéo (mode synchrone sans Celery)"""
    import asyncio
    from pathlib import Path

    # Validation UUID
    if not validate_uuid(task_id):
        raise HTTPException(400, "Invalid task ID format")

    # Vérifier ownership
    video = db.query(Video).filter(
        Video.task_id == task_id,
        Video.user_id == current_user.id
    ).first()

    if not video:
        raise HTTPException(404, "Video not found or access denied")

    if video.status == 'processing':
        return {"task_id": task_id, "status": "processing", "progress": 50, "message": "Analysis in progress"}

    if video.status == 'completed':
        return {"task_id": task_id, "status": "completed", "progress": 100, "message": "Analysis already completed"}

    # Mise à jour
    video.status = 'processing'
    video.processing_started_at = datetime.utcnow()
    db.commit()

    logger.info(f"Analysis started (sync mode): {task_id} by user {current_user.username}")

    # Lancer l'analyse en arrière-plan (async)
    asyncio.create_task(run_analysis_sync(task_id, current_user.id))

    return {
        "task_id": task_id,
        "status": "processing",
        "progress": 50,
        "message": "Analysis started - processing in background"
    }


async def run_analysis_sync(task_id: str, user_id: int):
    """Version synchrone et optimisée de l'analyse vidéo"""
    import cv2
    import numpy as np
    from datetime import datetime
    from pathlib import Path
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models.video import Video
    from trackers.tracker import Tracker
    from team_assigner.team_assigner import TeamAssigner
    from player_ball_assigner.player_ball_assigner import PlayerBallAssigner
    from camera_movement_estimator.camera_movement_estimator import CameraMovementEstimator
    from view_transformer.view_transformer import ViewTransformer
    from speed_and_distance_estimator.speed_and_distance_estimator import SpeedAndDistance_Estimator as SpeedAndDistanceEstimator
    from utils.video_utils import read_video, save_video

    db = SessionLocal()

    try:
        video = db.query(Video).filter(Video.task_id == task_id).first()
        if not video:
            logger.error(f"Video {task_id} not found")
            return

        input_path = video.storage_path
        output_path = Path(VIDEO_OUTPUT_DIR) / 'processed' / f"{task_id}_analyzed.mp4"

        if not Path(input_path).exists():
            raise Exception(f"Video file not found: {input_path}")

        logger.info(f"🎬 Starting optimized analysis for {task_id}")

        # Lecture vidéo optimisée (1 frame sur 4 pour accélérer)
        logger.info(f"📖 Reading video: {input_path}")
        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Lire TOUTES les frames pour une vidéo parfaitement fluide (pas de saut)
        frame_interval = 1
        video_frames = []
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % frame_interval == 0:
                video_frames.append(frame)
            frame_count += 1
        cap.release()

        logger.info(f"✅ Read {len(video_frames)} frames (sampled 1/{frame_interval})")

        # Calculer le FPS ajusté pour la vidéo de sortie
        # Pour garder la durée originale, on divise le FPS par l'intervalle
        output_fps = fps / frame_interval
        logger.info(f"🎥 Output FPS: {output_fps} (original: {fps}, interval: {frame_interval})")

        # Créer le dossier stubs s'il n'existe pas
        (VIDEO_OUTPUT_DIR / 'stubs').mkdir(parents=True, exist_ok=True)

        # Tracking YOLO optimisé
        logger.info("🔍 Object tracking...")
        model_path = str(Path('/app/models') / "best.pt") if (Path('/app/models') / "best.pt").exists() else 'yolov8m.pt'
        tracker = Tracker(model_path)

        tracks = tracker.get_object_tracks(
            video_frames,
            read_from_stub=False,
            stub_path=str(VIDEO_OUTPUT_DIR / 'stubs' / f"{task_id}_tracks.pkl")
        )
        logger.info("✅ Tracking complete")

        tracker.add_position_to_tracks(tracks)

        # Estimation mouvement caméra
        logger.info("📹 Camera movement estimation...")
        camera_estimator = CameraMovementEstimator(video_frames[0])
        camera_movements = camera_estimator.get_camera_movement(
            video_frames,
            read_from_stub=False,
            stub_path=str(VIDEO_OUTPUT_DIR / 'stubs' / f"{task_id}_camera.pkl")
        )
        camera_estimator.add_adjust_positions_to_tracks(tracks, camera_movements)

        # Transformation de perspective
        logger.info("🗺️ Perspective transformation...")
        view_transformer = ViewTransformer()
        view_transformer.add_transformed_position_to_tracks(tracks)

        # Interpolation ballon
        logger.info("🎯 Ball interpolation...")
        tracks["ball"] = tracker.interpolate_ball_positions(tracks["ball"])

        # Calcul vitesse/distance
        logger.info("⚡ Speed and distance calculation...")
        speed_estimator = SpeedAndDistanceEstimator()
        speed_estimator.add_speed_and_distance_to_tracks(tracks)

        # Assignation équipes
        logger.info("🏃 Team assignment...")
        team_assigner = TeamAssigner()
        team_assigner.assign_team_color(video_frames[0], tracks['players'][0])

        for frame_num, player_track in enumerate(tracks['players']):
            for player_id, track in player_track.items():
                team = team_assigner.get_player_team(
                    video_frames[frame_num],
                    track['bbox'],
                    player_id
                )
                tracks['players'][frame_num][player_id]['team'] = team
                tracks['players'][frame_num][player_id]['team_color'] = team_assigner.team_colors[team]

        # Contrôle ballon
        logger.info("⚽ Ball control assignment...")
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

        team_ball_control = np.array(team_ball_control)

        # Génération vidéo annotée
        logger.info("🎨 Generating annotated video...")
        output_video_frames = tracker.draw_annotations(video_frames, tracks, team_ball_control)
        output_video_frames = camera_estimator.draw_camera_movement(output_video_frames, camera_movements)
        output_video_frames = speed_estimator.draw_speed_and_distance(output_video_frames, tracks)

        # Dupliquer les frames pour revenir au nombre de frames original (vidéo fluide)
        logger.info(f"📹 Interpolating frames: {len(output_video_frames)} -> {len(output_video_frames) * frame_interval} frames")
        interpolated_frames = []
        for frame in output_video_frames:
            # Dupliquer chaque frame 'frame_interval' fois
            for _ in range(frame_interval):
                interpolated_frames.append(frame)
        output_video_frames = interpolated_frames
        logger.info(f"✅ Interpolated to {len(output_video_frames)} frames")

        # Sauvegarde avec FPS original pour une vidéo fluide
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Utiliser VideoWriter avec le FPS original
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(
            str(output_path),
            fourcc,
            fps,  # FPS original pour une vidéo fluide
            (output_video_frames[0].shape[1], output_video_frames[0].shape[0])
        )
        for frame in output_video_frames:
            out.write(frame)
        out.release()

        logger.info(f"✅ Video saved: {output_path} at {output_fps} FPS")

        # Mise à jour BDD
        video.status = 'completed'
        video.output_path = str(output_path)
        video.analysis_result = {
            'total_frames': len(video_frames),
            'total_players': sum(len(f) for f in tracks['players']),
            'possession_team1': float((team_ball_control == 1).sum() / len(team_ball_control) * 100),
            'possession_team2': float((team_ball_control == 2).sum() / len(team_ball_control) * 100),
            'processing_time': 'completed'
        }
        db.commit()

        logger.info(f"✅ Analysis complete for {task_id}")

    except Exception as exc:
        logger.error(f"❌ Error analyzing {task_id}: {exc}")
        try:
            video.status = 'error'
            video.analysis_result = {'error': str(exc)}
            db.commit()
        except:
            pass
    finally:
        db.close()


@app.get("/status/{task_id}")
async def get_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère le statut"""
    if not validate_uuid(task_id):
        raise HTTPException(400, "Invalid task ID format")

    video = db.query(Video).filter(
        Video.task_id == task_id,
        Video.user_id == current_user.id
    ).first()

    if not video:
        raise HTTPException(404, "Video not found")

    progress = 0
    if video.status == 'uploaded':
        progress = 0
    elif video.status == 'processing':
        progress = 50
    elif video.status == 'completed':
        progress = 100

    return {
        "task_id": task_id,
        "status": video.status,
        "progress": progress,
        "message": None,
        "analysis_result": video.analysis_result if video.status == 'completed' else None
    }


@app.get("/download/{task_id}")
async def download_video(
    task_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Télécharge une vidéo analysée (token dans header ou URL)"""
    # Extraire le token du header ou de l'URL
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    else:
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(401, "Authentication required")

    # Vérifier le token
    from app.auth import decode_token
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(401, "Invalid token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(401, "Invalid token")

    current_user = db.query(User).filter(User.id == int(user_id)).first()
    if current_user is None:
        raise HTTPException(401, "User not found")

    """Télécharge une vidéo analysée"""
    if not validate_uuid(task_id):
        raise HTTPException(400, "Invalid task ID format")

    video = db.query(Video).filter(
        Video.task_id == task_id,
        Video.user_id == current_user.id
    ).first()

    if not video:
        raise HTTPException(404, "Video not found")

    if video.status != 'completed':
        raise HTTPException(400, f"Analysis not completed (status: {video.status})")

    if not video.output_path or not Path(video.output_path).exists():
        raise HTTPException(404, "Output file not found")

    logger.info(f"Video downloaded: {task_id} by user {current_user.username}")

    return FileResponse(
        video.output_path,
        media_type="video/mp4",
        filename=f"bl_genius_analysis_{task_id}.mp4"
    )


@app.get("/videos")
async def list_videos(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Liste les vidéos de l'utilisateur"""
    if skip < 0:
        skip = 0
    if limit < 1:
        limit = 10
    if limit > 100:
        limit = 100

    videos = db.query(Video).filter(
        Video.user_id == current_user.id
    ).order_by(Video.uploaded_at.desc()).offset(skip).limit(limit).all()

    return [video.to_dict() for video in videos]


@app.delete("/videos/{task_id}")
async def delete_video(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Supprime une vidéo"""
    if not validate_uuid(task_id):
        raise HTTPException(400, "Invalid task ID format")

    video = db.query(Video).filter(
        Video.task_id == task_id,
        Video.user_id == current_user.id
    ).first()

    if not video:
        raise HTTPException(404, "Video not found")

    # Suppression des fichiers
    try:
        if video.storage_path and Path(video.storage_path).exists():
            Path(video.storage_path).unlink()
        if video.output_path and Path(video.output_path).exists():
            Path(video.output_path).unlink()
    except Exception as e:
        logger.warning(f"Error deleting files: {e}")

    db.delete(video)
    db.commit()

    logger.info(f"Video deleted: {task_id} by user {current_user.username}")

    return {"message": "Video deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
