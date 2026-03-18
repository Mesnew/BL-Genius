# 🚀 Guide de Déploiement - BL Genius

Ce guide est destiné au **collègue réseau** pour déployer l'application sur les VMs Proxmox.

---

## 📋 Prérequis

### VMs à créer dans Proxmox

| VM | Rôle | Spécifications | IP suggérée |
|----|------|----------------|-------------|
| **bl-genius-app** | Application complète (Docker) | 8 vCPU / 16 GB RAM / 200 GB SSD | 192.168.1.100 |

> **Note** : Ce déploiement utilise une seule VM avec Docker Compose. Pour la production avec haute disponibilité, voir la section "Architecture Multi-VM".

### Ports à ouvrir

- **80** : HTTP (redirection vers HTTPS)
- **443** : HTTPS (application web)
- **8000** : API FastAPI (optionnel, via Nginx)

---

## 🔧 Installation sur la VM

### 1. Préparation de la VM

```bash
# Se connecter en SSH à la VM
ssh user@192.168.1.100

# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances
sudo apt install -y curl git
```

### 2. Installation de Docker

```bash
# Script d'installation Docker officiel
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER
newgrp docker

# Vérification
docker --version
docker compose version
```

### 3. Déploiement de l'application

```bash
# Créer le répertoire de l'application
mkdir -p /opt/bl-genius
cd /opt/bl-genius

# Copier les fichiers du projet (via git clone ou SCP)
git clone https://votre-repo/bl-genius.git .
# OU
cp -r /chemin/vers/les/fichiers/* .

# Créer le fichier .env
cp .env.example .env
nano .env  # Modifier les valeurs
```

### 4. Configuration du fichier .env

```bash
# Éditer le fichier .env
sudo nano /opt/bl-genius/.env
```

**Valeurs à modifier impérativement :**

```env
# Mot de passe PostgreSQL (changer !)
POSTGRES_PASSWORD=votre_mot_de_passe_tres_securise

# Clé secrète (générer une nouvelle)
SECRET_KEY=$(openssl rand -base64 32)

# Chemins de stockage (adapter si besoin)
VIDEO_STORAGE_PATH=/opt/bl-genius/data/videos
MODEL_STORAGE_PATH=/opt/bl-genius/models
```

### 5. Création des répertoires de stockage

```bash
# Créer les répertoires
sudo mkdir -p /opt/bl-genius/data/videos/uploads
sudo mkdir -p /opt/bl-genius/data/videos/processed
sudo mkdir -p /opt/bl-genius/models

# Permissions
sudo chown -R $USER:$USER /opt/bl-genius/data

# Copier les modèles YLO (si présents localement)
cp /chemin/vers/yolov8m.pt /opt/bl-genius/models/
cp /chemin/vers/best.pt /opt/bl-genius/models/  # Si modèle fine-tuné
```

### 6. Lancement des services

```bash
cd /opt/bl-genius

# Télécharger les images et construire
docker compose pull
docker compose build

# Lancement en arrière-plan
docker compose up -d

# Vérification des logs
docker compose logs -f
```

### 7. Vérification du déploiement

```bash
# Vérifier que tous les conteneurs sont UP
docker compose ps

# Test de l'API
curl http://localhost:8000/health

# Test de la base de données
docker compose exec postgres pg_isready -U blgenius

# Test Redis
docker compose exec redis redis-cli ping
```

---

## 🌐 Configuration DNS et SSL

### Option 1 : Let's Encrypt (Recommandé)

```bash
# Installer Certbot
sudo apt install -y certbot

# Générer le certificat
sudo certbot certonly --standalone -d bl-genius.votredomaine.com

# Copier les certificats
cp /etc/letsencrypt/live/bl-genius.votredomaine.com/fullchain.pem /opt/bl-genius/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/bl-genius.votredomaine.com/privkey.pem /opt/bl-genius/nginx/ssl/key.pem

# Redémarrer Nginx
docker compose restart nginx
```

### Option 2 : Certificat auto-signé (Test uniquement)

```bash
# Créer les certificats auto-signés
mkdir -p /opt/bl-genius/nginx/ssl
cd /opt/bl-genius/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout key.pem -out cert.pem \
    -subj "/C=FR/ST=State/L=City/O=Organization/CN=bl-genius.local"

# Redémarrer Nginx
docker compose restart nginx
```

