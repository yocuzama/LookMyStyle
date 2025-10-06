"""API LookMyStyle: productos, clientes y carrito (sin JWT en este commit).

Incluye:
- CRUD de productos y clientes.
- Carrito: crear/recuperar, agregar/actualizar/quitar ítems, ver y checkout.
- Validaciones con Pydantic y persistencia con SQLAlchemy 2.x.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import Body, Depends, FastAPI, HTTPException, Path, Query, status
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine
from .deps import get_db
from .models import CarritoItemORM, CarritoORM, ClienteORM, ProductoORM
from .schemas import (
    Carrito,
    CarritoItem,
    CarritoItemIn,
    CheckoutResult,
    Cliente,
    ClienteIn,
    Producto,
    ProductoIn,
)

app = FastAPI(title="LookMyStyle API", version="0.3.0")


@app.on_event("startup")
def on_startup() -> None:
    """Crea las tablas si no existen al iniciar la app."""
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> dict:
    """Ping simple de la API."""
    return {"ok": True, "app": "LookMyStyle"}


@app.get("/health")
def health() -> dict:
    """Indicador de salud."""
    return {"status": "healthy"}


@app.get("/productos", response_model=List[Producto], tags=["Productos"])
def listar_productos(
    categoria: Optional[str] = Query(None, description="Filtra por categoría"),
    min_price: Optional[float] = Query(None, ge=0, description="Precio mínimo"),
    max_price: Optional[float] = Query(None, ge=0, description="Precio máximo"),
    db: Session = Depends(get_db),
) -> List[Producto]:
    """Lista productos con filtros opcionales por categoría y rango de precio."""
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
) -> Producto:
    """Obtiene un producto por su identificador."""
    prod = db.get(ProductoORM, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return prod


@app.post(
    "/productos",
    response_model=Producto,
    status_code=status.HTTP_201_CREATED,
    tags=["Productos"],
)
def crear_producto(producto_in: ProductoIn, db: Session = Depends(get_db)) -> Producto:
    """Crea un nuevo producto."""
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
) -> Producto:
    """Actualiza completamente un producto existente."""
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


@app.delete(
    "/productos/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Productos"],
)
def eliminar_producto(
    producto_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db),
) -> None:
    """Elimina un producto por identificador."""
    prod = db.get(ProductoORM, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    db.delete(prod)
    db.commit()


@app.get("/clientes", response_model=List[Cliente], tags=["Clientes"])
def listar_clientes(
    q: Optional[str] = Query(None, description="Buscar por nombre o email"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[Cliente]:
    """Lista clientes con búsqueda y paginación."""
    query = db.query(ClienteORM)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(ClienteORM.nombre.like(term), ClienteORM.email.like(term))
        )
    return query.order_by(ClienteORM.id).offset(offset).limit(limit).all()


@app.get("/clientes/{cliente_id}", response_model=Cliente, tags=["Clientes"])
def obtener_cliente(
    cliente_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db),
) -> Cliente:
    """Obtiene un cliente por identificador."""
    cli = db.get(ClienteORM, cliente_id)
    if not cli:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cli


@app.post(
    "/clientes",
    response_model=Cliente,
    status_code=status.HTTP_201_CREATED,
    tags=["Clientes"],
)
def crear_cliente(cliente_in: ClienteIn, db: Session = Depends(get_db)) -> Cliente:
    """Crea un nuevo cliente, validando unicidad de email."""
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
) -> Cliente:
    """Actualiza completamente un cliente, validando unicidad de email."""
    cli = db.get(ClienteORM, cliente_id)
    if not cli:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if (
        db.query(ClienteORM)
        .filter(ClienteORM.email == cliente_in.email, ClienteORM.id != cliente_id)
        .first()
    ):
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


@app.delete(
    "/clientes/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Clientes"]
)
def eliminar_cliente(
    cliente_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db),
) -> None:
    """Elimina un cliente por identificador."""
    cli = db.get(ClienteORM, cliente_id)
    if not cli:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(cli)
    db.commit()


def _ensure_cliente(db: Session, cliente_id: int) -> ClienteORM:
    """Garantiza que el cliente exista o lanza 404."""
    cli = db.execute(
        select(ClienteORM).where(ClienteORM.id == cliente_id)
    ).scalar_one_or_none()
    if not cli:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cli


def _ensure_carrito_abierto(db: Session, carrito_id: int) -> CarritoORM:
    """Garantiza que el carrito exista y esté abierto; si no, lanza 404/409."""
    car = db.execute(
        select(CarritoORM).where(CarritoORM.id == carrito_id)
    ).scalar_one_or_none()
    if not car:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    if car.estado != "abierto":
        raise HTTPException(status_code=409, detail="El carrito ya está cerrado")
    return car


def _get_or_create_open_cart(db: Session, cliente_id: int) -> CarritoORM:
    """Obtiene el carrito abierto del cliente o crea uno vacío."""
    car = db.execute(
        select(CarritoORM).where(
            CarritoORM.cliente_id == cliente_id, CarritoORM.estado == "abierto"
        )
    ).scalar_one_or_none()
    if car:
        return car
    car = CarritoORM(
        cliente_id=cliente_id, estado="abierto", created_at=datetime.utcnow()
    )
    db.add(car)
    db.flush()
    return car


def _compose_carrito_response(db: Session, carrito: CarritoORM) -> Carrito:
    """Arma la respuesta del carrito con ítems, subtotales y total."""
    rows = db.execute(
        select(
            CarritoItemORM.producto_id,
            ProductoORM.nombre,
            CarritoItemORM.cantidad,
            func.coalesce(CarritoItemORM.precio_unitario, ProductoORM.precio).label(
                "precio"
            ),
            (
                CarritoItemORM.cantidad
                * func.coalesce(CarritoItemORM.precio_unitario, ProductoORM.precio)
            ).label("subtotal"),
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


@app.post(
    "/clientes/{cliente_id}/carrito",
    response_model=Carrito,
    status_code=status.HTTP_201_CREATED,
    tags=["Carrito"],
)
def crear_o_recuperar_carrito(
    cliente_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db),
) -> Carrito:
    """Crea o recupera el carrito abierto de un cliente."""
    _ensure_cliente(db, cliente_id)
    car = _get_or_create_open_cart(db, cliente_id)
    db.commit()
    return _compose_carrito_response(db, car)


@app.get("/clientes/{cliente_id}/carrito", response_model=Carrito, tags=["Carrito"])
def ver_carrito_cliente(
    cliente_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db),
) -> Carrito:
    """Obtiene el carrito abierto del cliente, creándolo si no existe."""
    _ensure_cliente(db, cliente_id)
    car = db.execute(
        select(CarritoORM).where(
            CarritoORM.cliente_id == cliente_id, CarritoORM.estado == "abierto"
        )
    ).scalar_one_or_none()
    if not car:
        car = _get_or_create_open_cart(db, cliente_id)
        db.commit()
    return _compose_carrito_response(db, car)


@app.get("/carritos/{carrito_id}", response_model=Carrito, tags=["Carrito"])
def ver_carrito(
    carrito_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db),
) -> Carrito:
    """Obtiene un carrito por identificador."""
    car = db.execute(
        select(CarritoORM).where(CarritoORM.id == carrito_id)
    ).scalar_one_or_none()
    if not car:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    return _compose_carrito_response(db, car)


@app.post(
    "/carritos/{carrito_id}/items",
    response_model=Carrito,
    status_code=status.HTTP_201_CREATED,
    tags=["Carrito"],
)
def agregar_item(
    carrito_id: int = Path(..., gt=0, description="ID (>0)"),
    item: CarritoItemIn = Body(...),
    db: Session = Depends(get_db),
) -> Carrito:
    """Agrega un ítem al carrito o acumula cantidad si ya existe."""
    car = _ensure_carrito_abierto(db, carrito_id)

    prod = db.execute(
        select(ProductoORM).where(ProductoORM.id == item.producto_id)
    ).scalar_one_or_none()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    existente = db.execute(
        select(CarritoItemORM).where(
            CarritoItemORM.carrito_id == car.id,
            CarritoItemORM.producto_id == item.producto_id,
        )
    ).scalar_one_or_none()

    nueva_cantidad = item.cantidad + (existente.cantidad if existente else 0)
    if prod.stock is not None and prod.stock < nueva_cantidad:
        raise HTTPException(
            status_code=409,
            detail=f"Stock insuficiente para '{prod.nombre}'. Disponible: {int(prod.stock or 0)}",
        )

    if existente:
        existente.cantidad = nueva_cantidad
        if existente.precio_unitario is None:
            existente.precio_unitario = prod.precio
    else:
        db.add(
            CarritoItemORM(
                carrito_id=car.id,
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                precio_unitario=prod.precio,
            )
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflicto al agregar el ítem")

    car = db.execute(select(CarritoORM).where(CarritoORM.id == car.id)).scalar_one()
    return _compose_carrito_response(db, car)


@app.put(
    "/carritos/{carrito_id}/items/{producto_id}",
    response_model=Carrito,
    tags=["Carrito"],
)
def actualizar_item(
    carrito_id: int = Path(..., gt=0, description="ID (>0)"),
    producto_id: int = Path(..., gt=0, description="ID (>0)"),
    item: CarritoItemIn = Body(...),
    db: Session = Depends(get_db),
) -> Carrito:
    """Actualiza la cantidad de un ítem existente en el carrito."""
    if producto_id != item.producto_id:
        raise HTTPException(
            status_code=400, detail="producto_id de la URL y del body no coinciden"
        )

    car = _ensure_carrito_abierto(db, carrito_id)

    ci = db.execute(
        select(CarritoItemORM).where(
            CarritoItemORM.carrito_id == car.id,
            CarritoItemORM.producto_id == producto_id,
        )
    ).scalar_one_or_none()
    if not ci:
        raise HTTPException(status_code=404, detail="Ítem no existe en el carrito")

    prod = db.execute(
        select(ProductoORM).where(ProductoORM.id == producto_id)
    ).scalar_one()
    if prod.stock is not None and prod.stock < item.cantidad:
        raise HTTPException(
            status_code=409,
            detail=f"Stock insuficiente para '{prod.nombre}'. Disponible: {int(prod.stock or 0)}",
        )

    ci.cantidad = item.cantidad
    if ci.precio_unitario is None:
        ci.precio_unitario = prod.precio
    db.commit()
    return _compose_carrito_response(db, car)


@app.delete(
    "/carritos/{carrito_id}/items/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Carrito"],
)
def eliminar_item(
    carrito_id: int = Path(..., gt=0, description="ID (>0)"),
    producto_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db),
) -> None:
    """Elimina un ítem del carrito."""
    car = _ensure_carrito_abierto(db, carrito_id)

    res = db.execute(
        delete(CarritoItemORM).where(
            CarritoItemORM.carrito_id == car.id,
            CarritoItemORM.producto_id == producto_id,
        )
    )
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Ítem no existe en el carrito")

    db.commit()


@app.post(
    "/carritos/{carrito_id}/checkout", response_model=CheckoutResult, tags=["Carrito"]
)
def checkout(
    carrito_id: int = Path(..., gt=0, description="ID (>0)"),
    db: Session = Depends(get_db),
) -> CheckoutResult:
    """Procesa el checkout: valida stock, descuenta y cierra el carrito."""
    car = _ensure_carrito_abierto(db, carrito_id)

    items = (
        db.execute(select(CarritoItemORM).where(CarritoItemORM.carrito_id == car.id))
        .scalars()
        .all()
    )
    if not items:
        raise HTTPException(status_code=400, detail="El carrito está vacío")

    insuficientes = []
    for it in items:
        prod = db.execute(
            select(ProductoORM).where(ProductoORM.id == it.producto_id)
        ).scalar_one_or_none()
        if not prod or prod.stock is None or prod.stock < it.cantidad:
            insuficientes.append(
                {
                    "producto_id": it.producto_id,
                    "nombre": getattr(prod, "nombre", "N/D"),
                    "stock_disponible": int(getattr(prod, "stock", 0) or 0),
                    "requerido": it.cantidad,
                }
            )
    if insuficientes:
        raise HTTPException(
            status_code=409,
            detail={"error": "stock_insuficiente", "items": insuficientes},
        )

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
                status_code=409,
                detail=f"Stock cambió concurrentemente para producto_id={it.producto_id}. Intenta de nuevo.",
            )

    car.estado = "cerrado"
    car.closed_at = datetime.utcnow()
    db.add(car)

    rows = db.execute(
        select(
            (
                CarritoItemORM.cantidad
                * func.coalesce(CarritoItemORM.precio_unitario, ProductoORM.precio)
            )
        )
        .join(ProductoORM, ProductoORM.id == CarritoItemORM.producto_id)
        .where(CarritoItemORM.carrito_id == car.id)
    ).all()
    total = float(sum(r[0] for r in rows))

    db.commit()
    return CheckoutResult(
        carrito_id=car.id,
        total_items=total_items,
        total=total,
        cerrado_en=car.closed_at.isoformat(),
    )
