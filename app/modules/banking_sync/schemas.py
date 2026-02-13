"""
AZALS MODULE - Schémas Pydantic Synchronisation Bancaire
=========================================================

Schémas de validation pour l'API de synchronisation bancaire.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# ENUMS (reproduits pour Pydantic)
# ============================================================================

from .models import BankProvider, ConnectionStatus, SyncStatus, TransactionStatus


# ============================================================================
# SCHEMAS CONNEXION BANCAIRE
# ============================================================================

class BankConnectionBase(BaseModel):
    """Schéma de base pour une connexion bancaire."""
    provider: BankProvider = BankProvider.BUDGET_INSIGHT
    bank_name: str = Field(..., min_length=1, max_length=255)
    bank_code: Optional[str] = Field(None, max_length=50)
    auto_sync: bool = True
    sync_frequency_hours: int = Field(default=24, ge=1, le=168)


class BankConnectionCreate(BaseModel):
    """Schéma de création d'une connexion bancaire."""
    provider: BankProvider = BankProvider.BUDGET_INSIGHT
    # Les credentials sont gérés via OAuth2 flow avec le provider
    # On reçoit juste un authorization_code ou un permanent_token
    authorization_code: Optional[str] = None
    permanent_token: Optional[str] = None
    redirect_uri: Optional[str] = None


class BankConnectionUpdate(BaseModel):
    """Schéma de mise à jour d'une connexion."""
    status: Optional[ConnectionStatus] = None
    is_active: Optional[bool] = None
    auto_sync: Optional[bool] = None
    sync_frequency_hours: Optional[int] = Field(None, ge=1, le=168)
    metadata: Optional[dict] = None


class BankConnectionResponse(BankConnectionBase):
    """Schéma de réponse pour une connexion bancaire."""
    id: UUID
    tenant_id: UUID
    provider_connection_id: Optional[str] = None
    provider_user_id: Optional[str] = None
    bank_logo_url: Optional[str] = None
    status: ConnectionStatus
    is_active: bool
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[SyncStatus] = None
    next_sync_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BankConnectionListResponse(BaseModel):
    """Schéma de réponse pour une liste de connexions."""
    connections: list[BankConnectionResponse]
    total: int


# ============================================================================
# SCHEMAS COMPTE BANCAIRE
# ============================================================================

class BankAccountResponse(BaseModel):
    """Schéma de réponse pour un compte bancaire."""
    id: UUID
    connection_id: UUID
    tenant_id: UUID
    provider_account_id: Optional[str] = None
    account_name: str
    account_number: Optional[str] = None
    account_type: Optional[str] = None
    currency: str = "EUR"
    balance: Optional[float] = None
    balance_date: Optional[datetime] = None
    linked_account_id: Optional[UUID] = None
    is_active: bool
    import_transactions: bool
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BankAccountUpdate(BaseModel):
    """Schéma de mise à jour d'un compte bancaire."""
    account_name: Optional[str] = None
    is_active: Optional[bool] = None
    import_transactions: Optional[bool] = None
    linked_account_id: Optional[UUID] = None


# ============================================================================
# SCHEMAS TRANSACTION BANCAIRE
# ============================================================================

class BankTransactionResponse(BaseModel):
    """Schéma de réponse pour une transaction bancaire."""
    id: UUID
    account_id: UUID
    tenant_id: UUID
    provider_transaction_id: Optional[str] = None
    transaction_date: datetime
    value_date: Optional[datetime] = None
    amount: float
    currency: str = "EUR"
    description: str
    original_description: Optional[str] = None
    category: Optional[str] = None
    counterparty_name: Optional[str] = None
    counterparty_iban: Optional[str] = None
    status: TransactionStatus
    matched_entry_id: Optional[UUID] = None
    confidence_score: Optional[float] = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    imported_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class BankTransactionListResponse(BaseModel):
    """Schéma de réponse pour une liste de transactions."""
    transactions: list[BankTransactionResponse]
    total: int
    page: int
    page_size: int


class BankTransactionUpdate(BaseModel):
    """Schéma de mise à jour d'une transaction."""
    status: Optional[TransactionStatus] = None
    matched_entry_id: Optional[UUID] = None
    category: Optional[str] = None


class ReconcileTransactionRequest(BaseModel):
    """Schéma pour rapprocher une transaction."""
    transaction_id: UUID
    entry_id: UUID
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)


# ============================================================================
# SCHEMAS LOG SYNCHRONISATION
# ============================================================================

class BankSyncLogResponse(BaseModel):
    """Schéma de réponse pour un log de synchronisation."""
    id: UUID
    connection_id: UUID
    tenant_id: UUID
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    accounts_synced: int = 0
    transactions_imported: int = 0
    transactions_updated: int = 0
    transactions_skipped: int = 0
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    details: dict = Field(default_factory=dict)
    triggered_by: Optional[str] = None
    triggered_by_user: Optional[UUID] = None

    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS ACTIONS
# ============================================================================

class SyncConnectionRequest(BaseModel):
    """Schéma pour déclencher une synchronisation."""
    force: bool = Field(default=False, description="Forcer la sync même si récente")
    sync_transactions: bool = Field(default=True, description="Importer les transactions")
    days_back: int = Field(default=90, ge=1, le=730, description="Nombre de jours en arrière")


class SyncConnectionResponse(BaseModel):
    """Schéma de réponse d'une synchronisation."""
    success: bool
    connection_id: UUID
    sync_log_id: Optional[UUID] = None
    message: str
    accounts_synced: int = 0
    transactions_imported: int = 0


class InitiateConnectionRequest(BaseModel):
    """Schéma pour initier une connexion bancaire."""
    provider: BankProvider = BankProvider.BUDGET_INSIGHT
    bank_code: Optional[str] = None
    redirect_uri: str


class InitiateConnectionResponse(BaseModel):
    """Schéma de réponse d'initiation de connexion."""
    authorization_url: str
    state: str  # State token pour sécurité OAuth2


class CompleteConnectionRequest(BaseModel):
    """Schéma pour finaliser une connexion bancaire."""
    provider: BankProvider
    authorization_code: str
    state: str


# ============================================================================
# SCHEMAS STATISTIQUES
# ============================================================================

class BankingStats(BaseModel):
    """Statistiques bancaires."""
    total_connections: int = 0
    active_connections: int = 0
    total_accounts: int = 0
    total_transactions: int = 0
    pending_transactions: int = 0
    matched_transactions: int = 0
    last_sync_at: Optional[datetime] = None


class BankingDashboard(BaseModel):
    """Dashboard bancaire."""
    stats: BankingStats
    recent_connections: list[BankConnectionResponse] = []
    recent_transactions: list[BankTransactionResponse] = []
    pending_reconciliations: int = 0


# ============================================================================
# SCHEMAS PROVIDER
# ============================================================================

class ProviderInfoResponse(BaseModel):
    """Informations sur un provider."""
    provider: BankProvider
    is_configured: bool
    is_active: bool
    supported_banks_count: int = 0
    features: dict = Field(default_factory=dict)


class ProvidersListResponse(BaseModel):
    """Liste des providers disponibles."""
    providers: list[ProviderInfoResponse]
    default_provider: BankProvider
