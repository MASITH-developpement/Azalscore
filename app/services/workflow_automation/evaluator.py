"""
AZALSCORE - Workflow Automation Condition Evaluator
Évaluation des conditions et expressions
"""
from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from .types import Condition, ConditionGroup, ConditionOperator


class ConditionEvaluator:
    """Évaluateur de conditions"""

    @staticmethod
    def evaluate(condition: Condition, variables: dict) -> bool:
        """Évalue une condition."""
        field_value = ConditionEvaluator._get_field_value(condition.field, variables)
        target_value = condition.value

        if isinstance(target_value, str):
            for var_name, var_value in variables.items():
                target_value = target_value.replace(f"${{{var_name}}}", str(var_value))

        operators = {
            ConditionOperator.EQUALS: lambda a, b: a == b,
            ConditionOperator.NOT_EQUALS: lambda a, b: a != b,
            ConditionOperator.GREATER_THAN: lambda a, b: ConditionEvaluator._compare(a, b) > 0,
            ConditionOperator.GREATER_OR_EQUAL: lambda a, b: ConditionEvaluator._compare(a, b) >= 0,
            ConditionOperator.LESS_THAN: lambda a, b: ConditionEvaluator._compare(a, b) < 0,
            ConditionOperator.LESS_OR_EQUAL: lambda a, b: ConditionEvaluator._compare(a, b) <= 0,
            ConditionOperator.CONTAINS: lambda a, b: str(b) in str(a) if a else False,
            ConditionOperator.NOT_CONTAINS: lambda a, b: str(b) not in str(a) if a else True,
            ConditionOperator.STARTS_WITH: lambda a, b: str(a).startswith(str(b)) if a else False,
            ConditionOperator.ENDS_WITH: lambda a, b: str(a).endswith(str(b)) if a else False,
            ConditionOperator.IS_EMPTY: lambda a, b: a is None or a == "" or a == [],
            ConditionOperator.IS_NOT_EMPTY: lambda a, b: a is not None and a != "" and a != [],
            ConditionOperator.IN_LIST: lambda a, b: a in (b if isinstance(b, list) else [b]),
            ConditionOperator.NOT_IN_LIST: lambda a, b: a not in (b if isinstance(b, list) else [b]),
            ConditionOperator.MATCHES_REGEX: lambda a, b: bool(re.match(str(b), str(a))) if a else False,
        }

        op_func = operators.get(condition.operator)
        if op_func:
            return op_func(field_value, target_value)
        return False

    @staticmethod
    def evaluate_group(group: ConditionGroup, variables: dict) -> bool:
        """Évalue un groupe de conditions."""
        results = [ConditionEvaluator.evaluate(c, variables) for c in group.conditions]

        if group.logical_operator == "OR":
            return any(results)
        return all(results)

    @staticmethod
    def _get_field_value(field_path: str, variables: dict) -> Any:
        """Récupère la valeur d'un champ par son chemin."""
        parts = field_path.split(".")
        value = variables

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    @staticmethod
    def _compare(a: Any, b: Any) -> int:
        """Compare deux valeurs."""
        try:
            a_num = Decimal(str(a)) if a else Decimal(0)
            b_num = Decimal(str(b)) if b else Decimal(0)
            if a_num > b_num:
                return 1
            elif a_num < b_num:
                return -1
            return 0
        except (ValueError, TypeError):
            a_str = str(a) if a else ""
            b_str = str(b) if b else ""
            if a_str > b_str:
                return 1
            elif a_str < b_str:
                return -1
            return 0
