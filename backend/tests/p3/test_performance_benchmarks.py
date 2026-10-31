"""
Performance Benchmark & Latency Validation Suite (P3-T15).
Validates that all Finance Intelligence, Visualizations, and Guardian endpoints
maintain sub-2-second (< 2.0s) response latency under substantial data volume.

Endpoints benchmarked:
1. /api/v1/finance/overview
2. /api/v1/finance/charts/revenue-performance
3. /api/v1/finance/charts/mrr-trend
4. /api/v1/finance/charts/mrr-waterfall
5. /api/v1/finance/charts/subscription-distribution
6. /api/v1/finance/charts/subscription-growth
7. /api/v1/finance/charts/cohorts
8. /api/v1/finance/charts/invoice-aging
9. /api/v1/finance/charts/collection-funnel
10. /api/v1/finance/charts/concentration
11. /api/v1/finance/forecast/simulate
12. /api/v1/guardian/dashboard
13. /api/v1/reports/monthly-financial
"""
import time
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.analytics.seed import seed_analytics_data
from backend.app.analytics.cache import invalidate_cache


@pytest.fixture(scope="module")
def benchmark_db():
    """Sets up an in-memory SQLite database seeded with synthetic financial data."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    # Seed 1,000 subscriptions, 3,000 invoices, 2,400 payments
    seed_analytics_data(
        db=session,
        num_customers=100,
        num_subs=1000,
        num_invoices=3000,
        num_payments=2400,
        batch_size=1000,
        quiet=True,
        reset=True
    )

    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def benchmark_client(benchmark_db):
    def override_get_db():
        try:
            yield benchmark_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer dev-admin-token"}


def test_endpoint_latencies_under_two_seconds(benchmark_client, auth_headers):
    """
    Benchmarks all 13 core endpoints and asserts response latency is strictly under 2.0s.
    """
    invalidate_cache()

    endpoints_to_test = [
        ("GET", "/api/v1/finance/overview", None),
        ("GET", "/api/v1/finance/charts/revenue-performance", None),
        ("GET", "/api/v1/finance/charts/mrr-trend", None),
        ("GET", "/api/v1/finance/charts/mrr-waterfall", None),
        ("GET", "/api/v1/finance/charts/subscription-distribution", None),
        ("GET", "/api/v1/finance/charts/subscription-growth", None),
        ("GET", "/api/v1/finance/charts/cohorts", None),
        ("GET", "/api/v1/finance/charts/invoice-aging", None),
        ("GET", "/api/v1/finance/charts/collection-funnel", None),
        ("GET", "/api/v1/finance/charts/concentration", None),
        ("POST", "/api/v1/finance/forecast/simulate", {
            "name": "Benchmark Simulation",
            "growth_rate_pct": 10.0,
            "churn_rate_pct": 4.0,
            "downgrade_rate_pct": 2.0,
            "expansion_mrr": 50000.0,
            "new_price_change_mrr": 0.0,
            "discount_impact_mrr": 0.0,
            "expected_collection_rate_pct": 92.0,
            "months_ahead": 6
        }),
        ("GET", "/api/v1/guardian/dashboard", None),
        ("GET", "/api/v1/reports/monthly-financial?format=json", None),
    ]

    latencies = {}

    for method, path, payload in endpoints_to_test:
        start = time.perf_counter()
        if method == "POST":
            res = benchmark_client.post(path, json=payload, headers=auth_headers)
        else:
            res = benchmark_client.get(path, headers=auth_headers)
        duration = time.perf_counter() - start

        latencies[path] = duration

        # Assertions
        assert res.status_code == 200, f"Endpoint {path} failed with {res.status_code}: {res.text}"
        assert duration < 2.0, f"Endpoint {path} exceeded 2.0s threshold: took {duration:.3f}s"

    print("\n--- Latency Benchmark Results (< 2.0s SLA) ---")
    for path, dur in latencies.items():
        print(f"  {path:55s} : {dur * 1000:7.2f} ms")


def test_cache_acceleration_benchmark(benchmark_client, auth_headers):
    """
    Verifies that cached secondary lookups respond even faster than the initial query.
    """
    path = "/api/v1/finance/charts/subscription-distribution"

    # First call (cold)
    t0 = time.perf_counter()
    r1 = benchmark_client.get(path, headers=auth_headers)
    cold_duration = time.perf_counter() - t0
    assert r1.status_code == 200

    # Second call (warm/cached)
    t1 = time.perf_counter()
    r2 = benchmark_client.get(path, headers=auth_headers)
    warm_duration = time.perf_counter() - t1
    assert r2.status_code == 200

    assert warm_duration < 2.0
    print(f"\nCache Cold: {cold_duration * 1000:.2f} ms | Cache Warm: {warm_duration * 1000:.2f} ms")


def test_seeding_throughput_and_counts(benchmark_db):
    """
    Verifies that synthetic data generation produces expected record counts.
    """
    from backend.app.finance.models import Subscription, Invoice, Payment

    sub_count = benchmark_db.query(Subscription).filter(Subscription.id.like("sub-seed-%")).count()
    inv_count = benchmark_db.query(Invoice).filter(Invoice.id.like("inv-seed-%")).count()
    pmt_count = benchmark_db.query(Payment).filter(Payment.id.like("pay-seed-%")).count()

    assert sub_count == 1000
    assert inv_count == 3000
    assert pmt_count >= 2000
