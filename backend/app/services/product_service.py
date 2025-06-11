"""
Product Service Layer.

Handles business logic and validation for product operations.
"""
import logging
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.cache import cache_key_wrapper, invalidate_cache_pattern, invalidate_cache_key
from app.models import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class ProductService:
    """Service for product business logic and data operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ProductRepository(session)

    @cache_key_wrapper("products:list", ttl=300)  # 5 minutes cache
    async def list(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        List products with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of products
        """
        # Use repository method if available, otherwise use direct query
        try:
            return await self.repo.list(skip=skip, limit=limit)
        except AttributeError:
            # Fallback if repository doesn't have list method
            statement = select(Product).offset(skip).limit(limit)
            result = await self.session.exec(statement)
            return result.all()

    async def create(self, payload: ProductCreate) -> Product:
        """
        Create a new product with business validation.
        
        Args:
            payload: Product creation data
            
        Returns:
            Created product
            
        Raises:
            ValueError: If business validation fails
        """
        # Business validations
        await self._validate_product_creation(payload)
        
        # Check for duplicate SKU
        existing_product = await self.repo.get_by_sku(payload.sku)
        if existing_product:
            raise ValueError(f"Product with SKU '{payload.sku}' already exists")

        # Create product instance
        product_data = payload.model_dump()
        product = Product(**product_data)
        
        try:
            self.session.add(product)
            await self.session.commit()
            await self.session.refresh(product)
            
            # Invalidate related caches
            await self._invalidate_product_caches()
            
            logger.info(f"Created product with SKU: {product.sku}")
            return product
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Database integrity error creating product: {e}")
            raise ValueError("Product with this SKU already exists")

    @cache_key_wrapper("products:detail", ttl=600)  # 10 minutes cache
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        return await self.repo.get_by_id(product_id)

    @cache_key_wrapper("products:sku", ttl=600)  # 10 minutes cache
    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        return await self.repo.get_by_sku(sku)

    async def update(self, product_id: int, payload: ProductUpdate) -> Optional[Product]:
        """
        Update a product with business validation.
        
        Args:
            product_id: ID of product to update
            payload: Update data
            
        Returns:
            Updated product or None if not found
            
        Raises:
            ValueError: If business validation fails
        """
        product = await self.repo.get_by_id(product_id)
        if not product:
            return None

        # Business validations for update
        await self._validate_product_update(product, payload)

        # Check for SKU conflicts if SKU is being updated
        if payload.sku and payload.sku != product.sku:
            existing_product = await self.repo.get_by_sku(payload.sku)
            if existing_product and existing_product.product_id != product_id:
                raise ValueError(f"Product with SKU '{payload.sku}' already exists")

        # Update only provided fields
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        try:
            self.session.add(product)
            await self.session.commit()
            await self.session.refresh(product)
            
            # Invalidate related caches
            await self._invalidate_product_caches(product_id)
            
            logger.info(f"Updated product with ID: {product_id}")
            return product
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Database integrity error updating product: {e}")
            raise ValueError("Product with this SKU already exists")

    async def delete(self, product_id: int) -> bool:
        """
        Delete a product.
        
        Args:
            product_id: ID of product to delete
            
        Returns:
            True if deleted, False if not found
        """
        product = await self.repo.get_by_id(product_id)
        if not product:
            return False

        # Business validation before deletion
        await self._validate_product_deletion(product)

        try:
            await self.session.delete(product)
            await self.session.commit()
            
            # Invalidate related caches
            await self._invalidate_product_caches(product_id)
            
            logger.info(f"Deleted product with ID: {product_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting product {product_id}: {e}")
            raise ValueError("Cannot delete product due to existing dependencies")

    async def update_stock(self, product_id: int, new_quantity: int) -> Optional[Product]:
        """
        Update product stock quantity.
        
        Args:
            product_id: ID of product to update
            new_quantity: New stock quantity
            
        Returns:
            Updated product or None if not found
            
        Raises:
            ValueError: If quantity is invalid
        """
        if new_quantity < 0:
            raise ValueError("Stock quantity cannot be negative")
            
        product = await self.repo.get_by_id(product_id)
        if not product:
            return None
            
        product.stock_quantity = new_quantity
        
        try:
            self.session.add(product)
            await self.session.commit()
            await self.session.refresh(product)
            
            # Invalidate related caches
            await self._invalidate_product_caches(product_id)
            
            logger.info(f"Updated stock for product {product_id} to {new_quantity}")
            return product
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating stock for product {product_id}: {e}")
            raise ValueError("Failed to update stock quantity")

    async def _validate_product_creation(self, payload: ProductCreate) -> None:
        """Validate business rules for product creation."""
        # Price validation
        min_price = Decimal(str(settings.MIN_PRODUCT_PRICE))
        max_price = Decimal(str(settings.MAX_PRODUCT_PRICE))
        
        if payload.unit_price < min_price:
            raise ValueError(f"Product price must be at least ${min_price}")
            
        if payload.unit_price > max_price:
            raise ValueError(f"Product price cannot exceed ${max_price}")
        
        # SKU validation
        if not payload.sku or len(payload.sku.strip()) == 0:
            raise ValueError("Product SKU is required")
            
        if len(payload.sku) > settings.MAX_SKU_LENGTH:
            raise ValueError(f"SKU cannot exceed {settings.MAX_SKU_LENGTH} characters")
            
        # Stock validation
        if hasattr(payload, 'stock_quantity') and payload.stock_quantity < 0:
            raise ValueError("Stock quantity cannot be negative")
            
        # Name validation
        if not payload.name or len(payload.name.strip()) == 0:
            raise ValueError("Product name is required")

    async def _validate_product_update(self, product: Product, payload: ProductUpdate) -> None:
        """Validate business rules for product update."""
        # Price validation
        if payload.unit_price is not None:
            min_price = Decimal(str(settings.MIN_PRODUCT_PRICE))
            max_price = Decimal(str(settings.MAX_PRODUCT_PRICE))
            
            if payload.unit_price < min_price:
                raise ValueError(f"Product price must be at least ${min_price}")
                
            if payload.unit_price > max_price:
                raise ValueError(f"Product price cannot exceed ${max_price}")
        
        # SKU validation
        if payload.sku is not None:
            if not payload.sku or len(payload.sku.strip()) == 0:
                raise ValueError("Product SKU cannot be empty")
                
            if len(payload.sku) > settings.MAX_SKU_LENGTH:
                raise ValueError(f"SKU cannot exceed {settings.MAX_SKU_LENGTH} characters")
                
        # Stock validation
        if hasattr(payload, 'stock_quantity') and payload.stock_quantity is not None:
            if payload.stock_quantity < 0:
                raise ValueError("Stock quantity cannot be negative")
                
        # Name validation
        if payload.name is not None and (not payload.name or len(payload.name.strip()) == 0):
            raise ValueError("Product name cannot be empty")

    async def _validate_product_deletion(self, product: Product) -> None:
        """Validate business rules for product deletion."""
        # Check if product has pending orders (this would require Order model)
        # For now, we'll just log the deletion
        logger.info(f"Validating deletion of product: {product.sku}")
        
        # Future: Add checks for:
        # - Active orders containing this product
        # - Cart items referencing this product
        # - Transaction history
        pass

    async def _invalidate_product_caches(self, product_id: Optional[int] = None) -> None:
        """
        Invalidate product-related cache entries.
        
        Args:
            product_id: Specific product ID to invalidate (if None, invalidates all)
        """
        try:
            # Always invalidate list caches as they might contain any product
            await invalidate_cache_pattern("products:list:*")
            
            if product_id:
                # Invalidate specific product cache
                await invalidate_cache_key(f"products:detail:{product_id}")
                
                # Try to get product to invalidate SKU cache
                # (we need to do this before/after the actual DB operation)
                product = await self.repo.get_by_id(product_id)
                if product:
                    await invalidate_cache_key(f"products:sku:{product.sku}")
            else:
                # Invalidate all product caches
                await invalidate_cache_pattern("products:detail:*")
                await invalidate_cache_pattern("products:sku:*")
                
            logger.debug(f"Cache invalidated for product_id: {product_id}")
            
        except Exception as e:
            # Don't fail the operation if cache invalidation fails
            logger.warning(f"Failed to invalidate product cache: {e}")

    async def get_active_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Get active products only with caching.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active products
        """
        return await self._get_active_products_cached(skip, limit)

    @cache_key_wrapper("products:active", ttl=300)  # 5 minutes cache
    async def _get_active_products_cached(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """Internal cached method for active products."""
        statement = (
            select(Product)
            .where(Product.status == "ACTIVE")
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()