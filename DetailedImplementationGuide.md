# JobPulse Detailed Implementation Guide

This guide breaks down the 10-Day Implementation Plan into actionable steps, including the key concepts you need to understand ("Prerequisites") before starting each day.

---

## Phase 1: Foundation (Days 1-2)

**Goal**: Get the backend running with a database and API endpoints.

### Prerequisites (What to know first)
1.  **Django Models**: Understand how Python classes define database tables.
    *   *Concept*: `class User(models.Model)` -> SQL `CREATE TABLE users...`
2.  **Django Rest Framework (DRF)**: Understand Serializers.
    *   *Concept*: Transforming complex data (like a User object) into JSON for APIs.
3.  **Docker Compose**: How to spin up multiple services (Django + Postgres) together.

### Day 1: Project Setup & User Models
1.  **Environment Setup**:
    *   Create `Dockerfile` for Python.
    *   Create `docker-compose.yml` with `web` (Django), `db` (Postgres), and `redis` services.
    *   *Guideline*: Ensure containers can talk to each other (check `MONGO_URI` or `DATABASE_URL`).
2.  **Initialize Project**:
    *   Run `django-admin startproject job_pulse .`
    *   Run `django-admin startapp users`.
3.  **Implement User Model**:
    *   Extend `AbstractUser`.
    *   Add fields: `telegram_id` (BigInt, Unique), `skills` (ArrayField), `preferences` (JSONField).
4.  **Database Migration**:
    *   Run `makemigrations` and `migrate`.
    *   *Check*: Connect to Postgres via CLI/UI and verify tables exist.

### Day 2: Core Models (Channels/Jobs) & Basic API
1.  **Create Apps**: `channels` and `jobs`.
2.  **Implement Channel Model**:
    *   Fields: `name` (e.g., @mychannel), `channel_id` (BigInt), `last_scraped_id` (Int).
3.  **Implement JobPost Model**:
    *   Fields: `raw_text`, `clean_text` (for creating matchable text), `source_link` (URL), `is_processed` (Bool).
4.  **Create Serializers**:
    *   `UserSerializer`, `ChannelSerializer`, `JobPostSerializer`.
5.  **Create Views (API)**:
    *   `POST /api/users/`: Create user (Onboarding).
    *   `POST /api/job_posts/`: Receive scraped jobs (Ingestion).
    *   *Guideline*: Use `generics.CreateAPIView` for simplicity.

---

## Phase 2: The Scraper (Days 3-4)

**Goal**: Build a standalone Python service that listens to Telegram channels.

### Prerequisites (What to know first)
1.  **Asyncio**: Python's async/await syntax. Telethon is purely async.
    *   *Concept*: Functions that pause (`await`) while waiting for network IO, not blocking the CPU.
2.  **Telethon Events**: How the library triggers code when a new message arrives.
    *   *Concept*: `@client.on(events.NewMessage)` decorator.
3.  **Requests Library**: How to send HTTP POST requests to your Django API.

### Day 3: Telethon Basic Setup
1.  **Get Credentials**: Get `api_id` and `api_hash` from my.telegram.org.
2.  **Service Setup**:
    *   Create `scraper/main.py`.
    *   Initialize `TelegramClient`.
3.  **Authentication**:
    *   Run the script locally once to generate the session file (login via phone number).
    *   *Guideline*: Identify how to persist this session (mount volume in Docker).

### Day 4: Channel Monitoring & Ingestion
1.  **Channel Joining**:
    *   Write a script/function that accepts a channel list and joins them: `client(JoinChannelRequest(channel))`.
2.  **Event Listener**:
    *   Implement `NewMessage` event handler.
    *   Extract: `event.message.message` (text), `event.chat.username` (channel).
3.  **API Integration**:
    *   Inside the handler, use `httpx` or `requests` to POST the data to `http://web:8000/api/job_posts/`.
    *   *Check*: Send a message in a test channel, verify a new row appears in the `JobPost` table.

---

