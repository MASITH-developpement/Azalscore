"""
AZALS - Sécurité et Authentification
Gestion JWT et hashing de mots de passe

SÉCURITÉ:
- Tokens JWT avec JTI unique pour révocation côté serveur
- Blacklist distribuée via Redis en production
- Bcrypt pour hashing des mots de passe
"""

import uuid
from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

# Configuration JWT
settings = get_settings()
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# P1 SÉCURITÉ: Refresh token réduit à 2 jours (OWASP recommande 24-48h pour SaaS financier)
REFRESH_TOKEN_EXPIRE_DAYS = 2


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie qu'un mot de passe en clair correspond au hash.
    Utilise bcrypt avec salt automatique.
    """
    if not plain_password or not hashed_password:
        return False
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


class PasswordTooLongError(ValueError):
    """Erreur levée quand le mot de passe dépasse la limite bcrypt."""
    pass


def get_password_hash(password: str) -> str:
    """
    Hash un mot de passe avec bcrypt.
    Le salt est généré automatiquement.

    IMPORTANT: bcrypt a une limite de 72 bytes. Les mots de passe plus longs
    sont rejetés pour éviter une troncature silencieuse qui affaiblirait la sécurité.

    Raises:
        PasswordTooLongError: Si le mot de passe dépasse 72 bytes en UTF-8
    """
    if not password:
        raise ValueError("Password cannot be empty")
    password_bytes = password.encode('utf-8')

    # Bcrypt limite stricte de 72 bytes - validation explicite
    if len(password_bytes) > 72:
        raise PasswordTooLongError(
            "Le mot de passe ne peut pas dépasser 72 caractères. "
            "Veuillez utiliser un mot de passe plus court."
        )

    # P1 SÉCURITÉ: bcrypt rounds=14 (OWASP 2023 recommande minimum 14, default=12 trop faible)
    salt = bcrypt.gensalt(rounds=14)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Crée un JWT access token avec JTI unique pour révocation.

    Args:
        data: Données à encoder (sub, tenant_id, role)
        expires_delta: Durée de validité personnalisée

    Returns:
        JWT signé avec jti unique

    SÉCURITÉ:
    - Chaque token a un jti (JWT ID) unique
    - Permet la révocation côté serveur via blacklist
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Ajouter JTI unique pour permettre la révocation
    jti = str(uuid.uuid4())

    to_encode.update({
        "exp": expire,
        "jti": jti,
        "iat": datetime.utcnow(),
        "type": "access"  # P1: Identifier le type de token
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def create_refresh_token(
    data: dict,
    expires_delta: timedelta | None = None,
    device_fingerprint: str | None = None
) -> str:
    """
    Crée un JWT refresh token avec JTI unique pour révocation.
    P1 SÉCURITÉ: Refresh Token Rotation (RTR) + Device Binding

    Args:
        data: Données à encoder (sub, tenant_id)
        expires_delta: Durée de validité personnalisée (défaut: 7 jours)
        device_fingerprint: Hash du device (IP + User-Agent) pour binding

    Returns:
        JWT refresh token signé

    SÉCURITÉ:
    - Durée de vie plus longue que l'access token
    - JTI unique pour révocation individuelle
    - Type "refresh" pour éviter confusion avec access token
    - Doit être révoqué à chaque utilisation (rotation)
    - Device binding pour détecter vol de token (P1 SÉCURITÉ)
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    # JTI unique pour la révocation
    jti = str(uuid.uuid4())

    to_encode.update({
        "exp": expire,
        "jti": jti,
        "iat": datetime.utcnow(),
        "type": "refresh"  # Identifier comme refresh token
    })

    # P1 SÉCURITÉ: Device Binding - ajouter fingerprint si fourni
    if device_fingerprint:
        to_encode["dfp"] = device_fingerprint

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def compute_device_fingerprint(client_ip: str, user_agent: str) -> str:
    """
    Calcule un fingerprint de device pour le binding des refresh tokens.
    P1 SÉCURITÉ: Détection de vol de token si utilisé depuis un autre device.

    Args:
        client_ip: Adresse IP du client
        user_agent: User-Agent du navigateur

    Returns:
        Hash SHA-256 tronqué (16 chars) du fingerprint

    Note:
        Le fingerprint est un hash pour préserver la confidentialité.
        On utilise seulement les 16 premiers caractères pour réduire la taille du token.
    """
    import hashlib
    # Normaliser les entrées
    ip = client_ip.strip() if client_ip else "unknown"
    ua = user_agent.strip()[:200] if user_agent else "unknown"  # Tronquer UA trop long

    # Hash combiné IP + User-Agent
    fingerprint_data = f"{ip}:{ua}:azals_dfp_salt"
    fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()

    # Retourner les 16 premiers caractères (suffisant pour détecter les changements)
    return fingerprint_hash[:16]


