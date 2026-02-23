# Anexi Microservices Architecture

This folder contains the microservices split of the Anexi SaaS backend.

## Services

- `auth-service`: `/auth/*`
- `orders-service`: `/orders/*`, `/boutiques/*`
- `payments-service`: `/payments/*`
- `analytics-service`: `/dashboard/*` + internal `/internal/events`
- `trust-service`: `/trust/*`
- `worker`: async task execution (Celery)
- `api-gateway`: single entrypoint routing requests to services
- `prometheus`: metrics scraper
- `grafana`: observability UI
- `jaeger`: distributed tracing backend

## Inter-service Communication

Two communication modes are implemented:

1. Synchronous API calls
- `api-gateway` forwards client calls to domain services.
- `payments-service` can emit analytics events to `analytics-service` via `/internal/events`.

2. Asynchronous message queue
- Redis + Celery used for background processing:
  - decision engine
  - analytics refresh
  - payment webhook processing
  - call agent stub (future)

## Orchestration

Use:

```bash
docker compose -f docker-compose.microservices.yml up -d --build
```

Gateway endpoint remains:
- `http://localhost:8000`
Grafana endpoint:
- `http://localhost:3000`

Health checks:
- `GET /health` on each service.
- `GET /metrics` on each service.

## Production Safety Decisions

1. No `Base.metadata.create_all()` in microservices runtime.
2. Database schema is managed once by `db-migrate` (`alembic upgrade head`).
3. Domain services start only after migrations are successful.
4. No `--reload` in orchestrated runtime (prevents multi-process schema races).
5. API gateway returns controlled `503/504` errors for upstream failures.
6. Internal services stay private (no host port exposure outside gateway + grafana).

## Startup Order

1. `postgres` + `redis`
2. `db-migrate`
3. Domain services (`auth/orders/payments/analytics/trust`)
4. `worker`
5. `api-gateway`
6. Observability (`jaeger`, `prometheus`, `grafana`)

## Verification Checklist

1. `docker compose -f docker-compose.microservices.yml ps`
2. `curl http://localhost:8000/health`
3. Check metrics:
   - `curl http://localhost:8000/metrics`
4. Open Grafana:
   - `http://localhost:3000` (default: `admin` / `admin`)
5. Smoke test:
   - `POST /auth/signup`
   - `POST /auth/login`
   - `POST /boutiques/`
   - `POST /orders/`
   - `POST /payments/webhook`
6. Check worker logs for received tasks.
