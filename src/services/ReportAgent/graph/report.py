from typing import TypedDict, List, Dict, Any
from sqlalchemy.engine import Engine
from ..prompts.report import (
    HUMAN_MAKE_CHARTS_PROMPT, 
    REPORT_PARSER_PROMPT_1, 
    GET_TABLES_FROM_CHART_PROMPT_2, 
    CODE_CHART_PROMPT_1, 
    BASE_CODE_AND_DESCRIPTION, 
    STREAMLIT_PROMPT_1, 
    REPORT_PROMPT_1
)
from src.services.AnalystAgent.toolkit import PostgresToolKit  # TODO: quizas PostgresToolKit debe ser una clase mas general
import asyncio

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser

from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import StateGraph, START, END


from src.logging_config import get_logger
logger = get_logger(module_name="report", DIR='graph')

parser = JsonOutputParser()



async def get_tables_from_description(semaphore, description : str, llm_information_structurer : BaseChatModel, prompt : str):
    logger.info("--- get_tables_from_description")
    async with semaphore:
        try:
            ai_response = await llm_information_structurer.ainvoke(prompt)
            logger.info(f"\n {ai_response.pretty_repr()}")
            tables_name = parser.parse(ai_response.content)
            tables_name = tables_name["tables"]

            input_tokens = ai_response.usage_metadata.get("input_tokens", 0)
            output_tokens = ai_response.usage_metadata.get("output_tokens", 0)
            logger.info("\n"*3)

            return {'tables_name':tables_name, 'description':description, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":1}
        except Exception as e:
            logger.error(f"{e}")
            return None


async def get_code_from_description(semaphore, llm_coder : BaseChatModel, prompt : str, description : str):
    logger.info("--- get_code_from_description") 
    async with semaphore:
        try:
            ai_response = await llm_coder.ainvoke(prompt)
            logger.info(f"\n {ai_response.pretty_repr()} \n")
            chart_code = ai_response.content

            input_tokens = ai_response.usage_metadata.get("input_tokens", 0)
            output_tokens = ai_response.usage_metadata.get("output_tokens", 0)
            logger.info("\n"*3)
            return {'chart_code':chart_code, 'description':description, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":1}
        except Exception as e:
            logger.error(f"{e}")
            return None


def get_documentation(schemas : Dict):
    doc = ""
    for key in schemas:
        doc += schemas[key]
        doc += "\n\n\n"
    return doc


def get_chart_description_documentation(code_charts_descriptions : Dict):
    doc = ""
    for dicc in code_charts_descriptions:
        doc += BASE_CODE_AND_DESCRIPTION.format(des=dicc['description'], code=dicc['chart_code'])
        doc += "\n\n"
    return doc
    




def create_report_agent(
        llm_charts_designer : BaseChatModel,
        llm_information_structurer : BaseChatModel,
        llm_coder : BaseChatModel,
        llm_streamlit_coder : BaseChatModel,
        llm_report_writer : BaseChatModel,
        engine : Engine,
        top_n : int = 15

) -> CompiledStateGraph:
    

    class State(TypedDict):
        # initial state
        analysis : str

        charts_description : str
        charts_description_list : List[str]
        extracted_tables_with_documentation : List[Dict[str, Any]]
        code_charts_descriptions : List[Dict[str, Any]]
        streamlit_code : str
        report : str

        input_tokens : int
        output_tokens : int
        api_calls : int

    
    # -------
    # -------

    def charts_designer_node(state : State) -> State:
        logger.info("xxx"*5 + " charts_designer_node " + "xxx"*5)
        analysis = state["analysis"]

        prompt = HUMAN_MAKE_CHARTS_PROMPT.format(analysis=analysis, top_n=top_n)
        ai_response = llm_charts_designer.invoke(prompt)
        logger.info(f"\n {ai_response.pretty_repr()} \n")

        input_tokens = ai_response.usage_metadata.get("input_tokens", 0)
        output_tokens = ai_response.usage_metadata.get("output_tokens", 0)
        api_calls = 1
        logger.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")
        logger.info("\n"*10)

        return {"charts_description":ai_response.content, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    


    def structure_ideas_node(state : State) -> State:
        logger.info("xxx"*5 + " structure_ideas_node " + "xxx"*5)

        input_tokens = state["input_tokens"]
        output_tokens = state["output_tokens"]
        api_calls = state["api_calls"]

        ideas = state["charts_description"]

        prompt = REPORT_PARSER_PROMPT_1.format(ideas=ideas)
        ai_response = llm_information_structurer.invoke(prompt)
        logger.info(f"\n {ai_response.pretty_repr()}")

        charts_description_list = parser.parse(ai_response.content)

        input_tokens += ai_response.usage_metadata.get("input_tokens", 0)
        output_tokens += ai_response.usage_metadata.get("output_tokens", 0)
        api_calls += 1
        logger.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")
        logger.info("\n"*10)

        return {"charts_description_list":charts_description_list, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    


    async def extracted_tables_node(state : State) -> State:
        logger.info("xxx"*5 + " extracted_tables_node " + "xxx"*5)

        input_tokens = state["input_tokens"]
        output_tokens = state["output_tokens"]
        api_calls = state["api_calls"]
        
        charts_description_list = state["charts_description_list"]

        pg_utils = PostgresToolKit(engine=engine)
        db_tables = pg_utils.get_tables_name()
        db_schemas = pg_utils.get_all_tables_schema()
        logger.info("esquemas y tablas conseguidos")

        prompt_list = [GET_TABLES_FROM_CHART_PROMPT_2.format(description=description, db_tables=db_tables) for description in charts_description_list]
        logger.info(f"len prompt_list: {len(prompt_list)}")

        semaphore = asyncio.Semaphore(5)
        logger.info("semaforo")

        tasks = [
            get_tables_from_description(
                semaphore=semaphore, 
                description=charts_description_list[i], 
                llm_information_structurer=llm_information_structurer, 
                prompt=prompt_list[i]
            ) for i in range(len(charts_description_list))
        ]

        result = await asyncio.gather(*tasks)
        logger.info(f"len result: {result}")


        extracted_tables_with_documentation = []
        for res in result:
            if result:
                input_tokens += res['input_tokens']
                output_tokens += res['output_tokens']
                api_calls += res['api_calls']
                schemas = {}
                for name in res['tables_name']:
                    schemas[name] = db_schemas[name]
                
                tables_des_schemas = {'tables_name':res['tables_name'], 'description':res['description'], 'schemas':schemas}
                extracted_tables_with_documentation.append(tables_des_schemas)
        
        logger.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")
        logger.info("\n"*10)
        
        return {'extracted_tables_with_documentation':extracted_tables_with_documentation, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    


    async def get_code_node(state : State) -> State:
        logger.info("xxx"*5 + " get_code_node " + "xxx"*5)

        input_tokens = state["input_tokens"]
        output_tokens = state["output_tokens"]
        api_calls = state["api_calls"]

        extracted_tables_with_documentation = state["extracted_tables_with_documentation"]

        url = engine.url
        logger.info(f"engine url: {url}")

        prompt_list = [
            CODE_CHART_PROMPT_1.format(
                drive_name=url.drivername,
                db_user=url.username,
                db_pass=url.password,
                db_host=url.host,
                db_port=url.port,
                db_name=url.database,
                doc=get_documentation(doc_dict['schemas']),
                description=doc_dict['description']
            ) for doc_dict in extracted_tables_with_documentation
        ]

        description_list = [doc_dict['description'] for doc_dict in extracted_tables_with_documentation]
        # TODO: Juntar prompt_list y description_list en un solo ciclo for

        semaphore = asyncio.Semaphore(5)
        logger.info("semaforo")

        tasks = [
            get_code_from_description(
                semaphore=semaphore,
                llm_coder=llm_coder,
                prompt=prompt_list[i],
                description=description_list[i]
            ) for i in len(extracted_tables_with_documentation)
        ]

        result = await asyncio.gather(*tasks)
        logger.info(f"len result {len(result)}")

        code_charts_descriptions = []
        for item in result:
            if item:
                input_tokens += item['input_tokens']
                output_tokens += item['output_tokens']
                api_calls += item['api_calls']
                code_charts_descriptions.append(item)
        
        logger.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")
        logger.info("\n"*10)

        return {"code_charts_descriptions":code_charts_descriptions, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    
    # TODO: Falta hacer el prompt
    def get_streamlit_code_node(state : State) -> State:
        logger.info("xxx"*5 + " get_streamlit_code_node " + "xxx"*5) 

        input_tokens = state["input_tokens"]
        output_tokens = state["output_tokens"]
        api_calls = state["api_calls"]

        code_charts_descriptions = state["code_charts_descriptions"]

        doc = get_chart_description_documentation(code_charts_descriptions)
        
        prompt = STREAMLIT_PROMPT_1.format(doc=doc)
        ai_response = llm_streamlit_coder.invoke(prompt)
        logger.debug(f"\n {ai_response.pretty_print()} \n")
        streamlit_code = parser.parse(ai_response.content)

        input_tokens += ai_response.usage_metadata.get("input_tokens", 0)
        output_tokens += ai_response.usage_metadata.get("output_tokens", 0)
        api_calls += 1
        logger.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")
        logger.info("\n"*10)

        return {"streamlit_code":streamlit_code, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    

    # TODO: Falta hacer el prompt
    def get_report_code(state : State) -> State:
        logger.info("xxx"*5 + " get_streamlit_code_node " + "xxx"*5)

        input_tokens = state["input_tokens"]
        output_tokens = state["output_tokens"]
        api_calls = state["api_calls"]

        streamlit = state["streamlit_code"]
        analiysis = state["analysis"]

        prompt = REPORT_PROMPT_1.format(streamlit=streamlit, analiysis=analiysis)
        ai_message = llm_report_writer.invoke(prompt)
        logger.debug(f"\n {ai_message.pretty_print()} \n")
        report = parser.parse(ai_message.content)

        input_tokens += ai_message.usage_metadata.get("input_tokens", 0)
        output_tokens += ai_message.usage_metadata.get("output_tokens", 0)
        api_calls += 1
        logger.info(f"input_tokens: {input_tokens}--output_tokens: {output_tokens}--api_calls: {api_calls}")

        return {"report":report, "input_tokens":input_tokens, "output_tokens":output_tokens, "api_calls":api_calls}
    

    builder = StateGraph(State)

    builder.add_node("charts_designer_node", charts_designer_node)
    builder.add_node("structure_ideas_node", structure_ideas_node)
    builder.add_node("extracted_tables_node", extracted_tables_node)
    builder.add_node("get_code_node", get_code_node)
    builder.add_node("get_streamlit_code_node", get_streamlit_code_node)
    builder.add_node("get_report_code", get_report_code)

    builder.add_edge(START, "charts_designer_node")
    builder.add_edge("charts_designer_node", "structure_ideas_node")
    builder.add_edge("structure_ideas_node", "extracted_tables_node")
    builder.add_edge("extracted_tables_node","get_code_node" )
    builder.add_edge("get_code_node", "get_streamlit_code_node")
    builder.add_edge("get_streamlit_code_node", "get_report_code")
    builder.add_edge("get_report_code", END)

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
    llm_charts_designer = ChatGoogleGenerativeAI(model=model, temperature=0.5, google_api_key=settings.GOOGLE_API_KEY)

    model = "openai/gpt-oss-120b"
    llm_information_structurer = ChatGroq(model=model, temperature=0.1, api_key=settings.GROQ_API_KEY)
     
    model = "gemini-2.5-flash"
    llm_coder = ChatGoogleGenerativeAI(model=model, temperature=0.5, google_api_key=settings.GOOGLE_API_KEY)

    model = "gemini-2.5-flash"
    llm_streamlit_coder = ChatGoogleGenerativeAI(model=model, temperature=0.5, google_api_key=settings.GOOGLE_API_KEY)

    model = "gemini-2.5-flash"
    llm_report_writer = ChatGoogleGenerativeAI(model=model, temperature=0.5, google_api_key=settings.GOOGLE_API_KEY)


    report_agent = create_report_agent(llm_charts_designer=llm_charts_designer, llm_information_structurer=llm_information_structurer, llm_coder=llm_coder, llm_streamlit_coder=llm_streamlit_coder, llm_report_writer=llm_report_writer, engine=engine)

    