"""
AZALS MODULE - Odoo Import - Schemas
=====================================

Schemas Pydantic pour les requetes/reponses API du module Odoo Import.
"""
from __future__ import annotations


from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ============================================================================
# CONFIGURATION SCHEMAS
# ============================================================================

class OdooConnectionConfigCreate(BaseModel):
    """Schema pour creer une configuration de connexion Odoo."""
    name: str = Field(..., min_length=1, max_length=255, description="Nom de la connexion")
    description: Optional[str] = Field(None, description="Description optionnelle")

    # Connexion
    odoo_url: str = Field(..., description="URL de l'instance Odoo (ex: https://mycompany.odoo.com)")
    odoo_database: str = Field(..., min_length=1, max_length=100, description="Nom de la base Odoo")

    # Authentification
    auth_method: str = Field("api_key", description="Methode: 'password' ou 'api_key'")
    username: str = Field(..., min_length=1, description="Nom d'utilisateur Odoo")
    credential: str = Field(..., min_length=1, description="Mot de passe ou API key")

    # Options de sync - Donnees de base
    sync_products: bool = Field(True, description="Synchroniser les produits")
    sync_contacts: bool = Field(True, description="Synchroniser les contacts/clients")
    sync_suppliers: bool = Field(True, description="Synchroniser les fournisseurs")
    # Commandes
    sync_purchase_orders: bool = Field(False, description="Synchroniser les commandes d'achat")
    sync_sale_orders: bool = Field(False, description="Synchroniser les commandes de vente")
    # Documents commerciaux
    sync_invoices: bool = Field(True, description="Synchroniser les factures")
    sync_quotes: bool = Field(True, description="Synchroniser les devis")
    # Finance
    sync_accounting: bool = Field(False, description="Synchroniser la comptabilite")
    sync_bank: bool = Field(False, description="Synchroniser les releves bancaires")
    # Services
    sync_interventions: bool = Field(False, description="Synchroniser les interventions")

    @field_validator('odoo_url')
    @classmethod
    def validate_odoo_url(cls, v: str) -> str:
        """Valide et normalise l'URL Odoo."""
        v = v.strip().rstrip('/')
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v

    @field_validator('auth_method')
    @classmethod
    def validate_auth_method(cls, v: str) -> str:
        """Valide la methode d'authentification."""
        if v not in ('password', 'api_key'):
            raise ValueError("auth_method doit etre 'password' ou 'api_key'")
        return v


