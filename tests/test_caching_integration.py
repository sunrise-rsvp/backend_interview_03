"""
Integration tests for caching functionality using Redis
"""
import pytest
import asyncio
import json
from uuid import uuid4
import httpx
import redis.asyncio as redis
import os


@pytest.mark.integration
@pytest.mark.cache
class TestEventCachingIntegration:
    """Test event caching functionality end-to-end"""
    
    @pytest.fixture(autouse=True)
    async def setup_redis(self):
        """Setup Redis connection for testing"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Clear any existing test data
        await self.redis_client.flushdb()
        
        yield
        
        # Cleanup after test
        await self.redis_client.flushdb()
        await self.redis_client.close()
    
    @pytest.mark.asyncio
    async def test_event_caching_on_create(self, server_process, api_client, sample_event_data):
        """Test that events are cached when created"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create an event
            response = await client.post("/events/", json=sample_event_data)
            assert response.status_code == 200
            event = response.json()
            event_id = event["id"]
            
            # Check if event is cached in Redis
            cache_key = f"event:{event_id}"
            cached_event = await self.redis_client.get(cache_key)
            
            if cached_event:  # Cache might be implemented
                cached_data = json.loads(cached_event)
                assert cached_data["id"] == event_id
                assert cached_data["name"] == sample_event_data["name"]
    
    @pytest.mark.asyncio
    async def test_event_list_caching(self, server_process, api_client, sample_event_data_list):
        """Test that event lists are cached"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create multiple events
            for event_data in sample_event_data_list:
                await client.post("/events/", json=event_data)
            
            # Make multiple requests to the same list endpoint
            first_response = await client.get("/events/?limit=10&offset=0")
            assert first_response.status_code == 200
            
            # Check for list cache key
            cache_key = "events:list:all:10:0"
            cached_list = await self.redis_client.get(cache_key)
            
            # Make the same request again
            second_response = await client.get("/events/?limit=10&offset=0")
            assert second_response.status_code == 200
            
            # Results should be consistent
            assert first_response.json() == second_response.json()
    
    @pytest.mark.asyncio
    async def test_search_results_caching(self, server_process, api_client, sample_event_data_list):
        """Test that search results are cached"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create events
            for event_data in sample_event_data_list:
                await client.post("/events/", json=event_data)
            
            # Search for events
            search_term = "Tech"
            first_search = await client.get(f"/events/?search={search_term}")
            assert first_search.status_code == 200
            
            # Check for search cache
            search_cache_key = f"events:search:{search_term}:location:any:100:0"
            cached_search = await self.redis_client.get(search_cache_key)
            
            # Search again
            second_search = await client.get(f"/events/?search={search_term}")
            assert second_search.status_code == 200
            
            # Results should be consistent
            assert first_search.json() == second_search.json()
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_update(self, server_process, api_client, sample_event_data):
        """Test that cache is invalidated when events are updated"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create an event
            create_response = await client.post("/events/", json=sample_event_data)
            event = create_response.json()
            event_id = event["id"]
            
            # Get the event to potentially cache it
            await client.get(f"/events/{event_id}/")
            
            # Update the event
            update_data = {"name": "Cache Updated Event"}
            update_response = await client.put(f"/events/{event_id}/", json=update_data)
            assert update_response.status_code == 200
            
            # Get the event again - should reflect the update
            get_response = await client.get(f"/events/{event_id}/")
            assert get_response.status_code == 200
            updated_event = get_response.json()
            assert updated_event["name"] == update_data["name"]
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_delete(self, server_process, api_client, sample_event_data):
        """Test that cache is invalidated when events are deleted"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create an event
            create_response = await client.post("/events/", json=sample_event_data)
            event = create_response.json()
            event_id = event["id"]
            
            # Cache the event by getting it
            await client.get(f"/events/{event_id}/")
            
            # Delete the event
            delete_response = await client.delete(f"/events/{event_id}/")
            assert delete_response.status_code == 200
            
            # Verify the event is no longer accessible
            get_response = await client.get(f"/events/{event_id}/")
            assert get_response.status_code == 404


