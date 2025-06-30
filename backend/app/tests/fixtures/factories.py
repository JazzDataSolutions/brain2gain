"""
Test data factories using Factory Boy for creating test objects.
"""

from decimal import Decimal
from uuid import uuid4
import random

import factory
from faker import Faker
from sqlmodel import Session

from app.core.security import get_password_hash
from app.models import (
    Cart,
    CartItem,
    Customer,
    Product,
    Role,
    SalesItem,
    SalesOrder,
    Stock,
    Transaction,
    User,
    UserRoleLink,
)

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

    id = factory.LazyFunction(uuid4)
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

    product_id = factory.Sequence(lambda n: n + 1)
    sku = factory.Sequence(lambda n: f"WP-{n:03d}")
    name = factory.LazyAttribute(
        lambda _: fake.sentence(nb_words=3)[:-1]
    )  # Remove period
    description = factory.LazyAttribute(lambda _: fake.text(max_nb_chars=200))
    unit_price = factory.LazyAttribute(
        lambda _: Decimal(
            str(
                fake.pydecimal(
                    left_digits=3,
                    right_digits=2,
                    positive=True,
                    min_value=10,
                    max_value=200,
                )
            )
        )
    )
    category = factory.Iterator(
        ["proteins", "creatine", "pre-workout", "vitamins", "amino-acids"]
    )
    brand = factory.Iterator(
        ["Optimum Nutrition", "Dymatize", "BSN", "Muscletech", "ON"]
    )
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

    customer_id = factory.LazyFunction(lambda: None)  # Let DB auto-generate
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

    so_id = factory.LazyFunction(lambda: None)  # Let DB auto-generate
    customer_id = factory.SubFactory(CustomerFactory)
    order_date = factory.LazyAttribute(lambda _: fake.date_time_this_year())
    status = factory.Iterator(
        ["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"]
    )


class SalesItemFactory(factory.Factory):
    """Factory for SalesItem model."""

    class Meta:
        model = SalesItem

    so_id = factory.SubFactory(SalesOrderFactory)
    product_id = factory.SubFactory(ProductFactory)
    qty = factory.LazyAttribute(lambda _: fake.random_int(min=1, max=5))
    unit_price = factory.LazyAttribute(
        lambda _: Decimal(
            str(
                fake.pydecimal(
                    left_digits=3,
                    right_digits=2,
                    positive=True,
                    min_value=10,
                    max_value=200,
                )
            )
        )
    )


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

    tx_id = factory.LazyFunction(lambda: None)  # Let DB auto-generate
    tx_type = factory.Iterator(["SALE", "PURCHASE", "CREDIT", "PAYMENT"])
    amount = factory.LazyAttribute(
        lambda _: Decimal(
            str(
                fake.pydecimal(
                    left_digits=3,
                    right_digits=2,
                    positive=True,
                    min_value=10,
                    max_value=1000,
                )
            )
        )
    )
    paid = True
    paid_date = factory.LazyAttribute(lambda _: fake.date_this_year())
    customer_id = factory.SubFactory(CustomerFactory)


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

    user_role_link = UserRoleLink(user_id=user.id, role_id=role.role_id)
    session.add(user_role_link)
    session.commit()

    return user


def create_product_with_stock(
    session: Session, stock_quantity: int = 100
) -> tuple[Product, Stock]:
    """Create a product with associated stock."""
    product = ProductFactory()
    session.add(product)
    session.commit()

    stock = StockFactory(product_id=product.product_id, quantity=stock_quantity)
    session.add(stock)
    session.commit()

    return product, stock


def create_order_with_items(
    session: Session, num_items: int = 3
) -> tuple[SalesOrder, list[SalesItem]]:
    """Create a sales order with multiple items."""
    customer = CustomerFactory()
    session.add(customer)
    session.commit()

    order = SalesOrderFactory(customer_id=customer.customer_id)
    session.add(order)
    session.commit()

    items = []

    for _ in range(num_items):
        product = ProductFactory()
        session.add(product)
        session.commit()

        item = SalesItemFactory(so_id=order.so_id, product_id=product.product_id)
        session.add(item)
        items.append(item)

    session.commit()

    return order, items


