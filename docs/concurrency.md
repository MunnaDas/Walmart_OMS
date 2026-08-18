# Concurrency, Inventory Consistency and Idempotency

## Problem

Two customers can attempt to purchase the last units of the same SKU at the same time. A read-then-write implementation can oversell because both transactions may observe the same available quantity.

## Reservation strategy

Order creation and inventory reservation are performed in one database transaction. PostgreSQL inventory rows are locked before quantities are changed:

```sql
SELECT *
FROM inventory
WHERE product_id = :product_id
  AND warehouse_id = :warehouse_id
FOR UPDATE;
```

The transaction then validates available stock, decreases `available_quantity`, increases `reserved_quantity`, creates the allocation and commits. If any item cannot be fulfilled, the complete order transaction rolls back.

## Why pessimistic locking?

Inventory is a high-contention resource and an oversell is more expensive than waiting briefly for a competing transaction. Row-level pessimistic locking keeps the critical section narrow while providing a clear correctness guarantee.

## Inventory invariants

The database protects core quantity invariants:

```text
available_quantity >= 0
reserved_quantity >= 0
damaged_quantity >= 0
available_quantity + reserved_quantity + damaged_quantity <= on_hand_quantity
```

The exact quantity semantics are defined by the inventory service; application checks provide useful domain errors while PostgreSQL constraints provide a final safety boundary.

Every material inventory mutation should also have a corresponding inventory movement record so operational changes remain auditable.

## Idempotent order creation

The `Idempotency-Key` header protects clients from retrying an order and accidentally creating duplicate reservations. The key is stored with a hash of the request payload.

```text
same key + same payload
        -> return original order

same key + different payload
        -> reject with conflict
```

The unique database constraint is the final concurrency guard when two requests with the same key arrive at the same time.

## Return consistency

Returns are validated against the quantity that remains returnable after previous returns. A customer cannot repeatedly return the original ordered quantity. Restocking is directed to inventory associated with the original fulfillment/allocation rather than selecting an arbitrary warehouse.

## Transaction boundaries

The current application deliberately keeps order creation, allocation and reservation in one PostgreSQL transaction. This makes the case-study consistency model straightforward and testable.

## Distributed evolution

If Inventory becomes a separate service, a database transaction can no longer span Order and Inventory. The next evolution would use an idempotent inventory reservation API plus an outbox/event pattern. Events such as `OrderCreated`, `InventoryReserved`, `OrderPacked`, `ShipmentCreated` and `OrderDelivered` can then be consumed asynchronously by notifications, analytics and integrations.
