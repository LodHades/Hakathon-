"""Specs A2UI que el backend emite y el frontend renderiza.

Cada componente tiene un Pydantic schema que actúa como contrato entre
el UIBuilderAgent (productor) y los renderers React registrados con
`useCopilotAction` en el frontend (consumidor).

Mantener este archivo sincronizado con `frontend/components/a2ui/`.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


ChartType = Literal["line", "bar", "pie", "scatter", "area"]


class ChartSpec(BaseModel):
    type: ChartType
    title: str
    data: list[dict[str, Any]] = Field(
        description="Lista de objetos con las columnas referenciadas por x/y."
    )
    x: str = Field(description="Nombre del campo en `data` para el eje X.")
    y: list[str] = Field(description="Nombre(s) del campo Y. Múltiples para series.")
    color: Optional[str] = Field(
        default=None, description="Campo categórico para color/serie (opcional)."
    )
    description: Optional[str] = Field(
        default=None, description="Texto corto explicando la gráfica."
    )


class KPISpec(BaseModel):
    label: str
    value: str = Field(description="Valor formateado, p.ej. '$1.2M', '23.5%', '4,212'.")
    delta: Optional[str] = Field(
        default=None,
        description="Variación vs. periodo anterior, formato '+12.5%' o '-3.2%'.",
    )
    trend: Optional[Literal["up", "down", "neutral"]] = None
    description: Optional[str] = None


class TableSpec(BaseModel):
    title: str
    columns: list[str]
    rows: list[list[Any]] = Field(
        description="Filas en orden de `columns`. Cada fila es lista de valores."
    )
    description: Optional[str] = None


class MarkdownSpec(BaseModel):
    content: str = Field(description="Contenido en Markdown. Soporta tablas, listas, énfasis.")
