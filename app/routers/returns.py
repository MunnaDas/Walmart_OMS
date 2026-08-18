from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.database import get_db
from app.models import Allocation, Inventory, InventoryMovement, Order, OrderItem, ReturnItem, ReturnOrder, User

router = APIRouter(prefix="/returns", tags=["Returns"])


class ReturnItemIn(BaseModel):
    order_item_id: int
    quantity: int = Field(gt=0)
    condition: str = "GOOD"
    restockable: bool = True


class ReturnIn(BaseModel):
    order_id: int
    reason: str
    items: list[ReturnItemIn]


@router.post("", status_code=201)
def create_return(data: ReturnIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.get(Order, data.order_id)
    if not order or order.status != "DELIVERED":
        raise HTTPException(409, "Only delivered orders can be returned")
    if user.role != "ADMIN" and order.customer_id != user.id:
        raise HTTPException(403, "You can only return your own orders")
    if not data.items:
        raise HTTPException(400, "At least one return item is required")
    try:
        return_order = ReturnOrder(order_id=order.id, reason=data.reason, status="REQUESTED")
        db.add(return_order)
        db.flush()
        requested_by_item: dict[int, int] = {}
        for item in data.items:
            requested_by_item[item.order_item_id] = requested_by_item.get(item.order_item_id, 0) + item.quantity
        for order_item_id, requested_quantity in requested_by_item.items():
            order_item = db.get(OrderItem, order_item_id)
            if not order_item or order_item.order_id != order.id:
                raise HTTPException(400, "Invalid return item")
            already_returned = db.query(ReturnItem).join(ReturnOrder, ReturnOrder.id == ReturnItem.return_id).filter(ReturnOrder.order_id == order.id, ReturnItem.order_item_id == order_item_id, ReturnOrder.status != "CANCELLED").with_for_update().all()
            returned_quantity = sum(item.quantity for item in already_returned)
            if requested_quantity > order_item.quantity - returned_quantity:
                raise HTTPException(409, f"Return quantity exceeds remaining returnable quantity for order item {order_item_id}")
        for item in data.items:
            db.add(ReturnItem(return_id=return_order.id, order_item_id=item.order_item_id, quantity=item.quantity, condition=item.condition, restockable=item.restockable))
        db.commit()
        db.refresh(return_order)
        return return_order
    except HTTPException:
        db.rollback()
        raise


@router.get("/{return_id}")
def get_return(return_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return_order = db.get(ReturnOrder, return_id)
    if not return_order:
        raise HTTPException(404, "Return not found")
    order = db.get(Order, return_order.order_id)
    if user.role != "ADMIN" and (not order or order.customer_id != user.id):
        raise HTTPException(403, "You do not have access to this return")
    items = db.query(ReturnItem).filter_by(return_id=return_id).all()
    return {"return": return_order, "items": items}


@router.post("/{return_id}/receive")
def receive_return(return_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    return_order = db.get(ReturnOrder, return_id)
    if not return_order or return_order.status != "REQUESTED":
        raise HTTPException(409, "Return must be in REQUESTED state")
    try:
        for item in db.query(ReturnItem).filter_by(return_id=return_id).all():
            if not item.restockable:
                continue
            order_item = db.get(OrderItem, item.order_item_id)
            allocations = db.query(Allocation).filter_by(order_item_id=order_item.id).order_by(Allocation.id).all()
            remaining = item.quantity
            for allocation in allocations:
                if remaining <= 0:
                    break
                query = db.query(Inventory).filter_by(product_id=order_item.product_id, warehouse_id=allocation.warehouse_id)
                if db.bind.dialect.name == "postgresql":
                    query = query.with_for_update()
                inventory = query.first()
                if not inventory:
                    continue
                take = min(remaining, allocation.quantity)
                inventory.on_hand_quantity += take
                inventory.available_quantity += take
                inventory.last_movement_at = datetime.utcnow()
                db.add(InventoryMovement(inventory_id=inventory.id, movement_type="RETURN", quantity=take, reference_type="RETURN", reference_id=str(return_order.id)))
                remaining -= take
            if remaining:
                raise HTTPException(409, "No matching fulfillment inventory location available for returned item")
        return_order.status = "RECEIVED"
        db.commit()
        db.refresh(return_order)
        return return_order
    except HTTPException:
        db.rollback()
        raise


@router.post("/{return_id}/refund")
def refund_return(return_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN"))):
    return_order = db.get(ReturnOrder, return_id)
    if not return_order or return_order.status != "RECEIVED":
        raise HTTPException(409, "Return must be received before refund")
    return_order.status = "REFUNDED"
    db.commit()
    db.refresh(return_order)
    return return_order
