# **1 — Functional Requirements & Non-Functional Requirements**

**Functional Requirements**

* **User Onboarding (via Telegram bot):** create user record, collect profile (skills, job titles, locations, notification preferences).  
* **Channel Management:** allow users to add/remove Telegram channels (by @username or t.me link); validate and persist channels; enqueue join requests for the scraper.  
* **Channel Scraping:** continuously monitor joined Telegram channels (Telethon worker) and capture new messages (text, media, message\_id, posted\_at, channel info).  
* **Job Extraction & Storage:** persist every captured post as a `JobPost` with raw content, extracted structured fields (title, skills, location, deadline), content hash, and direct post link.  
* **Matching Engine:** evaluate each JobPost against registered users’ preferences and compute a relevance score; support simple weighted keyword matching in MVP and a pluggable interface for future ML/embedding matchers.  
* **Notifications:** notify matched users via the Telegram bot immediately (or per user-configured cadence) including direct post link and full post text; support optional media forwarding or re-uploading.  
* **Deduplication & Forward Detection:** detect identical or near-duplicate posts (forwards) and avoid duplicate notifications.  
* **Admin Operations:** admin panel to manage channels, monitor scraper health/logs, view queued posts, and manage blacklisted channels or users.  
* **User Controls:** let users pause notifications, change preferences, view recent matched posts, and delete their account/data.

**Non-Functional Requirements**

* **Scalability:** support incremental growth — start with dozens of channels and scale to hundreds; design workers and queues so scraping/processing can be horizontally scaled.  
* **Reliability & Availability:** ensure scraper and bot have high uptime; handle Telegram `FloodWait` and transient failures gracefully with retries/backoff; deliver notifications within defined SLAs (e.g., \< 30s for instant mode under normal load).  
* **Performance & Latency:** matching and notification pipeline should process a new post end-to-end within target latency for instant mode (MVP target: ≤ 60 seconds).  
* **Security & Privacy:** protect Telegram API credentials and user session files; encrypt sensitive config and provide data deletion endpoints; minimize stored PII (store telegram\_id and preferences only).

* **Maintainability & Observability:** clear logs, metrics, sent/failure tracking; health endpoints for worker processes; easy admin debugging via Django admin.

* **Extensibility:** modular design so new matchers, notification channels (email/push), or source types (websites) can be added without major refactor.

* **Cost Efficiency:** prefer low-cost hosting options early (Railway/Render) and design to limit unnecessary operations (e.g., avoid re-processing duplicates).

Example: For the notification SLA, define instant mode as “notify within 60s 95% of the time” when system is under normal operating load (e.g., ≤ 50 new posts/minute).  
 Example: For privacy, provide `/delete_account` via the bot that removes user record, preferences, and notification history within 24 hours.  
 Example: For deduplication, generate `content_hash = sha256(normalized_text)` and skip saving/sending posts with identical hash; mark near-duplicates by trigram/embedding similarity for forwarding cases.

# **2 — Define the System’s Core Features (Main Use Cases)**

**Core Features (high-level)**

* **User Onboarding & Profile Management:** collect skills, job titles, preferred locations, notification cadence, and initial channel subscriptions via the Telegram bot.

* **Channel Add / Validate / Join:** allow users to add channels by username or link; backend validates format and enqueues Telethon worker to join and monitor the channel.

* **Continuous Channel Monitoring (Scraper):** Telethon worker(s) listen for new posts, extract raw message data (text, media, message\_id, posted\_at), and forward payloads to the backend.

* **Job Parsing & Enrichment:** parse raw messages to extract structured fields (title, company, skills, location, deadline) and produce normalized representations for matching and deduplication.

* **Matching Engine & Scoring:** evaluate each JobPost against users’ preferences, compute a relevance score, and produce a ranked list of matched users for each post.

* **Notification Delivery:** send matched users immediate Telegram messages (or scheduled digests), including direct post link, full description, extracted fields, and optional media forwarding.

* **Post Storage & User History:** persist JobPosts and Notification records for user browsing, auditing, and feedback (save/applied/ignored).

* **Admin & Observability:** admin UI for managing channels, viewing worker health, logs, metrics, and handling manual joins/unjoins or blacklisting.

**Main Use Cases (actors, triggers, success criteria)**

1. **UC-01: User Onboards via Bot**

   * *Actor:* Telegram user

   * *Trigger:* `/start` command

   * *Flow:* Bot prompts sequentially for skills, title, location, and notification cadence; backend creates/updates user.

   * *Success:* User record exists with preferences; bot confirms setup.

2. **UC-02: User Adds a Channel**

   * *Actor:* Telegram user

   * *Trigger:* `/addchannel @channel` or paste link

   * *Flow:* Bot validates input → calls backend → backend creates Channel if new and enqueues join task → Telethon joins channel.

   * *Success:* Channel saved and assigned to user; scraper begins monitoring.

3. **UC-03: Scraper Detects New Post**

   * *Actor:* Telethon worker

   * *Trigger:* New message event in joined channel

   * *Flow:* Worker captures message metadata, builds `post_link`, uploads media if any, POSTs `/api/new_post`.

   * *Success:* JobPost created in DB and processing task enqueued.

4. **UC-04: Post Processing & Matching**

   * *Actor:* Celery worker (matching service)

   * *Trigger:* job\_post created event

   * *Flow:* Normalize text, extract fields, dedupe, compute score against each interested user, create Notification records for matches above threshold.

   * *Success:* Notification records are created and queued for delivery.

5. **UC-05: Notify User**

   * *Actor:* Telegram bot (sender) via Celery task

   * *Trigger:* pending Notification record

   * *Flow:* Build message (title, link, description, extracted fields), attempt to forward media or include stored media links, send message to user, mark notification sent or failed.

   * *Success:* User receives message with direct link and post text.

6. **UC-06: User Browses History / Feedback**

   * *Actor:* Telegram user

   * *Trigger:* `/history` or UI action

   * *Flow:* Bot fetches saved matched posts for user and displays list; user marks saved/applied/irrelevant which feeds back into matching.

   * *Success:* User sees history and feedback is recorded.

7. **UC-07: Admin Manages Channels & System**

   * *Actor:* Admin (web or Django admin)

   * *Trigger:* Admin action

   * *Flow:* View channel join status, force rejoin/unjoin, view processing errors, blacklist channels, view metrics.

   * *Success:* Admin can maintain health and moderate channel sources.

