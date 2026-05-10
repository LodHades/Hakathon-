"""MCP server local que expone Pandas + Docling.

Soporta dos transports:
  - stdio (default): para clientes que lanzan el server como subproceso
  - sse: para uso en Docker / red

Uso:
  python -m mcp_server.server                  # stdio
  python -m mcp_server.server --transport sse  # SSE en :8765
"""

from __future__ import annotations

import argparse
import sys

from loguru import logger
from mcp.server.fastmcp import FastMCP

from mcp_server.cache import make_cache
from mcp_server.tools import docling_tools, pandas_tools


def build_mcp(host: str = "0.0.0.0", port: int = 8765) -> FastMCP:
    
    mcp = FastMCP(name="data-mcp", host=host, port=port)
    cache = make_cache(ttl_seconds=3600, maxsize=100)
    pandas_tools.register(mcp, cache)
    docling_tools.register(mcp, cache)
    
    return mcp


def main() -> None:
    
    parser = argparse.ArgumentParser(description="data-mcp server")
    
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport del MCP. stdio para subproceso, sse para red.",
    )
    
    parser.add_argument("--host", default="0.0.0.0", help="Host SSE (ignorado en stdio).")
    parser.add_argument("--port", type=int, default=8765, help="Puerto SSE.")
    parser.add_argument("--log-level", default="INFO")
    
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level=args.log_level)

    mcp = build_mcp(host=args.host, port=args.port)
    logger.info(f"data-mcp arrancando con transport={args.transport}")
    
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
