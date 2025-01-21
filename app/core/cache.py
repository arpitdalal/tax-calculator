from collections import OrderedDict
from datetime import datetime
from typing import TypeVar, Generic, Optional, Hashable

K = TypeVar('K', bound=Hashable)
V = TypeVar('V')

class LRUCache(Generic[K, V]):
    """
    In-memory cache implementation using OrderedDict.
    Supports any hashable type as key and any type as value.
    """
    def __init__(self, capacity: int = 100, ttl_in_seconds: int = 3600):
        self.cache: OrderedDict[K, tuple[V, float]] = OrderedDict()
        self.capacity = capacity
        self.ttl_in_seconds = ttl_in_seconds

    def __contains__(self, key: K) -> bool:
        """Support 'in' operator"""
        return key in self.cache

    def __delitem__(self, key: K) -> None:
        """Support delete operation"""
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """Clear entire cache"""
        self.cache.clear()

    def get(self, key: K) -> Optional[V]:
        if key not in self.cache:
            return None
        value, timestamp = self.cache[key]
        if datetime.now().timestamp() - timestamp > self.ttl_in_seconds:
            del self.cache[key]
            return None
        self.cache.move_to_end(key)
        return value

    def put(self, key: K, value: V) -> None:
        if key in self.cache:
            del self.cache[key]
        elif len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = (value, datetime.now().timestamp())
        self.cache.move_to_end(key) 