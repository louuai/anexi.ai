from typing import Optional
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr


# ============== AUTH SCHEMAS ==============

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "user"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    tenant_id: int


# ============== USER SCHEMAS ==============

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "user"


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== USER PROFILE SCHEMAS ==============


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    selling_type: str

    class Config:
        from_attributes = True


class NotificationSettings(BaseModel):
    order_updates: bool = True
    risk_alerts: bool = True
    email_digest: bool = False


class SystemSettings(BaseModel):
    language: str = "en"
    timezone: str = "UTC"


class ProfileSettingsResponse(BaseModel):
    user_id: int
    full_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    notifications: NotificationSettings
    system: SystemSettings


class ProfileSettingsUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    notifications: Optional[NotificationSettings] = None
    system: Optional[SystemSettings] = None


class ProfilePasswordUpdateRequest(BaseModel):
    current_password: str
    new_password: str


# ============== BOUTIQUE SCHEMAS ==============

class BoutiqueCreate(BaseModel):
    name: str
    owner_id: int


class BoutiqueResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== CUSTOMER SCHEMAS ==============

class CustomerCreate(BaseModel):
    full_name: Optional[str] = None
    phone: str
    email: Optional[EmailStr] = None
    boutique_id: int


class CustomerResponse(BaseModel):
    id: int
    full_name: Optional[str]
    phone: str
    email: Optional[str]
    boutique_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== ORDER SCHEMAS ==============

class OrderCreate(BaseModel):
    customer_id: int
    boutique_id: int
    product_name: str
    price: Decimal
    status: str = "pending"


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    boutique_id: int
    product_name: str
    price: Decimal
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrderWithDecision(OrderResponse):
    """Order avec sa décision AI"""
    ai_decision: Optional[str] = None
    trust_score: Optional[Decimal] = None


# ============== CALL SCHEMAS ==============

class CallCreate(BaseModel):
    order_id: int
    agent_id: Optional[int] = None
    audio_url: Optional[str] = None
    transcript: Optional[str] = None


class CallResponse(BaseModel):
    id: int
    order_id: int
    agent_id: Optional[int]
    audio_url: Optional[str]
    transcript: Optional[str]
    ai_score: Optional[Decimal]
    ai_decision: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============== AI DECISION SCHEMAS ==============

class AIDecisionCreate(BaseModel):
    source_type: str  # order / call / behavior
    source_id: int
    score: Decimal
    decision: str  # auto_confirm / call_required / reject
    explanation: Optional[str] = None


class AIDecisionResponse(BaseModel):
    id: int
    source_type: str
    source_id: int
    score: Decimal
    decision: str
    explanation: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============== ADS INSIGHTS SCHEMAS ==============

class AdsInsightCreate(BaseModel):
    boutique_id: int
    source: str  # facebook / google / tiktok
    insight: str
    suggestion: Optional[str] = None


class AdsInsightResponse(BaseModel):
    id: int
    boutique_id: int
    source: str
    insight: str
    suggestion: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============== WEBHOOK SCHEMAS ==============

class WebhookOrderPayload(BaseModel):
    """Payload reçu des webhooks Shopify/WooCommerce"""
    customer_name: Optional[str] = None
    customer_phone: str
    customer_email: Optional[EmailStr] = None
    product_name: str
    price: Decimal
    order_source: str = "webhook"


# ============== PAYMENT SCHEMAS ==============

class PaymentCreate(BaseModel):
    boutique_id: int
    customer_id: int
    plan: str
    amount: Decimal
    payment_method: str = "card"


class PaymentResponse(BaseModel):
    id: int
    user_id: int
    boutique_id: int
    customer_id: int
    plan: str
    amount: Decimal
    payment_method: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

