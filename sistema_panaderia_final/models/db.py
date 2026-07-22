import sqlite3
from contextlib import contextmanager

from flask import current_app


@contextmanager
def get_db():
    """Entrega una conexión SQLite configurada y la cierra al finalizar."""
    conn = sqlite3.connect(current_app.config["DB_PATH"], timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
