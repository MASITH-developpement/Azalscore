"""
AZALS MODULE 13 - POS Router
=============================
Endpoints API pour le Point de Vente.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User

from .models import POSSessionStatus, POSTerminalStatus, POSTransactionStatus
from .schemas import (
    CashMovementCreate,
    CashMovementResponse,
    DailyReportResponse,
    HoldTransactionCreate,
    HoldTransactionResponse,
    PaymentCreate,
    POSDashboard,
    POSUserCreate,
    POSUserLogin,
    POSUserResponse,
    POSUserUpdate,
    QuickKeyCreate,
    QuickKeyResponse,
    SessionCloseRequest,
    SessionOpenRequest,
    SessionResponse,
    StoreCreate,
    StoreResponse,
    StoreUpdate,
    TerminalCreate,
    TerminalDashboard,
    TerminalResponse,
    TerminalUpdate,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
)
from .service import POSService

router = APIRouter(prefix="/pos", tags=["POS - Point de Vente"])


def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> POSService:
    """Service POS avec authentification obligatoire."""
    return POSService(db, tenant_id)


# ============================================================================
# STORES
# ============================================================================

@router.post("/stores", response_model=StoreResponse, status_code=201)
def create_store(
    data: StoreCreate,
    service: POSService = Depends(get_service)
):
    """Créer un magasin."""
    try:
        return service.create_store(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stores", response_model=list[StoreResponse])
def list_stores(
    is_active: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: POSService = Depends(get_service)
):
    """Lister les magasins."""
    return service.list_stores(is_active=is_active, skip=skip, limit=limit)


@router.get("/stores/{store_id}", response_model=StoreResponse)
def get_store(
    store_id: int,
    service: POSService = Depends(get_service)
):
    """Récupérer un magasin."""
    store = service.get_store(store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Magasin introuvable")
    return store


@router.patch("/stores/{store_id}", response_model=StoreResponse)
def update_store(
    store_id: int,
    data: StoreUpdate,
    service: POSService = Depends(get_service)
):
    """Mettre à jour un magasin."""
    store = service.update_store(store_id, data)
    if not store:
        raise HTTPException(status_code=404, detail="Magasin introuvable")
    return store


@router.delete("/stores/{store_id}", status_code=204)
def delete_store(
    store_id: int,
    service: POSService = Depends(get_service)
):
    """Désactiver un magasin."""
    if not service.delete_store(store_id):
        raise HTTPException(status_code=404, detail="Magasin introuvable")


# ============================================================================
# TERMINALS
# ============================================================================

@router.post("/terminals", response_model=TerminalResponse, status_code=201)
def create_terminal(
    data: TerminalCreate,
    service: POSService = Depends(get_service)
):
    """Créer un terminal."""
    try:
        return service.create_terminal(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/terminals", response_model=list[TerminalResponse])
def list_terminals(
    store_id: int | None = None,
    status: POSTerminalStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: POSService = Depends(get_service)
):
    """Lister les terminaux."""
    return service.list_terminals(
        store_id=store_id, status=status, skip=skip, limit=limit
    )


@router.get("/terminals/{terminal_id}", response_model=TerminalResponse)
def get_terminal(
    terminal_id: int,
    service: POSService = Depends(get_service)
):
    """Récupérer un terminal."""
    terminal = service.get_terminal(terminal_id)
    if not terminal:
        raise HTTPException(status_code=404, detail="Terminal introuvable")
    return terminal


@router.patch("/terminals/{terminal_id}", response_model=TerminalResponse)
def update_terminal(
    terminal_id: int,
    data: TerminalUpdate,
    service: POSService = Depends(get_service)
):
    """Mettre à jour un terminal."""
    terminal = service.update_terminal(terminal_id, data)
    if not terminal:
        raise HTTPException(status_code=404, detail="Terminal introuvable")
    return terminal


@router.post("/terminals/{terminal_id}/ping", response_model=TerminalResponse)
def ping_terminal(
    terminal_id: int,
    service: POSService = Depends(get_service)
):
    """Heartbeat du terminal."""
    terminal = service.ping_terminal(terminal_id)
    if not terminal:
        raise HTTPException(status_code=404, detail="Terminal introuvable")
    return terminal


@router.post("/terminals/{terminal_id}/sync", response_model=TerminalResponse)
def sync_terminal(
    terminal_id: int,
    service: POSService = Depends(get_service)
):
    """Marquer terminal synchronisé."""
    terminal = service.sync_terminal(terminal_id)
    if not terminal:
        raise HTTPException(status_code=404, detail="Terminal introuvable")
    return terminal


@router.get("/terminals/{terminal_id}/dashboard", response_model=TerminalDashboard)
def get_terminal_dashboard(
    terminal_id: int,
    service: POSService = Depends(get_service)
):
    """Dashboard d'un terminal."""
    try:
        return service.get_terminal_dashboard(terminal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# POS USERS (Cashiers)
# ============================================================================

@router.post("/users", response_model=POSUserResponse, status_code=201)
def create_pos_user(
    data: POSUserCreate,
    service: POSService = Depends(get_service)
):
    """Créer un utilisateur POS (caissier)."""
    try:
        return service.create_pos_user(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users", response_model=list[POSUserResponse])
def list_pos_users(
    is_active: bool | None = None,
    is_manager: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: POSService = Depends(get_service)
):
    """Lister les utilisateurs POS."""
    return service.list_pos_users(
        is_active=is_active, is_manager=is_manager, skip=skip, limit=limit
    )


@router.get("/users/{user_id}", response_model=POSUserResponse)
def get_pos_user(
    user_id: int,
    service: POSService = Depends(get_service)
):
    """Récupérer un utilisateur POS."""
    user = service.get_pos_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


@router.patch("/users/{user_id}", response_model=POSUserResponse)
def update_pos_user(
    user_id: int,
    data: POSUserUpdate,
    service: POSService = Depends(get_service)
):
    """Mettre à jour un utilisateur POS."""
    user = service.update_pos_user(user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


@router.post("/users/login", response_model=POSUserResponse)
def login_pos_user(
    data: POSUserLogin,
    service: POSService = Depends(get_service)
):
    """Authentifier un utilisateur POS."""
    user = service.authenticate_pos_user(data)
    if not user:
        raise HTTPException(status_code=401, detail="Authentification échouée")
    return user


# ============================================================================
# SESSIONS
# ============================================================================

@router.post("/sessions/open", response_model=SessionResponse, status_code=201)
def open_session(
    data: SessionOpenRequest,
    service: POSService = Depends(get_service)
):
    """Ouvrir une session de caisse."""
    try:
        return service.open_session(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    terminal_id: int | None = None,
    status: POSSessionStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: POSService = Depends(get_service)
):
    """Lister les sessions."""
    return service.list_sessions(
        terminal_id=terminal_id, status=status,
        date_from=date_from, date_to=date_to,
        skip=skip, limit=limit
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: int,
    service: POSService = Depends(get_service)
):
    """Récupérer une session."""
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return session


@router.post("/sessions/{session_id}/close", response_model=SessionResponse)
def close_session(
    session_id: int,
    data: SessionCloseRequest,
    closed_by_id: int = Query(..., description="ID utilisateur qui ferme"),
    service: POSService = Depends(get_service)
):
    """Fermer une session de caisse."""
    try:
        return service.close_session(session_id, data, closed_by_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/terminals/{terminal_id}/session", response_model=SessionResponse)
def get_current_session(
    terminal_id: int,
    service: POSService = Depends(get_service)
):
    """Récupérer session active du terminal."""
    session = service.get_current_session(terminal_id)
    if not session:
        raise HTTPException(status_code=404, detail="Pas de session active")
    return session


# ============================================================================
# CASH MOVEMENTS
# ============================================================================

@router.post(
    "/sessions/{session_id}/cash-movements",
    response_model=CashMovementResponse,
    status_code=201
)
def add_cash_movement(
    session_id: int,
    data: CashMovementCreate,
    performed_by_id: int = Query(..., description="ID utilisateur"),
    service: POSService = Depends(get_service)
):
    """Ajouter un mouvement de caisse."""
    try:
        return service.add_cash_movement(session_id, data, performed_by_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/sessions/{session_id}/cash-movements",
    response_model=list[CashMovementResponse]
)
def list_cash_movements(
    session_id: int,
    service: POSService = Depends(get_service)
):
    """Lister mouvements de caisse d'une session."""
    return service.list_cash_movements(session_id)


# ============================================================================
# TRANSACTIONS
# ============================================================================

@router.post(
    "/sessions/{session_id}/transactions",
    response_model=TransactionResponse,
    status_code=201
)
def create_transaction(
    session_id: int,
    data: TransactionCreate,
    cashier_id: int = Query(..., description="ID caissier"),
    service: POSService = Depends(get_service)
):
    """Créer une transaction."""
    try:
        return service.create_transaction(session_id, data, cashier_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transactions", response_model=TransactionListResponse)
def list_transactions(
    session_id: int | None = None,
    status: POSTransactionStatus | None = None,
    customer_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: POSService = Depends(get_service)
):
    """Lister les transactions."""
    items, total = service.list_transactions(
        session_id=session_id, status=status, customer_id=customer_id,
        date_from=date_from, date_to=date_to, skip=skip, limit=limit
    )
    return TransactionListResponse(
        items=items, total=total, page=skip // limit + 1, page_size=limit
    )


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    service: POSService = Depends(get_service)
):
    """Récupérer une transaction."""
    tx = service.get_transaction(transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction introuvable")
    return tx


@router.get("/transactions/receipt/{receipt_number}", response_model=TransactionResponse)
def get_transaction_by_receipt(
    receipt_number: str,
    service: POSService = Depends(get_service)
):
    """Récupérer transaction par numéro ticket."""
    tx = service.get_transaction_by_receipt(receipt_number)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction introuvable")
    return tx


@router.post(
    "/transactions/{transaction_id}/payments",
    response_model=TransactionResponse
)
def add_payment(
    transaction_id: int,
    data: PaymentCreate,
    service: POSService = Depends(get_service)
):
    """Ajouter un paiement à une transaction."""
    try:
        return service.add_payment(transaction_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transactions/{transaction_id}/void", response_model=TransactionResponse)
def void_transaction(
    transaction_id: int,
    reason: str = Query(..., min_length=1),
    voided_by_id: int = Query(..., description="ID utilisateur"),
    service: POSService = Depends(get_service)
):
    """Annuler une transaction."""
    try:
        return service.void_transaction(transaction_id, reason, voided_by_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/transactions/{transaction_id}/refund",
    response_model=TransactionResponse,
    status_code=201
)
def refund_transaction(
    transaction_id: int,
    session_id: int = Query(..., description="Session pour le remboursement"),
    cashier_id: int = Query(..., description="ID caissier"),
    reason: str = Query(..., min_length=1),
    line_items: list[dict] = None,
    service: POSService = Depends(get_service)
):
    """Créer un remboursement."""
    try:
        return service.refund_transaction(
            transaction_id, line_items or [], session_id, cashier_id, reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# QUICK KEYS
# ============================================================================

@router.post("/quick-keys", response_model=QuickKeyResponse, status_code=201)
def create_quick_key(
    data: QuickKeyCreate,
    service: POSService = Depends(get_service)
):
    """Créer un raccourci produit."""
    try:
        return service.create_quick_key(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quick-keys", response_model=list[QuickKeyResponse])
def list_quick_keys(
    store_id: int | None = None,
    page: int = Query(1, ge=1),
    service: POSService = Depends(get_service)
):
    """Lister les raccourcis."""
    return service.list_quick_keys(store_id=store_id, page=page)


@router.delete("/quick-keys/{quick_key_id}", status_code=204)
def delete_quick_key(
    quick_key_id: int,
    service: POSService = Depends(get_service)
):
    """Supprimer un raccourci."""
    if not service.delete_quick_key(quick_key_id):
        raise HTTPException(status_code=404, detail="Raccourci introuvable")


# ============================================================================
# HOLD TRANSACTIONS
# ============================================================================

@router.post(
    "/sessions/{session_id}/hold",
    response_model=HoldTransactionResponse,
    status_code=201
)
def hold_transaction(
    session_id: int,
    data: HoldTransactionCreate,
    held_by_id: int = Query(..., description="ID utilisateur"),
    service: POSService = Depends(get_service)
):
    """Mettre une transaction en attente."""
    try:
        return service.hold_transaction(session_id, data, held_by_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hold", response_model=list[HoldTransactionResponse])
def list_held_transactions(
    session_id: int | None = None,
    service: POSService = Depends(get_service)
):
    """Lister les transactions en attente."""
    return service.list_held_transactions(session_id=session_id)


@router.post("/hold/{hold_id}/recall")
def recall_held_transaction(
    hold_id: int,
    service: POSService = Depends(get_service)
):
    """Récupérer une transaction en attente."""
    data = service.recall_held_transaction(hold_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Transaction en attente introuvable")
    return data


# ============================================================================
# DAILY REPORTS (Z-Report)
# ============================================================================

@router.post(
    "/stores/{store_id}/reports/daily",
    response_model=DailyReportResponse,
    status_code=201
)
def generate_daily_report(
    store_id: int,
    report_date: date = Query(..., description="Date du rapport"),
    service: POSService = Depends(get_service)
):
    """Générer rapport journalier (Z-Report)."""
    try:
        return service.generate_daily_report(store_id, report_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/stores/{store_id}/reports/daily/{report_date}",
    response_model=DailyReportResponse
)
def get_daily_report(
    store_id: int,
    report_date: date,
    service: POSService = Depends(get_service)
):
    """Récupérer rapport journalier."""
    report = service.get_daily_report(store_id, report_date)
    if not report:
        raise HTTPException(status_code=404, detail="Rapport introuvable")
    return report


@router.get("/reports/daily", response_model=list[DailyReportResponse])
def list_daily_reports(
    store_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    service: POSService = Depends(get_service)
):
    """Lister rapports journaliers."""
    return service.list_daily_reports(
        store_id=store_id, date_from=date_from, date_to=date_to,
        skip=skip, limit=limit
    )


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=POSDashboard)
def get_pos_dashboard(
    store_id: int | None = None,
    service: POSService = Depends(get_service)
):
    """Dashboard POS global."""
    return service.get_pos_dashboard(store_id=store_id)


# ============================================================================
# OFFLINE SYNC
# ============================================================================

@router.post("/terminals/{terminal_id}/offline-queue")
def queue_offline_transaction(
    terminal_id: int,
    transaction_data: dict,
    service: POSService = Depends(get_service)
):
    """Mettre en file une transaction offline."""
    queue_item = service.queue_offline_transaction(terminal_id, transaction_data)
    return {"queue_id": queue_item.id, "status": "queued"}


@router.post("/terminals/{terminal_id}/sync-offline")
def sync_offline_transactions(
    terminal_id: int,
    service: POSService = Depends(get_service)
):
    """Synchroniser transactions offline."""
    synced = service.sync_offline_transactions(terminal_id)
    return {"synced_count": synced}
