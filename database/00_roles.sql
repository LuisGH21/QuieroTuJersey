-- =============================================================
-- QuieroTuJersey - 00_roles.sql
-- Crea el rol de la aplicacion y la base de datos del proyecto.
-- Ejecutar como superusuario de PostgreSQL (postgres).
-- La contrasena NO se guarda aqui: se asigna despues con \password.
-- =============================================================

CREATE ROLE quierotujersey_app
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE;

CREATE DATABASE quierotujersey
    WITH ENCODING 'UTF8'
    TEMPLATE template0;

-- Solo el rol de la aplicacion (y el duenio) pueden conectarse
REVOKE CONNECT ON DATABASE quierotujersey FROM PUBLIC;
GRANT CONNECT ON DATABASE quierotujersey TO quierotujersey_app;
