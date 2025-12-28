# Deploying JobPulse to Railway

This guide covers how to deploy the project to Railway.app. We have configured the backend to serve static files using WhiteNoise, so you don't need a separate Nginx service for the simplest deployment.

## Prerequisites
- GitHub Account (with this repo pushed)
- Railway Account (https://railway.app)

## Deployment Steps

### 1. Database & Redis
1.  Create a **New Project** on Railway.
2.  Add a **PostgreSQL** service.
3.  Add a **Redis** service.

### 2. Backend Service
1.  In the same project, add a **New Service** from **GitHub Repo**.
2.  Select your `jobpulse` repository.
3.  **Variables**: Add the following Environment Variables:
    *   `SECRET_KEY`: (Generate a strong random string)
    *   `DEBUG`: `False`
    *   `DATABASE_URL`: (Use the internal connection string from the Postgres service)
    *   `CELERY_BROKER_URL`: (Use the internal connection string from the Redis service)
    *   `CELERY_RESULT_BACKEND`: (Same as above)
    *   `Allowed Hosts`: `*` (or your railway domain)
    *   `CSRF_TRUSTED_ORIGINS`: `https://your-project.up.railway.app`
    *   `GEMINI_API_KEY`: (Your Google API Key)
    *   `API_ID`, `API_HASH`, `BOT_TOKEN`: (Your Telegram credentials)
    *   `PORT`: `8000` (Optional, Railway usually detects it, but setting it explicitly helps)

4.  **Build Settings**:
    *   Railway should auto-detect the `backend/Dockerfile`. If not, configure the **Root Directory** to `backend`.
    *   **Start Command**: `gunicorn --bind 0.0.0.0:$PORT core.wsgi:application`
        *   (If `$PORT` is not substituted correctly in your trial, use `0.0.0.0:8000` and set `PORT` env var to `8000`).

### 3. Worker Service (Optional but Recommended)
To run Celery background tasks:
1.  Add another service from the **Same GitHub Repo**.
2.  **Variables**: Copy the same variables as the Backend.
3.  **Start Command**: `celery -A core worker -l info`
4.  **Root Directory**: `backend`

### 4. Bot Service
1.  Add another service from the **Same GitHub Repo**.
2.  **Variables**: Needs Redis, Backend URL, and Telegram creds.
3.  **Root Directory**: `bot`
4.  **Start Command**: `python main.py`

## Notes
- **Static Files**: Configuring `WhiteNoise` (which we just did) ensures CSS/JS load correctly without Nginx.
- **Cost**: Running 3 separate services (Web, Worker, Bot) + DB + Redis might exceed free/trial limits.
    *   *Money Saving Tip*: You can run the bot and worker inside the web container using a supervisor script, but that's advanced. For now, start with just the Web service to verify.
