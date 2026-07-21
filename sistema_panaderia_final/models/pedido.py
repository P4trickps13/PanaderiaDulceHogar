from datetime import datetime

from models.db import get_db
from models.producto import obtener_producto


class ErrorPedido(ValueError):
    pass


class Pedido:
    def __init__(self, usuario_id=None, pedido_id=None):
        self.usuario_id = usuario_id
        self.pedido_id = pedido_id
        self.items = {}

    def agregar_item(self, producto_id, cantidad):
        if isinstance(producto_id, dict):
            producto_id = producto_id.get("id")
        try:
            producto_id = int(producto_id)
            cantidad = int(cantidad)
        except (TypeError, ValueError) as error:
            raise ErrorPedido("Producto o cantidad no válidos.") from error
        if cantidad <= 0:
            raise ErrorPedido("La cantidad debe ser mayor que cero.")
        self.items[producto_id] = self.items.get(producto_id, 0) + cantidad

    def calcular_total(self):
        total = 0.0
        for producto_id, cantidad in self.items.items():
            producto = obtener_producto(producto_id)
            if not producto or not producto["activo"]:
                raise ErrorPedido("Uno de los productos ya no está disponible.")
            if cantidad > producto["stock"]:
                raise ErrorPedido(f"Stock insuficiente para {producto['nombre']}.")
            total += float(producto["precio"]) * cantidad
        return round(total, 2)

    def guardar(self, metodo_pago="yape", numero_operacion="", estado="pendiente"):
        if not self.usuario_id:
            raise ErrorPedido("Se necesita un usuario para registrar el pedido.")
        if not self.items:
            raise ErrorPedido("El pedido no contiene productos.")
        if estado not in {"pendiente", "preparando", "entregado", "pagado"}:
            raise ErrorPedido("Estado de pedido no válido.")

        with get_db() as conn:
            usuario = conn.execute(
                "SELECT id FROM usuarios WHERE id = ?", (int(self.usuario_id),)
            ).fetchone()
            if not usuario:
                raise ErrorPedido("El usuario no existe.")

            detalle = []
            total = 0.0
            for producto_id, cantidad in self.items.items():
                producto = conn.execute(
                    "SELECT * FROM productos WHERE id = ?", (producto_id,)
                ).fetchone()
                if not producto or not producto["activo"]:
                    raise ErrorPedido("Uno de los productos ya no está disponible.")
                if cantidad > producto["stock"]:
                    raise ErrorPedido(f"Stock insuficiente para {producto['nombre']}.")

                precio = float(producto["precio"])
                subtotal = round(precio * cantidad, 2)
                total += subtotal
                detalle.append((producto_id, cantidad, precio, subtotal))

            total = round(total, 2)
            if total <= 0:
                raise ErrorPedido("El total del pedido debe ser positivo.")

            cursor = conn.execute(
                """
                INSERT INTO pedidos (usuario_id, fecha, total, estado, metodo_pago, numero_operacion)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    int(self.usuario_id),
                    datetime.now().isoformat(timespec="seconds"),
                    total,
                    estado,
                    metodo_pago,
                    numero_operacion.strip(),
                ),
            )
            self.pedido_id = cursor.lastrowid

            for producto_id, cantidad, precio, subtotal in detalle:
                actualizado = conn.execute(
                    """
                    UPDATE productos
                    SET stock = stock - ?
                    WHERE id = ? AND activo = 1 AND stock >= ?
                    """,
                    (cantidad, producto_id, cantidad),
                )
                if actualizado.rowcount != 1:
                    raise ErrorPedido("El stock cambió durante la compra. Intenta nuevamente.")

                conn.execute(
                    """
                    INSERT INTO pedido_detalles
                        (pedido_id, producto_id, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (self.pedido_id, producto_id, cantidad, precio, subtotal),
                )

            conn.commit()
            return self.pedido_id

    def actualizar_estado(self, estado):
        if not self.pedido_id:
            raise ErrorPedido("Pedido no válido.")
        if estado not in {"pendiente", "preparando", "entregado", "pagado"}:
            raise ErrorPedido("Estado no válido.")
        with get_db() as conn:
            cursor = conn.execute(
                "UPDATE pedidos SET estado = ? WHERE id = ?",
                (estado, int(self.pedido_id)),
            )
            if cursor.rowcount == 0:
                raise ErrorPedido("El pedido no existe.")
            conn.commit()
        return True

    def listar(self):
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT p.*, u.nombre AS cliente,
                       c.serie || '-' || c.numero AS comprobante
                FROM pedidos p
                JOIN usuarios u ON u.id = p.usuario_id
                LEFT JOIN comprobantes c ON c.id = (
                    SELECT MAX(c2.id) FROM comprobantes c2 WHERE c2.pedido_id = p.id
                )
                ORDER BY p.fecha DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def listar_por_usuario(usuario_id):
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT p.*, u.nombre AS cliente,
                       c.serie || '-' || c.numero AS comprobante
                FROM pedidos p
                JOIN usuarios u ON u.id = p.usuario_id
                LEFT JOIN comprobantes c ON c.id = (
                    SELECT MAX(c2.id) FROM comprobantes c2 WHERE c2.pedido_id = p.id
                )
                WHERE p.usuario_id = ?
                ORDER BY p.fecha DESC
                """,
                (int(usuario_id),),
            ).fetchall()
        return [dict(row) for row in rows]


def listar_pedidos():
    return Pedido().listar()


def actualizar_estado(pedido_id, estado):
    return Pedido(pedido_id=pedido_id).actualizar_estado(estado)


def pedidos_por_usuario(usuario_id):
    return Pedido.listar_por_usuario(usuario_id)
