from sqlalchemy.engine import Engine
from sqlalchemy import text
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_core.tools.base import BaseTool
from typing import List
from sqlalchemy import text, MetaData, Table
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

class PostgresToolKit:
    def __init__(self, engine : Engine, top_n : int = 15, schema_name : str = 'public'):
        self.engine = engine
        self.schema_name = schema_name
        self.top_n = top_n
    
    # ---  Helper methods

    def _get_db_tables_names(self) -> str:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    f"""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = '{self.schema_name}'
                    ORDER BY table_name
                    """
                ))
                rows = result.fetchall()
                response = f"Hay {len(rows)} tablas en la base de datos:\n\n"
                for row in rows:
                    response += f"{row[0]}\n"
                return response
        except Exception as e:
            return f"Error: {e}"
        
    
    def _get_table_schema(self, table_name: str) -> str:
        try:
            metadata = MetaData()
            # Intenta cargar la tabla. Si falla, SQLAlchemy lanzará error.
            table = Table(table_name, metadata, autoload_with=self.engine)
            
            ddl = CreateTable(table).compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True}
            )
            return str(ddl)
        except Exception as e:
            return f"Error obteniendo esquema de la tabla '{table_name}': {str(e)}"
    
    def _get_tables_schemas(self, tables_names : List[str]) -> str:
        try:
            schemas = ""
            for name in tables_names:
                schemas += f"{self._get_table_schema(name)}"
                schemas += "\n\n"
            return schemas
        except Exception as e:
            return f"- Error: {e} \n\n"
        
    
    def _query_data_base(self, query: str) -> str:
        try:
            # Se recomienda usar bloques try/except para conexiones DB
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
            
            if len(rows) > self.top_n:
                response = f"Hay {len(rows)} registros en la respuesta de la consulta. Se ha limitado a los primeros {self.top_n} registros: \n\n {rows[:self.top_n]}"
                return response
            else:
                response = f"Hay {len(rows)} registros en la respuesta de la consulta: \n\n {rows}"
                return response
        except Exception as e:
            return f"Error ejecutando query SQL: {str(e)}"
        


    # --- args_schema

    class TablesSchemas(BaseModel):
        tables_names : List[str] = Field(description="Lista con los nombres de las tablas de la base de datos")
    
    class QueryDataBaseArgs(BaseModel):
        query: str = Field(description="Query SQL válida para PostgreSQL.")


    # --- return

    def get_tools(self) -> List[BaseTool]:
        tools = [
            StructuredTool.from_function(
                name="get_db_tables_names",
                description="Retorna el nombre de todas las tablas de la base de datos del usuario",
                func=self._get_db_tables_names
                # No needs args
            ),
            StructuredTool.from_function(
                name="get_tables_schemas",
                description="Retorna el esquema de una lista de tablas",
                func=self._get_tables_schemas,
                args_schema=self.TablesSchemas
            ),
            StructuredTool.from_function(
                name="query_data_base",
                description="Ejecuta una consulta SQL en PostgreSQL y retorna hasta 15 filas.",
                func=self._query_data_base,
                args_schema=self.QueryDataBaseArgs
            )
        ]

        return tools
    

    # --- Postgres Utils

    def get_all_tables_schema(self) -> dict:
        metadata = MetaData()
        metadata.reflect(bind=self.engine)

        schemas = {}

        for table_name, table in metadata.tables.items():
            ddl = CreateTable(table).compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True}
            )
            schemas[table_name] = str(ddl)

        return schemas
    


    def get_tables_name(self, schema_name : str = 'public') -> List[str]:
        with self.engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = '{schema_name}'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result]
        return tables
    



    

if __name__=="__main__":
    pass

