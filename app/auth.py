"""Autenticación JWT con subject tipo UUID."""
from datetime import datetime, timedelta
import os
from typing import Optional
from uuid import UUID
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .deps import get_db
from .models import ClienteORM

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-please-change")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MIN", "480"))

router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def _authenticate_email_exists(db: Session, email: str) -> Optional[ClienteORM]:
    return db.query(ClienteORM).filter(ClienteORM.email == email).first()

@router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username
    cliente = _authenticate_email_exists(db, email)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email no registrado", headers={"WWW-Authenticate": "Bearer"})
    token = create_access_token({"sub": str(cliente.id)})
    return {"access_token": token, "token_type": "bearer"}

def get_current_cliente_id(token: str = Depends(oauth2_scheme)) -> UUID:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise credentials_exception
        return UUID(sub)
    except Exception:
        raise credentials_exception
