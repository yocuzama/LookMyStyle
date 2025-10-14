"""Esquemas Pydantic para entrada/salida de la API."""
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class _Config:
    """Config común para modelos ORM."""
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
    """Datos base de un item de carrito."""
    producto_id: UUID
    cantidad: int
    precio_unitario: Optional[float] = None
    model_config = _Config.__dict__


class CarritoItemCreate(CarritoItemBase):
    """Payload de creación de item."""


class CarritoItem(CarritoItemBase):
    """Item con ID."""
    id: UUID


class CarritoBase(BaseModel):
    """Datos base de un carrito."""
    cliente_id: UUID
    estado: str
    model_config = _Config.__dict__


class CarritoCreate(CarritoBase):
    """Payload de creación de carrito."""
    items: Optional[List[CarritoItemCreate]] = None


class Carrito(CarritoBase):
    """Carrito con ID e items."""
    id: UUID
    items: List[CarritoItem] = []


ProductoIn = ProductoCreate
ClienteIn = ClienteCreate
CarritoIn = CarritoCreate
CarritoItemIn = CarritoItemCreate
