"""
AZALS MODULE - Schémas Server Connections
==========================================

Schémas Pydantic pour l'API des connexions serveur.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import json


# ============================================================================
# ENUMS (pour référence)
# ============================================================================

class ServerStatus(str):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    CONNECTING = "CONNECTING"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"
    UNKNOWN = "UNKNOWN"


class ConnectionType(str):
    SSH_PASSWORD = "SSH_PASSWORD"
    SSH_KEY = "SSH_KEY"
    SSH_KEY_PASSWORD = "SSH_KEY_PASSWORD"


class ServerRole(str):
    PRODUCTION = "PRODUCTION"
    STAGING = "STAGING"
    DEVELOPMENT = "DEVELOPMENT"
    BACKUP = "BACKUP"
    DATABASE = "DATABASE"
    CUSTOM = "CUSTOM"


# ============================================================================
# SERVER CONNECTION
# ============================================================================

class ServerConnectionCreate(BaseModel):
    """Création d'une connexion serveur."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(default=22, ge=1, le=65535)
    connection_type: str = "SSH_PASSWORD"
    username: str = Field(..., min_length=1, max_length=100)
    password: Optional[str] = None
    private_key: Optional[str] = None
    passphrase: Optional[str] = None
    role: str = "PRODUCTION"
    environment: str = "production"
    working_directory: str = "/home/azalscore"
    azalscore_path: str = "/opt/azalscore"
    timeout_seconds: int = 30
    retry_count: int = 3
    is_default: bool = False
    tags: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None


class ServerConnectionUpdate(BaseModel):
    """Mise à jour d'une connexion serveur."""
    name: Optional[str] = None
    description: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    connection_type: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None
    passphrase: Optional[str] = None
    role: Optional[str] = None
    environment: Optional[str] = None
    working_directory: Optional[str] = None
    azalscore_path: Optional[str] = None
    timeout_seconds: Optional[int] = None
    retry_count: Optional[int] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None