def create_cart_with_items(
    session: Session, user_id: str = None, num_items: int = 2
) -> tuple[Cart, list[CartItem]]:
    """Create a cart with multiple items."""
    if user_id is None:
        user = UserFactory()
        session.add(user)
        session.commit()
        user_id = user.id

    cart = CartFactory(user_id=user_id)
    session.add(cart)
    session.commit()

    items = []
    for _ in range(num_items):
        product = ProductFactory()
        session.add(product)
        session.commit()

        item = CartItemFactory(cart_id=cart.cart_id, product_id=product.product_id)
        session.add(item)
        items.append(item)

    session.commit()
    return cart, items


# ─── ANALYTICS-SPECIFIC FACTORIES AND HELPERS ────────────────────────────────


def create_analytics_test_data(session: Session, time_period_days: int = 30) -> dict:
    """
    Create a comprehensive dataset for analytics testing.

    Returns a dictionary with all created objects for easy access in tests.
    """
    from datetime import datetime, timedelta

    # Create customers
    customers = []
    for _i in range(20):
        customer = CustomerFactory()
        session.add(customer)
        customers.append(customer)
    session.commit()

    # Create products with stock
    products = []
    for _i in range(10):
        product = ProductFactory()
        session.add(product)
        session.commit()

        stock = StockFactory(
            product_id=product.product_id, quantity=fake.random_int(min=0, max=500)
        )
        session.add(stock)
        products.append((product, stock))
    session.commit()

    # Create orders and transactions across time period
    orders = []
    transactions = []

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=time_period_days)

    for _i in range(50):  # 50 orders across the period
        # Random date within the period
        order_date = fake.date_time_between(start_date=start_date, end_date=end_date)

        customer = fake.random.choice(customers)
        order = SalesOrderFactory(
            customer_id=customer.customer_id,
            order_date=order_date,
            status=fake.random.choice(
                ["PENDING", "COMPLETED", "COMPLETED", "COMPLETED"]
            ),  # Bias toward completed
        )
        session.add(order)
        session.commit()

        # Add items to order
        num_items = fake.random_int(min=1, max=4)

        for _ in range(num_items):
            product, _ = fake.random.choice(products)
            quantity = fake.random_int(min=1, max=3)
            unit_price = product.unit_price

            item = SalesItemFactory(
                so_id=order.so_id,
                product_id=product.product_id,
                qty=quantity,
                unit_price=unit_price,
            )
            session.add(item)
        orders.append(order)

        # Create corresponding transaction if order is completed
        if order.status == "COMPLETED":
            transaction = TransactionFactory(
                customer_id=customer.customer_id,
                tx_type="SALE",
                paid=True,
                paid_date=order_date,
            )
            session.add(transaction)
            transactions.append(transaction)

    session.commit()

    # Create some carts (for abandonment rate calculation)
    carts = []
    for _i in range(15):
        user = UserFactory()
        session.add(user)
        session.commit()

        cart = CartFactory(user_id=user.id)
        session.add(cart)
        session.commit()

        # Add items to some carts
        for _ in range(fake.random_int(min=1, max=3)):
            product, _ = fake.random.choice(products)
            cart_item = CartItemFactory(
                cart_id=cart.cart_id, product_id=product.product_id
            )
            session.add(cart_item)

        carts.append(cart)

    session.commit()

    return {
        "customers": customers,
        "products": [p[0] for p in products],
        "stocks": [p[1] for p in products],
        "orders": orders,
        "transactions": transactions,
        "carts": carts,
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "days": time_period_days,
        },
    }


