#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL is up"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is up"

# Wait for Elasticsearch to be ready
echo "Waiting for Elasticsearch..."
while ! curl -s http://elasticsearch:9200 > /dev/null; do
  sleep 1
done
echo "Elasticsearch is up"

# Run database migrations
echo "Running database migrations..."
cd /app
alembic upgrade head

echo "Starting application..."
exec "$@"
