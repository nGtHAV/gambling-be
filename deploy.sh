#!/bin/bash

# COSC Casino Backend Deployment Script
# Deploys Django backend with PostgreSQL database using Docker

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

# Get script directory (gambling-be/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Root directory (final/)
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Check Docker
check_docker() {
    print_header "Checking Docker Installation"
    
    if ! command -v docker &> /dev/null; then
        print_message $RED "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_message $GREEN "✓ Docker is installed"
    
    if ! command -v docker compose &> /dev/null; then
        print_message $RED "Docker Compose is not installed."
        exit 1
    fi
    print_message $GREEN "✓ Docker Compose is installed"
    
    if ! docker info &> /dev/null; then
        print_message $RED "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    print_message $GREEN "✓ Docker daemon is running"
}

# Setup environment
setup_env() {
    print_header "Setting Up Environment"
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            print_message $YELLOW "Creating .env file from .env.example..."
            cp .env.example .env
            print_message $GREEN "✓ .env file created"
            print_message $YELLOW "⚠ Please review and update .env with your settings"
        else
            print_message $RED ".env.example not found. Please create .env manually."
            exit 1
        fi
    else
        print_message $GREEN "✓ .env file exists"
    fi
}

# Build and deploy backend
deploy() {
    print_header "Deploying Backend"
    
    print_message $YELLOW "Building backend and database containers..."
    docker compose build db backend
    print_message $GREEN "✓ Containers built"
    
    print_message $YELLOW "Starting containers..."
    docker compose up -d db backend
    print_message $GREEN "✓ Containers started"
    
    print_message $YELLOW "Waiting for database..."
    sleep 5
    
    print_message $YELLOW "Running migrations..."
    docker compose exec -T backend python manage.py migrate --noinput
    print_message $GREEN "✓ Migrations complete"
    
    print_message $YELLOW "Collecting static files..."
    docker compose exec -T backend python manage.py collectstatic --noinput 2>/dev/null || true
    print_message $GREEN "✓ Static files collected"
}

# Create superuser
create_superuser() {
    print_header "Creating Superuser"
    
    read -p "Do you want to create a superuser? (y/n): " create_su
    if [ "$create_su" = "y" ] || [ "$create_su" = "Y" ]; then
        docker compose exec backend python manage.py createsuperuser
        print_message $GREEN "✓ Superuser created"
    fi
}

# Show status
show_status() {
    print_header "Backend Status"
    
    docker compose ps db backend
    
    echo ""
    print_message $GREEN "=============================================="
    print_message $GREEN "  Backend is running!"
    print_message $GREEN "=============================================="
    echo ""
    print_message $BLUE "Backend API: http://localhost:8000/api"
    print_message $BLUE "Admin Panel: http://localhost:8000/admin"
    print_message $BLUE "Database:    localhost:5432"
    echo ""
}

# Stop containers
stop() {
    print_header "Stopping Backend"
    docker compose stop db backend
    print_message $GREEN "✓ Backend stopped"
}

# Rebuild
rebuild() {
    print_header "Rebuilding Backend"
    docker compose stop backend
    docker compose build --no-cache backend
    docker compose up -d backend
    sleep 3
    docker compose exec -T backend python manage.py migrate --noinput
    print_message $GREEN "✓ Backend rebuilt"
    show_status
}

# View logs
logs() {
    print_header "Viewing Backend Logs"
    docker compose logs -f backend db
}

# Database backup
backup() {
    print_header "Backing Up Database"
    BACKUP_FILE="backend_backup_$(date +%Y%m%d_%H%M%S).sql"
    docker compose exec -T db pg_dump -U gambling_user gambling_db > "$BACKUP_FILE"
    print_message $GREEN "✓ Database backed up to $BACKUP_FILE"
}

# Run migrations
migrate() {
    print_header "Running Migrations"
    docker compose exec backend python manage.py makemigrations
    docker compose exec backend python manage.py migrate
    print_message $GREEN "✓ Migrations complete"
}

# Django shell
shell() {
    print_header "Opening Django Shell"
    docker compose exec backend python manage.py shell
}

# Show help
show_help() {
    echo "COSC Casino Backend Deployment Script"
    echo ""
    echo "Usage: ./deploy.sh [command]"
    echo ""
    echo "Commands:"
    echo "  deploy      Deploy backend and database"
    echo "  start       Start containers"
    echo "  stop        Stop containers"
    echo "  restart     Restart containers"
    echo "  rebuild     Rebuild backend container"
    echo "  logs        View logs"
    echo "  status      Show status"
    echo "  migrate     Run database migrations"
    echo "  shell       Open Django shell"
    echo "  backup      Backup database"
    echo "  help        Show this help"
    echo ""
}

# Main
case "${1:-deploy}" in
    deploy)
        check_docker
        setup_env
        deploy
        create_superuser
        show_status
        ;;
    start)
        docker compose up -d db backend
        show_status
        ;;
    stop)
        stop
        ;;
    restart)
        docker compose restart db backend
        show_status
        ;;
    rebuild)
        check_docker
        rebuild
        ;;
    logs)
        logs
        ;;
    status)
        show_status
        ;;
    migrate)
        migrate
        ;;
    shell)
        shell
        ;;
    backup)
        backup
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
