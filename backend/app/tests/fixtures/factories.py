"""
Test data factories using Factory Boy for creating test objects.
"""

import factory
from faker import Faker
from sqlmodel import Session
from decimal import Decimal
from uuid import uuid4

from app.models import (
    User, Role, UserRoleLink, Product, Stock, Customer, 
    SalesOrder, SalesItem, Cart, CartItem, Transaction
)
from app.core.security import get_password_hash

fake = Faker()


class RoleFactory(factory.Factory):
    """Factory for Role model."""
    
    class Meta:
        model = Role
    
    role_id = factory.LazyFunction(uuid4)
    name = factory.Iterator(["ADMIN", "MANAGER", "SELLER", "ACCOUNTANT", "USER"])
    description = factory.LazyAttribute(lambda obj: f"Role for {obj.name.lower()}")


class UserFactory(factory.Factory):
    """Factory for User model."""
    
    class Meta:
        model = User
    
    user_id = factory.LazyFunction(uuid4)
    email = factory.LazyAttribute(lambda _: fake.email())
    hashed_password = factory.LazyFunction(lambda: get_password_hash("testpassword123"))
    full_name = factory.LazyAttribute(lambda _: fake.name())
    is_active = True
    is_superuser = False


class SuperUserFactory(UserFactory):
    """Factory for superuser."""
    
    is_superuser = True
    email = factory.Sequence(lambda n: f"admin{n}@brain2gain.com")


class ProductFactory(factory.Factory):
    """Factory for Product model."""
    
    class Meta:
        model = Product
    
    product_id = factory.LazyFunction(uuid4)
    sku = factory.Sequence(lambda n: f"WP-{n:03d}")
    name = factory.LazyAttribute(lambda _: fake.sentence(nb_words=3)[:-1])  # Remove period
    description = factory.LazyAttribute(lambda _: fake.text(max_nb_chars=200))
    unit_price = factory.LazyAttribute(lambda _: Decimal(str(fake.pydecimal(
        left_digits=2, right_digits=2, positive=True, min_value=10, max_value=200
    ))))
    category = factory.Iterator([
        "proteins", "creatine", "pre-workout", "vitamins", "amino-acids"
    ])
    brand = factory.Iterator([
        "Optimum Nutrition", "Dymatize", "BSN", "Muscletech", "ON"
    ])
    status = factory.Iterator(["ACTIVE", "INACTIVE", "DISCONTINUED"])


class StockFactory(factory.Factory):
    """Factory for Stock model."""
    
    class Meta:
        model = Stock
    
    stock_id = factory.LazyFunction(uuid4)
    product_id = factory.SubFactory(ProductFactory)
    quantity = factory.LazyAttribute(lambda _: fake.random_int(min=0, max=1000))
    reserved_quantity = factory.LazyAttribute(lambda _: fake.random_int(min=0, max=50))
    min_stock_level = factory.LazyAttribute(lambda _: fake.random_int(min=5, max=20))


class CustomerFactory(factory.Factory):
    """Factory for Customer model."""
    
    class Meta:
        model = Customer
    
    customer_id = factory.LazyFunction(uuid4)
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name = factory.LazyAttribute(lambda _: fake.last_name())
    email = factory.LazyAttribute(lambda _: fake.email())
    phone = factory.LazyAttribute(lambda _: fake.phone_number())
    address = factory.LazyAttribute(lambda _: fake.address())
    city = factory.LazyAttribute(lambda _: fake.city())
    country = factory.LazyAttribute(lambda _: fake.country())
    is_active = True


class SalesOrderFactory(factory.Factory):
    """Factory for SalesOrder model."""
    
    class Meta:
        model = SalesOrder
    
    order_id = factory.LazyFunction(uuid4)
    customer_id = factory.SubFactory(CustomerFactory)
    order_date = factory.LazyAttribute(lambda _: fake.date_time_this_year())
    status = factory.Iterator(["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"])
    total_amount = factory.LazyAttribute(lambda _: Decimal(str(fake.pydecimal(
        left_digits=3, right_digits=2, positive=True, min_value=20, max_value=500
    ))))
    shipping_address = factory.LazyAttribute(lambda _: fake.address())
    payment_method = factory.Iterator(["CREDIT_CARD", "DEBIT_CARD", "PAYPAL", "BANK_TRANSFER"])


