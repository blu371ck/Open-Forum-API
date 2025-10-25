#!/bin/bash

set -e

echo "Waiting for PostgreSQL to start..."
while ! pg_isready -h db -p 5432 -U $POSTGRES_USER > /dev/null 2>&1; do
    sleep 1
done
echo "PostgreSQL started."

echo "Seeding database..."

python -m app.seed

echo "Starting API server..."
exec "$@"