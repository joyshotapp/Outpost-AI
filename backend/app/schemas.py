"""Pydantic schemas for API request/response validation"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class UserRegisterRequest(BaseModel):
    """User registration request"""

    email: EmailStr
    password: str
    full_name: str
    role: str  # 'buyer', 'supplier', 'admin'


class UserLoginRequest(BaseModel):
    """User login request"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response after login or refresh"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""

    refresh_token: str


class UserResponse(BaseModel):
    """User response"""

    id: int
    email: str
    full_name: Optional[str]
    role: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Complete login response with user info and tokens"""

    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Supplier Schemas
class SupplierCreateRequest(BaseModel):
    """Supplier creation request"""

    company_name: str
    company_slug: str
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    country: str
    city: Optional[str] = None
    industry: Optional[str] = None
    company_description: Optional[str] = None
    number_of_employees: Optional[int] = None
    established_year: Optional[int] = None
    certifications: Optional[str] = None
    main_products: Optional[str] = None
    manufacturing_capacity: Optional[str] = None
    lead_time_days: Optional[int] = None

    @field_validator("company_slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", v):
            raise ValueError(
                "Slug must only contain lowercase letters, numbers, and hyphens, "
                "and must start and end with a letter or number"
            )
        return v


class SupplierUpdateRequest(BaseModel):
    """Supplier update request"""

    company_name: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    company_description: Optional[str] = None
    number_of_employees: Optional[int] = None
    established_year: Optional[int] = None
    certifications: Optional[str] = None
    main_products: Optional[str] = None
    manufacturing_capacity: Optional[str] = None
    lead_time_days: Optional[int] = None


class SupplierResponse(BaseModel):
    """Supplier response"""

    id: int
    user_id: int
    company_name: str
    company_slug: str
    website: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    country: str
    city: Optional[str]
    industry: Optional[str]
    company_description: Optional[str]
    number_of_employees: Optional[int]
    established_year: Optional[int]
    certifications: Optional[str]
    main_products: Optional[str]
    manufacturing_capacity: Optional[str]
    lead_time_days: Optional[int]
    is_verified: bool
    is_active: bool
    view_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierListResponse(BaseModel):
    """Supplier list response"""

    id: int
    company_name: str
    company_slug: str
    country: str
    industry: Optional[str]
    is_verified: bool
    is_active: bool
    view_count: int

    class Config:
        from_attributes = True


# S3 Upload Schemas
class S3PresignedUrlRequest(BaseModel):
    """Request for generating S3 presigned URL"""

    filename: str
    resource_type: str  # 'videos', 'documents', etc.
    content_type: str  # MIME type
    file_size: int  # File size in bytes


class S3PresignedUrlResponse(BaseModel):
    """Response with S3 presigned URL and metadata"""

    url: str
    fields: dict
    expires_at: str
    max_file_size: int


class S3UploadStatusRequest(BaseModel):
    """Request to check upload status"""

    object_key: str


class S3UploadStatusResponse(BaseModel):
    """Response with upload status"""

    exists: bool
    object_key: Optional[str] = None
    download_url: Optional[str] = None


# Video Schemas
class VideoLanguageVersionRequest(BaseModel):
    """Request for creating/updating video language version"""

    language_code: str  # e.g., 'en', 'zh', 'es', 'fr'
    title: str
    description: Optional[str] = None
    subtitle_url: Optional[str] = None
    voice_url: Optional[str] = None


class VideoLanguageVersionResponse(BaseModel):
    """Response for video language version"""

    id: int
    video_id: int
    language_code: str
    title: str
    description: Optional[str]
    subtitle_url: Optional[str]
    voice_url: Optional[str]
    # Sprint 6 localization status fields
    localization_status: str = "pending"
    provider_job_id: Optional[str] = None
    cdn_url: Optional[str] = None
    compression_ratio: Optional[float] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class LocalizationJobStatusResponse(BaseModel):
    """Status of a video language version localization job"""

    video_id: int
    language_code: str
    localization_status: str
    provider_job_id: Optional[str] = None
    cdn_url: Optional[str] = None
    compression_ratio: Optional[float] = None
    error_message: Optional[str] = None
    subtitle_url: Optional[str] = None
    voice_url: Optional[str] = None


class VideoLocalizationRequest(BaseModel):
    """Request for enqueueing multilingual video generation"""

    target_languages: list[str]
    source_language: str = "en"

    @field_validator("source_language")
    @classmethod
    def normalize_source_language(cls, value: str) -> str:
        normalized = (value or "").strip().lower()
        if not normalized:
            raise ValueError("source_language is required")
        return normalized

    @field_validator("target_languages")
    @classmethod
    def normalize_target_languages(cls, value: list[str]) -> list[str]:
        normalized = sorted({language.strip().lower() for language in value if language and language.strip()})
        if not normalized:
            raise ValueError("target_languages must include at least one language")
        return normalized


class VideoLocalizationTaskResponse(BaseModel):
    """Response for multilingual generation task enqueue"""

    task_id: str
    status: str
    video_id: int
    source_language: str
    target_languages: list[str]


class VideoLocalizationStatusSummary(BaseModel):
    """Summary of all language version statuses for a video"""

    video_id: int
    versions: list[LocalizationJobStatusResponse]
    total: int
    completed: int
    failed: int
    pending: int


class VideoCreateRequest(BaseModel):
    """Request for creating a video"""

    supplier_id: int
    title: str
    description: Optional[str] = None
    video_url: str
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    video_type: Optional[str] = None  # product, company, testimonial, etc.
    language_versions: Optional[list[VideoLanguageVersionRequest]] = None


class VideoUpdateRequest(BaseModel):
    """Request for updating a video"""

    title: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    video_type: Optional[str] = None
    is_published: Optional[bool] = None


class VideoResponse(BaseModel):
    """Response for video with all details"""

    id: int
    supplier_id: int
    title: str
    description: Optional[str]
    video_url: str
    thumbnail_url: Optional[str]
    duration_seconds: Optional[int]
    video_type: Optional[str]
    is_published: bool
    view_count: int
    created_at: str
    updated_at: str
    language_versions: list[VideoLanguageVersionResponse] = []

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    """Response for video list (lightweight)"""

    id: int
    supplier_id: int
    title: str
    video_type: Optional[str]
    thumbnail_url: Optional[str]
    is_published: bool
    view_count: int
    created_at: str

    class Config:
        from_attributes = True


# RFQ Schemas
class RFQCreateRequest(BaseModel):
    """Request for creating a new RFQ"""

    title: str
    description: str
    specifications: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    required_delivery_date: Optional[str] = None
    # Note: attachment_url should come from S3 presigned upload, not in request body


class RFQResponse(BaseModel):
    """Response for RFQ details"""

    id: int
    buyer_id: int
    supplier_id: Optional[int]
    title: str
    description: str
    specifications: Optional[str]
    quantity: Optional[int]
    unit: Optional[str]
    required_delivery_date: Optional[str]
    attachment_url: Optional[str]
    status: str
    lead_score: Optional[int]
    lead_grade: Optional[str]
    parsed_data: Optional[str]
    pdf_vision_data: Optional[str]
    ai_summary: Optional[str]
    draft_reply: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RFQListResponse(BaseModel):
    """Response for RFQ list (lightweight)"""

    id: int
    buyer_id: int
    supplier_id: Optional[int]
    title: str
    status: str
    lead_score: Optional[int]
    lead_grade: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeNamespaceInitResponse(BaseModel):
    """Response for supplier Pinecone namespace initialization"""

    supplier_id: int
    namespace: str
    index_name: str
    initialized: bool


class KnowledgeDocumentCreateRequest(BaseModel):
    """Create knowledge document request"""

    supplier_id: int
    title: str
    source_type: str
    language: str = "en"
    text_content: Optional[str] = None
    source_s3_key: Optional[str] = None

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        allowed = {"transcript", "catalog", "manual", "faq", "other"}
        normalized = v.strip().lower()
        if normalized not in allowed:
            raise ValueError(f"source_type must be one of: {', '.join(sorted(allowed))}")
        return normalized

    @field_validator("text_content")
    @classmethod
    def validate_content_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("text_content cannot be empty when provided")
        return v

    @field_validator("source_s3_key")
    @classmethod
    def validate_s3_key_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("source_s3_key cannot be empty when provided")
        return v


class KnowledgeDocumentResponse(BaseModel):
    """Knowledge document response"""

    id: int
    supplier_id: int
    title: str
    source_type: str
    source_s3_key: Optional[str]
    language: str
    status: str
    chunk_count: int
    pinecone_namespace: str
    pinecone_document_id: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeQueryRequest(BaseModel):
    """Knowledge retrieval query request"""

    supplier_id: int
    query: str
    top_k: int = 5

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        if v < 1 or v > 20:
            raise ValueError("top_k must be between 1 and 20")
        return v


class KnowledgeMatch(BaseModel):
    """Single retrieved chunk match"""

    id: str
    score: float
    chunk_text: str
    source_title: Optional[str]
    source_type: Optional[str]
    chunk_index: Optional[int]


class KnowledgeQueryResponse(BaseModel):
    """Knowledge retrieval query response"""

    supplier_id: int
    namespace: str
    matches: list[KnowledgeMatch]


class RAGChatRequest(BaseModel):
    """RAG chat request"""

    supplier_id: int
    question: str
    language: str = "en"
    top_k: int = 5

    @field_validator("top_k")
    @classmethod
    def validate_chat_top_k(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("top_k must be between 1 and 10")
        return v


class RAGChatResponse(BaseModel):
    """RAG chat response"""

    supplier_id: int
    question: str
    answer: str
    language: str
    confidence_score: int
    should_escalate: bool
    matched_chunks: list[KnowledgeMatch]


class NotificationResponse(BaseModel):
    """In-app notification response"""

    id: int
    supplier_id: int
    conversation_id: Optional[int]
    notification_type: str
    title: str
    message: str
    is_read: int
    metadata_json: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeSupplierContextResponse(BaseModel):
    """Current supplier knowledge namespace context"""

    supplier_id: int
    namespace: str


class VisitorIntentEventCreateRequest(BaseModel):
    """Public visitor behavior event ingest payload"""

    supplier_id: int
    visitor_session_id: str
    event_type: str
    page_url: Optional[str] = None
    event_data: Optional[dict] = None
    session_duration_seconds: Optional[int] = None
    visitor_email: Optional[str] = None
    visitor_company: Optional[str] = None
    visitor_country: Optional[str] = None
    consent_given: bool = True


class VisitorIntentEventCreateResponse(BaseModel):
    """Response for visitor behavior event ingest"""

    accepted: bool
    queued_for_scoring: bool
    event_id: Optional[int] = None
    reason: Optional[str] = None


class VisitorIntentEventListResponse(BaseModel):
    """Visitor intent event item for supplier dashboard"""

    id: int
    supplier_id: int
    visitor_session_id: str
    visitor_email: Optional[str]
    visitor_company: Optional[str]
    visitor_country: Optional[str]
    event_type: str
    page_url: Optional[str]
    session_duration_seconds: Optional[int]
    intent_score: Optional[int]
    intent_level: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class VisitorIntentSummaryResponse(BaseModel):
    """Aggregate visitor intent metrics for supplier dashboard"""

    supplier_id: int
    total_events: int
    high_intent_count: int
    medium_intent_count: int
    avg_intent_score: float
    latest_event_at: Optional[datetime]
    generated_at: datetime


class VisitorIntentProviderBreakdown(BaseModel):
    """Provider source distribution in benchmark window"""

    rb2b_events: int
    leadfeeder_events: int
    unidentified_provider_events: int


class VisitorIntentRateMetrics(BaseModel):
    """Rate-based benchmark metrics (0.0 - 1.0)"""

    email_identified_rate: float
    company_identified_rate: float
    country_identified_rate: float
    intent_scored_rate: float
    high_or_medium_intent_rate: float
    provider_coverage_rate: float


class VisitorIntentQualityGates(BaseModel):
    """Sprint 5 benchmark quality gates"""

    provider_coverage_pass: bool
    identification_pass: bool
    scoring_pass: bool
    overall_pass: bool


class VisitorIntentBenchmarkResponse(BaseModel):
    """Visitor intent benchmark output for Sprint 5.10 validation"""

    supplier_id: int
    window_days: int
    total_events: int
    provider_breakdown: VisitorIntentProviderBreakdown
    rates: VisitorIntentRateMetrics
    quality_gates: VisitorIntentQualityGates
    generated_at: datetime


class VisitorIntentOpsMetricsResponse(BaseModel):
    """Operational metrics for Sprint 5 monitoring dashboard"""

    supplier_id: int
    window_hours: int
    total_events: int
    high_intent_events: int
    medium_intent_events: int
    unread_high_intent_notifications: int
    avg_intent_score: float
    alert_high_intent_spike: bool
    alert_unread_backlog: bool
    generated_at: datetime
