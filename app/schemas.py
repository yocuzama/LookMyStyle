from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional

class ClienteIn(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    telefono: Optional[str] = Field(None, min_length=7, max_length=20)

class Cliente(ClienteIn):
    id: int
    model_config = ConfigDict(from_attributes=True)
