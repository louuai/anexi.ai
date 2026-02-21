#!/bin/bash

echo "🚀 Anexi.ai - Quick Start Script"
echo "================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker n'est pas installé!${NC}"
    echo "Installez Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose n'est pas installé!${NC}"
    echo "Installez Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker est installé${NC}"
echo ""

# Start services
echo "📦 Démarrage des services..."
echo ""

docker-compose up -d

echo ""
echo -e "${GREEN}✅ Services démarrés!${NC}"
echo ""
echo "📊 Services disponibles:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - PostgreSQL: localhost:5433"
echo ""
echo "📝 Commandes utiles:"
echo "  - Voir les logs: docker-compose logs -f"
echo "  - Arrêter: docker-compose down"
echo "  - Redémarrer: docker-compose restart"
echo ""
echo -e "${YELLOW}⏳ Attendez ~30 secondes que tout démarre...${NC}"
echo ""
echo "🎉 Ouvrez http://localhost:3000 pour commencer!"
