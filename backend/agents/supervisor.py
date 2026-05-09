"""Supervisor LangGraph que orquesta AnalyticsAgent + UIBuilderAgent.

Cada agente existente tiene un estado custom (analytics: `messages_analyst` +
`messages_ReAct`; ui_builder: `analysis` + `messages`). `create_supervisor`
del paquete oficial `langgraph_supervisor` espera subagentes que expongan un
estado con `messages`. Para conciliar:

- Envolvemos cada agente en un subgrafo de adaptación (`build_*_subgraph`)
  que: lee el contexto desde `messages` del supervisor, invoca el agente
  interno con su estado nativo, y vuelca el resultado a `messages` + campos
  custom del estado del supervisor.

- El estado del supervisor extiende `messages` con `analysis` (texto
  intermedio del analyst) y `ui_components` (lista de specs A2UI emitidas
  por el ui_builder). El frontend lee `ui_components` para renderizar.
"""

from __future__ import annotations

import json
from operator import add
from typing import Annotated, Sequence, TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph_supervisor import create_supervisor

from backend.agents.analytics.prompts.analyst import (
    HUMAN_DEEP_QUERIES_PROMPT_2,
    SYSTEM_DEEP_QUERIES_PROMPT_3,
)
from backend.logging_config import get_logger


logger = get_logger(module_name="supervisor", DIR="graph")


class SupervisorState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    analysis: str
    ui_components: Annotated[list[dict], add]


SUPERVISOR_PROMPT = """\
Eres el supervisor de un sistema de análisis de datos con dos agentes especializados:

1. `analytics`: analista que consulta bases de datos SQL y archivos (CSV/JSON/PDF) y produce
   un análisis textual con hallazgos clave, citas y conclusiones.
2. `ui_builder`: diseñador de UI que toma el análisis de `analytics` y emite componentes A2UI
   (gráficos, KPIs, tablas, markdown) para renderizar en el chat.

Flujo típico:
- Pregunta de datos del usuario → transferir a `analytics`.
- Cuando `analytics` regrese con un análisis → transferir a `ui_builder` para renderizar visuales.
- Cuando `ui_builder` termine → finalizar con un mensaje de cierre breve para el usuario.

No hagas el trabajo de los agentes tú mismo: solo decide a quién transferir.
"""


def _last_human_content(messages: Sequence[BaseMessage]) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            return str(m.content)
    return ""


def build_analytics_subgraph(
    planner_agent: CompiledStateGraph,
    analyst_agent: CompiledStateGraph,
) -> CompiledStateGraph:
    """Subgrafo que: extrae el topic del último HumanMessage, corre planner +
    analyst con su estado nativo, y devuelve el análisis como AIMessage(name=analytics)
    además de poblar `analysis` en el estado del supervisor.
    """

    async def run_node(state: SupervisorState) -> dict:
        topic = _last_human_content(state["messages"])
        if not topic:
            logger.warning("analytics_subgraph: no HumanMessage en historia")
            return {
                "messages": [
                    AIMessage(content="No encontré una pregunta concreta para analizar.", name="analytics")
                ]
            }

        logger.info(f"analytics topic={topic!r}")
        plan_state = await planner_agent.ainvoke({"topic": topic})
        plan = plan_state["plan"]

        analyst_init = {
            "messages_analyst": [
                SystemMessage(content=SYSTEM_DEEP_QUERIES_PROMPT_3.format(topic=topic, plan=plan)),
                HumanMessage(content=HUMAN_DEEP_QUERIES_PROMPT_2.format(topic=topic)),
            ]
        }
        result = await analyst_agent.ainvoke(analyst_init)
        analysis = result["messages_analyst"][-1].content

        return {
            "messages": [AIMessage(content=analysis, name="analytics")],
            "analysis": analysis,
        }

    builder = StateGraph(SupervisorState)
    builder.add_node("run", run_node)
    builder.add_edge(START, "run")
    builder.add_edge("run", END)
    return builder.compile(name="analytics")


