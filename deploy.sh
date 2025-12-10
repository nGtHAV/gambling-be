#!/bin/bash

# COSC Casino Backend Deployment Script
# Deploys Django backend with PostgreSQL database

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
    
    cd gambling_be
    pip install -r requirements.txt
    pip install gunicorn
    print_message $GREEN "✓ Dependencies installed"
}

# Setup environment
setup_env() {
    print_header "Setting Up Environment"
    
    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=sqlite:///db.sqlite3
# For PostgreSQL use:
# DATABASE_URL=postgres://gambling_user:your_password@localhost:5432/gambling_db

# Django Configuration
SECRET_KEY=change-this-to-a-random-secret-key-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
        print_message $GREEN "✓ .env file created"
        print_message $YELLOW "⚠ Edit .env to configure your settings"
    else
        print_message $GREEN "✓ .env file exists"
    fi
}

# Run migrations
run_migrations() {
    print_header "Running Database Migrations"
    
    cd gambling_be
    $PYTHON_CMD manage.py migrate
    print_message $GREEN "✓ Migrations complete"
}

# Create superuser
create_superuser() {
    print_header "Create Superuser"
    
    read -p "Create a superuser? (y/n): " create_su
    if [ "$create_su" = "y" ] || [ "$create_su" = "Y" ]; then
        cd gambling_be
        $PYTHON_CMD manage.py createsuperuser
    fi
}

# Start development server
start_dev() {
    print_header "Starting Development Server"
    
    cd gambling_be
    print_message $GREEN "Starting Django development server..."
    print_message $BLUE "Backend running at: http://localhost:8000"
    print_message $BLUE "Admin panel at: http://localhost:8000/admin"
    print_message $YELLOW "Press Ctrl+C to stop"
    echo ""
    $PYTHON_CMD manage.py runserver 0.0.0.0:8000
}

# Start production server
start_prod() {
    print_header "Starting Production Server"
    
    cd gambling_be
    print_message $GREEN "Starting Gunicorn production server..."
    print_message $BLUE "Backend running at: http://localhost:8000"
    print_message $YELLOW "Press Ctrl+C to stop"
    echo ""
    gunicorn gambling_be.wsgi:application --bind 0.0.0.0:8000 --workers 4
}

# Show status
show_status() {
    print_header "Backend Status"
    
    if curl -s http://localhost:8000/api/ > /dev/null 2>&1; then
        print_message $GREEN "✓ Backend is running at http://localhost:8000"
    else
        print_message $RED "✗ Backend is not running"
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
    echo "  dev        Start development server (port 8000)"
    echo "  prod       Start production server with Gunicorn"
    echo "  superuser  Create a superuser account"
    echo "  status     Check if backend is running"
    echo "  help       Show this help message"
    echo ""
    echo "Quick Start:"
    echo "  ./deploy.sh install    # First time setup"
    echo "  ./deploy.sh migrate    # Setup database"
    echo "  ./deploy.sh dev        # Start server"
    echo ""
    echo "URLs:"
    echo "  API:    http://localhost:8000/api/"
    echo "  Admin:  http://localhost:8000/admin/"
}

# Main
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
        source venv/bin/activate 2>/dev/null || setup_venv
        run_migrations
        ;;
    dev)
        source venv/bin/activate 2>/dev/null || setup_venv
        start_dev
        ;;
    prod)
        source venv/bin/activate 2>/dev/null || setup_venv
        start_prod
        ;;
    superuser)
        source venv/bin/activate 2>/dev/null || setup_venv
        create_superuser
        ;;
    status)
        show_status
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
