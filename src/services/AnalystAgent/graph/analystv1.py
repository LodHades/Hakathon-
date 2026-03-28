from sqlalchemy.engine import Engine
from ..toolkit import PostgresToolKit
from ..prompts.analyst import SQL_AGENT_SYSTEM_PROMPT_3, SHOULD_END_PROMPT_1

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, RemoveMessage
from langchain_core.output_parsers import JsonOutputParser

from langgraph.graph.state import CompiledStateGraph, StateGraph, START, END
from typing import TypedDict, Annotated, Sequence, Literal, Dict
from langgraph.graph import add_messages
from langgraph.prebuilt import ToolNode


from src.logging_config import get_logger
logger_analyst = get_logger(module_name="deep_queries", DIR="graph") # thinking_react
logger_querier = get_logger(module_name="thinking_react", DIR="graph")

def create_analyst_agent(llm_analyst : BaseChatModel, llm_querier : BaseChatModel, llm_halting : BaseChatModel, engine : Engine) -> CompiledStateGraph:
    toolkit = PostgresToolKit(engine=engine)
    tools = toolkit.get_tools()

    llm_querier_with_tools = llm_querier.bind_tools(tools)

    parser = JsonOutputParser()

    class State(TypedDict):
        messages_analyst : Annotated[Sequence[BaseMessage], add_messages]
        messages_ReAct : Annotated[Sequence[BaseMessage], add_messages]

        should_end : Dict
        input_tokens : int
        output_tokens : int
        api_calls : int
    
    # -------
    # -------

    tool_node_querier = ToolNode(tools=tools, messages_key="messages_ReAct")



    def initial_deep_query_node(state : State) -> State:
        logger_analyst.info("xxx"*5 + " initial_deep_query_node " + "xxx"*5)
        initial_messages = state["messages_analyst"]

        ai_message = llm_analyst.invoke(initial_messages)
        logger_analyst.info(f"\n {ai_message.pretty_repr()} \n")


        input_tokens = ai_message.usage_metadata.get("input_tokens", 0)
        output_tokens = ai_message.usage_metadata.get("output_tokens", 0)
        api_calls = 1
        logger_analyst.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")

        return {"messages_analyst":ai_message, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    



    def set_ReAct_messages_node(state : State) -> State:
        logger_querier.info("xxx"*5 + " set_ReAct_messages_node " + "xxx"*5 )
        logger_analyst.info("xxx"*5 + " set_ReAct_messages_node " + "xxx"*5)

        
        messages_ReAct = state["messages_ReAct"] # Aqui supongo que ya se reinico el estado messages_ReAct; es una lista vacia
        logger_querier.info(f"len messages_ReAct: {len(messages_ReAct)}")
        messages_ReAct.append(SystemMessage(content=SQL_AGENT_SYSTEM_PROMPT_3))

        ai_message = state["messages_analyst"][-1] # Esto es una query en lenguaje natural a una db
        analyst_message = HumanMessage(content=ai_message.content)
        logger_querier.info(f"\n {analyst_message.pretty_repr()} \n")
        messages_ReAct.append(analyst_message)

        return {"messages_ReAct":messages_ReAct}




    
    def querier_ReAct_node(state : State) -> State:
        logger_querier.info("xxx"*5 + " querier_ReAct_node " + "xxx"*5 )
        logger_analyst.info("xxx"*5 + " querier_ReAct_node " + "xxx"*5)

        input_tokens = state["input_tokens"]
        output_tokens = state["output_tokens"]
        api_calls = state["api_calls"]

        messages_ReAct = state["messages_ReAct"] 

        ai_message = llm_querier_with_tools.invoke(messages_ReAct) # llamada a tool o respuesta de la query
        logger_querier.info(f"\n {ai_message.pretty_repr()} \n")

        input_tokens += ai_message.usage_metadata.get("input_tokens", 0)
        output_tokens += ai_message.usage_metadata.get("output_tokens", 0)
        api_calls += 1
        logger_querier.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")

        return {"messages_ReAct":ai_message, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    


    def should_continue_with_sql(state : State) -> Literal["tool_node_wrapper", "clear_ReAct_messages_node"]:
        logger_querier.info("--"*5 + " should_continue_with_sql ")
        logger_analyst.info("--"*5 + " should_continue_with_sql ")

        last_ai_message = state["messages_ReAct"][-1]
        if last_ai_message.tool_calls:
            logger_querier.info("tool_node_wrapper")
            return "tool_node_wrapper"
        logger_querier.info("clear_ReAct_messages_node")
        logger_querier.info("\n"*10)
        return "clear_ReAct_messages_node"
    


    def tool_node_wrapper(state : State) -> State:
        logger_querier.info("xxx"*5 + " tool_node_wrapper " + "xxx"*5)
        logger_analyst.info("xxx"*5 + " tool_node_wrapper " + "xxx"*5)

        # tool_messages_dict será un dict como {"messages_react": [ToolMessage, ToolMessage, ...]}
        tool_messages_dict = tool_node_querier.invoke(state)
        for tool_message in tool_messages_dict["messages_ReAct"]:
            logger_querier.info(f"\n {tool_message.pretty_repr()} \n")
        
        return tool_messages_dict
    


    def clear_ReAct_messages_node(state : State) -> State:
        logger_analyst.info("xxx"*5 + " clear_ReAct_messages_node " + "xxx"*5)
        ai_message = state["messages_ReAct"][-1]
        messages = state["messages_ReAct"]

        querier_message = HumanMessage(content=ai_message.content)
        logger_analyst.info(f"\n {querier_message.pretty_repr()} \n")

        return {"messages_analyst":querier_message, "messages_ReAct":[RemoveMessage(id=m.id) for m in messages]}



    def deep_query_node(state : State) -> State:
        logger_analyst.info("xxx"*5 + " deep_query_node " + "xxx"*5)

        input_tokens = state["input_tokens"]
        output_tokens = state["output_tokens"]
        api_calls = state["api_calls"]

        messages_analyst = state["messages_analyst"]

        ai_message = llm_analyst.invoke(messages_analyst)
        logger_analyst.info(f"n {ai_message.pretty_repr()} \n")
        input_tokens += ai_message.usage_metadata.get("input_tokens", 0)
        output_tokens += ai_message.usage_metadata.get("output_tokens", 0)
        api_calls += 1
        logger_analyst.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")

        return {"messages_analyst":ai_message, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}


    
    def should_end_node(state : State) -> State:
        logger_analyst.info("xxx"*5 + " deep_query_node " + "xxx"*5)

        input_tokens = state["input_tokens"]
        output_tokens = state["output_tokens"]
        api_calls = state["api_calls"]

        last_analyst_message = state["messages_analyst"][-1].content
        prompt = SHOULD_END_PROMPT_1.format(tex=last_analyst_message)

        ai_message = llm_halting.invoke(prompt)
        input_tokens += ai_message.usage_metadata.get("input_tokens", 0)
        output_tokens += ai_message.usage_metadata.get("output_tokens", 0)
        api_calls += 1

        json = parser.parse(ai_message.content)
        logger_analyst.info(f"json: \n {json} \n")

        logger_analyst.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")

        return {"should_end":json, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    


    def should_end(state : State) -> Literal["set_ReAct_messages_node", END]: # type: ignore
        logger_analyst.info("---"*5 + " deep_query_node ")
        should_end_dict = state["should_end"]
        
        if should_end_dict["query"]:
            logger_analyst.info("set_ReAct_messages_node")
            return "set_ReAct_messages_node"
        else:
            logger_analyst.info("END")
            return END


    # -------
    # -------


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

    graph = builder.compile()

    return graph


        


if __name__ == "__main__":

    from src.services.AnalystAgent.prompts import analyst
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_groq import ChatGroq
    from sqlalchemy import create_engine
    from src import settings
    from src.logging_config import setup_base_logging

    setup_base_logging()

    db_user = "postgres"
    db_pass = "postgres"
    db_host = "localhost"
    db_port = "5434"
    db_name = "northwind"

    conn_string = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(conn_string)

    model = "gemini-2.0-flash"
    llm_analyst = ChatGoogleGenerativeAI(model=model, temperature=0.5, google_api_key=settings.GOOGLE_API_KEY)

    model = "openai/gpt-oss-120b"
    llm_querier = ChatGroq(model=model, temperature=0.1, api_key=settings.GROQ_API_KEY)

    model = "openai/gpt-oss-120b"
    llm_halting = ChatGroq(model=model, temperature=0.1, api_key=settings.GROQ_API_KEY)

    analyst_agent = create_analyst_agent(llm_analyst=llm_analyst, llm_querier=llm_querier, llm_halting=llm_halting, engine=engine)

    # image_data = analyst_agent.get_graph().draw_mermaid_png()
    # with open("analyst.png", "wb") as image_file:
    #     image_file.write(image_data)


    path = settings.ROOT / "test" / "graphs_states" / "analyst" / "plan.md"
    with open(path, 'r', encoding='utf-8') as f:
        plan = f.read()
    
    topic = "ventas, clientes y empleados"
    messages = [
        SystemMessage(content=analyst.SYSTEM_DEEP_QUERIES_PROMPT_3.format(topic=topic, plan=plan)),
        HumanMessage(content=analyst.HUMAN_DEEP_QUERIES_PROMPT_2.format(topic=topic))
    ]

    initial_state = {'messages_analyst':messages}
    agent_response = analyst_agent.invoke(initial_state)
    analysis = agent_response['messages_analyst']

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
    analysis = doc

    path = settings.ROOT / "test" / "graphs_states" / "analyst" / "analysis.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(analysis)

    

"""
python3 -m src.services.AnalystAgent.graph.analystv1.


"""