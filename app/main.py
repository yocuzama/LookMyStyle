from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status, Path, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func, asc, desc, or_
from sqlalchemy.exc import IntegrityError

from .database import engine, Base
from .deps import get_db
from .models import ClienteORM  # y ProductoORM si lo integras
from .schemas import ClienteIn, Cliente

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # crea tablas
    yield

app = FastAPI(title="LookMyStyle API", version="0.3.0", lifespan=lifespan)

# Ajusta orígenes si tienes frontend aparte
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
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Buscar por nombre o email"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    order_by: str = Query("id", pattern="^(id|nombre|email|telefono)$"),
    order_dir: str = Query("asc", pattern="^(asc|desc)$"),
):
    stmt = select(ClienteORM)
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(ClienteORM.nombre.like(term), ClienteORM.email.like(term)))

    stmt = stmt.order_by(build_order(order_by, order_dir)).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())

@app.get("/clientes/{cliente_id}", response_model=Cliente, tags=["Clientes"])
def obtener_cliente(
    cliente_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    cli = db.get(ClienteORM, cliente_id)
    if not cli:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cli

@app.post("/clientes", response_model=Cliente, status_code=status.HTTP_201_CREATED, tags=["Clientes"])
def crear_cliente(payload: ClienteIn, db: Session = Depends(get_db)):
    cli = ClienteORM(**payload.model_dump())
    db.add(cli)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # email UNIQUE
        raise HTTPException(status_code=409, detail="El email ya está registrado")
    db.refresh(cli)
    return cli

@app.put("/clientes/{cliente_id}", response_model=Cliente, tags=["Clientes"])
def actualizar_cliente(
    payload: ClienteIn,
    cliente_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    cli = db.get(ClienteORM, cliente_id)
    if not cli:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    for k, v in payload.model_dump().items():
        setattr(cli, k, v)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El email ya está registrado")
    db.refresh(cli)
    return cli

@app.delete("/clientes/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Clientes"])
def eliminar_cliente(
    cliente_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    cli = db.get(ClienteORM, cliente_id)
    if not cli:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(cli)
    db.commit()
