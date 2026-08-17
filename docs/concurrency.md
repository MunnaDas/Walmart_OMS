# Concurrency and Overselling

## Problem

Two customers may attempt to purchase the last units of the same SKU at the same time. A read-then-write implementation can oversell because both transactions may observe the same available quantity.

## Approach

Order creation is a single database transaction. Before changing inventory, the PostgreSQL implementation executes a row-level lock equivalent to:

```sql
SELECT * FROM inventory
WHERE product_id = :product_id
  AND warehouse_id = :warehouse_id
FOR UPDATE;
```

The transaction then validates `available_quantity`, decreases it, increases `reserved_quantity`, creates the allocation, and commits. If any item cannot be fulfilled, the complete order transaction is rolled back.

## Why pessimistic locking?

Inventory is a contention-heavy resource and an oversell is more expensive than waiting briefly for a lock. Row-level pessimistic locking keeps the critical section small while preserving strong consistency.

## Idempotency

The `Idempotency-Key` request header prevents client retries from creating duplicate orders and duplicate reservations.

## Distributed evolution

If Inventory becomes a separate microservice, the database transaction cannot span the Order and Inventory services. The next evolution would use an inventory reservation API with an idempotency key and an outbox/event pattern. Kafka can distribute `OrderCreated`, `InventoryReserved`, `OrderPacked`, `ShipmentCreated` and other domain events to downstream consumers.
