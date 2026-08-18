from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.database import get_db
from app.models import Inventory, InventoryMovement, User

router = APIRouter(prefix="/inventory", tags=["Inventory"])


class ReservationIn(BaseModel):
    product_id: int
    warehouse_id: int
    quantity: int = Field(gt=0)
    reference_id: str | None = None


@router.get("/{product_id}")
def inventory(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    return db.query(Inventory).filter_by(product_id=product_id).all()


@router.post("/reserve")
def reserve(data: ReservationIn, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    q = db.query(Inventory).filter_by(product_id=data.product_id, warehouse_id=data.warehouse_id)
    if db.bind.dialect.name == "postgresql":
        q = q.with_for_update()
    inv = q.first()
    if not inv or inv.available_quantity < data.quantity:
        raise HTTPException(409, "Insufficient inventory")
    inv.available_quantity -= data.quantity
    inv.reserved_quantity += data.quantity
    inv.last_movement_at = datetime.utcnow()
    db.add(InventoryMovement(inventory_id=inv.id, movement_type="RESERVATION", quantity=data.quantity, reference_type="ORDER", reference_id=data.reference_id))
    db.commit()
    db.refresh(inv)
    return {"reserved": data.quantity, "available": inv.available_quantity, "reserved_total": inv.reserved_quantity, "warehouse_id": inv.warehouse_id}


@router.post("/release")
def release(data: ReservationIn, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    q = db.query(Inventory).filter_by(product_id=data.product_id, warehouse_id=data.warehouse_id)
    if db.bind.dialect.name == "postgresql":
        q = q.with_for_update()
    inv = q.first()
    if not inv or inv.reserved_quantity < data.quantity:
        raise HTTPException(409, "Invalid reservation")
    inv.reserved_quantity -= data.quantity
    inv.available_quantity += data.quantity
    inv.last_movement_at = datetime.utcnow()
    db.add(InventoryMovement(inventory_id=inv.id, movement_type="RELEASE", quantity=data.quantity, reference_type="ORDER", reference_id=data.reference_id))
    db.commit()
    db.refresh(inv)
    return inv


@router.get("/{product_id}/movements")
def movements(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    ids = [row.id for row in db.query(Inventory).filter_by(product_id=product_id).all()]
    if not ids:
        return []
    return db.query(InventoryMovement).filter(InventoryMovement.inventory_id.in_(ids)).order_by(InventoryMovement.created_at.desc()).limit(500).all()
