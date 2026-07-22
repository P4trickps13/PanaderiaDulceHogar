import numpy as np
import pandas as pd


COLUMNAS_REQUERIDAS = {"producto", "cantidad", "subtotal", "fecha"}


def limpiar_datos(df):
    """Limpia, valida y transforma el detalle de ventas."""
    faltantes = COLUMNAS_REQUERIDAS.difference(df.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas obligatorias: {', '.join(sorted(faltantes))}")

    datos = df.copy()
    datos = datos.replace([np.inf, -np.inf], np.nan)
    datos["producto"] = (
        datos["producto"]
        .astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )
    datos["cantidad"] = pd.to_numeric(datos["cantidad"], errors="coerce")
    datos["subtotal"] = pd.to_numeric(datos["subtotal"], errors="coerce")
    datos["fecha"] = pd.to_datetime(datos["fecha"], errors="coerce")

    if "precio_unitario" in datos:
        datos["precio_unitario"] = pd.to_numeric(datos["precio_unitario"], errors="coerce")

    datos = datos.dropna(subset=["producto", "cantidad", "subtotal", "fecha"])
    datos = datos[datos["producto"].str.len() > 0]
    datos = datos.drop_duplicates()
    datos = datos[(datos["cantidad"] > 0) & (datos["subtotal"] > 0)]
    datos["cantidad"] = datos["cantidad"].astype(int)
    datos["subtotal"] = datos["subtotal"].astype(float)

    return datos.reset_index(drop=True)
