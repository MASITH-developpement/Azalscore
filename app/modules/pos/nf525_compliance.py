"""
AZALSCORE - Service de Conformité NF525
========================================
Norme NF525 (NF Z42-013) pour logiciels de caisse en France.

Exigences principales:
- Inaltérabilité: Les données enregistrées ne peuvent être modifiées ni supprimées
- Sécurisation: Signature cryptographique des données (chaîne de hachage SHA-256)
- Conservation: Conservation des données pendant 6 ans minimum
- Archivage: Export périodique et sécurisé des données

BOI-TVA-DECLA-30-10-30 - Article 286 CGI
"""
from __future__ import annotations


import hashlib
import hmac
import json
import logging
import secrets
import uuid as uuid_module
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.types import JSON, UniversalUUID
from app.db import Base

logger = logging.getLogger(__name__)


# ============================================================================
# MODÈLES NF525
# ============================================================================

class NF525EventType(str, Enum):
    """Types d'événements NF525 à journaliser."""
    # Opérations de vente
    TICKET_CREATED = "TICKET_CREATED"
    TICKET_COMPLETED = "TICKET_COMPLETED"
    TICKET_VOIDED = "TICKET_VOIDED"
    PAYMENT_ADDED = "PAYMENT_ADDED"
    REFUND_CREATED = "REFUND_CREATED"

    # Opérations de caisse
    SESSION_OPENED = "SESSION_OPENED"
    SESSION_CLOSED = "SESSION_CLOSED"
    CASH_IN = "CASH_IN"
    CASH_OUT = "CASH_OUT"
    Z_REPORT = "Z_REPORT"
    X_REPORT = "X_REPORT"

    # Opérations système
    SYSTEM_START = "SYSTEM_START"
    SYSTEM_STOP = "SYSTEM_STOP"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"

    # Archivage
    ARCHIVE_CREATED = "ARCHIVE_CREATED"
    ARCHIVE_VERIFIED = "ARCHIVE_VERIFIED"


class NF525EventLog(Base):
    """Journal d'événements NF525 (immuable)."""
    __tablename__ = "nf525_event_log"

    id: Mapped[UniversalUUID] = mapped_column(UniversalUUID, primary_key=True, default=uuid_module.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Séquence (inaltérable)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Événement
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Références
    terminal_id: Mapped[str | None] = mapped_column(String(50))
    session_id: Mapped[str | None] = mapped_column(String(50))
    transaction_id: Mapped[str | None] = mapped_column(String(50))
    receipt_number: Mapped[str | None] = mapped_column(String(50))
    user_id: Mapped[str | None] = mapped_column(String(50))

    # Données de l'événement
    event_data: Mapped[dict | None] = mapped_column(JSON)

    # Montants (pour vérification cumulative)
    amount_ht: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    amount_tva: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    amount_ttc: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # Totaux cumulatifs (Grand Total - obligatoire NF525)
    cumulative_total_ht: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cumulative_total_tva: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cumulative_total_ttc: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cumulative_transaction_count: Mapped[int | None] = mapped_column(Integer)

    # Chaîne de hachage (inaltérabilité)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    current_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hash_chain_valid: Mapped[bool] = mapped_column(Boolean, default=True)

    # Signature
    signature: Mapped[str | None] = mapped_column(String(128))

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_nf525_seq', 'tenant_id', 'sequence_number', unique=True),
        Index('idx_nf525_hash', 'tenant_id', 'current_hash'),
        Index('idx_nf525_date', 'tenant_id', 'event_timestamp'),
        Index('idx_nf525_type', 'tenant_id', 'event_type'),
    )


