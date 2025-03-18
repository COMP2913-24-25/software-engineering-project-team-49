#!/bin/bash

# Set environment
export FLASK_ENV=production
export FLASK_APP=run.py  # Ensure the correct entry point

# Run migrations (only if needed)
echo "Running migrations..."
flask db migrate -m "Auto migration" || true
flask db upgrade || true

# Start the app
echo "Starting the application..."
gunicorn -w 2 -b 0.0.0.0:5000 --timeout 120 run:app
