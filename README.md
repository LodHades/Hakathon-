# MED-data-analyst-agent
Agente para análisis de datos (FastAPI + CopilotKit + LangGraph) con tools vía MCP:

- `mcp_server`: Pandas + Docling (server propio)
- Snowflake (opcional, MCP externo vía `uvx mcp-server-snowflake`)
- BigQuery/GCP (opcional, MCP externo vía `uvx mcp-server-bigquery`)

## Levantar con Docker
1) Copia `.env.example` a `.env` y completa `GOOGLE_API_KEY` y `GROQ_API_KEY`.
2) Levanta servicios:

`docker compose up --build`

3) Abre:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`

## MCP Snowflake / BigQuery (opcional)
El backend puede lanzar estos MCPs como subprocesos (transport `stdio`) si:

- `MCP_SNOWFLAKE_ENABLED=true` y credenciales `SNOWFLAKE_*` configuradas
- `MCP_BIGQUERY_ENABLED=true` y `GCP_PROJECT_ID` + `GOOGLE_APPLICATION_CREDENTIALS` configuradas

Nota: si usas `GOOGLE_APPLICATION_CREDENTIALS`, monta el archivo JSON en el contenedor (por ejemplo con un volume).
