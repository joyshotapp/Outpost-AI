"""Buyer model"""

from sqlalchemy import Boolean, Column, Integer, String, Text

from app.database import Base
from app.models.base import BaseModel


class Buyer(BaseModel):
    """Buyer profile model"""

    __tablename__ = "buyers"

    # Basic Info
    user_id = Column(Integer, nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    website = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    # Location & Industry
    country = Column(String(2), nullable=False, index=True)  # ISO country code
    city = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True, index=True)

    # Sourcing Info
    company_description = Column(Text, nullable=True)
    number_of_employees = Column(Integer, nullable=True)
    primary_sourcing_needs = Column(String(500), nullable=True)  # Comma-separated
    annual_sourcing_budget = Column(Integer, nullable=True)  # In USD

    # Sourcing Preferences
    preferred_payment_terms = Column(String(100), nullable=True)
    preferred_shipping_method = Column(String(100), nullable=True)
    import_experience = Column(String(50), nullable=True)  # 'new', 'experienced', 'expert'

    # Status
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Buyer {self.company_name} ({self.country})>"
