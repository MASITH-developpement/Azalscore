"""
AZALS - Sécurité et Authentification
Gestion JWT et hashing de mots de passe
"""

from datetime import datetime, timedelta
from typing import Optional
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


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un JWT access token.
    
    Args:
        data: Données à encoder (sub, tenant_id, role)
        expires_delta: Durée de validité personnalisée
    
    Returns:
        JWT signé
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Décode et valide un JWT.
    
    Args:
        token: JWT à décoder
    
    Returns:
        Payload du JWT si valide, None sinon
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
