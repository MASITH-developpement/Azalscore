"""
AZALSCORE - Data Import/Export Transformers
Transformateurs pour les champs d'import
"""
from __future__ import annotations

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Any

from .types import TransformationType

logger = logging.getLogger(__name__)


class FieldTransformer:
    """Transformateur de champs"""

    @staticmethod
    def transform(value: Any, transformation: dict) -> Any:
        """Applique une transformation à une valeur"""
        transform_type = TransformationType(transformation.get("type", "trim"))

        transformers = {
            TransformationType.UPPERCASE: FieldTransformer._uppercase,
            TransformationType.LOWERCASE: FieldTransformer._lowercase,
            TransformationType.TRIM: FieldTransformer._trim,
            TransformationType.DATE_FORMAT: FieldTransformer._date_format,
            TransformationType.NUMBER_FORMAT: FieldTransformer._number_format,
            TransformationType.LOOKUP: FieldTransformer._lookup,
            TransformationType.CONCATENATE: FieldTransformer._concatenate,
            TransformationType.SPLIT: FieldTransformer._split,
            TransformationType.DEFAULT: FieldTransformer._default,
            TransformationType.CUSTOM: FieldTransformer._custom,
        }

        transformer = transformers.get(transform_type)
        if transformer:
            return transformer(value, transformation)
        return value

    @staticmethod
    def _uppercase(value: Any, params: dict) -> Any:
        return str(value).upper() if value else value

    @staticmethod
    def _lowercase(value: Any, params: dict) -> Any:
        return str(value).lower() if value else value

    @staticmethod
    def _trim(value: Any, params: dict) -> Any:
        return str(value).strip() if value else value

    @staticmethod
    def _date_format(value: Any, params: dict) -> Any:
        """Convertit une date d'un format à un autre"""
        if not value:
            return value

        input_format = params.get("input_format", "%d/%m/%Y")
        output_format = params.get("output_format", "%Y-%m-%d")

        if isinstance(value, (date, datetime)):
            return value.strftime(output_format)

        input_formats = [input_format, "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y%m%d"]
        for fmt in input_formats:
            try:
                parsed = datetime.strptime(str(value), fmt)
                return parsed.strftime(output_format)
            except ValueError:
                continue
        return value

    @staticmethod
    def _number_format(value: Any, params: dict) -> Any:
        """Formate un nombre"""
        if not value:
            return value

        decimal_separator = params.get("input_decimal", ",")
        thousands_separator = params.get("input_thousands", " ")
        output_decimal = params.get("output_decimal", ".")
        precision = params.get("precision")

        try:
            str_value = str(value)
            str_value = str_value.replace(thousands_separator, "")
            str_value = str_value.replace(decimal_separator, ".")
            num_value = Decimal(str_value)

            if precision is not None:
                num_value = round(num_value, precision)

            result = str(num_value)
            if output_decimal != ".":
                result = result.replace(".", output_decimal)

            return result
        except (ValueError, TypeError):
            return value

    @staticmethod
    def _lookup(value: Any, params: dict) -> Any:
        """Recherche une valeur dans une table de correspondance"""
        lookup_table = params.get("table", {})
        default = params.get("default")
        case_sensitive = params.get("case_sensitive", False)

        if not case_sensitive and value:
            value_lower = str(value).lower()
            for key, mapped_value in lookup_table.items():
                if str(key).lower() == value_lower:
                    return mapped_value
        else:
            if value in lookup_table:
                return lookup_table[value]

        return default if default is not None else value

    @staticmethod
    def _concatenate(value: Any, params: dict) -> Any:
        """Concatène avec d'autres valeurs"""
        prefix = params.get("prefix", "")
        suffix = params.get("suffix", "")
        return f"{prefix}{value or ''}{suffix}"

    @staticmethod
    def _split(value: Any, params: dict) -> Any:
        """Divise une valeur et retourne une partie"""
        if not value:
            return value

        separator = params.get("separator", ",")
        index = params.get("index", 0)

        parts = str(value).split(separator)
        if 0 <= index < len(parts):
            return parts[index].strip()
        return value

    @staticmethod
    def _default(value: Any, params: dict) -> Any:
        """Retourne une valeur par défaut si vide"""
        default_value = params.get("value")
        if value is None or (isinstance(value, str) and not value.strip()):
            return default_value
        return value

    @staticmethod
    def _custom(value: Any, params: dict) -> Any:
        """Transformation personnalisée via opérations prédéfinies sécurisées

        IMPORTANT: N'utilise PAS eval() pour des raisons de sécurité.
        Supporte uniquement des opérations prédéfinies et sûres.
        """
        operation = params.get("operation")
        if not operation:
            return value

        try:
            if operation == "substring":
                start = params.get("start", 0)
                end = params.get("end")
                if value and isinstance(value, str):
                    return value[start:end] if end else value[start:]

            elif operation == "pad_left":
                width = params.get("width", 0)
                char = params.get("char", " ")[:1] or " "
                return str(value or "").rjust(width, char)

            elif operation == "pad_right":
                width = params.get("width", 0)
                char = params.get("char", " ")[:1] or " "
                return str(value or "").ljust(width, char)

            elif operation == "replace_chars":
                old_char = params.get("old", "")
                new_char = params.get("new", "")
                if value and isinstance(value, str):
                    return value.replace(old_char, new_char)

            elif operation == "extract_digits":
                if value:
                    return "".join(c for c in str(value) if c.isdigit())

            elif operation == "extract_alpha":
                if value:
                    return "".join(c for c in str(value) if c.isalpha())

            elif operation == "format_phone":
                if value:
                    digits = "".join(c for c in str(value) if c.isdigit())
                    if len(digits) == 10:
                        return " ".join([digits[i:i+2] for i in range(0, 10, 2)])

            elif operation == "normalize_spaces":
                if value and isinstance(value, str):
                    return " ".join(value.split())

            else:
                logger.warning(f"Opération custom non reconnue: {operation}")

            return value
        except Exception as e:
            logger.warning(f"Erreur transformation custom: {e}")
            return value