def build_ui_builder_subgraph(ui_agent: CompiledStateGraph) -> CompiledStateGraph:
    """Subgrafo que: toma `analysis` del estado supervisor, invoca al ui_builder
    interno y recolecta las specs A2UI emitidas (ToolMessages) en `ui_components`.
    Devuelve un mensaje resumen al chat.
    """

    async def run_node(state: SupervisorState) -> dict:
        analysis = state.get("analysis") or ""
        if not analysis:
            logger.warning("ui_builder_subgraph: estado sin `analysis`")
            return {
                "messages": [
                    AIMessage(
                        content="No hay análisis previo del que generar componentes.",
                        name="ui_builder",
                    )
                ]
            }

        logger.info(f"ui_builder analysis_len={len(analysis)}")
        result = await ui_agent.ainvoke({"analysis": analysis})

        components: list[dict] = []
        for m in result["messages"]:
            if m.type == "tool":
                try:
                    components.append(json.loads(m.content))
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"tool message no parseable: {m.content[:120]!r}")

        breakdown = ", ".join(sorted({c.get("a2ui", "?") for c in components})) or "ninguno"
        summary = f"Generé {len(components)} componentes A2UI ({breakdown})."

        return {
            "messages": [AIMessage(content=summary, name="ui_builder")],
            "ui_components": components,
        }

    builder = StateGraph(SupervisorState)
    builder.add_node("run", run_node)
    builder.add_edge(START, "run")
    builder.add_edge("run", END)
    return builder.compile(name="ui_builder")


def build_supervisor(
    supervisor_llm: BaseChatModel,
    planner_agent: CompiledStateGraph,
    analyst_agent: CompiledStateGraph,
    ui_agent: CompiledStateGraph,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """Construye el grafo supervisor que orquesta analytics + ui_builder.

    `checkpointer` opcional para conversaciones multi-turno con `thread_id`.
    """
    analytics_sub = build_analytics_subgraph(planner_agent, analyst_agent)
    ui_sub = build_ui_builder_subgraph(ui_agent)

    workflow = create_supervisor(
        agents=[analytics_sub, ui_sub],
        model=supervisor_llm,
        prompt=SUPERVISOR_PROMPT,
        state_schema=SupervisorState,
    )
    return workflow.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    import asyncio
    from pathlib import Path

    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_groq import ChatGroq
    from sqlalchemy.ext.asyncio import create_async_engine

    from backend.agents.analytics.graph import create_analyst_agent
    from backend.agents.analytics.planner import create_planner_agent
    from backend.agents.ui_builder.graph import create_ui_builder_agent
    from backend.logging_config import setup_base_logging
    from backend.settings import settings
    from backend.toolkits.mcp_client import build_default_client

    setup_base_logging()

    async_engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5434/northwind"
    )

    llm_planner = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", temperature=0.5, google_api_key=settings.GOOGLE_API_KEY
    )
    llm_analyst = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", temperature=0.5, google_api_key=settings.GOOGLE_API_KEY
    )
    llm_querier = ChatGroq(model="openai/gpt-oss-120b", temperature=0.1, api_key=settings.GROQ_API_KEY)
    llm_halting = ChatGroq(model="openai/gpt-oss-120b", temperature=0.1, api_key=settings.GROQ_API_KEY)
    llm_ui = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", temperature=0.4, google_api_key=settings.GOOGLE_API_KEY
    )
    llm_supervisor = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", temperature=0.0, google_api_key=settings.GOOGLE_API_KEY
    )

    async def main():
        mcp_tools = await build_default_client().get_tools()

        planner = create_planner_agent(
            llm_planner=llm_planner, engine=async_engine.sync_engine
        )
        analyst = create_analyst_agent(
            llm_analyst=llm_analyst,
            llm_querier=llm_querier,
            llm_halting=llm_halting,
            engine=async_engine.sync_engine,
            extra_tools=mcp_tools,
        )
        ui_builder = create_ui_builder_agent(llm=llm_ui)

        supervisor = build_supervisor(
            supervisor_llm=llm_supervisor,
            planner_agent=planner,
            analyst_agent=analyst,
            ui_agent=ui_builder,
        )

        initial = {
            "messages": [
                HumanMessage(
                    content="Analiza ventas, clientes y empleados de la base de datos northwind y dame un dashboard."
                )
            ],
        }
        final = await supervisor.ainvoke(initial)

        out_dir = Path(settings.ROOT) / "test" / "graphs_states" / "supervisor"
        out_dir.mkdir(parents=True, exist_ok=True)

        with open(out_dir / "messages.txt", "w", encoding="utf-8") as f:
            for m in final["messages"]:
                f.write(f"--- {m.type}{f' (name={m.name})' if getattr(m, 'name', None) else ''} ---\n")
                f.write(str(m.content))
                f.write("\n\n")

        with open(out_dir / "components.json", "w", encoding="utf-8") as f:
            json.dump(final.get("ui_components", []), f, indent=2, ensure_ascii=False)

        print(f"OK -> {out_dir}")
        await async_engine.dispose()

    asyncio.run(main())


"""
python -m backend.agents.supervisor
"""
