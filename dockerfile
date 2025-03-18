# Use an official Python runtime
FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy the application files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask app port
EXPOSE 5000

# Command to run the application using gunicorn
CMD ["sh", "-c", "flask db upgrade && gunicorn -w 2 -b 0.0.0.0:5000 run:app"]
