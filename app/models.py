# app/models.py
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Numeric
from .database import Base

from datetime import datetime
from typing import List  
from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship


# -------- Productos --------
class ProductoORM(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    categoria: Mapped[str] = mapped_column(String(40), nullable=False)
    precio: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

# -------- Clientes --------
class ClienteORM(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # navegar desde Cliente → Carritos
    carritos: Mapped[List["CarritoORM"]] = relationship(back_populates="cliente", lazy="selectin")

    


# -------- Carritos --------
class CarritoORM(Base):
    __tablename__ = "carritos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="abierto", index=True)  # 'abierto' | 'cerrado'
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    items: Mapped[List["CarritoItemORM"]] = relationship(
        back_populates="carrito",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # navegar desde Cliente → Carritos
    cliente: Mapped["ClienteORM"] = relationship(back_populates="carritos")


class CarritoItemORM(Base):
    __tablename__ = "carrito_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    carrito_id: Mapped[int] = mapped_column(ForeignKey("carritos.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), nullable=False, index=True)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    # Snapshot del precio al momento de agregar (si prefieres precio dinámico, puedes dejarlo en NULL)
    precio_unitario: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)

    carrito: Mapped["CarritoORM"] = relationship(back_populates="items")
    producto: Mapped["ProductoORM"] = relationship()

    __table_args__ = (
        UniqueConstraint("carrito_id", "producto_id", name="uq_carrito_producto"),
        CheckConstraint("cantidad > 0", name="ck_cantidad_pos"),
    )
