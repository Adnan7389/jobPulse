# # 🚀 **JobPulse — Full Implementation Roadmap (Daily Guide)**

**Duration:** 14–18 days (2–3 weeks MVP)
**Skill Level:** Beginner–Intermediate
**Stack:** Django + Telethon + Aiogram + Celery + PostgreSQL + Redis + Gemini + Ollama

---

# # **Day 1 — Foundation Setup**

## ✅ **What You Must Do Today**

* Install core tools
* Prepare development environment
* Initialize the monorepo structure
* Create a GitHub repo
* Set up virtual environments for backend, bot, scraper

### Tasks:

1. Install:

   * Python 3.10+
   * PostgreSQL
   * Redis
   * Docker
   * Git & GitHub
   * VSCode + Extensions (Python, Docker, GitLens)

2. Clone your empty repository & initialize directory structure:

```
jobpulse/
  backend/
  scraper/
  bot/
  matching_engine/
  worker/
```

3. Create virtual environments:

```
python -m venv venv
source venv/bin/activate
```

---

## 📘 **What You Must Learn Before/While Doing This**

### 🔹 Python Virtual Environments

Why? Avoid dependency conflicts.

**Learn:**

* How to create venv
* How to activate/deactivate
* Requirements.txt basics

### 🔹 Git basics

* commit / push
* branching
* .gitignore

### 🔹 PostgreSQL basics

* Create DB
* Users
* Connections

---

## 🎥 Recommended Resources

