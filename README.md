# QuieroTuJersey

Proyecto final de Unix: tienda en línea de jerseys de la Liga MX desplegada
en Linux instalado de forma nativa (bare metal), con NGINX como proxy inverso,
Gunicorn como servidor de aplicaciones, Flask y PostgreSQL.

## Arquitectura

```
Navegador -> NGINX (:80) -> Gunicorn (127.0.0.1:8000) -> Flask -> PostgreSQL (:5432)
```

NGINX y Gunicorn se ejecutan como servicios de systemd.

## Estructura

```
app/                  Aplicación Flask (app.py, database.py, templates/)
database/             Scripts SQL en orden de ejecución
  00_roles.sql        Rol quierotujersey_app y base quierotujersey
  01_base.sql         Equipos, jerseys e inventario con datos iniciales
  02_pedidos.sql      Clientes, pedidos y detalle de pedido
  03_vistas_funciones.sql  Vistas y funciones PL/pgSQL
deploy/               Configuración de despliegue
  quierotujersey.service      Servicio systemd de Gunicorn
  quierotujersey.nginx.conf   Sitio de NGINX
scripts/respaldo_bd.sh  Respaldo completo de la BD con pg_dump
.env.example          Plantilla de variables de entorno
```

## Vistas

| Ruta | Descripción |
|---|---|
| `/` | Inicio |
| `/jerseys` | Catálogo |
| `/jerseys/<id>` | Detalle y selección de talla |
| `/carrito` | Carrito de compras |
| `/checkout` | Datos del cliente y confirmación |
| `/pedido/<id>` | Pedido registrado |
| `/admin/login` | Acceso de administrador |
| `/admin` | Lista de jerseys (alta, edición, baja) |
| `/admin/jerseys/nuevo`, `/admin/jerseys/<id>/editar` | Formulario de jersey |
| `/admin/pedidos` | Pedidos y cancelación |
| `/estado` | Estado del sistema y de la conexión a la BD (JSON) |

## Crear la base de datos

Como superusuario de PostgreSQL:

```bash
psql -d postgres -f database/00_roles.sql
psql -d quierotujersey -f database/01_base.sql
psql -d quierotujersey -f database/02_pedidos.sql
psql -d quierotujersey -f database/03_vistas_funciones.sql
psql -d postgres -c "\password quierotujersey_app"
```

## Ejecutar en desarrollo

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env    # y llenar los valores
python app/app.py
```

Abrir `http://127.0.0.1:5001/`.

Para generar el hash de la contraseña de administrador:

```bash
python -c 'import getpass; from werkzeug.security import generate_password_hash as g; print(g(getpass.getpass()))'
```

## Ejecutar con Gunicorn

```bash
gunicorn --chdir app --workers 3 --bind 127.0.0.1:8000 app:app
```

## Respaldo de la base de datos

```bash
./scripts/respaldo_bd.sh
```
