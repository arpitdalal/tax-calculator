import pytest

from dataclasses import dataclass
from datetime import datetime, timedelta
from unittest.mock import patch

from app.core.cache import LRUCache

@pytest.fixture
def create_cache():
    """Create a cache with configurable capacity and TTL"""
    def make_lru_cache(capacity: int = 100, ttl_in_seconds: int = 3600):
        return LRUCache(capacity=capacity, ttl_in_seconds=ttl_in_seconds)
    return make_lru_cache

def test_cache_set_get(create_cache):
    """Test that the cache can set and get values"""
    cache = create_cache()
    cache.put("2023", [{"test": "data"}])
    assert cache.get("2023") == [{"test": "data"}]
    cache.put(42, "integer key")
    assert cache.get(42) == "integer key"
    cache.put((1, "composite"), "tuple key")
    assert cache.get((1, "composite")) == "tuple key"

def test_cache_clear(create_cache):
    """Test that the cache can clear"""
    cache = create_cache()
    cache.put("2023", [{"test": "data"}])
    cache.clear()
    assert cache.get("2023") is None

def test_cache_clear_year(create_cache):
    """Test that the cache can clear a year"""
    cache = create_cache()
    cache.put("2023", [{"test": "data"}])
    cache.put("2022", [{"test": "other"}])
    del cache["2023"]
    assert cache.get("2023") is None
    assert cache.get("2022") is not None

def test_cache_capacity_eviction(create_cache):
    """Test that the cache can evict items when the capacity is reached"""
    cache = create_cache(capacity=2, ttl_in_seconds=1)
    cache.put(1, {"first": "item"})
    cache.put(2, {"second": "item"})
    cache.put(3, {"third": "item"})
    assert cache.get(1) is None
    assert cache.get(2) is not None
    assert cache.get(3) is not None

def test_cache_ttl_expiration(create_cache):
    """Test that the cache can evict items when the TTL expires"""
    cache = create_cache(capacity=2, ttl_in_seconds=1)
    start_time = datetime(2024, 1, 1, 12, 0, 0)
    
    with patch('app.core.cache.datetime') as mock_datetime:
        mock_datetime.now.return_value = start_time
        cache.put("key", {"data": "value"})
        assert cache.get("key") is not None
        
        mock_datetime.now.return_value = start_time + timedelta(seconds=1.1)
        assert cache.get("key") is None

def test_cache_contains_operator(create_cache):
    """Test that the cache can check if a key is in the cache"""
    cache = create_cache()
    cache.put("test_key", {"data": "value"})
    assert "test_key" in cache
    assert "non_existent" not in cache

def test_lru_ordering(create_cache):
    """Test that the cache can evict items when the capacity is reached"""
    cache = create_cache(capacity=2, ttl_in_seconds=1)
    cache.put(1, {"first": "item"})
    cache.put(2, {"second": "item"})
    cache.get(1)
    cache.put(3, {"third": "item"})
    assert cache.get(1) is not None
    assert cache.get(2) is None
    assert cache.get(3) is not None

def test_custom_hashable_key(create_cache):
    """Test that custom hashable objects work as keys"""
    @dataclass(frozen=True)
    class CustomKey:
        id: int
        name: str
    
    cache = create_cache()
    key = CustomKey(1, "test")
    cache.put(key, "custom key value")
    assert cache.get(key) == "custom key value"

def test_custom_capacity_and_ttl(create_cache):
    """Test that the cache can evict items when the capacity is reached"""
    start_time = datetime(2024, 1, 1, 12, 0, 0)
    cache = create_cache(capacity=1, ttl_in_seconds=2)
    
    with patch('app.core.cache.datetime') as mock_datetime:
        mock_datetime.now.return_value = start_time
        cache.put(1, {"first": "item"})
        cache.put(2, {"second": "item"})
        assert cache.get(1) is None
        assert cache.get(2) is not None
        
        mock_datetime.now.return_value = start_time + timedelta(seconds=2.1)
        assert cache.get(2) is None
