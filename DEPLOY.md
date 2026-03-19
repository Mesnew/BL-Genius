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

## 6. Acceder a l'application

Apres le demarrage des conteneurs, accedez au frontend :

```
http://<IP_SERVEUR>:3000
```

**Important** : Le frontend est servi en mode production (Next.js standalone). Les modifications du code source ne sont PAS prises en compte automatiquement. Pour modifier le frontend, il faut rebuild :

```bash
docker compose build --no-cache frontend
docker compose up -d frontend
```

## 7. Firewall

```bash
sudo ufw allow 3000/tcp   # Frontend
sudo ufw allow 8000/tcp   # API (optionnel, si acces direct)
sudo ufw enable
```

## 8. Commandes utiles

```bash
# Voir les logs
docker compose logs -f backend
docker compose logs -f celery
docker compose logs -f frontend  # Logs du frontend

# Redemarrer un service
docker compose restart backend
docker compose restart frontend

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

## 9. Troubleshooting

### Le frontend n'est pas accessible (port 3000)

1. **Verifier que le conteneur tourne** :
   ```bash
   docker compose ps
   # Doit afficher "frontend" avec status "Up"
   ```

2. **Verifier les logs** :
   ```bash
   docker compose logs frontend
   ```

3. **Verifier le firewall** :
   ```bash
   sudo ufw status
   # Doit afficher "3000/tcp ALLOW"
   ```

4. **Verifier que NEXT_PUBLIC_API_URL est bien defini** dans le `.env` :
   ```env
   NEXT_PUBLIC_API_URL=http://<IP_SERVEUR>:8000
   ```
   Puis rebuild :
   ```bash
   docker compose build --no-cache frontend
   docker compose up -d frontend
   ```

5. **Si le frontend affiche une erreur 500** :
   C'est souvent car l'API n'est pas accessible. Verifiez :
   ```bash
   curl http://localhost:8000/health
   ```

### Erreur "Cannot connect to backend"

Si le frontend affiche une erreur de connexion au backend :

1. Verifiez que le backend tourne :
   ```bash
   docker compose ps backend
   ```

2. Verifiez que ALLOWED_ORIGINS contient bien l'URL du frontend dans `.env` :
   ```env
   ALLOWED_ORIGINS=http://<IP_SERVEUR>:3000
   ```

3. Redemarrez le backend :
   ```bash
   docker compose restart backend
   ```

## Architecture

```
Navigateur :3000 --> Frontend (Next.js standalone)
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

**Note importante** : Le frontend est build en mode **production standalone** (Docker multi-stage). Cela signifie :
- Le code source n'est PAS monte en volume
- Les modifications necessitent un rebuild
- Le serveur lit uniquement les fichiers dans `.next/standalone/`

## Ports

| Service    | Port | Usage              |
|------------|------|--------------------|
| Frontend   | 3000 | Interface web      |
| Backend    | 8000 | API REST + WebSocket |
| PostgreSQL | 5432 | Base de donnees    |
| Redis      | 6379 | File de taches     |
