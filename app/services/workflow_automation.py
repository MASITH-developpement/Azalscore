"""
Service de Workflow Automation - AZALSCORE
Automatisation des processus métier avec workflows configurables
"""
from __future__ import annotations


import ast
import asyncio
import hashlib
import json
import logging
import operator
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, Callable, TypeVar, Generic, Union
from dataclasses import dataclass, field
from collections import defaultdict
import uuid
import re

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class WorkflowStatus(str, Enum):
    """Statut d'un workflow"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    """Statut d'exécution"""
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TriggerType(str, Enum):
    """Types de déclencheurs"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    WEBHOOK = "webhook"
    CONDITION = "condition"


class ActionType(str, Enum):
    """Types d'actions"""
    SEND_EMAIL = "send_email"
    SEND_NOTIFICATION = "send_notification"
    UPDATE_RECORD = "update_record"
    CREATE_RECORD = "create_record"
    HTTP_REQUEST = "http_request"
    EXECUTE_SCRIPT = "execute_script"
    APPROVAL = "approval"
    DELAY = "delay"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"
    SET_VARIABLE = "set_variable"
    LOG = "log"
    CALL_WORKFLOW = "call_workflow"


class ConditionOperator(str, Enum):
    """Opérateurs de condition"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_THAN = "less_than"
    LESS_OR_EQUAL = "less_or_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    MATCHES_REGEX = "matches_regex"


class ApprovalStatus(str, Enum):
    """Statut d'approbation"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class WorkflowVariable:
    """Variable de workflow"""
    name: str
    value: Any
    data_type: str = "string"
    is_input: bool = False
    is_output: bool = False
    description: str = ""


@dataclass
class Condition:
    """Condition d'évaluation"""
    field: str
    operator: ConditionOperator
    value: Any
    logical_operator: str = "AND"


@dataclass
class ConditionGroup:
    """Groupe de conditions"""
    conditions: list[Condition]
    logical_operator: str = "AND"


@dataclass
class TriggerConfig:
    """Configuration d'un déclencheur"""
    type: TriggerType
    event_name: Optional[str] = None
    schedule: Optional[str] = None
    conditions: Optional[ConditionGroup] = None
    webhook_secret: Optional[str] = None


@dataclass
class ActionConfig:
    """Configuration d'une action"""
    id: str
    type: ActionType
    name: str
    description: str = ""
    parameters: dict = field(default_factory=dict)
    timeout_seconds: int = 300
    retry_count: int = 0
    retry_delay_seconds: int = 60
    on_error: str = "fail"
    conditions: Optional[ConditionGroup] = None
    next_action_id: Optional[str] = None
    on_true_action_id: Optional[str] = None
    on_false_action_id: Optional[str] = None


@dataclass
class ApprovalConfig:
    """Configuration d'approbation"""
    approvers: list[str]
    approval_type: str = "any"
    min_approvals: int = 1
    escalation_timeout_hours: int = 24
    escalation_to: Optional[list[str]] = None
    reminder_hours: list[int] = field(default_factory=lambda: [4, 12])
    allow_delegation: bool = False
    require_comment: bool = False


@dataclass
class WorkflowDefinition:
    """Définition d'un workflow"""
    id: str
    name: str
    description: str
    version: int
    tenant_id: str
    entity_type: Optional[str]
    triggers: list[TriggerConfig]
    actions: list[ActionConfig]
    variables: list[WorkflowVariable] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ActionResult:
    """Résultat d'exécution d'une action"""
    action_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    output: Any = None
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class ApprovalRequest:
    """Demande d'approbation"""
    id: str
    execution_id: str
    action_id: str
    tenant_id: str
    approvers: list[str]
    approval_config: ApprovalConfig
    entity_type: str
    entity_id: str
    entity_data: dict
    status: ApprovalStatus
    created_at: datetime
    expires_at: datetime
    decisions: list[dict] = field(default_factory=list)
    comments: list[dict] = field(default_factory=list)
    escalation_count: int = 0


@dataclass
class WorkflowExecution:
    """Exécution d'un workflow"""
    id: str
    workflow_id: str
    workflow_version: int
    tenant_id: str
    trigger_type: TriggerType
    trigger_data: dict
    entity_type: Optional[str]
    entity_id: Optional[str]
    status: ExecutionStatus
    current_action_id: Optional[str]
    variables: dict
    action_results: list[ActionResult]
    started_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str] = None
    parent_execution_id: Optional[str] = None
    retry_count: int = 0


@dataclass
class ScheduledWorkflow:
    """Workflow planifié"""
    id: str
    workflow_id: str
    tenant_id: str
    schedule: str
    next_run_at: datetime
    last_run_at: Optional[datetime]
    last_run_status: Optional[ExecutionStatus]
    is_active: bool
    created_at: datetime
    input_variables: dict = field(default_factory=dict)


# ============================================================================
# Action Handlers
# ============================================================================

class ActionHandler(ABC):
    """Classe de base pour les handlers d'actions"""

    @abstractmethod
    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        """Exécute l'action et retourne (output, error)"""
        pass


class SendEmailHandler(ActionHandler):
    """Handler pour l'envoi d'emails"""

    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        params = action.parameters
        to = self._resolve_value(params.get("to"), variables)
        subject = self._resolve_value(params.get("subject"), variables)
        body = self._resolve_value(params.get("body"), variables)
        template_id = params.get("template_id")

        try:
            logger.info(f"Envoi email à {to}: {subject}")
            return {"sent_to": to, "subject": subject}, None
        except Exception as e:
            return None, str(e)

    def _resolve_value(self, value: Any, variables: dict) -> Any:
        """Résout les variables dans une valeur"""
        if isinstance(value, str):
            for var_name, var_value in variables.items():
                value = value.replace(f"${{{var_name}}}", str(var_value))
                value = value.replace(f"${{variables.{var_name}}}", str(var_value))
        return value


