/**
 * AZALSCORE - Website CMS API
 * ============================
 * Complete typed API client for Website/CMS module.
 * Covers: Pages, Blog, Testimonials, Contact Forms, Newsletter, Media, SEO, Analytics
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const websiteKeys = {
  all: ['website'] as const,

  // Pages
  pages: () => [...websiteKeys.all, 'pages'] as const,
  page: (id: string) => [...websiteKeys.pages(), id] as const,
  pageBySlug: (slug: string) => [...websiteKeys.pages(), 'slug', slug] as const,
  menu: () => [...websiteKeys.all, 'menu'] as const,

  // Blog
  posts: () => [...websiteKeys.all, 'posts'] as const,
  post: (id: string) => [...websiteKeys.posts(), id] as const,
  postBySlug: (slug: string) => [...websiteKeys.posts(), 'slug', slug] as const,

  // Testimonials
  testimonials: () => [...websiteKeys.all, 'testimonials'] as const,
  testimonial: (id: string) => [...websiteKeys.testimonials(), id] as const,

  // Contact
  submissions: () => [...websiteKeys.all, 'submissions'] as const,
  submission: (id: string) => [...websiteKeys.submissions(), id] as const,

  // Newsletter
  subscribers: () => [...websiteKeys.all, 'subscribers'] as const,

  // Media
  media: () => [...websiteKeys.all, 'media'] as const,
  mediaItem: (id: string) => [...websiteKeys.media(), id] as const,

  // SEO
  seo: () => [...websiteKeys.all, 'seo'] as const,

  // Analytics
  analytics: (period?: string) => [...websiteKeys.all, 'analytics', period] as const,
  analyticsDashboard: () => [...websiteKeys.all, 'analytics-dashboard'] as const,

  // Public config
  publicConfig: () => [...websiteKeys.all, 'public-config'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type PageType = 'LANDING' | 'PRODUCT' | 'PRICING' | 'ABOUT' | 'CONTACT' | 'BLOG' | 'DOCUMENTATION' | 'LEGAL' | 'CUSTOM';
export type PublishStatus = 'DRAFT' | 'PENDING_REVIEW' | 'PUBLISHED' | 'ARCHIVED';
export type ContentType = 'ARTICLE' | 'NEWS' | 'CASE_STUDY' | 'TESTIMONIAL' | 'FAQ' | 'TUTORIAL' | 'RELEASE_NOTE';
export type FormCategory = 'CONTACT' | 'DEMO_REQUEST' | 'QUOTE_REQUEST' | 'SUPPORT' | 'NEWSLETTER' | 'FEEDBACK';
export type SubmissionStatus = 'NEW' | 'READ' | 'REPLIED' | 'CLOSED' | 'SPAM';
export type MediaType = 'IMAGE' | 'VIDEO' | 'DOCUMENT' | 'AUDIO';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface SitePage {
  id: number;
  tenant_id: string;
  slug: string;
  page_type: PageType;
  title: string;
  subtitle?: string | null;
  content?: string | null;
  excerpt?: string | null;
  featured_image?: string | null;
  hero_video?: string | null;
  meta_title?: string | null;
  meta_description?: string | null;
  meta_keywords?: string | null;
  canonical_url?: string | null;
  og_image?: string | null;
  template: string;
  layout_config?: Record<string, unknown> | null;
  sections?: Array<Record<string, unknown>> | null;
  status: PublishStatus;
  published_at?: string | null;
  parent_id?: number | null;
  sort_order: number;
  show_in_menu: boolean;
  show_in_footer: boolean;
  language: string;
  translations?: Record<string, number> | null;
  view_count: number;
  is_homepage: boolean;
  is_system: boolean;
  requires_auth: boolean;
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface SitePageListItem {
  id: number;
  slug: string;
  page_type: PageType;
  title: string;
  status: PublishStatus;
  sort_order: number;
  show_in_menu: boolean;
  is_homepage: boolean;
  view_count: number;
  updated_at: string;
}

export interface BlogPost {
  id: number;
  tenant_id: string;
  slug: string;
  content_type: ContentType;
  title: string;
  subtitle?: string | null;
  content?: string | null;
  excerpt?: string | null;
  featured_image?: string | null;
  gallery?: Array<Record<string, unknown>> | null;
  meta_title?: string | null;
  meta_description?: string | null;
  meta_keywords?: string | null;
  category?: string | null;
  tags?: string[] | null;
  author_id?: number | null;
  author_name?: string | null;
  author_avatar?: string | null;
  author_bio?: string | null;
  status: PublishStatus;
  published_at?: string | null;
  language: string;
  translations?: Record<string, number> | null;
  view_count: number;
  like_count: number;
  share_count: number;
  comment_count: number;
  reading_time?: number | null;
  is_featured: boolean;
  is_pinned: boolean;
  allow_comments: boolean;
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface BlogPostListItem {
  id: number;
  slug: string;
  content_type: ContentType;
  title: string;
  excerpt?: string | null;
  featured_image?: string | null;
  category?: string | null;
  tags?: string[] | null;
  author_name?: string | null;
  status: PublishStatus;
  published_at?: string | null;
  view_count: number;
  reading_time?: number | null;
  is_featured: boolean;
  is_pinned: boolean;
}

export interface Testimonial {
  id: number;
  tenant_id: string;
  client_name: string;
  client_title?: string | null;
  client_company?: string | null;
  client_logo?: string | null;
  client_avatar?: string | null;
  quote: string;
  full_testimonial?: string | null;
  industry?: string | null;
  use_case?: string | null;
  modules_used?: string[] | null;
  metrics?: Array<Record<string, unknown>> | null;
  video_url?: string | null;
  case_study_url?: string | null;
  status: PublishStatus;
  published_at?: string | null;
  rating?: number | null;
  sort_order: number;
  is_featured: boolean;
  show_on_homepage: boolean;
  language: string;
  created_at: string;
  updated_at: string;
}

export interface ContactSubmission {
  id: number;
  tenant_id: string;
  form_category: FormCategory;
  first_name?: string | null;
  last_name?: string | null;
  email: string;
  phone?: string | null;
  company?: string | null;
  job_title?: string | null;
  subject?: string | null;
  message?: string | null;
  source_page?: string | null;
  utm_source?: string | null;
  utm_medium?: string | null;
  utm_campaign?: string | null;
  referrer?: string | null;
  interested_modules?: string[] | null;
  company_size?: string | null;
  timeline?: string | null;
  budget?: string | null;
  custom_fields?: Record<string, unknown> | null;
  status: SubmissionStatus;
  assigned_to?: number | null;
  response?: string | null;
  responded_at?: string | null;
  responded_by?: number | null;
  notes?: string | null;
  follow_up_date?: string | null;
  consent_marketing: boolean;
  consent_newsletter: boolean;
  consent_privacy: boolean;
  created_at: string;
  updated_at: string;
}

export interface NewsletterSubscriber {
  id: number;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  company?: string | null;
  language: string;
  interests?: string[] | null;
  frequency: string;
  is_active: boolean;
  is_verified: boolean;
  verified_at?: string | null;
  source?: string | null;
  emails_received: number;
  emails_opened: number;
  emails_clicked: number;
  created_at: string;
}

export interface SiteMedia {
  id: number;
  tenant_id: string;
  filename: string;
  original_name?: string | null;
  media_type: MediaType;
  mime_type?: string | null;
  url: string;
  storage_path?: string | null;
  file_size?: number | null;
  width?: number | null;
  height?: number | null;
  duration?: number | null;
  thumbnail_url?: string | null;
  optimized_url?: string | null;
  alt_text?: string | null;
  title?: string | null;
  description?: string | null;
  caption?: string | null;
  folder: string;
  tags?: string[] | null;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface SiteSEO {
  id: number;
  tenant_id: string;
  site_title?: string | null;
  site_description?: string | null;
  site_keywords?: string | null;
  og_site_name?: string | null;
  og_default_image?: string | null;
  og_locale?: string | null;
  twitter_card?: string | null;
  twitter_site?: string | null;
  twitter_creator?: string | null;
  google_site_verification?: string | null;
  bing_site_verification?: string | null;
  organization_schema?: Record<string, unknown> | null;
  local_business_schema?: Record<string, unknown> | null;
  robots_txt?: string | null;
  sitemap_url?: string | null;
  google_analytics_id?: string | null;
  google_tag_manager_id?: string | null;
  facebook_pixel_id?: string | null;
  head_scripts?: string | null;
  body_scripts?: string | null;
  redirects?: Array<{ from: string; to: string; status?: number }> | null;
  updated_at: string;
}

export interface SiteAnalytics {
  id: number;
  tenant_id: string;
  date: string;
  period: string;
  page_views: number;
  unique_visitors: number;
  sessions: number;
  bounce_rate?: number | null;
  avg_session_duration?: number | null;
  pages_per_session?: number | null;
  traffic_sources?: Record<string, number> | null;
  referrers?: Record<string, number> | null;
  countries?: Record<string, number> | null;
  cities?: Record<string, number> | null;
  devices?: Record<string, number> | null;
  browsers?: Record<string, number> | null;
  top_pages?: Array<Record<string, unknown>> | null;
  form_submissions: number;
  newsletter_signups: number;
  demo_requests: number;
  blog_views: number;
  top_posts?: Array<Record<string, unknown>> | null;
}

export interface AnalyticsDashboard {
  period: string;
  total_page_views: number;
  total_unique_visitors: number;
  total_sessions: number;
  avg_bounce_rate?: number | null;
  total_form_submissions: number;
  total_newsletter_signups: number;
  total_demo_requests: number;
  total_blog_views: number;
  traffic_by_source: Record<string, number>;
  top_pages: Array<Record<string, unknown>>;
  top_posts: Array<Record<string, unknown>>;
  daily_stats: Array<Record<string, unknown>>;
}

export interface SiteMenuItem {
  id: number;
  slug: string;
  title: string;
  page_type: PageType;
  sort_order: number;
  parent_id?: number | null;
  children: SiteMenuItem[];
}

export interface PublicSiteConfig {
  site_title: string;
  site_description?: string | null;
  og_image?: string | null;
  menu: SiteMenuItem[];
  footer_pages: SiteMenuItem[];
  analytics_enabled: boolean;
  language: string;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface PageCreate {
  slug: string;
  page_type?: PageType;
  title: string;
  subtitle?: string;
  content?: string;
  excerpt?: string;
  featured_image?: string;
  hero_video?: string;
  meta_title?: string;
  meta_description?: string;
  meta_keywords?: string;
  canonical_url?: string;
  og_image?: string;
  template?: string;
  layout_config?: Record<string, unknown>;
  sections?: Array<Record<string, unknown>>;
  parent_id?: number;
  sort_order?: number;
  show_in_menu?: boolean;
  show_in_footer?: boolean;
  language?: string;
  is_homepage?: boolean;
  requires_auth?: boolean;
}

export interface PageUpdate {
  slug?: string;
  page_type?: PageType;
  title?: string;
  subtitle?: string;
  content?: string;
  excerpt?: string;
  featured_image?: string;
  hero_video?: string;
  meta_title?: string;
  meta_description?: string;
  meta_keywords?: string;
  canonical_url?: string;
  og_image?: string;
  template?: string;
  layout_config?: Record<string, unknown>;
  sections?: Array<Record<string, unknown>>;
  parent_id?: number;
  sort_order?: number;
  show_in_menu?: boolean;
  show_in_footer?: boolean;
  language?: string;
  requires_auth?: boolean;
}

export interface BlogPostCreate {
  slug: string;
  content_type?: ContentType;
  title: string;
  subtitle?: string;
  content?: string;
  excerpt?: string;
  featured_image?: string;
  gallery?: Array<Record<string, unknown>>;
  meta_title?: string;
  meta_description?: string;
  meta_keywords?: string;
  category?: string;
  tags?: string[];
  author_name?: string;
  author_avatar?: string;
  author_bio?: string;
  language?: string;
  reading_time?: number;
  is_featured?: boolean;
  is_pinned?: boolean;
  allow_comments?: boolean;
}

export interface BlogPostUpdate {
  slug?: string;
  content_type?: ContentType;
  title?: string;
  subtitle?: string;
  content?: string;
  excerpt?: string;
  featured_image?: string;
  gallery?: Array<Record<string, unknown>>;
  meta_title?: string;
  meta_description?: string;
  meta_keywords?: string;
  category?: string;
  tags?: string[];
  author_name?: string;
  author_avatar?: string;
  author_bio?: string;
  language?: string;
  reading_time?: number;
  is_featured?: boolean;
  is_pinned?: boolean;
  allow_comments?: boolean;
}

export interface TestimonialCreate {
  client_name: string;
  client_title?: string;
  client_company?: string;
  client_logo?: string;
  client_avatar?: string;
  quote: string;
  full_testimonial?: string;
  industry?: string;
  use_case?: string;
  modules_used?: string[];
  metrics?: Array<Record<string, unknown>>;
  video_url?: string;
  case_study_url?: string;
  rating?: number;
  sort_order?: number;
  is_featured?: boolean;
  show_on_homepage?: boolean;
  language?: string;
}

export interface TestimonialUpdate {
  client_name?: string;
  client_title?: string;
  client_company?: string;
  client_logo?: string;
  client_avatar?: string;
  quote?: string;
  full_testimonial?: string;
  industry?: string;
  use_case?: string;
  modules_used?: string[];
  metrics?: Array<Record<string, unknown>>;
  video_url?: string;
  case_study_url?: string;
  rating?: number;
  sort_order?: number;
  is_featured?: boolean;
  show_on_homepage?: boolean;
}

export interface ContactSubmissionCreate {
  form_category: FormCategory;
  first_name?: string;
  last_name?: string;
  email: string;
  phone?: string;
  company?: string;
  job_title?: string;
  subject?: string;
  message?: string;
  source_page?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  interested_modules?: string[];
  company_size?: string;
  timeline?: string;
  budget?: string;
  custom_fields?: Record<string, unknown>;
  consent_marketing?: boolean;
  consent_newsletter?: boolean;
  consent_privacy?: boolean;
}

export interface ContactSubmissionUpdate {
  status?: SubmissionStatus;
  assigned_to?: number;
  response?: string;
  notes?: string;
  follow_up_date?: string;
}

export interface NewsletterSubscribeRequest {
  email: string;
  first_name?: string;
  last_name?: string;
  company?: string;
  language?: string;
  interests?: string[];
  frequency?: string;
  source?: string;
  source_page?: string;
  gdpr_consent?: boolean;
}

export interface MediaCreate {
  filename: string;
  original_name?: string;
  media_type: MediaType;
  mime_type?: string;
  url: string;
  storage_path?: string;
  file_size?: number;
  width?: number;
  height?: number;
  duration?: number;
  thumbnail_url?: string;
  optimized_url?: string;
  alt_text?: string;
  title?: string;
  description?: string;
  caption?: string;
  folder?: string;
  tags?: string[];
}

export interface MediaUpdate {
  alt_text?: string;
  title?: string;
  description?: string;
  caption?: string;
  folder?: string;
  tags?: string[];
}

export interface SEOUpdate {
  site_title?: string;
  site_description?: string;
  site_keywords?: string;
  og_site_name?: string;
  og_default_image?: string;
  og_locale?: string;
  twitter_card?: string;
  twitter_site?: string;
  twitter_creator?: string;
  google_site_verification?: string;
  bing_site_verification?: string;
  organization_schema?: Record<string, unknown>;
  local_business_schema?: Record<string, unknown>;
  robots_txt?: string;
  sitemap_url?: string;
  google_analytics_id?: string;
  google_tag_manager_id?: string;
  facebook_pixel_id?: string;
  head_scripts?: string;
  body_scripts?: string;
  redirects?: Array<{ from: string; to: string; status?: number }>;
}

export interface PublishRequest {
  publish: boolean;
  schedule_at?: string;
}

// ============================================================================
// HOOKS - PAGES
// ============================================================================

export function usePages(filters?: {
  page_type?: PageType;
  status?: PublishStatus;
  show_in_menu?: boolean;
  language?: string;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...websiteKeys.pages(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.page_type) params.append('page_type', filters.page_type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.show_in_menu !== undefined) params.append('show_in_menu', String(filters.show_in_menu));
      if (filters?.language) params.append('language', filters.language);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: SitePageListItem[]; total: number }>(
        `/website/pages${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function usePage(id: string) {
  return useQuery({
    queryKey: websiteKeys.page(id),
    queryFn: async () => {
      const response = await api.get<SitePage>(`/website/pages/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function usePageBySlug(slug: string) {
  return useQuery({
    queryKey: websiteKeys.pageBySlug(slug),
    queryFn: async () => {
      const response = await api.get<SitePage>(`/website/pages/slug/${slug}`);
      return response;
    },
    enabled: !!slug,
  });
}

export function useCreatePage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: PageCreate) => {
      return api.post<SitePage>('/website/pages', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.pages() });
      queryClient.invalidateQueries({ queryKey: websiteKeys.menu() });
    },
  });
}

export function useUpdatePage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: PageUpdate }) => {
      return api.put<SitePage>(`/website/pages/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.pages() });
      queryClient.invalidateQueries({ queryKey: websiteKeys.page(id) });
      queryClient.invalidateQueries({ queryKey: websiteKeys.menu() });
    },
  });
}

export function useDeletePage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/website/pages/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.pages() });
      queryClient.invalidateQueries({ queryKey: websiteKeys.menu() });
    },
  });
}

export function usePublishPage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: PublishRequest }) => {
      return api.post<SitePage>(`/website/pages/${id}/publish`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.page(id) });
      queryClient.invalidateQueries({ queryKey: websiteKeys.pages() });
    },
  });
}

export function useDuplicatePage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, newSlug }: { id: string; newSlug: string }) => {
      return api.post<SitePage>(`/website/pages/${id}/duplicate`, { new_slug: newSlug });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.pages() });
    },
  });
}

export function useSiteMenu() {
  return useQuery({
    queryKey: websiteKeys.menu(),
    queryFn: async () => {
      const response = await api.get<{ menu: SiteMenuItem[]; footer: SiteMenuItem[] }>('/website/menu');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - BLOG
// ============================================================================

export function useBlogPosts(filters?: {
  content_type?: ContentType;
  status?: PublishStatus;
  category?: string;
  tag?: string;
  is_featured?: boolean;
  language?: string;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...websiteKeys.posts(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.content_type) params.append('content_type', filters.content_type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.category) params.append('category', filters.category);
      if (filters?.tag) params.append('tag', filters.tag);
      if (filters?.is_featured !== undefined) params.append('is_featured', String(filters.is_featured));
      if (filters?.language) params.append('language', filters.language);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: BlogPostListItem[]; total: number }>(
        `/website/blog${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useBlogPost(id: string) {
  return useQuery({
    queryKey: websiteKeys.post(id),
    queryFn: async () => {
      const response = await api.get<BlogPost>(`/website/blog/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useBlogPostBySlug(slug: string) {
  return useQuery({
    queryKey: websiteKeys.postBySlug(slug),
    queryFn: async () => {
      const response = await api.get<BlogPost>(`/website/blog/slug/${slug}`);
      return response;
    },
    enabled: !!slug,
  });
}

export function useCreateBlogPost() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: BlogPostCreate) => {
      return api.post<BlogPost>('/website/blog', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.posts() });
    },
  });
}

export function useUpdateBlogPost() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: BlogPostUpdate }) => {
      return api.put<BlogPost>(`/website/blog/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.posts() });
      queryClient.invalidateQueries({ queryKey: websiteKeys.post(id) });
    },
  });
}

export function useDeleteBlogPost() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/website/blog/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.posts() });
    },
  });
}

export function usePublishBlogPost() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: PublishRequest }) => {
      return api.post<BlogPost>(`/website/blog/${id}/publish`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.post(id) });
      queryClient.invalidateQueries({ queryKey: websiteKeys.posts() });
    },
  });
}

export function useBlogCategories() {
  return useQuery({
    queryKey: [...websiteKeys.posts(), 'categories'],
    queryFn: async () => {
      const response = await api.get<{ categories: Array<{ name: string; count: number }> }>(
        '/website/blog/categories'
      );
      return response;
    },
  });
}

export function useBlogTags() {
  return useQuery({
    queryKey: [...websiteKeys.posts(), 'tags'],
    queryFn: async () => {
      const response = await api.get<{ tags: Array<{ name: string; count: number }> }>(
        '/website/blog/tags'
      );
      return response;
    },
  });
}

// ============================================================================
// HOOKS - TESTIMONIALS
// ============================================================================

export function useTestimonials(filters?: {
  status?: PublishStatus;
  is_featured?: boolean;
  show_on_homepage?: boolean;
  industry?: string;
  language?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...websiteKeys.testimonials(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.is_featured !== undefined) params.append('is_featured', String(filters.is_featured));
      if (filters?.show_on_homepage !== undefined) params.append('show_on_homepage', String(filters.show_on_homepage));
      if (filters?.industry) params.append('industry', filters.industry);
      if (filters?.language) params.append('language', filters.language);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Testimonial[]; total: number }>(
        `/website/testimonials${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useTestimonial(id: string) {
  return useQuery({
    queryKey: websiteKeys.testimonial(id),
    queryFn: async () => {
      const response = await api.get<Testimonial>(`/website/testimonials/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateTestimonial() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: TestimonialCreate) => {
      return api.post<Testimonial>('/website/testimonials', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.testimonials() });
    },
  });
}

export function useUpdateTestimonial() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TestimonialUpdate }) => {
      return api.put<Testimonial>(`/website/testimonials/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.testimonials() });
      queryClient.invalidateQueries({ queryKey: websiteKeys.testimonial(id) });
    },
  });
}

export function useDeleteTestimonial() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/website/testimonials/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.testimonials() });
    },
  });
}

export function usePublishTestimonial() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: PublishRequest }) => {
      return api.post<Testimonial>(`/website/testimonials/${id}/publish`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.testimonial(id) });
      queryClient.invalidateQueries({ queryKey: websiteKeys.testimonials() });
    },
  });
}

// ============================================================================
// HOOKS - CONTACT SUBMISSIONS
// ============================================================================

export function useContactSubmissions(filters?: {
  form_category?: FormCategory;
  status?: SubmissionStatus;
  assigned_to?: number;
  from_date?: string;
  to_date?: string;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...websiteKeys.submissions(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.form_category) params.append('form_category', filters.form_category);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.assigned_to) params.append('assigned_to', String(filters.assigned_to));
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: ContactSubmission[]; total: number }>(
        `/website/contact${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useContactSubmission(id: string) {
  return useQuery({
    queryKey: websiteKeys.submission(id),
    queryFn: async () => {
      const response = await api.get<ContactSubmission>(`/website/contact/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useSubmitContactForm() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ContactSubmissionCreate) => {
      return api.post<ContactSubmission>('/website/contact', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.submissions() });
    },
  });
}

export function useUpdateContactSubmission() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ContactSubmissionUpdate }) => {
      return api.put<ContactSubmission>(`/website/contact/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.submissions() });
      queryClient.invalidateQueries({ queryKey: websiteKeys.submission(id) });
    },
  });
}

export function useReplyToSubmission() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, response }: { id: string; response: string }) => {
      return api.post<ContactSubmission>(`/website/contact/${id}/reply`, { response });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.submission(id) });
      queryClient.invalidateQueries({ queryKey: websiteKeys.submissions() });
    },
  });
}

export function useMarkSubmissionAsSpam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<ContactSubmission>(`/website/contact/${id}/spam`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.submissions() });
    },
  });
}

// ============================================================================
// HOOKS - NEWSLETTER
// ============================================================================

export function useNewsletterSubscribers(filters?: {
  is_active?: boolean;
  is_verified?: boolean;
  language?: string;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...websiteKeys.subscribers(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      if (filters?.is_verified !== undefined) params.append('is_verified', String(filters.is_verified));
      if (filters?.language) params.append('language', filters.language);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: NewsletterSubscriber[]; total: number }>(
        `/website/newsletter${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useSubscribeNewsletter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: NewsletterSubscribeRequest) => {
      return api.post<NewsletterSubscriber>('/website/newsletter/subscribe', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.subscribers() });
    },
  });
}

export function useUnsubscribeNewsletter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (token: string) => {
      return api.post('/website/newsletter/unsubscribe', { token });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.subscribers() });
    },
  });
}

export function useVerifyNewsletterEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (token: string) => {
      return api.post('/website/newsletter/verify', { token });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.subscribers() });
    },
  });
}

export function useExportNewsletterSubscribers() {
  return useMutation({
    mutationFn: async (format: 'csv' | 'excel') => {
      return api.post<{ download_url: string; expires_at: string }>(
        '/website/newsletter/export',
        { format }
      );
    },
  });
}

// ============================================================================
// HOOKS - MEDIA
// ============================================================================

export function useSiteMedia(filters?: {
  media_type?: MediaType;
  folder?: string;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...websiteKeys.media(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.media_type) params.append('media_type', filters.media_type);
      if (filters?.folder) params.append('folder', filters.folder);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: SiteMedia[]; total: number }>(
        `/website/media${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useSiteMediaItem(id: string) {
  return useQuery({
    queryKey: websiteKeys.mediaItem(id),
    queryFn: async () => {
      const response = await api.get<SiteMedia>(`/website/media/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useUploadMedia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, folder, alt_text, title }: {
      file: File;
      folder?: string;
      alt_text?: string;
      title?: string;
    }) => {
      const formData = new FormData();
      formData.append('file', file);
      if (folder) formData.append('folder', folder);
      if (alt_text) formData.append('alt_text', alt_text);
      if (title) formData.append('title', title);
      return api.post<SiteMedia>('/website/media/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.media() });
    },
  });
}

export function useUpdateMedia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: MediaUpdate }) => {
      return api.put<SiteMedia>(`/website/media/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.media() });
      queryClient.invalidateQueries({ queryKey: websiteKeys.mediaItem(id) });
    },
  });
}

export function useDeleteMedia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/website/media/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.media() });
    },
  });
}

export function useMediaFolders() {
  return useQuery({
    queryKey: [...websiteKeys.media(), 'folders'],
    queryFn: async () => {
      const response = await api.get<{ folders: string[] }>('/website/media/folders');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - SEO
// ============================================================================

export function useSiteSEO() {
  return useQuery({
    queryKey: websiteKeys.seo(),
    queryFn: async () => {
      const response = await api.get<SiteSEO>('/website/seo');
      return response;
    },
  });
}

export function useUpdateSiteSEO() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: SEOUpdate) => {
      return api.put<SiteSEO>('/website/seo', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteKeys.seo() });
      queryClient.invalidateQueries({ queryKey: websiteKeys.publicConfig() });
    },
  });
}

export function useGenerateSitemap() {
  return useMutation({
    mutationFn: async () => {
      return api.post<{ sitemap_url: string }>('/website/seo/generate-sitemap');
    },
  });
}

// ============================================================================
// HOOKS - ANALYTICS
// ============================================================================

export function useSiteAnalytics(period: string = '30d') {
  return useQuery({
    queryKey: websiteKeys.analytics(period),
    queryFn: async () => {
      const response = await api.get<{ items: SiteAnalytics[] }>(
        `/website/analytics?period=${period}`
      );
      return response;
    },
  });
}

export function useAnalyticsDashboard(period: string = '30d') {
  return useQuery({
    queryKey: [...websiteKeys.analyticsDashboard(), period],
    queryFn: async () => {
      const response = await api.get<AnalyticsDashboard>(
        `/website/analytics/dashboard?period=${period}`
      );
      return response;
    },
  });
}

export function useTrackPageView() {
  return useMutation({
    mutationFn: async (data: {
      page_path: string;
      page_title?: string;
      referrer?: string;
      user_agent?: string;
    }) => {
      return api.post('/website/analytics/track', data);
    },
  });
}

// ============================================================================
// HOOKS - PUBLIC SITE CONFIG
// ============================================================================

export function usePublicSiteConfig() {
  return useQuery({
    queryKey: websiteKeys.publicConfig(),
    queryFn: async () => {
      const response = await api.get<PublicSiteConfig>('/website/public/config');
      return response;
    },
  });
}
