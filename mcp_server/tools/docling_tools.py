"""Tools de Docling: parseo de documentos (PDF, DOCX, HTML, etc.) a markdown
y extracción de tablas como DataFrames cacheados (puente con pandas_tools).
"""

from __future__ import annotations

from typing import Any

from loguru import logger
from mcp.server.fastmcp import FastMCP

from cachetools import TTLCache

from mcp_server.cache import cache_put, cache_require


def register(mcp: FastMCP, cache: TTLCache) -> None:

    @mcp.tool()
    def parse_document(path: str) -> dict[str, Any]:
        """Parsea un documento (PDF/DOCX/HTML/PPTX/MD) con Docling.

        Cachea el documento bajo un `doc_id` y retorna su markdown completo
        más metadata de las tablas detectadas. Cada tabla queda accesible
        por su índice vía `extract_table(doc_id, idx)`.
        """
        from docling.document_converter import DocumentConverter

        logger.info(f"parse_document path={path}")
        
        converter = DocumentConverter()
        result = converter.convert(path)
        document = result.document

        markdown = document.export_to_markdown()
        tables = list(getattr(document, "tables", []) or [])

        doc_id = cache_put(cache, {"document": document, "tables": tables}, prefix="doc")

        return {
            "doc_id": doc_id,
            "markdown": markdown,
            "num_tables": len(tables),
            "num_pages": getattr(document, "num_pages", None),
        }

    @mcp.tool()
    def get_document_markdown(doc_id: str) -> dict[str, Any]:
        """Retorna el markdown del documento cacheado."""
        
        entry = cache_require(cache, doc_id)
        markdown = entry["document"].export_to_markdown()
        
        return {"doc_id": doc_id, "markdown": markdown}

    @mcp.tool()
    def list_document_tables(doc_id: str) -> dict[str, Any]:
        """Lista las tablas detectadas en el documento."""
        
        entry = cache_require(cache, doc_id)
        tables = entry["tables"]
        summary = []
        
        for i, table in enumerate(tables):
            label = getattr(table, "label", None) or getattr(table, "self_ref", f"table_{i}")
            summary.append({"index": i, "label": str(label)})
        
        return {"doc_id": doc_id, "num_tables": len(tables), "tables": summary}

    @mcp.tool()
    def extract_table(doc_id: str, index: int) -> dict[str, Any]:
        """Convierte la tabla N del documento a DataFrame cacheado.

        Retorna `df_id` para que `df_head`, `df_query`, etc., la consuman.
        """
        entry = cache_require(cache, doc_id)
        tables = entry["tables"]
        if not (0 <= index < len(tables)):
            raise IndexError(f"índice {index} fuera de rango (tablas: {len(tables)})")

        table = tables[index]
        df = table.export_to_dataframe()
        df_id = cache_put(cache, df, prefix="df")
        
        return {
            "df_id": df_id,
            "doc_id": doc_id,
            "index": index,
            "shape": list(df.shape),
            "columns": list(df.columns.astype(str)),
            "rows": df.head(10).to_dict(orient="records"),
        }
