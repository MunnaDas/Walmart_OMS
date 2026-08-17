from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Shipment, Order, Fulfillment
import uuid

router = APIRouter(prefix="/shipments", tags=["Shipments"])

@router.post("", status_code=201)
def create_shipment(order_id: int, carrier: str = "MOCK_CARRIER", db: Session = Depends(get_db)):
    order = db.get(Order, order_id); f = db.query(Fulfillment).filter_by(order_id=order_id).first()
    if not order or not f: raise HTTPException(404, "Order or fulfillment not found")
    if f.status != "PACKED": raise HTTPException(409, "Order must be packed")
    s = Shipment(order_id=order_id, carrier=carrier, tracking_number=f"OMS-{uuid.uuid4().hex[:12].upper()}", status="SHIPPED", shipped_at=datetime.utcnow())
    order.status = "SHIPPED"; db.add(s); db.commit(); db.refresh(s); return s

@router.get("/{shipment_id}")
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    s = db.get(Shipment, shipment_id)
    if not s: raise HTTPException(404, "Shipment not found")
    return s

@router.post("/{shipment_id}/deliver")
def deliver(shipment_id: int, db: Session = Depends(get_db)):
    s = db.get(Shipment, shipment_id)
    if not s: raise HTTPException(404, "Shipment not found")
    s.status = "DELIVERED"; order = db.get(Order, s.order_id); order.status = "DELIVERED"; db.commit(); return s
