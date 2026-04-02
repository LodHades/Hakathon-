
### Descripcion:

1. Visión General de la Base de Datos

Tipo de gráfico: Gráfico de Barras Horizontal
Propósito: Visualizar el número de registros en cada tabla, permitiendo una comparación rápida de los tamaños de las tablas y destacando cuáles están vacías o son las más grandes. Esto complementa la "Interpretación rápida" inicial.
Tablas utilizadas: Todas las tablas de la base de datos (meta-información).

### Codigo:

```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

# Configuración de la conexión a la base de datos
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

# Consulta SQL para obtener el número de registros por tabla
QUERY = """
SELECT 'categories' AS table_name, COUNT(*) AS record_count FROM categories
UNION ALL
SELECT 'customer_customer_demo' AS table_name, COUNT(*) AS record_count FROM customer_customer_demo
UNION ALL
SELECT 'customer_demographics' AS table_name, COUNT(*) AS record_count FROM customer_demographics
UNION ALL
SELECT 'customers' AS table_name, COUNT(*) AS record_count FROM customers
UNION ALL
SELECT 'employee_territories' AS table_name, COUNT(*) AS record_count FROM employee_territories
UNION ALL
SELECT 'employees' AS table_name, COUNT(*) AS record_count FROM employees
UNION ALL
SELECT 'order_details' AS table_name, COUNT(*) AS record_count FROM order_details
UNION ALL
SELECT 'orders' AS table_name, COUNT(*) AS record_count FROM orders
UNION ALL
SELECT 'products' AS table_name, COUNT(*) AS record_count FROM products
UNION ALL
SELECT 'region' AS table_name, COUNT(*) AS record_count FROM region
UNION ALL
SELECT 'shippers' AS table_name, COUNT(*) AS record_count FROM shippers
UNION ALL
SELECT 'suppliers' AS table_name, COUNT(*) AS record_count FROM suppliers
UNION ALL
SELECT 'territories' AS table_name, COUNT(*) AS record_count FROM territories
UNION ALL
SELECT 'us_states' AS table_name, COUNT(*) AS record_count FROM us_states;
"""

# Carga de datos con pandas
df = pd.read_sql_query(QUERY, engine)

# Ordenar el DataFrame para que el gráfico muestre las barras ordenadas
df = df.sort_values('record_count', ascending=True)

# Generación de la gráfica
fig = px.bar(
    df,
    x='record_count',
    y='table_name',
    orientation='h', # Para un gráfico de barras horizontal
    title='Número de Registros por Tabla en la Base de Datos Northwind',
    labels={
        'record_count': 'Número de Registros',
        'table_name': 'Tabla'
    }
)

# Mostrar la gráfica
fig.show()
```

---



### Descripcion:

2. Ventas Totales Acumuladas

Tipo de gráfico: Indicador (Gauge/Number)
Propósito: Mostrar de manera prominente el valor total de todas las ventas ($1,265,793.04) como una métrica clave. Se puede combinar con un pequeño "delta" si hubiera un período anterior para comparar.
Tablas utilizadas: `Orders`, `Order_Details`

### Codigo:

```python
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import URL, create_engine

# Database connection details
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

# 1. Consulta SQL (QUERY)
QUERY = """
SELECT
    SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_sales
FROM
    order_details AS od;
"""

# 2. Carga de datos con pandas
df = pd.read_sql_query(QUERY, engine)

# 3. Generación de la gráfica
total_sales_value = df['total_sales'].iloc[0]

fig = go.Figure(go.Indicator(
    mode="number",
    value=total_sales_value,
    title={"text": "<b>Ventas Totales Acumuladas</b>"},
    number={'prefix': "$", 'valueformat': ".2f"}
))

fig.update_layout(
    height=250,
    margin=dict(l=20, r=20, t=50, b=20)
)

fig.show()
```

---



### Descripcion:

3. Tendencia de Ventas Mensuales a lo Largo del Tiempo

Tipo de gráfico: Gráfico de Líneas con Marcadores
Propósito: Visualizar la distribución de ventas totales por mes y año (`1996-07` a `1998-05`), identificando tendencias de crecimiento, estacionalidad y el pico de ventas en `1998-04`. Esto complementa la "Distribución de ventas totales por mes".
Tablas utilizadas: `Orders`, `Order_Details`

