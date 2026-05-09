"""Helpers de cache para el MCP server.

Usa `cachetools.TTLCache` directamente (sin clase custom) y provee helpers
para:
  - generar IDs (`df_<...>`, `txt_<...>`, `doc_<...>`)
  - `require` con error claro
  - mantener "sliding TTL" (renovar TTL en cada acceso)

Nota: `cachetools` no es thread-safe por defecto, por eso los helpers
sincronizan por cache instancia.
"""

from __future__ import annotations

from threading import RLock
from typing import Any
from uuid import uuid4

from cachetools import TTLCache


def make_cache(*, ttl_seconds: int = 3600, maxsize: int = 100) -> TTLCache:
    cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
    # cachetools caches no son thread-safe; guardamos el lock en la instancia.
    setattr(cache, "_mcp_lock", RLock())
    return cache


def _lock_for(cache: TTLCache) -> RLock:
    lock = getattr(cache, "_mcp_lock", None)
    if lock is not None:
        return lock
    lock = RLock()
    setattr(cache, "_mcp_lock", lock)
    return lock


def cache_put(cache: TTLCache, value: Any, *, prefix: str = "obj") -> str:
    key = f"{prefix}_{uuid4().hex[:12]}"
    with _lock_for(cache):
        cache[key] = value
    return key


def cache_get(cache: TTLCache, key: str) -> Any | None:
    """Retorna el valor cacheado y renueva su TTL (sliding TTL)."""
    with _lock_for(cache):
        try:
            value = cache[key]
        except KeyError:
            return None

        # Sliding TTL: reinsertar para resetear el TTL.
        cache.pop(key, None)
        cache[key] = value
        return value


def cache_require(cache: TTLCache, key: str) -> Any:
    value = cache_get(cache, key)
    if value is None:
        raise KeyError(f"id '{key}' no encontrado o expirado")
    return value


def cache_delete(cache: TTLCache, key: str) -> bool:
    with _lock_for(cache):
        return cache.pop(key, None) is not None


def cache_clear(cache: TTLCache) -> int:
    with _lock_for(cache):
        n = len(cache)
        cache.clear()
        return n


def cache_keys(cache: TTLCache) -> list[str]:
    with _lock_for(cache):
        # Fuerza purge de expirados sin depender de APIs internas
        for k in list(cache.keys()):
            try:
                _ = cache[k]
            except KeyError:
                pass
        return list(cache.keys())
