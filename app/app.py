
import json
import os
import platform
import re
from decimal import Decimal
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    abort,
    request,
    redirect,
    url_for,
    session,
    flash
)

from database import obtener_conexion


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


@app.route("/")
def inicio():
    return render_template(
        "index.html",
        sistema=platform.platform(),
        version_python=platform.python_version()
    )


@app.route("/estado")
def estado():
    try:
        with obtener_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT version();")
                version_bd = cursor.fetchone()[0]
        estado_bd = "conectada"
    except Exception:
        version_bd = None
        estado_bd = "sin conexion"

    return {
        "aplicacion": "QuieroTuJersey",
        "sistema": platform.platform(),
        "python": platform.python_version(),
        "base_de_datos": estado_bd,
        "version_bd": version_bd
    }


@app.route("/jerseys")
def mostrar_jerseys():
    consulta = """
        SELECT
            id_jersey,
            equipo,
            temporada,
            tipo,
            precio,
            stock_total
        FROM v_catalogo
        ORDER BY id_jersey;
    """

    with obtener_conexion() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta)
            resultados = cursor.fetchall()

    jerseys = []

    for fila in resultados:
        jerseys.append({
            "id": fila[0],
            "equipo": fila[1],
            "temporada": fila[2],
            "tipo": fila[3],
            "precio": fila[4],
            "stock": fila[5]
        })

    return render_template("jerseys.html", jerseys=jerseys)


@app.route("/jerseys/<int:id_jersey>")
def detalle_jersey(id_jersey):
    consulta = """
        SELECT
            j.id_jersey,
            e.nombre,
            j.temporada,
            j.tipo,
            j.precio,
            j.descripcion
        FROM jerseys j
        INNER JOIN equipos e
            ON j.id_equipo = e.id_equipo
        WHERE j.id_jersey = %s
          AND j.activo;
    """

    consulta_tallas = """
        SELECT talla, stock
        FROM inventario
        WHERE id_jersey = %s
        ORDER BY CASE talla
            WHEN 'S' THEN 1
            WHEN 'M' THEN 2
            WHEN 'L' THEN 3
            WHEN 'XL' THEN 4
            WHEN 'XXL' THEN 5
        END;
    """

    with obtener_conexion() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta, (id_jersey,))
            producto = cursor.fetchone()

            if producto is None:
                abort(404)

            cursor.execute(consulta_tallas, (id_jersey,))
            tallas = cursor.fetchall()

    jersey = {
        "id": producto[0],
        "equipo": producto[1],
        "temporada": producto[2],
        "tipo": producto[3],
        "precio": producto[4],
        "descripcion": producto[5]
    }

    return render_template(
        "detalle_jersey.html",
        jersey=jersey,
        tallas=tallas
    )


@app.route("/carrito/agregar/<int:id_jersey>", methods=["POST"])
def agregar_al_carrito(id_jersey):
    talla = request.form.get("talla", "")

    try:
        cantidad = int(request.form.get("cantidad", ""))
    except (TypeError, ValueError):
        cantidad = 0

    if cantidad < 1:
        flash("Selecciona una cantidad válida.")
        return redirect(url_for("detalle_jersey", id_jersey=id_jersey))

    consulta = """
        SELECT i.stock
        FROM inventario i
        INNER JOIN jerseys j
            ON j.id_jersey = i.id_jersey
        WHERE i.id_jersey = %s
          AND i.talla = %s
          AND j.activo;
    """

    with obtener_conexion() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta, (id_jersey, talla))
            resultado = cursor.fetchone()

    if resultado is None or resultado[0] == 0:
        flash("La talla seleccionada no está disponible.")
        return redirect(url_for("detalle_jersey", id_jersey=id_jersey))

    stock = resultado[0]
    carrito = session.get("carrito", [])

    producto_existente = None

    for producto in carrito:
        if (
            producto["id_jersey"] == id_jersey
            and producto["talla"] == talla
        ):
            producto_existente = producto
            break

    cantidad_actual = (
        producto_existente["cantidad"]
        if producto_existente is not None
        else 0
    )

    if cantidad_actual + cantidad > stock:
        flash(
            f"No hay suficientes unidades. "
            f"Stock disponible: {stock}."
        )
        return redirect(url_for("detalle_jersey", id_jersey=id_jersey))

    if producto_existente is not None:
        producto_existente["cantidad"] += cantidad
    else:
        carrito.append({
            "id_jersey": id_jersey,
            "talla": talla,
            "cantidad": cantidad
        })

    session["carrito"] = carrito

    flash("Producto agregado correctamente al carrito.")
    return redirect(url_for("ver_carrito"))


