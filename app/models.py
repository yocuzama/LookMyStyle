"""Modelos ORM con UUID y columnas de autoría."""
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    Index,
    func,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from .database import Base


class AuditMixin:
    """Columnas de autoría requeridas por la rúbrica."""
    creado_por = Column(UNIQUEIDENTIFIER, nullable=True)
    actualizado_por = Column(UNIQUEIDENTIFIER, nullable=True)
    fecha_creacion = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("(sysutcdatetime())"),
    )
    fecha_actualizacion = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=text("(sysutcdatetime())"),
        onupdate=func.sysutcdatetime(),
    )


class ClienteORM(AuditMixin, Base):
    """Clientes."""
    __tablename__ = "clientes"
    id = Column(
        UNIQUEIDENTIFIER,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("NEWID()"),
    )
    nombre = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True, unique=True)
    telefono = Column(String(30), nullable=True)
    carritos = relationship("CarritoORM", back_populates="cliente", cascade="all, delete-orphan")


class ProductoORM(AuditMixin, Base):
    """Productos."""
    __tablename__ = "productos"
    id = Column(
        UNIQUEIDENTIFIER,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("NEWID()"),
    )
    nombre = Column(String(150), nullable=False, index=True)
    categoria = Column(String(100), nullable=True, index=True)
    precio = Column(Numeric(12, 2), nullable=False)
    stock = Column(Integer, nullable=True)
    items = relationship("CarritoItemORM", back_populates="producto", cascade="all, delete")


class CarritoORM(AuditMixin, Base):
    """Carritos de compra."""
    __tablename__ = "carritos"
    id = Column(
        UNIQUEIDENTIFIER,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("NEWID()"),
    )
    cliente_id = Column(UNIQUEIDENTIFIER, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    estado = Column(String(20), nullable=False, default="abierto")
    cliente = relationship("ClienteORM", back_populates="carritos")
    items = relationship("CarritoItemORM", back_populates="carrito", cascade="all, delete-orphan")


class CarritoItemORM(AuditMixin, Base):
    """Ítems del carrito."""
    __tablename__ = "carrito_items"
    id = Column(
        UNIQUEIDENTIFIER,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("NEWID()"),
    )
    carrito_id = Column(UNIQUEIDENTIFIER, ForeignKey("carritos.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(UNIQUEIDENTIFIER, ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Numeric(12, 2), nullable=True)
    carrito = relationship("CarritoORM", back_populates="items")
    producto = relationship("ProductoORM", back_populates="items")


Index("ix_productos_nombre", ProductoORM.nombre)
Index("ix_productos_categoria", ProductoORM.categoria)
