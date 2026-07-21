from dataclasses import dataclass

from models.db import get_db


@dataclass
class Producto:
    id: int
    nombre: str
    descripcion: str
    precio: float
    stock: int
    activo: int = 1
    imagen: str | None = None

    def validar(self):
        self.nombre = self.nombre.strip()
        self.descripcion = self.descripcion.strip()
        self.precio = float(self.precio)
        self.stock = int(self.stock)
        self.activo = 1 if int(self.activo) else 0
        if not self.nombre or not self.descripcion:
            raise ValueError("Nombre y descripción son obligatorios.")
        if self.precio <= 0 or self.stock < 0:
            raise ValueError("El precio debe ser positivo y el stock no puede ser negativo.")
        return self

    def disponible(self, cantidad=1):
        return bool(self.activo) and self.stock >= cantidad > 0

    def actualizar_stock(self, cantidad):
        nuevo_stock = self.stock + int(cantidad)
        if nuevo_stock < 0:
            raise ValueError("El stock no puede ser negativo.")
        self.stock = nuevo_stock

    def aplicar_descuento(self, porcentaje):
        porcentaje = float(porcentaje)
        if not 0 <= porcentaje <= 1:
            raise ValueError("El descuento debe estar entre 0 y 1.")
        self.precio = round(self.precio * (1 - porcentaje), 2)

    def obtener_info(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "precio": self.precio,
            "stock": self.stock,
            "disponible": self.disponible(),
        }


def listar_productos():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM productos WHERE activo = 1 ORDER BY nombre"
        ).fetchall()
    return [dict(row) for row in rows]


def listar_todos_productos():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM productos ORDER BY nombre").fetchall()
    return [dict(row) for row in rows]


def obtener_producto(producto_id):
    if isinstance(producto_id, dict):
        producto_id = producto_id.get("id")
    try:
        producto_id = int(producto_id)
    except (TypeError, ValueError):
        return None

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM productos WHERE id = ?",
            (producto_id,),
        ).fetchone()
    return dict(row) if row else None


def crear_producto(nombre, descripcion, precio, stock, imagen="pan-frances.svg"):
    producto = Producto(0, nombre, descripcion, precio, stock, 1, imagen).validar()

    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO productos (nombre, descripcion, precio, stock, activo, imagen)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (producto.nombre, producto.descripcion, producto.precio, producto.stock, producto.imagen),
        )
        conn.commit()
        return cursor.lastrowid


def actualizar_producto(producto_id, nombre, descripcion, precio, stock, activo=1):
    producto = Producto(int(producto_id), nombre, descripcion, precio, stock, activo).validar()

    with get_db() as conn:
        cursor = conn.execute(
            """
            UPDATE productos
            SET nombre = ?, descripcion = ?, precio = ?, stock = ?, activo = ?
            WHERE id = ?
            """,
            (producto.nombre, producto.descripcion, producto.precio, producto.stock, producto.activo, producto.id),
        )
        if cursor.rowcount == 0:
            raise ValueError("El producto no existe.")
        conn.commit()


def actualizar_imagen(producto_id, imagen):
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE productos SET imagen = ? WHERE id = ?",
            (imagen, int(producto_id)),
        )
        if cursor.rowcount == 0:
            raise ValueError("El producto no existe.")
        conn.commit()
