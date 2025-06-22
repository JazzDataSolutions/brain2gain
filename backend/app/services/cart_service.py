from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Cart, CartItem
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.cart import (
    AddToCartRequest,
    CartItemRead,
    CartRead,
    UpdateCartItemRequest,
)


class CartService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cart_repo = CartRepository(session)
        self.product_repo = ProductRepository(session)

    async def get_or_create_cart(self, user_id: UUID | None = None, session_id: str | None = None) -> Cart:
        """Get existing cart or create new one"""
        cart = None

        if user_id:
            cart = await self.cart_repo.get_cart_by_user(user_id)
        elif session_id:
            cart = await self.cart_repo.get_cart_by_session(session_id)

        if not cart:
            cart_data = Cart(
                user_id=user_id,
                session_id=session_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            cart = await self.cart_repo.create_cart(cart_data)

        return cart

    async def add_to_cart(
        self,
        request: AddToCartRequest,
        user_id: UUID | None = None,
        session_id: str | None = None
    ) -> CartRead:
        """Add product to cart"""
        # Verify product exists and is active
        product = await self.product_repo.get_by_id(request.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        if product.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product is not available"
            )

        # Get or create cart
        cart = await self.get_or_create_cart(user_id, session_id)

        # Check if item already exists in cart
        existing_item = await self.cart_repo.get_cart_item(cart.cart_id, request.product_id)

        if existing_item:
            # Update quantity
            existing_item.quantity += request.quantity
            existing_item.updated_at = datetime.utcnow()
            await self.cart_repo.update_cart_item(existing_item)
        else:
            # Add new item
            cart_item = CartItem(
                cart_id=cart.cart_id,
                product_id=request.product_id,
                quantity=request.quantity,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await self.cart_repo.add_cart_item(cart_item)

        # Update cart timestamp
        cart.updated_at = datetime.utcnow()
        self.session.add(cart)
        await self.session.commit()

        return await self.get_cart_details(cart.cart_id)

    async def update_cart_item(
        self,
        product_id: int,
        request: UpdateCartItemRequest,
        user_id: UUID | None = None,
        session_id: str | None = None
    ) -> CartRead:
        """Update cart item quantity"""
        cart = await self.get_or_create_cart(user_id, session_id)

        cart_item = await self.cart_repo.get_cart_item(cart.cart_id, product_id)
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found in cart"
            )

        cart_item.quantity = request.quantity
        cart_item.updated_at = datetime.utcnow()
        await self.cart_repo.update_cart_item(cart_item)

        # Update cart timestamp
        cart.updated_at = datetime.utcnow()
        self.session.add(cart)
        await self.session.commit()

        return await self.get_cart_details(cart.cart_id)

    async def remove_from_cart(
        self,
        product_id: int,
        user_id: UUID | None = None,
        session_id: str | None = None
    ) -> CartRead:
        """Remove item from cart"""
        cart = await self.get_or_create_cart(user_id, session_id)

        cart_item = await self.cart_repo.get_cart_item(cart.cart_id, product_id)
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found in cart"
            )

        await self.cart_repo.remove_cart_item(cart_item)

        # Update cart timestamp
        cart.updated_at = datetime.utcnow()
        self.session.add(cart)
        await self.session.commit()

        return await self.get_cart_details(cart.cart_id)

    async def get_cart(
        self,
        user_id: UUID | None = None,
        session_id: str | None = None
    ) -> CartRead:
        """Get cart details"""
        cart = await self.get_or_create_cart(user_id, session_id)
        return await self.get_cart_details(cart.cart_id)

    async def clear_cart(
        self,
        user_id: UUID | None = None,
        session_id: str | None = None
    ) -> None:
        """Clear all items from cart"""
        cart = await self.get_or_create_cart(user_id, session_id)
        await self.cart_repo.clear_cart(cart.cart_id)

    async def get_cart_details(self, cart_id: int) -> CartRead:
        """Get detailed cart information with items and totals"""
        items = await self.cart_repo.get_cart_items_with_products(cart_id)

        cart_items = []
        total_amount = Decimal('0.00')
        item_count = 0

        for item in items:
            item_total = item.product.unit_price * item.quantity
            total_amount += item_total
            item_count += item.quantity

            cart_items.append(CartItemRead(
                product_id=item.product_id,
                quantity=item.quantity,
                product_name=item.product.name,
                product_sku=item.product.sku,
                unit_price=item.product.unit_price,
                total_price=item_total
            ))

        # Get cart info
        cart = await self.session.get(Cart, cart_id)

        return CartRead(
            cart_id=cart_id,
            user_id=cart.user_id,
            session_id=cart.session_id,
            items=cart_items,
            total_amount=total_amount,
            item_count=item_count,
            created_at=cart.created_at,
            updated_at=cart.updated_at
        )
