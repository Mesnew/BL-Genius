# Infrastructure - BL Genius

## Réponse rapide : Une seule VM suffit ?

**Oui, une seule VM suffit** pour démarrer, mais les ressources dépendent de l'usage.

---

## 📊 Configuration Recommandée

### Option 1 : Une seule VM (Recommandé pour démarrer)

| Ressource | Minimum | Recommandé | Optimal |
|-----------|---------|------------|---------|
| **CPU** | 4 vCPU | 6-8 vCPU | 8+ vCPU |
| **RAM** | 8 GB | 12-16 GB | 16-32 GB |
| **Disque** | 100 GB SSD | 200 GB SSD | 500 GB SSD |
| **Réseau** | 1 Gbps | 1 Gbps | 1 Gbps |

**Pourquoi autant de ressources ?**

```
Ressources par service :
┌────────────────────────────────────────────────────────┐
│ Service          │ CPU    │ RAM       │ Usage          │
├────────────────────────────────────────────────────────┤
│ PostgreSQL       │ ~5%    │ 500 MB    │ Base de données│
│ Redis            │ ~2%    │ 100 MB    │ File d'attente │
│ FastAPI          │ ~5%    │ 300 MB    │ API Web        │
│ Next.js          │ ~5%    │ 300 MB    │ Frontend       │
│ Nginx            │ ~2%    │ 50 MB     │ Proxy          │
│ Celery + YOLO    │ 80-100%│ 4-8 GB    │ 🎯 IA (GOURMAND)│
└────────────────────────────────────────────────────────┘
                              │
                              └── Traitement vidéo = intensif
```

**Le traitement vidéo (YOLO) est le goulot d'étranglement :**
- Analyse d'une vidéo de 5 minutes : ~2-5 minutes de traitement
- Consomme 4-8 GB RAM pendant l'analyse
- Utilise 100% des CPU disponibles

---

## 🏗️ Option 2 : Architecture Multi-VM (Production)

Si tu as besoin de traiter plusieurs vidéos en parallèle ou pour de la haute disponibilité :

### VM 1 : Web (Frontend + API)
| Ressource | Valeur |
|-----------|--------|
| CPU | 2-4 vCPU |
| RAM | 4-8 GB |
| Disque | 50 GB |
| IP | 192.168.1.10 |

**Services :** Nginx, Next.js, FastAPI

### VM 2 : IA (Workers Celery)
| Ressource | Valeur |
|-----------|--------|
| CPU | 4-8 vCPU |
| RAM | 8-16 GB |
| Disque | 100 GB + NFS |
| IP | 192.168.1.20 |

**Services :** Celery Workers (peut scaler horizontalement)

### VM 3 : Base de données
| Ressource | Valeur |
|-----------|--------|
| CPU | 2-4 vCPU |
| RAM | 4-8 GB |
| Disque | 200 GB SSD |
| IP | 192.168.1.30 |

**Services :** PostgreSQL, Redis

### VM 4 : Stockage (optionnel)
| Ressource | Valeur |
|-----------|--------|
| Disque | 500 GB - 2 TB |

**Services :** NFS Server pour les vidéos

---

## 🎯 Recommandations selon l'usage

### Usage 1 : Développement / Test
```yaml
VM: 1
CPU: 4 vCPU
RAM: 8 GB
Disque: 100 GB
Prix estimé: ~20-40€/mois (cloud)

Convient pour:
- Développement
- Tests
- 1-2 utilisateurs simultanés
- Traitement vidéo occasionnel
```

### Usage 2 : Production Légère (Recommandé)
```yaml
VM: 1
CPU: 6-8 vCPU
RAM: 16 GB
Disque: 200 GB SSD
Prix estimé: ~40-80€/mois (cloud)

Convient pour:
- 5-10 utilisateurs simultanés
- 5-10 vidéos/jour
- Site web public
```

### Usage 3 : Production Intensive
```yaml
VM: 3-4 (Multi-VM)
Web: 4 vCPU / 8 GB
IA: 8 vCPU / 16 GB (x2 pour parallèle)
DB: 4 vCPU / 8 GB
Prix estimé: ~150-300€/mois (cloud)

Convient pour:
- 50+ utilisateurs simultanés
- Traitement vidéo en masse
- Haute disponibilité
```

---

## 💡 Optimisations possibles

### Si tu as peu de ressources (4 vCPU / 8 GB)

