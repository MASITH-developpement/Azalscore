"""
AZALSCORE AI API Routes

API REST pour l'interface avec le système IA.
Seul Theo est exposé à l'interface graphique.

Conformité: AZA-API, AZA-FE-003
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
import logging

from app.ai.theo import get_theo, TheoResponse, ConversationState
from app.ai.orchestrator import get_ai_orchestrator, AICallRequest, AIModule
from app.ai.guardian import get_guardian
from app.ai.auth import get_auth_manager, PrivilegeLevel
from app.ai.audit import get_audit_logger
from app.ai.roles import AIRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Orchestration"])


# ==================== MODÈLES ====================

class StartSessionRequest(BaseModel):
    """Requête de démarrage de session"""
    user_id: Optional[str] = None


class StartSessionResponse(BaseModel):
    """Réponse de démarrage de session"""
    session_id: str
    message: str


class ChatRequest(BaseModel):
    """Requête de chat avec Theo"""
    session_id: str
    message: str
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Réponse de chat"""
    session_id: str
    message: str
    state: str
    requires_validation: bool = False
    confidence: Optional[float] = None
    actions_taken: list = Field(default_factory=list)


class ConfirmIntentionRequest(BaseModel):
    """Requête de confirmation d'intention"""
    session_id: str
    confirmed: bool
    additional_info: Optional[str] = None


class LoginRequest(BaseModel):
    """Requête de connexion"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Réponse de connexion"""
    session_id: str
    mfa_required: bool
    message: str


class MFARequest(BaseModel):
    """Requête de vérification MFA"""
    session_id: str
    code: str


class MFAResponse(BaseModel):
    """Réponse MFA"""
    success: bool
    message: str
    privilege_level: Optional[str] = None


class AlertResponse(BaseModel):
    """Alerte Guardian"""
    id: str
    type: str
    message: str
    severity: str
    timestamp: str
    acknowledged: bool


# ==================== DÉPENDANCES ====================

def get_optional_auth_session(authorization: Optional[str] = Header(None)):
    """Récupère la session d'auth optionnelle"""
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    session_id = authorization[7:]
    auth_manager = get_auth_manager()
    return auth_manager.get_session(session_id)


def require_auth_session(authorization: str = Header(...)):
    """Requiert une session authentifiée"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    session_id = authorization[7:]
    auth_manager = get_auth_manager()
    session = auth_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return session


def require_admin_session(authorization: str = Header(...)):
    """Requiert une session admin"""
    session = require_auth_session(authorization)

    if session.privilege_level not in [PrivilegeLevel.ADMIN, PrivilegeLevel.OWNER]:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    if not session.is_mfa_complete():
        raise HTTPException(status_code=403, detail="MFA verification required")

    return session


# ==================== ROUTES THEO (Interface publique) ====================

@router.post("/theo/start", response_model=StartSessionResponse)
async def start_theo_session(request: StartSessionRequest):
    """
    Démarre une nouvelle session de dialogue avec Theo

    Theo est l'unique interface IA exposée aux utilisateurs.
    """
    theo = get_theo()
    session_id = theo.start_session(user_id=request.user_id)

    return StartSessionResponse(
        session_id=session_id,
        message="Session démarrée. Comment puis-je vous aider ?"
    )


@router.post("/theo/chat", response_model=ChatResponse)
async def chat_with_theo(request: ChatRequest):
    """
    Envoie un message à Theo et reçoit sa réponse

    Theo analyse l'intention, clarifie si nécessaire,
    puis orchestre les modules IA internes.
    """
    theo = get_theo()

    response = theo.process_input(
        session_id=request.session_id,
        user_input=request.message,
        user_id=request.user_id
    )

    return ChatResponse(
        session_id=response.session_id,
        message=response.message,
        state=response.state.value,
        requires_validation=response.requires_validation,
        confidence=response.metadata.get("confidence") if response.metadata else None,
        actions_taken=response.actions_taken
    )


@router.post("/theo/confirm", response_model=ChatResponse)
async def confirm_theo_intention(request: ConfirmIntentionRequest):
    """
    Confirme ou infirme la compréhension de Theo

    Après clarification, l'utilisateur confirme que Theo
    a bien compris son intention.
    """
    theo = get_theo()

    response = theo.confirm_intention(
        session_id=request.session_id,
        confirmed=request.confirmed,
        additional_info=request.additional_info
    )

    return ChatResponse(
        session_id=response.session_id,
        message=response.message,
        state=response.state.value,
        requires_validation=response.requires_validation,
        actions_taken=response.actions_taken
    )


@router.get("/theo/history/{session_id}")
async def get_theo_history(session_id: str):
    """
    Récupère l'historique d'une session Theo

    Permet de revoir les échanges précédents.
    """
    theo = get_theo()
    history = theo.get_session_history(session_id)

    return {"session_id": session_id, "history": history}


@router.post("/theo/end/{session_id}")
async def end_theo_session(session_id: str):
    """
    Termine une session Theo

    Clôture proprement la session de dialogue.
    """
    theo = get_theo()
    success = theo.end_session(session_id)

    if success:
        return {"message": "Session terminée avec succès"}
    else:
        raise HTTPException(status_code=404, detail="Session non trouvée")


# ==================== ROUTES AUTH ====================

@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authentification par mot de passe (premier facteur)

    Pour les utilisateurs privilégiés, le MFA est requis.
    """
    auth_manager = get_auth_manager()

    session = auth_manager.authenticate_password(
        username=request.username,
        password=request.password
    )

    if not session:
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    mfa_required = session.metadata.get("mfa_pending", False)

    return LoginResponse(
        session_id=session.session_id,
        mfa_required=mfa_required,
        message="Authentification réussie. " + (
            "Veuillez entrer le code MFA envoyé par email." if mfa_required
            else "Connecté."
        )
    )


