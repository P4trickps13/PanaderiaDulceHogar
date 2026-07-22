from flask import Blueprint, flash, redirect, render_template, request, url_for

from models.comprobante import emitir_comprobante
from models.pedido import ErrorPedido, actualizar_estado, listar_pedidos
from routes.login import login_requerido


vendedor_bp = Blueprint("vendedor", __name__, url_prefix="/vendedor")


@vendedor_bp.route("/")
@login_requerido("vendedor", "admin")
def panel():
    return render_template("vendedor.html", pedidos=listar_pedidos())


@vendedor_bp.route("/pedido/<int:pedido_id>/estado", methods=["POST"])
@login_requerido("vendedor", "admin")
def estado(pedido_id):
    try:
        actualizar_estado(pedido_id, request.form.get("estado", ""))
        flash("Estado actualizado.", "ok")
    except ErrorPedido as error:
        flash(str(error), "error")
    return redirect(url_for("vendedor.panel"))


@vendedor_bp.route("/pedido/<int:pedido_id>/comprobante", methods=["POST"])
@login_requerido("vendedor", "admin")
def comprobante(pedido_id):
    try:
        codigo = emitir_comprobante(
            pedido_id,
            request.form.get("tipo", ""),
            request.form.get("documento_cliente", ""),
        )
        flash(f"Comprobante emitido: {codigo}", "ok")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("vendedor.panel"))