class SendNotificationHandler(ActionHandler):
    """Handler pour l'envoi de notifications"""

    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        params = action.parameters
        recipients = self._resolve_list(params.get("recipients", []), variables)
        title = self._resolve_value(params.get("title"), variables)
        message = self._resolve_value(params.get("message"), variables)
        channels = params.get("channels", ["in_app"])

        try:
            logger.info(f"Notification envoyée à {recipients}")
            return {"notified": recipients, "channels": channels}, None
        except Exception as e:
            return None, str(e)

    def _resolve_value(self, value: Any, variables: dict) -> Any:
        if isinstance(value, str):
            for var_name, var_value in variables.items():
                value = value.replace(f"${{{var_name}}}", str(var_value))
        return value

    def _resolve_list(self, value: list, variables: dict) -> list:
        return [self._resolve_value(v, variables) for v in value]


class UpdateRecordHandler(ActionHandler):
    """Handler pour la mise à jour d'enregistrements"""

    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        params = action.parameters
        entity_type = params.get("entity_type")
        entity_id = self._resolve_value(params.get("entity_id"), variables)
        updates = self._resolve_dict(params.get("updates", {}), variables)

        try:
            logger.info(f"Mise à jour {entity_type}/{entity_id}: {updates}")
            return {"entity_type": entity_type, "entity_id": entity_id, "updates": updates}, None
        except Exception as e:
            return None, str(e)

    def _resolve_value(self, value: Any, variables: dict) -> Any:
        if isinstance(value, str):
            for var_name, var_value in variables.items():
                value = value.replace(f"${{{var_name}}}", str(var_value))
        return value

    def _resolve_dict(self, d: dict, variables: dict) -> dict:
        return {k: self._resolve_value(v, variables) for k, v in d.items()}


class CreateRecordHandler(ActionHandler):
    """Handler pour la création d'enregistrements"""

    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        params = action.parameters
        entity_type = params.get("entity_type")
        data = self._resolve_dict(params.get("data", {}), variables)

        try:
            record_id = str(uuid.uuid4())
            logger.info(f"Création {entity_type}: {record_id}")
            return {"entity_type": entity_type, "record_id": record_id, "data": data}, None
        except Exception as e:
            return None, str(e)

    def _resolve_dict(self, d: dict, variables: dict) -> dict:
        result = {}
        for k, v in d.items():
            if isinstance(v, str):
                for var_name, var_value in variables.items():
                    v = v.replace(f"${{{var_name}}}", str(var_value))
            result[k] = v
        return result


