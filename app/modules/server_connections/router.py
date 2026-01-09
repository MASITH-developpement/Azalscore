"""
AZALS MODULE - Router Server Connections
=========================================

API REST pour la gestion des connexions serveur.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user

from .service import get_server_connection_service
from .schemas import (
    ServerConnectionCreate, ServerConnectionUpdate,
    ServerConnectionResponse, ServerConnectionListResponse,
    CommandExecutionRequest, CommandExecutionResponse, CommandExecutionListResponse,
    QuickCommandRequest, QuickCommandResponse,
    DeploymentRequest, DeploymentResponse, DeploymentListResponse,
    HealthCheckResponse,
    FileTransferRequest, FileTransferResponse,
    FileListRequest, FileListResponse,
    ServerEventResponse,
    ServerDashboardResponse,
    ConnectionTestRequest, ConnectionTestResponse,
    GitStatusResponse, GitPullRequest, GitPullResponse,
    ServiceStatusResponse, ServiceActionRequest, ServiceActionResponse,
    DockerContainersResponse, DockerComposeActionRequest, DockerComposeActionResponse
)


router = APIRouter(prefix="/api/v1/servers", tags=["Server Connections"])


# ============================================================================
# HELPERS
# ============================================================================

def get_service(db: Session, current_user: dict):
    """Obtenir le service de connexions serveur."""
    return get_server_connection_service(
        db=db,
        tenant_id=current_user["tenant_id"],
        actor_id=current_user.get("user_id"),
        actor_email=current_user.get("email")
    )


def require_admin_role(current_user: dict):
    """Vérifier que l'utilisateur a un rôle admin."""
    role = current_user.get("role", "")
    if role not in ["SUPER_ADMIN", "DIRIGEANT", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Rôle ADMIN ou supérieur requis pour gérer les serveurs."
        )


# ============================================================================
# SERVER CONNECTIONS CRUD
# ============================================================================

