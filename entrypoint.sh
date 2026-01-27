#!/bin/bash

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Ingest data from Excel files
echo "Ingesting data from Excel files..."
python manage.py ingest_data --sync

# Collect static files (for production)
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# Start the server
echo "Starting server..."
exec "$@"