class HttpRequestHandler(ActionHandler):
    """Handler pour les requêtes HTTP avec protection SSRF"""

    # Liste des hôtes/réseaux interdits (SSRF protection)
    # nosec B104 - Ce sont des hôtes BLOQUÉS, pas des bindings
    BLOCKED_HOSTS = {
        "localhost", "127.0.0.1", "0.0.0.0", "::1",  # nosec B104
        "metadata.google.internal", "169.254.169.254",  # Cloud metadata
    }

    BLOCKED_NETWORKS = [
        "10.", "172.16.", "172.17.", "172.18.", "172.19.",
        "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
        "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
        "172.30.", "172.31.", "192.168.",  # Réseaux privés
    ]

    def _is_safe_url(self, url: str) -> tuple[bool, str]:
        """Vérifie si l'URL est sûre (protection SSRF)"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)

            # Vérifier le schéma
            if parsed.scheme not in ("http", "https"):
                return False, f"Schéma non autorisé: {parsed.scheme}"

            # Vérifier l'hôte
            host = parsed.hostname or ""
            host_lower = host.lower()

            if host_lower in self.BLOCKED_HOSTS:
                return False, f"Hôte bloqué: {host}"

            # Vérifier les réseaux privés
            for network in self.BLOCKED_NETWORKS:
                if host.startswith(network):
                    return False, f"Réseau privé non autorisé: {host}"

            # Vérifier les adresses IPv6 locales
            if host.startswith("[") and ("::1" in host or "fe80:" in host.lower()):
                return False, f"Adresse IPv6 locale non autorisée: {host}"

            return True, ""
        except Exception as e:
            return False, f"URL invalide: {str(e)}"

    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        params = action.parameters
        method = params.get("method", "GET")
        url = self._resolve_value(params.get("url"), variables)
        headers = self._resolve_dict(params.get("headers", {}), variables)
        body = self._resolve_value(params.get("body"), variables)
        timeout = min(params.get("timeout", 30), 60)  # Max 60 secondes

        # Validation SSRF
        is_safe, error_msg = self._is_safe_url(url)
        if not is_safe:
            logger.warning(f"Requête HTTP bloquée (SSRF): {url} - {error_msg}")
            return None, f"URL non autorisée: {error_msg}"

        # Valider la méthode HTTP
        allowed_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
        if method.upper() not in allowed_methods:
            return None, f"Méthode HTTP non autorisée: {method}"

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=body if isinstance(body, dict) else None,
                    data=body if isinstance(body, str) else None,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=False  # Pas de redirections automatiques (sécurité)
                ) as response:
                    # Limiter la taille de la réponse (1 Mo max)
                    max_size = 1024 * 1024
                    response_body = await response.text()
                    if len(response_body) > max_size:
                        response_body = response_body[:max_size] + "... [tronqué]"

                    try:
                        response_json = json.loads(response_body)
                    except json.JSONDecodeError:
                        response_json = None

                    return {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "body": response_json or response_body
                    }, None if response.status < 400 else f"HTTP {response.status}"

        except ImportError:
            logger.warning("aiohttp non disponible, simulation de requête HTTP")
            return {"status_code": 200, "body": {}}, None
        except asyncio.TimeoutError:
            return None, "Timeout de la requête HTTP"
        except Exception as e:
            logger.exception(f"Erreur requête HTTP: {e}")
            return None, str(e)

    def _resolve_value(self, value: Any, variables: dict) -> Any:
        if isinstance(value, str):
            for var_name, var_value in variables.items():
                value = value.replace(f"${{{var_name}}}", str(var_value))
        return value

    def _resolve_dict(self, d: dict, variables: dict) -> dict:
        return {k: self._resolve_value(v, variables) for k, v in d.items()}


class ExecuteScriptHandler(ActionHandler):
    """
    Handler pour l'exécution de scripts Python sécurisés.

    SÉCURITÉ (bandit B102 - exec):
    L'utilisation de exec() est intentionnelle pour les workflows.
    Mesures de sécurité appliquées:
    1. SAFE_BUILTINS: Seules les fonctions sûres sont disponibles
    2. FORBIDDEN_KEYWORDS: Mots-clés dangereux bloqués
    3. Validation AST: Analyse syntaxique pour bloquer les patterns dangereux
    4. Double-underscore bloqué: Pas d'accès aux attributs spéciaux
    5. Taille limitée: MAX_SCRIPT_SIZE caractères maximum
    6. Isolation: Variables copiées, pas d'accès au contexte global
    """

    # Builtins sûrs autorisés - Liste blanche stricte
    SAFE_BUILTINS = {
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "dict": dict,
        "float": float,
        "int": int,
        "len": len,
        "list": list,
        "max": max,
        "min": min,
        "round": round,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "zip": zip,
        "range": range,
        "enumerate": enumerate,
        "True": True,
        "False": False,
        "None": None,
    }

    # Mots-clés dangereux interdits - Liste noire extensive
    FORBIDDEN_KEYWORDS = {
        # Exécution de code
        "import", "exec", "eval", "compile", "open", "file",
        # Introspection dangereuse
        "__import__", "__builtins__", "__class__", "__bases__",
        "__subclasses__", "__mro__", "__globals__", "__code__",
        "__dict__", "__module__", "__name__", "__qualname__",
        # Accès aux attributs
        "getattr", "setattr", "delattr", "hasattr",
        "globals", "locals", "vars", "dir",
        # Types dangereux
        "type", "object", "super", "classmethod", "staticmethod",
        # Modules système
        "os", "sys", "subprocess", "shutil", "socket", "pickle",
        "marshal", "ctypes", "multiprocessing", "threading",
        # Fichiers et I/O
        "input", "print", "breakpoint", "exit", "quit",
    }

    # Taille maximale du script (caractères)
    MAX_SCRIPT_SIZE = 10000

    def _validate_script(self, script: str) -> tuple[bool, str]:
        """
        Valide le script avant exécution avec validation AST.

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        import ast

        if not script or not script.strip():
            return False, "Script vide"

        if len(script) > self.MAX_SCRIPT_SIZE:
            return False, f"Script trop long (max {self.MAX_SCRIPT_SIZE} caractères)"

        # Vérifier les caractères nuls et encoding tricks
        if "\x00" in script or "\\" + "x" in script:
            return False, "Caractères invalides détectés"

        # Vérifier les mots-clés interdits
        script_lower = script.lower()
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in script_lower:
                return False, f"Mot-clé interdit: {keyword}"

        # Vérifier les tentatives d'accès aux attributs sensibles
        if "__" in script:
            return False, "Accès aux attributs spéciaux interdit"

        # Validation AST - Parse et vérifie la syntaxe
        try:
            tree = ast.parse(script, mode='exec')
        except SyntaxError as e:
            return False, f"Erreur de syntaxe: {e}"

        # Vérifier les nodes AST dangereux
        for node in ast.walk(tree):
            # Bloquer les imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return False, "Import interdit"
            # Bloquer les appels à des fonctions interdites
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.FORBIDDEN_KEYWORDS:
                        return False, f"Appel interdit: {node.func.id}"
            # Bloquer l'accès aux attributs avec __
            if isinstance(node, ast.Attribute):
                if node.attr.startswith("_"):
                    return False, f"Accès attribut privé interdit: {node.attr}"

        return True, ""

    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        params = action.parameters
        script = params.get("script", "")

        # Validation du script
        is_valid, error_msg = self._validate_script(script)
        if not is_valid:
            logger.warning(f"Script rejeté: {error_msg}")
            return None, f"Script invalide: {error_msg}"

        try:
            local_vars = {
                "variables": dict(variables),  # Copie pour isolation
                "context": dict(context),
                "result": None
            }

            # Exécution sandbox - voir docstring classe pour mesures sécurité
            exec(  # nosec B102 - Sandbox: SAFE_BUILTINS + FORBIDDEN_KEYWORDS + AST validation
                script,
                {"__builtins__": self.SAFE_BUILTINS},
                local_vars
            )

            return local_vars.get("result"), None
        except SyntaxError as e:
            return None, f"Erreur de syntaxe: {str(e)}"
        except Exception as e:
            logger.warning(f"Erreur exécution script: {e}")
            return None, f"Erreur script: {str(e)}"


class DelayHandler(ActionHandler):
    """Handler pour les délais"""

    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        params = action.parameters
        delay_seconds = params.get("delay_seconds", 0)
        delay_until = params.get("delay_until")

        if delay_until:
            target_time = datetime.fromisoformat(delay_until)
            delay_seconds = (target_time - datetime.utcnow()).total_seconds()
            delay_seconds = max(0, delay_seconds)

        await asyncio.sleep(min(delay_seconds, 300))

        return {"delayed_seconds": delay_seconds}, None


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

    def _resolve_value(self, value: Any, variables: dict) -> Any:
        if isinstance(value, str):
            for var_name, var_value in variables.items():
                value = value.replace(f"${{{var_name}}}", str(var_value))
        return value


class LogHandler(ActionHandler):
    """Handler pour la journalisation"""

    async def execute(
        self,
        action: ActionConfig,
        context: dict,
        variables: dict
    ) -> tuple[Any, Optional[str]]:
        params = action.parameters
        level = params.get("level", "INFO")
        message = self._resolve_value(params.get("message", ""), variables)

        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[Workflow] {message}")

        return {"logged": message, "level": level}, None

    def _resolve_value(self, value: Any, variables: dict) -> Any:
        if isinstance(value, str):
            for var_name, var_value in variables.items():
                value = value.replace(f"${{{var_name}}}", str(var_value))
        return value


# ============================================================================
# Condition Evaluator
# ============================================================================

class ConditionEvaluator:
    """Évaluateur de conditions"""

    @staticmethod
    def evaluate(condition: Condition, variables: dict) -> bool:
        """Évalue une condition"""
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
        """Évalue un groupe de conditions"""
        results = [ConditionEvaluator.evaluate(c, variables) for c in group.conditions]

        if group.logical_operator == "OR":
            return any(results)
        return all(results)

    @staticmethod
    def _get_field_value(field_path: str, variables: dict) -> Any:
        """Récupère la valeur d'un champ par son chemin"""
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
        """Compare deux valeurs"""
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


# ============================================================================
# Workflow Engine
# ============================================================================

