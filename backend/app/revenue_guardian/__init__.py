"""
Revenue Guardian: Autonomous Anomaly Detection & Revenue Leakage Protection Engine.
"""
from backend.app.revenue_guardian.models import RiskAlert, RiskDetectionRun
from backend.app.revenue_guardian.detection import run_detection_cycle
from backend.app.revenue_guardian.rules import ALL_DETECTION_RULES
