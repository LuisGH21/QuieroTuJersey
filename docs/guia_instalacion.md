# Guía de instalación y despliegue — QuieroTuJersey

Guía para las Etapas 5 (instalación bare metal) y 6 (despliegue) del proyecto
final de Unix. Sistema elegido: **Ubuntu Server 26.04 LTS** sobre un equipo
**x86_64 (Intel/AMD)**.

Convenciones de esta guía:

- `[MAC]` se ejecuta en la Terminal de la MacBook.
- `[SRV]` se ejecuta en el servidor Linux (directo o por SSH).
- `[FOTO]` indica una evidencia para el reporte. Durante el instalador no hay
  capturas de pantalla: se toman fotos con el celular.

---

## 0. Requisitos y respaldo

| Requisito | Mínimo | Recomendado |
|---|---|---|
| Procesador | x86_64 (Intel o AMD) | — |
| RAM | 1.5 GB | 4 GB o más |
| Disco para Linux | 25 GB | 50 GB o más |
| USB para el instalador | 4 GB | 8 GB o más (se borra completa) |
| Red | Wi-Fi | Cable Ethernet (el instalador lo detecta sin configuración) |

Antes de tocar el disco:

1. Respaldar la información del equipo (disco externo o nube).
2. Si el equipo tiene Windows con **BitLocker**, guardar la clave de recuperación
   (cuenta Microsoft → Dispositivos → Claves de recuperación).
3. Anotar marca y modelo del equipo; se usarán en el reporte.

Formas de instalación válidas para la rúbrica:

| Opción | Cuándo usarla |
|---|---|
| A. Disco completo | El equipo se dedica solo a Linux. Es la más sencilla. |
| B. Arranque dual con Windows | El equipo se sigue usando con Windows. |
| C. Disco externo/SSD por USB | El equipo es prestado y su disco no se toca. |

---

## 1. Preparar la USB de instalación `[MAC]`

1. Descargar `ubuntu-26.04.1-live-server-amd64.iso` desde
   https://ubuntu.com/download/server y el archivo `SHA256SUMS` de la misma página.
2. Verificar la integridad de la ISO:

```bash
cd ~/Downloads
```

```bash
shasum -a 256 ubuntu-26.04.1-live-server-amd64.iso
```

```bash
grep live-server-amd64 SHA256SUMS
```

Los dos valores deben ser idénticos.

3. Identificar la USB (conectarla y comparar la lista antes y después):

```bash
diskutil list external
```

Anotar el identificador, por ejemplo `/dev/disk4`. **Verificar el tamaño:
si se elige el disco equivocado, se borra.**

4. Grabar la ISO (sustituir `N` por el número correcto):

```bash
diskutil unmountDisk /dev/diskN
```

```bash
sudo dd if=ubuntu-26.04.1-live-server-amd64.iso of=/dev/rdiskN bs=4m
```

La copia tarda unos minutos sin mostrar avance; presionar `Ctrl + T` muestra el
progreso.

```bash
diskutil eject /dev/diskN
```

Alternativa gráfica: balenaEtcher.

---

## 2. Preparar el equipo

### Solo para arranque dual (opción B), desde Windows

1. Desactivar el **Inicio rápido**: Panel de control → Opciones de energía →
   Elegir el comportamiento de los botones de inicio/apagado → desmarcar
   "Activar inicio rápido".
2. Liberar espacio: clic derecho en Inicio → Administración de discos → clic
   derecho en `C:` → **Reducir volumen** → al menos 50 000 MB.
3. Dejar ese espacio como "No asignado". No crear partición desde Windows.

### En todos los casos

1. Conectar la USB y el cable de red.
2. Encender y abrir el menú de arranque (según la marca: F12 Dell/Lenovo,
   F9 HP, F8 o Esc ASUS, F12 Acer). Elegir la USB en modo **UEFI**.
3. Secure Boot puede quedar activado: Ubuntu lo soporta.

---

## 3. Instalador de Ubuntu Server `[FOTO en cada pantalla]`

| Pantalla | Selección |
|---|---|
| Idioma | Español |
| Teclado | Spanish (Latin American) |
| Tipo de instalación | Ubuntu Server (no la versión minimizada) |
| Red | La interfaz cableada obtiene IP por DHCP. **Anotar la IP.** |
| Proxy | Vacío |
| Mirror | El sugerido |
| Almacenamiento | Ver tabla siguiente |
| Perfil | Nombre: tu nombre · Servidor: `quierotujersey-srv` · Usuario: `luis` |
| Ubuntu Pro | Omitir |
| SSH | **Marcar "Install OpenSSH server"** |
| Snaps adicionales | Ninguno |

