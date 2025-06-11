"""
Unit tests for Product Service layer.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import uuid4

from app.services.product_service import ProductService
from app.repositories.product_repository import ProductRepository
from app.models import Product
from app.tests.fixtures.factories import ProductFactory
from app.core.cache import CacheService


class TestProductService:
    """Test cases for ProductService."""
    
    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create a mock ProductRepository."""
        return Mock(spec=ProductRepository)
    
    @pytest.fixture
    def mock_cache(self) -> Mock:
        """Create a mock CacheService."""
        return Mock(spec=CacheService)
    
    @pytest.fixture
    def service(self, mock_repository: Mock, mock_cache: Mock) -> ProductService:
        """Create a ProductService instance with mocked dependencies."""
        return ProductService(repository=mock_repository, cache=mock_cache)
    
    def test_get_product_by_id_from_cache(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test getting product by ID from cache."""
        # Setup
        product_id = uuid4()
        cached_product = ProductFactory(product_id=product_id)
        mock_cache.get.return_value = cached_product
        
        # Execute
        result = service.get_product_by_id(product_id)
        
        # Assert
        assert result == cached_product
        mock_cache.get.assert_called_once_with(f"product:{product_id}")
        mock_repository.get_by_id.assert_not_called()
    
    def test_get_product_by_id_from_db_cache_miss(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test getting product by ID from database when cache misses."""
        # Setup
        product_id = uuid4()
        db_product = ProductFactory(product_id=product_id)
        mock_cache.get.return_value = None  # Cache miss
        mock_repository.get_by_id.return_value = db_product
        
        # Execute
        result = service.get_product_by_id(product_id)
        
        # Assert
        assert result == db_product
        mock_cache.get.assert_called_once_with(f"product:{product_id}")
        mock_repository.get_by_id.assert_called_once_with(product_id)
        mock_cache.set.assert_called_once_with(f"product:{product_id}", db_product, ttl=3600)
    
    def test_get_product_by_id_not_found(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test getting non-existent product by ID."""
        # Setup
        product_id = uuid4()
        mock_cache.get.return_value = None
        mock_repository.get_by_id.return_value = None
        
        # Execute
        result = service.get_product_by_id(product_id)
        
        # Assert
        assert result is None
        mock_cache.set.assert_not_called()
    
    def test_create_product_success(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test creating a new product successfully."""
        # Setup
        product_data = {
            "sku": "NEW-001",
            "name": "New Product",
            "unit_price": Decimal("45.99"),
            "category": "proteins"
        }
        created_product = ProductFactory(**product_data)
        mock_repository.get_by_sku.return_value = None  # SKU doesn't exist
        mock_repository.create.return_value = created_product
        
        # Execute
        result = service.create_product(**product_data)
        
        # Assert
        assert result == created_product
        mock_repository.get_by_sku.assert_called_once_with("NEW-001")
        mock_repository.create.assert_called_once_with(**product_data)
        mock_cache.invalidate_pattern.assert_called_once_with("products:*")
    
    def test_create_product_duplicate_sku(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test creating product with duplicate SKU."""
        # Setup
        product_data = {
            "sku": "EXISTING-001",
            "name": "Duplicate SKU Product",
            "unit_price": Decimal("45.99")
        }
        existing_product = ProductFactory(sku="EXISTING-001")
        mock_repository.get_by_sku.return_value = existing_product
        
        # Execute & Assert
        with pytest.raises(ValueError, match="Product with SKU.*already exists"):
            service.create_product(**product_data)
        
        mock_repository.create.assert_not_called()
        mock_cache.invalidate_pattern.assert_not_called()
    
    def test_update_product_success(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test updating product successfully."""
        # Setup
        product_id = uuid4()
        update_data = {"name": "Updated Name", "unit_price": Decimal("55.99")}
        updated_product = ProductFactory(product_id=product_id, **update_data)
        mock_repository.update.return_value = updated_product
        
        # Execute
        result = service.update_product(product_id, **update_data)
        
        # Assert
        assert result == updated_product
        mock_repository.update.assert_called_once_with(product_id, **update_data)
        mock_cache.delete.assert_called_once_with(f"product:{product_id}")
        mock_cache.invalidate_pattern.assert_called_once_with("products:*")
    
    def test_update_product_not_found(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test updating non-existent product."""
        # Setup
        product_id = uuid4()
        mock_repository.update.return_value = None
        
        # Execute
        result = service.update_product(product_id, name="Updated Name")
        
        # Assert
        assert result is None
        mock_cache.delete.assert_not_called()
        mock_cache.invalidate_pattern.assert_not_called()
    
    def test_delete_product_success(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test deleting product successfully."""
        # Setup
        product_id = uuid4()
        mock_repository.delete.return_value = True
        
        # Execute
        result = service.delete_product(product_id)
        
        # Assert
        assert result is True
        mock_repository.delete.assert_called_once_with(product_id)
        mock_cache.delete.assert_called_once_with(f"product:{product_id}")
        mock_cache.invalidate_pattern.assert_called_once_with("products:*")
    
    def test_delete_product_not_found(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test deleting non-existent product."""
        # Setup
        product_id = uuid4()
        mock_repository.delete.return_value = False
        
        # Execute
        result = service.delete_product(product_id)
        
        # Assert
        assert result is False
        mock_cache.delete.assert_not_called()
        mock_cache.invalidate_pattern.assert_not_called()
    
    def test_get_products_by_category_cached(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test getting products by category from cache."""
        # Setup
        category = "proteins"
        cached_products = [ProductFactory(category=category) for _ in range(3)]
        mock_cache.get.return_value = cached_products
        
        # Execute
        result = service.get_products_by_category(category)
        
        # Assert
        assert result == cached_products
        mock_cache.get.assert_called_once_with(f"products:category:{category}")
        mock_repository.get_by_category.assert_not_called()
    
    def test_get_products_by_category_cache_miss(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test getting products by category when cache misses."""
        # Setup
        category = "proteins"
        db_products = [ProductFactory(category=category) for _ in range(3)]
        mock_cache.get.return_value = None
        mock_repository.get_by_category.return_value = db_products
        
        # Execute
        result = service.get_products_by_category(category)
        
        # Assert
        assert result == db_products
        mock_cache.get.assert_called_once_with(f"products:category:{category}")
        mock_repository.get_by_category.assert_called_once_with(category)
        mock_cache.set.assert_called_once_with(f"products:category:{category}", db_products, ttl=1800)
    
    def test_search_products_with_filters(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test searching products with multiple filters."""
        # Setup
        filters = {
            "category": "proteins",
            "min_price": Decimal("20.00"),
            "max_price": Decimal("80.00"),
            "status": "ACTIVE"
        }
        search_results = [ProductFactory(**filters) for _ in range(2)]
        
        with patch.object(service, '_apply_search_filters', return_value=search_results) as mock_filter:
            # Execute
            result = service.search_products(**filters)
            
            # Assert
            assert result == search_results
            mock_filter.assert_called_once_with(**filters)
    
    def test_get_featured_products_cached(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test getting featured products from cache."""
        # Setup
        featured_products = [ProductFactory() for _ in range(5)]
        mock_cache.get.return_value = featured_products
        
        # Execute
        result = service.get_featured_products(limit=5)
        
        # Assert
        assert result == featured_products
        mock_cache.get.assert_called_once_with("products:featured:5")
        mock_repository.get_featured.assert_not_called()
    
    def test_get_low_stock_products(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test getting low stock products."""
        # Setup
        low_stock_products = [ProductFactory() for _ in range(3)]
        mock_repository.get_low_stock_products.return_value = low_stock_products
        
        # Execute
        result = service.get_low_stock_products()
        
        # Assert
        assert result == low_stock_products
        mock_repository.get_low_stock_products.assert_called_once()
        # Low stock should not be cached (real-time data)
        mock_cache.get.assert_not_called()
        mock_cache.set.assert_not_called()
    
    def test_bulk_update_status(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test bulk updating product status."""
        # Setup
        product_ids = [uuid4() for _ in range(3)]
        new_status = "INACTIVE"
        mock_repository.bulk_update_status.return_value = 3
        
        # Execute
        result = service.bulk_update_status(product_ids, new_status)
        
        # Assert
        assert result == 3
        mock_repository.bulk_update_status.assert_called_once_with(product_ids, new_status)
        
        # Should invalidate individual product caches
        for product_id in product_ids:
            mock_cache.delete.assert_any_call(f"product:{product_id}")
        
        # Should invalidate list caches
        mock_cache.invalidate_pattern.assert_called_once_with("products:*")
    
    def test_get_product_analytics(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test getting product analytics."""
        # Setup
        analytics_data = {
            "total_products": 150,
            "active_products": 120,
            "categories": {"proteins": 50, "creatine": 30, "vitamins": 40},
            "low_stock_count": 5
        }
        
        mock_repository.get_total_count.return_value = 150
        mock_repository.get_count_by_status.return_value = {"ACTIVE": 120, "INACTIVE": 30}
        mock_repository.get_count_by_category.return_value = {"proteins": 50, "creatine": 30, "vitamins": 40}
        mock_repository.get_low_stock_count.return_value = 5
        
        # Execute
        result = service.get_product_analytics()
        
        # Assert
        assert result["total_products"] == 150
        assert result["active_products"] == 120
        assert result["categories"] == {"proteins": 50, "creatine": 30, "vitamins": 40}
        assert result["low_stock_count"] == 5
    
    @pytest.mark.asyncio
    async def test_async_bulk_import_products(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test asynchronous bulk import of products."""
        # Setup
        product_data_list = [
            {"sku": f"BULK-{i:03d}", "name": f"Bulk Product {i}", "unit_price": Decimal("30.00")}
            for i in range(1, 4)
        ]
        
        # Mock that no SKUs exist
        mock_repository.get_by_sku.return_value = None
        mock_repository.create.side_effect = [
            ProductFactory(**data) for data in product_data_list
        ]
        
        # Execute
        result = await service.async_bulk_import_products(product_data_list)
        
        # Assert
        assert len(result["created"]) == 3
        assert len(result["skipped"]) == 0
        assert len(result["errors"]) == 0
        
        # Should create all products
        assert mock_repository.create.call_count == 3
        
        # Should invalidate caches once at the end
        mock_cache.invalidate_pattern.assert_called_once_with("products:*")
    
    def test_validate_product_data_valid(self, service: ProductService):
        """Test validating valid product data."""
        product_data = {
            "sku": "VALID-001",
            "name": "Valid Product",
            "unit_price": Decimal("45.99"),
            "category": "proteins",
            "status": "ACTIVE"
        }
        
        # Should not raise any exception
        service._validate_product_data(product_data)
    
    def test_validate_product_data_invalid_price(self, service: ProductService):
        """Test validating product data with invalid price."""
        product_data = {
            "sku": "INVALID-001",
            "name": "Invalid Product",
            "unit_price": Decimal("-10.00"),  # Negative price
            "category": "proteins"
        }
        
        with pytest.raises(ValueError, match="Unit price must be positive"):
            service._validate_product_data(product_data)
    
    def test_validate_product_data_invalid_sku(self, service: ProductService):
        """Test validating product data with invalid SKU."""
        product_data = {
            "sku": "",  # Empty SKU
            "name": "Invalid Product",
            "unit_price": Decimal("45.99"),
            "category": "proteins"
        }
        
        with pytest.raises(ValueError, match="SKU cannot be empty"):
            service._validate_product_data(product_data)
    
    def test_cache_warming(self, service: ProductService, mock_repository: Mock, mock_cache: Mock):
        """Test cache warming functionality."""
        # Setup
        popular_products = [ProductFactory() for _ in range(10)]
        categories = ["proteins", "creatine", "vitamins"]
        
        mock_repository.get_popular_products.return_value = popular_products
        mock_repository.get_categories.return_value = categories
        mock_repository.get_by_category.side_effect = [
            [ProductFactory(category=cat) for _ in range(5)] for cat in categories
        ]
        
        # Execute
        service.warm_cache()
        
        # Assert
        mock_cache.set.assert_any_call("products:popular:10", popular_products, ttl=3600)
        for category in categories:
            mock_cache.set.assert_any_call(
                f"products:category:{category}",
                mock_repository.get_by_category.return_value,
                ttl=1800
            )