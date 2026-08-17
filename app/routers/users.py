from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/users", tags=["Users"])
class UserIn(BaseModel):
    name: str
    email: str
    role: str = "CUSTOMER"

@router.post("", status_code=201)
def create_user(data: UserIn, db: Session = Depends(get_db)):
    user = User(**data.model_dump()); db.add(user); db.commit(); db.refresh(user); return user

@router.get("")
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()
