# app/main.py
from fastapi import FastAPI, HTTPException, status, Path, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import engine, Base
from .deps import get_db
from .models import ProductoORM
from .schemas import ProductoIn, Producto

app = FastAPI(title="LookMyStyle API", version="0.2.0")

# Crear tablas al iniciar
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"ok": True, "app": "LookMyStyle"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# -------- Productos (SQLAlchemy + SQL Server) --------

@app.get("/productos", response_model=List[Producto], tags=["Productos"])
def listar_productos(
    categoria: Optional[str] = Query(None, description="Filtra por categoría"),
    min_price: Optional[float] = Query(None, ge=0, description="Precio mínimo"),
    max_price: Optional[float] = Query(None, ge=0, description="Precio máximo"),
    db: Session = Depends(get_db),
):
    q = db.query(ProductoORM)
    if categoria is not None:
        q = q.filter(func.lower(ProductoORM.categoria) == func.lower(categoria.strip()))
    if min_price is not None:
        q = q.filter(ProductoORM.precio >= min_price)
    if max_price is not None:
        q = q.filter(ProductoORM.precio <= max_price)
    return q.all()

@app.get("/productos/{producto_id}", response_model=Producto, tags=["Productos"])
def obtener_producto(
    producto_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db),
):
    prod = db.get(ProductoORM, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return prod

@app.post("/productos", response_model=Producto, status_code=status.HTTP_201_CREATED, tags=["Productos"])
def crear_producto(producto_in: ProductoIn, db: Session = Depends(get_db)):
    prod = ProductoORM(**producto_in.model_dump())
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

@app.put("/productos/{producto_id}", response_model=Producto, tags=["Productos"])
def actualizar_producto(
    producto_id: int = Path(..., gt=0, description="ID (>0)"),
    producto_in: ProductoIn = ...,
    db: Session = Depends(get_db),
):
    prod = db.get(ProductoORM, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    data = producto_in.model_dump()
    prod.nombre = data["nombre"]
    prod.categoria = data["categoria"]
    prod.precio = data["precio"]
    prod.stock = data["stock"]
    db.commit()
    db.refresh(prod)
    return prod

@app.delete("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Productos"])
def eliminar_producto(
    producto_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db),
):
    prod = db.get(ProductoORM, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    db.delete(prod)
    db.commit()
