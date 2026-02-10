"""
AZALS MODULE - Marceau Router
===============================

Routes API FastAPI pour l'agent Marceau.
"""

import uuid
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User

from .config import get_or_create_marceau_config, reset_marceau_config, update_marceau_config
from .memory import MarceauMemoryService
from .models import ActionStatus, MarceauAction, MarceauConfig, MarceauConversation, MarceauKnowledgeDocument, MemoryType
from .orchestrator import MarceauOrchestrator
from .schemas import (
    ActionListResponse,
    ActionValidationRequest,
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationListResponse,
    ConversationStatsResponse,
    FeedbackCreate,
    FeedbackResponse,
    KnowledgeDocumentResponse,
    MarceauActionResponse,
    MarceauConfigResponse,
    MarceauConfigUpdate,
    MarceauConversationResponse,
    MarceauDashboardResponse,
    MarceauMemoryCreate,
    MarceauMemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    ScheduledTaskCreate,
    ScheduledTaskResponse,
    ScheduledTaskUpdate,
)

router = APIRouter(prefix="/marceau", tags=["Marceau AI Assistant"])


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_orchestrator(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> MarceauOrchestrator:
    """Factory orchestrateur avec tenant et authentification."""
    return MarceauOrchestrator(tenant_id, db)


def get_memory_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> MarceauMemoryService:
    """Factory service memoire."""
    return MarceauMemoryService(tenant_id, db)


# ============================================================================
# CONFIGURATION
# ============================================================================

@router.get("/config", response_model=MarceauConfigResponse)
async def get_config(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Recupere la configuration Marceau du tenant."""
    config = get_or_create_marceau_config(tenant_id, db)
    return config


@router.patch("/config", response_model=MarceauConfigResponse)
async def update_config(
    data: MarceauConfigUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Met a jour la configuration Marceau."""
    config = update_marceau_config(
        tenant_id,
        db,
        **data.model_dump(exclude_unset=True)
    )
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")
    return config


@router.post("/config/reset", response_model=MarceauConfigResponse)
async def reset_config(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Reinitialise la configuration aux valeurs par defaut."""
    config = reset_marceau_config(tenant_id, db)
    return config


# ============================================================================
# ACTIONS
# ============================================================================

@router.get("/actions", response_model=ActionListResponse)
async def list_actions(
    module: str | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    requires_validation: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Liste des actions Marceau avec filtres."""
    filters = [MarceauAction.tenant_id == tenant_id]

    if module:
        filters.append(MarceauAction.module == module)
    if status:
        filters.append(MarceauAction.status == status)
    if date_from:
        filters.append(MarceauAction.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        filters.append(MarceauAction.created_at <= datetime.combine(date_to, datetime.max.time()))
    if requires_validation is not None:
        filters.append(MarceauAction.required_human_validation == requires_validation)

    query = db.query(MarceauAction).filter(*filters)
    total = query.count()

    actions = query.order_by(
        MarceauAction.created_at.desc()
    ).offset(skip).limit(limit).all()

    return ActionListResponse(
        items=actions,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/actions/{action_id}", response_model=MarceauActionResponse)
async def get_action(
    action_id: uuid.UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Recupere une action par ID."""
    action = db.query(MarceauAction).filter(
        MarceauAction.id == action_id,
        MarceauAction.tenant_id == tenant_id
    ).first()

    if not action:
        raise HTTPException(status_code=404, detail="Action non trouvee")
    return action


@router.post("/actions/{action_id}/validate", response_model=MarceauActionResponse)
async def validate_action(
    action_id: uuid.UUID,
    data: ActionValidationRequest,
    orchestrator: MarceauOrchestrator = Depends(get_orchestrator),
    current_user: User = Depends(get_current_user)
):
    """Valide ou rejette une action en attente."""
    await orchestrator.initialize()

    action = await orchestrator.validate_action(
        action_id=action_id,
        approved=data.approved,
        validated_by=current_user.id,
        notes=data.notes
    )

    if not action:
        raise HTTPException(status_code=404, detail="Action non trouvee ou deja traitee")
    return action


@router.delete("/actions/{action_id}")
async def delete_action(
    action_id: uuid.UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Supprime une action."""
    action = db.query(MarceauAction).filter(
        MarceauAction.id == action_id,
        MarceauAction.tenant_id == tenant_id
    ).first()

    if not action:
        raise HTTPException(status_code=404, detail="Action non trouvee")

    db.delete(action)
    db.commit()

    return {"status": "deleted"}


# ============================================================================
# CONVERSATIONS
# ============================================================================

@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    outcome: str | None = None,
    intent: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    customer_id: uuid.UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Liste des conversations telephoniques."""
    filters = [MarceauConversation.tenant_id == tenant_id]

    if outcome:
        filters.append(MarceauConversation.outcome == outcome)
    if intent:
        filters.append(MarceauConversation.intent == intent)
    if date_from:
        filters.append(MarceauConversation.started_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        filters.append(MarceauConversation.started_at <= datetime.combine(date_to, datetime.max.time()))
    if customer_id:
        filters.append(MarceauConversation.customer_id == customer_id)

    query = db.query(MarceauConversation).filter(*filters)
    total = query.count()

    conversations = query.order_by(
        MarceauConversation.started_at.desc()
    ).offset(skip).limit(limit).all()

    return ConversationListResponse(
        items=conversations,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/conversations/{conversation_id}", response_model=MarceauConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Recupere une conversation par ID."""
    conversation = db.query(MarceauConversation).filter(
        MarceauConversation.id == conversation_id,
        MarceauConversation.tenant_id == tenant_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation non trouvee")
    return conversation


@router.get("/conversations/stats", response_model=ConversationStatsResponse)
async def get_conversation_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Statistiques des conversations."""
    from sqlalchemy import func
    from datetime import timedelta

    start_date = datetime.utcnow() - timedelta(days=days)

    base_filter = [
        MarceauConversation.tenant_id == tenant_id,
        MarceauConversation.started_at >= start_date
    ]

    total = db.query(func.count(MarceauConversation.id)).filter(*base_filter).scalar() or 0

    avg_duration = db.query(func.avg(MarceauConversation.duration_seconds)).filter(*base_filter).scalar()

    avg_satisfaction = db.query(func.avg(MarceauConversation.satisfaction_score)).filter(
        *base_filter,
        MarceauConversation.satisfaction_score != None
    ).scalar()

    outcomes = db.query(
        MarceauConversation.outcome,
        func.count(MarceauConversation.id)
    ).filter(*base_filter).group_by(MarceauConversation.outcome).all()

    intents = db.query(
        MarceauConversation.intent,
        func.count(MarceauConversation.id)
    ).filter(*base_filter).group_by(MarceauConversation.intent).all()

    return ConversationStatsResponse(
        total_conversations=total,
        avg_duration_seconds=float(avg_duration) if avg_duration else 0.0,
        avg_satisfaction_score=float(avg_satisfaction) if avg_satisfaction else None,
        outcomes_distribution={str(o): c for o, c in outcomes if o},
        intents_distribution={str(i): c for i, c in intents if i},
        calls_by_hour={},
        calls_by_day={}
    )


# ============================================================================
# CHAT
# ============================================================================

@router.post("/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(
    data: ChatMessageRequest,
    orchestrator: MarceauOrchestrator = Depends(get_orchestrator)
):
    """Envoie un message au chat Marceau."""
    await orchestrator.initialize()

    result = await orchestrator.chat(
        message=data.message,
        conversation_id=data.conversation_id
    )

    return ChatMessageResponse(**result)


@router.websocket("/chat")
async def websocket_chat(
    websocket: WebSocket,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """WebSocket pour chat temps reel avec Marceau."""
    await websocket.accept()

    orchestrator = MarceauOrchestrator(tenant_id, db)
    await orchestrator.initialize()

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")

            result = await orchestrator.chat(message)

            await websocket.send_json(result)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "error": str(e),
            "message": "Erreur de connexion"
        })


# ============================================================================
# MEMOIRE
# ============================================================================

@router.post("/memory", response_model=MarceauMemoryResponse)
async def create_memory(
    data: MarceauMemoryCreate,
    memory_service: MarceauMemoryService = Depends(get_memory_service)
):
    """Cree une nouvelle memoire."""
    memory = await memory_service.store_memory(
        content=data.content,
        memory_type=MemoryType(data.memory_type),
        tags=data.tags,
        importance_score=data.importance_score,
        summary=data.summary,
        is_permanent=data.is_permanent,
        source=data.source
    )
    return memory


@router.post("/memory/search", response_model=MemorySearchResponse)
async def search_memory(
    data: MemorySearchRequest,
    memory_service: MarceauMemoryService = Depends(get_memory_service)
):
    """Recherche dans la memoire."""
    memory_types = [MemoryType(mt) for mt in data.memory_types] if data.memory_types else None

    memories, total = await memory_service.search_memories(
        query=data.query,
        memory_types=memory_types,
        tags=data.tags,
        limit=data.limit
    )

    return MemorySearchResponse(
        memories=memories,
        query=data.query,
        total_results=total
    )


@router.get("/memory/stats")
async def get_memory_stats(
    memory_service: MarceauMemoryService = Depends(get_memory_service)
):
    """Statistiques de la memoire."""
    return await memory_service.get_stats()


@router.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: uuid.UUID,
    memory_service: MarceauMemoryService = Depends(get_memory_service)
):
    """Supprime une memoire."""
    if not await memory_service.delete_memory(memory_id):
        raise HTTPException(status_code=404, detail="Memoire non trouvee")
    return {"status": "deleted"}


# ============================================================================
# DOCUMENTS DE CONNAISSANCE
# ============================================================================

@router.post("/knowledge/upload", response_model=KnowledgeDocumentResponse)
async def upload_knowledge_document(
    file: UploadFile = File(...),
    category: str | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Upload un document pour enrichir la base de connaissances."""
    # Valider le type de fichier
    allowed_types = ["application/pdf", "application/msword",
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                     "text/plain", "text/csv"]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non supporte: {file.content_type}"
        )

    # Lire le contenu
    content = await file.read()

    # Creer l'entree en base
    doc = MarceauKnowledgeDocument(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        file_name=file.filename,
        file_type=file.content_type.split("/")[-1],
        file_size=len(content),
        category=category,
        tags=[],
        uploaded_by=current_user.id,
        is_processed=False
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    # TODO: Declencher traitement asynchrone pour extraction et embeddings

    return doc


@router.get("/knowledge", response_model=list[KnowledgeDocumentResponse])
async def list_knowledge_documents(
    category: str | None = None,
    processed_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Liste les documents de connaissance."""
    filters = [MarceauKnowledgeDocument.tenant_id == tenant_id]

    if category:
        filters.append(MarceauKnowledgeDocument.category == category)
    if processed_only:
        filters.append(MarceauKnowledgeDocument.is_processed == True)

    docs = db.query(MarceauKnowledgeDocument).filter(
        *filters
    ).order_by(
        MarceauKnowledgeDocument.created_at.desc()
    ).offset(skip).limit(limit).all()

    return docs


@router.delete("/knowledge/{document_id}")
async def delete_knowledge_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Supprime un document de connaissance."""
    doc = db.query(MarceauKnowledgeDocument).filter(
        MarceauKnowledgeDocument.id == document_id,
        MarceauKnowledgeDocument.tenant_id == tenant_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouve")

    db.delete(doc)
    db.commit()

    return {"status": "deleted"}


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=MarceauDashboardResponse)
async def get_dashboard(
    orchestrator: MarceauOrchestrator = Depends(get_orchestrator)
):
    """Dashboard Marceau complet."""
    await orchestrator.initialize()
    data = await orchestrator.get_dashboard_data()

    # Convertir les actions en format response
    data["recent_actions"] = [
        MarceauActionResponse.model_validate(a) for a in data["recent_actions"]
    ]

    return MarceauDashboardResponse(**data)


# ============================================================================
# INTEGRATIONS TEST
# ============================================================================

@router.post("/integrations/test/{integration_name}")
async def test_integration(
    integration_name: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Teste une integration externe."""
    config = get_or_create_marceau_config(tenant_id, db)

    if integration_name == "ors":
        # Test OpenRouteService
        api_key = config.integrations.get("ors_api_key")
        if not api_key:
            return {"success": False, "error": "Cle API ORS non configuree"}

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openrouteservice.org/v2/health",
                    headers={"Authorization": api_key}
                )
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    elif integration_name == "asterisk":
        # Test Asterisk AMI
        ami_config = config.telephony_config
        host = ami_config.get("asterisk_ami_host", "localhost")
        port = ami_config.get("asterisk_ami_port", 5038)

        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            return {
                "success": result == 0,
                "message": "Connexion OK" if result == 0 else f"Impossible de se connecter a {host}:{port}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    else:
        return {"success": False, "error": f"Integration {integration_name} non supportee"}
