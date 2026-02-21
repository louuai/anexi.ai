#!/bin/bash

echo "🔧 Anexi.ai - Local Development Setup"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Step 1: Backend Setup
echo -e "${BLUE}📦 Step 1: Backend Setup${NC}"
echo "=========================="
cd anexi-backend

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 n'est pas installé!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python trouvé: $(python3 --version)${NC}"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate || source .venv/Scripts/activate

# Install dependencies
echo "Installation des dépendances..."
pip install -r requirements.txt

echo -e "${GREEN}✅ Backend configuré${NC}"
echo ""

# Step 2: Database Setup
echo -e "${BLUE}📊 Step 2: Database Setup${NC}"
echo "========================="
echo "⚠️  Assurez-vous que PostgreSQL est installé et en cours d'exécution"
echo "Database: anexi"
echo "User: postgres"
echo "Port: 5433"
echo ""

read -p "Appuyez sur Enter si PostgreSQL est prêt..."

# Run migrations
echo "Exécution des migrations..."
alembic upgrade head

echo -e "${GREEN}✅ Database configurée${NC}"
echo ""

# Step 3: Frontend Setup
echo -e "${BLUE}🎨 Step 3: Frontend Setup${NC}"
echo "========================="
cd ../frontend
echo -e "${GREEN}✅ Frontend prêt (fichiers statiques)${NC}"
echo ""

# Done
cd ..
echo ""
echo -e "${GREEN}🎉 Setup complet!${NC}"
echo ""
echo "📝 Pour démarrer:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd anexi-backend"
echo "  source .venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd frontend"
echo "  python -m http.server 3000"
echo "  # OU double-click sur index.html"
echo ""
echo "Puis ouvrez: http://localhost:3000"
echo ""
