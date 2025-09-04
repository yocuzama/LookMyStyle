# app/main.py
from fastapi import FastAPI, HTTPException, status, Path, Query, Depends, Body 
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, select, update, delete 
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from .database import engine, Base
from .deps import get_db
from .models import ProductoORM, ClienteORM, CarritoORM, CarritoItemORM 
from .schemas import (ProductoIn, Producto, ClienteIn, Cliente, CarritoItemIn, CarritoItem, Carrito, CheckoutResult)

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

# -------- Clientes --------

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
        # En SQL Server normalmente la collation es case-insensitive
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
    # Chequeo optimista de unicidad de email
    if db.query(ClienteORM).filter(ClienteORM.email == cliente_in.email).first():
        raise HTTPException(status_code=409, detail="Email ya registrado")
    cli = ClienteORM(**cliente_in.model_dump())
    db.add(cli)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Respaldo por si la unicidad viene solo desde la DB
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

    # Unicidad del email ignorando el propio registro
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

def _ensure_cliente(db: Session, cliente_id: int) -> ClienteORM:
    cli = db.execute(select(ClienteORM).where(ClienteORM.id == cliente_id)).scalar_one_or_none()
    if not cli:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cli

def _ensure_carrito_abierto(db: Session, carrito_id: int) -> CarritoORM:
    car = db.execute(select(CarritoORM).where(CarritoORM.id == carrito_id)).scalar_one_or_none()
    if not car:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    if car.estado != "abierto":
        raise HTTPException(status_code=409, detail="El carrito ya está cerrado")
    return car

def _get_or_create_open_cart(db: Session, cliente_id: int) -> CarritoORM:
    car = db.execute(
        select(CarritoORM).where(CarritoORM.cliente_id == cliente_id, CarritoORM.estado == "abierto")
    ).scalar_one_or_none()
    if car:
        return car
    car = CarritoORM(cliente_id=cliente_id, estado="abierto", created_at=datetime.utcnow())
    db.add(car)
    db.flush()  # asegura car.id
    return car

def _compose_carrito_response(db: Session, carrito: CarritoORM) -> Carrito:
    rows = db.execute(
        select(
            CarritoItemORM.producto_id,
            ProductoORM.nombre,
            CarritoItemORM.cantidad,
            func.coalesce(CarritoItemORM.precio_unitario, ProductoORM.precio).label("precio"),
            (CarritoItemORM.cantidad * func.coalesce(CarritoItemORM.precio_unitario, ProductoORM.precio)).label("subtotal"),
        )
        .join(ProductoORM, ProductoORM.id == CarritoItemORM.producto_id)
        .where(CarritoItemORM.carrito_id == carrito.id)
        .order_by(ProductoORM.nombre.asc())
    ).all()

    items = [
        CarritoItem(
            producto_id=r.producto_id,
            nombre_producto=r.nombre,
            cantidad=r.cantidad,
            precio_unitario=float(r.precio),
            subtotal=float(r.subtotal),
        )
        for r in rows
    ]
    total = float(sum(i.subtotal for i in items))
    return Carrito(
        id=carrito.id,
        cliente_id=carrito.cliente_id,
        estado=carrito.estado,
        items=items,
        total=total,
    )


# -------- Carrito --------

@app.post("/clientes/{cliente_id}/carrito", response_model=Carrito, status_code=status.HTTP_201_CREATED, tags=["Carrito"])
def crear_o_recuperar_carrito(
    cliente_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db)
):
    _ensure_cliente(db, cliente_id)
    car = _get_or_create_open_cart(db, cliente_id)
    db.commit()
    return _compose_carrito_response(db, car)

@app.get("/clientes/{cliente_id}/carrito", response_model=Carrito, tags=["Carrito"])
def ver_carrito_cliente(
    cliente_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db)
):
    _ensure_cliente(db, cliente_id)
    car = db.execute(
        select(CarritoORM).where(CarritoORM.cliente_id == cliente_id, CarritoORM.estado == "abierto")
    ).scalar_one_or_none()
    if not car:
        car = _get_or_create_open_cart(db, cliente_id)  # crea vacío
        db.commit()
    return _compose_carrito_response(db, car)

@app.get("/carritos/{carrito_id}", response_model=Carrito, tags=["Carrito"])
def ver_carrito(
    carrito_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db)
):
    car = db.execute(select(CarritoORM).where(CarritoORM.id == carrito_id)).scalar_one_or_none()
    if not car:
        raise HTTPException(404, "Carrito no encontrado")
    return _compose_carrito_response(db, car)

