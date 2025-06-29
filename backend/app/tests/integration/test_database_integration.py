"""
Integration tests for database functionality.
Tests the complete database stack: models, repositories, and services.
"""

import pytest
from decimal import Decimal
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool

from app.models import Product, User, Stock, Customer, Cart, CartItem
from app.repositories.product_repository import ProductRepository


# In-memory SQLite for integration testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    SQLModel.metadata.create_all(test_engine)
    
    with Session(test_engine) as session:
        try:
            yield session
        finally:
            session.rollback()
    
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(scope="function")
def sample_products(db_session: Session) -> list[Product]:
    """Create sample products for testing"""
    products = [
        Product(
            sku="INT-001",
            name="Integration Test Whey Protein",
            description="High quality whey protein for integration testing",
            unit_price=Decimal("45.99"),
            category="proteins",
            brand="Test Brand",
            status="ACTIVE"
        ),
        Product(
            sku="INT-002", 
            name="Integration Test Creatine",
            description="Pure creatine monohydrate for integration testing",
            unit_price=Decimal("29.99"),
            category="creatine",
            brand="Test Brand",
            status="ACTIVE"
        ),
        Product(
            sku="INT-003",
            name="Integration Test Pre-Workout",
            description="Energy boosting pre-workout for integration testing",
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


class TestDatabaseIntegration:
    """Integration tests for complete database functionality."""

    def test_database_creation_and_tables(self, db_session: Session):
        """Test that database is created with all required tables."""
        # Test that we can execute basic queries on all main tables
        
        # Test Product table
        product_result = db_session.exec(select(Product)).all()
        assert isinstance(product_result, list)
        
        # Test we can query other tables without errors
        user_result = db_session.exec(select(User)).all()
        assert isinstance(user_result, list)

    def test_product_repository_crud_integration(self, db_session: Session):
        """Test complete CRUD operations through ProductRepository."""
        repository = ProductRepository(db_session)
        
        # CREATE
        product_data = {
            "sku": "CRUD-001",
            "name": "CRUD Test Product",
            "description": "Product for CRUD integration testing",
            "unit_price": Decimal("55.99"),
            "category": "proteins",
            "brand": "CRUD Brand",
            "status": "ACTIVE",
        }
        
        created_product = repository.create(**product_data)
        assert created_product.sku == "CRUD-001"
        assert created_product.product_id is not None
        
        # READ
        retrieved_product = repository.get_by_id(created_product.product_id)
        assert retrieved_product is not None
        assert retrieved_product.sku == "CRUD-001"
        assert retrieved_product.name == "CRUD Test Product"
        
        # READ by SKU
        sku_product = repository.get_by_sku("CRUD-001")
        assert sku_product is not None
        assert sku_product.product_id == created_product.product_id
        
        # UPDATE
        updated_product = repository.update(
            created_product.product_id,
            name="Updated CRUD Product",
            unit_price=Decimal("65.99")
        )
        assert updated_product is not None
        assert updated_product.name == "Updated CRUD Product"
        assert updated_product.unit_price == Decimal("65.99")
        
        # Verify update persisted
        re_retrieved = repository.get_by_id(created_product.product_id)
        assert re_retrieved.name == "Updated CRUD Product"
        
        # DELETE
        delete_success = repository.delete(created_product.product_id)
        assert delete_success is True
        
        # Verify deletion
        deleted_product = repository.get_by_id(created_product.product_id)
        assert deleted_product is None

    def test_product_repository_queries_integration(self, db_session: Session, sample_products: list[Product]):
        """Test complex queries through ProductRepository."""
        repository = ProductRepository(db_session)
        
        # Test category filtering
        protein_products = repository.get_by_category("proteins")
        assert len(protein_products) == 1
        assert protein_products[0].category == "proteins"
        
        # Test status filtering
        active_products = repository.get_active_products()
        assert len(active_products) == 2
        
        discontinued_products = repository.get_by_status("DISCONTINUED")
        assert len(discontinued_products) == 1
        assert discontinued_products[0].status == "DISCONTINUED"
        
        # Test search
        search_results = repository.search_by_name("Integration Test")
        assert len(search_results) == 3  # All sample products contain "Integration Test"
        
        # Test pagination
        page1 = repository.get_paginated(offset=0, limit=2)
        assert len(page1) == 2
        
        page2 = repository.get_paginated(offset=2, limit=2)
        assert len(page2) == 1
        
        # Verify no overlap
        page1_ids = [p.product_id for p in page1]
        page2_ids = [p.product_id for p in page2]
        assert not set(page1_ids).intersection(set(page2_ids))
        
        # Test counting
        total_count = repository.count()
        assert total_count == 3
        
        protein_count = repository.count_by_category("proteins")
        assert protein_count == 1
        
        creatine_count = repository.count_by_category("creatine")
        assert creatine_count == 1

    def test_product_repository_business_rules(self, db_session: Session):
        """Test business rules and constraints through repository."""
        repository = ProductRepository(db_session)
        
        # Test duplicate SKU handling
        product1_data = {
            "sku": "DUPLICATE-001",
            "name": "First Product",
            "unit_price": Decimal("30.00"),
            "category": "proteins",
            "brand": "Test Brand"
        }
        
        product2_data = {
            "sku": "DUPLICATE-001",  # Same SKU
            "name": "Second Product",
            "unit_price": Decimal("40.00"),
            "category": "creatine",
            "brand": "Test Brand"
        }
        
        # First product should create successfully
        product1 = repository.create(**product1_data)
        assert product1.sku == "DUPLICATE-001"
        
        # Second product with same SKU should fail
        with pytest.raises(Exception):  # Could be IntegrityError or other DB constraint error
            repository.create(**product2_data)

    def test_multiple_repository_transactions(self, db_session: Session):
        """Test that multiple operations in single transaction work correctly."""
        repository = ProductRepository(db_session)
        
        # Create multiple products in same transaction
        products_data = [
            {
                "sku": f"BATCH-{i:03d}",
                "name": f"Batch Product {i}",
                "unit_price": Decimal(f"{25 + i}.99"),
                "category": "proteins",
                "brand": "Batch Brand"
            }
            for i in range(1, 6)
        ]
        
        created_products = []
        for product_data in products_data:
            product = repository.create(**product_data)
            created_products.append(product)
        
        # Verify all products were created
        assert len(created_products) == 5
        
        # Verify they're all in the database
        total_count = repository.count()
        assert total_count >= 5  # At least the 5 we created
        
        # Test bulk operations
        product_ids = [p.product_id for p in created_products]
        updated_count = repository.bulk_update_status(product_ids, "DISCONTINUED")
        assert updated_count == 5
        
        # Verify bulk update worked
        discontinued_products = repository.get_by_status("DISCONTINUED")
        discontinued_ids = [p.product_id for p in discontinued_products]
        for product_id in product_ids:
            assert product_id in discontinued_ids

    def test_database_relationships(self, db_session: Session, sample_products: list[Product]):
        """Test that database relationships work correctly."""
        # Note: This is a basic test since our current model doesn't have complex relationships
        # But it validates that the database schema is properly set up
        
        product = sample_products[0]
        
        # Test that we can query related data (even if no relations exist yet)
        # This validates that the database schema is intact
        statement = select(Product).where(Product.product_id == product.product_id)
        result = db_session.exec(statement).first()
        
        assert result is not None
        assert result.product_id == product.product_id
        assert result.sku == product.sku

    def test_database_performance_basic(self, db_session: Session):
        """Test basic database performance with bulk operations."""
        repository = ProductRepository(db_session)
        
        # Create a larger number of products to test performance
        import time
        start_time = time.time()
        
        batch_size = 50
        for i in range(batch_size):
            product_data = {
                "sku": f"PERF-{i:04d}",
                "name": f"Performance Test Product {i}",
                "unit_price": Decimal(f"{20 + (i % 30)}.99"),
                "category": "proteins" if i % 2 == 0 else "creatine",
                "brand": "Performance Brand"
            }
            repository.create(**product_data)
        
        creation_time = time.time() - start_time
        
        # Test that creation was reasonably fast (should be under 5 seconds for 50 products)
        assert creation_time < 5.0, f"Creation took {creation_time:.2f} seconds, which is too slow"
        
        # Test bulk query performance
        start_time = time.time()
        all_products = repository.get_all()
        query_time = time.time() - start_time
        
        assert len(all_products) >= batch_size
        assert query_time < 1.0, f"Query took {query_time:.2f} seconds, which is too slow"

    def test_database_consistency(self, db_session: Session):
        """Test database consistency and transaction handling."""
        repository = ProductRepository(db_session)
        
        # Test transaction consistency
        initial_count = repository.count()
        
        try:
            # Create a product
            product = repository.create(
                sku="CONSISTENCY-001",
                name="Consistency Test Product",
                unit_price=Decimal("30.00"),
                category="proteins",
                brand="Test Brand"
            )
            
            # Verify it exists
            intermediate_count = repository.count()
            assert intermediate_count == initial_count + 1
            
            # Verify we can retrieve it
            retrieved = repository.get_by_id(product.product_id)
            assert retrieved is not None
            assert retrieved.sku == "CONSISTENCY-001"
            
        except Exception as e:
            pytest.fail(f"Database consistency test failed: {e}")
        
        # Final verification
        final_count = repository.count()
        assert final_count == initial_count + 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])