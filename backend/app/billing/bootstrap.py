from datetime import date
from typing import Optional, Dict, Any, List
from backend.app.core.database import SessionLocal
from backend.app.shared.ports import BillingControlPort
from backend.app.shared.registry import register_port
from backend.app.billing.models import BillingRun
from backend.app.billing.engine import run_billing_engine

class BillingControlServiceImpl(BillingControlPort):
    def run_now(self, as_of: Optional[date] = None, dry_run: bool = False) -> Dict[str, Any]:
        run = run_billing_engine(as_of=as_of, dry_run=dry_run, triggered_by="CONTROL_PORT")
        return {
            "run_id": run.id,
            "status": run.status,
            "subscriptions_checked": run.subscriptions_checked,
            "invoices_created": run.invoices_created,
            "failures": run.failures
        }

    def last_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            runs = db.query(BillingRun).order_by(BillingRun.started_at.desc()).limit(limit).all()
            return [
                {
                    "id": r.id,
                    "started_at": r.started_at.isoformat(),
                    "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                    "status": r.status,
                    "triggered_by": r.triggered_by,
                    "subscriptions_checked": r.subscriptions_checked,
                    "invoices_created": r.invoices_created,
                    "failures": r.failures
                }
                for r in runs
            ]
        finally:
            db.close()

def bootstrap():
    register_port("billing_control", BillingControlServiceImpl())
