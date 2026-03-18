# 📖 Guide d'Utilisation - BL Genius (Sécurisé)

## 🚀 Comment déployer

### Étape 1 : Préparer le serveur

```bash
# Se connecter au serveur
ssh user@192.168.1.100

# Aller dans le dossier de l'application
cd /opt/bl-genius
```

### Étape 2 : Lancer le déploiement

```bash
# Rendre le script exécutable (si besoin)
chmod +x deploy.sh

# Lancer le déploiement
./deploy.sh
```

**Ce que fait le script :**
1. ✅ Vérifie que Docker est installé
2. ✅ Vérifie le fichier `.env`
3. ✅ Génère une clé secrète si nécessaire
4. ✅ Crée les répertoires de stockage
5. ✅ Construit les images Docker
6. ✅ Démarre tous les services
7. ✅ Vérifie que tout fonctionne

### Étape 3 : Vérifier le déploiement

```bash
# Voir les conteneurs en cours
docker-compose ps

# Voir les logs
docker-compose logs -f

# Test de santé
curl http://localhost:8000/health
```

---

## 🔐 Comment fonctionne l'authentification

### Architecture de sécurité

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   Nginx     │────▶│  FastAPI    │
│  (Browser)  │     │  (Proxy)    │     │   (API)     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                          ┌────────────────────┼────────────────────┐
                          │                    │                    │
                          ▼                    ▼                    ▼
                   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
                   │  PostgreSQL │      │    Redis    │      │   Celery    │
                   │  (Users)    │      │   (Tokens)  │      │   (Worker)  │
                   └─────────────┘      └─────────────┘      └─────────────┘
```

### Flux d'authentification

```
1. INSCRIPTION
   Client ──POST /auth/register──▶ API
   Body: {email, username, password}

   API ──Hash password──▶ PostgreSQL
   API ──Génère JWT──▶ Client

   Response: {access_token, token_type: "bearer"}

2. CONNEXION
   Client ──POST /auth/login──▶ API
   Body: {username, password}

   API ──Vérifie hash──▶ PostgreSQL
   API ──Génère JWT──▶ Client

3. REQUÊTE PROTÉGÉE
   Client ──GET /videos──▶ API
   Header: Authorization: Bearer TOKEN

   API ──Vérifie JWT──▶ PostgreSQL
   API ──Filtre par user_id──▶ PostgreSQL
   API ──Résultat──▶ Client
```

---

## 📝 Comment utiliser l'API

### 1. Inscription (Première fois)

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "monuser",
    "password": "monmotdepasse123"
  }'
```

**Réponse :**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### 2. Connexion

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "monuser",
    "password": "monmotdepasse123"
  }'
```

### 3. Upload une vidéo

```bash
# Stocker le token dans une variable
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Upload
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/chemin/vers/video.mp4"
```

**Réponse :**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "uploaded",
  "progress": 0,
  "message": "Video uploaded successfully"
}
```

### 4. Lancer l'analyse

```bash
curl -X POST http://localhost:8000/analyze/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse :**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "processing",
  "progress": 0,
  "message": "Analysis started"
}
```

### 5. Vérifier le statut

```bash
curl http://localhost:8000/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse :**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "progress": 100,
  "analysis_result": {
    "total_frames": 7500,
    "total_players": 22,
    "possession_team1": 52.3,
    "possession_team2": 47.7
  }
}
```

### 6. Télécharger le résultat

```bash
curl -O http://localhost:8000/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Authorization: Bearer $TOKEN"
```

### 7. Lister mes vidéos

```bash
curl http://localhost:8000/videos \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🛡️ Sécurités en place

### 1. Authentification JWT
- Token signé avec SECRET_KEY
- Expiration après 24h
- Vérifié sur chaque requête protégée

### 2. Rate Limiting
| Route | Limite |
|-------|--------|
| `/auth/register` | 5/heure |
| `/auth/login` | 10/minute |
| `/upload` | 5/minute |
| `/analyze` | 10/heure |

### 3. Validation des entrées
- UUID vérifié pour task_id
- Extensions de fichiers limitées (.mp4, .avi, .mov, .mkv, .webm)
- Taille max: 500 MB
- Noms de fichiers nettoyés (UUID généré)

### 4. Isolation des données
- Chaque utilisateur ne voit que SES vidéos
- Vérification user_id sur chaque requête
- Pas d'accès aux vidéos des autres utilisateurs

### 5. Headers de sécurité
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy` configuré
- `Strict-Transport-Security` (HSTS)

