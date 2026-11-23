
from database import obtener_conexion
from flask import Flask, render_template, abort

app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template(
        "index.html",
        titulo="Mi primera aplicación dinámica",
        sistema="macOS ARM64",
        mensaje="Flask y HTML conectados correctamente"
    )


@app.route("/saludo")
def saludo():
    return "<h1>Bienvenido a mi proyecto final Unix</h1>"


@app.route("/estado")
def estado():
    return {
        "servidor": "Flask",
        "sistema": "macOS",
        "estado": "activo"
    }


@app.route("/jerseys")
def mostrar_jerseys():
    consulta = """
        SELECT
            j.id_jersey,
            e.nombre AS equipo,
            j.temporada,
            j.tipo,
            j.precio,
            COALESCE(SUM(i.stock), 0) AS stock
        FROM jerseys j
        INNER JOIN equipos e
            ON j.id_equipo = e.id_equipo
        LEFT JOIN inventario i
            ON j.id_jersey = i.id_jersey
        GROUP BY
            j.id_jersey,
            e.nombre,
            j.temporada,
            j.tipo,
            j.precio
        ORDER BY j.id_jersey;
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
        WHERE j.id_jersey = %s;
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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