class OdooConnectionConfigUpdate(BaseModel):
    """Schema pour modifier une configuration de connexion Odoo."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    odoo_url: Optional[str] = None
    odoo_database: Optional[str] = None
    auth_method: Optional[str] = None
    username: Optional[str] = None
    credential: Optional[str] = None  # Nouveau mot de passe/API key
    sync_products: Optional[bool] = None
    sync_contacts: Optional[bool] = None
    sync_suppliers: Optional[bool] = None
    sync_purchase_orders: Optional[bool] = None
    sync_sale_orders: Optional[bool] = None
    sync_invoices: Optional[bool] = None
    sync_quotes: Optional[bool] = None
    sync_accounting: Optional[bool] = None
    sync_bank: Optional[bool] = None
    sync_interventions: Optional[bool] = None
    is_active: Optional[bool] = None

    @field_validator('odoo_url')
    @classmethod
    def validate_odoo_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().rstrip('/')
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v


class OdooConnectionConfigResponse(BaseModel):
    """Schema de reponse pour une configuration de connexion."""
    id: UUID
    tenant_id: str
    name: str
    description: Optional[str]
    odoo_url: str
    odoo_database: str
    odoo_version: Optional[str]
    auth_method: str
    username: str
    # Note: credential n'est jamais retourne pour securite

    sync_products: bool
    sync_contacts: bool
    sync_suppliers: bool
    sync_purchase_orders: bool
    sync_sale_orders: bool = False
    sync_invoices: bool = True
    sync_quotes: bool = True
    sync_accounting: bool = False
    sync_bank: bool = False
    sync_interventions: bool = False

    products_last_sync_at: Optional[datetime]
    contacts_last_sync_at: Optional[datetime]
    suppliers_last_sync_at: Optional[datetime]
    orders_last_sync_at: Optional[datetime]

    total_imports: int
    total_products_imported: int
    total_contacts_imported: int
    total_suppliers_imported: int
    total_orders_imported: int
    last_error_message: Optional[str]

    is_active: bool
    is_connected: bool
    last_connection_test_at: Optional[datetime]

    # Planification
    schedule_mode: str = "disabled"
    schedule_cron_expression: Optional[str] = None
    schedule_interval_minutes: Optional[int] = None
    schedule_timezone: str = "Europe/Paris"
    schedule_paused: bool = False
    next_scheduled_run: Optional[datetime] = None
    last_scheduled_run: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TEST CONNECTION
# ============================================================================

class OdooTestConnectionRequest(BaseModel):
    """Schema pour tester une connexion Odoo."""
    odoo_url: str
    odoo_database: str
    auth_method: str = "api_key"
    username: str
    credential: str

    @field_validator('odoo_url')
    @classmethod
    def validate_odoo_url(cls, v: str) -> str:
        v = v.strip().rstrip('/')
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v


class OdooTestConnectionResponse(BaseModel):
    """Reponse du test de connexion."""
    success: bool
    message: str
    odoo_version: Optional[str] = None
    database_name: Optional[str] = None
    user_name: Optional[str] = None
    available_models: Optional[List[str]] = None


# ============================================================================
# IMPORT OPERATIONS
# ============================================================================

class OdooImportRequest(BaseModel):
    """Schema pour lancer un import."""
    config_id: UUID
    sync_type: str = Field(..., description="Type: products, contacts, suppliers, purchase_orders, full")
    full_sync: bool = Field(False, description="Si True, ignore le delta et reimporte tout")

    @field_validator('sync_type')
    @classmethod
    def validate_sync_type(cls, v: str) -> str:
        valid = ['products', 'contacts', 'suppliers', 'purchase_orders', 'full']
        if v not in valid:
            raise ValueError(f"sync_type doit etre parmi: {valid}")
        return v


class OdooImportProgress(BaseModel):
    """Progression d'un import en cours."""
    import_id: UUID
    sync_type: str
    status: str
    progress_percent: int = Field(0, ge=0, le=100)
    current_record: int = 0
    total_records: int = 0
    created_count: int = 0
    updated_count: int = 0
    error_count: int = 0
    started_at: datetime
    estimated_completion: Optional[datetime] = None


class OdooImportHistoryResponse(BaseModel):
    """Historique d'un import."""
    id: UUID
    config_id: UUID
    sync_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    total_records: int
    created_count: int
    updated_count: int
    skipped_count: int
    error_count: int
    error_details: List[Dict[str, Any]]
    is_delta_sync: bool
    delta_from_date: Optional[datetime]
    triggered_by: Optional[UUID]
    trigger_method: str

    class Config:
        from_attributes = True


# ============================================================================
# FIELD MAPPING
# ============================================================================

