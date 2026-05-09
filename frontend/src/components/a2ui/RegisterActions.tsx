/**
 * Registra los renderers A2UI con `useCopilotAction` matcheando por nombre
 * los tools que el backend (UIBuilderAgent) emite: `emit_chart`, `emit_kpi`,
 * `emit_table`, `emit_markdown`.
 *
 * CopilotKit captura las tool calls del agente y, si encuentra una action
 * con el mismo nombre, llama a su `render()` con los args de la tool —
 * mostrando el componente inline en lugar de la tool call cruda.
 */

import { useCopilotAction } from "@copilotkit/react-core";

import { ChartRenderer } from "./ChartRenderer";
import { KpiRenderer } from "./KpiRenderer";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { TableRenderer } from "./TableRenderer";
import type { ChartSpec, KPISpec, MarkdownSpec, TableSpec } from "./types";

export function RegisterA2UIActions() {
  useCopilotAction({
    name: "emit_chart",
    description: "Renderiza un gráfico (line/bar/pie/scatter/area).",
    parameters: [
      { name: "type", type: "string", required: true },
      { name: "title", type: "string", required: true },
      { name: "data", type: "object[]", required: true },
      { name: "x", type: "string", required: true },
      { name: "y", type: "string[]", required: true },
      { name: "color", type: "string", required: false },
      { name: "description", type: "string", required: false },
    ],
    render: ({ args, status }) => {
      if (status !== "complete") {
        return <div className="a2ui-pending">Generando gráfico…</div>;
      }
      return <ChartRenderer spec={args as unknown as ChartSpec} />;
    },
  });

  useCopilotAction({
    name: "emit_kpi",
    description: "Renderiza una métrica destacada (KPI).",
    parameters: [
      { name: "label", type: "string", required: true },
      { name: "value", type: "string", required: true },
      { name: "delta", type: "string", required: false },
      { name: "trend", type: "string", required: false },
      { name: "description", type: "string", required: false },
    ],
    render: ({ args, status }) => {
      if (status !== "complete") {
        return <div className="a2ui-pending">Generando KPI…</div>;
      }
      return <KpiRenderer spec={args as unknown as KPISpec} />;
    },
  });

  useCopilotAction({
    name: "emit_table",
    description: "Renderiza una tabla.",
    parameters: [
      { name: "title", type: "string", required: true },
      { name: "columns", type: "string[]", required: true },
      { name: "rows", type: "object[]", required: true },
      { name: "description", type: "string", required: false },
    ],
    render: ({ args, status }) => {
      if (status !== "complete") {
        return <div className="a2ui-pending">Generando tabla…</div>;
      }
      return <TableRenderer spec={args as unknown as TableSpec} />;
    },
  });

  useCopilotAction({
    name: "emit_markdown",
    description: "Renderiza un bloque de texto en Markdown.",
    parameters: [{ name: "content", type: "string", required: true }],
    render: ({ args, status }) => {
      if (status !== "complete") return null;
      return <MarkdownRenderer spec={args as unknown as MarkdownSpec} />;
    },
  });

  return null;
}
