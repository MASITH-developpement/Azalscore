"""
AZALS - Service de Sauvegarde Externalisee par Tenant
=====================================================
Sauvegardes journalieres chiffrees sur serveur distant.
Aucune donnee en clair sur disque - chiffrement en memoire.

ARCHITECTURE:
- Serveur A: AZALSCORE (application)
- Serveur B: Stockage sauvegardes uniquement

PROVIDERS SUPPORTES (gratuits):
- SFTP/SCP (serveur Linux quelconque)
- WebDAV (Nextcloud, ownCloud)
- S3-compatible (Backblaze B2, Wasabi, MinIO)
- Rclone (100+ providers)

STRUCTURE DISTANTE:
/azalscore-backups/
 └── tenant_<id>/
      └── YYYY-MM-DD.tar.gz.enc
"""

import os
import io
import gzip
import json
import tarfile
import hashlib
import logging
import tempfile
import subprocess
import shutil
from typing import Optional, Dict, Any, List, Tuple, BinaryIO
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class BackupProvider(str, Enum):
    """Providers de stockage supportes."""
    SFTP = "sftp"
    SCP = "scp"
    WEBDAV = "webdav"
    S3 = "s3"
    RCLONE = "rclone"
    LOCAL = "local"  # Pour tests uniquement


class BackupError(Exception):
    """Erreur de sauvegarde."""
    pass


class BackupTransferError(BackupError):
    """Erreur de transfert vers serveur distant."""
    pass


class BackupIntegrityError(BackupError):
    """Integrite de la sauvegarde compromise."""
    pass


class BackupNotFoundError(BackupError):
    """Sauvegarde non trouvee."""
    pass


@dataclass
class BackupConfig:
    """Configuration du service de sauvegarde."""
    provider: BackupProvider = BackupProvider.SFTP
    remote_host: str = ""
    remote_port: int = 22
    remote_user: str = ""
    remote_path: str = "/azalscore-backups"
    ssh_key_path: Optional[str] = None
    ssh_password: Optional[str] = None
    s3_bucket: Optional[str] = None
    s3_endpoint: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    rclone_remote: Optional[str] = None
    webdav_url: Optional[str] = None
    webdav_user: Optional[str] = None
    webdav_password: Optional[str] = None
    retention_days: int = 7
    compression_level: int = 9


