from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    DEEP_SEEK_API_KEY: Optional[str] = Field(default=None, alias="DEEP_SEEK_API_KEY")

    LOG_LEVEL: str = "INFO"

    # SQLAlchemy URL del Postgres por defecto que el analyst consulta
    # (independiente del MCP). Si None, el analyst no tendrá tools SQL nativas
    # y deberá apoyarse en MCP/archivos.
    DATA_DB_URL: Optional[str] = None

    # data-mcp (Pandas + Docling) — propio
    MCP_DATA_TRANSPORT: Literal["stdio", "sse"] = "stdio"
    MCP_DATA_COMMAND: str = "python"
    MCP_DATA_URL: str = "http://localhost:8765/sse"

    # Snowflake MCP (oficial: Snowflake-Labs/mcp). Las credenciales SNOWFLAKE_*
    # se inyectan al subproceso vía os.environ (heredado).
    MCP_SNOWFLAKE_ENABLED: bool = False
    MCP_SNOWFLAKE_TRANSPORT: Literal["stdio", "sse"] = "stdio"
    MCP_SNOWFLAKE_COMMAND: str = "uvx"
    MCP_SNOWFLAKE_ARGS: str = "mcp-server-snowflake"
    MCP_SNOWFLAKE_URL: str = ""

    # BigQuery / GCP MCP (community: mcp-server-bigquery). Credenciales vía
    # GOOGLE_APPLICATION_CREDENTIALS / GCP_PROJECT_ID en el env del proceso.
    MCP_BIGQUERY_ENABLED: bool = False
    MCP_BIGQUERY_TRANSPORT: Literal["stdio", "sse"] = "stdio"
    MCP_BIGQUERY_COMMAND: str = "uvx"
    MCP_BIGQUERY_ARGS: str = "mcp-server-bigquery"
    MCP_BIGQUERY_URL: str = ""

    # Frontend CORS (orígenes permitidos)
    FRONTEND_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def ROOT(self) -> Path:
        return ROOT


settings = Settings()


if __name__ == "__main__":
    print(f"ROOT: {settings.ROOT}")
