"""Website visitor tracking model for analytics."""
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
from datetime import datetime

from app.db.base_class import Base


class WebsiteVisitor(Base):
    """Track website visitors for analytics."""

    __tablename__ = "website_visitors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, unique=True, nullable=False, index=True)
    visitor_ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    referrer = Column(String, nullable=True)
    landing_page = Column(String, nullable=False)
    current_page = Column(String, nullable=True)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    browser = Column(String, nullable=True)
    os = Column(String, nullable=True)

    page_views = Column(Integer, default=1)
    time_on_site = Column(Integer, default=0)
    pages_visited = Column(JSON, default=list)

    utm_source = Column(String, nullable=True)
    utm_medium = Column(String, nullable=True)
    utm_campaign = Column(String, nullable=True)
    utm_term = Column(String, nullable=True)
    utm_content = Column(String, nullable=True)

    converted_to_lead = Column(Boolean, default=False)
    lead_id = Column(UUID(as_uuid=True), nullable=True)

    first_visit = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_visit = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_visitor_session", "session_id"),
        Index("idx_visitor_date", "first_visit"),
        Index("idx_visitor_converted", "converted_to_lead"),
    )
