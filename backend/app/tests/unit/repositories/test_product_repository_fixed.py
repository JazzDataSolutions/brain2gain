"""
Fixed unit tests for Product Repository layer with real database.
"""

from decimal import Decimal
import pytest
from sqlmodel import Session

from app.repositories.product_repository import ProductRepository
from app.models import Product
from app.tests.database_conftest import db_test_utils

# Import fixtures from database_conftest
pytest_plugins = ["app.tests.database_conftest"]


class TestProductRepositoryFixed:
    """Test cases for ProductRepository with real database integration."""

    @pytest.fixture
    def repository(self, db_session: Session) -> ProductRepository:
        """Create a ProductRepository instance with database session."""
        return ProductRepository(db_session)

    def test_create_product(self, repository: ProductRepository, db_session: Session):
        """Test creating a new product."""
        product_data = {
            "sku": "TEST-CREATE-001",
            "name": "Test Whey Protein Creation",
            "description": "High quality whey protein for creation test",
            "unit_price": Decimal("45.99"),
            "category": "proteins",
            "brand": "Test Brand",
            "status": "ACTIVE",
        }

        product = repository.create(**product_data)

        assert product.sku == "TEST-CREATE-001"
        assert product.name == "Test Whey Protein Creation"
        assert product.unit_price == Decimal("45.99")
        assert product.category == "proteins"
        assert product.status == "ACTIVE"
        assert product.product_id is not None

        # Verify it's actually in the database
        db_product = repository.get_by_id(product.product_id)
        assert db_product is not None
        assert db_product.sku == "TEST-CREATE-001"

    def test_get_product_by_id(self, repository: ProductRepository, sample_products: list[Product]):
        """Test retrieving a product by ID."""
        test_product = sample_products[0]
        
        # Retrieve product by ID
        retrieved_product = repository.get_by_id(test_product.product_id)
        
        assert retrieved_product is not None
        assert retrieved_product.product_id == test_product.product_id
        assert retrieved_product.sku == test_product.sku
        assert retrieved_product.name == test_product.name

    def test_get_product_by_id_not_found(self, repository: ProductRepository):
        """Test retrieving a non-existent product returns None."""
        non_existent_id = 99999
        product = repository.get_by_id(non_existent_id)
        assert product is None

    def test_get_product_by_sku(self, repository: ProductRepository, sample_products: list[Product]):
        """Test retrieving a product by SKU."""
        test_product = sample_products[0]
        
        retrieved_product = repository.get_by_sku(test_product.sku)
        
        assert retrieved_product is not None
        assert retrieved_product.sku == test_product.sku
        assert retrieved_product.product_id == test_product.product_id

    def test_get_product_by_sku_not_found(self, repository: ProductRepository):
        """Test retrieving a product by non-existent SKU returns None."""
        product = repository.get_by_sku("NON-EXISTENT-SKU")
        assert product is None

    def test_get_products_by_category(self, repository: ProductRepository, sample_products: list[Product]):
        """Test retrieving products by category."""
        # Get products by 'proteins' category
        protein_products = repository.get_by_category("proteins")
        
        assert len(protein_products) >= 1
        for product in protein_products:
            assert product.category == "proteins"

    def test_get_products_by_category_empty(self, repository: ProductRepository):
        """Test retrieving products by non-existent category returns empty list."""
        products = repository.get_by_category("non-existent-category")
        assert products == []

    def test_get_active_products(self, repository: ProductRepository, sample_products: list[Product]):
        """Test retrieving only active products."""
        active_products = repository.get_active_products()
        
        # Should have at least 2 active products from sample_products
        assert len(active_products) >= 2
        for product in active_products:
            assert product.status == "ACTIVE"

    def test_search_products_by_name(self, repository: ProductRepository, sample_products: list[Product]):
        """Test searching products by name."""
        # Search for products containing "Test"
        search_results = repository.search_by_name("Test")
        
        assert len(search_results) >= 1
        for product in search_results:
            assert "Test" in product.name

    def test_search_products_by_name_case_insensitive(self, repository: ProductRepository, sample_products: list[Product]):
        """Test searching products by name is case insensitive."""
        # Search with lowercase
        search_results = repository.search_by_name("test")
        
        assert len(search_results) >= 1
        for product in search_results:
            assert "Test" in product.name or "test" in product.name.lower()

    def test_search_products_by_name_no_results(self, repository: ProductRepository):
        """Test searching products by name with no matches returns empty list."""
        search_results = repository.search_by_name("NonExistentProductName")
        assert search_results == []

    def test_update_product(self, repository: ProductRepository, sample_products: list[Product]):
        """Test updating a product."""
        test_product = sample_products[0]
        original_name = test_product.name
        
        # Update product name and price
        update_data = {
            "name": "Updated Test Product Name",
            "unit_price": Decimal("99.99")
        }
        
        updated_product = repository.update(test_product.product_id, **update_data)
        
        assert updated_product is not None
        assert updated_product.product_id == test_product.product_id
        assert updated_product.name == "Updated Test Product Name"
        assert updated_product.unit_price == Decimal("99.99")
        assert updated_product.name != original_name

    def test_update_product_not_found(self, repository: ProductRepository):
        """Test updating a non-existent product returns None."""
        non_existent_id = 99999
        update_data = {"name": "This Should Not Work"}
        
        result = repository.update(non_existent_id, **update_data)
        assert result is None

    def test_delete_product(self, repository: ProductRepository, db_session: Session):
        """Test deleting a product."""
        # Create a product specifically for deletion test
        product = db_test_utils.create_test_product(
            db_session,
            sku="DELETE-TEST-001",
            name="Product To Delete"
        )
        
        product_id = product.product_id
        
        # Delete the product
        success = repository.delete(product_id)
        assert success is True
        
        # Verify it's deleted
        deleted_product = repository.get_by_id(product_id)
        assert deleted_product is None

    def test_delete_product_not_found(self, repository: ProductRepository):
        """Test deleting a non-existent product returns False."""
        non_existent_id = 99999
        success = repository.delete(non_existent_id)
        assert success is False

    def test_get_all_products(self, repository: ProductRepository, sample_products: list[Product]):
        """Test retrieving all products."""
        all_products = repository.get_all()
        
        # Should have at least the sample products
        assert len(all_products) >= len(sample_products)
        
        # Verify our sample products are in the results
        product_skus = [p.sku for p in all_products]
        for sample_product in sample_products:
            assert sample_product.sku in product_skus

    def test_get_products_with_pagination(self, repository: ProductRepository, sample_products: list[Product]):
        """Test retrieving products with pagination."""
        # Get first page (limit 2)
        first_page = repository.get_paginated(offset=0, limit=2)
        assert len(first_page) <= 2
        
        # Get second page
        second_page = repository.get_paginated(offset=2, limit=2)
        
        # Verify pages don't overlap
        first_page_ids = [p.product_id for p in first_page]
        second_page_ids = [p.product_id for p in second_page]
        
        # No overlap between pages
        assert not set(first_page_ids).intersection(set(second_page_ids))

    def test_count_products(self, repository: ProductRepository, sample_products: list[Product]):
        """Test counting products."""
        count = repository.count()
        assert count >= len(sample_products)
        assert isinstance(count, int)

    def test_count_products_by_category(self, repository: ProductRepository, sample_products: list[Product]):
        """Test counting products by category."""
        protein_count = repository.count_by_category("proteins")
        assert protein_count >= 1
        assert isinstance(protein_count, int)
        
        # Test non-existent category
        zero_count = repository.count_by_category("non-existent-category")
        assert zero_count == 0

    def test_get_products_by_status(self, repository: ProductRepository, sample_products: list[Product]):
        """Test retrieving products by status."""
        active_products = repository.get_by_status("ACTIVE")
        discontinued_products = repository.get_by_status("DISCONTINUED")
        
        assert len(active_products) >= 2  # From sample products
        assert len(discontinued_products) >= 1  # From sample products
        
        for product in active_products:
            assert product.status == "ACTIVE"
        
        for product in discontinued_products:
            assert product.status == "DISCONTINUED"

    def test_repository_session_management(self, repository: ProductRepository):
        """Test that repository properly manages database session."""
        # Repository should have a session
        assert repository.session is not None
        
        # Should be able to perform basic query
        try:
            count = repository.count()
            assert isinstance(count, int)
        except Exception as e:
            pytest.fail(f"Repository session management failed: {e}")

    def test_product_creation_with_minimal_data(self, repository: ProductRepository):
        """Test creating a product with only required fields."""
        minimal_data = {
            "sku": "MINIMAL-001",
            "name": "Minimal Product",
            "unit_price": Decimal("10.00"),
            "category": "proteins",
            "brand": "Test Brand"
            # status will default to ACTIVE
        }
        
        product = repository.create(**minimal_data)
        
        assert product.sku == "MINIMAL-001"
        assert product.name == "Minimal Product"
        assert product.status == "ACTIVE"  # Should default
        assert product.description is not None  # Should have some default or empty string

    def test_duplicate_sku_handling(self, repository: ProductRepository, sample_products: list[Product]):
        """Test handling of duplicate SKU creation."""
        existing_sku = sample_products[0].sku
        
        duplicate_data = {
            "sku": existing_sku,
            "name": "Duplicate SKU Product",
            "unit_price": Decimal("25.00"),
            "category": "proteins",
            "brand": "Test Brand"
        }
        
        # This should raise an exception or handle duplicate SKU gracefully
        with pytest.raises(Exception):  # Could be IntegrityError or custom exception
            repository.create(**duplicate_data)