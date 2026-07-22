PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('admin', 'cliente', 'vendedor'))
);

CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    precio REAL NOT NULL CHECK (precio > 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    imagen TEXT NOT NULL DEFAULT 'pan-frances.svg'
);

CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    total REAL NOT NULL CHECK (total > 0),
    estado TEXT NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'preparando', 'entregado', 'pagado')),
    metodo_pago TEXT NOT NULL DEFAULT 'yape',
    numero_operacion TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS pedido_detalles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario REAL NOT NULL CHECK (precio_unitario > 0),
    subtotal REAL NOT NULL CHECK (subtotal > 0),
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE TABLE IF NOT EXISTS comprobantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('boleta', 'factura')),
    serie TEXT NOT NULL,
    numero TEXT NOT NULL,
    documento_cliente TEXT,
    nombre_cliente TEXT DEFAULT '',
    ruc TEXT DEFAULT '',
    razon_social TEXT DEFAULT '',
    fecha TEXT NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
);

CREATE INDEX IF NOT EXISTS idx_pedidos_usuario ON pedidos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado_fecha ON pedidos(estado, fecha);
CREATE INDEX IF NOT EXISTS idx_detalles_pedido ON pedido_detalles(pedido_id);
CREATE INDEX IF NOT EXISTS idx_detalles_producto ON pedido_detalles(producto_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_comprobante_numero
    ON comprobantes(tipo, serie, numero);

INSERT OR IGNORE INTO usuarios (id, nombre, email, password_hash, rol) VALUES
(1, 'Administrador', 'admin@panaderia.com', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'admin'),
(2, 'Vendedor', 'vendedor@panaderia.com', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'vendedor'),
(3, 'Cliente', 'cliente@panaderia.com', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'cliente');

INSERT OR IGNORE INTO productos (id, nombre, descripcion, precio, stock, activo, imagen) VALUES
(1, 'Pan frances', 'Pan crujiente recien horneado.', 0.40, 200, 1, 'pan-frances.svg'),
(2, 'Croissant', 'Masa hojaldrada con mantequilla.', 3.50, 40, 1, 'croissant.svg'),
(3, 'Empanada de pollo', 'Empanada artesanal rellena.', 4.50, 50, 1, 'empanada.svg'),
(4, 'Torta de chocolate', 'Porcion de torta humeda.', 7.00, 25, 1, 'torta-chocolate.svg'),
(5, 'Cafe americano', 'Cafe caliente para acompanar.', 4.00, 60, 1, 'cafe.svg'),
(6, 'Baguette artesanal', 'Pan largo de corteza dorada y miga suave.', 4.80, 35, 1, 'baguette.svg'),
(7, 'Dona glaseada', 'Dona suave con cobertura dulce.', 3.20, 45, 1, 'dona.svg'),
(8, 'Pan integral', 'Pan con harina integral y semillas.', 1.20, 90, 1, 'pan-integral.svg'),
(9, 'Alfajor', 'Galletas suaves con manjar blanco.', 2.80, 60, 1, 'alfajor.svg'),
(10, 'Muffin de vainilla', 'Quequito individual esponjoso.', 3.80, 42, 1, 'muffin.svg'),
(11, 'Milhojas', 'Postre hojaldrado con crema pastelera.', 6.50, 22, 1, 'milhojas.svg'),
(12, 'Jugo natural', 'Bebida fresca para acompanar el pedido.', 5.00, 30, 1, 'jugo.svg');

UPDATE productos SET imagen = 'pan-frances.svg' WHERE id = 1 AND (imagen IS NULL OR imagen = '');
UPDATE productos SET imagen = 'croissant.svg' WHERE id = 2 AND (imagen IS NULL OR imagen = '' OR imagen = 'pan-frances.svg');
UPDATE productos SET imagen = 'empanada.svg' WHERE id = 3 AND (imagen IS NULL OR imagen = '' OR imagen = 'pan-frances.svg');
UPDATE productos SET imagen = 'torta-chocolate.svg' WHERE id = 4 AND (imagen IS NULL OR imagen = '' OR imagen = 'pan-frances.svg');
UPDATE productos SET imagen = 'cafe.svg' WHERE id = 5 AND (imagen IS NULL OR imagen = '' OR imagen = 'pan-frances.svg');
