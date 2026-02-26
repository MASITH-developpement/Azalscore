"""
AZALSCORE - Workflow Automation Variable Handlers
Handlers pour la gestion des variables et expressions
"""
from __future__ import annotations

import ast
import logging
import operator
from typing import Any, Optional

from ..types import ActionConfig
from .base import ActionHandler

logger = logging.getLogger(__name__)


class SafeExpressionEvaluator:
    """
    Évaluateur d'expressions sécurisé.
    Remplace eval() avec une approche whitelist stricte.
    Supporte: opérations arithmétiques, comparaisons, accès dict/list.
    """

    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.And: lambda a, b: a and b,
        ast.Or: lambda a, b: a or b,
        ast.Not: operator.not_,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    SAFE_FUNCTIONS = {
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "round": round,
        "lower": lambda s: s.lower() if isinstance(s, str) else s,
        "upper": lambda s: s.upper() if isinstance(s, str) else s,
    }

    def __init__(self, variables: dict, context: dict):
        self.variables = variables
        self.context = context

    def evaluate(self, expression: str) -> Any:
        """Évalue une expression de manière sécurisée."""
        try:
            tree = ast.parse(expression, mode='eval')
            return self._eval_node(tree.body)
        except (SyntaxError, ValueError, TypeError, KeyError) as e:
            raise ValueError(f"Expression invalide: {e}")

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Num):  # Python 3.7 compat
            return node.n

        if isinstance(node, ast.Str):  # Python 3.7 compat
            return node.s

        if isinstance(node, ast.Name):
            name = node.id
            if name == "variables":
                return self.variables
            if name == "context":
                return self.context
            if name in self.variables:
                return self.variables[name]
            if name in self.context:
                return self.context[name]
            if name in self.SAFE_FUNCTIONS:
                return self.SAFE_FUNCTIONS[name]
            raise ValueError(f"Variable non définie: {name}")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self.SAFE_OPERATORS:
                raise ValueError(f"Opérateur non autorisé: {op_type.__name__}")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self.SAFE_OPERATORS[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self.SAFE_OPERATORS:
                raise ValueError(f"Opérateur non autorisé: {op_type.__name__}")
            operand = self._eval_node(node.operand)
            return self.SAFE_OPERATORS[op_type](operand)

        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                op_type = type(op)
                if op_type not in self.SAFE_OPERATORS:
                    raise ValueError(f"Opérateur non autorisé: {op_type.__name__}")
                right = self._eval_node(comparator)
                if not self.SAFE_OPERATORS[op_type](left, right):
                    return False
                left = right
            return True

        if isinstance(node, ast.BoolOp):
            op_type = type(node.op)
            if op_type not in self.SAFE_OPERATORS:
                raise ValueError(f"Opérateur non autorisé: {op_type.__name__}")
            values = [self._eval_node(v) for v in node.values]
            if op_type == ast.And:
                return all(values)
            return any(values)

        if isinstance(node, ast.IfExp):
            test = self._eval_node(node.test)
            return self._eval_node(node.body) if test else self._eval_node(node.orelse)

        if isinstance(node, ast.Subscript):
            value = self._eval_node(node.value)
            if isinstance(node.slice, ast.Index):  # Python 3.8 compat
                index = self._eval_node(node.slice.value)
            else:
                index = self._eval_node(node.slice)
            return value[index]

        if isinstance(node, ast.Attribute):
            value = self._eval_node(node.value)
            attr = node.attr
            if isinstance(value, dict) and attr in value:
                return value[attr]
            if hasattr(value, attr) and not attr.startswith('_'):
                return getattr(value, attr)
            raise ValueError(f"Attribut non autorisé: {attr}")

        if isinstance(node, ast.Call):
            func = self._eval_node(node.func)
            if func not in self.SAFE_FUNCTIONS.values():
                raise ValueError("Appel de fonction non autorisé")
            args = [self._eval_node(arg) for arg in node.args]
            return func(*args)

        if isinstance(node, ast.List):
            return [self._eval_node(elt) for elt in node.elts]

        if isinstance(node, ast.Dict):
            return {
                self._eval_node(k): self._eval_node(v)
                for k, v in zip(node.keys, node.values)
            }

        raise ValueError(f"Expression non supportée: {type(node).__name__}")


class SetVariableHandler(ActionHandler):
    """Handler pour définir des variables"""

    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        params = action.parameters
        var_name = params.get("name")
        var_value = self._resolve_value(params.get("value"), variables)
        expression = params.get("expression")

        if expression:
            try:
                # Utilise SafeExpressionEvaluator au lieu de eval() (B307 fix)
                evaluator = SafeExpressionEvaluator(variables, context)
                var_value = evaluator.evaluate(expression)
            except Exception as e:
                return None, f"Erreur expression: {str(e)}"

        variables[var_name] = var_value
        return {"variable": var_name, "value": var_value}, None
