from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Warehouse, Inventory, Product
from pydantic import BaseModel

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])
class WarehouseIn(BaseModel):
    code: str
    name: str
    capacity: int

class StockIn(BaseModel):
    product_id: int
    quantity: int
    bin_code: str = "DEFAULT"

@router.post("", status_code=201)
def create_warehouse(data: WarehouseIn, db: Session = Depends(get_db)):
    w = Warehouse(**data.model_dump()); db.add(w); db.commit(); db.refresh(w); return w

@router.get("")
def list_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()

@router.post("/{warehouse_id}/stock", status_code=201)
def add_stock(warehouse_id: int, data: StockIn, db: Session = Depends(get_db)):
    if not db.get(Warehouse, warehouse_id) or not db.get(Product, data.product_id): raise HTTPException(404, "Warehouse or product not found")
    inv = db.query(Inventory).filter_by(warehouse_id=warehouse_id, product_id=data.product_id).first()
    if not inv: inv = Inventory(warehouse_id=warehouse_id, product_id=data.product_id, bin_code=data.bin_code); db.add(inv)
    inv.available_quantity += data.quantity
    db.commit(); db.refresh(inv); return inv
