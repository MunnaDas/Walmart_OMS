from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.database import get_db
from app.models import Inventory, Warehouse, Order

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/inventory-aging")
def inventory_aging(db: Session = Depends(get_db)):
    rows = db.query(Inventory, Warehouse).join(Warehouse, Warehouse.id == Inventory.warehouse_id).all()
    return [{"warehouse": w.code, "product_id": i.product_id, "quantity": i.available_quantity, "age_days": (datetime.utcnow() - i.received_at).days} for i,w in rows]

@router.get("/warehouse-utilization")
def warehouse_utilization(db: Session = Depends(get_db)):
    return [{"warehouse": w.code, "capacity": w.capacity, "used": w.used_capacity, "utilization_pct": round((w.used_capacity / w.capacity) * 100, 2) if w.capacity else 0} for w in db.query(Warehouse).all()]

@router.get("/revenue")
def revenue(db: Session = Depends(get_db)):
    value = db.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(Order.status != "CANCELLED").scalar()
    count = db.query(func.count(Order.id)).filter(Order.status != "CANCELLED").scalar()
    return {"order_count": count, "revenue": float(value)}
