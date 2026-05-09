from typing import Annotated, Dict, Literal, Optional, Sequence, TypedDict

from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, RemoveMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools.base import BaseTool
from langgraph.graph import add_messages
from langgraph.graph.state import START, CompiledStateGraph, StateGraph
from langgraph.prebuilt import ToolNode
from sqlalchemy.engine import Engine

from backend.logging_config import get_logger

from .prompts.analyst import SHOULD_END_PROMPT_1, SQL_AGENT_SYSTEM_PROMPT_3


logger_analyst = get_logger(module_name="deep_queries", DIR="graph")
logger_querier = get_logger(module_name="thinking_react", DIR="graph")


def create_analyst_agent(
    llm_analyst: BaseChatModel,
    llm_querier: BaseChatModel,
    llm_halting: BaseChatModel,
    engine: Engine,
    extra_tools: Optional[list[BaseTool]] = None,
) -> CompiledStateGraph:
    """`engine` debe ser sync. Si vienes de `AsyncEngine`, pasa
    `async_engine.sync_engine` (langchain SQLDatabase requiere sync para
    introspección; con asyncpg el shim de greenlet maneja la ejecución).
    """
    db = SQLDatabase(engine=engine)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm_querier)
    tools = toolkit.get_tools() + list(extra_tools or [])
    logger_querier.info(f"querier tools: {[t.name for t in tools]}")

    llm_querier_with_tools = llm_querier.bind_tools(tools)
    parser = JsonOutputParser()

    class State(TypedDict):
        messages_analyst: Annotated[Sequence[BaseMessage], add_messages]
        messages_ReAct: Annotated[Sequence[BaseMessage], add_messages]

        should_end: Dict
        input_tokens: int
        output_tokens: int
        api_calls: int

    tool_node_querier = ToolNode(tools=tools, messages_key="messages_ReAct")

    async def initial_deep_query_node(state: State) -> dict:
        logger_analyst.info("xxx" * 5 + " initial_deep_query_node " + "xxx" * 5)
        ai_message = await llm_analyst.ainvoke(state["messages_analyst"])
        logger_analyst.info(f"\n {ai_message.pretty_repr()} \n")

        usage = ai_message.usage_metadata or {}
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        api_calls = 1
        logger_analyst.info(
            f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}"
        )

        return {
            "messages_analyst": ai_message,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "api_calls": api_calls,
        }

    async def set_ReAct_messages_node(state: State) -> dict:
        logger_querier.info("xxx" * 5 + " set_ReAct_messages_node " + "xxx" * 5)

        messages_ReAct = list(state["messages_ReAct"])
        messages_ReAct.append(SystemMessage(content=SQL_AGENT_SYSTEM_PROMPT_3))

        ai_message = state["messages_analyst"][-1]
        analyst_message = HumanMessage(content=ai_message.content)
        logger_querier.info(f"\n {analyst_message.pretty_repr()} \n")
        messages_ReAct.append(analyst_message)

        return {"messages_ReAct": messages_ReAct}

    async def querier_ReAct_node(state: State) -> dict:
        logger_querier.info("xxx" * 5 + " querier_ReAct_node " + "xxx" * 5)

        ai_message = await llm_querier_with_tools.ainvoke(state["messages_ReAct"])
        logger_querier.info(f"\n {ai_message.pretty_repr()} \n")

        usage = ai_message.usage_metadata or {}
        input_tokens = state["input_tokens"] + usage.get("input_tokens", 0)
        output_tokens = state["output_tokens"] + usage.get("output_tokens", 0)
        api_calls = state["api_calls"] + 1
        logger_querier.info(
            f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}"
        )

        return {
            "messages_ReAct": ai_message,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "api_calls": api_calls,
        }

    def should_continue_with_sql(
        state: State,
    ) -> Literal["tool_node_wrapper", "clear_ReAct_messages_node"]:
        last = state["messages_ReAct"][-1]
        if last.tool_calls:
            return "tool_node_wrapper"
        return "clear_ReAct_messages_node"

    async def tool_node_wrapper(state: State) -> dict:
        logger_querier.info("xxx" * 5 + " tool_node_wrapper " + "xxx" * 5)
        tool_messages_dict = await tool_node_querier.ainvoke(state)
        for tool_message in tool_messages_dict["messages_ReAct"]:
            logger_querier.info(f"\n {tool_message.pretty_repr()} \n")
        return tool_messages_dict

    async def clear_ReAct_messages_node(state: State) -> dict:
        logger_analyst.info("xxx" * 5 + " clear_ReAct_messages_node " + "xxx" * 5)
        ai_message = state["messages_ReAct"][-1]
        messages = state["messages_ReAct"]

        querier_message = HumanMessage(content=ai_message.content)
        logger_analyst.info(f"\n {querier_message.pretty_repr()} \n")

        return {
            "messages_analyst": querier_message,
            "messages_ReAct": [RemoveMessage(id=m.id) for m in messages],
        }

    async def deep_query_node(state: State) -> dict:
        logger_analyst.info("xxx" * 5 + " deep_query_node " + "xxx" * 5)

        ai_message = await llm_analyst.ainvoke(state["messages_analyst"])
        logger_analyst.info(f"\n {ai_message.pretty_repr()} \n")

        usage = ai_message.usage_metadata or {}
        input_tokens = state["input_tokens"] + usage.get("input_tokens", 0)
        output_tokens = state["output_tokens"] + usage.get("output_tokens", 0)
        api_calls = state["api_calls"] + 1
        logger_analyst.info(
            f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}"
        )

        return {
            "messages_analyst": ai_message,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "api_calls": api_calls,
        }

    async def should_end_node(state: State) -> dict:
        logger_analyst.info("xxx" * 5 + " should_end_node " + "xxx" * 5)

        last_analyst_message = state["messages_analyst"][-1].content
        prompt = SHOULD_END_PROMPT_1.format(tex=last_analyst_message)

        ai_message = await llm_halting.ainvoke(prompt)
        usage = ai_message.usage_metadata or {}
        input_tokens = state["input_tokens"] + usage.get("input_tokens", 0)
        output_tokens = state["output_tokens"] + usage.get("output_tokens", 0)
        api_calls = state["api_calls"] + 1

        parsed = parser.parse(ai_message.content)
        logger_analyst.info(f"json: \n {parsed} \n")

        return {
            "should_end": parsed,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "api_calls": api_calls,
        }

    def should_end(state: State) -> Literal["set_ReAct_messages_node", "__end__"]:
        if state["should_end"]["query"]:
            return "set_ReAct_messages_node"
        return "__end__"

    builder = StateGraph(State)
    builder.add_node("initial_deep_query_node", initial_deep_query_node)
    builder.add_node("set_ReAct_messages_node", set_ReAct_messages_node)
    builder.add_node("querier_ReAct_node", querier_ReAct_node)
    builder.add_node("tool_node_wrapper", tool_node_wrapper)
    builder.add_node("clear_ReAct_messages_node", clear_ReAct_messages_node)
    builder.add_node("deep_query_node", deep_query_node)
    builder.add_node("should_end_node", should_end_node)

    builder.add_edge(START, "initial_deep_query_node")
    builder.add_edge("initial_deep_query_node", "set_ReAct_messages_node")
    builder.add_edge("set_ReAct_messages_node", "querier_ReAct_node")
    builder.add_conditional_edges("querier_ReAct_node", should_continue_with_sql)
    builder.add_edge("tool_node_wrapper", "querier_ReAct_node")
    builder.add_edge("clear_ReAct_messages_node", "deep_query_node")
    builder.add_edge("deep_query_node", "should_end_node")
    builder.add_conditional_edges("should_end_node", should_end)

    return builder.compile()


