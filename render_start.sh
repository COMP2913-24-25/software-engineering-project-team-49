#!/bin/bash

# Set environment
export FLASK_ENV=production

# Try to run migrations if needed
echo "Attempting database migrations..."
flask db stamp head || echo "Failed to stamp head, continuing..."
flask db migrate || echo "Failed to migrate, continuing..."
flask db upgrade || echo "Failed to upgrade, continuing..."

# Start the app with gunicorn
echo "Starting the application..."
gunicorn -w 2 -b 0.0.0.0:5000 --timeout 120 run:app