#!/bin/bash
# Script d'attente de la disponibilité de PostgreSQL

echo "Attente de PostgreSQL sur $POSTGRES_HOST:$POSTGRES_PORT..."
until nc -z -v -w30 "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  echo "PostgreSQL non disponible, nouvelle tentative..."
  sleep 30
done

echo "PostgreSQL disponible"
exec "$@"
