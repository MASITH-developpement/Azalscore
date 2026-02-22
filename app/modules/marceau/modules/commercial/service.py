"""
AZALS MODULE - Marceau Commercial Service
==========================================

Service de gestion commerciale automatisee.
Integration complete avec les modules commercial et email d'AZALSCORE.

Actions:
- create_quote: Creation devis automatique
- send_quote: Envoi devis par email
- follow_up: Relance automatique devis
- sync_crm: Synchronisation HubSpot
"""

import logging
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.modules.marceau.models import ActionStatus, MarceauAction, ModuleName

logger = logging.getLogger(__name__)


class CommercialService:
    """
    Service commercial Marceau.
    Gere la creation automatique de devis, suivi clients, CRM sync.
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
        """Execute une action commerciale."""
        action_handlers = {
            "create_quote": self._create_quote,
            "send_quote": self._send_quote,
            "follow_up": self._follow_up,
            "sync_crm": self._sync_crm,
        }

        handler = action_handlers.get(action, self._unknown_action)
        return await handler(data, context)

    # =========================================================================
    # CREATE QUOTE
    # =========================================================================

    async def _create_quote(self, data: dict, context: list[str]) -> dict:
        """
        Cree un devis automatiquement.

        Args:
            data: {
                "customer_name": str (obligatoire)
                "customer_email": str (optionnel)
                "customer_phone": str (optionnel)
                "description": str (obligatoire)
                "articles": list[{description, quantity, unit_price}] (optionnel)
                "notes": str (optionnel)
                "validity_days": int (defaut: 30)
            }

        Returns:
            Resultat avec quote_id, quote_number
        """
        try:
            # Import des modeles commercial
            from app.modules.commercial.models import (
                CommercialDocument,
                Customer,
                CustomerType,
                DocumentLine,
                DocumentStatus,
                DocumentType,
            )

            # Validation champs obligatoires
            required_fields = ["customer_name", "description"]
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                return {
                    "success": False,
                    "error": f"Champs obligatoires manquants: {', '.join(missing)}",
                    "missing_fields": missing,
                    "module": "commercial"
                }

            # 1. Recuperer ou creer le client
            customer = await self._get_or_create_customer(
                name=data["customer_name"],
                email=data.get("customer_email"),
                phone=data.get("customer_phone"),
            )

            # 2. Generer numero de devis
            quote_number = await self._generate_document_number("DEV")

            # 3. Calculer dates
            validity_days = data.get("validity_days", 30)
            validity_date = date.today() + timedelta(days=validity_days)

            # 4. Creer le devis
            quote = CommercialDocument(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                customer_id=customer.id,
                type=DocumentType.QUOTE,
                number=quote_number,
                status=DocumentStatus.DRAFT,
                date=date.today(),
                validity_date=validity_date,
                notes=data.get("description", ""),
                internal_notes=data.get("notes", ""),
                currency="EUR",
                subtotal=Decimal("0.00"),
                tax_amount=Decimal("0.00"),
                total=Decimal("0.00"),
            )

            self.db.add(quote)

            # 5. Ajouter les lignes si articles fournis
            articles = data.get("articles", [])
            line_number = 0
            subtotal = Decimal("0.00")

            for article in articles:
                line_number += 1
                quantity = Decimal(str(article.get("quantity", 1)))
                unit_price = Decimal(str(article.get("unit_price", 0)))
                line_total = quantity * unit_price

                line = DocumentLine(
                    id=uuid.uuid4(),
                    tenant_id=self.tenant_id,
                    document_id=quote.id,
                    line_number=line_number,
                    description=article.get("description", "Article"),
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_percent=Decimal("0.00"),
                    tax_rate=Decimal("20.00"),  # TVA standard
                    line_total=line_total,
                )
                self.db.add(line)
                subtotal += line_total

            # 6. Calculer totaux
            tax_rate = Decimal("0.20")  # 20% TVA
            tax_amount = subtotal * tax_rate
            total = subtotal + tax_amount

            quote.subtotal = subtotal
            quote.tax_amount = tax_amount
            quote.total = total

            # 7. Creer l'action Marceau
            action = MarceauAction(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                module=ModuleName.COMMERCIAL,
                action_type="quote_created",
                status=ActionStatus.COMPLETED,
                input_data=data,
                output_data={
                    "quote_id": str(quote.id),
                    "quote_number": quote_number,
                    "customer_id": str(customer.id),
                    "total": str(total),
                },
                related_entity_type="CommercialDocument",
                related_entity_id=quote.id,
                confidence_score=0.95,
            )

            self.db.add(action)
            self.db.commit()
            self.db.refresh(quote)

            logger.info(f"[MARCEAU] Devis {quote_number} cree - {total}EUR")

            return {
                "success": True,
                "quote_id": str(quote.id),
                "quote_number": quote_number,
                "customer_id": str(customer.id),
                "customer_name": customer.name,
                "subtotal": str(subtotal),
                "tax_amount": str(tax_amount),
                "total": str(total),
                "validity_date": validity_date.isoformat(),
                "line_count": line_number,
                "action_id": str(action.id),
                "message": f"Devis {quote_number} cree avec succes pour {customer.name}",
                "module": "commercial"
            }

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur creation devis: {e}")
            return {
                "success": False,
                "error": str(e),
                "module": "commercial"
            }

    # =========================================================================
    # SEND QUOTE
    # =========================================================================

    async def _send_quote(self, data: dict, context: list[str]) -> dict:
        """
        Envoie un devis par email.

        Args:
            data: {
                "quote_id": str (obligatoire)
                "recipient_email": str (optionnel, sinon email client)
                "subject": str (optionnel)
                "message": str (optionnel)
            }

        Returns:
            Resultat avec email_sent, email_id
        """
        try:
            from app.modules.commercial.models import CommercialDocument, DocumentStatus
            from app.modules.email.service import EmailService

            quote_id = data.get("quote_id")
            if not quote_id:
                return {
                    "success": False,
                    "error": "quote_id obligatoire",
                    "module": "commercial"
                }

            # Recuperer le devis
            quote = self.db.query(CommercialDocument).filter(
                CommercialDocument.id == uuid.UUID(quote_id),
                CommercialDocument.tenant_id == self.tenant_id
            ).first()

            if not quote:
                return {
                    "success": False,
                    "error": f"Devis {quote_id} non trouve",
                    "module": "commercial"
                }

            # Recuperer le client
            from app.modules.commercial.models import Customer
            customer = self.db.query(Customer).filter(
                Customer.id == quote.customer_id
            ).first()

            if not customer:
                return {
                    "success": False,
                    "error": "Client du devis non trouve",
                    "module": "commercial"
                }

            # Email destinataire
            recipient = data.get("recipient_email") or customer.email
            if not recipient:
                return {
                    "success": False,
                    "error": "Aucun email destinataire (client ou parametre)",
                    "module": "commercial"
                }

            # Preparer l'email
            subject = data.get("subject") or f"Devis {quote.number} - {customer.name}"
            message = data.get("message") or self._generate_quote_email_body(quote, customer)

            # Envoyer via EmailService
            email_service = EmailService(self.db, self.tenant_id)

            from app.modules.email.schemas import SendEmailRequest
            email_request = SendEmailRequest(
                to=recipient,
                subject=subject,
                body_html=message,
                body_text=message.replace("<br>", "\n").replace("<p>", "").replace("</p>", "\n"),
            )

            result = email_service.send_email(email_request)

            if result.success:
                # Mettre a jour le statut du devis
                quote.status = DocumentStatus.SENT
                quote.updated_at = datetime.utcnow()

                # Creer action Marceau
                action = MarceauAction(
                    id=uuid.uuid4(),
                    tenant_id=self.tenant_id,
                    module=ModuleName.COMMERCIAL,
                    action_type="quote_sent",
                    status=ActionStatus.COMPLETED,
                    input_data=data,
                    output_data={"email_id": result.email_id, "recipient": recipient},
                    related_entity_type="CommercialDocument",
                    related_entity_id=quote.id,
                    confidence_score=1.0,
                )
                self.db.add(action)
                self.db.commit()

                logger.info(f"[MARCEAU] Devis {quote.number} envoye a {recipient}")

                return {
                    "success": True,
                    "quote_id": str(quote.id),
                    "quote_number": quote.number,
                    "email_sent": True,
                    "email_id": result.email_id,
                    "recipient": recipient,
                    "message": f"Devis {quote.number} envoye a {recipient}",
                    "module": "commercial"
                }
            else:
                return {
                    "success": False,
                    "error": f"Echec envoi email: {result.error}",
                    "module": "commercial"
                }

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur envoi devis: {e}")
            return {
                "success": False,
                "error": str(e),
                "module": "commercial"
            }

    def _generate_quote_email_body(self, quote, customer) -> str:
        """Genere le corps de l'email pour un devis."""
        return f"""
        <p>Bonjour {customer.name},</p>

        <p>Veuillez trouver ci-joint notre devis <strong>{quote.number}</strong>
        d'un montant de <strong>{quote.total} EUR TTC</strong>.</p>

        <p>Ce devis est valable jusqu'au {quote.validity_date.strftime('%d/%m/%Y') if quote.validity_date else 'non defini'}.</p>

        <p>N'hesitez pas a nous contacter pour toute question.</p>

        <p>Cordialement,<br>
        L'equipe commerciale</p>
        """

    # =========================================================================
    # FOLLOW UP
    # =========================================================================

    async def _follow_up(self, data: dict, context: list[str]) -> dict:
        """
        Relance automatique des devis en attente.

        Args:
            data: {
                "days_since_sent": int (defaut: 7)
                "max_followups": int (defaut: 3)
                "quote_id": str (optionnel, sinon tous les devis eligibles)
            }

        Returns:
            Liste des relances effectuees
        """
        try:
            from app.modules.commercial.models import CommercialDocument, Customer, DocumentStatus, DocumentType

            days_since = data.get("days_since_sent", 7)
            max_followups = data.get("max_followups", 3)
            specific_quote_id = data.get("quote_id")

            cutoff_date = datetime.utcnow() - timedelta(days=days_since)

            # Construire la requete
            query = self.db.query(CommercialDocument).filter(
                CommercialDocument.tenant_id == self.tenant_id,
                CommercialDocument.type == DocumentType.QUOTE,
                CommercialDocument.status == DocumentStatus.SENT,
                CommercialDocument.updated_at < cutoff_date,
            )

            if specific_quote_id:
                query = query.filter(CommercialDocument.id == uuid.UUID(specific_quote_id))

            quotes_to_follow = query.all()

            if not quotes_to_follow:
                return {
                    "success": True,
                    "followups_sent": 0,
                    "message": "Aucun devis eligible pour relance",
                    "module": "commercial"
                }

            followups_sent = []
            errors = []

            for quote in quotes_to_follow:
                # Compter les relances precedentes
                previous_followups = self.db.query(MarceauAction).filter(
                    MarceauAction.tenant_id == self.tenant_id,
                    MarceauAction.related_entity_id == quote.id,
                    MarceauAction.action_type == "quote_followup",
                ).count()

                if previous_followups >= max_followups:
                    continue

                # Recuperer le client
                customer = self.db.query(Customer).filter(
                    Customer.id == quote.customer_id
                ).first()

                if not customer or not customer.email:
                    errors.append(f"Devis {quote.number}: client sans email")
                    continue

                # Generer le message de relance avec LLM si disponible
                followup_message = await self._generate_followup_message(
                    quote, customer, previous_followups + 1, context
                )

                # Envoyer la relance
                result = await self._send_quote({
                    "quote_id": str(quote.id),
                    "subject": f"Relance: Devis {quote.number}",
                    "message": followup_message,
                }, context)

                if result.get("success"):
                    # Creer action de relance
                    action = MarceauAction(
                        id=uuid.uuid4(),
                        tenant_id=self.tenant_id,
                        module=ModuleName.COMMERCIAL,
                        action_type="quote_followup",
                        status=ActionStatus.COMPLETED,
                        input_data={"quote_id": str(quote.id), "followup_number": previous_followups + 1},
                        output_data=result,
                        related_entity_type="CommercialDocument",
                        related_entity_id=quote.id,
                        confidence_score=0.9,
                    )
                    self.db.add(action)
                    followups_sent.append({
                        "quote_number": quote.number,
                        "customer": customer.name,
                        "followup_number": previous_followups + 1,
                    })
                else:
                    errors.append(f"Devis {quote.number}: {result.get('error')}")

            self.db.commit()

            logger.info(f"[MARCEAU] {len(followups_sent)} relances envoyees")

            return {
                "success": True,
                "followups_sent": len(followups_sent),
                "details": followups_sent,
                "errors": errors if errors else None,
                "message": f"{len(followups_sent)} relance(s) envoyee(s)",
                "module": "commercial"
            }

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur relance devis: {e}")
            return {
                "success": False,
                "error": str(e),
                "module": "commercial"
            }

    async def _generate_followup_message(
        self, quote, customer, followup_number: int, context: list[str]
    ) -> str:
        """Genere un message de relance personnalise."""
        try:
            from app.modules.marceau.llm_client import get_llm_client_for_tenant

            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            prompt = f"""
Genere un email de relance professionnel et personnalise pour un devis.

Informations:
- Client: {customer.name}
- Devis numero: {quote.number}
- Montant: {quote.total} EUR
- Date du devis: {quote.date}
- Relance numero: {followup_number}

Contexte entreprise:
{chr(10).join(context[:3]) if context else "Aucun contexte specifique"}

Consignes:
- Ton professionnel mais chaleureux
- Ne pas etre trop insistant
- Proposer de repondre aux questions
- Format HTML simple (balises p, br, strong uniquement)
- Maximum 150 mots
"""

            response = await llm.generate(prompt, temperature=0.7, max_tokens=300)

            # Verifier que la reponse est du HTML valide
            if "<p>" in response or "<br>" in response:
                return response
            else:
                # Fallback si pas de HTML
                return f"<p>{response}</p>"

        except Exception as e:
            logger.warning(f"[MARCEAU] LLM indisponible pour relance, fallback: {e}")
            # Fallback sans LLM
            return f"""
            <p>Bonjour {customer.name},</p>

            <p>Nous nous permettons de revenir vers vous concernant notre devis
            <strong>{quote.number}</strong> du {quote.date.strftime('%d/%m/%Y')}
            d'un montant de <strong>{quote.total} EUR</strong>.</p>

            <p>Avez-vous eu l'occasion de l'examiner ? Nous restons a votre disposition
            pour toute question ou information complementaire.</p>

            <p>Cordialement,<br>
            L'equipe commerciale</p>
            """

    # =========================================================================
    # SYNC CRM (HUBSPOT)
    # =========================================================================

    async def _sync_crm(self, data: dict, context: list[str]) -> dict:
        """
        Synchronise les donnees avec HubSpot CRM.

        Args:
            data: {
                "sync_type": str (contacts|deals|all)
                "direction": str (push|pull|both)
                "since": str (date ISO, optionnel)
            }

        Returns:
            Statistiques de synchronisation
        """
        try:
            from app.modules.marceau.config import get_or_create_marceau_config

            config = get_or_create_marceau_config(self.tenant_id, self.db)
            hubspot_key = config.integrations.get("hubspot_api_key") if config.integrations else None

            if not hubspot_key:
                return {
                    "success": False,
                    "error": "Cle API HubSpot non configuree. Configurez-la dans Administration > Marceau > Integrations.",
                    "module": "commercial"
                }

            sync_type = data.get("sync_type", "all")
            direction = data.get("direction", "both")
            since_date = data.get("since")

            stats = {
                "contacts_pushed": 0,
                "contacts_pulled": 0,
                "deals_pushed": 0,
                "deals_pulled": 0,
                "errors": [],
            }

            # Synchronisation des contacts
            if sync_type in ["contacts", "all"]:
                if direction in ["push", "both"]:
                    result = await self._push_contacts_to_hubspot(hubspot_key, since_date)
                    stats["contacts_pushed"] = result.get("count", 0)
                    if result.get("errors"):
                        stats["errors"].extend(result["errors"])

                if direction in ["pull", "both"]:
                    result = await self._pull_contacts_from_hubspot(hubspot_key, since_date)
                    stats["contacts_pulled"] = result.get("count", 0)
                    if result.get("errors"):
                        stats["errors"].extend(result["errors"])

            # Synchronisation des deals (opportunites)
            if sync_type in ["deals", "all"]:
                if direction in ["push", "both"]:
                    result = await self._push_deals_to_hubspot(hubspot_key, since_date)
                    stats["deals_pushed"] = result.get("count", 0)
                    if result.get("errors"):
                        stats["errors"].extend(result["errors"])

                if direction in ["pull", "both"]:
                    result = await self._pull_deals_from_hubspot(hubspot_key, since_date)
                    stats["deals_pulled"] = result.get("count", 0)
                    if result.get("errors"):
                        stats["errors"].extend(result["errors"])

            # Creer action
            total_synced = (
                stats["contacts_pushed"] + stats["contacts_pulled"] +
                stats["deals_pushed"] + stats["deals_pulled"]
            )

            action = MarceauAction(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                module=ModuleName.COMMERCIAL,
                action_type="crm_sync",
                status=ActionStatus.COMPLETED,
                input_data=data,
                output_data=stats,
                confidence_score=1.0,
            )
            self.db.add(action)
            self.db.commit()

            logger.info(f"[MARCEAU] Sync CRM: {total_synced} elements synchronises")

            return {
                "success": True,
                "stats": stats,
                "total_synced": total_synced,
                "message": f"Synchronisation terminee: {total_synced} element(s)",
                "module": "commercial"
            }

        except Exception as e:
            logger.exception(f"[MARCEAU] Erreur sync CRM: {e}")
            return {
                "success": False,
                "error": str(e),
                "module": "commercial"
            }

    async def _push_contacts_to_hubspot(self, api_key: str, since: str | None) -> dict:
        """Pousse les clients vers HubSpot."""
        import httpx
        from app.modules.commercial.models import Customer

        query = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.is_active == True,
        )

        if since:
            query = query.filter(Customer.updated_at >= datetime.fromisoformat(since))

        customers = query.limit(100).all()
        count = 0
        errors = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for customer in customers:
                try:
                    # Preparer les donnees HubSpot
                    properties = {
                        "company": customer.name,
                        "email": customer.email or "",
                        "phone": customer.phone or "",
                        "address": customer.address_line1 or "",
                        "city": customer.city or "",
                        "zip": customer.postal_code or "",
                        "country": customer.country_code or "FR",
                    }

                    # Creer ou mettre a jour le contact
                    response = await client.post(
                        "https://api.hubapi.com/crm/v3/objects/contacts",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json={"properties": properties}
                    )

                    if response.status_code in [200, 201]:
                        count += 1
                    elif response.status_code == 409:
                        # Contact existe deja, ignorer
                        pass
                    else:
                        errors.append(f"Client {customer.name}: {response.text[:100]}")

                except Exception as e:
                    errors.append(f"Client {customer.name}: {str(e)[:50]}")

        return {"count": count, "errors": errors}

    async def _pull_contacts_from_hubspot(self, api_key: str, since: str | None) -> dict:
        """Recupere les contacts depuis HubSpot."""
        # Implementation simplifiee - recuperation basique
        return {"count": 0, "errors": [], "message": "Pull contacts non implemente"}

    async def _push_deals_to_hubspot(self, api_key: str, since: str | None) -> dict:
        """Pousse les opportunites vers HubSpot."""
        from app.modules.commercial.models import Opportunity

        query = self.db.query(Opportunity).filter(
            Opportunity.tenant_id == self.tenant_id,
        )

        if since:
            query = query.filter(Opportunity.updated_at >= datetime.fromisoformat(since))

        opportunities = query.limit(100).all()
        count = 0
        errors = []

        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            for opp in opportunities:
                try:
                    properties = {
                        "dealname": opp.name,
                        "amount": str(opp.amount) if opp.amount else "0",
                        "dealstage": self._map_stage_to_hubspot(opp.status.value if opp.status else "NEW"),
                        "closedate": opp.expected_close_date.isoformat() if opp.expected_close_date else None,
                    }

                    response = await client.post(
                        "https://api.hubapi.com/crm/v3/objects/deals",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json={"properties": properties}
                    )

                    if response.status_code in [200, 201]:
                        count += 1
                    else:
                        errors.append(f"Opportunite {opp.name}: {response.text[:100]}")

                except Exception as e:
                    errors.append(f"Opportunite {opp.name}: {str(e)[:50]}")

        return {"count": count, "errors": errors}

    async def _pull_deals_from_hubspot(self, api_key: str, since: str | None) -> dict:
        """Recupere les deals depuis HubSpot."""
        return {"count": 0, "errors": [], "message": "Pull deals non implemente"}

    def _map_stage_to_hubspot(self, status: str) -> str:
        """Mappe les statuts AZALSCORE vers HubSpot."""
        mapping = {
            "NEW": "appointmentscheduled",
            "QUALIFIED": "qualifiedtobuy",
            "PROPOSAL": "presentationscheduled",
            "NEGOTIATION": "decisionmakerboughtin",
            "WON": "closedwon",
            "LOST": "closedlost",
        }
        return mapping.get(status, "appointmentscheduled")

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    async def _get_or_create_customer(
        self, name: str, email: str | None = None, phone: str | None = None
    ):
        """Recupere ou cree un client."""
        from app.modules.commercial.models import Customer, CustomerType

        # Chercher par email ou nom
        query = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
        )

        if email:
            existing = query.filter(Customer.email == email).first()
            if existing:
                return existing

        existing = query.filter(Customer.name == name).first()
        if existing:
            return existing

        # Creer nouveau client
        code = await self._generate_customer_code()

        customer = Customer(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            email=email,
            phone=phone,
            type=CustomerType.PROSPECT,
            is_active=True,
        )

        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        logger.info(f"[MARCEAU] Client cree: {name} ({code})")
        return customer

    async def _generate_customer_code(self) -> str:
        """Genere un code client unique."""
        from app.modules.commercial.models import Customer

        # Trouver le dernier code
        last = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.code.like("CLI-%"),
        ).order_by(Customer.code.desc()).first()

        if last and last.code:
            try:
                num = int(last.code.split("-")[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        return f"CLI-{num:05d}"

    async def _generate_document_number(self, prefix: str) -> str:
        """Genere un numero de document unique."""
        from app.modules.commercial.models import CommercialDocument

        year = datetime.now().year

        # Trouver le dernier numero pour ce type et cette annee
        pattern = f"{prefix}-{year}-%"
        last = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.number.like(pattern),
        ).order_by(CommercialDocument.number.desc()).first()

        if last and last.number:
            try:
                num = int(last.number.split("-")[2]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        return f"{prefix}-{year}-{num:05d}"

    async def _unknown_action(self, data: dict, context: list[str]) -> dict:
        """Action non reconnue."""
        return {
            "success": False,
            "error": "Action non reconnue",
            "available_actions": ["create_quote", "send_quote", "follow_up", "sync_crm"],
            "module": "commercial"
        }
