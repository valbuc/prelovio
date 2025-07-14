# Use Python 3.11 slim image with explicit platform
FROM --platform=linux/amd64 python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies in a single layer
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy all project files
COPY . .

# Install poetry first
RUN pip install --no-cache-dir poetry

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry lock
RUN poetry install --only main --no-interaction --no-ansi

# Pre-download the model during build time
RUN python -c "from transformers import pipeline; pipeline('image-segmentation', model='briaai/RMBG-1.4', trust_remote_code=True)"

# Create necessary directories
RUN mkdir -p prelovium/webapp/temp/uploads

# Set environment variables
ENV PORT=8080
ENV FLASK_APP=prelovium.webapp.app:app
ENV FLASK_ENV=production
ENV GOOGLE_CLOUD_PROJECT=prelovium

# Expose the port
EXPOSE 8080

# Run the application with proper binding
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 prelovium.webapp.app:app"] 