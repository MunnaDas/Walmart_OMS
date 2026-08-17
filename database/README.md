# Database

`schema.sql` is a standalone PostgreSQL reference schema for the OMS. `seed.sql` contains safe demo data for a local walkthrough.

For production, use Alembic migrations so schema changes are versioned and reviewable.

Recommended startup flow:

```bash
alembic upgrade head
psql "$DATABASE_URL" -f database/seed.sql
uvicorn app.main:app --reload
```

The SQL schema mirrors the main OMS domains: users, catalog, warehouses/locations, inventory and movements, orders/items, allocations, fulfillment/packages, shipments, returns/items, notifications and audit logs.
