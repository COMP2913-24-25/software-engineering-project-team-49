#!/bin/bash

# Set environment
export FLASK_ENV=production
export FLASK_APP=app:create_app

# Try to run migrations if needed
echo "Attempting database migrations..."
flask db init || echo "Database already initialized"
echo "Running migrations..."
flask db stamp head
flask db migrate -m "Initial migration"
echo "Upgrading database..."
flask db upgrade

# Verify migration success
if [ $? -ne 0 ]; then
    echo "ERROR: Database migration failed, exiting"
    exit 1
fi

# Start the app with gunicorn
echo "Starting the application..."
gunicorn -w 2 -b 0.0.0.0:5000 --timeout 120 run:app