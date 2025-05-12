# backend/app/api/routes/productos.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
import uuid
from app.models import Producto
from app.services.product_service import ProductService
from app.core.db import get_session  # Asegúrate de tener esta función

router = APIRouter(prefix="/productos", tags=["productos"])

@router.get("/", response_model=list[Producto])
def listar_productos(
    skip: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session),
) -> list[Producto]:
    service = ProductoService(session)
    return service.listar(skip=skip, limit=limit)

@router.post("/", response_model=Producto)
def crear_producto(producto: Producto, session: Session = Depends(get_session)):
    service = ProductoService(session)
    return service.crear(producto)

@router.get("/{producto_id}", response_model=Producto)
def obtener_producto(producto_id: uuid.UUID, session: Session = Depends(get_session)):
    service = ProductoService(session)
    try:
        return service.obtener(producto_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

@router.put("/{producto_id}", response_model=Producto)
def actualizar_producto(producto_id: uuid.UUID, datos: Producto, session: Session = Depends(get_session)):
    service = ProductoService(session)
    try:
        return service.actualizar(producto_id, datos)
    except ValueError:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

@router.delete("/{producto_id}")
def eliminar_producto(producto_id: uuid.UUID, session: Session = Depends(get_session)):
    service = ProductoService(session)
    try:
        service.eliminar(producto_id)
        return {"message": "Producto eliminado"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
