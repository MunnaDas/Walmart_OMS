from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order, OrderItem, Inventory, Allocation, Fulfillment, Product
from pydantic import BaseModel

router = APIRouter(prefix="/orders", tags=["Orders"])

class ItemIn(BaseModel):
    product_id: int
    quantity: int

class OrderIn(BaseModel):
    customer_id: str
    items: list[ItemIn]

@router.post("", status_code=201)
def create_order(data: OrderIn, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), db: Session = Depends(get_db)):
    if not data.items:
        raise HTTPException(400, "Order must contain items")
    if idempotency_key:
        existing = db.query(Order).filter_by(idempotency_key=idempotency_key).first()
        if existing:
            return existing
    try:
        order = Order(customer_id=data.customer_id, idempotency_key=idempotency_key)
        db.add(order); db.flush()
        total = 0.0
        for item in data.items:
            if item.quantity <= 0:
                raise HTTPException(400, "Quantity must be positive")
            p = db.get(Product, item.product_id)
            if not p:
                raise HTTPException(404, f"Product {item.product_id} not found")
            oi = OrderItem(order_id=order.id, product_id=p.id, quantity=item.quantity, unit_price=p.price)
            db.add(oi); db.flush()
            remaining = item.quantity
            q = db.query(Inventory).filter(Inventory.product_id == p.id, Inventory.available_quantity > 0).order_by(Inventory.available_quantity.desc())
            if db.bind.dialect.name == "postgresql":
                q = q.with_for_update()
            for stock in q.all():
                if remaining <= 0:
                    break
                take = min(remaining, stock.available_quantity)
                stock.available_quantity -= take
                stock.reserved_quantity += take
                stock.last_movement_at = __import__("datetime").datetime.utcnow()
                db.add(Allocation(order_id=order.id, order_item_id=oi.id, warehouse_id=stock.warehouse_id, quantity=take))
                remaining -= take
            if remaining:
                raise HTTPException(409, f"Insufficient inventory for {p.sku}")
            total += p.price * item.quantity
        order.total_amount = total
        order.status = "ALLOCATED"
        db.add(Fulfillment(order_id=order.id, status="ALLOCATED"))
        db.commit(); db.refresh(order)
        return order
    except HTTPException:
        db.rollback(); raise
    except Exception:
        db.rollback(); raise

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
        for a in db.query(Allocation).filter_by(order_id=order_id, status="ALLOCATED").all():
            oi = db.get(OrderItem, a.order_item_id)
            q = db.query(Inventory).filter_by(product_id=oi.product_id, warehouse_id=a.warehouse_id)
            if db.bind.dialect.name == "postgresql": q = q.with_for_update()
            stock = q.first()
            if not stock or stock.reserved_quantity < a.quantity:
                raise HTTPException(409, "Reservation state is inconsistent")
            stock.reserved_quantity -= a.quantity
            stock.available_quantity += a.quantity
            a.status = "RELEASED"
        order.status = "CANCELLED"
        db.commit(); db.refresh(order)
        return order
    except HTTPException:
        db.rollback(); raise
