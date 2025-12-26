# Notification Pipeline Testing Guide

Follow these steps to verify the end-to-end flow of the notification system.

## 1. Environment Preparation

Ensure all services are running and the bot is accessible.

```bash
# Rebuild and restart services to apply changes
docker-compose up -d --build

# Check status
docker-compose ps
```

## 2. Manual Verification Flow

### Step A: Setup a Match
1. **Register a User**: Use the bot to complete onboarding. Ensure you provide skills and preferences that you can easily match later (e.g., Skill: "Python", Location: "Remote").
2. **Verify User in DB**:
   ```bash
   docker-compose exec db psql -U postgres -d jobpulse -c "SELECT id, telegram_id, username FROM users_user;"
   ```

### Step B: Trigger the Orchestrator
Create a `JobPost` that matches the user's preferences. You can do this via the Django admin or by running a shell command:

```bash
docker-compose exec web python manage.py shell <<EOF
from apps.channels.models import Channel
from apps.jobs.models import JobPost
from apps.jobs.services.orchestrator import MatchOrchestrator

# Ensure a channel exists
channel, _ = Channel.objects.get_or_create(name="Test Channel", channel_username="test_channel")

# Create a matching job post
job = JobPost.objects.create(
    channel=channel,
    message_id=12345,
    raw_text="Join our team as a Senior Python Developer! Remote position.",
    category="software",
    work_mode="remote",
    source_link="https://t.me/test_channel/12345"
)

# Trigger matching
MatchOrchestrator.run(job)
EOF
```

## 3. Monitoring Results

### Check Celery Logs
Monitor the worker to see the task dispatch and any retry attempts.
```bash
docker-compose logs -f celery_worker
```
*Look for: `Enqueued notification...` and `Successfully sent notification...`*

### Check Bot Logs
Monitor the bot to see it receiving the HTTP request and sending the Telegram message.
```bash
docker-compose logs -f bot
```
*Look for: `Internal Notification API started...` and `Received notification request for ID...`*

### Check Database State
Verify that the notification was created and marked as sent.
```bash
docker-compose exec db psql -U postgres -d jobpulse -c "SELECT id, user_id, is_sent, match_score FROM notifications_notification;"
```

## 4. Testing Resilience (Failure Scenarios)

### Scenario: Bot Service Down
1. Stop the bot: `docker-compose stop bot`
2. Trigger the orchestrator (Step B).
3. Check Celery logs: `docker-compose logs -f celery_worker`.
4. **Observation**: You should see the task failing and raising a `Retry`.
5. Start the bot: `docker-compose start bot`.
6. **Observation**: On the next retry attempt, the notification should be delivered.

### Scenario: Simulating Rate Limits (Advanced)
If you have multiple workers or high traffic, you might see 429 errors. To verify handling, you can temporarily modify `bot/services/api.py` to return a 429 status for every 2nd request, then observe the Celery worker respecting the `Retry-After` header.
