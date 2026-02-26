"""
Implémentation du sous-programme : validate_json_schema

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 25+ endroits dans le codebase
"""

from typing import Dict, Any, List
import re


def _validate_type(value: Any, expected_type: str) -> tuple[bool, str]:
    """Valide le type d'une valeur."""
    type_mapping = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }

    if expected_type not in type_mapping:
        return True, ""  # Type inconnu, on accepte

    expected = type_mapping[expected_type]

    # Cas spécial: boolean peut être confondu avec int en Python
    if expected_type == "boolean" and isinstance(value, bool):
        return True, ""
    if expected_type == "integer" and isinstance(value, bool):
        return False, f"Attendu integer, reçu boolean"

    if not isinstance(value, expected):
        actual_type = type(value).__name__
        return False, f"Attendu {expected_type}, reçu {actual_type}"

    return True, ""


def _validate_string_constraints(value: str, schema: dict, path: str) -> List[str]:
    """Valide les contraintes sur une string."""
    errors = []

    if "minLength" in schema:
        if len(value) < schema["minLength"]:
            errors.append(f"{path}: longueur minimum {schema['minLength']}")

    if "maxLength" in schema:
        if len(value) > schema["maxLength"]:
            errors.append(f"{path}: longueur maximum {schema['maxLength']}")

    if "pattern" in schema:
        pattern = schema["pattern"]
        if not re.match(pattern, value):
            errors.append(f"{path}: ne correspond pas au pattern {pattern}")

    if "enum" in schema:
        if value not in schema["enum"]:
            errors.append(f"{path}: doit être parmi {schema['enum']}")

    return errors


def _validate_number_constraints(value, schema: dict, path: str) -> List[str]:
    """Valide les contraintes sur un nombre."""
    errors = []

    if "minimum" in schema:
        if value < schema["minimum"]:
            errors.append(f"{path}: minimum {schema['minimum']}")

    if "maximum" in schema:
        if value > schema["maximum"]:
            errors.append(f"{path}: maximum {schema['maximum']}")

    if "exclusiveMinimum" in schema:
        if value <= schema["exclusiveMinimum"]:
            errors.append(f"{path}: doit être > {schema['exclusiveMinimum']}")

    if "exclusiveMaximum" in schema:
        if value >= schema["exclusiveMaximum"]:
            errors.append(f"{path}: doit être < {schema['exclusiveMaximum']}")

    if "multipleOf" in schema:
        if value % schema["multipleOf"] != 0:
            errors.append(f"{path}: doit être multiple de {schema['multipleOf']}")

    return errors


def _validate_array_constraints(value: list, schema: dict, path: str) -> List[str]:
    """Valide les contraintes sur un array."""
    errors = []

    if "minItems" in schema:
        if len(value) < schema["minItems"]:
            errors.append(f"{path}: minimum {schema['minItems']} éléments")

    if "maxItems" in schema:
        if len(value) > schema["maxItems"]:
            errors.append(f"{path}: maximum {schema['maxItems']} éléments")

    if "uniqueItems" in schema and schema["uniqueItems"]:
        # Vérification d'unicité (pour types hashables)
        seen = []
        for item in value:
            if item in seen:
                errors.append(f"{path}: éléments doivent être uniques")
                break
            seen.append(item)

    # Validation des items
    if "items" in schema:
        items_schema = schema["items"]
        for i, item in enumerate(value):
            item_errors = _validate_value(item, items_schema, f"{path}[{i}]")
            errors.extend(item_errors)

    return errors


def _validate_object_constraints(value: dict, schema: dict, path: str) -> List[str]:
    """Valide les contraintes sur un object."""
    errors = []

    # Propriétés requises
    if "required" in schema:
        for prop in schema["required"]:
            if prop not in value:
                errors.append(f"{path}: propriété requise '{prop}' manquante")

    # Validation des propriétés
    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            if prop_name in value:
                prop_errors = _validate_value(value[prop_name], prop_schema, f"{path}.{prop_name}")
                errors.extend(prop_errors)

    # Propriétés additionnelles
    if "additionalProperties" in schema:
        if schema["additionalProperties"] is False:
            allowed_props = set(schema.get("properties", {}).keys())
            for prop in value.keys():
                if prop not in allowed_props:
                    errors.append(f"{path}: propriété non autorisée '{prop}'")

    return errors


def _validate_value(value: Any, schema: dict, path: str = "$") -> List[str]:
    """Valide une valeur contre un schéma."""
    errors = []

    if not isinstance(schema, dict):
        return errors

    # Validation du type
    if "type" in schema:
        expected_type = schema["type"]

        # Support des types multiples
        if isinstance(expected_type, list):
            type_valid = False
            for t in expected_type:
                is_valid, _ = _validate_type(value, t)
                if is_valid:
                    type_valid = True
                    break
            if not type_valid:
                errors.append(f"{path}: type doit être parmi {expected_type}")
        else:
            is_valid, error = _validate_type(value, expected_type)
            if not is_valid:
                errors.append(f"{path}: {error}")
                return errors  # Pas la peine de continuer si le type est mauvais

    # Contraintes selon le type
    if isinstance(value, str):
        errors.extend(_validate_string_constraints(value, schema, path))
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        errors.extend(_validate_number_constraints(value, schema, path))
    elif isinstance(value, list):
        errors.extend(_validate_array_constraints(value, schema, path))
    elif isinstance(value, dict):
        errors.extend(_validate_object_constraints(value, schema, path))

    # Enum (pour tous les types)
    if "enum" in schema and not isinstance(value, str):
        if value not in schema["enum"]:
            errors.append(f"{path}: doit être parmi {schema['enum']}")

    # Const
    if "const" in schema:
        if value != schema["const"]:
            errors.append(f"{path}: doit être égal à {schema['const']}")

    return errors


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide des données JSON contre un schéma JSON Schema.

    Supporte un sous-ensemble de JSON Schema Draft-07:
    - Types: string, number, integer, boolean, array, object, null
    - Contraintes string: minLength, maxLength, pattern, enum
    - Contraintes number: minimum, maximum, exclusiveMinimum, exclusiveMaximum
    - Contraintes array: minItems, maxItems, uniqueItems, items
    - Contraintes object: required, properties, additionalProperties

    Args:
        inputs: {
            "data": object,  # Données à valider
            "schema": object,  # Schéma JSON Schema
        }

    Returns:
        {
            "is_valid": boolean,  # True si données valides
            "errors": array,  # Liste des erreurs de validation
            "error_count": number,  # Nombre d'erreurs
        }
    """
    data = inputs.get("data")
    schema = inputs.get("schema")

    # Schéma requis
    if schema is None:
        return {
            "is_valid": False,
            "errors": ["Schéma requis"],
            "error_count": 1
        }

    if not isinstance(schema, dict):
        return {
            "is_valid": False,
            "errors": ["Schéma doit être un objet"],
            "error_count": 1
        }

    # Validation
    errors = _validate_value(data, schema)

    return {
        "is_valid": len(errors) == 0,
        "errors": errors if errors else None,
        "error_count": len(errors)
    }
