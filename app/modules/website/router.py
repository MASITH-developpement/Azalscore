"""
AZALS MODULE T8 - Router Site Web
==================================

API REST pour le site web officiel.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user

from .service import get_website_service
from .schemas import (
    SitePageCreate, SitePageUpdate, SitePageResponse, SitePageListResponse,
    BlogPostCreate, BlogPostUpdate, BlogPostResponse, BlogPostListResponse,
    TestimonialCreate, TestimonialUpdate, TestimonialResponse,
    ContactSubmissionCreate, ContactSubmissionUpdate, ContactSubmissionResponse,
    NewsletterSubscribeRequest, NewsletterUnsubscribeRequest, NewsletterSubscriberResponse,
    SiteMediaCreate, SiteMediaUpdate, SiteMediaResponse,
    SiteSEOUpdate, SiteSEOResponse,
    SiteAnalyticsResponse, AnalyticsDashboardResponse,
    PublishRequest, PublicSiteConfigResponse
)

router = APIRouter(prefix="/website", tags=["Website"])


# ============================================================================
# PAGES
# ============================================================================

@router.post("/pages", response_model=SitePageResponse, status_code=201)
def create_page(
    data: SitePageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer une page du site."""
    service = get_website_service(db, current_user["tenant_id"], current_user["user_id"])
    return service.create_page(data)


