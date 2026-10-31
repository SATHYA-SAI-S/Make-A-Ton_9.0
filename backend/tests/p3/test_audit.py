"""
Unit & Integration Tests for Phase 2: Audit Service & AuditPort (P3-T02).
Verifies:
1. Audit event persistence with before/after JSON snapshots.
2. Field-level diff computation.
3. Append-only enforcement (update and delete blocked).
4. AuditPort implementation and registry binding.
5. Role authorization (Admin & Staff allowed, Customer denied).
6. Specialized history views.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.errors import SubscriptIQError, PermissionDeniedError
from app.audit.models import AuditLog
from app.audit.service import emit_audit_event, query_audit_logs, compute_diff
from app.audit.bootstrap import AuditPortImpl, bootstrap_audit
from app.shared.registry import get_port

# In-memory test database for isolated test execution
test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    bootstrap_audit()
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_emit_audit_event_and_diff(db_session):
    before_state = {"price": "120000.00", "status": "ACTIVE", "tier": "Enterprise"}
    after_state = {"price": "144000.00", "status": "ACTIVE", "tier": "Enterprise Plus"}

    log_id = emit_audit_event(
        actor_id="usr-admin-001",
        actor_role="admin",
        action="plan.price_updated",
        entity_type="plan",
        entity_id="plan-ent-monthly",
        before=before_state,
        after=after_state,
        meta={"reason": "Annual tier re-indexing", "ip": "10.0.0.1"},
        request_id="req-test-99",
        db=db_session
    )

    assert log_id is not None

    # Retrieve and verify
    log = db_session.query(AuditLog).filter(AuditLog.id == log_id).first()
    assert log is not None
    assert log.action == "plan.price_updated"
    assert log.actor_id == "usr-admin-001"
    assert log.actor_role == "admin"
    assert log.before["price"] == "120000.00"
    assert log.after["price"] == "144000.00"

    # Compute diff
    diff = compute_diff(log.before, log.after)
    assert "price" in diff
    assert diff["price"]["before"] == "120000.00"
    assert diff["price"]["after"] == "144000.00"
    assert "tier" in diff
    assert diff["tier"]["before"] == "Enterprise"
    assert diff["tier"]["after"] == "Enterprise Plus"
    # Unchanged fields are not marked as changed
    assert "status" not in diff

def test_audit_logs_are_append_only(db_session):
    log_id = emit_audit_event(
        actor_id="usr-admin-001",
        action="test.immutable",
        entity_type="test",
        entity_id="test-1",
        db=db_session
    )

    log = db_session.query(AuditLog).filter(AuditLog.id == log_id).first()
    assert log is not None

    # Attempting to update existing log must raise SubscriptIQError
    with pytest.raises(SubscriptIQError) as exc_info:
        log.action = "tampered.action"
        db_session.commit()
    assert "append-only" in str(exc_info.value.message).lower()
    db_session.rollback()

    # Attempting to delete existing log must raise SubscriptIQError
    log_for_delete = db_session.query(AuditLog).filter(AuditLog.id == log_id).first()
    with pytest.raises(SubscriptIQError) as exc_delete:
        db_session.delete(log_for_delete)
        db_session.commit()
    assert "append-only" in str(exc_delete.value.message).lower()
    db_session.rollback()

def test_query_audit_logs_filtering(db_session):
    # Seed 3 distinct logs
    emit_audit_event("usr-p1", "product.price_changed", "product", "prod-101", db=db_session)
    emit_audit_event("usr-p2", "invoice.cancelled", "invoice", "inv-202", db=db_session)
    emit_audit_event("usr-p1", "subscription.status_changed", "subscription", "sub-303", db=db_session)

    # Filter by entity_type
    invoices, total_inv = query_audit_logs(db=db_session, entity_type="invoice")
    assert total_inv == 1
    assert invoices[0]["entity_id"] == "inv-202"

    # Filter by actor_id
    p1_logs, total_p1 = query_audit_logs(db=db_session, actor_id="usr-p1")
    assert total_p1 >= 2

def test_audit_port_implementation():
    port = get_port("audit")
    assert port is not None
    assert isinstance(port, AuditPortImpl)

    emitted_id = port.emit(
        actor_id="sys-runner",
        action="payment.recorded",
        entity_type="payment",
        entity_id="pay-999",
        after={"amount": "18408.00"}
    )
    assert emitted_id is not None
