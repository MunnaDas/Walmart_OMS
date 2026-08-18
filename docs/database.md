# Database Model and Migration Strategy

## Database

PostgreSQL is the system of record for transactional OMS data. SQLAlchemy models define the persistence model and Alembic migrations are the authoritative mechanism for schema changes.

The application must not create or alter tables during startup.

```text
Deployment
   |
   +--> alembic upgrade head
   |
   +--> start FastAPI
```

## Core entities

```text
User
  |
  +--> Orders

Product
  |
  +--> Inventory <-- Warehouse
  |
  +--> OrderItems

Order
  |
  +--> OrderItems
  +--> Allocations --> Warehouse
  +--> Fulfillment
  +--> Packages
  +--> Shipments
  +--> Returns --> ReturnItems

Inventory
  |
  +--> InventoryMovements
```

The exact physical schema is maintained through the repository's SQLAlchemy models and Alembic migrations. `database/schema.sql` is kept as a useful SQL reference for the case study and must remain consistent with the migration state.

## Important constraints

### Orders

- Customer references an existing user.
- Idempotency keys are unique when supplied.
- Order totals cannot be negative.
- Order-item quantities must be positive.
- Unit prices use fixed precision and cannot be negative.

### Inventory

- Product/warehouse inventory is unique according to the supported inventory granularity.
- On-hand, available, reserved and damaged quantities cannot be negative.
- Quantity-balance constraints prevent impossible inventory states.
- Inventory movement quantities must be positive.

### Warehouses

- Warehouse capacity cannot be negative.
- Used capacity cannot be negative or exceed total capacity.
- Warehouse location identifiers are unique within their warehouse.

### Returns

- Return quantities must be positive.
- A return cannot exceed the remaining returnable quantity for an order item.
- Restocking is associated with the original fulfillment/allocation path.

## Money

Order totals, product prices and item unit prices use fixed-precision `NUMERIC`/Python `Decimal` values. Binary floating point is not used for monetary persistence.

## Migration workflow

Create a migration when the model changes:

```bash
alembic revision --autogenerate -m "describe schema change"
```

Review the generated migration carefully rather than treating autogeneration as authoritative, then apply it with:

```bash
alembic upgrade head
```

In CI, migrations are applied to PostgreSQL before the integration tests run. This catches model/migration mismatches before deployment.

## Migration safety

Production migrations should be backward-compatible where possible. For large tables, prefer expand/contract changes:

1. Add the new nullable column/index/structure.
2. Deploy code that can read both representations.
3. Backfill safely in batches.
4. Switch reads/writes.
5. Remove the old representation in a later migration.

Destructive schema changes should never be hidden inside application startup.
