# Celery + Redis Task Queue Setup

Factory Insider uses Celery with Redis for asynchronous task processing and scheduled jobs.

## Architecture

```
┌─────────────────┐
│  FastAPI App    │
│  (API Requests) │
└────────┬────────┘
         │
         ├──► Redis Broker ◄──────────┐
         │                            │
         └──► Task Queue              │
              (email, video, etc.)    │
                                      │
                    ┌─────────────────┘
                    │
         ┌──────────▼──────────┐
         │ Celery Worker Pool  │
         │  (4 processes)      │
         └────────────────────┘
              │
              ├──► Email Tasks
              ├──► Video Processing
              ├──► Analytics
              └──► Maintenance
```

## Setup

### 1. Installation

Dependencies are already in `requirements.txt`:
```bash
pip install celery==5.3.4 redis==5.0.1
```

### 2. Configuration

Settings are in `app/config.py`:
```python
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
```

### 3. Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or using local Redis
redis-server
```

### 4. Start Celery Worker

```bash
# Using provided script
bash backend/run_celery.sh

# Or manually
cd backend
celery -A app.celery worker -l info -c 4
```

### 5. (Optional) Start Celery Beat Scheduler

For periodic tasks:
```bash
celery -A app.celery beat -l info
```

## Task Queue Management

### Available Queues

- **email**: Email sending tasks
- **video**: Video processing tasks
- **analytics**: Analytics and tracking tasks
- **ai**: AI/ML tasks (for future)
- **celery**: Default queue

### Example: Queue an Email

```python
from app.task_utils import queue_email

# In your API endpoint
task_id = queue_email(
    to_email="user@example.com",
    subject="Welcome to Factory Insider",
    html_content="<h1>Welcome</h1>"
)

# Track progress
from app.task_utils import get_task_status
status = get_task_status(task_id)
print(status)  # {"id": "...", "state": "SUCCESS", "result": {...}}
```

### Example: Queue Bulk Emails

```python
from app.task_utils import queue_bulk_emails

recipients = ["user1@example.com", "user2@example.com"]
task_id = queue_bulk_emails(
    recipient_list=recipients,
    subject="Newsletter",
    html_content="<h1>Latest News</h1>"
)
```

### Example: Queue Video Processing

```python
from app.task_utils import queue_video_processing, queue_thumbnail_generation

# Process metadata
task_id = queue_video_processing(
    video_id=1,
    video_url="https://s3.example.com/video.mp4"
)

# Generate thumbnails
task_id = queue_thumbnail_generation(
    video_id=1,
    video_url="https://s3.example.com/video.mp4",
    timestamps=[10, 30, 60]
)
```

### Example: Track User Activity

```python
from app.task_utils import queue_user_activity

queue_user_activity(
    user_id=1,
    action="view",
    resource_type="video",
    resource_id=5
)
```

## Task Definition

### Creating a New Task

```python
from celery import shared_task

@shared_task(name="app.tasks.module.task_name")
def my_task(param1: str, param2: int) -> dict:
    """Task docstring"""
    try:
        # Task logic here
        return {"status": "success", "result": "..."}
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        raise
```

### Task Routing

Configure in `app/celery.py`:
```python
celery_app.conf.task_routes = {
    "app.tasks.email.*": {"queue": "email"},
    "app.tasks.video.*": {"queue": "video"},
}
```

## Periodic Tasks (Beat)

Configured in `app/celery.py`:

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "cleanup-sessions": {
        "task": "app.tasks.maintenance.cleanup_old_sessions",
        "schedule": crontab(minute=0),  # Every hour
    },
    "update-views": {
        "task": "app.tasks.analytics.update_view_counts",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
}
```

### Schedule Options

- `crontab(minute=0)` - Every hour
- `crontab(minute="*/15")` - Every 15 minutes
- `crontab(hour=3, minute=0)` - Daily at 3 AM
- `crontab(day_of_week=1)` - Every Monday
- `crontab(hour=0, minute=0, day_of_month=1)` - Monthly on 1st

## Monitoring

### Celery Flower (Web UI)

```bash
pip install flower
flower -A app.celery
# Access at http://localhost:5555
```

### Task Status API

Use Redis CLI:
```bash
redis-cli
> KEYS celery*
> GET celery-task-meta-<task_id>
```

## Best Practices

### 1. Always Return a Result

```python
@shared_task
def my_task():
    return {"status": "completed"}  # Good
    # return  # Bad - returns None
```

### 2. Use Task IDs for Tracking

```python
task = my_task.delay()
task_id = task.id
# Store task_id in database to track progress
```

### 3. Handle Long-Running Tasks

```python
@shared_task(bind=True)
def long_task(self):
    total_steps = 100
    for i in range(total_steps):
        # Update progress
        self.update_state(state='PROGRESS', meta={'current': i})
        # Do work
```

### 4. Retry Failed Tasks

```python
@shared_task(bind=True, autoretry_for=(Exception,),
             retry_kwargs={'max_retries': 3}, retry_backoff=True)
def reliable_task(self):
    pass
```

### 5. Set Time Limits

```python
@shared_task(time_limit=300, soft_time_limit=250)
def time_sensitive_task():
    pass
```

## Troubleshooting

### Tasks Not Running

1. Check Redis connection:
   ```bash
   redis-cli ping  # Should return PONG
   ```

2. Check Celery worker is running:
   ```bash
   ps aux | grep celery
   ```

3. Check queue:
   ```bash
   celery -A app.celery inspect active
   ```

### High Memory Usage

- Adjust worker pool size: `-c 2` (2 processes)
- Increase max tasks per child: `worker_max_tasks_per_child=100`

### Slow Task Execution

- Check worker logs: `celery -A app.celery worker -l debug`
- Monitor with Flower: `flower -A app.celery`
- Profile tasks with line_profiler

## Related Documentation

- [Celery Documentation](https://docs.celeryproject.io/)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Monitoring](https://flower.readthedocs.io/)
