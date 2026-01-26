"""Tests pour le router v2 du module Website - CORE SaaS v2."""

import pytest
from uuid import uuid4


BASE_URL = "/v2/website"


# ============================================================================
# TESTS PAGES
# ============================================================================

def test_create_page_success(test_client, mock_website_service, sample_page_data):
    response = test_client.post(f"{BASE_URL}/pages", json=sample_page_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_page_data["title"]


def test_list_pages(test_client):
    response = test_client.get(f"{BASE_URL}/pages")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_page_success(test_client):
    response = test_client.get(f"{BASE_URL}/pages/{uuid4()}")
    assert response.status_code == 200


def test_get_page_by_slug_success(test_client):
    response = test_client.get(f"{BASE_URL}/pages/slug/test-page")
    assert response.status_code == 200


def test_update_page_success(test_client):
    response = test_client.put(f"{BASE_URL}/pages/{uuid4()}", json={"title": "Updated"})
    assert response.status_code == 200


def test_publish_page_success(test_client):
    response = test_client.post(f"{BASE_URL}/pages/{uuid4()}/publish")
    assert response.status_code == 200


def test_delete_page_success(test_client):
    response = test_client.delete(f"{BASE_URL}/pages/{uuid4()}")
    assert response.status_code == 204


# ============================================================================
# TESTS BLOG
# ============================================================================

def test_create_blog_post_success(test_client, mock_website_service, sample_blog_data):
    response = test_client.post(f"{BASE_URL}/blog/posts", json=sample_blog_data)
    assert response.status_code == 201


def test_list_blog_posts(test_client):
    response = test_client.get(f"{BASE_URL}/blog/posts")
    assert response.status_code == 200


def test_list_blog_posts_with_filters(test_client):
    response = test_client.get(f"{BASE_URL}/blog/posts", params={"category": "Tech", "published_only": True})
    assert response.status_code == 200


def test_list_blog_categories(test_client):
    response = test_client.get(f"{BASE_URL}/blog/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data


def test_get_blog_post_success(test_client):
    response = test_client.get(f"{BASE_URL}/blog/posts/{uuid4()}")
    assert response.status_code == 200


def test_get_blog_post_by_slug_success(test_client):
    response = test_client.get(f"{BASE_URL}/blog/posts/slug/test-post")
    assert response.status_code == 200


def test_update_blog_post_success(test_client):
    response = test_client.put(f"{BASE_URL}/blog/posts/{uuid4()}", json={"title": "Updated Post"})
    assert response.status_code == 200


def test_publish_blog_post_success(test_client):
    response = test_client.post(f"{BASE_URL}/blog/posts/{uuid4()}/publish")
    assert response.status_code == 200


def test_delete_blog_post_success(test_client):
    response = test_client.delete(f"{BASE_URL}/blog/posts/{uuid4()}")
    assert response.status_code == 204


# ============================================================================
# TESTS TESTIMONIALS
# ============================================================================

def test_create_testimonial_success(test_client, mock_website_service, sample_testimonial_data):
    response = test_client.post(f"{BASE_URL}/testimonials", json=sample_testimonial_data)
    assert response.status_code == 201


def test_list_testimonials(test_client):
    response = test_client.get(f"{BASE_URL}/testimonials")
    assert response.status_code == 200


def test_list_testimonials_published_only(test_client):
    response = test_client.get(f"{BASE_URL}/testimonials", params={"published_only": True})
    assert response.status_code == 200


def test_get_testimonial_success(test_client):
    response = test_client.get(f"{BASE_URL}/testimonials/{uuid4()}")
    assert response.status_code == 200


def test_update_testimonial_success(test_client):
    response = test_client.put(f"{BASE_URL}/testimonials/{uuid4()}", json={"rating": 4})
    assert response.status_code == 200


def test_publish_testimonial_success(test_client):
    response = test_client.post(f"{BASE_URL}/testimonials/{uuid4()}/publish")
    assert response.status_code == 200


def test_delete_testimonial_success(test_client):
    response = test_client.delete(f"{BASE_URL}/testimonials/{uuid4()}")
    assert response.status_code == 204


# ============================================================================
# TESTS CONTACT
# ============================================================================

def test_submit_contact_form_success(test_client, mock_website_service, sample_contact_data):
    response = test_client.post(f"{BASE_URL}/contact", json=sample_contact_data)
    assert response.status_code == 201


def test_list_contact_submissions(test_client):
    response = test_client.get(f"{BASE_URL}/contact/submissions")
    assert response.status_code == 200


def test_list_contact_submissions_with_filters(test_client):
    response = test_client.get(f"{BASE_URL}/contact/submissions", params={"category": "GENERAL", "status": "NEW"})
    assert response.status_code == 200


def test_get_contact_submission_success(test_client):
    response = test_client.get(f"{BASE_URL}/contact/submissions/{uuid4()}")
    assert response.status_code == 200


def test_update_contact_submission_success(test_client):
    response = test_client.put(f"{BASE_URL}/contact/submissions/{uuid4()}", json={"status": "PROCESSED"})
    assert response.status_code == 200


def test_get_contact_stats(test_client):
    response = test_client.get(f"{BASE_URL}/contact/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data


# ============================================================================
# TESTS NEWSLETTER
# ============================================================================

def test_subscribe_newsletter_success(test_client, mock_website_service, sample_newsletter_data):
    response = test_client.post(f"{BASE_URL}/newsletter/subscribe", json=sample_newsletter_data)
    assert response.status_code == 201


def test_verify_newsletter_subscription(test_client):
    response = test_client.post(f"{BASE_URL}/newsletter/verify/test-token")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_unsubscribe_newsletter_success(test_client):
    response = test_client.post(f"{BASE_URL}/newsletter/unsubscribe", params={"email": "test@example.com"})
    assert response.status_code == 200


def test_list_newsletter_subscribers(test_client):
    response = test_client.get(f"{BASE_URL}/newsletter/subscribers")
    assert response.status_code == 200


def test_list_newsletter_subscribers_verified_only(test_client):
    response = test_client.get(f"{BASE_URL}/newsletter/subscribers", params={"verified_only": True})
    assert response.status_code == 200


def test_get_newsletter_stats(test_client):
    response = test_client.get(f"{BASE_URL}/newsletter/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data


# ============================================================================
# TESTS MEDIA
# ============================================================================

def test_upload_media_success(test_client, mock_website_service, sample_media_data):
    response = test_client.post(f"{BASE_URL}/media", json=sample_media_data)
    assert response.status_code == 201


def test_list_media(test_client):
    response = test_client.get(f"{BASE_URL}/media")
    assert response.status_code == 200


def test_list_media_by_type(test_client):
    response = test_client.get(f"{BASE_URL}/media", params={"media_type": "IMAGE"})
    assert response.status_code == 200


def test_get_media_success(test_client):
    response = test_client.get(f"{BASE_URL}/media/{uuid4()}")
    assert response.status_code == 200


def test_update_media_success(test_client):
    response = test_client.put(f"{BASE_URL}/media/{uuid4()}", json={"title": "Updated Media"})
    assert response.status_code == 200


def test_delete_media_success(test_client):
    response = test_client.delete(f"{BASE_URL}/media/{uuid4()}")
    assert response.status_code == 204


# ============================================================================
# TESTS SEO
# ============================================================================

def test_get_seo_config(test_client):
    response = test_client.get(f"{BASE_URL}/seo")
    assert response.status_code == 200
    data = response.json()
    assert "site_title" in data


def test_update_seo_config(test_client):
    update_data = {"site_title": "AZALSCORE Updated", "meta_description": "New description"}
    response = test_client.put(f"{BASE_URL}/seo", json=update_data)
    assert response.status_code == 200


# ============================================================================
# TESTS ANALYTICS
# ============================================================================

def test_get_analytics_dashboard(test_client):
    response = test_client.get(f"{BASE_URL}/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_visits" in data


def test_list_analytics(test_client):
    response = test_client.get(f"{BASE_URL}/analytics")
    assert response.status_code == 200


def test_list_analytics_with_limit(test_client):
    response = test_client.get(f"{BASE_URL}/analytics", params={"limit": 50})
    assert response.status_code == 200


def test_record_analytics(test_client):
    data = {"event": "page_view", "page": "/home"}
    response = test_client.post(f"{BASE_URL}/analytics/record", json=data)
    assert response.status_code == 200


# ============================================================================
# TESTS PUBLIC CONFIG & HOMEPAGE
# ============================================================================

def test_get_public_site_config(test_client):
    response = test_client.get(f"{BASE_URL}/config")
    assert response.status_code == 200
    data = response.json()
    assert "site_name" in data


def test_get_homepage(test_client):
    response = test_client.get(f"{BASE_URL}/homepage")
    assert response.status_code == 200
    data = response.json()
    assert "title" in data


# ============================================================================
# TESTS VALIDATION & ERRORS
# ============================================================================

def test_create_page_missing_fields(test_client):
    response = test_client.post(f"{BASE_URL}/pages", json={"title": "Only Title"})
    assert response.status_code == 422


def test_create_blog_post_missing_fields(test_client):
    response = test_client.post(f"{BASE_URL}/blog/posts", json={"title": "Only Title"})
    assert response.status_code == 422


def test_create_testimonial_missing_fields(test_client):
    response = test_client.post(f"{BASE_URL}/testimonials", json={"author_name": "Only Name"})
    assert response.status_code == 422


def test_get_nonexistent_page(test_client, mock_website_service, monkeypatch):
    def mock_get(self, _id):
        return None
    from app.modules.website import service
    monkeypatch.setattr(service.WebsiteService, "get_page", mock_get)
    response = test_client.get(f"{BASE_URL}/pages/{uuid4()}")
    assert response.status_code == 404


def test_get_nonexistent_blog_post(test_client, mock_website_service, monkeypatch):
    def mock_get(self, _id):
        return None
    from app.modules.website import service
    monkeypatch.setattr(service.WebsiteService, "get_blog_post", mock_get)
    response = test_client.get(f"{BASE_URL}/blog/posts/{uuid4()}")
    assert response.status_code == 404


def test_delete_nonexistent_media(test_client, mock_website_service, monkeypatch):
    def mock_delete(self, _id):
        return False
    from app.modules.website import service
    monkeypatch.setattr(service.WebsiteService, "delete_media", mock_delete)
    response = test_client.delete(f"{BASE_URL}/media/{uuid4()}")
    assert response.status_code == 404


# ============================================================================
# TESTS PAGINATION & LIMITS
# ============================================================================

def test_list_blog_posts_pagination(test_client):
    response = test_client.get(f"{BASE_URL}/blog/posts", params={"limit": 10})
    assert response.status_code == 200


def test_list_testimonials_pagination(test_client):
    response = test_client.get(f"{BASE_URL}/testimonials", params={"limit": 20})
    assert response.status_code == 200


def test_list_contact_submissions_pagination(test_client):
    response = test_client.get(f"{BASE_URL}/contact/submissions", params={"limit": 15})
    assert response.status_code == 200


def test_list_newsletter_subscribers_pagination(test_client):
    response = test_client.get(f"{BASE_URL}/newsletter/subscribers", params={"limit": 25})
    assert response.status_code == 200


# ============================================================================
# TESTS ISOLATION TENANT
# ============================================================================

def test_pages_tenant_isolation(test_client):
    response = test_client.get(f"{BASE_URL}/pages")
    assert response.status_code == 200


def test_blog_tenant_isolation(test_client):
    response = test_client.get(f"{BASE_URL}/blog/posts")
    assert response.status_code == 200


def test_contact_tenant_isolation(test_client):
    response = test_client.get(f"{BASE_URL}/contact/submissions")
    assert response.status_code == 200


def test_media_tenant_isolation(test_client):
    response = test_client.get(f"{BASE_URL}/media")
    assert response.status_code == 200
