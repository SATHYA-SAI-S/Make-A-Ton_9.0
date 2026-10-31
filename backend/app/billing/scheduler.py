from datetime import date
from typing import Optional
from app.celery_app import celery_app
from app.billing.engine import run_billing_engine

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def task_run_billing(self, as_of_str: Optional[str] = None, dry_run: bool = False):
    try:
        as_of = date.fromisoformat(as_of_str) if as_of_str else date.today()
        billing_run = run_billing_engine(as_of=as_of, dry_run=dry_run, triggered_by="CELERY_SCHEDULER")
        return {"run_id": billing_run.id, "status": billing_run.status, "invoices": billing_run.invoices_created}
    except Exception as exc:
        raise self.retry(exc=exc)

BEAT = {
    "daily-billing-job": {
        "task": "app.billing.scheduler.task_run_billing",
        "schedule": 86400.0,  # Run daily
    }
}
