from sqlalchemy.engine import Engine
from ..toolkit import PostgresToolKit
from ..prompts.planner import TABLE_SCHEMA_TEMPLATE_3, PLANER_PROMPT_2

from langchain_core.language_models.chat_models import BaseChatModel

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph


from src.logging_config import get_logger
logger = get_logger(module_name="planer", DIR="graph")



def create_planner_agent(llm_planner : BaseChatModel, engine : Engine) -> CompiledStateGraph:

    db_utils = PostgresToolKit(engine=engine)

    class State(TypedDict):
        # initial state
        topic : str
    
        doc : str
        plan : str

        input_tokens : int
        output_tokens : int
        api_calls : int
    

    def documenter_node(state : State):
        logger.info("xxx"*5 + " documenter_node " + "xxx"*5)

        url = engine.url
        logger.info(f"\n Usuario: {url.username} | Host: {url.host} | DB: {url.database} | Password: {url.password} \n")
        tables_name = db_utils.get_tables_name()
        logger.info(f"\n hay {len(tables_name)} tabas en la base de datos. 5 primeras tablas: \n\n {tables_name[:5]} \n")

        doc_tables = []
        schemas_dict = db_utils.get_all_tables_schema()
        for name in schemas_dict:
            logger.info(f"{name}")
            doc_tables.append(
                TABLE_SCHEMA_TEMPLATE_3.format(table_name=name, schema=schemas_dict[name])
            )
        
        doc = "\n\n".join(doc_tables)
        logger.debug(f"\n\n\n\n {doc}")
        return {"doc":doc, "input_tokens":0, "output_tokens":0, "api_calls":0}
    


    def planner_node(state : State) -> State:
        logger.info("xxx"*5 + " planner_node " + "xxx"*5)
        doc = state["doc"]
        topic = state["topic"]

        logger.info("ejecutando plan")
        prompt = PLANER_PROMPT_2.format(doc=doc, topic=topic)
        ai_message = llm_planner.invoke(prompt)

        input_tokens = ai_message.usage_metadata.get("input_tokens", 0)
        output_tokens = ai_message.usage_metadata.get("output_tokens", 0)
        api_calls = 1

        logger.info(f"\n input_tokens: {input_tokens}, output_tokens: {output_tokens}, api_calls: {api_calls}")
        logger.debug(f"\n\n\n {ai_message.content}")
        return {"plan":ai_message.content, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    

    builder = StateGraph(State)

    builder.add_node("documenter_node",documenter_node)
    builder.add_node("planner_node", planner_node)

    builder.add_edge(START, "documenter_node")
    builder.add_edge("documenter_node", "planner_node")
    builder.add_edge("planner_node", END)
    
    graph = builder.compile()

    return graph






if __name__=="__main__":

    from sqlalchemy import create_engine
    from langchain_google_genai import ChatGoogleGenerativeAI
    from src import settings
    from src.logging_config import setup_base_logging

    setup_base_logging()

    db_user = "postgres"
    db_pass = "postgres"
    db_host = "localhost"
    db_port = "5434"
    db_name = "northwind"

    topic = "ventas, clientes y empleados"

    conn_string = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(conn_string)

    model = "gemini-2.0-flash"
    llm_planner = ChatGoogleGenerativeAI(model=model, temperature=0.5, google_api_key=settings.GOOGLE_API_KEY)


    planner_agent = create_planner_agent(llm_planner=llm_planner, engine=engine)
    initial_state = {'topic':topic}
    agent_response = planner_agent.invoke(initial_state)

    plan = agent_response['plan']
    doc = agent_response['doc']


    path = settings.ROOT / "test" / "graphs_states" / "analyst" / "plan.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(plan)
    

    path = settings.ROOT / "test" / "graphs_states" / "analyst" / "doc.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(doc)
    
    

"""
python3 -m src.services.AnalystAgent.graph.plannerv1


"""




    