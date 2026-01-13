# ==============================================================================
# AZALSCORE - Dockerfile Production Multi-Tenant
# ==============================================================================
# Image optimisée pour production avec:
# - Multi-stage build (image finale légère ~200MB)
# - User non-root (sécurité)
# - Health check intégré
# - Cache pip optimisé
# ==============================================================================

# =============================================================================
# STAGE 1: Builder - Installation des dépendances
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Installer les dépendances système pour compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# =============================================================================
# STAGE 2: Production - Image finale légère
# =============================================================================
FROM python:3.11-slim AS production

# Labels
LABEL maintainer="MASITH <contact@masith.fr>"
LABEL description="AZALSCORE - ERP Multi-Tenant Production"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

# Créer user non-root pour sécurité
RUN groupadd --gid 1000 azals && \
    useradd --uid 1000 --gid azals --shell /bin/bash --create-home azals

WORKDIR /app

# Installer dépendances runtime uniquement
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copier wheels depuis builder et installer
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Copier le code source
COPY --chown=azals:azals . .

# Changer vers user non-root
USER azals

# Port exposé
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Commande de démarrage (2 workers pour production)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 2 --limit-concurrency 100"]
