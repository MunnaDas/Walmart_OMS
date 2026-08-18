# Interview Walkthrough

## 1. Requirement discovery

The OMS manages the journey from order placement through inventory reservation, warehouse allocation, picking, packing, shipping and returns. The primary consistency boundary is inventory reservation because an oversell directly violates the order promise.

## 2. Why a modular monolith?

The case study needs multiple business capabilities, but independently deploying every capability would add operational complexity without evidence that it is necessary. The implementation therefore uses explicit modules and a service layer inside one deployable application. Orders, Inventory and Fulfillment have clear boundaries that can later become services.

## 3. Authentication and authorization

Protected APIs use JWT bearer authentication. Role-based checks distinguish customer, warehouse operator and administrative capabilities, while customer resources are scoped to the authenticated customer where appropriate.

For a real enterprise deployment, the token issuer would normally be an OAuth 2.0/OIDC identity provider rather than the case-study token mechanism.

## 4. Overselling

Reservation is transactional. PostgreSQL row-level locking (`FOR UPDATE`) serializes competing reservations for the same inventory row. If stock cannot satisfy an item, the transaction rolls back so a partially reserved order is not left behind.

## 5. Idempotency

Order creation accepts an `Idempotency-Key`. The request hash is persisted with the key so a retry of the same request returns the original order, while reusing the key with a different payload is rejected. A database uniqueness constraint protects against concurrent duplicate keys.

## 6. Warehouse allocation

An order item can be split across warehouses. The current allocator favors available inventory while keeping the allocation inside the same transactional order workflow. A production allocator can add distance, shipping SLA, carrier cost, warehouse capacity and promised-delivery scoring.

## 7. Fulfillment

Fulfillment uses explicit state transitions:

```text
ALLOCATED -> PICKING -> PICKED -> PACKING -> PACKED -> READY_TO_SHIP
```

Invalid transitions return a conflict rather than silently changing state. Shipment progression follows its own validated lifecycle through delivery.

## 8. Returns

Returns are item-level. The requested quantity is checked against the remaining returnable quantity, so repeated return requests cannot exceed what was actually ordered/shipped. Restockable inventory is returned to an appropriate fulfillment warehouse rather than an arbitrary stock location.

## 9. Database and migrations

Alembic is the schema authority. Application startup does not create tables implicitly. Money uses fixed-precision numeric types and database constraints protect critical quantity and uniqueness invariants.

## 10. Scaling

FastAPI instances are stateless and can scale horizontally behind a load balancer. PostgreSQL remains the transactional system of record. Redis is a possible future optimization for hot catalog reads, while Kafka is a possible future event transport.

Neither is required for the current consistency-critical path.

## 11. Event-driven evolution

The synchronous transaction completes the order and reservation first. Events such as `OrderCreated`, `InventoryReserved` and `ShipmentCreated` are natural boundaries for notifications, analytics and external integrations.

Before introducing asynchronous publication in a distributed deployment, an outbox pattern should be used to guarantee that committed database changes cannot lose their corresponding events.

## 12. Observability and operations

The application exposes liveness and readiness checks. CI runs against PostgreSQL and validates linting, migrations, tests and coverage. A production deployment should extend this with structured logs, correlation IDs, metrics and distributed tracing.

## 13. Next production steps

The strongest next improvements are an outbox/event mechanism, stronger observability, rate limiting, enterprise OIDC integration, carrier integrations, background workers and deeper concurrent-load testing. These are deliberately kept separate from the current transactional core so the case-study implementation remains understandable.