class ServerConnectionResponse(BaseModel):
    """Réponse connexion serveur."""
    id: int
    tenant_id: str
    name: str
    description: Optional[str]
    host: str
    port: int
    connection_type: str
    username: str
    role: str
    environment: str
    working_directory: str
    azalscore_path: str
    status: str
    last_connection: Optional[datetime]
    last_health_check: Optional[datetime]
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    disk_usage: Optional[float]
    uptime_seconds: Optional[int]
    timeout_seconds: int
    retry_count: int
    is_active: bool
    is_default: bool
    tags: Optional[List[str]]
    extra_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    @field_validator("tags", "extra_data", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    model_config = ConfigDict(from_attributes=True)


class ServerConnectionListResponse(BaseModel):
    """Liste des connexions serveur."""
    id: int
    name: str
    host: str
    port: int
    role: str
    status: str
    is_active: bool
    is_default: bool
    last_connection: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# COMMAND EXECUTION
# ============================================================================

class CommandExecutionRequest(BaseModel):
    """Demande d'exécution de commande."""
    command: str = Field(..., min_length=1)
    working_directory: Optional[str] = None
    timeout_ms: int = Field(default=60000, ge=1000, le=600000)
    command_type: str = "shell"  # shell, git, docker, azalscore
    sudo: bool = False
    environment: Optional[Dict[str, str]] = None


class CommandExecutionResponse(BaseModel):
    """Réponse d'exécution de commande."""
    id: int
    server_id: int
    command: str
    command_type: str
    status: str
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommandExecutionListResponse(BaseModel):
    """Liste des exécutions de commande."""
    id: int
    server_id: int
    command: str
    command_type: Optional[str]
    status: str
    exit_code: Optional[int]
    duration_ms: Optional[int]
    executed_by: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# QUICK COMMANDS (commandes prédéfinies)
# ============================================================================

class QuickCommandRequest(BaseModel):
    """Commande rapide prédéfinie."""
    command_name: str = Field(..., min_length=1)
    parameters: Optional[Dict[str, str]] = None


class QuickCommandResponse(BaseModel):
    """Réponse commande rapide."""
    command_name: str
    description: str
    result: CommandExecutionResponse


# ============================================================================
# DEPLOYMENT
# ============================================================================

class DeploymentRequest(BaseModel):
    """Demande de déploiement."""
    deployment_type: str = "update"  # full, update, hotfix, rollback
    git_branch: str = "main"
    git_commit: Optional[str] = None
    run_migrations: bool = True
    restart_services: bool = True
    backup_first: bool = True
    notify_on_complete: bool = True


class DeploymentResponse(BaseModel):
    """Réponse de déploiement."""
    id: int
    server_id: int
    deployment_type: str
    version_from: Optional[str]
    version_to: Optional[str]
    git_branch: str
    git_commit: Optional[str]
    status: str
    progress_percent: int
    current_step: Optional[str]
    logs: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    can_rollback: bool
    deployed_by: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeploymentListResponse(BaseModel):
    """Liste des déploiements."""
    id: int
    server_id: int
    deployment_type: str
    version_to: Optional[str]
    git_branch: str
    status: str
    progress_percent: int
    deployed_by: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# HEALTH CHECK
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Réponse de vérification de santé."""
    id: int
    server_id: int
    is_healthy: bool
    status: str
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    memory_total_gb: Optional[float]
    memory_available_gb: Optional[float]
    disk_usage: Optional[float]
    disk_total_gb: Optional[float]
    disk_available_gb: Optional[float]
    uptime_seconds: Optional[int]
    load_average: Optional[List[float]]
    services_status: Optional[Dict[str, str]]
    azalscore_status: Optional[str]
    azalscore_version: Optional[str]
    ssh_latency_ms: Optional[int]
    http_latency_ms: Optional[int]
    error_message: Optional[str]
    checked_at: datetime

    @field_validator("load_average", "services_status", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# FILE TRANSFER
# ============================================================================

class FileTransferRequest(BaseModel):
    """Demande de transfert de fichier."""
    direction: str = "upload"  # upload, download
    local_path: str
    remote_path: str
    overwrite: bool = False
    create_dirs: bool = True


class FileTransferResponse(BaseModel):
    """Réponse de transfert de fichier."""
    success: bool
    direction: str
    local_path: str
    remote_path: str
    bytes_transferred: int
    duration_ms: int
    error_message: Optional[str] = None


class FileListRequest(BaseModel):
    """Demande de liste de fichiers."""
    path: str = "."
    recursive: bool = False
    pattern: Optional[str] = None


class FileInfo(BaseModel):
    """Information sur un fichier."""
    name: str
    path: str
    is_directory: bool
    size: int
    permissions: str
    owner: str
    group: str
    modified_at: datetime


class FileListResponse(BaseModel):
    """Liste des fichiers."""
    path: str
    files: List[FileInfo]
    total_count: int


# ============================================================================
# SERVER EVENTS
# ============================================================================

class ServerEventResponse(BaseModel):
    """Réponse événement serveur."""
    id: int
    server_id: int
    event_type: str
    event_data: Optional[Dict[str, Any]]
    description: Optional[str]
    severity: str
    actor_email: Optional[str]
    created_at: datetime

    @field_validator("event_data", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# GIT OPERATIONS
# ============================================================================

class GitStatusResponse(BaseModel):
    """Statut Git du serveur."""
    branch: str
    commit_hash: str
    commit_message: str
    commit_date: datetime
    is_clean: bool
    modified_files: List[str]
    untracked_files: List[str]
    ahead: int
    behind: int


class GitPullRequest(BaseModel):
    """Demande de git pull."""
    branch: Optional[str] = None
    force: bool = False
    stash_changes: bool = True


class GitPullResponse(BaseModel):
    """Réponse git pull."""
    success: bool
    previous_commit: str
    new_commit: str
    files_changed: int
    insertions: int
    deletions: int
    output: str


# ============================================================================
# SERVICE MANAGEMENT
# ============================================================================

class ServiceStatusResponse(BaseModel):
    """Statut d'un service."""
    name: str
    status: str  # running, stopped, error
    pid: Optional[int]
    uptime: Optional[str]
    memory_usage: Optional[str]
    cpu_usage: Optional[str]


class ServiceActionRequest(BaseModel):
    """Action sur un service."""
    service_name: str
    action: str  # start, stop, restart, status


class ServiceActionResponse(BaseModel):
    """Réponse action service."""
    service_name: str
    action: str
    success: bool
    output: str
    new_status: Optional[str]


# ============================================================================
# DOCKER OPERATIONS
# ============================================================================

class DockerContainerInfo(BaseModel):
    """Information sur un conteneur Docker."""
    id: str
    name: str
    image: str
    status: str
    state: str
    created: datetime
    ports: Dict[str, Any]
    health: Optional[str]


class DockerContainersResponse(BaseModel):
    """Liste des conteneurs Docker."""
    containers: List[DockerContainerInfo]
    total_count: int


class DockerComposeActionRequest(BaseModel):
    """Action Docker Compose."""
    action: str  # up, down, restart, logs, ps
    services: Optional[List[str]] = None
    detach: bool = True
    follow_logs: bool = False
    tail: int = 100


class DockerComposeActionResponse(BaseModel):
    """Réponse action Docker Compose."""
    action: str
    success: bool
    output: str
    services_affected: List[str]


# ============================================================================
# DASHBOARD & STATS
# ============================================================================

class ServerDashboardResponse(BaseModel):
    """Dashboard serveur complet."""
    server: ServerConnectionResponse
    health: Optional[HealthCheckResponse]
    recent_commands: List[CommandExecutionListResponse]
    recent_deployments: List[DeploymentListResponse]
    recent_events: List[ServerEventResponse]


class ServerStatsResponse(BaseModel):
    """Statistiques serveur."""
    total_commands_executed: int
    successful_commands: int
    failed_commands: int
    total_deployments: int
    successful_deployments: int
    failed_deployments: int
    average_command_duration_ms: float
    uptime_percent: float
    last_30_days_health: List[Dict[str, Any]]


# ============================================================================
# BATCH OPERATIONS
# ============================================================================

class BatchCommandRequest(BaseModel):
    """Exécution de commandes sur plusieurs serveurs."""
    server_ids: List[int]
    command: str
    timeout_ms: int = 60000
    parallel: bool = True
    stop_on_error: bool = False


class BatchCommandResult(BaseModel):
    """Résultat par serveur."""
    server_id: int
    server_name: str
    success: bool
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    duration_ms: Optional[int]
    error_message: Optional[str]


class BatchCommandResponse(BaseModel):
    """Réponse batch."""
    total_servers: int
    successful: int
    failed: int
    results: List[BatchCommandResult]


# ============================================================================
# CONNECTION TEST
# ============================================================================

class ConnectionTestRequest(BaseModel):
    """Test de connexion."""
    host: str
    port: int = 22
    username: str
    password: Optional[str] = None
    private_key: Optional[str] = None
    passphrase: Optional[str] = None
    timeout_seconds: int = 10


class ConnectionTestResponse(BaseModel):
    """Réponse test de connexion."""
    success: bool
    latency_ms: int
    server_info: Optional[Dict[str, str]]
    error_message: Optional[str]
