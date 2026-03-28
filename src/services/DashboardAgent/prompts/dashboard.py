
PANELS_DESCRIPTION_PROMPT_1 = """
Eres un asistente util experto analisis de datos y reprecentacion de graficas que explican datos y experto en grafana.
Se te proporcionará un analisis de una base de datos que consiste en consultas en lenguage natural hacie la base de datos y la respuesta a esa consulta
tu tarea consiste generar una lista de {top_n} ideas de visualizaciones para paneles de Grafana que permitan explicar y complementar el informe anterior.


Para cada idea de visualización, incluye obligatoriamente la siguiente información:

1. **Tipo de visualización del panel**  
   Debe ser una visualización **nativa de Grafana**, seleccionada exclusivamente de la siguiente lista:
   - timeseries
   - barchart
   - stat
   - gauge
   - table
   - piechart
   - histogram
   - geomap
   - xychart


2. **Propósito de la visualización**  
   Describe claramente qué información busca resaltar la gráfica o qué pregunta específica ayuda a responder dentro del contexto del informe.

3. **Tablas de la base de datos utilizadas**  
   Indica explícitamente qué tablas de la base de datos se emplean para construir la visualización.

3. **Dimensión temporal (si aplica)**  
   En el caso de visualizaciones dependientes del tiempo, especifica explícitamente:
   - El período de tiempo que cubre la visualización. Este periodo de tiempo debe ser congruente con los datos.

Presenta las ideas de forma clara, estructurada y fácil de interpretar.


### Analisis de la base de datos

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

### Ideas

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



JSON_CHART_GRAFANA_PROMPT_8 = """
Eres un Arquitecto de Datos experto en Grafana 12.3.0 y PostgreSQL. Tu objetivo es generar la configuración JSON de un panel (panel JSON model) listo para ser importado.

### ENTRADAS:
1. **Documentación de Base de Datos:** Esquema y tablas disponibles.
2. **Requerimiento:** Descripción de la visualización deseada.

### TAREA:
Generar un **único objeto JSON** que represente un panel de Grafana válido.

### ESPECIFICACIONES TÉCNICAS DEL JSON:
El JSON debe seguir esta estructura base:

```json
{{
  "type": "<tipo_visualizacion>",
  "gridPos": {{ "x": <num>, "y": <num>, "w": <num>, "h": <num> }},
  "title": "<titulo_del_panel>",
  "datasource": {{
    "type": "postgres",
    "uid": "pg-db-1"
  }},
  "targets": [
    {{
      "format": "table", 
      "group": [],
      "metricColumn": "none",
      "rawQuery": true,
      "rawSql": "<CONSULTA_SQL_AQUI>",
      "refId": "A",
      "select": [[{{"params": ["value"]}}]],
      "timeColumn": "time",
      "where": [{{"name": "$__timeFilter", "params": [], "datatype": "varchar"}}]
    }}
  ],
  "options": {{}},
  "fieldConfig": {{ "defaults": {{ "unit": "none" }}, "overrides": [] }}
}}
```

### REGLAS DE VISUALIZACIÓN:
Usa uno de los siguientes tipos nativos para la clave "type":
["timeseries", "barchart", "gauge", "stat", "table", "piechart", "histogram", "geomap", "xychart"]

### REGLAS PARA SQL (POSTGRESQL):
1. La consulta debe basarse **únicamente** en la documentación proporcionada.
2. **Prohibido:** No uses funciones específicas de plugins (como `time_bucket`) ni macros de Grafana (`$__timeFrom`, `$__timeTo`, `$__timeFilter`). Usa funciones nativas de PostgreSQL (ej. `date_trunc`, `NOW()`).
3. **Requisito Temporal:** Para gráficas de tipo `timeseries`, `state-timeline` o `barchart` evolutivos, la consulta **DEBE** devolver una columna llamada explícitamente `time` (en minúsculas) con formato `TIMESTAMP` o `TIMESTAMPTZ`.
4. Asegúrate de castear los tipos de datos si es necesario (ej. contadores a numeric/float).

### FORMATO DE RESPUESTA:
- Generar un **único objeto JSON**
---
### Documentación de la base de datos
{doc}

### Descripción de la gráfica
{desc}
"""