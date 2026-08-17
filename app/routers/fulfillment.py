from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Fulfillment, Order, Package
from pydantic import BaseModel

router = APIRouter(prefix="/fulfillment", tags=["Fulfillment"])

class PickIn(BaseModel):
    picker_id: str

class PackIn(BaseModel):
    weight: float = 0
    dimensions: str = "UNKNOWN"

TRANSITIONS = {
    "ALLOCATED": "PICKING",
    "PICKING": "PICKED",
    "PICKED": "PACKING",
    "PACKING": "PACKED",
    "PACKED": "READY_TO_SHIP",
}
ORDER_STATUS = {
    "PICKING": "PICKING", "PICKED": "PICKED", "PACKING": "PACKING",
    "PACKED": "PACKED", "READY_TO_SHIP": "READY_TO_SHIP"
}

def advance(f, target):
    if TRANSITIONS.get(f.status) != target:
        raise HTTPException(409, f"Cannot transition {f.status} -> {target}")
    f.status = target

@router.get("/{fulfillment_id}")
def get_fulfillment(fulfillment_id: int, db: Session = Depends(get_db)):
    f = db.get(Fulfillment, fulfillment_id)
    if not f:
        raise HTTPException(404, "Fulfillment not found")
    return f

@router.post("/{fulfillment_id}/start-picking")
def start_picking(fulfillment_id: int, data: PickIn, db: Session = Depends(get_db)):
    f = db.get(Fulfillment, fulfillment_id)
    if not f:
        raise HTTPException(404, "Fulfillment not found")
    advance(f, "PICKING")
    f.picker_id = data.picker_id
    order = db.get(Order, f.order_id); order.status = "PICKING"
    db.commit(); db.refresh(f); return f

@router.post("/{fulfillment_id}/complete-picking")
def complete_picking(fulfillment_id: int, db: Session = Depends(get_db)):
    f = db.get(Fulfillment, fulfillment_id)
    if not f:
        raise HTTPException(404, "Fulfillment not found")
    advance(f, "PICKED")
    db.get(Order, f.order_id).status = "PICKED"
    db.commit(); db.refresh(f); return f

@router.post("/{fulfillment_id}/start-packing")
def start_packing(fulfillment_id: int, db: Session = Depends(get_db)):
    f = db.get(Fulfillment, fulfillment_id)
    if not f:
        raise HTTPException(404, "Fulfillment not found")
    advance(f, "PACKING")
    db.get(Order, f.order_id).status = "PACKING"
    db.commit(); db.refresh(f); return f

@router.post("/{fulfillment_id}/pack")
def pack(fulfillment_id: int, data: PackIn, db: Session = Depends(get_db)):
    f = db.get(Fulfillment, fulfillment_id)
    if not f:
        raise HTTPException(404, "Fulfillment not found")
    advance(f, "PACKED")
    order = db.get(Order, f.order_id)
    package = Package(order_id=order.id, weight=data.weight, dimensions=data.dimensions, status="PACKED")
    db.add(package)
    f.packed_at = datetime.utcnow()
    order.status = "PACKED"
    db.commit(); db.refresh(package); db.refresh(f)
    return {"fulfillment": f, "package": package}
