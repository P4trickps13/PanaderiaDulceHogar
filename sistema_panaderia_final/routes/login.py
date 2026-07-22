import sqlite3
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models.usuario import crear_usuario, validar_login


login_bp = Blueprint("login", __name__)


def login_requerido(*roles):
    def decorador(vista):
        @wraps(vista)
        def wrapper(*args, **kwargs):
            if "usuario_id" not in session:
                flash("Inicia sesión para continuar.", "error")
                return redirect(url_for("login.ingresar"))
            if roles and session.get("rol") not in roles:
                flash("No tienes permiso para entrar a esa sección.", "error")
                return redirect(url_for("cliente.catalogo"))
            return vista(*args, **kwargs)

        return wrapper

    return decorador


@login_bp.route("/")
def inicio():
    if session.get("rol") == "admin":
        return redirect(url_for("admin.dashboard"))
    if session.get("rol") == "vendedor":
        return redirect(url_for("vendedor.panel"))
    return redirect(url_for("cliente.catalogo"))


@login_bp.route("/login", methods=["GET", "POST"])
def ingresar():
    if request.method == "POST":
        usuario = validar_login(
            request.form.get("email", ""),
            request.form.get("password", ""),
        )
        if usuario:
            carrito = dict(session.get("carrito", {}))
            session.clear()
            if carrito:
                session["carrito"] = carrito
            session["usuario_id"] = usuario.id
            session["nombre"] = usuario.nombre
            session["rol"] = usuario.rol
            return redirect(url_for("login.inicio"))
        flash("Correo o contraseña incorrectos.", "error")
    return render_template("login.html")


@login_bp.route("/registro", methods=["POST"])
def registro():
    try:
        crear_usuario(
            request.form.get("nombre", ""),
            request.form.get("email", ""),
            request.form.get("password", ""),
            "cliente",
        )
        flash("Cuenta creada. Ahora puedes ingresar.", "ok")
    except sqlite3.IntegrityError:
        flash("Ese correo ya está registrado.", "error")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("login.ingresar"))


@login_bp.route("/logout")
def salir():
    session.clear()
    return redirect(url_for("login.ingresar"))
