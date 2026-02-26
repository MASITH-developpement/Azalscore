"""
AZALS MODULE HR_VAULT - Service
=================================

Service metier pour le coffre-fort RH.
Gere le chiffrement, les acces, la conformite RGPD et les signatures.
"""
from __future__ import annotations


import hashlib
import io
import os
import uuid
import zipfile
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional, BinaryIO

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import (
    AccessDeniedException,
    ConsentRequiredException,
    DecryptionException,
    DocumentIntegrityException,
    DocumentNotFoundException,
    EncryptionException,
    EncryptionKeyNotFoundException,
    FileSizeLimitException,
    GDPRExportExpiredException,
    GDPRRequestAlreadyProcessedException,
    GDPRRequestNotFoundException,
    InvalidFileTypeException,
    RetentionPeriodActiveException,
    StorageException,
    VaultNotActivatedException,
)
from .models import (
    AlertType,
    EncryptionAlgorithm,
    GDPRRequestStatus,
    GDPRRequestType,
    RetentionPeriod,
    SignatureStatus,
    VaultAccessLog,
    VaultAccessPermission,
    VaultAccessRole,
    VaultAccessType,
    VaultAlert,
    VaultConsent,
    VaultDocument,
    VaultDocumentCategory,
    VaultDocumentStatus,
    VaultDocumentType,
    VaultDocumentVersion,
    VaultEncryptionKey,
    VaultGDPRRequest,
    VaultStatistics,
)
from .repository import HRVaultRepository
from .schemas import (
    VaultCategoryCreate,
    VaultCategoryResponse,
    VaultCategoryUpdate,
    VaultDashboardStats,
    VaultDocumentFilters,
    VaultDocumentListResponse,
    VaultDocumentResponse,
    VaultDocumentUpload,
    VaultDocumentUpdate,
    VaultEmployeeStats,
    VaultExportRequest,
    VaultExportResponse,
    VaultGDPRRequestCreate,
    VaultGDPRRequestProcess,
    VaultGDPRRequestResponse,
    VaultSignatureRequest,
    VaultSignatureStatus,
)


# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]

# Durees de conservation par type de document
RETENTION_RULES: dict[VaultDocumentType, RetentionPeriod] = {
    VaultDocumentType.PAYSLIP: RetentionPeriod.FIFTY_YEARS,
    VaultDocumentType.PAYSLIP_SUMMARY: RetentionPeriod.FIFTY_YEARS,
    VaultDocumentType.TAX_STATEMENT: RetentionPeriod.TEN_YEARS,
    VaultDocumentType.CONTRACT: RetentionPeriod.LIFETIME_PLUS_5,
    VaultDocumentType.AMENDMENT: RetentionPeriod.LIFETIME_PLUS_5,
    VaultDocumentType.TERMINATION_LETTER: RetentionPeriod.FIFTY_YEARS,
    VaultDocumentType.STC: RetentionPeriod.FIFTY_YEARS,
    VaultDocumentType.WORK_CERTIFICATE: RetentionPeriod.FIFTY_YEARS,
    VaultDocumentType.MEDICAL_APTITUDE: RetentionPeriod.TEN_YEARS,
    VaultDocumentType.ACCIDENT_DECLARATION: RetentionPeriod.TEN_YEARS,
    VaultDocumentType.DIPLOMA: RetentionPeriod.PERMANENT,
    VaultDocumentType.DEGREE: RetentionPeriod.PERMANENT,
    VaultDocumentType.CERTIFICATION: RetentionPeriod.TEN_YEARS,
    VaultDocumentType.RIB: RetentionPeriod.FIVE_YEARS,
    VaultDocumentType.ID_DOCUMENT: RetentionPeriod.FIVE_YEARS,
}


