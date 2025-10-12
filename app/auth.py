import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .deps import get_db
from .models import ClienteORM

JWT_SECRET = os.getenv("JWT_SECRET", "change_me_in_env")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_EXP_MIN = int(os.getenv("JWT_EXP_MIN", "60"))

router = APIRouter(prefix="/auth", tags=["Auth"])


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


def _create_access_token(subject: str, expires_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


@router.post("/token", response_model=TokenOut, summary="Obtener token de acceso (JWT)")
def issue_token(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> TokenOut:
    cli = db.execute(
        select(ClienteORM).where(ClienteORM.email == form.username)
    ).scalar_one_or_none()
    if not cli:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas"
        )
    token = _create_access_token(subject=str(cli.id), expires_minutes=JWT_EXP_MIN)
    return TokenOut(access_token=token)
PY