### Codigo:

```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

QUERY = """
SELECT
    EXTRACT(YEAR FROM o.order_date) AS sales_year,
    EXTRACT(MONTH FROM o.order_date) AS sales_month,
    SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_sales
FROM
    orders AS o
JOIN
    order_details AS od ON o.order_id = od.order_id
WHERE
    o.order_date >= '1996-07-01' AND o.order_date < '1998-06-01'
GROUP BY
    sales_year,
    sales_month
ORDER BY
    sales_year,
    sales_month;
"""

df = pd.read_sql_query(QUERY, engine)

df['month_year'] = pd.to_datetime(df['sales_year'].astype(str) + '-' + df['sales_month'].astype(str) + '-01')

fig = px.line(
    df,
    x='month_year',
    y='total_sales',
    markers=True,
    title='Tendencia de Ventas Mensuales a lo Largo del Tiempo (Julio 1996 - Mayo 1998)'
)

fig.update_layout(
    xaxis_title='Mes y Año',
    yaxis_title='Ventas Totales',
    xaxis=dict(tickformat="%Y-%m") # Format x-axis ticks to show Year-Month
)

fig.show()
```

---



### Descripcion:

4. Ventas Mensuales con Resalte del Mes Pico

Tipo de gráfico: Gráfico de Barras (con una barra resaltada)
Propósito: Mostrar las ventas de cada mes como barras, pero con la barra correspondiente a "Abril de 1998" ($123,798.68) destacada con un color diferente o una anotación para enfatizar el mes de mayores ventas.
Tablas utilizadas: `Orders`, `Order_Details`

### Codigo:

```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

# Configuración de la conexión a la base de datos
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

# 1. Consulta SQL (QUERY)
QUERY = """
SELECT
    TO_CHAR(o.order_date, 'YYYY-MM') AS month_year,
    SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_sales
FROM
    orders o
JOIN
    order_details od ON o.order_id = od.order_id
GROUP BY
    month_year
ORDER BY
    month_year;
"""

# 2. Carga de datos con pandas
df = pd.read_sql_query(QUERY, engine)

# Convertir month_year a tipo datetime para un orden correcto en el eje X
df['month_year_dt'] = pd.to_datetime(df['month_year'])
df = df.sort_values('month_year_dt')

# Crear una columna para resaltar el mes específico
df['highlight'] = df['month_year'].apply(lambda x: 'Abril 1998 (Pico)' if x == '1998-04' else 'Otros Meses')

# 3. Generación de la gráfica
fig = px.bar(
    df,
    x='month_year',
    y='total_sales',
    color='highlight',
    color_discrete_map={
        'Abril 1998 (Pico)': '#EF553B',  # Color para el mes pico
        'Otros Meses': '#636EFA'       # Color para los otros meses
    },
    title='Ventas Mensuales con Resalte del Mes Pico',
    labels={
        'month_year': 'Mes y Año',
        'total_sales': 'Ventas Totales ($)',
        'highlight': 'Resalte'
    },
    hover_data={'total_sales': ':.2f'} # Formato de hover para las ventas
)

# Actualizar el layout para mejor visualización
fig.update_layout(
    xaxis_title='Mes y Año',
    yaxis_title='Ventas Totales ($)',
    xaxis={'categoryorder':'array', 'categoryarray':df['month_year']}, # Asegura el orden correcto en el eje X
    legend_title_text='Categoría'
)

# Mostrar la gráfica
fig.show()
```

---



### Descripcion:

5. Top 3 Empleados por Ventas

Tipo de gráfico: Gráfico de Barras Horizontal
Propósito: Comparar visualmente el rendimiento de ventas de los 3 empleados principales, haciendo fácil ver la diferencia en los ingresos generados por Margaret Peacock, Janet Leverling y Nancy Davolio.
Tablas utilizadas: `Employees`, `Orders`, `Order_Details`

### Codigo:

