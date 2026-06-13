"""
Redis Client Module
Handles connection and operations with Redis cache
"""

import os
import redis
import json
import hashlib
from dotenv import load_dotenv
from typing import Any, Dict, Optional, Tuple

load_dotenv()

def get_redis_client() -> Optional[redis.Redis]:
    """Get connection to Redis instance, return None if unavailable"""
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    try:
        r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True, socket_connect_timeout=2)
        r.ping()  # test connection
        return r
    except Exception as e:
        print(f"Warning: Redis connection failed: {e}")
        return None

def get_cached_prediction(r: redis.Redis, request_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Generate cache key and retrieve cached prediction if available"""
    if not r:
        return None, None
    try:
        serialized_input = json.dumps(request_data, sort_keys=True)
        cache_key = f"prediction:{hashlib.md5(serialized_input.encode()).hexdigest()}"
        cached_val = r.get(cache_key)
        if cached_val:
            cached_res = json.loads(cached_val)
            cached_res["cached"] = True
            return cache_key, cached_res
        return cache_key, None
    except Exception as e:
        print(f"Warning: Redis cache lookup failed: {e}")
        return None, None

def set_cached_prediction(r: redis.Redis, cache_key: str, response_dict: Dict[str, Any], ttl: int = 3600):
    """Cache prediction result in Redis"""
    if r and cache_key:
        try:
            r.set(cache_key, json.dumps(response_dict), ex=ttl)
        except Exception as e:
            print(f"Warning: Failed to cache in Redis: {e}")
