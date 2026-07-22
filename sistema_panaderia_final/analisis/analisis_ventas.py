import sqlite3
from contextlib import closing
from pathlib import Path

import numpy as np
import pandas as pd
from flask import current_app


RUTA_DB_PREDETERMINADA = Path(__file__).resolve().parents[1] / "database" / "panaderia.db"

CONSULTA_VENTAS = """
    SELECT
        pedidos.id AS pedido_id,
        productos.nombre AS producto,
        pedido_detalles.cantidad,
        pedido_detalles.precio_unitario,
        pedido_detalles.subtotal,
        pedidos.fecha,
        pedidos.estado
    FROM pedido_detalles
    INNER JOIN productos
        ON pedido_detalles.producto_id = productos.id
    INNER JOIN pedidos
        ON pedido_detalles.pedido_id = pedidos.id
    ORDER BY pedidos.fecha, pedidos.id
"""

CONSULTA_VENTAS_PAGADAS = """
    SELECT
        pedidos.id AS pedido_id,
        productos.nombre AS producto,
        pedido_detalles.cantidad,
        pedido_detalles.precio_unitario,
        pedido_detalles.subtotal,
        pedidos.fecha,
        pedidos.estado
    FROM pedido_detalles
    INNER JOIN productos
        ON pedido_detalles.producto_id = productos.id
    INNER JOIN pedidos
        ON pedido_detalles.pedido_id = pedidos.id
    WHERE pedidos.estado = 'pagado'
    ORDER BY pedidos.fecha, pedidos.id
"""


def resolver_ruta_db(ruta_db=None):
    if ruta_db is not None:
        return Path(ruta_db)
    try:
        return Path(current_app.config["DB_PATH"])
    except RuntimeError:
        return RUTA_DB_PREDETERMINADA


def obtener_ventas(ruta_db=None, solo_pagadas=True):
    """Obtiene el detalle de ventas en un DataFrame."""
    consulta = CONSULTA_VENTAS_PAGADAS if solo_pagadas else CONSULTA_VENTAS
    with closing(sqlite3.connect(resolver_ruta_db(ruta_db))) as conexion:
        return pd.read_sql_query(consulta, conexion)


def ventas_totales(df):
    if df.empty or "subtotal" not in df:
        return 0.0
    return round(float(np.sum(df["subtotal"])), 2)


def producto_mas_vendido(df):
    if df.empty:
        return "Sin ventas"
    cantidades = unidades_por_producto(df)
    return str(cantidades.index[0]) if not cantidades.empty else "Sin ventas"


def promedio_venta(df):
    """Calcula el promedio por pedido, no por línea de detalle."""
    if df.empty:
        return 0.0
    if "pedido_id" in df:
        totales_pedido = df.groupby("pedido_id")["subtotal"].sum()
        return round(float(np.mean(totales_pedido)), 2)
    return round(float(np.mean(df["subtotal"])), 2)


def cantidad_total_vendida(df):
    if df.empty or "cantidad" not in df:
        return 0
    return int(np.sum(df["cantidad"]))


def producto_mayor_ingreso(df):
    if df.empty:
        return "Sin ventas"
    ingresos = ventas_por_producto(df)
    return str(ingresos.index[0]) if not ingresos.empty else "Sin ventas"


def ventas_por_producto(df):
    if df.empty:
        return pd.Series(dtype="float64", name="subtotal")
    return df.groupby("producto")["subtotal"].sum().sort_values(ascending=False)


def unidades_por_producto(df):
    if df.empty:
        return pd.Series(dtype="int64", name="cantidad")
    return df.groupby("producto")["cantidad"].sum().sort_values(ascending=False)


def ventas_por_fecha(df):
    if df.empty:
        return pd.Series(dtype="float64", name="subtotal")
    fechas = pd.to_datetime(df["fecha"], errors="coerce")
    datos = df.assign(fecha=fechas).dropna(subset=["fecha"])
    return datos.groupby(datos["fecha"].dt.strftime("%Y-%m-%d"))["subtotal"].sum()


def ventas_por_mes(df):
    if df.empty:
        return pd.Series(dtype="float64", name="subtotal")
    fechas = pd.to_datetime(df["fecha"], errors="coerce")
    datos = df.assign(fecha=fechas).dropna(subset=["fecha"])
    return datos.groupby(datos["fecha"].dt.strftime("%Y-%m"))["subtotal"].sum()


def promedio_cantidad_producto(df):
    if df.empty or "cantidad" not in df:
        return 0.0
    return round(float(np.mean(df["cantidad"])), 2)


def productos_stock_bajo(limite=30, ruta_db=None):
    consulta = """
        SELECT id, nombre, stock
        FROM productos
        WHERE activo = 1 AND stock <= ?
        ORDER BY stock ASC, nombre ASC
    """
    with closing(sqlite3.connect(resolver_ruta_db(ruta_db))) as conexion:
        return pd.read_sql_query(consulta, conexion, params=(limite,))


def desviacion_ventas(df):
    """Calcula la desviación estándar de los totales por pedido."""
    if df.empty or "subtotal" not in df:
        return 0.0
    valores = (
        df.groupby("pedido_id")["subtotal"].sum()
        if "pedido_id" in df
        else df["subtotal"]
    )
    return round(float(np.std(valores)), 2)
