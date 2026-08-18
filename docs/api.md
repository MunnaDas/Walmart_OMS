# API Guide

FastAPI exposes the interactive OpenAPI documentation at `/docs` when the application is running.

## Authentication

Protected endpoints require a bearer token:

```text
Authorization: Bearer <JWT>
```

Use the authentication endpoints exposed by the application to obtain a token in the case-study environment. Customers can only access customer-scoped resources they are authorized to see.

## API conventions

- `2xx` — successful operation
- `400` — malformed or invalid request
- `401` — missing/invalid authentication
- `403` — authenticated but not authorized
- `404` — resource not found
- `409` — domain conflict such as insufficient inventory, duplicate idempotency use or invalid state transition
- `422` — request validation failure where applicable

## Idempotent order creation

Order creation supports the `Idempotency-Key` header.

```text
POST /orders
Idempotency-Key: 7d2d...
```

The same key and request payload return the original order. Reusing the key with a different request payload is rejected.

## Pagination

List endpoints use bounded pagination rather than returning unbounded database result sets. Clients should always treat the page size as a server-controlled maximum.

When consuming list APIs, clients should persist the pagination parameters and continue until all required records have been retrieved.

## Health endpoints

```text
GET /health/live
GET /health/ready
GET /health
```

`/health/live` is intended for process liveness. `/health/ready` verifies that the application is ready to serve requests and its required dependencies are available.

## Domain workflows

### Order

```text
Create order
   ↓
Reserve inventory
   ↓
Allocate warehouse stock
   ↓
Fulfillment
   ↓
Shipment
   ↓
Delivery
```

### Fulfillment

```text
ALLOCATED
   ↓
PICKING → PICKED → PACKING → PACKED → READY_TO_SHIP
```

Invalid transitions are rejected.

### Returns

Returns are item-level and quantity-aware. A return request is validated against the remaining returnable quantity. Restockable items are returned through the appropriate inventory path.

## Response contracts

API responses use explicit schemas rather than exposing arbitrary internal ORM state. This keeps public contracts stable while allowing database models to evolve.

For the authoritative endpoint list and generated request/response schemas, use the running FastAPI OpenAPI document at `/docs` or `/openapi.json`.
