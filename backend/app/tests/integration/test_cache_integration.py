"""
Integration tests for Redis Cache functionality.
"""

import pytest
import asyncio
from decimal import Decimal
from uuid import uuid4
import json
from typing import Any

from app.core.cache import CacheService
from app.models import Product
from app.tests.fixtures.factories import ProductFactory


@pytest.mark.asyncio
class TestCacheIntegration:
    """Integration tests for CacheService with Redis."""
    
    @pytest.fixture
    def cache_service(self) -> CacheService:
        """Create a CacheService instance for testing."""
        return CacheService()
    
    @pytest.fixture
    async def clean_cache(self, cache_service: CacheService):
        """Clean cache before and after tests."""
        await cache_service.flush_all()
        yield
        await cache_service.flush_all()
    
    async def test_basic_set_get_operations(self, cache_service: CacheService, clean_cache):
        """Test basic cache set and get operations."""
        # Test string value
        await cache_service.set("test:string", "hello world", ttl=60)
        result = await cache_service.get("test:string")
        assert result == "hello world"
        
        # Test dict value
        test_dict = {"name": "Test Product", "price": 45.99}
        await cache_service.set("test:dict", test_dict, ttl=60)
        result = await cache_service.get("test:dict")
        assert result == test_dict
        
        # Test list value
        test_list = [1, 2, 3, "test"]
        await cache_service.set("test:list", test_list, ttl=60)
        result = await cache_service.get("test:list")
        assert result == test_list
    
    async def test_product_caching(self, cache_service: CacheService, clean_cache):
        """Test caching Product model objects."""
        # Create test product
        product = ProductFactory()
        product_dict = {
            "product_id": str(product.product_id),
            "sku": product.sku,
            "name": product.name,
            "description": product.description,
            "unit_price": str(product.unit_price),
            "category": product.category,
            "brand": product.brand,
            "status": product.status
        }
        
        # Cache the product
        cache_key = f"product:{product.product_id}"
        await cache_service.set(cache_key, product_dict, ttl=3600)
        
        # Retrieve from cache
        cached_product = await cache_service.get(cache_key)
        assert cached_product is not None
        assert cached_product["sku"] == product.sku
        assert cached_product["name"] == product.name
        assert Decimal(cached_product["unit_price"]) == product.unit_price
    
    async def test_cache_expiration(self, cache_service: CacheService, clean_cache):
        """Test cache TTL and expiration."""
        # Set with short TTL
        await cache_service.set("test:expire", "will expire", ttl=1)
        
        # Should exist immediately
        result = await cache_service.get("test:expire")
        assert result == "will expire"
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Should be expired
        result = await cache_service.get("test:expire")
        assert result is None
    
    async def test_cache_miss(self, cache_service: CacheService, clean_cache):
        """Test cache miss scenarios."""
        # Non-existent key
        result = await cache_service.get("non:existent:key")
        assert result is None
        
        # Expired key (already tested above)
        await cache_service.set("test:will_delete", "temp value", ttl=60)
        await cache_service.delete("test:will_delete")
        result = await cache_service.get("test:will_delete")
        assert result is None
    
    async def test_cache_delete(self, cache_service: CacheService, clean_cache):
        """Test cache deletion operations."""
        # Set multiple keys
        await cache_service.set("test:delete1", "value1", ttl=60)
        await cache_service.set("test:delete2", "value2", ttl=60)
        
        # Verify they exist
        assert await cache_service.get("test:delete1") == "value1"
        assert await cache_service.get("test:delete2") == "value2"
        
        # Delete one key
        await cache_service.delete("test:delete1")
        assert await cache_service.get("test:delete1") is None
        assert await cache_service.get("test:delete2") == "value2"
        
        # Delete the other
        await cache_service.delete("test:delete2")
        assert await cache_service.get("test:delete2") is None
    
    async def test_pattern_invalidation(self, cache_service: CacheService, clean_cache):
        """Test pattern-based cache invalidation."""
        # Set multiple keys with same pattern
        await cache_service.set("products:list:page1", ["product1", "product2"], ttl=60)
        await cache_service.set("products:list:page2", ["product3", "product4"], ttl=60)
        await cache_service.set("products:category:proteins", ["protein1"], ttl=60)
        await cache_service.set("other:data", "should remain", ttl=60)
        
        # Verify all exist
        assert await cache_service.get("products:list:page1") is not None
        assert await cache_service.get("products:list:page2") is not None
        assert await cache_service.get("products:category:proteins") is not None
        assert await cache_service.get("other:data") == "should remain"
        
        # Invalidate products pattern
        await cache_service.invalidate_pattern("products:*")
        
        # Products keys should be gone
        assert await cache_service.get("products:list:page1") is None
        assert await cache_service.get("products:list:page2") is None
        assert await cache_service.get("products:category:proteins") is None
        
        # Other data should remain
        assert await cache_service.get("other:data") == "should remain"
    
    async def test_concurrent_access(self, cache_service: CacheService, clean_cache):
        """Test concurrent cache access."""
        async def set_values(prefix: str, count: int):
            tasks = []
            for i in range(count):
                key = f"{prefix}:item:{i}"
                value = f"value_{prefix}_{i}"
                tasks.append(cache_service.set(key, value, ttl=60))
            await asyncio.gather(*tasks)
        
        async def get_values(prefix: str, count: int) -> list:
            tasks = []
            for i in range(count):
                key = f"{prefix}:item:{i}"
                tasks.append(cache_service.get(key))
            return await asyncio.gather(*tasks)
        
        # Set values concurrently from multiple "clients"
        await asyncio.gather(
            set_values("client1", 10),
            set_values("client2", 10),
            set_values("client3", 10)
        )
        
        # Get values concurrently
        results1, results2, results3 = await asyncio.gather(
            get_values("client1", 10),
            get_values("client2", 10),
            get_values("client3", 10)
        )
        
        # Verify all values are correct
        assert all(r == f"value_client1_{i}" for i, r in enumerate(results1))
        assert all(r == f"value_client2_{i}" for i, r in enumerate(results2))
        assert all(r == f"value_client3_{i}" for i, r in enumerate(results3))
    
    async def test_large_data_caching(self, cache_service: CacheService, clean_cache):
        """Test caching large datasets."""
        # Create large product list
        large_product_list = []
        for i in range(1000):
            product_data = {
                "product_id": str(uuid4()),
                "sku": f"LARGE-{i:04d}",
                "name": f"Large Dataset Product {i}",
                "description": f"Description for product {i} " * 10,  # Make it larger
                "unit_price": str(Decimal("45.99")),
                "category": "proteins",
                "brand": "Test Brand",
                "status": "ACTIVE"
            }
            large_product_list.append(product_data)
        
        # Cache large dataset
        await cache_service.set("products:large_list", large_product_list, ttl=300)
        
        # Retrieve and verify
        cached_list = await cache_service.get("products:large_list")
        assert cached_list is not None
        assert len(cached_list) == 1000
        assert cached_list[0]["sku"] == "LARGE-0000"
        assert cached_list[999]["sku"] == "LARGE-0999"
    
    async def test_cache_hit_rate_monitoring(self, cache_service: CacheService, clean_cache):
        """Test cache hit rate monitoring."""
        # Set some test data
        await cache_service.set("hit_rate:item1", "value1", ttl=60)
        await cache_service.set("hit_rate:item2", "value2", ttl=60)
        await cache_service.set("hit_rate:item3", "value3", ttl=60)
        
        # Simulate hits and misses
        await cache_service.get("hit_rate:item1")  # Hit
        await cache_service.get("hit_rate:item1")  # Hit
        await cache_service.get("hit_rate:item2")  # Hit
        await cache_service.get("hit_rate:missing1")  # Miss
        await cache_service.get("hit_rate:missing2")  # Miss
        
        # Get cache stats (if available)
        stats = await cache_service.get_stats()
        if stats:
            assert "hits" in stats or "get_hits" in stats
            assert "misses" in stats or "get_misses" in stats
    
    async def test_cache_serialization_edge_cases(self, cache_service: CacheService, clean_cache):
        """Test cache serialization with edge cases."""
        # Test None values
        await cache_service.set("test:none", None, ttl=60)
        result = await cache_service.get("test:none")
        assert result is None
        
        # Test empty structures
        await cache_service.set("test:empty_list", [], ttl=60)
        result = await cache_service.get("test:empty_list")
        assert result == []
        
        await cache_service.set("test:empty_dict", {}, ttl=60)
        result = await cache_service.get("test:empty_dict")
        assert result == {}
        
        # Test nested structures
        nested_data = {
            "level1": {
                "level2": {
                    "level3": ["item1", "item2", {"nested": True}]
                }
            },
            "numbers": [1, 2, 3.14, Decimal("10.99")]
        }
        
        # Convert Decimal to string for JSON serialization
        serializable_data = json.loads(json.dumps(nested_data, default=str))
        await cache_service.set("test:nested", serializable_data, ttl=60)
        result = await cache_service.get("test:nested")
        assert result["level1"]["level2"]["level3"][2]["nested"] is True
    
    async def test_cache_performance_benchmarks(self, cache_service: CacheService, clean_cache):
        """Test cache performance with benchmarks."""
        import time
        
        # Benchmark SET operations
        start_time = time.time()
        set_tasks = []
        for i in range(100):
            key = f"perf:set:{i}"
            value = f"performance_test_value_{i}"
            set_tasks.append(cache_service.set(key, value, ttl=60))
        
        await asyncio.gather(*set_tasks)
        set_duration = time.time() - start_time
        
        # Benchmark GET operations
        start_time = time.time()
        get_tasks = []
        for i in range(100):
            key = f"perf:set:{i}"
            get_tasks.append(cache_service.get(key))
        
        results = await asyncio.gather(*get_tasks)
        get_duration = time.time() - start_time
        
        # Verify all operations completed successfully
        assert len(results) == 100
        assert all(r is not None for r in results)
        
        # Performance assertions (these may need adjustment based on hardware)
        assert set_duration < 2.0, f"SET operations took too long: {set_duration}s"
        assert get_duration < 1.0, f"GET operations took too long: {get_duration}s"
        
        print(f"Performance: SET {set_duration:.3f}s, GET {get_duration:.3f}s")
    
    async def test_cache_connection_resilience(self, cache_service: CacheService, clean_cache):
        """Test cache behavior under connection issues."""
        # This test would need a way to simulate Redis connection issues
        # For now, we'll test the graceful degradation behavior
        
        # Set a value normally
        await cache_service.set("resilience:test", "normal_value", ttl=60)
        result = await cache_service.get("resilience:test")
        assert result == "normal_value"
        
        # Test behavior when Redis is temporarily unavailable
        # (This would need integration with test containers or mock failures)
        
        # For now, just test that the cache service handles errors gracefully
        try:
            # Attempt operation that might fail
            await cache_service.get("potentially:failing:key")
        except Exception as e:
            # Should handle gracefully, not crash the application
            pytest.fail(f"Cache service should handle errors gracefully: {e}")
    
    async def test_multi_tenant_cache_isolation(self, cache_service: CacheService, clean_cache):
        """Test cache isolation between different tenants/contexts."""
        # Simulate multi-tenant scenario with prefixed keys
        tenant1_prefix = "tenant1"
        tenant2_prefix = "tenant2"
        
        # Set data for different tenants
        await cache_service.set(f"{tenant1_prefix}:products:list", ["tenant1_product1"], ttl=60)
        await cache_service.set(f"{tenant2_prefix}:products:list", ["tenant2_product1"], ttl=60)
        
        # Verify isolation
        tenant1_data = await cache_service.get(f"{tenant1_prefix}:products:list")
        tenant2_data = await cache_service.get(f"{tenant2_prefix}:products:list")
        
        assert tenant1_data == ["tenant1_product1"]
        assert tenant2_data == ["tenant2_product1"]
        
        # Invalidate one tenant's cache
        await cache_service.invalidate_pattern(f"{tenant1_prefix}:*")
        
        # Verify only tenant1's data is gone
        assert await cache_service.get(f"{tenant1_prefix}:products:list") is None
        assert await cache_service.get(f"{tenant2_prefix}:products:list") == ["tenant2_product1"]