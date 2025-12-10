#!/bin/bash#!/bin/bash



# COSC Casino Backend Deployment Script# COSC Casino Backend Deployment Script

# Deploys Django backend locally (non-Docker)# Deploys Django backend with PostgreSQL database using Docker



set -eset -e



# Colors# Colors

RED='\033[0;31m'RED='\033[0;31m'

GREEN='\033[0;32m'GREEN='\033[0;32m'

YELLOW='\033[1;33m'YELLOW='\033[1;33m'

BLUE='\033[0;34m'BLUE='\033[0;34m'

NC='\033[0m'NC='\033[0m'



print_message() {print_message() {

    echo -e "${1}${2}${NC}"    echo -e "${1}${2}${NC}"

}}



print_header() {print_header() {

    echo ""    echo ""

    print_message $BLUE "=============================================="    print_message $BLUE "=============================================="

    print_message $BLUE "$1"    print_message $BLUE "$1"

    print_message $BLUE "=============================================="    print_message $BLUE "=============================================="

    echo ""    echo ""

}}



# Get script directory# Get script directory (gambling-be/)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"# Root directory (final/)

ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check Pythoncd "$ROOT_DIR"

check_python() {

    print_header "Checking Python Installation"# Check Docker

    check_docker() {

    if command -v python3 &> /dev/null; then    print_header "Checking Docker Installation"

        PYTHON_CMD="python3"    

    elif command -v python &> /dev/null; then    if ! command -v docker &> /dev/null; then

        PYTHON_CMD="python"        print_message $RED "Docker is not installed. Please install Docker first."

    else        exit 1

        print_message $RED "Python is not installed. Please install Python 3.10+."    fi

        exit 1    print_message $GREEN "✓ Docker is installed"

    fi    

        if ! command -v docker compose &> /dev/null; then

    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)        print_message $RED "Docker Compose is not installed."

    print_message $GREEN "✓ Python $PYTHON_VERSION found"        exit 1

}    fi

    print_message $GREEN "✓ Docker Compose is installed"

# Setup virtual environment    

setup_venv() {    if ! docker info &> /dev/null; then

    print_header "Setting Up Virtual Environment"        print_message $RED "Docker daemon is not running. Please start Docker."

            exit 1

    if [ ! -d "venv" ]; then    fi

        print_message $YELLOW "Creating virtual environment..."    print_message $GREEN "✓ Docker daemon is running"

        $PYTHON_CMD -m venv venv}

        print_message $GREEN "✓ Virtual environment created"

    else# Setup environment

        print_message $GREEN "✓ Virtual environment exists"setup_env() {

    fi    print_header "Setting Up Environment"

        

    # Activate venv    if [ ! -f .env ]; then

    source venv/bin/activate        if [ -f .env.example ]; then

    print_message $GREEN "✓ Virtual environment activated"            print_message $YELLOW "Creating .env file from .env.example..."

                cp .env.example .env

    # Upgrade pip            print_message $GREEN "✓ .env file created"

    pip install --upgrade pip > /dev/null 2>&1            print_message $YELLOW "⚠ Please review and update .env with your settings"

}        else

            print_message $RED ".env.example not found. Please create .env manually."

# Install dependencies            exit 1

install_deps() {        fi

    print_header "Installing Dependencies"    else

            print_message $GREEN "✓ .env file exists"

    pip install -r requirements.txt    fi

    pip install gunicorn}

    print_message $GREEN "✓ Dependencies installed"

}# Build and deploy backend

