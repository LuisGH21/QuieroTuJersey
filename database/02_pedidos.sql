
CREATE TABLE clientes (
    id_cliente INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE pedidos (
    id_pedido INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cliente INTEGER NOT NULL,
    fecha TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(10,2) NOT NULL CHECK (total >= 0),
    estado VARCHAR(20) NOT NULL DEFAULT 'confirmado',

    CONSTRAINT fk_pedido_cliente
        FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente),

    CONSTRAINT chk_estado_pedido
        CHECK (estado IN ('pendiente', 'confirmado', 'cancelado'))
);

CREATE TABLE detalle_pedido (
    id_detalle INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_pedido INTEGER NOT NULL,
    id_inventario INTEGER NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) NOT NULL CHECK (precio_unitario > 0),

    CONSTRAINT fk_detalle_pedido
        FOREIGN KEY (id_pedido)
        REFERENCES pedidos(id_pedido),

    CONSTRAINT fk_detalle_inventario
        FOREIGN KEY (id_inventario)
        REFERENCES inventario(id_inventario),

    CONSTRAINT uq_pedido_inventario
        UNIQUE (id_pedido, id_inventario)
);

GRANT SELECT, INSERT, UPDATE, DELETE
ON clientes, pedidos, detalle_pedido
TO quierotujersey_app;

GRANT USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA public
TO quierotujersey_app;