```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

QUERY = """
SELECT
    e.first_name || ' ' || e.last_name AS employee_name,
    SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_sales
FROM
    employees AS e
JOIN
    orders AS o ON e.employee_id = o.employee_id
JOIN
    order_details AS od ON o.order_id = od.order_id
GROUP BY
    e.employee_id, employee_name
ORDER BY
    total_sales DESC
LIMIT 3;
"""

df = pd.read_sql_query(QUERY, engine)

df_sorted = df.sort_values('total_sales', ascending=True)

fig = px.bar(
    df_sorted,
    x='total_sales',
    y='employee_name',
    orientation='h',
    title='Top 3 Empleados por Ventas',
    labels={
        'total_sales': 'Ventas Totales',
        'employee_name': 'Empleado'
    }
)

fig.show()
```

---



### Descripcion:

6. Top 5 Clientes por Gasto Total

Tipo de gráfico: Gráfico de Barras Horizontal
Propósito: Resaltar los 5 clientes que más han gastado, mostrando claramente la contribución de cada compañía a los ingresos totales y su ranking.
Tablas utilizadas: `Customers`, `Orders`, `Order_Details`

### Codigo:

```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

# Database connection details
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

# SQL Query to get the top 5 customers by total spending
QUERY = """
SELECT
    c.company_name,
    SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_spent
FROM
    customers AS c
JOIN
    orders AS o ON c.customer_id = o.customer_id
JOIN
    order_details AS od ON o.order_id = od.order_id
GROUP BY
    c.customer_id, c.company_name
ORDER BY
    total_spent DESC
LIMIT 5;
"""

# Load data into DataFrame
df = pd.read_sql_query(QUERY, engine)

# Sort the DataFrame by total_spent in ascending order for correct plotting
# (Plotly's horizontal bar chart will place the first item in 'y' at the bottom,
# so sorting ascending ensures the highest value is at the top of the chart).
df = df.sort_values(by='total_spent', ascending=True)

# Generate the horizontal bar chart
fig = px.bar(
    df,
    x='total_spent',
    y='company_name',
    orientation='h',  # Set orientation to horizontal
    title='Top 5 Clientes por Gasto Total',
    labels={
        'total_spent': 'Gasto Total',
        'company_name': 'Nombre de la Compañía'
    }
)

# Customize layout for better readability
fig.update_layout(
    xaxis_title='Gasto Total',
    yaxis_title='Nombre de la Compañía',
    # Ensure the y-axis categories are displayed in the order of the DataFrame
    yaxis={'categoryorder':'total ascending'} # This ensures the smallest value is at the bottom, largest at the top
)


fig.show()
```

---



### Descripcion:

7. Top 5 Productos por Cantidad Vendida

Tipo de gráfico: Gráfico de Barras Horizontal
Propósito: Visualizar los productos más populares en términos de unidades vendidas, ayudando a identificar los artículos clave para la gestión de inventario y promociones.
Tablas utilizadas: `Products`, `Order_Details`

### Codigo:

```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

# Configuración de la conexión a la base de datos
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

# 1. Consulta SQL (QUERY)
QUERY = """
SELECT
    p.product_name,
    SUM(od.quantity) AS total_quantity_sold
FROM
    products AS p
JOIN
    order_details AS od ON p.product_id = od.product_id
GROUP BY
    p.product_name
ORDER BY
    total_quantity_sold DESC
LIMIT 5;
"""

# 2. Carga de datos con pandas
df = pd.read_sql_query(QUERY, engine)

# Asegurarse de que el DataFrame esté ordenado para la visualización (Plotly Express a veces reordena)
df = df.sort_values(by='total_quantity_sold', ascending=True)

# 3. Generación de la gráfica
fig = px.bar(
    df,
    x='total_quantity_sold',
    y='product_name',
    orientation='h',
    title='Top 5 Productos por Cantidad Vendida',
    labels={
        'total_quantity_sold': 'Cantidad Total Vendida',
        'product_name': 'Producto'
    }
)

fig.update_layout(
    xaxis_title='Cantidad Total Vendida',
    yaxis_title='Producto',
    showlegend=False
)

fig.show()
```

---



### Descripcion:

8. Impacto de Descuentos (Promedio y Total)

