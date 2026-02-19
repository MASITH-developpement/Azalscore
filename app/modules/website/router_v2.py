"""
AZALSCORE MODULE WEBSITE - Router v2 CORE SaaS
=============================================

Endpoints pour le site web officiel AZALSCORE.
Migration CORE SaaS v2 avec SaaSContext.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.core.database import get_db

from .models import ContentType, FormCategory, MediaType, PageType, PublishStatus, SubmissionStatus
from .schemas import (
    AnalyticsDashboardResponse,
    BlogPostCreate,
    BlogPostListResponse,
    BlogPostResponse,
    BlogPostUpdate,
    ContactSubmissionCreate,
    ContactSubmissionResponse,
    ContactSubmissionUpdate,
    NewsletterSubscribeRequest,
    NewsletterSubscriberResponse,
    PublicSiteConfigResponse,
    SiteAnalyticsResponse,
    SiteMediaCreate,
    SiteMediaResponse,
    SiteMediaUpdate,
    SitePageCreate,
    SitePageListResponse,
    SitePageResponse,
    SitePageUpdate,
    SiteSEOResponse,
    SiteSEOUpdate,
    TestimonialCreate,
    TestimonialResponse,
    TestimonialUpdate,
)
from .service import WebsiteService

router = APIRouter(prefix="/v2/website", tags=["Website v2 - CORE SaaS"])


# ============================================================================
# FACTORY SERVICE
# ============================================================================

def get_website_service(db: Session, tenant_id: str, user_id: str) -> WebsiteService:
    """Factory pour créer un service Website avec SaaSContext."""
    return WebsiteService(db, tenant_id, user_id)


# ============================================================================
# PAGES
# ============================================================================

@router.post("/pages", response_model=SitePageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    data: SitePageCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Crée une nouvelle page du site.

    **Permissions requises:** website.pages.create
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        page = service.create_page(
            title=data.title,
            slug=data.slug,
            page_type=data.page_type,
            content=data.content or {},
            meta_description=data.meta_description,
            meta_keywords=data.meta_keywords,
            created_by=service.user_id
        )
        return page
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pages", response_model=List[SitePageListResponse])
async def list_pages(
    page_type: PageType | None = Query(None, description="Filtrer par type"),
    published_only: bool = Query(False, description="Seulement publiées"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les pages du site.

    **Permissions requises:** website.pages.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    pages = service.list_pages(page_type=page_type, published_only=published_only)

    return pages


@router.get("/pages/{page_id}", response_model=SitePageResponse)
async def get_page(
    page_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère une page par ID.

    **Permissions requises:** website.pages.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    page = service.get_page(int(page_id))

    if not page:
        raise HTTPException(status_code=404, detail="Page non trouvée")

    return page


@router.get("/pages/slug/{slug}", response_model=SitePageResponse)
async def get_page_by_slug(
    slug: str,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère une page par slug.

    **Permissions requises:** website.pages.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    page = service.get_page_by_slug(slug)

    if not page:
        raise HTTPException(status_code=404, detail="Page non trouvée")

    return page


@router.put("/pages/{page_id}", response_model=SitePageResponse)
async def update_page(
    page_id: UUID,
    data: SitePageUpdate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met à jour une page.

    **Permissions requises:** website.pages.update
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        update_data = data.model_dump(exclude_unset=True)
        page = service.update_page(int(page_id), **update_data)
        return page
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/pages/{page_id}/publish", response_model=SitePageResponse)
async def publish_page(
    page_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Publie une page.

    **Permissions requises:** website.pages.publish
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        page = service.publish_page(int(page_id), published_by=service.user_id)
        return page
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Supprime une page.

    **Permissions requises:** website.pages.delete
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    success = service.delete_page(int(page_id))

    if not success:
        raise HTTPException(status_code=404, detail="Page non trouvée")

    return None


# ============================================================================
# BLOG POSTS
# ============================================================================

@router.post("/blog/posts", response_model=BlogPostResponse, status_code=status.HTTP_201_CREATED)
async def create_blog_post(
    data: BlogPostCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Crée un article de blog.

    **Permissions requises:** website.blog.create
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        post = service.create_blog_post(
            title=data.title,
            slug=data.slug,
            content=data.content,
            excerpt=data.excerpt,
            category=data.category,
            tags=data.tags or [],
            featured_image_url=data.featured_image_url,
            author_id=service.user_id,
            meta_description=data.meta_description,
            meta_keywords=data.meta_keywords
        )
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/blog/posts", response_model=List[BlogPostListResponse])
async def list_blog_posts(
    category: str | None = Query(None, description="Filtrer par catégorie"),
    tag: str | None = Query(None, description="Filtrer par tag"),
    published_only: bool = Query(False, description="Seulement publiés"),
    limit: int = Query(50, ge=1, le=100, description="Nombre maximum"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les articles de blog.

    **Permissions requises:** website.blog.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    posts = service.list_blog_posts(
        category=category,
        tag=tag,
        published_only=published_only,
        limit=limit
    )

    return posts


@router.get("/blog/categories")
async def list_blog_categories(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les catégories de blog.

    **Permissions requises:** website.blog.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    categories = service.get_blog_categories()

    return {"categories": categories}


@router.get("/blog/posts/{post_id}", response_model=BlogPostResponse)
async def get_blog_post(
    post_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère un article de blog par ID.

    **Permissions requises:** website.blog.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    post = service.get_blog_post(int(post_id))

    if not post:
        raise HTTPException(status_code=404, detail="Article non trouvé")

    return post


@router.get("/blog/posts/slug/{slug}", response_model=BlogPostResponse)
async def get_blog_post_by_slug(
    slug: str,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère un article de blog par slug.

    **Permissions requises:** website.blog.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    post = service.get_blog_post_by_slug(slug)

    if not post:
        raise HTTPException(status_code=404, detail="Article non trouvé")

    return post


@router.put("/blog/posts/{post_id}", response_model=BlogPostResponse)
async def update_blog_post(
    post_id: UUID,
    data: BlogPostUpdate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met à jour un article de blog.

    **Permissions requises:** website.blog.update
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        update_data = data.model_dump(exclude_unset=True)
        post = service.update_blog_post(int(post_id), **update_data)
        return post
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/blog/posts/{post_id}/publish", response_model=BlogPostResponse)
async def publish_blog_post(
    post_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Publie un article de blog.

    **Permissions requises:** website.blog.publish
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        post = service.publish_blog_post(int(post_id), published_by=service.user_id)
        return post
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/blog/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog_post(
    post_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Supprime un article de blog.

    **Permissions requises:** website.blog.delete
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    success = service.delete_blog_post(int(post_id))

    if not success:
        raise HTTPException(status_code=404, detail="Article non trouvé")

    return None


# ============================================================================
# TESTIMONIALS
# ============================================================================

@router.post("/testimonials", response_model=TestimonialResponse, status_code=status.HTTP_201_CREATED)
async def create_testimonial(
    data: TestimonialCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Crée un témoignage.

    **Permissions requises:** website.testimonials.create
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        testimonial = service.create_testimonial(
            author_name=data.author_name,
            author_role=data.author_role,
            company=data.company,
            content=data.content,
            rating=data.rating or 5,
            created_by=service.user_id,
            author_photo_url=data.author_photo_url
        )
        return testimonial
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/testimonials", response_model=List[TestimonialResponse])
async def list_testimonials(
    published_only: bool = Query(False, description="Seulement publiés"),
    limit: int = Query(50, ge=1, le=100, description="Nombre maximum"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les témoignages.

    **Permissions requises:** website.testimonials.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    testimonials = service.list_testimonials(published_only=published_only, limit=limit)

    return testimonials


@router.get("/testimonials/{testimonial_id}", response_model=TestimonialResponse)
async def get_testimonial(
    testimonial_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère un témoignage par ID.

    **Permissions requises:** website.testimonials.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    testimonial = service.get_testimonial(int(testimonial_id))

    if not testimonial:
        raise HTTPException(status_code=404, detail="Témoignage non trouvé")

    return testimonial


@router.put("/testimonials/{testimonial_id}", response_model=TestimonialResponse)
async def update_testimonial(
    testimonial_id: UUID,
    data: TestimonialUpdate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met à jour un témoignage.

    **Permissions requises:** website.testimonials.update
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        update_data = data.model_dump(exclude_unset=True)
        testimonial = service.update_testimonial(int(testimonial_id), **update_data)
        return testimonial
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/testimonials/{testimonial_id}/publish", response_model=TestimonialResponse)
async def publish_testimonial(
    testimonial_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Publie un témoignage.

    **Permissions requises:** website.testimonials.publish
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        testimonial = service.publish_testimonial(int(testimonial_id), published_by=service.user_id)
        return testimonial
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/testimonials/{testimonial_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_testimonial(
    testimonial_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Supprime un témoignage.

    **Permissions requises:** website.testimonials.delete
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    success = service.delete_testimonial(int(testimonial_id))

    if not success:
        raise HTTPException(status_code=404, detail="Témoignage non trouvé")

    return None


# ============================================================================
# CONTACT SUBMISSIONS
# ============================================================================

@router.post("/contact", response_model=ContactSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact_form(
    data: ContactSubmissionCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Soumet un formulaire de contact.

    **Permissions requises:** Aucune (endpoint public)
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        submission = service.create_contact_submission(
            name=data.name,
            email=data.email,
            subject=data.subject,
            message=data.message,
            category=data.category or FormCategory.GENERAL,
            phone=data.phone,
            company=data.company
        )
        return submission
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contact/submissions", response_model=List[ContactSubmissionResponse])
async def list_contact_submissions(
    category: FormCategory | None = Query(None, description="Filtrer par catégorie"),
    status: SubmissionStatus | None = Query(None, description="Filtrer par statut"),
    limit: int = Query(50, ge=1, le=100, description="Nombre maximum"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les soumissions de contact.

    **Permissions requises:** website.contact.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    submissions = service.list_contact_submissions(
        category=category,
        status=status,
        limit=limit
    )

    return submissions


@router.get("/contact/submissions/{submission_id}", response_model=ContactSubmissionResponse)
async def get_contact_submission(
    submission_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère une soumission de contact par ID.

    **Permissions requises:** website.contact.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    submission = service.get_contact_submission(int(submission_id))

    if not submission:
        raise HTTPException(status_code=404, detail="Soumission non trouvée")

    return submission


@router.put("/contact/submissions/{submission_id}", response_model=ContactSubmissionResponse)
async def update_contact_submission(
    submission_id: UUID,
    data: ContactSubmissionUpdate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met à jour une soumission de contact.

    **Permissions requises:** website.contact.update
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        update_data = data.model_dump(exclude_unset=True)
        submission = service.update_contact_submission(int(submission_id), **update_data)
        return submission
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/contact/stats")
async def get_contact_stats(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère les statistiques des contacts.

    **Permissions requises:** website.contact.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    stats = service.get_contact_stats()

    return stats


# ============================================================================
# NEWSLETTER
# ============================================================================

@router.post("/newsletter/subscribe", response_model=NewsletterSubscriberResponse, status_code=status.HTTP_201_CREATED)
async def subscribe_newsletter(
    data: NewsletterSubscribeRequest,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Inscrit à la newsletter.

    **Permissions requises:** Aucune (endpoint public)
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        subscriber = service.subscribe_newsletter(
            email=data.email,
            name=data.name,
            interests=data.interests
        )
        return subscriber
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/newsletter/verify/{token}")
async def verify_newsletter_subscription(
    token: str,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Vérifie une inscription à la newsletter.

    **Permissions requises:** Aucune (endpoint public)
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        success = service.verify_newsletter_subscription(token)
        return {"success": success, "message": "Inscription vérifiée"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/newsletter/unsubscribe")
async def unsubscribe_newsletter(
    email: str = Query(..., description="Email à désinscrire"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Désinscrit de la newsletter.

    **Permissions requises:** Aucune (endpoint public)
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    success = service.unsubscribe_newsletter(email)

    if not success:
        raise HTTPException(status_code=404, detail="Abonnement non trouvé")

    return {"success": True, "message": "Désinscription effectuée"}


@router.get("/newsletter/subscribers", response_model=List[NewsletterSubscriberResponse])
async def list_newsletter_subscribers(
    verified_only: bool = Query(False, description="Seulement vérifiés"),
    limit: int = Query(50, ge=1, le=100, description="Nombre maximum"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les abonnés à la newsletter.

    **Permissions requises:** website.newsletter.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    subscribers = service.list_newsletter_subscribers(verified_only=verified_only, limit=limit)

    return subscribers


@router.get("/newsletter/stats")
async def get_newsletter_stats(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère les statistiques de la newsletter.

    **Permissions requises:** website.newsletter.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    stats = service.get_newsletter_stats()

    return stats


# ============================================================================
# MEDIA
# ============================================================================

@router.post("/media", response_model=SiteMediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    data: SiteMediaCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Upload un média.

    **Permissions requises:** website.media.create
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        media = service.create_media(
            filename=data.filename,
            file_url=data.file_url,
            media_type=data.media_type,
            title=data.title,
            alt_text=data.alt_text,
            uploaded_by=service.user_id,
            file_size=data.file_size,
            mime_type=data.mime_type
        )
        return media
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/media", response_model=List[SiteMediaResponse])
async def list_media(
    media_type: MediaType | None = Query(None, description="Filtrer par type"),
    limit: int = Query(50, ge=1, le=100, description="Nombre maximum"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les médias.

    **Permissions requises:** website.media.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    media = service.list_media(media_type=media_type, limit=limit)

    return media


@router.get("/media/{media_id}", response_model=SiteMediaResponse)
async def get_media(
    media_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère un média par ID.

    **Permissions requises:** website.media.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    media = service.get_media(int(media_id))

    if not media:
        raise HTTPException(status_code=404, detail="Média non trouvé")

    return media


@router.put("/media/{media_id}", response_model=SiteMediaResponse)
async def update_media(
    media_id: UUID,
    data: SiteMediaUpdate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met à jour un média.

    **Permissions requises:** website.media.update
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        update_data = data.model_dump(exclude_unset=True)
        media = service.update_media(int(media_id), **update_data)
        return media
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: UUID,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Supprime un média.

    **Permissions requises:** website.media.delete
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    success = service.delete_media(int(media_id))

    if not success:
        raise HTTPException(status_code=404, detail="Média non trouvé")

    return None


# ============================================================================
# SEO
# ============================================================================

@router.get("/seo", response_model=SiteSEOResponse)
async def get_seo_config(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère la configuration SEO.

    **Permissions requises:** website.seo.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    seo = service.get_seo_config()

    if not seo:
        raise HTTPException(status_code=404, detail="Configuration SEO non trouvée")

    return seo


@router.put("/seo", response_model=SiteSEOResponse)
async def update_seo_config(
    data: SiteSEOUpdate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met à jour la configuration SEO.

    **Permissions requises:** website.seo.update
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        update_data = data.model_dump(exclude_unset=True)
        seo = service.update_seo_config(**update_data)
        return seo
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# ANALYTICS
# ============================================================================

@router.get("/analytics/dashboard", response_model=AnalyticsDashboardResponse)
async def get_analytics_dashboard(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère le dashboard analytics.

    **Permissions requises:** website.analytics.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    dashboard = service.get_analytics_dashboard()

    return dashboard


@router.get("/analytics", response_model=List[SiteAnalyticsResponse])
async def list_analytics(
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les données analytics.

    **Permissions requises:** website.analytics.read
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    analytics = service.list_analytics(limit=limit)

    return analytics


@router.post("/analytics/record")
async def record_analytics(
    data: dict,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Enregistre un événement analytics.

    **Permissions requises:** Aucune (endpoint public)
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    try:
        service.record_analytics(**data)
        return {"success": True, "message": "Événement enregistré"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PUBLIC CONFIG & HOMEPAGE
# ============================================================================

@router.get("/config", response_model=PublicSiteConfigResponse)
async def get_public_site_config(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère la configuration publique du site.

    **Permissions requises:** Aucune (endpoint public)
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    config = service.get_public_site_config()

    return config


@router.get("/homepage", response_model=SitePageResponse)
async def get_homepage(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère la page d'accueil.

    **Permissions requises:** Aucune (endpoint public)
    """
    service = get_website_service(db, context.tenant_id, context.user_id)

    homepage = service.get_homepage()

    if not homepage:
        raise HTTPException(status_code=404, detail="Page d'accueil non trouvée")

    return homepage


