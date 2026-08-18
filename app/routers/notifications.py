from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.database import get_db
from app.models import Notification, User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationIn(BaseModel):
    user_id: int | None = None
    event_type: str
    message: str


@router.post("", status_code=201)
def create_notification(data: NotificationIn, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN"))):
    n = Notification(**data.model_dump())
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


@router.get("")
def list_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Notification).order_by(Notification.created_at.desc())
    if user.role != "ADMIN":
        query = query.filter(Notification.user_id == user.id)
    return query.limit(100).all()