@router.post("/auth/mfa", response_model=MFAResponse)
async def verify_mfa(request: MFARequest):
    """
    Vérifie le code MFA (deuxième facteur)

    Complète l'authentification multi-facteurs.
    """
    auth_manager = get_auth_manager()

    session = auth_manager.verify_mfa_code(
        session_id=request.session_id,
        code=request.code
    )

    if not session:
        raise HTTPException(status_code=401, detail="Code MFA invalide ou expiré")

    return MFAResponse(
        success=True,
        message="Authentification MFA réussie",
        privilege_level=session.privilege_level.value
    )


@router.post("/auth/logout")
async def logout(authorization: str = Header(...)):
    """
    Déconnexion

    Invalide la session courante.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid authorization")

    session_id = authorization[7:]
    auth_manager = get_auth_manager()

    if auth_manager.logout(session_id):
        return {"message": "Déconnexion réussie"}
    else:
        raise HTTPException(status_code=404, detail="Session non trouvée")


# ==================== ROUTES ADMIN (Protégées) ====================

@router.get("/admin/alerts", response_model=list[AlertResponse])
async def get_pending_alerts(session=Depends(require_admin_session)):
    """
    Liste les alertes Guardian en attente

    Requiert des privilèges administrateur avec MFA.
    """
    guardian = get_guardian()
    alerts = guardian.get_pending_alerts()

    return [
        AlertResponse(
            id=a["id"],
            type=a["type"],
            message=a["message"],
            severity=a["severity"],
            timestamp=a["timestamp"],
            acknowledged=a["acknowledged"]
        )
        for a in alerts
    ]


@router.post("/admin/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, session=Depends(require_admin_session)):
    """
    Acquitte une alerte Guardian

    Requiert des privilèges administrateur avec MFA.
    """
    guardian = get_guardian()

    if guardian.acknowledge_alert(alert_id, session.user_id):
        return {"message": "Alerte acquittée"}
    else:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")


@router.get("/admin/audit/report")
async def get_audit_report(
    session=Depends(require_admin_session),
    hours: int = 24
):
    """
    Génère un rapport d'audit

    Requiert des privilèges administrateur avec MFA.
    """
    from datetime import datetime, timedelta

    audit = get_audit_logger()

    report = audit.export_audit_report(
        start_date=datetime.utcnow() - timedelta(hours=hours),
        end_date=datetime.utcnow()
    )

    return report


@router.get("/admin/sessions")
async def get_active_sessions(session=Depends(require_admin_session)):
    """
    Liste les sessions actives

    Requiert des privilèges administrateur avec MFA.
    """
    auth_manager = get_auth_manager()

    sessions = []
    for s in auth_manager._sessions.values():
        if s.is_valid():
            sessions.append({
                "session_id": s.session_id,
                "user_id": s.user_id,
                "privilege_level": s.privilege_level.value,
                "created_at": s.created_at.isoformat(),
                "expires_at": s.expires_at.isoformat(),
                "mfa_complete": s.is_mfa_complete()
            })

    return {"active_sessions": sessions}


# ==================== ROUTES STATUS ====================

@router.get("/status")
async def get_ai_status():
    """
    Statut du système IA

    Accessible publiquement pour le monitoring.
    """
    orchestrator = get_ai_orchestrator()
    guardian = get_guardian()

    return {
        "status": "operational",
        "modules": {
            "theo": "active",
            "orchestrator": "active",
            "guardian": "active",
            "gpt": "active" if AIModule.GPT in orchestrator._module_clients else "not_configured",
            "claude": "active" if AIModule.CLAUDE in orchestrator._module_clients else "not_configured"
        },
        "pending_alerts": len(guardian.get_pending_alerts()),
        "version": "1.0.0"
    }
