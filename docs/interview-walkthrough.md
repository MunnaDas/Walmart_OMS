# Interview Walkthrough

## 1. Requirement discovery
The OMS needs to manage the complete journey from order placement through inventory reservation, warehouse allocation, picking, packing, shipping and returns. The critical consistency boundary is inventory reservation.

## 2. Why modular monolith
A modular monolith reduces deployment and operational complexity for the take-home exercise while preserving explicit module boundaries. High-volume modules can later be extracted into services.

## 3. Overselling
Reservation is transactional. PostgreSQL row-level locking (`FOR UPDATE`) serializes competing reservations for the same inventory row. The API returns HTTP 409 when stock is unavailable.

## 4. Warehouse allocation
The allocator can split an order item across warehouses. It currently prefers warehouses with the highest available quantity; a production version can add distance, shipping SLA, cost and capacity scoring.

## 5. Fulfillment
Fulfillment uses a state machine: ALLOCATED -> PICKING -> PICKED -> PACKING -> PACKED -> READY_TO_SHIP. Invalid transitions return HTTP 409.

## 6. Event-driven evolution
The synchronous transaction completes the order and reservation first. Events such as OrderCreated, InventoryReserved and ShipmentCreated can be published to Kafka for notifications and analytics.

## 7. Scaling
Stateless FastAPI instances can scale horizontally behind a load balancer. PostgreSQL uses indexes and connection pooling; Redis can be introduced for hot catalog reads; Kafka decouples downstream consumers; Kubernetes can autoscale API workers and event consumers.

## 8. Next production steps
Add OAuth/JWT authentication, idempotency keys, Alembic migrations, outbox pattern, carrier integrations, distributed tracing, structured logging, rate limiting, secrets management and full PostgreSQL concurrency tests.
