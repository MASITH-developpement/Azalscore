"""
AZALS MODULE M2A - Service Documents
=====================================

Service de gestion des documents comptables.
Gère le flux complet: réception -> OCR -> IA -> comptabilisation.
"""

import hashlib
import logging
import uuid
from datetime import date, datetime
from typing import Any, BinaryIO
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models import (
    AccountingAlert,
    AccountingDocument,
    AlertSeverity,
    AlertType,
    ConfidenceLevel,
    DocumentSource,
    DocumentStatus,
    DocumentType,
    PaymentStatus,
)
from ..schemas import DocumentReject, DocumentUpdate, DocumentValidate
from .ai_classification_service import AIClassificationService
from .auto_accounting_service import AutoAccountingService
from .ocr_service import OCRService

logger = logging.getLogger(__name__)


class DocumentService:
    """Service de gestion des documents comptables.

    Principe clé: Une facture reçue = la comptabilité se fait toute seule.
    L'humain valide par exception uniquement.
    """

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.ocr_service = OCRService(db, tenant_id)
        self.ai_service = AIClassificationService(db, tenant_id)
        self.accounting_service = AutoAccountingService(db, tenant_id)

    # =========================================================================
    # CRÉATION ET UPLOAD
    # =========================================================================

    def create_document(
        self,
        document_type: DocumentType,
        source: DocumentSource,
        file_content: BinaryIO | None = None,
        file_path: str | None = None,
        original_filename: str | None = None,
        created_by: UUID | None = None,
        **kwargs
    ) -> AccountingDocument:
        """Crée un nouveau document et lance le traitement automatique.

        Args:
            document_type: Type de document (facture, note de frais, etc.)
            source: Source du document (email, upload, etc.)
            file_content: Contenu du fichier (optionnel)
            file_path: Chemin du fichier (optionnel)
            original_filename: Nom du fichier original
            created_by: ID de l'utilisateur créateur
            **kwargs: Autres champs du document

        Returns:
            AccountingDocument créé
        """
        # Calcule le hash si fichier fourni
        file_hash = None
        if file_content:
            file_hash = self._calculate_hash(file_content)
            file_content.seek(0)  # Reset pour lecture ultérieure

            # Vérifie les doublons
            existing = self.ocr_service.check_duplicate(file_hash)
            if existing:
                logger.warning(f"Duplicate document detected: {existing.id}")
                self._create_alert(
                    alert_type=AlertType.DUPLICATE_SUSPECTED,
                    title="Document en double détecté",
                    message=f"Ce document semble être un doublon de {existing.reference or existing.id}",
                    document_id=existing.id,
                    severity=AlertSeverity.WARNING
                )

        # Crée le document
        document = AccountingDocument(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            document_type=document_type,
            source=source,
            status=DocumentStatus.RECEIVED,
            original_filename=original_filename,
            file_hash=file_hash,
            payment_status=PaymentStatus.UNPAID,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            received_at=datetime.utcnow(),
            **{k: v for k, v in kwargs.items() if hasattr(AccountingDocument, k)}
        )

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        logger.info(f"Document created: {document.id} ({document_type.value})")

        # Lance le traitement automatique si fichier fourni
        if file_path or file_content:
            self.process_document(document.id, file_path)

        return document

    def process_document(
        self,
        document_id: UUID,
        file_path: str | None = None
    ) -> AccountingDocument:
        """Traite un document: OCR -> IA -> Comptabilisation.

        Cette méthode orchestre tout le flux automatique.

        Args:
            document_id: ID du document
            file_path: Chemin du fichier (si pas déjà stocké)

        Returns:
            Document mis à jour
        """
        document = self.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Utilise le chemin stocké si pas fourni
        if not file_path:
            file_path = document.file_path

        if not file_path:
            raise ValueError("No file path available for processing")

        # 1. OCR - Extraction du texte
        logger.info(f"Starting OCR for document {document_id}")
        self.ocr_service.process_document(document_id, file_path)

        # Recharge le document après OCR
        self.db.refresh(document)

        # 2. Classification IA
        logger.info(f"Starting AI classification for document {document_id}")
        self.ai_service.classify_document(document_id)

        # Recharge après classification
        self.db.refresh(document)

        # 3. Génération de l'écriture comptable
        logger.info(f"Generating accounting entry for document {document_id}")
        auto_entry = self.accounting_service.process_document(document_id)

        # Recharge final
        self.db.refresh(document)

        # Vérifie s'il y a des alertes à créer
        self._check_and_create_alerts(document)

        logger.info(
            f"Document {document_id} processed successfully. "
            f"Status: {document.status.value}, "
            f"Auto-validated: {auto_entry.auto_validated}"
        )

        return document

    # =========================================================================
    # LECTURE
    # =========================================================================

    def get_document(self, document_id: UUID) -> AccountingDocument | None:
        """Récupère un document par son ID."""
        return self.db.query(AccountingDocument).filter(
            AccountingDocument.id == document_id,
            AccountingDocument.tenant_id == self.tenant_id
        ).first()

    def list_documents(
        self,
        document_type: DocumentType | None = None,
        status: DocumentStatus | None = None,
        payment_status: PaymentStatus | None = None,
        partner_name: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        requires_validation: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list[AccountingDocument], int]:
        """Liste les documents avec filtres.

        Returns:
            Tuple[List[documents], total_count]
        """
        query = self.db.query(AccountingDocument).filter(
            AccountingDocument.tenant_id == self.tenant_id
        )

        # Filtres
        if document_type:
            query = query.filter(AccountingDocument.document_type == document_type)

        if status:
            query = query.filter(AccountingDocument.status == status)

        if payment_status:
            query = query.filter(AccountingDocument.payment_status == payment_status)

        if partner_name:
            query = query.filter(
                AccountingDocument.partner_name.ilike(f"%{partner_name}%")
            )

        if start_date:
            query = query.filter(AccountingDocument.document_date >= start_date)

        if end_date:
            query = query.filter(AccountingDocument.document_date <= end_date)

        if requires_validation is not None:
            query = query.filter(AccountingDocument.requires_validation == requires_validation)

        if search:
            search_filter = or_(
                AccountingDocument.reference.ilike(f"%{search}%"),
                AccountingDocument.partner_name.ilike(f"%{search}%"),
                AccountingDocument.original_filename.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        # Total
        total = query.count()

        # Pagination
        offset = (page - 1) * page_size
        documents = query.order_by(
            AccountingDocument.received_at.desc()
        ).offset(offset).limit(page_size).all()

        return documents, total

    def get_documents_for_validation(
        self,
        confidence_filter: ConfidenceLevel | None = None,
        limit: int = 50
    ) -> list[AccountingDocument]:
        """Récupère les documents en attente de validation.

        Pour la vue Expert-comptable.
        """
        query = self.db.query(AccountingDocument).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.requires_validation,
            AccountingDocument.status.in_([
                DocumentStatus.PENDING_VALIDATION,
                DocumentStatus.ANALYZED
            ])
        )

        if confidence_filter:
            query = query.filter(AccountingDocument.ai_confidence == confidence_filter)

        return query.order_by(
            AccountingDocument.ai_confidence_score.asc(),  # Plus basse confiance en premier
            AccountingDocument.received_at.asc()
        ).limit(limit).all()

    # =========================================================================
    # MISE À JOUR
    # =========================================================================

    def update_document(
        self,
        document_id: UUID,
        update_data: DocumentUpdate
    ) -> AccountingDocument:
        """Met à jour un document."""
        document = self.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Mise à jour des champs
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(document, key):
                setattr(document, key, value)

        document.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(document)

        return document

    def validate_document(
        self,
        document_id: UUID,
        validated_by: UUID,
        validation_data: DocumentValidate
    ) -> AccountingDocument:
        """Valide un document (par l'expert-comptable).

        Args:
            document_id: ID du document
            validated_by: ID de l'utilisateur qui valide
            validation_data: Données de validation

        Returns:
            Document validé
        """
        document = self.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Applique les corrections si fournies
        if validation_data.corrected_amount_untaxed:
            document.amount_untaxed = validation_data.corrected_amount_untaxed
        if validation_data.corrected_amount_tax:
            document.amount_tax = validation_data.corrected_amount_tax
        if validation_data.corrected_amount_total:
            document.amount_total = validation_data.corrected_amount_total

        # Si compte corrigé, enregistre pour apprentissage IA
        if validation_data.corrected_account_code:
            # Récupère la dernière classification
            classification = self.ai_service.get_latest_classification(document_id)
            if classification:
                self.ai_service.record_correction(
                    classification_id=classification.id,
                    corrected_by=validated_by,
                    corrected_account_code=validation_data.corrected_account_code,
                    feedback=validation_data.validation_notes
                )

        # Met à jour le document
        document.status = DocumentStatus.VALIDATED
        document.requires_validation = False
        document.validated_by = validated_by
        document.validated_at = datetime.utcnow()
        document.validation_notes = validation_data.validation_notes
        document.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(document)

        # Lance la comptabilisation si pas déjà fait
        if not document.journal_entry_id:
            self.accounting_service.process_document(document_id, force_validation=False)

        return document

    def reject_document(
        self,
        document_id: UUID,
        rejected_by: UUID,
        rejection_data: DocumentReject
    ) -> AccountingDocument:
        """Rejette un document."""
        document = self.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        document.status = DocumentStatus.REJECTED
        document.requires_validation = False
        document.validated_by = rejected_by
        document.validated_at = datetime.utcnow()
        document.validation_notes = f"REJETÉ: {rejection_data.rejection_reason}"
        document.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(document)

        return document

    def bulk_validate(
        self,
        document_ids: list[UUID],
        validated_by: UUID
    ) -> dict[str, Any]:
        """Validation en masse de documents.

        Pour l'expert-comptable.
        """
        results = {
            "validated": 0,
            "failed": 0,
            "failed_ids": [],
            "errors": {}
        }

        for doc_id in document_ids:
            self.validate_document(
                document_id=doc_id,
                validated_by=validated_by,
                validation_data=DocumentValidate()
            )
            results["validated"] += 1

        return results

    # =========================================================================
    # SUPPRESSION
    # =========================================================================

    def delete_document(self, document_id: UUID) -> bool:
        """Supprime un document (si non comptabilisé)."""
        document = self.get_document(document_id)
        if not document:
            return False

        # Vérifie si comptabilisé
        if document.status == DocumentStatus.ACCOUNTED:
            raise ValueError("Cannot delete an accounted document")

        self.db.delete(document)
        self.db.commit()
        return True

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _calculate_hash(self, file_content: BinaryIO) -> str:
        """Calcule le hash SHA-256 d'un fichier."""
        sha256 = hashlib.sha256()
        for chunk in iter(lambda: file_content.read(8192), b""):
            sha256.update(chunk)
        return sha256.hexdigest()

    def _check_and_create_alerts(self, document: AccountingDocument):
        """Vérifie et crée des alertes si nécessaire."""
        # Alerte si confiance faible
        if document.ai_confidence in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]:
            self._create_alert(
                alert_type=AlertType.LOW_CONFIDENCE,
                title="Confiance IA faible",
                message=f"Le document {document.reference or 'sans référence'} "
                        f"a un score de confiance de {document.ai_confidence_score}%. "
                        f"Validation manuelle requise.",
                document_id=document.id,
                severity=AlertSeverity.WARNING
            )

        # Alerte si informations manquantes
        missing = []
        if not document.amount_total:
            missing.append("montant total")
        if not document.document_date:
            missing.append("date")
        if not document.partner_name:
            missing.append("partenaire")

        if missing:
            self._create_alert(
                alert_type=AlertType.MISSING_INFO,
                title="Informations manquantes",
                message=f"Le document est incomplet. Champs manquants: {', '.join(missing)}",
                document_id=document.id,
                severity=AlertSeverity.WARNING
            )

    def _create_alert(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        document_id: UUID | None = None,
        severity: AlertSeverity = AlertSeverity.WARNING,
        target_roles: list[str] = None
    ):
        """Crée une alerte."""
        if target_roles is None:
            target_roles = ["EXPERT_COMPTABLE"]

        alert = AccountingAlert(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            document_id=document_id,
            entity_type="document" if document_id else None,
            entity_id=document_id,
            target_roles=target_roles,
            created_at=datetime.utcnow()
        )
        self.db.add(alert)

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def get_document_stats(self) -> dict[str, Any]:
        """Récupère les statistiques des documents."""
        # Par statut
        status_counts = dict(
            self.db.query(
                AccountingDocument.status,
                func.count(AccountingDocument.id)
            ).filter(
                AccountingDocument.tenant_id == self.tenant_id
            ).group_by(AccountingDocument.status).all()
        )

        # Par type
        type_counts = dict(
            self.db.query(
                AccountingDocument.document_type,
                func.count(AccountingDocument.id)
            ).filter(
                AccountingDocument.tenant_id == self.tenant_id
            ).group_by(AccountingDocument.document_type).all()
        )

        # En attente de validation
        pending_validation = self.db.query(AccountingDocument).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.requires_validation
        ).count()

        # Erreurs
        errors = self.db.query(AccountingDocument).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.status == DocumentStatus.ERROR
        ).count()

        return {
            "by_status": {s.value if hasattr(s, 'value') else s: c for s, c in status_counts.items()},
            "by_type": {t.value if hasattr(t, 'value') else t: c for t, c in type_counts.items()},
            "pending_validation": pending_validation,
            "errors": errors,
            "total": sum(status_counts.values()) if status_counts else 0,
        }
