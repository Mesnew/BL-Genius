# BL Genius - Deploiement Proxmox

## Pre-requis

VM Proxmox (Ubuntu 22.04 ou Debian 12) :
- **CPU** : 4+ vCPU
- **RAM** : 8 GB minimum (16 GB recommande pour l'inference YOLO)
- **Disque** : 50 GB SSD

## 1. Installer Docker

```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Docker Compose plugin
sudo apt install docker-compose-plugin -y
```

## 2. Cloner le projet

```bash
cd /opt
git clone https://github.com/Mesnew/BL-Genius.git bl-genius
cd bl-genius
```

## 3. Configurer l'environnement

```bash
cp .env.example .env
nano .env
```

Modifier dans `.env` :

```env
# Generer une cle secrete
SECRET_KEY=<resultat de: openssl rand -hex 32>

# Mot de passe PostgreSQL
POSTGRES_PASSWORD=<mot_de_passe_fort>
DATABASE_URL=postgresql://blgenius:<mot_de_passe_fort>@postgres:5432/blgenius

# IP ou domaine du serveur (remplacer localhost)
ALLOWED_ORIGINS=http://<IP_SERVEUR>:3000
NEXT_PUBLIC_API_URL=http://<IP_SERVEUR>:8000
NEXT_PUBLIC_WS_URL=ws://<IP_SERVEUR>:8000
```

## 4. Creer les dossiers

```bash
mkdir -p data/videos/uploads data/videos/processed models
```

## 5. Build et lancement

```bash
docker compose build --no-cache
docker compose up -d
```

Verifier que tout tourne :

```bash
docker compose ps
# 5 services doivent etre UP : postgres, redis, backend, celery, frontend

curl http://localhost:8000/health
# {"status":"healthy","database":"connected",...}
```

## 6. Firewall

```bash
sudo ufw allow 3000/tcp   # Frontend
sudo ufw allow 8000/tcp   # API (optionnel, si acces direct)
sudo ufw enable
```

## 7. Commandes utiles

```bash
# Voir les logs
docker compose logs -f backend
docker compose logs -f celery

# Redemarrer un service
docker compose restart backend

# Tout arreter
docker compose down

# Tout arreter + supprimer les donnees
docker compose down -v

# Mettre a jour
cd /opt/bl-genius
git pull
docker compose build --no-cache
docker compose up -d
```

## Architecture

```
Navigateur :3000 --> Frontend (Next.js)
                         |
                         v
                    Backend :8000 (FastAPI)
                    /           \
              PostgreSQL      Redis
               :5432          :6379
                                |
                           Celery Worker
                          (YOLO inference)
```

## Ports

| Service    | Port | Usage              |
|------------|------|--------------------|
| Frontend   | 3000 | Interface web      |
| Backend    | 8000 | API REST + WebSocket |
| PostgreSQL | 5432 | Base de donnees    |
| Redis      | 6379 | File de taches     |
