from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from analisis.resumen import generar_resumen
from models.producto import (
    actualizar_imagen,
    actualizar_producto,
    crear_producto,
    listar_todos_productos,
)
from routes.login import login_requerido


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
EXTENSIONES_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}
MIMES_PERMITIDOS = {"image/png", "image/jpeg", "image/webp"}


def archivo_permitido(archivo):
    if not archivo or not archivo.filename:
        return False
    nombre = secure_filename(archivo.filename)
    extension_valida = "." in nombre and nombre.rsplit(".", 1)[1].lower() in EXTENSIONES_PERMITIDAS
    mime_valido = archivo.mimetype in MIMES_PERMITIDOS
    return extension_valida and mime_valido


@admin_bp.route("/")
@login_requerido("admin")
def dashboard():
    productos = listar_todos_productos()
    analisis = generar_resumen()
    return render_template(
        "admin.html",
        productos=productos,
        analisis=analisis,
        resumen={"pedidos": analisis["pedidos_pagados"], "total": analisis["ventas_totales"]},
        productos_bajo_stock=analisis["productos_bajo_stock"],
        ventas_dia=analisis["ventas_dia"],
        ventas_mes=analisis["ventas_mes"],
    )


@admin_bp.route("/api/dashboard")
@login_requerido("admin")
def api_dashboard():
    """Entrega datos actualizados para refrescar los gráficos sin recargar la página."""
    analisis = generar_resumen()
    return jsonify(
        {
            "ventas_fecha": analisis["ventas_fecha"],
            "productos": analisis["productos"],
            "actualizado": True,
        }
    )


@admin_bp.route("/productos/crear", methods=["POST"])
@login_requerido("admin")
def crear_producto_admin():
    try:
        imagen = guardar_imagen(request.files.get("imagen"))
        crear_producto(
            request.form.get("nombre", ""),
            request.form.get("descripcion", ""),
            request.form.get("precio", ""),
            request.form.get("stock", ""),
            imagen or "pan-frances.svg",
        )
        flash("Producto creado correctamente.", "ok")
    except (TypeError, ValueError) as error:
        flash(str(error), "error")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/productos/<int:producto_id>/imagen", methods=["POST"])
@login_requerido("admin")
def subir_imagen_producto(producto_id):
    try:
        imagen = guardar_imagen(request.files.get("imagen"))
        if not imagen:
            raise ValueError("Selecciona una imagen PNG, JPG, JPEG o WEBP válida.")
        actualizar_imagen(producto_id, imagen)
        flash("Imagen actualizada.", "ok")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/productos/<int:producto_id>/editar", methods=["POST"])
@login_requerido("admin")
def editar_producto(producto_id):
    try:
        actualizar_producto(
            producto_id,
            request.form.get("nombre", ""),
            request.form.get("descripcion", ""),
            request.form.get("precio", ""),
            request.form.get("stock", ""),
            request.form.get("activo", 0),
        )
        flash("Producto actualizado correctamente.", "ok")
    except (TypeError, ValueError) as error:
        flash(str(error), "error")
    return redirect(url_for("admin.dashboard"))


def guardar_imagen(archivo):
    if not archivo or not archivo.filename:
        return None
    if not archivo_permitido(archivo):
        raise ValueError("Formato de imagen no permitido.")

    nombre_seguro = secure_filename(archivo.filename)
    extension = nombre_seguro.rsplit(".", 1)[1].lower()
    base = Path(nombre_seguro).stem[:40] or "imagen"
    nombre_final = f"producto-{base}-{uuid4().hex[:10]}.{extension}"
    destino = Path(current_app.config["UPLOAD_FOLDER"]) / nombre_final
    archivo.save(destino)
    return nombre_final


@admin_bp.route("/reportes")
@login_requerido("admin")
def reportes():
    tipo = request.args.get("tipo", "dia")
    if tipo not in {"dia", "mes"}:
        tipo = "dia"

    analisis = generar_resumen()
    reporte = analisis["ventas_dia"] if tipo == "dia" else analisis["ventas_mes"]
    return render_template("reportes.html", reporte=reporte, tipo=tipo)
