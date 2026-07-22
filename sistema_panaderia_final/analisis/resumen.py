from analisis.analisis_ventas import (
    cantidad_total_vendida,
    desviacion_ventas,
    obtener_ventas,
    producto_mas_vendido,
    producto_mayor_ingreso,
    productos_stock_bajo,
    promedio_venta,
    unidades_por_producto,
    ventas_por_fecha,
    ventas_por_mes,
    ventas_por_producto,
    ventas_totales,
)
from analisis.graficos import generar_graficos
from analisis.limpieza_datos import limpiar_datos


def _serie_a_diccionario(serie, convertir=int):
    return {str(indice): convertir(valor) for indice, valor in serie.items()}


def _serie_a_filas(serie):
    return [
        {"periodo": str(indice), "total": round(float(valor), 2)}
        for indice, valor in serie.items()
    ]


def generar_resumen(ruta_db=None):
    """Genera métricas coherentes usando únicamente pedidos pagados."""
    df = limpiar_datos(obtener_ventas(ruta_db=ruta_db, solo_pagadas=True))

    ventas_fecha = ventas_por_fecha(df)
    ventas_mes = ventas_por_mes(df)
    ingresos_producto = ventas_por_producto(df)
    unidades_producto = unidades_por_producto(df)
    stock_bajo = productos_stock_bajo(limite=30, ruta_db=ruta_db)

    pedidos_pagados = int(df["pedido_id"].nunique()) if "pedido_id" in df else 0

    return {
        "pedidos_pagados": pedidos_pagados,
        "ventas_totales": ventas_totales(df),
        "producto_mas_vendido": producto_mas_vendido(df),
        "producto_mayor_ingreso": producto_mayor_ingreso(df),
        "promedio_venta": promedio_venta(df),
        "cantidad_total_vendida": cantidad_total_vendida(df),
        "desviacion_ventas": desviacion_ventas(df),
        "ventas_fecha": _serie_a_diccionario(ventas_fecha, float),
        "productos": _serie_a_diccionario(unidades_producto, int),
        "ingresos_producto": _serie_a_diccionario(ingresos_producto, float),
        "ventas_dia": _serie_a_filas(ventas_fecha.sort_index(ascending=False)),
        "ventas_mes": _serie_a_filas(ventas_mes.sort_index(ascending=False)),
        "productos_bajo_stock": stock_bajo.to_dict(orient="records"),
    }


def generar_recursos_graficos(ruta_db=None, carpeta_salida="resultados"):
    """Exporta gráficos Matplotlib como evidencia; no se muestran en el dashboard."""
    df = limpiar_datos(obtener_ventas(ruta_db=ruta_db, solo_pagadas=True))
    return generar_graficos(df, carpeta_salida)
