import hmac
import re
from dataclasses import dataclass
from hashlib import sha256

from werkzeug.security import check_password_hash, generate_password_hash

from models.db import get_db


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@dataclass
class Usuario:
    id: int
    nombre: str
    email: str
    rol: str

    def tiene_permiso(self, accion):
        permisos = {
            "admin": {"crear_producto", "editar_producto", "ver_reportes"},
            "vendedor": {"gestionar_pedidos", "emitir_comprobante"},
            "cliente": {"realizar_compra"},
        }
        return accion in permisos.get(self.rol, set())

    def mostrar_perfil(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol,
        }


def generar_hash(password):
    return generate_password_hash(password)


def buscar_por_email(email):
    email = email.strip().lower()
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM usuarios WHERE lower(email) = ?",
            (email,),
        ).fetchone()


def crear_usuario(nombre, email, password, rol="cliente"):
    nombre = nombre.strip()
    email = email.strip().lower()
    if not nombre:
        raise ValueError("El nombre es obligatorio.")
    if not EMAIL_RE.match(email):
        raise ValueError("El correo no tiene un formato válido.")
    if len(password) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")
    if rol not in {"admin", "cliente", "vendedor"}:
        raise ValueError("Rol no válido.")

    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO usuarios (nombre, email, password_hash, rol)
            VALUES (?, ?, ?, ?)
            """,
            (nombre, email, generar_hash(password), rol),
        )
        conn.commit()
        return cursor.lastrowid


def _validar_hash_guardado(password_hash, password):
    # Compatibilidad con los usuarios de demostración creados con SHA-256.
    if len(password_hash) == 64 and all(c in "0123456789abcdef" for c in password_hash.lower()):
        legado = sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(password_hash, legado)
    return check_password_hash(password_hash, password)


def validar_login(email, password):
    fila = buscar_por_email(email)
    if fila and _validar_hash_guardado(fila["password_hash"], password):
        return Usuario(fila["id"], fila["nombre"], fila["email"], fila["rol"])
    return None
