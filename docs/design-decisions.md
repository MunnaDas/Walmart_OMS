# Design Decisions

## Modular monolith first

The case study requires clear service boundaries but does not provide operational evidence that independently deployed services are necessary. A modular monolith keeps deployment and debugging simple while separating Catalog, Orders, Inventory, Fulfillment, Shipments, Returns and Analytics responsibilities.

The boundaries are intentional so high-scale modules can later be extracted without first untangling a monolithic codebase.

## PostgreSQL for transactional inventory

Inventory reservation is the critical consistency boundary. PostgreSQL row-level locking with `FOR UPDATE` prevents competing transactions from reserving the same available quantity.

PostgreSQL also provides foreign keys, uniqueness constraints and quantity checks so important invariants are protected below the application layer.

## Alembic instead of startup schema creation

Database schema changes belong in migrations rather than application startup. Alembic makes schema evolution explicit, reviewable and deployable across environments. The API therefore does not call `Base.metadata.create_all()` when it starts.

## Decimal for money

Prices and monetary totals use fixed-precision `NUMERIC` values rather than binary floating point. This avoids rounding behavior that is inappropriate for order totals and financial calculations.

## Split allocation

An order item can be allocated across multiple warehouses. This avoids rejecting an order simply because no single warehouse contains the entire requested quantity and leaves room for future allocation scoring based on distance, shipping SLA, cost and capacity.

## Service layer

HTTP routers should not become the location of business rules. Order, inventory and fulfillment workflows are handled by services so state transitions, transactional behavior and domain validation can be reused by APIs and tested independently.

## JWT and RBAC

The case study needs authenticated actors and different permissions for customers, warehouse operators and administrators. JWT bearer authentication with role checks provides a small, understandable security boundary without coupling the application to a particular identity provider.

For a production deployment, token issuance would normally be delegated to an enterprise OAuth 2.0/OIDC provider.

## Pessimistic locking over optimistic retries

Inventory is highly contended and overselling is unacceptable. Pessimistic row locking gives a direct correctness guarantee and keeps the critical section small. Optimistic concurrency can be reconsidered if the workload characteristics change.

## Event-driven extension

The transactional core remains synchronous. Events such as `OrderCreated`, `InventoryReserved`, `OrderPacked`, `ShipmentCreated`, `OrderDelivered` and `ReturnCreated` are natural integration boundaries for notifications, analytics and external systems.

An outbox pattern should be introduced before publishing these events from a distributed production deployment so database state and event publication cannot diverge.
