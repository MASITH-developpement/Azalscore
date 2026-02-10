"""
AZALS - Safe Expression Evaluator
==================================
Evaluateur d'expressions securise pour conditions declaratives.
Remplace eval() avec un parser qui n'accepte que les comparaisons.

SECURITE P1-1:
- Aucune execution de code arbitraire
- Whitelist d'operateurs autorises
- Pas d'acces aux builtins Python
"""

import ast
import operator
import re
from typing import Any, Union

import logging

logger = logging.getLogger(__name__)


class SafeExpressionError(Exception):
    """Erreur lors de l'evaluation securisee."""
    pass


# Operateurs autorises (whitelist)
SAFE_OPERATORS = {
    # Comparaisons
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    # Booleens
    ast.And: lambda a, b: a and b,
    ast.Or: lambda a, b: a or b,
    ast.Not: operator.not_,
    # Arithmetique basique (pour calculs dans conditions)
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    # Unaires
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Types de valeurs autorisees
SAFE_VALUE_TYPES = (int, float, str, bool, type(None), list, dict)


class SafeExpressionEvaluator:
    """
    Evaluateur d'expressions securise.

    Supporte uniquement:
    - Comparaisons: ==, !=, <, <=, >, >=
    - Booleens: and, or, not
    - Arithmetique: +, -, *, /, %
    - Litteraux: nombres, strings, True, False, None
    - Listes et dicts litteraux

    Usage:
        evaluator = SafeExpressionEvaluator()
        result = evaluator.evaluate("0.15 < 0.2")  # True
        result = evaluator.evaluate("'active' == 'active'")  # True
    """

    def __init__(self, max_expression_length: int = 500):
        """
        Args:
            max_expression_length: Longueur max de l'expression (DoS protection)
        """
        self.max_length = max_expression_length

    def evaluate(self, expression: str, variables: dict = None) -> Any:
        """
        Evalue une expression de maniere securisee.

        Args:
            expression: Expression a evaluer (ex: "0.15 < 0.2")
            variables: Variables disponibles (non utilise pour l'instant)

        Returns:
            Resultat de l'evaluation

        Raises:
            SafeExpressionError: Si l'expression est invalide ou dangereuse
        """
        if not isinstance(expression, str):
            raise SafeExpressionError(f"Expression must be a string, got {type(expression)}")

        expression = expression.strip()

        if not expression:
            raise SafeExpressionError("Empty expression")

        if len(expression) > self.max_length:
            raise SafeExpressionError(
                f"Expression too long ({len(expression)} > {self.max_length})"
            )

        try:
            # Parser l'expression en AST
            tree = ast.parse(expression, mode='eval')

            # Evaluer de maniere securisee
            return self._eval_node(tree.body)

        except SyntaxError as e:
            raise SafeExpressionError(f"Syntax error in expression: {e}")
        except SafeExpressionError:
            raise
        except Exception as e:
            raise SafeExpressionError(f"Evaluation error: {e}")

    def _eval_node(self, node: ast.AST) -> Any:
        """Evalue un noeud AST de maniere recursive et securisee."""

        # Litteraux
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, SAFE_VALUE_TYPES):
                raise SafeExpressionError(f"Unsafe value type: {type(node.value)}")
            return node.value

        # Compatibilite Python < 3.8
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Str):
            return node.s
        if isinstance(node, ast.NameConstant):
            return node.value

        # Listes
        if isinstance(node, ast.List):
            return [self._eval_node(elem) for elem in node.elts]

        # Tuples
        if isinstance(node, ast.Tuple):
            return tuple(self._eval_node(elem) for elem in node.elts)

        # Dicts
        if isinstance(node, ast.Dict):
            keys = [self._eval_node(k) if k else None for k in node.keys]
            values = [self._eval_node(v) for v in node.values]
            return dict(zip(keys, values))

        # Operations binaires (arithmetique)
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise SafeExpressionError(f"Unsafe binary operator: {op_type.__name__}")

            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return SAFE_OPERATORS[op_type](left, right)

        # Operations unaires
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise SafeExpressionError(f"Unsafe unary operator: {op_type.__name__}")

            operand = self._eval_node(node.operand)
            return SAFE_OPERATORS[op_type](operand)

        # Comparaisons
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left)

            for op, comparator in zip(node.ops, node.comparators):
                op_type = type(op)
                if op_type not in SAFE_OPERATORS:
                    raise SafeExpressionError(f"Unsafe comparison operator: {op_type.__name__}")

                right = self._eval_node(comparator)

                if not SAFE_OPERATORS[op_type](left, right):
                    return False

                left = right

            return True

        # Operations booleennes
        if isinstance(node, ast.BoolOp):
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise SafeExpressionError(f"Unsafe boolean operator: {op_type.__name__}")

            values = [self._eval_node(v) for v in node.values]

            if op_type == ast.And:
                return all(values)
            elif op_type == ast.Or:
                return any(values)

        # Expressions ternaires (x if cond else y)
        if isinstance(node, ast.IfExp):
            condition = self._eval_node(node.test)
            if condition:
                return self._eval_node(node.body)
            else:
                return self._eval_node(node.orelse)

        # Membership tests (in, not in)
        if isinstance(node, ast.Compare):
            for op in node.ops:
                if isinstance(op, (ast.In, ast.NotIn)):
                    left = self._eval_node(node.left)
                    right = self._eval_node(node.comparators[0])
                    if isinstance(op, ast.In):
                        return left in right
                    else:
                        return left not in right

        # Tout autre noeud est interdit
        raise SafeExpressionError(
            f"Unsafe AST node type: {type(node).__name__}. "
            f"Only comparisons, boolean ops, and literals are allowed."
        )


# Instance globale pour reutilisation
_evaluator = SafeExpressionEvaluator()


def safe_eval(expression: str) -> Any:
    """
    Fonction utilitaire pour evaluation securisee.

    Args:
        expression: Expression a evaluer

    Returns:
        Resultat de l'evaluation

    Raises:
        SafeExpressionError: Si l'expression est invalide

    Examples:
        >>> safe_eval("0.15 < 0.2")
        True
        >>> safe_eval("'active' == 'active'")
        True
        >>> safe_eval("10 + 5 > 12")
        True
        >>> safe_eval("True and False")
        False
    """
    return _evaluator.evaluate(expression)


def is_safe_expression(expression: str) -> bool:
    """
    Verifie si une expression est valide et securisee.

    Args:
        expression: Expression a verifier

    Returns:
        True si l'expression est valide et securisee
    """
    try:
        _evaluator.evaluate(expression)
        return True
    except SafeExpressionError:
        return False


__all__ = [
    'SafeExpressionEvaluator',
    'SafeExpressionError',
    'safe_eval',
    'is_safe_expression',
]