def verify_device_fingerprint(
    token_fingerprint: str | None,
    current_fingerprint: str,
    strict: bool = False
) -> tuple[bool, str]:
    """
    Vérifie si le device fingerprint correspond.
    P1 SÉCURITÉ: Détection de tentative d'utilisation depuis un autre device.

    Args:
        token_fingerprint: Fingerprint stocké dans le token (peut être None pour tokens legacy)
        current_fingerprint: Fingerprint du device actuel
        strict: Si True, rejette les tokens sans fingerprint

    Returns:
        Tuple (is_valid, reason)

    Note:
        En mode non-strict, les tokens legacy sans fingerprint sont acceptés
        pour permettre une migration progressive.
    """
    # Token legacy sans fingerprint
    if token_fingerprint is None:
        if strict:
            return False, "Token sans device binding - renouvellement requis"
        return True, "Token legacy accepté (pas de fingerprint)"

    # Comparaison du fingerprint
    if token_fingerprint == current_fingerprint:
        return True, "Device vérifié"

    # Fingerprint différent - possible vol de token
    return False, "Device mismatch - possible token theft"


def refresh_access_token(refresh_token: str) -> tuple[str, str] | None:
    """
    Utilise un refresh token pour obtenir une nouvelle paire access/refresh.
    P1 SÉCURITÉ: Rotation des refresh tokens.

    Args:
        refresh_token: Le refresh token actuel

    Returns:
        Tuple (new_access_token, new_refresh_token) ou None si invalide

    SÉCURITÉ:
    - Vérifie que le token est de type "refresh"
    - Révoque l'ancien refresh token (rotation)
    - Génère une nouvelle paire de tokens
    - Empêche la réutilisation d'un refresh token compromis
    """
    try:
        # Décoder le refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        # Vérifier que c'est bien un refresh token
        if payload.get("type") != "refresh":
            return None

        # Vérifier si blacklisté
        jti = payload.get("jti")
        if jti:
            from app.core.token_blacklist import is_token_blacklisted
            if is_token_blacklisted(jti):
                return None

        # Révoquer l'ancien refresh token (ROTATION)
        revoke_token(refresh_token)

        # Extraire les données utilisateur
        user_data = {
            "sub": payload.get("sub"),
            "tenant_id": payload.get("tenant_id"),
            "role": payload.get("role"),
        }

        # Générer nouvelle paire de tokens
        new_access = create_access_token(user_data)
        new_refresh = create_refresh_token(user_data)

        return (new_access, new_refresh)

    except JWTError:
        return None


def decode_access_token(token: str, check_blacklist: bool = True) -> dict | None:
    """
    Décode et valide un JWT, vérifie la blacklist.

    Args:
        token: JWT à décoder
        check_blacklist: Si True, vérifie que le token n'est pas révoqué

    Returns:
        Payload du JWT si valide et non révoqué, None sinon

    SÉCURITÉ:
    - P0: Valide la taille du token avant décodage (protection DoS)
    - Vérifie la signature et l'expiration
    - Vérifie que le token n'est pas dans la blacklist (révoqué)
    """
    # P0 SÉCURITÉ: Limite taille token pour éviter DoS par tokens géants
    # JWT typique: 500-1500 chars. Max raisonnable: 8KB
    MAX_TOKEN_SIZE = 8192
    if not token or len(token) > MAX_TOKEN_SIZE:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Vérifier si le token est blacklisté
        if check_blacklist:
            jti = payload.get("jti")
            if jti:
                from app.core.token_blacklist import is_token_blacklisted
                if is_token_blacklisted(jti):
                    return None

        return payload
    except JWTError:
        return None


def revoke_token(token: str) -> bool:
    """
    Révoque un token JWT en l'ajoutant à la blacklist.

    Args:
        token: JWT à révoquer

    Returns:
        True si révoqué avec succès, False sinon
    """
    try:
        # Décoder sans vérifier la blacklist (le token peut déjà y être)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = payload.get("exp")

        if not jti or not exp:
            return False

        # Convertir exp en timestamp si nécessaire
        if isinstance(exp, datetime):
            exp_timestamp = exp.timestamp()
        else:
            exp_timestamp = float(exp)

        from app.core.token_blacklist import blacklist_token
        return blacklist_token(jti, exp_timestamp)

    except JWTError:
        return False
