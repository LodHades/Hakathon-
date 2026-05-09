"""UIBuilderAgent: recibe un análisis y emite componentes A2UI.

Loop ReAct simple:
- `prepare_node`: inyecta system + human (con el análisis) en `messages`.
- `builder_node`: invoca al LLM con tools de a2ui.
- `tool_node`: ejecuta las tool calls (devuelven specs A2UI serializadas).
- Termina cuando el LLM responde sin tool calls.

Los componentes emitidos quedan en los `ToolMessage`s del state. El supervisor
o caller los recolecta vía streaming (`astream_events`) para que CopilotKit
los renderice inline.
"""

from __future__ import annotations

from typing import Annotated, Literal, Optional, Sequence, TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools.base import BaseTool
from langgraph.graph import START, StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from backend.logging_config import get_logger

from .a2ui_tools import get_ui_tools
from .prompts import UI_BUILDER_SYSTEM_PROMPT


logger = get_logger(module_name="ui_builder", DIR="graph")


class UIBuilderState(TypedDict):
    analysis: str
    messages: Annotated[Sequence[BaseMessage], add_messages]

    input_tokens: int
    output_tokens: int
    api_calls: int


def create_ui_builder_agent(
    llm: BaseChatModel,
    extra_tools: Optional[list[BaseTool]] = None,
) -> CompiledStateGraph:
    tools = get_ui_tools() + list(extra_tools or [])
    llm_with_tools = llm.bind_tools(tools)
    tool_node = ToolNode(tools=tools, messages_key="messages")

    async def prepare_node(state: UIBuilderState) -> dict:
        logger.info("xxx" * 5 + " prepare_node " + "xxx" * 5)
        sys_msg = SystemMessage(content=UI_BUILDER_SYSTEM_PROMPT)
        human_msg = HumanMessage(
            content=f"### Análisis a visualizar\n\n{state['analysis']}"
        )
        return {
            "messages": [sys_msg, human_msg],
            "input_tokens": 0,
            "output_tokens": 0,
            "api_calls": 0,
        }

    async def builder_node(state: UIBuilderState) -> dict:
        logger.info("xxx" * 5 + " builder_node " + "xxx" * 5)
        ai_message = await llm_with_tools.ainvoke(state["messages"])
        logger.info(f"\n {ai_message.pretty_repr()} \n")

        usage = getattr(ai_message, "usage_metadata", None) or {}
        input_tokens = state["input_tokens"] + usage.get("input_tokens", 0)
        output_tokens = state["output_tokens"] + usage.get("output_tokens", 0)
        api_calls = state["api_calls"] + 1
        logger.info(f"input_tokens={input_tokens} output_tokens={output_tokens} api_calls={api_calls}")

        return {
            "messages": [ai_message],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "api_calls": api_calls,
        }

    def should_continue(state: UIBuilderState) -> Literal["tool_node", "__end__"]:
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tool_node"
        return "__end__"

    builder = StateGraph(UIBuilderState)
    builder.add_node("prepare_node", prepare_node)
    builder.add_node("builder_node", builder_node)
    builder.add_node("tool_node", tool_node)

    builder.add_edge(START, "prepare_node")
    builder.add_edge("prepare_node", "builder_node")
    builder.add_conditional_edges("builder_node", should_continue)
    builder.add_edge("tool_node", "builder_node")

    return builder.compile()


if __name__ == "__main__":
    import asyncio
    import json

    from langchain_google_genai import ChatGoogleGenerativeAI

    from backend.logging_config import setup_base_logging
    from backend.settings import settings

    setup_base_logging()

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.4,
        google_api_key=settings.GOOGLE_API_KEY,
    )

    analysis_path = settings.ROOT / "test" / "graphs_states" / "analyst" / "analysis.md"
    if analysis_path.exists():
        analysis = analysis_path.read_text(encoding="utf-8")
    else:
        analysis = (
            "Las ventas totales fueron $1,265,793 con un pico en abril 1998. "
            "El cliente principal aporta el 12% del ingreso y la categoría top "
            "es 'Beverages' con 25% del total."
        )

    async def main():
        agent = create_ui_builder_agent(llm=llm)
        final = await agent.ainvoke({"analysis": analysis})

        components = []
        for m in final["messages"]:
            if m.type == "tool":
                try:
                    components.append(json.loads(m.content))
                except Exception:
                    pass

        out_path = settings.ROOT / "test" / "graphs_states" / "ui_builder" / "components.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(components, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{len(components)} componentes -> {out_path}")

    asyncio.run(main())


"""
python -m backend.agents.ui_builder.graph
"""
