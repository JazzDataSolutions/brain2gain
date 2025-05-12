# backend/app/services/product_service.py
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Product
from app.schemas.product import ProductCreate
from app.repositories.product_repository import ProductRepository

import uuid

class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
        elf.repo = ProductRepository(session)

    def listar(self, skip: int = 0, limit: int = 10) -> list[Product]:
        statement = select(Producto).offset(skip).limit(limit)
        return self.session.exec(statement).all()

    async def create(self, payload: ProductCreate) -> Product:
        # 1) Validar duplicado
        if await self.repo.get_by_sku(payload.sku):
            raise HTTPException(status_code=409, detail="SKU duplicado")

        # 2) Crear entidad
        product = Product(**payload.dict())
        await self.repo.add(product)

        # 3) Commit / rollback
        try:
            await self.session.commit()
            await self.session.refresh(product)
            return product
        except IntegrityError:
            await self.session.rollback()

    def get(self, producto_id: uuid.UUID) -> Product:
        producto = self.session.get(Product, producto_id)
        if not producto:
            raise ValueError("Producto no encontrado")
        return producto

    def update(self, producto_id: uuid.UUID, datos: Product) -> Product:
        producto = self.obtener(producto_id)
        producto.nombre = datos.nombre
        producto.descripcion = datos.descripcion
        producto.precio = datos.precio
        producto.stock = datos.stock
        producto.imagen_url = datos.imagen_url
        self.session.add(producto)
        self.session.commit()
        self.session.refresh(producto)
        return producto

    def delete(self, producto_id: uuid.UUID) -> None:
        producto = self.obtener(producto_id)
        self.session.delete(producto)
        self.session.commit()
