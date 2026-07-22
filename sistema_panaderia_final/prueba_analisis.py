from pathlib import Path

from analisis.analisis_ventas import (
    cantidad_total_vendida,
    desviacion_ventas,
    obtener_ventas,
    producto_mas_vendido,
    producto_mayor_ingreso,
    productos_stock_bajo,
    promedio_venta,
    ventas_por_fecha,
    ventas_totales,
)
from analisis.graficos import generar_graficos
from analisis.limpieza_datos import limpiar_datos


def main():
    df = limpiar_datos(obtener_ventas(solo_pagadas=True))

    print("DETALLE DE VENTAS PAGADAS")
    print(df if not df.empty else "Sin ventas pagadas")
    print("-" * 50)
    print("Ventas totales:", ventas_totales(df))
    print("Producto más vendido:", producto_mas_vendido(df))
    print("Producto con mayor ingreso:", producto_mayor_ingreso(df))
    print("Cantidad vendida:", cantidad_total_vendida(df))
    print("Promedio por pedido:", promedio_venta(df))
    print("Desviación de ventas:", desviacion_ventas(df))
    print("Ventas por fecha:")
    print(ventas_por_fecha(df))
    print("Productos con stock bajo:")
    print(productos_stock_bajo(limite=30))

    rutas = generar_graficos(df, Path(__file__).resolve().parent / "resultados")
    print("Gráficos generados:")
    for nombre, ruta in rutas.items():
        print(f"- {nombre}: {ruta}")


if __name__ == "__main__":
    main()
