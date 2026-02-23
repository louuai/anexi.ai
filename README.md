# anexi.ai

Plateforme SaaS pour automatiser les operations e-commerce.

## Structure
- `anexi-backend/`: API FastAPI + base de donnees
- `frontend/`: pages HTML/CSS/JS
- `microservices/`: gateway + domain services
- `observability/`: Prometheus, Grafana dashboards, provisioning

## Lancement (Docker)
```bash
docker compose -f docker-compose.microservices.yml up -d --build
```

## Endpoints
- Frontend: `http://localhost:8080`
- API Gateway: `http://localhost:8000`
- Grafana: `http://localhost:3000` (admin/admin)
- Jaeger: `http://localhost:16686`
- PostgreSQL (host mapping): `localhost:5434`

## PGAdmin Connection (Docker PostgreSQL)
- Host: `127.0.0.1`
- Port: `5434`
- Database: `anexi`
- Username: `postgres`
- Password: `louaiouni05062001`

## Useful Commands
```bash
# stop
docker compose -f docker-compose.microservices.yml down

# show status
docker compose -f docker-compose.microservices.yml ps

# logs
docker compose -f docker-compose.microservices.yml logs -f

# rerun safe migrations
docker compose -f docker-compose.microservices.yml run --rm db-migrate
```

## Repository
`https://github.com/louuai/anexi.ai.git`
