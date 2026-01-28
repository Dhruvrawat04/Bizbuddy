"""
Simple In-Memory Caching Layer for Dashboard Statistics
Reduces database load by caching frequently accessed data
"""
from datetime import datetime, timedelta
from typing import Any, Optional, Callable
import threading

class SimpleCache:
    """Thread-safe in-memory cache with TTL support"""
    
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if datetime.now() < expiry:
                    return value
                else:
                    # Expired, remove it
                    del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL (default 5 minutes)"""
        with self._lock:
            expiry = datetime.now() + timedelta(seconds=ttl_seconds)
            self._cache[key] = (value, expiry)
    
    def delete(self, key: str):
        """Remove key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self):
        """Clear entire cache"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        with self._lock:
            total_keys = len(self._cache)
            expired_keys = sum(1 for _, (_, expiry) in self._cache.items() 
                             if datetime.now() >= expiry)
            return {
                'total_keys': total_keys,
                'active_keys': total_keys - expired_keys,
                'expired_keys': expired_keys
            }
    
    def cached(self, key: str, ttl_seconds: int = 300):
        """Decorator for caching function results"""
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                # Try to get from cache
                cached_value = self.get(key)
                if cached_value is not None:
                    return cached_value
                
                # Not in cache, execute function
                result = func(*args, **kwargs)
                
                # Store in cache
                self.set(key, result, ttl_seconds)
                return result
            return wrapper
        return decorator


# Global cache instance
cache = SimpleCache()


def get_cached_or_fetch(cache_key: str, fetch_func: Callable, ttl_seconds: int = 300) -> Any:
    """
    Helper function to get cached value or fetch and cache it
    
    Args:
        cache_key: Unique key for this cached data
        fetch_func: Function to call if cache miss (should return the data)
        ttl_seconds: Time to live in seconds (default 5 minutes)
    
    Returns:
        The cached or freshly fetched data
    """
    # Try cache first
    cached_value = cache.get(cache_key)
    if cached_value is not None:
        return cached_value
    
    # Cache miss - fetch data
    fresh_value = fetch_func()
    
    # Store in cache
    cache.set(cache_key, fresh_value, ttl_seconds)
    
    return fresh_value


def invalidate_cache_pattern(pattern: str):
    """
    Invalidate all cache keys matching a pattern
    
    Args:
        pattern: String pattern to match (simple substring match)
    """
    keys_to_delete = []
    
    # Find matching keys
    for key in cache._cache.keys():
        if pattern in key:
            keys_to_delete.append(key)
    
    # Delete them
    for key in keys_to_delete:
        cache.delete(key)


# Cache keys constants for consistency
CACHE_KEYS = {
    'DASHBOARD_STATS': 'dashboard:stats',
    'LOW_STOCK_COUNT': 'dashboard:low_stock_count',
    'TODAY_SALES': 'dashboard:today_sales',
    'PRODUCT_COUNT': 'dashboard:product_count',
    'TOTAL_REVENUE': 'dashboard:total_revenue',
    'CATEGORY_SALES': 'analytics:category_sales',
    'TOP_PRODUCTS': 'analytics:top_products:{}',  # Format with limit
    'SALES_BY_DATE': 'analytics:sales_by_date:{}',  # Format with days
}


# Usage example:
"""
from cache_layer import cache, get_cached_or_fetch, CACHE_KEYS

# Option 1: Using decorator
@cache.cached(CACHE_KEYS['DASHBOARD_STATS'], ttl_seconds=300)
def get_dashboard_stats():
    # Expensive database query
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM products"))
        return result.scalar()

# Option 2: Using helper function
def fetch_sales_data():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT SUM(total_amount) FROM sales"))
        return result.scalar()

total_sales = get_cached_or_fetch(
    CACHE_KEYS['TOTAL_REVENUE'],
    fetch_sales_data,
    ttl_seconds=300
)

# Option 3: Manual cache usage
cached_data = cache.get('my_key')
if cached_data is None:
    cached_data = expensive_operation()
    cache.set('my_key', cached_data, ttl_seconds=600)
"""
