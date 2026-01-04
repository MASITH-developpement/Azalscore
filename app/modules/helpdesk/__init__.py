"""
AZALS MODULE 16 - Helpdesk
===========================
Système de support client complet.

Fonctionnalités:
- Gestion des tickets (création, assignation, suivi)
- Catégories et priorisation
- Équipes et agents support
- SLA (Service Level Agreements)
- Base de connaissances (KB)
- Réponses pré-enregistrées
- Enquêtes de satisfaction
- Automatisations et règles
- Dashboard et statistiques

Intégrations AZALS:
- M1 Commercial (clients CRM)
- T0 IAM (agents = utilisateurs)
"""

from .models import (
    TicketCategory,
    HelpdeskTeam,
    HelpdeskAgent,
    HelpdeskSLA,
    Ticket,
    TicketReply,
    TicketAttachment,
    TicketHistory,
    CannedResponse,
    KBCategory,
    KBArticle,
    SatisfactionSurvey,
    HelpdeskAutomation,
    TicketStatus,
    TicketPriority,
    TicketSource,
    AgentStatus
)

from .service import HelpdeskService
from .router import router

__all__ = [
    # Models
    "TicketCategory",
    "HelpdeskTeam",
    "HelpdeskAgent",
    "HelpdeskSLA",
    "Ticket",
    "TicketReply",
    "TicketAttachment",
    "TicketHistory",
    "CannedResponse",
    "KBCategory",
    "KBArticle",
    "SatisfactionSurvey",
    "HelpdeskAutomation",
    # Enums
    "TicketStatus",
    "TicketPriority",
    "TicketSource",
    "AgentStatus",
    # Service & Router
    "HelpdeskService",
    "router"
]
