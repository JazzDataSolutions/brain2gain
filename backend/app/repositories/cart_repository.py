from typing import Optional, List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.models import Cart, CartItem, Product

class CartRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_cart_by_user(self, user_id: UUID) -> Optional[Cart]:
        """Get cart by user ID"""
        statement = select(Cart).where(Cart.user_id == user_id)
        result = await self.session.exec(statement)
        return result.first()

    async def get_cart_by_session(self, session_id: str) -> Optional[Cart]:
        """Get cart by session ID (for guest users)"""
        statement = select(Cart).where(Cart.session_id == session_id)
        result = await self.session.exec(statement)
        return result.first()

    async def get_cart_with_items(self, cart_id: int) -> Optional[Cart]:
        """Get cart with its items and product details"""
        statement = (
            select(Cart)
            .where(Cart.cart_id == cart_id)
            .options(
                selectinload(Cart.items).selectinload(CartItem.product)
            )
        )
        result = await self.session.exec(statement)
        return result.first()

    async def create_cart(self, cart: Cart) -> Cart:
        """Create a new cart"""
        self.session.add(cart)
        await self.session.commit()
        await self.session.refresh(cart)
        return cart

    async def get_cart_item(self, cart_id: int, product_id: int) -> Optional[CartItem]:
        """Get specific cart item"""
        statement = select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id
        )
        result = await self.session.exec(statement)
        return result.first()

    async def add_cart_item(self, cart_item: CartItem) -> CartItem:
        """Add item to cart"""
        self.session.add(cart_item)
        await self.session.commit()
        await self.session.refresh(cart_item)
        return cart_item

    async def update_cart_item(self, cart_item: CartItem) -> CartItem:
        """Update cart item quantity"""
        self.session.add(cart_item)
        await self.session.commit()
        await self.session.refresh(cart_item)
        return cart_item

    async def remove_cart_item(self, cart_item: CartItem) -> None:
        """Remove item from cart"""
        await self.session.delete(cart_item)
        await self.session.commit()

    async def clear_cart(self, cart_id: int) -> None:
        """Remove all items from cart"""
        statement = select(CartItem).where(CartItem.cart_id == cart_id)
        result = await self.session.exec(statement)
        items = result.all()
        
        for item in items:
            await self.session.delete(item)
        
        await self.session.commit()

    async def get_cart_items_with_products(self, cart_id: int) -> List[CartItem]:
        """Get all cart items with product details"""
        statement = (
            select(CartItem)
            .where(CartItem.cart_id == cart_id)
            .options(selectinload(CartItem.product))
        )
        result = await self.session.exec(statement)
        return result.all()