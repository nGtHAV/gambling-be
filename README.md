# COSC Casino - Backend

A Django REST Framework backend for the COSC Casino educational gambling platform.

## Tech Stack

- **Django 6.0** - Web framework
- **Django REST Framework** - API toolkit
- **PostgreSQL** - Database
- **JWT** - Authentication

## Quick Start

```bash
# Install dependencies
./deploy.sh install

# Setup PostgreSQL database
./deploy.sh setup-db

# Run migrations
./deploy.sh migrate

# Create admin user
./deploy.sh superuser

# Start development server
./deploy.sh dev
```

Backend runs at: **http://localhost:8000**

## Available Commands

| Command | Description |
|---------|-------------|
| `./deploy.sh install` | Install dependencies and setup |
| `./deploy.sh setup-db` | Create PostgreSQL database and user |
| `./deploy.sh migrate` | Run database migrations |
| `./deploy.sh dev` | Start development server |
| `./deploy.sh prod` | Start production server (Gunicorn) |
| `./deploy.sh superuser` | Create admin account |
| `./deploy.sh status` | Check server status |

## Manual Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Setup PostgreSQL database (as postgres user)
sudo -u postgres psql -c "CREATE USER gambling_user WITH PASSWORD 'gambling_password';"
sudo -u postgres psql -c "CREATE DATABASE gambling_db OWNER gambling_user;"

# Django commands
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000

# Production
gunicorn gambling_be.wsgi:application --bind 0.0.0.0:8000
```

## Project Structure

```
gambling_be/
├── deploy.sh              # Deployment script
├── manage.py              # Django CLI
├── requirements.txt       # Python dependencies
├── gambling_be/           # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── games/                 # Games application
    ├── models.py          # Database models
    ├── views.py           # API views
    ├── urls.py            # URL routing
    ├── serializers.py     # DRF serializers
    ├── game_logic.py      # Game algorithms
    └── admin.py           # Admin configuration
```

## Environment Variables

Create `.env`:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL Database
DATABASE_NAME=gambling_db
DATABASE_USER=gambling_user
DATABASE_PASSWORD=gambling_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

## API Endpoints

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register/` | POST | Register new user |
| `/api/auth/login/` | POST | Login (returns JWT) |
| `/api/auth/logout/` | POST | Logout |
| `/api/auth/me/` | GET | Get current user |

### Games

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/games/blackjack/` | POST | Play blackjack |
| `/api/games/poker/` | POST | Play poker |
| `/api/games/roulette/` | POST | Play roulette |
| `/api/games/dice/` | POST | Play dice |
| `/api/games/minesweeper/` | POST | Play minesweeper |
| `/api/games/history/` | GET | Get game history |

### Coins

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/coins/request/` | POST | Request more coins |
| `/api/admin/coin-requests/` | GET | List all requests (admin) |
| `/api/admin/coin-requests/<id>/approve/` | POST | Approve request |
| `/api/admin/coin-requests/<id>/reject/` | POST | Reject request |

## Database Models

### UserProfile
- `user` - OneToOne to Django User
- `coins` - Integer (default: 1000)
- `total_wagered` - Integer
- `total_won` - Integer

### GameHistory
- `user` - ForeignKey to User
- `game_type` - CharField
- `bet_amount` - Integer
- `result` - CharField
- `payout` - Integer
- `timestamp` - DateTime

### CoinRequest
- `user` - ForeignKey to User
- `amount` - Integer
- `reason` - TextField
- `status` - CharField (pending/approved/rejected)
- `created_at` - DateTime

## Game Logic

Each game has a built-in house edge (5-10%):

| Game | House Edge |
|------|------------|
| Blackjack | 7% |
| Poker | 8% |
| Roulette | 11% |
| Dice | 7% |
| Minesweeper | 8% |

## Admin Panel

Access at: **http://localhost:8000/admin**

Features:
- Manage users and profiles
- View game history
- Approve/reject coin requests
- Monitor statistics

## License

Educational use only.
