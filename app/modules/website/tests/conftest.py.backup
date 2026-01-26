"""Configuration pytest et fixtures pour les tests Website."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.saas_context import SaaSContext, UserRole


@pytest.fixture
def tenant_id():
    return "tenant-test-001"


@pytest.fixture
def user_id():
    return "user-test-001"


@pytest.fixture(autouse=True)
def mock_saas_context(monkeypatch, tenant_id, user_id):
    def mock_get_context():
        return SaaSContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=UserRole.ADMIN,
            permissions={"website.*"},
            scope="tenant",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

    from app.modules.website import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)
    return mock_get_context


@pytest.fixture
def mock_website_service(monkeypatch, tenant_id, user_id):
    """Mock du service Website."""
    from app.modules.website.models import PageType, FormCategory, MediaType, PublishStatus

    class MockWebsiteService:
        def __init__(self, db, tenant_id, user_id=None):
            self.db = db
            self.tenant_id = tenant_id
            self.user_id = int(user_id) if user_id else None

        # Pages
        def create_page(self, **kwargs):
            return {"id": str(uuid4()), "tenant_id": self.tenant_id, "title": kwargs.get("title"), "slug": kwargs.get("slug")}

        def list_pages(self, **kwargs):
            return [{"id": str(uuid4()), "title": f"Page {i}"} for i in range(3)]

        def get_page(self, page_id):
            return {"id": str(uuid4()), "title": "Page 1"}

        def get_page_by_slug(self, slug):
            return {"id": str(uuid4()), "slug": slug}

        def update_page(self, page_id, **kwargs):
            return {"id": page_id, **kwargs}

        def publish_page(self, page_id, **kwargs):
            return {"id": page_id, "status": "PUBLISHED"}

        def delete_page(self, page_id):
            return True

        # Blog
        def create_blog_post(self, **kwargs):
            return {"id": str(uuid4()), "title": kwargs.get("title")}

        def list_blog_posts(self, **kwargs):
            return [{"id": str(uuid4()), "title": f"Post {i}"} for i in range(3)]

        def get_blog_categories(self):
            return ["Tech", "Business", "News"]

        def get_blog_post(self, post_id):
            return {"id": str(uuid4()), "title": "Post 1"}

        def get_blog_post_by_slug(self, slug):
            return {"id": str(uuid4()), "slug": slug}

        def update_blog_post(self, post_id, **kwargs):
            return {"id": post_id, **kwargs}

        def publish_blog_post(self, post_id, **kwargs):
            return {"id": post_id, "status": "PUBLISHED"}

        def delete_blog_post(self, post_id):
            return True

        # Testimonials
        def create_testimonial(self, **kwargs):
            return {"id": str(uuid4()), "author_name": kwargs.get("author_name")}

        def list_testimonials(self, **kwargs):
            return [{"id": str(uuid4()), "author_name": f"Author {i}"} for i in range(2)]

        def get_testimonial(self, testimonial_id):
            return {"id": str(uuid4()), "author_name": "John Doe"}

        def update_testimonial(self, testimonial_id, **kwargs):
            return {"id": testimonial_id, **kwargs}

        def publish_testimonial(self, testimonial_id, **kwargs):
            return {"id": testimonial_id, "status": "PUBLISHED"}

        def delete_testimonial(self, testimonial_id):
            return True

        # Contact
        def create_contact_submission(self, **kwargs):
            return {"id": str(uuid4()), "email": kwargs.get("email")}

        def list_contact_submissions(self, **kwargs):
            return [{"id": str(uuid4()), "email": f"user{i}@test.com"} for i in range(2)]

        def get_contact_submission(self, submission_id):
            return {"id": str(uuid4()), "email": "user@test.com"}

        def update_contact_submission(self, submission_id, **kwargs):
            return {"id": submission_id, **kwargs}

        def get_contact_stats(self):
            return {"total": 10, "new": 3, "processed": 7}

        # Newsletter
        def subscribe_newsletter(self, **kwargs):
            return {"id": str(uuid4()), "email": kwargs.get("email")}

        def verify_newsletter_subscription(self, token):
            return True

        def unsubscribe_newsletter(self, email):
            return True

        def list_newsletter_subscribers(self, **kwargs):
            return [{"id": str(uuid4()), "email": f"sub{i}@test.com"} for i in range(2)]

        def get_newsletter_stats(self):
            return {"total": 100, "verified": 85, "active": 80}

        # Media
        def create_media(self, **kwargs):
            return {"id": str(uuid4()), "filename": kwargs.get("filename")}

        def list_media(self, **kwargs):
            return [{"id": str(uuid4()), "filename": f"file{i}.jpg"} for i in range(2)]

        def get_media(self, media_id):
            return {"id": str(uuid4()), "filename": "file1.jpg"}

        def update_media(self, media_id, **kwargs):
            return {"id": media_id, **kwargs}

        def delete_media(self, media_id):
            return True

        # SEO
        def get_seo_config(self):
            return {"id": str(uuid4()), "site_title": "AZALSCORE"}

        def update_seo_config(self, **kwargs):
            return {"id": str(uuid4()), **kwargs}

        # Analytics
        def get_analytics_dashboard(self):
            return {"total_visits": 1000, "unique_visitors": 500}

        def list_analytics(self, **kwargs):
            return [{"id": str(uuid4()), "page_views": 100}]

        def record_analytics(self, **kwargs):
            pass

        # Config
        def get_public_site_config(self):
            return {"site_name": "AZALSCORE", "logo_url": "/logo.png"}

        def get_homepage(self):
            return {"id": str(uuid4()), "title": "Accueil"}

    from app.modules.website import router_v2
    def mock_get_service(db, tenant_id, user_id):
        return MockWebsiteService(db, tenant_id, user_id)

    monkeypatch.setattr(router_v2, "get_website_service", mock_get_service)
    return MockWebsiteService(None, tenant_id, user_id)


# Fixtures de données
@pytest.fixture
def sample_page_data():
    return {"title": "Test Page", "slug": "test-page", "page_type": "STATIC", "content": {}}


@pytest.fixture
def sample_blog_data():
    return {"title": "Test Post", "slug": "test-post", "content": "Content", "category": "Tech"}


@pytest.fixture
def sample_testimonial_data():
    return {"author_name": "John Doe", "author_role": "CEO", "company": "Test Inc", "content": "Great!", "rating": 5}


@pytest.fixture
def sample_contact_data():
    return {"name": "John Doe", "email": "john@test.com", "subject": "Question", "message": "Hello"}


@pytest.fixture
def sample_newsletter_data():
    return {"email": "subscriber@test.com", "name": "Subscriber"}


@pytest.fixture
def sample_media_data():
    return {"filename": "test.jpg", "file_url": "/uploads/test.jpg", "media_type": "IMAGE"}
