from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])
class NotificationIn(BaseModel):
    user_id: int | None = None
    event_type: str
    message: str

@router.post("", status_code=201)
def create_notification(data: NotificationIn, db: Session = Depends(get_db)):
    n = Notification(**data.model_dump()); db.add(n); db.commit(); db.refresh(n); return n

@router.get("")
def list_notifications(db: Session = Depends(get_db)):
    return db.query(Notification).order_by(Notification.created_at.desc()).limit(100).all()
