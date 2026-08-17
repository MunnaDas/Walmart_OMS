from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import Order, OrderItem, Inventory, Allocation, Fulfillment, Product, Warehouse
from pydantic import BaseModel

router = APIRouter(prefix="/orders", tags=["Orders"])
class ItemIn(BaseModel):
    product_id: int
    quantity: int
class OrderIn(BaseModel):
    customer_id: str
    items: list[ItemIn]

@router.post("", status_code=201)
def create_order(data: OrderIn, db: Session = Depends(get_db)):
    if not data.items: raise HTTPException(400, "Order must contain items")
    order = Order(customer_id=data.customer_id); db.add(order); db.flush()
    total = 0
    for item in data.items:
        p = db.get(Product, item.product_id)
        if not p or item.quantity <= 0: db.rollback(); raise HTTPException(400, "Invalid product or quantity")
        inv = db.query(Inventory).filter_by(product_id=p.id).order_by(Inventory.available_quantity.desc())
        remaining = item.quantity
        oi = OrderItem(order_id=order.id, product_id=p.id, quantity=item.quantity, unit_price=p.price); db.add(oi); db.flush()
        for stock in inv.with_for_update() if db.bind.dialect.name == "postgresql" else inv:
            if remaining <= 0: break
            take = min(remaining, stock.available_quantity)
            if take: stock.available_quantity -= take; stock.reserved_quantity += take; db.add(Allocation(order_id=order.id, order_item_id=oi.id, warehouse_id=stock.warehouse_id, quantity=take)); remaining -= take
        if remaining: db.rollback(); raise HTTPException(409, f"Insufficient inventory for {p.sku}")
        total += p.price * item.quantity
    order.total_amount = total; order.status = "ALLOCATED"
    db.add(Fulfillment(order_id=order.id, status="ALLOCATED")); db.commit(); db.refresh(order); return order

@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order: raise HTTPException(404, "Order not found")
    return order

@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order: raise HTTPException(404, "Order not found")
    if order.status in {"SHIPPED", "DELIVERED", "CANCELLED"}: raise HTTPException(409, "Order cannot be cancelled")
    allocations = db.query(Allocation).filter_by(order_id=order_id).all()
    for a in allocations:
        inv = db.query(Inventory).filter_by(product_id=db.get(OrderItem, a.order_item_id).product_id, warehouse_id=a.warehouse_id).with_for_update() if db.bind.dialect.name == "postgresql" else db.query(Inventory).filter_by(product_id=db.get(OrderItem, a.order_item_id).product_id, warehouse_id=a.warehouse_id)
        stock = inv.first(); stock.reserved_quantity -= a.quantity; stock.available_quantity += a.quantity; a.status = "RELEASED"
    order.status = "CANCELLED"; db.commit(); return order
