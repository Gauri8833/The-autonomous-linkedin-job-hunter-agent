#!/bin/bash
echo "========================================"
echo "LinkedIn Job Hunter Agent"
echo "========================================"
echo ""

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Installing Chromium browser..."
python -m playwright install chromium

echo ""
echo "Starting backend server..."
echo "The agent will be available at http://localhost:8000"
echo ""

python backend.py