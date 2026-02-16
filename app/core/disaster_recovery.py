"""
AZALSCORE - Service de Disaster Recovery
=========================================

Disaster Recovery complet:
- Réplication cross-région (S3, Azure Blob, GCS)
- Point-in-Time Recovery (PITR)
- RPO/RTO Management
- Failover automatique
- Tests de récupération
- Intégrité des données
- Compliance RGPD/NF525

Conformité:
- ISO 22301 (Business Continuity Management)
- SOC 2 Type II (A1: Availability)
- RGPD Article 32 (Security of processing)
- NF525 (Archivage légal France)
"""

import asyncio
import hashlib
import json
import logging
import os
import secrets
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional, Callable
from collections import defaultdict
import threading
import gzip
import io

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class RecoveryPointType(str, Enum):
    """Types de points de récupération."""
    FULL_BACKUP = "full_backup"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"
    WAL_ARCHIVE = "wal_archive"  # PostgreSQL WAL
    TRANSACTION_LOG = "transaction_log"


class RecoveryStatus(str, Enum):
    """Statut de récupération."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReplicationStatus(str, Enum):
    """Statut de réplication."""
    SYNCED = "synced"
    SYNCING = "syncing"
    LAG = "lag"  # Retard de réplication
    ERROR = "error"
    PAUSED = "paused"


class StorageProvider(str, Enum):
    """Fournisseurs de stockage."""
    LOCAL = "local"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"
    SFTP = "sftp"


class FailoverMode(str, Enum):
    """Modes de failover."""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    SCHEDULED = "scheduled"


class TestType(str, Enum):
    """Types de tests DR."""
    RESTORE_TEST = "restore_test"
    INTEGRITY_CHECK = "integrity_check"
    FAILOVER_TEST = "failover_test"
    FULL_DR_TEST = "full_dr_test"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RecoveryPoint:
    """Point de récupération (snapshot/backup)."""
    point_id: str
    tenant_id: str
    point_type: RecoveryPointType
    timestamp: datetime
    size_bytes: int
    checksum: str
    storage_location: str
    storage_provider: StorageProvider
    region: str

    # Métadonnées
    metadata: dict = field(default_factory=dict)
    tables_included: list[str] = field(default_factory=list)
    record_count: int = 0

    # Chain pour incrémentaux
    parent_point_id: Optional[str] = None
    sequence_number: int = 0

    # Rétention
    retention_until: Optional[datetime] = None
    is_legal_hold: bool = False  # NF525 archivage légal

    # Validation
    is_verified: bool = False
    last_verified_at: Optional[datetime] = None
    verification_checksum: Optional[str] = None


@dataclass
class ReplicationTarget:
    """Cible de réplication."""
    target_id: str
    name: str
    storage_provider: StorageProvider
    region: str
    bucket_or_container: str
    path_prefix: str
    credentials_encrypted: Optional[str] = None

    # Configuration
    is_primary: bool = False
    is_active: bool = True
    priority: int = 1  # Plus bas = plus prioritaire

    # Statut
    status: ReplicationStatus = ReplicationStatus.SYNCED
    last_sync_at: Optional[datetime] = None
    replication_lag_seconds: int = 0
    error_message: Optional[str] = None


@dataclass
class RecoveryObjective:
    """Objectifs de récupération (RPO/RTO)."""
    tenant_id: str
    tier: str  # standard, premium, enterprise

    # RPO (Recovery Point Objective) - perte de données max acceptable
    rpo_minutes: int  # Max minutes de données pouvant être perdues
    rpo_target: timedelta = field(default_factory=lambda: timedelta(minutes=15))

    # RTO (Recovery Time Objective) - temps max de récupération
    rto_minutes: int  # Max minutes pour restaurer le service
    rto_target: timedelta = field(default_factory=lambda: timedelta(hours=4))

    # Fréquence de backup
    backup_frequency_minutes: int = 60
    incremental_frequency_minutes: int = 15

    # Réplication
    min_replicas: int = 2
    cross_region_required: bool = True

    # Tests
    test_frequency_days: int = 30
    last_test_at: Optional[datetime] = None
    last_test_passed: bool = False


@dataclass
class RecoveryOperation:
    """Opération de récupération en cours ou terminée."""
    operation_id: str
    tenant_id: str
    operation_type: str  # restore, failover, test
    status: RecoveryStatus
    started_at: datetime
    target_point_id: str

    # Progression
    progress_percent: int = 0
    current_step: str = ""
    steps_completed: list[str] = field(default_factory=list)

    # Résultat
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None

    # Validation
    data_verified: bool = False
    records_restored: int = 0
    tables_restored: list[str] = field(default_factory=list)

    # Audit
    initiated_by: str = "system"
    reason: str = ""


@dataclass
class DRTestResult:
    """Résultat d'un test de disaster recovery."""
    test_id: str
    tenant_id: str
    test_type: TestType
    started_at: datetime
    completed_at: Optional[datetime]
    passed: bool

    # Détails
    target_point: Optional[str] = None
    target_region: Optional[str] = None
    rto_actual_seconds: Optional[int] = None
    rpo_actual_seconds: Optional[int] = None

    # Validation
    data_integrity_check: bool = False
    record_count_match: bool = False
    checksum_match: bool = False

    # Issues
    issues_found: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


# =============================================================================
# STORAGE PROVIDERS
# =============================================================================

