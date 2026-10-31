"""
Financial Forecasting & Scenario Simulator Engine.
Provides explainable forward-looking MRR, ARR, Invoiced, Collected and Outstanding projections
with step-by-step mathematical reasoning and scenario persistence.
"""
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, select

from app.core.money import to_money, ROUND_HALF_UP
from app.finance.models import (
    Subscription,
    Invoice,
    Payment,
    Plan,
    ForecastScenario,
)
from app.finance.overview import compute_mrr_sql, normalize_mrr


def _to_decimal(val: Any, default: str = "0.00") -> Decimal:
    if val is None:
        return Decimal(default)
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal(default)


def extract_baseline_assumptions(db: Session) -> Dict[str, Decimal]:
    """
    Extracts baseline assumptions from the past 6 months of historical data.
    Computes real historical monthly growth, churn, and invoice collection rates.
    Falls back gracefully to steady baseline if historical data is limited.
    """
    today = date.today()
    six_months_ago = today - timedelta(days=180)

    # 1. Historical Collection Rate
    inv_stats = db.query(
        func.sum(Invoice.total).label("total_invoiced"),
        func.sum(Invoice.amount_paid).label("total_collected")
    ).filter(
        Invoice.invoice_date >= six_months_ago,
        Invoice.status != "CANCELLED"
    ).first()

    total_inv = _to_decimal(inv_stats.total_invoiced) if inv_stats and inv_stats.total_invoiced else Decimal("0.00")
    total_col = _to_decimal(inv_stats.total_collected) if inv_stats and inv_stats.total_collected else Decimal("0.00")

    if total_inv > Decimal("0.00"):
        hist_collection_rate = ((total_col / total_inv) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        hist_collection_rate = Decimal("95.00")

    # 2. Historical Churn & Growth
    cur_mrr = compute_mrr_sql(db, as_of=today)

    new_subs = db.query(Subscription).filter(
        Subscription.start_date >= six_months_ago,
        Subscription.status == "ACTIVE"
    ).all()
    new_mrr_total = Decimal("0.00")
    for s in new_subs:
        if s.plan:
            new_mrr_total += normalize_mrr(s.plan.price, s.plan.billing_frequency)

    closed_subs = db.query(Subscription).filter(
        Subscription.expiry_date >= six_months_ago,
        Subscription.status == "CLOSED"
    ).all()
    churn_mrr_total = Decimal("0.00")
    for s in closed_subs:
        if s.plan:
            churn_mrr_total += normalize_mrr(s.plan.price, s.plan.billing_frequency)

    # Convert 6-month aggregate to monthly averages
    if cur_mrr > Decimal("0.00"):
        hist_growth = ((new_mrr_total / Decimal("6")) / cur_mrr * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        hist_churn = ((churn_mrr_total / Decimal("6")) / cur_mrr * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        hist_growth = Decimal("0.00")
        hist_churn = Decimal("0.00")

    return {
        "new_growth_pct": hist_growth,
        "churn_pct": hist_churn,
        "expansion_pct": Decimal("0.00"),
        "contraction_pct": Decimal("0.00"),
        "collection_rate_pct": hist_collection_rate,
        "price_increase_pct": Decimal("0.00"),
        "discount_pct": Decimal("0.00")
    }


def simulate_curve(
    starting_mrr: Decimal,
    assumptions: Dict[str, Any],
    horizon_months: int = 12,
    start_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Simulates monthly financial projection curve based on explainable model:
    MRR_next = MRR * (1 + new_growth - churn - downgrade) + upgrade_effect + price_change - discount
    Collected = Invoiced * Collection Rate
    Outstanding = Invoiced - Collected
    """
    if not start_date:
        start_date = date.today()

    new_growth_pct = _to_decimal(assumptions.get("new_growth_pct", 0.0))
    churn_pct = _to_decimal(assumptions.get("churn_pct", 0.0))
    # Support both naming conventions: expansion_pct / upgrade_pct and contraction_pct / downgrade_pct
    expansion_pct = _to_decimal(assumptions.get("expansion_pct", assumptions.get("upgrade_pct", 0.0)))
    contraction_pct = _to_decimal(assumptions.get("contraction_pct", assumptions.get("downgrade_pct", 0.0)))
    price_increase_pct = _to_decimal(assumptions.get("price_increase_pct", assumptions.get("price_change_pct", 0.0)))
    discount_pct = _to_decimal(assumptions.get("discount_pct", 0.0))
    collection_rate_pct = _to_decimal(assumptions.get("collection_rate_pct", 100.0))

    projection = []
    current_step_mrr = starting_mrr

    for i in range(1, horizon_months + 1):
        target_year = start_date.year + (start_date.month - 1 + i) // 12
        target_month = ((start_date.month - 1 + i) % 12) + 1
        month_str = f"{target_year:04d}-{target_month:02d}"

        # 1. Net Growth multiplier: 1 + (new - churn - contraction) / 100
        net_rate = (new_growth_pct - churn_pct - contraction_pct) / Decimal("100.00")
        base_next = (current_step_mrr * (Decimal("1.00") + net_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 2. Additive effects
        expansion_amt = (current_step_mrr * (expansion_pct / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        price_amt = (current_step_mrr * (price_increase_pct / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        discount_amt = (current_step_mrr * (discount_pct / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        next_mrr = base_next + expansion_amt + price_amt - discount_amt
        if next_mrr < Decimal("0.00"):
            next_mrr = Decimal("0.00")

        next_mrr = next_mrr.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        arr = (next_mrr * Decimal("12.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Billed invoiced revenue tracks recurring MRR
        proj_invoiced = next_mrr
        proj_collected = (proj_invoiced * (collection_rate_pct / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        proj_outstanding = (proj_invoiced - proj_collected).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Step explanation text
        step_terms = []
        if new_growth_pct != Decimal("0.00"):
            step_terms.append(f"+ {new_growth_pct / Decimal('100.00'):.2f}")
        if churn_pct != Decimal("0.00"):
            step_terms.append(f"- {churn_pct / Decimal('100.00'):.2f}")
        if contraction_pct != Decimal("0.00"):
            step_terms.append(f"- {contraction_pct / Decimal('100.00'):.2f}")

        if step_terms:
            explanation_parts = [f"Starting MRR {current_step_mrr} * (1 {' '.join(step_terms)})"]
        else:
            explanation_parts = [f"Starting MRR {current_step_mrr} * 1.00"]

        if expansion_amt != Decimal("0.00"):
            explanation_parts.append(f"+ expansion {expansion_amt}")
        if price_amt != Decimal("0.00"):
            explanation_parts.append(f"+ price change {price_amt}")
        if discount_amt != Decimal("0.00"):
            explanation_parts.append(f"- discount {discount_amt}")

        explanation = " ".join(explanation_parts)

        projection.append({
            "month": month_str,
            "mrr": str(next_mrr),
            "arr": str(arr),
            "projected_invoiced": str(proj_invoiced),
            "projected_collected": str(proj_collected),
            "projected_outstanding": str(proj_outstanding),
            "step_explanation": explanation,
        })

        current_step_mrr = next_mrr

    return projection


def run_forecast_simulation(
    db: Session,
    horizon_months: int = 12,
    assumptions: Optional[Dict[str, Any]] = None,
    starting_mrr_override: Optional[Decimal] = None
) -> Dict[str, Any]:
    """
    Executes a complete forecast simulation comparing baseline historical trajectory
    against simulated scenario assumptions.
    """
    today = date.today()
    if starting_mrr_override is not None:
        starting_mrr = to_money(starting_mrr_override)
    else:
        starting_mrr = compute_mrr_sql(db, as_of=today)

    baseline_assumptions = extract_baseline_assumptions(db)

    # 1. Baseline curve
    baseline_curve = simulate_curve(
        starting_mrr=starting_mrr,
        assumptions=baseline_assumptions,
        horizon_months=horizon_months,
        start_date=today
    )

    # 2. Simulation assumptions
    if assumptions is None or len(assumptions) == 0:
        sim_assumptions = {k: float(v) for k, v in baseline_assumptions.items()}
    else:
        # Check if all zeros passed - if all zeros, zero assumptions equal baseline
        all_zeros = True
        for k in ["new_growth_pct", "churn_pct", "expansion_pct", "upgrade_pct", "contraction_pct", "downgrade_pct", "price_increase_pct", "price_change_pct", "discount_pct"]:
            if k in assumptions and _to_decimal(assumptions[k]) != Decimal("0.00"):
                all_zeros = False
                break

        if all_zeros and "collection_rate_pct" not in assumptions:
            sim_assumptions = {k: float(v) for k, v in baseline_assumptions.items()}
        else:
            sim_assumptions = {
                "new_growth_pct": float(assumptions.get("new_growth_pct", baseline_assumptions["new_growth_pct"])),
                "churn_pct": float(assumptions.get("churn_pct", baseline_assumptions["churn_pct"])),
                "expansion_pct": float(assumptions.get("expansion_pct", assumptions.get("upgrade_pct", baseline_assumptions["expansion_pct"]))),
                "contraction_pct": float(assumptions.get("contraction_pct", assumptions.get("downgrade_pct", baseline_assumptions["contraction_pct"]))),
                "collection_rate_pct": float(assumptions.get("collection_rate_pct", baseline_assumptions["collection_rate_pct"])),
                "price_increase_pct": float(assumptions.get("price_increase_pct", assumptions.get("price_change_pct", baseline_assumptions["price_increase_pct"]))),
                "discount_pct": float(assumptions.get("discount_pct", baseline_assumptions["discount_pct"])),
            }

    # 3. Projected curve
    projected_curve = simulate_curve(
        starting_mrr=starting_mrr,
        assumptions=sim_assumptions,
        horizon_months=horizon_months,
        start_date=today
    )

    # 4. Compute summaries
    ending_mrr = _to_decimal(projected_curve[-1]["mrr"]) if projected_curve else starting_mrr
    if starting_mrr > Decimal("0.00"):
        total_growth_pct = (((ending_mrr - starting_mrr) / starting_mrr) * Decimal("100.00")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        # Annualized growth rate over horizon
        if horizon_months > 0:
            annual_factor = Decimal("12.0") / Decimal(str(horizon_months))
            projected_annual_growth_pct = (total_growth_pct * annual_factor).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        else:
            projected_annual_growth_pct = total_growth_pct
    else:
        total_growth_pct = Decimal("0.0")
        projected_annual_growth_pct = Decimal("0.0")

    total_proj_invoiced = sum([_to_decimal(p["projected_invoiced"]) for p in projected_curve])
    total_proj_collected = sum([_to_decimal(p["projected_collected"]) for p in projected_curve])
    total_proj_outstanding = sum([_to_decimal(p["projected_outstanding"]) for p in projected_curve])

    summary = {
        "starting_mrr": str(starting_mrr),
        "ending_mrr": str(ending_mrr),
        "horizon_months": horizon_months,
        "projected_growth_pct": float(total_growth_pct),
        "projected_annual_growth_pct": float(projected_annual_growth_pct),
        "total_projected_invoiced": str(to_money(total_proj_invoiced)),
        "total_projected_collected": str(to_money(total_proj_collected)),
        "total_projected_outstanding": str(to_money(total_proj_outstanding)),
    }

    return {
        "starting_mrr": str(starting_mrr),
        "horizon_months": horizon_months,
        "baseline_assumptions": {k: float(v) for k, v in baseline_assumptions.items()},
        "simulated_assumptions": sim_assumptions,
        "baseline": baseline_curve,
        "projection": projected_curve,
        "summary": summary
    }


def save_forecast_scenario(
    db: Session,
    name: str,
    description: Optional[str] = None,
    horizon_months: int = 12,
    assumptions: Optional[Dict[str, Any]] = None,
    created_by: Optional[str] = None
) -> ForecastScenario:
    """
    Executes and persists a scenario into the forecast_scenarios table.
    """
    sim_result = run_forecast_simulation(
        db=db,
        horizon_months=horizon_months,
        assumptions=assumptions
    )

    scenario = ForecastScenario(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        horizon_months=horizon_months,
        assumptions=sim_result["simulated_assumptions"],
        projection=sim_result["projection"],
        summary=sim_result["summary"],
        created_by=created_by
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


def list_forecast_scenarios(db: Session, limit: int = 50) -> List[ForecastScenario]:
    return db.query(ForecastScenario).order_by(ForecastScenario.created_at.desc()).limit(limit).all()


def get_forecast_scenario(db: Session, scenario_id: str) -> Optional[ForecastScenario]:
    return db.query(ForecastScenario).filter(ForecastScenario.id == scenario_id).first()


def delete_forecast_scenario(db: Session, scenario_id: str) -> bool:
    scenario = get_forecast_scenario(db, scenario_id)
    if not scenario:
        return False
    db.delete(scenario)
    db.commit()
    return True