@app.post("/carritos/{carrito_id}/items", response_model=Carrito, status_code=status.HTTP_201_CREATED, tags=["Carrito"])
def agregar_item(
    carrito_id: int = Path(..., gt=0, description="ID (>0)"),
    item: CarritoItemIn = Body(...),
    db: Session = Depends(get_db)
):
    car = _ensure_carrito_abierto(db, carrito_id)

    prod = db.execute(select(ProductoORM).where(ProductoORM.id == item.producto_id)).scalar_one_or_none()
    if not prod:
        raise HTTPException(404, "Producto no encontrado")

    existente = db.execute(
        select(CarritoItemORM).where(
            CarritoItemORM.carrito_id == car.id,
            CarritoItemORM.producto_id == item.producto_id
        )
    ).scalar_one_or_none()

    nueva_cantidad = item.cantidad + (existente.cantidad if existente else 0)
    if prod.stock is not None and prod.stock < nueva_cantidad:
        raise HTTPException(409, detail=f"Stock insuficiente para '{prod.nombre}'. Disponible: {int(prod.stock or 0)}")

    if existente:
        existente.cantidad = nueva_cantidad
        if existente.precio_unitario is None:
            existente.precio_unitario = prod.precio  # snapshot opcional
        db.add(existente)
    else:
        db.add(CarritoItemORM(
            carrito_id=car.id,
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            precio_unitario=prod.precio  # snapshot opcional
        ))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Conflicto al agregar el ítem (posible duplicado)")

    car = db.execute(select(CarritoORM).where(CarritoORM.id == car.id)).scalar_one()
    return _compose_carrito_response(db, car)

@app.put("/carritos/{carrito_id}/items/{producto_id}", response_model=Carrito, tags=["Carrito"])
def actualizar_item(
    carrito_id: int = Path(..., gt=0, description="ID (>0)"),
    producto_id: int = Path(..., gt=0, description="ID (>0)"),
    item: CarritoItemIn = Body(...),
    db: Session = Depends(get_db)
):
    if producto_id != item.producto_id:
        raise HTTPException(400, "producto_id de la URL y del body no coinciden")

    car = _ensure_carrito_abierto(db, carrito_id)

    ci = db.execute(
        select(CarritoItemORM).where(
            CarritoItemORM.carrito_id == car.id,
            CarritoItemORM.producto_id == producto_id
        )
    ).scalar_one_or_none()
    if not ci:
        raise HTTPException(404, "Ítem no existe en el carrito")

    prod = db.execute(select(ProductoORM).where(ProductoORM.id == producto_id)).scalar_one()
    if prod.stock is not None and prod.stock < item.cantidad:
        raise HTTPException(409, detail=f"Stock insuficiente para '{prod.nombre}'. Disponible: {int(prod.stock or 0)}")

    ci.cantidad = item.cantidad
    if ci.precio_unitario is None:
        ci.precio_unitario = prod.precio
    db.add(ci)
    db.commit()
    return _compose_carrito_response(db, car)

@app.delete("/carritos/{carrito_id}/items/{producto_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Carrito"])
def eliminar_item(
    carrito_id: int = Path(..., gt=0, description="ID (>0)"),
    producto_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db)
):
    car = _ensure_carrito_abierto(db, carrito_id)

    res = db.execute(
        delete(CarritoItemORM).where(
            CarritoItemORM.carrito_id == car.id,
            CarritoItemORM.producto_id == producto_id
        )
    )
    if res.rowcount == 0:
        raise HTTPException(404, "Ítem no existe en el carrito")

    db.commit()
    return

@app.post("/carritos/{carrito_id}/checkout", response_model=CheckoutResult, tags=["Carrito"])
def checkout(
    carrito_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db)
):
    car = _ensure_carrito_abierto(db, carrito_id)

    items = db.execute(
        select(CarritoItemORM).where(CarritoItemORM.carrito_id == car.id)
    ).scalars().all()
    if not items:
        raise HTTPException(400, "El carrito está vacío")

    # Verificación previa de stock
    insuficientes = []
    for it in items:
        prod = db.execute(select(ProductoORM).where(ProductoORM.id == it.producto_id)).scalar_one_or_none()
        if not prod or prod.stock < it.cantidad:
            insuficientes.append({
                "producto_id": it.producto_id,
                "nombre": getattr(prod, "nombre", "N/D"),
                "stock_disponible": int(getattr(prod, "stock", 0) or 0),
                "requerido": it.cantidad
            })
    if insuficientes:
        raise HTTPException(status_code=409, detail={"error": "stock_insuficiente", "items": insuficientes})

    # Descuento atómico por producto
    total_items = 0
    for it in items:
        q = it.cantidad
        total_items += q
        res = db.execute(
            update(ProductoORM)
            .where(ProductoORM.id == it.producto_id, ProductoORM.stock >= q)
            .values(stock=ProductoORM.stock - q)
        )
        if res.rowcount != 1:
            db.rollback()
            raise HTTPException(
                409,
                detail=f"Stock cambió concurrentemente para producto_id={it.producto_id}. Intenta de nuevo."
            )

    # Cierra carrito
    car.estado = "cerrado"
    car.closed_at = datetime.utcnow()
    db.add(car)

    # Total final (snapshot si existe; si no, precio actual)
    rows = db.execute(
        select(
            (CarritoItemORM.cantidad * func.coalesce(CarritoItemORM.precio_unitario, ProductoORM.precio))
        ).join(ProductoORM, ProductoORM.id == CarritoItemORM.producto_id
        ).where(CarritoItemORM.carrito_id == car.id)
    ).all()
    total = float(sum(r[0] for r in rows))

    db.commit()
    return CheckoutResult(
        carrito_id=car.id,
        total_items=total_items,
        total=total,
        cerrado_en=car.closed_at.isoformat()
    )

