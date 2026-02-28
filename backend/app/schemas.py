"""Pydantic schemas for API request/response validation"""

from typing import Optional

from pydantic import BaseModel, EmailStr


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

    user_id: int
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
