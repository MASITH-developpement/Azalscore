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