# ============================================================================
# INDEXNOW API - Notification des moteurs de recherche
# ============================================================================

@router.post("/indexnow", status_code=status.HTTP_202_ACCEPTED)
async def notify_indexnow(
    urls: List[str] = Query(..., description="URLs à notifier"),
    context: SaaSContext = Depends(get_saas_context),
):
    """
    Notifie les moteurs de recherche (Bing, Yandex, etc.) des URLs mises à jour via IndexNow.

    **Permissions requises:** website.indexnow.notify

    IndexNow permet d'informer instantanément les moteurs de recherche
    des modifications de contenu sans attendre le crawl.
    """
    import httpx
    import logging

    logger = logging.getLogger(__name__)
    INDEXNOW_KEY = "azalscore-indexnow-2026-key"
    HOST = "azalscore.com"

    # Endpoints IndexNow (Bing et Yandex supportent IndexNow)
    INDEXNOW_ENDPOINTS = [
        "https://api.indexnow.org/indexnow",
        "https://www.bing.com/indexnow",
        "https://yandex.com/indexnow",
    ]

    results = {"success": [], "failed": []}

    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint in INDEXNOW_ENDPOINTS:
            try:
                # Format pour plusieurs URLs
                payload = {
                    "host": HOST,
                    "key": INDEXNOW_KEY,
                    "keyLocation": f"https://{HOST}/{INDEXNOW_KEY}.txt",
                    "urlList": urls
                }

                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code in [200, 202]:
                    results["success"].append(endpoint)
                    logger.info(f"IndexNow notification sent to {endpoint}")
                else:
                    results["failed"].append({
                        "endpoint": endpoint,
                        "status": response.status_code
                    })
                    logger.warning(f"IndexNow failed for {endpoint}: {response.status_code}")

            except Exception as e:
                results["failed"].append({
                    "endpoint": endpoint,
                    "error": str(e)
                })
                logger.error(f"IndexNow error for {endpoint}: {e}")

    return {
        "message": "IndexNow notifications sent",
        "urls_count": len(urls),
        "results": results
    }


