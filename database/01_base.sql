-- =============================================================
-- QuieroTuJersey - 01_base.sql
-- Catalogo: equipos, jerseys e inventario por talla.
-- Ejecutar conectado a la base quierotujersey.
-- =============================================================

BEGIN;

-- -------------------------------------------------------------
-- Tabla: equipos
-- -------------------------------------------------------------
CREATE TABLE equipos (
    id_equipo INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre    VARCHAR(100) NOT NULL UNIQUE,
    ciudad    VARCHAR(100) NOT NULL
);

-- -------------------------------------------------------------
-- Tabla: jerseys (un modelo por equipo, temporada y tipo)
-- -------------------------------------------------------------
CREATE TABLE jerseys (
    id_jersey   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_equipo   INTEGER NOT NULL,
    temporada   VARCHAR(20) NOT NULL,
    tipo        VARCHAR(30) NOT NULL,
    precio      NUMERIC(10,2) NOT NULL,
    descripcion TEXT,

    CONSTRAINT fk_jersey_equipo
        FOREIGN KEY (id_equipo)
        REFERENCES equipos(id_equipo),

    CONSTRAINT chk_precio
        CHECK (precio > 0),

    CONSTRAINT uq_jersey_modelo
        UNIQUE (id_equipo, temporada, tipo)
);

-- -------------------------------------------------------------
-- Tabla: inventario (existencias por jersey y talla)
-- -------------------------------------------------------------
CREATE TABLE inventario (
    id_inventario INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_jersey     INTEGER NOT NULL,
    talla         VARCHAR(5) NOT NULL,
    stock         INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT fk_inventario_jersey
        FOREIGN KEY (id_jersey)
        REFERENCES jerseys(id_jersey),

    CONSTRAINT chk_stock
        CHECK (stock >= 0),

    CONSTRAINT chk_talla
        CHECK (talla IN ('S', 'M', 'L', 'XL', 'XXL')),

    CONSTRAINT uq_jersey_talla
        UNIQUE (id_jersey, talla)
);

-- -------------------------------------------------------------
-- Datos iniciales
-- -------------------------------------------------------------
INSERT INTO equipos (nombre, ciudad) VALUES
    ('América',   'Ciudad de México'),
    ('Chivas',    'Guadalajara'),
    ('Pumas',     'Ciudad de México'),
    ('Cruz Azul', 'Ciudad de México'),
    ('Tigres',    'San Nicolás de los Garza'),
    ('Monterrey', 'Monterrey');

INSERT INTO jerseys (id_equipo, temporada, tipo, precio, descripcion) VALUES
    (1, '2026/27', 'Local',     1899.00, 'Jersey local del América'),
    (2, '2026/27', 'Local',     1799.00, 'Jersey local de Chivas'),
    (3, '2026/27', 'Visitante', 1699.00, 'Jersey visitante de Pumas'),
    (4, '2026/27', 'Local',     1899.00, 'Jersey local de Cruz Azul'),
    (5, '2026/27', 'Local',     1999.00, 'Jersey local de Tigres'),
    (6, '2026/27', 'Local',     1999.00, 'Jersey local de Monterrey');

INSERT INTO inventario (id_jersey, talla, stock) VALUES
    (1, 'S', 5), (1, 'M', 10), (1, 'L', 8), (1, 'XL', 3),
    (2, 'S', 4), (2, 'M', 8),  (2, 'L', 6), (2, 'XL', 2),
    (3, 'S', 3), (3, 'M', 6),  (3, 'L', 5), (3, 'XL', 2),
    (4, 'S', 4), (4, 'M', 7),  (4, 'L', 6), (4, 'XL', 3),
    (5, 'S', 5), (5, 'M', 9),  (5, 'L', 7), (5, 'XL', 4),
    (6, 'S', 4), (6, 'M', 8),  (6, 'L', 7), (6, 'XL', 3);

-- -------------------------------------------------------------
-- Permisos del rol de la aplicacion
-- -------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE, DELETE
    ON equipos, jerseys, inventario
    TO quierotujersey_app;

GRANT USAGE, SELECT
    ON ALL SEQUENCES IN SCHEMA public
    TO quierotujersey_app;

COMMIT;
