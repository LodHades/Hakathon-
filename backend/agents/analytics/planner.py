from typing import TypedDict

from langchain_community.utilities import SQLDatabase
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.engine import Engine

from backend.logging_config import get_logger

from .prompts.planner import PLANER_PROMPT_2, TABLE_SCHEMA_TEMPLATE_3


logger = get_logger(module_name="planer", DIR="graph")


def create_planner_agent(llm_planner: BaseChatModel, engine: Engine) -> CompiledStateGraph:
    """`engine` es el sync `Engine`. Si vienes de un `AsyncEngine`, pasa
    `async_engine.sync_engine` (langchain SQLDatabase requiere sync para
    introspección; con asyncpg el shim de greenlet maneja la ejecución).
    """
    db = SQLDatabase(engine=engine)

    class State(TypedDict):
        topic: str

        doc: str
        plan: str

        input_tokens: int
        output_tokens: int
        api_calls: int

    async def documenter_node(state: State) -> dict:
        logger.info("xxx" * 5 + " documenter_node " + "xxx" * 5)

        url = engine.url
        logger.info(f"\n Usuario: {url.username} | Host: {url.host} | DB: {url.database} \n")
        tables_name = db.get_usable_table_names()
        logger.info(
            f"\n hay {len(tables_name)} tablas en la base de datos. 5 primeras: \n\n {tables_name[:5]} \n"
        )

        doc_tables = []
        for name in tables_name:
            logger.info(f"{name}")
            doc_tables.append(
                TABLE_SCHEMA_TEMPLATE_3.format(table_name=name, schema=db.get_table_info([name]))
            )

        doc = "\n\n".join(doc_tables)
        logger.debug(f"\n\n\n\n {doc}")
        return {"doc": doc, "input_tokens": 0, "output_tokens": 0, "api_calls": 0}

    async def planner_node(state: State) -> dict:
        logger.info("xxx" * 5 + " planner_node " + "xxx" * 5)
        doc = state["doc"]
        topic = state["topic"]

        prompt = PLANER_PROMPT_2.format(doc=doc, topic=topic)
        ai_message = await llm_planner.ainvoke(prompt)

        input_tokens = (ai_message.usage_metadata or {}).get("input_tokens", 0)
        output_tokens = (ai_message.usage_metadata or {}).get("output_tokens", 0)
        api_calls = 1

        logger.info(
            f"\n input_tokens: {input_tokens}, output_tokens: {output_tokens}, api_calls: {api_calls}"
        )
        logger.debug(f"\n\n\n {ai_message.content}")
        return {
            "plan": ai_message.content,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "api_calls": api_calls,
        }

    builder = StateGraph(State)
    builder.add_node("documenter_node", documenter_node)
    builder.add_node("planner_node", planner_node)
    builder.add_edge(START, "documenter_node")
    builder.add_edge("documenter_node", "planner_node")
    builder.add_edge("planner_node", END)
    return builder.compile()


if __name__ == "__main__":
    import asyncio

    from langchain_google_genai import ChatGoogleGenerativeAI
    from sqlalchemy.ext.asyncio import create_async_engine

    from backend.logging_config import setup_base_logging
    from backend.settings import settings

    setup_base_logging()

    topic = "ventas, clientes y empleados"
    async_engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5434/northwind"
    )

    llm_planner = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", temperature=0.5, google_api_key=settings.GOOGLE_API_KEY
    )

    planner_agent = create_planner_agent(
        llm_planner=llm_planner, engine=async_engine.sync_engine
    )

    async def main():
        agent_response = await planner_agent.ainvoke({"topic": topic})

        plan = agent_response["plan"]
        doc = agent_response["doc"]

        plan_path = settings.ROOT / "test" / "graphs_states" / "analyst" / "plan.md"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(plan, encoding="utf-8")

        doc_path = settings.ROOT / "test" / "graphs_states" / "analyst" / "doc.md"
        doc_path.write_text(doc, encoding="utf-8")

        await async_engine.dispose()

    asyncio.run(main())


"""
python -m backend.agents.analytics.planner
"""
