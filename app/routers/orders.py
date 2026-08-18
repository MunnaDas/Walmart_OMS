import hashlib
import json
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Allocation, Fulfillment, Inventory, InventoryMovement, Order, OrderItem, Product

router = APIRouter(prefix="/orders", tags=["Orders"])


class ItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderIn(BaseModel):
    customer_id: int
    items: list[ItemIn]


def request_hash(data: OrderIn) -> str:
    canonical = json.dumps(data.model_dump(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@router.post("", status_code=201)
def create_order(
    data: OrderIn,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    if not data.items:
        raise HTTPException(400, "Order must contain items")

    payload_hash = request_hash(data)
    if idempotency_key:
        existing = db.query(Order).filter_by(idempotency_key=idempotency_key).first()
        if existing:
            if existing.idempotency_request_hash != payload_hash:
                raise HTTPException(409, "Idempotency-Key was already used with a different request")
            return existing

    try:
        order = Order(
            customer_id=data.customer_id,
            idempotency_key=idempotency_key,
            idempotency_request_hash=payload_hash if idempotency_key else None,
        )
        db.add(order)
        db.flush()

        total = Decimal("0.00")
        for item in data.items:
            product = db.get(Product, item.product_id)
            if not product:
                raise HTTPException(404, f"Product {item.product_id} not found")

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.price,
            )
            db.add(order_item)
            db.flush()

            remaining = item.quantity
            query = (
                db.query(Inventory)
                .filter(
                    Inventory.product_id == product.id,
                    Inventory.available_quantity > 0,
                )
                .order_by(Inventory.available_quantity.desc(), Inventory.id)
            )
            if db.bind.dialect.name == "postgresql":
                query = query.with_for_update()

            for stock in query.all():
                if remaining <= 0:
                    break
                take = min(remaining, stock.available_quantity)
                stock.available_quantity -= take
                stock.reserved_quantity += take
                stock.last_movement_at = datetime.utcnow()
                db.add(
                    Allocation(
                        order_id=order.id,
                        order_item_id=order_item.id,
                        warehouse_id=stock.warehouse_id,
                        quantity=take,
                    )
                )
                db.add(
                    InventoryMovement(
                        inventory_id=stock.id,
                        movement_type="RESERVATION",
                        quantity=take,
                        reference_type="ORDER",
                        reference_id=str(order.id),
                    )
                )
                remaining -= take

            if remaining:
                raise HTTPException(409, f"Insufficient inventory for {product.sku}")
            total += product.price * item.quantity

        order.total_amount = total
        order.status = "ALLOCATED"
        db.add(Fulfillment(order_id=order.id, status="ALLOCATED"))
        db.commit()
        db.refresh(order)
        return order
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        if idempotency_key:
            existing = db.query(Order).filter_by(idempotency_key=idempotency_key).first()
            if existing:
                if existing.idempotency_request_hash != payload_hash:
                    raise HTTPException(409, "Idempotency-Key was already used with a different request")
                return existing
        raise HTTPException(409, "Order could not be created because of a concurrent or duplicate request")
    except Exception:
        db.rollback()
        raise


@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order


@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status in {"SHIPPED", "DELIVERED", "CANCELLED"}:
        raise HTTPException(409, "Order cannot be cancelled")
    try:
        for allocation in db.query(Allocation).filter_by(order_id=order_id, status="ALLOCATED").all():
            order_item = db.get(OrderItem, allocation.order_item_id)
            query = db.query(Inventory).filter_by(
                product_id=order_item.product_id,
                warehouse_id=allocation.warehouse_id,
            )
            if db.bind.dialect.name == "postgresql":
                query = query.with_for_update()
            stock = query.first()
            if not stock or stock.reserved_quantity < allocation.quantity:
                raise HTTPException(409, "Reservation state is inconsistent")
            stock.reserved_quantity -= allocation.quantity
            stock.available_quantity += allocation.quantity
            stock.last_movement_at = datetime.utcnow()
            allocation.status = "RELEASED"
            db.add(
                InventoryMovement(
                    inventory_id=stock.id,
                    movement_type="RELEASE",
                    quantity=allocation.quantity,
                    reference_type="ORDER",
                    reference_id=str(order.id),
                )
            )
        order.status = "CANCELLED"
        db.commit()
        db.refresh(order)
        return order
    except HTTPException:
        db.rollback()
        raise
