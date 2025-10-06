"""Schemas Pydantic de entrada y salida para la API LookMyStyle."""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from pydantic.config import ConfigDict


class ProductoIn(BaseModel):
    """Entrada para crear o actualizar productos."""

    nombre: str = Field(..., min_length=1, max_length=80)
    categoria: str = Field(..., min_length=1, max_length=40)
    precio: float = Field(..., gt=0)
    stock: int = Field(0, ge=0)


class Producto(ProductoIn):
    """Salida de producto."""

    id: int
    model_config = ConfigDict(from_attributes=True)


class ClienteIn(BaseModel):
    """Entrada para crear o actualizar clientes."""

    nombre: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    telefono: Optional[str] = Field(None, min_length=7, max_length=20)


class Cliente(ClienteIn):
    """Salida de cliente."""

    id: int
    model_config = ConfigDict(from_attributes=True)


class CarritoItemIn(BaseModel):
    """Entrada para agregar o actualizar ítems del carrito."""

    producto_id: int
    cantidad: int = Field(..., gt=0)


class CarritoItem(BaseModel):
    """Salida de renglón del carrito."""

    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: float
    subtotal: float


class Carrito(BaseModel):
    """Salida del carrito con sus ítems y total."""

    id: int
    cliente_id: int
    estado: str
    items: List[CarritoItem]
    total: float
    model_config = ConfigDict(from_attributes=True)


class CheckoutResult(BaseModel):
    """Salida del proceso de checkout."""

    carrito_id: int
    total_items: int
    total: float
    cerrado_en: str
