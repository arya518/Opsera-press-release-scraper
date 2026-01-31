#!/bin/bash
# Quick run script for the Opsera Press Release Scraper

echo "======================================"
echo "Opsera Press Release Scraper"
echo "======================================"
echo ""

# Check if credentials.json exists
if [ ! -f "credentials.json" ]; then
    echo "ERROR: credentials.json not found!"
    echo "Please follow setup instructions in README.md"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing/updating dependencies..."
pip install -q -r requirements.txt

# Run the scraper
echo ""
echo "Running scraper..."
python scraper.py

# Deactivate virtual environment
deactivate

echo ""
echo "Done!"
