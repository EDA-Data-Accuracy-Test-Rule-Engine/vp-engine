#!/bin/bash

# VP Data Accuracy Test Rule Engine - Setup Script
# This script sets up the complete environment for the VP Engine

set -e

echo "🚀 Setting up VP Data Accuracy Test Rule Engine..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
print_status "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python 3.8 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION found"

# Create virtual environment
print_status "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt

# Install package in development mode
print_status "Installing VP Engine in development mode..."
pip install -e .

# Create necessary directories
print_status "Creating directory structure..."
mkdir -p data outputs templates config logs

# Copy environment template
print_status "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_success "Environment template copied to .env"
    print_warning "Please edit .env file with your configuration"
else
    print_warning ".env file already exists"
fi

# Create demo data
print_status "Creating demo data..."
python scripts/create_demo_data.py

# Test installation
print_status "Testing installation..."
if vp-engine --version &> /dev/null; then
    print_success "VP Engine CLI installed successfully"
else
    print_error "CLI installation failed"
    exit 1
fi

# Create basic test
print_status "Running basic functionality test..."
python -c "
import sys
sys.path.insert(0, 'src')
try:
    from src.models.validation import DataSourceType, ValidationRule, RuleType
    from src.database.connectors import DatabaseManager
    from src.core.validation_engine import ValidationEngine
    print('✅ All core modules import successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

# Display success message
echo ""
echo "🎉 VP Data Accuracy Test Rule Engine setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Configure .env file with your database and API keys"
echo "3. Start the interactive workflow: vp-engine start"
echo ""
echo "🎪 Quick demo:"
echo "   vp-engine start"
echo "   → Choose '3. CSV File'"
echo "   → Enter path: data/sample_employees.csv"
echo "   → Try AI suggestions or existing rules"
echo ""
echo "📖 Documentation: README.md"
echo "🔧 Sample rules: templates/sample_employee_rules.json"
echo "📊 Demo data: data/sample_employees.csv"
echo ""
print_success "Setup complete! Happy data validating! 🚀"