deploy() {

# Setup environment    print_header "Deploying Backend"

setup_env() {    

    print_header "Setting Up Environment"    print_message $YELLOW "Building backend and database containers..."

        docker compose build db backend

    if [ ! -f ".env" ]; then    print_message $GREEN "✓ Containers built"

        cat > .env << 'EOF'    

# Database Configuration (SQLite for development)    print_message $YELLOW "Starting containers..."

DATABASE_URL=sqlite:///db.sqlite3    docker compose up -d db backend

    print_message $GREEN "✓ Containers started"

# For PostgreSQL use:    

# DATABASE_NAME=gambling_db    print_message $YELLOW "Waiting for database..."

# DATABASE_USER=gambling_user    sleep 5

# DATABASE_PASSWORD=your_password    

# DATABASE_HOST=localhost    print_message $YELLOW "Running migrations..."

# DATABASE_PORT=5432    docker compose exec -T backend python manage.py migrate --noinput

    print_message $GREEN "✓ Migrations complete"

# Django Configuration    

SECRET_KEY=change-this-to-a-random-secret-key-in-production    print_message $YELLOW "Collecting static files..."

DEBUG=True    docker compose exec -T backend python manage.py collectstatic --noinput 2>/dev/null || true

ALLOWED_HOSTS=localhost,127.0.0.1    print_message $GREEN "✓ Static files collected"

}

# CORS

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000# Create superuser

EOFcreate_superuser() {

        print_message $GREEN "✓ .env file created"    print_header "Creating Superuser"

        print_message $YELLOW "⚠ Edit .env to configure your settings"    

    else    read -p "Do you want to create a superuser? (y/n): " create_su

        print_message $GREEN "✓ .env file exists"    if [ "$create_su" = "y" ] || [ "$create_su" = "Y" ]; then

    fi        docker compose exec backend python manage.py createsuperuser

}        print_message $GREEN "✓ Superuser created"

    fi

# Run migrations}

run_migrations() {

    print_header "Running Database Migrations"# Show status

    show_status() {

    $PYTHON_CMD manage.py migrate    print_header "Backend Status"

    print_message $GREEN "✓ Migrations complete"    

}    docker compose ps db backend

    

# Create superuser    echo ""

create_superuser() {    print_message $GREEN "=============================================="

    print_header "Create Superuser"    print_message $GREEN "  Backend is running!"

        print_message $GREEN "=============================================="

    read -p "Create a superuser? (y/n): " create_su    echo ""

    if [ "$create_su" = "y" ] || [ "$create_su" = "Y" ]; then    print_message $BLUE "Backend API: http://localhost:8000/api"

        $PYTHON_CMD manage.py createsuperuser    print_message $BLUE "Admin Panel: http://localhost:8000/admin"

    fi    print_message $BLUE "Database:    localhost:5432"

}    echo ""

}

# Start development server

start_dev() {# Stop containers

    print_header "Starting Development Server"stop() {

        print_header "Stopping Backend"

    print_message $GREEN "Starting Django development server..."    docker compose stop db backend

    print_message $BLUE "Backend running at: http://localhost:8000"    print_message $GREEN "✓ Backend stopped"

    print_message $BLUE "Admin panel at: http://localhost:8000/admin"}

    print_message $YELLOW "Press Ctrl+C to stop"

    echo ""# Rebuild

    $PYTHON_CMD manage.py runserver 0.0.0.0:8000rebuild() {

}    print_header "Rebuilding Backend"

    docker compose stop backend

# Start production server    docker compose build --no-cache backend

start_prod() {    docker compose up -d backend

    print_header "Starting Production Server"    sleep 3

        docker compose exec -T backend python manage.py migrate --noinput

    print_message $GREEN "Starting Gunicorn production server..."    print_message $GREEN "✓ Backend rebuilt"

    print_message $BLUE "Backend running at: http://localhost:8000"    show_status

    print_message $YELLOW "Press Ctrl+C to stop"}

    echo ""

    gunicorn gambling_be.wsgi:application --bind 0.0.0.0:8000 --workers 4# View logs

}logs() {

    print_header "Viewing Backend Logs"

# Show status    docker compose logs -f backend db

show_status() {}

    print_header "Backend Status"

    # Database backup

    if curl -s http://localhost:8000/api/ > /dev/null 2>&1; thenbackup() {

        print_message $GREEN "✓ Backend is running at http://localhost:8000"    print_header "Backing Up Database"

    else    BACKUP_FILE="backend_backup_$(date +%Y%m%d_%H%M%S).sql"

        print_message $RED "✗ Backend is not running"    docker compose exec -T db pg_dump -U gambling_user gambling_db > "$BACKUP_FILE"

    fi    print_message $GREEN "✓ Database backed up to $BACKUP_FILE"

}}



# Show help# Run migrations

show_help() {migrate() {

    echo "COSC Casino Backend Deployment Script (Local)"    print_header "Running Migrations"

    echo ""    docker compose exec backend python manage.py makemigrations

    echo "Usage: ./deploy.sh [command]"    docker compose exec backend python manage.py migrate

    echo ""    print_message $GREEN "✓ Migrations complete"

    echo "Commands:"}

    echo "  install    Install dependencies and setup environment"

    echo "  migrate    Run database migrations"# Django shell

    echo "  dev        Start development server (port 8000)"shell() {

    echo "  prod       Start production server with Gunicorn"    print_header "Opening Django Shell"

    echo "  superuser  Create a superuser account"    docker compose exec backend python manage.py shell

    echo "  status     Check if backend is running"}

    echo "  help       Show this help message"

    echo ""# Show help

    echo "Quick Start:"show_help() {

    echo "  ./deploy.sh install    # First time setup"    echo "COSC Casino Backend Deployment Script"

    echo "  ./deploy.sh migrate    # Setup database"    echo ""

    echo "  ./deploy.sh dev        # Start server"    echo "Usage: ./deploy.sh [command]"

    echo ""    echo ""

    echo "URLs:"    echo "Commands:"

    echo "  API:    http://localhost:8000/api/"    echo "  deploy      Deploy backend and database"

    echo "  Admin:  http://localhost:8000/admin/"    echo "  start       Start containers"

}    echo "  stop        Stop containers"

    echo "  restart     Restart containers"

# Main    echo "  rebuild     Rebuild backend container"

case "${1:-help}" in    echo "  logs        View logs"

    install)    echo "  status      Show status"

        check_python    echo "  migrate     Run database migrations"

        setup_venv    echo "  shell       Open Django shell"

        install_deps    echo "  backup      Backup database"

        setup_env    echo "  help        Show this help"

        print_message $GREEN "✓ Installation complete!"    echo ""

        print_message $YELLOW "Next: ./deploy.sh migrate"}

        ;;

    migrate)# Main

        source venv/bin/activate 2>/dev/null || setup_venvcase "${1:-deploy}" in

        run_migrations    deploy)

        ;;        check_docker

    dev)        setup_env

        source venv/bin/activate 2>/dev/null || setup_venv        deploy

        start_dev        create_superuser

        ;;        show_status

    prod)        ;;

        source venv/bin/activate 2>/dev/null || setup_venv    start)

        start_prod        docker compose up -d db backend

        ;;        show_status

    superuser)        ;;

        source venv/bin/activate 2>/dev/null || setup_venv    stop)

        create_superuser        stop

        ;;        ;;

    status)    restart)

        show_status        docker compose restart db backend

        ;;        show_status

    help|--help|-h)        ;;

        show_help    rebuild)

        ;;        check_docker

    *)        rebuild

        print_message $RED "Unknown command: $1"        ;;

        show_help    logs)

        exit 1        logs

        ;;        ;;

esac    status)

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