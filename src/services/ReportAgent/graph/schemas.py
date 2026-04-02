
from pydantic import BaseModel
from typing import TypedDict, List, Optional


class ChartsDict(TypedDict):
    charts : List[str]


class StructureIdeas(BaseModel):
    charts_dict : ChartsDict








if __name__ == "__main__":
    charts_dict = {
    "charts": [
        "1. Evolución de las Ventas Mensuales\n*   **Tipo de gráfico:** Gráfico de Líneas (`px.line`).\n*   **Propósito:** Mostrar la tendencia de las ventas a lo largo del tiempo. Permite identificar visualmente la estacionalidad, el crecimiento y el mes pico de ventas (abril de 1998) mencionado en el análisis.\n*   **Tablas utilizadas:** `Orders`, `Order_Details`.",
        "2. Comparación Anual de Ventas\n*   **Tipo de gráfico:** Gráfico de Barras (`px.bar`).\n*   **Propósito:** Comparar el rendimiento de ventas total de cada año completo (1996, 1997) y el período parcial de 1998. Ayuda a entender el crecimiento interanual de un vistazo.\n*   **Tablas utilizadas:** `Orders`, `Order_Details`.",
        "3. Desglose de Ventas por Trimestre\n*   **Tipo de gráfico:** Gráfico de Anillo o Dónut (`go.Pie` con `hole`).\n*   **Propósito:** Visualizar la contribución de cada trimestre fiscal a las ventas totales. Responde a la pregunta: ¿En qué parte del año se concentran más las ventas?\n*   **Tablas utilizadas:** `Orders`, `Order_Details`.",
        "4. Mapa de Calor de Ventas Mensuales\n*   **Tipo de gráfico:** Mapa de Calor (`px.imshow` o `go.Heatmap`).\n*   **Propósito:** Identificar patrones estacionales de manera más clara. El eje X representaría los meses y el eje Y los años. El color de cada celda indicaría el volumen de ventas, facilitando la comparación de un mes específico a través de los años.\n*   **Tablas utilizadas:** `Orders`, `Order_Details`.",
        "5. Ranking de Empleados por Ventas Totales\n*   **Tipo de gráfico:** Gráfico de Barras Horizontales (`px.bar` con `orientation='h'`).\n*   **Propósito:** Visualizar de forma clara y ordenada el rendimiento de todos los empleados, no solo los 3 primeros. Las barras horizontales son ideales para etiquetas de texto largas como los nombres de los empleados.\n*   **Tablas utilizadas:** `Employees`, `Orders`, `Order_Details`.",
        "6. Contribución de cada Empleado al Total de Ventas\n*   **Tipo de gráfico:** Diagrama de Treemap (`px.treemap`).\n*   **Propósito:** Mostrar la proporción de las ventas totales que cada empleado ha generado. Este gráfico es muy efectivo para resaltar la gran contribución de los empleados con mejor desempeño (como Margaret Peacock) en comparación con el resto.\n*   **Tablas utilizadas:** `Employees`, `Orders`, `Order_Details`.",
        "7. Ranking de Clientes por Gasto Total\n*   **Tipo de gráfico:** Gráfico de Barras Horizontales (`px.bar` con `orientation='h'`).\n*   **Propósito:** Representar visualmente a los clientes más valiosos (Top 5 o Top 10) y comparar su gasto total. Facilita la identificación de los \"clientes clave\".\n*   **Tablas utilizadas:** `Customers`, `Orders`, `Order_Details`.",
        "8. Distribución Geográfica de las Ventas\n*   **Tipo de gráfico:** Mapa Geográfico (Choropleth Map, `px.choropleth`).\n*   **Propósito:** Mostrar en qué países se concentran las ventas. El color de cada país representaría el volumen total de ventas, ayudando a identificar los mercados más importantes y potenciales áreas de expansión.\n*   **Tablas utilizadas:** `Customers`, `Orders`, `Order_Details`.",
        "9. Top 10 Productos por Cantidad Vendida vs. Ingresos Generados\n*   **Tipo de gráfico:** Gráfico de Barras Agrupadas (`px.bar` con `barmode='group'`).\n*   **Propósito:** Comparar dos métricas clave para los productos más populares: la cantidad total vendida y los ingresos totales generados. Esto permite identificar productos de alto volumen pero bajo margen, y viceversa.\n*   **Tablas utilizadas:** `Products`, `Order_Details`.",
        "10. Distribución de Ingresos por Categoría de Producto\n*   **Tipo de gráfico:** Gráfico de Anillo (`go.Pie` con `hole`).\n*   **Propósito:** Entender qué categorías de productos (bebidas, condimentos, lácteos, etc.) son las más importantes para el negocio en términos de ingresos.\n*   **Tablas utilizadas:** `Products`, `Categories`, `Order_Details`.",
        "11. Impacto del Descuento en los Ingresos\n*   **Tipo de gráfico:** Gráfico de Cascada (`go.Waterfall`).\n*   **Propósito:** Ilustrar cómo se llega a las ventas netas totales. El gráfico comenzaría con los ingresos brutos (sin descuento), mostraría una barra negativa para el \"Total de Descuentos\" ($88,665.55) y terminaría con las ventas netas finales ($1,265,793.04).\n*   **Tablas utilizadas:** `Order_Details`.",
        "12. Relación entre Descuento y Cantidad Vendida\n*   **Tipo de gráfico:** Gráfico de Dispersión (`px.scatter`).\n*   **Propósito:** Explorar si existe una correlación entre el nivel de descuento aplicado en una línea de pedido y la cantidad de unidades vendidas. Cada punto representaría una línea de la tabla `order_details`.\n*   **Tablas utilizadas:** `Order_Details`.",
        "13. Comparación de Tiempos de Envío por Transportista\n*   **Tipo de gráfico:** Diagrama de Cajas (Box Plot, `px.box`).\n*   **Propósito:** Ir más allá del promedio y mostrar la distribución completa de los tiempos de envío para cada transportista. Permite ver la mediana, los cuartiles y los valores atípicos, ofreciendo una visión más completa de la consistencia y fiabilidad de cada uno.\n*   **Tablas utilizadas:** `Shippers`, `Orders`.",
        "14. Dashboard de Indicadores Clave (KPIs)\n*   **Tipo de gráfico:** Indicadores Numéricos (`go.Indicator`).\n*   **Propósito:** Presentar las métricas más importantes del informe de una manera clara y directa, como si fuera un cuadro de mando. Se pueden crear varios indicadores para: \"Ventas Totales\", \"Descuento Total\", \"Número de Pedidos\" y \"Cliente Principal\".\n*   **Tablas utilizadas:** `Orders`, `Order_Details`, `Customers`.",
        "15. Tabla Interactiva de Pedidos\n*   **Tipo de gráfico:** Tabla (`go.Table`).\n*   **Propósito:** Ofrecer una vista detallada y explorable de los datos. Una tabla interactiva con los pedidos más recientes o más grandes, que incluya cliente, empleado, fecha y valor, permitiría a los usuarios ordenar y filtrar la información para realizar sus propias micro-exploraciones.\n*   **Tablas utilizadas:** `Orders`, `Order_Details`, `Customers`, `Employees`."
        ]
    }

    y = {"hola":1}
    x = StructureIdeas(charts_dict=y)
    print(1+1)


"""
python3 -m src.services.ReportAgent.graph.schemas


"""