---

## 📊 Commandes de gestion

### Voir les logs

```bash
# Tous les services
docker compose logs -f

# Service spécifique
docker compose logs -f backend
docker compose logs -f celery-worker
docker compose logs -f postgres
```

### Redémarrer un service

```bash
docker compose restart backend
docker compose restart celery-worker
```

### Mise à jour de l'application

```bash
cd /opt/bl-genius

# Pull des dernières versions
git pull

# Rebuild et redémarrage
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Backup de la base de données

```bash
# Backup
docker compose exec postgres pg_dump -U blgenius blgenius > backup_$(date +%Y%m%d).sql

# Restore
docker compose exec -T postgres psql -U blgenius blgenius < backup_20240101.sql
```

### Nettoyage des vieilles vidéos

```bash
# Supprimer les vidéos de plus de 7 jours
find /opt/bl-genius/data/videos/processed -name "*.mp4" -mtime +7 -delete
```

---

## 🔍 Dépannage

### Problème : Le worker Celery ne démarre pas

```bash
# Vérifier les logs
docker compose logs celery-worker

# Redémarrer le worker
docker compose restart celery-worker
```

### Problème : La base de données ne répond pas

```bash
# Vérifier PostgreSQL
docker compose exec postgres pg_isready -U blgenius

# Si nécessaire, réinitialiser
docker compose down -v  # ATTENTION: supprime les données !
docker compose up -d
```

### Problème : "No space left on device"

```bash
# Nettoyer Docker
docker system prune -a

# Vérifier l'espace disque
df -h
```

### Problème : Les vidéos ne s'affichent pas

```bash
# Vérifier les permissions
ls -la /opt/bl-genius/data/videos/

# Corriger si nécessaire
sudo chown -R 1000:1000 /opt/bl-genius/data/videos
```

---

## 🏗️ Architecture Multi-VM (Production)

Pour une architecture distribuée avec plusieurs VMs :

```
┌─────────────────────────────────────────────────────────────┐
│                    PROXMOX CLUSTER                          │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  WEB-01     │  │  AI-01      │  │  DB-01      │         │
│  │  (Docker)   │  │  (Docker)   │  │  (Docker)   │         │
│  │             │  │             │  │             │         │
│  │ • Frontend  │  │ • Celery    │  │ • PostgreSQL│         │
│  │ • Backend   │  │ • YOLO      │  │ • Redis     │         │
│  │ • Nginx     │  │             │  │             │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │               │
│         └────────────────┼────────────────┘               │
│                          │                                 │
│                   ┌──────┴──────┐                         │
│                   │  NFS Server │                         │
│                   │  (Videos)   │                         │
│                   └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### Configuration pour Multi-VM

**Sur DB-01 (192.168.1.30) :**
```yaml
# docker-compose.db.yml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

**Sur AI-01 (192.168.1.20) :**
```yaml
# docker-compose.worker.yml
version: '3.8'
services:
  celery-worker:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://user:pass@192.168.1.30:5432/blgenius
      - REDIS_URL=redis://192.168.1.30:6379/0
```

**Sur WEB-01 (192.168.1.10) :**
```yaml
# docker-compose.web.yml
version: '3.8'
services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://user:pass@192.168.1.30:5432/blgenius
      - REDIS_URL=redis://192.168.1.30:6379/0
```

---

## 📞 Support

En cas de problème :

1. Vérifier les logs : `docker compose logs -f`
2. Vérifier l'espace disque : `df -h`
3. Vérifier la mémoire : `free -h`
4. Redémarrer les services : `docker compose restart`

---

## ✅ Checklist de validation

- [ ] Docker installé et fonctionnel
- [ ] Fichier `.env` configuré
- [ ] Répertoires de stockage créés
- [ ] Modèles YOLO copiés
- [ ] `docker compose up -d` exécuté sans erreur
- [ ] `curl http://localhost:8000/health` retourne "healthy"
- [ ] Interface web accessible sur https://IP_VM
- [ ] Upload d'une vidéo test fonctionnel
- [ ] Analyse complète d'une vidéo test réussie
