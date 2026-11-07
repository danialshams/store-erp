#!/usr/bin/env bash
# Safe restore drill: only to a separate, existing EMPTY PostgreSQL database.
set -euo pipefail
: "${DATABASE_URL:?Original DATABASE_URL is required for source safety check}"
: "${RESTORE_DATABASE_URL:?Set RESTORE_DATABASE_URL for an isolated empty target}"
SOURCE="${DATABASE_URL/postgresql+psycopg2:/postgresql:}"
SOURCE="${SOURCE/postgresql+psycopg:/postgresql:}"
TARGET="${RESTORE_DATABASE_URL/postgresql+psycopg2:/postgresql:}"
TARGET="${TARGET/postgresql+psycopg:/postgresql:}"
if [[ "$SOURCE" == "$TARGET" ]];then echo "Refusing restore into current production/source database" >&2;exit 2;fi
FILE="${1:?Provide .dump backup file path}"
[[ -f "$FILE" ]] || { echo "Backup file not found" >&2; exit 2;}
pg_restore --list "$FILE" >/dev/null
COUNT="$(psql "$TARGET" -Atq -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")"
[[ "$COUNT" == 0 ]] || { echo "Target database is not empty; restore aborted" >&2;exit 2;}
pg_restore --single-transaction --exit-on-error --no-owner --no-acl --dbname="$TARGET" "$FILE"
RESTORED="$(psql "$TARGET" -Atq -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")"
[[ "$RESTORED" -ge 35 ]] || { echo "Restore failed verification" >&2;exit 1;}
echo "Restore successful into isolated target: $RESTORED business and infrastructure tables"
