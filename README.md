# Walmart OMS

A production-oriented Warehouse Order Management System built with FastAPI and PostgreSQL for the Walmart backend engineering case study.

## What the system covers

- Product catalog and multi-warehouse inventory
- Warehouse zones, bins and capacity tracking
- Transaction-safe inventory reservation with PostgreSQL row locking
- Idempotent order creation with request-payload protection
- Warehouse allocation and split allocation
- Picking and packing with explicit state transitions
- Package and shipment lifecycle
- Item-level returns with controlled restocking
- Notifications and audit records
- Inventory, warehouse and revenue analytics
- JWT authentication and role-based authorization
- Health/liveness/readiness endpoints
- Pagination for list-oriented APIs
- Alembic database migrations
- Dockerized PostgreSQL development environment
- PostgreSQL-backed integration tests and GitHub Actions CI

## Architecture

The application is a modular monolith. HTTP routers remain thin and delegate business workflows to domain services, while SQLAlchemy/Alembic and PostgreSQL provide the transactional persistence boundary.

```text
Client
  |
  v
FastAPI Routers
  |
  +--> Authentication / RBAC
  |
  v
Domain Services
  |
  +--> Order Service
  +--> Inventory Service
  +--> Fulfillment Service
  +--> Shipment / Return workflows
  |
  v
SQLAlchemy
  |
  v
PostgreSQL
```

The modular structure deliberately keeps deployment simple while preserving boundaries that can later be extracted into independently deployed services.

## Security

Protected APIs use JWT bearer authentication. Authorization is role-based; customer operations are scoped to the authenticated customer where applicable, while warehouse and administrative operations require the corresponding role.

The repository is intentionally not a full identity provider. Token issuance is kept simple for the case study; production deployment would normally integrate with an enterprise identity provider/OAuth 2.0 or OIDC platform.

## Order lifecycle

```text
CREATED → ALLOCATED → PICKING → PICKED → PACKING → PACKED
        → READY_TO_SHIP → SHIPPED → IN_TRANSIT
        → OUT_FOR_DELIVERY → DELIVERED
```

Invalid fulfillment/shipment transitions are rejected rather than silently mutating state.

Cancellation releases only still-reserved inventory. Returns are item-level and enforce the remaining returnable quantity before restocking eligible inventory.

## Inventory consistency

Order creation and inventory reservation execute in one database transaction. PostgreSQL inventory rows are locked with `SELECT ... FOR UPDATE` before quantities are changed. This prevents concurrent requests from reserving the same available stock.

Inventory mutations maintain explicit quantities for on-hand, available, reserved and damaged stock and create inventory movement records for traceability. Database constraints protect non-negative quantities and quantity-balance invariants.

## Idempotency

Clients can send an `Idempotency-Key` header when creating an order. The key is persisted with a request hash. Repeating the same key and payload returns the original order; reusing the key with a different payload is rejected.

The database uniqueness constraint remains the final concurrency guard against duplicate keys.

## Database migrations

Alembic is the schema authority. The application does not call `Base.metadata.create_all()` during startup.

Run migrations before starting the application in a deployment environment:

```bash
alembic upgrade head
```

## Run locally

```bash
docker compose up --build
```

API documentation is available at `http://localhost:8000/docs`.

## Health checks

- `GET /health/live` — process/liveness check
- `GET /health/ready` — dependency/readiness check
- `GET /health` — service health information

## Testing and CI

Tests run against PostgreSQL rather than SQLite so the production database behavior used for locking and constraints is exercised.

CI validates:

```text
Ruff
  ↓
Alembic migration
  ↓
PostgreSQL
  ↓
pytest + coverage
```

The test suite covers the critical order/inventory lifecycle as well as authentication, authorization and production database behavior.

## Documentation

See `docs/` for the detailed architecture, data model, concurrency strategy, security model, API behavior, testing strategy, design decisions and interview walkthrough.
