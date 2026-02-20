"""
Implémentation du sous-programme : validate_coordinates

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 15+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


# Limites de coordonnées
LAT_MIN = -90.0
LAT_MAX = 90.0
LON_MIN = -180.0
LON_MAX = 180.0

# Précision recommandée pour différents usages
PRECISION_LEVELS = {
    "country": 0,  # ~111 km
    "city": 2,  # ~1.1 km
    "neighborhood": 3,  # ~110 m
    "street": 4,  # ~11 m
    "building": 5,  # ~1.1 m
    "precise": 6,  # ~0.11 m
}


def _to_float(value) -> float | None:
    """Convertit une valeur en float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(',', '.')
        if cleaned and _is_number(cleaned):
            return float(cleaned)
    return None


def _is_number(s: str) -> bool:
    """Vérifie si une chaîne est un nombre valide."""
    if not s:
        return False
    if s[0] in '+-':
        s = s[1:]
    if not s:
        return False
    return s.replace('.', '', 1).isdigit()


def _get_precision(value: float) -> int:
    """Détermine le nombre de décimales significatives."""
    str_val = str(value)
    if '.' not in str_val:
        return 0
    decimal_part = str_val.split('.')[1].rstrip('0')
    return len(decimal_part)


def _get_precision_level(precision: int) -> str:
    """Détermine le niveau de précision."""
    if precision <= 0:
        return "country"
    elif precision <= 2:
        return "city"
    elif precision <= 3:
        return "neighborhood"
    elif precision <= 4:
        return "street"
    elif precision <= 5:
        return "building"
    else:
        return "precise"


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide des coordonnées GPS (latitude, longitude).

    Plages valides:
    - Latitude: -90 à +90
    - Longitude: -180 à +180

    Args:
        inputs: {
            "lat": number,  # Latitude
            "lon": number,  # Longitude (optionnel)
            "min_precision": number,  # Décimales minimum (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si coordonnées valides
            "latitude": number,  # Latitude normalisée
            "longitude": number,  # Longitude normalisée
            "precision": number,  # Décimales de précision
            "precision_level": string,  # Niveau (city, street, etc.)
            "hemisphere_lat": string,  # N ou S
            "hemisphere_lon": string,  # E ou W
            "dms_lat": string,  # Format DMS (ex: 48°51'24"N)
            "dms_lon": string,  # Format DMS
            "error": string,  # Message d'erreur si invalide
        }
    """
    lat_input = inputs.get("lat")
    lon_input = inputs.get("lon")
    min_precision = inputs.get("min_precision")

    # Latitude requise
    if lat_input is None:
        return {
            "is_valid": False,
            "latitude": None,
            "longitude": None,
            "precision": None,
            "precision_level": None,
            "hemisphere_lat": None,
            "hemisphere_lon": None,
            "dms_lat": None,
            "dms_lon": None,
            "error": "Latitude requise"
        }

    # Conversion latitude
    lat = _to_float(lat_input)
    if lat is None:
        return {
            "is_valid": False,
            "latitude": None,
            "longitude": None,
            "precision": None,
            "precision_level": None,
            "hemisphere_lat": None,
            "hemisphere_lon": None,
            "dms_lat": None,
            "dms_lon": None,
            "error": "Format de latitude invalide"
        }

    # Validation plage latitude
    if lat < LAT_MIN or lat > LAT_MAX:
        return {
            "is_valid": False,
            "latitude": lat,
            "longitude": None,
            "precision": None,
            "precision_level": None,
            "hemisphere_lat": None,
            "hemisphere_lon": None,
            "dms_lat": None,
            "dms_lon": None,
            "error": f"Latitude hors plage ({LAT_MIN} à {LAT_MAX})"
        }

    # Conversion longitude (si fournie)
    lon = None
    if lon_input is not None:
        lon = _to_float(lon_input)
        if lon is None:
            return {
                "is_valid": False,
                "latitude": lat,
                "longitude": None,
                "precision": None,
                "precision_level": None,
                "hemisphere_lat": "N" if lat >= 0 else "S",
                "hemisphere_lon": None,
                "dms_lat": None,
                "dms_lon": None,
                "error": "Format de longitude invalide"
            }

        # Validation plage longitude
        if lon < LON_MIN or lon > LON_MAX:
            return {
                "is_valid": False,
                "latitude": lat,
                "longitude": lon,
                "precision": None,
                "precision_level": None,
                "hemisphere_lat": "N" if lat >= 0 else "S",
                "hemisphere_lon": None,
                "dms_lat": None,
                "dms_lon": None,
                "error": f"Longitude hors plage ({LON_MIN} à {LON_MAX})"
            }

    # Calcul de la précision
    lat_precision = _get_precision(lat)
    lon_precision = _get_precision(lon) if lon is not None else 0
    precision = min(lat_precision, lon_precision) if lon is not None else lat_precision

    # Vérification précision minimale
    if min_precision is not None and precision < min_precision:
        return {
            "is_valid": False,
            "latitude": lat,
            "longitude": lon,
            "precision": precision,
            "precision_level": _get_precision_level(precision),
            "hemisphere_lat": "N" if lat >= 0 else "S",
            "hemisphere_lon": "E" if lon and lon >= 0 else "W" if lon else None,
            "dms_lat": None,
            "dms_lon": None,
            "error": f"Précision insuffisante (minimum {min_precision} décimales)"
        }

    # Hémisphères
    hemisphere_lat = "N" if lat >= 0 else "S"
    hemisphere_lon = "E" if lon and lon >= 0 else "W" if lon else None

    # Conversion en DMS (Degrees, Minutes, Seconds)
    def to_dms(decimal_deg: float, is_lat: bool) -> str:
        is_negative = decimal_deg < 0
        decimal_deg = abs(decimal_deg)
        degrees = int(decimal_deg)
        minutes_float = (decimal_deg - degrees) * 60
        minutes = int(minutes_float)
        seconds = (minutes_float - minutes) * 60

        direction = ""
        if is_lat:
            direction = "S" if is_negative else "N"
        else:
            direction = "W" if is_negative else "E"

        return f"{degrees}°{minutes}'{seconds:.1f}\"{direction}"

    dms_lat = to_dms(lat, True)
    dms_lon = to_dms(lon, False) if lon is not None else None

    return {
        "is_valid": True,
        "latitude": round(lat, 8),
        "longitude": round(lon, 8) if lon is not None else None,
        "precision": precision,
        "precision_level": _get_precision_level(precision),
        "hemisphere_lat": hemisphere_lat,
        "hemisphere_lon": hemisphere_lon,
        "dms_lat": dms_lat,
        "dms_lon": dms_lon,
        "error": None
    }
