"""Create the initial Walmart OMS schema.

Revision ID: 0001_initial_schema
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(200), nullable=False),
        sa.Column("role", sa.String(40), nullable=False, server_default="CUSTOMER"),
        sa.Column("password_hash", sa.String(255), nullable=False, server_default=""),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.CheckConstraint("price >= 0", name="ck_products_price_non_negative"),
        sa.UniqueConstraint("sku", name="uq_products_sku"),
    )
    op.create_table(
        "warehouses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("used_capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.CheckConstraint("capacity >= 0", name="ck_warehouses_capacity_non_negative"),
        sa.CheckConstraint("used_capacity >= 0", name="ck_warehouses_used_capacity_non_negative"),
        sa.CheckConstraint("capacity = 0 OR used_capacity <= capacity", name="ck_warehouses_capacity_limit"),
        sa.UniqueConstraint("code", name="uq_warehouses_code"),
    )
    op.create_table(
        "warehouse_locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("warehouses.id"), nullable=False),
        sa.Column("zone", sa.String(50), nullable=False, server_default="DEFAULT"),
        sa.Column("aisle", sa.String(50), nullable=False, server_default="A"),
        sa.Column("bin_code", sa.String(64), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.CheckConstraint("capacity >= 0", name="ck_locations_capacity_non_negative"),
        sa.UniqueConstraint("warehouse_id", "bin_code", name="uq_warehouse_bin"),
    )
    op.create_table(
        "inventory",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("warehouses.id"), nullable=False),
        sa.Column("bin_code", sa.String(64), nullable=False, server_default="DEFAULT"),
        sa.Column("on_hand_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("damaged_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("received_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_movement_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("on_hand_quantity >= 0", name="ck_inventory_on_hand_non_negative"),
        sa.CheckConstraint("available_quantity >= 0", name="ck_inventory_available_non_negative"),
        sa.CheckConstraint("reserved_quantity >= 0", name="ck_inventory_reserved_non_negative"),
        sa.CheckConstraint("damaged_quantity >= 0", name="ck_inventory_damaged_non_negative"),
        sa.CheckConstraint("available_quantity + reserved_quantity + damaged_quantity <= on_hand_quantity", name="ck_inventory_quantity_balance"),
        sa.UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_warehouse"),
    )
    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("inventory_id", sa.Integer(), sa.ForeignKey("inventory.id"), nullable=False),
        sa.Column("movement_type", sa.String(40), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reference_type", sa.String(40)),
        sa.Column("reference_id", sa.String(80)),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_movement_quantity_positive"),
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="CREATED"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("idempotency_request_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("total_amount >= 0", name="ck_orders_total_non_negative"),
        sa.UniqueConstraint("idempotency_key", name="uq_orders_idempotency_key"),
    )
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
    )
    op.create_table(
        "allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("order_item_id", sa.Integer(), sa.ForeignKey("order_items.id"), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("warehouses.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="ALLOCATED"),
        sa.CheckConstraint("quantity > 0", name="ck_allocations_quantity_positive"),
    )
    op.create_table(
        "fulfillments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="ALLOCATED"),
        sa.Column("picker_id", sa.String(100)),
        sa.Column("packed_at", sa.DateTime()),
        sa.UniqueConstraint("order_id", name="uq_fulfillments_order"),
    )
    op.create_table(
        "packages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("warehouses.id")),
        sa.Column("weight", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("dimensions", sa.String(100), nullable=False, server_default="UNKNOWN"),
        sa.Column("status", sa.String(30), nullable=False, server_default="PACKED"),
    )
    op.create_table(
        "shipments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("package_id", sa.Integer(), sa.ForeignKey("packages.id")),
        sa.Column("carrier", sa.String(80), nullable=False, server_default="MOCK_CARRIER"),
        sa.Column("tracking_number", sa.String(100), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="READY_TO_SHIP"),
        sa.Column("shipped_at", sa.DateTime()),
        sa.Column("delivered_at", sa.DateTime()),
        sa.UniqueConstraint("tracking_number", name="uq_shipments_tracking_number"),
    )
    op.create_table(
        "returns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("reason", sa.String(250), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="REQUESTED"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "return_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("return_id", sa.Integer(), sa.ForeignKey("returns.id"), nullable=False),
        sa.Column("order_item_id", sa.Integer(), sa.ForeignKey("order_items.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("condition", sa.String(30), nullable=False, server_default="GOOD"),
        sa.Column("restockable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("quantity > 0", name="ck_return_items_quantity_positive"),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(50), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("details", sa.String(1000), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("idx_inventory_product_warehouse", "inventory", ["product_id", "warehouse_id"])
    op.create_index("idx_inventory_available", "inventory", ["product_id", "available_quantity"])
    op.create_index("idx_orders_customer_status", "orders", ["customer_id", "status"])
    op.create_index("idx_order_items_order", "order_items", ["order_id"])
    op.create_index("idx_allocations_order", "allocations", ["order_id"])
    op.create_index("idx_movements_inventory_time", "inventory_movements", ["inventory_id", "created_at"])
    op.create_index("idx_shipments_status", "shipments", ["status"])
    op.create_index("idx_returns_order_status", "returns", ["order_id", "status"])


def downgrade() -> None:
    for table in (
        "audit_logs", "notifications", "return_items", "returns", "shipments",
        "packages", "fulfillments", "allocations", "order_items", "orders",
        "inventory_movements", "inventory", "warehouse_locations", "warehouses",
        "products", "users",
    ):
        op.drop_table(table)
