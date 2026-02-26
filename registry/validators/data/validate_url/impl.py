"""
Implémentation du sous-programme : validate_url

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 15+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Protocoles autorisés
ALLOWED_PROTOCOLS = {"http", "https", "ftp", "ftps", "mailto", "tel", "file"}

# Pattern pour validation URL (simplifié mais robuste)
URL_PATTERN = re.compile(
    r'^(?P<protocol>[a-z][a-z0-9+.-]*)://'  # Protocole
    r'(?:(?P<userinfo>[^@/]+)@)?'  # User info (optionnel)
    r'(?P<host>'
    r'(?P<ipv4>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|'  # IPv4
    r'(?:\[(?P<ipv6>[^\]]+)\])|'  # IPv6
    r'(?P<domain>[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)'  # Domaine
    r')'
    r'(?::(?P<port>\d{1,5}))?'  # Port (optionnel)
    r'(?P<path>/[^?#]*)?'  # Chemin (optionnel)
    r'(?:\?(?P<query>[^#]*))?'  # Query string (optionnel)
    r'(?:#(?P<fragment>.*))?$',  # Fragment (optionnel)
    re.IGNORECASE
)

# Pattern simplifié pour URLs sans protocole
DOMAIN_PATTERN = re.compile(
    r'^(?P<domain>[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?'
    r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+)'
    r'(?::(?P<port>\d{1,5}))?'
    r'(?P<path>/[^?#]*)?'
    r'(?:\?(?P<query>[^#]*))?'
    r'(?:#(?P<fragment>.*))?$'
)


def _validate_port(port_str: str) -> tuple[bool, int | None, str]:
    """Valide un numéro de port."""
    if not port_str:
        return True, None, ""

    if not port_str.isdigit():
        return False, None, "Le port doit être numérique"

    port = int(port_str)
    if port < 1 or port > 65535:
        return False, port, f"Port invalide: {port} (doit être entre 1 et 65535)"

    return True, port, ""


def _validate_ipv4(ip: str) -> bool:
    """Valide une adresse IPv4."""
    parts = ip.split('.')
    if len(parts) != 4:
        return False

    for part in parts:
        if not part.isdigit():
            return False
        num = int(part)
        if num < 0 or num > 255:
            return False

    return True


def _get_default_port(protocol: str) -> int | None:
    """Retourne le port par défaut pour un protocole."""
    defaults = {
        "http": 80,
        "https": 443,
        "ftp": 21,
        "ftps": 990,
        "ssh": 22,
    }
    return defaults.get(protocol.lower())


def _extract_tld(domain: str) -> str | None:
    """Extrait le TLD d'un domaine."""
    if '.' not in domain:
        return None
    return domain.rsplit('.', 1)[-1].lower()


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide une URL selon RFC 3986.

    Args:
        inputs: {
            "url": string,  # URL à valider
            "require_https": boolean,  # Exiger HTTPS (optionnel)
            "allowed_protocols": array,  # Protocoles autorisés (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si URL valide
            "normalized_url": string,  # URL normalisée
            "protocol": string,  # Protocole (http, https, etc.)
            "domain": string,  # Domaine ou IP
            "host": string,  # Host complet (domain:port)
            "port": number,  # Port (null si défaut)
            "path": string,  # Chemin
            "query": string,  # Query string
            "fragment": string,  # Fragment
            "tld": string,  # Top-level domain
            "is_secure": boolean,  # True si protocole sécurisé
            "is_ip": boolean,  # True si host est une IP
            "error": string,  # Message d'erreur si invalide
        }
    """
    url = inputs.get("url", "")
    require_https = inputs.get("require_https", False)
    allowed_protocols = inputs.get("allowed_protocols", list(ALLOWED_PROTOCOLS))

    # Valeur vide
    if not url:
        return {
            "is_valid": False,
            "normalized_url": None,
            "protocol": None,
            "domain": None,
            "host": None,
            "port": None,
            "path": None,
            "query": None,
            "fragment": None,
            "tld": None,
            "is_secure": None,
            "is_ip": None,
            "error": "URL requise"
        }

    url = str(url).strip()

    # Longueur maximale raisonnable
    if len(url) > 2048:
        return {
            "is_valid": False,
            "normalized_url": None,
            "protocol": None,
            "domain": None,
            "host": None,
            "port": None,
            "path": None,
            "query": None,
            "fragment": None,
            "tld": None,
            "is_secure": None,
            "is_ip": None,
            "error": "URL trop longue (max 2048 caractères)"
        }

    # Tentative de match avec protocole
    match = URL_PATTERN.match(url)

    # Si pas de match, essayer d'ajouter https://
    if not match and not url.startswith(('http://', 'https://', 'ftp://')):
        domain_match = DOMAIN_PATTERN.match(url)
        if domain_match:
            url = 'https://' + url
            match = URL_PATTERN.match(url)

    if not match:
        return {
            "is_valid": False,
            "normalized_url": None,
            "protocol": None,
            "domain": None,
            "host": None,
            "port": None,
            "path": None,
            "query": None,
            "fragment": None,
            "tld": None,
            "is_secure": None,
            "is_ip": None,
            "error": "Format d'URL invalide"
        }

    # Extraction des composants
    groups = match.groupdict()
    protocol = groups.get("protocol", "").lower()
    ipv4 = groups.get("ipv4")
    ipv6 = groups.get("ipv6")
    domain = groups.get("domain")
    port_str = groups.get("port", "")
    path = groups.get("path", "") or "/"
    query = groups.get("query")
    fragment = groups.get("fragment")

    # Déterminer le host
    if ipv4:
        host_domain = ipv4
        is_ip = True
        if not _validate_ipv4(ipv4):
            return {
                "is_valid": False,
                "normalized_url": None,
                "protocol": protocol,
                "domain": ipv4,
                "host": None,
                "port": None,
                "path": None,
                "query": None,
                "fragment": None,
                "tld": None,
                "is_secure": None,
                "is_ip": True,
                "error": "Adresse IPv4 invalide"
            }
    elif ipv6:
        host_domain = f"[{ipv6}]"
        is_ip = True
    else:
        host_domain = domain.lower() if domain else ""
        is_ip = False

    # Validation du protocole
    if protocol not in [p.lower() for p in allowed_protocols]:
        return {
            "is_valid": False,
            "normalized_url": None,
            "protocol": protocol,
            "domain": host_domain,
            "host": None,
            "port": None,
            "path": None,
            "query": None,
            "fragment": None,
            "tld": None,
            "is_secure": None,
            "is_ip": is_ip,
            "error": f"Protocole non autorisé: {protocol}"
        }

    # Vérification HTTPS requis
    if require_https and protocol != "https":
        return {
            "is_valid": False,
            "normalized_url": None,
            "protocol": protocol,
            "domain": host_domain,
            "host": None,
            "port": None,
            "path": None,
            "query": None,
            "fragment": None,
            "tld": _extract_tld(host_domain) if not is_ip else None,
            "is_secure": False,
            "is_ip": is_ip,
            "error": "HTTPS requis"
        }

    # Validation du port
    is_valid_port, port, port_error = _validate_port(port_str)
    if not is_valid_port:
        return {
            "is_valid": False,
            "normalized_url": None,
            "protocol": protocol,
            "domain": host_domain,
            "host": None,
            "port": None,
            "path": None,
            "query": None,
            "fragment": None,
            "tld": _extract_tld(host_domain) if not is_ip else None,
            "is_secure": None,
            "is_ip": is_ip,
            "error": port_error
        }

    # Construction du host
    if port and port != _get_default_port(protocol):
        host = f"{host_domain}:{port}"
    else:
        host = host_domain

    # TLD
    tld = _extract_tld(host_domain) if not is_ip else None

    # URL normalisée
    normalized = f"{protocol}://{host}{path}"
    if query:
        normalized += f"?{query}"
    if fragment:
        normalized += f"#{fragment}"

    # Protocoles sécurisés
    is_secure = protocol in {"https", "ftps", "sftp", "ssh"}

    return {
        "is_valid": True,
        "normalized_url": normalized,
        "protocol": protocol,
        "domain": host_domain,
        "host": host,
        "port": port,
        "path": path,
        "query": query,
        "fragment": fragment,
        "tld": tld,
        "is_secure": is_secure,
        "is_ip": is_ip,
        "error": None
    }
