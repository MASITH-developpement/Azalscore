"""
Implémentation du sous-programme : validate_booking_overlap

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 15+ endroits dans le codebase
"""

from typing import Dict, Any, List
from datetime import datetime, date, time


def _parse_datetime(value) -> datetime | None:
    """Parse une valeur en datetime."""
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(value, time.min)

    if isinstance(value, str):
        value = value.strip()

        # Format ISO: YYYY-MM-DDTHH:MM:SS
        if 'T' in value:
            parts = value.split('T')
            if len(parts) == 2:
                date_parts = parts[0].split('-')
                time_parts = parts[1].replace('Z', '').split(':')
                if len(date_parts) == 3 and len(time_parts) >= 2:
                    year = int(date_parts[0])
                    month = int(date_parts[1])
                    day = int(date_parts[2])
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    second = int(time_parts[2].split('.')[0]) if len(time_parts) > 2 else 0
                    return datetime(year, month, day, hour, minute, second)

        # Format YYYY-MM-DD HH:MM:SS
        if ' ' in value:
            parts = value.split(' ')
            if len(parts) >= 2:
                date_parts = parts[0].split('-')
                time_parts = parts[1].split(':')
                if len(date_parts) == 3 and len(time_parts) >= 2:
                    year = int(date_parts[0])
                    month = int(date_parts[1])
                    day = int(date_parts[2])
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    second = int(time_parts[2].split('.')[0]) if len(time_parts) > 2 else 0
                    return datetime(year, month, day, hour, minute, second)

        # Format YYYY-MM-DD (date seule)
        if len(value) == 10 and value.count('-') == 2:
            parts = value.split('-')
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                return datetime(int(parts[0]), int(parts[1]), int(parts[2]))

    return None


