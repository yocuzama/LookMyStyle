"""Esquemas Pydantic para entrada y salida."""

from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class _Config:
    """Configuración para mapear desde atributos ORM."""

    from_attributes = True


class ClienteBase(BaseModel):
    """Datos base de un cliente."""

    nombre: str
    email: EmailStr
    telefono: Optional[str] = None
    model_config = _Config.__dict__


class ClienteCreate(ClienteBase):
    """Payload de creación de cliente."""


class Cliente(ClienteBase):
    """Cliente con ID."""

    id: UUID


class ProductoBase(BaseModel):
    """Datos base de un producto."""

    nombre: str
    categoria: Optional[str] = None
    precio: float
    stock: Optional[int] = None
    model_config = _Config.__dict__


class ProductoCreate(ProductoBase):
    """Payload de creación de producto."""


class Producto(ProductoBase):
    """Producto con ID."""

    id: UUID


class CarritoItemBase(BaseModel):
    """Datos base de un ítem de carrito."""

    producto_id: UUID
    cantidad: int
    precio_unitario: Optional[float] = None
    model_config = _Config.__dict__


class CarritoItemCreate(CarritoItemBase):
    """Payload de creación de ítem."""


class CarritoItem(CarritoItemBase):
    """Ítem de carrito enriquecido."""

    id: Optional[UUID] = None
    nombre_producto: Optional[str] = None
    subtotal: Optional[float] = None


class CarritoBase(BaseModel):
    """Datos base de un carrito."""

    cliente_id: UUID
    estado: str
    model_config = _Config.__dict__


class CarritoCreate(CarritoBase):
    """Payload de creación de carrito."""

    items: Optional[List[CarritoItemCreate]] = None


class Carrito(BaseModel):
    """Carrito con ID, items y total."""

    id: UUID
    cliente_id: UUID
    estado: str
    items: List[CarritoItem] = Field(default_factory=list)
    total: Optional[float] = None
    model_config = _Config.__dict__


class CheckoutResult(BaseModel):
    """Resultado de un checkout de carrito."""

    carrito_id: UUID
    total_items: int
    total: float
    cerrado_en: str


ProductoIn = ProductoCreate
ClienteIn = ClienteCreate
CarritoIn = CarritoCreate
CarritoItemIn = CarritoItemCreate
