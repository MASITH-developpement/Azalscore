"""
AZALS - MODULE IA TRANSVERSE - API Router
==========================================
Endpoints pour l'assistant IA central.

Principes de gouvernance:
- IA assistante, JAMAIS décisionnaire finale
- Double confirmation pour points rouges
- Traçabilité complète de toutes les actions
"""


from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db

from .schemas import (
    AIConfigResponse,
    # Config
    AIConfigUpdate,
    AIHealthCheck,
    AIQuestionRequest,
    AIQuestionResponse,
    # Dashboard
    AIStats,
    # Analysis
    AnalysisRequest,
    AnalysisResponse,
    # Conversation
    ConversationCreate,
    ConversationResponse,
    DecisionConfirmation,
    # Decision Support
    DecisionSupportCreate,
    DecisionSupportResponse,
    # Feedback
    FeedbackCreate,
    MessageCreate,
    MessageResponse,
    # Prediction
    PredictionRequest,
    PredictionResponse,
    RiskAcknowledge,
    # Risk
    RiskAlertCreate,
    RiskAlertResponse,
    RiskResolve,
    # Synthesis
    SynthesisRequest,
    SynthesisResponse,
)
from .service import AIAssistantService

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


# ============================================================================
# HELPER - Extraction contexte
# ============================================================================

def get_context(request: Request) -> dict:
    """Extrait le contexte de la requête."""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


