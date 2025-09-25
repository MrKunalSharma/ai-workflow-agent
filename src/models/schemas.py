"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class EmailPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class EmailIntent(str, Enum):
    PRICING_INQUIRY = "pricing_inquiry"
    SUPPORT_REQUEST = "support_request"
    COMPLAINT = "complaint"
    FEATURE_REQUEST = "feature_request"
    GENERAL_INQUIRY = "general_inquiry"
    SALES_OPPORTUNITY = "sales_opportunity"

class EmailStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"

class EmailBase(BaseModel):
    sender: EmailStr
    subject: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=10000)
    cc: Optional[List[EmailStr]] = []
    attachments: Optional[List[Dict[str, Any]]] = []

class EmailCreate(EmailBase):
    account_id: Optional[str] = None
    thread_id: Optional[str] = None
    
    @validator('content')
    def validate_content(cls, v):
        # Basic XSS prevention
        if '<script>' in v.lower():
            raise ValueError('Invalid content detected')
        return v

class EmailResponse(BaseModel):
    id: str
    status: EmailStatus
    intent: EmailIntent
    priority: EmailPriority
    sentiment_score: float = Field(..., ge=-1, le=1)
    confidence_score: float = Field(..., ge=0, le=1)
    suggested_response: str
    response_time_ms: int
    requires_human: bool
    processed_at: datetime
    tags: List[str] = []
    
class BatchEmailRequest(BaseModel):
    emails: List[EmailCreate]
    priority_override: Optional[EmailPriority] = None
    async_processing: bool = True

class WebhookConfig(BaseModel):
    url: str = Field(..., regex="^https://")
    events: List[str]
    secret: str = Field(..., min_length=32)
    active: bool = True

class Organization(BaseModel):
    name: str
    domain: str
    plan: str = "starter"
    api_key: str = Field(..., min_length=32)
    monthly_limit: int = 1000
    webhooks: List[WebhookConfig] = []