**Limiter le traitement :**
```env
# .env
CELERY_WORKER_CONCURRENCY=1  # Un seul worker
FRAME_SAMPLE_FPS=2.0         # Moins de frames analysées
YOLO_CONFIDENCE=0.5          # Moins de détections
```

**Résultat :**
- ✅ L'application fonctionne
- ⚠️ Analyse plus lente (vidéo 5 min = 10 min de traitement)
- ⚠️ Un seul traitement à la fois

### Si tu as beaucoup de ressources (8+ vCPU / 32 GB)

**Paralléliser :**
```yaml
# docker-compose.yml
services:
  celery-worker-1:
    # Worker 1
  celery-worker-2:
    # Worker 2 (ajouté)
  celery-worker-3:
    # Worker 3 (ajouté)
```

**Résultat :**
- ✅ 3 vidéos analysées simultanément
- ✅ Temps de traitement réduit

---

## 🔧 Configuration Proxmox recommandée

### Pour une seule VM

```bash
# Création VM Proxmox
qm create 100 \
  --name bl-genius-app \
  --memory 16384 \      # 16 GB RAM
  --cores 8 \           # 8 vCPU
  --cpu host \          # CPU host pour meilleures perfs
  --net0 virtio,bridge=vmbr0 \
  --scsihw virtio-scsi-single \
  --scsi0 local-lvm:200  # 200 GB disque

# Activer NUMA (si plusieurs sockets CPU)
qm set 100 --numa 1
```

### Pour Multi-VM

```bash
# VM Web
qm create 101 --name bl-genius-web --memory 8192 --cores 4 --scsi0 local-lvm:50

# VM IA (x2 si besoin)
qm create 102 --name bl-genius-ia --memory 16384 --cores 8 --scsi0 local-lvm:100

# VM DB
qm create 103 --name bl-genius-db --memory 8192 --cores 4 --scsi0 local-lvm:200
```

---

## 📈 Monitoring des ressources

### Surveiller l'utilisation

```bash
# CPU et RAM
docker stats

# Espace disque
df -h

# I/O disque (si lent)
iostat -x 1

# Processus gourmands
htop
```

### Alertes à configurer

| Métrique | Seuil d'alerte |
|----------|----------------|
| CPU | > 90% pendant 5 min |
| RAM | > 85% utilisée |
| Disque | > 80% plein |
| I/O | > 100 MB/s en écriture |

---

## 🎯 Décision tree

```
Combien d'utilisateurs simultanés ?
│
├─ 1-5 utilisateurs ───────► 1 VM (4 vCPU / 8 GB)
│
├─ 5-20 utilisateurs ──────► 1 VM (6-8 vCPU / 16 GB)
│
├─ 20-50 utilisateurs ─────► 1 VM (8+ vCPU / 32 GB)
│                            OU Multi-VM
│
└─ 50+ utilisateurs ───────► Multi-VM obligatoire

Combien de vidéos par jour ?
│
├─ < 10 vidéos/jour ───────► 1 VM suffit
│
├─ 10-50 vidéos/jour ──────► 1 VM puissante (8 vCPU)
│                            OU Multi-VM
│
└─ 50+ vidéos/jour ────────► Multi-VM avec workers dédiés
```

---

## ✅ Résumé pour ton collègue

### Option recommandée : Une seule VM

**Specs :**
- **CPU :** 6-8 vCPU (minimum 4)
- **RAM :** 16 GB (minimum 8)
- **Disque :** 200 GB SSD (minimum 100)
- **OS :** Ubuntu 22.04 LTS

**Prix estimé :**
- Proxmox (on-premise) : Coût électricité uniquement
- Cloud OVH/Scaleway : ~40-60€/mois
- Cloud AWS/Azure : ~80-120€/mois

### Quand passer à Multi-VM ?

- ❌ CPU à 100% constamment
- ❌ Plus de RAM disponible
- ❌ File d'attente Celery qui s'allonge
- ❌ Besoin de haute disponibilité (pas de downtime)

---

## 🚀 Commande rapide Proxmox

```bash
# Créer la VM en une commande
qm create 100 --name bl-genius \
  --memory 16384 --cores 8 --cpu host \
  --net0 virtio,bridge=vmbr0 \
  --scsi0 local-lvm:200 \
  --ide2 local:iso/ubuntu-22.04.iso \
  --boot order=scsi0

# Démarrer
qm start 100
```

Puis installer Docker et déployer avec `docker compose up -d`.
