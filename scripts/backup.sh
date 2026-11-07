#!/usr/bin/env bash
# Non-destructive PostgreSQL backup. Never stores plaintext passwords or uploads data.
set -euo pipefail
: "${DATABASE_URL:?Set DATABASE_URL to a PostgreSQL connection string}"
case "${DATABASE_URL}" in
 postgresql+psycopg2://*) PGURL="postgresql://${DATABASE_URL#postgresql+psycopg2://}";;
 postgresql+psycopg://*) PGURL="postgresql://${DATABASE_URL#postgresql+psycopg://}";;
 postgres://*) PGURL="postgresql://${DATABASE_URL#postgres://}";;
 postgresql://*) PGURL="${DATABASE_URL}";;
 *) echo 'Only PostgreSQL backups are supported' >&2;exit 2;;
esac
OUT="${1:-backups/erp-$(date -u +%Y%m%dT%H%M%SZ).dump}"
mkdir -p "$(dirname "$OUT")"
umask 077
TEMP="$(mktemp "${OUT}.partial.XXXXXX")"
trap 'rm -f "$TEMP"' EXIT
pg_dump --format=custom --compress=6 --no-owner --no-acl --file="$TEMP" "$PGURL"
pg_restore --list "$TEMP" >/dev/null
mv -f "$TEMP" "$OUT"
trap - EXIT
chmod 600 "$OUT"
echo "Backup verified and saved to $OUT"