@router.get("/pages", response_model=List[SitePageListResponse])
def list_pages(
    page_type: Optional[str] = None,
    status: Optional[str] = None,
    parent_id: Optional[int] = None,
    show_in_menu: Optional[bool] = None,
    language: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les pages."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.list_pages(page_type, status, parent_id, show_in_menu, language, skip, limit)


@router.get("/pages/{page_id}", response_model=SitePageResponse)
def get_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer une page."""
    service = get_website_service(db, current_user["tenant_id"])
    page = service.get_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page non trouvée")
    return page


@router.get("/pages/slug/{slug}", response_model=SitePageResponse)
def get_page_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer une page par slug."""
    service = get_website_service(db, current_user["tenant_id"])
    page = service.get_page_by_slug(slug)
    if not page:
        raise HTTPException(status_code=404, detail="Page non trouvée")
    return page


@router.put("/pages/{page_id}", response_model=SitePageResponse)
def update_page(
    page_id: int,
    data: SitePageUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour une page."""
    service = get_website_service(db, current_user["tenant_id"], current_user["user_id"])
    page = service.update_page(page_id, data)
    if not page:
        raise HTTPException(status_code=404, detail="Page non trouvée ou système")
    return page


@router.post("/pages/{page_id}/publish", response_model=SitePageResponse)
def publish_page(
    page_id: int,
    data: PublishRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Publier/dépublier une page."""
    service = get_website_service(db, current_user["tenant_id"])
    page = service.publish_page(page_id, data.publish)
    if not page:
        raise HTTPException(status_code=404, detail="Page non trouvée")
    return page


@router.delete("/pages/{page_id}", status_code=204)
def delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Supprimer une page."""
    service = get_website_service(db, current_user["tenant_id"])
    if not service.delete_page(page_id):
        raise HTTPException(status_code=404, detail="Page non trouvée ou système")


# ============================================================================
# BLOG
# ============================================================================

@router.post("/blog/posts", response_model=BlogPostResponse, status_code=201)
def create_blog_post(
    data: BlogPostCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer un article de blog."""
    service = get_website_service(db, current_user["tenant_id"], current_user["user_id"])
    return service.create_blog_post(data)


@router.get("/blog/posts", response_model=List[BlogPostListResponse])
def list_blog_posts(
    content_type: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    status: Optional[str] = None,
    is_featured: Optional[bool] = None,
    language: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les articles."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.list_blog_posts(
        content_type, category, tag, status, is_featured, language, skip, limit
    )


@router.get("/blog/categories")
def get_blog_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les catégories du blog."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.get_blog_categories()


@router.get("/blog/posts/{post_id}", response_model=BlogPostResponse)
def get_blog_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un article."""
    service = get_website_service(db, current_user["tenant_id"])
    post = service.get_blog_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return post


@router.get("/blog/posts/slug/{slug}", response_model=BlogPostResponse)
def get_blog_post_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un article par slug."""
    service = get_website_service(db, current_user["tenant_id"])
    post = service.get_blog_post_by_slug(slug)
    if not post:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return post


@router.put("/blog/posts/{post_id}", response_model=BlogPostResponse)
def update_blog_post(
    post_id: int,
    data: BlogPostUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un article."""
    service = get_website_service(db, current_user["tenant_id"], current_user["user_id"])
    post = service.update_blog_post(post_id, data)
    if not post:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return post


@router.post("/blog/posts/{post_id}/publish", response_model=BlogPostResponse)
def publish_blog_post(
    post_id: int,
    data: PublishRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Publier/dépublier un article."""
    service = get_website_service(db, current_user["tenant_id"])
    post = service.publish_blog_post(post_id, data.publish)
    if not post:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return post


@router.delete("/blog/posts/{post_id}", status_code=204)
def delete_blog_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Supprimer un article."""
    service = get_website_service(db, current_user["tenant_id"])
    if not service.delete_blog_post(post_id):
        raise HTTPException(status_code=404, detail="Article non trouvé")


# ============================================================================
# TESTIMONIALS
# ============================================================================

@router.post("/testimonials", response_model=TestimonialResponse, status_code=201)
def create_testimonial(
    data: TestimonialCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer un témoignage."""
    service = get_website_service(db, current_user["tenant_id"], current_user["user_id"])
    return service.create_testimonial(data)


@router.get("/testimonials", response_model=List[TestimonialResponse])
def list_testimonials(
    industry: Optional[str] = None,
    is_featured: Optional[bool] = None,
    show_on_homepage: Optional[bool] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les témoignages."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.list_testimonials(industry, is_featured, show_on_homepage, status, skip, limit)


@router.get("/testimonials/{testimonial_id}", response_model=TestimonialResponse)
def get_testimonial(
    testimonial_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un témoignage."""
    service = get_website_service(db, current_user["tenant_id"])
    testimonial = service.get_testimonial(testimonial_id)
    if not testimonial:
        raise HTTPException(status_code=404, detail="Témoignage non trouvé")
    return testimonial


@router.put("/testimonials/{testimonial_id}", response_model=TestimonialResponse)
def update_testimonial(
    testimonial_id: int,
    data: TestimonialUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un témoignage."""
    service = get_website_service(db, current_user["tenant_id"], current_user["user_id"])
    testimonial = service.update_testimonial(testimonial_id, data)
    if not testimonial:
        raise HTTPException(status_code=404, detail="Témoignage non trouvé")
    return testimonial


@router.post("/testimonials/{testimonial_id}/publish", response_model=TestimonialResponse)
def publish_testimonial(
    testimonial_id: int,
    data: PublishRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Publier/dépublier un témoignage."""
    service = get_website_service(db, current_user["tenant_id"])
    testimonial = service.publish_testimonial(testimonial_id, data.publish)
    if not testimonial:
        raise HTTPException(status_code=404, detail="Témoignage non trouvé")
    return testimonial


@router.delete("/testimonials/{testimonial_id}", status_code=204)
def delete_testimonial(
    testimonial_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Supprimer un témoignage."""
    service = get_website_service(db, current_user["tenant_id"])
    if not service.delete_testimonial(testimonial_id):
        raise HTTPException(status_code=404, detail="Témoignage non trouvé")


# ============================================================================
# CONTACT
# ============================================================================

@router.post("/contact", response_model=ContactSubmissionResponse, status_code=201)
def submit_contact_form(
    data: ContactSubmissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Soumettre un formulaire de contact."""
    service = get_website_service(db, current_user["tenant_id"])

    # Anti-spam basique (honeypot)
    if hasattr(data, "honeypot") and data.custom_fields and data.custom_fields.get("honeypot"):
        raise HTTPException(status_code=400, detail="Soumission invalide")

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    referrer = request.headers.get("referer")

    return service.create_contact_submission(data, ip_address, user_agent, referrer)


@router.get("/contact/submissions", response_model=List[ContactSubmissionResponse])
def list_contact_submissions(
    form_category: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les soumissions."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.list_contact_submissions(form_category, status, assigned_to, skip, limit)


@router.get("/contact/submissions/{submission_id}", response_model=ContactSubmissionResponse)
def get_contact_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer une soumission."""
    service = get_website_service(db, current_user["tenant_id"])
    submission = service.get_contact_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Soumission non trouvée")

    # Marquer comme lu
    service.mark_submission_read(submission_id)
    return submission


@router.put("/contact/submissions/{submission_id}", response_model=ContactSubmissionResponse)
def update_contact_submission(
    submission_id: int,
    data: ContactSubmissionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour une soumission."""
    service = get_website_service(db, current_user["tenant_id"], current_user["user_id"])
    submission = service.update_contact_submission(submission_id, data)
    if not submission:
        raise HTTPException(status_code=404, detail="Soumission non trouvée")
    return submission


@router.get("/contact/stats")
def get_contact_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Statistiques des contacts."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.get_contact_stats()


# ============================================================================
# NEWSLETTER
# ============================================================================

@router.post("/newsletter/subscribe", response_model=NewsletterSubscriberResponse, status_code=201)
def subscribe_newsletter(
    data: NewsletterSubscribeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """S'abonner à la newsletter."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.subscribe_newsletter(data)


@router.post("/newsletter/verify/{token}")
def verify_newsletter(
    token: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Vérifier l'email d'un abonné."""
    service = get_website_service(db, current_user["tenant_id"])
    subscriber = service.verify_newsletter(token)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Token invalide")
    return {"message": "Email vérifié", "email": subscriber.email}


@router.post("/newsletter/unsubscribe")
def unsubscribe_newsletter(
    data: NewsletterUnsubscribeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Se désabonner de la newsletter."""
    service = get_website_service(db, current_user["tenant_id"])
    subscriber = service.unsubscribe_newsletter(data.token)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Token invalide")
    return {"message": "Désabonnement effectué", "email": subscriber.email}


@router.get("/newsletter/subscribers", response_model=List[NewsletterSubscriberResponse])
def list_newsletter_subscribers(
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les abonnés newsletter."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.list_newsletter_subscribers(is_active, is_verified, skip, limit)


@router.get("/newsletter/stats")
def get_newsletter_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Statistiques newsletter."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.get_newsletter_stats()


# ============================================================================
# MEDIA
# ============================================================================

@router.post("/media", response_model=SiteMediaResponse, status_code=201)
def create_media(
    data: SiteMediaCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer un média."""
    service = get_website_service(db, current_user["tenant_id"], current_user["user_id"])
    return service.create_media(data)


@router.get("/media", response_model=List[SiteMediaResponse])
def list_media(
    media_type: Optional[str] = None,
    folder: Optional[str] = None,
    tag: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les médias."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.list_media(media_type, folder, tag, skip, limit)


@router.get("/media/{media_id}", response_model=SiteMediaResponse)
def get_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un média."""
    service = get_website_service(db, current_user["tenant_id"])
    media = service.get_media(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Média non trouvé")
    return media


@router.put("/media/{media_id}", response_model=SiteMediaResponse)
def update_media(
    media_id: int,
    data: SiteMediaUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un média."""
    service = get_website_service(db, current_user["tenant_id"], current_user["user_id"])
    media = service.update_media(media_id, data)
    if not media:
        raise HTTPException(status_code=404, detail="Média non trouvé")
    return media


@router.delete("/media/{media_id}", status_code=204)
def delete_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Supprimer un média."""
    service = get_website_service(db, current_user["tenant_id"])
    if not service.delete_media(media_id):
        raise HTTPException(status_code=404, detail="Média non trouvé")


# ============================================================================
# SEO
# ============================================================================

@router.get("/seo", response_model=SiteSEOResponse)
def get_seo_config(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer la configuration SEO."""
    service = get_website_service(db, current_user["tenant_id"])
    seo = service.get_seo_config()
    if not seo:
        raise HTTPException(status_code=404, detail="Configuration SEO non trouvée")
    return seo


@router.put("/seo", response_model=SiteSEOResponse)
def update_seo_config(
    data: SiteSEOUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour la configuration SEO."""
    service = get_website_service(db, current_user["tenant_id"], current_user["user_id"])
    return service.update_seo_config(data)


# ============================================================================
# ANALYTICS
# ============================================================================

@router.get("/analytics/dashboard", response_model=AnalyticsDashboardResponse)
def get_analytics_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Dashboard analytics."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.get_analytics_dashboard(days)


@router.get("/analytics", response_model=List[SiteAnalyticsResponse])
def get_analytics(
    start_date: datetime,
    end_date: datetime,
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les analytics pour une période."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.get_analytics(start_date, end_date, period)


@router.post("/analytics/record")
def record_analytics(
    date: datetime,
    period: str = "daily",
    data: dict = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Enregistrer des données analytics."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.record_analytics(date, period, data)


# ============================================================================
# PUBLIC CONFIG
# ============================================================================

@router.get("/config", response_model=PublicSiteConfigResponse)
def get_public_site_config(
    language: str = "fr",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Configuration publique du site."""
    service = get_website_service(db, current_user["tenant_id"])
    return service.get_public_site_config(language)


@router.get("/homepage", response_model=SitePageResponse)
def get_homepage(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer la page d'accueil."""
    service = get_website_service(db, current_user["tenant_id"])
    page = service.get_homepage()
    if not page:
        raise HTTPException(status_code=404, detail="Page d'accueil non trouvée")
    return page
