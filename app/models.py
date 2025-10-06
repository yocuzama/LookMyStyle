"""Modelos ORM actuales de LookMyStyle."""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import (
    String,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class ProductoORM(Base):
    """Producto del catálogo.

    Atributos:
        id: Identificador interno.
        nombre: Nombre del producto.
        categoria: Categoría del producto.
        precio: Precio unitario.
        stock: Unidades disponibles en inventario.
    """

    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    categoria: Mapped[str] = mapped_column(String(40), nullable=False)
    precio: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ClienteORM(Base):
    """Cliente de la tienda.

    Atributos:
        id: Identificador interno.
        nombre: Nombre completo del cliente.
        email: Correo electrónico único.
        telefono: Número de contacto opcional.
        carritos: Carritos asociados al cliente.
    """

    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(
        String(120), nullable=False, unique=True, index=True
    )
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    carritos: Mapped[List["CarritoORM"]] = relationship(
        back_populates="cliente", lazy="selectin"
    )


class CarritoORM(Base):
    """Carrito de compras asociado a un cliente.

    Atributos:
        id: Identificador interno del carrito.
        cliente_id: Identificador del cliente dueño del carrito.
        estado: Estado del carrito; 'abierto' o 'cerrado'.
        created_at: Fecha de creación (UTC).
        closed_at: Fecha de cierre si aplica (UTC).
        items: Ítems contenidos en el carrito.
        cliente: Cliente propietario del carrito.
    """

    __tablename__ = "carritos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"), nullable=False, index=True
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="abierto", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    items: Mapped[List["CarritoItemORM"]] = relationship(
        back_populates="carrito",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    cliente: Mapped["ClienteORM"] = relationship(back_populates="carritos")


class CarritoItemORM(Base):
    """Ítem dentro de un carrito.

    Atributos:
        id: Identificador interno del ítem.
        carrito_id: Identificador del carrito al que pertenece.
        producto_id: Identificador del producto agregado.
        cantidad: Unidades del producto en el carrito.
        precio_unitario: Precio tomado como snapshot al agregar, si existe.
        carrito: Carrito asociado.
        producto: Producto asociado.
    """

    __tablename__ = "carrito_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    carrito_id: Mapped[int] = mapped_column(
        ForeignKey("carritos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id"), nullable=False, index=True
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    carrito: Mapped["CarritoORM"] = relationship(back_populates="items")
    producto: Mapped["ProductoORM"] = relationship()

    __table_args__ = (
        UniqueConstraint("carrito_id", "producto_id", name="uq_carrito_producto"),
        CheckConstraint("cantidad > 0", name="ck_cantidad_pos"),
    )
