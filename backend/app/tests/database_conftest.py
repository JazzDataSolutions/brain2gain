"""
Database testing configuration
Provides fixtures for tests that require database access
"""

import asyncio
import pytest
import pytest_asyncio
from collections.abc import Generator, AsyncGenerator
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.models import Product, User, Stock, Customer, SalesOrder, Cart, CartItem
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers


# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create engine with check_same_thread=False for SQLite
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.
    Uses in-memory SQLite for fast, isolated tests.
    """
    # Create all tables
    SQLModel.metadata.create_all(test_engine)
    
    with Session(test_engine) as session:
        try:
            yield session
        finally:
            session.rollback()
    
    # Drop all tables after test
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(scope="function") 
def db(db_session: Session) -> Session:
    """Alias for db_session for backward compatibility"""
    return db_session


@pytest.fixture(scope="function")
def client_with_db(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database dependency overridden
    """
    from app.core.db import get_session
    
    def override_get_session():
        return db_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up override
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_products(db_session: Session) -> list[Product]:
    """Create sample products for testing"""
    from decimal import Decimal
    
    products = [
        Product(
            sku="TEST-001",
            name="Test Whey Protein",
            description="High quality whey protein for testing",
            unit_price=Decimal("45.99"),
            category="proteins",
            brand="Test Brand",
            status="ACTIVE"
        ),
        Product(
            sku="TEST-002", 
            name="Test Creatine",
            description="Pure creatine monohydrate for testing",
            unit_price=Decimal("29.99"),
            category="creatine",
            brand="Test Brand",
            status="ACTIVE"
        ),
        Product(
            sku="TEST-003",
            name="Test Pre-Workout",
            description="Energy boosting pre-workout for testing",
            unit_price=Decimal("39.99"),
            category="pre-workout",
            brand="Test Brand",
            status="DISCONTINUED"
        )
    ]
    
    for product in products:
        db_session.add(product)
    
    db_session.commit()
    
    # Refresh to get the generated IDs
    for product in products:
        db_session.refresh(product)
    
    return products


@pytest.fixture(scope="function")
def sample_user(db_session: Session) -> User:
    """Create a sample user for testing"""
    from app.core.security import get_password_hash
    
    user = User(
        email="test@brain2gain.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def sample_superuser(db_session: Session) -> User:
    """Create a sample superuser for testing"""
    from app.core.security import get_password_hash
    
    user = User(
        email="admin@brain2gain.com",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def sample_stock(db_session: Session, sample_products: list[Product]) -> list[Stock]:
    """Create sample stock records for testing"""
    stock_records = []
    
    for product in sample_products:
        stock = Stock(
            product_id=product.product_id,
            quantity=100,
            reserved_quantity=0,
            min_stock_level=10
        )
        db_session.add(stock)
        stock_records.append(stock)
    
    db_session.commit()
    
    for stock in stock_records:
        db_session.refresh(stock)
    
    return stock_records


@pytest.fixture(scope="function")
def sample_customer(db_session: Session) -> Customer:
    """Create a sample customer for testing"""
    customer = Customer(
        first_name="Juan",
        last_name="Pérez",
        email="juan.perez@email.com",
        phone="+52 55 1234 5678",
        address="Av. Revolución 123",
        city="Ciudad de México",
        country="México",
        is_active=True
    )
    
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    
    return customer


@pytest.fixture(scope="function")
def sample_cart(db_session: Session, sample_user: User) -> Cart:
    """Create a sample cart for testing"""
    cart = Cart(
        user_id=sample_user.user_id,
        session_id="test-session-123",
        is_active=True
    )
    
    db_session.add(cart)
    db_session.commit()
    db_session.refresh(cart)
    
    return cart


@pytest.fixture(scope="function")
def sample_cart_with_items(
    db_session: Session, 
    sample_cart: Cart, 
    sample_products: list[Product]
) -> Cart:
    """Create a cart with sample items for testing"""
    for i, product in enumerate(sample_products[:2]):  # Add first 2 products
        cart_item = CartItem(
            cart_id=sample_cart.cart_id,
            product_id=product.product_id,
            quantity=i + 1,  # quantity 1 and 2
            unit_price=product.unit_price
        )
        db_session.add(cart_item)
    
    db_session.commit()
    
    # Refresh cart to get updated relationships
    db_session.refresh(sample_cart)
    
    return sample_cart


# Async fixtures for async tests
@pytest_asyncio.fixture
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create an async database session for async tests
    """
    # Create async engine for testing
    async_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async with AsyncSession(async_engine) as session:
        try:
            yield session
        finally:
            await session.rollback()
    
    # Clean up
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await async_engine.dispose()


# Test database utilities
class DatabaseTestUtils:
    """Utility class for database testing operations"""
    
    @staticmethod
    def create_test_product(
        session: Session,
        sku: str = "TEST-UTIL-001",
        name: str = "Test Product",
        category: str = "proteins",
        price: str = "50.00"
    ) -> Product:
        """Create a test product with minimal required fields"""
        from decimal import Decimal
        
        product = Product(
            sku=sku,
            name=name,
            description=f"Test description for {name}",
            unit_price=Decimal(price),
            category=category,
            brand="Test Brand",
            status="ACTIVE"
        )
        
        session.add(product)
        session.commit()
        session.refresh(product)
        
        return product
    
    @staticmethod
    def create_test_stock(
        session: Session,
        product: Product,
        quantity: int = 100
    ) -> Stock:
        """Create a test stock record for a product"""
        stock = Stock(
            product_id=product.product_id,
            quantity=quantity,
            reserved_quantity=0,
            min_stock_level=10
        )
        
        session.add(stock)
        session.commit()
        session.refresh(stock)
        
        return stock
    
    @staticmethod
    def cleanup_database(session: Session):
        """Clean up all test data from database"""
        # Delete in correct order to respect foreign key constraints
        session.execute("DELETE FROM cart_items")
        session.execute("DELETE FROM carts")
        session.execute("DELETE FROM sales_items")
        session.execute("DELETE FROM sales_orders")
        session.execute("DELETE FROM stocks")
        session.execute("DELETE FROM products")
        session.execute("DELETE FROM customers")
        session.execute("DELETE FROM user_role_links")
        session.execute("DELETE FROM users")
        session.execute("DELETE FROM roles")
        session.commit()


# Export utility instance
db_test_utils = DatabaseTestUtils()