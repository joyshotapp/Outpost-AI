"""Pydantic schemas for API request/response validation"""

import re
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
    created_at: str
    updated_at: str

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
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


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
    created_at: str
    updated_at: str

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
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