**Examples / Scenarios**

* *Simple notification scenario:* A new "Backend Developer — Addis Ababa" post appears in @ethiopia\_jobs → Telethon posts to backend → matching finds 12 users with matching skills/location → 12 Telegram messages are sent with `https://t.me/ethiopia_jobs/1234`.

* *Duplicate prevention scenario:* The same post is forwarded to three channels; dedupe logic identifies identical `content_hash` and only one JobPost is stored; users subscribed to any of those channels still receive a single notification per unique post.

* *User feedback loop:* User marks a notification as "irrelevant" which lowers weight of the matching tokens for that user, improving personalization over time.

# **3 — High-Level Architecture (HLD)**

##    **Major System Components**

* **Telegram Bot Service**  
  * Handles all user interactions: onboarding, preference updates, channel submissions, history browsing.  
  * Sends notifications to users.  
  * Communicates with Backend API for all persistent operations.  
* **Backend API (Django REST Framework)**  
  * Central application logic.  
  * Exposes endpoints for: user profile, channels, new post ingestion, matching pipeline triggers, notifications.  
  * Stores users, channels, posts, and notification history.  
  * Provides admin and observability tools.  
* **Telegram Scraper (Telethon Worker)**  
  * Runs as an independent service.  
  * Authenticates via Telegram API.  
  * Joins channels dynamically when instructed.  
  * Listens to new messages in all joined channels.  
  * Pushes scraped raw posts into Backend API.

* **Matching & Processing Worker (Celery / RQ Worker)**

  * Processes JobPosts:  
    * normalize text  
    * extract structured fields  
    * compute content\_hash  
    * dedupe  
    * run AI matching cascade (Gemini → Ollama → NLP)  
  * Produces Notification tasks.
  * **Note**: Can be extracted as independent microservice if matching workload exceeds 10,000 jobs/day or requires independent scaling.    
* **Notification Delivery Worker**  
  * Sends actual Telegram messages to users via the bot.  
  * Handles retries, rate limit backoff, and failure tracking.  
* **Database Layer (PostgreSQL)**  
  * Stores all persistent entities:  
    * users, channels, job\_posts, notifications, error logs, admin flags.  
  * Provides indexing and search support (GIN indexes for text search).  
* **Object Storage (Optional for MVP)**  
  * Stores media from Telegram posts (images, PDFs).  
  * Alternatives:  
    * Cloud: AWS S3, DigitalOcean Spaces, Supabase Storage  
    * Local: server file storage (for MVP)  
* **Admin/Monitoring Interface**

  * Django Admin for data management.

  * Optional metrics dashboard (Prometheus \+ Grafana or simple Django views).

  * Logs for worker and scraper processes.

## **How Components Interact (High-Level Flow)**

#### 1\. User onboarding & preference setup

User opens bot → Bot sends user input to Backend → Backend stores user preferences.

#### 2\. User adds a Telegram channel

Bot → Backend (`POST /channels/add`) → DB saves the channel → Celery task instructs Telethon worker → Telethon joins channel → Telethon acknowledges join back to backend.

#### 3\. New post appears in a channel

Telethon Worker → detects new message → builds payload (text, media, post link) → sends to Backend (`POST /job_posts/new`) → Backend stores raw JobPost → Celery worker triggers processing pipeline.

#### 4\. JobPost Processing

Celery Worker:

* dedupe

* parse & extract structured fields

* run matching against users

* create Notification tasks

#### 5\. User Notification

Notification Worker reads tasks → uses Bot API to send messages → marks as sent or failed.

## **Component Diagram (Textual Form)**

               \[ User (Telegram) \]

                         |

                     interacts

                         |

                 \[ Telegram Bot \]

                         |

               \+---------+---------+

               |                   |

        store profile        receive matches

               |                   |

         \[ Backend API (Django) \] \<----------------+

               |                                   |

        write/read DB                              |

               |                                   |

        \[ PostgreSQL DB \]                          |

                                                   |

      Scraped posts → \[ Telethon Scraper \] → API \--+

                                                   |

                    Matching tasks → \[ Celery Workers \]

                                                   |

                                Notifications → \[ Bot Sender Worker \]

## Architecture Principles

* **Event-driven:** new posts trigger async processing → matching → notifications.

* **Decoupled pipelines:** scraper, processing, and notifications are separate services so each scales independently.

* **Bot is stateless:** all persistent logic lives in backend, ensuring resilience.

* **Extensible:** the same architecture can support website scraping in the future.

## **Sync/Async Architecture Patterns**

The JobPulse system combines synchronous and asynchronous components, requiring careful integration patterns:

### **Synchronous Components (Django)**

* **Django REST API**
  * Handles HTTP requests from Telethon scraper and Aiogram bot
  * Synchronous request/response cycle
  * ORM database operations (PostgreSQL)
  * Admin panel views

* **Celery Task Definitions**
  * Task definitions are sync (function signatures in Django)
  * Task execution happens in Celery worker processes

* **Database Layer**
  * PostgreSQL accessed via Django ORM (sync)
  * All database queries use sync patterns

### **Asynchronous Components**

* **Telethon Scraper**
  * Runs async event loop to monitor Telegram channels
  * Async message handlers
  * Makes sync HTTP POST to Django API when posting jobs

* **Aiogram Bot**
  * Async bot handlers for user commands
  * Async event loop for Telegram updates
  * Makes sync HTTP calls to Django API

### **Communication Bridges**

**Async → Sync**:
* Telethon/Aiogram use `httpx` or `requests` to POST to Django API
* Django receives standard HTTP requests (sync handler)
* Works seamlessly without async/sync conflict

**Sync → Async**:
* Django creates Celery tasks
* Celery worker executes task
* Task can trigger async operations (send Telegram message via Aiogram API)
* Aiogram bot uses `asyncio.run()` or dedicated event loop

**Shared Resources**:
* PostgreSQL database is accessed via sync Django ORM
* Redis used by Celery (sync client in Django)
* No direct async/sync database conflicts

### **Error Handling Across Boundaries**

* HTTP timeouts configured for Telethon/Aiogram → Django calls
* Celery retries handle transient failures
* Async services log errors to Django via HTTP error reporting endpoint
* Admin can monitor all services from Django admin panel