def create_churn_scenario_data(session: Session) -> dict:
    """
    Create specific data scenario for testing churn rate calculations.
    """
    from datetime import datetime, timedelta

    customers = []
    orders = []
    transactions = []

    # Scenario: 10 customers, 5 are churned (haven't ordered in 60+ days)
    current_date = datetime.utcnow()

    # Active customers (ordered recently)
    for _i in range(5):
        customer = CustomerFactory()
        session.add(customer)
        session.commit()
        customers.append(customer)

        # Recent order (within last 30 days)
        recent_date = current_date - timedelta(days=fake.random_int(min=1, max=30))
        order = SalesOrderFactory(
            customer_id=customer.customer_id, order_date=recent_date, status="COMPLETED"
        )
        session.add(order)
        orders.append(order)

        transaction = TransactionFactory(
            customer_id=customer.customer_id,
            tx_type="SALE",
            paid=True,
            paid_date=recent_date,
        )
        session.add(transaction)
        transactions.append(transaction)

    # Churned customers (last order 60+ days ago)
    for _i in range(5):
        customer = CustomerFactory()
        session.add(customer)
        session.commit()
        customers.append(customer)

        # Old order (60+ days ago)
        old_date = current_date - timedelta(days=fake.random_int(min=60, max=180))
        order = SalesOrderFactory(
            customer_id=customer.customer_id, order_date=old_date, status="COMPLETED"
        )
        session.add(order)
        orders.append(order)

        transaction = TransactionFactory(
            customer_id=customer.customer_id,
            tx_type="SALE",
            paid=True,
            paid_date=old_date,
        )
        session.add(transaction)
        transactions.append(transaction)

    session.commit()

    return {
        "customers": customers,
        "orders": orders,
        "transactions": transactions,
        "active_customers": 5,
        "churned_customers": 5,
        "expected_churn_rate": 50.0,  # 5 out of 10 customers churned
    }


def create_mrr_scenario_data(session: Session) -> dict:
    """
    Create specific data scenario for testing MRR calculations.
    """
    from datetime import datetime, timedelta

    customers = []
    orders = []
    transactions = []

    current_date = datetime.utcnow()
    thirty_days_ago = current_date - timedelta(days=30)

    # Create customers with multiple orders (recurring revenue pattern)
    recurring_amounts = []

    for _i in range(8):  # 8 customers with recurring patterns
        customer = CustomerFactory()
        session.add(customer)
        session.commit()
        customers.append(customer)

        # Each customer has 2-3 orders in the last 30 days
        num_orders = fake.random_int(min=2, max=3)
        customer_total = Decimal("0")

        for _j in range(num_orders):
            order_date = fake.date_time_between(
                start_date=thirty_days_ago, end_date=current_date
            )
            amount = Decimal(
                str(
                    fake.pydecimal(
                        left_digits=2,
                        right_digits=2,
                        positive=True,
                        min_value=50,
                        max_value=200,
                    )
                )
            )

            order = SalesOrderFactory(
                customer_id=customer.customer_id,
                order_date=order_date,
                status="COMPLETED",
            )
            session.add(order)
            orders.append(order)

            transaction = TransactionFactory(
                customer_id=customer.customer_id,
                tx_type="SALE",
                amount=amount,
                paid=True,
                paid_date=order_date,
            )
            session.add(transaction)
            transactions.append(transaction)
            customer_total += amount

        recurring_amounts.append(customer_total)

    session.commit()

    expected_mrr = sum(recurring_amounts)

    return {
        "customers": customers,
        "orders": orders,
        "transactions": transactions,
        "expected_mrr": float(expected_mrr),
        "expected_arr": float(expected_mrr * 12),
    }


def create_conversion_scenario_data(session: Session) -> dict:
    """
    Create specific data scenario for testing conversion rate calculations.
    """
    # Create visitors (represented by carts)
    users = []
    carts = []
    orders = []

    # Scenario: 20 visitors, 4 convert (20% conversion rate)

    # 16 visitors who added to cart but didn't convert
    for _i in range(16):
        user = UserFactory()
        session.add(user)
        session.commit()
        users.append(user)

        cart = CartFactory(user_id=user.id)
        session.add(cart)
        carts.append(cart)

    # 4 visitors who converted
    for _i in range(4):
        user = UserFactory()
        session.add(user)
        session.commit()
        users.append(user)

        cart = CartFactory(user_id=user.id)
        session.add(cart)
        carts.append(cart)

        # Create corresponding order
        customer = CustomerFactory(email=user.email)
        session.add(customer)
        session.commit()

        order = SalesOrderFactory(customer_id=customer.customer_id, status="COMPLETED")
        session.add(order)
        orders.append(order)

    session.commit()

    return {
        "users": users,
        "carts": carts,
        "orders": orders,
        "total_visitors": 20,
        "converting_customers": 4,
        "expected_conversion_rate": 20.0,
    }
