"""Website lead model for capturing leads from website."""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.db.base_class import Base


class LeadSource(str, enum.Enum):
    """Source of the lead."""

    WEBSITE_FORM = "website_form"
    DEMO_REQUEST = "demo_request"
    CONTACT_FORM = "contact_form"
    PRICING_INQUIRY = "pricing_inquiry"
    NEWSLETTER = "newsletter"


class LeadStatus(str, enum.Enum):
    """Status of the lead in the sales pipeline."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    DEMO_SCHEDULED = "demo_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    WON = "won"
    LOST = "lost"


class WebsiteLead(Base):
    """Leads captured from website."""

    __tablename__ = "website_leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    job_title = Column(String, nullable=True)

    source = Column(Enum(LeadSource), default=LeadSource.WEBSITE_FORM)
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW, index=True)
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
