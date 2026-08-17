from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import ReturnOrder, ReturnItem, Order, OrderItem, Inventory

router = APIRouter(prefix="/returns", tags=["Returns"])

class ReturnItemIn(BaseModel):
    order_item_id: int
    quantity: int
    condition: str = "GOOD"
    restockable: bool = True

class ReturnIn(BaseModel):
    order_id: int
    reason: str
    items: list[ReturnItemIn]

@router.post("", status_code=201)
def create_return(data: ReturnIn, db: Session = Depends(get_db)):
    order = db.get(Order, data.order_id)
    if not order or order.status != "DELIVERED":
        raise HTTPException(409, "Only delivered orders can be returned")
    if not data.items:
        raise HTTPException(400, "At least one return item is required")
    r = ReturnOrder(order_id=order.id, reason=data.reason, status="REQUESTED")
    db.add(r); db.flush()
    for item in data.items:
        oi = db.get(OrderItem, item.order_item_id)
        if not oi or oi.order_id != order.id or item.quantity <= 0 or item.quantity > oi.quantity:
            db.rollback(); raise HTTPException(400, "Invalid return item or quantity")
        db.add(ReturnItem(return_id=r.id, order_item_id=oi.id, quantity=item.quantity, condition=item.condition, restockable=item.restockable))
    db.commit(); db.refresh(r); return r

@router.get("/{return_id}")
def get_return(return_id: int, db: Session = Depends(get_db)):
    r = db.get(ReturnOrder, return_id)
    if not r:
        raise HTTPException(404, "Return not found")
    items = db.query(ReturnItem).filter_by(return_id=return_id).all()
    return {"return": r, "items": items}

@router.post("/{return_id}/receive")
def receive_return(return_id: int, db: Session = Depends(get_db)):
    r = db.get(ReturnOrder, return_id)
    if not r or r.status != "REQUESTED":
        raise HTTPException(409, "Return must be in REQUESTED state")
    for item in db.query(ReturnItem).filter_by(return_id=return_id).all():
        if not item.restockable:
            continue
        oi = db.get(OrderItem, item.order_item_id)
        inv = db.query(Inventory).filter_by(product_id=oi.product_id).order_by(Inventory.available_quantity.desc()).first()
        if not inv:
            raise HTTPException(409, "No inventory location available for returned item")
        inv.on_hand_quantity += item.quantity
        inv.available_quantity += item.quantity
        inv.last_movement_at = datetime.utcnow()
    r.status = "RECEIVED"
    db.commit(); db.refresh(r); return r

@router.post("/{return_id}/refund")
def refund_return(return_id: int, db: Session = Depends(get_db)):
    r = db.get(ReturnOrder, return_id)
    if not r or r.status != "RECEIVED":
        raise HTTPException(409, "Return must be received before refund")
    r.status = "REFUNDED"
    db.commit(); db.refresh(r); return r
