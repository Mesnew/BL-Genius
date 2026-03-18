# 🔒 Guide de Sécurité - BL Genius

## Analyse des vulnérabilités et corrections

---

## 🚨 Vulnérabilités Critiques à Corriger

### 1. ❌ Aucune Authentification

**Problème :** L'API est complètement ouverte, n'importe qui peut uploader des vidéos.

**Solution :** Implémenter JWT Authentication

```python
# backend/app/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Middleware pour protéger les routes
from functools import wraps

def require_auth(func):
    @wraps(func)
    async def wrapper(*args, current_user: str = Depends(get_current_user), **kwargs):
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper
```

**Routes à protéger :**
```python
@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),  # Ajouter ceci
    db: Session = Depends(get_db)
):
    # Vérifier que l'utilisateur est authentifié
    ...
```

---

### 2. ❌ CORS Trop Permissif

**Problème actuel :**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🚨 Trop dangereux !
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Correction :**
```python
from fastapi.middleware.cors import CORSMiddleware
import os

# Origines autorisées (configurer via variable d'environnement)
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Pas "*"
    allow_headers=["Authorization", "Content-Type"],  # Pas "*"
    expose_headers=["X-Request-ID"],
    max_age=600,
)
```

---

### 3. ❌ Upload de Fichiers Non Sécurisé

**Problèmes :**
- Pas de limite de taille
- Pas de vérification du contenu réel (seulement l'extension)
- Pas de scan antivirus
- Nom de fichier non sécurisé

**Correction :**
```python
import magic  # python-magic
from fastapi import UploadFile, HTTPException
import uuid
import os

# Configuration
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
ALLOWED_MIME_TYPES = {
    'video/mp4': '.mp4',
    'video/x-msvideo': '.avi',
    'video/quicktime': '.mov',
    'video/x-matroska': '.mkv',
}

async def validate_video_file(file: UploadFile) -> tuple:
    """
    Valide un fichier vidéo uploadé
    """
    # Vérifier la taille
    file_size = 0
    contents = await file.read()
    file_size = len(contents)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(413, f"Fichier trop grand. Max: {MAX_FILE_SIZE / 1024 / 1024}MB")

    if file_size == 0:
        raise HTTPException(400, "Fichier vide")

    # Vérifier le type MIME réel (pas juste l'extension)
    mime_type = magic.from_buffer(contents, mime=True)

    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(415, f"Type de fichier non supporté: {mime_type}")

    # Vérifier l'extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    expected_ext = ALLOWED_MIME_TYPES[mime_type]

    if file_ext != expected_ext:
        raise HTTPException(400, f"Extension {file_ext} ne correspond pas au type {mime_type}")

    # Générer un nom de fichier sécurisé (UUID)
    safe_filename = f"{uuid.uuid4()}{expected_ext}"

    return contents, safe_filename, mime_type

# Utilisation dans la route
@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validation sécurisée
    contents, safe_filename, mime_type = await validate_video_file(file)

    # Sauvegarde
    file_path = VIDEO_OUTPUT_DIR / 'uploads' / safe_filename
    with open(file_path, "wb") as f:
        f.write(contents)

    ...
```

**requirements.txt additionnel :**
```
python-magic==0.4.27
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

---

### 4. ❌ Pas de Rate Limiting

**Problème :** N'importe qui peut spammer l'API.

**Solution :** Implémenter SlowAPI

```python
# backend/app/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

# Dans main.py
from app.rate_limit import limiter, RateLimitExceeded

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Utilisation
@app.post("/upload")
@limiter.limit("5/minute")  # Max 5 uploads par minute par IP
async def upload_video(request: Request, ...):
    ...

@app.post("/analyze/{task_id}")
@limiter.limit("10/hour")  # Max 10 analyses par heure
async def analyze_video(request: Request, ...):
    ...
```

**requirements.txt :**
```
slowapi==0.1.9
```

---

### 5. ❌ Injection SQL Possible

**Problème :** Bien que SQLAlchemy protège, il faut vérifier toutes les requêtes brutes.

**Vérification :**
```python
# ❌ DANGEREUX - Ne jamais faire ça
db.execute(f"SELECT * FROM videos WHERE task_id = '{task_id}'")

# ✅ SÉCURISÉ - Utiliser des paramètres
db.execute("SELECT * FROM videos WHERE task_id = %s", (task_id,))

# ✅ ENCORE MIEUX - Utiliser ORM
db.query(Video).filter(Video.task_id == task_id).first()
```

---

### 6. ❌ Pas de Validation des Entrées

**Problème :** Les paramètres d'URL ne sont pas validés.

**Solution :**
```python
from pydantic import BaseModel, Field, validator
import re

class TaskIdRequest(BaseModel):
    task_id: str = Field(..., min_length=36, max_length=36)

    @validator('task_id')
    def validate_uuid(cls, v):
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', v):
            raise ValueError('Invalid UUID format')
        return v

@app.get("/status/{task_id}")
async def get_status(
    task_id: str,  # FastAPI valide automatiquement avec Pydantic
    db: Session = Depends(get_db)
):
    # Validation supplémentaire
    if not re.match(r'^[0-9a-f-]{36}$', task_id):
        raise HTTPException(400, "Invalid task ID format")
    ...
```

---

### 7. ❌ Exposition d'Informations Sensibles

**Problème :** Les erreurs exposent des détails internes.

**Solution :**
```python
# backend/app/exceptions.py
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """Handler global pour masquer les erreurs internes"""

    # Logger l'erreur complète (côté serveur)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Retourner un message générique (côté client)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred"}
    )

