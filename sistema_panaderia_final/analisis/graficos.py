from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analisis.analisis_ventas import unidades_por_producto, ventas_por_fecha


def _guardar_sin_datos(titulo, ruta):
    figura, eje = plt.subplots(figsize=(8, 4.5))
    eje.set_title(titulo)
    eje.text(0.5, 0.5, "Sin ventas pagadas", ha="center", va="center")
    eje.set_axis_off()
    figura.tight_layout()
    figura.savefig(ruta, dpi=150)
    plt.close(figura)


def generar_graficos(df, carpeta_salida="resultados"):
    """Genera dos gráficos PNG y devuelve sus rutas."""
    carpeta = Path(carpeta_salida)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta_ventas = carpeta / "ventas_por_dia.png"
    ruta_productos = carpeta / "unidades_por_producto.png"

    ventas = ventas_por_fecha(df)
    if ventas.empty:
        _guardar_sin_datos("Ventas pagadas por día", ruta_ventas)
    else:
        figura, eje = plt.subplots(figsize=(8, 4.5))
        ventas.plot(kind="line", marker="o", ax=eje)
        eje.set_title("Ventas pagadas por día")
        eje.set_xlabel("Fecha")
        eje.set_ylabel("Total (S/)")
        eje.tick_params(axis="x", rotation=30)
        figura.tight_layout()
        figura.savefig(ruta_ventas, dpi=150)
        plt.close(figura)

    unidades = unidades_por_producto(df)
    if unidades.empty:
        _guardar_sin_datos("Unidades vendidas por producto", ruta_productos)
    else:
        figura, eje = plt.subplots(figsize=(8, 4.5))
        unidades.sort_values().plot(kind="barh", ax=eje)
        eje.set_title("Unidades vendidas por producto")
        eje.set_xlabel("Unidades")
        eje.set_ylabel("Producto")
        figura.tight_layout()
        figura.savefig(ruta_productos, dpi=150)
        plt.close(figura)

    return {"ventas": ruta_ventas, "productos": ruta_productos}
