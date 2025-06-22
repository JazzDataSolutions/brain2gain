"""
Unit tests for Product Repository layer.
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlmodel import Session

from app.repositories.product_repository import ProductRepository
from app.tests.fixtures.factories import (
    ProductFactory,
    create_product_with_stock,
)


class TestProductRepository:
    """Test cases for ProductRepository."""

    @pytest.fixture
    def repository(self, db: Session) -> ProductRepository:
        """Create a ProductRepository instance."""
        return ProductRepository(db)

    def test_create_product(self, repository: ProductRepository):
        """Test creating a new product."""
        product_data = {
            "sku": "TEST-001",
            "name": "Test Whey Protein",
            "description": "High quality whey protein",
            "unit_price": Decimal("45.99"),
            "category": "proteins",
            "brand": "Test Brand",
            "status": "ACTIVE"
        }

        product = repository.create(**product_data)

        assert product.sku == "TEST-001"
        assert product.name == "Test Whey Protein"
        assert product.unit_price == Decimal("45.99")
        assert product.category == "proteins"
        assert product.status == "ACTIVE"
        assert product.product_id is not None

    def test_get_product_by_id(self, repository: ProductRepository, db: Session):
        """Test retrieving a product by ID."""
        # Create test product
        product = ProductFactory()
        db.add(product)
        db.commit()

        # Retrieve product
        found_product = repository.get_by_id(product.product_id)

        assert found_product is not None
        assert found_product.product_id == product.product_id
        assert found_product.sku == product.sku
        assert found_product.name == product.name

    def test_get_product_by_id_not_found(self, repository: ProductRepository):
        """Test retrieving a non-existent product."""
        non_existent_id = uuid4()
        product = repository.get_by_id(non_existent_id)

        assert product is None

    def test_get_product_by_sku(self, repository: ProductRepository, db: Session):
        """Test retrieving a product by SKU."""
        # Create test product
        product = ProductFactory(sku="UNIQUE-SKU-001")
        db.add(product)
        db.commit()

        # Retrieve product by SKU
        found_product = repository.get_by_sku("UNIQUE-SKU-001")

        assert found_product is not None
        assert found_product.sku == "UNIQUE-SKU-001"
        assert found_product.product_id == product.product_id

    def test_get_product_by_sku_not_found(self, repository: ProductRepository):
        """Test retrieving a non-existent product by SKU."""
        product = repository.get_by_sku("NON-EXISTENT-SKU")

        assert product is None

    def test_get_products_by_category(self, repository: ProductRepository, db: Session):
        """Test retrieving products by category."""
        # Create test products
        protein1 = ProductFactory(category="proteins")
        protein2 = ProductFactory(category="proteins")
        creatine = ProductFactory(category="creatine")

        db.add_all([protein1, protein2, creatine])
        db.commit()

        # Get proteins
        proteins = repository.get_by_category("proteins")

        assert len(proteins) >= 2
        assert all(p.category == "proteins" for p in proteins)

        product_ids = [p.product_id for p in proteins]
        assert protein1.product_id in product_ids
        assert protein2.product_id in product_ids
        assert creatine.product_id not in product_ids

    def test_get_active_products(self, repository: ProductRepository, db: Session):
        """Test retrieving only active products."""
        # Create test products
        active1 = ProductFactory(status="ACTIVE")
        active2 = ProductFactory(status="ACTIVE")
        inactive = ProductFactory(status="INACTIVE")

        db.add_all([active1, active2, inactive])
        db.commit()

        # Get active products
        active_products = repository.get_active_products()

        assert len(active_products) >= 2
        assert all(p.status == "ACTIVE" for p in active_products)

        product_ids = [p.product_id for p in active_products]
        assert active1.product_id in product_ids
        assert active2.product_id in product_ids
        assert inactive.product_id not in product_ids

    def test_search_products_by_name(self, repository: ProductRepository, db: Session):
        """Test searching products by name."""
        # Create test products
        whey1 = ProductFactory(name="Gold Standard Whey Protein")
        whey2 = ProductFactory(name="Premium Whey Isolate")
        creatine = ProductFactory(name="Creatine Monohydrate")

        db.add_all([whey1, whey2, creatine])
        db.commit()

        # Search for whey products
        whey_products = repository.search_by_name("whey")

        assert len(whey_products) >= 2

        product_ids = [p.product_id for p in whey_products]
        assert whey1.product_id in product_ids
        assert whey2.product_id in product_ids
        assert creatine.product_id not in product_ids

    def test_update_product(self, repository: ProductRepository, db: Session):
        """Test updating a product."""
        # Create test product
        product = ProductFactory(name="Original Name", unit_price=Decimal("50.00"))
        db.add(product)
        db.commit()

        # Update product
        updated_product = repository.update(
            product.product_id,
            name="Updated Name",
            unit_price=Decimal("55.00")
        )

        assert updated_product.name == "Updated Name"
        assert updated_product.unit_price == Decimal("55.00")
        assert updated_product.product_id == product.product_id

    def test_update_product_not_found(self, repository: ProductRepository):
        """Test updating a non-existent product."""
        non_existent_id = uuid4()

        updated_product = repository.update(
            non_existent_id,
            name="Updated Name"
        )

        assert updated_product is None

    def test_delete_product(self, repository: ProductRepository, db: Session):
        """Test deleting a product."""
        # Create test product
        product = ProductFactory()
        db.add(product)
        db.commit()
        product_id = product.product_id

        # Delete product
        result = repository.delete(product_id)

        assert result is True

        # Verify product is deleted
        deleted_product = repository.get_by_id(product_id)
        assert deleted_product is None

    def test_delete_product_not_found(self, repository: ProductRepository):
        """Test deleting a non-existent product."""
        non_existent_id = uuid4()

        result = repository.delete(non_existent_id)

        assert result is False

    def test_get_products_with_pagination(self, repository: ProductRepository, db: Session):
        """Test retrieving products with pagination."""
        # Create multiple test products
        products = [ProductFactory() for _ in range(15)]
        db.add_all(products)
        db.commit()

        # Get first page
        page1 = repository.get_paginated(skip=0, limit=10)
        assert len(page1) == 10

        # Get second page
        page2 = repository.get_paginated(skip=10, limit=10)
        assert len(page2) >= 5  # At least 5 more products

        # Ensure no overlap
        page1_ids = {p.product_id for p in page1}
        page2_ids = {p.product_id for p in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_get_products_by_price_range(self, repository: ProductRepository, db: Session):
        """Test retrieving products by price range."""
        # Create test products with different prices
        cheap = ProductFactory(unit_price=Decimal("20.00"))
        medium = ProductFactory(unit_price=Decimal("50.00"))
        expensive = ProductFactory(unit_price=Decimal("100.00"))

        db.add_all([cheap, medium, expensive])
        db.commit()

        # Get products in price range 30-80
        products_in_range = repository.get_by_price_range(
            min_price=Decimal("30.00"),
            max_price=Decimal("80.00")
        )

        product_ids = [p.product_id for p in products_in_range]
        assert medium.product_id in product_ids
        assert cheap.product_id not in product_ids
        assert expensive.product_id not in product_ids

    def test_get_low_stock_products(self, repository: ProductRepository, db: Session):
        """Test retrieving products with low stock."""
        # Create products with stock
        low_stock_product, low_stock = create_product_with_stock(db, stock_quantity=5)
        normal_stock_product, normal_stock = create_product_with_stock(db, stock_quantity=100)

        # Set min stock levels
        low_stock.min_stock_level = 10
        normal_stock.min_stock_level = 10
        db.commit()

        # Get low stock products
        low_stock_products = repository.get_low_stock_products()

        product_ids = [p.product_id for p in low_stock_products]
        assert low_stock_product.product_id in product_ids
        assert normal_stock_product.product_id not in product_ids

    def test_bulk_update_status(self, repository: ProductRepository, db: Session):
        """Test bulk updating product status."""
        # Create test products
        products = [ProductFactory(status="ACTIVE") for _ in range(3)]
        db.add_all(products)
        db.commit()

        product_ids = [p.product_id for p in products]

        # Bulk update to inactive
        updated_count = repository.bulk_update_status(product_ids, "INACTIVE")

        assert updated_count == 3

        # Verify all products are inactive
        for product_id in product_ids:
            product = repository.get_by_id(product_id)
            assert product.status == "INACTIVE"

    def test_get_product_count_by_category(self, repository: ProductRepository, db: Session):
        """Test getting product count by category."""
        # Create test products
        proteins = [ProductFactory(category="proteins") for _ in range(3)]
        creatines = [ProductFactory(category="creatine") for _ in range(2)]

        db.add_all(proteins + creatines)
        db.commit()

        # Get count by category
        category_counts = repository.get_count_by_category()

        assert "proteins" in category_counts
        assert "creatine" in category_counts
        assert category_counts["proteins"] >= 3
        assert category_counts["creatine"] >= 2
