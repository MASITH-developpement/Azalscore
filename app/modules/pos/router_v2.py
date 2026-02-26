"""
AZALS MODULE 13 - POS Router v2 (CORE SaaS)
============================================
Endpoints API v2 pour le Point de Vente utilisant CORE SaaS.

MIGRATION v1 -> v2:
- Utilise SaaSContext au lieu de get_current_user + get_tenant_id
- Service factory: get_pos_service(db, context.tenant_id, context.user_id)
- Pattern unifié: context: SaaSContext = Depends(get_saas_context)
"""
from __future__ import annotations


from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

from .models import POSProductQuickKey, POSSessionStatus, POSTerminalStatus, POSTransactionStatus
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
    SessionDashboardResponse,
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

router = APIRouter(prefix="/v2/pos", tags=["POS v2 - CORE SaaS"])


def get_pos_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
) -> POSService:
    """Service POS v2 avec CORE SaaS."""
    return POSService(db, context.tenant_id, str(context.user_id))


# ============================================================================
# STORES
# ============================================================================

@router.post("/stores", response_model=StoreResponse, status_code=201)
def create_store(
    data: StoreCreate,
    service: POSService = Depends(get_pos_service)
):
    """Créer un magasin."""
    return service.create_store(data)


@router.get("/stores", response_model=list[StoreResponse])
def list_stores(
    is_active: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: POSService = Depends(get_pos_service)
):
    """Lister les magasins."""
    return service.list_stores(is_active=is_active, skip=skip, limit=limit)


@router.get("/stores/{store_id}", response_model=StoreResponse)
def get_store(
    store_id: int,
    service: POSService = Depends(get_pos_service)
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
    service: POSService = Depends(get_pos_service)
):
    """Mettre à jour un magasin."""
    store = service.update_store(store_id, data)
    if not store:
        raise HTTPException(status_code=404, detail="Magasin introuvable")
    return store


@router.delete("/stores/{store_id}", status_code=204)
def delete_store(
    store_id: int,
    service: POSService = Depends(get_pos_service)
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
    service: POSService = Depends(get_pos_service)
):
    """Créer un terminal."""
    return service.create_terminal(data)


@router.get("/terminals", response_model=list[TerminalResponse])
def list_terminals(
    store_id: int | None = None,
    status: POSTerminalStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: POSService = Depends(get_pos_service)
):
    """Lister les terminaux."""
    return service.list_terminals(
        store_id=store_id, status=status, skip=skip, limit=limit
    )


@router.get("/terminals/{terminal_id}", response_model=TerminalResponse)
def get_terminal(
    terminal_id: int,
    service: POSService = Depends(get_pos_service)
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
    service: POSService = Depends(get_pos_service)
):
    """Mettre à jour un terminal."""
    terminal = service.update_terminal(terminal_id, data)
    if not terminal:
        raise HTTPException(status_code=404, detail="Terminal introuvable")
    return terminal


@router.delete("/terminals/{terminal_id}", status_code=204)
def delete_terminal(
    terminal_id: int,
    service: POSService = Depends(get_pos_service)
):
    """Désactiver un terminal (soft delete)."""
    terminal = service.get_terminal(terminal_id)
    if not terminal:
        raise HTTPException(status_code=404, detail="Terminal introuvable")
    terminal.is_active = False
    return


# ============================================================================
# POS USERS (Cashiers)
# ============================================================================

@router.post("/users", response_model=POSUserResponse, status_code=201)
def create_pos_user(
    data: POSUserCreate,
    service: POSService = Depends(get_pos_service)
):
    """Créer un utilisateur POS (caissier)."""
    return service.create_pos_user(data)


@router.get("/users", response_model=list[POSUserResponse])
def list_pos_users(
    is_active: bool | None = None,
    is_manager: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: POSService = Depends(get_pos_service)
):
    """Lister les utilisateurs POS."""
    return service.list_pos_users(
        is_active=is_active, is_manager=is_manager, skip=skip, limit=limit
    )


@router.post("/users/login", response_model=POSUserResponse)
def login_pos_user(
    data: POSUserLogin,
    service: POSService = Depends(get_pos_service)
):
    """Authentifier un utilisateur POS."""
    user = service.authenticate_pos_user(data)
    if not user:
        raise HTTPException(status_code=401, detail="Authentification échouée")
    return user


