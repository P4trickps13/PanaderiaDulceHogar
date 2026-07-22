import sqlite3
import tempfile
import unittest
from contextlib import closing
from io import BytesIO
from pathlib import Path

import pandas as pd

from analisis.analisis_ventas import obtener_ventas, ventas_totales
from analisis.graficos import generar_graficos
from analisis.limpieza_datos import limpiar_datos
from analisis.resumen import generar_recursos_graficos, generar_resumen
from app import SQL_PATH, create_app
from models.comprobante import Comprobante
from models.pedido import ErrorPedido, Pedido
from models.producto import Producto
from models.usuario import Usuario


class SistemaPanaderiaTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        carpeta = Path(self.temporal.name)
        self.db_path = carpeta / "pruebas.db"
        self.generated_folder = carpeta / "generated"
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "clave-pruebas",
                "DB_PATH": self.db_path,
                "SQL_PATH": SQL_PATH,
                "UPLOAD_FOLDER": carpeta / "uploads",
                "GENERATED_FOLDER": self.generated_folder,
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temporal.cleanup()

    def iniciar_sesion(self, email, password="123456"):
        return self.client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )

    def crear_pedido_desde_carrito(self, producto_id="2", cantidad="2"):
        self.iniciar_sesion("cliente@panaderia.com")
        self.client.post(
            "/carrito/agregar",
            data={"producto_id": producto_id, "cantidad": cantidad},
            follow_redirects=True,
        )
        respuesta = self.client.post(
            "/pedido/crear",
            data={"numero_operacion": "987654321"},
            follow_redirects=True,
        )
        with closing(sqlite3.connect(self.db_path)) as conn:
            pedido_id = conn.execute("SELECT MAX(id) FROM pedidos").fetchone()[0]
        return pedido_id, respuesta

    def test_programacion_orientada_a_objetos(self):
        producto = Producto(1, "Pan", "Pan artesanal", 10.0, 5)
        producto.aplicar_descuento(0.10)
        self.assertEqual(producto.precio, 9.0)
        self.assertTrue(producto.disponible(2))

        usuario = Usuario(1, "Admin", "admin@correo.com", "admin")
        self.assertTrue(usuario.tiene_permiso("ver_reportes"))
        self.assertFalse(usuario.tiene_permiso("realizar_compra"))

        comprobante = Comprobante("boleta", "Cliente")
        self.assertEqual(comprobante.generar_numero(7), "B001-00000007")
        self.assertIn("fecha", comprobante.informacion())

    def test_validaciones_de_objetos(self):
        producto = Producto(1, "Pan", "Pan artesanal", 10.0, 2)
        with self.assertRaises(ValueError):
            producto.actualizar_stock(-3)
        with self.assertRaises(ValueError):
            producto.aplicar_descuento(1.5)
        with self.assertRaises(ValueError):
            Comprobante("ticket", "Cliente")

    def test_control_de_acceso_por_roles(self):
        respuesta = self.client.get("/admin/")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/login", respuesta.location)

        respuesta = self.iniciar_sesion("cliente@panaderia.com")
        self.assertIn(b"Panader", respuesta.data)
        respuesta = self.client.get("/admin/", follow_redirects=True)
        self.assertNotIn(b"Dashboard administrador", respuesta.data)

        self.client.get("/logout")
        respuesta = self.iniciar_sesion("admin@panaderia.com")
        self.assertIn(b"Dashboard administrador", respuesta.data)

    def test_cliente_no_puede_crear_producto(self):
        self.iniciar_sesion("cliente@panaderia.com")
        respuesta = self.client.post(
            "/admin/productos/crear",
            data={
                "nombre": "Producto no autorizado",
                "descripcion": "No debe guardarse",
                "precio": "4.50",
                "stock": "10",
            },
            follow_redirects=True,
        )
        self.assertIn(b"No tienes permiso", respuesta.data)
        with closing(sqlite3.connect(self.db_path)) as conn:
            cantidad = conn.execute(
                "SELECT COUNT(*) FROM productos WHERE nombre = 'Producto no autorizado'"
            ).fetchone()[0]
        self.assertEqual(cantidad, 0)

    def test_dashboard_funciona_sin_ventas_y_muestra_graficos_interactivos(self):
        respuesta = self.iniciar_sesion("admin@panaderia.com")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b"Sin ventas", respuesta.data)
        self.assertIn(b"S/ 0.00", respuesta.data)
        self.assertIn(b'<canvas id="ventasChart"></canvas>', respuesta.data)
        self.assertIn(b'<canvas id="productosChart"></canvas>', respuesta.data)
        self.assertIn(b"js/chart.umd.min.js", respuesta.data)
        self.assertIn(b"js/dashboard.js", respuesta.data)
        self.assertNotIn(b"cdn.jsdelivr.net", respuesta.data)
        self.assertNotIn(b"generated/ventas_por_dia.png", respuesta.data)
        self.assertNotIn(b"generated/unidades_por_producto.png", respuesta.data)
        self.assertNotIn(b'id="ventasFallback"', respuesta.data)
        self.assertNotIn(b'id="productosFallback"', respuesta.data)
        self.assertIn(b"Pasa el cursor", respuesta.data)
        self.assertIn(b'id="filtroVentas"', respuesta.data)
        self.assertIn(b'id="limiteProductos"', respuesta.data)
        self.assertIn(b'id="actualizarGraficos"', respuesta.data)
        self.assertIn(b"/admin/api/dashboard", respuesta.data)

    def test_api_dashboard_requiere_admin_y_devuelve_datos(self):
        respuesta = self.client.get("/admin/api/dashboard")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/login", respuesta.location)

        self.iniciar_sesion("admin@panaderia.com")
        respuesta = self.client.get("/admin/api/dashboard")
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.get_json()
        self.assertTrue(datos["actualizado"])
        self.assertIn("ventas_fecha", datos)
        self.assertIn("productos", datos)

    def test_carrito_se_conserva_al_iniciar_sesion(self):
        self.client.post(
            "/carrito/agregar",
            data={"producto_id": "2", "cantidad": "2"},
            follow_redirects=True,
        )
        respuesta = self.iniciar_sesion("cliente@panaderia.com")
        self.assertIn(b"Carrito", respuesta.data)
        respuesta = self.client.get("/carrito")
        self.assertIn(b"Croissant", respuesta.data)
        self.assertIn(b"7.00", respuesta.data)

    def test_registro_de_usuario_y_correo_duplicado(self):
        respuesta = self.client.post(
            "/registro",
            data={
                "nombre": "Nueva Cliente",
                "email": "NUEVA@CORREO.COM",
                "password": "abcdef",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Cuenta creada", respuesta.data)
        with closing(sqlite3.connect(self.db_path)) as conn:
            correo = conn.execute(
                "SELECT email FROM usuarios WHERE nombre = 'Nueva Cliente'"
            ).fetchone()[0]
        self.assertEqual(correo, "nueva@correo.com")

        respuesta = self.client.post(
            "/registro",
            data={
                "nombre": "Duplicada",
                "email": "nueva@correo.com",
                "password": "abcdef",
            },
            follow_redirects=True,
        )
        self.assertIn(b"ya est", respuesta.data)

    def test_crear_pedido_descuenta_stock(self):
        _, respuesta = self.crear_pedido_desde_carrito()
        self.assertIn(b"Pedido registrado", respuesta.data)

        with closing(sqlite3.connect(self.db_path)) as conn:
            pedido = conn.execute(
                "SELECT total, estado FROM pedidos ORDER BY id DESC LIMIT 1"
            ).fetchone()
            stock = conn.execute("SELECT stock FROM productos WHERE id = 2").fetchone()[0]
        self.assertEqual(pedido, (7.0, "pendiente"))
        self.assertEqual(stock, 38)

    def test_no_permite_cantidad_mayor_al_stock(self):
        self.iniciar_sesion("cliente@panaderia.com")
        respuesta = self.client.post(
            "/carrito/agregar",
            data={"producto_id": "2", "cantidad": "9999"},
            follow_redirects=True,
        )
        self.assertIn(b"unidades disponibles", respuesta.data)

    def test_pedido_invalido_no_se_registra(self):
        with self.app.app_context():
            pedido = Pedido(usuario_id=3)
            pedido.agregar_item(2, 9999)
            with self.assertRaises(ErrorPedido):
                pedido.guardar(numero_operacion="12345")
        with closing(sqlite3.connect(self.db_path)) as conn:
            cantidad = conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        self.assertEqual(cantidad, 0)

    def test_vendedor_emite_un_solo_comprobante_y_marca_pagado(self):
        pedido_id, _ = self.crear_pedido_desde_carrito()
        self.client.get("/logout")
        self.iniciar_sesion("vendedor@panaderia.com")

        respuesta = self.client.post(
            f"/vendedor/pedido/{pedido_id}/comprobante",
            data={"tipo": "boleta", "documento_cliente": "12345678"},
            follow_redirects=True,
        )
        self.assertIn(b"B001-00000001", respuesta.data)

        respuesta = self.client.post(
            f"/vendedor/pedido/{pedido_id}/comprobante",
            data={"tipo": "factura", "documento_cliente": "20123456789"},
            follow_redirects=True,
        )
        self.assertIn(b"B001-00000001", respuesta.data)

        with closing(sqlite3.connect(self.db_path)) as conn:
            estado = conn.execute(
                "SELECT estado FROM pedidos WHERE id = ?", (pedido_id,)
            ).fetchone()[0]
            cantidad = conn.execute(
                "SELECT COUNT(*) FROM comprobantes WHERE pedido_id = ?", (pedido_id,)
            ).fetchone()[0]
        self.assertEqual(estado, "pagado")
        self.assertEqual(cantidad, 1)

    def test_admin_crea_y_edita_producto(self):
        self.iniciar_sesion("admin@panaderia.com")
        respuesta = self.client.post(
            "/admin/productos/crear",
            data={
                "nombre": "Pan de prueba",
                "descripcion": "Producto para prueba automatizada",
                "precio": "2.50",
                "stock": "15",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Producto creado", respuesta.data)

        with closing(sqlite3.connect(self.db_path)) as conn:
            producto_id = conn.execute(
                "SELECT id FROM productos WHERE nombre = 'Pan de prueba'"
            ).fetchone()[0]

        respuesta = self.client.post(
            f"/admin/productos/{producto_id}/editar",
            data={
                "nombre": "Pan de prueba mejorado",
                "descripcion": "Producto actualizado",
                "precio": "3.00",
                "stock": "12",
                "activo": "1",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Producto actualizado", respuesta.data)
        with closing(sqlite3.connect(self.db_path)) as conn:
            producto = conn.execute(
                "SELECT nombre, precio, stock FROM productos WHERE id = ?", (producto_id,)
            ).fetchone()
        self.assertEqual(producto, ("Pan de prueba mejorado", 3.0, 12))

    def test_rechaza_archivo_que_no_es_imagen(self):
        self.iniciar_sesion("admin@panaderia.com")
        respuesta = self.client.post(
            "/admin/productos/1/imagen",
            data={"imagen": (BytesIO(b"contenido"), "archivo.txt")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertIn(b"Formato de imagen no permitido", respuesta.data)

    def test_analisis_considera_solo_pedidos_pagados(self):
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO pedidos (usuario_id, fecha, total, estado, metodo_pago) VALUES (3, '2026-07-01T10:00:00', 7, 'pagado', 'yape')"
            )
            pagado_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO pedido_detalles (pedido_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (?, 2, 2, 3.5, 7)",
                (pagado_id,),
            )
            conn.execute(
                "INSERT INTO pedidos (usuario_id, fecha, total, estado, metodo_pago) VALUES (3, '2026-07-02T10:00:00', 100, 'pendiente', 'yape')"
            )
            pendiente_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO pedido_detalles (pedido_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (?, 4, 1, 100, 100)",
                (pendiente_id,),
            )
            conn.commit()

        with self.app.app_context():
            df = limpiar_datos(obtener_ventas(solo_pagadas=True))
            resumen = generar_resumen()
        self.assertEqual(ventas_totales(df), 7.0)
        self.assertEqual(resumen["pedidos_pagados"], 1)
        self.assertEqual(resumen["producto_mas_vendido"], "Croissant")

    def test_reportes_por_dia_y_mes(self):
        self.iniciar_sesion("admin@panaderia.com")
        respuesta_dia = self.client.get("/admin/reportes?tipo=dia")
        respuesta_mes = self.client.get("/admin/reportes?tipo=mes")
        self.assertEqual(respuesta_dia.status_code, 200)
        self.assertEqual(respuesta_mes.status_code, 200)
        self.assertIn("por día".encode(), respuesta_dia.data)
        self.assertIn("por mes".encode(), respuesta_mes.data)

    def test_limpieza_y_graficos(self):
        df = pd.DataFrame(
            {
                "pedido_id": [1, 1, 2, 3],
                "producto": [" Pan  artesanal ", " Pan  artesanal ", "Cafe", ""],
                "cantidad": [1, 1, -2, 1],
                "precio_unitario": [1, 1, 4, 2],
                "subtotal": [1, 1, -8, 2],
                "fecha": ["2026-07-01", "2026-07-01", "fecha-invalida", "2026-07-02"],
                "estado": ["pagado", "pagado", "pagado", "pagado"],
            }
        )
        limpio = limpiar_datos(df)
        self.assertEqual(len(limpio), 1)
        self.assertEqual(limpio.iloc[0]["producto"], "Pan artesanal")

        carpeta = Path(self.temporal.name) / "graficos"
        rutas = generar_graficos(limpio, carpeta)
        self.assertTrue(rutas["ventas"].exists())
        self.assertTrue(rutas["productos"].exists())


    def test_recursos_graficos_web_se_generan(self):
        carpeta = Path(self.temporal.name) / "recursos_web"
        with self.app.app_context():
            rutas = generar_recursos_graficos(
                ruta_db=self.db_path,
                carpeta_salida=carpeta,
            )
        self.assertTrue(rutas["ventas"].exists())
        self.assertTrue(rutas["productos"].exists())
        self.assertGreater(rutas["ventas"].stat().st_size, 1000)
        self.assertGreater(rutas["productos"].stat().st_size, 1000)

    def test_actualizar_y_vaciar_carrito(self):
        self.client.post(
            "/carrito/agregar",
            data={"producto_id": "2", "cantidad": "2"},
            follow_redirects=True,
        )
        respuesta = self.client.post(
            "/carrito/actualizar",
            data={"producto_id": "2", "accion": "restar"},
            follow_redirects=True,
        )
        self.assertIn(b"Croissant", respuesta.data)
        self.assertIn(b"3.50", respuesta.data)

        respuesta = self.client.post("/carrito/vaciar", follow_redirects=True)
        self.assertIn(b"carrito esta vacio", respuesta.data.lower())

    def test_vendedor_actualiza_estado_y_rechaza_estado_invalido(self):
        pedido_id, _ = self.crear_pedido_desde_carrito()
        self.client.get("/logout")
        self.iniciar_sesion("vendedor@panaderia.com")

        respuesta = self.client.post(
            f"/vendedor/pedido/{pedido_id}/estado",
            data={"estado": "preparando"},
            follow_redirects=True,
        )
        self.assertIn(b"Estado actualizado", respuesta.data)

        respuesta = self.client.post(
            f"/vendedor/pedido/{pedido_id}/estado",
            data={"estado": "cancelado"},
            follow_redirects=True,
        )
        self.assertIn(b"Estado no v", respuesta.data)
        with closing(sqlite3.connect(self.db_path)) as conn:
            estado = conn.execute(
                "SELECT estado FROM pedidos WHERE id = ?", (pedido_id,)
            ).fetchone()[0]
        self.assertEqual(estado, "preparando")

    def test_limpieza_detecta_columnas_faltantes(self):
        with self.assertRaisesRegex(ValueError, "Faltan columnas"):
            limpiar_datos(pd.DataFrame({"producto": ["Pan"]}))


if __name__ == "__main__":
    unittest.main()
