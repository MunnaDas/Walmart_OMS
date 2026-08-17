# Assumptions

- PostgreSQL is the production database; SQLite is supported only for local smoke tests.
- Inventory is tracked per SKU and warehouse and can be further refined to bin/location level.
- A customer order is allocated from one or more warehouses; split fulfillment is supported by the Allocation entity.
- Inventory reservation and release are strongly consistent and occur in the same database transaction as order creation/cancellation.
- Picking and packing are warehouse operations represented by explicit fulfillment states.
- Carrier integration is mocked; shipment records expose an adapter-friendly boundary for real carriers.
- Notifications and analytics are downstream concerns and can consume domain events asynchronously.
- Authentication/RBAC, Kafka and Kubernetes are extension points for the case-study discussion and production hardening.
