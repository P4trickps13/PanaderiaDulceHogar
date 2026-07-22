import os
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, session

from routes.admin import admin_bp
from routes.cliente import cliente_bp
from routes.login import login_bp
from routes.vendedor import vendedor_bp


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "panaderia.db"
SQL_PATH = BASE_DIR / "database" / "panaderia.sql"
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
GENERATED_FOLDER = BASE_DIR / "static" / "generated"


def create_app(test_config=None):
    """Crea y configura la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("PANADERIA_SECRET_KEY", "clave-solo-para-desarrollo"),
        DB_PATH=DB_PATH,
        SQL_PATH=SQL_PATH,
        UPLOAD_FOLDER=UPLOAD_FOLDER,
        GENERATED_FOLDER=GENERATED_FOLDER,
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if test_config:
        app.config.update(test_config)

    init_db(app)

    app.register_blueprint(login_bp)
    app.register_blueprint(cliente_bp)
    app.register_blueprint(vendedor_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def carrito_global():
        carrito = session.get("carrito", {})
        total = 0
        for cantidad in carrito.values():
            try:
                total += max(int(cantidad), 0)
            except (TypeError, ValueError):
                continue
        return {"carrito_total": total}

    return app


def init_db(app):
    """Inicializa la base de datos y aplica migraciones compatibles."""
    db_path = Path(app.config["DB_PATH"])
    sql_path = Path(app.config["SQL_PATH"])
    upload_folder = Path(app.config["UPLOAD_FOLDER"])
    generated_folder = Path(app.config["GENERATED_FOLDER"])

    db_path.parent.mkdir(parents=True, exist_ok=True)
    upload_folder.mkdir(parents=True, exist_ok=True)
    generated_folder.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(sql_path.read_text(encoding="utf-8"))
        migrar_productos_imagen(conn)
        migrar_comprobantes_cliente(conn)
        migrar_comprobantes_unicos(conn)
        conn.commit()


def migrar_productos_imagen(conn):
    existe = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'productos'"
    ).fetchone()
    if not existe:
        return

    columnas = [fila[1] for fila in conn.execute("PRAGMA table_info(productos)").fetchall()]
    if "imagen" not in columnas:
        conn.execute("ALTER TABLE productos ADD COLUMN imagen TEXT DEFAULT 'pan-frances.svg'")


def migrar_comprobantes_cliente(conn):
    existe = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'comprobantes'"
    ).fetchone()
    if not existe:
        return

    columnas = [fila[1] for fila in conn.execute("PRAGMA table_info(comprobantes)").fetchall()]
    migraciones = {
        "nombre_cliente": "TEXT DEFAULT ''",
        "ruc": "TEXT DEFAULT ''",
        "razon_social": "TEXT DEFAULT ''",
    }
    for columna, definicion in migraciones.items():
        if columna not in columnas:
            conn.execute(f"ALTER TABLE comprobantes ADD COLUMN {columna} {definicion}")


def migrar_comprobantes_unicos(conn):
    """Conserva un comprobante por pedido y protege la integridad futura."""
    existe = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'comprobantes'"
    ).fetchone()
    if not existe:
        return

    conn.execute(
        """
        DELETE FROM comprobantes
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM comprobantes
            GROUP BY pedido_id
        )
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_comprobante_pedido
        ON comprobantes(pedido_id)
        """
    )


app = create_app()


if __name__ == "__main__":
    debug_habilitado = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_habilitado)
