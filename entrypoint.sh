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

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')"

# Collect static files (for production)
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# Start the server
echo "Starting server..."
exec "$@"