def _intervals_overlap(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> bool:
    """Vérifie si deux intervalles se chevauchent."""
    # Deux intervalles se chevauchent si l'un commence avant que l'autre ne finisse
    return start1 < end2 and start2 < end1


def _get_overlap_minutes(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> int:
    """Calcule la durée de chevauchement en minutes."""
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)
    if overlap_start < overlap_end:
        return int((overlap_end - overlap_start).total_seconds() / 60)
    return 0


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide l'absence de chevauchement entre réservations.

    Vérifie:
    - Pas de chevauchement entre la nouvelle réservation et les existantes
    - Ou pas de chevauchement mutuel dans une liste de réservations

    Args:
        inputs: {
            "new_booking": dict,  # Nouvelle réservation {start, end, resource_id?}
            "existing_bookings": array,  # Réservations existantes [{start, end, resource_id?, id?}]
            "allow_adjacent": boolean,  # Autoriser les créneaux adjacents (défaut: true)
            "buffer_minutes": number,  # Temps tampon entre réservations (défaut: 0)
            "check_resource": boolean,  # Vérifier par ressource (défaut: true)
        }

        OU

        inputs: {
            "bookings": array,  # Liste de réservations à vérifier mutuellement
            "allow_adjacent": boolean,
            "buffer_minutes": number,
            "check_resource": boolean,
        }

    Returns:
        {
            "is_valid": boolean,  # True si pas de chevauchement
            "has_overlap": boolean,  # True si chevauchement détecté
            "overlapping_bookings": array,  # Paires de réservations qui se chevauchent
            "overlap_details": array,  # Détails des chevauchements
            "total_overlap_minutes": number,  # Durée totale de chevauchement
            "error": string,  # Message d'erreur si chevauchement
        }
    """
    new_booking = inputs.get("new_booking")
    existing_bookings = inputs.get("existing_bookings", [])
    bookings = inputs.get("bookings", [])
    allow_adjacent = inputs.get("allow_adjacent", True)
    buffer_minutes = inputs.get("buffer_minutes", 0)
    check_resource = inputs.get("check_resource", True)

    overlapping_bookings = []
    overlap_details = []
    total_overlap_minutes = 0

    # Mode 1: Vérifier une nouvelle réservation contre les existantes
    if new_booking:
        new_start = _parse_datetime(new_booking.get("start"))
        new_end = _parse_datetime(new_booking.get("end"))
        new_resource = new_booking.get("resource_id")

        if new_start is None:
            return {
                "is_valid": False,
                "has_overlap": None,
                "overlapping_bookings": [],
                "overlap_details": [],
                "total_overlap_minutes": 0,
                "error": "Date de début de la nouvelle réservation invalide"
            }

        if new_end is None:
            return {
                "is_valid": False,
                "has_overlap": None,
                "overlapping_bookings": [],
                "overlap_details": [],
                "total_overlap_minutes": 0,
                "error": "Date de fin de la nouvelle réservation invalide"
            }

        if new_end <= new_start:
            return {
                "is_valid": False,
                "has_overlap": None,
                "overlapping_bookings": [],
                "overlap_details": [],
                "total_overlap_minutes": 0,
                "error": "La date de fin doit être après la date de début"
            }

        # Appliquer le buffer
        from datetime import timedelta
        if buffer_minutes > 0:
            new_start = new_start - timedelta(minutes=buffer_minutes)
            new_end = new_end + timedelta(minutes=buffer_minutes)

        for idx, booking in enumerate(existing_bookings):
            booking_start = _parse_datetime(booking.get("start"))
            booking_end = _parse_datetime(booking.get("end"))
            booking_resource = booking.get("resource_id")
            booking_id = booking.get("id", f"booking_{idx}")

            if booking_start is None or booking_end is None:
                continue

            # Si check_resource, ne comparer que les mêmes ressources
            if check_resource and new_resource and booking_resource:
                if new_resource != booking_resource:
                    continue

            # Vérifier le chevauchement
            if _intervals_overlap(new_start, new_end, booking_start, booking_end):
                # Si allow_adjacent, les créneaux qui se touchent exactement ne sont pas un chevauchement
                if allow_adjacent and (new_end == booking_start or new_start == booking_end):
                    continue

                overlap_mins = _get_overlap_minutes(new_start, new_end, booking_start, booking_end)
                total_overlap_minutes += overlap_mins

                overlapping_bookings.append({
                    "new_booking": new_booking,
                    "existing_booking": booking
                })

                overlap_details.append({
                    "existing_booking_id": booking_id,
                    "existing_start": booking_start.isoformat(),
                    "existing_end": booking_end.isoformat(),
                    "overlap_minutes": overlap_mins,
                    "resource_id": booking_resource
                })

    # Mode 2: Vérifier les chevauchements mutuels dans une liste
    elif bookings:
        from datetime import timedelta

        parsed_bookings = []
        for idx, booking in enumerate(bookings):
            start = _parse_datetime(booking.get("start"))
            end = _parse_datetime(booking.get("end"))
            if start and end:
                parsed_bookings.append({
                    "index": idx,
                    "id": booking.get("id", f"booking_{idx}"),
                    "start": start,
                    "end": end,
                    "resource_id": booking.get("resource_id"),
                    "original": booking
                })

        # Comparer chaque paire
        for i in range(len(parsed_bookings)):
            for j in range(i + 1, len(parsed_bookings)):
                b1 = parsed_bookings[i]
                b2 = parsed_bookings[j]

                # Si check_resource, ne comparer que les mêmes ressources
                if check_resource and b1["resource_id"] and b2["resource_id"]:
                    if b1["resource_id"] != b2["resource_id"]:
                        continue

                start1 = b1["start"]
                end1 = b1["end"]
                start2 = b2["start"]
                end2 = b2["end"]

                # Appliquer le buffer
                if buffer_minutes > 0:
                    start1 = start1 - timedelta(minutes=buffer_minutes)
                    end1 = end1 + timedelta(minutes=buffer_minutes)

                if _intervals_overlap(start1, end1, start2, end2):
                    # Si allow_adjacent
                    if allow_adjacent and (end1 == start2 or start1 == end2):
                        continue

                    overlap_mins = _get_overlap_minutes(
                        b1["start"], b1["end"], b2["start"], b2["end"]
                    )
                    total_overlap_minutes += overlap_mins

                    overlapping_bookings.append({
                        "booking_1": b1["original"],
                        "booking_2": b2["original"]
                    })

                    overlap_details.append({
                        "booking_1_id": b1["id"],
                        "booking_2_id": b2["id"],
                        "overlap_minutes": overlap_mins,
                        "resource_id": b1["resource_id"] or b2["resource_id"]
                    })

    else:
        return {
            "is_valid": False,
            "has_overlap": None,
            "overlapping_bookings": [],
            "overlap_details": [],
            "total_overlap_minutes": 0,
            "error": "Aucune réservation à vérifier (new_booking ou bookings requis)"
        }

    has_overlap = len(overlapping_bookings) > 0

    if has_overlap:
        if len(overlapping_bookings) == 1:
            error_msg = "Chevauchement détecté avec une réservation existante"
        else:
            error_msg = f"Chevauchement détecté avec {len(overlapping_bookings)} réservations"
    else:
        error_msg = None

    return {
        "is_valid": not has_overlap,
        "has_overlap": has_overlap,
        "overlapping_bookings": overlapping_bookings,
        "overlap_details": overlap_details,
        "total_overlap_minutes": total_overlap_minutes,
        "error": error_msg
    }