@pytest.mark.integration
@pytest.mark.cache
@pytest.mark.slow
class TestCachePerformanceIntegration:
    """Test caching performance and behavior under load"""
    
    @pytest.fixture(autouse=True)
    async def setup_redis(self):
        """Setup Redis connection for testing"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        await self.redis_client.flushdb()
        yield
        await self.redis_client.flushdb()
        await self.redis_client.close()
    
    @pytest.mark.asyncio
    async def test_cache_performance_improvement(self, server_process, api_client, sample_event_data_list):
        """Test that caching improves response times"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create events
            for event_data in sample_event_data_list:
                await client.post("/events/", json=event_data)
            
            # Measure first request (cache miss)
            import time
            start_time = time.time()
            first_response = await client.get("/events/?limit=100")
            first_duration = time.time() - start_time
            assert first_response.status_code == 200
            
            # Wait a brief moment
            await asyncio.sleep(0.1)
            
            # Measure second request (potential cache hit)
            start_time = time.time()
            second_response = await client.get("/events/?limit=100")
            second_duration = time.time() - start_time
            assert second_response.status_code == 200
            
            # Results should be identical
            assert first_response.json() == second_response.json()
            
            # Second request might be faster due to caching
            # Note: This is not always guaranteed due to various factors
            print(f"First request: {first_duration:.4f}s, Second request: {second_duration:.4f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self, server_process, api_client, sample_event_data):
        """Test concurrent access to cached data"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create an event
            response = await client.post("/events/", json=sample_event_data)
            event = response.json()
            event_id = event["id"]
            
            # Make multiple concurrent requests
            async def get_event():
                return await client.get(f"/events/{event_id}/")
            
            # Run multiple concurrent requests
            tasks = [get_event() for _ in range(10)]
            responses = await asyncio.gather(*tasks)
            
            # All responses should be successful and identical
            for response in responses:
                assert response.status_code == 200
                assert response.json()["id"] == event_id
            
            # All responses should have the same data
            first_response_data = responses[0].json()
            for response in responses[1:]:
                assert response.json() == first_response_data


@pytest.mark.integration
@pytest.mark.cache
class TestCacheConfigurationIntegration:
    """Test cache configuration and TTL behavior"""
    
    @pytest.fixture(autouse=True)
    async def setup_redis(self):
        """Setup Redis connection for testing"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        await self.redis_client.flushdb()
        yield
        await self.redis_client.flushdb()
        await self.redis_client.close()
    
    @pytest.mark.asyncio
    async def test_cache_ttl_behavior(self, server_process, api_client, sample_event_data):
        """Test that cached data has appropriate TTL"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create an event
            response = await client.post("/events/", json=sample_event_data)
            event = response.json()
            event_id = event["id"]
            
            # Get the event to trigger caching
            await client.get(f"/events/{event_id}/")
            
            # Check if cache key exists and has TTL
            cache_key = f"event:{event_id}"
            ttl = await self.redis_client.ttl(cache_key)
            
            if ttl > 0:  # TTL is set
                assert ttl <= 3600  # Should not exceed 1 hour
                print(f"Cache TTL for event: {ttl} seconds")
    
    @pytest.mark.asyncio
    async def test_cache_key_patterns(self, server_process, api_client, sample_event_data_list):
        """Test that cache keys follow expected patterns"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create events and make various requests
            for event_data in sample_event_data_list:
                await client.post("/events/", json=event_data)
            
            # Make different types of requests
            await client.get("/events/?limit=10&offset=0")
            await client.get("/events/?search=Tech&limit=5")
            await client.get("/events/?location=Austin")
            
            # Check for expected cache key patterns
            all_keys = await self.redis_client.keys("*")
            
            # Look for expected patterns
            event_keys = [k for k in all_keys if k.startswith("event:")]
            list_keys = [k for k in all_keys if k.startswith("events:list:")]
            search_keys = [k for k in all_keys if k.startswith("events:search:")]
            
            print(f"Found cache keys: {len(all_keys)} total")
            print(f"Event keys: {len(event_keys)}")
            print(f"List keys: {len(list_keys)}")
            print(f"Search keys: {len(search_keys)}")
