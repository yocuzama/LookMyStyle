"""Aplicación FastAPI con CORS y endpoints básicos."""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from uuid import uuid4

from .deps import get_db
from .models import ClienteORM, ProductoORM
from .auth import get_current_cliente_id
from .schemas import (
    Cliente,
    ClienteCreate,
    ClienteIn,
    Producto,
    ProductoCreate,
    ProductoIn,
)

app = FastAPI(title="LookMyStyle API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    """Salud del servicio."""
    return {"status": "ok"}


@app.get("/clientes", response_model=list[Cliente])
def list_clientes(db: Session = Depends(get_db), _: int = Depends(get_current_cliente_id)):
    """Lista clientes."""
    rows = db.query(ClienteORM).all()
    return rows


@app.post("/clientes", response_model=Cliente, status_code=status.HTTP_201_CREATED)
def create_cliente(payload: ClienteIn, db: Session = Depends(get_db)):
    """Crea un cliente."""
    exists = db.query(ClienteORM).filter(ClienteORM.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    obj = ClienteORM(id=uuid4(), **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/productos", response_model=list[Producto])
def list_productos(db: Session = Depends(get_db)):
    """Lista productos."""
    rows = db.query(ProductoORM).all()
    return rows


@app.post("/productos", response_model=Producto, status_code=status.HTTP_201_CREATED)
def create_producto(payload: ProductoIn, db: Session = Depends(get_db), _: int = Depends(get_current_cliente_id)):
    """Crea un producto."""
    obj = ProductoORM(id=uuid4(), **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
