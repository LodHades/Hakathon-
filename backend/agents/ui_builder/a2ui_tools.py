"""Tools LangChain que el UIBuilderAgent invoca para emitir componentes A2UI.

Estos tools no tienen efecto en el backend más allá de validar y serializar
la spec: el frontend (CopilotKit `useCopilotAction`) intercepta la tool call
y renderiza el componente. El return string es solo confirmación para el LLM.
"""

from __future__ import annotations

import json
from typing import Any, Literal, Optional

from langchain_core.tools import tool

from .a2ui_schemas import ChartSpec, ChartType, KPISpec, MarkdownSpec, TableSpec


def _emit(component: str, spec: dict[str, Any]) -> str:
    return json.dumps({"a2ui": component, "spec": spec}, ensure_ascii=False)


@tool
def emit_chart(
    type: ChartType,
    title: str,
    data: list[dict[str, Any]],
    x: str,
    y: list[str],
    color: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """Renderiza un gráfico en el chat.

    Tipos soportados: line (evolución temporal), bar (comparaciones),
    pie (composición), scatter (correlación), area (acumulado).

    Pasa los datos concretos en `data` (lista de objetos), referenciando los
    campos por nombre en `x` (eje X, único) y `y` (eje Y, lista para series).
    """
    spec = ChartSpec(type=type, title=title, data=data, x=x, y=y, color=color, description=description)
    return _emit("chart", spec.model_dump())


@tool
def emit_kpi(
    label: str,
    value: str,
    delta: Optional[str] = None,
    trend: Optional[Literal["up", "down", "neutral"]] = None,
    description: Optional[str] = None,
) -> str:
    """Renderiza un KPI / métrica destacada (totales, promedios, máximos, etc.).

    `value` debe venir formateado como string ('$1.2M', '23.5%', '4,212').
    `delta` opcional para mostrar variación vs. periodo anterior ('+12.5%').
    """
    spec = KPISpec(label=label, value=value, delta=delta, trend=trend, description=description)
    return _emit("kpi", spec.model_dump())


@tool
def emit_table(
    title: str,
    columns: list[str],
    rows: list[list[Any]],
    description: Optional[str] = None,
) -> str:
    """Renderiza una tabla con columnas y filas.

    Útil para rankings, top-N o listados que no se prestan a una gráfica.
    `rows` es lista de listas; cada fila debe tener len == len(columns).
    """
    spec = TableSpec(title=title, columns=columns, rows=rows, description=description)
    return _emit("table", spec.model_dump())


@tool
def emit_markdown(content: str) -> str:
    """Renderiza un bloque de texto en Markdown.

    Úsalo para introducciones, conclusiones o explicaciones entre componentes.
    Soporta listas, tablas y énfasis.
    """
    spec = MarkdownSpec(content=content)
    return _emit("markdown", spec.model_dump())


def get_ui_tools() -> list:
    return [emit_chart, emit_kpi, emit_table, emit_markdown]
