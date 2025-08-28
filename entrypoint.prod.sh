#!/bin/sh

# Production entrypoint script for Django with ASGI

set -e  # Exit on any error

echo "Starting Django production entrypoint..."

# Health check for database using DATABASE_URL
if [ -n "$DB_URL" ]; then
  echo "Checking database connection..."
  
  # Try to connect to the database using Django's database check
  python manage.py shell << EOF
import sys
from django.db import connection
from django.db.utils import OperationalError  


try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        print('Database connection successful!')
except OperationalError as e:
    print(f'Database connection failed: {e}')
    sys.exit(1)
EOF
  
  if [ $? -ne 0 ]; then
    echo "Waiting for database to be ready..."
    while true; do
      python manage.py shell << EOF
import sys
from django.db import connection
from django.db.utils import OperationalError 

try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        print('Database is ready!')
        sys.exit(0)
except OperationalError:
    sys.exit(1)
EOF
      if [ $? -eq 0 ]; then
        break
      fi
      echo "Database not ready, retrying in 2 seconds..."
      sleep 2
    done
  fi
fi

# Run database migrations
echo "Applying database migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput


# Start Gunicorn with Uvicorn workers for ASGI
echo "Starting uvicorn server with ASGI..."
exec uvicorn travelers.asgi:application --host 0.0.0.0 --port 8000
