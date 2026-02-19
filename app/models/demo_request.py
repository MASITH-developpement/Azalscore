"""Demo request model for scheduling demos."""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Date
from datetime import datetime

from app.db.base import Base
from app.core.types import UniversalUUID


class DemoRequest(Base):
    """Demo requests from website."""

    __tablename__ = "demo_requests"

    # id is automatically provided by UUIDMixin in Base
    lead_id = Column(UniversalUUID(), nullable=True)

    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=False)

    preferred_date = Column(Date, nullable=True)
    preferred_time = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    modules_interested = Column(Text, nullable=True)

    company_size = Column(String, nullable=True)
    current_solution = Column(String, nullable=True)
    specific_needs = Column(Text, nullable=True)

    scheduled = Column(Boolean, default=False)
    demo_date = Column(DateTime, nullable=True)
    demo_completed = Column(Boolean, default=False)
    meeting_link = Column(String, nullable=True)
    assigned_to = Column(UniversalUUID(), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
