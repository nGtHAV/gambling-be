#!/bin/bash

# COSC Casino Backend Deployment Script
# Deploys Django backend locally

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    echo -e "${1}${2}${NC}"
}

print_header() {
    echo ""
    print_message $BLUE "=============================================="
    print_message $BLUE "$1"
    print_message $BLUE "=============================================="
    echo ""
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
check_python() {
    print_header "Checking Python Installation"
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_message $RED "Python is not installed. Please install Python 3.10+."
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_message $GREEN "✓ Python $PYTHON_VERSION found"
}

# Setup virtual environment
setup_venv() {
    print_header "Setting Up Virtual Environment"
    
    if [ ! -d "venv" ]; then
        print_message $YELLOW "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
        print_message $GREEN "✓ Virtual environment created"
    else
        print_message $GREEN "✓ Virtual environment exists"
    fi
    
    # Activate venv
    source venv/bin/activate
    print_message $GREEN "✓ Virtual environment activated"
    
    # Upgrade pip
    pip install --upgrade pip > /dev/null 2>&1
}

# Install dependencies
install_deps() {
    print_header "Installing Dependencies"
    
    pip install -r requirements.txt
    pip install gunicorn
    print_message $GREEN "✓ Dependencies installed"
}

# Setup environment file
setup_env() {
    print_header "Setting Up Environment"
    
    if [ ! -f ".env" ]; then
        print_message $YELLOW "Creating default .env file..."
        cat > .env << 'EOF'
# Django Configuration
SECRET_KEY=change-this-in-production-use-a-long-random-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000
EOF
        print_message $GREEN "✓ Default .env file created"
        print_message $YELLOW "⚠ Update SECRET_KEY for production!"
    else
        print_message $GREEN "✓ .env file exists"
    fi
}

# Run migrations
migrate() {
    print_header "Running Migrations"
    
    source venv/bin/activate
    python manage.py migrate
    print_message $GREEN "✓ Migrations complete"
}

# Create superuser
create_superuser() {
    print_header "Creating Superuser"
    
    source venv/bin/activate
    python manage.py createsuperuser
}

# Start development server
dev() {
    print_header "Starting Development Server"
    
    source venv/bin/activate
    print_message $GREEN "Backend running at: http://localhost:8000"
    print_message $GREEN "Admin panel at: http://localhost:8000/admin"
    python manage.py runserver 0.0.0.0:8000
}

# Start production server
prod() {
    print_header "Starting Production Server"
    
    source venv/bin/activate
    print_message $GREEN "Backend running at: http://localhost:8000"
    gunicorn gambling_be.wsgi:application --bind 0.0.0.0:8000 --workers 3
}

# Show status
status() {
    print_header "Backend Status"
    
    if lsof -i :8000 > /dev/null 2>&1; then
        print_message $GREEN "✓ Backend is running on port 8000"
        lsof -i :8000
    else
        print_message $YELLOW "Backend is not running"
    fi
}

# Show help
show_help() {
    echo "COSC Casino Backend Deployment Script"
    echo ""
    echo "Usage: ./deploy.sh [command]"
    echo ""
    echo "Commands:"
    echo "  install    Install dependencies and setup environment"
    echo "  migrate    Run database migrations"
    echo "  dev        Start development server"
    echo "  prod       Start production server (Gunicorn)"
    echo "  superuser  Create admin account"
    echo "  status     Check server status"
    echo "  help       Show this help message"
    echo ""
    echo "Quick Start:"
    echo "  ./deploy.sh install"
    echo "  ./deploy.sh migrate"
    echo "  ./deploy.sh superuser"
    echo "  ./deploy.sh dev"
}

# Main script
case "${1:-help}" in
    install)
        check_python
        setup_venv
        install_deps
        setup_env
        print_message $GREEN "✓ Installation complete!"
        print_message $YELLOW "Next: ./deploy.sh migrate"
        ;;
    migrate)
        migrate
        ;;
    dev)
        dev
        ;;
    prod)
        prod
        ;;
    superuser)
        create_superuser
        ;;
    status)
        status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_message $RED "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
