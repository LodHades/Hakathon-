from typing import List, Dict, Any
from ..prompts.dashboard import PANELS_DESCRIPTION_PROMPT_1, REPORT_PARSER_PROMPT_1, GET_TABLES_FROM_CHART_PROMPT_2, JSON_CHART_GRAFANA_PROMPT_8
from sqlalchemy.engine import Engine
from src.services.AnalystAgent.toolkit import PostgresToolKit # TODO: quizas PostgresToolKit debe ser una classe mas general
import asyncio 

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser

from langgraph.graph.state import CompiledStateGraph
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

from src.logging_config import get_logger
logger = get_logger(module_name="grafana", DIR='graph')

parser = JsonOutputParser()



async def get_tables_from_description(semaphore, description : str, llm_information_structurer : BaseChatModel, prompt : str):
    logger.info("--- get_tables_from_description")
    async with semaphore:
        try:
            ai_response = await llm_information_structurer.ainvoke(prompt)
            logger.info(f"\n {ai_response.content} \n")
            tables_name = parser.parse(ai_response.content)
            tables_name = tables_name['tables']


            input_tokens = ai_response.usage_metadata.get("input_tokens", 0)
            output_tokens = ai_response.usage_metadata.get("output_tokens", 0)
            logger.info("\n"*3)

            return {'tables_name':tables_name, 'description':description, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":1}
        except Exception as e:
            logger.error(f"{e}")
            return None
        

async def get_json_panel(semaphore ,llm_grafana_expert : BaseChatModel, prompt : str):
    logger.info("--- get_json_panel")
    async with semaphore:
        try:
            ai_response = await llm_grafana_expert.ainvoke(prompt)
            logger.info(f"\n {ai_response.content} \n")
            json_panel = parser.parse(ai_response.content)

            input_tokens = ai_response.usage_metadata.get("input_tokens", 0)
            output_tokens = ai_response.usage_metadata.get("output_tokens", 0)
            logger.info("\n"*3)
            return {'json_panel':json_panel, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":1}
        except Exception as e:
            logger.error(f"{e}")
            return None


def get_documentation(schemas : Dict):
    doc = ""
    for key in schemas:
        doc += schemas[key]
        doc += "\n\n\n"
    return doc




# TODO: pensar, en este momento mi idea es que create_dashboard_agent cree el json de todos los paneles de grafana; 
# quizas sea buena idea partir esta funcion en dos agentes, 
def create_dashboard_agent(
        llm_panels_designer : BaseChatModel, 
        llm_information_structurer : BaseChatModel,
        llm_grafana_expert : BaseChatModel,
        engine : Engine,
        top_n : int = 15

) -> CompiledStateGraph:
    
    #parser = JsonOutputParser()

    class State(TypedDict):
        # initial state
        analysis : str

        panels_descriptions : str
        panels_descriptions_list : List[str]
        extracted_tables_with_documentation : List[Dict[str, Any]]
        grafana_jsons_panels : List[Dict[str, Any]]

        input_tokens : int
        output_tokens : int
        api_calls : int
    
    # -------
    # -------

    def panels_designer_node(state : State) -> State:
        logger.info("xxx"*5 + " panels_designer_node " + "xxx"*5)
        analysis = state['analysis']

        prompt = PANELS_DESCRIPTION_PROMPT_1.format(top_n=top_n, analysis=analysis)
        ai_message = llm_panels_designer.invoke(prompt)
        logger.info(f"\n {ai_message.pretty_repr()}")

        input_tokens = ai_message.usage_metadata.get("input_tokens", 0)
        output_tokens = ai_message.usage_metadata.get("output_tokens", 0)
        api_calls = 1
        logger.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")
        logger.info("\n"*10)

        return {"panels_descriptions":ai_message.content, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    


    def structure_panles_node(state : State) -> State:
        logger.info("xxx"*5 + " structure_panles_node " + "xxx"*5)

        input_tokens = state["input_tokens"]
        output_tokens = state["output_tokens"]
        api_calls = state["api_calls"]

        ideas = state['panels_descriptions']

        prompt = REPORT_PARSER_PROMPT_1.format(ideas=ideas)
        ai_response = llm_information_structurer.invoke(prompt)
        logger.info(f"{ai_response.pretty_repr()}")
        panels_descriptions_list = parser.parse(ai_response.content)

        input_tokens += ai_response.usage_metadata.get("input_tokens", 0)
        output_tokens += ai_response.usage_metadata.get("output_tokens", 0)
        api_calls += 1
        logger.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")
        logger.info("\n"*10)


        return {"panels_descriptions_list":panels_descriptions_list['charts'], "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    

    
    async def extracted_tables_node(state : State) -> State:
        logger.info("xxx"*5 + " extracted_tables_node " + "xxx"*5)

        input_tokens = state["input_tokens"]
        output_tokens = state["output_tokens"]
        api_calls = state["api_calls"]

        panels_descriptions_list = state["panels_descriptions_list"]

        if len(panels_descriptions_list) == 0:
            raise ValueError(f"panels_descriptions_list es una lista vacia")
        
        pg_utils = PostgresToolKit(engine=engine)
        db_tables = pg_utils.get_tables_name()
        db_schemas = pg_utils.get_all_tables_schema()
        logger.info("esquemas y tablas conseguidos")
        
        semaphore = asyncio.Semaphore(5)
        logger.info("semaforo: \n\n")

        tasks = [
            get_tables_from_description(
                semaphore, 
                description,
                llm_information_structurer, 
                GET_TABLES_FROM_CHART_PROMPT_2.format(description=description, db_tables=db_tables)
            ) for description in panels_descriptions_list
        ]

        result = await asyncio.gather(*tasks)
        logger.info(f"result tasks len: {len(result)} \n\n")


        extracted_tables_with_documentation = []
        for res in result:
            logger.info(f"type res: {type(res)}")
            if res:
                input_tokens += res['input_tokens']
                output_tokens += res['output_tokens']
                api_calls += res['api_calls']
                schemas = {}
                for name in res['tables_name']:
                    logger.info(f"name: {name}")
                    schemas[name] = db_schemas[name]
                tables_des_schemas = {'tables_name':res['tables_name'], 'description':res['description'], 'schemas':schemas}
                extracted_tables_with_documentation.append(tables_des_schemas)
                logger.info("\n\n")
        
        logger.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")
        logger.info("\n"*10)
        
        return {'extracted_tables_with_documentation':extracted_tables_with_documentation, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    


    async def grafana_json_node(state : State) -> State:
        logger.info("xxx"*5 + " grafana_json_node " + "xxx"*5)

        input_tokens = state["input_tokens"]
        output_tokens = state["output_tokens"]
        api_calls = state["api_calls"]

        extracted_tables_with_documentation = state['extracted_tables_with_documentation']

        prompt_list = [
            JSON_CHART_GRAFANA_PROMPT_8.format(doc=get_documentation(schemas=item['schemas']), desc=item['description']) for item in extracted_tables_with_documentation
        ]
        logger.info(f"len prompt_list: {len(prompt_list)}")

        semaphore = asyncio.Semaphore(6)

        tasks = [
            get_json_panel(
                semaphore=semaphore,
                llm_grafana_expert=llm_grafana_expert,
                prompt=prompt
            )
            for prompt in prompt_list
        ]

        result = await asyncio.gather(*tasks)
        logger.info(f"len result: {len(result)}")

        grafana_jsons_panels = []
        for res in result:
            if res:
                input_tokens += res['input_tokens']
                output_tokens += res['output_tokens']
                api_calls += res['api_calls']
                grafana_jsons_panels.append(res['json_panel'])
        
        logger.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")
        logger.info("\n"*10)

        return {'grafana_jsons_panels':grafana_jsons_panels, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    

    # -------
    # -------


    builder = StateGraph(State)

    builder.add_node("panels_designer_node", panels_designer_node)
    builder.add_node("structure_panles_node", structure_panles_node)
    builder.add_node("extracted_tables_node", extracted_tables_node)
    builder.add_node("grafana_json_node", grafana_json_node)

    builder.add_edge(START, "panels_designer_node")
    builder.add_edge("panels_designer_node", "structure_panles_node")
    builder.add_edge("structure_panles_node", "extracted_tables_node")
    builder.add_edge("extracted_tables_node", "grafana_json_node")
    builder.add_edge("grafana_json_node", END)

    graph = builder.compile()

    return graph







if __name__=="__main__":

    from src import settings
    from sqlalchemy import create_engine
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_groq import ChatGroq
    import json
    from src.logging_config import setup_base_logging
    import asyncio

    setup_base_logging()

    db_user = "postgres"
    db_pass = "postgres"
    db_host = "localhost"
    db_port = "5434"
    db_name = "northwind"

    conn_string = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(conn_string)


    model = "gemini-2.5-pro"
    llm_panels_designer = ChatGoogleGenerativeAI(model=model, temperature=0.5, google_api_key=settings.GOOGLE_API_KEY)

    model = "openai/gpt-oss-120b"
    llm_information_structurer = ChatGroq(model=model, temperature=0.1, api_key=settings.GROQ_API_KEY)
    
    
    model = "gemini-2.5-flash"
    llm_grafana_expert = ChatGoogleGenerativeAI(model=model, temperature=0.5, google_api_key=settings.GOOGLE_API_KEY)

    dashboard_agent = create_dashboard_agent(llm_panels_designer=llm_panels_designer, llm_information_structurer=llm_information_structurer, llm_grafana_expert=llm_grafana_expert, engine=engine)



    path = settings.ROOT / "test" / "graphs_states" / "analyst" / "analysis.md"
    with open(path, 'r', encoding='utf-8') as f:
        analysis = f.read()
    
    initial_state = {'analysis':analysis}


    
    async def run_create_dashboard_agent():
        agente_response = await dashboard_agent.ainvoke(initial_state)
        return agente_response  
    agente_response = asyncio.run(run_create_dashboard_agent())


    
    grafana_jsons_panels = agente_response['grafana_jsons_panels']
    path = settings.ROOT / "test" / "graphs_states" / "grafana" / "panels.json"

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(grafana_jsons_panels, f, indent=2, ensure_ascii=False)
    


"""
python3 -m src.grafana_graph.graphs.create_dashboard_agent


"""