# Testing and CI

## Test strategy

The test suite focuses on business invariants and PostgreSQL behavior rather than only HTTP happy paths.

### Core scenarios

- order creation
- multi-item atomicity
- inventory reservation
- insufficient-stock conflicts
- concurrent reservation behavior
- idempotent retries
- idempotency-key payload mismatch
- fulfillment state transitions
- shipment state transitions
- return quantity limits
- inventory movement/audit behavior
- authentication failures
- role-based authorization
- customer resource ownership
- readiness/liveness behavior

## PostgreSQL integration

Tests run against PostgreSQL rather than SQLite because the production design depends on PostgreSQL transaction semantics and row-level locking. This prevents a test suite from passing against a database engine with materially different concurrency behavior.

## CI quality gates

GitHub Actions validates the application in an environment that starts PostgreSQL before running the tests.

```text
Checkout
   ↓
Python dependencies
   ↓
Ruff
   ↓
Alembic upgrade head
   ↓
pytest
   ↓
coverage threshold
```

The lint configuration intentionally focuses on correctness and maintainability rules compatible with FastAPI dependency injection patterns.

## Local test commands

```bash
pytest -q
```

For coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

For linting:

```bash
ruff check .
```

## What should be added next

The next testing maturity step is load/concurrency testing with multiple simultaneous order requests for the same SKU. This should measure lock contention, transaction latency and the rate of successful versus rejected reservations under realistic contention.
