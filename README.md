# QuieroTuJersey

Proyecto final de Unix. Flask muestra un catálogo de jerseys con precios,
tallas y existencias consultados en PostgreSQL.

## Ejecutar en local

Necesitas Python 3 y una instancia local de PostgreSQL con las tablas
`equipos`, `jerseys` e `inventario`. Crea un archivo `.env` en la raíz
del proyecto con los valores de tu conexión para `DB_HOST`, `DB_PORT`,
`DB_NAME`, `DB_USER` y `DB_PASSWORD`.

Desde la raíz del proyecto, ejecuta:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app/app.py
```

Abre [el catálogo local](http://127.0.0.1:5001/jerseys).
