from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ReturnOrder, Order
from pydantic import BaseModel

router = APIRouter(prefix="/returns", tags=["Returns"])
class ReturnIn(BaseModel):
    order_id: int
    reason: str

@router.post("", status_code=201)
def create_return(data: ReturnIn, db: Session = Depends(get_db)):
    order = db.get(Order, data.order_id)
    if not order or order.status != "DELIVERED": raise HTTPException(409, "Only delivered orders can be returned")
    r = ReturnOrder(**data.model_dump()); db.add(r); db.commit(); db.refresh(r); return r

@router.get("/{return_id}")
def get_return(return_id: int, db: Session = Depends(get_db)):
    r = db.get(ReturnOrder, return_id)
    if not r: raise HTTPException(404, "Return not found")
    return r

@router.post("/{return_id}/receive")
def receive_return(return_id: int, db: Session = Depends(get_db)):
    r = db.get(ReturnOrder, return_id)
    if not r: raise HTTPException(404, "Return not found")
    r.status = "RECEIVED"; db.commit(); return r

@router.post("/{return_id}/refund")
def refund_return(return_id: int, db: Session = Depends(get_db)):
    r = db.get(ReturnOrder, return_id)
    if not r or r.status != "RECEIVED": raise HTTPException(409, "Return must be received first")
    r.status = "REFUNDED"; db.commit(); return r
