FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directories
RUN mkdir -p storage/templates storage/certificates storage/qr storage/fonts

# Expose port (use environment variable)
EXPOSE ${PORT:-8000}

# Run the application (port from environment variable)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
