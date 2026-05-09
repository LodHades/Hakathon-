"""Tools de Pandas para el MCP server.

Devuelven IDs cacheados (`df_<...>` o `txt_<...>`) en vez del DataFrame entero
para evitar saturar el contexto del agente. El agente luego usa `df_head`,
`df_describe`, `df_query`, etc., para inspeccionar y consultar.
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd
from loguru import logger
from mcp.server.fastmcp import FastMCP

from mcp_server.cache import TTLCache


def _df_summary(df_id: str, df: pd.DataFrame) -> dict[str, Any]:
    return {
        "df_id": df_id,
        "shape": list(df.shape),
        "columns": list(df.columns.astype(str)),
        "dtypes": {str(c): str(t) for c, t in df.dtypes.items()},
    }


def _records(df: pd.DataFrame, n: int) -> list[dict[str, Any]]:
    return df.head(n).to_dict(orient="records")


def register(mcp: FastMCP, cache: TTLCache) -> None:
    @mcp.tool()
    def read_csv(
        path: str,
        separator: str = ",",
        header: Optional[int] = 0,
        encoding: str = "utf-8",
        nrows: Optional[int] = None,
    ) -> dict[str, Any]:
        """Lee un CSV (ruta local o URL) y lo cachea como DataFrame.

        Retorna un `df_id` con el que las demás tools pueden inspeccionarlo.
        """
        logger.info(f"read_csv path={path} sep={separator!r} nrows={nrows}")
        df = pd.read_csv(path, sep=separator, header=header, encoding=encoding, nrows=nrows)
        df_id = cache.put(df, prefix="df")
        return _df_summary(df_id, df)

    @mcp.tool()
    def read_json(
        path: str,
        orient: Optional[str] = None,
        lines: bool = False,
        encoding: str = "utf-8",
    ) -> dict[str, Any]:
        """Lee un JSON (ruta local o URL) y lo cachea como DataFrame.

        `lines=True` para JSONL. `orient` opcional ('records', 'split', 'index', 'columns', 'values').
        """
        logger.info(f"read_json path={path} orient={orient} lines={lines}")
        df = pd.read_json(path, orient=orient, lines=lines, encoding=encoding)
        df_id = cache.put(df, prefix="df")
        return _df_summary(df_id, df)

    @mcp.tool()
    def read_txt(path: str, encoding: str = "utf-8") -> dict[str, Any]:
        """Lee un archivo de texto plano y lo cachea como string.

        Retorna `txt_id` y longitud. Para inspeccionar usa `get_text`.
        """
        logger.info(f"read_txt path={path}")
        with open(path, "r", encoding=encoding) as f:
            content = f.read()
        txt_id = cache.put(content, prefix="txt")
        return {"txt_id": txt_id, "length": len(content), "preview": content[:500]}

    @mcp.tool()
    def get_text(txt_id: str, start: int = 0, length: int = 4000) -> dict[str, Any]:
        """Retorna una porción del texto cacheado bajo `txt_id`."""
        text: str = cache.require(txt_id)
        chunk = text[start : start + length]
        return {"txt_id": txt_id, "start": start, "length": len(chunk), "content": chunk}

    @mcp.tool()
    def df_head(df_id: str, n: int = 10) -> dict[str, Any]:
        """Retorna las primeras `n` filas del DataFrame `df_id`."""
        df: pd.DataFrame = cache.require(df_id)
        return {"df_id": df_id, "n": min(n, len(df)), "rows": _records(df, n)}

    @mcp.tool()
    def df_describe(df_id: str, include: Optional[str] = None) -> dict[str, Any]:
        """`df.describe()` del DataFrame. `include='all'` para columnas no numéricas."""
        df: pd.DataFrame = cache.require(df_id)
        desc = df.describe(include=include) if include else df.describe()
        return {"df_id": df_id, "describe": desc.to_dict()}

    @mcp.tool()
    def df_columns(df_id: str) -> dict[str, Any]:
        """Esquema del DataFrame: nombres de columnas y dtypes."""
        df: pd.DataFrame = cache.require(df_id)
        return {
            "df_id": df_id,
            "shape": list(df.shape),
            "columns": list(df.columns.astype(str)),
            "dtypes": {str(c): str(t) for c, t in df.dtypes.items()},
        }

    @mcp.tool()
    def df_sample(df_id: str, n: int = 10, random_state: int = 42) -> dict[str, Any]:
        """Muestra aleatoria de `n` filas."""
        df: pd.DataFrame = cache.require(df_id)
        sample = df.sample(n=min(n, len(df)), random_state=random_state)
        return {"df_id": df_id, "n": len(sample), "rows": sample.to_dict(orient="records")}

    @mcp.tool()
    def df_query(df_id: str, expr: str, top: int = 15) -> dict[str, Any]:
        """Aplica `df.query(expr)` (sintaxis Pandas) y cachea el resultado.

        Retorna un nuevo `df_id`, su shape y las primeras `top` filas.
        """
        df: pd.DataFrame = cache.require(df_id)
        result = df.query(expr)
        new_id = cache.put(result, prefix="df")
        return {
            "df_id": new_id,
            "source_df_id": df_id,
            "expr": expr,
            "shape": list(result.shape),
            "rows": _records(result, top),
        }

    @mcp.tool()
    def df_value_counts(df_id: str, column: str, top: int = 20) -> dict[str, Any]:
        """`df[column].value_counts()` con los `top` valores más frecuentes."""
        df: pd.DataFrame = cache.require(df_id)
        if column not in df.columns:
            raise KeyError(f"columna '{column}' no existe en df {df_id}")
        counts = df[column].value_counts().head(top)
        return {
            "df_id": df_id,
            "column": column,
            "top": top,
            "counts": {str(k): int(v) for k, v in counts.items()},
        }

    @mcp.tool()
    def df_groupby_agg(
        df_id: str,
        group_by: list[str],
        agg: dict[str, str],
        top: int = 50,
    ) -> dict[str, Any]:
        """`df.groupby(group_by).agg(agg)`. `agg` es un dict columna→función ('sum','mean',...)."""
        df: pd.DataFrame = cache.require(df_id)
        result = df.groupby(group_by).agg(agg).reset_index()
        new_id = cache.put(result, prefix="df")
        return {
            "df_id": new_id,
            "source_df_id": df_id,
            "shape": list(result.shape),
            "rows": _records(result, top),
        }

    @mcp.tool()
    def cache_list() -> dict[str, Any]:
        """Lista todos los IDs cacheados (df_ y txt_) actualmente vivos."""
        return {"keys": cache.keys()}

    @mcp.tool()
    def cache_drop(key: str) -> dict[str, Any]:
        """Elimina un objeto del cache."""
        ok = cache.delete(key)
        return {"key": key, "deleted": ok}
