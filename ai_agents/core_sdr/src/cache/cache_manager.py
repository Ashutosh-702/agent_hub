import hashlib
import json
import logging
import time
from typing import Dict, Any, Optional, List

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False

from ..core.models import CacheEntry, Company

logger = logging.getLogger(__name__)


class MongoCache:
    """MongoDB-based cache implementation."""
    
    def __init__(self, mongo_uri: str):
        if not MONGO_AVAILABLE:
            raise ImportError("PyMongo package not available")
        
        self.mongo_uri = mongo_uri
        self.client = None
        self.db = None
        self.collection = None
        self.connected = False
        
        self._connect()
    
    def _connect(self):
        """Establish MongoDB connection and set up collection."""
        try:
            self.client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test the connection
            self.client.admin.command('ismaster')
            
            self.db = self.client.get_default_database()
            self.collection = self.db.leadgen_cache
            
            # Create TTL index for automatic expiration
            self.collection.create_index("expires_at", expireAfterSeconds=0)
            
            self.connected = True
            logger.info("Successfully connected to MongoDB cache")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning(f"Failed to connect to MongoDB: {str(e)}")
            self.connected = False
        except Exception as e:
            logger.error(f"MongoDB connection error: {str(e)}")
            self.connected = False
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached entry by key."""
        if not self.connected:
            return None
        
        try:
            entry = self.collection.find_one({'_id': key})
            if entry and entry.get('expires_at', 0) > time.time():
                return entry['data']
            elif entry:
                # Remove expired entry
                self.collection.delete_one({'_id': key})
        except Exception as e:
            logger.warning(f"MongoDB get error: {str(e)}")
        
        return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: int = 86400):
        """Set cached entry with TTL."""
        if not self.connected:
            return
        
        try:
            expires_at = time.time() + ttl
            self.collection.replace_one(
                {'_id': key},
                {
                    '_id': key,
                    'data': value,
                    'expires_at': expires_at,
                    'created_at': time.time()
                },
                upsert=True
            )
        except Exception as e:
            logger.warning(f"MongoDB set error: {str(e)}")
    
    def delete(self, key: str) -> bool:
        """Delete cached entry by key."""
        if not self.connected:
            return False
        
        try:
            result = self.collection.delete_one({'_id': key})
            return result.deleted_count > 0
        except Exception as e:
            logger.warning(f"MongoDB delete error: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """Clear all cached entries."""
        if not self.connected:
            return False
        
        try:
            self.collection.drop()
            # Recreate the TTL index
            self.collection.create_index("expires_at", expireAfterSeconds=0)
            return True
        except Exception as e:
            logger.warning(f"MongoDB clear error: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.connected:
            return {"connected": False, "total_entries": 0}
        
        try:
            total_entries = self.collection.count_documents({})
            expired_entries = self.collection.count_documents({
                "expires_at": {"$lt": time.time()}
            })
            
            return {
                "connected": True,
                "total_entries": total_entries,
                "expired_entries": expired_entries,
                "active_entries": total_entries - expired_entries
            }
        except Exception as e:
            logger.warning(f"MongoDB stats error: {str(e)}")
            return {"connected": False, "error": str(e)}


class NoOpCache:
    """No-operation cache for when MongoDB is not available."""
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: int = 86400):
        pass
    
    def delete(self, key: str) -> bool:
        return True
    
    def clear(self) -> bool:
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        return {"connected": False, "cache_type": "no-op"}


class CacheManager:
    """MongoDB-only cache manager."""
    
    def __init__(self, mongo_uri: Optional[str] = None, default_ttl: int = 86400):
        self.default_ttl = default_ttl
        
        if mongo_uri and MONGO_AVAILABLE:
            try:
                self.cache = MongoCache(mongo_uri)
                logger.info("MongoDB cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize MongoDB cache: {str(e)}")
                self.cache = NoOpCache()
        else:
            logger.info("No MongoDB URI provided or PyMongo not available, using no-op cache")
            self.cache = NoOpCache()
    
    def _generate_cache_key(self, query: str, params: Dict[str, Any]) -> str:
        """Generate MD5 hash key from query and parameters."""
        # Normalize query and params for consistent hashing
        normalized_query = query.lower().strip()
        normalized_params = json.dumps(params, sort_keys=True)
        
        key_string = f"{normalized_query}:{normalized_params}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query: str, params: Dict[str, Any]) -> Optional[CacheEntry]:
        """
        Get cached results for a query.
        
        Args:
            query: Original search query
            params: Search parameters
            
        Returns:
            CacheEntry if found, None otherwise
        """
        cache_key = self._generate_cache_key(query, params)
        data = self.cache.get(cache_key)
        
        if data:
            try:
                return CacheEntry(**data)
            except Exception as e:
                logger.warning(f"Failed to deserialize cache entry: {str(e)}")
        
        return None
    
    def set(self, query: str, params: Dict[str, Any], 
            dsl_query: Dict[str, Any], results: List[Company], 
            credits_used: int, total_found: int):
        """
        Cache search results.
        
        Args:
            query: Original search query
            params: Search parameters
            dsl_query: Generated DSL query
            results: Search results
            credits_used: API credits consumed
            total_found: Total number of results found
        """
        cache_key = self._generate_cache_key(query, params)
        
        cache_entry = CacheEntry(
            key=cache_key,
            query=query,
            dsl_query=dsl_query,
            results=results,
            timestamp=time.time(),
            credits_used=credits_used,
            total_found=total_found
        )
        
        cache_data = cache_entry.dict()
        self.cache.set(cache_key, cache_data, self.default_ttl)
    
    def delete(self, query: str, params: Dict[str, Any]) -> bool:
        """Delete cached entry for a query."""
        cache_key = self._generate_cache_key(query, params)
        return self.cache.delete(cache_key)
    
    def clear_all(self) -> bool:
        """Clear all cached entries."""
        return self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and connection status."""
        stats = self.cache.get_stats()
        stats['cache_type'] = 'mongodb' if isinstance(self.cache, MongoCache) else 'no-op'
        return stats
    
    def is_connected(self) -> bool:
        """Check if cache is connected and functional."""
        return isinstance(self.cache, MongoCache) and self.cache.connected