"""
AZALS - Module Synchronisation Bancaire - API Router
=====================================================
Endpoints API pour la synchronisation bancaire automatique.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.saas_context import SaaSContext, get_saas_context
from app.db import get_db

from .models import BankProvider, ConnectionStatus, TransactionStatus
from .schemas import (
    BankAccountResponse,
    BankConnectionListResponse,
    BankConnectionResponse,
    BankConnectionUpdate,
    BankingDashboard,
    BankingStats,
    BankTransactionListResponse,
    CompleteConnectionRequest,
    InitiateConnectionRequest,
    InitiateConnectionResponse,
    ProvidersListResponse,
    ReconcileTransactionRequest,
    SyncConnectionRequest,
    SyncConnectionResponse,
)
from .service import BankingSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/banking-sync", tags=["Banking Sync"])


# ============================================================================
# CONNEXIONS BANCAIRES
# ============================================================================

@router.get("/connections", response_model=BankConnectionListResponse)
def list_connections(
    status_filter: Optional[ConnectionStatus] = None,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les connexions bancaires du tenant.
    
    - **status**: Filtrer par statut (ACTIVE, ERROR, etc.)
    """
    service = BankingSyncService(db, ctx.tenant_id, ctx.user_id)
    return service.list_connections(status=status_filter)


@router.get("/connections/{connection_id}", response_model=BankConnectionResponse)
def get_connection(
    connection_id: UUID,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupère les détails d'une connexion bancaire."""
    service = BankingSyncService(db, ctx.tenant_id, ctx.user_id)
    connection = service.get_connection(str(connection_id))
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connexion non trouvée"
        )
    
    return BankConnectionResponse.model_validate(connection)


@router.patch("/connections/{connection_id}", response_model=BankConnectionResponse)
def update_connection(
    connection_id: UUID,
    data: BankConnectionUpdate,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Met à jour une connexion bancaire."""
    service = BankingSyncService(db, ctx.tenant_id, ctx.user_id)
    connection = service.update_connection(str(connection_id), data)
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connexion non trouvée"
        )
    
    return BankConnectionResponse.model_validate(connection)


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: UUID,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Supprime une connexion bancaire."""
    service = BankingSyncService(db, ctx.tenant_id, ctx.user_id)
    success = service.delete_connection(str(connection_id))
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connexion non trouvée"
        )
    
    return None


# ============================================================================
# OAUTH2 FLOW
# ============================================================================

