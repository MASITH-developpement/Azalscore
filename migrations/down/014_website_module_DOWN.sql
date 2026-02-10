-- AZALS - ROLLBACK Migration WEBSITE MODULE
-- Annule la creation du module site web officiel (T8)

DO $$
BEGIN
    -- Drop triggers
    DROP TRIGGER IF EXISTS update_site_pages_updated_at ON site_pages;
    DROP TRIGGER IF EXISTS update_blog_posts_updated_at ON blog_posts;
    DROP TRIGGER IF EXISTS update_testimonials_updated_at ON testimonials;
    DROP TRIGGER IF EXISTS update_contact_submissions_updated_at ON contact_submissions;
    DROP TRIGGER IF EXISTS update_newsletter_subscribers_updated_at ON newsletter_subscribers;
    DROP TRIGGER IF EXISTS update_site_media_updated_at ON site_media;
    DROP TRIGGER IF EXISTS update_site_seo_updated_at ON site_seo;

    -- Drop indexes for site_analytics
    DROP INDEX IF EXISTS idx_site_analytics_tenant;
    DROP INDEX IF EXISTS idx_site_analytics_date;
    DROP INDEX IF EXISTS idx_site_analytics_period;

    -- Drop indexes for site_seo
    DROP INDEX IF EXISTS idx_site_seo_tenant;

    -- Drop indexes for site_media
    DROP INDEX IF EXISTS idx_site_media_tenant;
    DROP INDEX IF EXISTS idx_site_media_type;
    DROP INDEX IF EXISTS idx_site_media_folder;

    -- Drop indexes for newsletter_subscribers
    DROP INDEX IF EXISTS idx_newsletter_subscribers_tenant;
    DROP INDEX IF EXISTS idx_newsletter_subscribers_email;
    DROP INDEX IF EXISTS idx_newsletter_subscribers_unique;

    -- Drop indexes for contact_submissions
    DROP INDEX IF EXISTS idx_contact_submissions_tenant;
    DROP INDEX IF EXISTS idx_contact_submissions_email;
    DROP INDEX IF EXISTS idx_contact_submissions_category;
    DROP INDEX IF EXISTS idx_contact_submissions_status;
    DROP INDEX IF EXISTS idx_contact_submissions_created;

    -- Drop indexes for testimonials
    DROP INDEX IF EXISTS idx_testimonials_tenant;
    DROP INDEX IF EXISTS idx_testimonials_industry;
    DROP INDEX IF EXISTS idx_testimonials_status;

    -- Drop indexes for blog_posts
    DROP INDEX IF EXISTS idx_blog_posts_tenant;
    DROP INDEX IF EXISTS idx_blog_posts_slug;
    DROP INDEX IF EXISTS idx_blog_posts_category;
    DROP INDEX IF EXISTS idx_blog_posts_status;
    DROP INDEX IF EXISTS idx_blog_posts_published;

    -- Drop indexes for site_pages
    DROP INDEX IF EXISTS idx_site_pages_tenant;
    DROP INDEX IF EXISTS idx_site_pages_slug;
    DROP INDEX IF EXISTS idx_site_pages_type;
    DROP INDEX IF EXISTS idx_site_pages_status;
    DROP INDEX IF EXISTS idx_site_pages_homepage;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS site_analytics CASCADE;
    DROP TABLE IF EXISTS site_seo CASCADE;
    DROP TABLE IF EXISTS site_media CASCADE;
    DROP TABLE IF EXISTS newsletter_subscribers CASCADE;
    DROP TABLE IF EXISTS contact_submissions CASCADE;
    DROP TABLE IF EXISTS testimonials CASCADE;
    DROP TABLE IF EXISTS blog_posts CASCADE;
    DROP TABLE IF EXISTS site_pages CASCADE;

    -- Drop ENUM types
    DROP TYPE IF EXISTS media_type;
    DROP TYPE IF EXISTS submission_status;
    DROP TYPE IF EXISTS form_category;
    DROP TYPE IF EXISTS content_type;
    DROP TYPE IF EXISTS publish_status;
    DROP TYPE IF EXISTS page_type;

    RAISE NOTICE 'Migration 014_website_module rolled back successfully';
END $$;