---

## 🔧 Gestion des erreurs

### Erreurs courantes

| Code | Signification | Solution |
|------|---------------|----------|
| 400 | Requête invalide | Vérifier les paramètres |
| 401 | Non authentifié | Se reconnecter, token invalide |
| 403 | Accès interdit | Compte désactivé |
| 404 | Ressource non trouvée | Vérifier le task_id |
| 413 | Fichier trop grand | Réduire la taille (< 500 MB) |
| 415 | Format non supporté | Utiliser MP4, AVI, MOV, MKV |
| 429 | Trop de requêtes | Attendre avant de réessayer |
| 500 | Erreur serveur | Contacter l'administrateur |

### Exemple d'erreur 401
```json
{
  "detail": "Could not validate credentials"
}
```
**Solution :** Renouveler le token avec `/auth/login`

### Exemple d'erreur 429
```json
{
  "detail": "Rate limit exceeded"
}
```
**Solution :** Attendre 1 minute avant de réessayer

---

## 📊 Monitoring

### Voir les logs en temps réel
```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f backend
docker-compose logs -f celery-worker
docker-compose logs -f postgres
```

### Statistiques Docker
```bash
# Utilisation des ressources
docker stats

# Espace disque
df -h

# Mémoire
free -h
```

### Health checks
```bash
# API
curl http://localhost:8000/health

# PostgreSQL
docker-compose exec postgres pg_isready -U blgenius

# Redis
docker-compose exec redis redis-cli ping
```

---

## 🔄 Cycle de vie d'une vidéo

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  UPLOAD  │───▶│  QUEUED  │───▶│PROCESSING│───▶│COMPLETED │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
      │                                              │
      │         ┌──────────┐                        │
      └────────▶│  ERROR   │◀───────────────────────┘
                └──────────┘
```

### États possibles
- `uploaded` : Vidéo uploadée, en attente d'analyse
- `processing` : Analyse en cours par Celery
- `completed` : Analyse terminée, résultat disponible
- `error` : Une erreur s'est produite

---

## 💾 Backup et restauration

### Backup de la base de données
```bash
# Backup
docker-compose exec postgres pg_dump -U blgenius blgenius > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup avec compression
docker-compose exec postgres pg_dump -U blgenius blgenius | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restauration
```bash
# Restaurer
docker-compose exec -T postgres psql -U blgenius blgenius < backup_20240318.sql
```

### Backup des vidéos
```bash
# Compresser les vidéos
tar -czf videos_backup_$(date +%Y%m%d).tar.gz data/videos/

# Sync vers un autre serveur
rsync -avz data/videos/ user@backup-server:/backups/bl-genius/
```

---

## 🆘 Dépannage

### Problème : "Could not validate credentials"
**Cause :** Token JWT invalide ou expiré
**Solution :**
```bash
# Se reconnecter
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"monuser","password":"monmotdepasse123"}'
```

### Problème : "Rate limit exceeded"
**Cause :** Trop de requêtes en peu de temps
**Solution :** Attendre 1 minute avant de réessayer

### Problème : "Database connection failed"
**Cause :** PostgreSQL n'est pas prêt
**Solution :**
```bash
# Vérifier PostgreSQL
docker-compose logs postgres

# Redémarrer
docker-compose restart postgres
```

### Problème : Le worker ne traite pas les vidéos
**Cause :** Celery worker arrêté ou erreur
**Solution :**
```bash
# Voir les logs
docker-compose logs celery-worker

# Redémarrer
docker-compose restart celery-worker
```

---

## 📞 Support

En cas de problème :
1. Vérifier les logs : `docker-compose logs -f`
2. Vérifier l'espace disque : `df -h`
3. Redémarrer les services : `docker-compose restart`
4. Contacter l'administrateur système

---

## ✅ Checklist post-déploiement

- [ ] Déploiement terminé sans erreur
- [ ] `curl http://localhost:8000/health` retourne "healthy"
- [ ] Inscription fonctionne (`POST /auth/register`)
- [ ] Connexion fonctionne (`POST /auth/login`)
- [ ] Upload avec token fonctionne
- [ ] Analyse d'une vidéo fonctionne
- [ ] Téléchargement du résultat fonctionne
- [ ] Les vidéos sont isolées par utilisateur
- [ ] Les logs montrent les accès (audit)
