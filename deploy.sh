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