"""
AZALS MODULE M2A - API Router Comptabilité Automatisée
=======================================================

Endpoints REST pour le module de comptabilité automatisée.
Endpoints organisés par vue utilisateur avec permissions RBAC.

Vues disponibles:
- /dirigeant: Dashboard simplifié, trésorerie, prévisions
- /assistante: Gestion documentaire uniquement
- /expert: Validation, contrôle, certification
- /common: Endpoints communs (documents, alertes)
"""

import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_tenant_id
from app.core.database import get_db

from .models import (
    ConfidenceLevel,
    DocumentSource,
    DocumentStatus,
    DocumentType,
    ReconciliationStatusAuto,
)
from .schemas import (
    AlertListResponse,
    AlertResolve,
    # Alert schemas
    AlertResponse,
    AssistanteDashboard,
    AutoEntryResponse,
    AutoEntryValidate,
    # Bank schemas
    BankConnectionCreate,
    BankConnectionListResponse,
    BankConnectionResponse,
    BankSyncSessionResponse,
    BankSyncTrigger,
    # Validation schemas
    BulkValidationRequest,
    BulkValidationResponse,
    # Dashboard schemas
    DirigeantDashboard,
    # Document schemas
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentReject,
    DocumentResponse,
    DocumentUpdate,
    DocumentValidate,
    ExpertComptableDashboard,
    ManualReconciliation,
    ReconciliationHistoryResponse,
    # Reconciliation schemas
    ReconciliationRuleCreate,
    ReconciliationRuleResponse,
    SyncedAccountResponse,
    SyncedTransactionListResponse,
    SyncedTransactionResponse,
)
from .services import (
    AIClassificationService,
    AutoAccountingService,
    BankPullService,
    DashboardService,
    DocumentService,
    ReconciliationService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounting", tags=["Comptabilité Automatisée"])


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_document_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> DocumentService:
    return DocumentService(db, tenant_id)


def get_dashboard_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> DashboardService:
    return DashboardService(db, tenant_id)


def get_bank_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> BankPullService:
    return BankPullService(db, tenant_id)


def get_reconciliation_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> ReconciliationService:
    return ReconciliationService(db, tenant_id)


def get_auto_accounting_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> AutoAccountingService:
    return AutoAccountingService(db, tenant_id)


# ============================================================================
# VUE DIRIGEANT - Dashboard simplifié, décision rapide
# ============================================================================

@router.get(
    "/dirigeant/dashboard",
    response_model=DirigeantDashboard,
    summary="Dashboard Dirigeant",
    description="""
    Dashboard simplifié pour le dirigeant.

    **ZÉRO jargon comptable** - Tout est présenté de manière compréhensible.

    Inclut:
    - Trésorerie actuelle (synchronisée en mode PULL)
    - Prévision de cash
    - Factures à payer / encaisser
    - Résultat estimé
    - Alertes critiques uniquement

    La synchronisation bancaire est déclenchée automatiquement à l'ouverture.
    """
)
async def get_dirigeant_dashboard(
    sync_bank: bool = Query(True, description="Synchroniser la banque avant"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """Récupère le dashboard dirigeant."""
    return service.get_dirigeant_dashboard(sync_bank=sync_bank)


# ============================================================================
# VUE ASSISTANTE - Gestion documentaire uniquement
# ============================================================================

@router.get(
    "/assistante/dashboard",
    response_model=AssistanteDashboard,
    summary="Dashboard Assistante",
    description="""
    Dashboard documentaire pour l'assistante.

    **AUCUN accès bancaire** - Uniquement les documents.

    Inclut:
    - Vue des documents reçus
    - Statuts des pièces
    - Alertes documentaires (pièce illisible, info manquante)

    L'assistante peut ajouter du contexte mais JAMAIS comptabiliser.
    """
)
async def get_assistante_dashboard(
    service: DashboardService = Depends(get_dashboard_service)
):
    """Récupère le dashboard assistante."""
    return service.get_assistante_dashboard()


@router.get(
    "/assistante/documents",
    response_model=DocumentListResponse,
    summary="Liste des documents (vue assistante)"
)
async def list_documents_assistante(
    document_type: DocumentType | None = None,
    status: DocumentStatus | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: DocumentService = Depends(get_document_service)
):
    """Liste les documents pour l'assistante."""
    documents, total = service.list_documents(
        document_type=document_type,
        status=status,
        search=search,
        page=page,
        page_size=page_size
    )

    return DocumentListResponse(
        items=[DocumentResponse.from_orm(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post(
    "/assistante/documents/upload",
    response_model=DocumentResponse,
    status_code=201,
    summary="Upload d'un document"
)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Query(DocumentType.INVOICE_RECEIVED),
    current_user=Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Upload un document pour traitement automatique.

    Le traitement OCR -> IA -> Comptabilisation est lancé automatiquement.
    L'utilisateur n'a rien d'autre à faire.
    """
    # Sauvegarde temporaire du fichier
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        document = service.create_document(
            document_type=document_type,
            source=DocumentSource.UPLOAD,
            file_path=tmp_path,
            original_filename=file.filename,
            created_by=current_user.id if current_user else None
        )
        return DocumentResponse.from_orm(document)
    finally:
        # Nettoie le fichier temporaire
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.patch(
    "/assistante/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Ajouter du contexte à un document"
)
async def update_document_context(
    document_id: UUID,
    update_data: DocumentUpdate,
    service: DocumentService = Depends(get_document_service)
):
    """
    Permet à l'assistante d'ajouter du contexte (notes, tags).

    **AUCUNE modification comptable possible** - Uniquement métadonnées.
    """
    document = service.update_document(document_id, update_data)
    return DocumentResponse.from_orm(document)


# ============================================================================
# VUE EXPERT-COMPTABLE - Validation des exceptions
# ============================================================================

@router.get(
    "/expert/dashboard",
    response_model=ExpertComptableDashboard,
    summary="Dashboard Expert-comptable",
    description="""
    Dashboard de validation pour l'expert-comptable.

    **UNIQUEMENT les exceptions** - Pas de ressaisie.

    Inclut:
    - File de validation (documents à confiance faible)
    - Taux de confiance IA
    - Statistiques de performance
    - Statut des rapprochements
    - Alertes comptables
    """
)
async def get_expert_dashboard(
    service: DashboardService = Depends(get_dashboard_service)
):
    """Récupère le dashboard expert-comptable."""
    return service.get_expert_comptable_dashboard()


@router.get(
    "/expert/validation-queue",
    summary="File de validation"
)
async def get_validation_queue(
    confidence: ConfidenceLevel | None = None,
    limit: int = Query(50, ge=1, le=100),
    service: DocumentService = Depends(get_document_service)
):
    """Récupère les documents en attente de validation."""
    documents = service.get_documents_for_validation(
        confidence_filter=confidence,
        limit=limit
    )
    return [DocumentResponse.from_orm(d) for d in documents]


@router.post(
    "/expert/documents/{document_id}/validate",
    response_model=DocumentResponse,
    summary="Valider un document"
)
async def validate_document(
    document_id: UUID,
    validation_data: DocumentValidate,
    current_user=Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Valide un document et son écriture comptable.

    Si des corrections sont fournies, elles sont enregistrées pour l'apprentissage IA.
    """
    document = service.validate_document(
        document_id=document_id,
        validated_by=current_user.id,
        validation_data=validation_data
    )
    return DocumentResponse.from_orm(document)


@router.post(
    "/expert/documents/{document_id}/reject",
    response_model=DocumentResponse,
    summary="Rejeter un document"
)
async def reject_document(
    document_id: UUID,
    rejection_data: DocumentReject,
    current_user=Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """Rejette un document."""
    document = service.reject_document(
        document_id=document_id,
        rejected_by=current_user.id,
        rejection_data=rejection_data
    )
    return DocumentResponse.from_orm(document)


@router.post(
    "/expert/bulk-validate",
    response_model=BulkValidationResponse,
    summary="Validation en masse"
)
async def bulk_validate(
    request: BulkValidationRequest,
    current_user=Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Valide plusieurs documents en une seule opération.

    Idéal pour les documents à haute confiance IA.
    """
    results = service.bulk_validate(
        document_ids=request.document_ids,
        validated_by=current_user.id
    )
    return BulkValidationResponse(**results)


@router.get(
    "/expert/auto-entries/{document_id}",
    response_model=AutoEntryResponse,
    summary="Détail écriture automatique"
)
async def get_auto_entry(
    document_id: UUID,
    service: AutoAccountingService = Depends(get_auto_accounting_service)
):
    """Récupère l'écriture automatique générée pour un document."""
    entries, _ = service.get_pending_entries()
    for entry in entries:
        if entry.document_id == document_id:
            return AutoEntryResponse.from_orm(entry)
    raise HTTPException(status_code=404, detail="Auto entry not found")


@router.post(
    "/expert/auto-entries/{entry_id}/validate",
    response_model=AutoEntryResponse,
    summary="Valider une écriture automatique"
)
async def validate_auto_entry(
    entry_id: UUID,
    validation: AutoEntryValidate,
    current_user=Depends(get_current_user),
    service: AutoAccountingService = Depends(get_auto_accounting_service)
):
    """Valide ou rejette une écriture automatique."""
    entry = service.validate_entry(
        auto_entry_id=entry_id,
        validated_by=current_user.id,
        approved=validation.approved,
        modified_lines=validation.modified_lines,
        modification_reason=validation.modification_reason
    )
    return AutoEntryResponse.from_orm(entry)


# ============================================================================
# BANQUE - Mode PULL uniquement
# ============================================================================

@router.get(
    "/bank/connections",
    response_model=BankConnectionListResponse,
    summary="Liste des connexions bancaires"
)
async def list_bank_connections(
    service: BankPullService = Depends(get_bank_service)
):
    """Liste les connexions bancaires actives."""
    connections = service.get_connections()
    return BankConnectionListResponse(
        items=[BankConnectionResponse.from_orm(c) for c in connections],
        total=len(connections)
    )


@router.post(
    "/bank/connections",
    response_model=BankConnectionResponse,
    status_code=201,
    summary="Créer une connexion bancaire"
)
async def create_bank_connection(
    connection_data: BankConnectionCreate,
    current_user=Depends(get_current_user),
    service: BankPullService = Depends(get_bank_service)
):
    """
    Crée une nouvelle connexion bancaire (Open Banking).

    La connexion est en mode PULL - les données sont récupérées à la demande.
    """
    connection = service.create_connection(
        provider=connection_data.provider,
        institution_id=connection_data.institution_id,
        institution_name=connection_data.institution_name,
        institution_logo_url=connection_data.institution_logo_url,
        created_by=current_user.id
    )
    return BankConnectionResponse.from_orm(connection)


@router.delete(
    "/bank/connections/{connection_id}",
    status_code=204,
    summary="Supprimer une connexion bancaire"
)
async def delete_bank_connection(
    connection_id: UUID,
    service: BankPullService = Depends(get_bank_service)
):
    """Supprime une connexion bancaire."""
    service.delete_connection(connection_id)
    return JSONResponse(status_code=204, content=None)


@router.post(
    "/bank/sync",
    response_model=list[BankSyncSessionResponse],
    summary="Synchroniser la banque (PULL)"
)
async def sync_bank(
    trigger: BankSyncTrigger = Body(default=BankSyncTrigger()),
    current_user=Depends(get_current_user),
    service: BankPullService = Depends(get_bank_service)
):
    """
    Déclenche une synchronisation bancaire.

    **Mode PULL** - La banque est interrogée à la demande.
    Jamais de webhooks ou push depuis la banque.
    """
    if trigger.connection_id:
        sessions = [service.sync_connection(
            connection_id=trigger.connection_id,
            triggered_by=current_user.id,
            sync_type=trigger.sync_type,
            start_date=trigger.sync_from_date,
            end_date=trigger.sync_to_date
        )]
    else:
        sessions = service.sync_all(
            triggered_by=current_user.id,
            sync_type=trigger.sync_type
        )

    return [BankSyncSessionResponse.from_orm(s) for s in sessions]


@router.get(
    "/bank/accounts",
    response_model=list[SyncedAccountResponse],
    summary="Comptes bancaires synchronisés"
)
async def list_synced_accounts(
    connection_id: UUID | None = None,
    service: BankPullService = Depends(get_bank_service)
):
    """Liste les comptes bancaires synchronisés."""
    accounts = service.get_synced_accounts(connection_id=connection_id)
    return [SyncedAccountResponse.from_orm(a) for a in accounts]


@router.get(
    "/bank/transactions",
    response_model=SyncedTransactionListResponse,
    summary="Transactions bancaires"
)
async def list_transactions(
    account_id: UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    status: ReconciliationStatusAuto | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: BankPullService = Depends(get_bank_service)
):
    """Liste les transactions bancaires synchronisées."""
    offset = (page - 1) * page_size
    transactions, total = service.get_transactions(
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        reconciliation_status=status,
        limit=page_size,
        offset=offset
    )

    # Calcul des totaux
    total_credits = sum(t.amount for t in transactions if t.amount > 0)
    total_debits = sum(abs(t.amount) for t in transactions if t.amount < 0)

    return SyncedTransactionListResponse(
        items=[SyncedTransactionResponse.from_orm(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
        total_credits=total_credits,
        total_debits=total_debits
    )


# ============================================================================
# RAPPROCHEMENT
# ============================================================================

@router.post(
    "/reconciliation/auto",
    summary="Lancer le rapprochement automatique"
)
async def auto_reconcile(
    service: ReconciliationService = Depends(get_reconciliation_service)
):
    """
    Lance le rapprochement automatique sur toutes les transactions en attente.

    Utilise l'IA pour matcher:
    - Transaction bancaire <-> Facture
    - Transaction bancaire <-> Note de frais
    """
    results = service.auto_reconcile_all()
    return results


@router.post(
    "/reconciliation/manual",
    response_model=ReconciliationHistoryResponse,
    summary="Rapprochement manuel"
)
async def manual_reconcile(
    reconciliation: ManualReconciliation,
    current_user=Depends(get_current_user),
    service: ReconciliationService = Depends(get_reconciliation_service)
):
    """Effectue un rapprochement manuel."""
    history = service.manual_reconcile(
        transaction_id=reconciliation.transaction_id,
        document_id=reconciliation.document_id,
        entry_line_id=reconciliation.entry_line_id,
        validated_by=current_user.id
    )
    return ReconciliationHistoryResponse.from_orm(history)


@router.get(
    "/reconciliation/rules",
    response_model=list[ReconciliationRuleResponse],
    summary="Règles de rapprochement"
)
async def list_reconciliation_rules(
    active_only: bool = True,
    service: ReconciliationService = Depends(get_reconciliation_service)
):
    """Liste les règles de rapprochement automatique."""
    rules = service.get_rules(active_only=active_only)
    return [ReconciliationRuleResponse.from_orm(r) for r in rules]


@router.post(
    "/reconciliation/rules",
    response_model=ReconciliationRuleResponse,
    status_code=201,
    summary="Créer une règle de rapprochement"
)
async def create_reconciliation_rule(
    rule_data: ReconciliationRuleCreate,
    current_user=Depends(get_current_user),
    service: ReconciliationService = Depends(get_reconciliation_service)
):
    """Crée une nouvelle règle de rapprochement."""
    rule = service.create_rule(
        name=rule_data.name,
        description=rule_data.description,
        match_criteria=rule_data.match_criteria,
        auto_reconcile=rule_data.auto_reconcile,
        min_confidence=rule_data.min_confidence,
        default_account_code=rule_data.default_account_code,
        default_tax_code=rule_data.default_tax_code,
        priority=rule_data.priority,
        created_by=current_user.id
    )
    return ReconciliationRuleResponse.from_orm(rule)


@router.get(
    "/reconciliation/stats",
    summary="Statistiques de rapprochement"
)
async def get_reconciliation_stats(
    service: ReconciliationService = Depends(get_reconciliation_service)
):
    """Récupère les statistiques de rapprochement."""
    return service.get_reconciliation_stats()


# ============================================================================
# DOCUMENTS (Endpoints communs)
# ============================================================================

@router.get(
    "/documents/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Détail d'un document"
)
async def get_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service)
):
    """Récupère le détail complet d'un document."""
    document = service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentDetailResponse.from_orm(document)


@router.delete(
    "/documents/{document_id}",
    status_code=204,
    summary="Supprimer un document"
)
async def delete_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service)
):
    """
    Supprime un document (si non comptabilisé).

    Les documents comptabilisés ne peuvent pas être supprimés.
    """
    if not service.delete_document(document_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return JSONResponse(status_code=204, content=None)


@router.get(
    "/documents/stats",
    summary="Statistiques des documents"
)
async def get_document_stats(
    service: DocumentService = Depends(get_document_service)
):
    """Récupère les statistiques des documents."""
    return service.get_document_stats()


# ============================================================================
# ALERTES
# ============================================================================

@router.get(
    "/alerts",
    response_model=AlertListResponse,
    summary="Liste des alertes"
)
async def list_alerts(
    resolved: bool | None = Query(False),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """Liste les alertes comptables."""
    from .models import AccountingAlert

    query = db.query(AccountingAlert).filter(
        AccountingAlert.tenant_id == tenant_id
    )

    if resolved is not None:
        query = query.filter(AccountingAlert.is_resolved == resolved)

    alerts = query.order_by(
        AccountingAlert.severity.desc(),
        AccountingAlert.created_at.desc()
    ).limit(limit).all()

    unread = sum(1 for a in alerts if not a.is_read)
    critical = sum(1 for a in alerts if a.severity.value == "CRITICAL")

    return AlertListResponse(
        items=[AlertResponse.from_orm(a) for a in alerts],
        total=len(alerts),
        unread_count=unread,
        critical_count=critical
    )


@router.post(
    "/alerts/{alert_id}/resolve",
    response_model=AlertResponse,
    summary="Résoudre une alerte"
)
async def resolve_alert(
    alert_id: UUID,
    resolution: AlertResolve,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """Marque une alerte comme résolue."""
    from datetime import datetime

    from .models import AccountingAlert

    alert = db.query(AccountingAlert).filter(
        AccountingAlert.id == alert_id,
        AccountingAlert.tenant_id == tenant_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_resolved = True
    alert.resolved_by = current_user.id
    alert.resolved_at = datetime.utcnow()
    alert.resolution_notes = resolution.resolution_notes

    db.commit()
    db.refresh(alert)

    return AlertResponse.from_orm(alert)


@router.post(
    "/alerts/{alert_id}/read",
    response_model=AlertResponse,
    summary="Marquer une alerte comme lue"
)
async def mark_alert_read(
    alert_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """Marque une alerte comme lue."""
    from datetime import datetime

    from .models import AccountingAlert

    alert = db.query(AccountingAlert).filter(
        AccountingAlert.id == alert_id,
        AccountingAlert.tenant_id == tenant_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    alert.read_by = current_user.id
    alert.read_at = datetime.utcnow()

    db.commit()
    db.refresh(alert)

    return AlertResponse.from_orm(alert)


# ============================================================================
# PERFORMANCE IA
# ============================================================================

@router.get(
    "/ai/performance",
    summary="Performance de l'IA"
)
async def get_ai_performance(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """Récupère les statistiques de performance de l'IA."""
    service = AIClassificationService(db, tenant_id)
    return service.get_ai_performance_stats()


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/health",
    summary="Health check du module"
)
async def health_check():
    """Vérifie l'état du module de comptabilité automatisée."""
    return {
        "status": "ok",
        "module": "automated_accounting",
        "version": "1.0.0",
        "features": {
            "ocr": True,
            "ai_classification": True,
            "auto_accounting": True,
            "bank_pull": True,
            "reconciliation": True
        }
    }