# **4 — Data Flow (User → System → DB → User)**

## 1\. User Registration & Preference Flow

**Trigger:** User starts interaction with the Telegram Bot (`/start`).

**Flow:**

1. **User → Telegram Bot**  
    User provides skills, job title, location, notification settings.

2. **Telegram Bot → Backend API**  
    Bot sends structured data to an endpoint like:  
    `POST /api/users/{telegram_id}/preferences`

3. **Backend API → Database (PostgreSQL)**  
    Backend validates and stores user profile data in `User` and `UserPreferences` tables.

4. **DB → Backend → Bot → User**  
    Bot confirms successful onboarding.

**Result:**  
 The user is now registered with preferences and ready to track channels.

## 2\. Add Channel Flow

**Trigger:** User sends `/addchannel @example_channel`.

**Flow:**

1. **User → Telegram Bot**  
    User submits a channel username or link.

2. **Bot → Backend API**  
    Bot calls:  
    `POST /api/channels/add` with `{ channel_name, user_id }`

3. **Backend → Database**  
    Channel is inserted or updated in `Channel` table, and added to user’s subscriptions.

4. **Backend → Celery Queue**  
    Celery task created to instruct the scraper to join the channel.

5. **Celery Worker → Telethon Scraper**  
    Scraper attempts to join and monitor the channel.

6. **Scraper → Backend API**  
    Scraper confirms join status (success/error).

7. **Backend → Bot → User**  
    User receives confirmation.

## 3\. Scraping & Post Ingestion Flow

**Trigger:** A new message is posted in a tracked Telegram channel.

**Flow:**

1. **Telethon Scraper detects new message**  
    Captures text, media, message\_id, timestamp, channel name.

2. **Scraper → Backend API**  
    Sends payload to:  
    `POST /api/job_posts/new`

3. **Backend API → Database**  
    Stores raw post in `JobPost (raw_text, channel_id, post_link, media, content_hash)`.

4. **Backend → Celery Queue**  
    Enqueues post-processing job.

## **4\. Post Processing & Matching Flow**

**Trigger:** New `JobPost` created.

**Flow:**

1. **Celery Worker → Database**  
    Loads JobPost from DB.

2. **Worker processes the post:**

   * Normalize text

   * Extract structured fields

   * Compute match score with each subscribed user

   * Create Notification entries

3. **Worker → Database**  
    Writes structured data to `JobPostExtracted` and `Notification` tables.

4. **Worker → Notification Queue**  
    Enqueues notification delivery tasks.

## 5\. Notification Delivery Flow

**Trigger:** Notification task ready.

**Flow:**

1. **Notification Worker → Telegram Bot API**  
    Sends formatted message including:

   * Job title

   * Full description

   * Direct post link (`t.me/channel/123`)

2. **Bot API → User**  
    User receives the notification instantly.

3. **Worker → Database**  
    Marks notification as `sent`, or `failed` with retry logic.

## **End-to-End Summary Example**

User adds skills → stored in DB → adds channels → scraper joins → new job posted → scraper captures → backend stores → worker processes/extracts → matching engine finds relevant users → notification worker sends messages → user gets real-time alert.

# **5 — Database Design (Tables, Fields, Relationships)**

## Database Design

### 1\. Users Table

Stores core user identity for Telegram.

**Table: `users`**

| Field | Type | Notes |
| ----- | ----- | ----- |
| id | UUID / BIGINT | PK |
| telegram\_id | BIGINT | Unique identifier from Telegram |
| username | VARCHAR | Optional |
| full\_name | VARCHAR | Optional |
| created\_at | TIMESTAMP |  |
| updated\_at | TIMESTAMP |  |

**Relationships:**

* 1-to-1 with `user_preferences`

* 1-to-many with `user_channels`

* 1-to-many with `notifications`

### 2\. User Preferences Table

Stores detailed profile & matching preferences.

**Table: `user_preferences`**

| Field | Type | Notes |
| ----- | ----- | ----- |
| id | UUID | PK |
| user\_id | FK(users.id) | Unique |
| skills | TEXT\[\] | List of skills |
| job\_titles | TEXT\[\] | List of roles |
| locations | TEXT\[\] | Preferred locations |
| years\_of\_experience | INT | **Added per your request** |
| notification\_mode | ENUM('instant','daily\_digest') |  |
| keywords | TEXT\[\] | Additional matching filters |
| created\_at | TIMESTAMP |  |
| updated\_at | TIMESTAMP |  |

**Notes:**

* `years_of_experience` influences scoring (more matches for appropriate seniority posts)

### 3\. Channels Table

Tracks Telegram channels users want to monitor.

**Table: `channels`**

| Field | Type | Notes |
| ----- | ----- | ----- |
| id | UUID | PK |
| name | VARCHAR | e.g., @ethiojobs |
| link | VARCHAR | t.me link |
| telegram\_channel\_id | BIGINT | From Telegram API |
| is\_active | BOOLEAN | If scraper successfully joined |
| added\_by\_user\_id | FK(users.id) | First user who added it |
| created\_at | TIMESTAMP |  |
| updated\_at | TIMESTAMP |  |

**Relationships:**

* Many-to-many with users via `user_channels`

### 4\. User Channels Table

Which user follows which channel.

**Table: `user_channels`**

| Field | Type | Notes |
| ----- | ----- | ----- |
| id | UUID | PK |
| user\_id | FK(users.id) |  |
| channel\_id | FK(channels.id) |  |
| created\_at | TIMESTAMP |  |

**Notes:**

* Supports users choosing different sets of channels.

### 5\. Job Posts Table (Raw Scraped Data)

Stores raw Telegram messages.

**Table: `job_posts`**

| Field | Type | Notes |
| ----- | ----- | ----- |
| id | UUID | PK |
| channel\_id | FK(channels.id) |  |
| message\_id | BIGINT | Telegram post ID |
| raw\_text | TEXT | Original content |
| media\_url | TEXT | Optional stored media |
| post\_link | VARCHAR | t.me/channel/message |
| content\_hash | TEXT | For deduplication |
| posted\_at | TIMESTAMP | Original timestamp |
| created\_at | TIMESTAMP | Ingestion time |

**Indexes:**

* `content_hash` for dedupe

* `(channel_id, message_id)` unique index

### **6\. Job Post Extracted Table (Structured Data)**

