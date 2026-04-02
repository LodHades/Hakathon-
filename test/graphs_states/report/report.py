import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import URL, create_engine

# --- Configuración de la Aplicación Streamlit ---
st.set_page_config(
    page_title="Reporte de Análisis Northwind",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Configuración Global de la Conexión a la Base de Datos ---
@st.cache_resource
def get_database_engine():
    """Crea y devuelve un motor de SQLAlchemy para la base de datos Northwind."""
    db_url = URL.create(
        drivername="postgresql+psycopg2",
        username="postgres",
        password="postgres",
        host="localhost",
        port=5434,
        database="northwind"
    )
    return create_engine(db_url)

engine = get_database_engine()

# --- Función para mostrar una sección de gráfica ---
def display_chart_section(title, description, chart_code_func, interpretation_text):
    """
    Muestra una sección completa con título, descripción, gráfica e interpretación.
    """
    st.header(title)
    st.markdown(description)
    st.markdown("---")

    try:
        fig = chart_code_func(engine)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("Ver Interpretación y Hallazgos"):
                st.markdown(interpretation_text)
        else:
            st.warning(f"La función de gráfica para '{title}' no devolvió una figura.")
    except Exception as e:
        st.error(f"⚠️ Error al generar la gráfica '{title}': {e}")
        st.info("Por favor, verifica la conexión a la base de datos o la consulta SQL.")
    st.markdown("---")

# --- Funciones Generadoras de Gráficas (sin cambios) ---
def chart_1_generator(engine):
    QUERY = """
    SELECT 'categories' AS table_name, COUNT(*) AS record_count FROM categories
    UNION ALL SELECT 'customer_customer_demo' AS table_name, COUNT(*) AS record_count FROM customer_customer_demo
    UNION ALL SELECT 'customer_demographics' AS table_name, COUNT(*) AS record_count FROM customer_demographics
    UNION ALL SELECT 'customers' AS table_name, COUNT(*) AS record_count FROM customers
    UNION ALL SELECT 'employee_territories' AS table_name, COUNT(*) AS record_count FROM employee_territories
    UNION ALL SELECT 'employees' AS table_name, COUNT(*) AS record_count FROM employees
    UNION ALL SELECT 'order_details' AS table_name, COUNT(*) AS record_count FROM order_details
    UNION ALL SELECT 'orders' AS table_name, COUNT(*) AS record_count FROM orders
    UNION ALL SELECT 'products' AS table_name, COUNT(*) AS record_count FROM products
    UNION ALL SELECT 'region' AS table_name, COUNT(*) AS record_count FROM region
    UNION ALL SELECT 'shippers' AS table_name, COUNT(*) AS record_count FROM shippers
    UNION ALL SELECT 'suppliers' AS table_name, COUNT(*) AS record_count FROM suppliers
    UNION ALL SELECT 'territories' AS table_name, COUNT(*) AS record_count FROM territories
    UNION ALL SELECT 'us_states' AS table_name, COUNT(*) AS record_count FROM us_states;
    """
    df = pd.read_sql_query(QUERY, engine)
    df = df.sort_values('record_count', ascending=True)
    fig = px.bar(df, x='record_count', y='table_name', orientation='h', title='Número de Registros por Tabla en la Base de Datos Northwind', labels={'record_count': 'Número de Registros', 'table_name': 'Tabla'})
    return fig

def chart_2_generator(engine):
    QUERY = "SELECT SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_sales FROM order_details AS od;"
    df = pd.read_sql_query(QUERY, engine)
    total_sales_value = df['total_sales'].iloc[0]
    fig = go.Figure(go.Indicator(mode="number", value=total_sales_value, title={"text": "<b>Ventas Totales Acumuladas</b>"}, number={'prefix': "$", 'valueformat': ".2f"}))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

def chart_3_generator(engine):
    QUERY = """
    SELECT EXTRACT(YEAR FROM o.order_date) AS sales_year, EXTRACT(MONTH FROM o.order_date) AS sales_month, SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_sales
    FROM orders AS o JOIN order_details AS od ON o.order_id = od.order_id
    WHERE o.order_date >= '1996-07-01' AND o.order_date < '1998-06-01'
    GROUP BY sales_year, sales_month ORDER BY sales_year, sales_month;
    """
    df = pd.read_sql_query(QUERY, engine)
    df['month_year'] = pd.to_datetime(df['sales_year'].astype(str) + '-' + df['sales_month'].astype(str) + '-01')
    fig = px.line(df, x='month_year', y='total_sales', markers=True, title='Tendencia de Ventas Mensuales a lo Largo del Tiempo (Julio 1996 - Mayo 1998)')
    fig.update_layout(xaxis_title='Mes y Año', yaxis_title='Ventas Totales', xaxis=dict(tickformat="%Y-%m"))
    return fig

def chart_4_generator(engine):
    QUERY = "SELECT TO_CHAR(o.order_date, 'YYYY-MM') AS month_year, SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_sales FROM orders o JOIN order_details od ON o.order_id = od.order_id GROUP BY month_year ORDER BY month_year;"
    df = pd.read_sql_query(QUERY, engine)
    df['month_year_dt'] = pd.to_datetime(df['month_year'])
    df = df.sort_values('month_year_dt')
    df['highlight'] = df['month_year'].apply(lambda x: 'Abril 1998 (Pico)' if x == '1998-04' else 'Otros Meses')
    fig = px.bar(df, x='month_year', y='total_sales', color='highlight', color_discrete_map={'Abril 1998 (Pico)': '#EF553B', 'Otros Meses': '#636EFA'}, title='Ventas Mensuales con Resalte del Mes Pico', labels={'month_year': 'Mes y Año', 'total_sales': 'Ventas Totales ($)', 'highlight': 'Resalte'}, hover_data={'total_sales': ':.2f'})
    fig.update_layout(xaxis_title='Mes y Año', yaxis_title='Ventas Totales ($)', xaxis={'categoryorder':'array', 'categoryarray':df['month_year']}, legend_title_text='Categoría')
    return fig

def chart_5_generator(engine):
    QUERY = "SELECT e.first_name || ' ' || e.last_name AS employee_name, SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_sales FROM employees AS e JOIN orders AS o ON e.employee_id = o.employee_id JOIN order_details AS od ON o.order_id = od.order_id GROUP BY e.employee_id, employee_name ORDER BY total_sales DESC LIMIT 3;"
    df = pd.read_sql_query(QUERY, engine)
    df_sorted = df.sort_values('total_sales', ascending=True)
    fig = px.bar(df_sorted, x='total_sales', y='employee_name', orientation='h', title='Top 3 Empleados por Ventas', labels={'total_sales': 'Ventas Totales', 'employee_name': 'Empleado'})
    return fig

def chart_6_generator(engine):
    QUERY = "SELECT c.company_name, SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_spent FROM customers AS c JOIN orders AS o ON c.customer_id = o.customer_id JOIN order_details AS od ON o.order_id = od.order_id GROUP BY c.customer_id, c.company_name ORDER BY total_spent DESC LIMIT 5;"
    df = pd.read_sql_query(QUERY, engine)
    df = df.sort_values(by='total_spent', ascending=True)
    fig = px.bar(df, x='total_spent', y='company_name', orientation='h', title='Top 5 Clientes por Gasto Total', labels={'total_spent': 'Gasto Total', 'company_name': 'Nombre de la Compañía'})
    fig.update_layout(xaxis_title='Gasto Total', yaxis_title='Nombre de la Compañía', yaxis={'categoryorder':'total ascending'})
    return fig

def chart_7_generator(engine):
    QUERY = "SELECT p.product_name, SUM(od.quantity) AS total_quantity_sold FROM products AS p JOIN order_details AS od ON p.product_id = od.product_id GROUP BY p.product_name ORDER BY total_quantity_sold DESC LIMIT 5;"
    df = pd.read_sql_query(QUERY, engine)
    df = df.sort_values(by='total_quantity_sold', ascending=True)
    fig = px.bar(df, x='total_quantity_sold', y='product_name', orientation='h', title='Top 5 Productos por Cantidad Vendida', labels={'total_quantity_sold': 'Cantidad Total Vendida', 'product_name': 'Producto'})
    fig.update_layout(xaxis_title='Cantidad Total Vendida', yaxis_title='Producto', showlegend=False)
    return fig

def chart_8_generator(engine):
    QUERY = "SELECT AVG(discount) * 100 AS average_discount_percentage, SUM(unit_price * quantity * discount) AS total_discount_amount FROM order_details;"
    df = pd.read_sql_query(QUERY, engine)
    avg_discount_pct = df['average_discount_percentage'].iloc[0]
    total_discount_loss = df['total_discount_amount'].iloc[0]
    fig = go.Figure()
    fig.add_trace(go.Indicator(mode="number", value=avg_discount_pct, title={"text": "Porcentaje Promedio de Descuento"}, number={'suffix': "%", 'valueformat': ".2f"}, domain={'row': 0, 'column': 0}))
    fig.add_trace(go.Indicator(mode="number", value=total_discount_loss, title={"text": "Monto Total Perdido por Descuentos"}, number={'prefix': "$", 'valueformat': ".2f"}, domain={'row': 0, 'column': 1}))
    fig.update_layout(grid={'rows': 1, 'columns': 2, 'pattern': "independent"}, title_text="Impacto de Descuentos (Promedio y Total)", height=300, margin=dict(l=20, r=20, t=80, b=20))
    return fig

def chart_9_generator(engine):
    QUERY = "SELECT s.company_name, AVG(EXTRACT(DAY FROM (o.shipped_date - o.order_date))) AS average_shipping_days FROM orders AS o JOIN shippers AS s ON o.ship_via = s.shipper_id WHERE o.shipped_date IS NOT NULL AND o.order_date IS NOT NULL GROUP BY s.company_name ORDER BY average_shipping_days ASC;"
    df = pd.read_sql_query(QUERY, engine)
    fig = px.bar(df, x="average_shipping_days", y="company_name", orientation="h", title="Eficiencia de Transportistas: Tiempo Promedio de Envío", labels={"average_shipping_days": "Tiempo Promedio de Envío (Días)", "company_name": "Transportista"})
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

def chart_10_generator(engine):
    QUERY = """
    WITH DailySales AS (
        SELECT o.order_date, SUM(od.unit_price * od.quantity * (1 - od.discount)) AS daily_sales
        FROM orders AS o JOIN order_details AS od ON o.order_id = od.order_id GROUP BY o.order_date
    )
    SELECT order_date, SUM(daily_sales) OVER (ORDER BY order_date) AS cumulative_sales FROM DailySales ORDER BY order_date;
    """
    df = pd.read_sql_query(QUERY, engine)
    fig = px.area(df, x="order_date", y="cumulative_sales", title="Ventas Acumuladas a lo Largo del Tiempo", labels={"order_date": "Fecha del Pedido", "cumulative_sales": "Ventas Acumuladas"})
    fig.update_layout(hovermode="x unified")
    return fig

def chart_11_generator(engine):
    QUERY = "SELECT c.category_name, SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_sales FROM categories AS c JOIN products AS p ON c.category_id = p.category_id JOIN order_details AS od ON p.product_id = od.product_id GROUP BY c.category_name ORDER BY total_sales DESC;"
    df = pd.read_sql_query(QUERY, engine)
    fig = px.pie(df, values='total_sales', names='category_name', title='Distribución de Ventas por Categoría de Producto', hole=0.3, labels={'category_name': 'Categoría de Producto', 'total_sales': 'Ventas Totales'}, hover_data=['total_sales'])
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')
    return fig

def chart_12_generator(engine):
    QUERY = """
    SELECT EXTRACT(YEAR FROM o.order_date) AS order_year, EXTRACT(MONTH FROM o.order_date) AS order_month, e.first_name || ' ' || e.last_name AS employee_name, SUM(od.unit_price * od.quantity * (1 - od.discount)) AS total_sales
    FROM employees AS e JOIN orders AS o ON e.employee_id = o.employee_id JOIN order_details AS od ON o.order_id = od.order_id
    GROUP BY order_year, order_month, employee_name ORDER BY order_year, order_month, employee_name;
    """
    df = pd.read_sql_query(QUERY, engine)
    df['order_month_str'] = df['order_month'].astype(str).str.zfill(2)
    df['year_month'] = df['order_year'].astype(str) + '-' + df['order_month_str']
    df = df.sort_values(by=['order_year', 'order_month'])
    fig = px.bar(df, x='year_month', y='total_sales', color='employee_name', title='Ventas por Empleado a lo Largo del Tiempo (Contribución Mensual)', labels={'year_month': 'Mes', 'total_sales': 'Ventas Totales', 'employee_name': 'Empleado'}, barmode='stack')
    fig.update_layout(xaxis_title='Mes', yaxis_title='Ventas Totales')
    return fig

def chart_13_generator(engine):
    QUERY = "SELECT p.product_name, od.discount FROM products AS p JOIN order_details AS od ON p.product_id = od.product_id;"
    df = pd.read_sql_query(QUERY, engine)
    df['discount_percentage'] = df['discount'] * 100
    fig = px.box(df, x='product_name', y='discount_percentage', title='Distribución de Descuentos por Producto', labels={'product_name': 'Producto', 'discount_percentage': 'Descuento (%)'})
    fig.update_layout(xaxis_tickangle=-45, height=600)
    return fig

def chart_14_generator(engine):
    QUERY = "SELECT ship_country, COUNT(order_id) AS total_orders FROM orders GROUP BY ship_country ORDER BY total_orders DESC;"
    df = pd.read_sql_query(QUERY, engine)
    fig = px.choropleth(df, locations="ship_country", locationmode="country names", color="total_orders", hover_name="ship_country", hover_data={"total_orders": True}, color_continuous_scale=px.colors.sequential.Plasma, title="Volumen de Órdenes por País de Envío")
    return fig

def chart_15_generator(engine):
    QUERY = "SELECT quantity, discount, product_id FROM order_details;"
    df = pd.read_sql_query(QUERY, engine)
    fig = px.scatter(df, x="quantity", y="discount", color="product_id", title="Relación entre Cantidad y Descuento por Producto en los Detalles del Pedido", labels={"quantity": "Cantidad de Producto", "discount": "Descuento Aplicado", "product_id": "ID de Producto"})
    return fig

# --- Contenido del Reporte ---

st.title("Reporte de Análisis de Datos: Northwind Trading Company (1996-1998)")

st.header("Introducción")
st.markdown("""
Este informe presenta un análisis exhaustivo de las operaciones de Northwind Trading Company, abarcando el período desde **Julio de 1996 hasta Mayo de 1998**. El objetivo principal es desglosar y comprender las dinámicas de ventas, el rendimiento de los empleados, el comportamiento de los clientes y la eficiencia operativa.

A través de una serie de visualizaciones interactivas, se identificarán tendencias clave, patrones significativos, anomalías y áreas de oportunidad. Los hallazgos presentados servirán como una base sólida para la toma de decisiones estratégicas, con el fin de optimizar procesos, potenciar el crecimiento y mejorar la rentabilidad general de la empresa.
""")

st.header("Metodología")
st.markdown("""
El análisis se realizó extrayendo datos directamente de la base de datos Northwind, alojada en un servidor PostgreSQL. Se utilizaron consultas SQL para agregar y transformar los datos, enfocándose en métricas clave de ventas, clientes, productos y logística.

Posteriormente, los datos fueron procesados y visualizados en este reporte interactivo utilizando Python, con las librerías `Pandas` para la manipulación de datos y `Plotly` para la generación de gráficos. La integración se realizó a través de `Streamlit`, permitiendo una exploración dinámica de los resultados.
""")

st.header("Análisis Detallado")

# --- Sección 1: Visión General ---
display_chart_section(
    "1. Visión General de la Base de Datos",
    "Esta gráfica inicial proporciona un mapa de la estructura de datos, mostrando el volumen de registros en cada tabla. Es el punto de partida para entender la escala y el alcance de la información disponible.",
    chart_1_generator,
    """
    **Hallazgos Clave:**
    - La tabla `order_details` es, con diferencia, la más grande, con **2,155 registros**. Esto confirma que es el núcleo transaccional del negocio, donde cada fila representa un producto dentro de un pedido.
    - Las tablas `orders` (830) y `customers` (91) tienen un tamaño considerable, indicando una base de clientes y un volumen de transacciones saludables para el período analizado.
    - Se observa que las tablas `customer_customer_demo` y `customer_demographics` están vacías, lo que representa una oportunidad perdida para segmentar clientes.
    - El bajo número de `employees` (9) y `categories` (8) sugiere que el análisis sobre estas dimensiones será manejable pero crítico, ya que un pequeño número de entidades impulsa todo el negocio.
    """
)

# --- Sección 2: Desempeño General de Ventas ---
st.subheader("2.1. Desempeño General de Ventas")
display_chart_section(
    "Ventas Totales Acumuladas",
    "Este indicador muestra la métrica de rendimiento más importante: el ingreso total generado durante todo el período de análisis.",
    chart_2_generator,
    """
    **Interpretación:**
    - El ingreso total generado por Northwind entre julio de 1996 y mayo de 1998 fue de **$1,265,793.04**.
    - Esta cifra representa el valor bruto de todas las transacciones, teniendo en cuenta los descuentos aplicados. Sirve como el principal indicador de salud financiera y punto de referencia para evaluar todas las demás métricas.
    """
)

display_chart_section(
    "Tendencia de Ventas Mensuales a lo Largo del Tiempo",
    "Este gráfico de líneas traza la evolución de los ingresos mensuales, permitiendo identificar patrones estacionales, tendencias de crecimiento y meses atípicos.",
    chart_3_generator,
    """
    **Interpretación:**
    - **Tendencia de Crecimiento:** Se observa una clara tendencia ascendente en las ventas a lo largo del período. Las ventas en 1997 fueron consistentemente más altas que en 1996, y los primeros meses de 1998 muestran un crecimiento aún más acelerado.
    - **Estacionalidad:** Hay picos recurrentes hacia finales de año (Oct-Dic 1996) y una notable aceleración en la primavera de 1997 y 1998.
    - **Anomalía Positiva:** El mes de **Abril de 1998** destaca como un punto de inflexión, con un crecimiento exponencial que rompe la tendencia anterior.
    """
)

display_chart_section(
    "Ventas Mensuales con Resalte del Mes Pico",
    "Este gráfico de barras refuerza los hallazgos del gráfico de líneas, destacando visualmente el mes de mayor rendimiento para un análisis más profundo.",
    chart_4_generator,
    """
    **Hallazgo Principal:**
    - El análisis confirma que **Abril de 1998** fue el mes con el mayor volumen de ventas, alcanzando un total de **$123,798.68**.
    - Este valor es más del doble del promedio mensual y representa un evento excepcional que merece una investigación detallada. Podría deberse a grandes contratos, una campaña de marketing exitosa o la entrada en un nuevo mercado.
    """
)

display_chart_section(
    "Ventas Acumuladas a lo Largo del Tiempo",
    "Este gráfico de área muestra cómo se ha construido el ingreso total a lo largo del tiempo, ilustrando la trayectoria de crecimiento de la empresa.",
    chart_10_generator,
    """
    **Interpretación:**
    - La curva de crecimiento acumulado muestra una aceleración constante. La pendiente de la curva se vuelve notablemente más pronunciada a partir de finales de 1997 y, sobre todo, en el pico de Abril de 1998.
    - Esta visualización confirma que el crecimiento de la empresa no ha sido lineal, sino que ha ganado impulso con el tiempo, lo que es un signo de un negocio saludable y en expansión.
    """
)

# --- Sección 3: Análisis de Contribución y Rendimiento ---
st.subheader("3.1. Análisis de Contribución y Rendimiento")
display_chart_section(
    "Top 3 Empleados por Ventas",
    "Identifica a los empleados con mejor desempeño en términos de ingresos generados, destacando a los principales impulsores de ventas de la compañía.",
    chart_5_generator,
    """
    **Hallazgos Clave:**
    - Existe una clara concentración del rendimiento en un pequeño grupo de empleados.
    - **Margaret Peacock** es la vendedora estrella, con ventas totales de **$232,890.85**.
    - Le siguen de cerca **Janet Leverling** ($202,812.84) y **Nancy Davolio** ($192,107.60).
    - Juntos, estos tres empleados son responsables de una porción muy significativa de los ingresos totales de la empresa, lo que subraya su importancia estratégica.
    """
)

display_chart_section(
    "Ventas por Empleado a lo Largo del Tiempo (Contribución Mensual)",
    "Este gráfico desglosa las ventas mensuales totales por la contribución de cada empleado, permitiendo analizar la consistencia y la evolución de su rendimiento.",
    chart_12_generator,
    """
    **Interpretación:**
    - La gráfica de barras apiladas confirma visualmente el dominio de los empleados de alto rendimiento. Las secciones de color correspondientes a Margaret Peacock, Janet Leverling y Nancy Davolio son consistentemente las más grandes en casi todos los meses.
    - Es crucial observar que el pico de ventas en Abril de 1998 no fue obra de un solo empleado, sino un esfuerzo combinado en el que varios vendedores, incluidos los de mayor rendimiento, tuvieron un mes excepcional. Esto sugiere un factor externo positivo (demanda del mercado, campaña) que todo el equipo supo capitalizar.
    """
)

display_chart_section(
    "Top 5 Clientes por Gasto Total",
    "Esta visualización destaca a los clientes más valiosos para la empresa, aquellos cuyo gasto acumulado es el más alto.",
    chart_6_generator,
    """
    **Hallazgos Clave (Principio de Pareto):**
    - Al igual que con los empleados, un pequeño número de clientes genera una parte desproporcionada de los ingresos.
    - Los tres clientes principales, **QUICK-Stop** ($110,277.31), **Ernst Handel** ($104,874.98) y **Save-a-lot Markets** ($104,361.95), han gastado más de $100,000 cada uno, situándose en un nivel muy superior al resto.
    - Estos clientes son activos estratégicos y deben ser gestionados con programas de fidelización y atención personalizada para asegurar su retención.
    """
)

# --- Sección 4: Análisis de Productos y Categorías ---
st.subheader("4.1. Análisis de Productos y Categorías")
display_chart_section(
    "Distribución de Ventas por Categoría de Producto",
    "Este gráfico de dona muestra qué categorías de productos contribuyen más a los ingresos totales, identificando las áreas de negocio más rentables.",
    chart_11_generator,
    """
    **Interpretación:**
    - Las categorías de **Bebidas (Beverages)** y **Productos Lácteos (Dairy Products)** son las dominantes, representando la mayor parte de los ingresos.
    - Estas dos categorías son el motor principal de las ventas de Northwind y donde se deben centrar los esfuerzos de marketing, gestión de inventario y desarrollo de nuevos productos.
    - Otras categorías como **Condimentos (Condiments)** y **Confitería (Confections)** también tienen una participación relevante.
    """
)

display_chart_section(
    "Top 5 Productos por Cantidad Vendida",
    "Identifica los productos individuales más populares, no por ingresos, sino por el número de unidades vendidas. Es un indicador clave de la demanda y la popularidad.",
    chart_7_generator,
    """
    **Hallazgos Clave:**
    - Los productos más vendidos en términos de volumen son principalmente quesos y productos gourmet:
        1. **Camembert Pierrot** (1,577 unidades)
        2. **Raclette Courdavault** (1,496 unidades)
        3. **Gorgonzola Telino** (1,397 unidades)
    - Estos productos son los favoritos de los clientes. Su disponibilidad es crítica, y cualquier problema en su cadena de suministro podría impactar negativamente las ventas. Son candidatos ideales para promociones cruzadas y estrategias de marketing.
    """
)

# --- Sección 5: Análisis Operativo y de Eficiencia ---
st.subheader("5.1. Análisis Operativo y de Eficiencia")
display_chart_section(
    "Impacto de Descuentos (Promedio y Total)",
    "Estos indicadores cuantifican el uso de descuentos y su impacto financiero directo en los ingresos de la empresa.",
    chart_8_generator,
    """
    **Interpretación Financiera:**
    - El descuento promedio aplicado en todas las transacciones es del **5.62%**. Aunque parece un porcentaje bajo, su efecto acumulado es considerable.
    - El monto total que la empresa ha dejado de percibir debido a los descuentos asciende a **$88,665.55**.
    - Este análisis revela un costo de oportunidad significativo. Es crucial evaluar si la estrategia de descuentos está generando un volumen de ventas adicional que compense esta reducción de ingresos, o si necesita ser reajustada.
    """
)

display_chart_section(
    "Dispersión de Descuentos por Producto",
    "Este diagrama de caja muestra la distribución de los descuentos aplicados a cada producto, revelando la consistencia (o inconsistencia) de la estrategia de precios.",
    chart_13_generator,
    """
    **Interpretación:**
    - La variabilidad en los descuentos es alta entre los diferentes productos. Algunos productos casi nunca se venden con descuento, mientras que otros muestran una amplia gama de descuentos aplicados (ver las "cajas" y "bigotes" largos).
    - Esta inconsistencia puede indicar una falta de una política de precios estandarizada. Los descuentos parecen aplicarse de manera discrecional en lugar de seguir una estrategia clara (por ejemplo, por volumen, por cliente, etc.).
    """
)

display_chart_section(
    "Relación entre Cantidad y Descuento en los Detalles del Pedido",
    "Este gráfico de dispersión busca una correlación entre la cantidad de un producto en un pedido y el descuento aplicado, para determinar si existen descuentos por volumen.",
    chart_15_generator,
    """
    **Hallazgo Principal:**
    - No se observa una correlación clara y sistemática entre la cantidad comprada y el descuento ofrecido. Los puntos están dispersos sin un patrón ascendente definido.
    - Esto refuerza la idea de que la empresa carece de una estrategia de descuentos por volumen formalizada. Implementar una podría incentivar compras más grandes y estandarizar el proceso de ventas.
    """
)

display_chart_section(
    "Eficiencia de Transportistas: Tiempo Promedio de Envío",
    "Compara el rendimiento de los diferentes socios logísticos en función del tiempo que tardan en entregar los pedidos.",
    chart_9_generator,
    """
    **Hallazgos Clave:**
    - Existen diferencias notables en la eficiencia de los transportistas.
    - **Federal Shipping** es el más rápido, con un tiempo de envío promedio de **7.47 días**.
    - **United Package** es el más lento, con un promedio de **9.23 días**.
    - Esta diferencia de casi dos días puede tener un impacto significativo en la satisfacción del cliente. La elección del transportista es un factor clave en la experiencia de compra.
    """
)

display_chart_section(
    "Volumen de Órdenes por País de Envío",
    "Este mapa coroplético visualiza la distribución geográfica de los pedidos, identificando los mercados clave para la empresa.",
    chart_14_generator,
    """
    **Interpretación Geográfica:**
    - Los principales mercados de Northwind se concentran en **América del Norte (especialmente EE. UU.)** y **Europa Occidental (con Alemania, Reino Unido y Austria a la cabeza)**.
    - También hay una presencia significativa en **América del Sur (Brasil, Venezuela)**.
    - Este mapa es fundamental para dirigir los esfuerzos de marketing internacional, adaptar las estrategias logísticas a las regiones con mayor volumen y explorar oportunidades de expansión en mercados adyacentes.
    """
)

# --- Conclusiones y Recomendaciones ---
st.header("Conclusiones Generales")
st.markdown("""
1.  **Crecimiento Sostenido:** La empresa experimentó un crecimiento robusto y acelerado durante el período 1996-1998, con un pico de rendimiento excepcional en Abril de 1998 que indica un alto potencial de mercado.

2.  **Concentración de Rendimiento (Principio de Pareto):** El éxito de la compañía depende en gran medida de un pequeño grupo de empleados de alto rendimiento (Margaret Peacock, Janet Leverling) y de un núcleo de clientes de alto valor (QUICK-Stop, Ernst Handel).

3.  **Foco en Categorías Clave:** Las categorías de Bebidas y Productos Lácteos son el pilar de los ingresos, y productos específicos como el queso Camembert Pierrot impulsan el volumen de ventas, demostrando una fuerte demanda en el nicho gourmet.

4.  **Oportunidades en la Estrategia de Precios:** La política de descuentos actual es inconsistente y representa un costo de oportunidad de casi $90,000. No parece estar ligada a una estrategia de volumen, lo que sugiere un área clara para la optimización.

5.  **Eficiencia Logística Variable:** La elección del transportista tiene un impacto directo en los tiempos de entrega, con diferencias de hasta dos días entre el más rápido y el más lento, afectando directamente la experiencia del cliente.
""")

st.header("Recomendaciones Estratégicas")
st.markdown("""
*   **Gestión de Cuentas Clave y Fidelización:**
    *   **Acción:** Implementar un programa de gestión de cuentas clave (KAM) para los 3-5 clientes principales.
    *   **Justificación:** Dado que una pequeña base de clientes genera una gran parte de los ingresos (Gráfica 6), asegurar su lealtad con un servicio personalizado, ofertas exclusivas y comunicación proactiva es fundamental para la estabilidad a largo plazo.

*   **Programas de Incentivos y Desarrollo de Talento:**
    *   **Acción:** Crear un programa de incentivos basado en el rendimiento de ventas y organizar sesiones de formación lideradas por los mejores vendedores, como Margaret Peacock.
    *   **Justificación:** Reconocer y recompensar a los empleados de alto rendimiento (Gráfica 5) los mantendrá motivados. Utilizar su experiencia para capacitar al resto del equipo puede elevar el rendimiento general del departamento de ventas (Gráfica 12).

*   **Optimización de la Estrategia de Descuentos:**
    *   **Acción:** Definir y estandarizar una política de descuentos clara. Implementar un sistema de descuentos por volumen.
    *   **Justificación:** El análisis muestra que los descuentos son discrecionales y costosos (Gráficas 8, 13, 15). Una política estandarizada reducirá la pérdida de ingresos y una estrategia de descuentos por volumen incentivará a los clientes a realizar pedidos más grandes.

*   **Optimización de la Cadena de Suministro y Logística:**
    *   **Acción:** Priorizar el uso de **Federal Shipping** para envíos críticos o para clientes de alto valor. Renegociar las tarifas con todos los transportistas basándose en su rendimiento.
    *   **Justificación:** La velocidad de entrega es un diferenciador clave (Gráfica 9). Utilizar al socio logístico más eficiente mejorará la satisfacción del cliente y puede justificar un costo premium.

*   **Foco en Marketing de Productos y Categorías:**
    *   **Acción:** Lanzar campañas de marketing centradas en las categorías de Bebidas y Productos Lácteos. Crear promociones cruzadas con los productos más vendidos como el Camembert Pierrot.
    *   **Justificación:** Capitalizar la popularidad existente (Gráficas 7 y 11) es la forma más eficiente de impulsar las ventas. Asegurar un inventario robusto para estos productos es crítico para satisfacer la demanda.
""")