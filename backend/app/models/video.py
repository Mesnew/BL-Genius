# ============================================
# VIDEO MODEL - BL Genius
# ============================================

from sqlalchemy import Column, String, Integer, DateTime, JSON, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime


class Video(Base):
    """
    Modèle de données pour les vidéos uploadées et analysées
    """
    __tablename__ = "videos"

    # Clé primaire UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identification
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    original_name = Column(String(500), nullable=False)

    # Chemins de stockage
    storage_path = Column(String(1000), nullable=False)  # Chemin vidéo originale
    output_path = Column(String(1000))                     # Chemin vidéo analysée

    # Statut et source
    status = Column(
        String(50),
        default='uploaded',
        nullable=False,
        index=True
    )  # uploaded, processing, completed, error

    source = Column(String(50), default='upload')  # upload, youtube
    youtube_url = Column(String(1000))  # URL YouTube si applicable

    # Métadonnées du fichier
    file_size_mb = Column(Numeric(10, 2))
    duration_sec = Column(Integer)
    resolution = Column(String(50))  # Ex: 1920x1080
    fps = Column(Integer)

    # Résultats de l'analyse (stocké en JSON)
    analysis_result = Column(JSON, default=dict)

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    processing_started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user = relationship("User", back_populates="videos")

    def __repr__(self):
        return f"<Video(id={self.id}, task_id={self.task_id}, status={self.status})>"

    def to_dict(self):
        """Convertit l'objet en dictionnaire pour l'API"""
        return {
            'id': str(self.id),
            'task_id': self.task_id,
            'original_name': self.original_name,
            'storage_path': self.storage_path,
            'output_path': self.output_path,
            'status': self.status,
            'source': self.source,
            'youtube_url': self.youtube_url,
            'file_size_mb': float(self.file_size_mb) if self.file_size_mb else None,
            'duration_sec': self.duration_sec,
            'resolution': self.resolution,
            'fps': self.fps,
            'analysis_result': self.analysis_result or {},
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'processing_started_at': self.processing_started_at.isoformat() if self.processing_started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class User(Base):
    """
    Modèle utilisateur (si authentification implémentée)
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Integer, default=1)
    is_admin = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Relations
    videos = relationship("Video", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
