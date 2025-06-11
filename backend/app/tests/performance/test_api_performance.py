"""
Performance tests for API endpoints.
"""

import pytest
import asyncio
import time
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlmodel import Session
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.tests.fixtures.factories import ProductFactory, create_product_with_stock


@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    @pytest.fixture
    def performance_client(self, client: TestClient) -> TestClient:
        """Client configured for performance testing."""
        return client
    
    @pytest.fixture
    def large_dataset(self, db: Session) -> list:
        """Create a large dataset for performance testing."""
        products = []
        for i in range(100):
            product, _ = create_product_with_stock(db, stock_quantity=100)
            products.append(product)
        return products
    
    def test_product_list_endpoint_performance(self, performance_client: TestClient, superuser_token_headers: dict, large_dataset):
        """Test performance of product list endpoint."""
        # Warm up
        response = performance_client.get("/api/v1/products/", headers=superuser_token_headers)
        assert response.status_code == 200
        
        # Performance test
        times = []
        for _ in range(10):
            start_time = time.time()
            response = performance_client.get("/api/v1/products/", headers=superuser_token_headers)
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        # Performance assertions
        avg_time = statistics.mean(times)
        max_time = max(times)
        min_time = min(times)
        
        # API should respond within acceptable limits
        assert avg_time < 0.5, f"Average response time too high: {avg_time:.3f}s"
        assert max_time < 1.0, f"Max response time too high: {max_time:.3f}s"
        
        print(f"Product List Performance - Avg: {avg_time:.3f}s, Min: {min_time:.3f}s, Max: {max_time:.3f}s")
    
    def test_product_search_performance(self, performance_client: TestClient, superuser_token_headers: dict, large_dataset):
        """Test performance of product search endpoint."""
        search_terms = ["protein", "whey", "creatine", "vitamin", "amino"]
        
        times = []
        for term in search_terms:
            start_time = time.time()
            response = performance_client.get(
                f"/api/v1/products/search?q={term}",
                headers=superuser_token_headers
            )
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        # Search should be fast
        assert avg_time < 0.3, f"Average search time too high: {avg_time:.3f}s"
        assert max_time < 0.5, f"Max search time too high: {max_time:.3f}s"
        
        print(f"Product Search Performance - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    def test_single_product_retrieval_performance(self, performance_client: TestClient, superuser_token_headers: dict, large_dataset):
        """Test performance of single product retrieval."""
        # Test with multiple products
        test_products = large_dataset[:10]
        times = []
        
        for product in test_products:
            start_time = time.time()
            response = performance_client.get(
                f"/api/v1/products/{product.product_id}",
                headers=superuser_token_headers
            )
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        # Single product retrieval should be very fast
        assert avg_time < 0.2, f"Average single product retrieval too slow: {avg_time:.3f}s"
        assert max_time < 0.3, f"Max single product retrieval too slow: {max_time:.3f}s"
        
        print(f"Single Product Performance - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    def test_concurrent_api_requests_performance(self, performance_client: TestClient, superuser_token_headers: dict, large_dataset):
        """Test API performance under concurrent load."""
        
        def make_request(endpoint: str) -> float:
            """Make a single API request and return response time."""
            start_time = time.time()
            response = performance_client.get(endpoint, headers=superuser_token_headers)
            end_time = time.time()
            
            assert response.status_code == 200
            return end_time - start_time
        
        # Prepare different endpoints to test
        endpoints = [
            "/api/v1/products/",
            "/api/v1/products/?category=proteins",
            "/api/v1/products/?status=ACTIVE",
            "/api/v1/products/search?q=protein",
        ]
        
        # Add specific product endpoints
        for product in large_dataset[:5]:
            endpoints.append(f"/api/v1/products/{product.product_id}")
        
        # Test concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit multiple requests concurrently
            futures = []
            for _ in range(50):  # 50 concurrent requests
                endpoint = endpoints[len(futures) % len(endpoints)]
                future = executor.submit(make_request, endpoint)
                futures.append(future)
            
            # Collect results
            times = []
            for future in as_completed(futures):
                response_time = future.result()
                times.append(response_time)
        
        # Analyze concurrent performance
        avg_time = statistics.mean(times)
        max_time = max(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
        
        # Performance assertions for concurrent load
        assert avg_time < 0.8, f"Average concurrent response time too high: {avg_time:.3f}s"
        assert max_time < 2.0, f"Max concurrent response time too high: {max_time:.3f}s"
        assert p95_time < 1.0, f"95th percentile response time too high: {p95_time:.3f}s"
        
        print(f"Concurrent Performance - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s, P95: {p95_time:.3f}s")
    
    def test_pagination_performance(self, performance_client: TestClient, superuser_token_headers: dict, large_dataset):
        """Test performance of paginated endpoints."""
        page_sizes = [10, 25, 50, 100]
        
        for page_size in page_sizes:
            times = []
            
            # Test first few pages
            for page in range(3):
                start_time = time.time()
                response = performance_client.get(
                    f"/api/v1/products/?skip={page * page_size}&limit={page_size}",
                    headers=superuser_token_headers
                )
                end_time = time.time()
                
                assert response.status_code == 200
                data = response.json()
                assert len(data.get("data", [])) <= page_size
                
                times.append(end_time - start_time)
            
            avg_time = statistics.mean(times)
            max_time = max(times)
            
            # Pagination should scale reasonably
            assert avg_time < 0.5, f"Page size {page_size} too slow: {avg_time:.3f}s"
            assert max_time < 0.8, f"Page size {page_size} max time too high: {max_time:.3f}s"
            
            print(f"Pagination Performance (size {page_size}) - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    def test_filtering_performance(self, performance_client: TestClient, superuser_token_headers: dict, large_dataset):
        """Test performance of filtered queries."""
        filters = [
            {"category": "proteins"},
            {"status": "ACTIVE"},
            {"category": "proteins", "status": "ACTIVE"},
            {"min_price": "20", "max_price": "100"},
            {"brand": "Optimum Nutrition"},
        ]
        
        for filter_params in filters:
            times = []
            
            for _ in range(5):
                query_string = "&".join([f"{k}={v}" for k, v in filter_params.items()])
                
                start_time = time.time()
                response = performance_client.get(
                    f"/api/v1/products/?{query_string}",
                    headers=superuser_token_headers
                )
                end_time = time.time()
                
                assert response.status_code == 200
                times.append(end_time - start_time)
            
            avg_time = statistics.mean(times)
            max_time = max(times)
            
            # Filtered queries should be optimized
            assert avg_time < 0.4, f"Filter {filter_params} too slow: {avg_time:.3f}s"
            assert max_time < 0.6, f"Filter {filter_params} max time too high: {max_time:.3f}s"
            
            print(f"Filter Performance {filter_params} - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    def test_cache_performance_impact(self, performance_client: TestClient, superuser_token_headers: dict, large_dataset):
        """Test performance impact of caching."""
        endpoint = "/api/v1/products/"
        
        # First request (cache miss)
        cache_miss_times = []
        for _ in range(3):
            start_time = time.time()
            response = performance_client.get(endpoint, headers=superuser_token_headers)
            end_time = time.time()
            
            assert response.status_code == 200
            cache_miss_times.append(end_time - start_time)
        
        # Subsequent requests (cache hit)
        cache_hit_times = []
        for _ in range(10):
            start_time = time.time()
            response = performance_client.get(endpoint, headers=superuser_token_headers)
            end_time = time.time()
            
            assert response.status_code == 200
            cache_hit_times.append(end_time - start_time)
        
        avg_cache_miss = statistics.mean(cache_miss_times)
        avg_cache_hit = statistics.mean(cache_hit_times)
        
        # Cache should provide significant performance improvement
        improvement_ratio = avg_cache_miss / avg_cache_hit
        assert improvement_ratio > 1.5, f"Cache improvement insufficient: {improvement_ratio:.2f}x"
        
        print(f"Cache Performance - Miss: {avg_cache_miss:.3f}s, Hit: {avg_cache_hit:.3f}s, Improvement: {improvement_ratio:.2f}x")
    
    @pytest.mark.benchmark
    def test_database_query_performance(self, performance_client: TestClient, superuser_token_headers: dict, large_dataset, benchmark):
        """Benchmark database query performance."""
        
        def query_products():
            response = performance_client.get("/api/v1/products/", headers=superuser_token_headers)
            assert response.status_code == 200
            return response.json()
        
        # Benchmark the function
        result = benchmark(query_products)
        
        # Verify we got data
        assert "data" in result
        assert len(result["data"]) > 0
        
        print(f"Database Query Benchmark - Mean: {benchmark.stats.mean:.3f}s")
    
    def test_memory_usage_during_large_requests(self, performance_client: TestClient, superuser_token_headers: dict, large_dataset):
        """Test memory usage during large data requests."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make large request
        response = performance_client.get(
            "/api/v1/products/?limit=1000",
            headers=superuser_token_headers
        )
        assert response.status_code == 200
        
        # Check memory after request
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - baseline_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 100, f"Memory increase too high: {memory_increase:.2f}MB"
        
        print(f"Memory Usage - Baseline: {baseline_memory:.2f}MB, Peak: {peak_memory:.2f}MB, Increase: {memory_increase:.2f}MB")
    
    def test_response_size_optimization(self, performance_client: TestClient, superuser_token_headers: dict, large_dataset):
        """Test response size optimization."""
        response = performance_client.get("/api/v1/products/?limit=50", headers=superuser_token_headers)
        assert response.status_code == 200
        
        # Check response size
        response_size = len(response.content)
        response_size_kb = response_size / 1024
        
        # Response should be reasonably sized
        assert response_size_kb < 500, f"Response too large: {response_size_kb:.2f}KB"
        
        # Check if compression headers are present
        content_encoding = response.headers.get("content-encoding")
        if content_encoding:
            print(f"Response compressed with: {content_encoding}")
        
        print(f"Response Size - {response_size_kb:.2f}KB for 50 products")
    
    def test_connection_pool_performance(self, performance_client: TestClient, superuser_token_headers: dict):
        """Test database connection pool performance."""
        
        def make_db_request():
            response = performance_client.get("/api/v1/products/?limit=10", headers=superuser_token_headers)
            assert response.status_code == 200
            return response
        
        # Test rapid consecutive requests
        times = []
        for _ in range(20):
            start_time = time.time()
            make_db_request()
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        variance = statistics.variance(times)
        
        # Connection pooling should provide consistent performance
        assert avg_time < 0.3, f"Average connection time too high: {avg_time:.3f}s"
        assert variance < 0.01, f"Performance variance too high: {variance:.6f}"
        
        print(f"Connection Pool Performance - Avg: {avg_time:.3f}s, Variance: {variance:.6f}")


@pytest.mark.load_test
class TestLoadTesting:
    """Load testing scenarios."""
    
    def test_sustained_load_simulation(self, performance_client: TestClient, superuser_token_headers: dict):
        """Simulate sustained load over time."""
        duration_seconds = 30
        requests_per_second = 5
        
        start_time = time.time()
        request_times = []
        request_count = 0
        
        while time.time() - start_time < duration_seconds:
            interval_start = time.time()
            
            # Make requests for this second
            for _ in range(requests_per_second):
                request_start = time.time()
                response = performance_client.get("/api/v1/products/?limit=10", headers=superuser_token_headers)
                request_end = time.time()
                
                assert response.status_code == 200
                request_times.append(request_end - request_start)
                request_count += 1
            
            # Wait for the remainder of the second
            interval_duration = time.time() - interval_start
            if interval_duration < 1.0:
                time.sleep(1.0 - interval_duration)
        
        # Analyze sustained load performance
        avg_response_time = statistics.mean(request_times)
        max_response_time = max(request_times)
        
        assert avg_response_time < 0.5, f"Sustained load avg response time too high: {avg_response_time:.3f}s"
        assert max_response_time < 1.0, f"Sustained load max response time too high: {max_response_time:.3f}s"
        
        print(f"Sustained Load Test - {request_count} requests, Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s")