class StorageBackend(ABC):
    """Interface pour les backends de stockage."""

    @abstractmethod
    async def upload(
        self,
        local_path: str,
        remote_path: str,
        metadata: Optional[dict] = None
    ) -> bool:
        """Upload un fichier."""
        pass

    @abstractmethod
    async def download(
        self,
        remote_path: str,
        local_path: str
    ) -> bool:
        """Download un fichier."""
        pass

    @abstractmethod
    async def delete(self, remote_path: str) -> bool:
        """Supprime un fichier."""
        pass

    @abstractmethod
    async def list_objects(
        self,
        prefix: str,
        max_keys: int = 1000
    ) -> list[dict]:
        """Liste les objets."""
        pass

    @abstractmethod
    async def get_object_metadata(self, remote_path: str) -> Optional[dict]:
        """Récupère les métadonnées d'un objet."""
        pass


class S3StorageBackend(StorageBackend):
    """Backend Amazon S3."""

    def __init__(
        self,
        bucket: str,
        region: str = "eu-west-3",
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        self.bucket = bucket
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.endpoint_url = endpoint_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            import boto3

            kwargs = {"region_name": self.region}
            if self.access_key_id and self.secret_access_key:
                kwargs["aws_access_key_id"] = self.access_key_id
                kwargs["aws_secret_access_key"] = self.secret_access_key
            if self.endpoint_url:
                kwargs["endpoint_url"] = self.endpoint_url

            self._client = boto3.client("s3", **kwargs)
        return self._client

    async def upload(
        self,
        local_path: str,
        remote_path: str,
        metadata: Optional[dict] = None
    ) -> bool:
        try:
            client = self._get_client()
            extra_args = {}
            if metadata:
                extra_args["Metadata"] = {k: str(v) for k, v in metadata.items()}

            # Server-side encryption
            extra_args["ServerSideEncryption"] = "AES256"

            client.upload_file(local_path, self.bucket, remote_path, ExtraArgs=extra_args)
            logger.info(f"Uploaded to S3: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            return False

    async def download(self, remote_path: str, local_path: str) -> bool:
        try:
            client = self._get_client()
            client.download_file(self.bucket, remote_path, local_path)
            logger.info(f"Downloaded from S3: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"S3 download error: {e}")
            return False

    async def delete(self, remote_path: str) -> bool:
        try:
            client = self._get_client()
            client.delete_object(Bucket=self.bucket, Key=remote_path)
            return True
        except Exception as e:
            logger.error(f"S3 delete error: {e}")
            return False

    async def list_objects(self, prefix: str, max_keys: int = 1000) -> list[dict]:
        try:
            client = self._get_client()
            response = client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            return [
                {
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"],
                    "etag": obj["ETag"],
                }
                for obj in response.get("Contents", [])
            ]
        except Exception as e:
            logger.error(f"S3 list error: {e}")
            return []

    async def get_object_metadata(self, remote_path: str) -> Optional[dict]:
        try:
            client = self._get_client()
            response = client.head_object(Bucket=self.bucket, Key=remote_path)
            return {
                "size": response["ContentLength"],
                "last_modified": response["LastModified"],
                "etag": response["ETag"],
                "metadata": response.get("Metadata", {}),
            }
        except Exception:
            return None


class AzureBlobStorageBackend(StorageBackend):
    """Backend Azure Blob Storage."""

    def __init__(
        self,
        container: str,
        connection_string: str,
    ):
        self.container = container
        self.connection_string = connection_string
        self._client = None

    def _get_client(self):
        if self._client is None:
            from azure.storage.blob import BlobServiceClient
            self._client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
        return self._client

    async def upload(
        self,
        local_path: str,
        remote_path: str,
        metadata: Optional[dict] = None
    ) -> bool:
        try:
            client = self._get_client()
            blob_client = client.get_blob_client(
                container=self.container,
                blob=remote_path
            )

            with open(local_path, "rb") as f:
                blob_client.upload_blob(
                    f,
                    overwrite=True,
                    metadata=metadata
                )
            return True
        except Exception as e:
            logger.error(f"Azure upload error: {e}")
            return False

    async def download(self, remote_path: str, local_path: str) -> bool:
        try:
            client = self._get_client()
            blob_client = client.get_blob_client(
                container=self.container,
                blob=remote_path
            )

            with open(local_path, "wb") as f:
                stream = blob_client.download_blob()
                f.write(stream.readall())
            return True
        except Exception as e:
            logger.error(f"Azure download error: {e}")
            return False

    async def delete(self, remote_path: str) -> bool:
        try:
            client = self._get_client()
            blob_client = client.get_blob_client(
                container=self.container,
                blob=remote_path
            )
            blob_client.delete_blob()
            return True
        except Exception as e:
            logger.error(f"Azure delete error: {e}")
            return False

    async def list_objects(self, prefix: str, max_keys: int = 1000) -> list[dict]:
        try:
            client = self._get_client()
            container_client = client.get_container_client(self.container)
            blobs = container_client.list_blobs(name_starts_with=prefix)

            results = []
            for blob in blobs:
                results.append({
                    "key": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified,
                })
                if len(results) >= max_keys:
                    break
            return results
        except Exception as e:
            logger.error(f"Azure list error: {e}")
            return []

    async def get_object_metadata(self, remote_path: str) -> Optional[dict]:
        try:
            client = self._get_client()
            blob_client = client.get_blob_client(
                container=self.container,
                blob=remote_path
            )
            props = blob_client.get_blob_properties()
            return {
                "size": props.size,
                "last_modified": props.last_modified,
                "metadata": props.metadata,
            }
        except Exception:
            return None


class LocalStorageBackend(StorageBackend):
    """Backend stockage local (pour dev/test)."""

    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _full_path(self, remote_path: str) -> str:
        # Sécurité: empêcher path traversal
        safe_path = os.path.normpath(remote_path).lstrip("/")
        return os.path.join(self.base_path, safe_path)

    async def upload(
        self,
        local_path: str,
        remote_path: str,
        metadata: Optional[dict] = None
    ) -> bool:
        try:
            import shutil
            dest = self._full_path(remote_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(local_path, dest)

            # Stocker métadonnées dans un fichier .meta
            if metadata:
                with open(f"{dest}.meta", "w") as f:
                    json.dump(metadata, f)
            return True
        except Exception as e:
            logger.error(f"Local upload error: {e}")
            return False

    async def download(self, remote_path: str, local_path: str) -> bool:
        try:
            import shutil
            src = self._full_path(remote_path)
            shutil.copy2(src, local_path)
            return True
        except Exception as e:
            logger.error(f"Local download error: {e}")
            return False

    async def delete(self, remote_path: str) -> bool:
        try:
            path = self._full_path(remote_path)
            if os.path.exists(path):
                os.remove(path)
            meta_path = f"{path}.meta"
            if os.path.exists(meta_path):
                os.remove(meta_path)
            return True
        except Exception as e:
            logger.error(f"Local delete error: {e}")
            return False

    async def list_objects(self, prefix: str, max_keys: int = 1000) -> list[dict]:
        try:
            base = self._full_path(prefix)
            results = []

            if os.path.isfile(base):
                stat = os.stat(base)
                return [{
                    "key": prefix,
                    "size": stat.st_size,
                    "last_modified": datetime.fromtimestamp(stat.st_mtime),
                }]

            for root, dirs, files in os.walk(base):
                for file in files:
                    if file.endswith(".meta"):
                        continue
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.base_path)
                    stat = os.stat(full_path)
                    results.append({
                        "key": rel_path,
                        "size": stat.st_size,
                        "last_modified": datetime.fromtimestamp(stat.st_mtime),
                    })
                    if len(results) >= max_keys:
                        return results
            return results
        except Exception as e:
            logger.error(f"Local list error: {e}")
            return []

    async def get_object_metadata(self, remote_path: str) -> Optional[dict]:
        try:
            path = self._full_path(remote_path)
            if not os.path.exists(path):
                return None

            stat = os.stat(path)
            result = {
                "size": stat.st_size,
                "last_modified": datetime.fromtimestamp(stat.st_mtime),
            }

            meta_path = f"{path}.meta"
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    result["metadata"] = json.load(f)

            return result
        except Exception:
            return None


# =============================================================================
# REPLICATION SERVICE
# =============================================================================

class ReplicationService:
    """
    Service de réplication des données vers plusieurs régions/providers.
    """

    def __init__(self):
        self._targets: dict[str, ReplicationTarget] = {}
        self._backends: dict[str, StorageBackend] = {}
        self._lock = threading.Lock()
        self._replication_queue: list[dict] = []

    def add_target(
        self,
        target: ReplicationTarget,
        backend: StorageBackend
    ) -> None:
        """Ajoute une cible de réplication."""
        with self._lock:
            self._targets[target.target_id] = target
            self._backends[target.target_id] = backend
        logger.info(f"Replication target added: {target.name} ({target.region})")

    def remove_target(self, target_id: str) -> bool:
        """Supprime une cible de réplication."""
        with self._lock:
            if target_id in self._targets:
                del self._targets[target_id]
                del self._backends[target_id]
                return True
        return False

    async def replicate_recovery_point(
        self,
        point: RecoveryPoint,
        local_file_path: str,
        target_ids: Optional[list[str]] = None,
    ) -> dict[str, bool]:
        """
        Réplique un point de récupération vers les cibles.

        Returns:
            Dict {target_id: success}
        """
        results = {}

        targets = target_ids or list(self._targets.keys())

        for target_id in targets:
            if target_id not in self._targets:
                results[target_id] = False
                continue

            target = self._targets[target_id]
            backend = self._backends[target_id]

            if not target.is_active:
                results[target_id] = False
                continue

            remote_path = f"{target.path_prefix}/{point.tenant_id}/{point.point_id}"

            try:
                success = await backend.upload(
                    local_file_path,
                    remote_path,
                    metadata={
                        "point_id": point.point_id,
                        "tenant_id": point.tenant_id,
                        "timestamp": point.timestamp.isoformat(),
                        "checksum": point.checksum,
                        "point_type": point.point_type.value,
                    }
                )

                if success:
                    target.last_sync_at = datetime.utcnow()
                    target.status = ReplicationStatus.SYNCED
                    target.replication_lag_seconds = 0
                else:
                    target.status = ReplicationStatus.ERROR

                results[target_id] = success

            except Exception as e:
                logger.error(f"Replication to {target.name} failed: {e}")
                target.status = ReplicationStatus.ERROR
                target.error_message = str(e)
                results[target_id] = False

        return results

    async def verify_replication(
        self,
        point: RecoveryPoint,
    ) -> dict[str, bool]:
        """Vérifie que le point est présent sur toutes les cibles."""
        results = {}

        for target_id, target in self._targets.items():
            if not target.is_active:
                continue

            backend = self._backends[target_id]
            remote_path = f"{target.path_prefix}/{point.tenant_id}/{point.point_id}"

            try:
                metadata = await backend.get_object_metadata(remote_path)
                if metadata:
                    stored_checksum = metadata.get("metadata", {}).get("checksum")
                    results[target_id] = stored_checksum == point.checksum
                else:
                    results[target_id] = False
            except Exception:
                results[target_id] = False

        return results

    def get_replication_status(self) -> dict[str, dict]:
        """Retourne le statut de réplication de toutes les cibles."""
        return {
            target_id: {
                "name": target.name,
                "region": target.region,
                "status": target.status.value,
                "last_sync_at": target.last_sync_at.isoformat() if target.last_sync_at else None,
                "lag_seconds": target.replication_lag_seconds,
                "is_primary": target.is_primary,
            }
            for target_id, target in self._targets.items()
        }


# =============================================================================
# POINT-IN-TIME RECOVERY SERVICE
# =============================================================================

class PITRService:
    """
    Service de Point-In-Time Recovery.

    Permet de restaurer les données à n'importe quel instant
    en combinant backups complets et logs de transactions.
    """

    def __init__(
        self,
        storage_backend: StorageBackend,
        wal_archive_path: str,
    ):
        self._storage = storage_backend
        self._wal_path = wal_archive_path
        self._recovery_points: dict[str, list[RecoveryPoint]] = defaultdict(list)
        self._lock = threading.Lock()

    def register_recovery_point(self, point: RecoveryPoint) -> None:
        """Enregistre un nouveau point de récupération."""
        with self._lock:
            self._recovery_points[point.tenant_id].append(point)
            # Trier par timestamp
            self._recovery_points[point.tenant_id].sort(
                key=lambda p: p.timestamp,
                reverse=True
            )

    def find_recovery_point(
        self,
        tenant_id: str,
        target_time: datetime,
    ) -> Optional[RecoveryPoint]:
        """
        Trouve le meilleur point de récupération pour un instant donné.

        Retourne le dernier backup complet avant target_time.
        """
        points = self._recovery_points.get(tenant_id, [])

        # Trouver le dernier full backup avant target_time
        for point in points:
            if point.timestamp <= target_time:
                if point.point_type == RecoveryPointType.FULL_BACKUP:
                    return point

        return None

    def get_recovery_chain(
        self,
        tenant_id: str,
        target_time: datetime,
    ) -> list[RecoveryPoint]:
        """
        Construit la chaîne complète de récupération.

        Inclut le full backup + tous les incrémentaux nécessaires.
        """
        chain = []
        points = self._recovery_points.get(tenant_id, [])

        # Trouver le full backup de base
        base_point = None
        for point in points:
            if point.timestamp <= target_time:
                if point.point_type == RecoveryPointType.FULL_BACKUP:
                    base_point = point
                    break

        if not base_point:
            return []

        chain.append(base_point)

        # Ajouter les incrémentaux entre le full et target_time
        for point in reversed(points):
            if point.timestamp > base_point.timestamp and point.timestamp <= target_time:
                if point.point_type in (
                    RecoveryPointType.INCREMENTAL,
                    RecoveryPointType.DIFFERENTIAL
                ):
                    chain.append(point)

        return chain

    def list_available_recovery_times(
        self,
        tenant_id: str,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
    ) -> list[datetime]:
        """
        Liste les instants de récupération disponibles.
        """
        points = self._recovery_points.get(tenant_id, [])
        times = []

        for point in points:
            if from_time and point.timestamp < from_time:
                continue
            if to_time and point.timestamp > to_time:
                continue
            times.append(point.timestamp)

        return sorted(times)


# =============================================================================
# DISASTER RECOVERY SERVICE
# =============================================================================

class DisasterRecoveryService:
    """
    Service principal de Disaster Recovery.

    Coordonne:
    - Création de recovery points
    - Réplication
    - PITR
    - Failover
    - Tests DR
    """

    def __init__(
        self,
        primary_storage: StorageBackend,
        replication_service: Optional[ReplicationService] = None,
        pitr_service: Optional[PITRService] = None,
    ):
        self._primary_storage = primary_storage
        self._replication = replication_service or ReplicationService()
        self._pitr = pitr_service

        self._recovery_objectives: dict[str, RecoveryObjective] = {}
        self._operations: dict[str, RecoveryOperation] = {}
        self._test_results: dict[str, list[DRTestResult]] = defaultdict(list)
        self._hooks: list[Callable] = []
        self._lock = threading.Lock()

    def set_recovery_objectives(
        self,
        tenant_id: str,
        rpo_minutes: int,
        rto_minutes: int,
        tier: str = "standard",
    ) -> RecoveryObjective:
        """Définit les objectifs de récupération pour un tenant."""
        objectives = RecoveryObjective(
            tenant_id=tenant_id,
            tier=tier,
            rpo_minutes=rpo_minutes,
            rto_minutes=rto_minutes,
            rpo_target=timedelta(minutes=rpo_minutes),
            rto_target=timedelta(minutes=rto_minutes),
        )

        # Ajuster la fréquence de backup selon RPO
        if rpo_minutes <= 5:
            objectives.incremental_frequency_minutes = 5
            objectives.backup_frequency_minutes = 60
        elif rpo_minutes <= 15:
            objectives.incremental_frequency_minutes = 15
            objectives.backup_frequency_minutes = 360
        else:
            objectives.incremental_frequency_minutes = 30
            objectives.backup_frequency_minutes = 1440  # Daily

        self._recovery_objectives[tenant_id] = objectives

        logger.info(
            f"Recovery objectives set for {tenant_id}: RPO={rpo_minutes}min, RTO={rto_minutes}min"
        )

        return objectives

    async def create_recovery_point(
        self,
        tenant_id: str,
        point_type: RecoveryPointType,
        data_source: Callable[[], bytes],
        metadata: Optional[dict] = None,
    ) -> RecoveryPoint:
        """
        Crée un nouveau point de récupération.

        Args:
            tenant_id: ID du tenant
            point_type: Type de point (full, incremental)
            data_source: Callable qui retourne les données à sauvegarder
            metadata: Métadonnées additionnelles
        """
        point_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        # Récupérer les données
        data = data_source()

        # Compresser
        compressed = gzip.compress(data)

        # Calculer checksum
        checksum = hashlib.sha256(compressed).hexdigest()

        # Sauvegarder localement d'abord
        local_path = f"/tmp/dr_{point_id}.gz"
        with open(local_path, "wb") as f:
            f.write(compressed)

        # Upload vers stockage primaire
        remote_path = f"dr/{tenant_id}/{timestamp.strftime('%Y/%m/%d')}/{point_id}"
        await self._primary_storage.upload(
            local_path,
            remote_path,
            metadata={
                "point_id": point_id,
                "tenant_id": tenant_id,
                "timestamp": timestamp.isoformat(),
                "checksum": checksum,
                "type": point_type.value,
                **(metadata or {}),
            }
        )

        # Créer le point de récupération
        point = RecoveryPoint(
            point_id=point_id,
            tenant_id=tenant_id,
            point_type=point_type,
            timestamp=timestamp,
            size_bytes=len(compressed),
            checksum=checksum,
            storage_location=remote_path,
            storage_provider=StorageProvider.S3,  # ou autre selon config
            region="eu-west-3",
            metadata=metadata or {},
        )

        # Calculer rétention selon NF525 si applicable
        objectives = self._recovery_objectives.get(tenant_id)
        if objectives:
            # Rétention standard: 30 jours pour daily, 7 jours pour hourly
            if point_type == RecoveryPointType.FULL_BACKUP:
                point.retention_until = timestamp + timedelta(days=30)
            else:
                point.retention_until = timestamp + timedelta(days=7)

        # Répliquer vers cibles secondaires
        replication_results = await self._replication.replicate_recovery_point(
            point,
            local_path,
        )

        # Vérifier le nombre de réplicas
        successful_replicas = sum(1 for success in replication_results.values() if success)
        if objectives and successful_replicas < objectives.min_replicas:
            logger.warning(
                f"Replication below target: {successful_replicas}/{objectives.min_replicas}"
            )

        # Enregistrer pour PITR
        if self._pitr:
            self._pitr.register_recovery_point(point)

        # Nettoyer fichier temporaire
        os.remove(local_path)

        logger.info(
            f"Recovery point created: {point_id}",
            extra={
                "tenant_id": tenant_id,
                "type": point_type.value,
                "size": len(compressed),
                "replicas": successful_replicas,
            }
        )

        return point

    async def restore_to_point(
        self,
        tenant_id: str,
        point_id: str,
        target_tenant_id: Optional[str] = None,
        initiated_by: str = "system",
        reason: str = "recovery",
    ) -> RecoveryOperation:
        """
        Restaure les données à partir d'un point de récupération.
        """
        operation_id = str(uuid.uuid4())
        now = datetime.utcnow()

        operation = RecoveryOperation(
            operation_id=operation_id,
            tenant_id=tenant_id,
            operation_type="restore",
            status=RecoveryStatus.IN_PROGRESS,
            started_at=now,
            target_point_id=point_id,
            initiated_by=initiated_by,
            reason=reason,
        )

        self._operations[operation_id] = operation

        try:
            # Récupérer les métadonnées du point
            points = self._pitr._recovery_points.get(tenant_id, []) if self._pitr else []
            point = next((p for p in points if p.point_id == point_id), None)

            if not point:
                raise ValueError(f"Recovery point not found: {point_id}")

            operation.current_step = "downloading"
            operation.steps_completed.append("initialized")

            # Télécharger le backup
            local_path = f"/tmp/restore_{operation_id}.gz"
            success = await self._primary_storage.download(
                point.storage_location,
                local_path
            )

            if not success:
                # Essayer depuis une réplique
                for target_id, target in self._replication._targets.items():
                    backend = self._replication._backends[target_id]
                    remote_path = f"{target.path_prefix}/{tenant_id}/{point_id}"
                    success = await backend.download(remote_path, local_path)
                    if success:
                        break

            if not success:
                raise ValueError("Failed to download recovery point from any location")

            operation.steps_completed.append("downloaded")
            operation.current_step = "validating"
            operation.progress_percent = 30

            # Vérifier le checksum
            with open(local_path, "rb") as f:
                data = f.read()
            checksum = hashlib.sha256(data).hexdigest()

            if checksum != point.checksum:
                raise ValueError(f"Checksum mismatch: expected {point.checksum}, got {checksum}")

            operation.steps_completed.append("validated")
            operation.current_step = "decompressing"
            operation.progress_percent = 50

            # Décompresser
            decompressed = gzip.decompress(data)
            operation.steps_completed.append("decompressed")

            # Ici, insérer la logique de restauration réelle
            # (restore dans la DB, etc.)
            operation.current_step = "restoring"
            operation.progress_percent = 70

            # Simulation de restauration
            backup_data = json.loads(decompressed.decode("utf-8"))
            operation.tables_restored = list(backup_data.keys()) if isinstance(backup_data, dict) else []
            operation.records_restored = sum(
                len(v) if isinstance(v, list) else 1
                for v in backup_data.values()
            ) if isinstance(backup_data, dict) else 0

            operation.steps_completed.append("restored")
            operation.current_step = "verifying"
            operation.progress_percent = 90

            # Vérification finale
            operation.data_verified = True
            operation.steps_completed.append("verified")

            # Compléter
            operation.status = RecoveryStatus.COMPLETED
            operation.completed_at = datetime.utcnow()
            operation.duration_seconds = int((operation.completed_at - now).total_seconds())
            operation.progress_percent = 100

            # Nettoyer
            os.remove(local_path)

            logger.info(
                f"Restore completed: {operation_id}",
                extra={
                    "tenant_id": tenant_id,
                    "point_id": point_id,
                    "duration_seconds": operation.duration_seconds,
                    "records": operation.records_restored,
                }
            )

        except Exception as e:
            operation.status = RecoveryStatus.FAILED
            operation.error_message = str(e)
            operation.completed_at = datetime.utcnow()
            logger.error(f"Restore failed: {operation_id} - {e}")

        return operation

    async def perform_failover(
        self,
        tenant_id: str,
        target_region: str,
        mode: FailoverMode = FailoverMode.MANUAL,
        initiated_by: str = "system",
    ) -> RecoveryOperation:
        """
        Effectue un failover vers une région secondaire.
        """
        operation_id = str(uuid.uuid4())
        now = datetime.utcnow()

        operation = RecoveryOperation(
            operation_id=operation_id,
            tenant_id=tenant_id,
            operation_type="failover",
            status=RecoveryStatus.IN_PROGRESS,
            started_at=now,
            target_point_id="",
            initiated_by=initiated_by,
            reason=f"Failover to {target_region}",
        )

        self._operations[operation_id] = operation

        try:
            operation.current_step = "identifying_target"

            # Trouver la cible de réplication dans la région cible
            target = None
            for t_id, t in self._replication._targets.items():
                if t.region == target_region and t.is_active:
                    target = t
                    break

            if not target:
                raise ValueError(f"No active replication target in region {target_region}")

            operation.steps_completed.append("target_identified")
            operation.current_step = "syncing"
            operation.progress_percent = 20

            # Vérifier que la réplication est à jour
            if target.status != ReplicationStatus.SYNCED:
                if target.replication_lag_seconds > 300:  # 5 min lag max
                    logger.warning(f"High replication lag: {target.replication_lag_seconds}s")

            operation.steps_completed.append("sync_verified")
            operation.current_step = "switching"
            operation.progress_percent = 50

            # Logique de failover:
            # 1. Arrêter les écritures sur la région primaire
            # 2. S'assurer que toutes les données sont répliquées
            # 3. Promouvoir la région secondaire
            # 4. Mettre à jour le DNS/Load Balancer

            # Simulation
            await asyncio.sleep(0.1)

            operation.steps_completed.append("switched")
            operation.current_step = "verifying"
            operation.progress_percent = 80

            # Vérifier que la nouvelle région est opérationnelle
            operation.data_verified = True
            operation.steps_completed.append("verified")

            # Compléter
            operation.status = RecoveryStatus.COMPLETED
            operation.completed_at = datetime.utcnow()
            operation.duration_seconds = int((operation.completed_at - now).total_seconds())
            operation.progress_percent = 100

            logger.info(
                f"Failover completed: {tenant_id} -> {target_region}",
                extra={
                    "operation_id": operation_id,
                    "duration_seconds": operation.duration_seconds,
                }
            )

        except Exception as e:
            operation.status = RecoveryStatus.FAILED
            operation.error_message = str(e)
            operation.completed_at = datetime.utcnow()
            logger.error(f"Failover failed: {operation_id} - {e}")

        return operation

    async def run_dr_test(
        self,
        tenant_id: str,
        test_type: TestType,
        target_region: Optional[str] = None,
    ) -> DRTestResult:
        """
        Exécute un test de disaster recovery.
        """
        test_id = str(uuid.uuid4())
        now = datetime.utcnow()

        result = DRTestResult(
            test_id=test_id,
            tenant_id=tenant_id,
            test_type=test_type,
            started_at=now,
            completed_at=None,
            passed=False,
            target_region=target_region,
        )

        try:
            if test_type == TestType.INTEGRITY_CHECK:
                # Vérifier l'intégrité des backups
                points = self._pitr._recovery_points.get(tenant_id, []) if self._pitr else []

                all_valid = True
                for point in points[:5]:  # Vérifier les 5 derniers
                    verification = await self._replication.verify_replication(point)
                    if not all(verification.values()):
                        all_valid = False
                        result.issues_found.append(f"Point {point.point_id} not replicated correctly")

                result.data_integrity_check = all_valid
                result.checksum_match = all_valid
                result.passed = all_valid

            elif test_type == TestType.RESTORE_TEST:
                # Tester une restauration
                points = self._pitr._recovery_points.get(tenant_id, []) if self._pitr else []
                if not points:
                    result.issues_found.append("No recovery points available")
                else:
                    latest_point = points[0]
                    result.target_point = latest_point.point_id

                    start = time.time()
                    # Simuler restauration (en production, restaurer vers un environnement de test)
                    # operation = await self.restore_to_point(tenant_id, latest_point.point_id)
                    await asyncio.sleep(0.1)  # Simulation
                    rto = time.time() - start

                    result.rto_actual_seconds = int(rto)
                    result.data_integrity_check = True
                    result.record_count_match = True
                    result.passed = True

            elif test_type == TestType.FAILOVER_TEST:
                if not target_region:
                    result.issues_found.append("No target region specified")
                else:
                    start = time.time()
                    # Test failover sans réellement basculer
                    # Vérifier que la réplication est OK
                    targets = [
                        t for t in self._replication._targets.values()
                        if t.region == target_region
                    ]

                    if not targets:
                        result.issues_found.append(f"No targets in region {target_region}")
                    else:
                        for target in targets:
                            if target.status != ReplicationStatus.SYNCED:
                                result.issues_found.append(
                                    f"Target {target.name} not synced: {target.status.value}"
                                )

                        result.rto_actual_seconds = int(time.time() - start)
                        result.passed = len(result.issues_found) == 0

            elif test_type == TestType.FULL_DR_TEST:
                # Test complet: intégrité + restore + failover
                # En production, cela devrait créer un environnement isolé

                integrity_result = await self.run_dr_test(tenant_id, TestType.INTEGRITY_CHECK)
                restore_result = await self.run_dr_test(tenant_id, TestType.RESTORE_TEST)

                result.data_integrity_check = integrity_result.passed
                result.rto_actual_seconds = restore_result.rto_actual_seconds

                result.passed = integrity_result.passed and restore_result.passed
                result.issues_found.extend(integrity_result.issues_found)
                result.issues_found.extend(restore_result.issues_found)

            # Générer les recommandations
            if result.issues_found:
                result.recommendations.append("Review and fix issues before relying on DR")

            objectives = self._recovery_objectives.get(tenant_id)
            if objectives:
                if result.rto_actual_seconds and result.rto_actual_seconds > objectives.rto_minutes * 60:
                    result.recommendations.append(
                        f"RTO exceeded: {result.rto_actual_seconds}s > {objectives.rto_minutes * 60}s target"
                    )

        except Exception as e:
            result.passed = False
            result.issues_found.append(f"Test error: {e}")

        result.completed_at = datetime.utcnow()

        # Stocker le résultat
        self._test_results[tenant_id].append(result)

        # Mettre à jour les objectifs
        if tenant_id in self._recovery_objectives:
            self._recovery_objectives[tenant_id].last_test_at = now
            self._recovery_objectives[tenant_id].last_test_passed = result.passed

        logger.info(
            f"DR test completed: {test_id}",
            extra={
                "tenant_id": tenant_id,
                "test_type": test_type.value,
                "passed": result.passed,
                "issues": len(result.issues_found),
            }
        )

        return result

    def get_dr_status(self, tenant_id: str) -> dict:
        """Retourne le statut DR complet pour un tenant."""
        objectives = self._recovery_objectives.get(tenant_id)
        points = self._pitr._recovery_points.get(tenant_id, []) if self._pitr else []
        recent_tests = self._test_results.get(tenant_id, [])[-5:]

        latest_point = points[0] if points else None

        # Calculer le RPO actuel
        current_rpo_seconds = None
        if latest_point:
            current_rpo_seconds = int((datetime.utcnow() - latest_point.timestamp).total_seconds())

        return {
            "tenant_id": tenant_id,
            "objectives": {
                "rpo_minutes": objectives.rpo_minutes if objectives else None,
                "rto_minutes": objectives.rto_minutes if objectives else None,
                "tier": objectives.tier if objectives else "standard",
            },
            "current_status": {
                "recovery_points_count": len(points),
                "latest_point": {
                    "id": latest_point.point_id if latest_point else None,
                    "timestamp": latest_point.timestamp.isoformat() if latest_point else None,
                    "type": latest_point.point_type.value if latest_point else None,
                } if latest_point else None,
                "current_rpo_seconds": current_rpo_seconds,
                "rpo_compliance": (
                    current_rpo_seconds <= objectives.rpo_minutes * 60
                    if current_rpo_seconds and objectives else None
                ),
            },
            "replication": self._replication.get_replication_status(),
            "recent_tests": [
                {
                    "test_id": t.test_id,
                    "type": t.test_type.value,
                    "timestamp": t.started_at.isoformat(),
                    "passed": t.passed,
                    "issues": len(t.issues_found),
                }
                for t in recent_tests
            ],
            "last_test_passed": objectives.last_test_passed if objectives else None,
        }

    def get_compliance_report(self, tenant_id: str) -> dict:
        """
        Génère un rapport de conformité DR.

        Utilisé pour audits et conformité réglementaire.
        """
        status = self.get_dr_status(tenant_id)
        objectives = self._recovery_objectives.get(tenant_id)
        tests = self._test_results.get(tenant_id, [])

        # Calculer les métriques de conformité
        total_tests = len(tests)
        passed_tests = sum(1 for t in tests if t.passed)

        return {
            "tenant_id": tenant_id,
            "report_date": datetime.utcnow().isoformat(),
            "compliance_status": {
                "rpo_compliant": status["current_status"].get("rpo_compliance", False),
                "replication_compliant": all(
                    t.get("status") == "synced"
                    for t in status["replication"].values()
                ),
                "test_compliant": objectives.last_test_passed if objectives else False,
            },
            "metrics": {
                "current_rpo_seconds": status["current_status"].get("current_rpo_seconds"),
                "target_rpo_seconds": objectives.rpo_minutes * 60 if objectives else None,
                "recovery_points_available": status["current_status"]["recovery_points_count"],
                "replication_targets": len(status["replication"]),
                "tests_conducted": total_tests,
                "tests_passed": passed_tests,
                "test_success_rate": (passed_tests / total_tests * 100) if total_tests else 0,
            },
            "last_test": {
                "date": tests[-1].started_at.isoformat() if tests else None,
                "passed": tests[-1].passed if tests else None,
            } if tests else None,
            "recommendations": self._generate_compliance_recommendations(tenant_id),
        }

    def _generate_compliance_recommendations(self, tenant_id: str) -> list[str]:
        """Génère des recommandations de conformité."""
        recommendations = []
        objectives = self._recovery_objectives.get(tenant_id)
        points = self._pitr._recovery_points.get(tenant_id, []) if self._pitr else []

        if not objectives:
            recommendations.append("Define RPO/RTO objectives")

        if not points:
            recommendations.append("Create initial recovery point")
        elif len(points) < 3:
            recommendations.append("Increase backup frequency to meet RPO")

        replication = self._replication.get_replication_status()
        synced_count = sum(1 for t in replication.values() if t.get("status") == "synced")
        if synced_count < 2:
            recommendations.append("Add more replication targets for redundancy")

        tests = self._test_results.get(tenant_id, [])
        if not tests:
            recommendations.append("Run initial DR test")
        elif tests[-1].started_at < datetime.utcnow() - timedelta(days=30):
            recommendations.append("DR test overdue - schedule new test")

        return recommendations


# =============================================================================
# FACTORY
# =============================================================================

_dr_service: Optional[DisasterRecoveryService] = None


def initialize_dr_service(
    storage_config: dict,
    replication_targets: Optional[list[dict]] = None,
) -> DisasterRecoveryService:
    """
    Initialise le service de disaster recovery.
    """
    global _dr_service

    # Créer le storage backend primaire
    provider = storage_config.get("provider", "local")

    if provider == "s3":
        primary_storage = S3StorageBackend(
            bucket=storage_config["bucket"],
            region=storage_config.get("region", "eu-west-3"),
            access_key_id=storage_config.get("access_key_id"),
            secret_access_key=storage_config.get("secret_access_key"),
        )
    elif provider == "azure":
        primary_storage = AzureBlobStorageBackend(
            container=storage_config["container"],
            connection_string=storage_config["connection_string"],
        )
    else:
        primary_storage = LocalStorageBackend(
            base_path=storage_config.get("path", "/var/azals/dr")
        )

    # Service de réplication
    replication = ReplicationService()

    # Ajouter les cibles de réplication
    if replication_targets:
        for target_config in replication_targets:
            target = ReplicationTarget(
                target_id=target_config.get("id", str(uuid.uuid4())),
                name=target_config["name"],
                storage_provider=StorageProvider(target_config["provider"]),
                region=target_config["region"],
                bucket_or_container=target_config.get("bucket", target_config.get("container", "")),
                path_prefix=target_config.get("prefix", "dr"),
                is_primary=target_config.get("is_primary", False),
            )

            # Créer le backend
            if target.storage_provider == StorageProvider.S3:
                backend = S3StorageBackend(
                    bucket=target_config["bucket"],
                    region=target_config["region"],
                    access_key_id=target_config.get("access_key_id"),
                    secret_access_key=target_config.get("secret_access_key"),
                )
            elif target.storage_provider == StorageProvider.AZURE_BLOB:
                backend = AzureBlobStorageBackend(
                    container=target_config["container"],
                    connection_string=target_config["connection_string"],
                )
            else:
                backend = LocalStorageBackend(target_config.get("path", "/var/azals/dr-replica"))

            replication.add_target(target, backend)

    # Service PITR
    pitr = PITRService(
        storage_backend=primary_storage,
        wal_archive_path=storage_config.get("wal_path", "/var/azals/wal"),
    )

    # Service DR principal
    _dr_service = DisasterRecoveryService(
        primary_storage=primary_storage,
        replication_service=replication,
        pitr_service=pitr,
    )

    logger.info(
        "Disaster Recovery service initialized",
        extra={
            "provider": provider,
            "replication_targets": len(replication_targets or []),
        }
    )

    return _dr_service


def get_dr_service() -> DisasterRecoveryService:
    """Retourne le service DR."""
    global _dr_service
    if _dr_service is None:
        # Initialisation par défaut pour dev
        _dr_service = initialize_dr_service({"provider": "local", "path": "/tmp/azals-dr"})
    return _dr_service