class HRVaultService:
    """
    Service principal du coffre-fort RH.

    Fonctionnalites:
    - Stockage securise et chiffre des documents
    - Gestion des acces par role
    - Historique complet des acces
    - Conformite RGPD (portabilite, droit a l'oubli)
    - Integration signature electronique
    - Alertes et notifications
    """

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: str,
        storage_path: str,
        master_key: bytes,
        current_user_id: Optional[uuid.UUID] = None,
        current_user_role: VaultAccessRole = VaultAccessRole.EMPLOYEE,
    ):
        self.session = session
        self.tenant_id = tenant_id
        self.storage_path = Path(storage_path)
        self.master_key = master_key
        self.current_user_id = current_user_id
        self.current_user_role = current_user_role

        self.repository = HRVaultRepository(session, tenant_id)

        # Creer le repertoire de stockage
        self.storage_path.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # CATEGORIES
    # ========================================================================

    async def list_categories(
        self,
        include_inactive: bool = False,
    ) -> list[VaultCategoryResponse]:
        """Liste les categories de documents."""
        categories = await self.repository.list_categories(include_inactive)
        result = []
        for cat in categories:
            doc_count = await self.repository.count_documents_by_category(cat.id)
            response = VaultCategoryResponse.model_validate(cat)
            response.documents_count = doc_count
            result.append(response)
        return result

    async def get_category(
        self,
        category_id: uuid.UUID,
    ) -> VaultCategoryResponse:
        """Recupere une categorie."""
        category = await self.repository.get_category(category_id)
        if not category:
            raise DocumentNotFoundException(str(category_id))

        doc_count = await self.repository.count_documents_by_category(category_id)
        response = VaultCategoryResponse.model_validate(category)
        response.documents_count = doc_count
        return response

    async def create_category(
        self,
        data: VaultCategoryCreate,
    ) -> VaultCategoryResponse:
        """Cree une nouvelle categorie."""
        self._check_admin_permission()

        category = VaultDocumentCategory(
            code=data.code,
            name=data.name,
            description=data.description,
            icon=data.icon,
            color=data.color,
            default_retention=data.default_retention,
            requires_signature=data.requires_signature,
            is_confidential=data.is_confidential,
            visible_to_employee=data.visible_to_employee,
            sort_order=data.sort_order,
            created_by=self.current_user_id,
        )
        category = await self.repository.create_category(category)
        return VaultCategoryResponse.model_validate(category)

    async def update_category(
        self,
        category_id: uuid.UUID,
        data: VaultCategoryUpdate,
    ) -> VaultCategoryResponse:
        """Met a jour une categorie."""
        self._check_admin_permission()

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = self.current_user_id
        category = await self.repository.update_category(category_id, update_data)
        return VaultCategoryResponse.model_validate(category)

    async def delete_category(self, category_id: uuid.UUID) -> bool:
        """Supprime une categorie."""
        self._check_admin_permission()

        doc_count = await self.repository.count_documents_by_category(category_id)
        if doc_count > 0:
            # Deplacer les documents vers "Autre" ou lever une erreur
            pass

        await self.repository.soft_delete_category(category_id, self.current_user_id)
        return True

    # ========================================================================
    # DOCUMENTS
    # ========================================================================

    async def list_documents(
        self,
        filters: VaultDocumentFilters,
        page: int = 1,
        page_size: int = 50,
    ) -> VaultDocumentListResponse:
        """Liste les documents avec filtres."""
        # Verifier les permissions
        if filters.employee_id:
            self._check_view_permission(filters.employee_id)

        skip = (page - 1) * page_size
        documents, total = await self.repository.list_documents(
            employee_id=filters.employee_id,
            document_type=filters.document_type,
            category_id=filters.category_id,
            status=filters.status,
            signature_status=filters.signature_status,
            date_from=filters.date_from,
            date_to=filters.date_to,
            pay_period=filters.pay_period,
            search=filters.search,
            tags=filters.tags,
            include_deleted=filters.include_deleted,
            skip=skip,
            limit=page_size,
        )

        return VaultDocumentListResponse(
            items=[VaultDocumentResponse.model_validate(d) for d in documents],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )

    async def get_document(
        self,
        document_id: uuid.UUID,
    ) -> VaultDocumentResponse:
        """Recupere un document."""
        document = await self.repository.get_document_with_relations(document_id)
        if not document:
            raise DocumentNotFoundException(str(document_id))

        # Verifier les permissions
        self._check_view_permission(document.employee_id)

        # Logger l'acces
        await self._log_access(
            document_id=document_id,
            employee_id=document.employee_id,
            access_type=VaultAccessType.VIEW,
        )

        # Marquer comme vu si c'est l'employe
        if self.current_user_id == document.employee_id:
            await self.repository.mark_as_viewed(document_id)

        return VaultDocumentResponse.model_validate(document)

    async def upload_document(
        self,
        data: VaultDocumentUpload,
        file_content: bytes,
        file_name: str,
        mime_type: str,
    ) -> VaultDocumentResponse:
        """Upload un nouveau document."""
        self._check_upload_permission(data.employee_id)

        # Validations
        if len(file_content) > MAX_FILE_SIZE:
            raise FileSizeLimitException(len(file_content), MAX_FILE_SIZE)

        if mime_type not in ALLOWED_MIME_TYPES:
            raise InvalidFileTypeException(mime_type, ALLOWED_MIME_TYPES)

        # Determiner la retention
        retention = RETENTION_RULES.get(
            data.document_type,
            RetentionPeriod.FIVE_YEARS,
        )

        # Obtenir ou creer une cle de chiffrement
        encryption_key = await self._get_or_create_encryption_key()

        # Chiffrer le fichier
        encrypted_content, file_hash = await self._encrypt_file(
            file_content,
            encryption_key,
        )

        # Generer le chemin de stockage
        doc_id = uuid.uuid4()
        storage_subpath = self._generate_storage_path(data.employee_id, doc_id)
        full_path = self.storage_path / storage_subpath

        # Sauvegarder le fichier
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_bytes(encrypted_content)
        except Exception as e:
            raise StorageException(str(e), "write")

        # Creer le document
        document = VaultDocument(
            id=doc_id,
            employee_id=data.employee_id,
            document_type=data.document_type,
            category_id=data.category_id,
            title=data.title,
            description=data.description,
            reference=data.reference,
            file_name=file_name,
            file_size=len(file_content),
            mime_type=mime_type,
            storage_path=storage_subpath,
            is_encrypted=True,
            encryption_key_id=encryption_key.id,
            file_hash=file_hash,
            document_date=data.document_date,
            period_start=data.period_start,
            period_end=data.period_end,
            pay_period=data.pay_period,
            gross_salary=data.gross_salary,
            net_salary=data.net_salary,
            retention_period=retention,
            tags=data.tags,
            signature_status=(
                SignatureStatus.PENDING
                if data.requires_signature
                else SignatureStatus.NOT_REQUIRED
            ),
            created_by=self.current_user_id,
        )

        document = await self.repository.create_document(document)

        # Creer la version initiale
        version = VaultDocumentVersion(
            document_id=document.id,
            version_number=1,
            file_name=file_name,
            file_size=len(file_content),
            storage_path=storage_subpath,
            file_hash=file_hash,
            encryption_key_id=encryption_key.id,
            created_by=self.current_user_id,
        )
        await self.repository.create_version(version)

        # Logger l'acces
        await self._log_access(
            document_id=document.id,
            employee_id=document.employee_id,
            access_type=VaultAccessType.EDIT,
        )

        # Notifier l'employe si demande
        if data.notify_employee:
            await self._notify_employee_new_document(document)

        return VaultDocumentResponse.model_validate(document)

    async def download_document(
        self,
        document_id: uuid.UUID,
    ) -> tuple[bytes, str, str]:
        """Telecharge un document (dechiffre)."""
        document = await self.repository.get_document(document_id)
        if not document:
            raise DocumentNotFoundException(str(document_id))

        # Verifier les permissions
        self._check_download_permission(document.employee_id)

        # Lire le fichier
        full_path = self.storage_path / document.storage_path
        try:
            encrypted_content = full_path.read_bytes()
        except FileNotFoundError:
            raise StorageException("Fichier non trouve", "read")

        # Recuperer la cle
        if not document.encryption_key_id:
            raise EncryptionKeyNotFoundException("null")

        encryption_key = await self.repository.get_encryption_key(
            document.encryption_key_id
        )
        if not encryption_key:
            raise EncryptionKeyNotFoundException(str(document.encryption_key_id))

        # Dechiffrer
        try:
            content = await self._decrypt_file(encrypted_content, encryption_key)
        except Exception as e:
            raise DecryptionException(str(e))

        # Verifier l'integrite
        computed_hash = hashlib.sha256(content).hexdigest()
        if computed_hash != document.file_hash:
            raise DocumentIntegrityException(
                str(document_id),
                document.file_hash,
                computed_hash,
            )

        # Logger l'acces
        await self._log_access(
            document_id=document_id,
            employee_id=document.employee_id,
            access_type=VaultAccessType.DOWNLOAD,
        )

        return content, document.file_name, document.mime_type

    async def update_document(
        self,
        document_id: uuid.UUID,
        data: VaultDocumentUpdate,
    ) -> VaultDocumentResponse:
        """Met a jour les metadonnees d'un document."""
        document = await self.repository.get_document(document_id)
        if not document:
            raise DocumentNotFoundException(str(document_id))

        self._check_edit_permission(document.employee_id)

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = self.current_user_id
        document = await self.repository.update_document(document_id, update_data)

        # Logger l'acces
        await self._log_access(
            document_id=document_id,
            employee_id=document.employee_id,
            access_type=VaultAccessType.EDIT,
        )

        return VaultDocumentResponse.model_validate(document)

    async def delete_document(
        self,
        document_id: uuid.UUID,
        reason: Optional[str] = None,
        force: bool = False,
    ) -> bool:
        """Supprime un document (soft delete)."""
        document = await self.repository.get_document(document_id)
        if not document:
            raise DocumentNotFoundException(str(document_id))

        self._check_delete_permission(document.employee_id)

        # Verifier la periode de conservation
        if not force and document.retention_end_date:
            if document.retention_end_date > date.today():
                raise RetentionPeriodActiveException(
                    str(document_id),
                    str(document.retention_end_date),
                )

        await self.repository.soft_delete_document(
            document_id,
            self.current_user_id,
            reason,
        )

        # Logger l'acces
        await self._log_access(
            document_id=document_id,
            employee_id=document.employee_id,
            access_type=VaultAccessType.DELETE,
        )

        return True

    # ========================================================================
    # CHIFFREMENT
    # ========================================================================

    async def _get_or_create_encryption_key(self) -> VaultEncryptionKey:
        """Obtient ou cree une cle de chiffrement."""
        key = await self.repository.get_active_encryption_key()
        if key:
            return key

        # Generer une nouvelle cle AES-256
        raw_key = os.urandom(32)
        encrypted_key = self._encrypt_with_master_key(raw_key)

        key = VaultEncryptionKey(
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            encrypted_key=encrypted_key,
            created_by=self.current_user_id,
        )
        return await self.repository.create_encryption_key(key)

    def _encrypt_with_master_key(self, data: bytes) -> bytes:
        """Chiffre avec la master key."""
        try:
            nonce = os.urandom(12)
            aesgcm = AESGCM(self.master_key)
            ciphertext = aesgcm.encrypt(nonce, data, None)
            return nonce + ciphertext
        except Exception as e:
            raise EncryptionException(str(e))

    def _decrypt_with_master_key(self, encrypted_data: bytes) -> bytes:
        """Dechiffre avec la master key."""
        try:
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]
            aesgcm = AESGCM(self.master_key)
            return aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            raise DecryptionException(str(e))

    async def _encrypt_file(
        self,
        content: bytes,
        key: VaultEncryptionKey,
    ) -> tuple[bytes, str]:
        """Chiffre un fichier et retourne le contenu chiffre et le hash."""
        file_hash = hashlib.sha256(content).hexdigest()

        # Recuperer la cle brute
        raw_key = self._decrypt_with_master_key(key.encrypted_key)

        # Chiffrer le fichier
        try:
            nonce = os.urandom(12)
            aesgcm = AESGCM(raw_key)
            encrypted = aesgcm.encrypt(nonce, content, None)
            return nonce + encrypted, file_hash
        except Exception as e:
            raise EncryptionException(str(e))

    async def _decrypt_file(
        self,
        encrypted_content: bytes,
        key: VaultEncryptionKey,
    ) -> bytes:
        """Dechiffre un fichier."""
        raw_key = self._decrypt_with_master_key(key.encrypted_key)

        try:
            nonce = encrypted_content[:12]
            ciphertext = encrypted_content[12:]
            aesgcm = AESGCM(raw_key)
            return aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            raise DecryptionException(str(e))

    def _generate_storage_path(
        self,
        employee_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> str:
        """Genere un chemin de stockage unique."""
        return f"{self.tenant_id}/{employee_id}/{document_id}"

    # ========================================================================
    # ACCES ET PERMISSIONS
    # ========================================================================

    def _check_admin_permission(self):
        """Verifie les permissions administrateur."""
        if self.current_user_role not in [
            VaultAccessRole.HR_ADMIN,
            VaultAccessRole.HR_DIRECTOR,
            VaultAccessRole.SYSTEM,
        ]:
            raise AccessDeniedException(
                str(self.current_user_id),
                "admin",
                "Seuls les administrateurs RH peuvent effectuer cette action",
            )

    def _check_view_permission(self, employee_id: uuid.UUID):
        """Verifie la permission de visualisation."""
        if self.current_user_id == employee_id:
            return  # L'employe peut voir ses propres documents

        if self.current_user_role in [
            VaultAccessRole.HR_ADMIN,
            VaultAccessRole.HR_DIRECTOR,
            VaultAccessRole.MANAGER,
            VaultAccessRole.LEGAL,
            VaultAccessRole.SYSTEM,
        ]:
            return

        raise AccessDeniedException(
            str(self.current_user_id),
            str(employee_id),
            "view",
        )

    def _check_download_permission(self, employee_id: uuid.UUID):
        """Verifie la permission de telechargement."""
        self._check_view_permission(employee_id)

    def _check_upload_permission(self, employee_id: uuid.UUID):
        """Verifie la permission d'upload."""
        if self.current_user_role in [
            VaultAccessRole.HR_ADMIN,
            VaultAccessRole.HR_DIRECTOR,
            VaultAccessRole.SYSTEM,
        ]:
            return

        raise AccessDeniedException(
            str(self.current_user_id),
            str(employee_id),
            "upload",
        )

    def _check_edit_permission(self, employee_id: uuid.UUID):
        """Verifie la permission d'edition."""
        if self.current_user_role in [
            VaultAccessRole.HR_ADMIN,
            VaultAccessRole.HR_DIRECTOR,
            VaultAccessRole.SYSTEM,
        ]:
            return

        raise AccessDeniedException(
            str(self.current_user_id),
            str(employee_id),
            "edit",
        )

    def _check_delete_permission(self, employee_id: uuid.UUID):
        """Verifie la permission de suppression."""
        if self.current_user_role in [
            VaultAccessRole.HR_ADMIN,
            VaultAccessRole.HR_DIRECTOR,
            VaultAccessRole.SYSTEM,
        ]:
            return

        raise AccessDeniedException(
            str(self.current_user_id),
            str(employee_id),
            "delete",
        )

    async def _log_access(
        self,
        document_id: uuid.UUID,
        employee_id: uuid.UUID,
        access_type: VaultAccessType,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """Enregistre un acces dans le journal."""
        log = VaultAccessLog(
            document_id=document_id,
            employee_id=employee_id,
            accessed_by=self.current_user_id,
            access_role=self.current_user_role,
            access_type=access_type,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )
        await self.repository.create_access_log(log)

    # ========================================================================
    # RGPD
    # ========================================================================

    async def create_gdpr_request(
        self,
        data: VaultGDPRRequestCreate,
    ) -> VaultGDPRRequestResponse:
        """Cree une demande RGPD."""
        request = VaultGDPRRequest(
            employee_id=data.employee_id,
            request_type=data.request_type,
            request_description=data.request_description,
            document_types=[dt.value for dt in data.document_types],
            period_start=data.period_start,
            period_end=data.period_end,
        )
        request = await self.repository.create_gdpr_request(request)
        return VaultGDPRRequestResponse.model_validate(request)

    async def process_gdpr_request(
        self,
        request_id: uuid.UUID,
        process_data: VaultGDPRRequestProcess,
    ) -> VaultGDPRRequestResponse:
        """Traite une demande RGPD."""
        self._check_admin_permission()

        request = await self.repository.get_gdpr_request(request_id)
        if not request:
            raise GDPRRequestNotFoundException(str(request_id))

        if request.status in [GDPRRequestStatus.COMPLETED, GDPRRequestStatus.REJECTED]:
            raise GDPRRequestAlreadyProcessedException(
                str(request_id),
                str(request.processed_at),
            )

        update_data = {
            "status": process_data.status,
            "response_details": process_data.response_details,
            "processed_at": datetime.utcnow(),
            "processed_by": self.current_user_id,
        }

        # Si c'est une demande de portabilite, generer l'export
        if (
            request.request_type == GDPRRequestType.PORTABILITY
            and process_data.status == GDPRRequestStatus.COMPLETED
        ):
            export = await self._generate_gdpr_export(request)
            update_data["export_file_path"] = export["file_path"]
            update_data["export_file_hash"] = export["file_hash"]
            update_data["export_expires_at"] = datetime.utcnow() + timedelta(days=7)

        # Si c'est une demande d'effacement, supprimer les documents
        if (
            request.request_type == GDPRRequestType.ERASURE
            and process_data.status == GDPRRequestStatus.COMPLETED
        ):
            await self._process_erasure_request(request)

        request = await self.repository.update_gdpr_request(request_id, update_data)
        return VaultGDPRRequestResponse.model_validate(request)

    async def _generate_gdpr_export(
        self,
        request: VaultGDPRRequest,
    ) -> dict[str, str]:
        """Genere un export ZIP pour la portabilite."""
        # Recuperer les documents
        doc_types = [VaultDocumentType(dt) for dt in request.document_types] if request.document_types else None
        documents, _ = await self.repository.list_documents(
            employee_id=request.employee_id,
            date_from=request.period_start,
            date_to=request.period_end,
        )

        if doc_types:
            documents = [d for d in documents if d.document_type in doc_types]

        # Creer le ZIP
        export_id = uuid.uuid4()
        export_path = self.storage_path / "exports" / f"{export_id}.zip"
        export_path.parent.mkdir(parents=True, exist_ok=True)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for doc in documents:
                try:
                    content, filename, _ = await self.download_document(doc.id)
                    # Ajouter au ZIP avec un nom unique
                    zip_filename = f"{doc.document_type.value}/{doc.document_date or 'unknown'}_{filename}"
                    zf.writestr(zip_filename, content)
                except Exception:
                    continue

        zip_content = buffer.getvalue()
        export_path.write_bytes(zip_content)
        file_hash = hashlib.sha256(zip_content).hexdigest()

        return {
            "file_path": str(export_path),
            "file_hash": file_hash,
        }

    async def _process_erasure_request(self, request: VaultGDPRRequest):
        """Traite une demande d'effacement RGPD."""
        # Recuperer les documents
        documents, _ = await self.repository.list_documents(
            employee_id=request.employee_id,
        )

        for doc in documents:
            # Verifier si le document peut etre supprime (hors conservation legale)
            if doc.retention_end_date and doc.retention_end_date > date.today():
                continue

            await self.repository.soft_delete_document(
                doc.id,
                self.current_user_id,
                f"Demande RGPD {request.request_code}",
            )

    async def download_gdpr_export(
        self,
        request_id: uuid.UUID,
    ) -> tuple[bytes, str]:
        """Telecharge un export RGPD."""
        request = await self.repository.get_gdpr_request(request_id)
        if not request:
            raise GDPRRequestNotFoundException(str(request_id))

        # Verifier que c'est bien l'employe ou un admin
        if (
            self.current_user_id != request.employee_id
            and self.current_user_role
            not in [VaultAccessRole.HR_ADMIN, VaultAccessRole.HR_DIRECTOR]
        ):
            raise AccessDeniedException(
                str(self.current_user_id),
                str(request_id),
                "download_export",
            )

        if not request.export_file_path:
            raise GDPRRequestNotFoundException(str(request_id))

        if request.export_expires_at and request.export_expires_at < datetime.utcnow():
            raise GDPRExportExpiredException(
                str(request_id),
                str(request.export_expires_at),
            )

        # Lire le fichier
        export_path = Path(request.export_file_path)
        content = export_path.read_bytes()

        # Incrementer le compteur de telechargement
        await self.repository.update_gdpr_request(
            request_id,
            {"download_count": request.download_count + 1},
        )

        return content, f"export_rgpd_{request.request_code}.zip"

    # ========================================================================
    # SIGNATURE ELECTRONIQUE
    # ========================================================================

    async def request_signature(
        self,
        data: VaultSignatureRequest,
    ) -> VaultSignatureStatus:
        """Demande une signature electronique pour un document."""
        document = await self.repository.get_document(data.document_id)
        if not document:
            raise DocumentNotFoundException(str(data.document_id))

        self._check_edit_permission(document.employee_id)

        # TODO: Integrer avec un provider de signature (Yousign, DocuSign)
        # Pour l'instant, simuler la creation de la demande

        await self.repository.update_document(
            data.document_id,
            {
                "signature_status": SignatureStatus.PENDING,
                "signature_request_id": str(uuid.uuid4()),
            },
        )

        return VaultSignatureStatus(
            document_id=data.document_id,
            signature_status=SignatureStatus.PENDING,
            signers=data.signers,
        )

    async def process_signature_webhook(
        self,
        signature_request_id: str,
        event: str,
        data: dict,
    ):
        """Traite un webhook de signature."""
        # Trouver le document par signature_request_id
        # TODO: Implementer la recherche par signature_request_id

        if event == "signature.done":
            pass  # Mettre a jour le statut
        elif event == "signature.refused":
            pass
        elif event == "signature.expired":
            pass

    # ========================================================================
    # STATISTIQUES ET DASHBOARD
    # ========================================================================

    async def get_dashboard_stats(self) -> VaultDashboardStats:
        """Recupere les statistiques du dashboard."""
        stats = await self.repository.compute_current_stats()

        return VaultDashboardStats(
            total_documents=stats.get("total_documents", 0),
            documents_by_type=stats.get("documents_by_type", {}),
            total_storage_bytes=stats.get("total_storage_bytes", 0),
            pending_signatures=stats.get("pending_signatures", 0),
            expiring_documents_30d=stats.get("expiring_documents_30d", 0),
            gdpr_requests_pending=stats.get("gdpr_requests_pending", 0),
        )

    async def get_employee_stats(
        self,
        employee_id: uuid.UUID,
    ) -> VaultEmployeeStats:
        """Recupere les statistiques d'un employe."""
        self._check_view_permission(employee_id)

        documents = await self.repository.list_employee_documents(employee_id)

        docs_by_type: dict[str, int] = {}
        total_size = 0
        pending_sigs = 0
        unread = 0

        for doc in documents:
            type_key = doc.document_type.value
            docs_by_type[type_key] = docs_by_type.get(type_key, 0) + 1
            total_size += doc.file_size

            if doc.signature_status == SignatureStatus.PENDING:
                pending_sigs += 1
            if not doc.employee_viewed:
                unread += 1

        return VaultEmployeeStats(
            employee_id=employee_id,
            employee_name="",  # A remplir depuis le service HR
            vault_activated=True,
            total_documents=len(documents),
            documents_by_type=docs_by_type,
            total_storage_bytes=total_size,
            pending_signatures=pending_sigs,
            unread_documents=unread,
        )

    # ========================================================================
    # EXPORT DOSSIER SALARIE
    # ========================================================================

    async def export_employee_folder(
        self,
        data: VaultExportRequest,
    ) -> VaultExportResponse:
        """Exporte le dossier complet d'un employe."""
        self._check_view_permission(data.employee_id)

        # Recuperer les documents
        documents, _ = await self.repository.list_documents(
            employee_id=data.employee_id,
            date_from=data.period_start,
            date_to=data.period_end,
        )

        if data.document_types:
            documents = [d for d in documents if d.document_type in data.document_types]

        # Generer le ZIP
        export_id = uuid.uuid4()
        export_path = self.storage_path / "exports" / f"{export_id}.zip"
        export_path.parent.mkdir(parents=True, exist_ok=True)

        total_size = 0
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for doc in documents:
                try:
                    content, filename, _ = await self.download_document(doc.id)
                    zip_filename = f"{doc.document_type.value}/{doc.document_date or 'unknown'}_{filename}"
                    zf.writestr(zip_filename, content)
                    total_size += len(content)
                except Exception:
                    continue

        zip_content = buffer.getvalue()
        export_path.write_bytes(zip_content)

        return VaultExportResponse(
            export_id=export_id,
            status="ready",
            file_path=str(export_path),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            document_count=len(documents),
            total_size_bytes=total_size,
        )

    # ========================================================================
    # ALERTES ET NOTIFICATIONS
    # ========================================================================

    async def _notify_employee_new_document(self, document: VaultDocument):
        """Notifie l'employe d'un nouveau document."""
        # TODO: Envoyer un email/notification

        # Creer une alerte
        alert = VaultAlert(
            employee_id=document.employee_id,
            document_id=document.id,
            alert_type=AlertType.MISSING_DOCUMENT,  # A changer
            title=f"Nouveau document: {document.title}",
            description=f"Un nouveau document a ete ajoute a votre coffre-fort.",
            severity="INFO",
            target_user_id=document.employee_id,
            action_url=f"/hr-vault/documents/{document.id}",
        )
        await self.repository.create_alert(alert)

        # Mettre a jour le document
        await self.repository.update_document(
            document.id,
            {
                "employee_notified": True,
                "notification_sent_at": datetime.utcnow(),
            },
        )

    async def get_alerts(
        self,
        unread_only: bool = False,
    ) -> list:
        """Recupere les alertes de l'utilisateur courant."""
        alerts = await self.repository.list_alerts(
            target_user_id=self.current_user_id,
            target_role=self.current_user_role,
            unread_only=unread_only,
        )
        return alerts

    async def mark_alert_read(self, alert_id: uuid.UUID) -> bool:
        """Marque une alerte comme lue."""
        return await self.repository.mark_alert_read(alert_id)

    async def dismiss_alert(self, alert_id: uuid.UUID) -> bool:
        """Masque une alerte."""
        return await self.repository.dismiss_alert(alert_id)


# ============================================================================
# FACTORY
# ============================================================================

def create_hr_vault_service(
    session: AsyncSession,
    tenant_id: str,
    storage_path: str,
    master_key: Optional[bytes] = None,
    current_user_id: Optional[uuid.UUID] = None,
    current_user_role: VaultAccessRole = VaultAccessRole.EMPLOYEE,
) -> HRVaultService:
    """
    Factory pour creer le service HR Vault.

    Args:
        session: Session de base de donnees
        tenant_id: ID du tenant
        storage_path: Chemin de stockage des fichiers
        master_key: Cle maitre de chiffrement (32 bytes)
        current_user_id: ID de l'utilisateur courant
        current_user_role: Role de l'utilisateur courant

    Returns:
        Service configure
    """
    if master_key is None:
        # En production, recuperer depuis un HSM ou service de secrets
        master_key = os.urandom(32)

    return HRVaultService(
        session=session,
        tenant_id=tenant_id,
        storage_path=storage_path,
        master_key=master_key,
        current_user_id=current_user_id,
        current_user_role=current_user_role,
    )
