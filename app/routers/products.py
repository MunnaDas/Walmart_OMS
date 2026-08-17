from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product
from pydantic import BaseModel

router = APIRouter(prefix="/products", tags=["Catalog"])
class ProductIn(BaseModel):
    sku: str
    name: str
    price: float

@router.post("", status_code=201)
def create_product(data: ProductIn, db: Session = Depends(get_db)):
    p = Product(**data.model_dump()); db.add(p); db.commit(); db.refresh(p); return p

@router.get("")
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()
