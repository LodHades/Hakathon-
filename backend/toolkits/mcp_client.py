"""Cliente MCP del backend.

Wrapper fino sobre `langchain_mcp_adapters.MultiServerMCPClient` que centraliza
la configuración de los MCP servers (data-mcp local + futuros: Snowflake, GCP).

El método `get_tools()` es async porque el adapter abre conexiones MCP
(stdio: lanza subproceso; sse: cliente HTTP) la primera vez que se solicitan tools.
"""

from __future__ import annotations

import os
import shlex
from typing import Any

from langchain_core.tools.base import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from loguru import logger

from backend.settings import settings


class MCPClient:
    def __init__(self, servers: dict[str, dict[str, Any]]):
        self._servers = servers
        self._client: MultiServerMCPClient | None = None

    async def get_tools(self) -> list[BaseTool]:
        if self._client is None:
            logger.bind(module="mcp_client").info(
                f"inicializando MultiServerMCPClient con {list(self._servers)}"
            )
            self._client = MultiServerMCPClient(self._servers)
        tools = await self._client.get_tools()
        logger.bind(module="mcp_client").info(f"{len(tools)} tools cargadas desde MCP")
        return tools


def _data_mcp_config() -> dict[str, Any]:
    if settings.MCP_DATA_TRANSPORT == "stdio":
        return {
            "command": settings.MCP_DATA_COMMAND,
            "args": ["-m", "mcp_server.server"],
            "transport": "stdio",
            "cwd": str(settings.ROOT),
        }
    return {
        "url": settings.MCP_DATA_URL,
        "transport": "sse",
    }


def _external_mcp_config(
    transport: str, command: str, args: str, url: str
) -> dict[str, Any]:
    """Config para MCPs externos (Snowflake, BigQuery) — credenciales vía env."""
    if transport == "stdio":
        return {
            "command": command,
            "args": shlex.split(args),
            "transport": "stdio",
            "env": dict(os.environ),
        }
    if not url:
        raise ValueError(
            "MCP transport=sse requiere URL (p.ej. MCP_SNOWFLAKE_URL / MCP_BIGQUERY_URL)"
        )
    return {"url": url, "transport": "sse"}


def build_default_client() -> MCPClient:
    """Construye un MCPClient con la configuración del .env.

    Registra siempre `data` (Pandas + Docling). Snowflake y BigQuery se
    añaden si su respectivo `MCP_*_ENABLED=true`.
    """
    servers: dict[str, dict[str, Any]] = {"data": _data_mcp_config()}

    if settings.MCP_SNOWFLAKE_ENABLED:
        servers["snowflake"] = _external_mcp_config(
            transport=settings.MCP_SNOWFLAKE_TRANSPORT,
            command=settings.MCP_SNOWFLAKE_COMMAND,
            args=settings.MCP_SNOWFLAKE_ARGS,
            url=settings.MCP_SNOWFLAKE_URL,
        )

    if settings.MCP_BIGQUERY_ENABLED:
        servers["bigquery"] = _external_mcp_config(
            transport=settings.MCP_BIGQUERY_TRANSPORT,
            command=settings.MCP_BIGQUERY_COMMAND,
            args=settings.MCP_BIGQUERY_ARGS,
            url=settings.MCP_BIGQUERY_URL,
        )

    return MCPClient(servers=servers)