Stores parsed info from raw post.

**Table: `job_posts_extracted`**

| Field | Type | Notes |
| ----- | ----- | ----- |
| id | UUID | PK |
| job\_post\_id | FK(job\_posts.id) | 1-to-1 |
| title | VARCHAR | Parsed job title |
| company | VARCHAR | Optional |
| skills | TEXT\[\] | Extracted skills |
| location | VARCHAR | Extracted location |
| seniority | VARCHAR | junior/mid/senior |
| deadline | DATE | Optional |
| experience\_required | INT | If parsed |
| normalized\_text | TEXT | Cleaned text for matching |
| created\_at | TIMESTAMP |  |

**Notes:**

* `experience_required` will be matched with `years_of_experience` for scoring.

### **7\. Notifications Table**

Stores who should be notified about which post, including AI match metadata.

**Table: `notifications`**

| Field | Type | Notes |
| ----- | ----- | ----- |
| id | UUID | PK |
| user\_id | FK(users.id) |  |
| job\_post\_id | FK(job\_posts.id) |  |
| score | FLOAT | Match score (0-100) |
| match\_source | VARCHAR(20) | **'gemini', 'ollama', or 'nlp'** (AI service used) ⭐ |
| status | ENUM('pending','sent','failed') |  |
| sent\_at | TIMESTAMP |  |
| created\_at | TIMESTAMP |  |

**Indexes:**

* `(user_id, job_post_id)` unique to avoid duplicates
* `match_source` for analytics queries

**Notes:**

* `match_source` tracks which AI service generated the match:
  * `'gemini'` - Matched via Google Gemini API (primary)
  * `'ollama'` - Matched via local Ollama LLM (fallback)
  * `'nlp'` - Matched via NLP/TF-IDF engine (final fallback)
* Enables analytics: track AI service performance and costs
* Useful for debugging: identify when fallbacks are triggered

### **8\. System Logs / Error Tracking**

Optional but recommended.

**Table: `scraper_errors`**

| Field | Type | Notes |
| ----- | ----- | ----- |
| id | UUID | PK |
| channel\_id | FK(channels.id) |  |
| error\_message | TEXT |  |
| traceback | TEXT |  |
| occurred\_at | TIMESTAMP |  |

### **9\. AI Matching Metrics Table** ⭐

Tracks AI service performance and cascade behavior.

**Table: `ai_matching_metrics`**

| Field | Type | Notes |
| ----- | ----- | ----- |
| id | UUID | PK |
| job\_post\_id | FK(job\_posts.id) |  |
| service\_tried | VARCHAR(20) | 'gemini', 'ollama', 'nlp' |
| success | BOOLEAN | True if service responded successfully |
| response\_time\_ms | INT | Latency in milliseconds |
| error\_message | TEXT | Error details if failed |
| created\_at | TIMESTAMP |  |

**Indexes:**

* `job_post_id` for job-level analysis
* `(service_tried, success)` for service performance queries
* `created_at` for time-series analytics

**Use Cases:**

* **Performance Monitoring**: Track average response times per service
  * Example: "Gemini avg: 1.2s, Ollama avg: 7.5s, NLP avg: 0.08s"
* **Success Rate Analysis**: Monitor when fallbacks trigger
  * Example: "Gemini succeeded 95%, fell back to Ollama 4%, NLP 1%"
* **Cost Tracking**: Calculate Gemini API usage
  * Example: "1,000 Gemini calls this month = $0.10"
* **Debugging**: Identify systematic failures
  * Example: "Ollama down between 2-3pm daily"
* **Optimization**: Find bottlenecks in cascade
  * Example: "Jobs with >500 word descriptions timeout on Gemini"

## **Entity Relationship Overview (Short Text Diagram)**

User 1---1 UserPreferences

User 1---\* UserChannels \*---1 Channel

Channel 1---\* JobPosts 1---1 JobPostsExtracted

JobPosts 1---\* Notifications \*---1 User

JobPosts 1---\* AIMatchingMetrics (tracking)

## **How AI Cascade Fits the Database**

### **Matching Flow with Database**

1. **New JobPost created** → Triggers matching pipeline
2. **AI Cascade attempts** (Gemini → Ollama → NLP):
   - Each attempt logged to `ai_matching_metrics`
   - Records: service tried, success/failure, latency, errors
3. **Successful matches** → Create `notifications` records:
   - Includes `score` from AI service
   - Includes `match_source` ('gemini', 'ollama', or 'nlp')
4. **Analytics queries** → Use `ai_matching_metrics`:
   - Service performance: `SELECT AVG(response_time_ms) GROUP BY service_tried`
   - Success rates: `SELECT service_tried, COUNT(*) WHERE success = true`
   - Cost estimation: `SELECT COUNT(*) WHERE service_tried = 'gemini'`

### **How Years of Experience Fits the System**

* Used during **matching**:  
   `abs(experience_required - user.years_of_experience)` affects score

* Used for **filtering irrelevant jobs**:  
   If “senior” detected and user is 0–1 years → lower score or skip

* Helps personalize notifications

* Improves long-term recommendations (future ML)

* **AI services** use this field in prompts for semantic matching

--- End of Step 5 —

# **🔧 6\. Detailed Low-Level Design (LLD)**

Below is a module-by-module breakdown of the system, how each part works internally, and how they interact. This is fully Google-Docs-ready.

## **A. User Management Module**

### **Responsibilities**

* Handle user registration (via Telegram bot ).

* Store profile: skills, job title, years of experience, preferred location, keywords.

* Manage the list of **Telegram channels each user added/selected**.

* Authenticate users (Telegram ID is the unique identity).

### **Components**

* **UserService**

  * Create/update user profile

  * Validates skills, experiences, preferences

* **UserPreferenceService**

  * Saves user-selected channels

  * Ensures matching logic uses *only* channels associated with the user

### **Key Internal Logic**

* Users may add channels dynamically via bot commands:  
   `/add_channel t.me/example_channel`

* System verifies channel is valid and scrappable.

## **B. Channel Management Module**

### **Responsibilities**

* Store the list of Telegram channels the system scrapes.

* Track channel metadata: title, link, last scraped message ID.

* Maintain relationships: **user ↔ selected channels**.

### **Components**

* **ChannelRegistryService**

  * Adds new channels

  * Prevents duplicates

