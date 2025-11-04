#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

# Optionally seed the database (comment out if not needed)
# echo "Seeding database..."
# python -m scripts.database_functions seed

echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