class OdooFieldMappingCreate(BaseModel):
    """Schema pour creer un mapping de champs personnalise."""
    config_id: UUID
    odoo_model: str = Field(..., description="Modele Odoo (ex: product.product)")
    azals_model: str = Field(..., description="Modele AZALSCORE (ex: Product)")
    field_mapping: Dict[str, str] = Field(..., description="Mapping {champ_odoo: champ_azals}")
    transformations: Optional[Dict[str, Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Transformations par champ"
    )
    is_active: bool = True
    priority: int = 100


class OdooFieldMappingResponse(BaseModel):
    """Reponse pour un mapping de champs."""
    id: UUID
    config_id: UUID
    odoo_model: str
    azals_model: str
    field_mapping: Dict[str, str]
    transformations: Dict[str, Dict[str, Any]]
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ODOO DATA PREVIEW
# ============================================================================

class OdooDataPreviewRequest(BaseModel):
    """Schema pour previsualiser les donnees Odoo avant import."""
    config_id: UUID
    model: str = Field(..., description="Modele Odoo a previsualiser")
    limit: int = Field(10, ge=1, le=100, description="Nombre de records a previsualiser")
    fields: Optional[List[str]] = Field(None, description="Champs specifiques a recuperer")


class OdooDataPreviewResponse(BaseModel):
    """Previsualisation des donnees Odoo."""
    model: str
    total_count: int
    preview_count: int
    fields: List[str]
    records: List[Dict[str, Any]]
    mapping_preview: List[Dict[str, Any]]  # Donnees mappees vers AZALSCORE


# ============================================================================
# STATUS & STATS
# ============================================================================

class OdooImportStatus(BaseModel):
    """Statut global des imports Odoo pour un tenant."""
    active_imports: List[OdooImportProgress]
    recent_imports: List[OdooImportHistoryResponse]
    configs: List[OdooConnectionConfigResponse]
    total_products_synced: int
    total_contacts_synced: int
    total_suppliers_synced: int
    total_orders_synced: int
    last_sync_at: Optional[datetime]
    next_scheduled_sync: Optional[datetime]


class OdooSyncStats(BaseModel):
    """Statistiques de synchronisation."""
    config_id: UUID
    config_name: str
    sync_type: str
    total_syncs: int
    last_sync_at: Optional[datetime]
    last_sync_status: Optional[str]
    average_duration_seconds: Optional[int]
    total_records_synced: int
    success_rate: Decimal = Field(..., ge=0, le=100)


# ============================================================================
# SCHEDULING SCHEMAS
# ============================================================================

class OdooScheduleConfigRequest(BaseModel):
    """Schema pour configurer la planification d'une connexion Odoo."""
    mode: str = Field(
        ...,
        description="Mode de planification: 'disabled', 'cron' ou 'interval'"
    )
    cron_expression: Optional[str] = Field(
        None,
        description="Expression cron si mode='cron' (ex: '0 8 * * 1-5' = 8h lun-ven)"
    )
    interval_minutes: Optional[int] = Field(
        None,
        ge=5,
        le=1440,
        description="Intervalle en minutes si mode='interval' (5-1440)"
    )
    timezone: str = Field(
        "Europe/Paris",
        description="Fuseau horaire pour le cron"
    )

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str) -> str:
        valid = ['disabled', 'cron', 'interval']
        if v not in valid:
            raise ValueError(f"mode doit etre parmi: {valid}")
        return v

    @field_validator('cron_expression')
    @classmethod
    def validate_cron(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Validation basique du format cron
        parts = v.strip().split()
        if len(parts) != 5:
            raise ValueError("Expression cron invalide (doit avoir 5 parties)")
        return v.strip()


class OdooScheduleConfigResponse(BaseModel):
    """Reponse pour la configuration de planification."""
    config_id: UUID
    mode: str
    cron_expression: Optional[str]
    interval_minutes: Optional[int]
    timezone: str
    is_paused: bool
    next_scheduled_run: Optional[datetime]
    last_scheduled_run: Optional[datetime]
    message: str


class OdooNextRunsResponse(BaseModel):
    """Liste des prochaines executions planifiees."""
    config_id: UUID
    mode: str
    next_runs: List[datetime]


# ============================================================================
# SELECTIVE IMPORT SCHEMAS
# ============================================================================

class OdooSelectiveImportRequest(BaseModel):
    """Schema pour un import selectif."""
    types: List[str] = Field(
        ...,
        min_length=1,
        description="Types a importer: products, contacts, suppliers, invoices, quotes, etc."
    )
    full_sync: bool = Field(
        False,
        description="Si True, ignore les deltas"
    )

    @field_validator('types')
    @classmethod
    def validate_types(cls, v: List[str]) -> List[str]:
        valid = [
            'products', 'contacts', 'suppliers', 'purchase_orders',
            'sale_orders', 'invoices', 'quotes', 'accounting',
            'bank', 'interventions'
        ]
        for t in v:
            if t not in valid:
                raise ValueError(f"Type invalide '{t}'. Valides: {valid}")
        return v


# ============================================================================
# ADVANCED HISTORY SEARCH SCHEMAS
# ============================================================================

class OdooHistorySearchRequest(BaseModel):
    """Schema pour la recherche avancee dans l'historique."""
    config_id: Optional[UUID] = Field(None, description="Filtrer par configuration")
    sync_type: Optional[str] = Field(None, description="Filtrer par type de sync")
    status: Optional[str] = Field(None, description="Filtrer par statut")
    trigger_method: Optional[str] = Field(None, description="Filtrer par declencheur")
    date_from: Optional[datetime] = Field(None, description="Date de debut")
    date_to: Optional[datetime] = Field(None, description="Date de fin")
    page: int = Field(1, ge=1, description="Page (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Taille de page")


class OdooHistorySearchResponse(BaseModel):
    """Reponse de la recherche dans l'historique."""
    items: List[OdooImportHistoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class OdooHistoryDetailResponse(OdooImportHistoryResponse):
    """Detail complet d'un historique d'import."""
    config_name: Optional[str] = None
    import_summary: Optional[Dict[str, Any]] = None
