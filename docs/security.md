# Security and Authorization

## Authentication

Protected API endpoints use JWT bearer authentication. The authenticated principal is resolved before the request reaches protected business operations.

```text
Authorization: Bearer <access-token>
```

The case-study token issuer is intentionally lightweight. Production deployment should normally use an enterprise OAuth 2.0/OIDC identity provider and validate issuer, audience, expiry and signing configuration according to the provider's policy.

## Authorization

Authorization is role-based and enforced at the API boundary.

| Role | Typical capabilities |
|---|---|
| `CUSTOMER` | Create/view own orders, manage eligible returns |
| `WAREHOUSE_OPERATOR` | Inventory and fulfillment operations |
| `ADMIN` | Administrative/catalog/operational capabilities |

Role checks should be combined with resource ownership checks. A valid customer token must not allow access to another customer's order simply because the order ID is known.

## Error behavior

Authentication failures should return `401 Unauthorized`. Authenticated users without the required role should receive `403 Forbidden`. Domain conflicts such as an invalid state transition or insufficient stock should use the appropriate business-level conflict response rather than being reported as authentication failures.

## Passwords and secrets

Passwords must never be persisted in plaintext. Passwords are represented by a password hash in the data model.

JWT signing keys, database credentials and other secrets must be supplied through environment/secret management rather than committed to the repository.

## Defense in depth

Database foreign keys, unique constraints and quantity checks remain important even when API validation exists. Authorization belongs at the API boundary, while business invariants remain enforced in services and the database.

## Production hardening roadmap

Before a public production deployment, add:

- enterprise OIDC/OAuth 2.0 integration
- key rotation and asymmetric signing where appropriate
- refresh-token/session strategy
- rate limiting and abuse protection
- audit trails for security-sensitive actions
- secret-manager integration
- security headers and TLS enforcement at the edge
- dependency and container vulnerability scanning
- structured security event logging
