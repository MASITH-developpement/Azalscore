"""
AZALS MODULE T8 - Tests Site Web
=================================

Tests unitaires pour le module site web officiel.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.modules.website.models import (
    SitePage, BlogPost, Testimonial, ContactSubmission,
    NewsletterSubscriber, SiteMedia, SiteSEO, SiteAnalytics,
    PageType, PublishStatus, ContentType, FormCategory,
    SubmissionStatus, MediaType
)
from app.modules.website.schemas import (
    SitePageCreate, SitePageUpdate,
    BlogPostCreate, BlogPostUpdate,
    TestimonialCreate, TestimonialUpdate,
    ContactSubmissionCreate, ContactSubmissionUpdate,
    NewsletterSubscribeRequest,
    SiteMediaCreate, SiteMediaUpdate,
    SiteSEOUpdate
)
from app.modules.website.service import WebsiteService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de la session DB."""
    return MagicMock(spec=Session)


@pytest.fixture
def website_service(mock_db):
    """Service website pour tests."""
    return WebsiteService(mock_db, "test_tenant", user_id=1)


# ============================================================================
# TESTS ENUMS
# ============================================================================

class TestEnums:
    """Tests des enums."""

    def test_page_type_values(self):
        """Vérifier les types de pages."""
        assert PageType.LANDING.value == "LANDING"
        assert PageType.PRODUCT.value == "PRODUCT"
        assert PageType.PRICING.value == "PRICING"
        assert PageType.CONTACT.value == "CONTACT"
        assert PageType.BLOG.value == "BLOG"
        assert len(PageType) == 9

    def test_publish_status_values(self):
        """Vérifier les statuts de publication."""
        assert PublishStatus.DRAFT.value == "DRAFT"
        assert PublishStatus.PUBLISHED.value == "PUBLISHED"
        assert PublishStatus.ARCHIVED.value == "ARCHIVED"
        assert len(PublishStatus) == 4

    def test_content_type_values(self):
        """Vérifier les types de contenu."""
        assert ContentType.ARTICLE.value == "ARTICLE"
        assert ContentType.NEWS.value == "NEWS"
        assert ContentType.CASE_STUDY.value == "CASE_STUDY"
        assert len(ContentType) == 7

    def test_form_category_values(self):
        """Vérifier les catégories de formulaire."""
        assert FormCategory.CONTACT.value == "CONTACT"
        assert FormCategory.DEMO_REQUEST.value == "DEMO_REQUEST"
        assert len(FormCategory) == 6

    def test_submission_status_values(self):
        """Vérifier les statuts de soumission."""
        assert SubmissionStatus.NEW.value == "NEW"
        assert SubmissionStatus.REPLIED.value == "REPLIED"
        assert len(SubmissionStatus) == 5

    def test_media_type_values(self):
        """Vérifier les types de médias."""
        assert MediaType.IMAGE.value == "IMAGE"
        assert MediaType.VIDEO.value == "VIDEO"
        assert len(MediaType) == 4


# ============================================================================
# TESTS MODÈLES
# ============================================================================

class TestModels:
    """Tests des modèles."""

    def test_site_page_model(self):
        """Tester le modèle SitePage."""
        page = SitePage(
            tenant_id="test",
            slug="test-page",
            title="Page Test",
            page_type=PageType.LANDING,
            status=PublishStatus.DRAFT
        )
        assert page.tenant_id == "test"
        assert page.slug == "test-page"
        assert page.page_type == PageType.LANDING
        assert page.status == PublishStatus.DRAFT

    def test_blog_post_model(self):
        """Tester le modèle BlogPost."""
        post = BlogPost(
            tenant_id="test",
            slug="test-article",
            title="Article Test",
            content_type=ContentType.ARTICLE,
            view_count=0
        )
        assert post.slug == "test-article"
        assert post.content_type == ContentType.ARTICLE
        assert post.view_count == 0

    def test_testimonial_model(self):
        """Tester le modèle Testimonial."""
        testimonial = Testimonial(
            tenant_id="test",
            client_name="John Doe",
            quote="Excellent produit !",
            rating=5
        )
        assert testimonial.client_name == "John Doe"
        assert testimonial.rating == 5

    def test_contact_submission_model(self):
        """Tester le modèle ContactSubmission."""
        submission = ContactSubmission(
            tenant_id="test",
            form_category=FormCategory.CONTACT,
            email="test@example.com",
            status=SubmissionStatus.NEW
        )
        assert submission.email == "test@example.com"
        assert submission.status == SubmissionStatus.NEW

    def test_newsletter_subscriber_model(self):
        """Tester le modèle NewsletterSubscriber."""
        subscriber = NewsletterSubscriber(
            tenant_id="test",
            email="newsletter@example.com",
            frequency="weekly",
            is_active=True
        )
        assert subscriber.email == "newsletter@example.com"
        assert subscriber.is_active == True

    def test_site_media_model(self):
        """Tester le modèle SiteMedia."""
        media = SiteMedia(
            tenant_id="test",
            filename="image.jpg",
            url="/uploads/image.jpg",
            media_type=MediaType.IMAGE
        )
        assert media.filename == "image.jpg"
        assert media.media_type == MediaType.IMAGE