def construir_carrito(carrito):
    """Consulta precio y stock vigentes de cada producto del carrito."""
    productos = []
    total = Decimal("0.00")

    consulta = """
        SELECT
            e.nombre,
            j.temporada,
            j.tipo,
            j.precio,
            i.stock
        FROM jerseys j
        INNER JOIN equipos e
            ON j.id_equipo = e.id_equipo
        INNER JOIN inventario i
            ON i.id_jersey = j.id_jersey
        WHERE j.id_jersey = %s
          AND i.talla = %s;
    """

    if carrito:
        with obtener_conexion() as conexion:
            with conexion.cursor() as cursor:
                for item in carrito:
                    cursor.execute(
                        consulta,
                        (item["id_jersey"], item["talla"])
                    )

                    resultado = cursor.fetchone()

                    if resultado is None:
                        continue

                    precio = resultado[3]
                    cantidad = item["cantidad"]
                    subtotal = precio * cantidad

                    productos.append({
                        "id_jersey": item["id_jersey"],
                        "equipo": resultado[0],
                        "temporada": resultado[1],
                        "tipo": resultado[2],
                        "precio": precio,
                        "talla": item["talla"],
                        "cantidad": cantidad,
                        "stock": resultado[4],
                        "subtotal": subtotal
                    })

                    total += subtotal

    return productos, total


@app.route("/carrito")
def ver_carrito():
    carrito = session.get("carrito", [])
    productos, total = construir_carrito(carrito)

    return render_template(
        "carrito.html",
        productos=productos,
        total=total
    )


@app.route("/carrito/actualizar/<int:id_jersey>", methods=["POST"])
def actualizar_carrito(id_jersey):
    talla = request.form.get("talla", "")

    try:
        nueva_cantidad = int(request.form.get("cantidad", ""))
    except (TypeError, ValueError):
        nueva_cantidad = 0

    if nueva_cantidad < 1:
        flash("La cantidad debe ser un número entero mayor que cero.")
        return redirect(url_for("ver_carrito"))

    carrito = session.get("carrito", [])

    producto_existente = None

    for producto in carrito:
        if (
            producto["id_jersey"] == id_jersey
            and producto["talla"] == talla
        ):
            producto_existente = producto
            break

    if producto_existente is None:
        flash("El producto no se encuentra en tu carrito.")
        return redirect(url_for("ver_carrito"))

    consulta = """
        SELECT stock
        FROM inventario
        WHERE id_jersey = %s
          AND talla = %s;
    """

    with obtener_conexion() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta, (id_jersey, talla))
            resultado = cursor.fetchone()

    if resultado is None:
        flash("El producto ya no tiene inventario registrado.")
        return redirect(url_for("ver_carrito"))

    stock = resultado[0]

    if nueva_cantidad > stock:
        flash(
            f"No puedes seleccionar {nueva_cantidad} unidades. "
            f"Solo hay {stock} disponibles."
        )
        return redirect(url_for("ver_carrito"))

    producto_existente["cantidad"] = nueva_cantidad
    session["carrito"] = carrito

    flash("Cantidad actualizada correctamente.")
    return redirect(url_for("ver_carrito"))


