"""
AZALSCORE - Data Import/Export Validators
Validateurs pour les champs d'import
"""
from __future__ import annotations

import re
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional

from .types import ValidationError, ValidationSeverity


class FieldValidator:
    """Validateur de champs"""

    @staticmethod
    def validate_required(value: Any, field_name: str) -> Optional[ValidationError]:
        """Valide qu'un champ est renseigné"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return ValidationError(
                row_number=0,
                field=field_name,
                value=value,
                message=f"Le champ '{field_name}' est obligatoire",
                severity=ValidationSeverity.ERROR,
                error_code="REQUIRED_FIELD"
            )
        return None

    @staticmethod
    def validate_type(value: Any, expected_type: str, field_name: str) -> Optional[ValidationError]:
        """Valide le type d'un champ"""
        type_validators = {
            "string": lambda v: isinstance(v, str) or v is None,
            "integer": lambda v: FieldValidator._is_valid_integer(v),
            "decimal": lambda v: FieldValidator._is_valid_decimal(v),
            "date": lambda v: FieldValidator._is_valid_date(v),
            "datetime": lambda v: FieldValidator._is_valid_datetime(v),
            "boolean": lambda v: FieldValidator._is_valid_boolean(v),
            "email": lambda v: FieldValidator._is_valid_email(v),
            "siren": lambda v: FieldValidator._is_valid_siren(v),
            "siret": lambda v: FieldValidator._is_valid_siret(v),
            "iban": lambda v: FieldValidator._is_valid_iban(v),
        }

        validator = type_validators.get(expected_type)
        if validator and not validator(value):
            return ValidationError(
                row_number=0,
                field=field_name,
                value=value,
                message=f"Le champ '{field_name}' doit être de type {expected_type}",
                severity=ValidationSeverity.ERROR,
                error_code="INVALID_TYPE"
            )
        return None

    @staticmethod
    def validate_length(value: Any, min_len: int, max_len: int, field_name: str) -> Optional[ValidationError]:
        """Valide la longueur d'un champ"""
        if value is None:
            return None
        str_value = str(value)
        if len(str_value) < min_len or len(str_value) > max_len:
            return ValidationError(
                row_number=0,
                field=field_name,
                value=value,
                message=f"Le champ '{field_name}' doit avoir entre {min_len} et {max_len} caractères",
                severity=ValidationSeverity.ERROR,
                error_code="INVALID_LENGTH"
            )
        return None

    @staticmethod
    def validate_pattern(value: Any, pattern: str, field_name: str) -> Optional[ValidationError]:
        """Valide un champ contre une expression régulière"""
        if value is None:
            return None
        if not re.match(pattern, str(value)):
            return ValidationError(
                row_number=0,
                field=field_name,
                value=value,
                message=f"Le champ '{field_name}' ne correspond pas au format attendu",
                severity=ValidationSeverity.ERROR,
                error_code="INVALID_PATTERN"
            )
        return None

    @staticmethod
    def validate_range(value: Any, min_val: Any, max_val: Any, field_name: str) -> Optional[ValidationError]:
        """Valide qu'une valeur est dans une plage"""
        if value is None:
            return None
        try:
            num_value = Decimal(str(value))
            if min_val is not None and num_value < Decimal(str(min_val)):
                return ValidationError(
                    row_number=0,
                    field=field_name,
                    value=value,
                    message=f"Le champ '{field_name}' doit être >= {min_val}",
                    severity=ValidationSeverity.ERROR,
                    error_code="VALUE_TOO_LOW"
                )
            if max_val is not None and num_value > Decimal(str(max_val)):
                return ValidationError(
                    row_number=0,
                    field=field_name,
                    value=value,
                    message=f"Le champ '{field_name}' doit être <= {max_val}",
                    severity=ValidationSeverity.ERROR,
                    error_code="VALUE_TOO_HIGH"
                )
        except (ValueError, TypeError):
            pass
        return None

    @staticmethod
    def validate_enum(value: Any, allowed_values: list, field_name: str) -> Optional[ValidationError]:
        """Valide qu'une valeur est dans une liste autorisée"""
        if value is None:
            return None
        if value not in allowed_values:
            return ValidationError(
                row_number=0,
                field=field_name,
                value=value,
                message=f"Le champ '{field_name}' doit être l'une des valeurs: {', '.join(map(str, allowed_values))}",
                severity=ValidationSeverity.ERROR,
                error_code="INVALID_ENUM_VALUE"
            )
        return None

    # ========================================================================
    # Private validation methods
    # ========================================================================

    @staticmethod
    def _is_valid_integer(value: Any) -> bool:
        if value is None or value == "":
            return True
        try:
            int(str(value).replace(" ", ""))
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _is_valid_decimal(value: Any) -> bool:
        if value is None or value == "":
            return True
        try:
            Decimal(str(value).replace(" ", "").replace(",", "."))
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _is_valid_date(value: Any) -> bool:
        if value is None or value == "":
            return True
        if isinstance(value, (date, datetime)):
            return True
        date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y%m%d"]
        for fmt in date_formats:
            try:
                datetime.strptime(str(value), fmt)
                return True
            except ValueError:
                continue
        return False

    @staticmethod
    def _is_valid_datetime(value: Any) -> bool:
        if value is None or value == "":
            return True
        if isinstance(value, datetime):
            return True
        datetime_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d/%m/%Y %H:%M:%S",
        ]
        for fmt in datetime_formats:
            try:
                datetime.strptime(str(value), fmt)
                return True
            except ValueError:
                continue
        return False

    @staticmethod
    def _is_valid_boolean(value: Any) -> bool:
        if value is None or value == "":
            return True
        if isinstance(value, bool):
            return True
        return str(value).lower() in ("true", "false", "1", "0", "oui", "non", "yes", "no")

    @staticmethod
    def _is_valid_email(value: Any) -> bool:
        if value is None or value == "":
            return True
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, str(value)))

    @staticmethod
    def _is_valid_siren(value: Any) -> bool:
        if value is None or value == "":
            return True
        siren = str(value).replace(" ", "")
        if len(siren) != 9 or not siren.isdigit():
            return False
        return FieldValidator._luhn_check(siren)

    @staticmethod
    def _is_valid_siret(value: Any) -> bool:
        if value is None or value == "":
            return True
        siret = str(value).replace(" ", "")
        if len(siret) != 14 or not siret.isdigit():
            return False
        return FieldValidator._luhn_check(siret)

    @staticmethod
    def _is_valid_iban(value: Any) -> bool:
        if value is None or value == "":
            return True
        iban = str(value).replace(" ", "").upper()
        if len(iban) < 15 or len(iban) > 34:
            return False
        if not iban[:2].isalpha() or not iban[2:4].isdigit():
            return False
        rearranged = iban[4:] + iban[:4]
        numeric = ""
        for char in rearranged:
            if char.isdigit():
                numeric += char
            else:
                numeric += str(ord(char) - 55)
        return int(numeric) % 97 == 1

    @staticmethod
    def _luhn_check(number: str) -> bool:
        """Vérifie la clé de Luhn (SIREN/SIRET)"""
        total = 0
        for i, char in enumerate(reversed(number)):
            digit = int(char)
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit
        return total % 10 == 0
