"""
AZALS MODULE - Marceau Telephony Service
==========================================

Service principal de gestion telephonique.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.modules.marceau.config import get_or_create_marceau_config
from app.modules.marceau.models import (
    ActionStatus,
    ConversationOutcome,
    MarceauAction,
    MarceauConversation,
    MemoryType,
    ModuleName,
)

logger = logging.getLogger(__name__)


class TelephonyService:
    """
    Service de gestion de la telephonie.
    Gere les appels entrants, sortants, et les actions associees.
    """

    def __init__(self, tenant_id: str, db: Session):
        """
        Initialise le service telephonie.

        Args:
            tenant_id: ID du tenant
            db: Session SQLAlchemy
        """
        self.tenant_id = tenant_id
        self.db = db
        self.config = None

    async def initialize(self):
        """Charge la configuration."""
        self.config = get_or_create_marceau_config(self.tenant_id, self.db)

    async def execute_action(
        self,
        action: str,
        data: dict,
        context: list[str]
    ) -> dict:
        """
        Execute une action telephonie.

        Args:
            action: Nom de l'action
            data: Donnees de la requete
            context: Contexte RAG

        Returns:
            Resultat de l'action
        """
        if not self.config:
            await self.initialize()

        action_handlers = {
            "handle_incoming_call": self._handle_incoming_call,
            "create_quote": self._create_quote_from_call,
            "schedule_appointment": self._schedule_appointment,
            "transfer_call": self._transfer_call,
            "end_call": self._end_call,
            "unknown": self._handle_unknown,
        }

        handler = action_handlers.get(action, self._handle_unknown)
        return await handler(data, context)

    async def _handle_incoming_call(self, data: dict, context: list[str]) -> dict:
        """
        Gere un appel entrant.

        Args:
            data: Donnees de l'appel (caller_phone, asterisk_call_id, etc.)
            context: Contexte RAG

        Returns:
            Resultat du traitement
        """
        caller_phone = data.get("caller_phone", "")
        caller_name = data.get("caller_name")
        asterisk_call_id = data.get("asterisk_call_id")

        # Creer la conversation
        conversation = MarceauConversation(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            caller_phone=caller_phone,
            caller_name=caller_name,
            asterisk_call_id=asterisk_call_id,
            asterisk_channel=data.get("asterisk_channel"),
            started_at=datetime.utcnow(),
        )

        self.db.add(conversation)

        # Chercher si client existant
        customer = await self._find_customer_by_phone(caller_phone)
        if customer:
            conversation.customer_id = customer.get("id")
            conversation.caller_name = customer.get("name")

        # Creer l'action
        action = MarceauAction(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            module=ModuleName.TELEPHONIE,
            action_type="call_received",
            status=ActionStatus.IN_PROGRESS,
            input_data=data,
            conversation_id=conversation.id,
            confidence_score=1.0,
        )

        self.db.add(action)
        self.db.commit()
        self.db.refresh(conversation)

        # Message d'accueil
        greeting = await self._generate_greeting(caller_name, customer)

        return {
            "success": True,
            "conversation_id": str(conversation.id),
            "action_id": str(action.id),
            "greeting": greeting,
            "customer_found": customer is not None,
            "customer": customer,
        }

    async def _create_quote_from_call(self, data: dict, context: list[str]) -> dict:
        """
        Cree un devis depuis un appel telephonique.

        Args:
            data: Donnees du devis
            context: Contexte RAG

        Returns:
            Resultat de creation
        """
        required_fields = ["customer_name", "phone", "description"]
        missing = [f for f in required_fields if not data.get(f)]

        if missing:
            return {
                "success": False,
                "error": f"Champs manquants: {', '.join(missing)}",
                "missing_fields": missing,
            }

        try:
            # Importer le service commercial
            from app.modules.commercial.models import (
                CommercialDocument,
                Customer,
                DocumentLine,
                DocumentStatus,
                DocumentType,
            )

            # Creer ou recuperer le client
            customer = await self._get_or_create_customer(data)

            # Generer numero de devis
            quote_number = await self._generate_quote_number()

            # Creer le devis
            quote = CommercialDocument(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                customer_id=customer.id,
                type=DocumentType.QUOTE,
                number=quote_number,
                status=DocumentStatus.DRAFT,
                notes=data.get("description", ""),
            )

            self.db.add(quote)

            # Ajouter les lignes si articles fournis
            articles = data.get("articles", [])
            for i, article in enumerate(articles):
                line = DocumentLine(
                    id=uuid.uuid4(),
                    tenant_id=self.tenant_id,
                    document_id=quote.id,
                    line_number=i + 1,
                    product_id=article.get("article_id"),
                    description=article.get("description", ""),
                    quantity=article.get("quantity", 1),
                    unit_price=article.get("unit_price", 0),
                )
                self.db.add(line)

            # Creer l'action
            action = MarceauAction(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                module=ModuleName.TELEPHONIE,
                action_type="quote_created",
                status=ActionStatus.COMPLETED,
                input_data=data,
                output_data={"quote_id": str(quote.id), "quote_number": quote_number},
                related_entity_type="CommercialDocument",
                related_entity_id=quote.id,
                confidence_score=0.95,
            )

            self.db.add(action)
            self.db.commit()
            self.db.refresh(quote)

            # Mettre a jour stats config
            config = get_or_create_marceau_config(self.tenant_id, self.db)
            config.total_quotes_created = (config.total_quotes_created or 0) + 1
            self.db.commit()

            logger.info(f"[MARCEAU] Devis {quote_number} cree pour tenant {self.tenant_id}")

            return {
                "success": True,
                "quote_id": str(quote.id),
                "quote_number": quote_number,
                "customer_id": str(customer.id),
                "action_id": str(action.id),
                "message": f"Devis {quote_number} cree avec succes",
            }

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur creation devis: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _schedule_appointment(self, data: dict, context: list[str]) -> dict:
        """
        Planifie un rendez-vous technique.

        Args:
            data: Donnees du RDV (address, description, preferred_date, etc.)
            context: Contexte RAG

        Returns:
            Resultat de planification
        """
        required_fields = ["address", "description"]
        missing = [f for f in required_fields if not data.get(f)]

        if missing:
            return {
                "success": False,
                "error": f"Champs manquants: {', '.join(missing)}",
                "missing_fields": missing,
            }

        try:
            # 1. Geocoder l'adresse
            address = data.get("address")
            coords = await self._geocode_address(address)

            if not coords:
                return {
                    "success": False,
                    "error": "Impossible de geocoder l'adresse",
                    "address": address,
                }

            # 2. Trouver la zone de service
            zone = await self._find_service_zone(coords)

            if not zone:
                return {
                    "success": False,
                    "error": "Nous n'intervenons pas dans ce secteur",
                    "address": address,
                    "suggestion": "Proposer de rappeler pour etendre la zone",
                }

            # 3. Chercher des creneaux disponibles
            preferred_date = data.get("preferred_date") or datetime.utcnow().date()
            max_date = preferred_date + timedelta(days=14)

            available_slots = await self._find_available_slots(
                zone_id=zone.get("id"),
                date_from=preferred_date,
                date_to=max_date,
                address=address,
                duration_minutes=self.config.telephony_config.get("appointment_duration_minutes", 60)
            )

            if not available_slots:
                return {
                    "success": False,
                    "error": "Aucun creneau disponible sous 14 jours",
                    "requires_manager_alert": True,
                    "suggestion": "Alerter le manager et proposer de rappeler",
                }

            # 4. Si un creneau est choisi, creer l'intervention
            chosen_slot = data.get("chosen_slot")
            if chosen_slot:
                intervention = await self._create_intervention(
                    data=data,
                    slot=chosen_slot,
                    zone=zone
                )

                # Mettre a jour stats
                config = get_or_create_marceau_config(self.tenant_id, self.db)
                config.total_appointments_scheduled = (config.total_appointments_scheduled or 0) + 1
                self.db.commit()

                return {
                    "success": True,
                    "intervention_id": str(intervention.get("id")),
                    "scheduled_date": chosen_slot.get("start"),
                    "technician_name": chosen_slot.get("technician_name"),
                    "message": "Rendez-vous confirme",
                }

            # Sinon, proposer les creneaux
            return {
                "success": True,
                "action": "propose_slots",
                "available_slots": available_slots[:3],  # Top 3
                "total_available": len(available_slots),
                "message": "Creneaux disponibles trouves",
            }

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur planification RDV: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _transfer_call(self, data: dict, context: list[str]) -> dict:
        """Transfere l'appel vers un autre numero."""
        target = data.get("target")
        reason = data.get("reason", "Transfert demande")
        conversation_id = data.get("conversation_id")

        if not target:
            return {
                "success": False,
                "error": "Numero de destination requis",
            }

        # Mettre a jour la conversation
        if conversation_id:
            conversation = self.db.query(MarceauConversation).filter(
                MarceauConversation.id == uuid.UUID(conversation_id),
                MarceauConversation.tenant_id == self.tenant_id
            ).first()

            if conversation:
                conversation.outcome = ConversationOutcome.TRANSFERRED
                conversation.transferred_to = target
                conversation.transfer_reason = reason
                conversation.ended_at = datetime.utcnow()
                self.db.commit()

        # TODO: Appeler Asterisk pour transferer

        return {
            "success": True,
            "transferred_to": target,
            "reason": reason,
        }

    async def _end_call(self, data: dict, context: list[str]) -> dict:
        """Termine un appel."""
        conversation_id = data.get("conversation_id")
        outcome = data.get("outcome", ConversationOutcome.INFORMATION_PROVIDED)
        transcript = data.get("transcript")
        summary = data.get("summary")

        if conversation_id:
            conversation = self.db.query(MarceauConversation).filter(
                MarceauConversation.id == uuid.UUID(conversation_id),
                MarceauConversation.tenant_id == self.tenant_id
            ).first()

            if conversation:
                conversation.ended_at = datetime.utcnow()
                conversation.outcome = ConversationOutcome(outcome) if isinstance(outcome, str) else outcome
                conversation.transcript = transcript
                conversation.summary = summary

                if conversation.ended_at and conversation.started_at:
                    conversation.duration_seconds = int(
                        (conversation.ended_at - conversation.started_at).total_seconds()
                    )

                self.db.commit()

                # Mettre a jour stats
                config = get_or_create_marceau_config(self.tenant_id, self.db)
                config.total_conversations = (config.total_conversations or 0) + 1
                self.db.commit()

        return {
            "success": True,
            "conversation_id": conversation_id,
            "outcome": outcome,
        }

    async def _handle_unknown(self, data: dict, context: list[str]) -> dict:
        """Gere une action inconnue."""
        return {
            "success": False,
            "error": "Action non reconnue",
            "suggestion": "Reformuler la demande",
        }

    # ========================================================================
    # HELPERS
    # ========================================================================

    async def _find_customer_by_phone(self, phone: str) -> dict | None:
        """Cherche un client par numero de telephone."""
        from app.modules.commercial.models import Customer

        customer = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            (Customer.phone == phone) | (Customer.mobile == phone)
        ).first()

        if customer:
            return {
                "id": str(customer.id),
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
            }
        return None

    async def _get_or_create_customer(self, data: dict):
        """Cree ou recupere un client."""
        from app.modules.commercial.models import Customer, CustomerType

        phone = data.get("phone", "")

        # Chercher existant
        customer = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            (Customer.phone == phone) | (Customer.mobile == phone)
        ).first()

        if not customer:
            # Generer code client
            count = self.db.query(Customer).filter(
                Customer.tenant_id == self.tenant_id
            ).count()

            customer = Customer(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                code=f"CLI{count + 1:05d}",
                name=data.get("customer_name", "Client"),
                phone=phone,
                email=data.get("email"),
                address_line1=data.get("address"),
                type=CustomerType.PROSPECT,
            )
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)

        return customer

    async def _generate_quote_number(self) -> str:
        """Genere un numero de devis unique."""
        from app.modules.commercial.models import CommercialDocument, DocumentType

        year = datetime.utcnow().year
        count = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.type == DocumentType.QUOTE
        ).count()

        return f"DEV-{year}-{count + 1:05d}"

    async def _geocode_address(self, address: str) -> dict | None:
        """Geocode une adresse."""
        # Utiliser OpenRouteService si configure
        ors_key = self.config.integrations.get("ors_api_key") if self.config else None

        if ors_key:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.openrouteservice.org/geocode/search",
                        params={"api_key": ors_key, "text": address, "size": 1},
                    )
                    data = response.json()

                    if data.get("features"):
                        coords = data["features"][0]["geometry"]["coordinates"]
                        return {"lng": coords[0], "lat": coords[1]}
            except Exception as e:
                logger.warning(f"[MARCEAU] Erreur geocodage ORS: {e}")

        # Fallback: coordonnees fictives pour dev
        logger.warning("[MARCEAU] Geocodage non configure - utilisation coords fictives")
        return {"lat": 48.8566, "lng": 2.3522}  # Paris par defaut

    async def _find_service_zone(self, coords: dict) -> dict | None:
        """Trouve la zone de service pour des coordonnees."""
        from app.modules.field_service.models import ServiceZone

        # Pour l'instant, retourner la premiere zone active
        zone = self.db.query(ServiceZone).filter(
            ServiceZone.tenant_id == self.tenant_id,
            ServiceZone.is_active == True
        ).first()

        if zone:
            return {
                "id": str(zone.id),
                "name": zone.name,
                "code": zone.code,
            }
        return None

    async def _find_available_slots(
        self,
        zone_id: str,
        date_from,
        date_to,
        address: str,
        duration_minutes: int
    ) -> list[dict]:
        """Trouve les creneaux disponibles."""
        from app.modules.field_service.models import Intervention, InterventionStatus, Technician

        # Recuperer techniciens de la zone
        technicians = self.db.query(Technician).filter(
            Technician.tenant_id == self.tenant_id,
            Technician.zone_id == uuid.UUID(zone_id),
            Technician.is_active == True
        ).all()

        slots = []

        for tech in technicians:
            # Recuperer interventions existantes
            existing = self.db.query(Intervention).filter(
                Intervention.tenant_id == self.tenant_id,
                Intervention.technician_id == tech.id,
                Intervention.scheduled_date >= date_from,
                Intervention.scheduled_date <= date_to,
                Intervention.status.notin_([
                    InterventionStatus.CANCELLED,
                    InterventionStatus.FAILED
                ])
            ).all()

            # Calculer creneaux libres (simplifie)
            working_hours = self.config.telephony_config.get("working_hours", {})
            start_hour = int(working_hours.get("start", "09:00").split(":")[0])
            end_hour = int(working_hours.get("end", "18:00").split(":")[0])

            current_date = date_from
            while current_date <= date_to:
                # Creneaux du jour
                for hour in range(start_hour, end_hour - 1):
                    slot_start = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
                    slot_end = slot_start + timedelta(minutes=duration_minutes)

                    # Verifier si libre
                    is_free = True
                    for intervention in existing:
                        if intervention.scheduled_date == current_date:
                            if intervention.scheduled_time_start:
                                int_start = datetime.combine(
                                    current_date,
                                    intervention.scheduled_time_start
                                )
                                int_end = int_start + timedelta(
                                    minutes=intervention.estimated_duration or 60
                                )
                                if not (slot_end <= int_start or slot_start >= int_end):
                                    is_free = False
                                    break

                    if is_free:
                        slots.append({
                            "technician_id": str(tech.id),
                            "technician_name": f"{tech.first_name} {tech.last_name}",
                            "start": slot_start.isoformat(),
                            "end": slot_end.isoformat(),
                            "travel_time_minutes": 15,  # A calculer avec ORS
                            "distance_km": 5.0,  # A calculer
                        })

                current_date += timedelta(days=1)

        # Trier par date
        slots.sort(key=lambda s: s["start"])

        return slots

    async def _create_intervention(self, data: dict, slot: dict, zone: dict) -> dict:
        """Cree une intervention."""
        from app.modules.field_service.models import Intervention, InterventionStatus, InterventionType

        # Generer reference
        count = self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id
        ).count()

        reference = f"INT-{datetime.utcnow().year}-{count + 1:05d}"

        # Parser dates
        start = datetime.fromisoformat(slot["start"])

        intervention = Intervention(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            reference=reference,
            intervention_type=InterventionType.MAINTENANCE,
            status=InterventionStatus.SCHEDULED,
            title=data.get("description", "Intervention")[:500],
            description=data.get("description"),
            customer_name=data.get("customer_name"),
            contact_phone=data.get("phone"),
            address_street=data.get("address"),
            technician_id=uuid.UUID(slot["technician_id"]),
            zone_id=uuid.UUID(zone["id"]),
            scheduled_date=start.date(),
            scheduled_time_start=start.time(),
            scheduled_time_end=(start + timedelta(minutes=60)).time(),
            estimated_duration=60,
        )

        self.db.add(intervention)

        # Creer action
        action = MarceauAction(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            module=ModuleName.TELEPHONIE,
            action_type="appointment_scheduled",
            status=ActionStatus.COMPLETED,
            input_data=data,
            output_data={
                "intervention_id": str(intervention.id),
                "reference": reference,
                "slot": slot
            },
            related_entity_type="Intervention",
            related_entity_id=intervention.id,
            confidence_score=0.95,
        )

        self.db.add(action)
        self.db.commit()
        self.db.refresh(intervention)

        logger.info(f"[MARCEAU] Intervention {reference} creee pour tenant {self.tenant_id}")

        return {
            "id": str(intervention.id),
            "reference": reference,
            "scheduled_date": str(intervention.scheduled_date),
            "technician_id": slot["technician_id"],
            "technician_name": slot["technician_name"],
        }

    async def _generate_greeting(self, caller_name: str | None, customer: dict | None) -> str:
        """Genere un message d'accueil personnalise."""
        if customer:
            name = customer.get("name", caller_name or "")
            return f"Bonjour {name}, bienvenue. Comment puis-je vous aider aujourd'hui?"
        elif caller_name:
            return f"Bonjour {caller_name}, bienvenue. Comment puis-je vous aider?"
        else:
            return "Bonjour et bienvenue. Comment puis-je vous aider?"
