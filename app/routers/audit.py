from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit"])
@router.get("")
def audit_logs(db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