* **ChannelScrapeCoordinator**

  * Tracks scrape schedule

  * Dispatches scrapers

### **Internal Logic**

* If user adds a new channel, the system:

  1. Registers it

  2. Schedules scraping

  3. Links it to that user

## **C. Scraper Module (Telegram Integration)**

### **Responsibilities**

* Scrape Telegram channels using:

  * Telethon (Python async client for scraping)

  * Aiogram (Python async bot for user interactions)

* Extract job information:

  * Job title

  * Company

  * Description

  * Salary

  * Location

  * **Direct link to the message**

* Store extracted data in DB.

### **Components**

* **TelegramClientService**

  * Handles API connection & authentication

* **MessageParser**

  * Extracts job details using regex & NLP heuristics

* **DeduplicationEngine**

  * Prevents storing the same post twice

### **Internal Logic**

* For each channel:

  * Fetch new messages since last scrape

  * Parse job content

  * Save job posting

  * Save **message link** using message ID

  * Update last\_scraped\_id

## **D. Job Matching Engine (AI-Powered Cascade)**

### **Responsibilities**

* Match users with job posts using an intelligent AI cascade pipeline:

  * **Primary**: Google Gemini API for semantic job-user matching

  * **Secondary**: Ollama Local LLM (Llama 3 / Mistral) as zero-cost fallback

  * **Final Fallback**: NLP engine (TF-IDF, fuzzy matching, regex)

* Filter matches by user preferences:

  * Skills

  * Job title

  * Preferred location

  * Years of experience

  * Keywords

  * **Channels user selected** (critical filter)

### **Components**

* **MatchOrchestrator**

  * Coordinates the AI cascade flow

  * Handles fallback logic when services fail

  * Ensures user-channel filtering is applied

* **GeminiMatchingService**

  * Primary AI matcher using Google Gemini API

  * Performs semantic similarity between job description and user profile

  * Returns relevance score (0-100)

* **OllamaMatchingService**

  * Secondary AI matcher using local Ollama LLM

  * Zero-cost fallback when Gemini unavailable or rate-limited

  * Runs Llama 3 or Mistral models locally

* **NLPMatchingEngine**

  * Final fallback using traditional NLP techniques

  * TF-IDF vectorization for text similarity

  * Fuzzy string matching for skills/titles

  * Regex-based experience extraction

  * Always available (100% uptime)

* **UserMatchFilter**

  * Critical pre-filter: only considers jobs from user's selected channels

  * Applies hard filters (location, experience range)

* **ExperienceMatcher**

  * Extracts required experience from job posts

  * Compares with user's years of experience

  * Adjusts score based on match quality

### **Internal Logic (AI Cascade Pipeline)**

```
# Step 1: Pre-filter by user's channel subscriptions
candidate_jobs = Jobs WHERE channel_id IN user.selected_channel_ids

# Step 2: For each candidate job
FOR job IN candidate_jobs:
  
  # Step 3: Try Gemini API first (primary)
  TRY:
    score = GeminiMatchingService.match(job, user_profile)
    source = "gemini"
  
  # Step 4: Fallback to Ollama if Gemini fails
  EXCEPT (APIError, RateLimitError, TimeoutError):
    TRY:
      score = OllamaMatchingService.match(job, user_profile)
      source = "ollama"
    
    # Step 5: Final fallback to NLP
    EXCEPT (ServiceUnavailable, ModelError):
      score = NLPMatchingEngine.match(job, user_profile)
      source = "nlp"
  
  # Step 6: Apply experience and location adjustments
  score = score * experience_match_factor(job, user)
  score = score * location_match_factor(job, user)
  
  # Step 7: If score exceeds threshold, create notification
  IF score > threshold:
    Notification.create(user, job, score, source)
```

### **Matching Algorithm Details**

**Gemini Semantic Matching** (Primary):
* Sends structured prompt with job description and user profile
* Gemini returns relevance score and reasoning
* Fast (< 2 seconds per match)
* Cost: ~$0.0001 per match

**Ollama Local Matching** (Secondary):
* Uses locally hosted Llama 3 or Mistral model
* No external API calls, zero cost
* Slower (5-10 seconds per match)
* Requires 4GB RAM

**NLP Fallback Matching** (Tertiary):
* TF-IDF cosine similarity for text matching
* Keyword overlap scoring: `overlap(job.skills, user.skills) / total_skills`
* Experience matching: `abs(required_years - user_years) < 2`
* Location exact or fuzzy match
* Ultra-fast (< 100ms per match)
* Always available

### **Benefits of This Architecture**

✅ **Accuracy**: Gemini provides state-of-the-art semantic understanding  
✅ **Cost efficiency**: Ollama handles overflow at zero cost  
✅ **100% uptime**: NLP ensures system never fails to match  
✅ **Scalability**: Easy to add more fallback layers or swap AI providers  
✅ **User privacy**: Follows user's channel selections strictly  

## **E. Notification Module (Telegram Bot)**

### **Responsibilities**

* Notify user immediately when matching job is found.

* Send formatted job details:

  * Title

  * Company

  * Location

  * Requirements

  * **Direct link to the Telegram post**

### **Components**

* **TelegramBotService**

  * Sends real-time messages

  * Handles bot commands

* **NotificationDispatcher**

  * Pushes notifications

  * Ensures one user only receives alerts from their own channels

### **Internal Logic**

* Job matched → Push notification to user:

📌 Job Found\!

Job: Junior Backend Developer

Experience: 1–2 years

From Channel: @AddisJobs

Link: https://t.me/addis\_jobs/12345

## **F. Admin Dashboard Module (Optional for later)**

### **Responsibilities**

* Manage channels

* Monitor scraper performance

* Analyze job trends

### **Components**

* **AnalyticsService**

  * Counts jobs per channel

  * System health monitoring

## **G. Scheduler Module**

### **Responsibilities**

* Periodically trigger:

  * Scraping

  * Matching

  * Data cleanup

### **Tools**

* Celery (Django)

* Django-crontab (simple MVP)

### **Behavior**

* Scrape every 1–5 minutes depending on load.

* Matching runs right after scraping.

## **H. Security Module**

### **Responsibilities**

* Prevent unauthorized access

* Sanitize channel inputs

* Manage Telegram API token securely

* Ensure AI service resilience and graceful degradation

### **Included Controls**

