from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.security import hash_password, require_roles
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/users", tags=["Users"])


class UserIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "CUSTOMER"


@router.post("", status_code=201)
def create_user(data: UserIn, db: Session = Depends(get_db), current_user: User | None = Depends(lambda: None)):
    if len(data.password) < 8:
        raise HTTPException(400, "Password must contain at least 8 characters")
    if data.role not in {"CUSTOMER", "WAREHOUSE_OPERATOR", "ADMIN"}:
        raise HTTPException(400, "Invalid user role")
    if db.query(User).count() and data.role != "CUSTOMER":
        raise HTTPException(403, "Only an administrator can create privileged users")
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(409, "Email already registered")
    user = User(name=data.name, email=data.email, role=data.role, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


@router.get("")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN"))):
    users = db.query(User).order_by(User.id).all()
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users]
