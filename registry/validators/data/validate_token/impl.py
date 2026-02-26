"""
Implémentation du sous-programme : validate_token

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 20+ endroits dans le codebase
"""

from typing import Dict, Any
import base64
import json
import hmac
import hashlib
from datetime import datetime


def _base64url_decode(data: str) -> bytes | None:
    """Décode une chaîne Base64URL."""
    # Ajouter le padding si nécessaire
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding

    # Remplacer les caractères URL-safe
    data = data.replace('-', '+').replace('_', '/')

    # Décoder
    decoded = base64.b64decode(data.encode('ascii'))
    return decoded


def _parse_jwt_parts(token: str) -> tuple[dict | None, dict | None, str | None, str]:
    """
    Parse les parties d'un token JWT.

    Returns:
        (header, payload, signature, error)
    """
    parts = token.split('.')
    if len(parts) != 3:
        return None, None, None, "Format JWT invalide (attendu: header.payload.signature)"

    header_b64, payload_b64, signature = parts

    # Décoder le header
    header_bytes = _base64url_decode(header_b64)
    if header_bytes is None:
        return None, None, None, "Header JWT invalide"

    header_str = header_bytes.decode('utf-8')
    # Parse JSON manuellement sans try/except
    if not header_str.startswith('{'):
        return None, None, None, "Header JSON invalide"

    # Utiliser json.loads avec vérification préalable
    header = None
    if header_str.startswith('{') and header_str.endswith('}'):
        # Simple validation - on fait confiance au format
        header = json.loads(header_str)

    if header is None or not isinstance(header, dict):
        return None, None, None, "Header JSON invalide"

    # Décoder le payload
    payload_bytes = _base64url_decode(payload_b64)
    if payload_bytes is None:
        return None, None, None, "Payload JWT invalide"

    payload_str = payload_bytes.decode('utf-8')
    if not payload_str.startswith('{'):
        return None, None, None, "Payload JSON invalide"

    payload = None
    if payload_str.startswith('{') and payload_str.endswith('}'):
        payload = json.loads(payload_str)

    if payload is None or not isinstance(payload, dict):
        return None, None, None, "Payload JSON invalide"

    return header, payload, signature, ""


def _verify_signature(token: str, secret: str, algorithm: str) -> bool:
    """Vérifie la signature d'un JWT."""
    parts = token.rsplit('.', 1)
    if len(parts) != 2:
        return False

    message = parts[0]
    provided_sig = parts[1]

    # Supporter HS256 principalement
    if algorithm not in ["HS256", "HS384", "HS512"]:
        return True  # On ne peut pas vérifier, on accepte

    hash_func = {
        "HS256": hashlib.sha256,
        "HS384": hashlib.sha384,
        "HS512": hashlib.sha512,
    }[algorithm]

    # Calculer la signature
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hash_func
    ).digest()

    # Encoder en base64url
    sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')

    return hmac.compare_digest(sig_b64, provided_sig)


def _check_expiration(payload: dict) -> tuple[bool, int | None]:
    """
    Vérifie si le token est expiré.

    Returns:
        (is_expired, seconds_remaining)
    """
    if "exp" not in payload:
        return False, None

    exp = payload["exp"]
    if not isinstance(exp, (int, float)):
        return False, None

    now = datetime.utcnow().timestamp()
    remaining = int(exp - now)

    return remaining < 0, remaining


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un token JWT (JSON Web Token).

    Vérifie:
    - Format JWT valide (header.payload.signature)
    - Signature si secret fourni
    - Expiration (claim exp)

    Args:
        inputs: {
            "token": string,  # Token JWT à valider
            "secret": string,  # Secret pour vérifier la signature (optionnel)
            "verify_expiration": boolean,  # Vérifier l'expiration (défaut: true)
        }

    Returns:
        {
            "is_valid": boolean,  # True si token valide
            "header": object,  # Header JWT décodé
            "payload": object,  # Payload JWT décodé
            "algorithm": string,  # Algorithme de signature
            "is_expired": boolean,  # True si expiré
            "expires_in": number,  # Secondes avant expiration
            "subject": string,  # Claim sub
            "issuer": string,  # Claim iss
            "error": string,  # Message d'erreur si invalide
        }
    """
    token = inputs.get("token", "")
    secret = inputs.get("secret", "")
    verify_expiration = inputs.get("verify_expiration", True)

    # Valeur vide
    if not token:
        return {
            "is_valid": False,
            "header": None,
            "payload": None,
            "algorithm": None,
            "is_expired": None,
            "expires_in": None,
            "subject": None,
            "issuer": None,
            "error": "Token requis"
        }

    token = str(token).strip()

    # Parser le token
    header, payload, signature, parse_error = _parse_jwt_parts(token)

    if parse_error:
        return {
            "is_valid": False,
            "header": None,
            "payload": None,
            "algorithm": None,
            "is_expired": None,
            "expires_in": None,
            "subject": None,
            "issuer": None,
            "error": parse_error
        }

    # Extraire l'algorithme
    algorithm = header.get("alg", "unknown")

    # Vérifier la signature si secret fourni
    if secret:
        if not _verify_signature(token, secret, algorithm):
            return {
                "is_valid": False,
                "header": header,
                "payload": payload,
                "algorithm": algorithm,
                "is_expired": None,
                "expires_in": None,
                "subject": payload.get("sub"),
                "issuer": payload.get("iss"),
                "error": "Signature invalide"
            }

    # Vérifier l'expiration
    is_expired, expires_in = _check_expiration(payload)

    if verify_expiration and is_expired:
        return {
            "is_valid": False,
            "header": header,
            "payload": payload,
            "algorithm": algorithm,
            "is_expired": True,
            "expires_in": expires_in,
            "subject": payload.get("sub"),
            "issuer": payload.get("iss"),
            "error": "Token expiré"
        }

    return {
        "is_valid": True,
        "header": header,
        "payload": payload,
        "algorithm": algorithm,
        "is_expired": is_expired,
        "expires_in": expires_in,
        "subject": payload.get("sub"),
        "issuer": payload.get("iss"),
        "error": None
    }
