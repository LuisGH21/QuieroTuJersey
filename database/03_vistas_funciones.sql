-- =============================================================
-- QuieroTuJersey - 03_vistas_funciones.sql
-- Vistas de consulta y funciones de negocio (PL/pgSQL).
-- Ejecutar conectado a la base quierotujersey, despues de 01 y 02.
-- =============================================================

BEGIN;

-- -------------------------------------------------------------
-- Baja logica de jerseys: un jersey con pedidos no se borra,
-- se marca como inactivo para conservar el historial.
-- -------------------------------------------------------------
ALTER TABLE jerseys
    ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE;

-- -------------------------------------------------------------
-- Vista: catalogo de jerseys activos con stock total
-- -------------------------------------------------------------
CREATE VIEW v_catalogo AS
SELECT
    j.id_jersey,
    e.nombre                   AS equipo,
    e.ciudad,
    j.temporada,
    j.tipo,
    j.precio,
    j.descripcion,
    COALESCE(SUM(i.stock), 0)  AS stock_total
FROM jerseys j
INNER JOIN equipos e
    ON e.id_equipo = j.id_equipo
LEFT JOIN inventario i
    ON i.id_jersey = j.id_jersey
WHERE j.activo
GROUP BY
    j.id_jersey, e.nombre, e.ciudad,
    j.temporada, j.tipo, j.precio, j.descripcion;

-- -------------------------------------------------------------
-- Vista: resumen de pedidos con datos del cliente
-- -------------------------------------------------------------
CREATE VIEW v_pedidos_resumen AS
SELECT
    p.id_pedido,
    p.fecha,
    c.nombre                      AS cliente,
    c.email,
    p.estado,
    p.total,
    COALESCE(SUM(d.cantidad), 0)  AS articulos
FROM pedidos p
INNER JOIN clientes c
    ON c.id_cliente = p.id_cliente
LEFT JOIN detalle_pedido d
    ON d.id_pedido = p.id_pedido
GROUP BY
    p.id_pedido, p.fecha, c.nombre, c.email, p.estado, p.total;

-- -------------------------------------------------------------
-- Funcion: confirmar_pedido
-- Recibe los datos del cliente y los articulos del carrito en JSON:
--   [{"id_jersey": 1, "talla": "M", "cantidad": 2}, ...]
-- En una sola transaccion: registra o reutiliza al cliente,
-- crea el pedido, inserta el detalle con el precio vigente,
-- descuenta el stock y calcula el total.
-- Si algun articulo no tiene stock suficiente, lanza un error
-- y no se guarda nada.
-- Devuelve el id del pedido creado.
-- -------------------------------------------------------------
CREATE FUNCTION confirmar_pedido(
    p_nombre VARCHAR,
    p_email  VARCHAR,
    p_items  JSONB
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_cliente    INTEGER;
    v_id_pedido     INTEGER;
    v_item          JSONB;
    v_id_inventario INTEGER;
    v_stock         INTEGER;
    v_precio        NUMERIC(10,2);
    v_cantidad      INTEGER;
    v_total         NUMERIC(10,2) := 0;
BEGIN
    IF p_items IS NULL
       OR jsonb_typeof(p_items) <> 'array'
       OR jsonb_array_length(p_items) = 0 THEN
        RAISE EXCEPTION 'El carrito esta vacio.';
    END IF;

    -- Cliente: se reutiliza si el email ya existe
    INSERT INTO clientes (nombre, email)
    VALUES (TRIM(p_nombre), LOWER(TRIM(p_email)))
    ON CONFLICT (email)
        DO UPDATE SET nombre = EXCLUDED.nombre
    RETURNING id_cliente INTO v_id_cliente;

    -- Pedido con total provisional
    INSERT INTO pedidos (id_cliente, total)
    VALUES (v_id_cliente, 0)
    RETURNING id_pedido INTO v_id_pedido;

    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
    LOOP
        v_cantidad := (v_item ->> 'cantidad')::INTEGER;

        IF v_cantidad IS NULL OR v_cantidad < 1 THEN
            RAISE EXCEPTION 'Cantidad invalida en el carrito.';
        END IF;

        -- Bloquea la fila de inventario para evitar ventas simultaneas
        SELECT i.id_inventario, i.stock, j.precio
          INTO v_id_inventario, v_stock, v_precio
          FROM inventario i
          INNER JOIN jerseys j
              ON j.id_jersey = i.id_jersey
         WHERE i.id_jersey = (v_item ->> 'id_jersey')::INTEGER
           AND i.talla     = v_item ->> 'talla'
           AND j.activo
           FOR UPDATE OF i;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'El jersey % en talla % no existe.',
                v_item ->> 'id_jersey', v_item ->> 'talla';
        END IF;

        IF v_stock < v_cantidad THEN
            RAISE EXCEPTION 'Stock insuficiente para el jersey % talla %: disponibles %.',
                v_item ->> 'id_jersey', v_item ->> 'talla', v_stock;
        END IF;

        INSERT INTO detalle_pedido (id_pedido, id_inventario, cantidad, precio_unitario)
        VALUES (v_id_pedido, v_id_inventario, v_cantidad, v_precio);

        UPDATE inventario
           SET stock = stock - v_cantidad
         WHERE id_inventario = v_id_inventario;

        v_total := v_total + (v_precio * v_cantidad);
    END LOOP;

    UPDATE pedidos
       SET total = v_total
     WHERE id_pedido = v_id_pedido;

    RETURN v_id_pedido;
END;
$$;

-- -------------------------------------------------------------
-- Funcion: cancelar_pedido
-- Cambia un pedido confirmado a cancelado y devuelve el stock.
-- -------------------------------------------------------------
CREATE FUNCTION cancelar_pedido(p_id_pedido INTEGER)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_estado VARCHAR(20);
BEGIN
    SELECT estado
      INTO v_estado
      FROM pedidos
     WHERE id_pedido = p_id_pedido
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El pedido % no existe.', p_id_pedido;
    END IF;

    IF v_estado = 'cancelado' THEN
        RAISE EXCEPTION 'El pedido % ya estaba cancelado.', p_id_pedido;
    END IF;

    UPDATE inventario i
       SET stock = i.stock + d.cantidad
      FROM detalle_pedido d
     WHERE d.id_pedido = p_id_pedido
       AND d.id_inventario = i.id_inventario;

    UPDATE pedidos
       SET estado = 'cancelado'
     WHERE id_pedido = p_id_pedido;
END;
$$;

-- -------------------------------------------------------------
-- Permisos del rol de la aplicacion
-- -------------------------------------------------------------
GRANT SELECT ON v_catalogo, v_pedidos_resumen TO quierotujersey_app;

REVOKE EXECUTE ON FUNCTION confirmar_pedido(VARCHAR, VARCHAR, JSONB) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION cancelar_pedido(INTEGER) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION confirmar_pedido(VARCHAR, VARCHAR, JSONB) TO quierotujersey_app;
GRANT EXECUTE ON FUNCTION cancelar_pedido(INTEGER) TO quierotujersey_app;

COMMIT;