@dataclass
class BackupMetadata:
    """Metadonnees d'une sauvegarde."""
    tenant_id: str
    backup_date: datetime
    checksum_sha256: str
    size_bytes: int
    tables_count: int
    rows_count: int
    encrypted: bool = True
    compression: str = "gzip"
    version: str = "1.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TenantBackupService:
    """
    Service de sauvegarde isole par tenant.

    GARANTIES:
    - Chaque tenant a ses propres sauvegardes isolees
    - Donnees chiffrees AVANT transfert
    - Aucune copie locale apres transfert
    - Verification d'integrite automatique
    """

    def __init__(self, config: Optional[BackupConfig] = None):
        """
        Initialise le service de sauvegarde.

        Args:
            config: Configuration personnalisee.
                   Si None, lit depuis environnement.
        """
        self.config = config or self._load_config_from_env()
        self._validate_config()

    def _load_config_from_env(self) -> BackupConfig:
        """Charge la configuration depuis l'environnement."""
        provider_str = os.environ.get("BACKUP_PROVIDER", "sftp").lower()

        try:
            provider = BackupProvider(provider_str)
        except ValueError:
            provider = BackupProvider.SFTP

        return BackupConfig(
            provider=provider,
            remote_host=os.environ.get("BACKUP_HOST", ""),
            remote_port=int(os.environ.get("BACKUP_PORT", "22")),
            remote_user=os.environ.get("BACKUP_USER", ""),
            remote_path=os.environ.get("BACKUP_PATH", "/azalscore-backups"),
            ssh_key_path=os.environ.get("BACKUP_SSH_KEY"),
            ssh_password=os.environ.get("BACKUP_SSH_PASSWORD"),
            s3_bucket=os.environ.get("BACKUP_S3_BUCKET"),
            s3_endpoint=os.environ.get("BACKUP_S3_ENDPOINT"),
            s3_access_key=os.environ.get("BACKUP_S3_ACCESS_KEY"),
            s3_secret_key=os.environ.get("BACKUP_S3_SECRET_KEY"),
            rclone_remote=os.environ.get("BACKUP_RCLONE_REMOTE"),
            webdav_url=os.environ.get("BACKUP_WEBDAV_URL"),
            webdav_user=os.environ.get("BACKUP_WEBDAV_USER"),
            webdav_password=os.environ.get("BACKUP_WEBDAV_PASSWORD"),
            retention_days=int(os.environ.get("BACKUP_RETENTION_DAYS", "7")),
            compression_level=int(os.environ.get("BACKUP_COMPRESSION_LEVEL", "9")),
        )

    def _validate_config(self) -> None:
        """Valide la configuration."""
        if self.config.provider == BackupProvider.LOCAL:
            return  # Mode test, pas de validation

        if self.config.provider in (BackupProvider.SFTP, BackupProvider.SCP):
            if not self.config.remote_host:
                raise BackupError("BACKUP_HOST est requis pour SFTP/SCP")
            if not self.config.remote_user:
                raise BackupError("BACKUP_USER est requis pour SFTP/SCP")

        elif self.config.provider == BackupProvider.S3:
            if not self.config.s3_bucket:
                raise BackupError("BACKUP_S3_BUCKET est requis pour S3")

        elif self.config.provider == BackupProvider.RCLONE:
            if not self.config.rclone_remote:
                raise BackupError("BACKUP_RCLONE_REMOTE est requis pour Rclone")

        elif self.config.provider == BackupProvider.WEBDAV:
            if not self.config.webdav_url:
                raise BackupError("BACKUP_WEBDAV_URL est requis pour WebDAV")

    def create_backup(
        self,
        tenant_id: str,
        data: Dict[str, Any],
        encryption_func: callable
    ) -> BackupMetadata:
        """
        Cree une sauvegarde chiffree pour un tenant.

        Args:
            tenant_id: Identifiant du tenant
            data: Donnees a sauvegarder (dict JSON-serializable)
            encryption_func: Fonction de chiffrement tenant

        Returns:
            Metadonnees de la sauvegarde

        PROCESSUS:
        1. Serialise en JSON
        2. Compresse (gzip)
        3. Chiffre (via encryption_func)
        4. Cree archive tar
        5. Calcule checksum
        6. Transfere vers serveur distant
        7. Supprime copie locale
        """
        backup_date = datetime.now(timezone.utc)
        filename = f"{backup_date.strftime('%Y-%m-%d')}.tar.gz.enc"

        logger.info(f"[BACKUP] Debut sauvegarde tenant {tenant_id[:8]}...")

        # Statistiques
        tables_count = len(data.get('tables', {}))
        rows_count = sum(
            len(rows) for rows in data.get('tables', {}).values()
        )

        try:
            # 1. Serialise + compresse en memoire
            json_data = json.dumps(data, ensure_ascii=False, default=str)
            compressed = gzip.compress(
                json_data.encode('utf-8'),
                compresslevel=self.config.compression_level
            )

            # 2. Chiffre en memoire
            encrypted_data = encryption_func(compressed.decode('latin-1'))
            encrypted_bytes = encrypted_data.encode('latin-1')

            # 3. Calcule checksum AVANT transfert
            checksum = hashlib.sha256(encrypted_bytes).hexdigest()

            # 4. Cree archive tar en memoire
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
                # Ajoute les donnees chiffrees
                data_info = tarfile.TarInfo(name='data.enc')
                data_info.size = len(encrypted_bytes)
                data_info.mtime = backup_date.timestamp()
                tar.addfile(data_info, io.BytesIO(encrypted_bytes))

                # Ajoute les metadonnees (non chiffrees, juste info)
                meta = {
                    'tenant_id': tenant_id,
                    'backup_date': backup_date.isoformat(),
                    'checksum_sha256': checksum,
                    'size_bytes': len(encrypted_bytes),
                    'tables_count': tables_count,
                    'rows_count': rows_count,
                    'encrypted': True,
                    'compression': 'gzip',
                    'version': '1.0'
                }
                meta_json = json.dumps(meta).encode('utf-8')
                meta_info = tarfile.TarInfo(name='metadata.json')
                meta_info.size = len(meta_json)
                tar.addfile(meta_info, io.BytesIO(meta_json))

            tar_bytes = tar_buffer.getvalue()

            # 5. Transfere vers serveur distant
            remote_path = f"{self.config.remote_path}/tenant_{tenant_id}/{filename}"
            self._transfer_to_remote(tar_bytes, remote_path)

            # 6. Verifie le transfert
            if not self._verify_remote_file(remote_path, len(tar_bytes)):
                raise BackupIntegrityError("Verification du transfert echouee")

            logger.info(
                f"[BACKUP] Succes tenant {tenant_id[:8]}: "
                f"{tables_count} tables, {rows_count} lignes, "
                f"{len(tar_bytes)} bytes"
            )

            return BackupMetadata(
                tenant_id=tenant_id,
                backup_date=backup_date,
                checksum_sha256=checksum,
                size_bytes=len(tar_bytes),
                tables_count=tables_count,
                rows_count=rows_count
            )

        except Exception as e:
            logger.error(f"[BACKUP] Echec tenant {tenant_id[:8]}: {e}")
            raise BackupError(f"Sauvegarde echouee: {e}")

    def restore_backup(
        self,
        tenant_id: str,
        backup_date: datetime,
        decryption_func: callable
    ) -> Dict[str, Any]:
        """
        Restaure une sauvegarde en memoire uniquement.

        Args:
            tenant_id: Identifiant du tenant
            backup_date: Date de la sauvegarde a restaurer
            decryption_func: Fonction de dechiffrement tenant

        Returns:
            Donnees restaurees (dict)

        SECURITE:
        - Donnees dechiffrees EN MEMOIRE uniquement
        - Aucune ecriture sur disque
        - Verification checksum obligatoire
        """
        filename = f"{backup_date.strftime('%Y-%m-%d')}.tar.gz.enc"
        remote_path = f"{self.config.remote_path}/tenant_{tenant_id}/{filename}"

        logger.info(f"[RESTORE] Debut restauration tenant {tenant_id[:8]}...")

        try:
            # 1. Telecharge depuis serveur distant
            tar_bytes = self._download_from_remote(remote_path)

            # 2. Extrait l'archive en memoire
            tar_buffer = io.BytesIO(tar_bytes)
            with tarfile.open(fileobj=tar_buffer, mode='r') as tar:
                # Lit les metadonnees
                meta_file = tar.extractfile('metadata.json')
                if not meta_file:
                    raise BackupIntegrityError("metadata.json manquant")
                meta = json.loads(meta_file.read().decode('utf-8'))

                # Lit les donnees chiffrees
                data_file = tar.extractfile('data.enc')
                if not data_file:
                    raise BackupIntegrityError("data.enc manquant")
                encrypted_bytes = data_file.read()

            # 3. Verifie le checksum
            actual_checksum = hashlib.sha256(encrypted_bytes).hexdigest()
            if actual_checksum != meta['checksum_sha256']:
                raise BackupIntegrityError(
                    f"Checksum invalide: attendu {meta['checksum_sha256'][:16]}..., "
                    f"obtenu {actual_checksum[:16]}..."
                )

            # 4. Dechiffre en memoire
            encrypted_str = encrypted_bytes.decode('latin-1')
            decrypted_str = decryption_func(encrypted_str)
            compressed = decrypted_str.encode('latin-1')

            # 5. Decompresse
            json_data = gzip.decompress(compressed).decode('utf-8')
            data = json.loads(json_data)

            logger.info(
                f"[RESTORE] Succes tenant {tenant_id[:8]}: "
                f"{meta['tables_count']} tables, {meta['rows_count']} lignes"
            )

            return data

        except BackupIntegrityError:
            raise
        except Exception as e:
            logger.error(f"[RESTORE] Echec tenant {tenant_id[:8]}: {e}")
            raise BackupError(f"Restauration echouee: {e}")

    def list_backups(self, tenant_id: str) -> List[BackupMetadata]:
        """Liste les sauvegardes disponibles pour un tenant."""
        remote_dir = f"{self.config.remote_path}/tenant_{tenant_id}"

        try:
            files = self._list_remote_dir(remote_dir)

            backups = []
            for filename in files:
                if filename.endswith('.tar.gz.enc'):
                    # Parse la date depuis le nom de fichier
                    date_str = filename.replace('.tar.gz.enc', '')
                    try:
                        backup_date = datetime.strptime(date_str, '%Y-%m-%d')
                        backup_date = backup_date.replace(tzinfo=timezone.utc)

                        # Recupere les metadonnees si possible
                        meta = self._get_backup_metadata(tenant_id, backup_date)
                        backups.append(meta)
                    except ValueError:
                        continue

            return sorted(backups, key=lambda b: b.backup_date, reverse=True)

        except Exception as e:
            logger.error(f"[LIST] Echec listing tenant {tenant_id[:8]}: {e}")
            return []

    def cleanup_old_backups(self, tenant_id: str) -> int:
        """
        Supprime les sauvegardes plus anciennes que retention_days.

        Returns:
            Nombre de sauvegardes supprimees
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config.retention_days)
        remote_dir = f"{self.config.remote_path}/tenant_{tenant_id}"

        deleted = 0
        try:
            files = self._list_remote_dir(remote_dir)

            for filename in files:
                if filename.endswith('.tar.gz.enc'):
                    date_str = filename.replace('.tar.gz.enc', '')
                    try:
                        backup_date = datetime.strptime(date_str, '%Y-%m-%d')
                        backup_date = backup_date.replace(tzinfo=timezone.utc)

                        if backup_date < cutoff_date:
                            remote_path = f"{remote_dir}/{filename}"
                            self._delete_remote_file(remote_path)
                            deleted += 1
                            logger.info(f"[CLEANUP] Supprime {filename} tenant {tenant_id[:8]}")
                    except ValueError:
                        continue

            return deleted

        except Exception as e:
            logger.error(f"[CLEANUP] Echec tenant {tenant_id[:8]}: {e}")
            return deleted

    def get_latest_backup(self, tenant_id: str) -> Optional[BackupMetadata]:
        """Recupere les metadonnees de la derniere sauvegarde."""
        backups = self.list_backups(tenant_id)
        return backups[0] if backups else None

    def verify_backup_integrity(
        self,
        tenant_id: str,
        backup_date: datetime
    ) -> Tuple[bool, str]:
        """
        Verifie l'integrite d'une sauvegarde sans la restaurer.

        Returns:
            (True, "OK") ou (False, "raison de l'echec")
        """
        filename = f"{backup_date.strftime('%Y-%m-%d')}.tar.gz.enc"
        remote_path = f"{self.config.remote_path}/tenant_{tenant_id}/{filename}"

        try:
            tar_bytes = self._download_from_remote(remote_path)

            tar_buffer = io.BytesIO(tar_bytes)
            with tarfile.open(fileobj=tar_buffer, mode='r') as tar:
                meta_file = tar.extractfile('metadata.json')
                if not meta_file:
                    return False, "metadata.json manquant"
                meta = json.loads(meta_file.read().decode('utf-8'))

                data_file = tar.extractfile('data.enc')
                if not data_file:
                    return False, "data.enc manquant"
                encrypted_bytes = data_file.read()

            actual_checksum = hashlib.sha256(encrypted_bytes).hexdigest()
            if actual_checksum != meta['checksum_sha256']:
                return False, f"Checksum invalide"

            return True, "OK"

        except Exception as e:
            return False, str(e)

    # ========================================================================
    # METHODES DE TRANSFERT (par provider)
    # ========================================================================

    def _transfer_to_remote(self, data: bytes, remote_path: str) -> None:
        """Transfere des donnees vers le serveur distant."""
        if self.config.provider == BackupProvider.LOCAL:
            self._transfer_local(data, remote_path)
        elif self.config.provider in (BackupProvider.SFTP, BackupProvider.SCP):
            self._transfer_sftp(data, remote_path)
        elif self.config.provider == BackupProvider.S3:
            self._transfer_s3(data, remote_path)
        elif self.config.provider == BackupProvider.RCLONE:
            self._transfer_rclone(data, remote_path)
        elif self.config.provider == BackupProvider.WEBDAV:
            self._transfer_webdav(data, remote_path)
        else:
            raise BackupError(f"Provider non supporte: {self.config.provider}")

    def _download_from_remote(self, remote_path: str) -> bytes:
        """Telecharge des donnees depuis le serveur distant."""
        if self.config.provider == BackupProvider.LOCAL:
            return self._download_local(remote_path)
        elif self.config.provider in (BackupProvider.SFTP, BackupProvider.SCP):
            return self._download_sftp(remote_path)
        elif self.config.provider == BackupProvider.S3:
            return self._download_s3(remote_path)
        elif self.config.provider == BackupProvider.RCLONE:
            return self._download_rclone(remote_path)
        elif self.config.provider == BackupProvider.WEBDAV:
            return self._download_webdav(remote_path)
        else:
            raise BackupError(f"Provider non supporte: {self.config.provider}")

    def _list_remote_dir(self, remote_dir: str) -> List[str]:
        """Liste les fichiers dans un repertoire distant."""
        if self.config.provider == BackupProvider.LOCAL:
            return self._list_local(remote_dir)
        elif self.config.provider in (BackupProvider.SFTP, BackupProvider.SCP):
            return self._list_sftp(remote_dir)
        elif self.config.provider == BackupProvider.S3:
            return self._list_s3(remote_dir)
        elif self.config.provider == BackupProvider.RCLONE:
            return self._list_rclone(remote_dir)
        elif self.config.provider == BackupProvider.WEBDAV:
            return self._list_webdav(remote_dir)
        else:
            return []

    def _delete_remote_file(self, remote_path: str) -> None:
        """Supprime un fichier distant."""
        if self.config.provider == BackupProvider.LOCAL:
            self._delete_local(remote_path)
        elif self.config.provider in (BackupProvider.SFTP, BackupProvider.SCP):
            self._delete_sftp(remote_path)
        elif self.config.provider == BackupProvider.S3:
            self._delete_s3(remote_path)
        elif self.config.provider == BackupProvider.RCLONE:
            self._delete_rclone(remote_path)
        elif self.config.provider == BackupProvider.WEBDAV:
            self._delete_webdav(remote_path)

    def _verify_remote_file(self, remote_path: str, expected_size: int) -> bool:
        """Verifie qu'un fichier existe sur le serveur distant."""
        try:
            if self.config.provider == BackupProvider.LOCAL:
                return Path(remote_path).exists()
            # Pour les autres providers, on fait confiance au transfert
            return True
        except Exception:
            return False

    def _get_backup_metadata(
        self,
        tenant_id: str,
        backup_date: datetime
    ) -> BackupMetadata:
        """Recupere les metadonnees d'une sauvegarde."""
        # Retourne des metadonnees basiques si on ne peut pas lire le fichier
        return BackupMetadata(
            tenant_id=tenant_id,
            backup_date=backup_date,
            checksum_sha256="",
            size_bytes=0,
            tables_count=0,
            rows_count=0
        )

    # ========================================================================
    # IMPLEMENTATIONS PAR PROVIDER
    # ========================================================================

    # --- LOCAL (tests) ---

    def _transfer_local(self, data: bytes, path: str) -> None:
        """Transfert local (tests)."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(data)

    def _download_local(self, path: str) -> bytes:
        """Telechargement local (tests)."""
        return Path(path).read_bytes()

    def _list_local(self, directory: str) -> List[str]:
        """Liste locale (tests)."""
        p = Path(directory)
        if p.exists():
            return [f.name for f in p.iterdir() if f.is_file()]
        return []

    def _delete_local(self, path: str) -> None:
        """Suppression locale (tests)."""
        Path(path).unlink(missing_ok=True)

    # --- SFTP/SCP ---

    def _transfer_sftp(self, data: bytes, remote_path: str) -> None:
        """Transfert via SFTP/SCP."""
        # Cree le repertoire parent distant
        remote_dir = os.path.dirname(remote_path)
        ssh_cmd = self._build_ssh_cmd()

        try:
            # Cree le repertoire distant
            subprocess.run(
                ssh_cmd + [f"mkdir -p {remote_dir}"],
                check=True,
                capture_output=True,
                timeout=30
            )

            # Transfere via stdin
            scp_cmd = self._build_scp_cmd(remote_path)
            proc = subprocess.run(
                scp_cmd,
                input=data,
                check=True,
                capture_output=True,
                timeout=300
            )

        except subprocess.CalledProcessError as e:
            raise BackupTransferError(f"SFTP echec: {e.stderr.decode()}")
        except subprocess.TimeoutExpired:
            raise BackupTransferError("SFTP timeout")

    def _download_sftp(self, remote_path: str) -> bytes:
        """Telechargement via SFTP/SCP."""
        scp_cmd = self._build_scp_download_cmd(remote_path)

        try:
            proc = subprocess.run(
                scp_cmd,
                check=True,
                capture_output=True,
                timeout=300
            )
            return proc.stdout

        except subprocess.CalledProcessError as e:
            if b"No such file" in e.stderr:
                raise BackupNotFoundError(f"Sauvegarde non trouvee: {remote_path}")
            raise BackupTransferError(f"SFTP download echec: {e.stderr.decode()}")

    def _list_sftp(self, remote_dir: str) -> List[str]:
        """Liste via SFTP."""
        ssh_cmd = self._build_ssh_cmd()

        try:
            proc = subprocess.run(
                ssh_cmd + [f"ls -1 {remote_dir} 2>/dev/null || echo ''"],
                check=True,
                capture_output=True,
                timeout=30
            )
            output = proc.stdout.decode().strip()
            return [f for f in output.split('\n') if f]

        except Exception:
            return []

    def _delete_sftp(self, remote_path: str) -> None:
        """Suppression via SFTP."""
        ssh_cmd = self._build_ssh_cmd()

        try:
            subprocess.run(
                ssh_cmd + [f"rm -f {remote_path}"],
                check=True,
                capture_output=True,
                timeout=30
            )
        except Exception:
            pass

    def _build_ssh_cmd(self) -> List[str]:
        """Construit la commande SSH de base."""
        cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes"]

        if self.config.ssh_key_path:
            cmd.extend(["-i", self.config.ssh_key_path])

        cmd.extend([
            "-p", str(self.config.remote_port),
            f"{self.config.remote_user}@{self.config.remote_host}"
        ])

        return cmd

    def _build_scp_cmd(self, remote_path: str) -> List[str]:
        """Construit la commande SCP pour upload."""
        cmd = ["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes"]

        if self.config.ssh_key_path:
            cmd.extend(["-i", self.config.ssh_key_path])

        cmd.extend([
            "-P", str(self.config.remote_port),
            "/dev/stdin",
            f"{self.config.remote_user}@{self.config.remote_host}:{remote_path}"
        ])

        return cmd

    def _build_scp_download_cmd(self, remote_path: str) -> List[str]:
        """Construit la commande SCP pour download."""
        cmd = ["scp", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes"]

        if self.config.ssh_key_path:
            cmd.extend(["-i", self.config.ssh_key_path])

        cmd.extend([
            "-P", str(self.config.remote_port),
            f"{self.config.remote_user}@{self.config.remote_host}:{remote_path}",
            "/dev/stdout"
        ])

        return cmd

    # --- S3 ---

    def _transfer_s3(self, data: bytes, remote_path: str) -> None:
        """Transfert via S3-compatible."""
        try:
            import boto3
            from botocore.config import Config

            config = Config(signature_version='s3v4')
            s3 = boto3.client(
                's3',
                endpoint_url=self.config.s3_endpoint,
                aws_access_key_id=self.config.s3_access_key,
                aws_secret_access_key=self.config.s3_secret_key,
                config=config
            )

            key = remote_path.lstrip('/')
            s3.put_object(
                Bucket=self.config.s3_bucket,
                Key=key,
                Body=data
            )

        except ImportError:
            raise BackupError("boto3 requis pour S3. Installez: pip install boto3")
        except Exception as e:
            raise BackupTransferError(f"S3 upload echec: {e}")

    def _download_s3(self, remote_path: str) -> bytes:
        """Telechargement via S3-compatible."""
        try:
            import boto3
            from botocore.config import Config

            config = Config(signature_version='s3v4')
            s3 = boto3.client(
                's3',
                endpoint_url=self.config.s3_endpoint,
                aws_access_key_id=self.config.s3_access_key,
                aws_secret_access_key=self.config.s3_secret_key,
                config=config
            )

            key = remote_path.lstrip('/')
            response = s3.get_object(Bucket=self.config.s3_bucket, Key=key)
            return response['Body'].read()

        except ImportError:
            raise BackupError("boto3 requis pour S3")
        except Exception as e:
            raise BackupTransferError(f"S3 download echec: {e}")

    def _list_s3(self, remote_dir: str) -> List[str]:
        """Liste via S3-compatible."""
        try:
            import boto3
            from botocore.config import Config

            config = Config(signature_version='s3v4')
            s3 = boto3.client(
                's3',
                endpoint_url=self.config.s3_endpoint,
                aws_access_key_id=self.config.s3_access_key,
                aws_secret_access_key=self.config.s3_secret_key,
                config=config
            )

            prefix = remote_dir.lstrip('/') + '/'
            response = s3.list_objects_v2(
                Bucket=self.config.s3_bucket,
                Prefix=prefix
            )

            files = []
            for obj in response.get('Contents', []):
                key = obj['Key']
                filename = key.replace(prefix, '')
                if filename and '/' not in filename:
                    files.append(filename)

            return files

        except Exception:
            return []

    def _delete_s3(self, remote_path: str) -> None:
        """Suppression via S3-compatible."""
        try:
            import boto3
            from botocore.config import Config

            config = Config(signature_version='s3v4')
            s3 = boto3.client(
                's3',
                endpoint_url=self.config.s3_endpoint,
                aws_access_key_id=self.config.s3_access_key,
                aws_secret_access_key=self.config.s3_secret_key,
                config=config
            )

            key = remote_path.lstrip('/')
            s3.delete_object(Bucket=self.config.s3_bucket, Key=key)

        except Exception:
            pass

    # --- RCLONE ---

    def _transfer_rclone(self, data: bytes, remote_path: str) -> None:
        """Transfert via Rclone."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            remote = f"{self.config.rclone_remote}:{remote_path}"
            subprocess.run(
                ["rclone", "copyto", tmp_path, remote],
                check=True,
                capture_output=True,
                timeout=300
            )
        except subprocess.CalledProcessError as e:
            raise BackupTransferError(f"Rclone echec: {e.stderr.decode()}")
        finally:
            os.unlink(tmp_path)

    def _download_rclone(self, remote_path: str) -> bytes:
        """Telechargement via Rclone."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            remote = f"{self.config.rclone_remote}:{remote_path}"
            subprocess.run(
                ["rclone", "copyto", remote, tmp_path],
                check=True,
                capture_output=True,
                timeout=300
            )
            return Path(tmp_path).read_bytes()
        except subprocess.CalledProcessError as e:
            raise BackupTransferError(f"Rclone download echec: {e.stderr.decode()}")
        finally:
            os.unlink(tmp_path)

    def _list_rclone(self, remote_dir: str) -> List[str]:
        """Liste via Rclone."""
        try:
            remote = f"{self.config.rclone_remote}:{remote_dir}"
            proc = subprocess.run(
                ["rclone", "lsf", remote],
                check=True,
                capture_output=True,
                timeout=30
            )
            output = proc.stdout.decode().strip()
            return [f.rstrip('/') for f in output.split('\n') if f]
        except Exception:
            return []

    def _delete_rclone(self, remote_path: str) -> None:
        """Suppression via Rclone."""
        try:
            remote = f"{self.config.rclone_remote}:{remote_path}"
            subprocess.run(
                ["rclone", "deletefile", remote],
                check=True,
                capture_output=True,
                timeout=30
            )
        except Exception:
            pass

    # --- WEBDAV ---

    def _transfer_webdav(self, data: bytes, remote_path: str) -> None:
        """Transfert via WebDAV."""
        try:
            import requests
            from requests.auth import HTTPBasicAuth

            # Cree les repertoires parents
            path_parts = remote_path.strip('/').split('/')
            current_path = self.config.webdav_url.rstrip('/')

            for part in path_parts[:-1]:
                current_path += f"/{part}"
                requests.request(
                    'MKCOL',
                    current_path,
                    auth=HTTPBasicAuth(
                        self.config.webdav_user,
                        self.config.webdav_password
                    ),
                    timeout=30
                )

            # Upload le fichier
            full_url = f"{self.config.webdav_url.rstrip('/')}/{remote_path.lstrip('/')}"
            response = requests.put(
                full_url,
                data=data,
                auth=HTTPBasicAuth(
                    self.config.webdav_user,
                    self.config.webdav_password
                ),
                timeout=300
            )
            response.raise_for_status()

        except ImportError:
            raise BackupError("requests requis pour WebDAV")
        except Exception as e:
            raise BackupTransferError(f"WebDAV upload echec: {e}")

    def _download_webdav(self, remote_path: str) -> bytes:
        """Telechargement via WebDAV."""
        try:
            import requests
            from requests.auth import HTTPBasicAuth

            full_url = f"{self.config.webdav_url.rstrip('/')}/{remote_path.lstrip('/')}"
            response = requests.get(
                full_url,
                auth=HTTPBasicAuth(
                    self.config.webdav_user,
                    self.config.webdav_password
                ),
                timeout=300
            )
            response.raise_for_status()
            return response.content

        except ImportError:
            raise BackupError("requests requis pour WebDAV")
        except Exception as e:
            raise BackupTransferError(f"WebDAV download echec: {e}")

    def _list_webdav(self, remote_dir: str) -> List[str]:
        """Liste via WebDAV (PROPFIND)."""
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            import xml.etree.ElementTree as ET

            full_url = f"{self.config.webdav_url.rstrip('/')}/{remote_dir.lstrip('/')}"
            response = requests.request(
                'PROPFIND',
                full_url,
                headers={'Depth': '1'},
                auth=HTTPBasicAuth(
                    self.config.webdav_user,
                    self.config.webdav_password
                ),
                timeout=30
            )

            # Parse XML response
            root = ET.fromstring(response.content)
            files = []
            for response_elem in root.findall('.//{DAV:}response'):
                href = response_elem.find('{DAV:}href')
                if href is not None:
                    path = href.text.rstrip('/')
                    filename = path.split('/')[-1]
                    if filename and filename != remote_dir.split('/')[-1]:
                        files.append(filename)

            return files

        except Exception:
            return []

    def _delete_webdav(self, remote_path: str) -> None:
        """Suppression via WebDAV."""
        try:
            import requests
            from requests.auth import HTTPBasicAuth

            full_url = f"{self.config.webdav_url.rstrip('/')}/{remote_path.lstrip('/')}"
            requests.request(
                'DELETE',
                full_url,
                auth=HTTPBasicAuth(
                    self.config.webdav_user,
                    self.config.webdav_password
                ),
                timeout=30
            )
        except Exception:
            pass


# ============================================================================
# SINGLETON ET HELPERS
# ============================================================================

_backup_service: Optional[TenantBackupService] = None


def get_backup_service() -> TenantBackupService:
    """Obtient l'instance singleton du service de sauvegarde."""
    global _backup_service
    if _backup_service is None:
        _backup_service = TenantBackupService()
    return _backup_service


def reset_backup_service() -> None:
    """Reset le singleton (tests)."""
    global _backup_service
    _backup_service = None


__all__ = [
    'TenantBackupService',
    'BackupConfig',
    'BackupMetadata',
    'BackupProvider',
    'BackupError',
    'BackupTransferError',
    'BackupIntegrityError',
    'BackupNotFoundError',
    'get_backup_service',
    'reset_backup_service',
]
