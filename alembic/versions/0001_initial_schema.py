"""Create the initial Walmart OMS schema.

Revision ID: 0001_initial_schema
Revises:
"""

from alembic import op

from app.database import Base
from app import models  # noqa: F401 - register models

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is the baseline migration for the existing application schema.
    # Subsequent changes should be generated as explicit Alembic revisions.
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
