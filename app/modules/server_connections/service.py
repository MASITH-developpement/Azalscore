"""
AZALS MODULE - Service Server Connections
==========================================

Logique métier pour la gestion des connexions serveur.
"""

import time
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from .models import (
    ServerConnection, ServerCredential, CommandExecution,
    ServerDeployment, ServerHealthCheck, ServerEvent,
    ServerStatus, ConnectionType, ServerRole,
    CommandStatus, DeploymentStatus
)
from .schemas import (
    ServerConnectionCreate, ServerConnectionUpdate,
    CommandExecutionRequest, DeploymentRequest,
    FileTransferRequest, ConnectionTestRequest
)
from .clients.ssh import SSHClient, SSHConnectionError, CommandResult

logger = logging.getLogger(__name__)


# ============================================================================
# CHIFFREMENT
# ============================================================================

def _encrypt_value(value: str) -> str:
    """Chiffre une valeur sensible."""
    try:
        from app.core.encryption import encrypt_data
        return encrypt_data(value)
    except ImportError:
        # Fallback si encryption non disponible
        import base64
        return base64.b64encode(value.encode()).decode()


def _decrypt_value(encrypted: str) -> str:
    """Déchiffre une valeur sensible."""
    try:
        from app.core.encryption import decrypt_data
        return decrypt_data(encrypted)
    except ImportError:
        # Fallback si encryption non disponible
        import base64
        return base64.b64decode(encrypted.encode()).decode()


