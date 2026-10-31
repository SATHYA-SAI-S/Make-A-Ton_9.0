"""
Customer Requests Pydantic Schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CustomerRequestCreate(BaseModel):
    subscription_id: str = Field(..., description="Target subscription ID")
    type: str = Field(..., description="Request type: UPGRADE, DOWNGRADE, PAUSE, CANCEL, RENEWAL")
    target_plan_id: Optional[str] = Field(None, description="Required for UPGRADE and DOWNGRADE")
    note: Optional[str] = Field(None, description="Customer request rationale")

class CustomerRequestReview(BaseModel):
    action: str = Field(..., description="Decision action: APPROVE or REJECT")
    decision_note: Optional[str] = Field(None, description="Staff decision note")

class CustomerRequestDTO(BaseModel):
    id: str
    customer_id: str
    subscription_id: str
    type: str
    target_plan_id: Optional[str] = None
    note: Optional[str] = None
    status: str
    decided_by: Optional[str] = None
    decided_at: Optional[str] = None
    decision_note: Optional[str] = None
    created_at: str
