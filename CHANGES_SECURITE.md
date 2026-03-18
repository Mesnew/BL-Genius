# ============================================
# MODIFICATIONS DE SÉCURITÉ EFFECTUÉES
# ============================================

## ✅ Fichiers modifiés

### 1. backend/requirements.txt
**Ajout des dépendances de sécurité :**
- python-jose[cryptography] - JWT tokens
- passlib[bcrypt] - Hashage mots de passe
- python-magic - Validation MIME type
- slowapi - Rate limiting
- email-validator - Validation emails
- bcrypt - Hashage sécurisé
- cryptography - Tokens sécurisés

### 2. backend/main.py
**Remplacé par version sécurisée avec :**
- ✅ Authentification JWT (/auth/register, /auth/login, /auth/me)
- ✅ Rate limiting (5 uploads/min, 10 analyses/heure)
- ✅ CORS restrictif (pas de "*")
- ✅ Validation UUID pour task_id
- ✅ Sanitization des noms de fichiers
- ✅ Limite de taille des fichiers (500 MB)
- ✅ Gestion des erreurs sans exposition interne
- ✅ Vérification ownership des vidéos (user_id)
- ✅ Headers de sécurité
- ✅ Logging des événements de sécurité

### 3. docker-compose.yml
**Ajout des variables d'environnement :**
- SECRET_KEY
- ALLOWED_ORIGINS
- MAX_FILE_SIZE_MB
- ENVIRONMENT
- DEBUG

### 4. backend/app/auth.py (créé)
Module d'authentification complet avec JWT

### 5. backend/app/validators.py (créé)
Validation sécurisée des entrées

### 6. backend/app/security_middleware.py (créé)
Middlewares de sécurité (headers, audit)

---

## 🔐 Nouvelles routes d'authentification

```
POST /auth/register    - Inscription (limitée à 5/heure)
POST /auth/login       - Connexion (limitée à 10/minute)
GET  /auth/me          - Infos utilisateur connecté
```

## 🔒 Routes protégées (nécessitent token JWT)

```
POST /upload           - Upload vidéo
POST /youtube          - Téléchargement YouTube
POST /analyze/{id}     - Lancer analyse
GET  /status/{id}      - Voir statut
GET  /download/{id}    - Télécharger résultat
GET  /videos           - Liste des vidéos
DELETE /videos/{id}    - Supprimer vidéo
```

---

## 🚀 Pour déployer les modifications

### 1. Rebuild les images Docker
```bash
cd /opt/bl-genius
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 2. Mettre à jour le fichier .env
```bash
# Générer une clé secrète forte
openssl rand -hex 32

# Éditer .env
nano .env
```

**Variables à configurer :**
```env
SECRET_KEY=votre_cle_generee_ci_dessus
ALLOWED_ORIGINS=http://localhost:3000,https://votredomaine.com
MAX_FILE_SIZE_MB=500
ENVIRONMENT=production
DEBUG=false
```

### 3. Tester l'authentification
```bash
# Inscription
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"testuser","password":"password123"}'

# Connexion
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# Upload avec token
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -F "file=@video.mp4"
```

---

## ⚠️ Changements breaking

**Avant :** Les routes étaient ouvertes à tous
**Après :** Toutes les routes nécessitent un token JWT

**Le frontend doit être mis à jour pour :**
1. Stocker le token après login
2. Envoyer le token dans le header `Authorization: Bearer TOKEN`
3. Gérer les erreurs 401 (non authentifié)

---

## 📋 Checklist de validation

- [ ] `docker compose up -d` démarre sans erreur
- [ ] `curl http://localhost:8000/health` retourne healthy
- [ ] Inscription fonctionne (`POST /auth/register`)
- [ ] Connexion fonctionne (`POST /auth/login`)
- [ ] Upload sans token retourne 401
- [ ] Upload avec token fonctionne
- [ ] Les vidéos sont isolées par utilisateur
- [ ] Rate limiting fonctionne (trop de requêtes = 429)

---

## 🔒 Sécurité renforcée

| Vulnérabilité | Avant | Après |
|--------------|-------|-------|
| Authentification | ❌ Aucune | ✅ JWT obligatoire |
| CORS | ❌ Origins "*" | ✅ Origins configurées |
| Rate limiting | ❌ Aucun | ✅ Par IP et par user |
| Upload | ❌ Extension seule | ✅ Extension + taille |
| Erreurs | ❌ Détails exposés | ✅ Messages génériques |
| Ownership | ❌ Toutes les vidéos visibles | ✅ Isolation par user |

---

## 📞 En cas de problème

Si l'application ne démarre pas :
```bash
# Voir les logs
docker compose logs backend

# Vérifier les variables d'environnement
docker compose exec backend env | grep SECRET

# Redémarrer
docker compose restart backend
```
