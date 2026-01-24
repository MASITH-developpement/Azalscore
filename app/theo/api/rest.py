"""
THÉO — REST API
================

REST endpoints pour l'intégration texte et le contrôle.
Utilisé en complément ou fallback du WebSocket.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
import logging

from app.theo.core.orchestrator import get_theo_orchestrator, OrchestratorResult
from app.theo.core.session_manager import get_session_manager, AuthorityLevel
from app.theo.companions import get_companion_registry, get_translator

logger = logging.getLogger(__name__)

theo_rest_router = APIRouter(prefix="/theo", tags=["Theo REST API"])


# ============================================================
# SCHEMAS
# ============================================================

class StartSessionRequest(BaseModel):
    """Requête de démarrage de session."""
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    companion_id: str = Field(default="theo")
    mode: str = Field(default="desktop")  # driving, desktop, mobile
    authority_level: Optional[str] = Field(default="user")


class StartSessionResponse(BaseModel):
    """Réponse de démarrage de session."""
    session_id: str
    companion_id: str
    mode: str
    state: str


class ProcessRequest(BaseModel):
    """Requête de traitement texte."""
    session_id: str
    text: str
    context: Optional[Dict[str, Any]] = None


class ProcessResponse(BaseModel):
    """Réponse de traitement."""
    type: str
    speech_text: str
    session_state: str
    intent: Optional[Dict[str, Any]] = None
    action_result: Optional[Dict[str, Any]] = None
    visual_state: str


class ConfirmRequest(BaseModel):
    """Requête de confirmation."""
    session_id: str
    confirmed: bool
    additional_info: Optional[str] = None


class CompanionInfo(BaseModel):
    """Information sur un compagnon."""
    id: str
    display_name: str
    gender: str
    description: str


# ============================================================
# SESSION ENDPOINTS
# ============================================================

@theo_rest_router.post("/session/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """
    Démarre une nouvelle session Théo.

    Args:
        request: Configuration de la session

    Returns:
        Informations de la session créée
    """
    session_manager = get_session_manager()

    # Mapper le niveau d'autorité
    authority_map = {
        "user": AuthorityLevel.USER,
        "design": AuthorityLevel.DESIGN,
        "admin": AuthorityLevel.ADMIN,
        "creator": AuthorityLevel.CREATOR,
    }
    authority = authority_map.get(request.authority_level, AuthorityLevel.USER)

    # Créer la session
    session = session_manager.create(
        user_id=request.user_id,
        tenant_id=request.tenant_id,
        companion_id=request.companion_id,
        authority_level=authority,
        mode=request.mode
    )

    return StartSessionResponse(
        session_id=session.session_id,
        companion_id=session.companion_id,
        mode=session.mode,
        state=session.state.value
    )


@theo_rest_router.post("/session/end")
async def end_session(session_id: str = Body(..., embed=True)):
    """
    Termine une session Théo.

    Args:
        session_id: ID de la session à terminer

    Returns:
        Confirmation
    """
    session_manager = get_session_manager()
    success = session_manager.end(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "ended", "session_id": session_id}


@theo_rest_router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Récupère les informations d'une session.

    Args:
        session_id: ID de la session

    Returns:
        Détails de la session
    """
    session_manager = get_session_manager()
    session = session_manager.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session.to_dict()


# ============================================================
# PROCESSING ENDPOINTS
# ============================================================

@theo_rest_router.post("/process", response_model=ProcessResponse)
async def process_text(request: ProcessRequest):
    """
    Traite une entrée texte.

    Args:
        request: Texte à traiter et contexte

    Returns:
        Réponse de Théo
    """
    session_manager = get_session_manager()
    orchestrator = get_theo_orchestrator()
    translator = get_translator()

    # Vérifier la session
    session = session_manager.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Traduire si compagnon
    translation = translator.translate(request.text)

    # Traiter
    result: OrchestratorResult = await orchestrator.process(
        request.session_id,
        translation.translated_text,
        context=request.context or {}
    )

    return ProcessResponse(
        type=result.type.value,
        speech_text=result.speech_text,
        session_state=result.session_state.value,
        intent=result.intent.to_dict() if result.intent else None,
        action_result=result.action_result,
        visual_state=result.visual_state
    )


