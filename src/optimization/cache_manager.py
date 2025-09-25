"""
Advanced caching for performance optimization
"""
from typing import Any, Optional, Dict
import redis
import pickle
import hashlib
from functools import wraps
from datetime import timedelta
import asyncio
from src.core.config import settings
from src.utils.logger import logger

class CacheManager:
    """Redis-based cache manager with advanced features"""
    
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=False
        )
        self.default_ttl = 300  # 5 minutes
        
    def _generate_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate cache key from parameters"""
        # Sort parameters for consistency
        sorted_params = sorted(params.items())
        param_str = str(sorted_params)
        
        # Generate hash
        hash_obj = hashlib.md5(param_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                return pickle.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            self.redis_client.setex(
                key,
                timedelta(seconds=ttl),
                pickle.dumps(value)
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        try:
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    def cache_result(self, prefix: str, ttl: int = None):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(
                    prefix,
                    {"args": args, "kwargs": kwargs}
                )
                
                # Check cache
                cached = self.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Store in cache
                self.set(cache_key, result, ttl)
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(
                    prefix,
                    {"args": args, "kwargs": kwargs}
                )
                
                # Check cache
                cached = self.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Store in cache
                self.set(cache_key, result, ttl)
                
                return result
            
            # Return appropriate wrapper
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator

# Global cache manager
cache_manager = CacheManager()

# Example usage in email processor
class OptimizedEmailProcessor:
    """Email processor with caching"""
    
    @cache_manager.cache_result("email_intent", ttl=3600)
    async def classify_intent(self, email_content: str) -> str:
        """Classify email intent with caching"""
        # Expensive AI operation
        # Result will be cached for 1 hour
        pass
    
    @cache_manager.cache_result("knowledge_search", ttl=1800)
    async def search_knowledge_base(self, query: str) -> List[Dict]:
        """Search knowledge base with caching"""
        # Expensive search operation
        # Result will be cached for 30 minutes
        pass
