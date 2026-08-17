from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Warehouse, WarehouseLocation, Inventory, Product

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])

class WarehouseIn(BaseModel):
    code: str
    name: str
    capacity: int

class LocationIn(BaseModel):
    zone: str = "DEFAULT"
    aisle: str = "A"
    bin_code: str
    capacity: int = 0

class StockIn(BaseModel):
    product_id: int
    quantity: int
    bin_code: str = "DEFAULT"

@router.post("", status_code=201)
def create_warehouse(data: WarehouseIn, db: Session = Depends(get_db)):
    if data.capacity < 0: raise HTTPException(400, "Capacity cannot be negative")
    w = Warehouse(**data.model_dump()); db.add(w); db.commit(); db.refresh(w); return w

@router.get("")
def list_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()

@router.post("/{warehouse_id}/locations", status_code=201)
def create_location(warehouse_id: int, data: LocationIn, db: Session = Depends(get_db)):
    if not db.get(Warehouse, warehouse_id): raise HTTPException(404, "Warehouse not found")
    location = WarehouseLocation(warehouse_id=warehouse_id, **data.model_dump())
    db.add(location); db.commit(); db.refresh(location); return location

@router.get("/{warehouse_id}/locations")
def list_locations(warehouse_id: int, db: Session = Depends(get_db)):
    if not db.get(Warehouse, warehouse_id): raise HTTPException(404, "Warehouse not found")
    return db.query(WarehouseLocation).filter_by(warehouse_id=warehouse_id).all()

@router.post("/{warehouse_id}/stock", status_code=201)
def add_stock(warehouse_id: int, data: StockIn, db: Session = Depends(get_db)):
    if data.quantity <= 0: raise HTTPException(400, "Quantity must be positive")
    w = db.get(Warehouse, warehouse_id); p = db.get(Product, data.product_id)
    if not w or not p: raise HTTPException(404, "Warehouse or product not found")
    if w.capacity and w.used_capacity + data.quantity > w.capacity:
        raise HTTPException(409, "Warehouse capacity exceeded")
    inv = db.query(Inventory).filter_by(warehouse_id=warehouse_id, product_id=data.product_id).first()
    if not inv:
        inv = Inventory(warehouse_id=warehouse_id, product_id=data.product_id, bin_code=data.bin_code); db.add(inv)
    inv.on_hand_quantity += data.quantity
    inv.available_quantity += data.quantity
    w.used_capacity += data.quantity
    db.commit(); db.refresh(inv); return inv