# ============================================================================
# CONVERSATIONS
# ============================================================================

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    data: ConversationCreate,
    tenant_id: str = Query(..., description="Tenant ID"),
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Créer une nouvelle conversation avec l'IA."""
    service = AIAssistantService(db, tenant_id)
    return service.create_conversation(user_id, data)


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    tenant_id: str = Query(...),
    user_id: int = Query(...),
    is_active: bool | None = None,
    module_source: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Lister les conversations d'un utilisateur."""
    service = AIAssistantService(db, tenant_id)
    return service.list_conversations(
        user_id, is_active, module_source, skip, limit
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Récupérer une conversation."""
    service = AIAssistantService(db, tenant_id)
    conversation = service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    return conversation


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def get_conversation_messages(
    conversation_id: int,
    tenant_id: str = Query(...),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Récupérer les messages d'une conversation."""
    service = AIAssistantService(db, tenant_id)
    return service.get_conversation_messages(conversation_id, skip, limit)


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
def send_message(
    conversation_id: int,
    data: MessageCreate,
    tenant_id: str = Query(...),
    user_id: int = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Envoyer un message dans une conversation et obtenir une réponse."""
    service = AIAssistantService(db, tenant_id)
    context = get_context(request) if request else {}
    return service.send_message(conversation_id, user_id, data, context)


@router.delete("/conversations/{conversation_id}")
def close_conversation(
    conversation_id: int,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Fermer une conversation."""
    service = AIAssistantService(db, tenant_id)
    service.close_conversation(conversation_id)
    return {"message": "Conversation fermée"}


# ============================================================================
# QUESTIONS DIRECTES
# ============================================================================

@router.post("/ask", response_model=AIQuestionResponse)
def ask_question(
    data: AIQuestionRequest,
    tenant_id: str = Query(...),
    user_id: int = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Poser une question directe à l'IA (sans conversation persistante)."""
    service = AIAssistantService(db, tenant_id)
    context = get_context(request) if request else {}
    return service.ask_question(user_id, data, context)


# ============================================================================
# ANALYSES
# ============================================================================

@router.post("/analyses", response_model=AnalysisResponse)
def create_analysis(
    data: AnalysisRequest,
    tenant_id: str = Query(...),
    user_id: int = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Demander une analyse IA."""
    service = AIAssistantService(db, tenant_id)
    context = get_context(request) if request else {}
    return service.create_analysis(user_id, data, context)


@router.get("/analyses", response_model=list[AnalysisResponse])
def list_analyses(
    tenant_id: str = Query(...),
    user_id: int | None = None,
    analysis_type: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Lister les analyses."""
    service = AIAssistantService(db, tenant_id)
    return service.list_analyses(user_id, analysis_type, status, skip, limit)


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: int,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Récupérer une analyse."""
    service = AIAssistantService(db, tenant_id)
    analysis = service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return analysis


# ============================================================================
# SUPPORT DE DÉCISION
# ============================================================================

@router.post("/decisions", response_model=DecisionSupportResponse)
def create_decision_support(
    data: DecisionSupportCreate,
    tenant_id: str = Query(...),
    user_id: int = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Créer un support de décision."""
    service = AIAssistantService(db, tenant_id)
    context = get_context(request) if request else {}
    return service.create_decision_support(user_id, data, context)


@router.get("/decisions", response_model=list[DecisionSupportResponse])
def list_decisions(
    tenant_id: str = Query(...),
    status: str | None = None,
    is_red_point: bool | None = None,
    priority: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Lister les supports de décision."""
    service = AIAssistantService(db, tenant_id)
    return service.list_decisions(status, is_red_point, priority, skip, limit)


@router.get("/decisions/{decision_id}", response_model=DecisionSupportResponse)
def get_decision(
    decision_id: int,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Récupérer un support de décision."""
    service = AIAssistantService(db, tenant_id)
    decision = service.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Décision non trouvée")
    return decision


@router.post("/decisions/{decision_id}/confirm", response_model=DecisionSupportResponse)
def confirm_decision(
    decision_id: int,
    data: DecisionConfirmation,
    tenant_id: str = Query(...),
    user_id: int = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Confirmer une décision.

    GOUVERNANCE: Pour les points rouges (is_red_point=True),
    une double confirmation par deux personnes différentes est requise.
    """
    service = AIAssistantService(db, tenant_id)
    context = get_context(request) if request else {}
    try:
        return service.confirm_decision(decision_id, user_id, data, context)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/decisions/{decision_id}/reject", response_model=DecisionSupportResponse)
def reject_decision(
    decision_id: int,
    notes: str | None = None,
    tenant_id: str = Query(...),
    user_id: int = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Rejeter une décision."""
    service = AIAssistantService(db, tenant_id)
    context = get_context(request) if request else {}
    return service.reject_decision(decision_id, user_id, notes, context)


# ============================================================================
# ALERTES DE RISQUE
# ============================================================================

@router.post("/risks", response_model=RiskAlertResponse)
def create_risk_alert(
    data: RiskAlertCreate,
    tenant_id: str = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Créer une alerte de risque (généralement par le système)."""
    service = AIAssistantService(db, tenant_id)
    context = get_context(request) if request else {}
    return service.create_risk_alert(data, context)


@router.get("/risks", response_model=list[RiskAlertResponse])
def list_risk_alerts(
    tenant_id: str = Query(...),
    status: str | None = None,
    risk_level: str | None = None,
    category: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Lister les alertes de risque."""
    service = AIAssistantService(db, tenant_id)
    return service.list_risk_alerts(status, risk_level, category, skip, limit)


@router.get("/risks/{risk_id}", response_model=RiskAlertResponse)
def get_risk_alert(
    risk_id: int,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Récupérer une alerte de risque."""
    service = AIAssistantService(db, tenant_id)
    alert = service.get_risk_alert(risk_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    return alert


@router.post("/risks/{risk_id}/acknowledge", response_model=RiskAlertResponse)
def acknowledge_risk(
    risk_id: int,
    data: RiskAcknowledge,
    tenant_id: str = Query(...),
    user_id: int = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Accuser réception d'une alerte de risque."""
    service = AIAssistantService(db, tenant_id)
    context = get_context(request) if request else {}
    return service.acknowledge_risk(risk_id, user_id, data, context)


@router.post("/risks/{risk_id}/resolve", response_model=RiskAlertResponse)
def resolve_risk(
    risk_id: int,
    data: RiskResolve,
    tenant_id: str = Query(...),
    user_id: int = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Résoudre une alerte de risque."""
    service = AIAssistantService(db, tenant_id)
    context = get_context(request) if request else {}
    return service.resolve_risk(risk_id, user_id, data, context)


# ============================================================================
# PRÉDICTIONS
# ============================================================================

@router.post("/predictions", response_model=PredictionResponse)
def create_prediction(
    data: PredictionRequest,
    tenant_id: str = Query(...),
    user_id: int = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Demander une prédiction IA."""
    service = AIAssistantService(db, tenant_id)
    context = get_context(request) if request else {}
    return service.create_prediction(user_id, data, context)


@router.get("/predictions", response_model=list[PredictionResponse])
def list_predictions(
    tenant_id: str = Query(...),
    prediction_type: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Lister les prédictions."""
    service = AIAssistantService(db, tenant_id)
    return service.list_predictions(prediction_type, status, skip, limit)


@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
def get_prediction(
    prediction_id: int,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Récupérer une prédiction."""
    service = AIAssistantService(db, tenant_id)
    prediction = service.get_prediction(prediction_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prédiction non trouvée")
    return prediction


# ============================================================================
# FEEDBACK
# ============================================================================

@router.post("/feedback")
def submit_feedback(
    data: FeedbackCreate,
    tenant_id: str = Query(...),
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Soumettre un feedback sur une réponse IA."""
    service = AIAssistantService(db, tenant_id)
    service.submit_feedback(user_id, data)
    return {"message": "Feedback enregistré"}


# ============================================================================
# SYNTHÈSES
# ============================================================================

@router.post("/synthesis", response_model=SynthesisResponse)
def generate_synthesis(
    data: SynthesisRequest,
    tenant_id: str = Query(...),
    user_id: int = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Générer une synthèse IA."""
    service = AIAssistantService(db, tenant_id)
    context = get_context(request) if request else {}
    return service.generate_synthesis(user_id, data, context)


# ============================================================================
# CONFIGURATION
# ============================================================================

@router.get("/config", response_model=AIConfigResponse)
def get_ai_config(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Récupérer la configuration IA du tenant."""
    service = AIAssistantService(db, tenant_id)
    return service.get_config()


@router.put("/config", response_model=AIConfigResponse)
def update_ai_config(
    data: AIConfigUpdate,
    tenant_id: str = Query(...),
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Mettre à jour la configuration IA."""
    service = AIAssistantService(db, tenant_id)
    return service.update_config(user_id, data)


# ============================================================================
# TABLEAU DE BORD
# ============================================================================

@router.get("/stats", response_model=AIStats)
def get_ai_stats(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Récupérer les statistiques IA."""
    service = AIAssistantService(db, tenant_id)
    return service.get_stats()


@router.get("/health", response_model=AIHealthCheck)
def check_ai_health(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Vérifier l'état de santé du service IA."""
    service = AIAssistantService(db, tenant_id)
    return service.health_check()
