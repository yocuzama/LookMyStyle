"""Aplicación FastAPI de LookMyStyle."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import Body, Depends, FastAPI, HTTPException, Path, Query, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import router as auth_router, get_current_cliente_id
from .database import Base, engine
from .deps import get_db
from .models import CarritoItemORM, CarritoORM, ClienteORM, ProductoORM
from .schemas import (
    Producto,
    ProductoCreate,
    ProductoIn,
    Cliente,
    ClienteCreate,
    ClienteIn,
    Carrito,
    CarritoCreate,
    CarritoItem,
    CarritoItemCreate,
    CarritoItemIn,
    CheckoutResult,
)

app = FastAPI(
    title="LookMyStyle API",
    version="0.3.0",
    swagger_ui_parameters={"persistAuthorization": True},
)


def custom_openapi():
    """Esquema OpenAPI con autenticación bearer por defecto."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description="LookMyStyle API",
    )
    comps = schema.setdefault("components", {}).setdefault("securitySchemes", {})
    comps["BearerAuth"] = {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Inicialización de metadatos de BD."""
    Base.metadata.create_all(bind=engine)


app.include_router(auth_router)


@app.get("/")
def root() -> dict:
    """Raíz del servicio."""
    return {"ok": True, "app": "LookMyStyle"}


@app.get("/health")
def health() -> dict:
    """Salud del servicio."""
    return {"status": "healthy"}


@app.get("/productos", response_model=List[Producto], tags=["Productos"])
def listar_productos(
    categoria: Optional[str] = Query(None, description="Filtra por categoría"),
    min_price: Optional[float] = Query(None, ge=0, description="Precio mínimo"),
    max_price: Optional[float] = Query(None, ge=0, description="Precio máximo"),
    db: Session = Depends(get_db),
) -> List[Producto]:
    """Lista productos con filtros opcionales."""
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
    producto_id: UUID = Path(..., description="UUID"),
    db: Session = Depends(get_db),
) -> Producto:
    """Obtiene un producto por UUID."""
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
def crear_producto(
    producto_in: ProductoIn,
    db: Session = Depends(get_db),
    current_cliente_id: UUID = Security(get_current_cliente_id),
) -> Producto:
    """Crea un producto nuevo."""
    prod = ProductoORM(**producto_in.model_dump())
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


@app.put("/productos/{producto_id}", response_model=Producto, tags=["Productos"])
def actualizar_producto(
    producto_id: UUID = Path(..., description="UUID"),
    producto_in: ProductoIn = Body(...),
    db: Session = Depends(get_db),
    current_cliente_id: UUID = Security(get_current_cliente_id),
) -> Producto:
    """Actualiza un producto existente."""
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
    producto_id: UUID = Path(..., description="UUID"),
    db: Session = Depends(get_db),
    current_cliente_id: UUID = Security(get_current_cliente_id),
) -> None:
    """Elimina un producto por UUID."""
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
    """Lista clientes con búsqueda básica."""
    query = db.query(ClienteORM)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(ClienteORM.nombre.like(term), ClienteORM.email.like(term))
        )
    return query.order_by(ClienteORM.nombre).offset(offset).limit(limit).all()


@app.get("/clientes/{cliente_id}", response_model=Cliente, tags=["Clientes"])
def obtener_cliente(
    cliente_id: UUID = Path(..., description="UUID"),
    db: Session = Depends(get_db),
) -> Cliente:
    """Obtiene un cliente por UUID."""
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
def crear_cliente(
    cliente_in: ClienteIn,
    db: Session = Depends(get_db),
) -> Cliente:
    """Crea un cliente nuevo sin requerir token."""
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
    cliente_id: UUID = Path(..., description="UUID"),
    cliente_in: ClienteIn = Body(...),
    db: Session = Depends(get_db),
    current_cliente_id: UUID = Security(get_current_cliente_id),
) -> Cliente:
    """Actualiza un cliente existente."""
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
    cliente_id: UUID = Path(..., description="UUID"),
    db: Session = Depends(get_db),
    current_cliente_id: UUID = Security(get_current_cliente_id),
) -> None:
    """Elimina un cliente por UUID."""
    cli = db.get(ClienteORM, cliente_id)
    if not cli:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(cli)
    db.commit()


def _ensure_cliente(db: Session, cliente_id: UUID) -> ClienteORM:
    """Garantiza que el cliente exista."""
    cli = db.execute(
        select(ClienteORM).where(ClienteORM.id == cliente_id)
    ).scalar_one_or_none()
    if not cli:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cli


def _ensure_carrito_abierto(db: Session, carrito_id: UUID) -> CarritoORM:
    """Garantiza que el carrito exista y esté abierto."""
    car = db.execute(
        select(CarritoORM).where(CarritoORM.id == carrito_id)
    ).scalar_one_or_none()
    if not car:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    if car.estado != "abierto":
        raise HTTPException(status_code=409, detail="El carrito ya está cerrado")
    return car


def _get_or_create_open_cart(db: Session, cliente_id: UUID) -> CarritoORM:
    """Obtiene el carrito abierto o lo crea."""
    car = db.execute(
        select(CarritoORM).where(
            CarritoORM.cliente_id == cliente_id, CarritoORM.estado == "abierto"
        )
    ).scalar_one_or_none()
    if car:
        return car
    car = CarritoORM(cliente_id=cliente_id, estado="abierto")
    db.add(car)
    db.flush()
    return car


def _compose_carrito_response(db: Session, carrito: CarritoORM) -> Carrito:
    """Compone la respuesta de carrito con items y total."""
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
    total = float(sum((i.subtotal or 0) for i in items))
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
    cliente_id: UUID = Path(..., description="UUID"),
    db: Session = Depends(get_db),
    current_cliente_id: UUID = Security(get_current_cliente_id),
) -> Carrito:
    """Crea o devuelve el carrito abierto del cliente."""
    _ensure_cliente(db, cliente_id)
    car = _get_or_create_open_cart(db, cliente_id)
    db.commit()
    return _compose_carrito_response(db, car)


@app.get("/clientes/{cliente_id}/carrito", response_model=Carrito, tags=["Carrito"])
def ver_carrito_cliente(
    cliente_id: UUID = Path(..., description="UUID"),
    db: Session = Depends(get_db),
) -> Carrito:
    """Muestra el carrito abierto del cliente."""
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
    carrito_id: UUID = Path(..., description="UUID"),
    db: Session = Depends(get_db),
) -> Carrito:
    """Muestra un carrito por UUID."""
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
    carrito_id: UUID = Path(..., description="UUID"),
    item: CarritoItemIn = Body(...),
    db: Session = Depends(get_db),
    current_cliente_id: UUID = Security(get_current_cliente_id),
) -> Carrito:
    """Agrega un ítem al carrito."""
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
    if existente:
        db.execute(
            update(CarritoItemORM)
            .where(
                CarritoItemORM.carrito_id == car.id,
                CarritoItemORM.producto_id == item.producto_id,
            )
            .values(cantidad=nueva_cantidad, precio_unitario=item.precio_unitario)
        )
    else:
        ci = CarritoItemORM(
            carrito_id=car.id,
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
        )
        db.add(ci)
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
    carrito_id: UUID = Path(..., description="UUID"),
    producto_id: UUID = Path(..., description="UUID"),
    item: CarritoItemIn = Body(...),
    db: Session = Depends(get_db),
    current_cliente_id: UUID = Security(get_current_cliente_id),
) -> Carrito:
    """Actualiza la cantidad o precio de un ítem."""
    if producto_id != item.producto_id:
        raise HTTPException(
            status_code=400, detail="producto_id de la URL y del body no coinciden"
        )
    car = _ensure_carrito_abierto(db, carrito_id)
    ci = db.execute(
        select(CarritoItemORM).where(
            CarritoItemORM.carrito_id == car.id,
            CarritoItemORM.producto_id == item.producto_id,
        )
    ).scalar_one_or_none()
    if not ci:
        raise HTTPException(status_code=404, detail="Ítem no existe en el carrito")
    db.execute(
        update(CarritoItemORM)
        .where(CarritoItemORM.id == ci.id)
        .values(cantidad=item.cantidad, precio_unitario=item.precio_unitario)
    )
    db.commit()
    car = db.execute(select(CarritoORM).where(CarritoORM.id == car.id)).scalar_one()
    return _compose_carrito_response(db, car)


@app.delete(
    "/carritos/{carrito_id}/items/{producto_id}",
    response_model=Carrito,
    tags=["Carrito"],
)
def eliminar_item(
    carrito_id: UUID = Path(..., description="UUID"),
    producto_id: UUID = Path(..., description="UUID"),
    db: Session = Depends(get_db),
    current_cliente_id: UUID = Security(get_current_cliente_id),
) -> Carrito:
    """Elimina un ítem del carrito."""
    car = _ensure_carrito_abierto(db, carrito_id)
    db.execute(
        delete(CarritoItemORM).where(
            CarritoItemORM.carrito_id == car.id,
            CarritoItemORM.producto_id == producto_id,
        )
    )
    db.commit()
    car = db.execute(select(CarritoORM).where(CarritoORM.id == car.id)).scalar_one()
    return _compose_carrito_response(db, car)


@app.post(
    "/carritos/{carrito_id}/checkout", response_model=CheckoutResult, tags=["Carrito"]
)
def checkout(
    carrito_id: UUID = Path(..., description="UUID"),
    db: Session = Depends(get_db),
    current_cliente_id: UUID = Security(get_current_cliente_id),
) -> CheckoutResult:
    """Cierra el carrito y devuelve el resumen."""
    car = _ensure_carrito_abierto(db, carrito_id)
    totals = db.execute(
        select(
            func.coalesce(func.sum(CarritoItemORM.cantidad), 0).label("total_items"),
            func.coalesce(
                func.sum(
                    CarritoItemORM.cantidad
                    * func.coalesce(CarritoItemORM.precio_unitario, ProductoORM.precio)
                ),
                0,
            ).label("total"),
        )
        .join(ProductoORM, ProductoORM.id == CarritoItemORM.producto_id)
        .where(CarritoItemORM.carrito_id == car.id)
    ).one()
    total_items = int(totals.total_items or 0)
    total = float(totals.total or 0.0)
    db.execute(
        update(CarritoORM).where(CarritoORM.id == car.id).set({"estado": "cerrado"})
    )
    db.commit()
    ahora = datetime.utcnow().isoformat()
    return CheckoutResult(
        carrito_id=car.id,
        total_items=total_items,
        total=total,
        cerrado_en=ahora,
    )
