from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.database import get_db
from app.models import Inventory, InventoryMovement, Product, User, Warehouse, WarehouseLocation

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


class WarehouseIn(BaseModel):
    code: str
    name: str
    capacity: int = Field(ge=0)


class LocationIn(BaseModel):
    zone: str = "DEFAULT"
    aisle: str = "A"
    bin_code: str
    capacity: int = Field(default=0, ge=0)


class StockIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    bin_code: str = "DEFAULT"


@router.post("", status_code=201)
def create_warehouse(data: WarehouseIn, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN"))):
    warehouse = Warehouse(**data.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.get("")
def list_warehouses(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    return db.query(Warehouse).order_by(Warehouse.id).offset(offset).limit(limit).all()


@router.post("/{warehouse_id}/locations", status_code=201)
def create_location(warehouse_id: int, data: LocationIn, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    if not db.get(Warehouse, warehouse_id):
        raise HTTPException(404, "Warehouse not found")
    location = WarehouseLocation(warehouse_id=warehouse_id, **data.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.get("/{warehouse_id}/locations")
def list_locations(warehouse_id: int, db: Session = Depends(get_db)):
    if not db.get(Warehouse, warehouse_id):
        raise HTTPException(404, "Warehouse not found")
    return db.query(WarehouseLocation).filter_by(warehouse_id=warehouse_id).order_by(WarehouseLocation.id).all()


@router.post("/{warehouse_id}/stock", status_code=201)
def add_stock(warehouse_id: int, data: StockIn, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    warehouse = db.get(Warehouse, warehouse_id)
    product = db.get(Product, data.product_id)
    if not warehouse or not product:
        raise HTTPException(404, "Warehouse or product not found")

    query = db.query(Warehouse).filter(Warehouse.id == warehouse_id)
    if db.bind.dialect.name == "postgresql":
        query = query.with_for_update()
    warehouse = query.one()

    if warehouse.capacity and warehouse.used_capacity + data.quantity > warehouse.capacity:
        raise HTTPException(409, "Warehouse capacity exceeded")

    inv = db.query(Inventory).filter_by(warehouse_id=warehouse_id, product_id=data.product_id).first()
    if not inv:
        inv = Inventory(warehouse_id=warehouse_id, product_id=data.product_id, bin_code=data.bin_code)
        db.add(inv)
        db.flush()

    inv.on_hand_quantity += data.quantity
    inv.available_quantity += data.quantity
    inv.last_movement_at = datetime.utcnow()
    warehouse.used_capacity += data.quantity
    db.add(InventoryMovement(inventory_id=inv.id, movement_type="RECEIPT", quantity=data.quantity, reference_type="WAREHOUSE_RECEIPT", reference_id=str(warehouse_id)))
    db.commit()
    db.refresh(inv)
    return inv
