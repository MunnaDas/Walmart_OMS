# Walmart OMS

A production-oriented Warehouse Order Management System built with FastAPI and PostgreSQL for the Walmart backend engineering case study.

## Scope
- Product catalog and multi-warehouse inventory
- Warehouse zones/bins and capacity tracking
- Transaction-safe inventory reservation to prevent overselling
- Idempotent order creation
- Warehouse allocation and split allocation
- Picking and packing with explicit state transitions
- Package and shipment lifecycle
- Item-level returns with restocking
- Notifications and audit APIs
- Inventory aging, warehouse utilization and revenue analytics
- Docker, PostgreSQL-backed tests and GitHub Actions CI

## Run

```bash
docker compose up --build
```

API docs: http://localhost:8000/docs

## Order lifecycle

```text
CREATED → ALLOCATED → PICKING → PICKED → PACKING → PACKED
        → READY_TO_SHIP → SHIPPED → IN_TRANSIT
        → OUT_FOR_DELIVERY → DELIVERED
```

Cancellation releases only still-reserved inventory. Returns are item-level and restock eligible items are added back to inventory when received.

## Architecture

The application is a modular monolith. Order, inventory, warehouse, fulfillment and shipment modules have explicit boundaries so they can later be extracted into microservices. PostgreSQL provides transactional consistency for the order/inventory path.

## Overselling protection

Order creation runs in one database transaction. PostgreSQL inventory rows are locked with `SELECT ... FOR UPDATE` before quantities are reserved. A failed multi-item order rolls back all reservations, so the operation is atomic.

## Idempotency

Clients can send an `Idempotency-Key` header on order creation. Repeating the same key returns the existing order rather than creating a duplicate reservation.

## Testing

CI runs against PostgreSQL rather than SQLite so the row-locking behavior used for overselling protection is exercised against the production database engine.

## Case-study documentation
See `docs/` for assumptions, architecture, data model, API lifecycle and design decisions.
