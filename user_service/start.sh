#!/bin/bash

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! nc -z postgres-compose 5432; do
  sleep 0.1
done
echo "PostgreSQL is ready!"

# Initialize the database
python -c "from database import create_db_tables; create_db_tables()"

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port 8001