### Particionamiento (Custom storage layout)

Para el reporte conviene un esquema manual y documentado:

| Partición | Tamaño | Formato | Punto de montaje | Propósito |
|---|---|---|---|---|
| EFI | 1 GB | FAT32 | `/boot/efi` | Arranque UEFI. En arranque dual **se reutiliza la de Windows sin formatear**. |
| boot | 2 GB | ext4 | `/boot` | Kernels e initramfs |
| swap | 4 GB | swap | — | Memoria de intercambio |
| raíz | 30 GB | ext4 | `/` | Sistema, PostgreSQL y aplicación |
| home | resto | ext4 | `/home` | Datos de usuarios |

En arranque dual se usa solo el espacio "free space" que se liberó en Windows.

Al terminar, retirar la USB cuando lo indique y reiniciar.

---

## 4. Primer arranque y evidencias de hardware nativo `[SRV]`

Iniciar sesión con el usuario `luis`. Desde aquí se puede trabajar por SSH desde
la Mac:

```bash
ssh luis@IP_DEL_SERVIDOR
```

Crear la carpeta de evidencias:

```bash
mkdir -p ~/evidencias
```

Comprobar que **no** es una máquina virtual (debe responder `none`):

```bash
systemd-detect-virt | tee ~/evidencias/01_virtualizacion.txt
```

Fabricante y modelo físico del equipo:

```bash
sudo dmidecode -t system | tee ~/evidencias/02_dmidecode.txt
```

Procesador, memoria, discos y red:

```bash
lscpu | tee ~/evidencias/03_lscpu.txt
```

```bash
free -h | tee ~/evidencias/04_memoria.txt
```

```bash
lsblk -f | tee ~/evidencias/05_particiones.txt
```

```bash
df -hT | tee ~/evidencias/06_espacio.txt
```

```bash
ip -br a | tee ~/evidencias/07_red.txt
```

```bash
hostnamectl | tee ~/evidencias/08_hostnamectl.txt
```

```bash
cat /etc/os-release | tee ~/evidencias/09_os_release.txt
```

`[FOTO]` o captura por SSH de cada salida.

---

## 5. Actualización del sistema `[SRV]`

```bash
sudo apt update
```

```bash
sudo apt full-upgrade -y
```

```bash
sudo reboot
```

---

## 6. Firewall (UFW) `[SRV]`

```bash
sudo ufw allow OpenSSH
```

```bash
sudo ufw enable
```

```bash
sudo ufw status verbose
```

El puerto 80 se abre en el paso 11, después de instalar NGINX.

---

## 7. Paquetes del servidor `[SRV]`

```bash
sudo apt install -y postgresql nginx python3-venv
```

Verificar versiones y servicios:

```bash
psql --version
```

```bash
nginx -v
```

```bash
python3 --version
```

```bash
systemctl status postgresql --no-pager
```

```bash
systemctl status nginx --no-pager
```

---

## 8. Usuario de sistema y directorio de la aplicación `[SRV]`

Usuario sin shell ni contraseña que ejecutará Gunicorn:

```bash
sudo useradd --system --home-dir /srv/quierotujersey --shell /usr/sbin/nologin quierotujersey
```

```bash
sudo mkdir -p /srv/quierotujersey
```

---

## 9. Copiar el proyecto al servidor

Como el repositorio aún no se publica, se envía un paquete desde la Mac.

`[MAC]` dentro de `~/proyecto-final-unix`, empaquetar la versión confirmada en Git
(no incluye `.env` ni `.venv`):

```bash
git archive --format=tar.gz -o ~/quierotujersey.tar.gz HEAD
```

```bash
scp ~/quierotujersey.tar.gz luis@IP_DEL_SERVIDOR:/tmp/
```

`[SRV]` extraer:

```bash
sudo tar -xzf /tmp/quierotujersey.tar.gz -C /srv/quierotujersey
```

```bash
ls -la /srv/quierotujersey
```

---

## 10. Base de datos `[SRV]`

```bash
cd /srv/quierotujersey/database
```

```bash
sudo -u postgres psql -v ON_ERROR_STOP=1 -d postgres -f 00_roles.sql
```

```bash
sudo -u postgres psql -v ON_ERROR_STOP=1 -d quierotujersey -f 01_base.sql
```

```bash
sudo -u postgres psql -v ON_ERROR_STOP=1 -d quierotujersey -f 02_pedidos.sql
```

