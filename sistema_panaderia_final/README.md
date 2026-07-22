# Sistema de Panadería Dulce Hogar

Proyecto final del curso Lenguaje de Programación. Integra programación orientada a objetos y programación procedural, una aplicación web Flask, persistencia SQLite y análisis de ventas con pandas, NumPy y Matplotlib.

## Requisitos

- Python 3.10 o superior.

## Instalación y ejecución

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abrir `http://127.0.0.1:5000`.

Para activar el modo de depuración únicamente durante desarrollo:

```bash
set FLASK_DEBUG=1
python app.py
```

## Usuarios de demostración

- `admin@panaderia.com` / `123456`
- `vendedor@panaderia.com` / `123456`
- `cliente@panaderia.com` / `123456`

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Para ejecutar cobertura, Ruff y Bandit:

```bash
pip install -r requirements-dev.txt
coverage run -m unittest discover -s tests
coverage report -m
ruff check .
bandit -q -r . -x ./.venv,./tests
```

## Análisis y gráficos

```bash
python prueba_analisis.py
```

El dashboard usa únicamente gráficos interactivos renderizados con una copia local de Chart.js (`static/js/chart.umd.min.js`). No necesita internet y no coloca archivos PNG dentro del dashboard.

Los gráficos permiten:

- Mostrar información emergente al pasar el cursor.
- Filtrar ventas por periodo.
- Cambiar la vista de ventas entre línea y barras.
- Mostrar el top 5, top 10 o todos los productos.
- Actualizar los datos desde SQLite sin recargar la página mediante `/admin/api/dashboard`.

Los PNG de Matplotlib se conservan únicamente en `resultados/` como evidencia académica exportable del uso de esa biblioteca.

## Organización principal

- `models/`: entidades, reglas de negocio y persistencia.
- `routes/`: autenticación y controladores por rol.
- `analisis/`: limpieza, métricas, resúmenes y gráficos.
- `templates/`: vistas HTML.
- `static/`: estilos, imágenes del catálogo y scripts.
- `tests/`: 21 pruebas automatizadas de objetos, roles, pedidos, stock, comprobantes, CRUD, análisis, API y visualización.

La relación entre el código y los criterios técnicos se resume en `EVIDENCIA_RUBRICA.md` y la auditoría final en `AUDITORIA_FINAL.md`.
