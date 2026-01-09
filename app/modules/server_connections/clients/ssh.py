"""
AZALS - Client SSH
==================

Client SSH/SFTP pour les connexions aux serveurs distants.
Utilise paramiko pour les opérations SSH sécurisées.
"""

import io
import os
import time
import logging
import socket
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

import paramiko
from paramiko import SSHClient as ParamikoSSHClient
from paramiko import AutoAddPolicy, RSAKey, Ed25519Key, ECDSAKey

logger = logging.getLogger(__name__)


class SSHConnectionError(Exception):
    """Erreur de connexion SSH."""
    pass


class SSHCommandError(Exception):
    """Erreur d'exécution de commande."""
    def __init__(self, message: str, exit_code: int, stdout: str, stderr: str):
        super().__init__(message)
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


@dataclass
class CommandResult:
    """Résultat d'une commande."""
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    command: str


@dataclass
class FileInfo:
    """Information sur un fichier."""
    name: str
    path: str
    is_directory: bool
    size: int
    permissions: str
    owner: str
    group: str
    modified_at: datetime


class SSHClient:
    """
    Client SSH pour la connexion aux serveurs distants.

    Supporte:
    - Authentification par mot de passe
    - Authentification par clé SSH (RSA, Ed25519, ECDSA)
    - Exécution de commandes
    - Transfert de fichiers SFTP
    - Gestion des timeouts
    """

    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = None,
        password: str = None,
        private_key: str = None,
        passphrase: str = None,
        timeout: int = 30,
        retry_count: int = 3
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.private_key = private_key
        self.passphrase = passphrase
        self.timeout = timeout
        self.retry_count = retry_count

        self._client: Optional[ParamikoSSHClient] = None
        self._sftp: Optional[paramiko.SFTPClient] = None
        self._connected = False
        self._server_info: Dict[str, str] = {}

    @property
    def is_connected(self) -> bool:
        """Vérifie si la connexion est active."""
        if not self._connected or not self._client:
            return False
        try:
            transport = self._client.get_transport()
            if transport and transport.is_active():
                return True
        except Exception:
            pass
        return False

    def connect(self) -> bool:
        """
        Établit la connexion SSH.

        Returns:
            True si la connexion est établie

        Raises:
            SSHConnectionError: Si la connexion échoue
        """
        if self.is_connected:
            return True

        last_error = None

        for attempt in range(self.retry_count):
            try:
                self._client = ParamikoSSHClient()
                self._client.set_missing_host_key_policy(AutoAddPolicy())

                connect_kwargs = {
                    "hostname": self.host,
                    "port": self.port,
                    "username": self.username,
                    "timeout": self.timeout,
                    "allow_agent": False,
                    "look_for_keys": False,
                }

                # Authentification par clé SSH
                if self.private_key:
                    pkey = self._load_private_key(self.private_key, self.passphrase)
                    connect_kwargs["pkey"] = pkey
                # Authentification par mot de passe
                elif self.password:
                    connect_kwargs["password"] = self.password

                self._client.connect(**connect_kwargs)
                self._connected = True

                # Récupérer les informations du serveur
                self._gather_server_info()

                logger.info(f"Connexion SSH établie vers {self.host}:{self.port}")
                return True

            except paramiko.AuthenticationException as e:
                last_error = f"Échec d'authentification: {str(e)}"
                logger.error(f"Échec d'authentification SSH vers {self.host}: {e}")
                break  # Pas de retry pour les erreurs d'auth

            except paramiko.SSHException as e:
                last_error = f"Erreur SSH: {str(e)}"
                logger.warning(f"Erreur SSH (tentative {attempt + 1}/{self.retry_count}): {e}")

            except socket.timeout:
                last_error = f"Timeout de connexion après {self.timeout}s"
                logger.warning(f"Timeout SSH (tentative {attempt + 1}/{self.retry_count})")

            except socket.error as e:
                last_error = f"Erreur réseau: {str(e)}"
                logger.warning(f"Erreur réseau (tentative {attempt + 1}/{self.retry_count}): {e}")

            except Exception as e:
                last_error = f"Erreur inattendue: {str(e)}"
                logger.error(f"Erreur inattendue lors de la connexion SSH: {e}")

            # Attendre avant de réessayer (backoff exponentiel)
            if attempt < self.retry_count - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)

        self._connected = False
        raise SSHConnectionError(last_error or "Échec de connexion SSH")

    def disconnect(self):
        """Ferme la connexion SSH."""
        try:
            if self._sftp:
                self._sftp.close()
                self._sftp = None
            if self._client:
                self._client.close()
                self._client = None
            self._connected = False
            logger.info(f"Connexion SSH fermée vers {self.host}")
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture SSH: {e}")

    def _load_private_key(self, key_str: str, passphrase: str = None) -> paramiko.PKey:
        """
        Charge une clé privée depuis une chaîne.

        Supporte RSA, Ed25519, et ECDSA.
        """
        key_classes = [RSAKey, Ed25519Key, ECDSAKey]
        key_io = io.StringIO(key_str)

        for key_class in key_classes:
            try:
                key_io.seek(0)
                return key_class.from_private_key(key_io, password=passphrase)
            except paramiko.SSHException:
                continue

        raise SSHConnectionError("Format de clé SSH non reconnu")

    def _gather_server_info(self):
        """Récupère les informations de base du serveur."""
        try:
            transport = self._client.get_transport()
            if transport:
                self._server_info = {
                    "server_version": transport.remote_version or "unknown",
                    "cipher": transport.remote_cipher or "unknown",
                    "mac": transport.remote_mac or "unknown",
                }
        except Exception:
            pass

    def execute(
        self,
        command: str,
        timeout: int = None,
        working_directory: str = None,
        sudo: bool = False,
        environment: Dict[str, str] = None
    ) -> CommandResult:
        """
        Exécute une commande sur le serveur distant.

        Args:
            command: Commande à exécuter
            timeout: Timeout en secondes (défaut: self.timeout)
            working_directory: Répertoire de travail
            sudo: Exécuter avec sudo
            environment: Variables d'environnement supplémentaires

        Returns:
            CommandResult avec exit_code, stdout, stderr, duration_ms
        """
        if not self.is_connected:
            self.connect()

        timeout = timeout or self.timeout
        start_time = time.time()

        # Construire la commande
        full_command = command

        if working_directory:
            full_command = f"cd {working_directory} && {full_command}"

        if sudo:
            full_command = f"sudo {full_command}"

        if environment:
            env_str = " ".join(f"{k}={v}" for k, v in environment.items())
            full_command = f"{env_str} {full_command}"

        try:
            stdin, stdout, stderr = self._client.exec_command(
                full_command,
                timeout=timeout,
                get_pty=sudo  # PTY nécessaire pour sudo
            )

            # Si sudo avec mot de passe
            if sudo and self.password:
                stdin.write(f"{self.password}\n")
                stdin.flush()

            # Lire les résultats
            stdout_str = stdout.read().decode("utf-8", errors="replace")
            stderr_str = stderr.read().decode("utf-8", errors="replace")
            exit_code = stdout.channel.recv_exit_status()

            duration_ms = int((time.time() - start_time) * 1000)

            logger.debug(f"Commande exécutée: {command[:50]}... (exit: {exit_code})")

            return CommandResult(
                exit_code=exit_code,
                stdout=stdout_str,
                stderr=stderr_str,
                duration_ms=duration_ms,
                command=command
            )

        except socket.timeout:
            raise SSHCommandError(
                f"Timeout lors de l'exécution de la commande",
                exit_code=-1,
                stdout="",
                stderr=f"Command timeout after {timeout}s"
            )
        except Exception as e:
            raise SSHCommandError(
                f"Erreur d'exécution: {str(e)}",
                exit_code=-1,
                stdout="",
                stderr=str(e)
            )

    def execute_script(
        self,
        script: str,
        timeout: int = None,
        working_directory: str = None
    ) -> CommandResult:
        """
        Exécute un script multi-lignes sur le serveur.

        Args:
            script: Script bash à exécuter
            timeout: Timeout en secondes
            working_directory: Répertoire de travail

        Returns:
            CommandResult
        """
        # Créer un script temporaire
        script_content = f"#!/bin/bash\nset -e\n{script}"
        remote_script = "/tmp/azalscore_temp_script.sh"

        # Uploader le script
        self._get_sftp().putfo(
            io.BytesIO(script_content.encode()),
            remote_script
        )

        # Exécuter
        try:
            result = self.execute(
                f"bash {remote_script}",
                timeout=timeout,
                working_directory=working_directory
            )
            return result
        finally:
            # Nettoyer
            try:
                self.execute(f"rm -f {remote_script}")
            except Exception:
                pass

    def _get_sftp(self) -> paramiko.SFTPClient:
        """Obtient ou crée une connexion SFTP."""
        if not self.is_connected:
            self.connect()

        if not self._sftp:
            self._sftp = self._client.open_sftp()

        return self._sftp

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        create_dirs: bool = True
    ) -> Tuple[bool, int]:
        """
        Upload un fichier vers le serveur.

        Args:
            local_path: Chemin local du fichier
            remote_path: Chemin distant
            create_dirs: Créer les répertoires manquants

        Returns:
            Tuple (success, bytes_transferred)
        """
        sftp = self._get_sftp()

        if create_dirs:
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                try:
                    self.execute(f"mkdir -p {remote_dir}")
                except Exception:
                    pass

        try:
            sftp.put(local_path, remote_path)
            stat = sftp.stat(remote_path)
            logger.info(f"Fichier uploadé: {local_path} -> {remote_path}")
            return True, stat.st_size
        except Exception as e:
            logger.error(f"Erreur upload: {e}")
            return False, 0

    def upload_content(
        self,
        content: str,
        remote_path: str,
        create_dirs: bool = True
    ) -> Tuple[bool, int]:
        """
        Upload du contenu texte vers un fichier distant.

        Args:
            content: Contenu à écrire
            remote_path: Chemin distant
            create_dirs: Créer les répertoires manquants

        Returns:
            Tuple (success, bytes_transferred)
        """
        sftp = self._get_sftp()

        if create_dirs:
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                try:
                    self.execute(f"mkdir -p {remote_dir}")
                except Exception:
                    pass

        try:
            content_bytes = content.encode("utf-8")
            sftp.putfo(io.BytesIO(content_bytes), remote_path)
            logger.info(f"Contenu uploadé vers: {remote_path}")
            return True, len(content_bytes)
        except Exception as e:
            logger.error(f"Erreur upload contenu: {e}")
            return False, 0

    def download_file(
        self,
        remote_path: str,
        local_path: str
    ) -> Tuple[bool, int]:
        """
        Télécharge un fichier depuis le serveur.

        Args:
            remote_path: Chemin distant
            local_path: Chemin local de destination

        Returns:
            Tuple (success, bytes_transferred)
        """
        sftp = self._get_sftp()

        # Créer le répertoire local si nécessaire
        local_dir = os.path.dirname(local_path)
        if local_dir:
            os.makedirs(local_dir, exist_ok=True)

        try:
            sftp.get(remote_path, local_path)
            size = os.path.getsize(local_path)
            logger.info(f"Fichier téléchargé: {remote_path} -> {local_path}")
            return True, size
        except Exception as e:
            logger.error(f"Erreur download: {e}")
            return False, 0

    def download_content(self, remote_path: str) -> Optional[str]:
        """
        Télécharge le contenu d'un fichier distant.

        Args:
            remote_path: Chemin distant

        Returns:
            Contenu du fichier ou None si erreur
        """
        sftp = self._get_sftp()

        try:
            with sftp.file(remote_path, "r") as f:
                return f.read().decode("utf-8")
        except Exception as e:
            logger.error(f"Erreur lecture fichier distant: {e}")
            return None

    def list_directory(
        self,
        path: str = ".",
        pattern: str = None
    ) -> List[FileInfo]:
        """
        Liste les fichiers d'un répertoire.

        Args:
            path: Chemin du répertoire
            pattern: Pattern glob (optionnel)

        Returns:
            Liste de FileInfo
        """
        sftp = self._get_sftp()
        result = []

        try:
            for attr in sftp.listdir_attr(path):
                if pattern and not self._match_pattern(attr.filename, pattern):
                    continue

                file_path = os.path.join(path, attr.filename)

                # Permissions en format octal
                perms = oct(attr.st_mode)[-3:] if attr.st_mode else "000"

                # Owner/Group (on utilise les IDs car les noms ne sont pas disponibles via SFTP)
                owner = str(attr.st_uid) if attr.st_uid else "unknown"
                group = str(attr.st_gid) if attr.st_gid else "unknown"

                result.append(FileInfo(
                    name=attr.filename,
                    path=file_path,
                    is_directory=attr.st_mode and (attr.st_mode & 0o40000) != 0,
                    size=attr.st_size or 0,
                    permissions=perms,
                    owner=owner,
                    group=group,
                    modified_at=datetime.fromtimestamp(attr.st_mtime) if attr.st_mtime else datetime.now()
                ))

        except Exception as e:
            logger.error(f"Erreur listage répertoire: {e}")

        return result

    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """Vérifie si un nom de fichier correspond à un pattern."""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)

    def file_exists(self, path: str) -> bool:
        """Vérifie si un fichier existe."""
        sftp = self._get_sftp()
        try:
            sftp.stat(path)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def delete_file(self, path: str) -> bool:
        """Supprime un fichier."""
        sftp = self._get_sftp()
        try:
            sftp.remove(path)
            logger.info(f"Fichier supprimé: {path}")
            return True
        except Exception as e:
            logger.error(f"Erreur suppression fichier: {e}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        """
        Teste la connexion au serveur.

        Returns:
            Dict avec success, latency_ms, server_info, error_message
        """
        start_time = time.time()

        try:
            self.connect()

            # Exécuter une commande simple
            result = self.execute("echo 'connection_test'", timeout=5)

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "success": result.exit_code == 0,
                "latency_ms": latency_ms,
                "server_info": self._server_info,
                "error_message": None
            }

        except SSHConnectionError as e:
            return {
                "success": False,
                "latency_ms": int((time.time() - start_time) * 1000),
                "server_info": None,
                "error_message": str(e)
            }

    def get_system_info(self) -> Dict[str, Any]:
        """
        Récupère les informations système du serveur.

        Returns:
            Dict avec hostname, os, kernel, uptime, etc.
        """
        info = {}

        try:
            # Hostname
            result = self.execute("hostname", timeout=5)
            if result.exit_code == 0:
                info["hostname"] = result.stdout.strip()

            # OS
            result = self.execute("cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'", timeout=5)
            if result.exit_code == 0:
                info["os"] = result.stdout.strip()

            # Kernel
            result = self.execute("uname -r", timeout=5)
            if result.exit_code == 0:
                info["kernel"] = result.stdout.strip()

            # Uptime
            result = self.execute("cat /proc/uptime | cut -d' ' -f1", timeout=5)
            if result.exit_code == 0:
                info["uptime_seconds"] = int(float(result.stdout.strip()))

            # CPU
            result = self.execute("nproc", timeout=5)
            if result.exit_code == 0:
                info["cpu_cores"] = int(result.stdout.strip())

            # Memory
            result = self.execute("free -b | grep Mem | awk '{print $2, $7}'", timeout=5)
            if result.exit_code == 0:
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    info["memory_total_bytes"] = int(parts[0])
                    info["memory_available_bytes"] = int(parts[1])

            # Disk
            result = self.execute("df -B1 / | tail -1 | awk '{print $2, $4}'", timeout=5)
            if result.exit_code == 0:
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    info["disk_total_bytes"] = int(parts[0])
                    info["disk_available_bytes"] = int(parts[1])

            # Load average
            result = self.execute("cat /proc/loadavg | cut -d' ' -f1-3", timeout=5)
            if result.exit_code == 0:
                parts = result.stdout.strip().split()
                info["load_average"] = [float(p) for p in parts[:3]]

        except Exception as e:
            logger.error(f"Erreur récupération infos système: {e}")

        return info

    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Récupère l'utilisation des ressources.

        Returns:
            Dict avec cpu_usage, memory_usage, disk_usage
        """
        usage = {}

        try:
            # CPU usage (moyenne sur 1 seconde)
            result = self.execute(
                "top -bn2 -d1 | grep 'Cpu(s)' | tail -1 | awk '{print 100 - $8}'",
                timeout=5
            )
            if result.exit_code == 0:
                usage["cpu_usage"] = float(result.stdout.strip())

            # Memory usage
            result = self.execute(
                "free | grep Mem | awk '{print ($3/$2) * 100}'",
                timeout=5
            )
            if result.exit_code == 0:
                usage["memory_usage"] = float(result.stdout.strip())

            # Disk usage
            result = self.execute(
                "df / | tail -1 | awk '{print $5}' | tr -d '%'",
                timeout=5
            )
            if result.exit_code == 0:
                usage["disk_usage"] = float(result.stdout.strip())

        except Exception as e:
            logger.error(f"Erreur récupération usage ressources: {e}")

        return usage

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