class WorkflowEngine:
    """Moteur d'exécution de workflows"""

    def __init__(self):
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._executions: dict[str, WorkflowExecution] = {}
        self._approval_requests: dict[str, ApprovalRequest] = {}
        self._scheduled_workflows: dict[str, ScheduledWorkflow] = {}
        self._event_subscriptions: dict[str, list[str]] = defaultdict(list)

        self._action_handlers: dict[ActionType, ActionHandler] = {
            ActionType.SEND_EMAIL: SendEmailHandler(),
            ActionType.SEND_NOTIFICATION: SendNotificationHandler(),
            ActionType.UPDATE_RECORD: UpdateRecordHandler(),
            ActionType.CREATE_RECORD: CreateRecordHandler(),
            ActionType.HTTP_REQUEST: HttpRequestHandler(),
            ActionType.EXECUTE_SCRIPT: ExecuteScriptHandler(),
            ActionType.DELAY: DelayHandler(),
            ActionType.SET_VARIABLE: SetVariableHandler(),
            ActionType.LOG: LogHandler(),
        }

        self._custom_handlers: dict[str, Callable] = {}
        self._entity_loaders: dict[str, Callable] = {}

    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Enregistre un workflow"""
        self._workflows[workflow.id] = workflow

        for trigger in workflow.triggers:
            if trigger.type == TriggerType.EVENT and trigger.event_name:
                self._event_subscriptions[trigger.event_name].append(workflow.id)
            elif trigger.type == TriggerType.SCHEDULED and trigger.schedule:
                self._create_schedule(workflow, trigger)

        logger.info(f"Workflow enregistré: {workflow.id} - {workflow.name}")

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Récupère un workflow par son ID"""
        return self._workflows.get(workflow_id)

    def list_workflows(self, tenant_id: str = None, status: WorkflowStatus = None) -> list[WorkflowDefinition]:
        """Liste les workflows"""
        workflows = list(self._workflows.values())

        if tenant_id:
            workflows = [w for w in workflows if w.tenant_id == tenant_id]

        if status:
            workflows = [w for w in workflows if w.status == status]

        return workflows

    def activate_workflow(self, workflow_id: str) -> bool:
        """Active un workflow"""
        workflow = self._workflows.get(workflow_id)
        if workflow:
            workflow.status = WorkflowStatus.ACTIVE
            workflow.updated_at = datetime.utcnow()
            return True
        return False

    def pause_workflow(self, workflow_id: str) -> bool:
        """Met en pause un workflow"""
        workflow = self._workflows.get(workflow_id)
        if workflow:
            workflow.status = WorkflowStatus.PAUSED
            workflow.updated_at = datetime.utcnow()
            return True
        return False

    def register_entity_loader(self, entity_type: str, loader: Callable) -> None:
        """Enregistre un loader d'entité"""
        self._entity_loaders[entity_type] = loader

    def register_custom_handler(self, action_name: str, handler: Callable) -> None:
        """Enregistre un handler d'action personnalisé"""
        self._custom_handlers[action_name] = handler

    async def trigger_event(
        self,
        event_name: str,
        event_data: dict,
        tenant_id: str
    ) -> list[str]:
        """Déclenche un événement et lance les workflows associés"""
        workflow_ids = self._event_subscriptions.get(event_name, [])
        execution_ids = []

        for workflow_id in workflow_ids:
            workflow = self._workflows.get(workflow_id)
            if not workflow or workflow.status != WorkflowStatus.ACTIVE:
                continue
            if workflow.tenant_id != tenant_id:
                continue

            for trigger in workflow.triggers:
                if trigger.type == TriggerType.EVENT and trigger.event_name == event_name:
                    if trigger.conditions:
                        if not ConditionEvaluator.evaluate_group(trigger.conditions, event_data):
                            continue

                    execution_id = await self.start_execution(
                        workflow_id=workflow_id,
                        trigger_type=TriggerType.EVENT,
                        trigger_data={"event_name": event_name, **event_data},
                        tenant_id=tenant_id
                    )
                    execution_ids.append(execution_id)

        return execution_ids

    async def start_execution(
        self,
        workflow_id: str,
        trigger_type: TriggerType,
        trigger_data: dict,
        tenant_id: str,
        entity_type: str = None,
        entity_id: str = None,
        input_variables: dict = None,
        parent_execution_id: str = None
    ) -> str:
        """Démarre l'exécution d'un workflow"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow non trouvé: {workflow_id}")

        if workflow.status != WorkflowStatus.ACTIVE:
            raise ValueError(f"Workflow non actif: {workflow_id}")

        execution_id = str(uuid.uuid4())

        variables = {}
        for var in workflow.variables:
            if var.is_input and input_variables and var.name in input_variables:
                variables[var.name] = input_variables[var.name]
            elif var.value is not None:
                variables[var.name] = var.value

        variables["__trigger_data__"] = trigger_data
        variables["__entity_type__"] = entity_type
        variables["__entity_id__"] = entity_id
        variables["__execution_id__"] = execution_id
        variables["__workflow_id__"] = workflow_id
        variables["__tenant_id__"] = tenant_id

        if entity_type and entity_id and entity_type in self._entity_loaders:
            try:
                entity_data = await self._entity_loaders[entity_type](entity_id, tenant_id)
                variables["entity"] = entity_data
            except Exception as e:
                logger.warning(f"Erreur chargement entité: {e}")

        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            workflow_version=workflow.version,
            tenant_id=tenant_id,
            trigger_type=trigger_type,
            trigger_data=trigger_data,
            entity_type=entity_type,
            entity_id=entity_id,
            status=ExecutionStatus.PENDING,
            current_action_id=None,
            variables=variables,
            action_results=[],
            started_at=datetime.utcnow(),
            completed_at=None,
            parent_execution_id=parent_execution_id
        )

        self._executions[execution_id] = execution

        asyncio.create_task(self._run_execution(execution, workflow))

        logger.info(f"Exécution démarrée: {execution_id} pour workflow {workflow_id}")

        return execution_id

    async def _run_execution(
        self,
        execution: WorkflowExecution,
        workflow: WorkflowDefinition
    ) -> None:
        """Exécute le workflow"""
        execution.status = ExecutionStatus.RUNNING

        try:
            if not workflow.actions:
                execution.status = ExecutionStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                return

            current_action = workflow.actions[0]
            action_map = {a.id: a for a in workflow.actions}

            while current_action:
                execution.current_action_id = current_action.id

                if current_action.conditions:
                    if not ConditionEvaluator.evaluate_group(
                        current_action.conditions,
                        execution.variables
                    ):
                        if current_action.next_action_id:
                            current_action = action_map.get(current_action.next_action_id)
                        else:
                            current_action = None
                        continue

                result = await self._execute_action(current_action, execution, action_map)
                execution.action_results.append(result)

                if result.status == ExecutionStatus.FAILED:
                    if current_action.on_error == "continue":
                        pass
                    elif current_action.on_error == "skip":
                        if current_action.next_action_id:
                            current_action = action_map.get(current_action.next_action_id)
                        else:
                            current_action = None
                        continue
                    else:
                        execution.status = ExecutionStatus.FAILED
                        execution.error = result.error
                        break

                if result.status == ExecutionStatus.WAITING:
                    execution.status = ExecutionStatus.WAITING
                    return

                if current_action.type == ActionType.CONDITION:
                    condition_result = result.output.get("result", False) if result.output else False
                    if condition_result and current_action.on_true_action_id:
                        current_action = action_map.get(current_action.on_true_action_id)
                    elif not condition_result and current_action.on_false_action_id:
                        current_action = action_map.get(current_action.on_false_action_id)
                    else:
                        current_action = None
                elif current_action.next_action_id:
                    current_action = action_map.get(current_action.next_action_id)
                else:
                    idx = workflow.actions.index(current_action)
                    if idx + 1 < len(workflow.actions):
                        current_action = workflow.actions[idx + 1]
                    else:
                        current_action = None

            if execution.status == ExecutionStatus.RUNNING:
                execution.status = ExecutionStatus.COMPLETED

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            logger.exception(f"Erreur exécution workflow: {e}")

        finally:
            if execution.status not in (ExecutionStatus.WAITING,):
                execution.completed_at = datetime.utcnow()

    async def _execute_action(
        self,
        action: ActionConfig,
        execution: WorkflowExecution,
        action_map: dict[str, ActionConfig]
    ) -> ActionResult:
        """Exécute une action"""
        started_at = datetime.utcnow()

        try:
            if action.type == ActionType.CONDITION:
                output, error = await self._execute_condition(action, execution)
            elif action.type == ActionType.APPROVAL:
                output, error = await self._execute_approval(action, execution)
                if error == "__WAITING__":
                    return ActionResult(
                        action_id=action.id,
                        status=ExecutionStatus.WAITING,
                        started_at=started_at,
                        completed_at=None,
                        output=output
                    )
            elif action.type == ActionType.PARALLEL:
                output, error = await self._execute_parallel(action, execution, action_map)
            elif action.type == ActionType.LOOP:
                output, error = await self._execute_loop(action, execution, action_map)
            elif action.type == ActionType.CALL_WORKFLOW:
                output, error = await self._execute_call_workflow(action, execution)
            else:
                handler = self._action_handlers.get(action.type)
                if not handler:
                    custom_handler = self._custom_handlers.get(action.type.value)
                    if custom_handler:
                        output = await custom_handler(action, execution.variables)
                        error = None
                    else:
                        raise ValueError(f"Handler non trouvé pour {action.type}")
                else:
                    output, error = await handler.execute(
                        action,
                        {"execution_id": execution.id, "tenant_id": execution.tenant_id},
                        execution.variables
                    )

            if output and isinstance(output, dict):
                execution.variables[f"action_{action.id}_output"] = output

            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            return ActionResult(
                action_id=action.id,
                status=ExecutionStatus.COMPLETED if not error else ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                output=output,
                error=error,
                duration_ms=duration_ms
            )

        except Exception as e:
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            return ActionResult(
                action_id=action.id,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                error=str(e),
                duration_ms=duration_ms
            )

    async def _execute_condition(
        self,
        action: ActionConfig,
        execution: WorkflowExecution
    ) -> tuple[Any, Optional[str]]:
        """Évalue une condition"""
        params = action.parameters
        conditions = params.get("conditions", [])
        logical_operator = params.get("logical_operator", "AND")

        condition_list = []
        for c in conditions:
            condition_list.append(Condition(
                field=c["field"],
                operator=ConditionOperator(c["operator"]),
                value=c["value"]
            ))

        group = ConditionGroup(conditions=condition_list, logical_operator=logical_operator)
        result = ConditionEvaluator.evaluate_group(group, execution.variables)

        return {"result": result}, None

    async def _execute_approval(
        self,
        action: ActionConfig,
        execution: WorkflowExecution
    ) -> tuple[Any, Optional[str]]:
        """Crée une demande d'approbation"""
        params = action.parameters
        approval_config = ApprovalConfig(
            approvers=params.get("approvers", []),
            approval_type=params.get("approval_type", "any"),
            min_approvals=params.get("min_approvals", 1),
            escalation_timeout_hours=params.get("escalation_timeout_hours", 24),
            escalation_to=params.get("escalation_to"),
            reminder_hours=params.get("reminder_hours", [4, 12]),
            allow_delegation=params.get("allow_delegation", False),
            require_comment=params.get("require_comment", False)
        )

        existing_request = None
        for req in self._approval_requests.values():
            if req.execution_id == execution.id and req.action_id == action.id:
                existing_request = req
                break

        if existing_request:
            if existing_request.status == ApprovalStatus.APPROVED:
                return {"approval_status": "approved", "decisions": existing_request.decisions}, None
            elif existing_request.status == ApprovalStatus.REJECTED:
                return {"approval_status": "rejected", "decisions": existing_request.decisions}, "Approbation rejetée"
            else:
                return {"approval_id": existing_request.id, "status": "pending"}, "__WAITING__"

        request_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=approval_config.escalation_timeout_hours)

        approval_request = ApprovalRequest(
            id=request_id,
            execution_id=execution.id,
            action_id=action.id,
            tenant_id=execution.tenant_id,
            approvers=approval_config.approvers,
            approval_config=approval_config,
            entity_type=execution.entity_type or "",
            entity_id=execution.entity_id or "",
            entity_data=execution.variables.get("entity", {}),
            status=ApprovalStatus.PENDING,
            created_at=datetime.utcnow(),
            expires_at=expires_at
        )

        self._approval_requests[request_id] = approval_request

        logger.info(f"Demande d'approbation créée: {request_id}")

        return {"approval_id": request_id, "status": "pending"}, "__WAITING__"

    async def _execute_parallel(
        self,
        action: ActionConfig,
        execution: WorkflowExecution,
        action_map: dict[str, ActionConfig]
    ) -> tuple[Any, Optional[str]]:
        """Exécute des actions en parallèle"""
        params = action.parameters
        action_ids = params.get("action_ids", [])
        wait_all = params.get("wait_all", True)

        tasks = []
        for action_id in action_ids:
            sub_action = action_map.get(action_id)
            if sub_action:
                tasks.append(self._execute_action(sub_action, execution, action_map))

        if wait_all:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            done, pending = await asyncio.wait(
                [asyncio.create_task(t) for t in tasks],
                return_when=asyncio.FIRST_COMPLETED
            )
            results = [t.result() for t in done]

        output = {"results": []}
        errors = []
        for r in results:
            if isinstance(r, ActionResult):
                output["results"].append({
                    "action_id": r.action_id,
                    "status": r.status.value,
                    "output": r.output
                })
                if r.error:
                    errors.append(r.error)
            elif isinstance(r, Exception):
                errors.append(str(r))

        return output, "; ".join(errors) if errors else None

    async def _execute_loop(
        self,
        action: ActionConfig,
        execution: WorkflowExecution,
        action_map: dict[str, ActionConfig]
    ) -> tuple[Any, Optional[str]]:
        """Exécute une boucle"""
        params = action.parameters
        collection_var = params.get("collection")
        item_var = params.get("item_variable", "item")
        index_var = params.get("index_variable", "index")
        action_ids = params.get("action_ids", [])
        max_iterations = params.get("max_iterations", 1000)

        collection = execution.variables.get(collection_var, [])
        if not isinstance(collection, list):
            collection = list(collection) if collection else []

        results = []
        for idx, item in enumerate(collection[:max_iterations]):
            execution.variables[item_var] = item
            execution.variables[index_var] = idx

            for action_id in action_ids:
                sub_action = action_map.get(action_id)
                if sub_action:
                    result = await self._execute_action(sub_action, execution, action_map)
                    results.append({
                        "iteration": idx,
                        "action_id": action_id,
                        "status": result.status.value,
                        "output": result.output
                    })

        return {"iterations": len(collection), "results": results}, None

    async def _execute_call_workflow(
        self,
        action: ActionConfig,
        execution: WorkflowExecution
    ) -> tuple[Any, Optional[str]]:
        """Appelle un sous-workflow"""
        params = action.parameters
        workflow_id = params.get("workflow_id")
        input_mapping = params.get("input_mapping", {})
        wait_completion = params.get("wait_completion", True)

        input_variables = {}
        for target_var, source_expr in input_mapping.items():
            if source_expr.startswith("${") and source_expr.endswith("}"):
                var_name = source_expr[2:-1]
                input_variables[target_var] = execution.variables.get(var_name)
            else:
                input_variables[target_var] = source_expr

        sub_execution_id = await self.start_execution(
            workflow_id=workflow_id,
            trigger_type=TriggerType.MANUAL,
            trigger_data={"parent_action_id": action.id},
            tenant_id=execution.tenant_id,
            input_variables=input_variables,
            parent_execution_id=execution.id
        )

        if wait_completion:
            while True:
                sub_execution = self._executions.get(sub_execution_id)
                if sub_execution and sub_execution.status in (
                    ExecutionStatus.COMPLETED,
                    ExecutionStatus.FAILED,
                    ExecutionStatus.CANCELLED
                ):
                    break
                await asyncio.sleep(0.5)

            sub_execution = self._executions.get(sub_execution_id)
            if sub_execution.status == ExecutionStatus.FAILED:
                return None, sub_execution.error

            return {
                "execution_id": sub_execution_id,
                "status": sub_execution.status.value,
                "variables": sub_execution.variables
            }, None

        return {"execution_id": sub_execution_id, "status": "started"}, None

    async def process_approval(
        self,
        request_id: str,
        user_id: str,
        approved: bool,
        comment: str = ""
    ) -> bool:
        """Traite une décision d'approbation"""
        request = self._approval_requests.get(request_id)
        if not request:
            return False

        if user_id not in request.approvers:
            return False

        if request.status != ApprovalStatus.PENDING:
            return False

        decision = {
            "user_id": user_id,
            "approved": approved,
            "comment": comment,
            "timestamp": datetime.utcnow().isoformat()
        }
        request.decisions.append(decision)

        if comment:
            request.comments.append({
                "user_id": user_id,
                "comment": comment,
                "timestamp": datetime.utcnow().isoformat()
            })

        if not approved:
            request.status = ApprovalStatus.REJECTED
        else:
            if request.approval_config.approval_type == "any":
                request.status = ApprovalStatus.APPROVED
            elif request.approval_config.approval_type == "all":
                approved_count = sum(1 for d in request.decisions if d["approved"])
                if approved_count >= len(request.approvers):
                    request.status = ApprovalStatus.APPROVED
            elif request.approval_config.approval_type == "majority":
                approved_count = sum(1 for d in request.decisions if d["approved"])
                if approved_count > len(request.approvers) / 2:
                    request.status = ApprovalStatus.APPROVED
            elif request.approval_config.approval_type == "threshold":
                approved_count = sum(1 for d in request.decisions if d["approved"])
                if approved_count >= request.approval_config.min_approvals:
                    request.status = ApprovalStatus.APPROVED

        if request.status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
            execution = self._executions.get(request.execution_id)
            if execution and execution.status == ExecutionStatus.WAITING:
                workflow = self._workflows.get(execution.workflow_id)
                if workflow:
                    asyncio.create_task(self._run_execution(execution, workflow))

        return True

    def get_pending_approvals(
        self,
        user_id: str,
        tenant_id: str = None
    ) -> list[ApprovalRequest]:
        """Récupère les approbations en attente pour un utilisateur"""
        pending = []
        for request in self._approval_requests.values():
            if request.status != ApprovalStatus.PENDING:
                continue
            if user_id not in request.approvers:
                continue
            if tenant_id and request.tenant_id != tenant_id:
                continue

            already_decided = any(d["user_id"] == user_id for d in request.decisions)
            if already_decided:
                continue

            pending.append(request)

        return sorted(pending, key=lambda x: x.created_at, reverse=True)

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Récupère une exécution par son ID"""
        return self._executions.get(execution_id)

    def get_executions(
        self,
        workflow_id: str = None,
        tenant_id: str = None,
        status: ExecutionStatus = None,
        limit: int = 100
    ) -> list[WorkflowExecution]:
        """Liste les exécutions"""
        executions = list(self._executions.values())

        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        if tenant_id:
            executions = [e for e in executions if e.tenant_id == tenant_id]
        if status:
            executions = [e for e in executions if e.status == status]

        executions.sort(key=lambda x: x.started_at, reverse=True)
        return executions[:limit]

    async def cancel_execution(self, execution_id: str, reason: str = "") -> bool:
        """Annule une exécution"""
        execution = self._executions.get(execution_id)
        if not execution:
            return False

        if execution.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED):
            return False

        execution.status = ExecutionStatus.CANCELLED
        execution.error = reason or "Annulé"
        execution.completed_at = datetime.utcnow()

        return True

    def _create_schedule(self, workflow: WorkflowDefinition, trigger: TriggerConfig) -> None:
        """Crée un planning pour un workflow"""
        schedule_id = str(uuid.uuid4())

        next_run = self._calculate_next_run(trigger.schedule)

        scheduled = ScheduledWorkflow(
            id=schedule_id,
            workflow_id=workflow.id,
            tenant_id=workflow.tenant_id,
            schedule=trigger.schedule,
            next_run_at=next_run,
            last_run_at=None,
            last_run_status=None,
            is_active=True,
            created_at=datetime.utcnow()
        )

        self._scheduled_workflows[schedule_id] = scheduled

    def _calculate_next_run(self, schedule: str) -> datetime:
        """Calcule la prochaine exécution (format cron simplifié)"""
        now = datetime.utcnow()

        if schedule.startswith("@"):
            shortcuts = {
                "@hourly": timedelta(hours=1),
                "@daily": timedelta(days=1),
                "@weekly": timedelta(weeks=1),
                "@monthly": timedelta(days=30),
            }
            delta = shortcuts.get(schedule, timedelta(hours=1))
            return now + delta

        return now + timedelta(hours=1)

    async def run_scheduled_workflows(self) -> list[str]:
        """Exécute les workflows planifiés"""
        now = datetime.utcnow()
        execution_ids = []

        for scheduled in self._scheduled_workflows.values():
            if not scheduled.is_active:
                continue
            if scheduled.next_run_at > now:
                continue

            workflow = self._workflows.get(scheduled.workflow_id)
            if not workflow or workflow.status != WorkflowStatus.ACTIVE:
                continue

            try:
                execution_id = await self.start_execution(
                    workflow_id=scheduled.workflow_id,
                    trigger_type=TriggerType.SCHEDULED,
                    trigger_data={"schedule_id": scheduled.id, "schedule": scheduled.schedule},
                    tenant_id=scheduled.tenant_id,
                    input_variables=scheduled.input_variables
                )
                execution_ids.append(execution_id)

                scheduled.last_run_at = now
                scheduled.next_run_at = self._calculate_next_run(scheduled.schedule)

            except Exception as e:
                logger.error(f"Erreur exécution planifiée: {e}")
                scheduled.last_run_status = ExecutionStatus.FAILED

        return execution_ids


# ============================================================================
# Workflow Builder (DSL)
# ============================================================================

class WorkflowBuilder:
    """Builder pour créer des workflows de manière fluide"""

    def __init__(self, workflow_id: str, name: str, tenant_id: str):
        self._workflow_id = workflow_id
        self._name = name
        self._tenant_id = tenant_id
        self._description = ""
        self._entity_type: Optional[str] = None
        self._triggers: list[TriggerConfig] = []
        self._actions: list[ActionConfig] = []
        self._variables: list[WorkflowVariable] = []
        self._action_counter = 0

    def description(self, desc: str) -> "WorkflowBuilder":
        """Définit la description"""
        self._description = desc
        return self

    def for_entity(self, entity_type: str) -> "WorkflowBuilder":
        """Définit le type d'entité"""
        self._entity_type = entity_type
        return self

    def on_event(
        self,
        event_name: str,
        conditions: list[dict] = None
    ) -> "WorkflowBuilder":
        """Ajoute un déclencheur sur événement"""
        condition_group = None
        if conditions:
            condition_group = ConditionGroup(
                conditions=[
                    Condition(
                        field=c["field"],
                        operator=ConditionOperator(c["operator"]),
                        value=c["value"]
                    )
                    for c in conditions
                ]
            )

        self._triggers.append(TriggerConfig(
            type=TriggerType.EVENT,
            event_name=event_name,
            conditions=condition_group
        ))
        return self

    def on_schedule(self, schedule: str) -> "WorkflowBuilder":
        """Ajoute un déclencheur planifié"""
        self._triggers.append(TriggerConfig(
            type=TriggerType.SCHEDULED,
            schedule=schedule
        ))
        return self

    def on_manual(self) -> "WorkflowBuilder":
        """Ajoute un déclencheur manuel"""
        self._triggers.append(TriggerConfig(type=TriggerType.MANUAL))
        return self

    def variable(
        self,
        name: str,
        data_type: str = "string",
        default_value: Any = None,
        is_input: bool = False,
        is_output: bool = False
    ) -> "WorkflowBuilder":
        """Ajoute une variable"""
        self._variables.append(WorkflowVariable(
            name=name,
            value=default_value,
            data_type=data_type,
            is_input=is_input,
            is_output=is_output
        ))
        return self

    def _next_action_id(self) -> str:
        """Génère un ID d'action unique"""
        self._action_counter += 1
        return f"action_{self._action_counter}"

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        **kwargs
    ) -> "WorkflowBuilder":
        """Ajoute une action d'envoi d'email"""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.SEND_EMAIL,
            name="Envoi email",
            parameters={"to": to, "subject": subject, "body": body, **kwargs}
        )
        self._actions.append(action)
        return self

    def send_notification(
        self,
        recipients: list[str],
        title: str,
        message: str,
        channels: list[str] = None
    ) -> "WorkflowBuilder":
        """Ajoute une action de notification"""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.SEND_NOTIFICATION,
            name="Notification",
            parameters={
                "recipients": recipients,
                "title": title,
                "message": message,
                "channels": channels or ["in_app"]
            }
        )
        self._actions.append(action)
        return self

    def update_record(
        self,
        entity_type: str,
        entity_id: str,
        updates: dict
    ) -> "WorkflowBuilder":
        """Ajoute une action de mise à jour"""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.UPDATE_RECORD,
            name=f"Mise à jour {entity_type}",
            parameters={"entity_type": entity_type, "entity_id": entity_id, "updates": updates}
        )
        self._actions.append(action)
        return self

    def require_approval(
        self,
        approvers: list[str],
        approval_type: str = "any",
        **kwargs
    ) -> "WorkflowBuilder":
        """Ajoute une étape d'approbation"""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.APPROVAL,
            name="Approbation requise",
            parameters={"approvers": approvers, "approval_type": approval_type, **kwargs}
        )
        self._actions.append(action)
        return self

    def delay(self, seconds: int = 0, until: str = None) -> "WorkflowBuilder":
        """Ajoute un délai"""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.DELAY,
            name="Délai",
            parameters={"delay_seconds": seconds, "delay_until": until}
        )
        self._actions.append(action)
        return self

    def set_variable(
        self,
        name: str,
        value: Any = None,
        expression: str = None
    ) -> "WorkflowBuilder":
        """Ajoute une action de définition de variable"""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.SET_VARIABLE,
            name=f"Définir {name}",
            parameters={"name": name, "value": value, "expression": expression}
        )
        self._actions.append(action)
        return self

    def log(self, message: str, level: str = "INFO") -> "WorkflowBuilder":
        """Ajoute une action de log"""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.LOG,
            name="Log",
            parameters={"message": message, "level": level}
        )
        self._actions.append(action)
        return self

    def http_request(
        self,
        url: str,
        method: str = "GET",
        headers: dict = None,
        body: Any = None
    ) -> "WorkflowBuilder":
        """Ajoute une requête HTTP"""
        action = ActionConfig(
            id=self._next_action_id(),
            type=ActionType.HTTP_REQUEST,
            name=f"HTTP {method}",
            parameters={"url": url, "method": method, "headers": headers or {}, "body": body}
        )
        self._actions.append(action)
        return self

    def build(self) -> WorkflowDefinition:
        """Construit le workflow"""
        for i, action in enumerate(self._actions[:-1]):
            if not action.next_action_id:
                action.next_action_id = self._actions[i + 1].id

        return WorkflowDefinition(
            id=self._workflow_id,
            name=self._name,
            description=self._description,
            version=1,
            tenant_id=self._tenant_id,
            entity_type=self._entity_type,
            triggers=self._triggers,
            actions=self._actions,
            variables=self._variables,
            status=WorkflowStatus.DRAFT
        )


