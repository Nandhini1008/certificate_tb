#!/bin/bash

# Start script for Render deployment
echo "Starting Certificate TB Backend..."

# Change to backend directory
cd backend

# Install dependencies if needed
pip install -r requirements.txt

# Start the application
PORT=${PORT:-8000}
echo "Starting FastAPI server on port $PORT..."
python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1