"""
AZALS MODULE T8 - Service Site Web
====================================

Logique métier pour le site web officiel.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from .models import (
    SitePage, BlogPost, Testimonial, ContactSubmission,
    NewsletterSubscriber, SiteMedia, SiteSEO, SiteAnalytics,
    PageType, PublishStatus, ContentType, FormCategory,
    SubmissionStatus, MediaType
)
from .schemas import (
    SitePageCreate, SitePageUpdate,
    BlogPostCreate, BlogPostUpdate,
    TestimonialCreate, TestimonialUpdate,
    ContactSubmissionCreate, ContactSubmissionUpdate,
    NewsletterSubscribeRequest,
    SiteMediaCreate, SiteMediaUpdate,
    SiteSEOUpdate
)


class WebsiteService:
    """Service de gestion du site web."""

    def __init__(self, db: Session, tenant_id: str, user_id: Optional[int] = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    # ========================================================================
    # PAGES
    # ========================================================================

    def create_page(self, data: SitePageCreate) -> SitePage:
        """Créer une page."""
        # Si homepage, retirer l'ancien
        if data.is_homepage:
            self._clear_homepage()

        page = SitePage(
            tenant_id=self.tenant_id,
            slug=data.slug,
            page_type=PageType[data.page_type],
            title=data.title,
            subtitle=data.subtitle,
            content=data.content,
            excerpt=data.excerpt,
            featured_image=data.featured_image,
            hero_video=data.hero_video,
            meta_title=data.meta_title,
            meta_description=data.meta_description,
            meta_keywords=data.meta_keywords,
            canonical_url=data.canonical_url,
            og_image=data.og_image,
            template=data.template,
            layout_config=data.layout_config,
            sections=data.sections,
            parent_id=data.parent_id,
            sort_order=data.sort_order,
            show_in_menu=data.show_in_menu,
            show_in_footer=data.show_in_footer,
            language=data.language,
            is_homepage=data.is_homepage,
            requires_auth=data.requires_auth,
            created_by=self.user_id,
        )
        self.db.add(page)
        self.db.commit()
        self.db.refresh(page)
        return page

    def get_page(self, page_id: int) -> Optional[SitePage]:
        """Récupérer une page par ID."""
        return self.db.query(SitePage).filter(
            SitePage.tenant_id == self.tenant_id,
            SitePage.id == page_id
        ).first()

    def get_page_by_slug(self, slug: str) -> Optional[SitePage]:
        """Récupérer une page par slug."""
        return self.db.query(SitePage).filter(
            SitePage.tenant_id == self.tenant_id,
            SitePage.slug == slug
        ).first()

    def get_homepage(self) -> Optional[SitePage]:
        """Récupérer la page d'accueil."""
        return self.db.query(SitePage).filter(
            SitePage.tenant_id == self.tenant_id,
            SitePage.is_homepage == True,
            SitePage.status == PublishStatus.PUBLISHED
        ).first()

    def list_pages(
        self,
        page_type: Optional[str] = None,
        status: Optional[str] = None,
        parent_id: Optional[int] = None,
        show_in_menu: Optional[bool] = None,
        language: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[SitePage]:
        """Lister les pages."""
        query = self.db.query(SitePage).filter(
            SitePage.tenant_id == self.tenant_id
        )

        if page_type:
            query = query.filter(SitePage.page_type == PageType[page_type])
        if status:
            query = query.filter(SitePage.status == PublishStatus[status])
        if parent_id is not None:
            query = query.filter(SitePage.parent_id == parent_id)
        if show_in_menu is not None:
            query = query.filter(SitePage.show_in_menu == show_in_menu)
        if language:
            query = query.filter(SitePage.language == language)

        return query.order_by(SitePage.sort_order).offset(skip).limit(limit).all()

    def update_page(self, page_id: int, data: SitePageUpdate) -> Optional[SitePage]:
        """Mettre à jour une page."""
        page = self.get_page(page_id)
        if not page or page.is_system:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "page_type" in update_data:
            update_data["page_type"] = PageType[update_data["page_type"]]

        for key, value in update_data.items():
            setattr(page, key, value)

        self.db.commit()
        self.db.refresh(page)
        return page

    def publish_page(self, page_id: int, publish: bool = True) -> Optional[SitePage]:
        """Publier/dépublier une page."""
        page = self.get_page(page_id)
        if not page:
            return None

        if publish:
            page.status = PublishStatus.PUBLISHED
            page.published_at = datetime.utcnow()
        else:
            page.status = PublishStatus.DRAFT

        self.db.commit()
        self.db.refresh(page)
        return page

    def delete_page(self, page_id: int) -> bool:
        """Supprimer une page."""
        page = self.get_page(page_id)
        if not page or page.is_system:
            return False

        self.db.delete(page)
        self.db.commit()
        return True

    def increment_page_views(self, page_id: int) -> None:
        """Incrémenter le compteur de vues."""
        self.db.query(SitePage).filter(
            SitePage.id == page_id,
            SitePage.tenant_id == self.tenant_id
        ).update({"view_count": SitePage.view_count + 1})
        self.db.commit()

    def get_menu_pages(self, language: str = "fr") -> List[SitePage]:
        """Récupérer les pages pour le menu."""
        return self.db.query(SitePage).filter(
            SitePage.tenant_id == self.tenant_id,
            SitePage.status == PublishStatus.PUBLISHED,
            SitePage.show_in_menu == True,
            SitePage.language == language
        ).order_by(SitePage.sort_order).all()

    def get_footer_pages(self, language: str = "fr") -> List[SitePage]:
        """Récupérer les pages pour le footer."""
        return self.db.query(SitePage).filter(
            SitePage.tenant_id == self.tenant_id,
            SitePage.status == PublishStatus.PUBLISHED,
            SitePage.show_in_footer == True,
            SitePage.language == language
        ).order_by(SitePage.sort_order).all()

    def _clear_homepage(self) -> None:
        """Retirer le flag homepage des autres pages."""
        self.db.query(SitePage).filter(
            SitePage.tenant_id == self.tenant_id,
            SitePage.is_homepage == True
        ).update({"is_homepage": False})

    # ========================================================================
    # BLOG
    # ========================================================================

    def create_blog_post(self, data: BlogPostCreate) -> BlogPost:
        """Créer un article de blog."""
        # Estimer le temps de lecture
        reading_time = data.reading_time
        if not reading_time and data.content:
            words = len(data.content.split())
            reading_time = max(1, words // 200)  # 200 mots/minute

        post = BlogPost(
            tenant_id=self.tenant_id,
            slug=data.slug,
            content_type=ContentType[data.content_type],
            title=data.title,
            subtitle=data.subtitle,
            content=data.content,
            excerpt=data.excerpt,
            featured_image=data.featured_image,
            gallery=data.gallery,
            meta_title=data.meta_title,
            meta_description=data.meta_description,
            meta_keywords=data.meta_keywords,
            category=data.category,
            tags=data.tags,
            author_id=self.user_id,
            author_name=data.author_name,
            author_avatar=data.author_avatar,
            author_bio=data.author_bio,
            language=data.language,
            reading_time=reading_time,
            is_featured=data.is_featured,
            is_pinned=data.is_pinned,
            allow_comments=data.allow_comments,
            created_by=self.user_id,
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def get_blog_post(self, post_id: int) -> Optional[BlogPost]:
        """Récupérer un article par ID."""
        return self.db.query(BlogPost).filter(
            BlogPost.tenant_id == self.tenant_id,
            BlogPost.id == post_id
        ).first()

    def get_blog_post_by_slug(self, slug: str) -> Optional[BlogPost]:
        """Récupérer un article par slug."""
        return self.db.query(BlogPost).filter(
            BlogPost.tenant_id == self.tenant_id,
            BlogPost.slug == slug
        ).first()

    def list_blog_posts(
        self,
        content_type: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        status: Optional[str] = None,
        is_featured: Optional[bool] = None,
        language: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[BlogPost]:
        """Lister les articles."""
        query = self.db.query(BlogPost).filter(
            BlogPost.tenant_id == self.tenant_id
        )

        if content_type:
            query = query.filter(BlogPost.content_type == ContentType[content_type])
        if category:
            query = query.filter(BlogPost.category == category)
        if tag:
            query = query.filter(BlogPost.tags.contains([tag]))
        if status:
            query = query.filter(BlogPost.status == PublishStatus[status])
        if is_featured is not None:
            query = query.filter(BlogPost.is_featured == is_featured)
        if language:
            query = query.filter(BlogPost.language == language)

        # Tri: pinned en premier, puis par date
        return query.order_by(
            BlogPost.is_pinned.desc(),
            BlogPost.published_at.desc()
        ).offset(skip).limit(limit).all()

    def update_blog_post(self, post_id: int, data: BlogPostUpdate) -> Optional[BlogPost]:
        """Mettre à jour un article."""
        post = self.get_blog_post(post_id)
        if not post:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "content_type" in update_data:
            update_data["content_type"] = ContentType[update_data["content_type"]]

        # Recalculer le temps de lecture si contenu modifié
        if "content" in update_data and update_data["content"]:
            words = len(update_data["content"].split())
            update_data["reading_time"] = max(1, words // 200)

        for key, value in update_data.items():
            setattr(post, key, value)

        self.db.commit()
        self.db.refresh(post)
        return post

    def publish_blog_post(self, post_id: int, publish: bool = True) -> Optional[BlogPost]:
        """Publier/dépublier un article."""
        post = self.get_blog_post(post_id)
        if not post:
            return None

        if publish:
            post.status = PublishStatus.PUBLISHED
            post.published_at = datetime.utcnow()
        else:
            post.status = PublishStatus.DRAFT

        self.db.commit()
        self.db.refresh(post)
        return post

    def delete_blog_post(self, post_id: int) -> bool:
        """Supprimer un article."""
        post = self.get_blog_post(post_id)
        if not post:
            return False

        self.db.delete(post)
        self.db.commit()
        return True

    def increment_post_views(self, post_id: int) -> None:
        """Incrémenter le compteur de vues."""
        self.db.query(BlogPost).filter(
            BlogPost.id == post_id,
            BlogPost.tenant_id == self.tenant_id
        ).update({"view_count": BlogPost.view_count + 1})
        self.db.commit()

    def get_blog_categories(self) -> List[Dict[str, Any]]:
        """Récupérer les catégories avec compteurs."""
        results = self.db.query(
            BlogPost.category,
            func.count(BlogPost.id).label("count")
        ).filter(
            BlogPost.tenant_id == self.tenant_id,
            BlogPost.status == PublishStatus.PUBLISHED,
            BlogPost.category.isnot(None)
        ).group_by(BlogPost.category).all()

        return [{"name": r.category, "count": r.count} for r in results]

    # ========================================================================
    # TESTIMONIALS
    # ========================================================================

    def create_testimonial(self, data: TestimonialCreate) -> Testimonial:
        """Créer un témoignage."""
        testimonial = Testimonial(
            tenant_id=self.tenant_id,
            client_name=data.client_name,
            client_title=data.client_title,
            client_company=data.client_company,
            client_logo=data.client_logo,
            client_avatar=data.client_avatar,
            quote=data.quote,
            full_testimonial=data.full_testimonial,
            industry=data.industry,
            use_case=data.use_case,
            modules_used=data.modules_used,
            metrics=data.metrics,
            video_url=data.video_url,
            case_study_url=data.case_study_url,
            rating=data.rating,
            sort_order=data.sort_order,
            is_featured=data.is_featured,
            show_on_homepage=data.show_on_homepage,
            language=data.language,
            created_by=self.user_id,
        )
        self.db.add(testimonial)
        self.db.commit()
        self.db.refresh(testimonial)
        return testimonial

    def get_testimonial(self, testimonial_id: int) -> Optional[Testimonial]:
        """Récupérer un témoignage."""
        return self.db.query(Testimonial).filter(
            Testimonial.tenant_id == self.tenant_id,
            Testimonial.id == testimonial_id
        ).first()

    def list_testimonials(
        self,
        industry: Optional[str] = None,
        is_featured: Optional[bool] = None,
        show_on_homepage: Optional[bool] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Testimonial]:
        """Lister les témoignages."""
        query = self.db.query(Testimonial).filter(
            Testimonial.tenant_id == self.tenant_id
        )

        if industry:
            query = query.filter(Testimonial.industry == industry)
        if is_featured is not None:
            query = query.filter(Testimonial.is_featured == is_featured)
        if show_on_homepage is not None:
            query = query.filter(Testimonial.show_on_homepage == show_on_homepage)
        if status:
            query = query.filter(Testimonial.status == PublishStatus[status])

        return query.order_by(Testimonial.sort_order).offset(skip).limit(limit).all()

    def update_testimonial(self, testimonial_id: int, data: TestimonialUpdate) -> Optional[Testimonial]:
        """Mettre à jour un témoignage."""
        testimonial = self.get_testimonial(testimonial_id)
        if not testimonial:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(testimonial, key, value)

        self.db.commit()
        self.db.refresh(testimonial)
        return testimonial

    def publish_testimonial(self, testimonial_id: int, publish: bool = True) -> Optional[Testimonial]:
        """Publier/dépublier un témoignage."""
        testimonial = self.get_testimonial(testimonial_id)
        if not testimonial:
            return None

        if publish:
            testimonial.status = PublishStatus.PUBLISHED
            testimonial.published_at = datetime.utcnow()
        else:
            testimonial.status = PublishStatus.DRAFT

        self.db.commit()
        self.db.refresh(testimonial)
        return testimonial

    def delete_testimonial(self, testimonial_id: int) -> bool:
        """Supprimer un témoignage."""
        testimonial = self.get_testimonial(testimonial_id)
        if not testimonial:
            return False

        self.db.delete(testimonial)
        self.db.commit()
        return True

    # ========================================================================
    # CONTACT
    # ========================================================================

    def create_contact_submission(
        self,
        data: ContactSubmissionCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None
    ) -> ContactSubmission:
        """Créer une soumission de contact."""
        submission = ContactSubmission(
            tenant_id=self.tenant_id,
            form_category=FormCategory[data.form_category],
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            company=data.company,
            job_title=data.job_title,
            subject=data.subject,
            message=data.message,
            source_page=data.source_page,
            utm_source=data.utm_source,
            utm_medium=data.utm_medium,
            utm_campaign=data.utm_campaign,
            referrer=referrer,
            interested_modules=data.interested_modules,
            company_size=data.company_size,
            timeline=data.timeline,
            budget=data.budget,
            custom_fields=data.custom_fields,
            consent_marketing=data.consent_marketing,
            consent_newsletter=data.consent_newsletter,
            consent_privacy=data.consent_privacy,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)

        # Auto-inscription newsletter si consentement
        if data.consent_newsletter:
            self._auto_subscribe_newsletter(data.email, data.first_name, data.last_name)

        return submission

    def get_contact_submission(self, submission_id: int) -> Optional[ContactSubmission]:
        """Récupérer une soumission."""
        return self.db.query(ContactSubmission).filter(
            ContactSubmission.tenant_id == self.tenant_id,
            ContactSubmission.id == submission_id
        ).first()

    def list_contact_submissions(
        self,
        form_category: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[ContactSubmission]:
        """Lister les soumissions."""
        query = self.db.query(ContactSubmission).filter(
            ContactSubmission.tenant_id == self.tenant_id
        )

        if form_category:
            query = query.filter(ContactSubmission.form_category == FormCategory[form_category])
        if status:
            query = query.filter(ContactSubmission.status == SubmissionStatus[status])
        if assigned_to is not None:
            query = query.filter(ContactSubmission.assigned_to == assigned_to)

        return query.order_by(ContactSubmission.created_at.desc()).offset(skip).limit(limit).all()

    def update_contact_submission(
        self,
        submission_id: int,
        data: ContactSubmissionUpdate
    ) -> Optional[ContactSubmission]:
        """Mettre à jour une soumission."""
        submission = self.get_contact_submission(submission_id)
        if not submission:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "status" in update_data:
            update_data["status"] = SubmissionStatus[update_data["status"]]

        # Marquer comme répondu si réponse
        if "response" in update_data and update_data["response"]:
            update_data["responded_at"] = datetime.utcnow()
            update_data["responded_by"] = self.user_id
            if submission.status == SubmissionStatus.NEW:
                update_data["status"] = SubmissionStatus.REPLIED

        for key, value in update_data.items():
            setattr(submission, key, value)

        self.db.commit()
        self.db.refresh(submission)
        return submission

    def mark_submission_read(self, submission_id: int) -> Optional[ContactSubmission]:
        """Marquer comme lu."""
        submission = self.get_contact_submission(submission_id)
        if not submission:
            return None

        if submission.status == SubmissionStatus.NEW:
            submission.status = SubmissionStatus.READ
            self.db.commit()
            self.db.refresh(submission)

        return submission

    def get_contact_stats(self) -> Dict[str, Any]:
        """Statistiques des contacts."""
        stats = {}

        # Par statut
        status_counts = self.db.query(
            ContactSubmission.status,
            func.count(ContactSubmission.id)
        ).filter(
            ContactSubmission.tenant_id == self.tenant_id
        ).group_by(ContactSubmission.status).all()

        stats["by_status"] = {s.value: c for s, c in status_counts}

        # Par catégorie
        category_counts = self.db.query(
            ContactSubmission.form_category,
            func.count(ContactSubmission.id)
        ).filter(
            ContactSubmission.tenant_id == self.tenant_id
        ).group_by(ContactSubmission.form_category).all()

        stats["by_category"] = {c.value: count for c, count in category_counts}

        # Nouveaux aujourd'hui
        today = datetime.utcnow().date()
        stats["new_today"] = self.db.query(ContactSubmission).filter(
            ContactSubmission.tenant_id == self.tenant_id,
            func.date(ContactSubmission.created_at) == today
        ).count()

        return stats

    def _auto_subscribe_newsletter(
        self,
        email: str,
        first_name: Optional[str],
        last_name: Optional[str]
    ) -> None:
        """Auto-inscription newsletter."""
        existing = self.db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.tenant_id == self.tenant_id,
            NewsletterSubscriber.email == email
        ).first()

        if not existing:
            subscriber = NewsletterSubscriber(
                tenant_id=self.tenant_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                source="contact_form",
                is_verified=True,
                verified_at=datetime.utcnow(),
                gdpr_consent=True,
                consent_date=datetime.utcnow(),
            )
            self.db.add(subscriber)

    # ========================================================================
    # NEWSLETTER
    # ========================================================================

    def subscribe_newsletter(self, data: NewsletterSubscribeRequest) -> NewsletterSubscriber:
        """S'abonner à la newsletter."""
        # Vérifier si déjà abonné
        existing = self.db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.tenant_id == self.tenant_id,
            NewsletterSubscriber.email == data.email
        ).first()

        if existing:
            if not existing.is_active:
                # Réactiver
                existing.is_active = True
                existing.unsubscribed_at = None
                self.db.commit()
            return existing

        # Générer tokens
        verification_token = str(uuid.uuid4())
        unsubscribe_token = str(uuid.uuid4())

        subscriber = NewsletterSubscriber(
            tenant_id=self.tenant_id,
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            company=data.company,
            language=data.language,
            interests=data.interests,
            frequency=data.frequency,
            verification_token=verification_token,
            unsubscribe_token=unsubscribe_token,
            source=data.source or "website",
            source_page=data.source_page,
            gdpr_consent=data.gdpr_consent,
            consent_date=datetime.utcnow(),
        )
        self.db.add(subscriber)
        self.db.commit()
        self.db.refresh(subscriber)
        return subscriber

    def verify_newsletter(self, token: str) -> Optional[NewsletterSubscriber]:
        """Vérifier l'email d'un abonné."""
        subscriber = self.db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.tenant_id == self.tenant_id,
            NewsletterSubscriber.verification_token == token
        ).first()

        if subscriber:
            subscriber.is_verified = True
            subscriber.verified_at = datetime.utcnow()
            subscriber.verification_token = None
            self.db.commit()
            self.db.refresh(subscriber)

        return subscriber

    def unsubscribe_newsletter(self, token: str) -> Optional[NewsletterSubscriber]:
        """Se désabonner de la newsletter."""
        subscriber = self.db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.tenant_id == self.tenant_id,
            NewsletterSubscriber.unsubscribe_token == token
        ).first()

        if subscriber:
            subscriber.is_active = False
            subscriber.unsubscribed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(subscriber)

        return subscriber

    def list_newsletter_subscribers(
        self,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[NewsletterSubscriber]:
        """Lister les abonnés."""
        query = self.db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.tenant_id == self.tenant_id
        )

        if is_active is not None:
            query = query.filter(NewsletterSubscriber.is_active == is_active)
        if is_verified is not None:
            query = query.filter(NewsletterSubscriber.is_verified == is_verified)

        return query.order_by(NewsletterSubscriber.created_at.desc()).offset(skip).limit(limit).all()

    def get_newsletter_stats(self) -> Dict[str, Any]:
        """Statistiques newsletter."""
        total = self.db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.tenant_id == self.tenant_id
        ).count()

        active = self.db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.tenant_id == self.tenant_id,
            NewsletterSubscriber.is_active == True
        ).count()

        verified = self.db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.tenant_id == self.tenant_id,
            NewsletterSubscriber.is_verified == True
        ).count()

        # Nouveaux cette semaine
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_this_week = self.db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.tenant_id == self.tenant_id,
            NewsletterSubscriber.created_at >= week_ago
        ).count()

        return {
            "total": total,
            "active": active,
            "verified": verified,
            "new_this_week": new_this_week,
            "unsubscribed": total - active,
        }

    # ========================================================================
    # MEDIA
    # ========================================================================

    def create_media(self, data: SiteMediaCreate) -> SiteMedia:
        """Créer un média."""
        media = SiteMedia(
            tenant_id=self.tenant_id,
            filename=data.filename,
            original_name=data.original_name,
            media_type=MediaType[data.media_type],
            mime_type=data.mime_type,
            url=data.url,
            storage_path=data.storage_path,
            file_size=data.file_size,
            width=data.width,
            height=data.height,
            duration=data.duration,
            thumbnail_url=data.thumbnail_url,
            optimized_url=data.optimized_url,
            alt_text=data.alt_text,
            title=data.title,
            description=data.description,
            caption=data.caption,
            folder=data.folder,
            tags=data.tags,
            created_by=self.user_id,
        )
        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)
        return media

    def get_media(self, media_id: int) -> Optional[SiteMedia]:
        """Récupérer un média."""
        return self.db.query(SiteMedia).filter(
            SiteMedia.tenant_id == self.tenant_id,
            SiteMedia.id == media_id
        ).first()

    def list_media(
        self,
        media_type: Optional[str] = None,
        folder: Optional[str] = None,
        tag: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[SiteMedia]:
        """Lister les médias."""
        query = self.db.query(SiteMedia).filter(
            SiteMedia.tenant_id == self.tenant_id
        )

        if media_type:
            query = query.filter(SiteMedia.media_type == MediaType[media_type])
        if folder:
            query = query.filter(SiteMedia.folder == folder)
        if tag:
            query = query.filter(SiteMedia.tags.contains([tag]))

        return query.order_by(SiteMedia.created_at.desc()).offset(skip).limit(limit).all()

    def update_media(self, media_id: int, data: SiteMediaUpdate) -> Optional[SiteMedia]:
        """Mettre à jour un média."""
        media = self.get_media(media_id)
        if not media:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(media, key, value)

        self.db.commit()
        self.db.refresh(media)
        return media

    def delete_media(self, media_id: int) -> bool:
        """Supprimer un média."""
        media = self.get_media(media_id)
        if not media:
            return False

        self.db.delete(media)
        self.db.commit()
        return True

    # ========================================================================
    # SEO
    # ========================================================================

    def get_seo_config(self) -> Optional[SiteSEO]:
        """Récupérer la configuration SEO."""
        return self.db.query(SiteSEO).filter(
            SiteSEO.tenant_id == self.tenant_id
        ).first()

    def update_seo_config(self, data: SiteSEOUpdate) -> SiteSEO:
        """Mettre à jour la configuration SEO."""
        seo = self.get_seo_config()

        if not seo:
            seo = SiteSEO(tenant_id=self.tenant_id)
            self.db.add(seo)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(seo, key, value)

        seo.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(seo)
        return seo

    # ========================================================================
    # ANALYTICS
    # ========================================================================

    def record_analytics(
        self,
        date: datetime,
        period: str = "daily",
        data: Dict[str, Any] = None
    ) -> SiteAnalytics:
        """Enregistrer des données analytics."""
        data = data or {}

        analytics = self.db.query(SiteAnalytics).filter(
            SiteAnalytics.tenant_id == self.tenant_id,
            SiteAnalytics.date == date,
            SiteAnalytics.period == period
        ).first()

        if not analytics:
            analytics = SiteAnalytics(
                tenant_id=self.tenant_id,
                date=date,
                period=period
            )
            self.db.add(analytics)

        for key, value in data.items():
            if hasattr(analytics, key):
                setattr(analytics, key, value)

        self.db.commit()
        self.db.refresh(analytics)
        return analytics

    def get_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        period: str = "daily"
    ) -> List[SiteAnalytics]:
        """Récupérer les analytics pour une période."""
        return self.db.query(SiteAnalytics).filter(
            SiteAnalytics.tenant_id == self.tenant_id,
            SiteAnalytics.period == period,
            SiteAnalytics.date >= start_date,
            SiteAnalytics.date <= end_date
        ).order_by(SiteAnalytics.date).all()

    def get_analytics_dashboard(self, days: int = 30) -> Dict[str, Any]:
        """Dashboard analytics."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        analytics = self.get_analytics(start_date, end_date, "daily")

        # Agréger les données
        total_views = sum(a.page_views for a in analytics)
        total_visitors = sum(a.unique_visitors for a in analytics)
        total_sessions = sum(a.sessions for a in analytics)
        total_submissions = sum(a.form_submissions for a in analytics)
        total_newsletter = sum(a.newsletter_signups for a in analytics)
        total_demos = sum(a.demo_requests for a in analytics)
        total_blog_views = sum(a.blog_views for a in analytics)

        # Moyenne bounce rate
        bounce_rates = [a.bounce_rate for a in analytics if a.bounce_rate]
        avg_bounce_rate = sum(bounce_rates) / len(bounce_rates) if bounce_rates else None

        # Agréger traffic sources
        traffic_sources: Dict[str, int] = {}
        for a in analytics:
            if a.traffic_sources:
                for source, count in a.traffic_sources.items():
                    traffic_sources[source] = traffic_sources.get(source, 0) + count

        # Top pages
        pages: Dict[str, int] = {}
        for a in analytics:
            if a.top_pages:
                for page in a.top_pages:
                    url = page.get("url", "")
                    pages[url] = pages.get(url, 0) + page.get("views", 0)
        top_pages = [{"url": k, "views": v} for k, v in sorted(pages.items(), key=lambda x: -x[1])[:10]]

        # Top posts
        posts: Dict[str, int] = {}
        for a in analytics:
            if a.top_posts:
                for post in a.top_posts:
                    slug = post.get("slug", "")
                    posts[slug] = posts.get(slug, 0) + post.get("views", 0)
        top_posts = [{"slug": k, "views": v} for k, v in sorted(posts.items(), key=lambda x: -x[1])[:10]]

        # Daily stats
        daily_stats = [
            {
                "date": a.date.isoformat(),
                "page_views": a.page_views,
                "unique_visitors": a.unique_visitors,
                "sessions": a.sessions,
            }
            for a in analytics
        ]

        return {
            "period": f"last_{days}_days",
            "total_page_views": total_views,
            "total_unique_visitors": total_visitors,
            "total_sessions": total_sessions,
            "avg_bounce_rate": avg_bounce_rate,
            "total_form_submissions": total_submissions,
            "total_newsletter_signups": total_newsletter,
            "total_demo_requests": total_demos,
            "total_blog_views": total_blog_views,
            "traffic_by_source": traffic_sources,
            "top_pages": top_pages,
            "top_posts": top_posts,
            "daily_stats": daily_stats,
        }

    # ========================================================================
    # PUBLIC CONFIG
    # ========================================================================

    def get_public_site_config(self, language: str = "fr") -> Dict[str, Any]:
        """Configuration publique du site."""
        seo = self.get_seo_config()
        menu_pages = self.get_menu_pages(language)
        footer_pages = self.get_footer_pages(language)

        def build_menu_tree(pages, parent_id=None):
            tree = []
            for page in pages:
                if page.parent_id == parent_id:
                    item = {
                        "id": page.id,
                        "slug": page.slug,
                        "title": page.title,
                        "page_type": page.page_type.value,
                        "sort_order": page.sort_order,
                        "parent_id": page.parent_id,
                        "children": build_menu_tree(pages, page.id)
                    }
                    tree.append(item)
            return sorted(tree, key=lambda x: x["sort_order"])

        return {
            "site_title": seo.site_title if seo else "AZALS",
            "site_description": seo.site_description if seo else None,
            "og_image": seo.og_default_image if seo else None,
            "menu": build_menu_tree(menu_pages),
            "footer_pages": [
                {
                    "id": p.id,
                    "slug": p.slug,
                    "title": p.title,
                    "page_type": p.page_type.value,
                    "sort_order": p.sort_order,
                    "parent_id": None,
                    "children": []
                }
                for p in sorted(footer_pages, key=lambda x: x.sort_order)
            ],
            "analytics_enabled": bool(seo and (seo.google_analytics_id or seo.google_tag_manager_id)),
            "language": language,
        }


def get_website_service(db: Session, tenant_id: str, user_id: Optional[int] = None) -> WebsiteService:
    """Factory pour le service website."""
    return WebsiteService(db, tenant_id, user_id)
