"""
AZALS MODULE HR_VAULT - Repository
====================================

Repository pattern pour l'acces aux donnees du coffre-fort RH.
Toutes les requetes sont filtrees par tenant_id.
"""

import hashlib
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .exceptions import (
    CategoryNotFoundException,
    DocumentNotFoundException,
    EncryptionKeyNotFoundException,
    GDPRRequestNotFoundException,
)
from .models import (
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


class HRVaultRepository:
    """Repository pour le coffre-fort RH."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    # ========================================================================
    # BASE QUERY - Filtrage tenant_id obligatoire
    # ========================================================================

    def _base_query(self, model):
        """Query de base avec filtre tenant_id obligatoire."""
        return select(model).where(model.tenant_id == self.tenant_id)

    def _active_query(self, model):
        """Query pour les enregistrements actifs (soft delete)."""
        return self._base_query(model).where(model.is_active == True)

    # ========================================================================
    # CATEGORIES
    # ========================================================================

    async def get_category(self, category_id: uuid.UUID) -> Optional[VaultDocumentCategory]:
        """Recupere une categorie par ID."""
        query = self._active_query(VaultDocumentCategory).where(
            VaultDocumentCategory.id == category_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_category_by_code(self, code: str) -> Optional[VaultDocumentCategory]:
        """Recupere une categorie par code."""
        query = self._active_query(VaultDocumentCategory).where(
            VaultDocumentCategory.code == code
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_categories(
        self,
        include_inactive: bool = False,
    ) -> list[VaultDocumentCategory]:
        """Liste toutes les categories."""
        if include_inactive:
            query = self._base_query(VaultDocumentCategory)
        else:
            query = self._active_query(VaultDocumentCategory)

        query = query.order_by(
            VaultDocumentCategory.sort_order,
            VaultDocumentCategory.name,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_category(
        self,
        category: VaultDocumentCategory,
    ) -> VaultDocumentCategory:
        """Cree une nouvelle categorie."""
        category.tenant_id = self.tenant_id
        self.session.add(category)
        await self.session.flush()
        return category

    async def update_category(
        self,
        category_id: uuid.UUID,
        data: dict[str, Any],
    ) -> VaultDocumentCategory:
        """Met a jour une categorie."""
        category = await self.get_category(category_id)
        if not category:
            raise CategoryNotFoundException(str(category_id))

        for key, value in data.items():
            if hasattr(category, key) and value is not None:
                setattr(category, key, value)

        category.version += 1
        category.updated_at = datetime.utcnow()
        await self.session.flush()
        return category

    async def soft_delete_category(
        self,
        category_id: uuid.UUID,
        deleted_by: Optional[uuid.UUID] = None,
    ) -> VaultDocumentCategory:
        """Supprime logiquement une categorie."""
        category = await self.get_category(category_id)
        if not category:
            raise CategoryNotFoundException(str(category_id))

        category.is_active = False
        category.deleted_at = datetime.utcnow()
        await self.session.flush()
        return category

    async def count_documents_by_category(
        self,
        category_id: uuid.UUID,
    ) -> int:
        """Compte les documents d'une categorie."""
        query = (
            select(func.count(VaultDocument.id))
            .where(VaultDocument.tenant_id == self.tenant_id)
            .where(VaultDocument.category_id == category_id)
            .where(VaultDocument.is_active == True)
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    # ========================================================================
    # DOCUMENTS
    # ========================================================================

    async def get_document(
        self,
        document_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Optional[VaultDocument]:
        """Recupere un document par ID."""
        if include_deleted:
            query = self._base_query(VaultDocument)
        else:
            query = self._active_query(VaultDocument)

        query = query.where(VaultDocument.id == document_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_document_with_relations(
        self,
        document_id: uuid.UUID,
    ) -> Optional[VaultDocument]:
        """Recupere un document avec ses relations."""
        query = (
            self._active_query(VaultDocument)
            .where(VaultDocument.id == document_id)
            .options(
                selectinload(VaultDocument.category),
                selectinload(VaultDocument.versions),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        employee_id: Optional[uuid.UUID] = None,
        document_type: Optional[VaultDocumentType] = None,
        category_id: Optional[uuid.UUID] = None,
        status: Optional[VaultDocumentStatus] = None,
        signature_status: Optional[SignatureStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        pay_period: Optional[str] = None,
        search: Optional[str] = None,
        tags: Optional[list[str]] = None,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[VaultDocument], int]:
        """Liste les documents avec filtres."""
        if include_deleted:
            query = self._base_query(VaultDocument)
        else:
            query = self._active_query(VaultDocument)

        # Filtres
        if employee_id:
            query = query.where(VaultDocument.employee_id == employee_id)
        if document_type:
            query = query.where(VaultDocument.document_type == document_type)
        if category_id:
            query = query.where(VaultDocument.category_id == category_id)
        if status:
            query = query.where(VaultDocument.status == status)
        if signature_status:
            query = query.where(VaultDocument.signature_status == signature_status)
        if date_from:
            query = query.where(VaultDocument.document_date >= date_from)
        if date_to:
            query = query.where(VaultDocument.document_date <= date_to)
        if pay_period:
            query = query.where(VaultDocument.pay_period == pay_period)
        if search:
            search_filter = or_(
                VaultDocument.title.ilike(f"%{search}%"),
                VaultDocument.description.ilike(f"%{search}%"),
                VaultDocument.reference.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)
        if tags:
            for tag in tags:
                query = query.where(VaultDocument.tags.contains([tag]))

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0

        # Pagination et tri
        query = query.order_by(desc(VaultDocument.created_at))
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def list_employee_documents(
        self,
        employee_id: uuid.UUID,
        document_type: Optional[VaultDocumentType] = None,
        visible_to_employee: bool = True,
    ) -> list[VaultDocument]:
        """Liste les documents d'un employe."""
        query = (
            self._active_query(VaultDocument)
            .where(VaultDocument.employee_id == employee_id)
        )

        if visible_to_employee:
            query = query.where(VaultDocument.visible_to_employee == True)
        if document_type:
            query = query.where(VaultDocument.document_type == document_type)

        query = query.order_by(desc(VaultDocument.document_date))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_document(self, document: VaultDocument) -> VaultDocument:
        """Cree un nouveau document."""
        document.tenant_id = self.tenant_id

        # Calcul date fin retention
        if document.retention_period:
            document.retention_end_date = self._calculate_retention_end_date(
                document.retention_period,
                document.document_date or date.today(),
            )

        self.session.add(document)
        await self.session.flush()
        return document

    async def update_document(
        self,
        document_id: uuid.UUID,
        data: dict[str, Any],
    ) -> VaultDocument:
        """Met a jour un document."""
        document = await self.get_document(document_id)
        if not document:
            raise DocumentNotFoundException(str(document_id))

        for key, value in data.items():
            if hasattr(document, key) and value is not None:
                setattr(document, key, value)

        document.version += 1
        document.updated_at = datetime.utcnow()
        await self.session.flush()
        return document

    async def soft_delete_document(
        self,
        document_id: uuid.UUID,
        deleted_by: Optional[uuid.UUID] = None,
        deletion_reason: Optional[str] = None,
    ) -> VaultDocument:
        """Supprime logiquement un document."""
        document = await self.get_document(document_id)
        if not document:
            raise DocumentNotFoundException(str(document_id))

        document.is_active = False
        document.status = VaultDocumentStatus.DELETED
        document.deleted_at = datetime.utcnow()
        document.deleted_by = deleted_by
        document.deletion_reason = deletion_reason
        await self.session.flush()
        return document

    async def mark_as_viewed(
        self,
        document_id: uuid.UUID,
    ) -> VaultDocument:
        """Marque un document comme vu par l'employe."""
        document = await self.get_document(document_id)
        if not document:
            raise DocumentNotFoundException(str(document_id))

        if not document.employee_viewed:
            document.employee_viewed = True
            document.first_viewed_at = datetime.utcnow()
            await self.session.flush()
        return document

    async def get_expiring_documents(
        self,
        days: int = 30,
    ) -> list[VaultDocument]:
        """Liste les documents expirant dans X jours."""
        expiry_date = date.today() + timedelta(days=days)
        query = (
            self._active_query(VaultDocument)
            .where(VaultDocument.expiry_date <= expiry_date)
            .where(VaultDocument.expiry_date >= date.today())
            .order_by(VaultDocument.expiry_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_signature_documents(self) -> list[VaultDocument]:
        """Liste les documents en attente de signature."""
        query = (
            self._active_query(VaultDocument)
            .where(
                VaultDocument.signature_status.in_([
                    SignatureStatus.PENDING,
                    SignatureStatus.SIGNED_EMPLOYEE,
                    SignatureStatus.SIGNED_EMPLOYER,
                ])
            )
            .order_by(VaultDocument.created_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    def _calculate_retention_end_date(
        self,
        retention: RetentionPeriod,
        start_date: date,
    ) -> date:
        """Calcule la date de fin de retention."""
        years_map = {
            RetentionPeriod.FIVE_YEARS: 5,
            RetentionPeriod.TEN_YEARS: 10,
            RetentionPeriod.THIRTY_YEARS: 30,
            RetentionPeriod.FIFTY_YEARS: 50,
            RetentionPeriod.PERMANENT: 100,
            RetentionPeriod.LIFETIME_PLUS_5: 70,  # Estimation
        }
        years = years_map.get(retention, 5)
        return start_date.replace(year=start_date.year + years)

    # ========================================================================
    # VERSIONS
    # ========================================================================

    async def create_version(
        self,
        version: VaultDocumentVersion,
    ) -> VaultDocumentVersion:
        """Cree une nouvelle version de document."""
        version.tenant_id = self.tenant_id
        self.session.add(version)
        await self.session.flush()
        return version

    async def list_document_versions(
        self,
        document_id: uuid.UUID,
    ) -> list[VaultDocumentVersion]:
        """Liste les versions d'un document."""
        query = (
            self._base_query(VaultDocumentVersion)
            .where(VaultDocumentVersion.document_id == document_id)
            .order_by(desc(VaultDocumentVersion.version_number))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ========================================================================
    # CLES DE CHIFFREMENT
    # ========================================================================

    async def get_encryption_key(
        self,
        key_id: uuid.UUID,
    ) -> Optional[VaultEncryptionKey]:
        """Recupere une cle de chiffrement."""
        query = (
            self._base_query(VaultEncryptionKey)
            .where(VaultEncryptionKey.id == key_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_encryption_key(self) -> Optional[VaultEncryptionKey]:
        """Recupere la cle de chiffrement active."""
        query = (
            self._base_query(VaultEncryptionKey)
            .where(VaultEncryptionKey.is_active == True)
            .where(
                or_(
                    VaultEncryptionKey.expires_at.is_(None),
                    VaultEncryptionKey.expires_at > datetime.utcnow(),
                )
            )
            .order_by(desc(VaultEncryptionKey.created_at))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_encryption_key(
        self,
        key: VaultEncryptionKey,
    ) -> VaultEncryptionKey:
        """Cree une nouvelle cle de chiffrement."""
        key.tenant_id = self.tenant_id
        self.session.add(key)
        await self.session.flush()
        return key

    async def rotate_encryption_key(
        self,
        old_key_id: uuid.UUID,
        new_key: VaultEncryptionKey,
    ) -> VaultEncryptionKey:
        """Effectue une rotation de cle."""
        old_key = await self.get_encryption_key(old_key_id)
        if not old_key:
            raise EncryptionKeyNotFoundException(str(old_key_id))

        # Creer nouvelle cle
        new_key.tenant_id = self.tenant_id
        self.session.add(new_key)
        await self.session.flush()

        # Desactiver ancienne cle
        old_key.is_active = False
        old_key.rotated_to_id = new_key.id
        old_key.rotated_at = datetime.utcnow()

        await self.session.flush()
        return new_key

    # ========================================================================
    # LOGS D'ACCES
    # ========================================================================

    async def create_access_log(self, log: VaultAccessLog) -> VaultAccessLog:
        """Cree un log d'acces."""
        log.tenant_id = self.tenant_id
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_access_logs(
        self,
        document_id: Optional[uuid.UUID] = None,
        employee_id: Optional[uuid.UUID] = None,
        accessed_by: Optional[uuid.UUID] = None,
        access_type: Optional[VaultAccessType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        success_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[VaultAccessLog], int]:
        """Liste les logs d'acces."""
        query = self._base_query(VaultAccessLog)

        if document_id:
            query = query.where(VaultAccessLog.document_id == document_id)
        if employee_id:
            query = query.where(VaultAccessLog.employee_id == employee_id)
        if accessed_by:
            query = query.where(VaultAccessLog.accessed_by == accessed_by)
        if access_type:
            query = query.where(VaultAccessLog.access_type == access_type)
        if date_from:
            query = query.where(VaultAccessLog.access_date >= date_from)
        if date_to:
            query = query.where(VaultAccessLog.access_date <= date_to)
        if success_only:
            query = query.where(VaultAccessLog.success == True)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0

        # Pagination et tri
        query = query.order_by(desc(VaultAccessLog.access_date))
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    # ========================================================================
    # PERMISSIONS
    # ========================================================================

    async def get_user_permissions(
        self,
        user_id: uuid.UUID,
        role: Optional[VaultAccessRole] = None,
    ) -> list[VaultAccessPermission]:
        """Recupere les permissions d'un utilisateur."""
        now = datetime.utcnow()
        query = (
            self._base_query(VaultAccessPermission)
            .where(VaultAccessPermission.is_active == True)
            .where(
                or_(
                    VaultAccessPermission.user_id == user_id,
                    VaultAccessPermission.role == role,
                )
            )
            .where(
                or_(
                    VaultAccessPermission.valid_from.is_(None),
                    VaultAccessPermission.valid_from <= now,
                )
            )
            .where(
                or_(
                    VaultAccessPermission.valid_until.is_(None),
                    VaultAccessPermission.valid_until >= now,
                )
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_permission(
        self,
        permission: VaultAccessPermission,
    ) -> VaultAccessPermission:
        """Cree une permission."""
        permission.tenant_id = self.tenant_id
        self.session.add(permission)
        await self.session.flush()
        return permission

    async def delete_permission(self, permission_id: uuid.UUID) -> bool:
        """Supprime une permission."""
        query = (
            self._base_query(VaultAccessPermission)
            .where(VaultAccessPermission.id == permission_id)
        )
        result = await self.session.execute(query)
        permission = result.scalar_one_or_none()
        if permission:
            permission.is_active = False
            await self.session.flush()
            return True
        return False

    # ========================================================================
    # CONSENTEMENTS
    # ========================================================================

    async def get_consent(
        self,
        employee_id: uuid.UUID,
        consent_type: str,
    ) -> Optional[VaultConsent]:
        """Recupere le consentement d'un employe."""
        query = (
            self._base_query(VaultConsent)
            .where(VaultConsent.employee_id == employee_id)
            .where(VaultConsent.consent_type == consent_type)
            .order_by(desc(VaultConsent.given_at))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_consent(self, consent: VaultConsent) -> VaultConsent:
        """Cree un consentement."""
        consent.tenant_id = self.tenant_id
        self.session.add(consent)
        await self.session.flush()
        return consent

    async def revoke_consent(
        self,
        employee_id: uuid.UUID,
        consent_type: str,
    ) -> Optional[VaultConsent]:
        """Revoque un consentement."""
        consent = await self.get_consent(employee_id, consent_type)
        if consent and consent.given:
            consent.revoked_at = datetime.utcnow()
            await self.session.flush()
        return consent

    # ========================================================================
    # DEMANDES RGPD
    # ========================================================================

    async def get_gdpr_request(
        self,
        request_id: uuid.UUID,
    ) -> Optional[VaultGDPRRequest]:
        """Recupere une demande RGPD."""
        query = (
            self._base_query(VaultGDPRRequest)
            .where(VaultGDPRRequest.id == request_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_gdpr_requests(
        self,
        employee_id: Optional[uuid.UUID] = None,
        request_type: Optional[GDPRRequestType] = None,
        status: Optional[GDPRRequestStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[VaultGDPRRequest], int]:
        """Liste les demandes RGPD."""
        query = self._base_query(VaultGDPRRequest)

        if employee_id:
            query = query.where(VaultGDPRRequest.employee_id == employee_id)
        if request_type:
            query = query.where(VaultGDPRRequest.request_type == request_type)
        if status:
            query = query.where(VaultGDPRRequest.status == status)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0

        # Pagination et tri
        query = query.order_by(desc(VaultGDPRRequest.requested_at))
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def create_gdpr_request(
        self,
        request: VaultGDPRRequest,
    ) -> VaultGDPRRequest:
        """Cree une demande RGPD."""
        request.tenant_id = self.tenant_id
        request.request_code = self._generate_gdpr_code()
        request.due_date = date.today() + timedelta(days=30)  # RGPD: 30 jours
        self.session.add(request)
        await self.session.flush()
        return request

    async def update_gdpr_request(
        self,
        request_id: uuid.UUID,
        data: dict[str, Any],
    ) -> VaultGDPRRequest:
        """Met a jour une demande RGPD."""
        request = await self.get_gdpr_request(request_id)
        if not request:
            raise GDPRRequestNotFoundException(str(request_id))

        for key, value in data.items():
            if hasattr(request, key) and value is not None:
                setattr(request, key, value)

        request.version += 1
        request.updated_at = datetime.utcnow()
        await self.session.flush()
        return request

    def _generate_gdpr_code(self) -> str:
        """Genere un code unique pour demande RGPD."""
        today = date.today()
        random_part = uuid.uuid4().hex[:6].upper()
        return f"GDPR-{today.year}{today.month:02d}-{random_part}"

    # ========================================================================
    # ALERTES
    # ========================================================================

    async def create_alert(self, alert: VaultAlert) -> VaultAlert:
        """Cree une alerte."""
        alert.tenant_id = self.tenant_id
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def list_alerts(
        self,
        target_user_id: Optional[uuid.UUID] = None,
        target_role: Optional[VaultAccessRole] = None,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[VaultAlert]:
        """Liste les alertes."""
        query = self._base_query(VaultAlert)

        if target_user_id:
            query = query.where(
                or_(
                    VaultAlert.target_user_id == target_user_id,
                    VaultAlert.target_user_id.is_(None),
                )
            )
        if target_role:
            query = query.where(
                or_(
                    VaultAlert.target_role == target_role,
                    VaultAlert.target_role.is_(None),
                )
            )
        if unread_only:
            query = query.where(VaultAlert.is_read == False)

        # Exclure alertes expirees ou dismissees
        query = query.where(VaultAlert.is_dismissed == False)
        query = query.where(
            or_(
                VaultAlert.expires_at.is_(None),
                VaultAlert.expires_at >= datetime.utcnow(),
            )
        )

        query = query.order_by(desc(VaultAlert.created_at))
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_alert_read(self, alert_id: uuid.UUID) -> bool:
        """Marque une alerte comme lue."""
        query = self._base_query(VaultAlert).where(VaultAlert.id == alert_id)
        result = await self.session.execute(query)
        alert = result.scalar_one_or_none()
        if alert:
            alert.is_read = True
            alert.read_at = datetime.utcnow()
            await self.session.flush()
            return True
        return False

    async def dismiss_alert(self, alert_id: uuid.UUID) -> bool:
        """Masque une alerte."""
        query = self._base_query(VaultAlert).where(VaultAlert.id == alert_id)
        result = await self.session.execute(query)
        alert = result.scalar_one_or_none()
        if alert:
            alert.is_dismissed = True
            alert.dismissed_at = datetime.utcnow()
            await self.session.flush()
            return True
        return False

    # ========================================================================
    # STATISTIQUES
    # ========================================================================

    async def get_statistics(
        self,
        date_stat: Optional[date] = None,
    ) -> Optional[VaultStatistics]:
        """Recupere les statistiques d'un jour."""
        stat_date = date_stat or date.today()
        query = (
            self._base_query(VaultStatistics)
            .where(VaultStatistics.date == stat_date)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_statistics(
        self,
        stats: VaultStatistics,
    ) -> VaultStatistics:
        """Cree un enregistrement de statistiques."""
        stats.tenant_id = self.tenant_id
        self.session.add(stats)
        await self.session.flush()
        return stats

    async def compute_current_stats(self) -> dict[str, Any]:
        """Calcule les statistiques actuelles."""
        # Total documents
        doc_count_query = select(func.count(VaultDocument.id)).where(
            VaultDocument.tenant_id == self.tenant_id,
            VaultDocument.is_active == True,
        )
        total_docs = (await self.session.execute(doc_count_query)).scalar() or 0

        # Documents par type
        type_query = (
            select(
                VaultDocument.document_type,
                func.count(VaultDocument.id),
            )
            .where(
                VaultDocument.tenant_id == self.tenant_id,
                VaultDocument.is_active == True,
            )
            .group_by(VaultDocument.document_type)
        )
        type_result = await self.session.execute(type_query)
        docs_by_type = {str(row[0].value): row[1] for row in type_result.fetchall()}

        # Total stockage
        storage_query = select(func.sum(VaultDocument.file_size)).where(
            VaultDocument.tenant_id == self.tenant_id,
            VaultDocument.is_active == True,
        )
        total_storage = (await self.session.execute(storage_query)).scalar() or 0

        # Signatures en attente
        sig_query = select(func.count(VaultDocument.id)).where(
            VaultDocument.tenant_id == self.tenant_id,
            VaultDocument.is_active == True,
            VaultDocument.signature_status.in_([
                SignatureStatus.PENDING,
                SignatureStatus.SIGNED_EMPLOYEE,
                SignatureStatus.SIGNED_EMPLOYER,
            ]),
        )
        pending_sigs = (await self.session.execute(sig_query)).scalar() or 0

        # Documents expirant dans 30 jours
        expiry_date = date.today() + timedelta(days=30)
        exp_query = select(func.count(VaultDocument.id)).where(
            VaultDocument.tenant_id == self.tenant_id,
            VaultDocument.is_active == True,
            VaultDocument.expiry_date <= expiry_date,
            VaultDocument.expiry_date >= date.today(),
        )
        expiring = (await self.session.execute(exp_query)).scalar() or 0

        # Demandes RGPD en attente
        gdpr_query = select(func.count(VaultGDPRRequest.id)).where(
            VaultGDPRRequest.tenant_id == self.tenant_id,
            VaultGDPRRequest.status == GDPRRequestStatus.PENDING,
        )
        gdpr_pending = (await self.session.execute(gdpr_query)).scalar() or 0

        return {
            "total_documents": total_docs,
            "documents_by_type": docs_by_type,
            "total_storage_bytes": total_storage,
            "pending_signatures": pending_sigs,
            "expiring_documents_30d": expiring,
            "gdpr_requests_pending": gdpr_pending,
        }
