from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models.pedido import ErrorPedido, Pedido
from models.producto import listar_productos, obtener_producto
from routes.login import login_requerido


cliente_bp = Blueprint("cliente", __name__)


@cliente_bp.route("/catalogo")
def catalogo():
    return render_template("catalogo.html", productos=listar_productos())


@cliente_bp.route("/carrito/agregar", methods=["POST"])
def agregar_carrito():
    try:
        producto_id = int(request.form.get("producto_id", 0))
        cantidad = int(request.form.get("cantidad", 1))
        producto = obtener_producto(producto_id)
        if not producto or not producto["activo"]:
            raise ValueError("El producto no está disponible.")
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")

        carrito = session.get("carrito", {})
        nueva_cantidad = int(carrito.get(str(producto_id), 0)) + cantidad
        if nueva_cantidad > int(producto["stock"]):
            raise ValueError(f"Solo hay {producto['stock']} unidades disponibles.")

        carrito[str(producto_id)] = nueva_cantidad
        session["carrito"] = carrito
        flash(
            f"Agregaste {cantidad} producto(s). Tu carrito tiene {sum(carrito.values())} item(s).",
            "ok",
        )
    except (TypeError, ValueError) as error:
        flash(str(error), "error")
    return redirect(url_for("cliente.catalogo"))


@cliente_bp.route("/carrito/actualizar", methods=["POST"])
def actualizar_carrito():
    carrito = session.get("carrito", {})
    producto_id = request.form.get("producto_id", "")
    accion = request.form.get("accion", "")
    cantidad_actual = int(carrito.get(producto_id, 0))
    producto = obtener_producto(producto_id)

    if accion == "sumar" and producto:
        if cantidad_actual + 1 <= int(producto["stock"]):
            carrito[producto_id] = cantidad_actual + 1
        else:
            flash("No hay más stock disponible.", "error")
    elif accion == "restar":
        nueva_cantidad = cantidad_actual - 1
        if nueva_cantidad > 0:
            carrito[producto_id] = nueva_cantidad
        else:
            carrito.pop(producto_id, None)
    elif accion == "quitar":
        carrito.pop(producto_id, None)

    session["carrito"] = carrito
    if accion in {"sumar", "restar", "quitar"}:
        flash("Carrito actualizado.", "ok")
    return redirect(url_for("cliente.carrito"))


@cliente_bp.route("/carrito/vaciar", methods=["POST"])
def vaciar_carrito():
    session["carrito"] = {}
    flash("Carrito vaciado.", "ok")
    return redirect(url_for("cliente.carrito"))


@cliente_bp.route("/carrito")
def carrito():
    productos = {str(producto["id"]): producto for producto in listar_productos()}
    items = []
    total = 0.0
    carrito_actualizado = {}

    for producto_id, cantidad in session.get("carrito", {}).items():
        producto = productos.get(str(producto_id))
        if not producto:
            continue
        cantidad = min(int(cantidad), int(producto["stock"]))
        if cantidad <= 0:
            continue
        subtotal = round(float(producto["precio"]) * cantidad, 2)
        total += subtotal
        carrito_actualizado[str(producto_id)] = cantidad
        items.append(
            {
                "producto": producto,
                "cantidad": cantidad,
                "subtotal": subtotal,
                "imagen": producto["imagen"] or "pan-frances.svg",
            }
        )

    session["carrito"] = carrito_actualizado
    return render_template("carrito.html", items=items, total=round(total, 2))


@cliente_bp.route("/pedido/crear", methods=["POST"])
@login_requerido("cliente", "admin")
def crear():
    carrito_sesion = session.get("carrito", {})
    if not carrito_sesion:
        flash("Tu carrito está vacío.", "error")
        return redirect(url_for("cliente.carrito"))

    pedido = Pedido(session["usuario_id"])
    try:
        for producto_id, cantidad in carrito_sesion.items():
            pedido.agregar_item(producto_id, cantidad)

        numero_operacion = request.form.get("numero_operacion", "").strip()
        if len(numero_operacion) < 3:
            raise ErrorPedido("Ingresa un número de operación válido.")

        pedido.guardar(metodo_pago="yape", numero_operacion=numero_operacion)
        session["carrito"] = {}
        flash("Pedido registrado. Validaremos tu pago por Yape.", "ok")
        return redirect(url_for("cliente.mis_pedidos"))
    except ErrorPedido as error:
        flash(str(error), "error")
        return redirect(url_for("cliente.carrito"))


@cliente_bp.route("/mis-pedidos")
@login_requerido("cliente", "admin")
def mis_pedidos():
    pedidos = Pedido.listar_por_usuario(session["usuario_id"])
    return render_template("mis_pedidos.html", pedidos=pedidos)