```bash
sudo -u postgres psql -v ON_ERROR_STOP=1 -d quierotujersey -f 03_vistas_funciones.sql
```

Asignar la contraseña del rol de la aplicación:

```bash
sudo -u postgres psql -c "\password quierotujersey_app"
```

Verificar:

```bash
sudo -u postgres psql -d quierotujersey -c '\dt'
```

```bash
sudo -u postgres psql -d quierotujersey -c '\dv'
```

---

## 11. Aplicación, servicio systemd y NGINX `[SRV]`

### Entorno virtual y dependencias

```bash
cd /srv/quierotujersey
```

```bash
sudo python3 -m venv .venv
```

```bash
sudo .venv/bin/pip install -r requirements.txt
```

### Variables de entorno

```bash
sudo cp .env.example .env
```

```bash
sudo nano .env
```

Valores en el servidor: `DB_HOST=localhost`, `DB_PORT=5432`,
`DB_NAME=quierotujersey`, `DB_USER=quierotujersey_app`, la contraseña del
paso 10, `FLASK_DEBUG=0`, una `FLASK_SECRET_KEY` nueva y el
`ADMIN_PASSWORD_HASH`.

Generar la clave secreta:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Propietario y permisos

```bash
sudo chown -R quierotujersey:quierotujersey /srv/quierotujersey
```

```bash
sudo chmod 750 /srv/quierotujersey
```

```bash
sudo chmod 600 /srv/quierotujersey/.env
```

```bash
ls -la /srv/quierotujersey
```

### Servicio de Gunicorn

```bash
sudo cp deploy/quierotujersey.service /etc/systemd/system/
```

```bash
sudo systemctl daemon-reload
```

```bash
sudo systemctl enable --now quierotujersey
```

```bash
systemctl status quierotujersey --no-pager
```

```bash
curl -s http://127.0.0.1:8000/estado
```

### NGINX

```bash
sudo cp deploy/quierotujersey.nginx.conf /etc/nginx/sites-available/quierotujersey
```

```bash
sudo ln -s /etc/nginx/sites-available/quierotujersey /etc/nginx/sites-enabled/
```

```bash
sudo rm /etc/nginx/sites-enabled/default
```

```bash
sudo nginx -t
```

```bash
sudo systemctl reload nginx
```

```bash
sudo ufw allow 'Nginx HTTP'
```

---

## 12. Verificación final `[SRV]` y `[MAC]`

```bash
curl -s http://localhost/estado
```

```bash
systemctl is-enabled nginx postgresql quierotujersey
```

```bash
sudo ss -tlnp
```

```bash
sudo ufw status verbose
```

Desde la Mac, abrir `http://IP_DEL_SERVIDOR/` en el navegador y recorrer todas
las vistas. `[FOTO]` de cada vista.

Prueba de arranque automático:

```bash
sudo reboot
```

Al volver, sin iniciar nada a mano:

```bash
systemctl is-active nginx postgresql quierotujersey
```

```bash
curl -s http://localhost/estado
```

---

## 13. Respaldo final para el entregable `[SRV]`

```bash
cd /srv/quierotujersey
```

```bash
sudo -u postgres pg_dump --no-owner -d quierotujersey -f /tmp/respaldo_quierotujersey.sql
```

```bash
scp luis@IP_DEL_SERVIDOR:/tmp/respaldo_quierotujersey.sql ~/proyecto-final-unix/database/
```

(El último comando se ejecuta en la Mac.)

---

## Lista de evidencias para el reporte

| # | Evidencia | Sección |
|---|---|---|
| 1 | Fotos del instalador (idioma, red, particiones, perfil, SSH) | 3 |
| 2 | `systemd-detect-virt` = `none` | 4 |
| 3 | `dmidecode` con fabricante y modelo reales | 4 |
| 4 | `lscpu`, `free -h`, `lsblk -f`, `df -hT` | 4 |
| 5 | `ip -br a` y `hostnamectl` | 4 |
| 6 | `ufw status verbose` | 6 y 12 |
| 7 | `systemctl status` de postgresql, nginx y quierotujersey | 7 y 11 |
| 8 | `ls -la /srv/quierotujersey` (propietario y permisos) | 11 |
| 9 | `nginx -t` exitoso | 11 |
| 10 | `curl /estado` mostrando Linux y PostgreSQL | 12 |
| 11 | Vistas del sitio desde otro equipo de la red | 12 |
| 12 | Servicios activos después de reiniciar | 12 |
