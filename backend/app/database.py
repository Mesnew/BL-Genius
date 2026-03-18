# ============================================
# DATABASE CONFIGURATION - BL Genius
# ============================================

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
import logging

logger = logging.getLogger(__name__)

# Récupération de l'URL de la base de données
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://blgenius:changeme@localhost:5432/blgenius'
)

# Configuration du moteur SQLAlchemy
engine_config = {
    'pool_pre_ping': True,  # Vérifie la connexion avant usage
    'pool_recycle': 3600,  # Recycle les connexions après 1h
}

# Pool spécifique pour SQLite (développement)
if DATABASE_URL.startswith('sqlite'):
    engine_config['connect_args'] = {'check_same_thread': False}
    engine_config['poolclass'] = StaticPool

# Création du moteur
engine = create_engine(DATABASE_URL, **engine_config)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()


def get_db():
    """
    Générateur de session de base de données pour FastAPI dependency injection
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialisation de la base de données (création des tables)
    """
    logger.info("🗄️ Initialisation de la base de données...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tables créées avec succès")


def check_db_connection():
    """
    Vérifie que la connexion à la base de données fonctionne

    Returns:
        bool: True si la connexion fonctionne
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"❌ Erreur de connexion à la BDD: {e}")
        return False


# Event listeners pour le debug (optionnel)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Active les foreign keys pour SQLite"""
    if DATABASE_URL.startswith('sqlite'):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
