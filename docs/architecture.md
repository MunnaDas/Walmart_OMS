# Architecture

The solution is a modular monolith implemented with FastAPI. The modules are Catalog, Inventory, Orders, Warehouses, Fulfillment, Shipments, Returns and Analytics.

```text
Customer / Warehouse UI
          |
       FastAPI
          |
  +-------+--------------------------------+
  | Catalog | Order | Inventory | Warehouse |
  | Fulfillment | Shipment | Returns       |
  +------------------+---------------------+
                     |
                 PostgreSQL
                     |
              Domain event boundary
                     |
              Kafka (future/bonus)
```

The synchronous order path remains strongly consistent. Inventory rows are locked during reservation to prevent overselling. Notifications and analytics can later consume events asynchronously without slowing the transactional order path.
