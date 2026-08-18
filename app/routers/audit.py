from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.database import get_db
from app.models import AuditLog, User

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("")
def audit_logs(db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN"))):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
