#!/bin/bash

# Bright Smile Dental Clinic AI Agent - Local Development Script

set -e

echo "🚀 Dental Clinic AI Agent - Local Development Setup"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install it first."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys!"
fi

# Initialize database
echo "🗄️  Initializing database..."
python database/init.py

# Start server
echo ""
echo "🌐 Starting FastAPI server..."
echo "📊 Dashboard: http://localhost:8000/dashboard"
echo "🔗 API Health: http://localhost:8000/health"
echo "📞 Webhook: http://localhost:8000/incoming-call"
echo ""
echo "To run tests: python tests/test_runner.py"
echo "To run specific scenario: python tests/test_runner.py 1"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
