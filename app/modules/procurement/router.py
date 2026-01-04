"""
AZALS MODULE M4 - Router Achats
===============================

Endpoints API pour la gestion des achats.
"""

from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user, get_tenant_id

from .models import (
    SupplierStatus, SupplierType, RequisitionStatus,
    PurchaseOrderStatus, ReceivingStatus, PurchaseInvoiceStatus
)
from .schemas import (
    SupplierCreate, SupplierUpdate, SupplierResponse, SupplierList,
    SupplierContactCreate, SupplierContactResponse,
    RequisitionCreate, RequisitionResponse,
    QuotationCreate, QuotationResponse,
    PurchaseOrderCreate, PurchaseOrderResponse, PurchaseOrderList,
    GoodsReceiptCreate, GoodsReceiptResponse,
    PurchaseInvoiceCreate, PurchaseInvoiceResponse, PurchaseInvoiceList,
    SupplierPaymentCreate, SupplierPaymentResponse,
    SupplierEvaluationCreate, SupplierEvaluationResponse,
    ProcurementDashboard
)
from .service import get_procurement_service

router = APIRouter(prefix="/procurement", tags=["Achats - Procurement"])


# =============================================================================
# FOURNISSEURS
# =============================================================================

@router.post("/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer un fournisseur."""
    service = get_procurement_service(db, tenant_id)
    existing = service.get_supplier_by_code(data.code)
    if existing:
        raise HTTPException(status_code=409, detail="Supplier code already exists")
    return service.create_supplier(data)


@router.get("/suppliers", response_model=SupplierList)
def list_suppliers(
    status: Optional[SupplierStatus] = None,
    supplier_type: Optional[SupplierType] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les fournisseurs."""
    service = get_procurement_service(db, tenant_id)
    items, total = service.list_suppliers(
        status=status,
        supplier_type=supplier_type,
        category=category,
        search=search,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return SupplierList(items=items, total=total)


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer un fournisseur."""
    service = get_procurement_service(db, tenant_id)
    supplier = service.get_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: UUID,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Mettre à jour un fournisseur."""
    service = get_procurement_service(db, tenant_id)
    supplier = service.update_supplier(supplier_id, data)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.post("/suppliers/{supplier_id}/approve", response_model=SupplierResponse)
def approve_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Approuver un fournisseur."""
    service = get_procurement_service(db, tenant_id)
    supplier = service.approve_supplier(supplier_id, current_user.id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.post("/suppliers/{supplier_id}/contacts", response_model=SupplierContactResponse, status_code=status.HTTP_201_CREATED)
def add_supplier_contact(
    supplier_id: UUID,
    data: SupplierContactCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Ajouter un contact fournisseur."""
    service = get_procurement_service(db, tenant_id)
    supplier = service.get_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return service.add_supplier_contact(supplier_id, data)


@router.get("/suppliers/{supplier_id}/contacts", response_model=List[SupplierContactResponse])
def get_supplier_contacts(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer les contacts d'un fournisseur."""
    service = get_procurement_service(db, tenant_id)
    return service.get_supplier_contacts(supplier_id)


# =============================================================================
# DEMANDES D'ACHAT
# =============================================================================

@router.post("/requisitions", response_model=RequisitionResponse, status_code=status.HTTP_201_CREATED)
def create_requisition(
    data: RequisitionCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une demande d'achat."""
    service = get_procurement_service(db, tenant_id)
    return service.create_requisition(data, current_user.id)


@router.get("/requisitions")
def list_requisitions(
    requisition_status: Optional[RequisitionStatus] = None,
    requester_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les demandes d'achat."""
    service = get_procurement_service(db, tenant_id)
    items, total = service.list_requisitions(
        status=requisition_status,
        requester_id=requester_id,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total}


@router.get("/requisitions/{requisition_id}", response_model=RequisitionResponse)
def get_requisition(
    requisition_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer une demande d'achat."""
    service = get_procurement_service(db, tenant_id)
    requisition = service.get_requisition(requisition_id)
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")
    return requisition


@router.post("/requisitions/{requisition_id}/submit", response_model=RequisitionResponse)
def submit_requisition(
    requisition_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Soumettre une demande d'achat."""
    service = get_procurement_service(db, tenant_id)
    requisition = service.submit_requisition(requisition_id)
    if not requisition:
        raise HTTPException(status_code=400, detail="Requisition not found or not draft")
    return requisition


@router.post("/requisitions/{requisition_id}/approve", response_model=RequisitionResponse)
def approve_requisition(
    requisition_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Approuver une demande d'achat."""
    service = get_procurement_service(db, tenant_id)
    requisition = service.approve_requisition(requisition_id, current_user.id)
    if not requisition:
        raise HTTPException(status_code=400, detail="Requisition not found or not submitted")
    return requisition


@router.post("/requisitions/{requisition_id}/reject", response_model=RequisitionResponse)
def reject_requisition(
    requisition_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Rejeter une demande d'achat."""
    service = get_procurement_service(db, tenant_id)
    requisition = service.reject_requisition(requisition_id, current_user.id, reason)
    if not requisition:
        raise HTTPException(status_code=400, detail="Requisition not found or not submitted")
    return requisition


# =============================================================================
# COMMANDES D'ACHAT
# =============================================================================

@router.post("/orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une commande d'achat."""
    service = get_procurement_service(db, tenant_id)
    return service.create_purchase_order(data, current_user.id)


@router.get("/orders", response_model=PurchaseOrderList)
def list_purchase_orders(
    supplier_id: Optional[UUID] = None,
    order_status: Optional[PurchaseOrderStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les commandes d'achat."""
    service = get_procurement_service(db, tenant_id)
    items, total = service.list_purchase_orders(
        supplier_id=supplier_id,
        status=order_status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return PurchaseOrderList(items=items, total=total)


@router.get("/orders/{order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer une commande d'achat."""
    service = get_procurement_service(db, tenant_id)
    order = service.get_purchase_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return order


@router.post("/orders/{order_id}/send", response_model=PurchaseOrderResponse)
def send_purchase_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Envoyer une commande au fournisseur."""
    service = get_procurement_service(db, tenant_id)
    order = service.send_purchase_order(order_id)
    if not order:
        raise HTTPException(status_code=400, detail="Order not found or not draft")
    return order


@router.post("/orders/{order_id}/confirm", response_model=PurchaseOrderResponse)
def confirm_purchase_order(
    order_id: UUID,
    supplier_reference: Optional[str] = None,
    confirmed_date: Optional[date] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Confirmer une commande."""
    service = get_procurement_service(db, tenant_id)
    order = service.confirm_purchase_order(order_id, supplier_reference, confirmed_date)
    if not order:
        raise HTTPException(status_code=400, detail="Order not found or not sent")
    return order


# =============================================================================
# RÉCEPTIONS
# =============================================================================

@router.post("/receipts", response_model=GoodsReceiptResponse, status_code=status.HTTP_201_CREATED)
def create_goods_receipt(
    data: GoodsReceiptCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une réception de marchandises."""
    service = get_procurement_service(db, tenant_id)
    try:
        return service.create_goods_receipt(data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/receipts/{receipt_id}/validate", response_model=GoodsReceiptResponse)
def validate_goods_receipt(
    receipt_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Valider une réception."""
    service = get_procurement_service(db, tenant_id)
    receipt = service.validate_goods_receipt(receipt_id, current_user.id)
    if not receipt:
        raise HTTPException(status_code=400, detail="Receipt not found or already validated")
    return receipt


# =============================================================================
# FACTURES D'ACHAT
# =============================================================================

@router.post("/invoices", response_model=PurchaseInvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_invoice(
    data: PurchaseInvoiceCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une facture d'achat."""
    service = get_procurement_service(db, tenant_id)
    return service.create_purchase_invoice(data, current_user.id)


@router.get("/invoices", response_model=PurchaseInvoiceList)
def list_purchase_invoices(
    supplier_id: Optional[UUID] = None,
    invoice_status: Optional[PurchaseInvoiceStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les factures d'achat."""
    service = get_procurement_service(db, tenant_id)
    items, total = service.list_purchase_invoices(
        supplier_id=supplier_id,
        status=invoice_status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return PurchaseInvoiceList(items=items, total=total)


@router.get("/invoices/{invoice_id}", response_model=PurchaseInvoiceResponse)
def get_purchase_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer une facture d'achat."""
    service = get_procurement_service(db, tenant_id)
    invoice = service.get_purchase_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("/invoices/{invoice_id}/validate", response_model=PurchaseInvoiceResponse)
def validate_purchase_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Valider une facture d'achat."""
    service = get_procurement_service(db, tenant_id)
    invoice = service.validate_purchase_invoice(invoice_id, current_user.id)
    if not invoice:
        raise HTTPException(status_code=400, detail="Invoice not found or already validated")
    return invoice


# =============================================================================
# PAIEMENTS
# =============================================================================

@router.post("/payments", response_model=SupplierPaymentResponse, status_code=status.HTTP_201_CREATED)
def create_supplier_payment(
    data: SupplierPaymentCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer un paiement fournisseur."""
    service = get_procurement_service(db, tenant_id)
    return service.create_supplier_payment(data, current_user.id)


# =============================================================================
# ÉVALUATIONS
# =============================================================================

@router.post("/evaluations", response_model=SupplierEvaluationResponse, status_code=status.HTTP_201_CREATED)
def create_supplier_evaluation(
    data: SupplierEvaluationCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une évaluation fournisseur."""
    service = get_procurement_service(db, tenant_id)
    return service.create_supplier_evaluation(data, current_user.id)


# =============================================================================
# DASHBOARD
# =============================================================================

@router.get("/dashboard", response_model=ProcurementDashboard)
def get_procurement_dashboard(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer le dashboard Achats."""
    service = get_procurement_service(db, tenant_id)
    return service.get_dashboard()
