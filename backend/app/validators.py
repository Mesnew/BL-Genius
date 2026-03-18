# ============================================
# VALIDATORS - BL Genius
# Validation sécurisée des entrées
# ============================================

import re
import uuid
import magic
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException
import os

# Configuration
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "500")) * 1024 * 1024  # 500 MB
ALLOWED_VIDEO_TYPES = {
    'video/mp4': '.mp4',
    'video/x-msvideo': '.avi',
    'video/quicktime': '.mov',
    'video/x-matroska': '.mkv',
    'video/webm': '.webm',
    'video/x-flv': '.flv',
}

# Regex pour validation UUID
UUID_REGEX = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)

# Regex pour noms de fichiers sécurisés
SAFE_FILENAME_REGEX = re.compile(r'^[a-zA-Z0-9._-]+$')


def validate_uuid(task_id: str) -> bool:
    """Valide le format UUID"""
    return bool(UUID_REGEX.match(task_id))


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour éviter les attaques par path traversal
    """
    # Supprimer les caractères dangereux
    filename = re.sub(r'[^\w\s.-]', '', filename)

    # Supprimer les points au début (fichiers cachés)
    filename = filename.lstrip('.')

    # Limiter la longueur
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext

    return filename


def validate_youtube_url(url: str) -> bool:
    """
    Valide qu'une URL est bien une URL YouTube valide
    """
    youtube_regex = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^\s&]+)',
        re.IGNORECASE
    )
    return bool(youtube_regex.match(url))


async def validate_video_file(file: UploadFile) -> Tuple[bytes, str, str]:
    """
    Valide un fichier vidéo uploadé de manière sécurisée

    Returns:
        Tuple[contenu, nom_sécurisé, mime_type]

    Raises:
        HTTPException: Si le fichier est invalide
    """
    # Vérifier que le fichier existe
    if not file.filename:
        raise HTTPException(400, "No file provided")

    # Lire le contenu
    contents = await file.read()

    # Vérifier la taille
    file_size = len(contents)
    if file_size == 0:
        raise HTTPException(400, "Empty file")

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            413,
            f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # Vérifier le type MIME réel (pas juste l'extension)
    mime_type = magic.from_buffer(contents, mime=True)

    if mime_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            415,
            f"Unsupported file type: {mime_type}. Allowed: {', '.join(ALLOWED_VIDEO_TYPES.keys())}"
        )

    # Vérifier l'extension
    original_ext = Path(file.filename).suffix.lower()
    expected_ext = ALLOWED_VIDEO_TYPES[mime_type]

    if original_ext != expected_ext:
        raise HTTPException(
            400,
            f"File extension {original_ext} does not match content type {mime_type}"
        )

    # Générer un nom de fichier sécurisé (UUID)
    safe_filename = f"{uuid.uuid4()}{expected_ext}"

    return contents, safe_filename, mime_type


def validate_task_id(task_id: str) -> str:
    """
    Valide et retourne un task_id sécurisé
    """
    if not task_id:
        raise HTTPException(400, "Task ID is required")

    if not validate_uuid(task_id):
        raise HTTPException(400, "Invalid task ID format")

    return task_id.lower()


def validate_pagination(skip: int, limit: int) -> Tuple[int, int]:
    """
    Valide les paramètres de pagination
    """
    if skip < 0:
        raise HTTPException(400, "Skip must be non-negative")

    if limit < 1:
        raise HTTPException(400, "Limit must be at least 1")

    if limit > 100:
        raise HTTPException(400, "Limit cannot exceed 100")

    return skip, limit


# Liste des extensions dangereuses à bloquer
DANGEROUS_EXTENSIONS = {
    '.exe', '.dll', '.bat', '.cmd', '.sh', '.php', '.jsp', '.asp',
    '.aspx', '.py', '.rb', '.pl', '.cgi', '.jar', '.war', '.ear'
}


def is_dangerous_file(filename: str) -> bool:
    """
    Vérifie si un fichier a une extension dangereuse
    """
    ext = Path(filename).suffix.lower()
    return ext in DANGEROUS_EXTENSIONS
