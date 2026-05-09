"""Dependency injection del backend.

Construye una sola vez el supervisor + sus dependencias (LLMs, engine SQL,
MCP tools) y lo expone como singleton async-friendly.
"""

from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from backend.agents.analytics.graph import create_analyst_agent
from backend.agents.analytics.planner import create_planner_agent
from backend.agents.supervisor import build_supervisor
from backend.agents.ui_builder.graph import create_ui_builder_agent
from backend.settings import settings
from backend.toolkits.mcp_client import build_default_client


_supervisor: CompiledStateGraph | None = None
_async_engine: AsyncEngine | None = None


async def get_supervisor() -> CompiledStateGraph:
    """Construye (o retorna) el supervisor compilado."""
    global _supervisor, _async_engine
    if _supervisor is not None:
        return _supervisor

    log = logger.bind(module="deps")
    log.info("inicializando supervisor + sub-agentes")

    if not settings.GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY no está configurada")
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY no está configurada")
    if not settings.DATA_DB_URL:
        raise RuntimeError("DATA_DB_URL no está configurada")

    llm_planner = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", temperature=0.5, google_api_key=settings.GOOGLE_API_KEY
    )
    llm_analyst = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", temperature=0.5, google_api_key=settings.GOOGLE_API_KEY
    )
    llm_querier = ChatGroq(
        model="openai/gpt-oss-120b", temperature=0.1, api_key=settings.GROQ_API_KEY
    )
    llm_halting = ChatGroq(
        model="openai/gpt-oss-120b", temperature=0.1, api_key=settings.GROQ_API_KEY
    )
    llm_ui = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", temperature=0.4, google_api_key=settings.GOOGLE_API_KEY
    )
    llm_supervisor = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", temperature=0.0, google_api_key=settings.GOOGLE_API_KEY
    )

    # Engine async (asyncpg). El `.sync_engine` se pasa a SQLDatabase porque
    # langchain requiere sync para introspección; con asyncpg el shim de
    # greenlet maneja la ejecución de queries debajo.
    _async_engine = create_async_engine(settings.DATA_DB_URL)
    sync_engine = _async_engine.sync_engine

    log.info("conectando MCP y descargando tools")
    mcp_tools = await build_default_client().get_tools()
    log.info(f"MCP tools cargadas: {[t.name for t in mcp_tools]}")

    planner = create_planner_agent(llm_planner=llm_planner, engine=sync_engine)
    analyst = create_analyst_agent(
        llm_analyst=llm_analyst,
        llm_querier=llm_querier,
        llm_halting=llm_halting,
        engine=sync_engine,
        extra_tools=mcp_tools,
    )
    ui_builder = create_ui_builder_agent(llm=llm_ui)

    _supervisor = build_supervisor(
        supervisor_llm=llm_supervisor,
        planner_agent=planner,
        analyst_agent=analyst,
        ui_agent=ui_builder,
        checkpointer=MemorySaver(),
    )
    log.info("supervisor listo")
    return _supervisor


async def shutdown() -> None:
    """Liberar recursos (engine async) en el shutdown del FastAPI."""
    global _async_engine
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
