import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User
from app.schemas.user import UserCreate, TokenData
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
logger = logging.getLogger("app.auth")

def register_user(db: Session, user_data: UserCreate) -> User:
    if db.query(User).filter(User.username == user_data.username).first():
        logger.warning("Registration failed: username exists username=%s", user_data.username)
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == user_data.email).first():
        logger.warning("Registration failed: email exists email=%s", user_data.email)
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("User registered user_id=%s username=%s role=%s", user.id, user.username, user.role)
    return user

def login_user(db: Session, username: str, password: str) -> dict:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        logger.warning("Login failed username=%s", username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        logger.warning("Login failed (inactive) username=%s", username)
        raise HTTPException(status_code=403, detail="Account is inactive")

    token = create_access_token({"sub": user.username, "role": user.role})
    logger.info("Login success user_id=%s username=%s", user.id, user.username)
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    if not payload:
        logger.warning("Token validation failed")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        logger.warning("Token user not found username=%s", payload.get("sub"))
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        logger.warning("Admin access denied user_id=%s", current_user.id)
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user