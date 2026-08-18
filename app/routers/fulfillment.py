from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.database import get_db
from app.models import Fulfillment, User
from app.services.fulfillment_service import FulfillmentService

router = APIRouter(prefix="/fulfillment", tags=["Fulfillment"])


class PickIn(BaseModel):
    picker_id: str


class PackIn(BaseModel):
    weight: Decimal = Field(default=Decimal("0.00"), ge=0)
    dimensions: str = "UNKNOWN"


def get_service(db: Session) -> FulfillmentService:
    return FulfillmentService(db)


@router.get("/{fulfillment_id}")
def get_fulfillment(fulfillment_id: int, db: Session = Depends(get_db)):
    f = db.get(Fulfillment, fulfillment_id)
    if not f:
        raise HTTPException(404, "Fulfillment not found")
    return f


@router.post("/{fulfillment_id}/start-picking")
def start_picking(fulfillment_id: int, data: PickIn, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    service = get_service(db)
    f = service.get(fulfillment_id)
    if not f:
        raise HTTPException(404, "Fulfillment not found")
    try:
        service.start_picking(f, data.picker_id)
        db.commit()
        db.refresh(f)
        return f
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc))


@router.post("/{fulfillment_id}/complete-picking")
def complete_picking(fulfillment_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    service = get_service(db)
    f = service.get(fulfillment_id)
    if not f:
        raise HTTPException(404, "Fulfillment not found")
    try:
        service.complete_picking(f)
        db.commit()
        db.refresh(f)
        return f
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc))


@router.post("/{fulfillment_id}/start-packing")
def start_packing(fulfillment_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    service = get_service(db)
    f = service.get(fulfillment_id)
    if not f:
        raise HTTPException(404, "Fulfillment not found")
    try:
        service.start_packing(f)
        db.commit()
        db.refresh(f)
        return f
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc))


@router.post("/{fulfillment_id}/pack")
def pack(fulfillment_id: int, data: PackIn, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN", "WAREHOUSE_OPERATOR"))):
    service = get_service(db)
    f = service.get(fulfillment_id)
    if not f:
        raise HTTPException(404, "Fulfillment not found")
    try:
        package = service.pack(f, data.weight, data.dimensions)
        db.commit()
        db.refresh(package)
        db.refresh(f)
        return {"fulfillment": f, "package": package}
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc))