@theo_rest_router.post("/confirm", response_model=ProcessResponse)
async def confirm_action(request: ConfirmRequest):
    """
    Confirme ou annule une action en attente.

    Args:
        request: Confirmation (oui/non) et info additionnelle

    Returns:
        Résultat de la confirmation
    """
    session_manager = get_session_manager()
    orchestrator = get_theo_orchestrator()

    # Vérifier la session
    session = session_manager.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Construire le texte de confirmation
    if request.confirmed:
        text = "oui" if not request.additional_info else f"oui, {request.additional_info}"
    else:
        text = "non" if not request.additional_info else f"non, {request.additional_info}"

    # Traiter comme une entrée normale
    result: OrchestratorResult = await orchestrator.process(
        request.session_id,
        text
    )

    return ProcessResponse(
        type=result.type.value,
        speech_text=result.speech_text,
        session_state=result.session_state.value,
        intent=result.intent.to_dict() if result.intent else None,
        action_result=result.action_result,
        visual_state=result.visual_state
    )


# ============================================================
# COMPANION ENDPOINTS
# ============================================================

@theo_rest_router.get("/companions", response_model=List[CompanionInfo])
async def list_companions():
    """
    Liste les compagnons disponibles.

    Returns:
        Liste des compagnons
    """
    registry = get_companion_registry()
    companions = registry.list_all()

    return [
        CompanionInfo(
            id=c.id,
            display_name=c.display_name,
            gender=c.gender.value,
            description=c.description
        )
        for c in companions
    ]


@theo_rest_router.get("/companions/{companion_id}", response_model=CompanionInfo)
async def get_companion(companion_id: str):
    """
    Récupère un compagnon par ID.

    Args:
        companion_id: ID du compagnon

    Returns:
        Détails du compagnon
    """
    registry = get_companion_registry()
    companion = registry.get(companion_id)

    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")

    return CompanionInfo(
        id=companion.id,
        display_name=companion.display_name,
        gender=companion.gender.value,
        description=companion.description
    )


@theo_rest_router.post("/session/{session_id}/companion")
async def change_companion(
    session_id: str,
    companion_id: str = Body(..., embed=True)
):
    """
    Change le compagnon actif d'une session.

    Args:
        session_id: ID de la session
        companion_id: ID du nouveau compagnon

    Returns:
        Confirmation
    """
    session_manager = get_session_manager()
    registry = get_companion_registry()

    # Vérifier la session
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Vérifier le compagnon
    companion = registry.get(companion_id)
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")

    # Changer
    session.companion_id = companion_id

    return {
        "status": "changed",
        "session_id": session_id,
        "companion_id": companion_id
    }


# ============================================================
# CONTEXT ENDPOINTS
# ============================================================

@theo_rest_router.post("/session/{session_id}/context")
async def update_context(
    session_id: str,
    current_page: Optional[str] = Body(None),
    erp_context: Optional[Dict[str, Any]] = Body(None)
):
    """
    Met à jour le contexte ERP de la session.

    Args:
        session_id: ID de la session
        current_page: Page actuelle dans l'ERP
        erp_context: Contexte ERP additionnel

    Returns:
        Confirmation
    """
    session_manager = get_session_manager()

    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_page is not None:
        session.current_page = current_page

    if erp_context is not None:
        session.erp_context.update(erp_context)

    return {
        "status": "updated",
        "current_page": session.current_page,
        "erp_context": session.erp_context
    }


# ============================================================
# CAPABILITIES ENDPOINTS
# ============================================================

@theo_rest_router.get("/capabilities")
async def list_capabilities():
    """
    Liste les capacités disponibles.

    Returns:
        Capacités et leurs providers
    """
    from app.theo.core.capability_registry import get_capability_registry
    registry = get_capability_registry()
    return registry.status()


@theo_rest_router.get("/actions")
async def list_actions():
    """
    Liste les actions disponibles via les adapters.

    Returns:
        Actions par adapter
    """
    from app.theo.delegator import get_delegator
    delegator = get_delegator()
    return delegator.get_available_actions()
