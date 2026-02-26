"""Website lead model for capturing leads from website."""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum as SQLEnum
from datetime import datetime
import enum

from app.db.base import Base
from app.core.types import UniversalUUID


class LeadSource(str, enum.Enum):
    """Source of the lead."""

    website_form = "website_form"
    demo_request = "demo_request"
    contact_form = "contact_form"
    pricing_inquiry = "pricing_inquiry"
    newsletter = "newsletter"


class LeadStatus(str, enum.Enum):
    """Status of the lead in the sales pipeline."""

    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    demo_scheduled = "demo_scheduled"
    proposal_sent = "proposal_sent"
    won = "won"
    lost = "lost"


class WebsiteLead(Base):
    """Leads captured from website."""

    __tablename__ = "website_leads"

    # id is automatically provided by UUIDMixin in Base
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    job_title = Column(String, nullable=True)

    source = Column(SQLEnum(LeadSource), default=LeadSource.website_form)
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.new, index=True)
    message = Column(Text, nullable=True)

    company_size = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    country = Column(String, nullable=True)

    visitor_session_id = Column(String, nullable=True)
    referrer_url = Column(String, nullable=True)
    utm_source = Column(String, nullable=True)
    utm_campaign = Column(String, nullable=True)

    assigned_to = Column(UniversalUUID(), nullable=True)
    last_contact_date = Column(DateTime, nullable=True)
    next_follow_up = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    converted_to_customer = Column(Boolean, default=False)
    customer_id = Column(UniversalUUID(), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
