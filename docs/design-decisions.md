# Design Decisions

## Modular monolith first
The case study asks for service boundaries but does not provide enough operational data to justify eight independently deployed services. Modules are isolated so Order, Inventory and Fulfillment can later become microservices.

## PostgreSQL for transactional inventory
Inventory reservation is the critical consistency boundary. Row-level locking with `FOR UPDATE` prevents two concurrent orders from consuming the same available stock.

## Split allocation
An order item can be allocated across multiple warehouses. This supports regional inventory optimization and avoids rejecting an order simply because no single warehouse has the full quantity.

## Event-driven extension
The code keeps downstream concerns behind clear boundaries. Kafka can be introduced for `OrderCreated`, `InventoryReserved`, `OrderPacked`, `ShipmentCreated`, `OrderDelivered` and `ReturnCreated` without changing the transactional core.
