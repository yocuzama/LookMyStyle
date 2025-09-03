from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Numeric
from .database import Base

class ClienteORM(Base):
    __tablename__ = "clientes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

# class ProductoORM(Base):
#     __tablename__ = "productos"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
#     nombre: Mapped[str] = mapped_column(String(80), nullable=False)
#     categoria: Mapped[str] = mapped_column(String(40), nullable=False)
#     precio: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # usar Decimal en schema
#     stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
