# ============================================
# BL GENIUS - MAIN API (Version Sécurisée)
# Avec authentification JWT, rate limiting, validation
# ============================================

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends, Request, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import torch
import warnings
from pydantic import BaseModel, EmailStr
import yt_dlp
import logging

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

# Imports sécurisés
from app.database import get_db, init_db, check_db_connection
from app.models.video import Video, User
from app.workers import celery_app, process_video
from app.auth import (
    get_current_user, get_current_active_user, get_password_hash,
    verify_password, create_access_token, Token
)
from app.validators import (
    validate_video_file, validate_task_id, validate_youtube_url,
    validate_pagination, sanitize_filename
)
from app.security_middleware import SecurityHeadersMiddleware, RequestValidationMiddleware, AuditLogMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Création de l'application
app = FastAPI(
    title="BL Genius - Football Analysis API",
    description="API sécurisée pour l'analyse de matchs de football",
    version="1.0.0",
    docs_url="/docs" if os.getenv("DEBUG") == "true" else None,  # Désactiver docs en prod
    redoc_url="/redoc" if os.getenv("DEBUG") == "true" else None
)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middlewares de sécurité
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(AuditLogMiddleware)

# CORS sécurisé
from fastapi.middleware.cors import CORSMiddleware
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# Configuration
VIDEO_OUTPUT_DIR = Path(os.getenv('VIDEO_OUTPUT_DIR', '/app/data/videos'))
VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(VIDEO_OUTPUT_DIR / 'uploads').mkdir(exist_ok=True)
(VIDEO_OUTPUT_DIR / 'processed').mkdir(exist_ok=True)

# ============================================
# MODÈLES PYDANTIC
# ============================================

class YouTubeRequest(BaseModel):
    url: str

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)

class UserLogin(BaseModel):
    username: str
    password: str

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
@limiter.limit("5/hour")  # Limite d'inscription
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

    logger.info(f"User registered: {user.username} ({user.email})")

    # Créer le token
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")  # Protection contre brute force
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
# API PRINCIPALE (Protégée par auth)
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


@app.post("/upload")
@limiter.limit("5/minute")  # Protection contre spam
async def upload_video(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload sécurisé d'une vidéo
    - Validation du type MIME
    - Génération de nom sécurisé (UUID)
    - Limite de taille: 500MB
    """
    try:
        # Validation sécurisée du fichier
        contents, safe_filename, mime_type = await validate_video_file(file)

        # Sauvegarde
        file_path = VIDEO_OUTPUT_DIR / 'uploads' / safe_filename
        with open(file_path, "wb") as f:
            f.write(contents)

        file_size = len(contents) / (1024 * 1024)  # MB

        # Création en BDD avec lien utilisateur
        video = Video(
            task_id=safe_filename.split('.')[0],
            original_name=sanitize_filename(file.filename),
            storage_path=str(file_path),
            status='uploaded',
            file_size_mb=file_size,
            user_id=current_user.id
        )
        db.add(video)
        db.commit()

        logger.info(f"Video uploaded: {video.task_id} by user {current_user.username}")

        return {
            "task_id": video.task_id,
            "status": "uploaded",
            "progress": 0,
            "message": "Video uploaded successfully. Use /analyze/{task_id} to start analysis."
        }

    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(500, "Upload failed")


@app.post("/youtube")
@limiter.limit("5/minute")
async def download_youtube(
    request: Request,
    youtube_req: YouTubeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Téléchargement sécurisé de vidéo YouTube"""
    # Validation de l'URL
    if not validate_youtube_url(youtube_req.url):
        raise HTTPException(400, "Invalid YouTube URL")

    try:
        task_id = str(uuid.uuid4())
        output_template = VIDEO_OUTPUT_DIR / 'uploads' / f"{task_id}_youtube"

        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': str(output_template) + '.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'max_filesize': 500 * 1024 * 1024,  # 500 MB max
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

        logger.info(f"YouTube video downloaded: {task_id} by user {current_user.username}")

        return {
            "task_id": task_id,
            "status": "uploaded",
            "progress": 0,
            "message": f"YouTube video downloaded: {title}"
        }

    except Exception as e:
        logger.error(f"YouTube download error: {e}")
        raise HTTPException(400, f"Download failed: {str(e)}")


@app.post("/analyze/{task_id}")
@limiter.limit("10/hour")  # Limite d'analyses
async def analyze_video(
    request: Request,
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Lance l'analyse d'une vidéo"""
    # Validation du task_id
    task_id = validate_task_id(task_id)

    # Vérifier que la vidéo appartient à l'utilisateur
    video = db.query(Video).filter(
        Video.task_id == task_id,
        Video.user_id == current_user.id
    ).first()

    if not video:
        raise HTTPException(404, "Video not found or access denied")

    if video.status == 'processing':
        return {"task_id": task_id, "status": "processing", "progress": 0}

    if video.status == 'completed':
        return {"task_id": task_id, "status": "completed", "progress": 100}

    # Mise à jour du statut
    video.status = 'processing'
    video.processing_started_at = datetime.utcnow()
    db.commit()

    # Envoi à Celery
    process_video.delay(task_id)

    logger.info(f"Analysis started: {task_id} by user {current_user.username}")

    return {
        "task_id": task_id,
        "status": "processing",
        "progress": 0,
        "message": "Analysis started"
    }


@app.get("/status/{task_id}")
async def get_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère le statut d'une analyse"""
    task_id = validate_task_id(task_id)

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
        "analysis_result": video.analysis_result if video.status == 'completed' else None
    }


@app.get("/download/{task_id}")
async def download_video(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Télécharge une vidéo analysée"""
    task_id = validate_task_id(task_id)

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
    """Liste les vidéos de l'utilisateur connecté"""
    skip, limit = validate_pagination(skip, limit)

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
    task_id = validate_task_id(task_id)

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
