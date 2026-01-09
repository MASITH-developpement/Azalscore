"""
AZALS MODULE - Modèles Server Connections
==========================================

Modèles SQLAlchemy pour la gestion des connexions serveur.
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    Enum, JSON, Float
)
from app.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class ServerStatus(str, enum.Enum):
    """Statuts de serveur."""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    CONNECTING = "CONNECTING"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"
    UNKNOWN = "UNKNOWN"


class ConnectionType(str, enum.Enum):
    """Types de connexion."""
    SSH_PASSWORD = "SSH_PASSWORD"
    SSH_KEY = "SSH_KEY"
    SSH_KEY_PASSWORD = "SSH_KEY_PASSWORD"


class ServerRole(str, enum.Enum):
    """Rôles du serveur."""
    PRODUCTION = "PRODUCTION"
    STAGING = "STAGING"
    DEVELOPMENT = "DEVELOPMENT"
    BACKUP = "BACKUP"
    DATABASE = "DATABASE"
    CUSTOM = "CUSTOM"


class CommandStatus(str, enum.Enum):
    """Statuts d'exécution de commande."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"


class DeploymentStatus(str, enum.Enum):
    """Statuts de déploiement."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


# ============================================================================
# MODÈLES
# ============================================================================

class ServerConnection(Base):
    """Configuration d'une connexion serveur."""
    __tablename__ = "server_connections"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Connexion
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=22)
    connection_type = Column(Enum(ConnectionType), default=ConnectionType.SSH_PASSWORD)

    # Authentification (chiffrés)
    username = Column(String(100), nullable=False)
    password_encrypted = Column(Text)  # Chiffré avec Fernet
    private_key_encrypted = Column(Text)  # Clé SSH chiffrée
    passphrase_encrypted = Column(Text)  # Passphrase de la clé

    # Configuration
    role = Column(Enum(ServerRole), default=ServerRole.PRODUCTION)
    environment = Column(String(50), default="production")
    working_directory = Column(String(500), default="/home/azalscore")
    azalscore_path = Column(String(500), default="/opt/azalscore")

    # État
    status = Column(Enum(ServerStatus), default=ServerStatus.UNKNOWN)
    last_connection = Column(DateTime)
    last_health_check = Column(DateTime)

    # Métriques serveur
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    uptime_seconds = Column(Integer)

    # Configuration avancée
    timeout_seconds = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)
    connection_config = Column(JSON)  # Config supplémentaire

    # Statuts
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Tags et métadonnées
    tags = Column(JSON)  # ["production", "france", "main"]
    extra_data = Column(JSON)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))


class ServerCredential(Base):
    """Stockage sécurisé des identifiants serveur."""
    __tablename__ = "server_credentials"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Type d'identifiant
    credential_type = Column(String(50), nullable=False)  # password, ssh_key, api_key
    name = Column(String(100))

    # Valeurs chiffrées
    value_encrypted = Column(Text, nullable=False)

    # Métadonnées
    is_primary = Column(Boolean, default=False)
    expires_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))


class CommandExecution(Base):
    """Historique des commandes exécutées."""
    __tablename__ = "server_command_executions"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Commande
    command = Column(Text, nullable=False)
    command_type = Column(String(50))  # shell, git, docker, azalscore
    working_directory = Column(String(500))

    # Résultat
    status = Column(Enum(CommandStatus), default=CommandStatus.PENDING)
    exit_code = Column(Integer)
    stdout = Column(Text)
    stderr = Column(Text)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)
    timeout_ms = Column(Integer, default=60000)

    # Exécuteur
    executed_by = Column(String(100))
    executed_by_id = Column(Integer)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)


class ServerDeployment(Base):
    """Historique des déploiements."""
    __tablename__ = "server_deployments"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Déploiement
    deployment_type = Column(String(50))  # full, update, hotfix, rollback
    version_from = Column(String(50))
    version_to = Column(String(50))
    git_branch = Column(String(100))
    git_commit = Column(String(50))

    # Statut
    status = Column(Enum(DeploymentStatus), default=DeploymentStatus.PENDING)
    progress_percent = Column(Integer, default=0)
    current_step = Column(String(100))

    # Logs
    logs = Column(Text)
    error_message = Column(Text)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Rollback
    can_rollback = Column(Boolean, default=True)
    rollback_version = Column(String(50))
    rolled_back_at = Column(DateTime)

    # Exécuteur
    deployed_by = Column(String(100))
    deployed_by_id = Column(Integer)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)


class ServerHealthCheck(Base):
    """Historique des vérifications de santé."""
    __tablename__ = "server_health_checks"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Résultat
    is_healthy = Column(Boolean, default=False)
    status = Column(Enum(ServerStatus))

    # Métriques
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    memory_total_gb = Column(Float)
    memory_available_gb = Column(Float)
    disk_usage = Column(Float)
    disk_total_gb = Column(Float)
    disk_available_gb = Column(Float)
    uptime_seconds = Column(Integer)
    load_average = Column(JSON)  # [1min, 5min, 15min]

    # Services
    services_status = Column(JSON)  # {"docker": "running", "nginx": "running"}
    azalscore_status = Column(String(50))  # running, stopped, error
    azalscore_version = Column(String(50))

    # Connectivité
    ssh_latency_ms = Column(Integer)
    http_latency_ms = Column(Integer)

    # Détails
    check_details = Column(JSON)
    error_message = Column(Text)

    # Audit
    checked_at = Column(DateTime, default=datetime.utcnow)


class ServerEvent(Base):
    """Événements serveur (audit)."""
    __tablename__ = "server_events"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Événement
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSON)
    description = Column(Text)
    severity = Column(String(20), default="info")  # info, warning, error, critical

    # Acteur
    actor_id = Column(Integer)
    actor_email = Column(String(255))
    actor_ip = Column(String(50))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
