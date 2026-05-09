import type { TableSpec } from "./types";

export function TableRenderer({ spec }: { spec: TableSpec }) {
  const { title, columns, rows, description } = spec;
  return (
    <div className="a2ui-card">
      <h3>{title}</h3>
      {description && <p className="desc">{description}</p>}
      <div style={{ overflowX: "auto" }}>
        <table className="a2ui-table">
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, ri) => (
              <tr key={ri}>
                {row.map((cell, ci) => (
                  <td key={ci}>{String(cell ?? "")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
