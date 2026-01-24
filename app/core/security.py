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

    salt = bcrypt.gensalt()
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
        "iat": datetime.utcnow()
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str, check_blacklist: bool = True) -> dict | None:
    """
    Décode et valide un JWT, vérifie la blacklist.

    Args:
        token: JWT à décoder
        check_blacklist: Si True, vérifie que le token n'est pas révoqué

    Returns:
        Payload du JWT si valide et non révoqué, None sinon

    SÉCURITÉ:
    - Vérifie la signature et l'expiration
    - Vérifie que le token n'est pas dans la blacklist (révoqué)
    """
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
