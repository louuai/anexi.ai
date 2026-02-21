# Anexi.ai Backend API

Intelligence layer pour e-commerce - Trust scoring, AI calls, et automatisation business pour marchés émergents.

## 🎯 Vue d'Ensemble

Anexi.ai est une plateforme SaaS B2B destinée aux e-commerçants (Facebook Ads sellers, Shopify merchants, WhatsApp sellers) dans les marchés émergents. L'objectif est de créer une infrastructure intelligente qui centralise les commandes, analyse le comportement client, réduit les fake orders, et automatise les confirmations.

## 🏗️ Architecture

```
anexi-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée FastAPI
│   ├── database.py          # Configuration SQLAlchemy
│   ├── models.py            # Modèles de base de données
│   ├── schemas.py           # Schémas Pydantic
│   ├── routes/              # Endpoints API
│   │   ├── auth.py          # Authentification (signup, login, JWT)
│   │   ├── orders.py        # Gestion des commandes
│   │   ├── boutiques.py     # Gestion des boutiques
│   │   ├── dashboard.py     # Statistiques et analytics
│   │   └── trust.py         # Trust layer et scoring
│   └── utils/
│       └── security.py      # Password hashing, JWT tokens
├── services/                # Business logic services
│   ├── analytics.py         # Analytics engine
│   ├── decision.py          # AI decision engine
│   └── trust.py             # Trust scoring service
├── alembic/                 # Migrations de base de données
│   ├── versions/
│   └── env.py
├── requirements.txt
├── alembic.ini
└── .env.example
```

## 📊 Base de Données

### Tables Principales

- **users**: Utilisateurs de la plateforme (merchants)
- **user_profiles**: Profils marchands (type de vente)
- **boutiques**: Boutiques e-commerce connectées
- **customers**: Clients finaux avec trust tracking
- **orders**: Commandes clients
- **calls**: Appels de confirmation AI
- **ai_decisions**: Décisions automatiques de l'AI Brain
- **ads_insights**: Insights des campagnes publicitaires

## 🚀 Installation

### Prérequis

- Python 3.11+
- PostgreSQL 13+
- pip

### Étapes

1. **Cloner le repository**
```bash
git clone <your-repo>
cd anexi-backend
```

2. **Créer un environnement virtuel**
```bash
python -m venv .venv
source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration de l'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos configurations
```

5. **Créer la base de données**
```bash
# Dans PostgreSQL
createdb anexi
```

6. **Exécuter les migrations**
```bash
alembic upgrade head
```

7. **Lancer le serveur**
```bash
uvicorn app.main:app --reload --port 8000
```

L'API sera accessible sur: `http://localhost:8000`
Documentation interactive: `http://localhost:8000/docs`

## 📚 API Endpoints

### Authentification

- `POST /auth/signup` - Créer un compte
- `POST /auth/login` - Se connecter (JWT token)
- `POST /auth/profile` - Choisir profil marchand
- `GET /auth/me` - Informations utilisateur connecté

### Boutiques

- `POST /boutiques/` - Créer une boutique
- `GET /boutiques/` - Lister mes boutiques
- `GET /boutiques/{id}` - Détails d'une boutique
- `POST /boutiques/{id}/customers` - Ajouter un client
- `GET /boutiques/{id}/customers` - Lister les clients

### Commandes

- `POST /orders/` - Créer une commande
- `GET /orders/` - Lister les commandes (avec filtres)
- `GET /orders/{id}` - Détails d'une commande
- `PATCH /orders/{id}/status` - Mettre à jour le statut

### Dashboard

- `GET /dashboard/stats` - Statistiques globales
- `GET /dashboard/recent-orders` - Commandes récentes
- `GET /dashboard/revenue-chart` - Graphique de revenus

### Trust Layer

- `GET /trust/customer/{id}/score` - Trust score d'un client
- `GET /trust/risky-customers` - Clients à risque
- `GET /trust/blacklist` - Liste noire

## 🔐 Authentification

L'API utilise JWT (JSON Web Tokens) pour l'authentification.

### Exemple d'utilisation

1. **Signup**
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }'
```

2. **Login**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

Réponse:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1
}
```

3. **Utiliser le token**
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🧪 Tests

```bash
# Installer pytest
pip install pytest pytest-cov

# Exécuter les tests
pytest

# Avec coverage
pytest --cov=app tests/
```

## 🔄 Migrations

### Créer une nouvelle migration
```bash
alembic revision --autogenerate -m "Description de la migration"
```

### Appliquer les migrations
```bash
alembic upgrade head
```

### Revenir en arrière
```bash
alembic downgrade -1
```

## 📦 Déploiement

### Docker (À venir - Phase 4)

```bash
docker-compose up -d
```

### Production

1. Configurer les variables d'environnement
2. Utiliser un reverse proxy (Nginx)
3. Utiliser gunicorn comme serveur WSGI

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🛣️ Roadmap

### Phase 1: MVP Core ✅
- ✅ Schéma de base de données complet
- ✅ Models SQLAlchemy avec relationships
- ✅ Authentication JWT
- ✅ CRUD basique (orders, boutiques, customers)
- ✅ Trust layer basique

### Phase 2: Modules Intelligence (En cours)
- 🔄 Behavioral Brain (scoring engine)
- 🔄 Event Pipeline (webhooks)
- 🔄 Decision Engine
- 🔄 AI Call Agent (simulation)

### Phase 3: Production Ready
- ⏳ Tests unitaires complets
- ⏳ Logging avancé
- ⏳ Rate limiting
- ⏳ Monitoring

### Phase 4: Infrastructure
- ⏳ Docker & Docker Compose
- ⏳ CI/CD Pipeline
- ⏳ Documentation complète

## 🤝 Contribution

Ce projet est dans le cadre d'un PFE (Projet de Fin d'Études).

## 📝 License

Proprietary - Anexi.ai

## 👨‍💻 Auteur

Louai Ouni - Fondateur Anexi.ai
