"""Supplier model"""

from sqlalchemy import Boolean, Column, Integer, String, Text

from app.database import Base
from app.models.base import BaseModel


class Supplier(BaseModel):
    """Supplier profile model"""

    __tablename__ = "suppliers"

    # Basic Info
    user_id = Column(Integer, nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    company_slug = Column(String(255), unique=True, nullable=False, index=True)
    website = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    # Location & Industry
    country = Column(String(2), nullable=False, index=True)  # ISO country code
    city = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True, index=True)

    # Company Details
    company_description = Column(Text, nullable=True)
    number_of_employees = Column(Integer, nullable=True)
    established_year = Column(Integer, nullable=True)
    certifications = Column(String(500), nullable=True)  # Comma-separated

    # Capabilities
    main_products = Column(String(500), nullable=True)  # Comma-separated
    manufacturing_capacity = Column(String(255), nullable=True)
    lead_time_days = Column(Integer, nullable=True)

    # Status
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    view_count = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<Supplier {self.company_name} ({self.country})>"