# ============================================================================
# Workflows Prédéfinis
# ============================================================================

def create_invoice_approval_workflow(tenant_id: str) -> WorkflowDefinition:
    """Crée un workflow d'approbation de factures"""
    return (
        WorkflowBuilder("invoice_approval", "Approbation Factures", tenant_id)
        .description("Workflow d'approbation des factures fournisseurs")
        .for_entity("invoice")
        .on_event("invoice.created", [
            {"field": "type", "operator": "equals", "value": "supplier_invoice"},
            {"field": "amount_total", "operator": "greater_than", "value": 1000}
        ])
        .variable("approval_threshold", "decimal", 5000)
        .send_notification(
            recipients=["${entity.created_by}"],
            title="Facture en attente d'approbation",
            message="La facture ${entity.number} de ${entity.amount_total}€ nécessite une approbation"
        )
        .require_approval(
            approvers=["manager", "accountant"],
            approval_type="any",
            escalation_timeout_hours=48
        )
        .update_record(
            entity_type="invoice",
            entity_id="${__entity_id__}",
            updates={"status": "approved", "approved_at": "${__now__}"}
        )
        .send_notification(
            recipients=["${entity.created_by}"],
            title="Facture approuvée",
            message="La facture ${entity.number} a été approuvée"
        )
        .build()
    )


