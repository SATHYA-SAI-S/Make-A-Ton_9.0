"""
Celery Beat Schedule definition for Analytics & Performance layer (P3-T07).
Exported as standard BEAT dictionary auto-merged by celery_app.py.
"""

BEAT = {
    "rebuild-revenue-snapshots-nightly": {
        "task": "backend.app.analytics.tasks.rebuild_revenue_snapshots",
        "schedule": 86400.0,  # Runs nightly every 24 hours
        "kwargs": {"months_back": 12},
    },
    "refresh-materialized-views-hourly": {
        "task": "backend.app.analytics.tasks.refresh_materialized_views",
        "schedule": 3600.0,  # Runs every hour
    },
}