* Rate-limiting

* Input validation

* Secure secret storage

### **AI Service Resilience**

**Gemini API Protection**:
* Rate limit monitoring (60 requests/min free tier)
* Automatic fallback to Ollama on rate limit errors
* Retry logic with exponential backoff
* API key rotation support

**Ollama Health Checks**:
* Monitor local service availability
* Restart on failures
* Resource usage monitoring (RAM, CPU)
* Fallback to NLP if Ollama unresponsive

**Graceful Degradation**:
* System always functions via NLP fallback
* Admin notifications when AI services degraded
* Matching quality metrics logged per source (Gemini/Ollama/NLP)
* Auto-recovery attempts before permanent fallback

**Error Tracking**:
* All AI failures logged to database
* Sentry integration for real-time alerts
* Daily reports on AI service health
* User transparency: notifications include match source

## **Summary Diagram (Text Format)**

User (Telegram Bot)

      ↓

User Service  ←→  User Preferences (skills, experience, channels)

      ↓

Channel Registry ←→ Scheduler → Scraper → Message Parser → DB

      ↓

Job Matching Engine → Notification Dispatcher → Telegram Bot → User

### **NB Reapplied Clearly:**

✔ Users receive notifications **only from channels they personally added/selected**.  
 ✔ Matching engine filters jobs strictly by `user.selected_channel_ids`.

**\--- End of Step 6** 

# **7\. Technology Stack & Infrastructure Recommendations**

## **A. Backend (Core Application)**

### **Recommended Framework**

* **Django (Python)** — chosen for:

  * Rapid development

  * Built-in admin panel

  * Strong ORM

  * Easy integration with Celery for scheduled scraping

  * Mature ecosystem

### **Key Backend Packages**

* **Telethon** → For scraping Telegram channels (async)

* **Aiogram** → For bot interactions and notifications (async)

* **Celery** → For scheduling scraping \+ matching tasks

* **Redis** → Celery message broker

* **PostgreSQL** → Primary database for users, jobs, channels

### **Why Django for this project**

* Handles complex models (Users → Channels → Jobs → Matches)

* Easy API creation with Django REST Framework (future mobile/Web app)

* Strong ecosystem for background tasks and admin panel

## **B. Frontend (Optional MVP)**

For MVP, all user interaction happens inside **Telegram Bot**.  
 No frontend is necessary.

If  later add a dashboard:

* **React.js** (optional)

* **Django REST Framework** as API backend

## **C. Telegram Integration**

### **Tools**

* **Telegram Bot API (via Aiogram)** for sending alerts and user interactions

* **Telegram Client API (Telethon)** for channel scraping (required for reading messages)

### **Why both APIs**

* **Bot API limitations**: Cannot read channel messages or join channels programmatically

* **Telethon capability**: Can read messages, join channels, and monitor updates

This combination is the industry standard for Telegram-based systems.

### **Why Aiogram for Bot**

* **Async-native**: Built on asyncio, perfectly matches Telethon's async architecture

* **Modern API**: Clean, intuitive interface with excellent typing support

* **Performance**: Non-blocking operations, handles high throughput efficiently

* **Active development**: Regular updates, strong community support

* **Integration**: Seamlessly works with Django via Celery task queue for notifications

### **Architecture Integration**

**Telethon Scraper** (Async Service):
* Runs independent event loop
* Monitors channels for new messages
* POSTs to Django REST API when job found

**Aiogram Bot** (Async Service):
* Handles user commands (`/start`, `/addchannel`, `/history`)
* Calls Django REST API for data operations
* Triggered by Celery tasks for sending notifications

**Django Backend** (Sync Service):
* Receives HTTP requests from both Telethon and Aiogram
* Orchestrates workflow via Celery
* Manages database operations

## **D. Job Extraction & NLP (Optional but Recommended)**

### **Libraries**

* **spaCy** or **NLTK** for extracting:

  * experience years

  * job title

  * location

  * salary

  * required skills

### **Why NLP matters**

Channel posts are unstructured; NLP helps improve match accuracy.

## **E. Storage Layer**

### **Primary Database**

* **PostgreSQL**

  * Good for relational data

  * Handles full-text search (for job keywords)

### **Cache Layer**

* **Redis**

  * Used by Celery

  * Can also store:

    * recently scraped messages

    * caching heavy queries

### **File Storage (Optional)**

If you want to store raw post images:

* **AWS S3**

* **DigitalOcean Spaces**

* or **Local storage** during MVP

## **F. Background Processing**

### **Celery \+ Redis**

Handles:

* Channel scraping every X minutes

* Job parsing

* Matching algorithm

* Sending batched notifications

### **Why Celery**

Scraping is slow → Celery makes the system scalable.

## **G. Deployment Infrastructure**

### **MVP Deployment Requirements**

**Minimum System Requirements**:
* **RAM**: 4GB (required for Ollama LLM)
* **CPU**: 2 cores minimum, 4 cores recommended
* **Storage**: 50GB SSD
* **Bandwidth**: Unmetered or 1TB+

**Why 4GB RAM is critical**:
* Ollama with Llama 3 or Mistral requires minimum 4GB
* Django + PostgreSQL + Redis: ~500MB
* Telethon + Aiogram services: ~300MB
* OS overhead: ~500MB
* **Total**: ~5.3GB (4GB is minimum, 8GB recommended for production)

### **Deployment Options**

#### **Option 1: Self-Hosted VPS (Recommended for MVP)**

**Provider Options**:
* **DigitalOcean Droplet**: $12/month (4GB RAM, 2 vCPU)
* **Hetzner Cloud**: €8/month (~$9, 4GB RAM, 2 vCPU)
* **Vultr**: $12/month (4GB RAM, 2 vCPU)

**Benefits**:
* Full control over environment
* Can run Ollama without restrictions
* Docker Compose for easy orchestration
* SSH access for debugging

**Deployment Stack** (Docker Compose):
```yaml
services:
  - django_api      # Backend API + Admin
  - celery_worker   # Background task processing
  - celery_beat     # Scheduled task orchestration
  - telethon        # Telegram channel scraper
  - aiogram_bot     # Telegram bot service
  - postgres        # Primary database
  - redis           # Celery message broker
  - ollama          # Local LLM service
```

#### **Option 2: Managed Platform**

