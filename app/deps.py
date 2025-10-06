"""Dependencias comunes de FastAPI: inyección de sesión DB por request."""

from typing import Generator
from sqlalchemy.orm import Session
from .database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Abre una sesión de base de datos por request y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
