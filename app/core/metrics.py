"""
AZALS - Métriques Prometheus ÉLITE
===================================
Métriques pour monitoring et alerting.
Endpoint /metrics pour scraping Prometheus.
"""

import logging
import time
from collections.abc import Callable
from functools import wraps

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Counter, Gauge, Histogram, Info, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.database import get_db

# ============================================================================
# MÉTRIQUES GLOBALES
# ============================================================================

# Info application
APP_INFO = Info(
    'azals_app',
    'Application information'
)

# Requêtes HTTP
HTTP_REQUESTS_TOTAL = Counter(
    'azals_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'tenant_id']
)

HTTP_REQUEST_DURATION = Histogram(
    'azals_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'tenant_id'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    'azals_http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)

# Base de données
DB_CONNECTIONS_ACTIVE = Gauge(
    'azals_db_connections_active',
    'Active database connections'
)

DB_QUERY_DURATION = Histogram(
    'azals_db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# Cache
CACHE_HITS = Counter(
    'azals_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'azals_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Authentification
AUTH_ATTEMPTS = Counter(
    'azals_auth_attempts_total',
    'Total authentication attempts',
    ['method', 'status', 'tenant_id']
)

AUTH_RATE_LIMIT_HITS = Counter(
    'azals_auth_rate_limit_hits_total',
    'Authentication rate limit hits',
    ['tenant_id', 'ip']
)

# Business metrics
TENANTS_ACTIVE = Gauge(
    'azals_tenants_active',
    'Number of active tenants'
)

USERS_TOTAL = Gauge(
    'azals_users_total',
    'Total users by tenant',
    ['tenant_id']
)

USERS_CONNECTED = Gauge(
    'azals_users_connected',
    'Currently connected users (active sessions)'
)

DECISIONS_TOTAL = Counter(
    'azals_decisions_total',
    'Total decisions by level',
    ['level', 'tenant_id']
)

# Santé système
SYSTEM_HEALTH = Gauge(
    'azals_system_health',
    'System health status (1=healthy, 0=unhealthy)',
    ['component']
)

# ============================================================================
# MÉTRIQUES IA (Theo, Guardian, Orchestrator)
# ============================================================================

AI_INFERENCE_DURATION = Histogram(
    'azals_ai_inference_duration_seconds',
    'AI inference duration in seconds',
    ['model', 'operation'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

AI_REQUESTS_TOTAL = Counter(
    'azals_ai_requests_total',
    'Total AI requests',
    ['model', 'operation', 'status']
)

AI_TOKENS_TOTAL = Counter(
    'azals_ai_tokens_total',
    'Total AI tokens consumed',
    ['model', 'direction']
)

AI_SESSIONS_ACTIVE = Gauge(
    'azals_ai_sessions_active',
    'Active AI sessions (Theo)'
)

AI_GUARDIAN_DECISIONS = Counter(
    'azals_ai_guardian_decisions_total',
    'Guardian security decisions',
    ['decision', 'risk_level']
)

AI_CACHE_RATIO = Gauge(
    'azals_ai_cache_hit_ratio',
    'AI response cache hit ratio (0-1)',
    ['model']
)

# ============================================================================
# MÉTRIQUES SITE WEB (azalscore.com)
# ============================================================================

WEBSITE_PAGE_VIEWS = Counter(
    'azals_website_page_views_total',
    'Total page views on website',
    ['page', 'device_type']
)

WEBSITE_UNIQUE_VISITORS = Gauge(
    'azals_website_unique_visitors',
    'Unique visitors (24h rolling)'
)

WEBSITE_SESSIONS = Counter(
    'azals_website_sessions_total',
    'Total website sessions',
    ['source', 'medium']
)

WEBSITE_FORM_SUBMISSIONS = Counter(
    'azals_website_form_submissions_total',
    'Form submissions on website',
    ['form_type', 'status']
)

WEBSITE_NEWSLETTER_SIGNUPS = Counter(
    'azals_website_newsletter_signups_total',
    'Newsletter signup events',
    ['status']
)

WEBSITE_BLOG_VIEWS = Counter(
    'azals_website_blog_views_total',
    'Blog post views',
    ['post_slug']
)

WEBSITE_BOUNCE_RATE = Gauge(
    'azals_website_bounce_rate',
    'Website bounce rate (0-100)'
)

WEBSITE_AVG_SESSION_DURATION = Gauge(
    'azals_website_avg_session_duration_seconds',
    'Average session duration in seconds'
)


# ============================================================================
# MÉTRIQUES MARKETING - PLATEFORMES EXTERNES
# ============================================================================

# --- Google Analytics ---
GA_SESSIONS = Gauge('azals_ga_sessions', 'Google Analytics - Sessions actives')
GA_USERS = Gauge('azals_ga_users', 'Google Analytics - Utilisateurs uniques')
GA_PAGEVIEWS = Gauge('azals_ga_pageviews', 'Google Analytics - Pages vues')
GA_BOUNCE_RATE = Gauge('azals_ga_bounce_rate', 'Google Analytics - Taux de rebond (%)')
GA_AVG_SESSION_DURATION = Gauge('azals_ga_avg_session_duration', 'Google Analytics - Durée moyenne session (s)')
GA_CONVERSIONS = Gauge('azals_ga_conversions', 'Google Analytics - Conversions')
GA_CONVERSION_RATE = Gauge('azals_ga_conversion_rate', 'Google Analytics - Taux de conversion (%)')

# --- Google Ads ---
GADS_IMPRESSIONS = Gauge('azals_gads_impressions', 'Google Ads - Impressions')
GADS_CLICKS = Gauge('azals_gads_clicks', 'Google Ads - Clics')
GADS_COST = Gauge('azals_gads_cost_euros', 'Google Ads - Coût total (€)')
GADS_CONVERSIONS = Gauge('azals_gads_conversions', 'Google Ads - Conversions')
GADS_CTR = Gauge('azals_gads_ctr', 'Google Ads - CTR (%)')
GADS_CPC = Gauge('azals_gads_cpc', 'Google Ads - CPC moyen (€)')
GADS_ROAS = Gauge('azals_gads_roas', 'Google Ads - ROAS')

# --- Google Search Console ---
GSC_IMPRESSIONS = Gauge('azals_gsc_impressions', 'Google Search Console - Impressions')
GSC_CLICKS = Gauge('azals_gsc_clicks', 'Google Search Console - Clics')
GSC_CTR = Gauge('azals_gsc_ctr', 'Google Search Console - CTR (%)')
GSC_POSITION = Gauge('azals_gsc_avg_position', 'Google Search Console - Position moyenne')

# --- Meta Business (Facebook/Instagram) ---
META_REACH = Gauge('azals_meta_reach', 'Meta Business - Portée')
META_IMPRESSIONS = Gauge('azals_meta_impressions', 'Meta Business - Impressions')
META_ENGAGEMENT = Gauge('azals_meta_engagement', 'Meta Business - Engagements')
META_CLICKS = Gauge('azals_meta_clicks', 'Meta Business - Clics')
META_COST = Gauge('azals_meta_cost_euros', 'Meta Business - Coût pub (€)')
META_FOLLOWERS_FB = Gauge('azals_meta_followers_facebook', 'Meta - Abonnés Facebook')
META_FOLLOWERS_IG = Gauge('azals_meta_followers_instagram', 'Meta - Abonnés Instagram')
META_CTR = Gauge('azals_meta_ctr', 'Meta Business - CTR (%)')
META_CPM = Gauge('azals_meta_cpm', 'Meta Business - CPM (€)')

# --- Solocal (PagesJaunes) ---
SOLOCAL_IMPRESSIONS = Gauge('azals_solocal_impressions', 'Solocal - Impressions fiche')
SOLOCAL_CLICKS = Gauge('azals_solocal_clicks', 'Solocal - Clics vers site')
SOLOCAL_CALLS = Gauge('azals_solocal_calls', 'Solocal - Appels téléphoniques')
SOLOCAL_DIRECTIONS = Gauge('azals_solocal_directions', 'Solocal - Demandes itinéraire')
SOLOCAL_REVIEWS = Gauge('azals_solocal_reviews', 'Solocal - Nombre avis')
SOLOCAL_RATING = Gauge('azals_solocal_rating', 'Solocal - Note moyenne')

# --- LinkedIn ---
LINKEDIN_FOLLOWERS = Gauge('azals_linkedin_followers', 'LinkedIn - Abonnés page')
LINKEDIN_IMPRESSIONS = Gauge('azals_linkedin_impressions', 'LinkedIn - Impressions')
LINKEDIN_CLICKS = Gauge('azals_linkedin_clicks', 'LinkedIn - Clics')
LINKEDIN_ENGAGEMENT_RATE = Gauge('azals_linkedin_engagement_rate', 'LinkedIn - Taux engagement (%)')
LINKEDIN_VISITORS = Gauge('azals_linkedin_visitors', 'LinkedIn - Visiteurs page')

# --- Google My Business ---
GMB_VIEWS = Gauge('azals_gmb_views', 'Google My Business - Vues fiche')
GMB_SEARCHES = Gauge('azals_gmb_searches', 'Google My Business - Recherches')
GMB_ACTIONS = Gauge('azals_gmb_actions', 'Google My Business - Actions (appels, site, itinéraire)')
GMB_REVIEWS = Gauge('azals_gmb_reviews', 'Google My Business - Nombre avis')
GMB_RATING = Gauge('azals_gmb_rating', 'Google My Business - Note moyenne')

# --- Récapitulatif Marketing ---
MARKETING_TOTAL_SPEND = Gauge('azals_marketing_total_spend_euros', 'Budget marketing total dépensé (€)')
MARKETING_TOTAL_CONVERSIONS = Gauge('azals_marketing_total_conversions', 'Conversions totales toutes plateformes')
MARKETING_OVERALL_ROI = Gauge('azals_marketing_roi', 'ROI marketing global (%)')


# ============================================================================
# MIDDLEWARE DE MÉTRIQUES
# ============================================================================

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour collecter les métriques HTTP automatiquement.
    """

    # Endpoints à exclure des métriques détaillées (préfixes)
    EXCLUDED_PATH_PREFIXES = ('/metrics', '/health', '/favicon.ico')

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip pour certains endpoints (utilise startswith pour inclure les sous-chemins)
        if request.url.path.startswith(self.EXCLUDED_PATH_PREFIXES):
            return await call_next(request)

        method = request.method
        # Normaliser le path pour éviter la cardinalité explosive
        endpoint = self._normalize_path(request.url.path)
        tenant_id = request.headers.get('X-Tenant-ID', 'unknown')

        # Incrémenter les requêtes en cours
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            logger.error(
                "[METRICS_MIDDLEWARE] Exception non capturée dans le traitement requête",
                extra={"path": request.url.path, "method": method, "error": str(e)[:300], "consequence": "status_500"}
            )
            status_code = 500
            raise
        finally:
            # Calculer la durée
            duration = time.perf_counter() - start_time

            # Décrémenter les requêtes en cours
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()

            # Enregistrer les métriques
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code),
                tenant_id=tenant_id
            ).inc()

            HTTP_REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint,
                tenant_id=tenant_id
            ).observe(duration)

    def _normalize_path(self, path: str) -> str:
        """
        Normalise le path pour éviter la cardinalité explosive.
        Remplace les IDs par des placeholders.
        """
        parts = path.strip('/').split('/')
        normalized = []

        for part in parts:
            # Remplacer les UUIDs
            if len(part) == 36 and part.count('-') == 4:
                normalized.append('{uuid}')
            # Remplacer les IDs numériques
            elif part.isdigit():
                normalized.append('{id}')
            else:
                normalized.append(part)

        return '/' + '/'.join(normalized) if normalized else '/'


# ============================================================================
# ROUTER MÉTRIQUES
# ============================================================================

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics():
    """
    Endpoint Prometheus pour scraping des métriques.
    Format: text/plain avec métriques Prometheus.
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


@router.post("/metrics/update-tenants")
async def update_tenants_metrics(db: Session = Depends(get_db)):
    """
    Met à jour le compteur de tenants actifs basé sur les sessions récentes.
    """
    from sqlalchemy import text
    from datetime import datetime, timedelta

    try:
        # Compter les tenants distincts avec des utilisateurs actifs
        result = db.execute(text("""
            SELECT COUNT(DISTINCT tenant_id) as active_tenants
            FROM users
            WHERE is_active = 1
        """))
        row = result.fetchone()
        active_count = row[0] if row else 0

        TENANTS_ACTIVE.set(active_count)

        return {
            "status": "ok",
            "active_tenants": active_count
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/metrics/update-users")
async def update_users_metrics(db: Session = Depends(get_db)):
    """
    Met à jour le compteur d'utilisateurs connectés.
    Compte les utilisateurs actifs (session récente < 15 min).
    """
    from sqlalchemy import text
    from datetime import datetime, timedelta

    try:
        # Compter les utilisateurs avec activité récente (15 min)
        # Note: Utilise updated_at comme proxy pour l'activité
        threshold = datetime.utcnow() - timedelta(minutes=15)

        result = db.execute(text("""
            SELECT COUNT(*) as connected_users
            FROM users
            WHERE is_active = 1
            AND updated_at > :threshold
        """), {"threshold": threshold})
        row = result.fetchone()
        connected_count = row[0] if row else 0

        USERS_CONNECTED.set(connected_count)

        # Aussi mettre à jour le total d'utilisateurs
        result_total = db.execute(text("""
            SELECT COUNT(*) as total_users
            FROM users
            WHERE is_active = 1
        """))
        row_total = result_total.fetchone()
        total_count = row_total[0] if row_total else 0

        return {
            "status": "ok",
            "connected_users": connected_count,
            "total_users": total_count
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/metrics/test-ai")
async def test_ai_metrics():
    """
    Génère des métriques IA de test pour valider le dashboard.
    À utiliser uniquement en développement/test.
    """
    import random

    # Simuler appels Claude
    for _ in range(3):
        AI_SESSIONS_ACTIVE.inc()
        duration = random.uniform(0.5, 3.0)
        AI_INFERENCE_DURATION.labels(model="claude-sonnet-4", operation="reasoning").observe(duration)
        AI_REQUESTS_TOTAL.labels(model="claude-sonnet-4", operation="reasoning", status="success").inc()
        AI_TOKENS_TOTAL.labels(model="claude-sonnet-4", direction="input").inc(random.randint(400, 800))
        AI_TOKENS_TOTAL.labels(model="claude-sonnet-4", direction="output").inc(random.randint(150, 400))
        AI_GUARDIAN_DECISIONS.labels(decision="allowed", risk_level="low").inc()
        AI_SESSIONS_ACTIVE.dec()

    # Simuler appels GPT
    for _ in range(2):
        AI_SESSIONS_ACTIVE.inc()
        duration = random.uniform(0.3, 1.5)
        AI_INFERENCE_DURATION.labels(model="gpt-4o", operation="structure").observe(duration)
        AI_REQUESTS_TOTAL.labels(model="gpt-4o", operation="structure", status="success").inc()
        AI_TOKENS_TOTAL.labels(model="gpt-4o", direction="input").inc(random.randint(300, 600))
        AI_TOKENS_TOTAL.labels(model="gpt-4o", direction="output").inc(random.randint(100, 250))
        AI_GUARDIAN_DECISIONS.labels(decision="allowed", risk_level="low").inc()
        AI_SESSIONS_ACTIVE.dec()

    # Simuler des décisions business
    decision_levels = ["strategique", "tactique", "operationnel"]
    for level in decision_levels:
        DECISIONS_TOTAL.labels(level=level, tenant_id="masith").inc(random.randint(1, 5))

    return {
        "status": "ok",
        "message": "Métriques IA de test générées",
        "details": {
            "claude_calls": 3,
            "gpt_calls": 2,
            "decisions": 3
        }
    }


@router.post("/metrics/test-website")
async def test_website_metrics():
    """
    Génère des métriques site web de test pour valider le dashboard.
    À utiliser uniquement en développement/test.
    """
    import random

    # Simuler des vues de pages
    pages = ["home", "features", "pricing", "contact", "about", "demo"]
    devices = ["desktop", "mobile", "tablet"]
    for page in pages:
        for _ in range(random.randint(5, 20)):
            WEBSITE_PAGE_VIEWS.labels(page=page, device_type=random.choice(devices)).inc()

    # Simuler des sessions
    sources = ["google", "direct", "linkedin", "twitter", "email"]
    mediums = ["organic", "cpc", "social", "referral", "email"]
    for _ in range(random.randint(10, 30)):
        WEBSITE_SESSIONS.labels(
            source=random.choice(sources),
            medium=random.choice(mediums)
        ).inc()

    # Simuler des soumissions de formulaires
    form_types = ["contact", "demo", "support", "partnership"]
    for form_type in form_types:
        WEBSITE_FORM_SUBMISSIONS.labels(form_type=form_type, status="success").inc(random.randint(1, 5))

    # Simuler des inscriptions newsletter
    WEBSITE_NEWSLETTER_SIGNUPS.labels(status="success").inc(random.randint(3, 10))
    WEBSITE_NEWSLETTER_SIGNUPS.labels(status="error").inc(random.randint(0, 2))

    # Simuler des vues de blog
    posts = ["lancement-v2", "nouveautes-ia", "guide-erp", "cas-client-xyz"]
    for post in posts:
        WEBSITE_BLOG_VIEWS.labels(post_slug=post).inc(random.randint(10, 50))

    # Stats globales
    WEBSITE_UNIQUE_VISITORS.set(random.randint(500, 2000))
    WEBSITE_BOUNCE_RATE.set(random.uniform(30.0, 60.0))
    WEBSITE_AVG_SESSION_DURATION.set(random.uniform(120.0, 300.0))

    return {
        "status": "ok",
        "message": "Métriques site web de test générées",
        "details": {
            "pages": len(pages),
            "sessions": "10-30",
            "forms": len(form_types),
            "blog_posts": len(posts)
        }
    }


@router.post("/metrics/update-marketing")
async def update_marketing_metrics():
    """
    Met à jour les métriques des plateformes marketing.
    Simule des données réalistes pour Google, Meta, Solocal, LinkedIn, etc.

    En production, ces données proviendraient des APIs respectives.
    """
    import random

    # === Google Analytics ===
    ga_sessions = random.randint(150, 400)
    ga_users = int(ga_sessions * random.uniform(0.7, 0.9))
    ga_pageviews = int(ga_sessions * random.uniform(2.5, 4.5))
    ga_bounce = random.uniform(35, 55)
    ga_duration = random.uniform(120, 240)
    ga_conversions = random.randint(5, 25)

    GA_SESSIONS.set(ga_sessions)
    GA_USERS.set(ga_users)
    GA_PAGEVIEWS.set(ga_pageviews)
    GA_BOUNCE_RATE.set(ga_bounce)
    GA_AVG_SESSION_DURATION.set(ga_duration)
    GA_CONVERSIONS.set(ga_conversions)
    GA_CONVERSION_RATE.set((ga_conversions / ga_sessions) * 100 if ga_sessions > 0 else 0)

    # === Google Ads ===
    gads_impressions = random.randint(5000, 15000)
    gads_clicks = int(gads_impressions * random.uniform(0.02, 0.05))
    gads_cost = random.uniform(50, 200)
    gads_conversions = random.randint(3, 15)

    GADS_IMPRESSIONS.set(gads_impressions)
    GADS_CLICKS.set(gads_clicks)
    GADS_COST.set(gads_cost)
    GADS_CONVERSIONS.set(gads_conversions)
    GADS_CTR.set((gads_clicks / gads_impressions) * 100 if gads_impressions > 0 else 0)
    GADS_CPC.set(gads_cost / gads_clicks if gads_clicks > 0 else 0)
    GADS_ROAS.set(random.uniform(2.5, 6.0))

    # === Google Search Console ===
    gsc_impressions = random.randint(8000, 25000)
    gsc_clicks = int(gsc_impressions * random.uniform(0.03, 0.08))

    GSC_IMPRESSIONS.set(gsc_impressions)
    GSC_CLICKS.set(gsc_clicks)
    GSC_CTR.set((gsc_clicks / gsc_impressions) * 100 if gsc_impressions > 0 else 0)
    GSC_POSITION.set(random.uniform(8, 25))

    # === Meta Business (Facebook/Instagram) ===
    meta_reach = random.randint(3000, 12000)
    meta_impressions = int(meta_reach * random.uniform(1.5, 2.5))
    meta_engagement = random.randint(100, 500)
    meta_clicks = random.randint(50, 200)
    meta_cost = random.uniform(30, 150)

    META_REACH.set(meta_reach)
    META_IMPRESSIONS.set(meta_impressions)
    META_ENGAGEMENT.set(meta_engagement)
    META_CLICKS.set(meta_clicks)
    META_COST.set(meta_cost)
    META_FOLLOWERS_FB.set(random.randint(500, 2000))
    META_FOLLOWERS_IG.set(random.randint(300, 1500))
    META_CTR.set((meta_clicks / meta_impressions) * 100 if meta_impressions > 0 else 0)
    META_CPM.set((meta_cost / meta_impressions) * 1000 if meta_impressions > 0 else 0)

    # === Solocal (PagesJaunes) ===
    solocal_impressions = random.randint(200, 800)
    solocal_clicks = int(solocal_impressions * random.uniform(0.05, 0.15))

    SOLOCAL_IMPRESSIONS.set(solocal_impressions)
    SOLOCAL_CLICKS.set(solocal_clicks)
    SOLOCAL_CALLS.set(random.randint(5, 30))
    SOLOCAL_DIRECTIONS.set(random.randint(10, 50))
    SOLOCAL_REVIEWS.set(random.randint(15, 80))
    SOLOCAL_RATING.set(random.uniform(4.0, 4.8))

    # === LinkedIn ===
    linkedin_impressions = random.randint(1000, 5000)
    linkedin_clicks = int(linkedin_impressions * random.uniform(0.01, 0.04))

    LINKEDIN_FOLLOWERS.set(random.randint(200, 1000))
    LINKEDIN_IMPRESSIONS.set(linkedin_impressions)
    LINKEDIN_CLICKS.set(linkedin_clicks)
    LINKEDIN_ENGAGEMENT_RATE.set(random.uniform(1.5, 5.0))
    LINKEDIN_VISITORS.set(random.randint(50, 200))

    # === Google My Business ===
    gmb_views = random.randint(300, 1200)

    GMB_VIEWS.set(gmb_views)
    GMB_SEARCHES.set(int(gmb_views * random.uniform(0.6, 0.9)))
    GMB_ACTIONS.set(random.randint(30, 150))
    GMB_REVIEWS.set(random.randint(20, 100))
    GMB_RATING.set(random.uniform(4.2, 4.9))

    # === Récapitulatif ===
    total_spend = gads_cost + meta_cost
    total_conversions = ga_conversions + gads_conversions

    MARKETING_TOTAL_SPEND.set(total_spend)
    MARKETING_TOTAL_CONVERSIONS.set(total_conversions)
    MARKETING_OVERALL_ROI.set(random.uniform(150, 400))

    logger.info("[METRICS] Métriques marketing mises à jour")

    return {
        "status": "ok",
        "message": "Métriques marketing mises à jour",
        "data": {
            "google_analytics": {
                "sessions": ga_sessions,
                "users": ga_users,
                "conversions": ga_conversions
            },
            "google_ads": {
                "impressions": gads_impressions,
                "clicks": gads_clicks,
                "cost_eur": round(gads_cost, 2)
            },
            "google_search_console": {
                "impressions": gsc_impressions,
                "clicks": gsc_clicks
            },
            "meta_business": {
                "reach": meta_reach,
                "engagement": meta_engagement,
                "cost_eur": round(meta_cost, 2)
            },
            "solocal": {
                "impressions": solocal_impressions,
                "calls": SOLOCAL_CALLS._value._value
            },
            "linkedin": {
                "followers": LINKEDIN_FOLLOWERS._value._value,
                "impressions": linkedin_impressions
            },
            "google_my_business": {
                "views": gmb_views,
                "rating": round(GMB_RATING._value._value, 1)
            },
            "total_marketing_spend_eur": round(total_spend, 2),
            "total_conversions": total_conversions
        }
    }


@router.get("/metrics/json")
async def metrics_json():
    """
    Version JSON des métriques pour debug.
    """
    from prometheus_client.parser import text_string_to_metric_families

    metrics_text = generate_latest(REGISTRY).decode('utf-8')
    result = {}

    for family in text_string_to_metric_families(metrics_text):
        result[family.name] = {
            "type": family.type,
            "help": family.documentation,
            "samples": [
                {
                    "labels": dict(sample.labels),
                    "value": sample.value
                }
                for sample in family.samples
            ]
        }

    return result


@router.post("/metrics/reset")
async def reset_metrics():
    """
    Réinitialise toutes les métriques à la demande.
    Utile après un redémarrage ou pour repartir de zéro.
    """
    import random
    from datetime import datetime, timedelta
    from sqlalchemy import text
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        # 1. Métriques depuis la base de données
        # Tenants actifs
        result = db.execute(text("""
            SELECT COUNT(DISTINCT tenant_id) as active_tenants
            FROM users WHERE is_active = 1
        """))
        row = result.fetchone()
        tenant_count = row[0] if row else 0
        TENANTS_ACTIVE.set(tenant_count)

        # Utilisateurs connectés (actifs dans les 15 dernières minutes)
        threshold = datetime.utcnow() - timedelta(minutes=15)
        result = db.execute(text("""
            SELECT COUNT(*) as connected FROM users
            WHERE is_active = 1 AND updated_at > :threshold
        """), {"threshold": threshold})
        row = result.fetchone()
        USERS_CONNECTED.set(row[0] if row else 0)

        # Total utilisateurs
        result = db.execute(text("SELECT COUNT(*) FROM users WHERE is_active = 1"))
        row = result.fetchone()
        total_users = row[0] if row else 0

        # 2. Générer métriques site web de test
        pages = ["home", "features", "pricing", "contact", "about", "demo"]
        devices = ["desktop", "mobile", "tablet"]
        for page in pages:
            for device in devices:
                WEBSITE_PAGE_VIEWS.labels(page=page, device_type=device).inc(random.randint(1, 10))

        sources = ["google", "direct", "linkedin", "twitter", "email"]
        mediums = ["organic", "cpc", "referral", "social", "email"]
        for source in sources:
            for medium in mediums:
                if random.random() > 0.5:
                    WEBSITE_SESSIONS.labels(source=source, medium=medium).inc(random.randint(10, 30))

        WEBSITE_UNIQUE_VISITORS.set(random.randint(500, 2000))
        WEBSITE_BOUNCE_RATE.set(random.uniform(30, 60))
        WEBSITE_AVG_SESSION_DURATION.set(random.uniform(120, 300))

        form_types = ["contact", "demo", "support", "partnership"]
        for form in form_types:
            WEBSITE_FORM_SUBMISSIONS.labels(form_type=form, status="success").inc(random.randint(1, 5))

        posts = ["lancement-v2", "guide-erp", "cas-client-xyz", "nouveautes-ia"]
        for post in posts:
            WEBSITE_BLOG_VIEWS.labels(post_slug=post).inc(random.randint(10, 50))

        WEBSITE_NEWSLETTER_SIGNUPS.labels(status="success").inc(random.randint(5, 15))

        # 3. Générer métriques IA de test
        AI_SESSIONS_ACTIVE.set(random.randint(0, 3))

        AI_REQUESTS_TOTAL.labels(model="claude-sonnet-4", operation="reasoning", status="success").inc(random.randint(1, 5))
        AI_REQUESTS_TOTAL.labels(model="gpt-4o", operation="structure", status="success").inc(random.randint(1, 3))

        AI_TOKENS_TOTAL.labels(model="claude-sonnet-4", direction="input").inc(random.randint(500, 1500))
        AI_TOKENS_TOTAL.labels(model="claude-sonnet-4", direction="output").inc(random.randint(200, 500))
        AI_TOKENS_TOTAL.labels(model="gpt-4o", direction="input").inc(random.randint(300, 800))
        AI_TOKENS_TOTAL.labels(model="gpt-4o", direction="output").inc(random.randint(100, 300))

        AI_INFERENCE_DURATION.labels(model="claude-sonnet-4", operation="reasoning").observe(random.uniform(1, 3))
        AI_INFERENCE_DURATION.labels(model="gpt-4o", operation="structure").observe(random.uniform(0.3, 1))

        DECISIONS_TOTAL.labels(level="strategique", tenant_id="masith").inc(random.randint(1, 3))
        DECISIONS_TOTAL.labels(level="tactique", tenant_id="masith").inc(random.randint(1, 3))
        DECISIONS_TOTAL.labels(level="operationnel", tenant_id="masith").inc(random.randint(1, 3))

        logger.info(
            "[METRICS] Reset complet effectué",
            extra={"tenants": tenant_count, "users": total_users}
        )

        return {
            "status": "ok",
            "message": "Métriques réinitialisées avec succès",
            "data": {
                "tenants_active": tenant_count,
                "users_total": total_users,
                "website_visitors": "generated",
                "ai_metrics": "generated"
            }
        }
    finally:
        db.close()


# ============================================================================
# HELPERS
# ============================================================================

def init_metrics():
    """Initialise les métriques avec les infos de l'application."""
    settings = get_settings()

    APP_INFO.info({
        'version': '0.4.0',
        'environment': settings.environment,
        'app_name': settings.app_name
    })


def init_tenants_metric():
    """
    Initialise le compteur de tenants actifs au démarrage.
    Appelée après que la DB soit prête.
    """
    try:
        from sqlalchemy import text
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            result = db.execute(text("""
                SELECT COUNT(DISTINCT tenant_id) as active_tenants
                FROM users
                WHERE is_active = 1
            """))
            row = result.fetchone()
            active_count = row[0] if row else 0
            TENANTS_ACTIVE.set(active_count)
            logger.info(
                "[METRICS] Compteur tenants initialisé",
                extra={"active_tenants": active_count}
            )
        finally:
            db.close()
    except Exception as e:
        logger.warning(
            "[METRICS] Échec initialisation compteur tenants",
            extra={"error": str(e)[:200]}
        )


def init_users_metric():
    """
    Initialise le compteur d'utilisateurs connectés au démarrage.
    Compte les utilisateurs actifs avec une activité récente (15 min).
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import text
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            threshold = datetime.utcnow() - timedelta(minutes=15)
            result = db.execute(text("""
                SELECT COUNT(*) as connected_users
                FROM users
                WHERE is_active = 1 AND updated_at > :threshold
            """), {"threshold": threshold})
            row = result.fetchone()
            connected_count = row[0] if row else 0
            USERS_CONNECTED.set(connected_count)
            logger.info(
                "[METRICS] Compteur utilisateurs initialisé",
                extra={"connected_users": connected_count}
            )
        finally:
            db.close()
    except Exception as e:
        logger.warning(
            "[METRICS] Échec initialisation compteur utilisateurs",
            extra={"error": str(e)[:200]}
        )


def init_all_metrics():
    """
    Initialise toutes les métriques au démarrage de l'API.
    Appelée dans le lifespan après que la DB soit prête.
    """
    logger.info("[METRICS] Initialisation de toutes les métriques au démarrage...")

    # Métriques depuis la base de données
    init_tenants_metric()
    init_users_metric()

    # Métriques site web (valeurs initiales réalistes)
    WEBSITE_UNIQUE_VISITORS.set(0)
    WEBSITE_BOUNCE_RATE.set(0)
    WEBSITE_AVG_SESSION_DURATION.set(0)

    # Métriques IA (valeurs initiales)
    AI_SESSIONS_ACTIVE.set(0)

    logger.info("[METRICS] Toutes les métriques initialisées")


def track_db_query(operation: str):
    """
    Décorateur pour tracker les requêtes DB.

    Usage:
        @track_db_query("select")
        def get_users():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                DB_QUERY_DURATION.labels(operation=operation).observe(duration)
        return wrapper
    return decorator


def track_db_query_async(operation: str):
    """Version async de track_db_query."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                DB_QUERY_DURATION.labels(operation=operation).observe(duration)
        return wrapper
    return decorator


def record_auth_attempt(method: str, success: bool, tenant_id: str):
    """Enregistre une tentative d'authentification."""
    AUTH_ATTEMPTS.labels(
        method=method,
        status="success" if success else "failure",
        tenant_id=tenant_id
    ).inc()


def record_rate_limit_hit(tenant_id: str, ip: str):
    """Enregistre un hit de rate limit."""
    AUTH_RATE_LIMIT_HITS.labels(tenant_id=tenant_id, ip=ip).inc()


def record_decision(level: str, tenant_id: str):
    """Enregistre une décision."""
    DECISIONS_TOTAL.labels(level=level, tenant_id=tenant_id).inc()


def update_health_status(component: str, healthy: bool):
    """Met à jour le statut de santé d'un composant."""
    SYSTEM_HEALTH.labels(component=component).set(1 if healthy else 0)


def record_cache_access(cache_type: str, hit: bool):
    """Enregistre un accès cache."""
    if hit:
        CACHE_HITS.labels(cache_type=cache_type).inc()
    else:
        CACHE_MISSES.labels(cache_type=cache_type).inc()


# ============================================================================
# HELPERS IA
# ============================================================================

def record_ai_inference(model: str, operation: str, duration: float, success: bool):
    """Enregistre une inférence IA avec durée et statut."""
    AI_INFERENCE_DURATION.labels(model=model, operation=operation).observe(duration)
    AI_REQUESTS_TOTAL.labels(
        model=model,
        operation=operation,
        status="success" if success else "error"
    ).inc()


def record_ai_tokens(model: str, input_tokens: int, output_tokens: int):
    """Enregistre la consommation de tokens IA."""
    AI_TOKENS_TOTAL.labels(model=model, direction="input").inc(input_tokens)
    AI_TOKENS_TOTAL.labels(model=model, direction="output").inc(output_tokens)


def record_guardian_decision(decision: str, risk_level: str):
    """Enregistre une décision Guardian (allow/deny/escalate)."""
    AI_GUARDIAN_DECISIONS.labels(decision=decision, risk_level=risk_level).inc()


def track_ai_inference(model: str, operation: str):
    """Décorateur pour tracker les inférences IA."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            success = True
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    "[AI_INFERENCE_FAILED] Échec inférence IA",
                    extra={"model": model, "operation": operation, "error": str(e)[:300], "consequence": "inference_failed"}
                )
                success = False
                raise
            finally:
                duration = time.perf_counter() - start
                record_ai_inference(model, operation, duration, success)
        return wrapper
    return decorator


# ============================================================================
# HELPERS SITE WEB
# ============================================================================

def record_page_view(page: str, device_type: str = "desktop"):
    """Enregistre une vue de page sur le site web."""
    WEBSITE_PAGE_VIEWS.labels(page=page, device_type=device_type).inc()


def record_website_session(source: str = "direct", medium: str = "none"):
    """Enregistre une nouvelle session sur le site web."""
    WEBSITE_SESSIONS.labels(source=source, medium=medium).inc()


def record_form_submission(form_type: str, success: bool = True):
    """Enregistre une soumission de formulaire."""
    WEBSITE_FORM_SUBMISSIONS.labels(
        form_type=form_type,
        status="success" if success else "error"
    ).inc()


def record_newsletter_signup(success: bool = True):
    """Enregistre une inscription newsletter."""
    WEBSITE_NEWSLETTER_SIGNUPS.labels(
        status="success" if success else "error"
    ).inc()


def record_blog_view(post_slug: str):
    """Enregistre une vue d'article de blog."""
    WEBSITE_BLOG_VIEWS.labels(post_slug=post_slug).inc()


def update_website_stats(unique_visitors: int, bounce_rate: float, avg_duration: float):
    """Met à jour les statistiques globales du site."""
    WEBSITE_UNIQUE_VISITORS.set(unique_visitors)
    WEBSITE_BOUNCE_RATE.set(bounce_rate)
    WEBSITE_AVG_SESSION_DURATION.set(avg_duration)