**Provider Options**:
* **Railway**: $15-20/month (with 4GB+ resources)
* **Render**: $15-25/month (4GB instance)
* **DigitalOcean App Platform**: $12-20/month
 
**Benefits**:
* Auto-deploy from GitHub
* Built-in monitoring
* Managed database backups
* Easy scaling

**Limitations**:
* Ollama may face memory constraints
* Less flexibility than VPS
* Higher cost for equivalent resources

### **Recommended MVP Approach**

**Phase 1 (Development)**:
* Use DigitalOcean Droplet ($12/month)
* Deploy via Docker Compose
* Single-server architecture
* Ollama runs locally

**Phase 2 (Production Growth)**:
* Upgrade to 8GB RAM droplet ($24/month)
* Add monitoring (Prometheus + Grafana)
* Implement auto-backups
* Consider separating database

**Phase 3 (Scale)**:
* Extract matching engine to separate service
* Use managed PostgreSQL
* Add load balancer
* Multiple Celery workers

### **Cost Breakdown (MVP)**

| Service | Provider | Monthly Cost |
| ----- | ----- | ----- |
| **VPS (4GB RAM)** | DigitalOcean | $12 |
| **Domain Name** | Namecheap | $1 |
| **Gemini API** | Google Cloud | $0-5 (free tier generous) |
| **Backups** | DigitalOcean | $0 (included) |
| **Total** |  | **~$13-18/month** |

**Note**: Ollama is zero-cost as it runs locally. Gemini free tier provides 60 requests/minute, sufficient for MVP.

### **Why Docker**

* Easy scaling

* Easy deployment

* Local development matches production

## **H. System Scaling Strategy**

### **Scale Horizontally**

* Add more Celery workers as you monitor more channels

### **Scale Data**

* Add PostgreSQL indexing for:

  * Channel ID

  * Keywords

  * Experience

  * Skills

### **Scale Scraping**

* Use multiple Telegram client sessions

* Use rotating sessions to avoid rate limits

## **I. Security Recommendations**

* Store API keys in environment variables

* Validate any channel link users enter

* Restrict allowed domains for channel URLs

* Do not expose internal APIs publicly without auth

* Set rate limits on bot commands

## **J. Monitoring & Logging**

### **Tools**

* **Prometheus \+ Grafana** (optional)

* **Sentry** — for exception tracking

* **Django admin** — for browsing data

### **Monitor**

* Scrape success rate

* API errors

* Message parsing errors

* Celery worker failures

# **Summary**

Your final stack for the Telegram Job Alert System:

| Layer | Tools |
| ----- | ----- |
| **Backend** | Django, Django REST Framework |
| **Scraping** | Telethon (async) |
| **Bot** | Aiogram (async) |
| **AI Matching** | Google Gemini API (primary) |
| **Local LLM** | Ollama (Llama 3 / Mistral) |
| **NLP Fallback** | spaCy/NLTK + TF-IDF |
| **Background Jobs** | Celery \+ Redis |
| **Database** | PostgreSQL |
| **Deployment** | Docker Compose on VPS (4GB+ RAM) |
| **Hosting** | DigitalOcean / Hetzner / Vultr |
| **Monitoring** | Sentry, Prometheus (optional) |

---

**--- End of Step 7 — System Design Completed ✅ ---**

## **JobPulse Project Folder Structure (Microservices-Ready Monorepo)**

```
jobPulse/
│
├── .env                             # Environment variables
├── docker-compose.yml               # Multi-service orchestration
├── README.md                        # Project documentation
│
├── backend/                         # Django Backend (Monolithic Core)
│   ├── manage.py
│   ├── requirements.txt
│   │
│   ├── core/                        # Django project settings
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── base.py              # Base settings
│   │   │   ├── local.py             # Development settings
│   │   │   └── production.py        # Production settings
│   │   ├── urls.py                  # Root URL config
│   │   ├── wsgi.py                  # WSGI entry
│   │   ├── asgi.py                  # ASGI entry
│   │   └── celery.py                # Celery config
│   │
│   ├── apps/                        # Django applications
│   │   ├── users/
│   │   │   ├── models.py            # User, UserPreferences
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   ├── services.py          # Business logic
│   │   │   ├── selectors.py         # Query helpers
│   │   │   └── urls.py
│   │   │
│   │   ├── channels/
│   │   │   ├── models.py            # Channel, UserChannels
│   │   │   ├── views.py
│   │   │   ├── tasks.py             # Celery tasks
│   │   │   └── urls.py
│   │   │
│   │   ├── jobs/
│   │   │   ├── models.py            # JobPost, JobPostExtracted
│   │   │   ├── services.py          # AI pipeline orchestration ⭐
│   │   │   ├── tasks.py             # Matching & processing tasks
│   │   │   ├── selectors.py         # Job queries
│   │   │   └── utils/
│   │   │       ├── normalize.py     # Text normalization
│   │   │       ├── experience_parser.py
│   │   │       └── skill_parser.py
│   │   │
│   │   └── notifications/
│   │       ├── models.py            # Notification
│   │       ├── services.py          # Notification logic
│   │       ├── tasks.py             # Delivery tasks
│   │       └── urls.py
│   │
│   ├── api/                         # REST API Layer
│   │   ├── root_router.py           # API router aggregation
│   │   ├── urls.py                  # API URL patterns
│   │   └── endpoints/
│   │       ├── user_api.py
│   │       ├── channel_api.py
│   │       ├── job_api.py
│   │       └── notification_api.py
│   │
│   ├── shared/                      # Shared utilities ⭐
│   │   ├── utils/
│   │   │   ├── ai_request.py        # Gemini API client
│   │   │   ├── ollama_client.py     # Ollama LLM client
│   │   │   ├── nlp_fallback.py      # TF-IDF/fuzzy NLP matcher
│   │   │   ├── experience_extractor.py
│   │   │   ├── skill_extractor.py
│   │   │   └── logger.py            # Logging utilities
│   │   │
│   │   └── schemas/                 # Shared Pydantic schemas
│   │       └── ...
│   │
│   ├── static/                      # Static files (CSS, JS)
│   ├── media/                       # Uploaded media files
│   └── logs/                        # Application logs
│
├── scraper/                         # Telethon Scraper Service (Async) ⭐
│   ├── main.py                      # Telethon client entry point
│   ├── requirements.txt             # Service-specific dependencies
│   ├── Dockerfile                   # Optional: separate container
│   ├── services/
│   │   └── channel_monitor.py       # Channel monitoring logic
│   ├── utils/
│   │   └── message_parser.py        # Parse Telegram messages
│   └── session/                     # Telethon session files
│
├── bot/                             # Aiogram Bot Service (Async) ⭐
│   ├── main.py                      # Aiogram bot entry point
│   ├── requirements.txt             # Service-specific dependencies
│   ├── Dockerfile                   # Optional: separate container
│   ├── handlers/
│   │   ├── start.py                 # /start command
│   │   ├── channels.py              # /addchannel, /removechannel
│   │   └── history.py               # /history command
│   ├── keyboards/                   # Telegram inline keyboards
│   └── services/
│       └── api_client.py            # Django API client
│
├── matching_engine/                 # AI Matching Service (Optional Microservice) ⭐
│   ├── main.py                      # Matching service entry
│   ├── requirements.txt             # AI/ML dependencies
│   ├── Dockerfile                   # Optional: separate container
│   ├── services/
│   │   ├── gemini_matcher.py        # Gemini API integration
│   │   ├── ollama_matcher.py        # Ollama integration
│   │   └── nlp_matcher.py           # NLP fallback
│   └── utils/
│       └── score_calculator.py      # Score computation
│
└── worker/                          # Celery Worker (Background Tasks)
    ├── tasks.py                     # Celery task definitions
    └── Dockerfile                   # Optional: separate worker container
```

