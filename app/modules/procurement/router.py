"""
AZALS MODULE M4 - Router Achats
===============================

Endpoints API pour la gestion des achats.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_tenant_id
from app.core.database import get_db

from .models import PurchaseInvoiceStatus, PurchaseOrderStatus, RequisitionStatus, SupplierStatus, SupplierType
from .schemas import (
    GoodsReceiptCreate,
    GoodsReceiptResponse,
    ProcurementDashboard,
    PurchaseInvoiceCreate,
    PurchaseInvoiceList,
    PurchaseInvoiceResponse,
    PurchaseOrderCreate,
    PurchaseOrderList,
    PurchaseOrderResponse,
    RequisitionCreate,
    RequisitionResponse,
    SupplierContactCreate,
    SupplierContactResponse,
    SupplierCreate,
    SupplierEvaluationCreate,
    SupplierEvaluationResponse,
    SupplierList,
    SupplierPaymentCreate,
    SupplierPaymentResponse,
    SupplierResponse,
    SupplierUpdate,
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
    status: SupplierStatus | None = None,
    supplier_type: SupplierType | None = None,
    category: str | None = None,
    search: str | None = None,
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


@router.get("/suppliers/{supplier_id}/contacts", response_model=list[SupplierContactResponse])
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
    requisition_status: RequisitionStatus | None = None,
    requester_id: UUID | None = None,
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
    supplier_id: UUID | None = None,
    order_status: PurchaseOrderStatus | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
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
    supplier_reference: str | None = None,
    confirmed_date: date | None = None,
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
# ACHATS V1 - COMMANDES SIMPLIFIÉES
# =============================================================================

@router.put("/orders/{order_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    order_id: UUID,
    data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Mettre à jour une commande d'achat (DRAFT uniquement)."""
    service = get_procurement_service(db, tenant_id)
    order = service.update_purchase_order(order_id, data, current_user.id)
    if not order:
        raise HTTPException(status_code=400, detail="Order not found or not in DRAFT status")
    return order


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Supprimer une commande d'achat (DRAFT uniquement)."""
    service = get_procurement_service(db, tenant_id)
    if not service.delete_purchase_order(order_id):
        raise HTTPException(status_code=400, detail="Order not found or not in DRAFT status")
    return None


@router.post("/orders/{order_id}/validate", response_model=PurchaseOrderResponse)
def validate_purchase_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Valider une commande d'achat (DRAFT → VALIDATED)."""
    service = get_procurement_service(db, tenant_id)
    order = service.validate_purchase_order(order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=400, detail="Order not found or not in DRAFT status")
    return order


@router.post("/orders/{order_id}/create-invoice", response_model=PurchaseInvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice_from_order(
    order_id: UUID,
    invoice_date: date | None = None,
    supplier_invoice_number: str | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une facture à partir d'une commande validée."""
    service = get_procurement_service(db, tenant_id)
    invoice = service.create_invoice_from_order(
        order_id, current_user.id, invoice_date, supplier_invoice_number
    )
    if not invoice:
        raise HTTPException(status_code=400, detail="Order not found, still in DRAFT, or has no lines")
    return invoice


@router.get("/orders/export/csv")
def export_orders_csv(
    supplier_id: UUID | None = None,
    order_status: PurchaseOrderStatus | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Exporter les commandes en CSV."""
    service = get_procurement_service(db, tenant_id)
    csv_content = service.export_orders_csv(
        supplier_id=supplier_id,
        status=order_status,
        start_date=start_date,
        end_date=end_date
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=commandes.csv"}
    )


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
    supplier_id: UUID | None = None,
    invoice_status: PurchaseInvoiceStatus | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
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
# ACHATS V1 - FACTURES SIMPLIFIÉES
# =============================================================================

@router.put("/invoices/{invoice_id}", response_model=PurchaseInvoiceResponse)
def update_purchase_invoice(
    invoice_id: UUID,
    data: PurchaseInvoiceCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Mettre à jour une facture d'achat (DRAFT uniquement)."""
    service = get_procurement_service(db, tenant_id)
    invoice = service.update_purchase_invoice(invoice_id, data, current_user.id)
    if not invoice:
        raise HTTPException(status_code=400, detail="Invoice not found or not in DRAFT status")
    return invoice


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Supprimer une facture d'achat (DRAFT uniquement)."""
    service = get_procurement_service(db, tenant_id)
    if not service.delete_purchase_invoice(invoice_id):
        raise HTTPException(status_code=400, detail="Invoice not found or not in DRAFT status")
    return None


@router.get("/invoices/export/csv")
def export_invoices_csv(
    supplier_id: UUID | None = None,
    invoice_status: PurchaseInvoiceStatus | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Exporter les factures en CSV."""
    service = get_procurement_service(db, tenant_id)
    csv_content = service.export_invoices_csv(
        supplier_id=supplier_id,
        status=invoice_status,
        start_date=start_date,
        end_date=end_date
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=factures-fournisseurs.csv"}
    )


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
