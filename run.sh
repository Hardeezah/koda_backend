#!/bin/bash
echo "🚀 Starting KodaTrade Backend..."
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
