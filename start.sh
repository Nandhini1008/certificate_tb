#!/bin/bash
# Startup script for Render deployment

echo "Starting Certificate TB Backend..."

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "Error: backend/main.py not found"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
cd backend
pip install -r requirements.txt

# Start the application
echo "Starting FastAPI application..."
python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
