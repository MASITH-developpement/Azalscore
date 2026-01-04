"""
AZALS MODULE M1 - Service Commercial
=====================================

Service pour le CRM et la gestion commerciale.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from uuid import UUID

from .models import (
    Customer, Contact, Opportunity, CommercialDocument, DocumentLine,
    Payment, CustomerActivity, PipelineStage, Product,
    CustomerType, OpportunityStatus, DocumentType, DocumentStatus
)
from .schemas import (
    CustomerCreate, CustomerUpdate,
    ContactCreate, ContactUpdate,
    OpportunityCreate, OpportunityUpdate,
    DocumentCreate, DocumentUpdate, DocumentLineCreate,
    PaymentCreate,
    ActivityCreate, ActivityUpdate,
    PipelineStageCreate,
    ProductCreate, ProductUpdate,
    SalesDashboard, PipelineStats
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
        """Créer un client."""
        customer = Customer(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump()
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def get_customer(self, customer_id: UUID) -> Optional[Customer]:
        """Récupérer un client par ID."""
        return self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.id == customer_id
        ).first()

    def get_customer_by_code(self, code: str) -> Optional[Customer]:
        """Récupérer un client par code."""
        return self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.code == code
        ).first()

    def list_customers(
        self,
        type: Optional[CustomerType] = None,
        assigned_to: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Customer], int]:
        """Lister les clients avec filtres."""
        query = self.db.query(Customer).filter(Customer.tenant_id == self.tenant_id)

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

    def update_customer(self, customer_id: UUID, data: CustomerUpdate) -> Optional[Customer]:
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

    def convert_prospect(self, customer_id: UUID) -> Optional[Customer]:
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
            **data.model_dump()
        )
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def get_contact(self, contact_id: UUID) -> Optional[Contact]:
        """Récupérer un contact."""
        return self.db.query(Contact).filter(
            Contact.tenant_id == self.tenant_id,
            Contact.id == contact_id
        ).first()

    def list_contacts(self, customer_id: UUID) -> List[Contact]:
        """Lister les contacts d'un client."""
        return self.db.query(Contact).filter(
            Contact.tenant_id == self.tenant_id,
            Contact.customer_id == customer_id,
            Contact.is_active == True
        ).order_by(Contact.is_primary.desc(), Contact.last_name).all()

    def update_contact(self, contact_id: UUID, data: ContactUpdate) -> Optional[Contact]:
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
        return opportunity

    def get_opportunity(self, opportunity_id: UUID) -> Optional[Opportunity]:
        """Récupérer une opportunité."""
        return self.db.query(Opportunity).filter(
            Opportunity.tenant_id == self.tenant_id,
            Opportunity.id == opportunity_id
        ).first()

    def list_opportunities(
        self,
        status: Optional[OpportunityStatus] = None,
        customer_id: Optional[UUID] = None,
        assigned_to: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Opportunity], int]:
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

    def update_opportunity(self, opportunity_id: UUID, data: OpportunityUpdate) -> Optional[Opportunity]:
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

    def win_opportunity(self, opportunity_id: UUID, win_reason: str = None) -> Optional[Opportunity]:
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

    def lose_opportunity(self, opportunity_id: UUID, loss_reason: str = None) -> Optional[Opportunity]:
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
        """Générer un numéro de document."""
        year = datetime.now().year
        prefix = {
            DocumentType.QUOTE: "DEV",
            DocumentType.ORDER: "CMD",
            DocumentType.INVOICE: "FAC",
            DocumentType.CREDIT_NOTE: "AVO",
            DocumentType.PROFORMA: "PRO",
            DocumentType.DELIVERY: "BL",
        }.get(doc_type, "DOC")

        # Compter les documents existants
        count = self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.type == doc_type,
            func.extract('year', CommercialDocument.date) == year
        ).count()

        return f"{prefix}-{year}-{str(count + 1).zfill(5)}"

    def _calculate_line_totals(self, line: DocumentLine) -> None:
        """Calculer les totaux d'une ligne."""
        subtotal = line.quantity * line.unit_price
        line.discount_amount = subtotal * Decimal(line.discount_percent) / 100
        line.subtotal = subtotal - line.discount_amount
        line.tax_amount = line.subtotal * Decimal(line.tax_rate) / 100
        line.total = line.subtotal + line.tax_amount

    def _calculate_document_totals(self, document: CommercialDocument) -> None:
        """Recalculer les totaux d'un document."""
        lines = self.db.query(DocumentLine).filter(
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
        # Générer le numéro
        number = self._generate_document_number(data.type)

        # Créer le document
        doc_data = data.model_dump(exclude={'lines'})
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
        return document

    def get_document(self, document_id: UUID) -> Optional[CommercialDocument]:
        """Récupérer un document."""
        return self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.id == document_id
        ).first()

    def get_document_by_number(self, doc_type: DocumentType, number: str) -> Optional[CommercialDocument]:
        """Récupérer un document par numéro."""
        return self.db.query(CommercialDocument).filter(
            CommercialDocument.tenant_id == self.tenant_id,
            CommercialDocument.type == doc_type,
            CommercialDocument.number == number
        ).first()

    def list_documents(
        self,
        doc_type: Optional[DocumentType] = None,
        status: Optional[DocumentStatus] = None,
        customer_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[CommercialDocument], int]:
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

        total = query.count()
        items = query.order_by(CommercialDocument.date.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update_document(self, document_id: UUID, data: DocumentUpdate) -> Optional[CommercialDocument]:
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

    def validate_document(self, document_id: UUID, user_id: UUID) -> Optional[CommercialDocument]:
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

    def send_document(self, document_id: UUID) -> Optional[CommercialDocument]:
        """Marquer un document comme envoyé."""
        document = self.get_document(document_id)
        if not document or document.status not in [DocumentStatus.VALIDATED, DocumentStatus.PENDING]:
            return None

        document.status = DocumentStatus.SENT

        self.db.commit()
        self.db.refresh(document)
        return document

    def convert_quote_to_order(self, quote_id: UUID, user_id: UUID) -> Optional[CommercialDocument]:
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

    def create_invoice_from_order(self, order_id: UUID, user_id: UUID) -> Optional[CommercialDocument]:
        """Créer une facture à partir d'une commande."""
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
        return invoice

    def add_document_line(self, document_id: UUID, data: DocumentLineCreate) -> Optional[DocumentLine]:
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

    def create_payment(self, data: PaymentCreate, user_id: UUID) -> Optional[Payment]:
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

    def list_payments(self, document_id: UUID) -> List[Payment]:
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
            **data.model_dump()
        )
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def list_activities(
        self,
        customer_id: Optional[UUID] = None,
        opportunity_id: Optional[UUID] = None,
        assigned_to: Optional[UUID] = None,
        is_completed: Optional[bool] = None,
        limit: int = 50
    ) -> List[CustomerActivity]:
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

    def complete_activity(self, activity_id: UUID) -> Optional[CustomerActivity]:
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

    def list_pipeline_stages(self) -> List[PipelineStage]:
        """Lister les étapes du pipeline."""
        return self.db.query(PipelineStage).filter(
            PipelineStage.tenant_id == self.tenant_id,
            PipelineStage.is_active == True
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

    def create_product(self, data: ProductCreate) -> Product:
        """Créer un produit."""
        product = Product(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_product(self, product_id: UUID) -> Optional[Product]:
        """Récupérer un produit."""
        return self.db.query(Product).filter(
            Product.tenant_id == self.tenant_id,
            Product.id == product_id
        ).first()

    def list_products(
        self,
        category: Optional[str] = None,
        is_service: Optional[bool] = None,
        is_active: Optional[bool] = True,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Product], int]:
        """Lister les produits."""
        query = self.db.query(Product).filter(Product.tenant_id == self.tenant_id)

        if category:
            query = query.filter(Product.category == category)
        if is_service is not None:
            query = query.filter(Product.is_service == is_service)
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        if search:
            search_filter = or_(
                Product.name.ilike(f"%{search}%"),
                Product.code.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        total = query.count()
        items = query.order_by(Product.name).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update_product(self, product_id: UUID, data: ProductUpdate) -> Optional[Product]:
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
            Customer.is_active == True
        ).count()

        active_customers = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.type == CustomerType.CUSTOMER,
            Customer.is_active == True
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


def get_commercial_service(db: Session, tenant_id: str) -> CommercialService:
    """Factory pour obtenir le service commercial."""
    return CommercialService(db, tenant_id)