* Python venv: [https://docs.python.org/3/library/venv.html](https://docs.python.org/3/library/venv.html)
* Git basics (10 minutes): [https://www.atlassian.com/git/tutorials](https://www.atlassian.com/git/tutorials)
* PostgreSQL basics: [https://www.postgresqltutorial.com/](https://www.postgresqltutorial.com/)

---

## ⚠️ Common Mistakes

* Installing Python 3.12 (many libs fail)
* Forgetting to activate venv
* Not adding `.env` to `.gitignore`
* Mixing system Python with venv packages

---

## 🧪 Small Exercise

* Create a PostgreSQL database called `jobpulse_db`
* Test connection using `psql`

---

**— End of Day 1**

# # **Day 2 — Django Backend Setup**

## ✅ **What You Must Do Today**

Today you will:

* Create the Django backend project
* Configure PostgreSQL database connection
* Create core apps (users, channels, jobs, notifications)
* Prepare settings structure (base/local/production)
* Install Django REST Framework

### **Tasks**

1. **Install Django + DRF**

```
pip install django djangorestframework psycopg2-binary python-dotenv
```

2. **Create Django project**

```
django-admin startproject core backend/
```

3. **Create main apps**

```
cd backend
python manage.py startapp users
python manage.py startapp channels
python manage.py startapp jobs
python manage.py startapp notifications
```

4. **Create modular settings files**
   Inside `backend/core/settings/`:

```
base.py
local.py
production.py
```

5. **Configure PostgreSQL connection** in `local.py`:

```py
DATABASES = {
  "default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "jobpulse_db",
    "USER": "postgres",
    "PASSWORD": "yourpassword",
    "HOST": "localhost",
    "PORT": 5432,
  }
}
```

6. **Run initial migrations**

```
python manage.py migrate
```

7. **Start the server**

```
python manage.py runserver
```

---

# 📘 **What You Must Learn Today**

### 🔹 Django Project Structure

Understand folders:

* `core/` → settings, URLs, config
* `apps/` → users, channels, etc
* `manage.py`

### 🔹 Django Models Basics

You need to know:

* `models.Model`
* fields (CharField, ForeignKey, JSONField, DateTimeField)
* migrations

### 🔹 Django REST Framework Basics

You will use:

* Serializers
* APIView / ViewSets
* Routers

---

# 🧠 **Key Concepts**

### **1. MVC/MVT in Django**

Django uses:

* Model
* Template
* View (but we’ll use API views)

### **2. Environments**

* base.py → shared config
* local.py → development
* production.py → deployment

### **3. .env file**

Store sensitive data:

```
SECRET_KEY=...
DB_PASSWORD=...
GEMINI_API_KEY=...
```

---

# 📚 Recommended Resources

* Django Official Tutorial
* DRF Quickstart → [https://www.django-rest-framework.org/tutorial/quickstart/](https://www.django-rest-framework.org/tutorial/quickstart/)
* Django Settings guide (split settings)

---

# ⚠️ Common Mistakes to Avoid

* Putting DB credentials in settings file
* Forgetting to add apps to `INSTALLED_APPS`
* Running server before applying migrations
* Mixing production/local settings

---

# 🧪 Mini Exercise

1. Create a test endpoint:

```py
from django.http import JsonResponse

def ping(request):
    return JsonResponse({"message": "pong"})
```

2. Add the route and test it in browser.

---

**— End of Day 2**

# # **Day 3 — User System, Authentication & Telegram User Model**

Today you’ll build the **foundation of all user-related logic**, including how Telegram users will be represented inside Django.

---

# ✅ **What You Must Do Today**

### **1. Create the User Model (custom user)**

Inside `users/models.py`:

* Use `AbstractBaseUser` + `PermissionsMixin`
* Fields needed:

  * `telegram_user_id` (bigint)
  * `username`
  * `first_name`
  * `last_name`
  * `skills` (JSON list)
  * `preferred_job_titles` (JSON list)
  * `location`
  * `experience_years`
  * `created_at`
  * `updated_at`

### **2. Add User Manager**

Implement:

* `create_user`
* `create_superuser`

### **3. Update settings**

In `core/settings/base.py`:

```py
AUTH_USER_MODEL = "users.User"
```

### **4. Create Serializers for user profile**

`users/serializers.py`:

* `UserSerializer`
* `UserPreferencesSerializer`

### **5. Create simple API endpoints**

Using DRF ViewSets:

* `update_profile`
* `get_profile`

### **6. Test with Swagger or Django REST Framework Browsable API**

---

# 📘 What You Must Learn Before Doing This

### 🔹 **Custom User Model**

Why?
Because login happens via Telegram, not email/password.

Must understand:

* AbstractBaseUser
* PermissionsMixin
* User managers

### 🔹 **JSONField**

Why?
User will store:

* skills = ["react", "django", "sql"]
* preferred_titles = ["frontend developer"]

Django's `JSONField` makes this easy.

### 🔹 **DRF Serializers**

Understand:

* Validation
* Updating nested fields
* Partial updates

---

# 🧠 Key Concepts

### **1. Telegram-first User System**

Your users **do NOT register** via the website.
Everything comes from Telegram bot authentication.

Therefore:

* `telegram_user_id` is the REAL user ID
* No password field required

### **2. Separation of Concerns**

* Bot collects user data
* Backend stores user data
* Scraper reads only channel posts
* Matching engine uses stored preferences

### **3. Partial Updates**

User will update skills/experience gradually.

Use:

```py
serializer = UserSerializer(user, data=request.data, partial=True)
```

---

# 📚 Recommended Resources

* Custom User Model Guide:
  [https://docs.djangoproject.com/en/4.2/topics/auth/customizing/#substituting-a-custom-user-model](https://docs.djangoproject.com/en/4.2/topics/auth/customizing/#substituting-a-custom-user-model)
* DRF Serializers:
  [https://www.django-rest-framework.org/api-guide/serializers/](https://www.django-rest-framework.org/api-guide/serializers/)

---

# ⚠️ Common Mistakes to Avoid

* Forgetting to set `AUTH_USER_MODEL` before running migrations
* Adding new fields to user without migration
* Using CharField for lists instead of JSON
* Adding password field (not needed for Telegram auth)

---

# 🧪 Mini Exercise

Create and test a user manually using Django shell:

```
python manage.py shell
```

```py
from users.models import User
u = User.objects.create(telegram_user_id=12345, username="adnan")
u.skills = ["python", "django"]
u.save()
```

---

**— End of Day 3**

# # **Day 4 — Telegram Bot Setup (Aiogram) + User Preference Collection**

Today you will set up the Telegram Bot (Aiogram), connect it to your Django backend, and implement the flow that collects user preferences (skills, job title, experience, location, and channel selection).

This is a **core part** of the system because users interact ONLY through Telegram.

---

# ✅ **What You Must Do Today**

## **1. Create the bot service folder**

Inside your project root:

```
bot/
  app.py
  handlers/
  keyboards/
  services/
  utils/
```

Install required packages:

```
pip install aiogram requests python-dotenv
```

---

## **2. Create the bot entry point**

`bot/app.py`:

```py
from aiogram import Bot, Dispatcher
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

async def main():
    from handlers import register_handlers
    register_handlers(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## **3. Implement the user onboarding flow**

Create `handlers/onboarding.py`:

Steps to build:

1. Start command → greet user
2. Ask for skills
3. Ask for preferred job titles
4. Ask for years of experience
5. Ask for location
6. Sync all data to Django backend
7. Ask user to choose Telegram channels to follow

Use FSM (Finite State Machine) in Aiogram:

* Makes multi-step conversations easy
* Ensures data is tracked cleanly

Install FSM storage:

```
pip install aiogram
```

---

## **4. Send collected data to Django backend**

Create a service file:

`bot/services/api.py`:

```py
import requests
import os

BASE_URL = os.getenv("BACKEND_API_URL")

def update_user_profile(telegram_id, data):
    return requests.post(
        f"{BASE_URL}/users/{telegram_id}/update/",
        json=data
    )
```

---

## **5. Implement channel selection**

Your system allows user to add their own channels dynamically.

Bot flow:

1. User taps “➕ Add Channel”
2. Bot asks user to forward the message from that channel
3. Bot extracts:

   * channel_id
   * title
   * link
4. Data is sent to backend:

```json
POST /channels/add
{
  "telegram_id": 12345,
  "channel_id": -10012345678,
  "title": "Ethiopian Jobs",
  "invite_link": "https://t.me/EthioJobs"
}
```

---

## **6. Test the bot manually**

Run:

```
python app.py
```

Use your Telegram app to:

* /start
* Provide skills
* Provide job titles
* Provide experience
* Provide location
* Add channels

Everything must be saved in your Django DB.

---

# 📘 What You Must Learn Today

## **🔹 Aiogram (async Telegram bot framework)**

Learn:

* Dispatcher
* Message handlers
* CallbackQuery handlers
* FSM (states)

Aiogram is async → fast and handles scale easily.

## **🔹 How Telegram forwarding works**

Forwarded message contains metadata:

* `forward_from_chat.id`
* `forward_from_chat.title`

This is how user adds channels dynamically.

## **🔹 Working with external APIs from bot**

Use simple `requests.post()` or `aiohttp` for async.

---

# 🧠 Key Concepts

### **1. Bot is stateless — Django stores everything**

The bot collects data → sends to backend → backend persists.

Bot never stores user data long-term.

### **2. Onboarding is critical**

If user onboarding is smooth, retention is high.

### **3. Channel selection is the core of personalization**

User sees jobs ONLY from channels they added.

---

# 📚 Recommended Resources

* Aiogram Docs → [https://docs.aiogram.dev](https://docs.aiogram.dev)
* Telegram Bot API → [https://core.telegram.org/bots/api](https://core.telegram.org/bots/api)
* FSM tutorial → Aiogram states

---

# ⚠️ Common Mistakes to Avoid

* Hardcoding user state in variables instead of FSM
* Forgetting to validate long lists (skills)
* Not handling non-text responses (e.g., users sending stickers accidentally)
* Not supporting "skip" options
* Forgetting to use environment variables for BOT_TOKEN

---

# 🧪 Mini Exercises

1. Add an echo command:

```py
@dp.message(F.text)
async def echo(message: Message):
    await message.answer(message.text)
```

2. Try forwarding a channel post and print the metadata:

```py
print(message.forward_from_chat)
```

---

**— End of Day 4**

# # **Day 5 — Telegram Scraper (Telethon) + Async Job Ingestion Pipeline**

Today you’ll build the **async Telegram scraper service** that listens to all user-added channels and sends new posts to your Django backend for storage and AI matching.

This is a CRITICAL part of the system because:

* It powers job ingestion
* It tracks user-specified channels
* It ensures your system stays updated automatically

---

# ✅ **What You Must Do Today**

---

## **1. Create the scraper service folder**

```
scraper/
  app.py
  client.py
  handlers/
  services/
  utils/
```

Install Telethon:

```
pip install telethon aioschedule python-dotenv requests
```

---

## **2. Set up Telethon client**

`client.py`:

```py
from telethon import TelegramClient
import os
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")

client = TelegramClient("scraper_session", api_id, api_hash)
```

---

## **3. Fetch channels from Django Backend**

One of the new features we added is that **users select their own channels**, so the scraper must dynamically load them.

Create:
`scraper/services/backend.py`

```py
import requests
import os

BASE = os.getenv("BACKEND_API_URL")

def fetch_channels():
    r = requests.get(f"{BASE}/channels/list/")
    return r.json()
```

---

## **4. Subscribe to channel events**

Telethon uses an async event handler:

`scraper/app.py`:

```py
from client import client
from telethon import events
from services.backend import send_post

@client.on(events.NewMessage(chats=CHANNEL_IDS))
async def new_post(event):
    post = {
        "channel_id": event.chat_id,
        "message_id": event.id,
        "text": event.message.message,
        "date": event.date.isoformat()
    }
    send_post(post)
```

> **But** CHANNEL_IDS must be dynamically loaded.

So you’ll implement a scheduler that refreshes channel list every X minutes.

---

## **5. Create dynamic channel loader**

`utils/channel_loader.py`:

```py
import asyncio

CHANNEL_IDS = []

async def refresh_channels():
    global CHANNEL_IDS
    data = fetch_channels()
    CHANNEL_IDS = [c["channel_id"] for c in data]
```

Schedule it like:

```py
import aioschedule as schedule

schedule.every(5).minutes.do(refresh_channels)
```

---

## **6. Send incoming posts to backend**

`scraper/services/backend.py`:

```py
def send_post(post_data):
    requests.post(f"{BASE}/jobs/ingest/", json=post_data)
```

The backend endpoint `/jobs/ingest/` stores the raw post and triggers the matching engine.

---

## **7. Run the scraper**

```
python app.py
```

Test by posting in a channel.

Your scraper should:

* detect new message
* extract text
* send it to Django backend

---

# 📘 What You Must Learn Today

---

### **🔹 Telethon Basics**

Learn:

* Connecting using api_id/api_hash
* Listening for events
* Accessing message metadata
* Chat IDs vs Channel IDs

### **🔹 Async Programming**

Understand:

* `async/await`
* Event loops
* Non-blocking operations

### **🔹 Scheduling**

To keep channel list updated dynamically.

You can use:

* `aioschedule`
* or custom `asyncio.sleep()` loops

---

# 🧠 Key Concepts

---

### **1. Scraper must be async for performance**

Telethon async = handles thousands of messages without blocking.

### **2. Scraper = message forwarder, not classifier**

Scraper:

* extracts raw text
* identifies channel + message ID
* sends to backend

Backend/AI decides relevance.

### **3. Job de-duplication**

Backend must check for duplicate:

* channel_id + message_id

---

# 📚 Recommended Resources

* Telethon basics → [https://docs.telethon.dev](https://docs.telethon.dev)
* Async Python tutorial → [https://realpython.com/async-io-python/](https://realpython.com/async-io-python/)
* Channel ID explanation: Telegram "supergroup vs channel"

---

# ⚠️ Common Mistakes to Avoid

* Using bot API instead of client API (Telethon is needed)
* Hardcoding channel IDs
* Scraper crashing from network errors (use try/except)
* Not storing `message_id` (you need it for direct link)
* Blocking the event loop with heavy tasks

---

# 🧪 Mini Exercises

### 1. Print every message from a test channel:

```py
@client.on(events.NewMessage)
async def handler(event):
    print(event.message.message)
```

### 2. Try forwarding a post:

```
print(event.chat_id, event.id)
```

---

**— End of Day 5**

# # **Day 6 — Job Ingestion API + Job Storage + Duplicate Prevention**

Today you will build the **backend ingestion pipeline** — the part where the scraper sends raw Telegram posts into Django, stores them, checks duplicates, and prepares them for AI matching.

This connects all the pieces you've already built.

---

# ✅ **What You Must Do Today**

---

## **1. Create the Job model in Django**

Inside `jobs/models.py`:

```py
from django.db import models
from django.conf import settings

class JobPost(models.Model):
    channel_id = models.BigIntegerField()
    message_id = models.BigIntegerField()
    text = models.TextField()
    date = models.DateTimeField()
    raw_data = models.JSONField(null=True, blank=True)

    # AI fields (filled later)
    extracted_skills = models.JSONField(null=True, blank=True)
    extracted_experience = models.FloatField(null=True, blank=True)
    extracted_location = models.CharField(max_length=100, null=True, blank=True)
    ai_summary = models.TextField(null=True, blank=True)
    gemini_status = models.CharField(max_length=20, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("channel_id", "message_id")
```

### 🔹 Why?

This prevents storing the same post twice.

---

## **2. Create ingestion API endpoint**

`jobs/views.py`:

```py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import JobPost

class IngestJobPost(APIView):
    def post(self, request):
        data = request.data

        obj, created = JobPost.objects.get_or_create(
            channel_id=data["channel_id"],
            message_id=data["message_id"],
            defaults={
                "text": data.get("text", ""),
                "date": data.get("date"),
                "raw_data": data
            }
        )

        return Response({"created": created})
```

---

## **3. Add URL route**

`core/urls.py`:

```py
path("jobs/ingest/", IngestJobPost.as_view()),
```

---

## **4. Prepare job for AI processing**

When a job is ingested, mark it as `pending`.

Later, Celery worker will run matching:

* Gemini → Ollama → NLP
* Save extracted fields
* Trigger user notifications

> You will implement this tomorrow (Day 7).

---

## **5. Test scraper → backend connection**

Run Django + Scraper:

* Send a message in your test channel
* Scraper receives it
* sends to `/jobs/ingest/`
* Django stores it
* New row appears in DB

---

# 📘 What You Must Learn Today

---

## 🔹 **Django ORM basics**

You should understand:

* `get_or_create` to prevent duplicates
* unique constraints
* saving JSON data
* model migrations

## 🔹 **Why duplicates happen**

Telegram sends:

* channel_id
* message_id

Together, they uniquely identify each post.

Without this, your AI gets duplicate inputs → double notifications.

---

# 🧠 Key Concepts

---

### **1. Job ingestion is NOT about AI yet**

Today you:

* store raw data
* validate
* deduplicate
  AI runs later.

### **2. Message metadata is essential**

You need:

* channel_id
* message_id
* text
* date

for links & notifications.

### **3. Atomic creation**

`get_or_create` avoids race conditions between scraper workers.

---

# 📚 Recommended Resources

* Django ORM get_or_create:
  [https://docs.djangoproject.com/en/4.2/ref/models/querysets/#get-or-create](https://docs.djangoproject.com/en/4.2/ref/models/querysets/#get-or-create)
* Unique constraints:
  [https://docs.djangoproject.com/en/4.2/ref/models/options/#unique-together](https://docs.djangoproject.com/en/4.2/ref/models/options/#unique-together)
* DRF API views:
  [https://www.django-rest-framework.org/api-guide/views/](https://www.django-rest-framework.org/api-guide/views/)

---

# ⚠️ Common Mistakes to Avoid

* Using `CharField` for message_id (use int64)
* Saving empty text (clean text before saving)
* Forgetting timezones when saving dates
* Not marking job as "pending" for matching
* Not storing raw JSON for debugging

---

# 🧪 Mini Exercises

### 1. Try saving the same post twice

You should get `created: false`.

### 2. Add a filter query

In Django shell:

```py
JobPost.objects.filter(channel_id=123).count()
```

### 3. Inspect a stored job:

```py
post = JobPost.objects.first()
print(post.raw_data)
```

---

**— End of Day 6**

# # **Day 7 — AI Matching Pipeline (Gemini → Ollama → NLP) + Celery Worker Setup**

Today is **one of the most important days**.
You will implement the full **AI Matching Engine**, including:

* Gemini semantic extraction
* Ollama fallback engine
* NLP fallback engine
* Match scoring logic
* Celery background worker
* Task routing (backend → worker → backend)

This connects Telegram posts → backend → AI → user notifications.

---

# ✅ **What You Must Do Today**

---

# ## **1. Install Celery + Redis**

In your backend environment:

```
pip install celery redis
```

Add Redis to Docker or install locally:

```
sudo apt install redis
sudo systemctl start redis
```

---

# ## **2. Create Celery configuration**

In `backend/core/celery.py`:

```py
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

In `backend/core/__init__.py`:

```py
from .celery import app as celery_app
__all__ = ("celery_app",)
```

---

# ## **3. Add Celery settings**

Inside `local.py`:

```py
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
```

---

# ## **4. Create matching task**

In `jobs/tasks.py`:

```py
from celery import shared_task
from .models import JobPost
from shared.ai import gemini_extract, ollama_extract, nlp_extract
from shared.scoring import calculate_score
from notifications.services import notify_users

@shared_task
def process_job_post(job_id):
    job = JobPost.objects.get(id=job_id)

    # Try Gemini first
    try:
        result = gemini_extract(job.text)
        job.gemini_status = "gemini"
    except:
        # Try Ollama next
        try:
            result = ollama_extract(job.text)
            job.gemini_status = "ollama"
        except:
            # Final fallback
            result = nlp_extract(job.text)
            job.gemini_status = "nlp"

    # Save extracted fields
    job.extracted_skills = result["skills"]
    job.extracted_experience = result["experience"]
    job.extracted_location = result["location"]
    job.ai_summary = result.get("summary", "")
    job.save()

    # Match against user preferences
    matches = calculate_score(job.id)

    # Notify matched users
    notify_users(job.id, matches)
```

---

# ## **5. Create ingestion → Celery trigger**

Update your ingestion API:

```py
from .tasks import process_job_post

class IngestJobPost(APIView):
    def post(self, request):
        ...
        if created:
            process_job_post.delay(obj.id)
```

Now every new post goes directly to the AI pipeline.

---

# ## **6. Implement Gemini extraction function**

`shared/ai/gemini_client.py`:

```py
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def gemini_extract(text):
    prompt = f"""
    Extract skills, required experience (in years), location, and give a short summary
    from the following job post:

    '{text}'

    Return as JSON: {{ "skills": [], "experience": 0, "location": "", "summary": "" }}
    """
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.to_dict()["json"]
```

---

# ## **7. Implement Ollama fallback (local LLM)**

`shared/ai/ollama_client.py`:

```py
import requests

def ollama_extract(text):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": f"""
            Extract skills, experience, location from this job post:
            {text}

            Return JSON with keys: skills, experience, location.
            """,
        }
    ).json()
    return response["response"]
```

---

# ## **8. Implement NLP fallback**

`shared/ai/nlp_fallback.py`:

```py
import re

def extract_experience(text):
    match = re.search(r"(\d+)\+?\s*years?", text)
    return int(match.group(1)) if match else 0

def extract_skills(text):
    SKILLS = ["python", "django", "react", "sql", "node", "aws"]
    return [s for s in SKILLS if s.lower() in text.lower()]

def extract_location(text):
    match = re.search(r"(Addis Ababa|Remote|Hybrid)", text, re.IGNORECASE)
    return match.group(1) if match else "Unknown"

def nlp_extract(text):
    return {
        "skills": extract_skills(text),
        "experience": extract_experience(text),
        "location": extract_location(text),
        "summary": text[:200]
    }
```

---

# ## **9. Implement match scoring logic**

`shared/scoring.py`:

```py
from users.models import User
from jobs.models import JobPost

def calculate_score(job_id):
    job = JobPost.objects.get(id=job_id)
    users = User.objects.all()

    matches = []
    for user in users:
        score = 0

        # Skill match
        for s in user.skills:
            if s.lower() in (job.extracted_skills or []):
                score += 40

        # Experience match
        if user.experience_years >= job.extracted_experience:
            score += 30

        # Location match
        if user.location.lower() == (job.extracted_location or "").lower():
            score += 30

        if score >= 50:
            matches.append(user.id)

    return matches
```

---

# ## **10. Start Celery worker**

```
celery -A core worker --loglevel=info
```

---

# 📘 What You Must Learn Today

### **1. How Celery Works**

* Producer → queue → consumer
* Asynchronous task execution
* Useful for slow AI/ML tasks

### **2. Gemini API basics**

### **3. Ollama local inference**

* how to run local Llama3/Mistral
* zero cost
* fast for short tasks

### **4. NLP basics**

* regex
* keyword extraction
* text cleaning

---

# 🧠 Key Concepts

### **1. Three-level fallback = no downtime**

Gemini → (limit reached) → Ollama → (offline) → NLP
This guarantees:

* reliability
* cost control
* stability

### **2. Celery decouples AI from HTTP**

Ingestion is fast
AI runs in background

### **3. Score-based matching**

You can tune:

* skill weight
* experience weight
* location weight

---

# 📚 Recommended Resources

* Celery official docs → [https://docs.celeryq.dev](https://docs.celeryq.dev)
* Gemini API quickstart → Google AI Studio
* Ollama → [https://ollama.com/](https://ollama.com/)
* Regex basics → [https://regex101.com](https://regex101.com)

---

# ⚠️ Common Mistakes to Avoid

* Running AI inside Django request (slow!)
* Using blocking code in async scraper
* Not handling empty text
* Not setting job status correctly
* Forgetting `.delay()` when calling Celery

---

# 🧪 Mini Exercises

1. Run task manually:

```py
process_job_post.delay(1)
```

2. Print matched users for a job
3. Simulate Gemini failure to test Ollama fallback

---

**— End of Day 7**

# # **Day 8 — User Notification System (Bot Notifications + Filtering by User Channels)**

Today you will implement the **notification layer**, which takes matched users from the AI pipeline and sends them job posts **only from the channels they selected**, with:

* Direct post link
* Full job description
* Clean formatting
* Real-time Telegram delivery

This completes the “end-to-end loop” of your system.

---

# ✅ **What You Must Do Today**

---

# ## **1. Create the Notification Model (Optional Logging)**

Inside `notifications/models.py`:

```py
from django.db import models
from django.conf import settings

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    job = models.ForeignKey("jobs.JobPost", on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
```

---

# ## **2. Create Notification Service**

`notifications/services.py`:

```py
import requests
from django.conf import settings
from users.models import User
from channels.models import Channel

BOT_URL = settings.BOT_SEND_MESSAGE_URL  # Exposed via API or webhook

def notify_users(job_id, matches):
    from jobs.models import JobPost
    job = JobPost.objects.get(id=job_id)

    for user_id in matches:
        user = User.objects.get(id=user_id)

        # 1️⃣ Check if the user follows this job's channel
        if not user.channels.filter(channel_id=job.channel_id).exists():
            continue

        # 2️⃣ Build direct Telegram link
        link = f"https://t.me/c/{str(job.channel_id)[4:]}/{job.message_id}"

        message = (
            f"📢 *New Job Matched For You* \n\n"
            f"{job.ai_summary or job.text[:500]}\n\n"
            f"🔗 [Open Job Post]({link})"
        )

        # 3️⃣ Send request to bot-api
        requests.post(
            BOT_URL,
            json={
                "telegram_id": user.telegram_user_id,
                "text": message,
                "parse_mode": "Markdown"
            }
        )
```

---

# ## **3. Implement Bot Message Sender Endpoint**

Inside the bot service:

`bot/handlers/send_message.py`:

```py
from aiogram import Bot
from aiogram.types import Message
from fastapi import APIRouter

router = APIRouter()

bot = Bot(token=os.getenv("BOT_TOKEN"))

@router.post("/bot/send/")
async def send_message(payload: dict):
    await bot.send_message(
        chat_id=payload["telegram_id"],
        text=payload["text"],
        parse_mode=payload.get("parse_mode", "HTML")
    )
    return {"status": "sent"}
```

This is the endpoint Django calls.

---

# ## **4. Add API URL for Bot Sender**

In bot’s FastAPI app:

```
app.include_router(router, prefix="/api")
```

Then in Django settings:

```
BOT_SEND_MESSAGE_URL="http://bot-service:8001/api/bot/send/"
```

---

# ## **5. Final Integration in AI Pipeline**

Your matching engine now ends with:

```
notify_users(job.id, matches)
```

This completes the loop:

* User adds channel
* Scraper fetches post
* Backend stores post
* AI matches
* Score matches user
* Notification delivered
* With correct post link

---

# ## **6. Test the Full Pipeline**

Do this test:

### STEP 1 — Add skill in bot:

“python, django”

### STEP 2 — Add channel in bot:

Forward a message → channel added

### STEP 3 — Make a post in that channel:

“Hiring Django developer with 2+ years exp”

### STEP 4 — Scraper receives → backend → Celery → AI → match → bot

You should receive:
**📢 New Job Matched For You**

* summary
* direct link

---

# 📘 What You Must Learn Today

---

## 🔹 **FastAPI Basics (for bot webhooks)**

You don’t need a full backend in bot — only a simple HTTP endpoint.

## 🔹 **Telegram direct post linking**

For private/supergroup channels:

```
https://t.me/c/<channel_id_without_prefix>/<message_id>
```

If channel ID = -10012345678
Remove -100 → 12345678

## 🔹 **Filtering logic**

Notifications must ONLY go to users who:

1. matched job
2. AND follow that channel

This avoids spam.

---

# 🧠 Key Concepts

---

### **1. Notification logic is separated from AI logic**

Good architecture → easier debugging & scaling.

### **2. Bot is the output device**

Backend → bot → user
Bot never computes matching.

### **3. Every notification must be idempotent**

No duplicates:

* Use notification logs
* Or check if job_id+user_id was already sent

### **4. Clean formatting increases engagement**

Use:

* Markdown
* Emojis
* Short summaries

---

# 📚 Recommended Resources

* Aiogram sending messages
* Telegram deep-linking for posts
* FastAPI quickstart (10 min)
* Markdown formatting in Telegram

---

# ⚠️ Common Mistakes to Avoid

* Sending message before AI finishes
* Sending to users who didn't follow that channel
* Not escaping Markdown special characters
* Hardcoding bot URL
* Forgetting to secure the bot’s send endpoint

---

# 🧪 Mini Exercises

1. Write a simple function to escape Markdown characters:

```
_ * [ ] ( ) ~ ` > # + - = | { } . !
```

2. Test bot sending:

```
curl -X POST http://localhost:8001/api/bot/send/ \
  -d '{"telegram_id":12345, "text":"hello"}'
```

3. Test filtering logic by adding/removing channels from user.

---

**— End of Day 8 —**

# # **Day 9 — Channel Management System (Dynamic User Channels + Admin Controls)**

Today you’ll build the complete **Channel Management System**, which handles:

* User-added channels (from Telegram forwards)
* Admin-added channels (web dashboard)
* Storing channel metadata
* Validating channel IDs
* Ensuring scraper syncs dynamically
* Preventing duplicate channels
* Linking users ↔ channels (many-to-many)

This system is critical because **users must only be notified from channels they personally added**.

---

# ✅ **What You Must Do Today**

---

# ## **1. Create Channel Model**

Inside `channels/models.py`:

```py
from django.db import models
from django.conf import settings

class Channel(models.Model):
    channel_id = models.BigIntegerField(unique=True)
    title = models.CharField(max_length=255)
    invite_link = models.CharField(max_length=255, null=True, blank=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
```

---

# ## **2. Add Many-to-Many Relationship Between Users & Channels**

Modify your `User` model:

```py
channels = models.ManyToManyField("channels.Channel", related_name="subscribers")
```

Run migrations.

---

# ## **3. Create API Endpoints for Channels**

In `channels/views.py`:

### **Add a channel**

```py
class AddChannel(APIView):
    def post(self, request):
        user = request.user
        data = request.data

        channel, created = Channel.objects.get_or_create(
            channel_id=data["channel_id"],
            defaults={
                "title": data.get("title", "Unknown"),
                "invite_link": data.get("invite_link"),
                "added_by": user
            }
        )

        user.channels.add(channel)
        return Response({"status": "added"})
```

### **List channels for scraper**

```py
class ListChannels(APIView):
    def get(self, request):
        channels = Channel.objects.all().values("channel_id")
        return Response(channels)
```

---

# ## **4. Add URLs**

In `core/urls.py`:

```py
path("channels/add/", AddChannel.as_view()),
path("channels/list/", ListChannels.as_view()),
```

---

# ## **5. Update Bot → Add Channel Flow**

User forwards a message → bot extracts channel info → bot sends to backend → backend stores + links user.

Add this in `bot/services/api.py`:

```py
def add_channel(telegram_id, channel_data):
    requests.post(
        f"{BASE}/channels/add/",
        json={
            "channel_id": channel_data["chat_id"],
            "title": channel_data["title"],
            "invite_link": channel_data["invite_link"]
        },
        headers={"X-Telegram-ID": str(telegram_id)}
    )
```

Bot handler:

```py
@dp.message(F.forward_from_chat)
async def forwarded_channel(msg: Message):
    chat = msg.forward_from_chat
    channel_data = {
        "chat_id": chat.id,
        "title": chat.title,
        "invite_link": f"https://t.me/{chat.username}" if chat.username else None
    }
    api.add_channel(msg.from_user.id, channel_data)
    await msg.answer("Channel added successfully!")
```

---

# ## **6. Update Scraper to Pull Dynamic Channels**

Your existing logic already supports dynamic refresh.
Now simply ensure scraper reads the channel list every 5 minutes:

```py
async def refresh_channels():
    global CHANNEL_IDS
    data = fetch_channels()
    CHANNEL_IDS = [c["channel_id"] for c in data]
```

This ensures:

* When a user adds a channel, scraper begins tracking it automatically.

---

# ## **7. Test End-to-End**

### **Test Flow:**

1. In bot → forward a channel message
2. Django stores channel
3. User is linked to channel
4. Scraper loads updated channel list
5. Send test post in channel
6. AI pipeline runs
7. You receive notification ONLY if you added channel

Perfect.

---

# 📘 What You Must Learn Today

---

## 🔹 **Telegram Channel Metadata**

Forwarded messages contain:

* `forward_from_chat.id`
* `forward_from_chat.title`
* `forward_from_chat.username`
* No invite link (you construct it manually)

## 🔹 **Many-to-Many relations**

User ↔ Channels is M2M because:

* User can follow many channels
* Channel can have many subscribers

## 🔹 **Dynamic scraper config**

Scraper must adjust channel list automatically without restart.

---

# 🧠 Key Concepts

---

### **1. User personalization is based on channel subscriptions**

This is the core of your system’s accuracy.
Users only want jobs from their own channels.

### **2. Channel validation happens automatically**

Because Telethon client will fail if channel is invalid → you can handle this later.

### **3. Caching channel list helps performance**

Later you can store channel list in Redis:

```
"scraper_channels": [ids...]
```

### **4. Deduplication across channels**

Same job may appear in two channels — you handle this via (channel_id, message_id).

---

# 📚 Recommended Resources

* Django M2M fields:
  [https://docs.djangoproject.com/en/4.2/topics/db/examples/many_to_many/](https://docs.djangoproject.com/en/4.2/topics/db/examples/many_to_many/)
* Telegram channel metadata docs
* Telethon chat objects

---

# ⚠️ Common Mistakes to Avoid

* Using username instead of channel_id (not reliable!)
* Forgetting to refresh scraper channel list
* Mixing user-specific channels with global channels
* Hardcoding channel mapping inside bot
* Not validating duplicates

---

# 🧪 Mini Exercises

1. Create 3 test channels & add them using bot.
2. Print user-subscriptions:

```py
user.channels.all()
```

3. Make one post in each channel — verify user receives notifications only from selected ones.
4. Test invalid channel forward.

---

**— End of Day 9 —**

# # **Day 10 — Admin Dashboard + Monitoring Panel (Django Admin Customization)**

Today you will make your internal admin tools — needed for operations, debugging, and managing your SaaS.
This includes:

* Viewing users
* Viewing channels
* Viewing job posts
* Monitoring AI processing
* Resending failed notifications
* Monitoring scraper activity
* Log visibility (errors, warnings)

This is the “control center” of the entire platform.

---

# ✅ **What You Must Do Today**

---

# ## **1. Enable Django Admin for All Models**

Register models in:

### **users/admin.py**

```py
from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("telegram_user_id", "username", "location", "experience_years")
    search_fields = ("telegram_user_id", "username", "location")
    list_filter = ("location",)
```

### **channels/admin.py**

```py
from django.contrib import admin
from .models import Channel

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("title", "channel_id", "added_by")
    search_fields = ("title", "channel_id")
```

### **jobs/admin.py**

```py
from django.contrib import admin
from .models import JobPost

@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ("channel_id", "message_id", "date", "gemini_status")
    list_filter = ("gemini_status", "date")
    search_fields = ("text",)
```

### **notifications/admin.py**

```py
from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "sent_at", "is_read")
    list_filter = ("is_read",)
```

---

# ## **2. Add Filtering Tools**

This helps the admin review problems quickly.

Examples:

* Filter job posts by:

  * date
  * channel
  * AI status (“gemini”, “ollama”, “nlp”)

* Filter users by:

  * experience
  * location

* Filter channels by:

  * added_by
  * title

---

# ## **3. Add “AI Extraction Preview” in Admin**

In `JobPostAdmin`, add:

```py
readonly_fields = ("extracted_skills", "extracted_experience", "ai_summary")
```

This helps you debug AI results for each job post.

---

# ## **4. Add a Button: Reprocess Job Post Manually**

Add to `jobs/admin.py`:

```py
actions = ["reprocess_ai"]

def reprocess_ai(self, request, queryset):
    from .tasks import process_job_post
    for job in queryset:
        process_job_post.delay(job.id)
```

This is valuable when:

* Gemini fails
* Ollama crashes
* Job seems incorrectly parsed

---

# ## **5. Add Channel Subscribers Count in Admin**

Modify ChannelAdmin:

```py
def subscriber_count(self, obj):
    return obj.subscribers.count()

list_display = ("title", "channel_id", "subscriber_count")
```

---

# ## **6. Add Scraper Health Monitoring**

Create page for:

* Last scraper heartbeat
* Last successful fetch
* Number of channels loaded
* Errors last 24 hours

Add a simple model:

`scraper/models.py`:

```py
class ScraperStatus(models.Model):
    last_heartbeat = models.DateTimeField()
    channel_count = models.IntegerField(default=0)
    last_error = models.TextField(null=True, blank=True)
```

Scraper sends heartbeats:

```
POST /scraper/heartbeat/
```

Record status → view in admin.

---

# ## **7. Add Notification Retry System**

Sometimes notifications fail.
Create a button:

In `NotificationAdmin`:

```py
actions = ["resend"]

def resend(self, request, queryset):
    from notifications.services import notify_user
    for notif in queryset:
        notify_user(notif.user, notif.job)
```

---

# ## **8. Add Read-Only Security Settings**

In Admin, restrict actions:

* Only superuser can delete channels
* Only superuser can delete users
* Developers can re-run AI
* Staff can view logs

---

# ## **9. Test the Dashboard**

Checklist:

* Can you see all users?
* Can you see channels they follow?
* Can you see job posts?
* Can you see AI extraction fields?
* Can you re-run AI?
* Can you re-send notifications?
* Can you see scraper health?

---

# 📘 What You Must Learn Today

---

### 🔹 **Django Admin Customization**

Learn:

* `ModelAdmin`
* `list_display`, `list_filter`, `search_fields`
* `readonly_fields`
* `actions` (custom buttons)

### 🔹 **Admin Permissions**

* `is_staff`
* `is_superuser`
* `user_passes_test`

### 🔹 **Monitoring Principles**

You must know how to build:

* Heartbeat endpoints
* Admin-readable logs
* Error dashboards

---

# 🧠 Key Concepts

---

### **1. Admin dashboard = your operations control panel**

Everything from here is used to:

* inspect AI results
* debug issues
* view notifications
* manage channels
* monitor scraper

### **2. Logs Matter**

You MUST add:

* scraper errors
* AI failures
* notification failures

### **3. Retry Buttons Save Time**

Reprocessing AI manually helps fix bad results.

---

# 📚 Recommended Resources

* Django Admin Advanced:
  [https://docs.djangoproject.com/en/4.2/ref/contrib/admin/](https://docs.djangoproject.com/en/4.2/ref/contrib/admin/)
* Django Permissions:
  [https://docs.djangoproject.com/en/4.2/topics/auth/default/](https://docs.djangoproject.com/en/4.2/topics/auth/default/)

---

# ⚠️ Common Mistakes to Avoid

* Showing sensitive API keys in admin
* Allowing channel deletion (breaks scraper)
* Allowing job deletion (breaks notifications)
* Not making AI fields readonly
* Not adding filters (makes debugging painful)

---

# 🧪 Mini Exercises

1. Create an admin filter for job posts with `gemini_status="nlp"`
2. Add admin tab to see “top 10 channels by subscribers”
3. Add pagination to JobPost admin
4. Add a “retry scraper” button (manual heartbeat trigger)

---

**— End of Day 10 —**

# # **Day 11 — Deployment Preparation (Docker, Environment Setup, and Service Orchestration)**

Today you will prepare your system for **deployment** in a real production environment.
You’ll build Docker images, configure environment variables, prepare services, orchestrate everything with Docker Compose, and create a production-ready folder layout.

This step is critical because your system has multiple moving parts:

* Django API backend
* Celery worker
* Redis
* Scraper (Telethon async service)
* Bot service (FastAPI + Aiogram)
* Ollama (local LLM server)
* PostgreSQL
* Nginx (optional)

Deployment preparation ensures everything runs together smoothly.

---

# ✅ **What You Must Do Today**

---

# ## **1. Create Deployment Folder Structure**

At root:

```
deploy/
  docker/
    backend/
      Dockerfile
    bot/
      Dockerfile
    scraper/
      Dockerfile
    worker/
      Dockerfile
    nginx/
      Dockerfile
    ollama/
      Dockerfile (optional)
  compose/
    docker-compose.prod.yml
  env/
    backend.env
    bot.env
    scraper.env
    worker.env
```

---

# ## **2. Create Backend Dockerfile**

`deploy/docker/backend/Dockerfile`:

```dockerfile
FROM python:3.10

WORKDIR /app
COPY backend/ /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

# ## **3. Create Worker Dockerfile**

`deploy/docker/worker/Dockerfile`:

```dockerfile
FROM python:3.10

WORKDIR /app
COPY backend/ /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["celery", "-A", "core", "worker", "--loglevel=info"]
```

---

# ## **4. Create Scraper Dockerfile**

`deploy/docker/scraper/Dockerfile`:

```dockerfile
FROM python:3.10

WORKDIR /app
COPY scraper/ /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
```

---

# ## **5. Create Bot Dockerfile**

`deploy/docker/bot/Dockerfile`:

```dockerfile
FROM python:3.10

WORKDIR /app
COPY bot/ /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
```

---

# ## **6. Add Ollama server (local LLM)**

Ollama must run on host or container with GPU/CPU support.

For CPU-only VPS:

```
docker run -d -p 11434:11434 ollama/ollama:latest
```

Download model:

```
ollama pull llama3
```

---

# ## **7. Create docker-compose.prod.yml**

`deploy/compose/docker-compose.prod.yml`:

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: jobpulse
      POSTGRES_USER: jobpulse
      POSTGRES_PASSWORD: password
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7
    restart: always

  backend:
    build: ../docker/backend
    env_file: ../env/backend.env
    depends_on:
      - postgres
      - redis

  worker:
    build: ../docker/worker
    env_file: ../env/worker.env
    depends_on:
      - backend
      - redis
      - postgres

  scraper:
    build: ../docker/scraper
    env_file: ../env/scraper.env
    depends_on:
      - backend

  bot:
    build: ../docker/bot
    env_file: ../env/bot.env
    depends_on:
      - backend

  nginx:
    image: nginx:latest
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - backend

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    restart: always

volumes:
  pgdata:
```

---

# ## **8. Create Environment Variable Files**

Example: `backend.env`:

```
DJANGO_SECRET_KEY=supersecret
DJANGO_DEBUG=0
DATABASE_URL=postgres://jobpulse:password@postgres:5432/jobpulse
REDIS_URL=redis://redis:6379/0

GEMINI_API_KEY=xxxx
OLLAMA_URL=http://ollama:11434
```

---

# ## **9. Prepare Django for Production**

### Collect static files:

```
python manage.py collectstatic
```

### Apply migrations:

```
python manage.py migrate
```

---

# ## **10. Run Docker Compose**

From `deploy/compose/`:

```
docker compose -f docker-compose.prod.yml up -d --build
```

Check logs:

```
docker logs backend
docker logs worker
docker logs scraper
docker logs bot
```

Everything should run!

---

# 📘 What You Must Learn Today

---

### 🔹 **Docker Basics**

You must understand:

* Dockerfile
* Images
* Containers
* Volumes
* Networks

### 🔹 **Docker Compose**

To orchestrate multi-service architecture.

### 🔹 **Gunicorn**

Production WSGI server for Django.

### 🔹 **Reverse Proxy (Nginx)**

To expose your backend to the internet.

### 🔹 **Environment Variables**

Never hardcode secrets.

---

# 🧠 Key Concepts

---

### **1. Your system is a distributed architecture**

Each service is isolated:

* Backend does not scrape
* Scraper does not compute AI
* Bot does not store database
* Worker does not talk to Telegram

This increases reliability and scalability.

### **2. Docker helps achieve reproducibility**

Your system will behave the same on any machine.

### **3. Docker Compose orchestrates everything**

Brings up:

* Redis
* Postgres
* Backend
* AI worker
* Bot
* Scraper
* Ollama
* Nginx

All with one command.

---

# 📚 Recommended Resources

* Docker Tutorial (10 min): [https://docs.docker.com/get-started/](https://docs.docker.com/get-started/)
* Dockerfile best practices
* Docker Compose overview
* Gunicorn + Django
* Nginx reverse proxy basics

---

# ⚠️ Common Mistakes to Avoid

* Using wrong Python base image (must match version)
* Forgetting to map volume for Postgres
* Failing to set environment variables
* Forgetting to expose ports for Ollama
* Running Django server inside container with `runserver` instead of Gunicorn
* Hardcoding API URLs (use env vars)

---

# 🧪 Mini Exercises

1. Run backend alone with Docker
2. Run scraper alone with Docker
3. Stop backend — see how Celery fails
4. Restart only worker container
5. Run `docker ps` and identify all services
6. Exec into Postgres container to inspect tables

---

**— End of Day 11**

********************************************************8

# # **Day 12 — Logging, Error Handling, and Observability (Making the System Stable & Debuggable)**

Today is all about **stability** — making sure your system is robust, fault-tolerant, and easy to troubleshoot.

You will implement:

* Centralized logging (backend, scraper, bot, worker)
* Error handlers for each service
* Monitoring endpoints
* Retry mechanisms
* Crash recovery
* Alerting (optional)

This ensures your SaaS doesn’t randomly break in production.

---

# ✅ **What You Must Do Today**

---

# ## **1. Add Centralized Logging (Backend + Worker)**

In `core/settings/base.py`:

```py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s:%(name)s: %(message)s"
        },
    },

    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "logs/app.log",
            "formatter": "standard",
        },
    },

    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
        },
        "jobs": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
    }
}
```

Create folder:

```
mkdir backend/logs
```

---

# ## **2. Add Logging to Scraper (Telethon)**

Wrap message handler:

```py
import logging
logger = logging.getLogger("scraper")

@client.on(events.NewMessage)
async def handler(event):
    try:
        ...
    except Exception as e:
        logger.error(f"Scraper error: {str(e)}")
```

---

# ## **3. Add Logging to Bot (Aiogram)**

Global error handler:

```py
from aiogram.utils.exceptions import TelegramAPIError

@dp.errors()
async def error_handler(update, exception):
    logging.error(f"Bot error: {exception}")
```

---

# ## **4. Add Error Logging to AI Pipeline**

Inside `process_job_post`:

```py
try:
    result = gemini_extract(job.text)
except Exception as e:
    logger.error(f"Gemini failed for job {job.id}: {e}")
```

Repeat for Ollama and NLP.

---

# ## **5. Create Monitoring Endpoints**

### Backend health check:

`core/views.py`:

```py
class HealthCheck(APIView):
    def get(self, request):
        return Response({"status": "ok"})
```

URL:

```
/health/
```

### Scraper heartbeat route:

`scraper/app.py` calls backend:

```
POST /scraper/heartbeat/
```

Save timestamp.

---

# ## **6. Add Retry Mechanism for Broken Jobs**

Inside `jobs/tasks.py`:

```py
@shared_task(bind=True, max_retries=3)
def process_job_post(self, job_id):
    try:
        ...
    except Exception as e:
        self.retry(exc=e, countdown=10)
```

---

# ## **7. Add Dead Letter Table**

Create a model:

```py
class FailedTask(models.Model):
    job_id = models.IntegerField()
    error = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

Save failures here.

---

# ## **8. Create Log Viewer in Admin Panel**

In admin, add:

```py
from django.http import HttpResponse
from django.contrib import admin

class LogViewerAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("logs/", self.view_logs),
        ]
        return custom + urls

    def view_logs(self, request):
        log = open("logs/app.log").read()
        return HttpResponse(f"<pre>{log}</pre>")
```

This gives you:

```
/admin/app/logs/
```

---

# ## **9. Add Alerting (Optional)**

If scraper crashes:

* Send alert to Telegram private admin channel
* Or email yourself

Add inside scraper error handler:

```py
requests.post(ALERT_URL, json={"error": str(e)})
```

---

# 📘 What You Must Learn Today

---

### 🔹 **Python Logging Library**

Core concepts:

* logger
* handler
* formatter
* file logging
* level control (DEBUG/INFO/WARN/ERROR)

### 🔹 **Error handling patterns**

* try/except
* logging exceptions
* Celery retry patterns

### 🔹 **Health check endpoints**

Used for:

* Kubernetes
* Docker Compose
* UptimeRobot
* Load balancers

### 🔹 **Monitoring importance**

If scraper fails, the whole system fails silently unless monitored.

---

# 🧠 Key Concepts

---

### **1. Logging = Your System’s Truth**

If a user reports missing notification:

* logs show AI result
* logs show scraper activity
* logs show matching score

### **2. Retry = Reliability**

AI or network failures need automatic retry.

### **3. Health Checks = Ops Stability**

Backend / bot / scraper must expose status.

### **4. Observability > Features**

A system with no monitoring is impossible to maintain.

---

# 📚 Recommended Resources

* Python logging basics
* Structured logging patterns
* Celery retries
* Django monitoring
* UptimeRobot for pings

---

# ⚠️ Common Mistakes to Avoid

* Logging too little (no clues)
* Logging too much (noise)
* Printing instead of logging
* Not rotating logs (files grow huge)
* Not timestamping logs
* Missing retries in Celery

---

# 🧪 Mini Exercises

1. Break Gemini API key → see fallback logs
2. Stop scraper intentionally → check heartbeat alerts
3. Add a fake exception in Celery and test retry
4. View logs in admin panel

---

**— End of Day 12 —**

************************************************************

# # **Day 13 — Security Hardening + API Protection + Rate Limiting + Secrets Management**

Today you will secure your system so it can safely run as a production SaaS.
You’ll lock down:

* APIs
* Telegram bot communication
* Backend secrets
* Channel abuse protections
* Request throttling
* CORS rules
* Authentication between microservices

This ensures nothing breaks, no one abuses your service, and your infrastructure stays safe.

---

# ✅ **What You Must Do Today**

---

# ## **1. Secure Bot → Backend Communication**

Right now, anyone can call:

```
POST /bot/send/
```

You need to secure this.

### Add a Bot Secret Token:

* Generate a random secret:

```
openssl rand -hex 32
```

Add to `.env`:

```
BOT_INTERNAL_SECRET=xxxxxxxxxxxxxx
```

### Add middleware in Django:

```py
class BotAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "bot" in request.path:
            token = request.headers.get("X-Internal-Token")
            if token != os.getenv("BOT_INTERNAL_SECRET"):
                return JsonResponse({"error": "Unauthorized"}, status=401)
        return self.get_response(request)
```

Add to `MIDDLEWARE`.

---

# ## **2. Secure Scraper → Backend Communication**

Add header:

```
X-Scraper-Token: <secret>
```

Backend check:

```py
if "scraper" in request.path and request.headers.get("X-Scraper-Token") != SCRAPER_TOKEN:
    return unauthorized
```

---

# ## **3. Rate Limit User-Facing APIs**

Install DRF throttling:

Add to `REST_FRAMEWORK` settings:

```py
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "30/min",
        "anon": "10/min",
    }
}
```

This protects:

* profile updates
* channel adding
* future endpoints (billing, auth, etc)

---

# ## **4. Restrict Allowed Hosts**

In `production.py`:

```py
ALLOWED_HOSTS = ["jobpulse.com", "www.jobpulse.com", "YOUR_SERVER_IP"]
```

---

# ## **5. Enforce CORS Rules**

Install:

```
pip install django-cors-headers
```

In settings:

```py
CORS_ALLOWED_ORIGINS = [
    "https://jobpulse.com",
]
```

---

# ## **6. Secure All Secrets**

Your `.env` must contain:

```
DJANGO_SECRET_KEY=
DATABASE_URL=
GEMINI_API_KEY=
OLLAMA_URL=
BOT_TOKEN=
BOT_INTERNAL_SECRET=
SCRAPER_SECRET=
REDIS_URL=
```

Never commit `.env`.

---

# ## **7. Hide Django Admin URL**

Change:

```
/admin/
```

to:

```
/super_secure_admin_982347/
```

To prevent automated attacks.

---

# ## **8. Protect Media & Logs Folders**

Add to nginx config:

```
location /logs/ {
    deny all;
}
```

Never expose logs publicly.

---

# ## **9. Protect Scraper Memory & Crashes**

Limit memory in Docker:

```yaml
scraper:
  mem_limit: 512m
```

---

# ## **10. Protect Against Abuse of Channel Adding**

Users may try to:

* add 100 spam channels
* add banned channels
* add porn/illegal channels

Add validation:

### Check channel type:

```py
if chat.type != "channel":
    reject()
```

### Limit channels per user:

```
MAX_CHANNELS = 20
```

---

# 📘 What You Must Learn Today

---

### 🔹 **API Security Basics**

* tokens
* secrets
* headers
* request validation

### 🔹 **CORS & AllowedHosts**

Protect from:

* CSRF
* Cross-site calls

### 🔹 **Rate Limiting**

Prevents abuse & overload.

### 🔹 **Bot-to-backend authentication**

Critical to avoid unauthorized message sending.

---

# 🧠 Key Concepts

---

### **1. Internal Secrets Are Mandatory**

Bot, scraper, and worker must authenticate like clients.

### **2. Security focuses on “least privilege”**

Bot should only send messages.
Scraper only ingests.

### **3. Rate limiting protects your server from abuse**

If someone tries to add 500 channels → blocked.

### **4. Admin URL must not be predictable**

Bots attack `/admin/` thousands of times per day.

---

# 📚 Recommended Resources

* DRF throttling
* Django security checklist:
  [https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
* OWASP API Security

---

# ⚠️ Common Mistakes to Avoid

* Hardcoding secrets in code
* Exposing admin route
* Returning raw errors (helps attackers)
* Allowing anyone to call your bot send endpoint
* Exposing logs or job extracts publicly
* Using “*” CORS

---

# 🧪 Mini Exercises

1. Attempt API call without token → Should fail
2. Add 30 channels in 1 minute → Should rate-limit
3. Rename Django admin URL
4. View logs → ensure no secrets printed
5. Try sending message via bot endpoint with wrong token → should block

---

**— End of Day 13 —**

****************************************************

# # **Day 14 — Final QA Testing + Bug Fixing + MVP Launch Checklist**

Today you will run full **end-to-end testing**, fix bugs, validate all flows, and prepare the system for your first MVP launch.

This day is crucial — most people fail because they deploy without testing the entire pipeline.

We will test:

* Telegram bot flows
* User onboarding
* Adding channels
* Scraper ingestion
* AI matching (Gemini → Ollama → NLP fallback)
* Notifications
* Admin dashboard
* Deployment environment
* Security rules
* Logs & monitoring
* Performance sanity checks

Ready? Let’s finish strong.

---

# ✅ **What You Must Do Today**

---

# ## **1. Full End-to-End Test Flow**

### Step-by-step flow you must test:

---

### **1. Start with a clean environment**

Delete old data:

```
docker compose down -v
docker compose up -d --build
```

---

### **2. Onboard a test user in Telegram bot**

Test:

* /start
* Set skills
* Set job title
* Set experience
* Set location
* Add channels
* Update preferences

Ensure backend captured everything.

---

### **3. Add some test Telegram channels**

Forward from:

* 1 real job channel
* 1 dummy testing channel

Verify database:

```
User.channels.all()
```

---

### **4. Run scraper & check ingestion**

Send message in channel:

```
Hiring React developer (2+ years)
```

Check Django logs:

* scraper received post
* backend stored post
* celery task triggered

---

### **5. Test AI Matching Pipeline**

Use different types of job posts:

* Clear roles (“We need a Django dev”)
* Messy ones (“We’re hiring someone with Python experience…”)
* Posts without skills
* Posts with too many skills

Verify:

### Tests

| Scenario     | Expected                   |
| ------------ | -------------------------- |
| Gemini works | `gemini_status = "gemini"` |
| Gemini fails | fallback to Ollama         |
| Ollama fails | fallback to NLP            |
| No match     | user gets nothing          |
| Match        | user receives notification |

---

### **6. Test Notification System**

Ensure notification includes:

* Job summary
* Direct clickable post link
* Markdown formatting
* Non-empty description

Test on:

* Private channels
* Public channels
* Supergroups
* Forward-restricted channels

---

# ## **2. Admin Dashboard Testing**

Inside `/admin`:

### Test:

* User list
* Channel list
* Job list
* Job AI extraction preview
* Re-run AI button
* Resend notification button
* Scraper heartbeat page
* Failed task table
* Logs viewer page

Everything should be smooth.

---

# ## **3. Security Validation**

### Test these:

✔ API throttling works
✔ Wrong bot token → blocked
✔ Wrong scraper secret → blocked
✔ Admin page hidden
✔ Error messages don’t expose stack traces
✔ CORS is restricted
✔ Only HTTPS allowed (if using Nginx)

---

# ## **4. Performance Checks**

You don’t need full load testing, but test essentials:

### 10 posts in 1 second:

* do all get ingested?
* does celery keep up?
* does fallback work smoothly?

### 20+ channels:

* scraper refresh logic works
* event handler keeps tracking

### 5 users with different skills:

* correct matching logic?

---

# ## **5. Fix Common Bugs**

Typical issues you will encounter:

### **Bug 1 — Incorrect channel link**

Fix:

```
link = f"https://t.me/c/{str(channel_id)[4:]}/{message_id}"
```

### **Bug 2 — Missing `forward_from_chat` in bot**

Fix:
Ask user to forward a post publicly (not anonymously).

### **Bug 3 — Scraper gets flood-wait**

Solution:

* Set safe limits
* Add retry logic
* Add error logging

### **Bug 4 — Gemini responses unstructured**

Add stricter prompt:

```
Return ONLY valid JSON with keys: skills, experience, location, summary.
```

### **Bug 5 — Celery worker crashed**

Possible:

* Redis offline
* DB connection dropped

Monitor logs.

---

# ## **6. Final Launch Checklist**

### **User System**

* [ ] Save preferences
* [ ] Update preferences works
* [ ] User-channels M2M works

### **Channel Management**

* [ ] User adds channels
* [ ] Scraper loads channel list
* [ ] Scraper receives posts

### **Job Ingestion**

* [ ] Deduplication works
* [ ] Job stored correctly
* [ ] AI extraction triggered

### **AI Pipeline**

* [ ] Gemini working
* [ ] Ollama fallback works
* [ ] NLP fallback works
* [ ] Extraction saved to DB

### **Matching**

* [ ] Skills match
* [ ] Experience match
* [ ] Location match
* [ ] Combined score correct

### **Notifications**

* [ ] Delivered to the right user
* [ ] Format is clean
* [ ] Direct link works
* [ ] Log saved

### **Dashboard**

* [ ] Job reprocessing works
* [ ] Notification resend works
* [ ] Logs visible
* [ ] Scraper heartbeat visible

### **Deployment**

* [ ] Docker Compose is running
* [ ] Logs rotated
* [ ] HTTPS enabled
* [ ] API rate-limited
* [ ] Secrets safe

---

# ## **7. Ready for MVP Launch 🚀**

If every test passes, your system is ready to launch as MVP.

**Congratulations — your Telegram Job Hunter SaaS is now a fully working, scalable system that uses AI, LLMs, scraping, notifications, channel personalization, and microservices architecture.**

---

# 🎉 **End of Day 14 — MVP Completed**