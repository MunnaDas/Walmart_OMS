from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Fulfillment, Order
from pydantic import BaseModel

router = APIRouter(prefix="/fulfillment", tags=["Fulfillment"])
class PickIn(BaseModel): picker_id: str

TRANSITIONS = {"ALLOCATED": {"PICKING"}, "PICKING": {"PICKED"}, "PICKED": {"PACKING"}, "PACKING": {"PACKED"}, "PACKED": {"READY_TO_SHIP"}}

def advance(f, target):
    if target not in TRANSITIONS.get(f.status, set()): raise HTTPException(409, f"Cannot transition {f.status} -> {target}")
    f.status = target

@router.get("/{fulfillment_id}")
def get_fulfillment(fulfillment_id: int, db: Session = Depends(get_db)):
    f = db.get(Fulfillment, fulfillment_id)
    if not f: raise HTTPException(404, "Fulfillment not found")
    return f

@router.post("/{fulfillment_id}/pick")
def pick(fulfillment_id: int, data: PickIn, db: Session = Depends(get_db)):
    f = db.get(Fulfillment, fulfillment_id)
    if not f: raise HTTPException(404, "Fulfillment not found")
    if f.status == "ALLOCATED": advance(f, "PICKING")
    elif f.status == "PICKING": advance(f, "PICKED"); f.picker_id = data.picker_id
    else: raise HTTPException(409, "Fulfillment is not in picking state")
    db.commit(); db.refresh(f); return f

@router.post("/{fulfillment_id}/pack")
def pack(fulfillment_id: int, db: Session = Depends(get_db)):
    f = db.get(Fulfillment, fulfillment_id)
    if not f: raise HTTPException(404, "Fulfillment not found")
    advance(f, "PACKING"); db.commit(); advance(f, "PACKED"); db.commit(); db.refresh(f); return f
