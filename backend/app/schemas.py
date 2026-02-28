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
