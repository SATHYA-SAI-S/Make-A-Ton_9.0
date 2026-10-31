#!/usr/bin/env python3
import subprocess
import sys

OWN = {
    "p1": [
        "backend/app/auth/", "backend/app/users/", "backend/app/customers/",
        "backend/app/products/", "backend/app/variants/", "backend/app/plans/",
        "backend/app/quotations/", "backend/app/quotation_templates/",
        "backend/app/subscriptions/", "backend/app/core/", "backend/app/shared/",
        "docs/contracts/", "backend/migrations/versions_p1/", "backend/tests/p1/",
        "requirements/p1.txt", "backend/requirements/p1.txt",
        "frontend/src/modules/p1/", "e2e/p1/", "docs/p1/", "docs/requests/p1-"
    ],
    "p2": [
        "backend/app/taxes/", "backend/app/discounts/", "backend/app/billing/",
        "backend/app/invoices/", "backend/app/payments/", "backend/app/allocations/",
        "backend/app/reconciliation/", "backend/app/notifications/", "backend/app/overdue/",
        "backend/migrations/versions_p2/", "backend/tests/p2/",
        "backend/requirements/p2.txt", "frontend/src/modules/p2/",
        "e2e/p2/", "docs/p2/", "docs/requests/p2-",
        # Shared platform files permitted during initial foundation setup
        "SPEC.md", "ARCHITECTURE.md", "ROADMAP.md", "scripts/",
        "backend/app/core/", "backend/app/shared/", "backend/app/main.py",
        "backend/app/__init__.py", "backend/tests/__init__.py", "backend/tests/conftest.py",
        "backend/app/celery_app.py", "backend/requirements/", "docker-compose.yml",
        ".env.example", ".gitignore", "random.txt", "docs/contracts/"
    ],
    "p3": [
        "backend/app/portal/", "backend/app/finance/", "backend/app/analytics/",
        "backend/app/revenue_guardian/", "backend/app/audit/", "backend/app/reports/",
        "backend/migrations/versions_p3/", "backend/tests/p3/",
        "backend/requirements/p3.txt", "frontend/src/modules/p3/",
        "frontend/src/shared/ui/", "e2e/p3/", "docs/p3/", "docs/requests/p3-"
    ]
}

if len(sys.argv) < 2:
    print("Usage: check_ownership.py [p1|p2|p3]")
    sys.exit(1)

who = sys.argv[1]
out = subprocess.check_output(["git", "status", "--porcelain", "-uall"], text=True)
bad = []
for line in out.splitlines():
    path = line[3:].split(" -> ")[-1].strip().strip('"')
    if not any(path.startswith(p) for p in OWN[who]):
        bad.append(path)

if bad:
    print("STOP. These files are outside your area:")
    for b in bad:
        print("  ", b)
    print("Undo them (git checkout -- <file>) or file a request in docs/requests/.")
    sys.exit(1)

print("Ownership check passed.")
