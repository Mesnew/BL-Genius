#!/bin/bash
# ============================================
# SCRIPT DE DÉPLOIEMENT - BL Genius
# ============================================

set -e  # Arrêter en cas d'erreur

echo "🚀 Déploiement de BL Genius (Version Sécurisée)"
echo "================================================"

# Couleurs pour les logs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker n'est pas installé${NC}"
    echo "Installez Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose n'est pas installé${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker et Docker Compose sont installés${NC}"

# Vérifier le fichier .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ Fichier .env manquant${NC}"
    echo "Copiez .env.example vers .env et configurez-le"
    exit 1
fi

echo -e "${GREEN}✅ Fichier .env trouvé${NC}"

# Vérifier que SECRET_KEY est configuré
if grep -q "SECRET_KEY=changez_cette_cle" .env; then
    echo -e "${YELLOW}⚠️  ATTENTION: SECRET_KEY n'a pas été modifié !${NC}"
    echo "Génération d'une nouvelle clé..."
    NEW_KEY=$(openssl rand -hex 32)
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_KEY/" .env
    echo -e "${GREEN}✅ Nouvelle SECRET_KEY générée${NC}"
fi

# Créer les répertoires nécessaires
echo "📁 Création des répertoires..."
mkdir -p data/videos/uploads
mkdir -p data/videos/processed
mkdir -p models
mkdir -p nginx/ssl

# Permissions
chmod 755 data
chmod 755 data/videos
chmod 755 data/videos/uploads
chmod 755 data/videos/processed

echo -e "${GREEN}✅ Répertoires créés${NC}"

# Arrêter les conteneurs existants
echo "🛑 Arrêt des conteneurs existants..."
docker-compose down --remove-orphans 2>/dev/null || true

# Nettoyer les images anciennes (optionnel)
echo "🧹 Nettoyage des images Docker..."
docker system prune -f 2>/dev/null || true

# Build des images
echo "🔨 Construction des images Docker..."
docker-compose build --no-cache

# Démarrage des services
echo "🚀 Démarrage des services..."
docker-compose up -d

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services (30s)..."
sleep 10

# Vérifier PostgreSQL
echo "🔍 Vérification de PostgreSQL..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U blgenius &>/dev/null; then
        echo -e "${GREEN}✅ PostgreSQL est prêt${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Vérifier Redis
echo "🔍 Vérification de Redis..."
if docker-compose exec -T redis redis-cli ping &>/dev/null; then
    echo -e "${GREEN}✅ Redis est prêt${NC}"
else
    echo -e "${RED}❌ Redis ne répond pas${NC}"
fi

# Vérifier le Backend
echo "🔍 Vérification du Backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo -e "${GREEN}✅ Backend est prêt${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Afficher le statut
echo ""
echo "📊 Statut des conteneurs:"
docker-compose ps

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ Déploiement terminé avec succès !${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "🌐 URLs d'accès:"
echo "   - API: http://localhost:8000"
echo "   - Frontend: http://localhost:3000"
echo "   - Documentation API: http://localhost:8000/docs (si DEBUG=true)"
echo ""
echo "🔐 Test de l'authentification:"
echo "   curl -X POST http://localhost:8000/auth/register \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\":\"test@test.com\",\"username\":\"test\",\"password\":\"password123\"}'"
echo ""
echo "📋 Commandes utiles:"
echo "   - Voir les logs: docker-compose logs -f"
echo "   - Arrêter: docker-compose down"
echo "   - Redémarrer: docker-compose restart"
echo ""
echo "⚠️  IMPORTANT: Changez le mot de passe PostgreSQL en production !"
