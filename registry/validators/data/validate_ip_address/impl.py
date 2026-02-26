"""
Implémentation du sous-programme : validate_ip_address

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 6+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Plages IPv4 réservées
IPV4_RESERVED_RANGES = {
    "loopback": ("127.0.0.0", "127.255.255.255"),
    "private_a": ("10.0.0.0", "10.255.255.255"),
    "private_b": ("172.16.0.0", "172.31.255.255"),
    "private_c": ("192.168.0.0", "192.168.255.255"),
    "link_local": ("169.254.0.0", "169.254.255.255"),
    "multicast": ("224.0.0.0", "239.255.255.255"),
    "broadcast": ("255.255.255.255", "255.255.255.255"),
    "unspecified": ("0.0.0.0", "0.0.0.0"),
}


def _ip_to_int(ip: str) -> int:
    """Convertit une IPv4 en entier."""
    parts = ip.split('.')
    return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])


def _validate_ipv4(ip: str) -> tuple[bool, str]:
    """
    Valide une adresse IPv4.

    Returns:
        (is_valid, error)
    """
    # Pattern basique
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        return False, "Format IPv4 invalide"

    parts = ip.split('.')
    if len(parts) != 4:
        return False, "IPv4 doit avoir 4 octets"

    for i, part in enumerate(parts):
        # Pas de zéros en tête (sauf 0 seul)
        if len(part) > 1 and part.startswith('0'):
            return False, f"Octet {i+1} ne doit pas avoir de zéro en tête"

        num = int(part)
        if num < 0 or num > 255:
            return False, f"Octet {i+1} hors plage (0-255): {num}"

    return True, ""


def _validate_ipv6(ip: str) -> tuple[bool, str]:
    """
    Valide une adresse IPv6.

    Returns:
        (is_valid, error)
    """
    # Normalisation: suppression des crochets si présents
    ip = ip.strip('[]')

    # Vérification de la syntaxe générale
    if ip == "::":
        return True, ""

    # Comptage des groupes et vérification du ::
    if "::" in ip:
        if ip.count("::") > 1:
            return False, "IPv6 ne peut contenir qu'un seul '::'"

        # Expansion du ::
        parts = ip.split("::")
        left = parts[0].split(":") if parts[0] else []
        right = parts[1].split(":") if parts[1] else []

        # Vérifier qu'on n'a pas trop de groupes
        if len(left) + len(right) > 7:
            return False, "Trop de groupes dans l'adresse IPv6"

        all_groups = left + ['0'] * (8 - len(left) - len(right)) + right
    else:
        all_groups = ip.split(":")
        if len(all_groups) != 8:
            return False, f"IPv6 doit avoir 8 groupes (reçu: {len(all_groups)})"

    # Validation de chaque groupe
    for i, group in enumerate(all_groups):
        if not group:
            continue  # Groupe vide (déjà géré par ::)

        if len(group) > 4:
            return False, f"Groupe {i+1} trop long (max 4 caractères)"

        if not re.match(r'^[0-9a-fA-F]+$', group):
            return False, f"Groupe {i+1} contient des caractères non hexadécimaux"

    return True, ""


def _get_ipv4_type(ip: str) -> tuple[str, bool]:
    """
    Détermine le type d'une adresse IPv4.

    Returns:
        (type_name, is_private)
    """
    ip_int = _ip_to_int(ip)

    for range_name, (start, end) in IPV4_RESERVED_RANGES.items():
        start_int = _ip_to_int(start)
        end_int = _ip_to_int(end)

        if start_int <= ip_int <= end_int:
            is_private = range_name.startswith("private") or range_name == "loopback"
            return range_name, is_private

    return "public", False


def _get_ipv6_type(ip: str) -> tuple[str, bool]:
    """
    Détermine le type d'une adresse IPv6.

    Returns:
        (type_name, is_private)
    """
    ip_lower = ip.lower().strip('[]')

    # Loopback
    if ip_lower == "::1":
        return "loopback", True

    # Unspecified
    if ip_lower == "::":
        return "unspecified", False

    # Link-local (fe80::/10)
    if ip_lower.startswith("fe8") or ip_lower.startswith("fe9") or ip_lower.startswith("fea") or ip_lower.startswith("feb"):
        return "link_local", True

    # Unique local (fc00::/7)
    if ip_lower.startswith("fc") or ip_lower.startswith("fd"):
        return "private", True

    # Multicast (ff00::/8)
    if ip_lower.startswith("ff"):
        return "multicast", False

    # IPv4-mapped (::ffff:)
    if "::ffff:" in ip_lower:
        return "ipv4_mapped", False

    return "public", False


def _expand_ipv6(ip: str) -> str:
    """Expanse une adresse IPv6 en format complet."""
    ip = ip.strip('[]')

    if "::" in ip:
        parts = ip.split("::")
        left = parts[0].split(":") if parts[0] else []
        right = parts[1].split(":") if parts[1] else []
        middle = ['0000'] * (8 - len(left) - len(right))
        all_groups = left + middle + right
    else:
        all_groups = ip.split(":")

    # Padding de chaque groupe
    expanded = [group.zfill(4) for group in all_groups]
    return ":".join(expanded)


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide une adresse IP (IPv4 ou IPv6).

    Args:
        inputs: {
            "ip_address": string,  # Adresse IP à valider
            "version": string,  # Version attendue: "ipv4", "ipv6", "any" (défaut: "any")
            "allow_private": boolean,  # Autoriser IPs privées (défaut: true)
        }

    Returns:
        {
            "is_valid": boolean,  # True si IP valide
            "normalized_ip": string,  # IP normalisée
            "version": string,  # Version détectée: "ipv4" ou "ipv6"
            "type": string,  # Type: public, private, loopback, etc.
            "is_private": boolean,  # True si IP privée/locale
            "is_loopback": boolean,  # True si loopback
            "is_multicast": boolean,  # True si multicast
            "expanded_ipv6": string,  # IPv6 en format complet (si applicable)
            "error": string,  # Message d'erreur si invalide
        }
    """
    ip_address = inputs.get("ip_address", "")
    version_hint = inputs.get("version", "any")
    allow_private = inputs.get("allow_private", True)

    # Valeur vide
    if not ip_address:
        return {
            "is_valid": False,
            "normalized_ip": None,
            "version": None,
            "type": None,
            "is_private": None,
            "is_loopback": None,
            "is_multicast": None,
            "expanded_ipv6": None,
            "error": "Adresse IP requise"
        }

    ip_address = str(ip_address).strip()

    # Détection de la version
    is_ipv4 = '.' in ip_address and ':' not in ip_address
    is_ipv6 = ':' in ip_address

    if not is_ipv4 and not is_ipv6:
        return {
            "is_valid": False,
            "normalized_ip": None,
            "version": None,
            "type": None,
            "is_private": None,
            "is_loopback": None,
            "is_multicast": None,
            "expanded_ipv6": None,
            "error": "Format d'adresse IP non reconnu"
        }

    # Vérification version attendue
    if version_hint == "ipv4" and not is_ipv4:
        return {
            "is_valid": False,
            "normalized_ip": ip_address,
            "version": "ipv6" if is_ipv6 else None,
            "type": None,
            "is_private": None,
            "is_loopback": None,
            "is_multicast": None,
            "expanded_ipv6": None,
            "error": "IPv4 attendu mais IPv6 fourni"
        }

    if version_hint == "ipv6" and not is_ipv6:
        return {
            "is_valid": False,
            "normalized_ip": ip_address,
            "version": "ipv4" if is_ipv4 else None,
            "type": None,
            "is_private": None,
            "is_loopback": None,
            "is_multicast": None,
            "expanded_ipv6": None,
            "error": "IPv6 attendu mais IPv4 fourni"
        }

    # Validation selon la version
    if is_ipv4:
        is_valid, error = _validate_ipv4(ip_address)
        if not is_valid:
            return {
                "is_valid": False,
                "normalized_ip": ip_address,
                "version": "ipv4",
                "type": None,
                "is_private": None,
                "is_loopback": None,
                "is_multicast": None,
                "expanded_ipv6": None,
                "error": error
            }

        ip_type, is_private = _get_ipv4_type(ip_address)
        is_loopback = ip_type == "loopback"
        is_multicast = ip_type == "multicast"

        # Vérification IPs privées autorisées
        if not allow_private and is_private:
            return {
                "is_valid": False,
                "normalized_ip": ip_address,
                "version": "ipv4",
                "type": ip_type,
                "is_private": True,
                "is_loopback": is_loopback,
                "is_multicast": is_multicast,
                "expanded_ipv6": None,
                "error": "Les adresses IP privées ne sont pas autorisées"
            }

        return {
            "is_valid": True,
            "normalized_ip": ip_address,
            "version": "ipv4",
            "type": ip_type,
            "is_private": is_private,
            "is_loopback": is_loopback,
            "is_multicast": is_multicast,
            "expanded_ipv6": None,
            "error": None
        }

    else:  # IPv6
        is_valid, error = _validate_ipv6(ip_address)
        if not is_valid:
            return {
                "is_valid": False,
                "normalized_ip": ip_address,
                "version": "ipv6",
                "type": None,
                "is_private": None,
                "is_loopback": None,
                "is_multicast": None,
                "expanded_ipv6": None,
                "error": error
            }

        ip_type, is_private = _get_ipv6_type(ip_address)
        is_loopback = ip_type == "loopback"
        is_multicast = ip_type == "multicast"
        expanded = _expand_ipv6(ip_address)

        # Vérification IPs privées autorisées
        if not allow_private and is_private:
            return {
                "is_valid": False,
                "normalized_ip": ip_address.lower(),
                "version": "ipv6",
                "type": ip_type,
                "is_private": True,
                "is_loopback": is_loopback,
                "is_multicast": is_multicast,
                "expanded_ipv6": expanded,
                "error": "Les adresses IP privées ne sont pas autorisées"
            }

        return {
            "is_valid": True,
            "normalized_ip": ip_address.lower(),
            "version": "ipv6",
            "type": ip_type,
            "is_private": is_private,
            "is_loopback": is_loopback,
            "is_multicast": is_multicast,
            "expanded_ipv6": expanded,
            "error": None
        }
