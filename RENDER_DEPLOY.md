# Deploying JobPulse to Render

Render is another great option, but it has one catch: **Redis is not free** on Render. You will need to use an external free Redis provider.

## Prerequisites
1.  **Render Account**: [https://render.com](https://render.com)
2.  **Upstash Account** (For Free Redis): [https://upstash.com](https://upstash.com)
3.  **GitHub Repo**: Pushed and ready.

## Step 1: External Redis (Upstash)
1.  Go to **Upstash Console** and create a new **Redis** database.
2.  Copy the connection string (starting with `redis://...`).
3.  You will use this as your `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`.

## Step 2: Render Configuration

### Option A: Manual Setup (Recommended for showcase)

#### 1. Database (PostgreSQL)
1.  Click **New +** -> **PostgreSQL**.
2.  Name: `jobpulse-db`.
3.  Plan: **Free**.
4.  Copy the `Internal Database URL` once created.

#### 2. Web Service (Backend)
1.  Click **New +** -> **Web Service**.
2.  Connect your GitHub repo.
3.  **Settings**:
    *   **Runtime**: Python 3
    *   **Build Command**: `pip install -r backend/requirements.txt`
    *   **Start Command**: `gunicorn --chdir backend --bind 0.0.0.0:$PORT core.wsgi:application`
        *   *Note*: The `--chdir backend` is important if your root is the repo root.
    *   **Plan**: Free.
4.  **Environment Variables**:
    *   `PYTHON_VERSION`: `3.11.0`
    *   `SECRET_KEY`, `DEBUG` (False), `GEMINI_API_KEY`...
    *   `DATABASE_URL`: (Paste from Step 2.1)
    *   `CELERY_BROKER_URL`: (Paste from Upstash)
    *   `CELERY_RESULT_BACKEND`: (Paste from Upstash)
    *   `CSRF_TRUSTED_ORIGINS`: `https://your-service-name.onrender.com`

#### 4. Bot Service (Web Service)
*The bot has an internal API, so it can run as a Web Service on the Free Tier.*
1.  Click **New +** -> **Web Service**.
2.  **Start Command**: `python main.py`
3.  **Root Directory**: `bot`
4.  **Environment Variables**:
    *   `BOT_TOKEN`, `API_ID`, `API_HASH`
    *   `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` (if using Upstash)
    *   `BACKEND_URL`: `https://your-backend-service.onrender.com`
5.  **Health Check Path**: `/` (or let it detect port 8080).

## Notes
*   **Spin Down**: Render Free Web Services spin down after 15 minutes of inactivity. This means the Bot might stop polling if no one hits the API.
    *   *Workaround*: Use a free uptime monitor (like UptimeRobot) to ping `https://your-bot-service.onrender.com` every 10 minutes to keep it awake.


### Option C: Monolith (All-in-One)
*Best for saving money. Runs Web, Worker, Bot, and Scraper in ONE service.*

1.  **Rename/Move**: Rename `Dockerfile.monolith` to `Dockerfile` in the root (or specific path setting).
2.  **Settings**:
    *   **Root Directory**: `.` (Root of repo).
    *   **Docker Context**: `.`
    *   **Dockerfile Path**: `Dockerfile.monolith` (Render setting).
3.  **Environment Variables**:
    *   Add ALL variables for Backend, Bot, Scraper.
    *   `PORT`: `8000` (Render will route traffic here for the Web part).
    *   `REDIS_HOST`, `DATABASE_URL`, etc.

**Note**:
*   The Bot runs on port 8080 internally, but since it's in the same container, it can't be exposed externally easily on Render Free tier (single port).
*   However, the Bot generally just polls Telegram, so it doesn't strictly need ingress unless you use Webhooks. Our code uses polling, so it works fine!