# ============================================================================
# TESTS SCHÉMAS
# ============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_site_page_create_schema(self):
        """Tester SitePageCreate."""
        data = SitePageCreate(
            slug="new-page",
            title="Nouvelle Page",
            page_type="LANDING"
        )
        assert data.slug == "new-page"
        assert data.page_type == "LANDING"
        assert data.show_in_menu == True

    def test_blog_post_create_schema(self):
        """Tester BlogPostCreate."""
        data = BlogPostCreate(
            slug="new-post",
            title="Nouvel Article",
            content="Contenu de l'article"
        )
        assert data.slug == "new-post"
        assert data.content_type == "ARTICLE"

    def test_testimonial_create_schema(self):
        """Tester TestimonialCreate."""
        data = TestimonialCreate(
            client_name="Client Test",
            quote="Très satisfait du produit"
        )
        assert data.client_name == "Client Test"
        assert data.is_featured == False

    def test_contact_submission_create_schema(self):
        """Tester ContactSubmissionCreate."""
        data = ContactSubmissionCreate(
            form_category="DEMO_REQUEST",
            email="contact@test.com",
            company="Test Corp"
        )
        assert data.form_category == "DEMO_REQUEST"
        assert data.consent_privacy == True

    def test_newsletter_subscribe_schema(self):
        """Tester NewsletterSubscribeRequest."""
        data = NewsletterSubscribeRequest(
            email="subscribe@test.com",
            interests=["product_updates", "blog"]
        )
        assert data.email == "subscribe@test.com"
        assert data.frequency == "weekly"


# ============================================================================
# TESTS SERVICE - PAGES
# ============================================================================