## Phase 3: The Bot (Days 5-6)

**Goal**: Allow users to interact with the system (Onboarding).

### Prerequisites (What to know first)
1.  **Aiogram Dispatchers**: How to route `/start` or text buttons to functions.
2.  **FSM (Finite State Machine)**: Handling multi-step flows (e.g., Step 1: Ask Name, Step 2: Ask Skills).
    *   *Concept*: Keeping track of "where" the user is in the conversation.

### Day 5: Bot Shell & State Machine
1.  **Bot Setup**:
    *   Create `bot/main.py` using `Aiogram`.
    *   Get Bot Token from @BotFather.
2.  **Define States**:
    *   Create `OnboardingState`: `WAITING_FOR_SKILLS`, `WAITING_FOR_LOCATION`.
3.  **Implement /start**:
    *   Send a welcome message.
    *   Transition state to `WAITING_FOR_SKILLS`.

### Day 6: Connecting Bot to Backend
1.  **Collect Data**:
    *   Store user answers in memory (FSM context) as they reply.
2.  **Save to Backend**:
    *   At the end of the flow, `POST` data to `http://web:8000/api/users/`.
    *   *Guideline*: Handle duplications (if user already exists).
3.  **Add Channel Command**:
    *   Implement `/addchannel @channel`.
    *   Validation: Check if channel exists on Telegram (using a simple check or regex).
    *   Send to backend: `POST /api/channels/`.

---

## Phase 4: Matching & Notifications (Days 7-8)

**Goal**: Process scraped jobs and alert users.

### Prerequisites (What to know first)
1.  **Celery Tasks**: Background jobs.
    *   *Concept*: Offloading heavy logic (matching) away from the API request loop.
2.  **Set Operations**: Basic Python sets for skill matching (`user_skills & job_skills`).

### Day 7: Matching Engine (Worker)
1.  **Celery Setup**:
    *   Configure Celery in Django (`celery.py`).
    *   Connect to Redis.
2.  **Process Task**:
    *   Create task `process_job_post(job_id)`.
    *   Logic: Clean text -> Extract keywords.
3.  **Matching Logic (V1)**:
    *   Fetch all users.
    *   Loop users: If `len(user.skills & extracted_skills) > 0`, it's a match.
    *   *Guideline*: This is O(N), fine for MVP. Optimization comes later.

### Day 8: Notifications
1.  **Trigger Notification**:
    *   If match found, save a `Notification` record in DB.
2.  **Delivery**:
    *   Create a task `send_telegram_alert`.
    *   Use the **Bot** (via API or directly if code shared) to send a message to `user.telegram_id`.
    *   *Content*: "New Job Found! [Link] \n Skills: Python, Django".
    *   *Check*: Scraper finds job -> Backend triggers Match -> Bot sends msg.

---

## Phase 5: Polish & Deploy (Days 9-10)

**Goal**: Make it stable and public.

### Prerequisites (What to know first)
1.  **Nginx**: Reverse Proxy.
    *   *Concept*: Hides internal ports (8000) and serves static files.
2.  **Production Security**: `DEBUG=False`, Allowed Hosts, Secrets.

### Day 9: Production Config
1.  **Nginx Config**:
    *   Create `nginx/default.conf`.
    *   Route `/static/` to files, `/` to Django.
2.  **Gunicorn**:
    *   Replace `python manage.py runserver` with `gunicorn core.wsgi:application`.
3.  **Docker Healthchecks**:
    *   Ensure containers restart if they crash.

### Day 10: Deployment
1.  **Cloud Provider**:
    *   Choose a provider (e.g., DigitalOcean, Railway, Render).
    *   Provision a remote Postgres DB (Managed is better) or use the containerized one with a Volume.
2.  **Deployment**:
    *   Push code to GitHub.
    *   Pull on server (or auto-deploy).
    *   Copy `.env` file (Secrets).
    *   `docker-compose up -d --build`.
3.  **Final Verification**:
    *   Run the full user loop on the live bot.
