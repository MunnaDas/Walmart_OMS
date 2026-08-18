# Architecture

Walmart OMS is implemented as a modular monolith using FastAPI, SQLAlchemy and PostgreSQL. The design keeps business boundaries explicit without introducing the operational overhead of multiple independently deployed services.

## High-level flow

```text
Client
  |
  v
FastAPI
  |
  +--> Authentication / JWT / RBAC
  |
  v
Routers
  |
  v
Domain Services
  |       \
  |        +--> State machines / domain validation
  |
  v
Repositories / SQLAlchemy
  |
  v
PostgreSQL
```

Routers are responsible for HTTP concerns: request validation, authentication dependencies, status codes and response serialization. Business workflows belong in services so they can be tested without coupling every rule to an HTTP endpoint.

## Main modules

- **Catalog** — products and product metadata
- **Inventory** — stock quantities, reservations and inventory movements
- **Orders** — order creation, totals, idempotency and lifecycle
- **Warehouses** — warehouse, location and capacity information
- **Fulfillment** — allocation, picking, packing and fulfillment state transitions
- **Shipments** — package and shipment lifecycle
- **Returns** — return authorization, quantity validation and restocking
- **Notifications** — application notification records
- **Audit** — business-operation traceability
- **Analytics** — operational and revenue-oriented read paths

## Transactional boundary

The most important consistency boundary is order creation plus inventory reservation. The operation runs in one PostgreSQL transaction. Inventory rows are locked before reservation and any failure rolls back the complete operation.

This is intentionally stronger than an eventually consistent reservation flow because overselling is a critical business failure for an OMS.

## Authentication and authorization

Requests to protected endpoints authenticate with a JWT bearer token. Role checks are enforced at the API boundary and ownership checks are applied to customer-scoped resources.

The application supports the roles needed by the case study, including customer, warehouse operator and administrator capabilities. Authentication is deliberately kept separate from the business services so an enterprise OIDC/OAuth provider can replace the case-study token issuer later.

## State management

Order, fulfillment and shipment workflows use explicit statuses and transition validation. A state transition is accepted only when the current state permits it. Invalid transitions return a conflict response instead of silently changing the resource.

## Database authority

SQLAlchemy models describe the application persistence model and Alembic migrations are the authoritative mechanism for changing the database schema. Application startup does not create tables implicitly.

PostgreSQL is also responsible for critical invariants such as uniqueness, foreign keys and non-negative inventory quantities. Application validation provides user-friendly errors before the database constraint is reached.

## Scaling path

The current modular monolith can scale horizontally as stateless FastAPI instances behind a load balancer. PostgreSQL remains the transactional system of record.

If individual modules later need independent scaling or deployment, Inventory, Orders and Fulfillment are the strongest candidates for extraction. At that point, synchronous cross-service transactions should be replaced with idempotent APIs and an outbox/event-driven workflow.

Kafka, Redis and distributed tracing are intentionally future architecture choices rather than mandatory dependencies of the current case-study implementation.
