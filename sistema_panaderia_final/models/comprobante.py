from dataclasses import dataclass
from datetime import datetime

from models.db import get_db


@dataclass(frozen=True)
class Comprobante:
    tipo: str
    cliente: str
    fecha: datetime | None = None

    def __post_init__(self):
        if self.tipo not in {"boleta", "factura"}:
            raise ValueError("Tipo de comprobante no válido.")
        if self.fecha is None:
            object.__setattr__(self, "fecha", datetime.now())

    @property
    def serie(self):
        return "B001" if self.tipo == "boleta" else "F001"

    def generar_numero(self, correlativo=1):
        correlativo = int(correlativo)
        if correlativo <= 0:
            raise ValueError("El correlativo debe ser positivo.")
        return f"{self.serie}-{correlativo:08d}"

    def informacion(self):
        return {
            "tipo": self.tipo,
            "cliente": self.cliente,
            "fecha": self.fecha.isoformat(timespec="seconds"),
        }


def emitir_comprobante(
    pedido_id,
    tipo,
    documento_cliente="",
    nombre_cliente="",
    ruc="",
    razon_social="",
):
    """Emite como máximo un comprobante por pedido y marca la venta como pagada."""
    pedido_id = int(pedido_id)
    comprobante = Comprobante(tipo=tipo, cliente=nombre_cliente or documento_cliente)

    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        pedido = conn.execute(
            "SELECT id FROM pedidos WHERE id = ?", (pedido_id,)
        ).fetchone()
        if not pedido:
            raise ValueError("El pedido no existe.")

        existente = conn.execute(
            """
            SELECT serie, numero FROM comprobantes
            WHERE pedido_id = ?
            ORDER BY id DESC LIMIT 1
            """,
            (pedido_id,),
        ).fetchone()
        if existente:
            return f"{existente['serie']}-{existente['numero']}"

        ultimo = conn.execute(
            """
            SELECT COALESCE(MAX(CAST(numero AS INTEGER)), 0) AS ultimo
            FROM comprobantes WHERE tipo = ? AND serie = ?
            """,
            (tipo, comprobante.serie),
        ).fetchone()["ultimo"]
        numero = f"{int(ultimo) + 1:08d}"

        conn.execute(
            """
            INSERT INTO comprobantes (
                pedido_id, tipo, serie, numero, documento_cliente,
                nombre_cliente, ruc, razon_social, fecha
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pedido_id,
                tipo,
                comprobante.serie,
                numero,
                documento_cliente.strip(),
                nombre_cliente.strip(),
                ruc.strip(),
                razon_social.strip(),
                comprobante.fecha.isoformat(timespec="seconds"),
            ),
        )
        conn.execute("UPDATE pedidos SET estado = 'pagado' WHERE id = ?", (pedido_id,))
        conn.commit()
        return f"{comprobante.serie}-{numero}"


def obtener_comprobante(comprobante_id):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT c.*, p.total, p.metodo_pago, p.numero_operacion, p.estado,
                   u.nombre AS usuario
            FROM comprobantes c
            JOIN pedidos p ON p.id = c.pedido_id
            JOIN usuarios u ON u.id = p.usuario_id
            WHERE c.id = ?
            """,
            (int(comprobante_id),),
        ).fetchone()


def obtener_comprobante_por_pedido(pedido_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM comprobantes WHERE pedido_id = ? ORDER BY id DESC LIMIT 1",
            (int(pedido_id),),
        ).fetchone()


def detalle_comprobante(pedido_id):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT d.*, pr.nombre
            FROM pedido_detalles d
            JOIN productos pr ON pr.id = d.producto_id
            WHERE d.pedido_id = ?
            ORDER BY d.id
            """,
            (int(pedido_id),),
        ).fetchall()
