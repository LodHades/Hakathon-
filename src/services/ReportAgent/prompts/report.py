
HUMAN_MAKE_CHARTS_PROMPT = """
Genera una lista de {top_n} ideas de visualizaciones con la librería de python plotly que permitan explicar y complementar el siguiente analisis de una base de datos 
Cada idea de gráfica debe incluir:

- El tipo de gráfico (por ejemplo: gráfico de barras, diagrama de calor, mapa, tabla, etc.).
- El propósito de la gráfica (qué información busca resaltar o qué pregunta ayuda a responder).
- Las tablas de la base de datos que se utilizan para construir la gráfica.

Proporciona las ideas de manera clara y estructurada.

### Analisis de datos:

{analysis}
"""


# ====================================================================================================================
# ====================================================================================================================


REPORT_PARSER_PROMPT_1 = """
Eres un experto en procesamiento y formateo de información.

Se te proporcionará una lista de ideas para gráficas para un analisis de una base de datos. En esta lista aparecen instrucciones para crear gráficas que ayuden a describir la información contenida en la base de datos.

Tu tarea consite en lo siguiente:
- 1. identificar las gráfica y las instrucciones para realizar la gráfica.
- 2. para cada gráfica debes **extraer textualmente** todo lo relacionado a sus instrucciones 
- 3. guarda las instrucciones en una lista de tal forma que cada elemento de la lista sea las instrucciones de una gráfica.

Debes devolver la salida en un JSON válido con el siguiente formato:

```json
{{
  "charts": [
    "instrucción para realizar una gráfica extraída del texto",
    "otra instrucción para realizar otra gráfica extraída del texto",
    ...
  ]
}}
```

**Importante:**
- No modifiques las instrucciones originales.
- No agregues explicaciones, comentarios ni texto adicional fuera del JSON.
- Si no hay instrucciones de gráficas, devuelve: 

```json
{{"charts": []}}
```

### lista de ideas:

{ideas}
"""


# ====================================================================================================================
# ====================================================================================================================



GET_TABLES_FROM_CHART_PROMPT_2 = """
Eres un asistente útil y experto en extracción de información.
Se te proporcionará un texto que describe una gráfica o visualización. 
El texto puede incluir detalles sobre el tipo de gráfico, los ejes, los valores, 
las tablas utilizadas de una base de datos para obtener la información, 
y el propósito de la gráfica.
Se te proporcionará también el nombre de todas las tablas de la base de datos

Tu tarea es identificar y extraer los nombres de las tablas de la base de datos mencionadas en la descripción y ponerlos en una lista.  
Hay veces en las que los nombres de las tablas en la descripción no coinciden exactamente con los 
nombres reales de la tabla de la base de datos, en ese caso pon el nombre de la tabla de los nombres de las tablas de la base de datos que se te promporcionó
Devuelve tu respuesta en el siguiente formato JSON:


```json
{{
  "tables": ["tabla_1", "tabla_2", ...]
}}
```

Si no se mencionan tablas en el texto, responde exactamente lo siguiente:

```json
{{
  "tables": []
}}
```

No incluyas comentarios, explicaciones ni texto adicional.

### Texto a analizar:

{description}

### Nombre de las tablas de la base de datos.

{db_tables}
"""


# ====================================================================================================================
# ====================================================================================================================



CODE_CHART_PROMPT_1 = """
Eres un asistente experto en análisis de datos y visualización con Python.

Se te proporcionará:
1. La documentación de una base de datos PostgreSQL.
2. La descripción de una gráfica que se desea generar a partir de dicha base de datos.

Tu tarea es producir el código Python completo para generar la gráfica utilizando `plotly`, `pandas` y `sqlalchemy`.

Sigue estos pasos:

1. **Consulta SQL (QUERY):**
   - Escribe una consulta en **PostgreSQL** que obtenga los datos necesarios para construir la gráfica, basándote en la descripción proporcionada.
   - La consulta debe ser clara, eficiente y utilizar los nombres de tablas y columnas indicados en la documentación de la base de datos.

2. **Carga de datos con pandas:**
   - Usa `sqlalchemy` y `pandas` para ejecutar la consulta y cargar los resultados en un DataFrame llamado `df`.

Ejemplo:
```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

db_url = URL.create(
    drivername={drive_name},
    username={db_user},
    password={db_pass},
    host={db_host},
    port={db_port},
    database={db_name}
)

engine = create_engine(db_url)
QUERY = \"\"\"TU_CONSULTA_AQUÍ\"\"\"
df = pd.read_sql_query(QUERY, engine)
```

3. **Generación de la gráfica:**
   - Usa `plotly` para generar la gráfica solicitada.
   - Asegúrate de incluir etiquetas de ejes, título y leyenda si corresponde.
   - No utilices datos ficticios: los datos deben provenir del DataFrame `df`.

4. **Salida final:**
   - Devuelve el código Python completo e integrado, incluyendo la definición de la consulta, la carga de datos y la creación de la gráfica.
   - No agregues explicaciones y solo devuelve el código python.

---

### Documentación de la base de datos

{doc}

### Descripción de la gráfica

{description}
"""


# ====================================================================================================================
# ====================================================================================================================



STREAMLIT_PROMPT_1 = """
Eres un experto en la librería de python streamlit. resiviras un docuemento que contiene graficas hechas con la librería de python plotly y una descripcion que detalla la grafica.
Tu tarea es hacer una aplicacion en streamlit que utilice estas graficas y sus descripciones.

No hagas comentarios y solo limitate a generar el codigo python.

### Documento co las graficas y su descripcion:

{doc}
"""



# ====================================================================================================================
# ====================================================================================================================




REPORT_PROMPT_1 = """
eres un asistente util

{streamlit}

---

{analiysis}
"""





# ====================================================================================================================
# ====================================================================================================================





BASE_CODE_AND_DESCRIPTION = """
### Descripcion:

{des}

### Codigo:

{code}

---
"""