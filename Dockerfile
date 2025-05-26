# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy all project files
COPY . .

# Install poetry
RUN pip install poetry

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install

# Create necessary directories
RUN mkdir -p prelovium/webapp/temp/uploads

# Set environment variables
ENV PORT=8080
ENV FLASK_APP=prelovium.webapp.app:app
ENV FLASK_ENV=production
ENV GOOGLE_CLOUD_PROJECT=prelovium

# Expose the port
EXPOSE 8080

# Run the application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 prelovium.webapp.app:app 