---

## **Architecture Highlights**

### **Microservices-Ready Monorepo Pattern**

This structure provides the **best of both worlds**:

✅ **Monolithic Simplicity** (MVP Phase):
- Single `docker-compose.yml` orchestrates all services
- Shared database (PostgreSQL) for all components
- Easy local development and debugging

✅ **Microservices Flexibility** (Scale Phase):
- Each service (`scraper/`, `bot/`, `matching_engine/`) is **independently deployable**
- Separate `Dockerfile` for each service (optional)
- Can scale horizontally (multiple instances per service)
- Can split database later if needed

---

## **Key Components Explained**

### **📁 `backend/` - Django Monolithic Core**

The heart of the system:
- Handles all persistent data (PostgreSQL via Django ORM)
- Exposes REST API for async services
- Runs Django admin panel
- Orchestrates Celery tasks

**Critical Files**:
- `apps/jobs/services.py` → **AI matching cascade orchestrator**
- `core/celery.py` → Celery configuration
- `api/endpoints/` → REST API for scraper/bot communication

---

### **📁 `shared/utils/` - AI Utilities** ⭐

Already implemented! Contains the AI cascade pipeline:

```python
# backend/shared/utils/ai_request.py
class GeminiMatcher:
    """Primary AI matcher using Google Gemini"""
    
# backend/shared/utils/ollama_client.py  
class OllamaMatcher:
    """Zero-cost local LLM fallback"""
    
# backend/shared/utils/nlp_fallback.py
class NLPMatcher:
    """Always-available TF-IDF matcher"""
```

These are called by `apps/jobs/services.py` in cascade order.

---

### **📁 `scraper/` - Telethon Service** ⭐

**Independent async service** that:
- Monitors Telegram channels using Telethon
- Captures new job posts
- POSTs to Django API (`/api/job_posts/new`)

**Why separate folder?**
- Different async execution model (event loop)
- Can run on separate server/container
- Independent scaling (multiple scraper instances)

---

### **📁 `bot/` - Aiogram Bot Service** ⭐

**Independent async service** that:
- Handles user interactions via Aiogram
- Processes `/start`, `/addchannel`, `/history` commands
- Calls Django REST API for data operations

**Why separate folder?**
- Async bot framework (Aiogram)
- Can restart without affecting Django
- Separate deployment for high-traffic bots

---

### **📁 `matching_engine/` - Optional AI Microservice** ⭐

**Optional separate service** for AI-heavy workloads:
- Contains Gemini, Ollama, NLP matchers
- Can be extracted from Django when scaling
- Useful if matching workload > 10,000 jobs/day

**Current state**: Logic is in `backend/shared/utils/` (monolithic)  
**Future state**: Extract to independent FastAPI service when needed

---

### **📁 `worker/` - Celery Worker**

Background task processor:
- Executes Celery tasks defined in Django apps
- Handles matching, notifications, extraction
- Can scale horizontally (multiple worker instances)

---

## **Deployment Options**

### **Option 1: Single Server (MVP - Current)**

All services in one `docker-compose.yml`:
```yaml
services:
  - postgres        # Database
  - redis           # Celery broker
  - django          # Backend API
  - celery_worker   # Background tasks
  - scraper         # Telethon service
  - bot             # Aiogram service
  - ollama          # Local LLM
```

**Cost**: $12-18/month (4GB VPS)

---

### **Option 2: Distributed (Scale Phase)**

Each service on separate containers/servers:
- `backend/` → Cloud Run / Heroku
- `scraper/` → Independent server (24/7 monitoring)
- `bot/` → Independent server (high availability)
- `matching_engine/` → GPU server (if using heavy models)

**Cost**: Scales with traffic

---

## **Advantages of Your Structure**

1. **🔧 Service Independence**: Each service can restart/deploy independently
2. **📦 Docker-Friendly**: Easy to containerize each service separately
3. **⚡ Horizontal Scaling**: Multiple instances of scraper/bot/worker
4. **🛠️ Team Collaboration**: Different teams can own different services
5. **🚀 Production-Ready**: Already follows microservices best practices

---

**This structure is enterprise-grade and superior to a flat Django structure!** ✨

---

## **Recent Updates to This Design**

This design document has been updated to reflect the following enhancements:

✅ **AI-First Matching**: Integrated Gemini → Ollama → NLP cascade pipeline  
✅ **Modern Bot Library**: Specified Aiogram for async-native bot implementation  
✅ **Sync/Async Patterns**: Documented integration between Django and async services  
✅ **Realistic Infrastructure**: Corrected requirements (4GB RAM) and costs ($12-18/month MVP)  
✅ **Complete Folder Structure**: Added AI utilities and service organization  
✅ **Error Resilience**: Documented AI service fallback and monitoring strategies

All features are production-ready and designed for incremental scaling from MVP to enterprise.

---

**End of JobPulse System Design Document**
