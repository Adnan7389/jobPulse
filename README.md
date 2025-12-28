# JobPulse

JobPulse is an intelligent job aggregation and notification system that scrapes job postings from Telegram channels, processes them using AI to extract structured metadata, and delivers personalized alerts to users.

## Architecture

- **Backend**: Django (DRF) + Celery + Redis
- **Database**: PostgreSQL
- **Scraper**: Telethon (Python)
- **Bot**: Aiogram (Python)
- **Deployment**: Docker Compose + Nginx + Gunicorn

## Setup & Deployment

### Prerequisites
- Docker & Docker Compose
- Telegram API Credentials (`API_ID`, `API_HASH`, `BOT_TOKEN`)
- Google Gemini API Key

### Configuration
1.  Copy `.env.example` to `.env` (or create `.env`):
    ```bash
    # Core
    SECRET_KEY=your_secret_key
    DEBUG=False
    
    # DB
    DATABASE_URL=postgres://postgres:postgres@db:5432/jobpulse
    
    # AI
    GEMINI_API_KEY=your_key
    
    # Telegram
    API_ID=12345
    API_HASH=abcdef
    BOT_TOKEN=123:ABC
    ```

### Running in Production
The project is configured to run with Nginx and Gunicorn out of the box.

1.  Build and start services:
    ```bash
    docker compose up -d --build
    ```

2.  Access the endpoints:
    - **API**: `http://localhost:8002/api/`
    - **Admin**: `http://localhost:8002/admin/`

3.  Verify status:
    ```bash
    curl http://localhost:8002/api/health/
    ```

## Development
For local development, you can map ports differently in `docker-compose.yml` or run services individually. 
The current `docker-compose.yml` maps Nginx to port `8002` to avoid conflicts.