if __name__ == "__main__":
    import asyncio

    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_groq import ChatGroq
    from sqlalchemy.ext.asyncio import create_async_engine

    from backend.agents.analytics.prompts import analyst
    from backend.logging_config import setup_base_logging
    from backend.settings import settings
    from backend.toolkits.mcp_client import build_default_client

    setup_base_logging()

    async_engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5434/northwind"
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

    async def main():
        mcp_tools = await build_default_client().get_tools()

        analyst_agent = create_analyst_agent(
            llm_analyst=llm_analyst,
            llm_querier=llm_querier,
            llm_halting=llm_halting,
            engine=async_engine.sync_engine,
            extra_tools=mcp_tools,
        )

        plan_path = settings.ROOT / "test" / "graphs_states" / "analyst" / "plan.md"
        plan = plan_path.read_text(encoding="utf-8")

        topic = "ventas, clientes y empleados"
        messages = [
            SystemMessage(
                content=analyst.SYSTEM_DEEP_QUERIES_PROMPT_3.format(topic=topic, plan=plan)
            ),
            HumanMessage(content=analyst.HUMAN_DEEP_QUERIES_PROMPT_2.format(topic=topic)),
        ]

        agent_response = await analyst_agent.ainvoke({"messages_analyst": messages})
        analysis = agent_response["messages_analyst"]

        doc = ""
        for i in range(2, len(analysis)):
            if i % 2 == 0:
                doc += "**Mensaje del analista** \n\n"
                doc += analysis[i].content
                doc += "\n\n ---\n\n"
            else:
                doc += "**Mensaje del asistente** \n\n"
                doc += analysis[i].content
                doc += "\n\n --- \n\n"

        out_path = settings.ROOT / "test" / "graphs_states" / "analyst" / "analysis.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(doc, encoding="utf-8")

        await async_engine.dispose()

    asyncio.run(main())


"""
python -m backend.agents.analytics.graph
"""
