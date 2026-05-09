"""TTL cache thread-safe en proceso para DataFrames, textos y documentos."""

from __future__ import annotations

import threading
import time
from typing import Any
from uuid import uuid4


class TTLCache:
    def __init__(self, ttl_seconds: int = 3600, maxsize: int = 100) -> None:
        self._data: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl_seconds
        self._maxsize = maxsize
        self._lock = threading.Lock()

    def put(self, value: Any, prefix: str = "obj") -> str:
        key = f"{prefix}_{uuid4().hex[:12]}"
        expires_at = time.time() + self._ttl
        with self._lock:
            self._evict_if_needed_locked()
            self._data[key] = (expires_at, value)
        return key

    def get(self, key: str) -> Any | None:
        """Retorna el valor cacheado y renueva su TTL (sliding TTL)."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            now = time.time()
            if now > expires_at:
                del self._data[key]
                return None
            self._data[key] = (now + self._ttl, value)
            return value

    def require(self, key: str) -> Any:
        value = self.get(key)
        if value is None:
            raise KeyError(f"id '{key}' no encontrado o expirado")
        return value

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._data.pop(key, None) is not None

    def clear(self) -> int:
        with self._lock:
            n = len(self._data)
            self._data.clear()
            return n

    def keys(self) -> list[str]:
        with self._lock:
            self._purge_expired_locked()
            return list(self._data.keys())

    def _evict_if_needed_locked(self) -> None:
        self._purge_expired_locked()
        if len(self._data) >= self._maxsize:
            oldest_key = min(self._data, key=lambda k: self._data[k][0])
            del self._data[oldest_key]

    def _purge_expired_locked(self) -> None:
        now = time.time()
        expired = [k for k, (exp, _) in self._data.items() if now > exp]
        for k in expired:
            del self._data[k]
