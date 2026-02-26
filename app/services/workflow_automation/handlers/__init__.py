"""
AZALSCORE - Workflow Automation Handlers
Handlers d'actions pour l'automatisation des workflows
"""
from .base import ActionHandler
from .email import SendEmailHandler
from .notification import SendNotificationHandler
from .record import UpdateRecordHandler, CreateRecordHandler
from .http import HttpRequestHandler
from .script import ExecuteScriptHandler
from .delay import DelayHandler
from .variable import SafeExpressionEvaluator, SetVariableHandler
from .log import LogHandler

__all__ = [
    "ActionHandler",
    "SendEmailHandler",
    "SendNotificationHandler",
    "UpdateRecordHandler",
    "CreateRecordHandler",
    "HttpRequestHandler",
    "ExecuteScriptHandler",
    "DelayHandler",
    "SafeExpressionEvaluator",
    "SetVariableHandler",
    "LogHandler",
]