Tipo de gráfico: Dos Indicadores (Number)
Propósito: Mostrar simultáneamente el porcentaje promedio de descuento y el monto total de dinero "perdido" por descuentos. Esto ofrece una visión clara y concisa del impacto financiero de las políticas de descuento.
Tablas utilizadas: `Order_Details`

### Codigo:

```python
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import URL, create_engine

# Database connection details
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

# SQL Query to get average discount percentage and total discount amount
QUERY = """
SELECT
    AVG(discount) * 100 AS average_discount_percentage,
    SUM(unit_price * quantity * discount) AS total_discount_amount
FROM
    order_details;
"""

# Load data into DataFrame
df = pd.read_sql_query(QUERY, engine)

# Extract the calculated values
avg_discount_pct = df['average_discount_percentage'].iloc[0]
total_discount_loss = df['total_discount_amount'].iloc[0]

# Create the Plotly figure
fig = go.Figure()

# Add the indicator for Average Discount Percentage
fig.add_trace(go.Indicator(
    mode="number",
    value=avg_discount_pct,
    title={"text": "Porcentaje Promedio de Descuento"},
    number={'suffix': "%", 'valueformat': ".2f"}, # Format to 2 decimal places and add '%' suffix
    domain={'row': 0, 'column': 0}
))

# Add the indicator for Total Money Lost due to Discounts
fig.add_trace(go.Indicator(
    mode="number",
    value=total_discount_loss,
    title={"text": "Monto Total Perdido por Descuentos"},
    number={'prefix': "$", 'valueformat': ".2f"}, # Format to 2 decimal places and add '$' prefix
    domain={'row': 0, 'column': 1}
))

# Update layout for the figure
fig.update_layout(
    grid={'rows': 1, 'columns': 2, 'pattern': "independent"}, # Arrange indicators in a 1x2 grid
    title_text="Impacto de Descuentos (Promedio y Total)",
    height=300, # Set a fixed height for the figure
    margin=dict(l=20, r=20, t=80, b=20) # Adjust margins
)

# Show the figure
fig.show()
```

---



### Descripcion:

9. Eficiencia de Transportistas (Tiempo Promedio de Envío)

Tipo de gráfico: Gráfico de Barras Horizontal
Propósito: Comparar el tiempo promedio de envío entre los diferentes transportistas, permitiendo identificar rápidamente cuál es el más eficiente y cuál podría necesitar mejoras o renegociación.
Tablas utilizadas: `Shippers`, `Orders`

### Codigo:

```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

# Configuración de la conexión a la base de datos
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

# 1. Consulta SQL para obtener los datos necesarios
QUERY = """
SELECT
    s.company_name,
    AVG(EXTRACT(DAY FROM (o.shipped_date - o.order_date))) AS average_shipping_days
FROM
    orders AS o
JOIN
    shippers AS s ON o.ship_via = s.shipper_id
WHERE
    o.shipped_date IS NOT NULL AND o.order_date IS NOT NULL
GROUP BY
    s.company_name
ORDER BY
    average_shipping_days ASC;
"""

# 2. Carga de datos con pandas
df = pd.read_sql_query(QUERY, engine)

# 3. Generación de la gráfica con plotly
fig = px.bar(
    df,
    x="average_shipping_days",
    y="company_name",
    orientation="h",
    title="Eficiencia de Transportistas: Tiempo Promedio de Envío",
    labels={
        "average_shipping_days": "Tiempo Promedio de Envío (Días)",
        "company_name": "Transportista"
    }
)

fig.update_layout(yaxis={'categoryorder':'total ascending'}) # Asegura que el eje Y se ordene por el valor de X
fig.show()
```

---



### Descripcion:

10. Ventas Acumuladas a lo Largo del Tiempo

Tipo de gráfico: Gráfico de Área Acumulada
Propósito: Mostrar el crecimiento total de las ventas acumuladas desde el inicio del período hasta el final, dando una perspectiva de cómo se ha construido el total de ventas a lo largo del tiempo.
Tablas utilizadas: `Orders`, `Order_Details`

### Codigo:

