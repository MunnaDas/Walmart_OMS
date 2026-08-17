from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Inventory, Product
from pydantic import BaseModel

router = APIRouter(prefix="/inventory", tags=["Inventory"])
class ReservationIn(BaseModel):
    product_id: int
    warehouse_id: int
    quantity: int

@router.get("/{product_id}")
def inventory(product_id: int, db: Session = Depends(get_db)):
    return db.query(Inventory).filter_by(product_id=product_id).all()

@router.post("/reserve")
def reserve(data: ReservationIn, db: Session = Depends(get_db)):
    if data.quantity <= 0: raise HTTPException(400, "Quantity must be positive")
    # PostgreSQL row-level lock prevents two concurrent orders from reserving the same stock.
    q = db.query(Inventory).filter_by(product_id=data.product_id, warehouse_id=data.warehouse_id)
    if db.bind.dialect.name == "postgresql": q = q.with_for_update()
    inv = q.first()
    if not inv or inv.available_quantity < data.quantity: raise HTTPException(409, "Insufficient inventory")
    inv.available_quantity -= data.quantity; inv.reserved_quantity += data.quantity
    db.commit(); db.refresh(inv)
    return {"reserved": data.quantity, "available": inv.available_quantity, "warehouse_id": inv.warehouse_id}

@router.post("/release")
def release(data: ReservationIn, db: Session = Depends(get_db)):
    q = db.query(Inventory).filter_by(product_id=data.product_id, warehouse_id=data.warehouse_id)
    if db.bind.dialect.name == "postgresql": q = q.with_for_update()
    inv = q.first()
    if not inv or inv.reserved_quantity < data.quantity: raise HTTPException(409, "Invalid reservation")
    inv.reserved_quantity -= data.quantity; inv.available_quantity += data.quantity
    db.commit(); db.refresh(inv); return inv
