"""
AZALS MODULE - Marceau Support Service
=======================================

Service de support client automatise.
Integration avec le module helpdesk d'AZALSCORE.

Actions:
- create_ticket: Creation ticket support
- respond_ticket: Reponse automatique avec RAG
- escalate: Escalade ticket
- resolve: Resolution ticket
"""
from __future__ import annotations


import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.modules.marceau.models import ActionStatus, MarceauAction, MemoryType, ModuleName

logger = logging.getLogger(__name__)


class SupportService:
    """
    Service support Marceau.
    Gere les tickets, FAQ automatique, escalade.
    """

    def __init__(self, tenant_id: str, db: Session):
        self.tenant_id = tenant_id
        self.db = db

    async def execute_action(
        self,
        action: str,
        data: dict,
        context: list[str]
    ) -> dict:
        """Execute une action support."""
        action_handlers = {
            "create_ticket": self._create_ticket,
            "respond_ticket": self._respond_ticket,
            "escalate": self._escalate,
            "resolve": self._resolve,
        }

        handler = action_handlers.get(action, self._unknown_action)
        return await handler(data, context)

    # =========================================================================
    # CREATE TICKET
    # =========================================================================

    async def _create_ticket(self, data: dict, context: list[str]) -> dict:
        """
        Cree un ticket support.

        Args:
            data: {
                "subject": str (obligatoire)
                "description": str (obligatoire)
                "customer_email": str (optionnel)
                "customer_name": str (optionnel)
                "priority": str (low|medium|high|urgent|critical)
                "category": str (optionnel)
                "source": str (web|email|phone|chat|api)
            }

        Returns:
            Ticket cree avec ticket_id, ticket_number
        """
        try:
            from app.modules.helpdesk.models import (
                Ticket,
                TicketPriority,
                TicketSource,
                TicketStatus,
            )

            # Validation
            required = ["subject", "description"]
            missing = [f for f in required if not data.get(f)]
            if missing:
                return {
                    "success": False,
                    "error": f"Champs obligatoires manquants: {', '.join(missing)}",
                    "module": "support"
                }

            # Detecter la priorite automatiquement si non fournie
            priority_str = data.get("priority")
            if not priority_str:
                priority_str = await self._detect_priority(
                    data["subject"], data["description"], context
                )

            # Mapper la priorite
            priority_map = {
                "low": TicketPriority.LOW,
                "medium": TicketPriority.MEDIUM,
                "high": TicketPriority.HIGH,
                "urgent": TicketPriority.URGENT,
                "critical": TicketPriority.CRITICAL,
            }
            priority = priority_map.get(priority_str.lower(), TicketPriority.MEDIUM)

            # Source
            source_str = data.get("source", "api")
            source_map = {
                "web": TicketSource.WEB,
                "email": TicketSource.EMAIL,
                "phone": TicketSource.PHONE,
                "chat": TicketSource.CHAT,
                "api": TicketSource.API,
                "internal": TicketSource.INTERNAL,
            }
            source = source_map.get(source_str.lower(), TicketSource.API)

            # Generer numero de ticket
            ticket_number = await self._generate_ticket_number()

            # Creer le ticket
            ticket = Ticket(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                number=ticket_number,
                subject=data["subject"],
                description=data["description"],
                status=TicketStatus.NEW,
                priority=priority,
                source=source,
                requester_name=data.get("customer_name"),
                requester_email=data.get("customer_email"),
                created_at=datetime.utcnow(),
            )

            self.db.add(ticket)

            # Creer action Marceau
            action = MarceauAction(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                module=ModuleName.SUPPORT,
                action_type="ticket_created",
                status=ActionStatus.COMPLETED,
                input_data=data,
                output_data={
                    "ticket_id": str(ticket.id),
                    "ticket_number": ticket_number,
                    "priority": priority.value,
                },
                related_entity_type="Ticket",
                related_entity_id=ticket.id,
                confidence_score=0.95,
            )

            self.db.add(action)
            self.db.commit()
            self.db.refresh(ticket)

            logger.info(f"[MARCEAU] Ticket {ticket_number} cree - priorite {priority.value}")

            return {
                "success": True,
                "ticket_id": str(ticket.id),
                "ticket_number": ticket_number,
                "subject": ticket.subject,
                "priority": priority.value,
                "status": TicketStatus.NEW.value,
                "action_id": str(action.id),
                "message": f"Ticket {ticket_number} cree avec succes",
                "module": "support"
            }

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur creation ticket: {e}")
            return {
                "success": False,
                "error": str(e),
                "module": "support"
            }

    async def _detect_priority(self, subject: str, description: str, context: list[str]) -> str:
        """Detecte la priorite d'un ticket via LLM."""
        try:
            from app.modules.marceau.llm_client import get_llm_client_for_tenant

            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            prompt = f"""
Analyse ce ticket support et determine sa priorite.

Sujet: {subject}
Description: {description}

Retourne UNIQUEMENT un mot parmi: low, medium, high, urgent, critical

Criteres:
- critical: Systeme en panne, perte de donnees, impact business immediat
- urgent: Fonctionnalite bloquee, client important, deadline proche
- high: Bug important, plusieurs utilisateurs impactes
- medium: Bug mineur, demande standard
- low: Question, amelioration, documentation

Priorite:"""

            response = await llm.generate(prompt, temperature=0.1, max_tokens=10)

            # Extraire la priorite de la reponse
            response_lower = response.lower().strip()
            for prio in ["critical", "urgent", "high", "medium", "low"]:
                if prio in response_lower:
                    return prio

            return "medium"

        except Exception as e:
            logger.warning(f"[MARCEAU] Detection priorite echouee: {e}")
            # Detection basique par mots-cles
            text = f"{subject} {description}".lower()

            if any(w in text for w in ["urgent", "bloque", "impossible", "crash", "panne"]):
                return "urgent"
            elif any(w in text for w in ["erreur", "bug", "probleme", "ne fonctionne"]):
                return "high"
            elif any(w in text for w in ["question", "comment", "aide"]):
                return "low"

            return "medium"

    # =========================================================================
    # RESPOND TICKET
    # =========================================================================

    async def _respond_ticket(self, data: dict, context: list[str]) -> dict:
        """
        Genere et envoie une reponse automatique a un ticket.

        Args:
            data: {
                "ticket_id": str (obligatoire)
                "auto_send": bool (defaut: False, si True envoie directement)
            }

        Returns:
            Reponse suggeree ou confirmee si auto_send
        """
        try:
            from app.modules.helpdesk.models import Ticket, TicketMessage, TicketStatus

            ticket_id = data.get("ticket_id")
            if not ticket_id:
                return {
                    "success": False,
                    "error": "ticket_id obligatoire",
                    "module": "support"
                }

            # Recuperer le ticket
            ticket = self.db.query(Ticket).filter(
                Ticket.id == uuid.UUID(ticket_id),
                Ticket.tenant_id == self.tenant_id
            ).first()

            if not ticket:
                return {
                    "success": False,
                    "error": f"Ticket {ticket_id} non trouve",
                    "module": "support"
                }

            # Recuperer l'historique des messages
            messages = self.db.query(TicketMessage).filter(
                TicketMessage.ticket_id == ticket.id
            ).order_by(TicketMessage.created_at).all()

            # Enrichir le contexte avec la base de connaissances
            from app.modules.marceau.memory import MarceauMemoryService

            memory = MarceauMemoryService(self.tenant_id, self.db)
            knowledge = await memory.retrieve_relevant_context(
                query=f"{ticket.subject} {ticket.description}",
                limit=5,
                memory_types=[MemoryType.KNOWLEDGE, MemoryType.LEARNING]
            )

            # Generer la reponse
            response_text = await self._generate_ticket_response(
                ticket, messages, knowledge + context
            )

            auto_send = data.get("auto_send", False)

            if auto_send:
                # Creer le message de reponse
                message = TicketMessage(
                    id=uuid.uuid4(),
                    tenant_id=self.tenant_id,
                    ticket_id=ticket.id,
                    content=response_text,
                    is_internal=False,
                    is_from_agent=True,
                    created_at=datetime.utcnow(),
                )
                self.db.add(message)

                # Mettre a jour le statut
                if ticket.status == TicketStatus.NEW:
                    ticket.status = TicketStatus.OPEN

                ticket.updated_at = datetime.utcnow()

                # Envoyer par email si adresse disponible
                email_sent = False
                if ticket.requester_email:
                    email_sent = await self._send_ticket_response_email(
                        ticket, response_text
                    )

                # Action Marceau
                action = MarceauAction(
                    id=uuid.uuid4(),
                    tenant_id=self.tenant_id,
                    module=ModuleName.SUPPORT,
                    action_type="ticket_responded",
                    status=ActionStatus.COMPLETED,
                    input_data=data,
                    output_data={
                        "response": response_text[:500],
                        "email_sent": email_sent,
                    },
                    related_entity_type="Ticket",
                    related_entity_id=ticket.id,
                    confidence_score=0.85,
                )
                self.db.add(action)
                self.db.commit()

                logger.info(f"[MARCEAU] Reponse envoyee ticket {ticket.number}")

                return {
                    "success": True,
                    "ticket_id": str(ticket.id),
                    "ticket_number": ticket.number,
                    "response": response_text,
                    "sent": True,
                    "email_sent": email_sent,
                    "action_id": str(action.id),
                    "message": f"Reponse envoyee pour ticket {ticket.number}",
                    "module": "support"
                }
            else:
                # Mode suggestion uniquement
                return {
                    "success": True,
                    "ticket_id": str(ticket.id),
                    "ticket_number": ticket.number,
                    "suggested_response": response_text,
                    "sent": False,
                    "requires_validation": True,
                    "message": "Reponse suggeree - validation requise avant envoi",
                    "module": "support"
                }

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur reponse ticket: {e}")
            return {
                "success": False,
                "error": str(e),
                "module": "support"
            }

    async def _generate_ticket_response(
        self, ticket, messages: list, context: list[str]
    ) -> str:
        """Genere une reponse pour un ticket."""
        try:
            from app.modules.marceau.llm_client import get_llm_client_for_tenant

            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            # Construire l'historique des messages
            history = ""
            for msg in messages[-5:]:  # 5 derniers messages
                role = "Agent" if msg.is_from_agent else "Client"
                history += f"\n{role}: {msg.content[:200]}"

            prompt = f"""
Tu es un agent support professionnel. Genere une reponse pour ce ticket.

TICKET:
Numero: {ticket.number}
Sujet: {ticket.subject}
Description: {ticket.description}
Priorite: {ticket.priority.value if ticket.priority else 'non definie'}

HISTORIQUE CONVERSATION:
{history if history else "Aucun message precedent"}

BASE DE CONNAISSANCES:
{chr(10).join(context[:3]) if context else "Aucune information pertinente trouvee"}

CONSIGNES:
- Reponse professionnelle et empathique
- Proposer une solution concrete si possible
- Demander des precisions si necessaire
- Format texte simple (pas de HTML)
- Maximum 200 mots

REPONSE:"""

            response = await llm.generate(prompt, temperature=0.7, max_tokens=400)
            return response.strip()

        except Exception as e:
            logger.warning(f"[MARCEAU] LLM indisponible, reponse generique: {e}")
            return f"""
Bonjour,

Merci pour votre message concernant "{ticket.subject}".

Nous avons bien pris en compte votre demande et un membre de notre equipe va l'examiner dans les plus brefs delais.

Si vous avez des informations complementaires a nous communiquer, n'hesitez pas a repondre a ce message.

Cordialement,
L'equipe Support
"""

    async def _send_ticket_response_email(self, ticket, response: str) -> bool:
        """Envoie la reponse par email."""
        try:
            from app.modules.email.service import EmailService
            from app.modules.email.schemas import SendEmailRequest

            email_service = EmailService(self.db, self.tenant_id)

            request = SendEmailRequest(
                to=ticket.requester_email,
                subject=f"Re: [{ticket.number}] {ticket.subject}",
                body_text=response,
                body_html=f"<p>{response.replace(chr(10), '<br>')}</p>",
            )

            result = email_service.send_email(request)
            return result.success

        except Exception as e:
            logger.warning(f"[MARCEAU] Echec envoi email ticket: {e}")
            return False

    # =========================================================================
    # ESCALATE
    # =========================================================================

    async def _escalate(self, data: dict, context: list[str]) -> dict:
        """
        Escalade un ticket.

        Args:
            data: {
                "ticket_id": str (obligatoire)
                "new_priority": str (optionnel)
                "new_team_id": str (optionnel)
                "reason": str (obligatoire)
                "notify_manager": bool (defaut: True)
            }

        Returns:
            Confirmation d'escalade
        """
        try:
            from app.modules.helpdesk.models import Ticket, TicketPriority, TicketStatus

            ticket_id = data.get("ticket_id")
            reason = data.get("reason")

            if not ticket_id or not reason:
                return {
                    "success": False,
                    "error": "ticket_id et reason obligatoires",
                    "module": "support"
                }

            # Recuperer le ticket
            ticket = self.db.query(Ticket).filter(
                Ticket.id == uuid.UUID(ticket_id),
                Ticket.tenant_id == self.tenant_id
            ).first()

            if not ticket:
                return {
                    "success": False,
                    "error": f"Ticket {ticket_id} non trouve",
                    "module": "support"
                }

            old_priority = ticket.priority
            old_team = ticket.team_id

            # Mettre a jour la priorite si demandee
            new_priority_str = data.get("new_priority")
            if new_priority_str:
                priority_map = {
                    "low": TicketPriority.LOW,
                    "medium": TicketPriority.MEDIUM,
                    "high": TicketPriority.HIGH,
                    "urgent": TicketPriority.URGENT,
                    "critical": TicketPriority.CRITICAL,
                }
                ticket.priority = priority_map.get(new_priority_str.lower(), ticket.priority)

            # Mettre a jour l'equipe si demandee
            new_team_id = data.get("new_team_id")
            if new_team_id:
                ticket.team_id = uuid.UUID(new_team_id)

            # Ajouter une note interne
            from app.modules.helpdesk.models import TicketMessage

            note = TicketMessage(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                ticket_id=ticket.id,
                content=f"[ESCALADE] {reason}",
                is_internal=True,
                is_from_agent=True,
                created_at=datetime.utcnow(),
            )
            self.db.add(note)

            ticket.updated_at = datetime.utcnow()

            # Notifier le manager si demande
            notify = data.get("notify_manager", True)
            manager_notified = False
            if notify:
                manager_notified = await self._notify_manager_escalation(ticket, reason)

            # Action Marceau
            action = MarceauAction(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                module=ModuleName.SUPPORT,
                action_type="ticket_escalated",
                status=ActionStatus.COMPLETED,
                input_data=data,
                output_data={
                    "old_priority": old_priority.value if old_priority else None,
                    "new_priority": ticket.priority.value if ticket.priority else None,
                    "manager_notified": manager_notified,
                },
                related_entity_type="Ticket",
                related_entity_id=ticket.id,
                confidence_score=1.0,
            )
            self.db.add(action)
            self.db.commit()

            logger.info(f"[MARCEAU] Ticket {ticket.number} escalade")

            return {
                "success": True,
                "ticket_id": str(ticket.id),
                "ticket_number": ticket.number,
                "new_priority": ticket.priority.value if ticket.priority else None,
                "manager_notified": manager_notified,
                "action_id": str(action.id),
                "message": f"Ticket {ticket.number} escalade avec succes",
                "module": "support"
            }

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur escalade ticket: {e}")
            return {
                "success": False,
                "error": str(e),
                "module": "support"
            }

    async def _notify_manager_escalation(self, ticket, reason: str) -> bool:
        """Notifie le manager d'une escalade."""
        # Implementation simplifiee - en production, envoyer email/notification
        logger.info(f"[MARCEAU] Notification manager: Escalade ticket {ticket.number}")
        return True

    # =========================================================================
    # RESOLVE
    # =========================================================================

    async def _resolve(self, data: dict, context: list[str]) -> dict:
        """
        Resout un ticket.

        Args:
            data: {
                "ticket_id": str (obligatoire)
                "resolution": str (obligatoire)
                "send_confirmation": bool (defaut: True)
                "add_to_knowledge": bool (defaut: False)
            }

        Returns:
            Confirmation de resolution
        """
        try:
            from app.modules.helpdesk.models import Ticket, TicketMessage, TicketStatus

            ticket_id = data.get("ticket_id")
            resolution = data.get("resolution")

            if not ticket_id or not resolution:
                return {
                    "success": False,
                    "error": "ticket_id et resolution obligatoires",
                    "module": "support"
                }

            # Recuperer le ticket
            ticket = self.db.query(Ticket).filter(
                Ticket.id == uuid.UUID(ticket_id),
                Ticket.tenant_id == self.tenant_id
            ).first()

            if not ticket:
                return {
                    "success": False,
                    "error": f"Ticket {ticket_id} non trouve",
                    "module": "support"
                }

            # Mettre a jour le statut
            ticket.status = TicketStatus.RESOLVED
            ticket.resolved_at = datetime.utcnow()
            ticket.updated_at = datetime.utcnow()

            # Ajouter le message de resolution
            message = TicketMessage(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                ticket_id=ticket.id,
                content=f"[RESOLUTION] {resolution}",
                is_internal=False,
                is_from_agent=True,
                created_at=datetime.utcnow(),
            )
            self.db.add(message)

            # Envoyer confirmation au client
            send_confirmation = data.get("send_confirmation", True)
            email_sent = False
            if send_confirmation and ticket.requester_email:
                email_sent = await self._send_resolution_email(ticket, resolution)

            # Ajouter a la base de connaissances si demande
            add_to_knowledge = data.get("add_to_knowledge", False)
            knowledge_added = False
            if add_to_knowledge:
                knowledge_added = await self._add_to_knowledge_base(ticket, resolution)

            # Action Marceau
            action = MarceauAction(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                module=ModuleName.SUPPORT,
                action_type="ticket_resolved",
                status=ActionStatus.COMPLETED,
                input_data=data,
                output_data={
                    "resolution": resolution[:500],
                    "email_sent": email_sent,
                    "knowledge_added": knowledge_added,
                },
                related_entity_type="Ticket",
                related_entity_id=ticket.id,
                confidence_score=1.0,
            )
            self.db.add(action)
            self.db.commit()

            logger.info(f"[MARCEAU] Ticket {ticket.number} resolu")

            return {
                "success": True,
                "ticket_id": str(ticket.id),
                "ticket_number": ticket.number,
                "status": TicketStatus.RESOLVED.value,
                "email_sent": email_sent,
                "knowledge_added": knowledge_added,
                "action_id": str(action.id),
                "message": f"Ticket {ticket.number} resolu avec succes",
                "module": "support"
            }

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur resolution ticket: {e}")
            return {
                "success": False,
                "error": str(e),
                "module": "support"
            }

    async def _send_resolution_email(self, ticket, resolution: str) -> bool:
        """Envoie l'email de resolution."""
        try:
            from app.modules.email.service import EmailService
            from app.modules.email.schemas import SendEmailRequest

            email_service = EmailService(self.db, self.tenant_id)

            body = f"""
Bonjour,

Votre demande [{ticket.number}] "{ticket.subject}" a ete resolue.

Resolution:
{resolution}

Si vous avez d'autres questions, n'hesitez pas a nous contacter.

Cordialement,
L'equipe Support
"""

            request = SendEmailRequest(
                to=ticket.requester_email,
                subject=f"[RESOLU] [{ticket.number}] {ticket.subject}",
                body_text=body,
                body_html=f"<p>{body.replace(chr(10), '<br>')}</p>",
            )

            result = email_service.send_email(request)
            return result.success

        except Exception as e:
            logger.warning(f"[MARCEAU] Echec envoi email resolution: {e}")
            return False

    async def _add_to_knowledge_base(self, ticket, resolution: str) -> bool:
        """Ajoute la resolution a la base de connaissances."""
        try:
            from app.modules.marceau.memory import MarceauMemoryService

            memory = MarceauMemoryService(self.tenant_id, self.db)

            # Creer un article de connaissance
            content = f"""
Probleme: {ticket.subject}

Description: {ticket.description}

Solution: {resolution}
"""

            await memory.store_memory(
                content=content,
                memory_type=MemoryType.KNOWLEDGE,
                tags=["support", "resolution", "faq"],
                importance_score=0.7,
                metadata={
                    "ticket_number": ticket.number,
                    "source": "ticket_resolution",
                }
            )

            return True

        except Exception as e:
            logger.warning(f"[MARCEAU] Echec ajout knowledge: {e}")
            return False

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    async def _generate_ticket_number(self) -> str:
        """Genere un numero de ticket unique."""
        from app.modules.helpdesk.models import Ticket

        year = datetime.now().year
        month = datetime.now().month

        # Trouver le dernier numero
        pattern = f"TKT-{year}{month:02d}-%"
        last = self.db.query(Ticket).filter(
            Ticket.tenant_id == self.tenant_id,
            Ticket.number.like(pattern),
        ).order_by(Ticket.number.desc()).first()

        if last and last.number:
            try:
                num = int(last.number.split("-")[2]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        return f"TKT-{year}{month:02d}-{num:05d}"

    async def _unknown_action(self, data: dict, context: list[str]) -> dict:
        """Action non reconnue."""
        return {
            "success": False,
            "error": "Action non reconnue",
            "available_actions": ["create_ticket", "respond_ticket", "escalate", "resolve"],
            "module": "support"
        }