@app.route("/carrito/eliminar/<int:id_jersey>", methods=["POST"])
def eliminar_del_carrito(id_jersey):
    talla = request.form.get("talla", "")
    carrito = session.get("carrito", [])

    carrito = [
        producto
        for producto in carrito
        if not (
            producto["id_jersey"] == id_jersey
            and producto["talla"] == talla
        )
    ]

    session["carrito"] = carrito

    flash("Producto eliminado del carrito.")
    return redirect(url_for("ver_carrito"))


PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_cliente(nombre, email):
    if len(nombre) < 2 or len(nombre) > 150:
        return "Escribe un nombre de entre 2 y 150 caracteres."

    if len(email) > 150 or not PATRON_EMAIL.match(email):
        return "Escribe un correo electrónico válido."

    return None


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    carrito = session.get("carrito", [])

    if not carrito:
        flash("Tu carrito está vacío.")
        return redirect(url_for("ver_carrito"))

    productos, total = construir_carrito(carrito)
    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip()

    if request.method == "POST":
        error = validar_cliente(nombre, email)

        if error:
            flash(error)
            return render_template(
                "checkout.html",
                productos=productos,
                total=total,
                nombre=nombre,
                email=email
            )

        articulos = [
            {
                "id_jersey": item["id_jersey"],
                "talla": item["talla"],
                "cantidad": item["cantidad"]
            }
            for item in carrito
        ]

        try:
            with obtener_conexion() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        "SELECT confirmar_pedido(%s, %s, %s::jsonb);",
                        (nombre, email, json.dumps(articulos))
                    )
                    id_pedido = cursor.fetchone()[0]
        except psycopg.errors.RaiseException as error_bd:
            flash(
                error_bd.diag.message_primary
                or "No se pudo confirmar el pedido."
            )
            return redirect(url_for("ver_carrito"))

        session["carrito"] = []

        mis_pedidos = session.get("mis_pedidos", [])
        mis_pedidos.append(id_pedido)
        session["mis_pedidos"] = mis_pedidos[-20:]

        return redirect(url_for("ver_pedido", id_pedido=id_pedido))

    return render_template(
        "checkout.html",
        productos=productos,
        total=total,
        nombre=nombre,
        email=email
    )


@app.route("/pedido/<int:id_pedido>")
def ver_pedido(id_pedido):
    # Solo se muestran los pedidos hechos desde este navegador
    if id_pedido not in session.get("mis_pedidos", []):
        abort(404)

    consulta_pedido = """
        SELECT id_pedido, fecha, cliente, email, estado, total, articulos
        FROM v_pedidos_resumen
        WHERE id_pedido = %s;
    """

    consulta_detalle = """
        SELECT
            e.nombre,
            j.temporada,
            j.tipo,
            i.talla,
            d.cantidad,
            d.precio_unitario,
            d.cantidad * d.precio_unitario AS subtotal
        FROM detalle_pedido d
        INNER JOIN inventario i
            ON i.id_inventario = d.id_inventario
        INNER JOIN jerseys j
            ON j.id_jersey = i.id_jersey
        INNER JOIN equipos e
            ON e.id_equipo = j.id_equipo
        WHERE d.id_pedido = %s
        ORDER BY d.id_detalle;
    """

    with obtener_conexion() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta_pedido, (id_pedido,))
            fila = cursor.fetchone()

            if fila is None:
                abort(404)

            cursor.execute(consulta_detalle, (id_pedido,))
            detalle = cursor.fetchall()

    pedido = {
        "id": fila[0],
        "fecha": fila[1],
        "cliente": fila[2],
        "email": fila[3],
        "estado": fila[4],
        "total": fila[5],
        "articulos": fila[6]
    }

    renglones = [
        {
            "equipo": r[0],
            "temporada": r[1],
            "tipo": r[2],
            "talla": r[3],
            "cantidad": r[4],
            "precio": r[5],
            "subtotal": r[6]
        }
        for r in detalle
    ]

    return render_template(
        "pedido.html",
        pedido=pedido,
        renglones=renglones
    )


if __name__ == "__main__":
    app.run(
        host=os.environ.get("FLASK_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASK_PORT", "5001")),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1"
    )
