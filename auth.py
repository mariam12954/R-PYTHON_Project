from app.models.user import User
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserOut, Token
from app.services.auth_service import register_user, login_user
from app.core.database import get_db
from pydantic import BaseModel
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register", response_model=UserOut, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    return register_user(db, user_data)

@router.post("/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    return login_user(db, credentials.username, credentials.password)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user