@router.post("/initiate", response_model=InitiateConnectionResponse)
def initiate_connection(
    request: InitiateConnectionRequest,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Initie le processus de connexion bancaire OAuth2.
    
    Retourne l'URL d'autorisation pour rediriger l'utilisateur vers la banque.
    """
    # TODO: Générer l'URL d'autorisation via le provider
    state_token = f"state_{ctx.tenant_id}_{ctx.user_id}"
    
    authorization_url = f"https://connect.{request.provider.value.lower()}.com/authorize?state={state_token}"
    
    return InitiateConnectionResponse(
        authorization_url=authorization_url,
        state=state_token
    )


@router.post("/complete", response_model=BankConnectionResponse, status_code=status.HTTP_201_CREATED)
def complete_connection(
    request: CompleteConnectionRequest,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Finalise la connexion bancaire après OAuth2.
    
    Appelé après que l'utilisateur a autorisé l'accès à sa banque.
    """
    service = BankingSyncService(db, ctx.tenant_id, ctx.user_id)
    
    connection = service.create_connection(
        provider=request.provider,
        authorization_code=request.authorization_code,
        redirect_uri=None
    )
    
    return BankConnectionResponse.model_validate(connection)


# ============================================================================
# SYNCHRONISATION
# ============================================================================

@router.post("/sync/{connection_id}", response_model=SyncConnectionResponse)
def sync_connection(
    connection_id: UUID,
    request: SyncConnectionRequest,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Déclenche la synchronisation d'une connexion bancaire.
    
    - **force**: Forcer la sync même si récente
    - **sync_transactions**: Importer les transactions
    - **days_back**: Nombre de jours en arrière (1-730)
    """
    service = BankingSyncService(db, ctx.tenant_id, ctx.user_id)
    
    result = service.sync_connection(
        str(connection_id),
        force=request.force,
        days_back=request.days_back
    )
    
    return result


# ============================================================================
# COMPTES ET TRANSACTIONS
# ============================================================================

@router.get("/accounts", response_model=list[BankAccountResponse])
def list_accounts(
    connection_id: Optional[UUID] = None,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les comptes bancaires synchronisés.
    
    - **connection_id**: Filtrer par connexion
    """
    service = BankingSyncService(db, ctx.tenant_id, ctx.user_id)
    return service.list_accounts(
        connection_id=str(connection_id) if connection_id else None
    )


@router.get("/transactions", response_model=BankTransactionListResponse)
def list_transactions(
    account_id: Optional[UUID] = None,
    status_filter: Optional[TransactionStatus] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les transactions bancaires importées.
    
    - **account_id**: Filtrer par compte
    - **status**: Filtrer par statut (PENDING, MATCHED, etc.)
    """
    service = BankingSyncService(db, ctx.tenant_id, ctx.user_id)
    return service.list_transactions(
        account_id=str(account_id) if account_id else None,
        status=status_filter,
        page=page,
        page_size=page_size
    )


@router.post("/reconcile", status_code=status.HTTP_200_OK)
def reconcile_transaction(
    request: ReconcileTransactionRequest,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Rapproche une transaction bancaire avec une écriture comptable.
    
    - **transaction_id**: ID de la transaction bancaire
    - **entry_id**: ID de l'écriture comptable
    - **confidence_score**: Score de confiance (0-1)
    """
    # TODO: Implémenter dans le service
    return {
        "success": True,
        "message": "Transaction rapprochée (à implémenter)"
    }


# ============================================================================
# STATISTIQUES
# ============================================================================

@router.get("/stats", response_model=BankingStats)
def get_banking_stats(
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupère les statistiques bancaires du tenant."""
    service = BankingSyncService(db, ctx.tenant_id, ctx.user_id)
    return service.get_stats()


@router.get("/dashboard", response_model=BankingDashboard)
def get_banking_dashboard(
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Récupère le dashboard bancaire.
    
    Inclut statistiques + connexions récentes + transactions récentes.
    """
    service = BankingSyncService(db, ctx.tenant_id, ctx.user_id)
    
    stats = service.get_stats()
    connections = service.list_connections()
    transactions = service.list_transactions(page=1, page_size=10)
    
    return BankingDashboard(
        stats=stats,
        recent_connections=connections.connections[:5],
        recent_transactions=transactions.transactions,
        pending_reconciliations=stats.pending_transactions
    )


# ============================================================================
# PROVIDERS
# ============================================================================

@router.get("/providers", response_model=ProvidersListResponse)
def list_providers(
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste les providers d'agrégation bancaire disponibles.
    
    Retourne la configuration et l'état de chaque provider.
    """
    from .schemas import ProviderInfoResponse
    
    providers = [
        ProviderInfoResponse(
            provider=BankProvider.BUDGET_INSIGHT,
            is_configured=False,  # TODO: Check tenant settings
            is_active=False,
            supported_banks_count=200,
            features={
                "french_banks": True,
                "european_banks": True,
                "real_time_sync": False,
                "psd2_compliant": True
            }
        ),
        ProviderInfoResponse(
            provider=BankProvider.BRIDGE,
            is_configured=False,
            is_active=False,
            supported_banks_count=150,
            features={
                "french_banks": True,
                "modern_api": True,
                "real_time_sync": True,
                "psd2_compliant": True
            }
        )
    ]
    
    return ProvidersListResponse(
        providers=providers,
        default_provider=BankProvider.BUDGET_INSIGHT
    )