@router.patch("/users/{user_id}", response_model=POSUserResponse)
def update_pos_user(
    user_id: int,
    data: POSUserUpdate,
    service: POSService = Depends(get_pos_service)
):
    """Mettre à jour un utilisateur POS."""
    user = service.update_pos_user(user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


# ============================================================================
# SESSIONS
# ============================================================================

@router.post("/sessions/open", response_model=SessionResponse, status_code=201)
def open_session(
    data: SessionOpenRequest,
    service: POSService = Depends(get_pos_service)
):
    """Ouvrir une session de caisse."""
    return service.open_session(data)


@router.post("/sessions/{session_id}/close", response_model=SessionResponse)
def close_session(
    session_id: int,
    data: SessionCloseRequest,
    closed_by_id: int = Query(..., description="ID utilisateur qui ferme"),
    service: POSService = Depends(get_pos_service)
):
    """Fermer une session de caisse."""
    return service.close_session(session_id, data, closed_by_id)


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    terminal_id: int | None = None,
    status: POSSessionStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: POSService = Depends(get_pos_service)
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
    service: POSService = Depends(get_pos_service)
):
    """Récupérer une session."""
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return session


@router.get("/sessions/{session_id}/dashboard", response_model=SessionDashboardResponse)
def get_session_dashboard(
    session_id: int,
    service: POSService = Depends(get_pos_service)
):
    """Dashboard d'une session."""
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    return SessionDashboardResponse(
        session_id=session.id,
        session_number=session.session_number,
        status=session.status.value,
        total_sales=float(session.total_sales or 0),
        transaction_count=session.transaction_count or 0,
        cash_total=float(session.cash_total or 0),
        card_total=float(session.card_total or 0),
    )


# ============================================================================
# TRANSACTIONS
# ============================================================================

@router.post("/transactions", response_model=TransactionResponse, status_code=201)
def create_transaction(
    session_id: int = Query(..., description="ID session"),
    cashier_id: int = Query(..., description="ID caissier"),
    data: TransactionCreate = None,
    service: POSService = Depends(get_pos_service)
):
    """Créer une transaction."""
    return service.create_transaction(session_id, data, cashier_id)


