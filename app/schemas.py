# app/schemas.py
from pydantic import BaseModel, Field, ConfigDict

# Campos comunes (entrada/salida)
class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=80)
    categoria: str = Field(..., min_length=1, max_length=40)
    precio: float = Field(..., gt=0)       # > 0
    stock: int = Field(default=0, ge=0)    # >= 0

# Cuerpo de entrada (POST/PUT)
class ProductoIn(ProductoBase):
    pass

# Respuesta/salida (incluye id)
class Producto(ProductoBase):
    id: int
    # Permite serializar desde objetos ORM (SQLAlchemy)
    model_config = ConfigDict(from_attributes=True)
