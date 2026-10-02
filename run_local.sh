#!/bin/bash
set -e

cd "$(dirname "$0")"

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo "No .venv found. Creating one with Python 3.13..."
    /opt/homebrew/opt/python@3.13/bin/python3.13 -m venv .venv
fi

source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt -q

# Check .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Copy .env.example to .env and fill in values."
    exit 1
fi

echo "Starting local server at http://localhost:8000"
python run.py
