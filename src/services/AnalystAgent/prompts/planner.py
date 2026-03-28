TABLE_SCHEMA_TEMPLATE_3 = """
### Nombre de la tabla:
{table_name}

### Esquema de la tabla
{schema}


---
"""


# ====================================================================================================================
# ====================================================================================================================



PLANER_PROMPT_2 = """
Eres un asistente útil y experto en análisis de datos.

Se te proporcionará la **documentación de una base de datos**, donde para cada tabla se describe:
- el nombre de la columna y el tipo de información que almacena
- la clave primaria y la clave foranea 

Tu tarea es, **a partir de esta documentación**, elaborar una **guía o plan detallado** con ideas para generar un **informe o análisis de datos** relacionado con el siguiente tema:

{topic}

El plan debe incluir:
1. **Tablas y relaciones relevantes**: qué tablas y conexiones son útiles para conseguir los datos necesarios.
2. **Sugerencias de consultas o análisis**: qué información obtener de la base de datos para abordar el tema.
3. **Posibles enfoques o indicadores**: métricas o perspectivas que podrían enriquecer el análisis.


### Documentación de la base de datos:

{doc}
"""



# ====================================================================================================================
# ====================================================================================================================
