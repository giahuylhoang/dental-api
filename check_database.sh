#!/bin/bash
# Quick database connection test script

echo "🔍 Checking database connection..."
echo ""

# Check if we're in the right directory
if [ ! -f "database/connection.py" ]; then
    echo "❌ Error: Please run this script from the dental-api directory"
    exit 1
fi

# Check Python environment
echo "📦 Python environment:"
which python3
python3 --version
echo ""

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if python3 -c "import psycopg2" 2>/dev/null; then
    echo "   ✅ psycopg2-binary installed"
else
    echo "   ❌ psycopg2-binary NOT installed"
    echo ""
    echo "   Install with:"
    echo "   pip install psycopg2-binary"
    echo "   # or"
    echo "   pip install -r requirements.txt"
    exit 1
fi

if python3 -c "import sqlalchemy" 2>/dev/null; then
    echo "   ✅ sqlalchemy installed"
else
    echo "   ❌ sqlalchemy NOT installed"
    exit 1
fi

echo ""
echo "🔍 Running database tests..."
python3 test_database.py
