from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status, Path, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func, asc, desc, or_
from sqlalchemy.exc import IntegrityError

from .database import engine, Base
from .deps import get_db
from .models import ProductoORM, ClienteORM 
from .schemas import ProductoIn, Producto, ClienteIn, Cliente

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # crea tablas
    yield

app = FastAPI(title="LookMyStyle API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}

def build_order(field: str, direction: str):
    m = {
        "id": ClienteORM.id,
        "nombre": ClienteORM.nombre,
        "email": ClienteORM.email,
        "telefono": ClienteORM.telefono,
    }
    col = m.get(field, ClienteORM.id)
    return asc(col) if direction.lower() == "asc" else desc(col)


@app.get("/clientes", response_model=List[Cliente], tags=["Clientes"])
def listar_clientes(
    q: Optional[str] = Query(None, description="Buscar por nombre o email"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(ClienteORM)
    if q:
        term = f"%{q.strip()}%"
        # En SQL Server, la collation suele ser case-insensitive
        query = query.filter(or_(ClienteORM.nombre.like(term), ClienteORM.email.like(term)))
    return query.order_by(ClienteORM.id).offset(offset).limit(limit).all()

@app.get("/clientes/{cliente_id}", response_model=Cliente, tags=["Clientes"])
def obtener_cliente(
    cliente_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db),
):
    cli = db.get(ClienteORM, cliente_id)
    if not cli:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cli

@app.post("/clientes", response_model=Cliente, status_code=status.HTTP_201_CREATED, tags=["Clientes"])
def crear_cliente(cliente_in: ClienteIn, db: Session = Depends(get_db)):
    # Chequeo optimista: email único
    if db.query(ClienteORM).filter(ClienteORM.email == cliente_in.email).first():
        raise HTTPException(status_code=409, detail="Email ya registrado")
    cli = ClienteORM(**cliente_in.model_dump())
    db.add(cli)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email ya registrado")
    db.refresh(cli)
    return cli

@app.put("/clientes/{cliente_id}", response_model=Cliente, tags=["Clientes"])
def actualizar_cliente(
    cliente_id: int = Path(..., gt=0, description="ID (>0)"),
    cliente_in: ClienteIn = ...,
    db: Session = Depends(get_db),
):
    cli = db.get(ClienteORM, cliente_id)
    if not cli:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Unicidad de email ignorando el propio registro
    if db.query(ClienteORM).filter(
        ClienteORM.email == cliente_in.email,
        ClienteORM.id != cliente_id
    ).first():
        raise HTTPException(status_code=409, detail="Email ya registrado")

    data = cliente_in.model_dump()
    cli.nombre = data["nombre"]
    cli.email = data["email"]
    cli.telefono = data["telefono"]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email ya registrado")

    db.refresh(cli)
    return cli

@app.delete("/clientes/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Clientes"])
def eliminar_cliente(
    cliente_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db),
):
    cli = db.get(ClienteORM, cliente_id)
    if not cli:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(cli)
    db.commit()
