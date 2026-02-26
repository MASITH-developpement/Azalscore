"""
AZALSCORE - Workflow Automation HTTP Handler
Handler pour les requêtes HTTP avec protection SSRF
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional
from urllib.parse import urlparse

from ..types import ActionConfig
from .base import ActionHandler

logger = logging.getLogger(__name__)


class HttpRequestHandler(ActionHandler):
    """Handler pour les requêtes HTTP avec protection SSRF"""

    # Liste des hôtes/réseaux interdits (SSRF protection)
    # nosec B104 - Ce sont des hôtes BLOQUÉS, pas des bindings
    BLOCKED_HOSTS = {
        "localhost", "127.0.0.1", "0.0.0.0", "::1",  # nosec B104
        "metadata.google.internal", "169.254.169.254",  # Cloud metadata
    }

    BLOCKED_NETWORKS = [
        "10.", "172.16.", "172.17.", "172.18.", "172.19.",
        "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
        "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
        "172.30.", "172.31.", "192.168.",  # Réseaux privés
    ]

    ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}

    def _is_safe_url(self, url: str) -> tuple[bool, str]:
        """Vérifie si l'URL est sûre (protection SSRF)."""
        try:
            parsed = urlparse(url)

            # Vérifier le schéma
            if parsed.scheme not in ("http", "https"):
                return False, f"Schéma non autorisé: {parsed.scheme}"

            # Vérifier l'hôte
            host = parsed.hostname or ""
            host_lower = host.lower()

            if host_lower in self.BLOCKED_HOSTS:
                return False, f"Hôte bloqué: {host}"

            # Vérifier les réseaux privés
            for network in self.BLOCKED_NETWORKS:
                if host.startswith(network):
                    return False, f"Réseau privé non autorisé: {host}"

            # Vérifier les adresses IPv6 locales
            if host.startswith("[") and ("::1" in host or "fe80:" in host.lower()):
                return False, f"Adresse IPv6 locale non autorisée: {host}"

            return True, ""
        except Exception as e:
            return False, f"URL invalide: {str(e)}"

    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        params = action.parameters
        method = params.get("method", "GET")
        url = self._resolve_value(params.get("url"), variables)
        headers = self._resolve_dict(params.get("headers", {}), variables)
        body = self._resolve_value(params.get("body"), variables)
        timeout = min(params.get("timeout", 30), 60)  # Max 60 secondes

        # Validation SSRF
        is_safe, error_msg = self._is_safe_url(url)
        if not is_safe:
            logger.warning(f"Requête HTTP bloquée (SSRF): {url} - {error_msg}")
            return None, f"URL non autorisée: {error_msg}"

        # Valider la méthode HTTP
        if method.upper() not in self.ALLOWED_METHODS:
            return None, f"Méthode HTTP non autorisée: {method}"

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=body if isinstance(body, dict) else None,
                    data=body if isinstance(body, str) else None,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=False  # Pas de redirections automatiques (sécurité)
                ) as response:
                    # Limiter la taille de la réponse (1 Mo max)
                    max_size = 1024 * 1024
                    response_body = await response.text()
                    if len(response_body) > max_size:
                        response_body = response_body[:max_size] + "... [tronqué]"

                    try:
                        response_json = json.loads(response_body)
                    except json.JSONDecodeError:
                        response_json = None

                    return {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "body": response_json or response_body
                    }, None if response.status < 400 else f"HTTP {response.status}"

        except ImportError:
            logger.warning("aiohttp non disponible, simulation de requête HTTP")
            return {"status_code": 200, "body": {}}, None
        except asyncio.TimeoutError:
            return None, "Timeout de la requête HTTP"
        except Exception as e:
            logger.exception(f"Erreur requête HTTP: {e}")
            return None, str(e)
