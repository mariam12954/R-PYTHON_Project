import json
import logging
from typing import Any, Optional
from redis import Redis
from redis.exceptions import RedisError
from app.core.config import settings

logger = logging.getLogger("app.cache")
_redis_client: Optional[Redis] = None
_cache_available: Optional[bool] = None


def _get_client() -> Optional[Redis]:
    global _redis_client, _cache_available
    if _redis_client is not None or _cache_available is False:
        return _redis_client

    try:
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.ping()
        _redis_client = client
        _cache_available = True
    except RedisError as exc:
        _cache_available = False
        logger.warning("Redis unavailable: %s", exc)
        _redis_client = None

    return _redis_client


def cache_get_json(key: str) -> Optional[Any]:
    client = _get_client()
    if not client:
        return None
    try:
        raw = client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except (RedisError, json.JSONDecodeError) as exc:
        logger.warning("Cache get failed for key=%s: %s", key, exc)
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
    client = _get_client()
    if not client:
        return
    ttl = ttl_seconds if ttl_seconds is not None else settings.CACHE_TTL_SECONDS
    try:
        client.setex(key, ttl, json.dumps(value))
    except (RedisError, TypeError) as exc:
        logger.warning("Cache set failed for key=%s: %s", key, exc)


def cache_delete(key: str) -> None:
    client = _get_client()
    if not client:
        return
    try:
        client.delete(key)
    except RedisError as exc:
        logger.warning("Cache delete failed for key=%s: %s", key, exc)


def cache_delete_pattern(pattern: str) -> None:
    client = _get_client()
    if not client:
        return
    try:
        keys = list(client.scan_iter(match=pattern))
        if keys:
            client.delete(*keys)
    except RedisError as exc:
        logger.warning("Cache pattern delete failed for pattern=%s: %s", pattern, exc)