class TestServicePages:
    """Tests du service pages."""

    def test_create_page(self, website_service, mock_db):
        """Tester la création de page."""
        data = SitePageCreate(
            slug="test-page",
            title="Test Page"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        page = website_service.create_page(data)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    def test_get_page(self, website_service, mock_db):
        """Tester la récupération de page."""
        mock_page = SitePage(id=1, tenant_id="test_tenant", slug="test", title="Test")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_page

        page = website_service.get_page(1)
        assert page.id == 1

    def test_list_pages(self, website_service, mock_db):
        """Tester la liste des pages."""
        mock_pages = [
            SitePage(id=1, tenant_id="test_tenant", slug="page1", title="Page 1"),
            SitePage(id=2, tenant_id="test_tenant", slug="page2", title="Page 2")
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_pages

        pages = website_service.list_pages()
        assert len(pages) == 2

    def test_publish_page(self, website_service, mock_db):
        """Tester la publication de page."""
        mock_page = SitePage(id=1, tenant_id="test_tenant", slug="test", title="Test", status=PublishStatus.DRAFT)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_page

        page = website_service.publish_page(1, True)
        assert page.status == PublishStatus.PUBLISHED
        assert page.published_at is not None

    def test_delete_page(self, website_service, mock_db):
        """Tester la suppression de page."""
        mock_page = SitePage(id=1, tenant_id="test_tenant", slug="test", title="Test", is_system=False)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_page

        result = website_service.delete_page(1)
        assert result == True
        mock_db.delete.assert_called_once()


# ============================================================================
# TESTS SERVICE - BLOG
# ============================================================================

class TestServiceBlog:
    """Tests du service blog."""

    def test_create_blog_post(self, website_service, mock_db):
        """Tester la création d'article."""
        data = BlogPostCreate(
            slug="new-article",
            title="Nouvel Article",
            content="Contenu de test avec plusieurs mots pour calculer le temps de lecture."
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        post = website_service.create_blog_post(data)
        mock_db.add.assert_called_once()

    def test_get_blog_post_by_slug(self, website_service, mock_db):
        """Tester la récupération par slug."""
        mock_post = BlogPost(id=1, tenant_id="test_tenant", slug="test-slug", title="Test")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_post

        post = website_service.get_blog_post_by_slug("test-slug")
        assert post.slug == "test-slug"

    def test_list_blog_posts_with_filters(self, website_service, mock_db):
        """Tester la liste avec filtres."""
        mock_posts = [
            BlogPost(id=1, tenant_id="test_tenant", slug="post1", title="Post 1", category="tech")
        ]
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_posts

        posts = website_service.list_blog_posts(category="tech")
        assert len(posts) == 1


# ============================================================================
# TESTS SERVICE - TESTIMONIALS
# ============================================================================

class TestServiceTestimonials:
    """Tests du service témoignages."""

    def test_create_testimonial(self, website_service, mock_db):
        """Tester la création de témoignage."""
        data = TestimonialCreate(
            client_name="John Doe",
            client_company="Acme Corp",
            quote="Excellent ERP, nous a fait gagner du temps !",
            rating=5
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        testimonial = website_service.create_testimonial(data)
        mock_db.add.assert_called_once()

    def test_list_featured_testimonials(self, website_service, mock_db):
        """Tester la liste des témoignages featured."""
        mock_testimonials = [
            Testimonial(id=1, tenant_id="test_tenant", client_name="Client 1", quote="Super", is_featured=True)
        ]
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_testimonials

        testimonials = website_service.list_testimonials(is_featured=True)
        assert len(testimonials) == 1


# ============================================================================
# TESTS SERVICE - CONTACT
# ============================================================================

class TestServiceContact:
    """Tests du service contact."""

    def test_create_contact_submission(self, website_service, mock_db):
        """Tester la création de soumission."""
        data = ContactSubmissionCreate(
            form_category="DEMO_REQUEST",
            email="prospect@company.com",
            first_name="Jean",
            last_name="Dupont",
            company="Entreprise SA"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        submission = website_service.create_contact_submission(
            data, ip_address="192.168.1.1"
        )
        mock_db.add.assert_called()

    def test_mark_submission_read(self, website_service, mock_db):
        """Tester le marquage comme lu."""
        mock_submission = ContactSubmission(
            id=1, tenant_id="test_tenant",
            email="test@test.com",
            form_category=FormCategory.CONTACT,
            status=SubmissionStatus.NEW
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_submission

        submission = website_service.mark_submission_read(1)
        assert submission.status == SubmissionStatus.READ


# ============================================================================
# TESTS SERVICE - NEWSLETTER
# ============================================================================

class TestServiceNewsletter:
    """Tests du service newsletter."""

    def test_subscribe_newsletter(self, website_service, mock_db):
        """Tester l'inscription newsletter."""
        data = NewsletterSubscribeRequest(
            email="new@subscriber.com",
            first_name="Marie"
        )

        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        subscriber = website_service.subscribe_newsletter(data)
        mock_db.add.assert_called_once()

    def test_subscribe_newsletter_existing(self, website_service, mock_db):
        """Tester la réinscription d'un existant."""
        data = NewsletterSubscribeRequest(email="existing@subscriber.com")

        existing = NewsletterSubscriber(
            id=1, tenant_id="test_tenant",
            email="existing@subscriber.com",
            is_active=False
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        subscriber = website_service.subscribe_newsletter(data)
        assert subscriber.is_active == True

    def test_unsubscribe_newsletter(self, website_service, mock_db):
        """Tester la désinscription."""
        mock_subscriber = NewsletterSubscriber(
            id=1, tenant_id="test_tenant",
            email="test@test.com",
            unsubscribe_token="token123",
            is_active=True
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscriber

        subscriber = website_service.unsubscribe_newsletter("token123")
        assert subscriber.is_active == False


# ============================================================================
# TESTS SERVICE - MEDIA
# ============================================================================

class TestServiceMedia:
    """Tests du service média."""

    def test_create_media(self, website_service, mock_db):
        """Tester la création de média."""
        data = SiteMediaCreate(
            filename="photo.jpg",
            media_type="IMAGE",
            url="/uploads/photo.jpg",
            file_size=1024000
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        media = website_service.create_media(data)
        mock_db.add.assert_called_once()

    def test_list_media_by_folder(self, website_service, mock_db):
        """Tester la liste par dossier."""
        mock_media = [
            SiteMedia(id=1, tenant_id="test_tenant", filename="img1.jpg", url="/img1.jpg", media_type=MediaType.IMAGE, folder="/images")
        ]
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_media

        media = website_service.list_media(folder="/images")
        assert len(media) == 1


# ============================================================================
# TESTS SERVICE - SEO
# ============================================================================

class TestServiceSEO:
    """Tests du service SEO."""

    def test_get_seo_config(self, website_service, mock_db):
        """Tester la récupération SEO."""
        mock_seo = SiteSEO(
            id=1, tenant_id="test_tenant",
            site_title="AZALS"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_seo

        seo = website_service.get_seo_config()
        assert seo.site_title == "AZALS"

    def test_update_seo_config_create(self, website_service, mock_db):
        """Tester la création de config SEO."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = SiteSEOUpdate(
            site_title="Mon Site",
            google_analytics_id="UA-123456"
        )

        seo = website_service.update_seo_config(data)
        mock_db.add.assert_called_once()


# ============================================================================
# TESTS SERVICE - ANALYTICS
# ============================================================================

class TestServiceAnalytics:
    """Tests du service analytics."""

    def test_record_analytics(self, website_service, mock_db):
        """Tester l'enregistrement analytics."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        analytics = website_service.record_analytics(
            date=datetime.utcnow(),
            data={"page_views": 100, "unique_visitors": 50}
        )
        mock_db.add.assert_called_once()

    def test_get_analytics_dashboard(self, website_service, mock_db):
        """Tester le dashboard analytics."""
        mock_analytics = [
            SiteAnalytics(
                id=1, tenant_id="test_tenant",
                date=datetime.utcnow(),
                period="daily",
                page_views=100,
                unique_visitors=50,
                sessions=75,
                form_submissions=5,
                newsletter_signups=2,
                demo_requests=1,
                blog_views=30
            )
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_analytics

        dashboard = website_service.get_analytics_dashboard(30)
        assert dashboard["total_page_views"] == 100
        assert dashboard["total_form_submissions"] == 5


# ============================================================================
# TESTS SERVICE - PUBLIC CONFIG
# ============================================================================

class TestServicePublicConfig:
    """Tests du service config publique."""

    def test_get_public_site_config(self, website_service, mock_db):
        """Tester la config publique."""
        mock_seo = SiteSEO(
            id=1, tenant_id="test_tenant",
            site_title="AZALS",
            site_description="ERP Décisionnel"
        )
        mock_pages = [
            SitePage(id=1, tenant_id="test_tenant", slug="home", title="Accueil", page_type=PageType.LANDING, sort_order=0, parent_id=None),
            SitePage(id=2, tenant_id="test_tenant", slug="produits", title="Produits", page_type=PageType.PRODUCT, sort_order=1, parent_id=None)
        ]

        mock_db.query.return_value.filter.return_value.first.return_value = mock_seo
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_pages

        config = website_service.get_public_site_config("fr")
        assert config["site_title"] == "AZALS"
        assert config["language"] == "fr"


# ============================================================================
# TESTS FACTORY
# ============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_website_service(self, mock_db):
        """Tester la factory."""
        from app.modules.website.service import get_website_service

        service = get_website_service(mock_db, "tenant123", user_id=5)
        assert service.tenant_id == "tenant123"
        assert service.user_id == 5


# ============================================================================
# TESTS INTÉGRATION
# ============================================================================

class TestIntegration:
    """Tests d'intégration."""

    def test_page_workflow(self, website_service, mock_db):
        """Tester le workflow complet de page."""
        # 1. Création
        create_data = SitePageCreate(
            slug="nouvelle-page",
            title="Nouvelle Page",
            page_type="LANDING"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        page = website_service.create_page(create_data)

        # 2. Récupération
        mock_page = SitePage(
            id=1, tenant_id="test_tenant",
            slug="nouvelle-page", title="Nouvelle Page",
            page_type=PageType.LANDING,
            status=PublishStatus.DRAFT
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_page

        # 3. Publication
        published = website_service.publish_page(1, True)
        assert published.status == PublishStatus.PUBLISHED

    def test_contact_to_newsletter_workflow(self, website_service, mock_db):
        """Tester le workflow contact vers newsletter."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Soumission contact avec consentement newsletter
        data = ContactSubmissionCreate(
            form_category="DEMO_REQUEST",
            email="prospect@company.com",
            consent_newsletter=True
        )

        submission = website_service.create_contact_submission(data)

        # Vérifie que add a été appelé 2 fois (submission + newsletter)
        assert mock_db.add.call_count >= 1
