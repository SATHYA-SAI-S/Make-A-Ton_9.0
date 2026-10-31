"""
Financial Forecasting & Scenario Simulator Router.
Provides endpoints for interactive what-if simulations and scenario persistence under /api/v1/finance/forecast.
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.database import get_db
from app.core.security import UserClaims, require_roles
from app.finance.forecasting import (
    run_forecast_simulation,
    save_forecast_scenario,
    list_forecast_scenarios,
    get_forecast_scenario,
    delete_forecast_scenario,
    extract_baseline_assumptions,
)

forecast_router = APIRouter(prefix="/forecast", tags=["Financial Forecasting & Simulator"])


class ForecastAssumptionsSchema(BaseModel):
    new_growth_pct: Optional[float] = None
    churn_pct: Optional[float] = None
    expansion_pct: Optional[float] = None
    upgrade_pct: Optional[float] = None
    contraction_pct: Optional[float] = None
    downgrade_pct: Optional[float] = None
    collection_rate_pct: Optional[float] = None
    price_increase_pct: Optional[float] = None
    price_change_pct: Optional[float] = None
    discount_pct: Optional[float] = None


class SimulateForecastRequest(BaseModel):
    horizon_months: int = Field(12, ge=1, le=36, description="Forecast horizon in months")
    assumptions: Optional[ForecastAssumptionsSchema] = None
    starting_mrr: Optional[float] = None


class SaveScenarioRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Scenario name")
    description: Optional[str] = None
    horizon_months: int = Field(12, ge=1, le=36)
    assumptions: Optional[ForecastAssumptionsSchema] = None


@forecast_router.post("/simulate", summary="Execute Explainable Forward-Looking Forecast Simulation")
def simulate_forecast(
    req: SimulateForecastRequest,
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    """
    Simulates forward-looking financial trajectory given what-if assumptions.
    Returns baseline historical trajectory, simulated projection, step explanations,
    and growth metrics.
    """
    assumptions_dict = req.assumptions.model_dump(exclude_unset=True) if req.assumptions else {}
    starting_mrr_dec = Decimal(str(req.starting_mrr)) if req.starting_mrr is not None else None

    return run_forecast_simulation(
        db=db,
        horizon_months=req.horizon_months,
        assumptions=assumptions_dict,
        starting_mrr_override=starting_mrr_dec
    )


@forecast_router.get("/baseline", summary="Get Current Historical Baseline Assumptions & Curve")
def get_baseline_forecast(
    horizon_months: int = Query(12, ge=1, le=36),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    """
    Returns the current business-as-usual baseline assumptions extracted from
    past 6 months and forward-looking projection.
    """
    return run_forecast_simulation(
        db=db,
        horizon_months=horizon_months,
        assumptions=None
    )


@forecast_router.post("/scenarios", status_code=status.HTTP_201_CREATED, summary="Save Simulation Scenario")
def create_scenario(
    req: SaveScenarioRequest,
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    """
    Persists a named scenario into the forecast_scenarios table.
    """
    assumptions_dict = req.assumptions.model_dump(exclude_unset=True) if req.assumptions else {}
    scenario = save_forecast_scenario(
        db=db,
        name=req.name,
        description=req.description,
        horizon_months=req.horizon_months,
        assumptions=assumptions_dict,
        created_by=getattr(current_user, "id", getattr(current_user, "sub", "staff")) if current_user else "staff"
    )
    return {
        "id": scenario.id,
        "name": scenario.name,
        "description": scenario.description,
        "horizon_months": scenario.horizon_months,
        "assumptions": scenario.assumptions,
        "summary": scenario.summary,
        "created_by": scenario.created_by,
        "created_at": scenario.created_at.isoformat() if scenario.created_at else None
    }


@forecast_router.get("/scenarios", summary="List Saved Simulation Scenarios")
def list_scenarios(
    limit: int = Query(50, ge=1, le=100),
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    scenarios = list_forecast_scenarios(db=db, limit=limit)
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "horizon_months": s.horizon_months,
            "assumptions": s.assumptions,
            "summary": s.summary,
            "created_by": s.created_by,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in scenarios
    ]


@forecast_router.get("/scenarios/{scenario_id}", summary="Get Scenario Details")
def get_scenario(
    scenario_id: str,
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    scenario = get_forecast_scenario(db=db, scenario_id=scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {
        "id": scenario.id,
        "name": scenario.name,
        "description": scenario.description,
        "horizon_months": scenario.horizon_months,
        "assumptions": scenario.assumptions,
        "projection": scenario.projection,
        "summary": scenario.summary,
        "created_by": scenario.created_by,
        "created_at": scenario.created_at.isoformat() if scenario.created_at else None
    }


@forecast_router.delete("/scenarios/{scenario_id}", summary="Delete Saved Scenario")
def delete_scenario(
    scenario_id: str,
    current_user: UserClaims = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db),
):
    success = delete_forecast_scenario(db=db, scenario_id=scenario_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"message": "Scenario deleted successfully", "id": scenario_id}
