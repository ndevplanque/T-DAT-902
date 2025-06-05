#!/bin/bash
echo "En attente de PostgreSQL à $POSTGRES_HOST:$POSTGRES_PORT..."
until nc -z -v -w30 "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  echo "PostgreSQL non disponible encore..."
  sleep 30
done

echo "PostgreSQL prêt !"
exec "$@"