```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

QUERY = """
WITH DailySales AS (
    SELECT
        o.order_date,
        SUM(od.unit_price * od.quantity * (1 - od.discount)) AS daily_sales
    FROM
        orders AS o
    JOIN
        order_details AS od ON o.order_id = od.order_id
    GROUP BY
        o.order_date
)
SELECT
    order_date,
    SUM(daily_sales) OVER (ORDER BY order_date) AS cumulative_sales
FROM
    DailySales
ORDER BY
    order_date;
"""

df = pd.read_sql_query(QUERY, engine)

fig = px.area(
    df,
    x="order_date",
    y="cumulative_sales",
    title="Ventas Acumuladas a lo Largo del Tiempo",
    labels={
        "order_date": "Fecha del Pedido",
        "cumulative_sales": "Ventas Acumuladas"
    }
)

fig.update_layout(hovermode="x unified")

fig.show()
```

---



### Descripcion:

11. Distribución de Ventas por Categoría de Producto

Tipo de gráfico: Gráfico de Tarta (Pie Chart) o Donut Chart
Propósito: Entender la proporción de las ventas totales que proviene de cada categoría de producto, identificando las categorías más rentables o populares.
Tablas utilizadas: `Categories`, `Products`, `Order_Details`

### Codigo:

```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

# Configuración de la URL de la base de datos
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

# Creación del motor de SQLAlchemy
engine = create_engine(db_url)

# Consulta SQL para obtener las ventas totales por categoría de producto
QUERY = """
SELECT
    c.category_name,
    SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_sales
FROM
    categories AS c
JOIN
    products AS p ON c.category_id = p.category_id
JOIN
    order_details AS od ON p.product_id = od.product_id
GROUP BY
    c.category_name
ORDER BY
    total_sales DESC;
"""

# Carga de datos en un DataFrame de pandas
df = pd.read_sql_query(QUERY, engine)

# Generación del gráfico de tarta (Pie Chart)
fig = px.pie(
    df,
    values='total_sales',
    names='category_name',
    title='Distribución de Ventas por Categoría de Producto',
    hole=0.3, # Para hacer un Donut Chart
    labels={'category_name': 'Categoría de Producto', 'total_sales': 'Ventas Totales'},
    hover_data=['total_sales']
)

# Personalización del layout
fig.update_traces(textposition='inside', textinfo='percent+label')
fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')

# Mostrar la gráfica
fig.show()
```

---



### Descripcion:

12. Ventas por Empleado a lo Largo del Tiempo (Contribución Mensual)

Tipo de gráfico: Gráfico de Barras Apiladas (Stacked Bar Chart)
Propósito: Visualizar la contribución de ventas de cada empleado por mes. Esto permite ver no solo quiénes son los mejores vendedores en general, sino también cómo su rendimiento varía mes a mes y cómo contribuyen al total mensual.
Tablas utilizadas: `Employees`, `Orders`, `Order_Details`

### Codigo:

```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

# Configuración de la conexión a la base de datos
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

# 1. Consulta SQL (QUERY)
QUERY = """
SELECT
    EXTRACT(YEAR FROM o.order_date) AS order_year,
    EXTRACT(MONTH FROM o.order_date) AS order_month,
    e.first_name || ' ' || e.last_name AS employee_name,
    SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_sales
FROM
    employees AS e
JOIN
    orders AS o ON e.employee_id = o.employee_id
JOIN
    order_details AS od ON o.order_id = od.order_id
GROUP BY
    order_year,
    order_month,
    employee_name
ORDER BY
    order_year,
    order_month,
    employee_name;
"""

# 2. Carga de datos con pandas
df = pd.read_sql_query(QUERY, engine)

# Asegurarse de que el mes tenga dos dígitos para una correcta ordenación en el eje X
df['order_month_str'] = df['order_month'].astype(str).str.zfill(2)
df['year_month'] = df['order_year'].astype(str) + '-' + df['order_month_str']

# Ordenar el DataFrame por año y mes para asegurar la correcta secuencia en el gráfico
df = df.sort_values(by=['order_year', 'order_month'])

# 3. Generación de la gráfica
fig = px.bar(
    df,
    x='year_month',
    y='total_sales',
    color='employee_name',
    title='Ventas por Empleado a lo Largo del Tiempo (Contribución Mensual)',
    labels={
        'year_month': 'Mes',
        'total_sales': 'Ventas Totales',
        'employee_name': 'Empleado'
    },
    barmode='stack' # Para un gráfico de barras apiladas
)

# Ajustar el layout para mejor visualización si es necesario
fig.update_layout(xaxis_title='Mes', yaxis_title='Ventas Totales')

# Mostrar la gráfica
fig.show()
```