class SalesItemFactory(factory.Factory):
    """Factory for SalesItem model."""
    
    class Meta:
        model = SalesItem
    
    item_id = factory.LazyFunction(uuid4)
    order_id = factory.SubFactory(SalesOrderFactory)
    product_id = factory.SubFactory(ProductFactory)
    quantity = factory.LazyAttribute(lambda _: fake.random_int(min=1, max=5))
    unit_price = factory.LazyAttribute(lambda _: Decimal(str(fake.pydecimal(
        left_digits=2, right_digits=2, positive=True, min_value=10, max_value=200
    ))))


class CartFactory(factory.Factory):
    """Factory for Cart model."""
    
    class Meta:
        model = Cart
    
    cart_id = factory.LazyFunction(uuid4)
    user_id = factory.SubFactory(UserFactory)
    session_id = factory.LazyAttribute(lambda _: fake.uuid4())
    created_at = factory.LazyAttribute(lambda _: fake.date_time_this_month())
    updated_at = factory.LazyAttribute(lambda _: fake.date_time_this_month())


class CartItemFactory(factory.Factory):
    """Factory for CartItem model."""
    
    class Meta:
        model = CartItem
    
    cart_item_id = factory.LazyFunction(uuid4)
    cart_id = factory.SubFactory(CartFactory)
    product_id = factory.SubFactory(ProductFactory)
    quantity = factory.LazyAttribute(lambda _: fake.random_int(min=1, max=10))
    added_at = factory.LazyAttribute(lambda _: fake.date_time_this_month())


class TransactionFactory(factory.Factory):
    """Factory for Transaction model."""
    
    class Meta:
        model = Transaction
    
    transaction_id = factory.LazyFunction(uuid4)
    order_id = factory.SubFactory(SalesOrderFactory)
    transaction_type = factory.Iterator(["SALE", "REFUND", "PAYMENT"])
    amount = factory.LazyAttribute(lambda _: Decimal(str(fake.pydecimal(
        left_digits=3, right_digits=2, positive=True, min_value=10, max_value=1000
    ))))
    transaction_date = factory.LazyAttribute(lambda _: fake.date_time_this_year())
    payment_method = factory.Iterator(["CREDIT_CARD", "DEBIT_CARD", "PAYPAL", "BANK_TRANSFER"])
    status = factory.Iterator(["PENDING", "COMPLETED", "FAILED", "CANCELLED"])
    external_reference = factory.LazyAttribute(lambda _: fake.uuid4())


# Factory helper functions for tests
def create_user_with_role(session: Session, role_name: str = "USER") -> User:
    """Create a user with a specific role."""
    role = session.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = RoleFactory(name=role_name)
        session.add(role)
        session.commit()
    
    user = UserFactory()
    session.add(user)
    session.commit()
    
    user_role_link = UserRoleLink(user_id=user.user_id, role_id=role.role_id)
    session.add(user_role_link)
    session.commit()
    
    return user


def create_product_with_stock(session: Session, stock_quantity: int = 100) -> tuple[Product, Stock]:
    """Create a product with associated stock."""
    product = ProductFactory()
    session.add(product)
    session.commit()
    
    stock = StockFactory(product_id=product.product_id, quantity=stock_quantity)
    session.add(stock)
    session.commit()
    
    return product, stock


def create_order_with_items(session: Session, num_items: int = 3) -> tuple[SalesOrder, list[SalesItem]]:
    """Create a sales order with multiple items."""
    customer = CustomerFactory()
    session.add(customer)
    session.commit()
    
    order = SalesOrderFactory(customer_id=customer.customer_id)
    session.add(order)
    session.commit()
    
    items = []
    total_amount = Decimal('0')
    
    for _ in range(num_items):
        product = ProductFactory()
        session.add(product)
        session.commit()
        
        item = SalesItemFactory(
            order_id=order.order_id,
            product_id=product.product_id
        )
        session.add(item)
        items.append(item)
        
        total_amount += item.unit_price * item.quantity
    
    order.total_amount = total_amount
    session.commit()
    
    return order, items


def create_cart_with_items(session: Session, user_id: str = None, num_items: int = 2) -> tuple[Cart, list[CartItem]]:
    """Create a cart with multiple items."""
    if user_id is None:
        user = UserFactory()
        session.add(user)
        session.commit()
        user_id = user.user_id
    
    cart = CartFactory(user_id=user_id)
    session.add(cart)
    session.commit()
    
    items = []
    for _ in range(num_items):
        product = ProductFactory()
        session.add(product)
        session.commit()
        
        item = CartItemFactory(
            cart_id=cart.cart_id,
            product_id=product.product_id
        )
        session.add(item)
        items.append(item)
    
    session.commit()
    return cart, items