def create_expense_report_workflow(tenant_id: str) -> WorkflowDefinition:
    """Crée un workflow de notes de frais"""
    return (
        WorkflowBuilder("expense_report", "Notes de Frais", tenant_id)
        .description("Workflow de validation des notes de frais")
        .for_entity("expense_report")
        .on_event("expense_report.submitted")
        .variable("auto_approve_limit", "decimal", 100)
        .log("Nouvelle note de frais soumise: ${entity.id}")
        .require_approval(
            approvers=["${entity.manager_id}"],
            approval_type="all",
            require_comment=True
        )
        .update_record(
            entity_type="expense_report",
            entity_id="${__entity_id__}",
            updates={"status": "validated"}
        )
        .send_email(
            to="${entity.employee_email}",
            subject="Note de frais validée",
            body="Votre note de frais #${entity.id} a été validée pour un montant de ${entity.total}€"
        )
        .build()
    )


def create_customer_onboarding_workflow(tenant_id: str) -> WorkflowDefinition:
    """Crée un workflow d'onboarding client"""
    return (
        WorkflowBuilder("customer_onboarding", "Onboarding Client", tenant_id)
        .description("Workflow d'intégration des nouveaux clients")
        .for_entity("customer")
        .on_event("customer.created")
        .send_email(
            to="${entity.email}",
            subject="Bienvenue chez AZALSCORE",
            body="Bonjour ${entity.name}, bienvenue !"
        )
        .delay(seconds=86400)
        .send_email(
            to="${entity.email}",
            subject="Premiers pas avec AZALSCORE",
            body="Découvrez nos fonctionnalités..."
        )
        .delay(seconds=259200)
        .send_notification(
            recipients=["sales_team"],
            title="Suivi client",
            message="Le client ${entity.name} a été créé il y a 3 jours"
        )
        .build()
    )


# ============================================================================
# Instance Globale
# ============================================================================

_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Retourne l'instance du moteur de workflow"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine
