from decimal import Decimal
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.database import get_db
from app.models import Product, User

router = APIRouter(prefix="/products", tags=["Catalog"])


class ProductIn(BaseModel):
    sku: str
    name: str
    price: Decimal = Field(ge=0)


@router.post("", status_code=201)
def create_product(data: ProductIn, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN"))):
    p = Product(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("")
def list_products(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    return db.query(Product).order_by(Product.id).offset(offset).limit(limit).all()
