"""
Implémentation du sous-programme : validate_time_slot

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 18+ endroits dans le codebase
"""

from typing import Dict, Any
from datetime import datetime, time, timedelta
import re


def _parse_time(time_value) -> time | None:
    """Parse une heure depuis différents formats."""
    if time_value is None:
        return None

    if isinstance(time_value, time):
        return time_value

    if isinstance(time_value, datetime):
        return time_value.time()

    if isinstance(time_value, str):
        time_str = time_value.strip()

        # Format HH:MM ou HH:MM:SS
        match = re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            second = int(match.group(3)) if match.group(3) else 0

            if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                return time(hour, minute, second)

        # Format HHMM
        if len(time_str) == 4 and time_str.isdigit():
            hour = int(time_str[:2])
            minute = int(time_str[2:])
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return time(hour, minute)

    return None


def _time_to_minutes(t: time) -> int:
    """Convertit une heure en minutes depuis minuit."""
    return t.hour * 60 + t.minute


def _minutes_to_time(minutes: int) -> time:
    """Convertit des minutes depuis minuit en heure."""
    hours = minutes // 60
    mins = minutes % 60
    return time(hours % 24, mins)


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un créneau horaire.

    Vérifie:
    - Format des heures valide
    - Cohérence début < fin
    - Durée minimale/maximale
    - Respect des horaires d'ouverture

    Args:
        inputs: {
            "start": string/time,  # Heure de début
            "end": string/time,  # Heure de fin (optionnel)
            "duration_minutes": number,  # Durée en minutes (si pas de fin)
            "min_duration_minutes": number,  # Durée minimale (défaut: 15)
            "max_duration_minutes": number,  # Durée maximale (défaut: 480 = 8h)
            "business_hours_start": string,  # Début horaires ouverture (optionnel)
            "business_hours_end": string,  # Fin horaires ouverture (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si créneau valide
            "start_time": string,  # Heure début (HH:MM)
            "end_time": string,  # Heure fin (HH:MM)
            "duration_minutes": number,  # Durée en minutes
            "duration_formatted": string,  # Durée formatée (1h30)
            "is_within_business_hours": boolean,  # Dans horaires ouverture
            "spans_midnight": boolean,  # Chevauche minuit
            "error": string,  # Message d'erreur si invalide
        }
    """
    start_input = inputs.get("start")
    end_input = inputs.get("end")
    duration_input = inputs.get("duration_minutes")
    min_duration = inputs.get("min_duration_minutes", 15)
    max_duration = inputs.get("max_duration_minutes", 480)
    biz_start_input = inputs.get("business_hours_start")
    biz_end_input = inputs.get("business_hours_end")

    # Heure de début requise
    if start_input is None:
        return {
            "is_valid": False,
            "start_time": None,
            "end_time": None,
            "duration_minutes": None,
            "duration_formatted": None,
            "is_within_business_hours": None,
            "spans_midnight": None,
            "error": "Heure de début requise"
        }

    # Parse de l'heure de début
    start_time = _parse_time(start_input)
    if start_time is None:
        return {
            "is_valid": False,
            "start_time": None,
            "end_time": None,
            "duration_minutes": None,
            "duration_formatted": None,
            "is_within_business_hours": None,
            "spans_midnight": None,
            "error": "Format d'heure de début invalide"
        }

    # Déterminer l'heure de fin
    end_time = None
    duration_minutes = None
    spans_midnight = False

    if end_input:
        end_time = _parse_time(end_input)
        if end_time is None:
            return {
                "is_valid": False,
                "start_time": start_time.strftime("%H:%M"),
                "end_time": None,
                "duration_minutes": None,
                "duration_formatted": None,
                "is_within_business_hours": None,
                "spans_midnight": None,
                "error": "Format d'heure de fin invalide"
            }

        start_minutes = _time_to_minutes(start_time)
        end_minutes = _time_to_minutes(end_time)

        if end_minutes <= start_minutes:
            # Chevauche minuit
            spans_midnight = True
            duration_minutes = (24 * 60 - start_minutes) + end_minutes
        else:
            duration_minutes = end_minutes - start_minutes

    elif duration_input:
        if not isinstance(duration_input, (int, float)) or duration_input <= 0:
            return {
                "is_valid": False,
                "start_time": start_time.strftime("%H:%M"),
                "end_time": None,
                "duration_minutes": None,
                "duration_formatted": None,
                "is_within_business_hours": None,
                "spans_midnight": None,
                "error": "Durée invalide"
            }

        duration_minutes = int(duration_input)
        end_minutes = (_time_to_minutes(start_time) + duration_minutes) % (24 * 60)
        end_time = _minutes_to_time(end_minutes)
        spans_midnight = (_time_to_minutes(start_time) + duration_minutes) >= 24 * 60

    else:
        return {
            "is_valid": False,
            "start_time": start_time.strftime("%H:%M"),
            "end_time": None,
            "duration_minutes": None,
            "duration_formatted": None,
            "is_within_business_hours": None,
            "spans_midnight": None,
            "error": "Heure de fin ou durée requise"
        }

    # Vérification durée minimale
    if duration_minutes < min_duration:
        return {
            "is_valid": False,
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M"),
            "duration_minutes": duration_minutes,
            "duration_formatted": f"{duration_minutes}min",
            "is_within_business_hours": None,
            "spans_midnight": spans_midnight,
            "error": f"Durée minimale: {min_duration} minutes"
        }

    # Vérification durée maximale
    if duration_minutes > max_duration:
        return {
            "is_valid": False,
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M"),
            "duration_minutes": duration_minutes,
            "duration_formatted": f"{duration_minutes // 60}h{duration_minutes % 60:02d}",
            "is_within_business_hours": None,
            "spans_midnight": spans_midnight,
            "error": f"Durée maximale: {max_duration // 60}h{max_duration % 60:02d}"
        }

    # Formatage durée
    if duration_minutes >= 60:
        hours = duration_minutes // 60
        mins = duration_minutes % 60
        duration_formatted = f"{hours}h{mins:02d}" if mins else f"{hours}h"
    else:
        duration_formatted = f"{duration_minutes}min"

    # Vérification horaires ouverture
    is_within_business_hours = True
    if biz_start_input and biz_end_input:
        biz_start = _parse_time(biz_start_input)
        biz_end = _parse_time(biz_end_input)

        if biz_start and biz_end:
            start_mins = _time_to_minutes(start_time)
            end_mins = _time_to_minutes(end_time)
            biz_start_mins = _time_to_minutes(biz_start)
            biz_end_mins = _time_to_minutes(biz_end)

            if not spans_midnight:
                is_within_business_hours = (
                    start_mins >= biz_start_mins and
                    end_mins <= biz_end_mins
                )
            else:
                is_within_business_hours = False  # Créneau de nuit

    return {
        "is_valid": True,
        "start_time": start_time.strftime("%H:%M"),
        "end_time": end_time.strftime("%H:%M"),
        "duration_minutes": duration_minutes,
        "duration_formatted": duration_formatted,
        "is_within_business_hours": is_within_business_hours,
        "spans_midnight": spans_midnight,
        "error": None
    }
