#!/usr/bin/env bash
# =============================================================
# QuieroTuJersey - respaldo completo de la base de datos
# Uso: ./scripts/respaldo_bd.sh [nombre_bd]
# Genera database/respaldo_quierotujersey_AAAAMMDD_HHMM.sql
# =============================================================
set -euo pipefail

BD="${1:-quierotujersey}"
DESTINO="$(cd "$(dirname "$0")/.." && pwd)/database"
ARCHIVO="${DESTINO}/respaldo_${BD}_$(date +%Y%m%d_%H%M).sql"

pg_dump \
    --dbname="$BD" \
    --no-owner \
    --format=plain \
    --file="$ARCHIVO"

echo "Respaldo generado: $ARCHIVO"
ls -lh "$ARCHIVO"
