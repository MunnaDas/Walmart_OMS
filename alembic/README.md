# Alembic migrations

This directory is reserved for versioned production database migrations.

Generate migrations from the SQLAlchemy models with:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Do not use `Base.metadata.create_all()` as the production schema migration mechanism. Keep migrations committed with the application changes.
