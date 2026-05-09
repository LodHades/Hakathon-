/**
 * Mirrors de los Pydantic schemas en `backend/agents/ui_builder/a2ui_schemas.py`.
 * Mantener sincronizados.
 */

export type ChartType = "line" | "bar" | "pie" | "scatter" | "area";

export interface ChartSpec {
  type: ChartType;
  title: string;
  data: Record<string, unknown>[];
  x: string;
  y: string[];
  color?: string;
  description?: string;
}

export interface KPISpec {
  label: string;
  value: string;
  delta?: string;
  trend?: "up" | "down" | "neutral";
  description?: string;
}

export interface TableSpec {
  title: string;
  columns: string[];
  rows: unknown[][];
  description?: string;
}

export interface MarkdownSpec {
  content: string;
}