---



### Descripcion:

13. Dispersión de Descuentos por Producto

Tipo de gráfico: Gráfico de Dispersión (Scatter Plot) o Box Plot
Propósito: Analizar si hay una correlación entre el precio unitario de un producto y el descuento aplicado, o la distribución de descuentos por producto. Un `Box Plot` por `product_id` o `category_id` de los descuentos podría mostrar la variabilidad.
Tablas utilizadas: `Products`, `Order_Details`

### Codigo:

```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

# Database connection details
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

# 1. Consulta SQL (QUERY)
QUERY = """
SELECT
    p.product_name,
    od.discount
FROM
    products AS p
JOIN
    order_details AS od ON p.product_id = od.product_id;
"""

# 2. Carga de datos con pandas
df = pd.read_sql_query(QUERY, engine)

# Convert discount to percentage for better readability
df['discount_percentage'] = df['discount'] * 100

# 3. Generación de la gráfica
fig = px.box(
    df,
    x='product_name',
    y='discount_percentage',
    title='Distribución de Descuentos por Producto',
    labels={
        'product_name': 'Producto',
        'discount_percentage': 'Descuento (%)'
    }
)

# Rotate x-axis labels for better readability if product names are long
fig.update_layout(xaxis_tickangle=-45)

fig.show()
```

---



### Descripcion:

14. Volumen de Órdenes por País de Envío

Tipo de gráfico: Mapa Coroplético (Choropleth Map)
Propósito: Visualizar geográficamente de dónde provienen los pedidos (o a dónde se envían), identificando las regiones o países con mayor actividad de ventas.
Tablas utilizadas: `Orders` (columna `ShipCountry`), `Customers` (columna `Country`)

### Codigo:

```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

# Configuración de la conexión a la base de datos
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

# Consulta SQL para obtener el volumen de órdenes por país de envío
QUERY = """
SELECT
    ship_country,
    COUNT(order_id) AS total_orders
FROM
    orders
GROUP BY
    ship_country
ORDER BY
    total_orders DESC;
"""

# Carga de datos en un DataFrame de pandas
df = pd.read_sql_query(QUERY, engine)

# Generación del mapa coroplético
fig = px.choropleth(
    df,
    locations="ship_country",
    locationmode="country names",
    color="total_orders",
    hover_name="ship_country",
    hover_data={"total_orders": True},
    color_continuous_scale=px.colors.sequential.Plasma,
    title="Volumen de Órdenes por País de Envío"
)

# Mostrar la gráfica
fig.show()
```

---



### Descripcion:

15. Relación entre Cantidad y Descuento en los Detalles del Pedido

Tipo de gráfico: Gráfico de Dispersión (Scatter Plot)
Propósito: Investigar si la cantidad de un producto comprado en un solo detalle de pedido influye en el descuento aplicado. Se puede colorear por `product_id` o `category_id` para buscar patrones.
Tablas utilizadas: `Order_Details`

### Codigo:

```python
import pandas as pd
import plotly.express as px
from sqlalchemy import URL, create_engine

# Configuración de la conexión a la base de datos
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5434,
    database="northwind"
)

engine = create_engine(db_url)

# 1. Consulta SQL
QUERY = """
SELECT
    quantity,
    discount,
    product_id
FROM
    order_details;
"""

# 2. Carga de datos con pandas
df = pd.read_sql_query(QUERY, engine)

# 3. Generación de la gráfica
fig = px.scatter(
    df,
    x="quantity",
    y="discount",
    color="product_id",
    title="Relación entre Cantidad y Descuento por Producto en los Detalles del Pedido",
    labels={
        "quantity": "Cantidad de Producto",
        "discount": "Descuento Aplicado",
        "product_id": "ID de Producto"
    }
)

fig.show()
```

---


