# app/schemas.py
from typing import Optional
from pydantic import BaseModel, Field, PositiveFloat, EmailStr, conint
from pydantic.config import ConfigDict

from typing import Optional, List  #carrito


# -------- Productos --------
class ProductoIn(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=80)
    categoria: str = Field(..., min_length=1, max_length=40)
    precio: PositiveFloat
    stock: conint(ge=0) = 0

class Producto(ProductoIn):
    id: int
    model_config = ConfigDict(from_attributes=True)

# -------- Clientes --------
class ClienteIn(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    telefono: Optional[str] = Field(None, min_length=7, max_length=20)

class Cliente(ClienteIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


# -------- Carrito --------
class CarritoItemIn(BaseModel):
    producto_id: int = Field(..., gt=0)
    cantidad: conint(ge=1, le=999)

class CarritoItem(BaseModel):
    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: PositiveFloat
    subtotal: PositiveFloat
    model_config = ConfigDict(from_attributes=True)

class Carrito(BaseModel):
    id: int
    cliente_id: int
    estado: str
    items: List[CarritoItem]
    total: PositiveFloat
    model_config = ConfigDict(from_attributes=True)

class CheckoutResult(BaseModel):
    carrito_id: int
    total_items: conint(ge=1)
    total: PositiveFloat
    cerrado_en: str
