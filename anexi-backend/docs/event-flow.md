# Anexi Commerce Data Intelligence - Event Flow

## 1) Event Ingestion Layer

`/events/ingestion/*` receives events from:

- webhooks (`/events/ingestion/webhooks`)
- API polling (`/events/ingestion/polling`)
- tracking script (`/events/ingestion/tracking`)
- internal services (`/events/ingestion/internal`)

Each request is normalized into the immutable canonical schema:

- `event_id`
- `tenant_id`
- `merchant_id`
- `customer_id`
- `event_type`
- `event_payload`
- `source_platform`
- `timestamp`
- `correlation_id`
- `trace_id`

## 2) Tenant/Merchant Attribution

- `tenant_id` defaults to authenticated user tenant and cannot cross tenant boundaries.
- `merchant_id` defaults to authenticated user id unless explicitly provided.
- all queries and writes are tenant-scoped.

## 3) Event Stream

After normalization and validation:

1. event is appended to `event_store` (append-only)
2. event is published to `EventStream`

`EventStream` supports:

- `memory` backend (default, local/dev)
- `kafka` backend (Kafka-compatible adapter boundary)

## 4) Event Store (Append-only)

Table: `event_store`

- chronological history with index on `timestamp`
- multi-tenant isolation (`tenant_id`)
- replay support (`/events/store/replay`)
- query by `customer_id` and `merchant_id`

## 5) Timeline Engine

`/timeline/customers/{customer_id}` rebuilds customer behavior as a chronologically ordered sequence:

- `view_product -> add_to_cart -> purchase -> refund` style timeline

This output is the base for analytics, trust scoring, and future AI models.

## 6) Trust Engine Evolution

Endpoint: `/trust-engine/score`

Scores:

- `contextual_score`: current interaction signal
- `historical_score`: timeline-derived behavior

Final formula:

`TrustScore = 0.4 * contextual_score + 0.6 * historical_score`

Historical signals include:

- purchases and confirmations
- cancellations
- refunds
- call outcomes
- interaction volume and behavior consistency

## 7) AI Prediction Layer Preparation

`app/modules/trust_engine/prediction.py` defines the future provider contract:

- purchase probability
- cancellation probability
- fraud risk

Current implementation ships a placeholder provider to keep integration points stable.