@router.get("/seo-status")
async def get_seo_status():
    """
    Retourne le statut SEO du site (fichiers de configuration, sitemap, etc.).

    **Permissions requises:** Aucune (endpoint public pour audit)
    """
    import os
    from datetime import datetime

    frontend_public = "/home/ubuntu/azalscore/frontend/public"

    files_status = {}
    required_files = [
        "robots.txt",
        "sitemap.xml",
        "manifest.webmanifest",
        "og-image.png",
        "twitter-image.png",
        "ai.txt",
        "humans.txt",
        ".well-known/security.txt",
        ".well-known/ai-plugin.json",
        "azalscore-indexnow-2026-key.txt"
    ]

    for file in required_files:
        filepath = os.path.join(frontend_public, file)
        if os.path.exists(filepath):
            stat = os.stat(filepath)
            files_status[file] = {
                "exists": True,
                "size_bytes": stat.st_size,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        else:
            files_status[file] = {"exists": False}

    return {
        "host": "azalscore.com",
        "seo_files": files_status,
        "sitemap_url": "https://azalscore.com/sitemap.xml",
        "robots_url": "https://azalscore.com/robots.txt",
        "indexnow_key": "azalscore-indexnow-2026-key",
        "structured_data": True,
        "open_graph": True,
        "twitter_cards": True,
        "canonical_urls": True,
        "checked_at": datetime.now().isoformat()
    }
