"""
AZALS MODULE M4 - Service Achats
================================

Service métier pour la gestion des achats.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from uuid import UUID

from .models import (
    Supplier, SupplierContact, PurchaseRequisition, PurchaseRequisitionLine,
    PurchaseOrder, PurchaseOrderLine,
    GoodsReceipt, GoodsReceiptLine, PurchaseInvoice, PurchaseInvoiceLine,
    SupplierPayment, PaymentAllocation, SupplierEvaluation,
    SupplierStatus, SupplierType, RequisitionStatus,
    PurchaseOrderStatus, ReceivingStatus, PurchaseInvoiceStatus
)
from .schemas import (
    SupplierCreate, SupplierUpdate, SupplierContactCreate,
    RequisitionCreate, PurchaseOrderCreate,
    GoodsReceiptCreate, PurchaseInvoiceCreate, SupplierPaymentCreate,
    SupplierEvaluationCreate, ProcurementDashboard
)


class ProcurementService:
    """Service pour la gestion des achats."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # FOURNISSEURS
    # =========================================================================

    def _generate_supplier_code(self) -> str:
        """Générer un code fournisseur automatique: FRN-XXXX."""
        count = self.db.query(Supplier).filter(
            Supplier.tenant_id == self.tenant_id
        ).count()
        return f"FRN-{count + 1:04d}"

    def create_supplier(self, data: SupplierCreate) -> Supplier:
        """Créer un fournisseur."""
        # Auto-generate code if not provided or empty
        code = data.code if data.code and data.code.strip() else self._generate_supplier_code()
        supplier = Supplier(
            tenant_id=self.tenant_id,
            code=code,
            name=data.name,
            legal_name=data.legal_name,
            type=data.type,
            tax_id=data.tax_id,
            vat_number=data.vat_number,
            email=data.email,
            phone=data.phone,
            website=data.website,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            postal_code=data.postal_code,
            city=data.city,
            country=data.country,
            payment_terms=data.payment_terms,
            currency=data.currency,
            credit_limit=data.credit_limit,
            discount_rate=data.discount_rate,
            category=data.category,
            bank_name=data.bank_name,
            iban=data.iban,
            bic=data.bic,
            notes=data.notes,
            tags=data.tags
        )
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def get_supplier(self, supplier_id: UUID) -> Optional[Supplier]:
        """Récupérer un fournisseur."""
        return self.db.query(Supplier).filter(
            Supplier.id == supplier_id,
            Supplier.tenant_id == self.tenant_id
        ).first()

    def get_supplier_by_code(self, code: str) -> Optional[Supplier]:
        """Récupérer un fournisseur par code."""
        return self.db.query(Supplier).filter(
            Supplier.code == code,
            Supplier.tenant_id == self.tenant_id
        ).first()

    def list_suppliers(
        self,
        status: Optional[SupplierStatus] = None,
        supplier_type: Optional[SupplierType] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Supplier], int]:
        """Lister les fournisseurs."""
        query = self.db.query(Supplier).filter(
            Supplier.tenant_id == self.tenant_id,
            Supplier.is_active == is_active
        )

        if status:
            query = query.filter(Supplier.status == status)
        if supplier_type:
            query = query.filter(Supplier.type == supplier_type)
        if category:
            query = query.filter(Supplier.category == category)
        if search:
            query = query.filter(
                or_(
                    Supplier.name.ilike(f"%{search}%"),
                    Supplier.code.ilike(f"%{search}%"),
                    Supplier.email.ilike(f"%{search}%")
                )
            )

        total = query.count()
        items = query.order_by(Supplier.name).offset(skip).limit(limit).all()
        return items, total

    def update_supplier(self, supplier_id: UUID, data: SupplierUpdate) -> Optional[Supplier]:
        """Mettre à jour un fournisseur."""
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(supplier, field, value)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def approve_supplier(self, supplier_id: UUID, user_id: UUID) -> Optional[Supplier]:
        """Approuver un fournisseur."""
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return None
        supplier.status = SupplierStatus.APPROVED
        supplier.approved_by = user_id
        supplier.approved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def add_supplier_contact(
        self,
        supplier_id: UUID,
        data: SupplierContactCreate
    ) -> SupplierContact:
        """Ajouter un contact fournisseur."""
        contact = SupplierContact(
            tenant_id=self.tenant_id,
            supplier_id=supplier_id,
            first_name=data.first_name,
            last_name=data.last_name,
            job_title=data.job_title,
            department=data.department,
            email=data.email,
            phone=data.phone,
            mobile=data.mobile,
            is_primary=data.is_primary,
            notes=data.notes
        )
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def get_supplier_contacts(self, supplier_id: UUID) -> List[SupplierContact]:
        """Récupérer les contacts d'un fournisseur."""
        return self.db.query(SupplierContact).filter(
            SupplierContact.supplier_id == supplier_id,
            SupplierContact.tenant_id == self.tenant_id,
            SupplierContact.is_active == True
        ).all()

    # =========================================================================
    # DEMANDES D'ACHAT
    # =========================================================================

    def create_requisition(
        self,
        data: RequisitionCreate,
        user_id: UUID
    ) -> PurchaseRequisition:
        """Créer une demande d'achat."""
        # Générer le numéro
        count = self.db.query(PurchaseRequisition).filter(
            PurchaseRequisition.tenant_id == self.tenant_id
        ).count()
        number = f"REQ-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"

        requisition = PurchaseRequisition(
            tenant_id=self.tenant_id,
            number=number,
            title=data.title,
            description=data.description,
            justification=data.justification,
            priority=data.priority,
            requester_id=user_id,
            department_id=data.department_id,
            requested_date=data.requested_date,
            required_date=data.required_date,
            budget_code=data.budget_code,
            notes=data.notes
        )
        self.db.add(requisition)
        self.db.flush()

        # Créer les lignes
        total = Decimal("0")
        for i, line_data in enumerate(data.lines, 1):
            line_total = (line_data.quantity * (line_data.estimated_price or Decimal("0")))
            total += line_total

            line = PurchaseRequisitionLine(
                tenant_id=self.tenant_id,
                requisition_id=requisition.id,
                line_number=i,
                product_id=line_data.product_id,
                product_code=line_data.product_code,
                description=line_data.description,
                quantity=line_data.quantity,
                unit=line_data.unit,
                estimated_price=line_data.estimated_price,
                total=line_total,
                preferred_supplier_id=line_data.preferred_supplier_id,
                required_date=line_data.required_date,
                notes=line_data.notes
            )
            self.db.add(line)

        requisition.estimated_total = total
        self.db.commit()
        self.db.refresh(requisition)
        return requisition

    def get_requisition(self, requisition_id: UUID) -> Optional[PurchaseRequisition]:
        """Récupérer une demande d'achat."""
        return self.db.query(PurchaseRequisition).filter(
            PurchaseRequisition.id == requisition_id,
            PurchaseRequisition.tenant_id == self.tenant_id
        ).first()

    def list_requisitions(
        self,
        status: Optional[RequisitionStatus] = None,
        requester_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[PurchaseRequisition], int]:
        """Lister les demandes d'achat."""
        query = self.db.query(PurchaseRequisition).filter(
            PurchaseRequisition.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(PurchaseRequisition.status == status)
        if requester_id:
            query = query.filter(PurchaseRequisition.requester_id == requester_id)

        total = query.count()
        items = query.order_by(PurchaseRequisition.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def approve_requisition(
        self,
        requisition_id: UUID,
        user_id: UUID
    ) -> Optional[PurchaseRequisition]:
        """Approuver une demande d'achat."""
        requisition = self.get_requisition(requisition_id)
        if not requisition or requisition.status != RequisitionStatus.SUBMITTED:
            return None
        requisition.status = RequisitionStatus.APPROVED
        requisition.approved_by = user_id
        requisition.approved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(requisition)
        return requisition

    def reject_requisition(
        self,
        requisition_id: UUID,
        user_id: UUID,
        reason: str
    ) -> Optional[PurchaseRequisition]:
        """Rejeter une demande d'achat."""
        requisition = self.get_requisition(requisition_id)
        if not requisition or requisition.status != RequisitionStatus.SUBMITTED:
            return None
        requisition.status = RequisitionStatus.REJECTED
        requisition.approved_by = user_id
        requisition.approved_at = datetime.utcnow()
        requisition.rejection_reason = reason
        self.db.commit()
        self.db.refresh(requisition)
        return requisition

    def submit_requisition(self, requisition_id: UUID) -> Optional[PurchaseRequisition]:
        """Soumettre une demande d'achat."""
        requisition = self.get_requisition(requisition_id)
        if not requisition or requisition.status != RequisitionStatus.DRAFT:
            return None
        requisition.status = RequisitionStatus.SUBMITTED
        self.db.commit()
        self.db.refresh(requisition)
        return requisition

    # =========================================================================
    # COMMANDES D'ACHAT
    # =========================================================================

    def create_purchase_order(
        self,
        data: PurchaseOrderCreate,
        user_id: UUID
    ) -> PurchaseOrder:
        """Créer une commande d'achat."""
        # Générer le numéro: CMD-YYYY-XXXX
        year = datetime.now().year
        count = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.tenant_id == self.tenant_id,
            func.extract('year', PurchaseOrder.created_at) == year
        ).count()
        number = f"CMD-{year}-{count + 1:04d}"

        order = PurchaseOrder(
            tenant_id=self.tenant_id,
            number=number,
            supplier_id=data.supplier_id,
            requisition_id=data.requisition_id,
            quotation_id=data.quotation_id,
            order_date=data.order_date,
            expected_date=data.expected_date,
            delivery_address=data.delivery_address,
            delivery_contact=data.delivery_contact,
            currency=data.currency,
            payment_terms=data.payment_terms,
            incoterms=data.incoterms,
            shipping_cost=data.shipping_cost,
            notes=data.notes,
            internal_notes=data.internal_notes,
            created_by=user_id
        )
        self.db.add(order)
        self.db.flush()

        # Créer les lignes
        subtotal = Decimal("0")
        tax_total = Decimal("0")

        for i, line_data in enumerate(data.lines, 1):
            discount = line_data.unit_price * line_data.quantity * (line_data.discount_percent / 100)
            line_subtotal = line_data.unit_price * line_data.quantity - discount
            line_tax = line_subtotal * (line_data.tax_rate / 100)
            line_total = line_subtotal + line_tax

            subtotal += line_subtotal
            tax_total += line_tax

            line = PurchaseOrderLine(
                tenant_id=self.tenant_id,
                order_id=order.id,
                line_number=i,
                product_id=line_data.product_id,
                product_code=line_data.product_code,
                description=line_data.description,
                quantity=line_data.quantity,
                unit=line_data.unit,
                unit_price=line_data.unit_price,
                discount_percent=line_data.discount_percent,
                tax_rate=line_data.tax_rate,
                total=line_total,
                expected_date=line_data.expected_date,
                requisition_line_id=line_data.requisition_line_id,
                notes=line_data.notes
            )
            self.db.add(line)

        order.subtotal = subtotal
        order.tax_amount = tax_total
        order.total = subtotal + tax_total + (data.shipping_cost or Decimal("0"))

        self.db.commit()
        self.db.refresh(order)
        return order

    def get_purchase_order(self, order_id: UUID) -> Optional[PurchaseOrder]:
        """Récupérer une commande d'achat."""
        return self.db.query(PurchaseOrder).filter(
            PurchaseOrder.id == order_id,
            PurchaseOrder.tenant_id == self.tenant_id
        ).first()

    def list_purchase_orders(
        self,
        supplier_id: Optional[UUID] = None,
        status: Optional[PurchaseOrderStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[PurchaseOrder], int]:
        """Lister les commandes d'achat."""
        query = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.tenant_id == self.tenant_id
        )

        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if status:
            query = query.filter(PurchaseOrder.status == status)
        if start_date:
            query = query.filter(PurchaseOrder.order_date >= start_date)
        if end_date:
            query = query.filter(PurchaseOrder.order_date <= end_date)

        total = query.count()
        items = query.order_by(PurchaseOrder.order_date.desc()).offset(skip).limit(limit).all()
        return items, total

    def send_purchase_order(self, order_id: UUID) -> Optional[PurchaseOrder]:
        """Envoyer une commande au fournisseur."""
        order = self.get_purchase_order(order_id)
        if not order or order.status != PurchaseOrderStatus.DRAFT:
            return None
        order.status = PurchaseOrderStatus.SENT
        order.sent_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(order)
        return order

    def confirm_purchase_order(
        self,
        order_id: UUID,
        supplier_reference: Optional[str] = None,
        confirmed_date: Optional[date] = None
    ) -> Optional[PurchaseOrder]:
        """Confirmer une commande (par le fournisseur)."""
        order = self.get_purchase_order(order_id)
        if not order or order.status != PurchaseOrderStatus.SENT:
            return None
        order.status = PurchaseOrderStatus.CONFIRMED
        order.confirmed_at = datetime.utcnow()
        order.confirmed_date = confirmed_date or date.today()
        if supplier_reference:
            order.supplier_reference = supplier_reference
        self.db.commit()
        self.db.refresh(order)
        return order

    # =========================================================================
    # ACHATS V1 - COMMANDES SIMPLIFIÉES
    # =========================================================================

    def validate_purchase_order(
        self,
        order_id: UUID,
        user_id: UUID
    ) -> Optional[PurchaseOrder]:
        """Valider une commande d'achat (DRAFT → VALIDATED/SENT)."""
        order = self.get_purchase_order(order_id)
        if not order or order.status != PurchaseOrderStatus.DRAFT:
            return None
        # V1: DRAFT → SENT (équivalent VALIDATED pour V1)
        order.status = PurchaseOrderStatus.SENT
        order.sent_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(order)
        return order

    def update_purchase_order(
        self,
        order_id: UUID,
        data: PurchaseOrderCreate,
        user_id: UUID
    ) -> Optional[PurchaseOrder]:
        """Mettre à jour une commande d'achat (DRAFT uniquement)."""
        order = self.get_purchase_order(order_id)
        if not order or order.status != PurchaseOrderStatus.DRAFT:
            return None

        # Mettre à jour les champs de base
        order.supplier_id = data.supplier_id
        order.order_date = data.order_date
        order.expected_date = data.expected_date
        order.delivery_address = data.delivery_address
        order.delivery_contact = data.delivery_contact
        order.currency = data.currency
        order.payment_terms = data.payment_terms
        order.incoterms = data.incoterms
        order.shipping_cost = data.shipping_cost or Decimal("0")
        order.notes = data.notes
        order.internal_notes = data.internal_notes

        # Supprimer les anciennes lignes
        self.db.query(PurchaseOrderLine).filter(
            PurchaseOrderLine.order_id == order_id
        ).delete()

        # Recréer les lignes
        subtotal = Decimal("0")
        tax_total = Decimal("0")

        for i, line_data in enumerate(data.lines, 1):
            discount = line_data.unit_price * line_data.quantity * (line_data.discount_percent / 100)
            line_subtotal = line_data.unit_price * line_data.quantity - discount
            line_tax = line_subtotal * (line_data.tax_rate / 100)
            line_total = line_subtotal + line_tax

            subtotal += line_subtotal
            tax_total += line_tax

            line = PurchaseOrderLine(
                tenant_id=self.tenant_id,
                order_id=order.id,
                line_number=i,
                product_id=line_data.product_id,
                product_code=line_data.product_code,
                description=line_data.description,
                quantity=line_data.quantity,
                unit=line_data.unit,
                unit_price=line_data.unit_price,
                discount_percent=line_data.discount_percent,
                tax_rate=line_data.tax_rate,
                total=line_total,
                expected_date=line_data.expected_date,
                requisition_line_id=line_data.requisition_line_id,
                notes=line_data.notes
            )
            self.db.add(line)

        order.subtotal = subtotal
        order.tax_amount = tax_total
        order.total = subtotal + tax_total + (data.shipping_cost or Decimal("0"))

        self.db.commit()
        self.db.refresh(order)
        return order

    def delete_purchase_order(self, order_id: UUID) -> bool:
        """Supprimer une commande d'achat (DRAFT uniquement)."""
        order = self.get_purchase_order(order_id)
        if not order or order.status != PurchaseOrderStatus.DRAFT:
            return False

        # Supprimer les lignes d'abord
        self.db.query(PurchaseOrderLine).filter(
            PurchaseOrderLine.order_id == order_id
        ).delete()

        # Supprimer la commande
        self.db.delete(order)
        self.db.commit()
        return True

    def get_order_lines(self, order_id: UUID) -> List[PurchaseOrderLine]:
        """Récupérer les lignes d'une commande."""
        return self.db.query(PurchaseOrderLine).filter(
            PurchaseOrderLine.order_id == order_id,
            PurchaseOrderLine.tenant_id == self.tenant_id
        ).order_by(PurchaseOrderLine.line_number).all()

    def create_invoice_from_order(
        self,
        order_id: UUID,
        user_id: UUID,
        invoice_date: Optional[date] = None,
        supplier_invoice_number: Optional[str] = None
    ) -> Optional[PurchaseInvoice]:
        """Créer une facture à partir d'une commande validée."""
        order = self.get_purchase_order(order_id)
        if not order or order.status == PurchaseOrderStatus.DRAFT:
            return None  # Ne peut pas créer une facture depuis un brouillon

        # Récupérer les lignes de la commande
        order_lines = self.get_order_lines(order_id)
        if not order_lines:
            return None

        # Générer le numéro de facture
        year = datetime.now().year
        count = self.db.query(PurchaseInvoice).filter(
            PurchaseInvoice.tenant_id == self.tenant_id,
            func.extract('year', PurchaseInvoice.created_at) == year
        ).count()
        number = f"FAF-{year}-{count + 1:04d}"

        # Créer la facture
        invoice = PurchaseInvoice(
            tenant_id=self.tenant_id,
            number=number,
            supplier_id=order.supplier_id,
            order_id=order_id,
            invoice_date=invoice_date or date.today(),
            supplier_invoice_number=supplier_invoice_number,
            currency=order.currency,
            payment_terms=order.payment_terms,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            total=order.total,
            remaining_amount=order.total,
            created_by=user_id
        )
        self.db.add(invoice)
        self.db.flush()

        # Copier les lignes
        for order_line in order_lines:
            invoice_line = PurchaseInvoiceLine(
                tenant_id=self.tenant_id,
                invoice_id=invoice.id,
                order_line_id=order_line.id,
                line_number=order_line.line_number,
                product_id=order_line.product_id,
                product_code=order_line.product_code,
                description=order_line.description,
                quantity=order_line.quantity,
                unit=order_line.unit,
                unit_price=order_line.unit_price,
                discount_percent=order_line.discount_percent,
                tax_rate=order_line.tax_rate,
                tax_amount=order_line.total * order_line.tax_rate / (100 + order_line.tax_rate),
                total=order_line.total
            )
            self.db.add(invoice_line)

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    # =========================================================================
    # RÉCEPTIONS
    # =========================================================================

    def create_goods_receipt(
        self,
        data: GoodsReceiptCreate,
        user_id: UUID
    ) -> GoodsReceipt:
        """Créer une réception de marchandises."""
        order = self.get_purchase_order(data.order_id)
        if not order:
            raise ValueError("Order not found")

        # Générer le numéro
        count = self.db.query(GoodsReceipt).filter(
            GoodsReceipt.tenant_id == self.tenant_id
        ).count()
        number = f"GR-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"

        receipt = GoodsReceipt(
            tenant_id=self.tenant_id,
            number=number,
            order_id=data.order_id,
            supplier_id=order.supplier_id,
            receipt_date=data.receipt_date,
            delivery_note=data.delivery_note,
            carrier=data.carrier,
            tracking_number=data.tracking_number,
            warehouse_id=data.warehouse_id,
            location=data.location,
            notes=data.notes,
            received_by=user_id
        )
        self.db.add(receipt)
        self.db.flush()

        # Créer les lignes
        for i, line_data in enumerate(data.lines, 1):
            line = GoodsReceiptLine(
                tenant_id=self.tenant_id,
                receipt_id=receipt.id,
                order_line_id=line_data.order_line_id,
                line_number=i,
                product_id=line_data.product_id,
                product_code=line_data.product_code,
                description=line_data.description,
                ordered_quantity=line_data.ordered_quantity,
                received_quantity=line_data.received_quantity,
                rejected_quantity=line_data.rejected_quantity,
                unit=line_data.unit,
                rejection_reason=line_data.rejection_reason,
                lot_number=line_data.lot_number,
                expiry_date=line_data.expiry_date,
                notes=line_data.notes
            )
            self.db.add(line)

            # Mettre à jour la ligne de commande
            order_line = self.db.query(PurchaseOrderLine).filter(
                PurchaseOrderLine.id == line_data.order_line_id
            ).first()
            if order_line:
                order_line.received_quantity += line_data.received_quantity

        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def validate_goods_receipt(
        self,
        receipt_id: UUID,
        user_id: UUID
    ) -> Optional[GoodsReceipt]:
        """Valider une réception."""
        receipt = self.db.query(GoodsReceipt).filter(
            GoodsReceipt.id == receipt_id,
            GoodsReceipt.tenant_id == self.tenant_id
        ).first()

        if not receipt or receipt.status != ReceivingStatus.DRAFT:
            return None

        receipt.status = ReceivingStatus.VALIDATED
        receipt.validated_by = user_id
        receipt.validated_at = datetime.utcnow()

        # Mettre à jour le statut de la commande
        order = self.get_purchase_order(receipt.order_id)
        if order:
            total_ordered = sum(l.quantity for l in self.db.query(PurchaseOrderLine).filter(
                PurchaseOrderLine.order_id == order.id
            ).all())
            total_received = sum(l.received_quantity for l in self.db.query(PurchaseOrderLine).filter(
                PurchaseOrderLine.order_id == order.id
            ).all())

            if total_received >= total_ordered:
                order.status = PurchaseOrderStatus.RECEIVED
            else:
                order.status = PurchaseOrderStatus.PARTIAL

        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    # =========================================================================
    # FACTURES D'ACHAT
    # =========================================================================

    def create_purchase_invoice(
        self,
        data: PurchaseInvoiceCreate,
        user_id: UUID
    ) -> PurchaseInvoice:
        """Créer une facture d'achat."""
        # Générer le numéro: FAF-YYYY-XXXX
        year = datetime.now().year
        count = self.db.query(PurchaseInvoice).filter(
            PurchaseInvoice.tenant_id == self.tenant_id,
            func.extract('year', PurchaseInvoice.created_at) == year
        ).count()
        number = f"FAF-{year}-{count + 1:04d}"

        invoice = PurchaseInvoice(
            tenant_id=self.tenant_id,
            number=number,
            supplier_id=data.supplier_id,
            order_id=data.order_id,
            invoice_date=data.invoice_date,
            due_date=data.due_date,
            supplier_invoice_number=data.supplier_invoice_number,
            supplier_invoice_date=data.supplier_invoice_date,
            currency=data.currency,
            payment_terms=data.payment_terms,
            payment_method=data.payment_method,
            notes=data.notes,
            created_by=user_id
        )
        self.db.add(invoice)
        self.db.flush()

        # Créer les lignes
        subtotal = Decimal("0")
        tax_total = Decimal("0")

        for i, line_data in enumerate(data.lines, 1):
            discount = line_data.unit_price * line_data.quantity * (line_data.discount_percent / 100)
            line_subtotal = line_data.unit_price * line_data.quantity - discount
            line_tax = line_subtotal * (line_data.tax_rate / 100)
            line_total = line_subtotal + line_tax

            subtotal += line_subtotal
            tax_total += line_tax

            line = PurchaseInvoiceLine(
                tenant_id=self.tenant_id,
                invoice_id=invoice.id,
                order_line_id=line_data.order_line_id,
                line_number=i,
                product_id=line_data.product_id,
                product_code=line_data.product_code,
                description=line_data.description,
                quantity=line_data.quantity,
                unit=line_data.unit,
                unit_price=line_data.unit_price,
                discount_percent=line_data.discount_percent,
                tax_rate=line_data.tax_rate,
                tax_amount=line_tax,
                total=line_total,
                account_id=line_data.account_id,
                analytic_code=line_data.analytic_code,
                notes=line_data.notes
            )
            self.db.add(line)

        invoice.subtotal = subtotal
        invoice.tax_amount = tax_total
        invoice.total = subtotal + tax_total
        invoice.remaining_amount = invoice.total

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def get_purchase_invoice(self, invoice_id: UUID) -> Optional[PurchaseInvoice]:
        """Récupérer une facture d'achat."""
        return self.db.query(PurchaseInvoice).filter(
            PurchaseInvoice.id == invoice_id,
            PurchaseInvoice.tenant_id == self.tenant_id
        ).first()

    def list_purchase_invoices(
        self,
        supplier_id: Optional[UUID] = None,
        status: Optional[PurchaseInvoiceStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[PurchaseInvoice], int]:
        """Lister les factures d'achat."""
        query = self.db.query(PurchaseInvoice).filter(
            PurchaseInvoice.tenant_id == self.tenant_id
        )

        if supplier_id:
            query = query.filter(PurchaseInvoice.supplier_id == supplier_id)
        if status:
            query = query.filter(PurchaseInvoice.status == status)
        if start_date:
            query = query.filter(PurchaseInvoice.invoice_date >= start_date)
        if end_date:
            query = query.filter(PurchaseInvoice.invoice_date <= end_date)

        total = query.count()
        items = query.order_by(PurchaseInvoice.invoice_date.desc()).offset(skip).limit(limit).all()
        return items, total

    def validate_purchase_invoice(
        self,
        invoice_id: UUID,
        user_id: UUID
    ) -> Optional[PurchaseInvoice]:
        """Valider une facture d'achat."""
        invoice = self.get_purchase_invoice(invoice_id)
        if not invoice or invoice.status != PurchaseInvoiceStatus.DRAFT:
            return None

        invoice.status = PurchaseInvoiceStatus.VALIDATED
        invoice.validated_by = user_id
        invoice.validated_at = datetime.utcnow()

        # Mettre à jour la commande si liée
        if invoice.order_id:
            order = self.get_purchase_order(invoice.order_id)
            if order:
                order.invoiced_amount += invoice.total
                if order.invoiced_amount >= order.total:
                    order.status = PurchaseOrderStatus.INVOICED

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    # =========================================================================
    # ACHATS V1 - FACTURES SIMPLIFIÉES
    # =========================================================================

    def update_purchase_invoice(
        self,
        invoice_id: UUID,
        data: PurchaseInvoiceCreate,
        user_id: UUID
    ) -> Optional[PurchaseInvoice]:
        """Mettre à jour une facture d'achat (DRAFT uniquement)."""
        invoice = self.get_purchase_invoice(invoice_id)
        if not invoice or invoice.status != PurchaseInvoiceStatus.DRAFT:
            return None

        # Mettre à jour les champs de base
        invoice.supplier_id = data.supplier_id
        invoice.order_id = data.order_id
        invoice.invoice_date = data.invoice_date
        invoice.due_date = data.due_date
        invoice.supplier_invoice_number = data.supplier_invoice_number
        invoice.supplier_invoice_date = data.supplier_invoice_date
        invoice.currency = data.currency
        invoice.payment_terms = data.payment_terms
        invoice.payment_method = data.payment_method
        invoice.notes = data.notes

        # Supprimer les anciennes lignes
        self.db.query(PurchaseInvoiceLine).filter(
            PurchaseInvoiceLine.invoice_id == invoice_id
        ).delete()

        # Recréer les lignes
        subtotal = Decimal("0")
        tax_total = Decimal("0")

        for i, line_data in enumerate(data.lines, 1):
            discount = line_data.unit_price * line_data.quantity * (line_data.discount_percent / 100)
            line_subtotal = line_data.unit_price * line_data.quantity - discount
            line_tax = line_subtotal * (line_data.tax_rate / 100)
            line_total = line_subtotal + line_tax

            subtotal += line_subtotal
            tax_total += line_tax

            line = PurchaseInvoiceLine(
                tenant_id=self.tenant_id,
                invoice_id=invoice.id,
                order_line_id=line_data.order_line_id,
                line_number=i,
                product_id=line_data.product_id,
                product_code=line_data.product_code,
                description=line_data.description,
                quantity=line_data.quantity,
                unit=line_data.unit,
                unit_price=line_data.unit_price,
                discount_percent=line_data.discount_percent,
                tax_rate=line_data.tax_rate,
                tax_amount=line_tax,
                total=line_total,
                account_id=line_data.account_id,
                analytic_code=line_data.analytic_code,
                notes=line_data.notes
            )
            self.db.add(line)

        invoice.subtotal = subtotal
        invoice.tax_amount = tax_total
        invoice.total = subtotal + tax_total
        invoice.remaining_amount = invoice.total

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def delete_purchase_invoice(self, invoice_id: UUID) -> bool:
        """Supprimer une facture d'achat (DRAFT uniquement)."""
        invoice = self.get_purchase_invoice(invoice_id)
        if not invoice or invoice.status != PurchaseInvoiceStatus.DRAFT:
            return False

        # Supprimer les lignes d'abord
        self.db.query(PurchaseInvoiceLine).filter(
            PurchaseInvoiceLine.invoice_id == invoice_id
        ).delete()

        # Supprimer la facture
        self.db.delete(invoice)
        self.db.commit()
        return True

    def get_invoice_lines(self, invoice_id: UUID) -> List[PurchaseInvoiceLine]:
        """Récupérer les lignes d'une facture."""
        return self.db.query(PurchaseInvoiceLine).filter(
            PurchaseInvoiceLine.invoice_id == invoice_id,
            PurchaseInvoiceLine.tenant_id == self.tenant_id
        ).order_by(PurchaseInvoiceLine.line_number).all()

    # =========================================================================
    # EXPORT CSV
    # =========================================================================

    def export_orders_csv(
        self,
        supplier_id: Optional[UUID] = None,
        status: Optional[PurchaseOrderStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> str:
        """Exporter les commandes en CSV."""
        orders, _ = self.list_purchase_orders(
            supplier_id=supplier_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            skip=0,
            limit=10000
        )

        lines = ["Numéro;Date;Fournisseur;Statut;HT;TVA;TTC"]
        for order in orders:
            supplier = self.get_supplier(order.supplier_id)
            supplier_name = supplier.name if supplier else ""
            lines.append(
                f"{order.number};{order.order_date};{supplier_name};"
                f"{order.status.value};{order.subtotal};{order.tax_amount};{order.total}"
            )

        return "\n".join(lines)

    def export_invoices_csv(
        self,
        supplier_id: Optional[UUID] = None,
        status: Optional[PurchaseInvoiceStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> str:
        """Exporter les factures en CSV."""
        invoices, _ = self.list_purchase_invoices(
            supplier_id=supplier_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            skip=0,
            limit=10000
        )

        lines = ["Numéro;Date;Fournisseur;Réf. Fournisseur;Statut;HT;TVA;TTC"]
        for invoice in invoices:
            supplier = self.get_supplier(invoice.supplier_id)
            supplier_name = supplier.name if supplier else ""
            lines.append(
                f"{invoice.number};{invoice.invoice_date};{supplier_name};"
                f"{invoice.supplier_invoice_number or ''};{invoice.status.value};"
                f"{invoice.subtotal};{invoice.tax_amount};{invoice.total}"
            )

        return "\n".join(lines)

    # =========================================================================
    # PAIEMENTS
    # =========================================================================

    def create_supplier_payment(
        self,
        data: SupplierPaymentCreate,
        user_id: UUID
    ) -> SupplierPayment:
        """Créer un paiement fournisseur."""
        # Générer le numéro
        count = self.db.query(SupplierPayment).filter(
            SupplierPayment.tenant_id == self.tenant_id
        ).count()
        number = f"PAY-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"

        payment = SupplierPayment(
            tenant_id=self.tenant_id,
            number=number,
            supplier_id=data.supplier_id,
            payment_date=data.payment_date,
            amount=data.amount,
            currency=data.currency,
            payment_method=data.payment_method,
            reference=data.reference,
            bank_account_id=data.bank_account_id,
            notes=data.notes,
            created_by=user_id
        )
        self.db.add(payment)
        self.db.flush()

        # Créer les affectations
        for alloc_data in data.allocations:
            allocation = PaymentAllocation(
                tenant_id=self.tenant_id,
                payment_id=payment.id,
                invoice_id=alloc_data.invoice_id,
                amount=alloc_data.amount
            )
            self.db.add(allocation)

            # Mettre à jour la facture
            invoice = self.get_purchase_invoice(alloc_data.invoice_id)
            if invoice:
                invoice.paid_amount += alloc_data.amount
                invoice.remaining_amount = invoice.total - invoice.paid_amount
                if invoice.remaining_amount <= 0:
                    invoice.status = PurchaseInvoiceStatus.PAID
                elif invoice.paid_amount > 0:
                    invoice.status = PurchaseInvoiceStatus.PARTIAL

        self.db.commit()
        self.db.refresh(payment)
        return payment

    # =========================================================================
    # ÉVALUATIONS
    # =========================================================================

    def create_supplier_evaluation(
        self,
        data: SupplierEvaluationCreate,
        user_id: UUID
    ) -> SupplierEvaluation:
        """Créer une évaluation fournisseur."""
        # Calculer le score global
        scores = [
            data.quality_score,
            data.price_score,
            data.delivery_score,
            data.service_score,
            data.reliability_score
        ]
        valid_scores = [s for s in scores if s is not None]
        overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else None

        # Statistiques
        total_orders = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.supplier_id == data.supplier_id,
            PurchaseOrder.order_date.between(data.period_start, data.period_end),
            PurchaseOrder.tenant_id == self.tenant_id
        ).count()

        total_amount = self.db.query(func.sum(PurchaseOrder.total)).filter(
            PurchaseOrder.supplier_id == data.supplier_id,
            PurchaseOrder.order_date.between(data.period_start, data.period_end),
            PurchaseOrder.tenant_id == self.tenant_id
        ).scalar() or Decimal("0")

        evaluation = SupplierEvaluation(
            tenant_id=self.tenant_id,
            supplier_id=data.supplier_id,
            evaluation_date=data.evaluation_date,
            period_start=data.period_start,
            period_end=data.period_end,
            quality_score=data.quality_score,
            price_score=data.price_score,
            delivery_score=data.delivery_score,
            service_score=data.service_score,
            reliability_score=data.reliability_score,
            overall_score=overall_score,
            total_orders=total_orders,
            total_amount=total_amount,
            comments=data.comments,
            recommendations=data.recommendations,
            evaluated_by=user_id
        )
        self.db.add(evaluation)

        # Mettre à jour le rating du fournisseur
        supplier = self.get_supplier(data.supplier_id)
        if supplier and overall_score:
            supplier.rating = overall_score
            supplier.last_evaluation_date = data.evaluation_date

        self.db.commit()
        self.db.refresh(evaluation)
        return evaluation

    # =========================================================================
    # DASHBOARD
    # =========================================================================

    def get_dashboard(self) -> ProcurementDashboard:
        """Générer le dashboard Achats."""
        today = date.today()
        first_of_month = today.replace(day=1)
        one_week = today + timedelta(days=7)

        # Fournisseurs
        total_suppliers = self.db.query(Supplier).filter(
            Supplier.tenant_id == self.tenant_id
        ).count()

        active_suppliers = self.db.query(Supplier).filter(
            Supplier.tenant_id == self.tenant_id,
            Supplier.status == SupplierStatus.APPROVED,
            Supplier.is_active == True
        ).count()

        pending_approvals = self.db.query(Supplier).filter(
            Supplier.tenant_id == self.tenant_id,
            Supplier.status == SupplierStatus.PENDING
        ).count()

        # Demandes
        pending_requisitions = self.db.query(PurchaseRequisition).filter(
            PurchaseRequisition.tenant_id == self.tenant_id,
            PurchaseRequisition.status == RequisitionStatus.SUBMITTED
        ).count()

        requisitions_this_month = self.db.query(PurchaseRequisition).filter(
            PurchaseRequisition.tenant_id == self.tenant_id,
            PurchaseRequisition.requested_date >= first_of_month
        ).count()

        # Commandes
        draft_orders = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.tenant_id == self.tenant_id,
            PurchaseOrder.status == PurchaseOrderStatus.DRAFT
        ).count()

        pending_orders = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.tenant_id == self.tenant_id,
            PurchaseOrder.status.in_([PurchaseOrderStatus.SENT, PurchaseOrderStatus.CONFIRMED])
        ).count()

        orders_this_month = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.tenant_id == self.tenant_id,
            PurchaseOrder.order_date >= first_of_month
        ).count()

        orders_amount = self.db.query(func.sum(PurchaseOrder.total)).filter(
            PurchaseOrder.tenant_id == self.tenant_id,
            PurchaseOrder.order_date >= first_of_month
        ).scalar() or Decimal("0")

        # Factures
        pending_invoices = self.db.query(PurchaseInvoice).filter(
            PurchaseInvoice.tenant_id == self.tenant_id,
            PurchaseInvoice.status == PurchaseInvoiceStatus.VALIDATED
        ).count()

        overdue_invoices = self.db.query(PurchaseInvoice).filter(
            PurchaseInvoice.tenant_id == self.tenant_id,
            PurchaseInvoice.status == PurchaseInvoiceStatus.VALIDATED,
            PurchaseInvoice.due_date < today
        ).count()

        invoices_this_month = self.db.query(PurchaseInvoice).filter(
            PurchaseInvoice.tenant_id == self.tenant_id,
            PurchaseInvoice.invoice_date >= first_of_month
        ).count()

        invoices_amount = self.db.query(func.sum(PurchaseInvoice.total)).filter(
            PurchaseInvoice.tenant_id == self.tenant_id,
            PurchaseInvoice.invoice_date >= first_of_month
        ).scalar() or Decimal("0")

        # Paiements
        unpaid_amount = self.db.query(func.sum(PurchaseInvoice.remaining_amount)).filter(
            PurchaseInvoice.tenant_id == self.tenant_id,
            PurchaseInvoice.status.in_([PurchaseInvoiceStatus.VALIDATED, PurchaseInvoiceStatus.PARTIAL])
        ).scalar() or Decimal("0")

        payments_due = self.db.query(func.sum(PurchaseInvoice.remaining_amount)).filter(
            PurchaseInvoice.tenant_id == self.tenant_id,
            PurchaseInvoice.status.in_([PurchaseInvoiceStatus.VALIDATED, PurchaseInvoiceStatus.PARTIAL]),
            PurchaseInvoice.due_date <= one_week
        ).scalar() or Decimal("0")

        return ProcurementDashboard(
            total_suppliers=total_suppliers,
            active_suppliers=active_suppliers,
            pending_approvals=pending_approvals,
            pending_requisitions=pending_requisitions,
            requisitions_this_month=requisitions_this_month,
            draft_orders=draft_orders,
            pending_orders=pending_orders,
            orders_this_month=orders_this_month,
            orders_amount_this_month=orders_amount,
            pending_invoices=pending_invoices,
            overdue_invoices=overdue_invoices,
            invoices_this_month=invoices_this_month,
            invoices_amount_this_month=invoices_amount,
            unpaid_amount=unpaid_amount,
            payments_due_this_week=payments_due
        )


def get_procurement_service(db: Session, tenant_id: str) -> ProcurementService:
    """Factory pour le service Achats."""
    return ProcurementService(db, tenant_id)
