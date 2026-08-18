from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.database import get_db
from app.models import Fulfillment, Order, Package, Shipment, User

router = APIRouter(prefix="/shipments", tags=["Shipments"])
TRANSITIONS = {"READY_TO_SHIP": "SHIPPED", "SHIPPED": "IN_TRANSIT", "IN_TRANSIT": "OUT_FOR_DELIVERY", "OUT_FOR_DELIVERY": "DELIVERED"}


@router.post("", status_code=201)
def create_shipment(order_id: int, carrier: str = "MOCK_CARRIER", db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    order = db.get(Order, order_id)
    f = db.query(Fulfillment).filter_by(order_id=order_id).first()
    package = db.query(Package).filter_by(order_id=order_id).order_by(Package.id.desc()).first()
    if not order or not f or not package:
        raise HTTPException(404, "Order, fulfillment or package not found")
    if f.status != "PACKED" or order.status != "PACKED":
        raise HTTPException(409, "Order must be packed")
    existing = db.query(Shipment).filter_by(order_id=order_id).first()
    if existing:
        return existing
    s = Shipment(order_id=order_id, package_id=package.id, carrier=carrier, tracking_number=f"OMS-{uuid.uuid4().hex[:12].upper()}", status="READY_TO_SHIP")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/{shipment_id}")
def get_shipment(shipment_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Shipment not found")
    return s


@router.post("/{shipment_id}/advance")
def advance_shipment(shipment_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(404, "Shipment not found")
    target = TRANSITIONS.get(s.status)
    if not target:
        raise HTTPException(409, f"Shipment already in terminal state: {s.status}")
    s.status = target
    order = db.get(Order, s.order_id)
    if target == "SHIPPED":
        s.shipped_at = datetime.utcnow()
        order.status = "SHIPPED"
    elif target == "DELIVERED":
        s.delivered_at = datetime.utcnow()
        order.status = "DELIVERED"
    db.commit()
    db.refresh(s)
    return s