class ServerConnectionService:
    """Service de gestion des connexions serveur."""

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        actor_id: Optional[int] = None,
        actor_email: Optional[str] = None
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self.actor_email = actor_email
        self._ssh_clients: Dict[int, SSHClient] = {}

    # ========================================================================
    # SERVER CONNECTION CRUD
    # ========================================================================

    def create_server(self, data: ServerConnectionCreate) -> ServerConnection:
        """Créer une nouvelle connexion serveur."""
        server = ServerConnection(
            tenant_id=self.tenant_id,
            name=data.name,
            description=data.description,
            host=data.host,
            port=data.port,
            connection_type=ConnectionType[data.connection_type],
            username=data.username,
            role=ServerRole[data.role],
            environment=data.environment,
            working_directory=data.working_directory,
            azalscore_path=data.azalscore_path,
            timeout_seconds=data.timeout_seconds,
            retry_count=data.retry_count,
            is_default=data.is_default,
            tags=data.tags,
            extra_data=data.extra_data,
            created_by=self.actor_email,
        )

        # Chiffrer les identifiants
        if data.password:
            server.password_encrypted = _encrypt_value(data.password)
        if data.private_key:
            server.private_key_encrypted = _encrypt_value(data.private_key)
        if data.passphrase:
            server.passphrase_encrypted = _encrypt_value(data.passphrase)

        # Si c'est le serveur par défaut, retirer le flag des autres
        if data.is_default:
            self.db.query(ServerConnection).filter(
                ServerConnection.tenant_id == self.tenant_id,
                ServerConnection.is_default == True
            ).update({"is_default": False})

        self.db.add(server)
        self.db.commit()
        self.db.refresh(server)

        self._log_event(server.id, "server.created", {
            "name": data.name,
            "host": data.host,
            "role": data.role,
        })

        logger.info(f"Serveur créé: {data.name} ({data.host})")
        return server

    def get_server(self, server_id: int) -> Optional[ServerConnection]:
        """Récupérer un serveur par ID."""
        return self.db.query(ServerConnection).filter(
            ServerConnection.id == server_id,
            ServerConnection.tenant_id == self.tenant_id
        ).first()

    def get_server_by_name(self, name: str) -> Optional[ServerConnection]:
        """Récupérer un serveur par nom."""
        return self.db.query(ServerConnection).filter(
            ServerConnection.name == name,
            ServerConnection.tenant_id == self.tenant_id
        ).first()

    def get_default_server(self) -> Optional[ServerConnection]:
        """Récupérer le serveur par défaut."""
        return self.db.query(ServerConnection).filter(
            ServerConnection.tenant_id == self.tenant_id,
            ServerConnection.is_default == True,
            ServerConnection.is_active == True
        ).first()

    def list_servers(
        self,
        role: Optional[str] = None,
        status: Optional[str] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 50
    ) -> List[ServerConnection]:
        """Lister les serveurs."""
        query = self.db.query(ServerConnection).filter(
            ServerConnection.tenant_id == self.tenant_id
        )

        if role:
            query = query.filter(ServerConnection.role == ServerRole[role])
        if status:
            query = query.filter(ServerConnection.status == ServerStatus[status])
        if is_active is not None:
            query = query.filter(ServerConnection.is_active == is_active)

        return query.order_by(
            ServerConnection.is_default.desc(),
            ServerConnection.name
        ).offset(skip).limit(limit).all()

    def update_server(
        self,
        server_id: int,
        data: ServerConnectionUpdate
    ) -> Optional[ServerConnection]:
        """Mettre à jour un serveur."""
        server = self.get_server(server_id)
        if not server:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Chiffrer les nouveaux identifiants
        if "password" in update_data and update_data["password"]:
            update_data["password_encrypted"] = _encrypt_value(update_data.pop("password"))
        else:
            update_data.pop("password", None)

        if "private_key" in update_data and update_data["private_key"]:
            update_data["private_key_encrypted"] = _encrypt_value(update_data.pop("private_key"))
        else:
            update_data.pop("private_key", None)

        if "passphrase" in update_data and update_data["passphrase"]:
            update_data["passphrase_encrypted"] = _encrypt_value(update_data.pop("passphrase"))
        else:
            update_data.pop("passphrase", None)

        # Convertir les enums
        if "connection_type" in update_data:
            update_data["connection_type"] = ConnectionType[update_data["connection_type"]]
        if "role" in update_data:
            update_data["role"] = ServerRole[update_data["role"]]

        # Gérer is_default
        if update_data.get("is_default"):
            self.db.query(ServerConnection).filter(
                ServerConnection.tenant_id == self.tenant_id,
                ServerConnection.is_default == True,
                ServerConnection.id != server_id
            ).update({"is_default": False})

        for key, value in update_data.items():
            if hasattr(server, key):
                setattr(server, key, value)

        self.db.commit()
        self.db.refresh(server)

        self._log_event(server_id, "server.updated", update_data)
        return server

    def delete_server(self, server_id: int) -> bool:
        """Supprimer un serveur."""
        server = self.get_server(server_id)
        if not server:
            return False

        # Fermer la connexion si active
        self._close_client(server_id)

        self._log_event(server_id, "server.deleted", {"name": server.name})

        self.db.delete(server)
        self.db.commit()
        return True

    # ========================================================================
    # SSH CONNECTION MANAGEMENT
    # ========================================================================

    def _get_client(self, server: ServerConnection) -> SSHClient:
        """Obtenir ou créer un client SSH pour un serveur."""
        if server.id in self._ssh_clients:
            client = self._ssh_clients[server.id]
            if client.is_connected:
                return client
            else:
                # Reconnecter
                del self._ssh_clients[server.id]

        # Déchiffrer les identifiants
        password = None
        private_key = None
        passphrase = None

        if server.password_encrypted:
            password = _decrypt_value(server.password_encrypted)
        if server.private_key_encrypted:
            private_key = _decrypt_value(server.private_key_encrypted)
        if server.passphrase_encrypted:
            passphrase = _decrypt_value(server.passphrase_encrypted)

        client = SSHClient(
            host=server.host,
            port=server.port,
            username=server.username,
            password=password,
            private_key=private_key,
            passphrase=passphrase,
            timeout=server.timeout_seconds,
            retry_count=server.retry_count
        )

        self._ssh_clients[server.id] = client
        return client

    def _close_client(self, server_id: int):
        """Fermer un client SSH."""
        if server_id in self._ssh_clients:
            try:
                self._ssh_clients[server_id].disconnect()
            except Exception:
                pass
            del self._ssh_clients[server_id]

    def connect(self, server_id: int) -> bool:
        """Établir la connexion à un serveur."""
        server = self.get_server(server_id)
        if not server:
            raise ValueError(f"Serveur {server_id} non trouvé")

        try:
            client = self._get_client(server)
            client.connect()

            server.status = ServerStatus.ONLINE
            server.last_connection = datetime.utcnow()
            self.db.commit()

            self._log_event(server_id, "server.connected", {})
            return True

        except SSHConnectionError as e:
            server.status = ServerStatus.ERROR
            self.db.commit()

            self._log_event(server_id, "server.connection_failed", {
                "error": str(e)
            }, severity="error")
            raise

    def disconnect(self, server_id: int):
        """Fermer la connexion à un serveur."""
        self._close_client(server_id)
        self._log_event(server_id, "server.disconnected", {})

    def test_connection(
        self,
        data: ConnectionTestRequest
    ) -> Dict[str, Any]:
        """Tester une connexion sans sauvegarder."""
        client = SSHClient(
            host=data.host,
            port=data.port,
            username=data.username,
            password=data.password,
            private_key=data.private_key,
            passphrase=data.passphrase,
            timeout=data.timeout_seconds
        )

        try:
            result = client.test_connection()
            return result
        finally:
            client.disconnect()

    # ========================================================================
    # COMMAND EXECUTION
    # ========================================================================

    def execute_command(
        self,
        server_id: int,
        data: CommandExecutionRequest
    ) -> CommandExecution:
        """Exécuter une commande sur un serveur."""
        server = self.get_server(server_id)
        if not server:
            raise ValueError(f"Serveur {server_id} non trouvé")

        # Créer l'enregistrement de commande
        execution = CommandExecution(
            server_id=server_id,
            tenant_id=self.tenant_id,
            command=data.command,
            command_type=data.command_type,
            working_directory=data.working_directory or server.working_directory,
            timeout_ms=data.timeout_ms,
            executed_by=self.actor_email,
            executed_by_id=self.actor_id,
            status=CommandStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        self.db.add(execution)
        self.db.commit()

        try:
            client = self._get_client(server)
            client.connect()

            result = client.execute(
                command=data.command,
                timeout=data.timeout_ms // 1000,
                working_directory=data.working_directory or server.working_directory,
                sudo=data.sudo,
                environment=data.environment
            )

            execution.status = CommandStatus.SUCCESS if result.exit_code == 0 else CommandStatus.FAILED
            execution.exit_code = result.exit_code
            execution.stdout = result.stdout[:50000]  # Limiter la taille
            execution.stderr = result.stderr[:50000]
            execution.duration_ms = result.duration_ms
            execution.completed_at = datetime.utcnow()

            server.status = ServerStatus.ONLINE
            server.last_connection = datetime.utcnow()

        except Exception as e:
            execution.status = CommandStatus.FAILED
            execution.stderr = str(e)
            execution.completed_at = datetime.utcnow()
            logger.error(f"Erreur exécution commande: {e}")

        self.db.commit()
        self.db.refresh(execution)

        self._log_event(server_id, "command.executed", {
            "command": data.command[:100],
            "status": execution.status.value,
            "exit_code": execution.exit_code
        })

        return execution

    def get_command_history(
        self,
        server_id: int,
        command_type: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[CommandExecution]:
        """Récupérer l'historique des commandes."""
        query = self.db.query(CommandExecution).filter(
            CommandExecution.server_id == server_id,
            CommandExecution.tenant_id == self.tenant_id
        )

        if command_type:
            query = query.filter(CommandExecution.command_type == command_type)
        if status:
            query = query.filter(CommandExecution.status == CommandStatus[status])

        return query.order_by(
            CommandExecution.created_at.desc()
        ).offset(skip).limit(limit).all()

    # ========================================================================
    # QUICK COMMANDS (commandes prédéfinies Azalscore)
    # ========================================================================

    QUICK_COMMANDS = {
        "status": {
            "description": "Vérifier le statut d'Azalscore",
            "command": "cd {azalscore_path} && docker-compose ps"
        },
        "logs": {
            "description": "Voir les logs récents",
            "command": "cd {azalscore_path} && docker-compose logs --tail=100"
        },
        "restart": {
            "description": "Redémarrer Azalscore",
            "command": "cd {azalscore_path} && docker-compose restart"
        },
        "stop": {
            "description": "Arrêter Azalscore",
            "command": "cd {azalscore_path} && docker-compose stop"
        },
        "start": {
            "description": "Démarrer Azalscore",
            "command": "cd {azalscore_path} && docker-compose up -d"
        },
        "update": {
            "description": "Mettre à jour depuis Git",
            "command": "cd {azalscore_path} && git pull origin main && docker-compose up -d --build"
        },
        "disk": {
            "description": "Espace disque",
            "command": "df -h"
        },
        "memory": {
            "description": "Utilisation mémoire",
            "command": "free -h"
        },
        "processes": {
            "description": "Processus en cours",
            "command": "ps aux --sort=-%mem | head -20"
        },
        "docker_ps": {
            "description": "Conteneurs Docker",
            "command": "docker ps -a"
        },
        "git_status": {
            "description": "Statut Git",
            "command": "cd {azalscore_path} && git status"
        },
        "git_log": {
            "description": "Historique Git récent",
            "command": "cd {azalscore_path} && git log --oneline -10"
        },
        "version": {
            "description": "Version Azalscore",
            "command": "cd {azalscore_path} && cat pyproject.toml | grep version"
        },
    }

    def execute_quick_command(
        self,
        server_id: int,
        command_name: str,
        parameters: Dict[str, str] = None
    ) -> CommandExecution:
        """Exécuter une commande rapide prédéfinie."""
        if command_name not in self.QUICK_COMMANDS:
            raise ValueError(f"Commande inconnue: {command_name}")

        server = self.get_server(server_id)
        if not server:
            raise ValueError(f"Serveur {server_id} non trouvé")

        cmd_info = self.QUICK_COMMANDS[command_name]
        command = cmd_info["command"]

        # Remplacer les variables
        command = command.format(
            azalscore_path=server.azalscore_path,
            working_directory=server.working_directory,
            **(parameters or {})
        )

        return self.execute_command(
            server_id,
            CommandExecutionRequest(
                command=command,
                command_type="azalscore",
                timeout_ms=120000
            )
        )

    # ========================================================================
    # HEALTH CHECKS
    # ========================================================================

    def perform_health_check(self, server_id: int) -> ServerHealthCheck:
        """Effectuer une vérification de santé."""
        server = self.get_server(server_id)
        if not server:
            raise ValueError(f"Serveur {server_id} non trouvé")

        health = ServerHealthCheck(
            server_id=server_id,
            tenant_id=self.tenant_id,
            checked_at=datetime.utcnow()
        )

        start_time = time.time()

        try:
            client = self._get_client(server)
            client.connect()

            health.ssh_latency_ms = int((time.time() - start_time) * 1000)

            # Récupérer les infos système
            system_info = client.get_system_info()
            usage = client.get_resource_usage()

            # CPU
            health.cpu_usage = usage.get("cpu_usage")

            # Memory
            health.memory_usage = usage.get("memory_usage")
            if "memory_total_bytes" in system_info:
                health.memory_total_gb = system_info["memory_total_bytes"] / (1024**3)
            if "memory_available_bytes" in system_info:
                health.memory_available_gb = system_info["memory_available_bytes"] / (1024**3)

            # Disk
            health.disk_usage = usage.get("disk_usage")
            if "disk_total_bytes" in system_info:
                health.disk_total_gb = system_info["disk_total_bytes"] / (1024**3)
            if "disk_available_bytes" in system_info:
                health.disk_available_gb = system_info["disk_available_bytes"] / (1024**3)

            # Uptime
            health.uptime_seconds = system_info.get("uptime_seconds")
            health.load_average = system_info.get("load_average")

            # Vérifier les services
            services = {}

            # Docker
            result = client.execute("systemctl is-active docker 2>/dev/null || echo 'inactive'", timeout=5)
            services["docker"] = result.stdout.strip()

            # Nginx (si présent)
            result = client.execute("systemctl is-active nginx 2>/dev/null || echo 'not_installed'", timeout=5)
            if result.stdout.strip() != "not_installed":
                services["nginx"] = result.stdout.strip()

            health.services_status = services

            # Vérifier Azalscore
            result = client.execute(
                f"cd {server.azalscore_path} && docker-compose ps -q api 2>/dev/null | head -1",
                timeout=10
            )
            if result.exit_code == 0 and result.stdout.strip():
                health.azalscore_status = "running"
                # Version
                result = client.execute(
                    f"cd {server.azalscore_path} && grep 'version' pyproject.toml | head -1 | cut -d'\"' -f2",
                    timeout=5
                )
                if result.exit_code == 0:
                    health.azalscore_version = result.stdout.strip()
            else:
                health.azalscore_status = "stopped"

            # Déterminer la santé globale
            health.is_healthy = (
                health.cpu_usage is not None and health.cpu_usage < 90 and
                health.memory_usage is not None and health.memory_usage < 90 and
                health.disk_usage is not None and health.disk_usage < 90
            )
            health.status = ServerStatus.ONLINE if health.is_healthy else ServerStatus.ERROR

            server.status = health.status
            server.last_health_check = datetime.utcnow()
            server.cpu_usage = health.cpu_usage
            server.memory_usage = health.memory_usage
            server.disk_usage = health.disk_usage
            server.uptime_seconds = health.uptime_seconds

        except Exception as e:
            health.is_healthy = False
            health.status = ServerStatus.OFFLINE
            health.error_message = str(e)
            server.status = ServerStatus.OFFLINE
            logger.error(f"Erreur health check: {e}")

        self.db.add(health)
        self.db.commit()
        self.db.refresh(health)

        return health

    def get_health_history(
        self,
        server_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ServerHealthCheck]:
        """Récupérer l'historique des health checks."""
        return self.db.query(ServerHealthCheck).filter(
            ServerHealthCheck.server_id == server_id,
            ServerHealthCheck.tenant_id == self.tenant_id
        ).order_by(
            ServerHealthCheck.checked_at.desc()
        ).offset(skip).limit(limit).all()

    # ========================================================================
    # DEPLOYMENTS
    # ========================================================================

    def create_deployment(
        self,
        server_id: int,
        data: DeploymentRequest
    ) -> ServerDeployment:
        """Créer et exécuter un déploiement."""
        server = self.get_server(server_id)
        if not server:
            raise ValueError(f"Serveur {server_id} non trouvé")

        deployment = ServerDeployment(
            server_id=server_id,
            tenant_id=self.tenant_id,
            deployment_type=data.deployment_type,
            git_branch=data.git_branch,
            git_commit=data.git_commit,
            status=DeploymentStatus.IN_PROGRESS,
            progress_percent=0,
            current_step="Initialisation",
            started_at=datetime.utcnow(),
            deployed_by=self.actor_email,
            deployed_by_id=self.actor_id,
        )

        self.db.add(deployment)
        self.db.commit()

        logs = []

        try:
            client = self._get_client(server)
            client.connect()

            path = server.azalscore_path

            # Récupérer la version actuelle
            result = client.execute(f"cd {path} && git rev-parse --short HEAD", timeout=10)
            deployment.version_from = result.stdout.strip() if result.exit_code == 0 else None

            # Étape 1: Backup (si demandé)
            if data.backup_first:
                deployment.current_step = "Backup"
                deployment.progress_percent = 10
                self.db.commit()

                result = client.execute(
                    f"cd {path} && docker-compose exec -T db pg_dump -U postgres azalscore > backup_$(date +%Y%m%d_%H%M%S).sql 2>&1 || echo 'Backup skipped'",
                    timeout=300
                )
                logs.append(f"Backup: {result.stdout}")

            # Étape 2: Git pull
            deployment.current_step = "Git pull"
            deployment.progress_percent = 30
            self.db.commit()

            result = client.execute(
                f"cd {path} && git fetch origin && git checkout {data.git_branch} && git pull origin {data.git_branch}",
                timeout=120
            )
            logs.append(f"Git: {result.stdout}")
            if result.exit_code != 0:
                raise Exception(f"Git pull failed: {result.stderr}")

            # Récupérer la nouvelle version
            result = client.execute(f"cd {path} && git rev-parse --short HEAD", timeout=10)
            deployment.version_to = result.stdout.strip() if result.exit_code == 0 else None

            # Étape 3: Build
            deployment.current_step = "Build"
            deployment.progress_percent = 50
            self.db.commit()

            result = client.execute(
                f"cd {path} && docker-compose build",
                timeout=600
            )
            logs.append(f"Build: {result.stdout[:1000]}")
            if result.exit_code != 0:
                raise Exception(f"Build failed: {result.stderr}")

            # Étape 4: Migrations (si demandé)
            if data.run_migrations:
                deployment.current_step = "Migrations"
                deployment.progress_percent = 70
                self.db.commit()

                result = client.execute(
                    f"cd {path} && docker-compose run --rm api python run_migrations.py",
                    timeout=300
                )
                logs.append(f"Migrations: {result.stdout}")

            # Étape 5: Restart (si demandé)
            if data.restart_services:
                deployment.current_step = "Restart services"
                deployment.progress_percent = 90
                self.db.commit()

                result = client.execute(
                    f"cd {path} && docker-compose up -d",
                    timeout=120
                )
                logs.append(f"Restart: {result.stdout}")

            # Succès
            deployment.status = DeploymentStatus.SUCCESS
            deployment.progress_percent = 100
            deployment.current_step = "Terminé"
            deployment.completed_at = datetime.utcnow()
            deployment.duration_seconds = int((deployment.completed_at - deployment.started_at).total_seconds())

        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            deployment.completed_at = datetime.utcnow()
            deployment.duration_seconds = int((deployment.completed_at - deployment.started_at).total_seconds())
            logs.append(f"ERREUR: {str(e)}")
            logger.error(f"Erreur déploiement: {e}")

        deployment.logs = "\n".join(logs)
        self.db.commit()
        self.db.refresh(deployment)

        self._log_event(server_id, "deployment.completed", {
            "type": data.deployment_type,
            "status": deployment.status.value,
            "version_to": deployment.version_to
        })

        return deployment

    def get_deployment_history(
        self,
        server_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[ServerDeployment]:
        """Récupérer l'historique des déploiements."""
        return self.db.query(ServerDeployment).filter(
            ServerDeployment.server_id == server_id,
            ServerDeployment.tenant_id == self.tenant_id
        ).order_by(
            ServerDeployment.created_at.desc()
        ).offset(skip).limit(limit).all()

    # ========================================================================
    # FILE OPERATIONS
    # ========================================================================

    def transfer_file(
        self,
        server_id: int,
        data: FileTransferRequest
    ) -> Dict[str, Any]:
        """Transférer un fichier."""
        server = self.get_server(server_id)
        if not server:
            raise ValueError(f"Serveur {server_id} non trouvé")

        start_time = time.time()

        try:
            client = self._get_client(server)
            client.connect()

            if data.direction == "upload":
                success, bytes_transferred = client.upload_file(
                    data.local_path,
                    data.remote_path,
                    create_dirs=data.create_dirs
                )
            else:
                success, bytes_transferred = client.download_file(
                    data.remote_path,
                    data.local_path
                )

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                "success": success,
                "direction": data.direction,
                "local_path": data.local_path,
                "remote_path": data.remote_path,
                "bytes_transferred": bytes_transferred,
                "duration_ms": duration_ms,
                "error_message": None
            }

        except Exception as e:
            return {
                "success": False,
                "direction": data.direction,
                "local_path": data.local_path,
                "remote_path": data.remote_path,
                "bytes_transferred": 0,
                "duration_ms": int((time.time() - start_time) * 1000),
                "error_message": str(e)
            }

    def list_files(
        self,
        server_id: int,
        path: str = ".",
        pattern: str = None
    ) -> Dict[str, Any]:
        """Lister les fichiers d'un répertoire."""
        server = self.get_server(server_id)
        if not server:
            raise ValueError(f"Serveur {server_id} non trouvé")

        client = self._get_client(server)
        client.connect()

        files = client.list_directory(path, pattern)

        return {
            "path": path,
            "files": [
                {
                    "name": f.name,
                    "path": f.path,
                    "is_directory": f.is_directory,
                    "size": f.size,
                    "permissions": f.permissions,
                    "owner": f.owner,
                    "group": f.group,
                    "modified_at": f.modified_at.isoformat()
                }
                for f in files
            ],
            "total_count": len(files)
        }

    # ========================================================================
    # EVENTS
    # ========================================================================

    def _log_event(
        self,
        server_id: int,
        event_type: str,
        event_data: Dict[str, Any],
        severity: str = "info"
    ):
        """Logger un événement serveur."""
        event = ServerEvent(
            server_id=server_id,
            tenant_id=self.tenant_id,
            event_type=event_type,
            event_data=event_data,
            severity=severity,
            actor_id=self.actor_id,
            actor_email=self.actor_email,
        )
        self.db.add(event)
        self.db.commit()

    def get_events(
        self,
        server_id: int,
        event_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[ServerEvent]:
        """Récupérer les événements."""
        query = self.db.query(ServerEvent).filter(
            ServerEvent.server_id == server_id,
            ServerEvent.tenant_id == self.tenant_id
        )

        if event_type:
            query = query.filter(ServerEvent.event_type == event_type)

        return query.order_by(
            ServerEvent.created_at.desc()
        ).offset(skip).limit(limit).all()

    # ========================================================================
    # CLEANUP
    # ========================================================================

    def close_all_connections(self):
        """Fermer toutes les connexions SSH."""
        for server_id in list(self._ssh_clients.keys()):
            self._close_client(server_id)


def get_server_connection_service(
    db: Session,
    tenant_id: str,
    actor_id: Optional[int] = None,
    actor_email: Optional[str] = None
) -> ServerConnectionService:
    """Factory pour le service de connexions serveur."""
    return ServerConnectionService(db, tenant_id, actor_id, actor_email)
