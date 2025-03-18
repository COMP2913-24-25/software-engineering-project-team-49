#!/bin/bash

# Set environment
export FLASK_ENV=production
export FLASK_APP=app:create_app  # Critical for migrations

# Run migrations (force stamping to avoid issues)
echo "Running migrations..."
flask db init --directory=migrations  # Ensure correct directory
flask db stamp head
flask db migrate -m "Render migration"
flask db upgrade

# Start the app
echo "Starting the application..."
gunicorn -w 2 -b 0.0.0.0:5000 --timeout 120 run:app