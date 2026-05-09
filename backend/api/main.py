"""Entry point FastAPI: monta CopilotKit runtime y healthcheck."""

from __future__ import annotations

from contextlib import asynccontextmanager

from copilotkit import CopilotKitSDK, LangGraphAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.api.deps import get_supervisor, shutdown
from backend.logging_config import setup_base_logging
from backend.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_base_logging()
    log = logger.bind(module="api")

    log.info("startup: construyendo supervisor")
    supervisor = await get_supervisor()

    sdk = CopilotKitSDK(
        agents=[
            LangGraphAgent(
                name="data_supervisor",
                description=(
                    "Pipeline de analítica de datos. Orquesta un agente analyst "
                    "(SQL + Pandas + Docling vía MCP) y un agente ui_builder que "
                    "emite componentes A2UI (charts, KPIs, tablas) inline en el chat."
                ),
                graph=supervisor,
            )
        ]
    )
    add_fastapi_endpoint(app, sdk, "/copilotkit")
    log.info("startup: listo")

    yield

    log.info("shutdown: liberando recursos")
    await shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title="Hakathon Data Analyst", version="0.1.0", lifespan=lifespan)

    origins = [o.strip() for o in settings.FRONTEND_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


"""
Run dev:
    uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

Endpoints:
    POST /copilotkit         CopilotKit runtime (chat + streaming)
    GET  /health
"""
