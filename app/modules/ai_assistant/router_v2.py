"""
AZALS - MODULE IA TRANSVERSE - Router v2 - CORE SaaS
====================================================
API pour l'assistant IA avec SaaSContext.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.core.database import get_db

from .service import AIAssistantService
from .schemas import (
    AIConfigUpdate,
    AnalysisRequest,
    ConversationCreate,
    DecisionConfirmation,
    DecisionSupportCreate,
    FeedbackCreate,
    MessageCreate,
    PredictionRequest,
    RiskAcknowledge,
    RiskAlertCreate,
    RiskResolve,
    SynthesisRequest,
)

router = APIRouter(prefix="/v2/ai", tags=["AI Assistant v2 - CORE SaaS"])


def get_ai_service(db: Session, tenant_id: str, user_id: str) -> AIAssistantService:
    """Factory pour créer le service AI avec contexte SaaS."""
    return AIAssistantService(db, tenant_id, user_id)


# ============================================================================
# CONFIGURATION
# ============================================================================

@router.get("/config")
async def get_config(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer la configuration AI."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    return service.get_config()


@router.put("/config")
async def update_config(
    data: AIConfigUpdate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Mettre à jour la configuration AI."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return service.update_config(user_id, data)


# ============================================================================
# CONVERSATIONS
# ============================================================================

@router.post("/conversations", status_code=201)
async def create_conversation(
    data: ConversationCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Créer une nouvelle conversation AI."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return service.create_conversation(user_id, data)


@router.get("/conversations")
async def list_conversations(
    active_only: bool = Query(True, description="Conversations actives uniquement"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Lister les conversations de l'utilisateur."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return service.list_conversations(user_id, active_only, skip, limit)


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer une conversation."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    conversation = service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("/conversations/{conversation_id}/messages", status_code=201)
async def add_message(
    conversation_id: int,
    data: MessageCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Ajouter un message et obtenir la réponse AI."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    try:
        user_message, assistant_message = service.add_message(conversation_id, user_id, data)
        return {
            "user_message": user_message,
            "assistant_message": assistant_message
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# ANALYSES
# ============================================================================

@router.post("/analyses", status_code=201)
async def create_analysis(
    data: AnalysisRequest,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Créer une analyse AI."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return service.create_analysis(user_id, data)


@router.get("/analyses")
async def list_analyses(
    analysis_type: str | None = Query(None, description="Type d'analyse"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Lister les analyses."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    return service.list_analyses(user_id, analysis_type, skip, limit)


@router.get("/analyses/{analysis_id}")
async def get_analysis(
    analysis_id: int,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer une analyse."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    analysis = service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


# ============================================================================
# DECISION SUPPORT (AIDE À LA DÉCISION)
# ============================================================================

@router.post("/decisions", status_code=201)
async def create_decision_support(
    data: DecisionSupportCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Créer un support de décision AI."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return service.create_decision_support(user_id, data)


@router.get("/decisions")
async def list_pending_decisions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Lister les décisions en attente."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    return service.list_pending_decisions(skip, limit)


@router.get("/decisions/{decision_id}")
async def get_decision(
    decision_id: int,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer un support de décision."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    decision = service.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@router.post("/decisions/{decision_id}/confirm")
async def confirm_decision(
    decision_id: int,
    data: DecisionConfirmation,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Confirmer une décision (simple ou double confirmation)."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    try:
        return service.confirm_decision(decision_id, user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/decisions/{decision_id}/reject")
async def reject_decision(
    decision_id: int,
    reason: str = Query(..., description="Raison du rejet"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Rejeter une décision."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    try:
        return service.reject_decision(decision_id, user_id, reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# RISK DETECTION (DÉTECTION DE RISQUES)
# ============================================================================

@router.post("/risks", status_code=201)
async def create_risk_alert(
    data: RiskAlertCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Créer une alerte de risque."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    return service.create_risk_alert(data)


@router.get("/risks")
async def list_active_risks(
    category: str | None = Query(None, description="Catégorie de risque"),
    level: str | None = Query(None, description="Niveau de risque"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Lister les risques actifs."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    return service.list_active_risks(category, level, skip, limit)


@router.get("/risks/{alert_id}")
async def get_risk_alert(
    alert_id: int,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer une alerte de risque."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    alert = service.get_risk_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Risk alert not found")
    return alert


@router.post("/risks/{alert_id}/acknowledge")
async def acknowledge_risk(
    alert_id: int,
    data: RiskAcknowledge,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Accuser réception d'un risque."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    try:
        return service.acknowledge_risk(alert_id, user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/risks/{alert_id}/resolve")
async def resolve_risk(
    alert_id: int,
    data: RiskResolve,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Résoudre un risque."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    try:
        return service.resolve_risk(alert_id, user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# PREDICTIONS
# ============================================================================

@router.post("/predictions", status_code=201)
async def create_prediction(
    data: PredictionRequest,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Créer une prédiction AI."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return service.create_prediction(user_id, data)


@router.get("/predictions")
async def list_predictions(
    prediction_type: str | None = Query(None, description="Type de prédiction"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Lister les prédictions."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    return service.list_predictions(prediction_type, skip, limit)


@router.get("/predictions/{prediction_id}")
async def get_prediction(
    prediction_id: int,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer une prédiction."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    prediction = service.get_prediction(prediction_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


# ============================================================================
# FEEDBACK & LEARNING
# ============================================================================

@router.post("/feedback", status_code=201)
async def add_feedback(
    data: FeedbackCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Ajouter un feedback sur une réponse AI."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return service.add_feedback(user_id, data)


# ============================================================================
# SYNTHESIS (SYNTHÈSES)
# ============================================================================

@router.post("/synthesis")
async def generate_synthesis(
    data: SynthesisRequest,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Générer une synthèse AI."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return service.generate_synthesis(user_id, data)


# ============================================================================
# STATISTICS & HEALTH
# ============================================================================

@router.get("/stats")
async def get_stats(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Statistiques globales AI."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    return service.get_stats()


@router.get("/health")
async def health_check(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Vérification de santé du système AI."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    return service.health_check()


# ============================================================================
# AUDIT LOGS
# ============================================================================

@router.get("/audit")
async def get_audit_logs(
    action: str | None = Query(None, description="Type d'action"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer les logs d'audit AI."""
    service = get_ai_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    return service.get_audit_logs(action, user_id, skip, limit)
