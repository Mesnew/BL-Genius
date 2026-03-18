# ============================================
# BL GENIUS - BACKEND API (FastAPI)
# ============================================

FROM python:3.11-slim

# Éviter les buffers Python pour les logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Pour OpenCV
    libgl1 \
    libglvnd0 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Pour PostgreSQL
    libpq-dev \
    gcc \
    # Utilitaires
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des requirements en premier (pour le cache Docker)
COPY requirements.txt requirements.txt
COPY requirements.db.txt requirements.db.txt

# Installation des dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements.db.txt

# Création des répertoires nécessaires
RUN mkdir -p /app/data/videos/uploads /app/data/videos/processed /app/models

# Copie du code source
COPY . .

# Création d'un utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Exposition du port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
