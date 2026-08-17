from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(40), default="CUSTOMER")
    password_hash: Mapped[str] = mapped_column(String(255), default="")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    price: Mapped[float] = mapped_column(Float)

class Warehouse(Base):
    __tablename__ = "warehouses"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    capacity: Mapped[int] = mapped_column(Integer, default=0)
    used_capacity: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")

class WarehouseLocation(Base):
    __tablename__ = "warehouse_locations"
    id: Mapped[int] = mapped_column(primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
    zone: Mapped[str] = mapped_column(String(50), default="DEFAULT")
    aisle: Mapped[str] = mapped_column(String(50), default="A")
    bin_code: Mapped[str] = mapped_column(String(64))
    capacity: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (UniqueConstraint("warehouse_id", "bin_code", name="uq_warehouse_bin"),)

class Inventory(Base):
    __tablename__ = "inventory"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
    bin_code: Mapped[str] = mapped_column(String(64), default="DEFAULT")
    on_hand_quantity: Mapped[int] = mapped_column(Integer, default=0)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)
    damaged_quantity: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=0)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_movement_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_warehouse"),)

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory.id"), index=True)
    movement_type: Mapped[str] = mapped_column(String(40))
    quantity: Mapped[int] = mapped_column(Integer)
    reference_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(40), default="CREATED", index=True)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)

class Allocation(Base):
    __tablename__ = "allocations"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="ALLOCATED")

class Fulfillment(Base):
    __tablename__ = "fulfillments"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    status: Mapped[str] = mapped_column(String(40), default="ALLOCATED")
    picker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    packed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class Package(Base):
    __tablename__ = "packages"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"), nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=0)
    dimensions: Mapped[str] = mapped_column(String(100), default="UNKNOWN")
    status: Mapped[str] = mapped_column(String(30), default="PACKED")

class Shipment(Base):
    __tablename__ = "shipments"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    package_id: Mapped[int | None] = mapped_column(ForeignKey("packages.id"), nullable=True)
    carrier: Mapped[str] = mapped_column(String(80), default="MOCK_CARRIER")
    tracking_number: Mapped[str] = mapped_column(String(100), unique=True)
    status: Mapped[str] = mapped_column(String(40), default="READY_TO_SHIP")
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class ReturnOrder(Base):
    __tablename__ = "returns"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    reason: Mapped[str] = mapped_column(String(250))
    status: Mapped[str] = mapped_column(String(40), default="REQUESTED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ReturnItem(Base):
    __tablename__ = "return_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    return_id: Mapped[int] = mapped_column(ForeignKey("returns.id"), index=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    condition: Mapped[str] = mapped_column(String(30), default="GOOD")
    restockable: Mapped[bool] = mapped_column(default=True)

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(80))
    message: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(80))
    details: Mapped[str] = mapped_column(String(1000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