@router.get("/transactions", response_model=TransactionListResponse)
def list_transactions(
    session_id: int | None = None,
    status: POSTransactionStatus | None = None,
    customer_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: POSService = Depends(get_pos_service)
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
    service: POSService = Depends(get_pos_service)
):
    """Récupérer une transaction."""
    tx = service.get_transaction(transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction introuvable")
    return tx


@router.post("/transactions/{transaction_id}/pay", response_model=TransactionResponse)
def add_payment(
    transaction_id: int,
    data: PaymentCreate,
    service: POSService = Depends(get_pos_service)
):
    """Ajouter un paiement à une transaction."""
    return service.add_payment(transaction_id, data)


@router.post("/transactions/{transaction_id}/void", response_model=TransactionResponse)
def void_transaction(
    transaction_id: int,
    reason: str = Query(..., min_length=1),
    voided_by_id: int = Query(..., description="ID utilisateur"),
    service: POSService = Depends(get_pos_service)
):
    """Annuler une transaction."""
    return service.void_transaction(transaction_id, reason, voided_by_id)


@router.post("/transactions/{transaction_id}/refund", response_model=TransactionResponse, status_code=201)
def refund_transaction(
    transaction_id: int,
    session_id: int = Query(..., description="Session pour le remboursement"),
    cashier_id: int = Query(..., description="ID caissier"),
    reason: str = Query(..., min_length=1),
    line_items: list[dict] = None,
    service: POSService = Depends(get_pos_service)
):
    """Créer un remboursement."""
    return service.refund_transaction(
        transaction_id, line_items or [], session_id, cashier_id, reason
    )


# ============================================================================
# HOLD TRANSACTIONS
# ============================================================================

@router.post("/hold", response_model=HoldTransactionResponse, status_code=201)
def hold_transaction(
    session_id: int = Query(..., description="ID session"),
    held_by_id: int = Query(..., description="ID utilisateur"),
    data: HoldTransactionCreate = None,
    service: POSService = Depends(get_pos_service)
):
    """Mettre une transaction en attente."""
    return service.hold_transaction(session_id, data, held_by_id)


@router.get("/hold", response_model=list[HoldTransactionResponse])
def list_held_transactions(
    session_id: int | None = None,
    service: POSService = Depends(get_pos_service)
):
    """Lister les transactions en attente."""
    return service.list_held_transactions(session_id=session_id)


@router.post("/hold/{hold_id}/resume")
def resume_held_transaction(
    hold_id: int,
    service: POSService = Depends(get_pos_service)
):
    """Reprendre une transaction en attente."""
    data = service.recall_held_transaction(hold_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Transaction en attente introuvable")
    return data


@router.delete("/hold/{hold_id}", status_code=204)
def delete_held_transaction(
    hold_id: int,
    service: POSService = Depends(get_pos_service)
):
    """Supprimer une transaction en attente."""
    data = service.recall_held_transaction(hold_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Transaction en attente introuvable")


# ============================================================================
# CASH MOVEMENTS
# ============================================================================

@router.post("/cash-movements", response_model=CashMovementResponse, status_code=201)
def add_cash_movement(
    session_id: int = Query(..., description="ID session"),
    performed_by_id: int = Query(..., description="ID utilisateur"),
    data: CashMovementCreate = None,
    service: POSService = Depends(get_pos_service)
):
    """Ajouter un mouvement de caisse."""
    return service.add_cash_movement(session_id, data, performed_by_id)


@router.get("/cash-movements", response_model=list[CashMovementResponse])
def list_cash_movements(
    session_id: int = Query(..., description="ID session"),
    service: POSService = Depends(get_pos_service)
):
    """Lister mouvements de caisse d'une session."""
    return service.list_cash_movements(session_id)


# ============================================================================
# QUICK KEYS
# ============================================================================

@router.post("/quick-keys", response_model=QuickKeyResponse, status_code=201)
def create_quick_key(
    data: QuickKeyCreate,
    service: POSService = Depends(get_pos_service)
):
    """Créer un raccourci produit."""
    return service.create_quick_key(data)


@router.get("/quick-keys", response_model=list[QuickKeyResponse])
def list_quick_keys(
    store_id: int | None = None,
    page: int = Query(1, ge=1),
    service: POSService = Depends(get_pos_service)
):
    """Lister les raccourcis."""
    return service.list_quick_keys(store_id=store_id, page=page)


@router.patch("/quick-keys/{quick_key_id}", response_model=QuickKeyResponse)
def update_quick_key(
    quick_key_id: int,
    data: QuickKeyCreate,
    service: POSService = Depends(get_pos_service)
):
    """Mettre à jour un raccourci."""
    # SÉCURITÉ: TOUJOURS filtrer par tenant_id
    existing = service.db.query(POSProductQuickKey).filter(
        POSProductQuickKey.tenant_id == service.tenant_id,
        POSProductQuickKey.id == quick_key_id
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Raccourci introuvable")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(existing, field, value)

    service.db.commit()
    service.db.refresh(existing)
    return existing


@router.delete("/quick-keys/{quick_key_id}", status_code=204)
def delete_quick_key(
    quick_key_id: int,
    service: POSService = Depends(get_pos_service)
):
    """Supprimer un raccourci."""
    if not service.delete_quick_key(quick_key_id):
        raise HTTPException(status_code=404, detail="Raccourci introuvable")


# ============================================================================
# DAILY REPORTS (Z-Report)
# ============================================================================

@router.get("/reports/daily", response_model=list[DailyReportResponse])
def list_daily_reports(
    store_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    service: POSService = Depends(get_pos_service)
):
    """Lister rapports journaliers."""
    return service.list_daily_reports(
        store_id=store_id, date_from=date_from, date_to=date_to,
        skip=skip, limit=limit
    )


@router.get("/reports/daily/{date}", response_model=DailyReportResponse)
def get_daily_report(
    date: date,
    store_id: int = Query(..., description="ID magasin"),
    service: POSService = Depends(get_pos_service)
):
    """Récupérer rapport journalier d'une date."""
    report = service.get_daily_report(store_id, date)
    if not report:
        raise HTTPException(status_code=404, detail="Rapport introuvable")
    return report


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=POSDashboard)
def get_pos_dashboard(
    store_id: int | None = None,
    service: POSService = Depends(get_pos_service)
):
    """Dashboard POS global."""
    return service.get_pos_dashboard(store_id=store_id)
