"""
AZALS - Compression HTTP ÉLITE
==============================
Compression gzip/deflate pour réduire bande passante.
Seuil minimal pour éviter surcharge sur petites réponses.
"""

import gzip
import zlib
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.datastructures import MutableHeaders
import logging

logger = logging.getLogger(__name__)


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware de compression HTTP.

    Supporte:
    - gzip (prioritaire, meilleure compatibilité)
    - deflate (fallback)

    Caractéristiques:
    - Seuil minimum 1KB pour éviter overhead sur petites réponses
    - Ignore les réponses déjà compressées
    - Ignore les types non compressibles (images, vidéos)
    - Niveau de compression configurable
    """

    # Types MIME à NE PAS compresser (déjà compressés ou binaires)
    SKIP_CONTENT_TYPES = {
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
        "image/svg+xml",
        "video/mp4",
        "video/webm",
        "audio/mpeg",
        "audio/ogg",
        "application/zip",
        "application/gzip",
        "application/x-gzip",
        "application/pdf",
    }

    # Types MIME à compresser
    COMPRESS_CONTENT_TYPES = {
        "text/html",
        "text/plain",
        "text/css",
        "text/javascript",
        "application/json",
        "application/javascript",
        "application/xml",
        "text/xml",
    }

    def __init__(
        self,
        app,
        minimum_size: int = 1024,  # 1KB minimum
        compress_level: int = 6,   # Niveau gzip (1-9)
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compress_level = compress_level

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Vérifier si le client supporte la compression
        accept_encoding = request.headers.get("Accept-Encoding", "")
        supports_gzip = "gzip" in accept_encoding
        supports_deflate = "deflate" in accept_encoding

        if not supports_gzip and not supports_deflate:
            return await call_next(request)

        # Exécuter la requête
        response = await call_next(request)

        # Ne pas compresser les réponses streaming
        if isinstance(response, StreamingResponse):
            return response

        # Vérifier si déjà compressé
        if response.headers.get("Content-Encoding"):
            return response

        # Vérifier le type de contenu
        content_type = response.headers.get("Content-Type", "")
        base_content_type = content_type.split(";")[0].strip()

        if base_content_type in self.SKIP_CONTENT_TYPES:
            return response

        # Vérifier si c'est un type compressible
        should_compress = (
            base_content_type in self.COMPRESS_CONTENT_TYPES or
            base_content_type.startswith("text/") or
            base_content_type.endswith("+json") or
            base_content_type.endswith("+xml")
        )

        if not should_compress:
            return response

        # Récupérer le body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Vérifier la taille minimale
        if len(body) < self.minimum_size:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

        # Compresser
        if supports_gzip:
            compressed_body = gzip.compress(body, compresslevel=self.compress_level)
            encoding = "gzip"
        else:
            compressed_body = zlib.compress(body, level=self.compress_level)
            encoding = "deflate"

        # Ne compresser que si ça vaut le coup (réduction > 10%)
        if len(compressed_body) >= len(body) * 0.9:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

        # Construire la réponse compressée
        headers = MutableHeaders(raw=list(response.headers.raw))
        headers["Content-Encoding"] = encoding
        headers["Content-Length"] = str(len(compressed_body))
        # Indiquer que la réponse varie selon Accept-Encoding
        vary = headers.get("Vary", "")
        if "Accept-Encoding" not in vary:
            headers["Vary"] = f"{vary}, Accept-Encoding" if vary else "Accept-Encoding"

        return Response(
            content=compressed_body,
            status_code=response.status_code,
            headers=dict(headers),
            media_type=response.media_type
        )


def get_compression_stats(original_size: int, compressed_size: int) -> dict:
    """Calcule les statistiques de compression."""
    ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "ratio": round(ratio, 2),
        "savings": original_size - compressed_size
    }