@router.post("", response_model=ServerConnectionResponse, status_code=201)
def create_server(
    data: ServerConnectionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Créer une nouvelle connexion serveur.

    Nécessite un rôle ADMIN ou supérieur.
    """
    require_admin_role(current_user)
    service = get_service(db, current_user)
    return service.create_server(data)


@router.get("", response_model=List[ServerConnectionListResponse])
def list_servers(
    role: Optional[str] = None,
    status: Optional[str] = None,
    is_active: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les serveurs configurés."""
    service = get_service(db, current_user)
    return service.list_servers(role, status, is_active, skip, limit)


@router.get("/default", response_model=ServerConnectionResponse)
def get_default_server(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer le serveur par défaut."""
    service = get_service(db, current_user)
    server = service.get_default_server()
    if not server:
        raise HTTPException(status_code=404, detail="Aucun serveur par défaut configuré")
    return server


@router.get("/{server_id}", response_model=ServerConnectionResponse)
def get_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un serveur par ID."""
    service = get_service(db, current_user)
    server = service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Serveur non trouvé")
    return server


@router.put("/{server_id}", response_model=ServerConnectionResponse)
def update_server(
    server_id: int,
    data: ServerConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un serveur."""
    require_admin_role(current_user)
    service = get_service(db, current_user)
    server = service.update_server(server_id, data)
    if not server:
        raise HTTPException(status_code=404, detail="Serveur non trouvé")
    return server


@router.delete("/{server_id}")
def delete_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Supprimer un serveur."""
    require_admin_role(current_user)
    service = get_service(db, current_user)
    if not service.delete_server(server_id):
        raise HTTPException(status_code=404, detail="Serveur non trouvé")
    return {"message": "Serveur supprimé"}


# ============================================================================
# CONNECTION MANAGEMENT
# ============================================================================

@router.post("/{server_id}/connect")
def connect_to_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Établir une connexion SSH au serveur."""
    service = get_service(db, current_user)
    try:
        service.connect(server_id)
        return {"message": "Connexion établie", "connected": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de connexion: {str(e)}")


@router.post("/{server_id}/disconnect")
def disconnect_from_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Fermer la connexion SSH au serveur."""
    service = get_service(db, current_user)
    service.disconnect(server_id)
    return {"message": "Connexion fermée", "connected": False}


@router.post("/test-connection", response_model=ConnectionTestResponse)
def test_connection(
    data: ConnectionTestRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Tester une connexion sans la sauvegarder."""
    require_admin_role(current_user)
    service = get_service(db, current_user)
    return service.test_connection(data)


# ============================================================================
# COMMAND EXECUTION
# ============================================================================

@router.post("/{server_id}/execute", response_model=CommandExecutionResponse)
def execute_command(
    server_id: int,
    data: CommandExecutionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Exécuter une commande sur le serveur.

    Nécessite un rôle ADMIN ou supérieur.
    """
    require_admin_role(current_user)
    service = get_service(db, current_user)
    try:
        return service.execute_command(server_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'exécution: {str(e)}")


@router.get("/{server_id}/commands", response_model=List[CommandExecutionListResponse])
def get_command_history(
    server_id: int,
    command_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer l'historique des commandes."""
    service = get_service(db, current_user)
    return service.get_command_history(server_id, command_type, status, skip, limit)


# ============================================================================
# QUICK COMMANDS
# ============================================================================

@router.get("/{server_id}/quick-commands")
def list_quick_commands(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les commandes rapides disponibles."""
    from .service import ServerConnectionService
    commands = []
    for name, info in ServerConnectionService.QUICK_COMMANDS.items():
        commands.append({
            "name": name,
            "description": info["description"]
        })
    return {"commands": commands}


@router.post("/{server_id}/quick-commands/{command_name}", response_model=CommandExecutionResponse)
def execute_quick_command(
    server_id: int,
    command_name: str,
    parameters: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Exécuter une commande rapide prédéfinie.

    Commandes disponibles:
    - status: Statut d'Azalscore
    - logs: Voir les logs récents
    - restart: Redémarrer Azalscore
    - stop/start: Arrêter/Démarrer
    - update: Mettre à jour depuis Git
    - disk/memory: Infos système
    - docker_ps: Conteneurs Docker
    - git_status/git_log: Infos Git
    - version: Version Azalscore
    """
    require_admin_role(current_user)
    service = get_service(db, current_user)
    try:
        return service.execute_quick_command(server_id, command_name, parameters)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# HEALTH CHECKS
# ============================================================================

@router.post("/{server_id}/health-check", response_model=HealthCheckResponse)
def perform_health_check(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Effectuer une vérification de santé du serveur."""
    service = get_service(db, current_user)
    try:
        return service.perform_health_check(server_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{server_id}/health-history", response_model=List[HealthCheckResponse])
def get_health_history(
    server_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer l'historique des health checks."""
    service = get_service(db, current_user)
    return service.get_health_history(server_id, skip, limit)


# ============================================================================
# DEPLOYMENTS
# ============================================================================

@router.post("/{server_id}/deploy", response_model=DeploymentResponse)
def deploy(
    server_id: int,
    data: DeploymentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Lancer un déploiement sur le serveur.

    Nécessite un rôle ADMIN ou supérieur.
    """
    require_admin_role(current_user)
    service = get_service(db, current_user)
    try:
        return service.create_deployment(server_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de déploiement: {str(e)}")


@router.get("/{server_id}/deployments", response_model=List[DeploymentListResponse])
def get_deployment_history(
    server_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer l'historique des déploiements."""
    service = get_service(db, current_user)
    return service.get_deployment_history(server_id, skip, limit)


@router.get("/{server_id}/deployments/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(
    server_id: int,
    deployment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les détails d'un déploiement."""
    service = get_service(db, current_user)
    deployments = service.get_deployment_history(server_id, limit=1000)
    for d in deployments:
        if d.id == deployment_id:
            return d
    raise HTTPException(status_code=404, detail="Déploiement non trouvé")


# ============================================================================
# FILE OPERATIONS
# ============================================================================

@router.post("/{server_id}/files/transfer", response_model=FileTransferResponse)
def transfer_file(
    server_id: int,
    data: FileTransferRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Transférer un fichier vers/depuis le serveur."""
    require_admin_role(current_user)
    service = get_service(db, current_user)
    try:
        return service.transfer_file(server_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{server_id}/files/list", response_model=FileListResponse)
def list_files(
    server_id: int,
    data: FileListRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les fichiers d'un répertoire distant."""
    service = get_service(db, current_user)
    try:
        return service.list_files(server_id, data.path, data.pattern)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# GIT OPERATIONS
# ============================================================================

@router.get("/{server_id}/git/status", response_model=GitStatusResponse)
def get_git_status(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer le statut Git du serveur."""
    service = get_service(db, current_user)
    server = service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Serveur non trouvé")

    # Exécuter git status
    result = service.execute_command(server_id, CommandExecutionRequest(
        command=f"cd {server.azalscore_path} && git status --porcelain && echo '---BRANCH---' && git branch --show-current && echo '---COMMIT---' && git log -1 --format='%h|%s|%ai'",
        command_type="git",
        timeout_ms=30000
    ))

    if result.exit_code != 0:
        raise HTTPException(status_code=500, detail=f"Erreur git: {result.stderr}")

    # Parser le résultat
    parts = result.stdout.split("---BRANCH---")
    status_part = parts[0].strip() if parts else ""
    rest = parts[1] if len(parts) > 1 else ""
    branch_parts = rest.split("---COMMIT---")
    branch = branch_parts[0].strip() if branch_parts else "main"
    commit_info = branch_parts[1].strip() if len(branch_parts) > 1 else ""

    modified = []
    untracked = []
    for line in status_part.split("\n"):
        if line.startswith(" M") or line.startswith("M "):
            modified.append(line[3:].strip())
        elif line.startswith("??"):
            untracked.append(line[3:].strip())

    commit_hash = ""
    commit_message = ""
    commit_date = None
    if "|" in commit_info:
        commit_parts = commit_info.split("|")
        commit_hash = commit_parts[0] if len(commit_parts) > 0 else ""
        commit_message = commit_parts[1] if len(commit_parts) > 1 else ""
        if len(commit_parts) > 2:
            from datetime import datetime
            try:
                commit_date = datetime.fromisoformat(commit_parts[2].strip().replace(" ", "T").split("+")[0])
            except Exception:
                commit_date = datetime.now()

    return {
        "branch": branch,
        "commit_hash": commit_hash,
        "commit_message": commit_message,
        "commit_date": commit_date or datetime.now(),
        "is_clean": len(modified) == 0 and len(untracked) == 0,
        "modified_files": modified,
        "untracked_files": untracked,
        "ahead": 0,
        "behind": 0
    }


@router.post("/{server_id}/git/pull", response_model=GitPullResponse)
def git_pull(
    server_id: int,
    data: GitPullRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Exécuter git pull sur le serveur."""
    require_admin_role(current_user)
    service = get_service(db, current_user)
    server = service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Serveur non trouvé")

    branch = data.branch or "main"
    path = server.azalscore_path

    # Sauvegarder le commit actuel
    result = service.execute_command(server_id, CommandExecutionRequest(
        command=f"cd {path} && git rev-parse --short HEAD",
        command_type="git",
        timeout_ms=10000
    ))
    previous_commit = result.stdout.strip() if result.exit_code == 0 else ""

    # Stash si demandé
    if data.stash_changes:
        service.execute_command(server_id, CommandExecutionRequest(
            command=f"cd {path} && git stash",
            command_type="git",
            timeout_ms=30000
        ))

    # Pull
    force_flag = "--force" if data.force else ""
    result = service.execute_command(server_id, CommandExecutionRequest(
        command=f"cd {path} && git pull origin {branch} {force_flag}",
        command_type="git",
        timeout_ms=120000
    ))

    # Nouveau commit
    new_result = service.execute_command(server_id, CommandExecutionRequest(
        command=f"cd {path} && git rev-parse --short HEAD",
        command_type="git",
        timeout_ms=10000
    ))
    new_commit = new_result.stdout.strip() if new_result.exit_code == 0 else ""

    return {
        "success": result.exit_code == 0,
        "previous_commit": previous_commit,
        "new_commit": new_commit,
        "files_changed": 0,
        "insertions": 0,
        "deletions": 0,
        "output": result.stdout + result.stderr
    }


# ============================================================================
# DOCKER OPERATIONS
# ============================================================================

@router.get("/{server_id}/docker/containers", response_model=DockerContainersResponse)
def list_docker_containers(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les conteneurs Docker."""
    service = get_service(db, current_user)
    result = service.execute_command(server_id, CommandExecutionRequest(
        command="docker ps -a --format '{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.State}}|{{.CreatedAt}}|{{.Ports}}'",
        command_type="docker",
        timeout_ms=30000
    ))

    containers = []
    for line in result.stdout.strip().split("\n"):
        if "|" in line:
            parts = line.split("|")
            if len(parts) >= 6:
                from datetime import datetime
                containers.append({
                    "id": parts[0],
                    "name": parts[1],
                    "image": parts[2],
                    "status": parts[3],
                    "state": parts[4],
                    "created": datetime.now(),  # Simplified
                    "ports": {},
                    "health": None
                })

    return {
        "containers": containers,
        "total_count": len(containers)
    }


@router.post("/{server_id}/docker/compose", response_model=DockerComposeActionResponse)
def docker_compose_action(
    server_id: int,
    data: DockerComposeActionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Exécuter une action Docker Compose.

    Actions disponibles: up, down, restart, logs, ps
    """
    require_admin_role(current_user)
    service = get_service(db, current_user)
    server = service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Serveur non trouvé")

    path = server.azalscore_path
    services_str = " ".join(data.services) if data.services else ""

    if data.action == "up":
        cmd = f"cd {path} && docker-compose up {'-d' if data.detach else ''} {services_str}"
    elif data.action == "down":
        cmd = f"cd {path} && docker-compose down {services_str}"
    elif data.action == "restart":
        cmd = f"cd {path} && docker-compose restart {services_str}"
    elif data.action == "logs":
        follow = "-f" if data.follow_logs else ""
        cmd = f"cd {path} && docker-compose logs {follow} --tail={data.tail} {services_str}"
    elif data.action == "ps":
        cmd = f"cd {path} && docker-compose ps"
    else:
        raise HTTPException(status_code=400, detail=f"Action non supportée: {data.action}")

    result = service.execute_command(server_id, CommandExecutionRequest(
        command=cmd,
        command_type="docker",
        timeout_ms=300000
    ))

    return {
        "action": data.action,
        "success": result.exit_code == 0,
        "output": result.stdout + result.stderr,
        "services_affected": data.services or []
    }


# ============================================================================
# EVENTS
# ============================================================================

@router.get("/{server_id}/events", response_model=List[ServerEventResponse])
def get_server_events(
    server_id: int,
    event_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les événements du serveur."""
    service = get_service(db, current_user)
    return service.get_events(server_id, event_type, skip, limit)


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/{server_id}/dashboard", response_model=ServerDashboardResponse)
def get_server_dashboard(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer le dashboard complet d'un serveur."""
    service = get_service(db, current_user)

    server = service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Serveur non trouvé")

    # Health check récent
    health_history = service.get_health_history(server_id, limit=1)
    health = health_history[0] if health_history else None

    # Commandes récentes
    commands = service.get_command_history(server_id, limit=10)

    # Déploiements récents
    deployments = service.get_deployment_history(server_id, limit=5)

    # Événements récents
    events = service.get_events(server_id, limit=10)

    return {
        "server": server,
        "health": health,
        "recent_commands": commands,
        "recent_deployments": deployments,
        "recent_events": events
    }
