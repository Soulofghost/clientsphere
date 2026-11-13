from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=120)
    company: str = Field(..., min_length=1, max_length=120)
    role: Optional[str] = "Stakeholder"
    phone: Optional[str] = None

class ContactResponse(BaseModel):
    id: str
    name: str
    email: str
    company: str
    role: str
    phone: Optional[str] = None
    created_at: str
    updated_at: str

class DealCreate(BaseModel):
    contact_id: str
    title: str = Field(..., min_length=1, max_length=160)
    value: float = Field(..., ge=0.0)
    stage: Optional[str] = "qualified"
    probability: Optional[int] = None
    expected_close: Optional[str] = None

class DealUpdate(BaseModel):
    title: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    expected_close: Optional[str] = None

class DealResponse(BaseModel):
    id: str
    contact_id: str
    contact_name: Optional[str] = None
    contact_company: Optional[str] = None
    title: str
    value: float
    stage: str
    probability: int
    expected_close: Optional[str] = None
    weighted_value: float
    created_at: str
    updated_at: str

class ActivityCreate(BaseModel):
    deal_id: Optional[str] = None
    contact_id: str
    activity_type: str
    notes: str = Field(..., min_length=1)

class ActivityResponse(BaseModel):
    id: str
    deal_id: Optional[str] = None
    contact_id: str
    activity_type: str
    notes: str
    created_at: str

class PipelineForecastResponse(BaseModel):
    total_pipeline_value: float
    weighted_pipeline_value: float
    closed_won_value: float
    total_active_deals: int
    win_rate_pct: float