# Dans main.py
from app.exceptions import global_exception_handler

app.add_exception_handler(Exception, global_exception_handler)
```

**Ne jamais faire :**
```python
# ❌ Expose les détails de la BDD
except Exception as e:
    raise HTTPException(500, f"Database error: {str(e)}")  # NON !

# ✅ Message générique
except Exception as e:
    logger.error(f"Database error: {e}")  # Log côté serveur
    raise HTTPException(500, "Internal server error")  # Message client
```

---

### 8. ❌ Pas de Headers de Sécurité

**Solution :** Ajouter des middlewares de sécurité

```python
# backend/app/security_headers.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Protection XSS
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # CSP (Content Security Policy)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "media-src 'self' blob:; "
            "connect-src 'self' ws: wss:;"
        )

        # HSTS (forcer HTTPS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        return response

# Dans main.py
from app.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

---

### 9. ❌ Secrets en Clair

**Problème :** Le SECRET_KEY est en dur dans le code.

**Vérification .env :**
```bash
# .env - À ne JAMAIS commiter
git update-index --skip-worktree .env  # Ignorer les changements locaux

# Ou ajouter dans .gitignore
# .env
# *.pem
# *.key
```

**Génération de secrets :**
```bash
# Générer une clé sécurisée
openssl rand -hex 32

# Générer pour JWT
openssl rand -base64 32
```

---

### 10. ❌ Pas de Logging de Sécurité

**Implémenter l'audit log :**
```python
# backend/app/audit.py
import logging
from datetime import datetime
from fastapi import Request

audit_logger = logging.getLogger("audit")

def log_security_event(event_type: str, request: Request, details: dict = None):
    """Log les événements de sécurité"""
    audit_logger.info({
        "timestamp": datetime.utcnow().isoformat(),
        "event": event_type,
        "ip": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "path": request.url.path,
        "details": details or {}
    })

# Utilisation
@app.post("/upload")
async def upload_video(request: Request, ...):
    log_security_event("FILE_UPLOAD", request, {"filename": file.filename, "size": file_size})
    ...
```

---

## 🔐 Configuration HTTPS Obligatoire

### Nginx avec SSL

```nginx
# nginx/nginx.conf (extrait SSL)
server {
    listen 443 ssl http2;

    # Certificats
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Configuration SSL sécurisée
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000" always;
}
```

---

## 📋 Checklist Sécurité

### Avant mise en production

- [ ] **Authentification JWT** implémentée
- [ ] **CORS** restreint aux domaines autorisés
- [ ] **Rate limiting** activé (5 req/min pour upload)
- [ ] **Validation des fichiers** par MIME type (pas juste extension)
- [ ] **Limite de taille** des fichiers (500 MB max)
- [ ] **Headers de sécurité** (CSP, HSTS, X-Frame-Options)
- [ ] **HTTPS obligatoire** (redirection 301)
- [ ] **Secrets** dans .env (pas dans le code)
- [ ] **Logging** des événements de sécurité
- [ ] **Gestion des erreurs** sans exposition d'infos internes
- [ ] **Dépendances** à jour (`pip audit`)
- [ ] **Container** non-root (USER dans Dockerfile)

### Commandes de vérification

```bash
# Vérifier les dépendances vulnérables
pip install safety
safety check

# Ou
pip install pip-audit
pip-audit

# Scanner les secrets dans le code
git-secrets --scan

# Test de pénétration basique
nmap -sV your-domain.com
```

---

## 🛡️ Fichiers à Créer

### Structure des fichiers sécurité

```
backend/
├── app/
│   ├── __init__.py
│   ├── auth.py              # JWT Authentication
│   ├── rate_limit.py        # Rate limiting
│   ├── security_headers.py  # Security headers
│   ├── audit.py             # Audit logging
│   └── exceptions.py        # Global exception handler
```

---

## 🚨 Priorités

### 🔴 Critique (à faire immédiatement)
1. **Authentification** - L'API est ouverte à tout le monde
2. **CORS** - Origins trop permissives
3. **Validation des uploads** - Vérifier le type MIME réel

### 🟠 Important (à faire cette semaine)
4. **Rate limiting** - Protéger contre le spam
5. **Headers de sécurité** - CSP, HSTS
6. **HTTPS obligatoire** - Redirection 80→443

### 🟡 Recommandé (à faire bientôt)
7. **Audit logging** - Tracer les actions
8. **Scan de dépendances** - Vérifier les vulnérabilités
9. **Tests de sécurité** - OWASP ZAP, etc.

---

## 📚 Ressources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Mozilla SSL Configuration](https://ssl-config.mozilla.org/)
