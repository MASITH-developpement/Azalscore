"""Website tracking API for analytics, leads, and demo requests."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.website_visitor import WebsiteVisitor
from app.models.website_lead import WebsiteLead
from app.models.demo_request import DemoRequest

router = APIRouter(prefix="/website", tags=["Website Tracking"])


class VisitorTrackingCreate(BaseModel):
    """Schema for tracking a visitor."""

    session_id: str
    landing_page: str
    current_page: Optional[str] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class LeadCreate(BaseModel):
    """Schema for creating a lead."""

    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    message: Optional[str] = None
    source: str = "website_form"
    visitor_session_id: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None


class DemoRequestCreate(BaseModel):
    """Schema for requesting a demo."""

    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    company: str
    company_size: Optional[str] = None
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    modules_interested: Optional[List[str]] = None
    specific_needs: Optional[str] = None
    current_solution: Optional[str] = None
    visitor_session_id: Optional[str] = None


class ContactFormCreate(BaseModel):
    """Schema for contact form submission."""

    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: Optional[str] = None
    message: str
    visitor_session_id: Optional[str] = None


@router.post("/track-visit")
async def track_visitor(
    visitor_data: VisitorTrackingCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Track website visitor for analytics."""
    visitor = (
        db.query(WebsiteVisitor)
        .filter(WebsiteVisitor.session_id == visitor_data.session_id)
        .first()
    )

    if visitor:
        visitor.current_page = visitor_data.current_page
        visitor.page_views += 1
        visitor.last_visit = datetime.utcnow()
        if visitor_data.current_page:
            pages = visitor.pages_visited or []
            pages.append(
                {
                    "page": visitor_data.current_page,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            visitor.pages_visited = pages
    else:
        visitor = WebsiteVisitor(
            session_id=visitor_data.session_id,
            visitor_ip=request.client.host if request.client else None,
            landing_page=visitor_data.landing_page,
            current_page=visitor_data.current_page,
            referrer=visitor_data.referrer,
            user_agent=visitor_data.user_agent,
            device_type=visitor_data.device_type,
            utm_source=visitor_data.utm_source,
            utm_medium=visitor_data.utm_medium,
            utm_campaign=visitor_data.utm_campaign,
        )
        db.add(visitor)

    db.commit()
    return {"status": "tracked", "session_id": visitor_data.session_id}


@router.post("/leads", response_model=dict)
async def create_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_db),
):
    """Create a new lead from website."""
    lead = WebsiteLead(
        full_name=lead_data.full_name,
        email=lead_data.email,
        phone=lead_data.phone,
        company=lead_data.company,
        job_title=lead_data.job_title,
        message=lead_data.message,
        source=lead_data.source,
        visitor_session_id=lead_data.visitor_session_id,
        company_size=lead_data.company_size,
        industry=lead_data.industry,
        status="new",
    )

    db.add(lead)

    if lead_data.visitor_session_id:
        visitor = (
            db.query(WebsiteVisitor)
            .filter(WebsiteVisitor.session_id == lead_data.visitor_session_id)
            .first()
        )
        if visitor:
            visitor.converted_to_lead = True
            visitor.lead_id = lead.id

    db.commit()
    db.refresh(lead)

    return {
        "success": True,
        "lead_id": str(lead.id),
        "message": "Merci ! Nous vous contacterons sous 24h.",
    }


@router.post("/demo-requests", response_model=dict)
async def create_demo_request(
    demo_data: DemoRequestCreate,
    db: Session = Depends(get_db),
):
    """Create a demo request."""
    lead = WebsiteLead(
        full_name=demo_data.full_name,
        email=demo_data.email,
        phone=demo_data.phone,
        company=demo_data.company,
        company_size=demo_data.company_size,
        source="demo_request",
        status="demo_scheduled",
        visitor_session_id=demo_data.visitor_session_id,
    )
    db.add(lead)
    db.flush()

    demo = DemoRequest(
        lead_id=lead.id,
        full_name=demo_data.full_name,
        email=demo_data.email,
        phone=demo_data.phone,
        company=demo_data.company,
        company_size=demo_data.company_size,
        preferred_date=demo_data.preferred_date,
        preferred_time=demo_data.preferred_time,
        modules_interested=(
            str(demo_data.modules_interested) if demo_data.modules_interested else None
        ),
        specific_needs=demo_data.specific_needs,
        current_solution=demo_data.current_solution,
    )
    db.add(demo)
    db.commit()

    return {
        "success": True,
        "demo_id": str(demo.id),
        "message": "Demande de démo reçue ! Nous vous contacterons pour planifier.",
    }


@router.post("/contact", response_model=dict)
async def create_contact_request(
    contact_data: ContactFormCreate,
    db: Session = Depends(get_db),
):
    """Handle contact form submission."""
    lead = WebsiteLead(
        full_name=contact_data.full_name,
        email=contact_data.email,
        phone=contact_data.phone,
        message=f"{contact_data.subject or 'Contact'}: {contact_data.message}",
        source="contact_form",
        visitor_session_id=contact_data.visitor_session_id,
        status="new",
    )

    db.add(lead)
    db.commit()

    return {
        "success": True,
        "message": "Message envoyé ! Nous vous répondrons rapidement.",
    }


@router.get("/analytics/summary")
async def get_analytics_summary(db: Session = Depends(get_db)):
    """Get website analytics summary for dashboard."""
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)

    total_visitors = db.query(func.count(WebsiteVisitor.id)).scalar() or 0
    visitors_this_week = (
        db.query(func.count(WebsiteVisitor.id))
        .filter(WebsiteVisitor.first_visit >= week_ago)
        .scalar()
        or 0
    )

    total_leads = db.query(func.count(WebsiteLead.id)).scalar() or 0
    leads_this_week = (
        db.query(func.count(WebsiteLead.id))
        .filter(WebsiteLead.created_at >= week_ago)
        .scalar()
        or 0
    )

    total_demos = db.query(func.count(DemoRequest.id)).scalar() or 0
    demos_this_week = (
        db.query(func.count(DemoRequest.id))
        .filter(DemoRequest.created_at >= week_ago)
        .scalar()
        or 0
    )

    conversion_rate = (total_leads / total_visitors * 100) if total_visitors > 0 else 0

    return {
        "visitors": {"total": total_visitors, "this_week": visitors_this_week},
        "leads": {"total": total_leads, "this_week": leads_this_week},
        "demos": {"total": total_demos, "this_week": demos_this_week},
        "conversion_rate": round(conversion_rate, 2),
    }
