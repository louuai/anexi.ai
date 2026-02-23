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

if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose plugin n'est pas installé!${NC}"
    echo "Installez Docker Compose: https://docs.docker.com/compose/"
    exit 1
fi

echo -e "${GREEN}✅ Docker est installé${NC}"
echo ""

# Start services
echo "📦 Démarrage des services..."
echo ""

docker compose -f docker-compose.microservices.yml up -d --build

echo ""
echo -e "${GREEN}✅ Services démarrés!${NC}"
echo ""
echo "📊 Services disponibles:"
echo "  - Frontend: http://localhost:3000"
echo "  - API Gateway: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - PostgreSQL: localhost:5433"
echo ""
echo "📝 Commandes utiles:"
echo "  - Voir les logs: docker compose -f docker-compose.microservices.yml logs -f"
echo "  - Arrêter: docker compose -f docker-compose.microservices.yml down"
echo "  - Redémarrer: docker compose -f docker-compose.microservices.yml restart"
echo ""
echo -e "${YELLOW}⏳ Attendez ~30 secondes que tout démarre...${NC}"
echo ""
echo "🎉 Ouvrez http://localhost:3000 pour commencer!"
