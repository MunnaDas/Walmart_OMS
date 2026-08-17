# Walmart OMS

A production-oriented Warehouse Order Management System built with FastAPI and PostgreSQL.

## Scope
- Product catalog and inventory
- Multi-warehouse allocation
- Transaction-safe inventory reservation to prevent overselling
- Order lifecycle
- Picking and packing
- Shipment lifecycle
- Returns and inventory restoration
- Notifications/event hooks
- Inventory aging, warehouse utilization and revenue analytics
- Docker, tests and GitHub Actions CI

## Run

```bash
docker compose up --build
```

API docs: http://localhost:8000/docs

## Architecture

The application is a modular monolith. Order, inventory, warehouse, fulfillment and shipment modules have explicit service boundaries so they can later be extracted into microservices. PostgreSQL provides transactional consistency for the order/inventory path; domain events are represented through an event publisher abstraction for future Kafka integration.

## Overselling protection

Inventory reservation executes inside a database transaction and locks the relevant inventory row with `SELECT ... FOR UPDATE`. Only one concurrent transaction can reserve the available quantity at a time.

## Case-study documentation
See `docs/` for assumptions, architecture, data model, API lifecycle and design decisions.
