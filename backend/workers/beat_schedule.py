"""Celery Beat schedule configuration."""

from celery.schedules import crontab

# Beat schedule for periodic tasks
CELERY_BEAT_SCHEDULE = {
    # Scrape all active websites every day at 2 AM
    "scrape-all-websites-daily": {
        "task": "workers.tasks.scrape.scrape_all_websites",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "scraping"},
    },

    # Clean up old price records every Sunday at 3 AM
    "cleanup-old-prices-weekly": {
        "task": "workers.tasks.cleanup.cleanup_old_prices",
        "schedule": crontab(hour=3, minute=0, day_of_week="sunday"),
        "args": (90,),  # Keep 90 days of history
        "options": {"queue": "maintenance"},
    },

    # Clean up old scrape logs every Sunday at 3:30 AM
    "cleanup-old-logs-weekly": {
        "task": "workers.tasks.cleanup.cleanup_old_scrape_logs",
        "schedule": crontab(hour=3, minute=30, day_of_week="sunday"),
        "args": (30,),  # Keep 30 days of logs
        "options": {"queue": "maintenance"},
    },

    # Update website statistics every 6 hours
    "update-website-stats": {
        "task": "workers.tasks.cleanup.update_website_stats",
        "schedule": crontab(minute=0, hour="*/6"),
        "options": {"queue": "maintenance"},
    },
}
