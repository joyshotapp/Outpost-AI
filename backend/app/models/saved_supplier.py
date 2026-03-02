"""SavedSupplier model — Sprint 10 (10.6: buyer bookmarks)."""

from sqlalchemy import Column, Integer, String, UniqueConstraint

from app.models.base import BaseModel


class SavedSupplier(BaseModel):
    """A buyer's saved/bookmarked supplier."""

    __tablename__ = "saved_suppliers"
    __table_args__ = (
        UniqueConstraint("buyer_id", "supplier_id", name="uq_saved_buyer_supplier"),
    )

    buyer_id = Column(Integer, nullable=False, index=True)
    supplier_id = Column(Integer, nullable=False, index=True)
    notes = Column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<SavedSupplier buyer={self.buyer_id} supplier={self.supplier_id}>"
