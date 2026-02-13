"""
AZALS MODULE M1 - Service Commercial
=====================================

Service pour le CRM et la gestion commerciale.
"""

import csv
import io
import logging
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

logger = logging.getLogger(__name__)

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from .models import (
    CatalogProduct,
    CommercialDocument,
    Contact,
    Customer,
    CustomerActivity,
    CustomerType,
    DocumentLine,
    DocumentStatus,
    DocumentType,
    Opportunity,
    OpportunityStatus,
    Payment,
    PipelineStage,
)
from .schemas import (
    ActivityCreate,
    ContactCreate,
    ContactUpdate,
    CustomerCreate,
    CustomerUpdate,
    DocumentCreate,
    DocumentLineCreate,
    DocumentUpdate,
    OpportunityCreate,
    OpportunityUpdate,
    PaymentCreate,
    PipelineStageCreate,
    PipelineStats,
    ProductCreate,
    ProductUpdate,
    SalesDashboard,
)


class CommercialService:
    """Service pour la gestion commerciale."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # GESTION DES CLIENTS
    # ========================================================================

    def create_customer(self, data: CustomerCreate, user_id: UUID) -> Customer:
        """Créer un client avec code auto-généré si non fourni."""
        from app.core.sequences import SequenceGenerator

        logger.info(
            "Creating customer | tenant=%s user=%s name=%s type=%s",
            self.tenant_id, user_id, data.name, data.type
        )

        data_dict = data.model_dump(by_alias=True, exclude_unset=False)

        # Auto-génère le code si non fourni ou vide
        if not data_dict.get('code'):
            seq = SequenceGenerator(self.db, self.tenant_id)
            data_dict['code'] = seq.next_reference("CLIENT")

        customer = Customer(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data_dict
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        logger.info("Customer created | id=%s code=%s", customer.id, customer.code)

        return customer

    def get_customer(self, customer_id: UUID) -> Customer | None:
        """Récupérer un client par ID."""
        return self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.id == customer_id
        ).first()

    def get_customer_by_code(self, code: str) -> Customer | None:
        """Récupérer un client par code."""
        return self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.code == code
        ).first()

    def get_next_customer_code(self) -> str:
        """Générer le prochain code client auto-incrémenté (CLI001, CLI002, etc.)."""
        # Chercher le dernier code client avec le format CLI###
        from sqlalchemy import desc
        last_customer = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.code.like("CLI%")
        ).order_by(desc(Customer.code)).first()

        if last_customer and last_customer.code.startswith("CLI"):
            try:
                # Extraire le numéro et incrémenter
                last_number = int(last_customer.code[3:])
                next_number = last_number + 1
            except ValueError:
                next_number = 1
        else:
            next_number = 1

        return f"CLI{next_number:03d}"

    def list_customers(
        self,
        type: CustomerType | None = None,
        assigned_to: UUID | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[Customer], int]:
        """Lister les clients avec filtres et eager loading."""
        # Utiliser eager loading pour éviter N+1 queries
        query = self.db.query(Customer).options(
            selectinload(Customer.contacts),
            selectinload(Customer.opportunities)
        ).filter(Customer.tenant_id == self.tenant_id)

        if type:
            query = query.filter(Customer.type == type)
        if assigned_to:
            query = query.filter(Customer.assigned_to == assigned_to)
        if is_active is not None:
            query = query.filter(Customer.is_active == is_active)
        if search:
            search_filter = or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.code.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        total = query.count()
        items = query.order_by(Customer.name).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def list_customers_excluding_suppliers(
        self,
        customer_type: CustomerType | None = None,
        assigned_to: UUID | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[Customer], int]:
        """Lister les clients en excluant les fournisseurs."""
        query = self.db.query(Customer).options(
            selectinload(Customer.contacts),
            selectinload(Customer.opportunities)
        ).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.type != CustomerType.SUPPLIER
        )

        if customer_type:
            query = query.filter(Customer.type == customer_type)
        if assigned_to:
            query = query.filter(Customer.assigned_to == assigned_to)
        if is_active is not None:
            query = query.filter(Customer.is_active == is_active)
        if search:
            search_filter = or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.code.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        total = query.count()
        items = query.order_by(Customer.name).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update_customer(self, customer_id: UUID, data: CustomerUpdate) -> Customer | None:
        """Mettre à jour un client."""
        customer = self.get_customer(customer_id)
        if not customer:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)

        self.db.commit()
        self.db.refresh(customer)
        return customer

    def delete_customer(self, customer_id: UUID) -> bool:
        """Supprimer un client."""
        customer = self.get_customer(customer_id)
        if not customer:
            return False

        self.db.delete(customer)
        self.db.commit()
        return True

    def convert_prospect(self, customer_id: UUID) -> Customer | None:
        """Convertir un prospect en client."""
        customer = self.get_customer(customer_id)
        if not customer:
            return None

        if customer.type in [CustomerType.PROSPECT, CustomerType.LEAD]:
            customer.type = CustomerType.CUSTOMER
            self.db.commit()
            self.db.refresh(customer)
        return customer

    # ========================================================================
    # GESTION DES CONTACTS
    # ========================================================================

    def create_contact(self, data: ContactCreate) -> Contact:
        """Créer un contact."""
        contact = Contact(
            tenant_id=self.tenant_id,
            is_active=True,  # Forcer explicitement is_active
            **data.model_dump()
        )
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def get_contact(self, contact_id: UUID) -> Contact | None:
        """Récupérer un contact."""
        return self.db.query(Contact).filter(
            Contact.tenant_id == self.tenant_id,
            Contact.id == contact_id
        ).first()

    def list_contacts(self, customer_id: UUID) -> list[Contact]:
        """Lister les contacts d'un client."""
        return self.db.query(Contact).filter(
            Contact.tenant_id == self.tenant_id,
            Contact.customer_id == customer_id,
            Contact.is_active
        ).order_by(Contact.is_primary.desc(), Contact.last_name).all()

    def list_all_contacts(
        self,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[Contact], int]:
        """Lister tous les contacts avec pagination."""
        query = self.db.query(Contact).filter(
            Contact.tenant_id == self.tenant_id,
            Contact.is_active
        )

        if search:
            search_filter = or_(
                Contact.first_name.ilike(f"%{search}%"),
                Contact.last_name.ilike(f"%{search}%"),
                Contact.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        total = query.count()
        items = query.order_by(Contact.last_name, Contact.first_name).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update_contact(self, contact_id: UUID, data: ContactUpdate) -> Contact | None:
        """Mettre à jour un contact."""
        contact = self.get_contact(contact_id)
        if not contact:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contact, field, value)

        self.db.commit()
        self.db.refresh(contact)
        return contact

    def delete_contact(self, contact_id: UUID) -> bool:
        """Supprimer un contact."""
        contact = self.get_contact(contact_id)
        if not contact:
            return False

        self.db.delete(contact)
        self.db.commit()
        return True

    # ========================================================================
    # GESTION DES OPPORTUNITÉS
    # ========================================================================

    def create_opportunity(self, data: OpportunityCreate, user_id: UUID) -> Opportunity:
        """Créer une opportunité."""
        logger.info(
            "Creating opportunity | tenant=%s user=%s name=%s customer_id=%s amount=%s",
            self.tenant_id, user_id, data.name, data.customer_id, data.amount
        )

        # Calculer le montant pondéré
        weighted = data.amount * Decimal(data.probability) / 100

        opportunity = Opportunity(
            tenant_id=self.tenant_id,
            created_by=user_id,
            weighted_amount=weighted,
            **data.model_dump()
        )
        self.db.add(opportunity)
        self.db.commit()
        self.db.refresh(opportunity)

        logger.info("Opportunity created | id=%s code=%s", opportunity.id, opportunity.code)

        return opportunity

    def get_opportunity(self, opportunity_id: UUID) -> Opportunity | None:
        """Récupérer une opportunité."""
        return self.db.query(Opportunity).filter(
            Opportunity.tenant_id == self.tenant_id,
            Opportunity.id == opportunity_id
        ).first()

    def list_opportunities(
        self,
        status: OpportunityStatus | None = None,
        customer_id: UUID | None = None,
        assigned_to: UUID | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[Opportunity], int]:
        """Lister les opportunités."""
        query = self.db.query(Opportunity).filter(Opportunity.tenant_id == self.tenant_id)

        if status:
            query = query.filter(Opportunity.status == status)
        if customer_id:
            query = query.filter(Opportunity.customer_id == customer_id)
        if assigned_to:
            query = query.filter(Opportunity.assigned_to == assigned_to)

        total = query.count()
        items = query.order_by(Opportunity.expected_close_date).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update_opportunity(self, opportunity_id: UUID, data: OpportunityUpdate) -> Opportunity | None:
        """Mettre à jour une opportunité."""
        opportunity = self.get_opportunity(opportunity_id)
        if not opportunity:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(opportunity, field, value)

        # Recalculer le montant pondéré
        opportunity.weighted_amount = opportunity.amount * Decimal(opportunity.probability) / 100

        # Marquer comme fermée si gagné/perdu
        if opportunity.status in [OpportunityStatus.WON, OpportunityStatus.LOST]:
            if not opportunity.actual_close_date:
                opportunity.actual_close_date = date.today()

        self.db.commit()
        self.db.refresh(opportunity)
        return opportunity

    def win_opportunity(self, opportunity_id: UUID, win_reason: str = None) -> Opportunity | None:
        """Marquer une opportunité comme gagnée."""
        opportunity = self.get_opportunity(opportunity_id)
        if not opportunity:
            return None

        opportunity.status = OpportunityStatus.WON
        opportunity.probability = 100
        opportunity.weighted_amount = opportunity.amount
        opportunity.actual_close_date = date.today()
        opportunity.win_reason = win_reason

        # Convertir le prospect en client
        customer = self.get_customer(opportunity.customer_id)
        if customer and customer.type in [CustomerType.PROSPECT, CustomerType.LEAD]:
            customer.type = CustomerType.CUSTOMER

        self.db.commit()
        self.db.refresh(opportunity)
        return opportunity

    def lose_opportunity(self, opportunity_id: UUID, loss_reason: str = None) -> Opportunity | None:
        """Marquer une opportunité comme perdue."""
        opportunity = self.get_opportunity(opportunity_id)
        if not opportunity:
            return None

        opportunity.status = OpportunityStatus.LOST
        opportunity.probability = 0
        opportunity.weighted_amount = Decimal("0")
        opportunity.actual_close_date = date.today()
        opportunity.loss_reason = loss_reason

        self.db.commit()
        self.db.refresh(opportunity)
        return opportunity

    # ========================================================================
    # GESTION DES DOCUMENTS COMMERCIAUX
    # ========================================================================

    def _generate_document_number(self, doc_type: DocumentType) -> str:
        """Générer un numéro de document via le système centralisé."""
        from app.core.sequences import SequenceGenerator

        # Mapping type document -> type séquence
        entity_type_map = {
            DocumentType.QUOTE: "DEVIS",
            DocumentType.ORDER: "COMMANDE_CLIENT",
            DocumentType.INVOICE: "FACTURE_VENTE",
            DocumentType.CREDIT_NOTE: "AVOIR_CLIENT",
            DocumentType.PROFORMA: "PROFORMA",
            DocumentType.DELIVERY: "BON_LIVRAISON",
        }

        entity_type = entity_type_map.get(doc_type, "DOCUMENT")
        seq = SequenceGenerator(self.db, self.tenant_id)
        return seq.next_reference(entity_type)

    def _calculate_line_totals(self, line: DocumentLine) -> None:
        """Calculer les totaux d'une ligne."""
        subtotal = line.quantity * line.unit_price
        line.discount_amount = subtotal * Decimal(line.discount_percent) / 100
        line.subtotal = subtotal - line.discount_amount
        line.tax_amount = line.subtotal * Decimal(line.tax_rate) / 100
        line.total = line.subtotal + line.tax_amount

    def _calculate_document_totals(self, document: CommercialDocument) -> None:
        """Recalculer les totaux d'un document."""
        # SÉCURITÉ: Toujours filtrer par tenant_id
        lines = self.db.query(DocumentLine).filter(
            DocumentLine.tenant_id == self.tenant_id,
            DocumentLine.document_id == document.id
        ).all()

        subtotal = sum(l.subtotal for l in lines)
        tax_amount = sum(l.tax_amount for l in lines)

        document.subtotal = subtotal
        document.discount_amount = subtotal * Decimal(document.discount_percent) / 100
        document.tax_amount = tax_amount
        document.total = (subtotal - document.discount_amount + tax_amount +
                         (document.shipping_cost or Decimal("0")))
        document.remaining_amount = document.total - document.paid_amount

    def create_document(self, data: DocumentCreate, user_id: UUID) -> CommercialDocument:
        """Créer un document commercial."""
        logger.info(
            "Creating document | tenant=%s user=%s type=%s customer_id=%s lines_count=%d",
            self.tenant_id, user_id, data.document_type, data.customer_id, len(data.lines)
        )

        # Générer le numéro
        number = self._generate_document_number(data.document_type)

        # Créer le document (by_alias=True pour mapper document_type->type, doc_date->date)
        doc_data = data.model_dump(exclude={'lines'}, by_alias=True)
        document = CommercialDocument(
            tenant_id=self.tenant_id,
            number=number,
            created_by=user_id,
            **doc_data
        )
        self.db.add(document)
        self.db.flush()

        # Ajouter les lignes
        for i, line_data in enumerate(data.lines, 1):
            line = DocumentLine(
                tenant_id=self.tenant_id,
                document_id=document.id,
                line_number=i,
                **line_data.model_dump()
            )
            self._calculate_line_totals(line)
            self.db.add(line)

        self.db.flush()
        self._calculate_document_totals(document)

        self.db.commit()
        self.db.refresh(document)

        logger.info("Document created | id=%s number=%s", document.id, document.number)

        return document

    def get_document(self, document_id: UUID) -> CommercialDocument | None:
        """Récupérer un document."""
        return self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.id == document_id
        ).first()

    def get_document_by_number(self, doc_type: DocumentType, number: str) -> CommercialDocument | None:
        """Récupérer un document par numéro."""
        return self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.type == doc_type,
            CommercialDocument.number == number
        ).first()

    def list_documents(
        self,
        doc_type: DocumentType | None = None,
        status: DocumentStatus | None = None,
        customer_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[CommercialDocument], int]:
        """Lister les documents."""
        query = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id
        )

        if doc_type:
            query = query.filter(CommercialDocument.type == doc_type)
        if status:
            query = query.filter(CommercialDocument.status == status)
        if customer_id:
            query = query.filter(CommercialDocument.customer_id == customer_id)
        if date_from:
            query = query.filter(CommercialDocument.date >= date_from)
        if date_to:
            query = query.filter(CommercialDocument.date <= date_to)
        if search:
            query = query.outerjoin(Customer, CommercialDocument.customer_id == Customer.id)
            search_filter = or_(
                CommercialDocument.number.ilike(f"%{search}%"),
                Customer.name.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        total = query.count()
        items = query.order_by(CommercialDocument.date.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update_document(self, document_id: UUID, data: DocumentUpdate) -> CommercialDocument | None:
        """Mettre à jour un document."""
        document = self.get_document(document_id)
        if not document:
            return None

        # Vérifier que le document est modifiable
        if document.status not in [DocumentStatus.DRAFT, DocumentStatus.PENDING]:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(document, field, value)

        self._calculate_document_totals(document)

        self.db.commit()
        self.db.refresh(document)
        return document

    def validate_document(self, document_id: UUID, user_id: UUID) -> CommercialDocument | None:
        """Valider un document."""
        document = self.get_document(document_id)
        if not document or document.status != DocumentStatus.DRAFT:
            return None

        document.status = DocumentStatus.VALIDATED
        document.validated_by = user_id
        document.validated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(document)
        return document

    def send_document(self, document_id: UUID) -> CommercialDocument | None:
        """Marquer un document comme envoyé."""
        document = self.get_document(document_id)
        if not document or document.status not in [DocumentStatus.VALIDATED, DocumentStatus.PENDING]:
            return None

        document.status = DocumentStatus.SENT

        self.db.commit()
        self.db.refresh(document)
        return document

    def delete_document(self, document_id: UUID) -> bool:
        """Supprimer un document (soft delete uniquement si DRAFT)."""
        document = self.get_document(document_id)
        if not document:
            return False

        # Seulement les brouillons peuvent être supprimés
        if document.status != DocumentStatus.DRAFT:
            return False

        # Soft delete
        document.is_active = False

        self.db.commit()
        return True

    def convert_quote_to_order(self, quote_id: UUID, user_id: UUID) -> CommercialDocument | None:
        """Convertir un devis en commande."""
        quote = self.get_document(quote_id)
        if not quote or quote.type != DocumentType.QUOTE:
            return None
        if quote.status not in [DocumentStatus.SENT, DocumentStatus.ACCEPTED]:
            return None

        # Marquer le devis comme accepté
        quote.status = DocumentStatus.ACCEPTED

        # Créer la commande
        order = CommercialDocument(
            tenant_id=self.tenant_id,
            customer_id=quote.customer_id,
            opportunity_id=quote.opportunity_id,
            type=DocumentType.ORDER,
            number=self._generate_document_number(DocumentType.ORDER),
            status=DocumentStatus.VALIDATED,
            date=date.today(),
            billing_address=quote.billing_address,
            shipping_address=quote.shipping_address,
            payment_terms=quote.payment_terms,
            payment_method=quote.payment_method,
            shipping_method=quote.shipping_method,
            shipping_cost=quote.shipping_cost,
            subtotal=quote.subtotal,
            discount_amount=quote.discount_amount,
            discount_percent=quote.discount_percent,
            tax_amount=quote.tax_amount,
            total=quote.total,
            currency=quote.currency,
            notes=quote.notes,
            terms=quote.terms,
            parent_id=quote.id,
            created_by=user_id,
            validated_by=user_id,
            validated_at=datetime.utcnow()
        )
        self.db.add(order)
        self.db.flush()

        # Copier les lignes
        for line in quote.lines:
            new_line = DocumentLine(
                tenant_id=self.tenant_id,
                document_id=order.id,
                line_number=line.line_number,
                product_id=line.product_id,
                product_code=line.product_code,
                description=line.description,
                quantity=line.quantity,
                unit=line.unit,
                unit_price=line.unit_price,
                discount_percent=line.discount_percent,
                discount_amount=line.discount_amount,
                subtotal=line.subtotal,
                tax_rate=line.tax_rate,
                tax_amount=line.tax_amount,
                total=line.total
            )
            self.db.add(new_line)

        self.db.commit()
        self.db.refresh(order)
        return order

    def create_invoice_from_order(self, order_id: UUID, user_id: UUID) -> CommercialDocument | None:
        """Créer une facture à partir d'une commande."""
        logger.info(
            "Creating invoice from order | tenant=%s user=%s order_id=%s",
            self.tenant_id, user_id, order_id
        )

        order = self.get_document(order_id)
        if not order or order.type != DocumentType.ORDER:
            return None

        # Créer la facture
        invoice = CommercialDocument(
            tenant_id=self.tenant_id,
            customer_id=order.customer_id,
            opportunity_id=order.opportunity_id,
            type=DocumentType.INVOICE,
            number=self._generate_document_number(DocumentType.INVOICE),
            status=DocumentStatus.VALIDATED,
            date=date.today(),
            due_date=date.today(),  # À calculer selon payment_terms
            billing_address=order.billing_address,
            shipping_address=order.shipping_address,
            payment_terms=order.payment_terms,
            payment_method=order.payment_method,
            shipping_cost=order.shipping_cost,
            subtotal=order.subtotal,
            discount_amount=order.discount_amount,
            discount_percent=order.discount_percent,
            tax_amount=order.tax_amount,
            total=order.total,
            remaining_amount=order.total,
            currency=order.currency,
            notes=order.notes,
            terms=order.terms,
            parent_id=order.id,
            created_by=user_id,
            validated_by=user_id,
            validated_at=datetime.utcnow()
        )
        self.db.add(invoice)
        self.db.flush()

        # Lier la facture à la commande
        order.invoice_id = invoice.id
        order.status = DocumentStatus.INVOICED

        # Copier les lignes
        for line in order.lines:
            new_line = DocumentLine(
                tenant_id=self.tenant_id,
                document_id=invoice.id,
                line_number=line.line_number,
                product_id=line.product_id,
                product_code=line.product_code,
                description=line.description,
                quantity=line.quantity,
                unit=line.unit,
                unit_price=line.unit_price,
                discount_percent=line.discount_percent,
                discount_amount=line.discount_amount,
                subtotal=line.subtotal,
                tax_rate=line.tax_rate,
                tax_amount=line.tax_amount,
                total=line.total
            )
            self.db.add(new_line)

        # Mettre à jour les stats client
        customer = self.get_customer(order.customer_id)
        if customer:
            customer.order_count = (customer.order_count or 0) + 1
            customer.total_revenue = (customer.total_revenue or Decimal("0")) + invoice.total
            customer.last_order_date = date.today()
            if not customer.first_order_date:
                customer.first_order_date = date.today()

        self.db.commit()
        self.db.refresh(invoice)

        logger.info("Invoice created | id=%s number=%s", invoice.id, invoice.number)

        return invoice

    def add_document_line(self, document_id: UUID, data: DocumentLineCreate) -> DocumentLine | None:
        """Ajouter une ligne à un document."""
        document = self.get_document(document_id)
        if not document or document.status != DocumentStatus.DRAFT:
            return None

        # Numéro de ligne
        max_line = self.db.query(func.max(DocumentLine.line_number)).filter(
            DocumentLine.document_id == document_id
        ).scalar() or 0

        line = DocumentLine(
            tenant_id=self.tenant_id,
            document_id=document_id,
            line_number=max_line + 1,
            **data.model_dump()
        )
        self._calculate_line_totals(line)
        self.db.add(line)
        self.db.flush()

        self._calculate_document_totals(document)

        self.db.commit()
        self.db.refresh(line)
        return line

    def delete_document_line(self, line_id: UUID) -> bool:
        """Supprimer une ligne de document."""
        line = self.db.query(DocumentLine).filter(
            DocumentLine.tenant_id == self.tenant_id,
            DocumentLine.id == line_id
        ).first()

        if not line:
            return False

        document = self.get_document(line.document_id)
        if not document or document.status != DocumentStatus.DRAFT:
            return False

        self.db.delete(line)
        self.db.flush()

        self._calculate_document_totals(document)

        self.db.commit()
        return True

    # ========================================================================
    # GESTION DES PAIEMENTS
    # ========================================================================

    def create_payment(self, data: PaymentCreate, user_id: UUID) -> Payment | None:
        """Enregistrer un paiement."""
        document = self.get_document(data.document_id)
        if not document or document.type != DocumentType.INVOICE:
            return None

        payment = Payment(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump()
        )
        self.db.add(payment)

        # Mettre à jour le document
        document.paid_amount = (document.paid_amount or Decimal("0")) + data.amount
        document.remaining_amount = document.total - document.paid_amount

        if document.remaining_amount <= 0:
            document.status = DocumentStatus.PAID

        self.db.commit()
        self.db.refresh(payment)
        return payment

    def list_payments(self, document_id: UUID) -> list[Payment]:
        """Lister les paiements d'un document."""
        return self.db.query(Payment).filter(
            Payment.tenant_id == self.tenant_id,
            Payment.document_id == document_id
        ).order_by(Payment.date).all()

    # ========================================================================
    # GESTION DES ACTIVITÉS
    # ========================================================================

    def create_activity(self, data: ActivityCreate, user_id: UUID) -> CustomerActivity:
        """Créer une activité."""
        activity = CustomerActivity(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump(by_alias=True, exclude_unset=False)
        )
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def list_activities(
        self,
        customer_id: UUID | None = None,
        opportunity_id: UUID | None = None,
        assigned_to: UUID | None = None,
        is_completed: bool | None = None,
        limit: int = 50
    ) -> list[CustomerActivity]:
        """Lister les activités."""
        query = self.db.query(CustomerActivity).filter(
            CustomerActivity.tenant_id == self.tenant_id
        )

        if customer_id:
            query = query.filter(CustomerActivity.customer_id == customer_id)
        if opportunity_id:
            query = query.filter(CustomerActivity.opportunity_id == opportunity_id)
        if assigned_to:
            query = query.filter(CustomerActivity.assigned_to == assigned_to)
        if is_completed is not None:
            query = query.filter(CustomerActivity.is_completed == is_completed)

        return query.order_by(CustomerActivity.date.desc()).limit(limit).all()

    def complete_activity(self, activity_id: UUID) -> CustomerActivity | None:
        """Marquer une activité comme terminée."""
        activity = self.db.query(CustomerActivity).filter(
            CustomerActivity.tenant_id == self.tenant_id,
            CustomerActivity.id == activity_id
        ).first()

        if not activity:
            return None

        activity.is_completed = True
        activity.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(activity)
        return activity

    # ========================================================================
    # GESTION DU PIPELINE
    # ========================================================================

    def create_pipeline_stage(self, data: PipelineStageCreate) -> PipelineStage:
        """Créer une étape du pipeline."""
        stage = PipelineStage(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(stage)
        self.db.commit()
        self.db.refresh(stage)
        return stage

    def list_pipeline_stages(self) -> list[PipelineStage]:
        """Lister les étapes du pipeline."""
        return self.db.query(PipelineStage).filter(
            PipelineStage.tenant_id == self.tenant_id,
            PipelineStage.is_active
        ).order_by(PipelineStage.order).all()

    def get_pipeline_stats(self) -> PipelineStats:
        """Obtenir les statistiques du pipeline."""
        stages = self.list_pipeline_stages()
        stats = []
        total_value = Decimal("0")
        weighted_value = Decimal("0")
        total_count = 0

        for stage in stages:
            opps = self.db.query(Opportunity).filter(
                Opportunity.tenant_id == self.tenant_id,
                Opportunity.stage == stage.name,
                Opportunity.status.notin_([OpportunityStatus.WON, OpportunityStatus.LOST])
            ).all()

            stage_value = sum(o.amount or Decimal("0") for o in opps)
            stage_weighted = sum(o.weighted_amount or Decimal("0") for o in opps)

            stats.append({
                "id": str(stage.id),
                "name": stage.name,
                "order": stage.order,
                "probability": stage.probability,
                "color": stage.color,
                "count": len(opps),
                "value": float(stage_value),
                "weighted_value": float(stage_weighted)
            })

            total_value += stage_value
            weighted_value += stage_weighted
            total_count += len(opps)

        avg_prob = sum(s["probability"] for s in stats) / len(stats) if stats else 0

        return PipelineStats(
            stages=stats,
            total_value=total_value,
            weighted_value=weighted_value,
            opportunities_count=total_count,
            average_probability=avg_prob
        )

    # ========================================================================
    # GESTION DES PRODUITS
    # ========================================================================

    def create_product(self, data: ProductCreate) -> CatalogProduct:
        """Créer un produit."""
        product = CatalogProduct(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_product(self, product_id: UUID) -> CatalogProduct | None:
        """Récupérer un produit."""
        return self.db.query(CatalogProduct).filter(
            CatalogProduct.tenant_id == self.tenant_id,
            CatalogProduct.id == product_id
        ).first()

    def list_products(
        self,
        category: str | None = None,
        is_service: bool | None = None,
        is_active: bool | None = True,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[CatalogProduct], int]:
        """Lister les produits."""
        query = self.db.query(CatalogProduct).filter(CatalogProduct.tenant_id == self.tenant_id)

        if category:
            query = query.filter(CatalogProduct.category == category)
        if is_service is not None:
            query = query.filter(CatalogProduct.is_service == is_service)
        if is_active is not None:
            query = query.filter(CatalogProduct.is_active == is_active)
        if search:
            search_filter = or_(
                CatalogProduct.name.ilike(f"%{search}%"),
                CatalogProduct.code.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        total = query.count()
        items = query.order_by(CatalogProduct.name).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update_product(self, product_id: UUID, data: ProductUpdate) -> CatalogProduct | None:
        """Mettre à jour un produit."""
        product = self.get_product(product_id)
        if not product:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        self.db.commit()
        self.db.refresh(product)
        return product

    # ========================================================================
    # DASHBOARD & STATISTIQUES
    # ========================================================================

    def get_dashboard(self) -> SalesDashboard:
        """Obtenir le dashboard commercial."""
        today = date.today()
        month_start = today.replace(day=1)

        # Chiffres clés
        invoices = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.type == DocumentType.INVOICE,
            CommercialDocument.status == DocumentStatus.PAID
        ).all()

        total_revenue = sum(i.total for i in invoices)

        orders = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.type == DocumentType.ORDER
        ).count()

        quotes = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.type == DocumentType.QUOTE
        ).count()

        invoice_count = len(invoices)

        # Pipeline
        open_opps = self.db.query(Opportunity).filter(
            Opportunity.tenant_id == self.tenant_id,
            Opportunity.status.notin_([OpportunityStatus.WON, OpportunityStatus.LOST])
        ).all()

        pipeline_value = sum(o.amount or Decimal("0") for o in open_opps)
        weighted_pipeline = sum(o.weighted_amount or Decimal("0") for o in open_opps)

        won_month = self.db.query(Opportunity).filter(
            Opportunity.tenant_id == self.tenant_id,
            Opportunity.status == OpportunityStatus.WON,
            Opportunity.actual_close_date >= month_start
        ).count()

        lost_month = self.db.query(Opportunity).filter(
            Opportunity.tenant_id == self.tenant_id,
            Opportunity.status == OpportunityStatus.LOST,
            Opportunity.actual_close_date >= month_start
        ).count()

        # Clients
        total_customers = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.is_active
        ).count()

        active_customers = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.type == CustomerType.CUSTOMER,
            Customer.is_active
        ).count()

        new_customers = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.type == CustomerType.CUSTOMER,
            Customer.first_order_date >= month_start
        ).count()

        # Conversion
        validated_quotes = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.type == DocumentType.QUOTE,
            CommercialDocument.status == DocumentStatus.ACCEPTED
        ).count()

        quote_to_order = (validated_quotes / quotes * 100) if quotes > 0 else 0
        avg_deal = total_revenue / invoice_count if invoice_count > 0 else Decimal("0")

        return SalesDashboard(
            total_revenue=total_revenue,
            total_orders=orders,
            total_quotes=quotes,
            total_invoices=invoice_count,
            pipeline_value=pipeline_value,
            weighted_pipeline=weighted_pipeline,
            opportunities_count=len(open_opps),
            won_this_month=won_month,
            lost_this_month=lost_month,
            total_customers=total_customers,
            new_customers_this_month=new_customers,
            active_customers=active_customers,
            quote_to_order_rate=quote_to_order,
            average_deal_size=avg_deal
        )


    # ========================================================================
    # EXPORT CSV
    # ========================================================================

    def export_customers_csv(
        self,
        type: CustomerType | None = None,
        is_active: bool | None = None
    ) -> str:
        """
        Exporter les clients au format CSV.
        SÉCURITÉ: Filtrage strict par tenant_id.
        """
        import csv
        import io

        query = self.db.query(Customer).filter(Customer.tenant_id == self.tenant_id)

        if type:
            query = query.filter(Customer.type == type)
        if is_active is not None:
            query = query.filter(Customer.is_active == is_active)

        customers = query.order_by(Customer.name).all()

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # En-têtes
        writer.writerow([
            'Code', 'Nom', 'Type', 'Email', 'Téléphone', 'Mobile',
            'Adresse', 'Ville', 'Code Postal', 'Pays',
            'SIRET', 'TVA Intra', 'Conditions Paiement',
            'CA Total', 'Nb Commandes', 'Actif', 'Créé le'
        ])

        # Données
        for c in customers:
            writer.writerow([
                c.code,
                c.name,
                c.type.value if c.type else '',
                c.email or '',
                c.phone or '',
                c.mobile or '',
                c.address_line1 or '',
                c.city or '',
                c.postal_code or '',
                c.country_code or 'FR',
                c.registration_number or '',
                c.tax_id or '',
                c.payment_terms.value if c.payment_terms else '',
                str(c.total_revenue or 0),
                str(c.order_count or 0),
                'Oui' if c.is_active else 'Non',
                c.created_at.strftime('%Y-%m-%d') if c.created_at else ''
            ])

        return output.getvalue()

    def export_contacts_csv(self, customer_id: UUID | None = None) -> str:
        """
        Exporter les contacts au format CSV.
        SÉCURITÉ: Filtrage strict par tenant_id.
        """
        import csv
        import io

        query = self.db.query(Contact).filter(Contact.tenant_id == self.tenant_id)

        if customer_id:
            query = query.filter(Contact.customer_id == customer_id)

        contacts = query.order_by(Contact.last_name, Contact.first_name).all()

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # En-têtes
        writer.writerow([
            'Prénom', 'Nom', 'Fonction', 'Email', 'Téléphone', 'Mobile',
            'Principal', 'Facturation', 'Décideur', 'Actif', 'Créé le'
        ])

        # Données
        for c in contacts:
            writer.writerow([
                c.first_name,
                c.last_name,
                c.job_title or '',
                c.email or '',
                c.phone or '',
                c.mobile or '',
                'Oui' if c.is_primary else 'Non',
                'Oui' if c.is_billing else 'Non',
                'Oui' if c.is_decision_maker else 'Non',
                'Oui' if c.is_active else 'Non',
                c.created_at.strftime('%Y-%m-%d') if c.created_at else ''
            ])

        return output.getvalue()

    def export_opportunities_csv(
        self,
        status: OpportunityStatus | None = None,
        customer_id: UUID | None = None
    ) -> str:
        """
        Exporter les opportunités au format CSV.
        SÉCURITÉ: Filtrage strict par tenant_id.
        """
        import csv
        import io

        query = self.db.query(Opportunity).filter(Opportunity.tenant_id == self.tenant_id)

        if status:
            query = query.filter(Opportunity.status == status)
        if customer_id:
            query = query.filter(Opportunity.customer_id == customer_id)

        opportunities = query.order_by(Opportunity.expected_close_date).all()

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # En-têtes
        writer.writerow([
            'Code', 'Nom', 'Statut', 'Montant', 'Probabilité', 'Montant Pondéré',
            'Date Conclusion Prévue', 'Date Conclusion Réelle',
            'Source', 'Raison Gain', 'Raison Perte', 'Créé le'
        ])

        # Données
        for o in opportunities:
            writer.writerow([
                o.code,
                o.name,
                o.status.value if o.status else '',
                str(o.amount or 0),
                str(o.probability or 0),
                str(o.weighted_amount or 0),
                o.expected_close_date.strftime('%Y-%m-%d') if o.expected_close_date else '',
                o.actual_close_date.strftime('%Y-%m-%d') if o.actual_close_date else '',
                o.source or '',
                o.win_reason or '',
                o.loss_reason or '',
                o.created_at.strftime('%Y-%m-%d') if o.created_at else ''
            ])

        return output.getvalue()

    def export_documents_csv(
        self,
        doc_type: DocumentType | None = None,
        status_filter: DocumentStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None
    ) -> str:
        """Exporter les documents au format CSV."""
        query = self.db.query(CommercialDocument).options(
            selectinload(CommercialDocument.customer),
            selectinload(CommercialDocument.lines)
        ).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.is_active == True
        )

        if doc_type:
            query = query.filter(CommercialDocument.type == doc_type)
        if status_filter:
            query = query.filter(CommercialDocument.status == status_filter)
        if date_from:
            query = query.filter(CommercialDocument.date >= date_from)
        if date_to:
            query = query.filter(CommercialDocument.date <= date_to)

        documents = query.order_by(CommercialDocument.date.desc()).all()

        output = io.StringIO()
        writer = csv.writer(output)

        # En-têtes
        writer.writerow([
            'Numéro',
            'Type',
            'Date',
            'Client',
            'Statut',
            'Total HT',
            'Total TTC',
            'Créé le',
            'Validé le',
            'Envoyé le'
        ])

        # Données
        for doc in documents:
            writer.writerow([
                doc.number,
                doc.type.value,
                doc.date.strftime('%Y-%m-%d') if doc.date else '',
                doc.customer.name if doc.customer else '',
                doc.status.value,
                f"{doc.total_amount_excl_tax:.2f}",
                f"{doc.total_amount_incl_tax:.2f}",
                doc.created_at.strftime('%Y-%m-%d %H:%M') if doc.created_at else '',
                doc.validated_at.strftime('%Y-%m-%d %H:%M') if doc.validated_at else '',
                doc.sent_at.strftime('%Y-%m-%d %H:%M') if doc.sent_at else ''
            ])

        return output.getvalue()


def get_commercial_service(db: Session, tenant_id: str) -> CommercialService:
    """Factory pour obtenir le service commercial."""
    return CommercialService(db, tenant_id)