class NF525Certificate(Base):
    """Certificat de conformité NF525."""
    __tablename__ = "nf525_certificates"

    id: Mapped[UniversalUUID] = mapped_column(UniversalUUID, primary_key=True, default=uuid_module.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Identification logiciel
    software_name: Mapped[str] = mapped_column(String(100), default="AZALSCORE")
    software_version: Mapped[str] = mapped_column(String(50))
    software_editor: Mapped[str] = mapped_column(String(100), default="AZALS Technologies")

    # Certificat NF525
    certificate_number: Mapped[str | None] = mapped_column(String(100))
    certificate_date: Mapped[datetime | None] = mapped_column(DateTime)
    certificate_expiry: Mapped[datetime | None] = mapped_column(DateTime)
    certifying_body: Mapped[str | None] = mapped_column(String(100))

    # Clé de signature (HMAC)
    signing_key_hash: Mapped[str] = mapped_column(String(64))  # Hash de la clé, pas la clé elle-même
    signing_key_created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Initialisation chaîne
    genesis_hash: Mapped[str] = mapped_column(String(64))  # Premier hash de la chaîne
    genesis_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Statut
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NF525Archive(Base):
    """Archive périodique NF525."""
    __tablename__ = "nf525_archives"

    id: Mapped[UniversalUUID] = mapped_column(UniversalUUID, primary_key=True, default=uuid_module.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Période
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    archive_type: Mapped[str] = mapped_column(String(20))  # daily, monthly, annual

    # Séquences incluses
    first_sequence: Mapped[int] = mapped_column(Integer)
    last_sequence: Mapped[int] = mapped_column(Integer)
    event_count: Mapped[int] = mapped_column(Integer)

    # Totaux de l'archive
    total_ht: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    total_tva: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    total_ttc: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    transaction_count: Mapped[int] = mapped_column(Integer)

    # Intégrité
    first_hash: Mapped[str] = mapped_column(String(64))
    last_hash: Mapped[str] = mapped_column(String(64))
    archive_hash: Mapped[str] = mapped_column(String(64))  # Hash de l'archive complète

    # Fichier
    file_path: Mapped[str | None] = mapped_column(String(500))
    file_size: Mapped[int | None] = mapped_column(Integer)

    # Vérification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    verification_result: Mapped[str | None] = mapped_column(Text)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str | None] = mapped_column(String(50))


class NF525GrandTotal(Base):
    """Totaux cumulatifs par terminal (Grand Total NF525)."""
    __tablename__ = "nf525_grand_totals"

    id: Mapped[UniversalUUID] = mapped_column(UniversalUUID, primary_key=True, default=uuid_module.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    terminal_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # Date du jour
    report_date: Mapped[date] = mapped_column(DateTime, nullable=False)

    # Compteurs
    first_ticket_number: Mapped[str | None] = mapped_column(String(50))
    last_ticket_number: Mapped[str | None] = mapped_column(String(50))
    ticket_count: Mapped[int] = mapped_column(Integer, default=0)
    void_count: Mapped[int] = mapped_column(Integer, default=0)

    # Totaux du jour
    daily_total_ht: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    daily_total_tva: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    daily_total_ttc: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    daily_refund_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # Grand Total cumulatif depuis initialisation
    grand_total_ht: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    grand_total_tva: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    grand_total_ttc: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    grand_total_transactions: Mapped[int] = mapped_column(Integer, default=0)

    # Intégrité
    day_start_hash: Mapped[str | None] = mapped_column(String(64))
    day_end_hash: Mapped[str | None] = mapped_column(String(64))
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_nf525_gt_date', 'tenant_id', 'terminal_id', 'report_date', unique=True),
    )


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class NF525ComplianceStatus:
    """Statut de conformité NF525."""
    is_compliant: bool
    certificate_valid: bool
    chain_integrity: bool
    archiving_current: bool
    last_verification: datetime | None
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    score: int = 0  # 0-100


@dataclass
class NF525VerificationResult:
    """Résultat de vérification d'intégrité."""
    is_valid: bool
    checked_from: int
    checked_to: int
    total_checked: int
    broken_at: int | None = None
    error_message: str | None = None
    execution_time_ms: int = 0


@dataclass
class NF525ArchiveResult:
    """Résultat de création d'archive."""
    success: bool
    archive_id: int | None = None
    file_path: str | None = None
    event_count: int = 0
    archive_hash: str | None = None
    error_message: str | None = None


# ============================================================================
# SERVICE NF525
# ============================================================================

class NF525ComplianceService:
    """Service de conformité NF525 pour logiciel de caisse."""

    # Identifiant logiciel (pour attestation)
    SOFTWARE_NAME = "AZALSCORE"
    SOFTWARE_VERSION = "3.0.0"
    SOFTWARE_EDITOR = "AZALS Technologies"

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self._signing_key: bytes | None = None

    # ========================================================================
    # INITIALISATION ET CERTIFICAT
    # ========================================================================

    def initialize_certificate(
        self,
        certificate_number: str | None = None,
        certificate_date: datetime | None = None,
        certifying_body: str = "LNE"
    ) -> NF525Certificate:
        """
        Initialiser le certificat NF525 pour le tenant.
        À faire une seule fois lors de la mise en service.
        """
        logger.info(
            "Initializing NF525 certificate | tenant=%s",
            self.tenant_id
        )

        # Vérifier qu'il n'existe pas déjà
        existing = self.db.query(NF525Certificate).filter(
            NF525Certificate.tenant_id == self.tenant_id,
            NF525Certificate.is_active == True
        ).first()

        if existing:
            raise ValueError("Un certificat NF525 actif existe déjà pour ce tenant")

        # Générer clé de signature
        signing_key = secrets.token_bytes(32)
        signing_key_hash = hashlib.sha256(signing_key).hexdigest()

        # Créer hash de genèse
        genesis_data = json.dumps({
            "tenant_id": self.tenant_id,
            "software": self.SOFTWARE_NAME,
            "version": self.SOFTWARE_VERSION,
            "timestamp": datetime.utcnow().isoformat()
        }, sort_keys=True)
        genesis_hash = hashlib.sha256(genesis_data.encode()).hexdigest()

        # Créer certificat
        cert = NF525Certificate(
            tenant_id=self.tenant_id,
            software_name=self.SOFTWARE_NAME,
            software_version=self.SOFTWARE_VERSION,
            software_editor=self.SOFTWARE_EDITOR,
            certificate_number=certificate_number,
            certificate_date=certificate_date,
            certificate_expiry=certificate_date + timedelta(days=365) if certificate_date else None,
            certifying_body=certifying_body,
            signing_key_hash=signing_key_hash,
            genesis_hash=genesis_hash,
            genesis_timestamp=datetime.utcnow(),
            is_active=True
        )

        self.db.add(cert)
        self.db.commit()
        self.db.refresh(cert)

        # Stocker la clé de signature de manière sécurisée (à implémenter avec vault)
        # Pour l'instant, on la retourne pour stockage externe
        logger.info(
            "NF525 certificate initialized | tenant=%s cert_id=%s",
            self.tenant_id, cert.id
        )

        # Enregistrer événement système
        self.log_event(
            event_type=NF525EventType.SYSTEM_START,
            event_data={
                "action": "certificate_initialized",
                "certificate_id": cert.id,
                "genesis_hash": genesis_hash
            }
        )

        return cert

    def get_certificate(self) -> NF525Certificate | None:
        """Récupérer le certificat actif."""
        return self.db.query(NF525Certificate).filter(
            NF525Certificate.tenant_id == self.tenant_id,
            NF525Certificate.is_active == True
        ).first()

    # ========================================================================
    # CHAÎNE DE HACHAGE
    # ========================================================================

    def _compute_hash(self, data: dict, previous_hash: str) -> str:
        """
        Calculer le hash SHA-256 d'un événement.
        Inclut le hash précédent pour créer la chaîne.
        """
        # Normaliser les données pour un hachage déterministe
        normalized = {
            "previous_hash": previous_hash,
            "sequence": data.get("sequence_number"),
            "type": data.get("event_type"),
            "timestamp": data.get("event_timestamp"),
            "terminal_id": data.get("terminal_id"),
            "receipt_number": data.get("receipt_number"),
            "amount_ttc": str(data.get("amount_ttc", "0")),
            "cumulative_ttc": str(data.get("cumulative_total_ttc", "0"))
        }

        hash_input = json.dumps(normalized, sort_keys=True).encode('utf-8')
        return hashlib.sha256(hash_input).hexdigest()

    def _sign_hash(self, hash_value: str, key: bytes) -> str:
        """Signer un hash avec HMAC-SHA256."""
        return hmac.new(key, hash_value.encode(), hashlib.sha256).hexdigest()

    def _get_previous_event(self) -> NF525EventLog | None:
        """Récupérer le dernier événement de la chaîne."""
        return self.db.query(NF525EventLog).filter(
            NF525EventLog.tenant_id == self.tenant_id
        ).order_by(NF525EventLog.sequence_number.desc()).first()

    def _get_next_sequence(self) -> int:
        """Obtenir le prochain numéro de séquence."""
        last = self._get_previous_event()
        return (last.sequence_number + 1) if last else 1

    def _get_cumulative_totals(self) -> tuple[Decimal, Decimal, Decimal, int]:
        """Obtenir les totaux cumulatifs actuels."""
        last = self._get_previous_event()
        if last:
            return (
                last.cumulative_total_ht or Decimal("0"),
                last.cumulative_total_tva or Decimal("0"),
                last.cumulative_total_ttc or Decimal("0"),
                last.cumulative_transaction_count or 0
            )
        return Decimal("0"), Decimal("0"), Decimal("0"), 0

    # ========================================================================
    # JOURNALISATION DES ÉVÉNEMENTS
    # ========================================================================

    def log_event(
        self,
        event_type: NF525EventType,
        terminal_id: str | None = None,
        session_id: str | None = None,
        transaction_id: str | None = None,
        receipt_number: str | None = None,
        user_id: str | None = None,
        amount_ht: Decimal | None = None,
        amount_tva: Decimal | None = None,
        amount_ttc: Decimal | None = None,
        event_data: dict | None = None
    ) -> NF525EventLog:
        """
        Enregistrer un événement dans le journal NF525.
        Chaque événement est chaîné cryptographiquement.
        """
        # Récupérer certificat
        cert = self.get_certificate()
        if not cert:
            raise ValueError("Aucun certificat NF525 initialisé")

        # Obtenir séquence et hash précédent
        sequence = self._get_next_sequence()
        previous = self._get_previous_event()
        previous_hash = previous.current_hash if previous else cert.genesis_hash

        # Calculer totaux cumulatifs
        cum_ht, cum_tva, cum_ttc, cum_count = self._get_cumulative_totals()

        # Mettre à jour si c'est une transaction
        if event_type in (NF525EventType.TICKET_COMPLETED, NF525EventType.REFUND_CREATED):
            cum_ht += amount_ht or Decimal("0")
            cum_tva += amount_tva or Decimal("0")
            cum_ttc += amount_ttc or Decimal("0")
            cum_count += 1

        # Préparer données pour hash
        event_timestamp = datetime.utcnow()
        hash_data = {
            "sequence_number": sequence,
            "event_type": event_type.value,
            "event_timestamp": event_timestamp.isoformat(),
            "terminal_id": terminal_id,
            "receipt_number": receipt_number,
            "amount_ttc": amount_ttc,
            "cumulative_total_ttc": cum_ttc
        }

        # Calculer hash
        current_hash = self._compute_hash(hash_data, previous_hash)

        # Créer événement
        event = NF525EventLog(
            tenant_id=self.tenant_id,
            sequence_number=sequence,
            event_type=event_type.value,
            event_timestamp=event_timestamp,
            terminal_id=terminal_id,
            session_id=session_id,
            transaction_id=transaction_id,
            receipt_number=receipt_number,
            user_id=user_id,
            event_data=event_data,
            amount_ht=amount_ht,
            amount_tva=amount_tva,
            amount_ttc=amount_ttc,
            cumulative_total_ht=cum_ht,
            cumulative_total_tva=cum_tva,
            cumulative_total_ttc=cum_ttc,
            cumulative_transaction_count=cum_count,
            previous_hash=previous_hash,
            current_hash=current_hash,
            hash_chain_valid=True
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        logger.debug(
            "NF525 event logged | seq=%s type=%s hash=%s",
            sequence, event_type.value, current_hash[:16]
        )

        return event

    def log_ticket(
        self,
        terminal_id: str,
        session_id: str,
        transaction_id: str,
        receipt_number: str,
        user_id: str,
        amount_ht: Decimal,
        amount_tva: Decimal,
        amount_ttc: Decimal,
        is_completed: bool = True,
        line_count: int = 0,
        payment_methods: list[str] | None = None
    ) -> NF525EventLog:
        """Enregistrer un ticket de caisse."""
        event_type = NF525EventType.TICKET_COMPLETED if is_completed else NF525EventType.TICKET_CREATED

        return self.log_event(
            event_type=event_type,
            terminal_id=terminal_id,
            session_id=session_id,
            transaction_id=transaction_id,
            receipt_number=receipt_number,
            user_id=user_id,
            amount_ht=amount_ht,
            amount_tva=amount_tva,
            amount_ttc=amount_ttc,
            event_data={
                "line_count": line_count,
                "payment_methods": payment_methods or []
            }
        )

    def log_void(
        self,
        terminal_id: str,
        session_id: str,
        transaction_id: str,
        receipt_number: str,
        user_id: str,
        void_reason: str,
        original_amount_ttc: Decimal
    ) -> NF525EventLog:
        """Enregistrer une annulation de ticket."""
        return self.log_event(
            event_type=NF525EventType.TICKET_VOIDED,
            terminal_id=terminal_id,
            session_id=session_id,
            transaction_id=transaction_id,
            receipt_number=receipt_number,
            user_id=user_id,
            amount_ttc=-original_amount_ttc,  # Négatif pour annulation
            event_data={
                "void_reason": void_reason,
                "original_amount": str(original_amount_ttc)
            }
        )

    def log_z_report(
        self,
        terminal_id: str,
        session_id: str,
        user_id: str,
        report_data: dict
    ) -> NF525EventLog:
        """Enregistrer un rapport Z (clôture journalière)."""
        return self.log_event(
            event_type=NF525EventType.Z_REPORT,
            terminal_id=terminal_id,
            session_id=session_id,
            user_id=user_id,
            event_data=report_data
        )

    # ========================================================================
    # VÉRIFICATION D'INTÉGRITÉ
    # ========================================================================

    def verify_chain_integrity(
        self,
        from_sequence: int | None = None,
        to_sequence: int | None = None
    ) -> NF525VerificationResult:
        """
        Vérifier l'intégrité de la chaîne de hachage.
        Retourne le premier événement où la chaîne est rompue.
        """
        import time
        start_time = time.time()

        logger.info(
            "Verifying NF525 chain integrity | tenant=%s from=%s to=%s",
            self.tenant_id, from_sequence, to_sequence
        )

        # Récupérer certificat
        cert = self.get_certificate()
        if not cert:
            return NF525VerificationResult(
                is_valid=False,
                checked_from=0,
                checked_to=0,
                total_checked=0,
                error_message="No certificate found"
            )

        # Construire requête
        query = self.db.query(NF525EventLog).filter(
            NF525EventLog.tenant_id == self.tenant_id
        )

        if from_sequence:
            query = query.filter(NF525EventLog.sequence_number >= from_sequence)
        if to_sequence:
            query = query.filter(NF525EventLog.sequence_number <= to_sequence)

        events = query.order_by(NF525EventLog.sequence_number).all()

        if not events:
            return NF525VerificationResult(
                is_valid=True,
                checked_from=0,
                checked_to=0,
                total_checked=0
            )

        # Vérifier chaque événement
        previous_hash = cert.genesis_hash
        if from_sequence and from_sequence > 1:
            # Récupérer le hash du dernier événement avant la plage
            prev_event = self.db.query(NF525EventLog).filter(
                NF525EventLog.tenant_id == self.tenant_id,
                NF525EventLog.sequence_number == from_sequence - 1
            ).first()
            if prev_event:
                previous_hash = prev_event.current_hash

        for event in events:
            # Vérifier que le hash précédent correspond
            if event.previous_hash != previous_hash:
                logger.error(
                    "Chain broken at sequence %s | expected=%s actual=%s",
                    event.sequence_number, previous_hash[:16], event.previous_hash[:16]
                )

                # Marquer l'événement
                event.hash_chain_valid = False
                self.db.commit()

                return NF525VerificationResult(
                    is_valid=False,
                    checked_from=events[0].sequence_number,
                    checked_to=event.sequence_number,
                    total_checked=events.index(event) + 1,
                    broken_at=event.sequence_number,
                    error_message=f"Chain broken at sequence {event.sequence_number}",
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )

            # Recalculer le hash
            hash_data = {
                "sequence_number": event.sequence_number,
                "event_type": event.event_type,
                "event_timestamp": event.event_timestamp.isoformat(),
                "terminal_id": event.terminal_id,
                "receipt_number": event.receipt_number,
                "amount_ttc": event.amount_ttc,
                "cumulative_total_ttc": event.cumulative_total_ttc
            }
            computed_hash = self._compute_hash(hash_data, previous_hash)

            if computed_hash != event.current_hash:
                logger.error(
                    "Hash mismatch at sequence %s | expected=%s actual=%s",
                    event.sequence_number, computed_hash[:16], event.current_hash[:16]
                )

                event.hash_chain_valid = False
                self.db.commit()

                return NF525VerificationResult(
                    is_valid=False,
                    checked_from=events[0].sequence_number,
                    checked_to=event.sequence_number,
                    total_checked=events.index(event) + 1,
                    broken_at=event.sequence_number,
                    error_message=f"Hash mismatch at sequence {event.sequence_number}",
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )

            previous_hash = event.current_hash

        logger.info(
            "Chain integrity verified | tenant=%s events=%s",
            self.tenant_id, len(events)
        )

        return NF525VerificationResult(
            is_valid=True,
            checked_from=events[0].sequence_number,
            checked_to=events[-1].sequence_number,
            total_checked=len(events),
            execution_time_ms=int((time.time() - start_time) * 1000)
        )

    # ========================================================================
    # ARCHIVAGE
    # ========================================================================

    def create_archive(
        self,
        period_start: datetime,
        period_end: datetime,
        archive_type: str = "daily",
        created_by: str | None = None
    ) -> NF525ArchiveResult:
        """
        Créer une archive sécurisée pour une période.
        L'archive contient tous les événements et peut être vérifiée.
        """
        logger.info(
            "Creating NF525 archive | tenant=%s type=%s from=%s to=%s",
            self.tenant_id, archive_type, period_start, period_end
        )

        # Récupérer événements de la période
        events = self.db.query(NF525EventLog).filter(
            NF525EventLog.tenant_id == self.tenant_id,
            NF525EventLog.event_timestamp >= period_start,
            NF525EventLog.event_timestamp <= period_end
        ).order_by(NF525EventLog.sequence_number).all()

        if not events:
            return NF525ArchiveResult(
                success=False,
                error_message="No events found for the specified period"
            )

        # Vérifier intégrité avant archivage
        verification = self.verify_chain_integrity(
            from_sequence=events[0].sequence_number,
            to_sequence=events[-1].sequence_number
        )

        if not verification.is_valid:
            return NF525ArchiveResult(
                success=False,
                error_message=f"Chain integrity check failed: {verification.error_message}"
            )

        # Calculer totaux
        total_ht = sum(e.amount_ht or Decimal("0") for e in events)
        total_tva = sum(e.amount_tva or Decimal("0") for e in events)
        total_ttc = sum(e.amount_ttc or Decimal("0") for e in events)
        tx_count = sum(
            1 for e in events
            if e.event_type in (NF525EventType.TICKET_COMPLETED.value, NF525EventType.REFUND_CREATED.value)
        )

        # Calculer hash de l'archive
        archive_data = {
            "tenant_id": self.tenant_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "first_sequence": events[0].sequence_number,
            "last_sequence": events[-1].sequence_number,
            "first_hash": events[0].current_hash,
            "last_hash": events[-1].current_hash,
            "event_count": len(events),
            "total_ttc": str(total_ttc)
        }
        archive_hash = hashlib.sha256(
            json.dumps(archive_data, sort_keys=True).encode()
        ).hexdigest()

        # Créer archive
        archive = NF525Archive(
            tenant_id=self.tenant_id,
            period_start=period_start,
            period_end=period_end,
            archive_type=archive_type,
            first_sequence=events[0].sequence_number,
            last_sequence=events[-1].sequence_number,
            event_count=len(events),
            total_ht=total_ht,
            total_tva=total_tva,
            total_ttc=total_ttc,
            transaction_count=tx_count,
            first_hash=events[0].current_hash,
            last_hash=events[-1].current_hash,
            archive_hash=archive_hash,
            is_verified=True,
            verified_at=datetime.utcnow(),
            created_by=created_by
        )

        self.db.add(archive)
        self.db.commit()
        self.db.refresh(archive)

        # Enregistrer événement d'archivage
        self.log_event(
            event_type=NF525EventType.ARCHIVE_CREATED,
            event_data={
                "archive_id": archive.id,
                "archive_type": archive_type,
                "event_count": len(events),
                "archive_hash": archive_hash
            }
        )

        logger.info(
            "NF525 archive created | tenant=%s archive_id=%s events=%s",
            self.tenant_id, archive.id, len(events)
        )

        return NF525ArchiveResult(
            success=True,
            archive_id=archive.id,
            event_count=len(events),
            archive_hash=archive_hash
        )

    def verify_archive(self, archive_id: int) -> NF525VerificationResult:
        """Vérifier l'intégrité d'une archive."""
        archive = self.db.query(NF525Archive).filter(
            NF525Archive.tenant_id == self.tenant_id,
            NF525Archive.id == archive_id
        ).first()

        if not archive:
            return NF525VerificationResult(
                is_valid=False,
                checked_from=0,
                checked_to=0,
                total_checked=0,
                error_message="Archive not found"
            )

        # Vérifier la chaîne
        result = self.verify_chain_integrity(
            from_sequence=archive.first_sequence,
            to_sequence=archive.last_sequence
        )

        # Mettre à jour statut archive
        archive.is_verified = result.is_valid
        archive.verified_at = datetime.utcnow()
        archive.verification_result = "OK" if result.is_valid else result.error_message
        self.db.commit()

        return result

    # ========================================================================
    # CONFORMITÉ GLOBALE
    # ========================================================================

    def check_compliance(self) -> NF525ComplianceStatus:
        """
        Vérifier la conformité globale NF525.
        Retourne un statut détaillé avec score.
        """
        logger.info("Checking NF525 compliance | tenant=%s", self.tenant_id)

        issues = []
        warnings = []
        score = 100

        # 1. Vérifier certificat
        cert = self.get_certificate()
        certificate_valid = cert is not None and cert.is_active

        if not certificate_valid:
            issues.append("Aucun certificat NF525 actif")
            score -= 30
        elif cert.certificate_expiry and cert.certificate_expiry < datetime.utcnow():
            issues.append("Certificat NF525 expiré")
            score -= 20

        # 2. Vérifier chaîne récente (derniers 1000 événements)
        chain_integrity = True
        last_event = self._get_previous_event()

        if last_event:
            from_seq = max(1, last_event.sequence_number - 1000)
            verification = self.verify_chain_integrity(from_sequence=from_seq)
            chain_integrity = verification.is_valid

            if not chain_integrity:
                issues.append(f"Rupture chaîne détectée à la séquence {verification.broken_at}")
                score -= 50
        else:
            warnings.append("Aucun événement enregistré")

        # 3. Vérifier archivage
        archiving_current = True
        last_archive = self.db.query(NF525Archive).filter(
            NF525Archive.tenant_id == self.tenant_id
        ).order_by(NF525Archive.period_end.desc()).first()

        if last_archive:
            days_since_archive = (datetime.utcnow() - last_archive.period_end).days
            if days_since_archive > 30:
                warnings.append(f"Dernier archivage il y a {days_since_archive} jours")
                archiving_current = False
                score -= 10
        else:
            warnings.append("Aucune archive créée")
            archiving_current = False
            score -= 5

        # 4. Vérifier numérotation séquentielle
        gaps = self.db.query(
            NF525EventLog.sequence_number
        ).filter(
            NF525EventLog.tenant_id == self.tenant_id
        ).order_by(NF525EventLog.sequence_number).all()

        if gaps:
            seq_numbers = [g[0] for g in gaps]
            expected = list(range(seq_numbers[0], seq_numbers[-1] + 1))
            if seq_numbers != expected:
                issues.append("Trous détectés dans la numérotation séquentielle")
                score -= 20

        # 5. Vérifier événements invalides
        invalid_count = self.db.query(func.count(NF525EventLog.id)).filter(
            NF525EventLog.tenant_id == self.tenant_id,
            NF525EventLog.hash_chain_valid == False
        ).scalar()

        if invalid_count > 0:
            issues.append(f"{invalid_count} événements avec chaîne invalide")
            score -= min(30, invalid_count * 5)

        # Déterminer conformité globale
        is_compliant = len(issues) == 0 and certificate_valid and chain_integrity

        return NF525ComplianceStatus(
            is_compliant=is_compliant,
            certificate_valid=certificate_valid,
            chain_integrity=chain_integrity,
            archiving_current=archiving_current,
            last_verification=datetime.utcnow(),
            issues=issues,
            warnings=warnings,
            score=max(0, score)
        )

    # ========================================================================
    # ATTESTATION
    # ========================================================================

    def generate_attestation(self) -> dict:
        """
        Générer l'attestation de conformité NF525.
        Document requis par l'administration fiscale.
        """
        cert = self.get_certificate()
        if not cert:
            raise ValueError("Aucun certificat NF525 initialisé")

        compliance = self.check_compliance()
        last_event = self._get_previous_event()

        # Statistiques globales
        total_events = self.db.query(func.count(NF525EventLog.id)).filter(
            NF525EventLog.tenant_id == self.tenant_id
        ).scalar()

        total_transactions = self.db.query(func.count(NF525EventLog.id)).filter(
            NF525EventLog.tenant_id == self.tenant_id,
            NF525EventLog.event_type == NF525EventType.TICKET_COMPLETED.value
        ).scalar()

        # Grand total
        grand_total = self.db.query(
            func.sum(NF525EventLog.amount_ttc)
        ).filter(
            NF525EventLog.tenant_id == self.tenant_id,
            NF525EventLog.event_type == NF525EventType.TICKET_COMPLETED.value
        ).scalar() or Decimal("0")

        return {
            "attestation": {
                "type": "ATTESTATION_NF525",
                "generated_at": datetime.utcnow().isoformat(),
                "tenant_id": self.tenant_id
            },
            "software": {
                "name": cert.software_name,
                "version": cert.software_version,
                "editor": cert.software_editor
            },
            "certificate": {
                "number": cert.certificate_number,
                "date": cert.certificate_date.isoformat() if cert.certificate_date else None,
                "expiry": cert.certificate_expiry.isoformat() if cert.certificate_expiry else None,
                "certifying_body": cert.certifying_body,
                "is_valid": cert.is_active and (
                    not cert.certificate_expiry or cert.certificate_expiry > datetime.utcnow()
                )
            },
            "chain_info": {
                "genesis_hash": cert.genesis_hash,
                "genesis_timestamp": cert.genesis_timestamp.isoformat(),
                "last_sequence": last_event.sequence_number if last_event else 0,
                "last_hash": last_event.current_hash if last_event else cert.genesis_hash,
                "total_events": total_events
            },
            "statistics": {
                "total_transactions": total_transactions,
                "grand_total_ttc": str(grand_total),
                "cumulative_total_ttc": str(last_event.cumulative_total_ttc) if last_event else "0"
            },
            "compliance": {
                "is_compliant": compliance.is_compliant,
                "score": compliance.score,
                "certificate_valid": compliance.certificate_valid,
                "chain_integrity": compliance.chain_integrity,
                "archiving_current": compliance.archiving_current,
                "issues": compliance.issues,
                "warnings": compliance.warnings
            },
            "legal_notice": (
                "Ce document atteste que le logiciel de caisse utilisé répond aux "
                "conditions d'inaltérabilité, de sécurisation, de conservation et "
                "d'archivage des données prévues au 3° bis du I de l'article 286 "
                "du code général des impôts."
            )
        }

    # ========================================================================
    # EXPORT FISCAL
    # ========================================================================

    def export_fiscal_data(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> dict:
        """
        Exporter les données fiscales pour contrôle.
        Format conforme aux exigences de l'administration.
        """
        events = self.db.query(NF525EventLog).filter(
            NF525EventLog.tenant_id == self.tenant_id,
            NF525EventLog.event_timestamp >= period_start,
            NF525EventLog.event_timestamp <= period_end
        ).order_by(NF525EventLog.sequence_number).all()

        # Vérifier intégrité
        if events:
            verification = self.verify_chain_integrity(
                from_sequence=events[0].sequence_number,
                to_sequence=events[-1].sequence_number
            )
        else:
            verification = NF525VerificationResult(
                is_valid=True, checked_from=0, checked_to=0, total_checked=0
            )

        # Préparer export
        return {
            "export_info": {
                "type": "EXPORT_FISCAL_NF525",
                "generated_at": datetime.utcnow().isoformat(),
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat()
            },
            "integrity": {
                "is_valid": verification.is_valid,
                "first_sequence": verification.checked_from,
                "last_sequence": verification.checked_to,
                "event_count": verification.total_checked
            },
            "events": [
                {
                    "sequence": e.sequence_number,
                    "type": e.event_type,
                    "timestamp": e.event_timestamp.isoformat(),
                    "terminal_id": e.terminal_id,
                    "receipt_number": e.receipt_number,
                    "amount_ht": str(e.amount_ht) if e.amount_ht else None,
                    "amount_tva": str(e.amount_tva) if e.amount_tva else None,
                    "amount_ttc": str(e.amount_ttc) if e.amount_ttc else None,
                    "cumulative_ttc": str(e.cumulative_total_ttc),
                    "hash": e.current_hash
                }
                for e in events
            ],
            "totals": {
                "transaction_count": sum(
                    1 for e in events
                    if e.event_type == NF525EventType.TICKET_COMPLETED.value
                ),
                "void_count": sum(
                    1 for e in events
                    if e.event_type == NF525EventType.TICKET_VOIDED.value
                ),
                "total_ht": str(sum(e.amount_ht or Decimal("0") for e in events)),
                "total_tva": str(sum(e.amount_tva or Decimal("0") for e in events)),
                "total_ttc": str(sum(e.amount_ttc or Decimal("0") for e in events))
            }
        }
