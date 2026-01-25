"""
AZALS MODULE M4 - Service Purchases
====================================

Service pour la gestion des achats.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, selectinload

from .models import (
    InvoiceStatus,
    OrderStatus,
    LegacyPurchaseInvoice,
    LegacyPurchaseInvoiceLine,
    LegacyPurchaseOrder,
    LegacyPurchaseOrderLine,
    PurchaseSupplier,
    SupplierStatus,
)
from .schemas import (
    PurchaseInvoiceCreate,
    PurchaseInvoiceLineCreate,
    PurchaseInvoiceUpdate,
    PurchaseOrderCreate,
    PurchaseOrderLineCreate,
    PurchaseOrderUpdate,
    PurchasesSummary,
    SupplierCreate,
    SupplierUpdate,
)


class PurchasesService:
    """Service pour la gestion des achats."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2

    # ========================================================================
    # GESTION DES FOURNISSEURS
    # ========================================================================

    def create_supplier(self, data: SupplierCreate, user_id: UUID) -> PurchaseSupplier:
        """Créer un fournisseur."""
        # Vérifier si le code existe déjà
        existing = self.get_supplier_by_code(data.code)
        if existing:
            raise ValueError(f"Un fournisseur avec le code {data.code} existe déjà")

        supplier = PurchaseSupplier(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump(exclude_unset=False)
        )
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def get_supplier(self, supplier_id: UUID) -> Optional[PurchaseSupplier]:
        """Récupérer un fournisseur par ID."""
        return self.db.query(PurchaseSupplier).filter(
            PurchaseSupplier.tenant_id == self.tenant_id,
            PurchaseSupplier.id == supplier_id
        ).first()

    def get_supplier_by_code(self, code: str) -> Optional[PurchaseSupplier]:
        """Récupérer un fournisseur par code."""
        return self.db.query(PurchaseSupplier).filter(
            PurchaseSupplier.tenant_id == self.tenant_id,
            PurchaseSupplier.code == code
        ).first()

    def get_next_supplier_code(self) -> str:
        """Générer le prochain code fournisseur auto-incrémenté (FRS001, FRS002, etc.)."""
        last_supplier = self.db.query(PurchaseSupplier).filter(
            PurchaseSupplier.tenant_id == self.tenant_id,
            PurchaseSupplier.code.like("FRS%")
        ).order_by(desc(PurchaseSupplier.code)).first()

        if last_supplier and last_supplier.code.startswith("FRS"):
            try:
                last_number = int(last_supplier.code[3:])
                next_number = last_number + 1
            except ValueError:
                next_number = 1
        else:
            next_number = 1

        return f"FRS{next_number:03d}"

    def list_suppliers(
        self,
        status: Optional[SupplierStatus] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[PurchaseSupplier], int]:
        """Lister les fournisseurs avec filtres."""
        query = self.db.query(PurchaseSupplier).filter(PurchaseSupplier.tenant_id == self.tenant_id)

        if status:
            query = query.filter(PurchaseSupplier.status == status)
        if is_active is not None:
            query = query.filter(PurchaseSupplier.is_active == is_active)
        if search:
            search_filter = or_(
                PurchaseSupplier.name.ilike(f"%{search}%"),
                PurchaseSupplier.code.ilike(f"%{search}%"),
                PurchaseSupplier.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        total = query.count()
        items = query.order_by(PurchaseSupplier.name).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update_supplier(self, supplier_id: UUID, data: SupplierUpdate) -> Optional[PurchaseSupplier]:
        """Mettre à jour un fournisseur."""
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(supplier, key, value)

        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def delete_supplier(self, supplier_id: UUID) -> bool:
        """Supprimer un fournisseur (soft delete)."""
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return False

        # Vérifier qu'il n'y a pas de commandes ou factures liées
        orders_count = self.db.query(LegacyPurchaseOrder).filter(
            LegacyPurchaseOrder.tenant_id == self.tenant_id,
            LegacyPurchaseOrder.supplier_id == supplier_id
        ).count()

        if orders_count > 0:
            raise ValueError("Impossible de supprimer un fournisseur ayant des commandes")

        supplier.is_active = False
        supplier.status = SupplierStatus.INACTIVE
        self.db.commit()
        return True

    # ========================================================================
    # GESTION DES COMMANDES
    # ========================================================================

    def create_order(self, data: PurchaseOrderCreate, user_id: UUID) -> LegacyPurchaseOrder:
        """Créer une commande d'achat."""
        # Générer un numéro de commande
        order_number = self.get_next_order_number()

        # Créer la commande
        order = LegacyPurchaseOrder(
            tenant_id=self.tenant_id,
            number=order_number,
            created_by=user_id,
            **data.model_dump(exclude={"lines"}, exclude_unset=False)
        )

        # Ajouter les lignes
        total_ht = Decimal("0.00")
        total_tax = Decimal("0.00")
        total_ttc = Decimal("0.00")

        for line_data in data.lines:
            line = LegacyPurchaseOrderLine(
                tenant_id=self.tenant_id,
                **line_data.model_dump(exclude_unset=False)
            )
            # Calculer les totaux de la ligne
            self._calculate_line_totals(line)
            order.lines.append(line)

            total_ht += line.subtotal
            total_tax += line.tax_amount
            total_ttc += line.total

        # Mettre à jour les totaux de la commande
        order.total_ht = total_ht
        order.total_tax = total_tax
        order.total_ttc = total_ttc

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def get_order(self, order_id: UUID) -> Optional[LegacyPurchaseOrder]:
        """Récupérer une commande par ID avec ses lignes."""
        return self.db.query(LegacyPurchaseOrder).options(
            selectinload(LegacyPurchaseOrder.lines),
            selectinload(LegacyPurchaseOrder.supplier)
        ).filter(
            LegacyPurchaseOrder.tenant_id == self.tenant_id,
            LegacyPurchaseOrder.id == order_id
        ).first()

    def get_next_order_number(self) -> str:
        """Générer le prochain numéro de commande (CA-2024-001)."""
        year = datetime.now().year
        prefix = f"CA-{year}-"

        last_order = self.db.query(LegacyPurchaseOrder).filter(
            LegacyPurchaseOrder.tenant_id == self.tenant_id,
            LegacyPurchaseOrder.number.like(f"{prefix}%")
        ).order_by(desc(LegacyPurchaseOrder.number)).first()

        if last_order:
            try:
                last_number = int(last_order.number.split("-")[-1])
                next_number = last_number + 1
            except ValueError:
                next_number = 1
        else:
            next_number = 1

        return f"{prefix}{next_number:03d}"

    def list_orders(
        self,
        supplier_id: Optional[UUID] = None,
        status: Optional[OrderStatus] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[LegacyPurchaseOrder], int]:
        """Lister les commandes avec filtres."""
        query = self.db.query(LegacyPurchaseOrder).options(
            selectinload(LegacyPurchaseOrder.supplier)
        ).filter(LegacyPurchaseOrder.tenant_id == self.tenant_id)

        if supplier_id:
            query = query.filter(LegacyPurchaseOrder.supplier_id == supplier_id)
        if status:
            query = query.filter(LegacyPurchaseOrder.status == status)
        if search:
            query = query.filter(
                or_(
                    LegacyPurchaseOrder.number.ilike(f"%{search}%"),
                    LegacyPurchaseOrder.reference.ilike(f"%{search}%")
                )
            )

        total = query.count()
        items = query.order_by(desc(LegacyPurchaseOrder.date)).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update_order(self, order_id: UUID, data: PurchaseOrderUpdate) -> Optional[LegacyPurchaseOrder]:
        """Mettre à jour une commande."""
        order = self.get_order(order_id)
        if not order:
            return None

        # Ne permettre la modification que si DRAFT
        if order.status not in [OrderStatus.DRAFT]:
            raise ValueError("Seules les commandes en brouillon peuvent être modifiées")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(order, key, value)

        self.db.commit()
        self.db.refresh(order)
        return order

    def validate_order(self, order_id: UUID, user_id: UUID) -> Optional[LegacyPurchaseOrder]:
        """Valider une commande (DRAFT → SENT)."""
        order = self.get_order(order_id)
        if not order:
            return None

        if order.status != OrderStatus.DRAFT:
            raise ValueError("Seules les commandes en brouillon peuvent être validées")

        if not order.lines:
            raise ValueError("La commande doit avoir au moins une ligne")

        order.status = OrderStatus.SENT
        order.validated_at = datetime.now()
        order.validated_by = user_id

        self.db.commit()
        self.db.refresh(order)
        return order

    def cancel_order(self, order_id: UUID) -> Optional[LegacyPurchaseOrder]:
        """Annuler une commande."""
        order = self.get_order(order_id)
        if not order:
            return None

        if order.status in [OrderStatus.RECEIVED, OrderStatus.INVOICED]:
            raise ValueError("Impossible d'annuler une commande reçue ou facturée")

        order.status = OrderStatus.CANCELLED
        self.db.commit()
        self.db.refresh(order)
        return order

    # ========================================================================
    # GESTION DES FACTURES
    # ========================================================================

    def create_invoice(self, data: PurchaseInvoiceCreate, user_id: UUID) -> LegacyPurchaseInvoice:
        """Créer une facture fournisseur."""
        # Vérifier si le numéro existe déjà
        existing = self.db.query(LegacyPurchaseInvoice).filter(
            LegacyPurchaseInvoice.tenant_id == self.tenant_id,
            LegacyPurchaseInvoice.number == data.number
        ).first()

        if existing:
            raise ValueError(f"Une facture avec le numéro {data.number} existe déjà")

        # Créer la facture
        invoice = LegacyPurchaseInvoice(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data.model_dump(exclude={"lines"}, exclude_unset=False)
        )

        # Ajouter les lignes
        total_ht = Decimal("0.00")
        total_tax = Decimal("0.00")
        total_ttc = Decimal("0.00")

        for line_data in data.lines:
            line = LegacyPurchaseInvoiceLine(
                tenant_id=self.tenant_id,
                **line_data.model_dump(exclude_unset=False)
            )
            # Calculer les totaux de la ligne
            self._calculate_line_totals(line)
            invoice.lines.append(line)

            total_ht += line.subtotal
            total_tax += line.tax_amount
            total_ttc += line.total

        # Mettre à jour les totaux de la facture
        invoice.total_ht = total_ht
        invoice.total_tax = total_tax
        invoice.total_ttc = total_ttc

        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def get_invoice(self, invoice_id: UUID) -> Optional[LegacyPurchaseInvoice]:
        """Récupérer une facture par ID avec ses lignes."""
        return self.db.query(LegacyPurchaseInvoice).options(
            selectinload(LegacyPurchaseInvoice.lines),
            selectinload(LegacyPurchaseInvoice.supplier)
        ).filter(
            LegacyPurchaseInvoice.tenant_id == self.tenant_id,
            LegacyPurchaseInvoice.id == invoice_id
        ).first()

    def list_invoices(
        self,
        supplier_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        status: Optional[InvoiceStatus] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[LegacyPurchaseInvoice], int]:
        """Lister les factures avec filtres."""
        query = self.db.query(LegacyPurchaseInvoice).options(
            selectinload(LegacyPurchaseInvoice.supplier)
        ).filter(LegacyPurchaseInvoice.tenant_id == self.tenant_id)

        if supplier_id:
            query = query.filter(LegacyPurchaseInvoice.supplier_id == supplier_id)
        if order_id:
            query = query.filter(LegacyPurchaseInvoice.order_id == order_id)
        if status:
            query = query.filter(LegacyPurchaseInvoice.status == status)
        if search:
            query = query.filter(
                or_(
                    LegacyPurchaseInvoice.number.ilike(f"%{search}%"),
                    LegacyPurchaseInvoice.reference.ilike(f"%{search}%")
                )
            )

        total = query.count()
        items = query.order_by(desc(LegacyPurchaseInvoice.invoice_date)).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update_invoice(self, invoice_id: UUID, data: PurchaseInvoiceUpdate) -> Optional[LegacyPurchaseInvoice]:
        """Mettre à jour une facture."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return None

        # Ne permettre la modification que si DRAFT
        if invoice.status not in [InvoiceStatus.DRAFT]:
            raise ValueError("Seules les factures en brouillon peuvent être modifiées")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(invoice, key, value)

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def validate_invoice(self, invoice_id: UUID, user_id: UUID) -> Optional[LegacyPurchaseInvoice]:
        """Valider une facture (DRAFT → VALIDATED)."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return None

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValueError("Seules les factures en brouillon peuvent être validées")

        if not invoice.lines:
            raise ValueError("La facture doit avoir au moins une ligne")

        invoice.status = InvoiceStatus.VALIDATED
        invoice.validated_at = datetime.now()
        invoice.validated_by = user_id

        # Si liée à une commande, mettre à jour le statut de la commande
        if invoice.order_id:
            order = self.get_order(invoice.order_id)
            if order and order.status != OrderStatus.INVOICED:
                order.status = OrderStatus.INVOICED
                self.db.commit()

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def pay_invoice(
        self,
        invoice_id: UUID,
        payment_date: datetime,
        payment_method: str,
        amount: Optional[Decimal] = None
    ) -> Optional[LegacyPurchaseInvoice]:
        """Enregistrer le paiement d'une facture."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return None

        if invoice.status != InvoiceStatus.VALIDATED:
            raise ValueError("Seules les factures validées peuvent être payées")

        paid_amount = amount or invoice.total_ttc

        invoice.paid_at = payment_date
        invoice.paid_amount = paid_amount
        invoice.payment_method = payment_method
        invoice.payment_date = payment_date

        if paid_amount >= invoice.total_ttc:
            invoice.status = InvoiceStatus.PAID
        else:
            # Logique pour paiement partiel si nécessaire
            invoice.status = InvoiceStatus.PAID

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    # ========================================================================
    # SUMMARY / DASHBOARD
    # ========================================================================

    def get_summary(self) -> PurchasesSummary:
        """Obtenir le résumé du module achats."""
        # Fournisseurs
        total_suppliers = self.db.query(PurchaseSupplier).filter(
            PurchaseSupplier.tenant_id == self.tenant_id
        ).count()

        active_suppliers = self.db.query(PurchaseSupplier).filter(
            PurchaseSupplier.tenant_id == self.tenant_id,
            PurchaseSupplier.status == SupplierStatus.APPROVED,
            PurchaseSupplier.is_active == True
        ).count()

        pending_suppliers = self.db.query(PurchaseSupplier).filter(
            PurchaseSupplier.tenant_id == self.tenant_id,
            PurchaseSupplier.status == SupplierStatus.PENDING
        ).count()

        # Commandes
        total_orders = self.db.query(LegacyPurchaseOrder).filter(
            LegacyPurchaseOrder.tenant_id == self.tenant_id
        ).count()

        draft_orders = self.db.query(LegacyPurchaseOrder).filter(
            LegacyPurchaseOrder.tenant_id == self.tenant_id,
            LegacyPurchaseOrder.status == OrderStatus.DRAFT
        ).count()

        sent_orders = self.db.query(LegacyPurchaseOrder).filter(
            LegacyPurchaseOrder.tenant_id == self.tenant_id,
            LegacyPurchaseOrder.status == OrderStatus.SENT
        ).count()

        confirmed_orders = self.db.query(LegacyPurchaseOrder).filter(
            LegacyPurchaseOrder.tenant_id == self.tenant_id,
            LegacyPurchaseOrder.status == OrderStatus.CONFIRMED
        ).count()

        received_orders = self.db.query(LegacyPurchaseOrder).filter(
            LegacyPurchaseOrder.tenant_id == self.tenant_id,
            LegacyPurchaseOrder.status == OrderStatus.RECEIVED
        ).count()

        # Factures
        total_invoices = self.db.query(LegacyPurchaseInvoice).filter(
            LegacyPurchaseInvoice.tenant_id == self.tenant_id
        ).count()

        pending_invoices = self.db.query(LegacyPurchaseInvoice).filter(
            LegacyPurchaseInvoice.tenant_id == self.tenant_id,
            LegacyPurchaseInvoice.status == InvoiceStatus.DRAFT
        ).count()

        validated_invoices = self.db.query(LegacyPurchaseInvoice).filter(
            LegacyPurchaseInvoice.tenant_id == self.tenant_id,
            LegacyPurchaseInvoice.status == InvoiceStatus.VALIDATED
        ).count()

        paid_invoices = self.db.query(LegacyPurchaseInvoice).filter(
            LegacyPurchaseInvoice.tenant_id == self.tenant_id,
            LegacyPurchaseInvoice.status == InvoiceStatus.PAID
        ).count()

        # Montants
        period_orders_sum = self.db.query(func.sum(LegacyPurchaseOrder.total_ttc)).filter(
            LegacyPurchaseOrder.tenant_id == self.tenant_id
        ).scalar() or Decimal("0.00")

        period_invoices_sum = self.db.query(func.sum(LegacyPurchaseInvoice.total_ttc)).filter(
            LegacyPurchaseInvoice.tenant_id == self.tenant_id
        ).scalar() or Decimal("0.00")

        period_paid_sum = self.db.query(func.sum(LegacyPurchaseInvoice.paid_amount)).filter(
            LegacyPurchaseInvoice.tenant_id == self.tenant_id,
            LegacyPurchaseInvoice.status == InvoiceStatus.PAID
        ).scalar() or Decimal("0.00")

        pending_payments_sum = self.db.query(func.sum(LegacyPurchaseInvoice.total_ttc)).filter(
            LegacyPurchaseInvoice.tenant_id == self.tenant_id,
            LegacyPurchaseInvoice.status == InvoiceStatus.VALIDATED
        ).scalar() or Decimal("0.00")

        # Moyennes
        avg_order = period_orders_sum / total_orders if total_orders > 0 else Decimal("0.00")
        avg_invoice = period_invoices_sum / total_invoices if total_invoices > 0 else Decimal("0.00")

        # Top fournisseurs
        top_suppliers_data = self.db.query(
            PurchaseSupplier.id,
            PurchaseSupplier.name,
            func.sum(LegacyPurchaseOrder.total_ttc).label("total")
        ).join(
            LegacyPurchaseOrder, LegacyPurchaseOrder.supplier_id == PurchaseSupplier.id
        ).filter(
            PurchaseSupplier.tenant_id == self.tenant_id
        ).group_by(
            PurchaseSupplier.id, PurchaseSupplier.name
        ).order_by(
            desc("total")
        ).limit(5).all()

        top_suppliers = [
            {
                "id": str(s.id),
                "name": s.name,
                "total": float(s.total)
            }
            for s in top_suppliers_data
        ]

        return PurchasesSummary(
            total_suppliers=total_suppliers,
            active_suppliers=active_suppliers,
            pending_suppliers=pending_suppliers,
            total_orders=total_orders,
            draft_orders=draft_orders,
            sent_orders=sent_orders,
            confirmed_orders=confirmed_orders,
            received_orders=received_orders,
            total_invoices=total_invoices,
            pending_invoices=pending_invoices,
            validated_invoices=validated_invoices,
            paid_invoices=paid_invoices,
            period_orders_amount=period_orders_sum,
            period_invoices_amount=period_invoices_sum,
            period_paid_amount=period_paid_sum,
            pending_payments_amount=pending_payments_sum,
            average_order_amount=avg_order,
            average_invoice_amount=avg_invoice,
            top_suppliers=top_suppliers
        )

    # ========================================================================
    # MÉTHODES PRIVÉES
    # ========================================================================

    def _calculate_line_totals(self, line):
        """Calculer les totaux d'une ligne (commande ou facture)."""
        # Montant avant remise
        subtotal_before_discount = line.quantity * line.unit_price

        # Remise
        line.discount_amount = subtotal_before_discount * (line.discount_percent / Decimal("100"))

        # Subtotal HT après remise
        line.subtotal = subtotal_before_discount - line.discount_amount

        # TVA
        line.tax_amount = line.subtotal * (line.tax_rate / Decimal("100"))

        # Total TTC
        line.total = line.subtotal + line.tax_amount
