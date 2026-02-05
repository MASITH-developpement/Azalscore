"""Website lead model for capturing leads from website."""
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, ENUM
from datetime import datetime
import enum

from app.db.base import Base


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

    source = Column(ENUM('website_form', 'demo_request', 'contact_form', 'pricing_inquiry', 'newsletter',
                         name='lead_source', create_type=False), default='website_form')
    status = Column(ENUM('new', 'contacted', 'qualified', 'demo_scheduled', 'proposal_sent', 'won', 'lost',
                         name='lead_status', create_type=False), default='new', index=True)
    message = Column(Text, nullable=True)

    company_size = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    country = Column(String, nullable=True)

    visitor_session_id = Column(String, nullable=True)
    referrer_url = Column(String, nullable=True)
    utm_source = Column(String, nullable=True)
    utm_campaign = Column(String, nullable=True)

    assigned_to = Column(UUID(as_uuid=True), nullable=True)
    last_contact_date = Column(DateTime, nullable=True)
    next_follow_up = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    converted_to_customer = Column(Boolean, default=False)
    customer_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
