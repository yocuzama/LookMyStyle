# app/models.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Numeric
from .database import Base

class ProductoORM(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    categoria: Mapped[str] = mapped_column(String(40), nullable=False)
    # Numeric(10,2) es mejor que Float para dinero
    precio: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
