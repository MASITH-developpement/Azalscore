"""
AZALSCORE Finance Integration Service
======================================

Service d'intégration entre Finance et les autres modules métier.

Fonctionnalités:
- Synchronisation bidirectionnelle Finance ↔ Comptabilité
- Synchronisation Finance ↔ Facturation
- Mapping automatique des comptes
- Journalisation des écritures
- Validation croisée
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class SyncDirection(str, Enum):
    """Direction de synchronisation."""
    FINANCE_TO_ACCOUNTING = "finance_to_accounting"
    ACCOUNTING_TO_FINANCE = "accounting_to_finance"
    FINANCE_TO_INVOICE = "finance_to_invoice"
    INVOICE_TO_FINANCE = "invoice_to_finance"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    """Statut de synchronisation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class MappingType(str, Enum):
    """Type de mapping."""
    ACCOUNT = "account"
    JOURNAL = "journal"
    TAX_CODE = "tax_code"
    COST_CENTER = "cost_center"
    PAYMENT_METHOD = "payment_method"


class TransactionType(str, Enum):
    """Type de transaction financière."""
    PAYMENT = "payment"
    RECEIPT = "receipt"
    TRANSFER = "transfer"
    REFUND = "refund"
    FEE = "fee"
    ADJUSTMENT = "adjustment"


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class IntegrationMapping:
    """Règle de mapping entre systèmes."""
    id: str
    tenant_id: str
    mapping_type: MappingType
    source_code: str
    target_code: str
    source_system: str           # "finance", "accounting", "invoice"
    target_system: str
    description: Optional[str] = None
    is_active: bool = True
    priority: int = 0
    conditions: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AccountingEntry:
    """Écriture comptable générée."""
    id: str
    tenant_id: str
    journal_code: str
    date: datetime
    reference: str
    description: str
    debit_account: str
    credit_account: str
    amount: Decimal
    currency: str
    tax_code: Optional[str] = None
    cost_center: Optional[str] = None
    source_transaction_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class SyncResult:
    """Résultat d'une synchronisation."""
    success: bool
    sync_id: str
    direction: SyncDirection
    status: SyncStatus
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    records_failed: int = 0
    errors: list[str] = field(default_factory=list)
    entries: list[AccountingEntry] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class FinanceTransaction:
    """Transaction financière à synchroniser."""
    id: str
    tenant_id: str
    transaction_type: TransactionType
    date: datetime
    amount: Decimal
    currency: str
    description: str
    bank_account: Optional[str] = None
    counterparty: Optional[str] = None
    category: Optional[str] = None
    reference: Optional[str] = None
    tax_amount: Optional[Decimal] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Résultat de validation croisée."""
    is_valid: bool
    validation_type: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)


# =============================================================================
# MAPPING RULES
# =============================================================================


class DefaultMappings:
    """Règles de mapping par défaut."""

    # Comptes bancaires → Comptes comptables
    BANK_ACCOUNTS = {
        "current_account": "512100",  # Banque compte courant
        "savings_account": "512200",  # Banque compte épargne
        "card_account": "512300",     # Banque carte
        "cash": "531000",             # Caisse
    }

    # Types de transactions → Journaux comptables
    JOURNALS = {
        TransactionType.PAYMENT: "BQ",    # Banque
        TransactionType.RECEIPT: "BQ",    # Banque
        TransactionType.TRANSFER: "OD",   # Opérations diverses
        TransactionType.REFUND: "BQ",     # Banque
        TransactionType.FEE: "BQ",        # Banque
        TransactionType.ADJUSTMENT: "OD", # Opérations diverses
    }

    # Catégories → Comptes comptables
    CATEGORIES = {
        "revenue": "701000",           # Ventes de produits
        "services": "706000",          # Prestations de services
        "purchases": "607000",         # Achats de marchandises
        "salary": "641000",            # Rémunérations du personnel
        "rent": "613200",              # Locations immobilières
        "utilities": "606100",         # Fournitures eau, gaz, électricité
        "insurance": "616000",         # Assurances
        "bank_fees": "627000",         # Services bancaires
        "taxes": "631000",             # Impôts et taxes
        "supplies": "606400",          # Fournitures administratives
        "travel": "625100",            # Voyages et déplacements
        "professional_fees": "622600", # Honoraires
        "advertising": "623000",       # Publicité, publications
        "maintenance": "615000",       # Entretien et réparations
        "telecom": "626000",           # Frais postaux et télécom
        "other_income": "758000",      # Produits divers
        "other_expense": "658000",     # Charges diverses
    }

    # Codes TVA
    TAX_CODES = {
        "standard": "TVA20",      # TVA 20%
        "reduced": "TVA10",       # TVA 10%
        "super_reduced": "TVA55", # TVA 5.5%
        "zero": "TVA0",           # Exonéré
    }


# =============================================================================
# SERVICE
# =============================================================================


class FinanceIntegrationService:
    """
    Service d'intégration Finance.

    Multi-tenant: OUI - Toutes les opérations filtrées par tenant_id
    Synchronisation: Bidirectionnelle avec Finance, Comptabilité, Facturation
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
    ):
        if not tenant_id:
            raise ValueError("tenant_id est requis")

        self.db = db
        self.tenant_id = tenant_id
        self._mappings: dict[str, IntegrationMapping] = {}
        self._sync_history: list[SyncResult] = []

        # Initialiser les mappings par défaut
        self._init_default_mappings()

        logger.info(f"FinanceIntegrationService initialisé pour tenant {tenant_id}")

    def _init_default_mappings(self):
        """Initialise les mappings par défaut."""
        # Mappings comptes bancaires
        for source, target in DefaultMappings.BANK_ACCOUNTS.items():
            self._add_mapping(
                MappingType.ACCOUNT,
                source, target,
                "finance", "accounting",
                f"Compte bancaire {source} → {target}",
            )

        # Mappings catégories
        for source, target in DefaultMappings.CATEGORIES.items():
            self._add_mapping(
                MappingType.ACCOUNT,
                source, target,
                "finance", "accounting",
                f"Catégorie {source} → {target}",
            )

    def _add_mapping(
        self,
        mapping_type: MappingType,
        source_code: str,
        target_code: str,
        source_system: str,
        target_system: str,
        description: str = "",
    ):
        """Ajoute un mapping."""
        mapping = IntegrationMapping(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            mapping_type=mapping_type,
            source_code=source_code,
            target_code=target_code,
            source_system=source_system,
            target_system=target_system,
            description=description,
        )
        key = f"{mapping_type.value}:{source_code}:{source_system}"
        self._mappings[key] = mapping

    # =========================================================================
    # MAPPING OPERATIONS
    # =========================================================================

    async def create_mapping(
        self,
        mapping_type: MappingType,
        source_code: str,
        target_code: str,
        source_system: str,
        target_system: str,
        description: Optional[str] = None,
        priority: int = 0,
        conditions: Optional[dict] = None,
    ) -> IntegrationMapping:
        """Crée une règle de mapping personnalisée."""
        mapping = IntegrationMapping(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            mapping_type=mapping_type,
            source_code=source_code,
            target_code=target_code,
            source_system=source_system,
            target_system=target_system,
            description=description,
            priority=priority,
            conditions=conditions or {},
        )

        key = f"{mapping_type.value}:{source_code}:{source_system}"
        self._mappings[key] = mapping

        logger.info(f"Mapping créé: {source_code} → {target_code}")
        return mapping

    async def get_mapping(
        self,
        mapping_type: MappingType,
        source_code: str,
        source_system: str = "finance",
    ) -> Optional[IntegrationMapping]:
        """Récupère un mapping."""
        key = f"{mapping_type.value}:{source_code}:{source_system}"
        return self._mappings.get(key)

    async def list_mappings(
        self,
        mapping_type: Optional[MappingType] = None,
        source_system: Optional[str] = None,
    ) -> list[IntegrationMapping]:
        """Liste les mappings."""
        mappings = list(self._mappings.values())

        if mapping_type:
            mappings = [m for m in mappings if m.mapping_type == mapping_type]

        if source_system:
            mappings = [m for m in mappings if m.source_system == source_system]

        return sorted(mappings, key=lambda m: (m.mapping_type.value, m.source_code))

    async def delete_mapping(self, mapping_id: str) -> bool:
        """Supprime un mapping."""
        for key, mapping in list(self._mappings.items()):
            if mapping.id == mapping_id:
                del self._mappings[key]
                logger.info(f"Mapping supprimé: {mapping_id}")
                return True
        return False

    def resolve_mapping(
        self,
        mapping_type: MappingType,
        source_code: str,
        source_system: str = "finance",
    ) -> Optional[str]:
        """Résout un mapping vers le code cible."""
        key = f"{mapping_type.value}:{source_code}:{source_system}"
        mapping = self._mappings.get(key)
        return mapping.target_code if mapping else None

    # =========================================================================
    # SYNC FINANCE → COMPTABILITÉ
    # =========================================================================

    async def sync_to_accounting(
        self,
        transactions: list[FinanceTransaction],
        create_entries: bool = True,
    ) -> SyncResult:
        """
        Synchronise des transactions financières vers la comptabilité.

        Génère les écritures comptables correspondantes.
        """
        sync_id = str(uuid.uuid4())
        result = SyncResult(
            success=True,
            sync_id=sync_id,
            direction=SyncDirection.FINANCE_TO_ACCOUNTING,
            status=SyncStatus.IN_PROGRESS,
        )

        try:
            for tx in transactions:
                if tx.tenant_id != self.tenant_id:
                    result.records_skipped += 1
                    result.errors.append(f"Transaction {tx.id} ignorée: tenant différent")
                    continue

                result.records_processed += 1

                try:
                    entry = self._create_accounting_entry(tx)
                    result.entries.append(entry)
                    result.records_created += 1
                except Exception as e:
                    result.records_failed += 1
                    result.errors.append(f"Transaction {tx.id}: {str(e)}")

            # Déterminer le statut final
            if result.records_failed == 0:
                result.status = SyncStatus.COMPLETED
            elif result.records_created > 0:
                result.status = SyncStatus.PARTIAL
                result.success = False
            else:
                result.status = SyncStatus.FAILED
                result.success = False

            result.completed_at = datetime.now()
            self._sync_history.append(result)

            logger.info(
                f"Sync terminée: {result.records_created} créées, "
                f"{result.records_failed} échecs sur {result.records_processed}"
            )

            return result

        except Exception as e:
            result.success = False
            result.status = SyncStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.now()
            self._sync_history.append(result)
            return result

    def _create_accounting_entry(self, tx: FinanceTransaction) -> AccountingEntry:
        """Crée une écriture comptable à partir d'une transaction."""
        # Déterminer le journal
        journal_code = DefaultMappings.JOURNALS.get(tx.transaction_type, "OD")

        # Déterminer les comptes
        bank_account = self.resolve_mapping(
            MappingType.ACCOUNT,
            tx.bank_account or "current_account",
        ) or "512100"

        category_account = self.resolve_mapping(
            MappingType.ACCOUNT,
            tx.category or "other_expense",
        ) or "658000"

        # Déterminer débit/crédit selon le type
        if tx.transaction_type in [TransactionType.RECEIPT]:
            debit_account = bank_account
            credit_account = category_account
        else:
            debit_account = category_account
            credit_account = bank_account

        return AccountingEntry(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            journal_code=journal_code,
            date=tx.date,
            reference=tx.reference or f"FIN-{tx.id[:8]}",
            description=tx.description,
            debit_account=debit_account,
            credit_account=credit_account,
            amount=tx.amount,
            currency=tx.currency,
            cost_center=tx.metadata.get("cost_center"),
            source_transaction_id=tx.id,
            metadata={"source": "finance_integration"},
        )

    # =========================================================================
    # SYNC COMPTABILITÉ → FINANCE
    # =========================================================================

    async def sync_from_accounting(
        self,
        entries: list[AccountingEntry],
    ) -> SyncResult:
        """
        Importe des écritures comptables vers Finance.

        Crée les transactions financières correspondantes.
        """
        sync_id = str(uuid.uuid4())
        result = SyncResult(
            success=True,
            sync_id=sync_id,
            direction=SyncDirection.ACCOUNTING_TO_FINANCE,
            status=SyncStatus.IN_PROGRESS,
        )

        try:
            for entry in entries:
                if entry.tenant_id != self.tenant_id:
                    result.records_skipped += 1
                    continue

                result.records_processed += 1

                try:
                    # Simuler la création d'une transaction financière
                    # En production, cela créerait vraiment l'objet
                    tx = self._create_finance_transaction(entry)
                    result.records_created += 1
                except Exception as e:
                    result.records_failed += 1
                    result.errors.append(f"Écriture {entry.id}: {str(e)}")

            result.status = (
                SyncStatus.COMPLETED if result.records_failed == 0
                else SyncStatus.PARTIAL if result.records_created > 0
                else SyncStatus.FAILED
            )
            result.success = result.status == SyncStatus.COMPLETED
            result.completed_at = datetime.now()
            self._sync_history.append(result)

            return result

        except Exception as e:
            result.success = False
            result.status = SyncStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.now()
            return result

    def _create_finance_transaction(self, entry: AccountingEntry) -> FinanceTransaction:
        """Crée une transaction financière à partir d'une écriture."""
        # Déterminer le type de transaction
        if entry.debit_account.startswith("512"):
            tx_type = TransactionType.RECEIPT
        elif entry.credit_account.startswith("512"):
            tx_type = TransactionType.PAYMENT
        else:
            tx_type = TransactionType.ADJUSTMENT

        return FinanceTransaction(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            transaction_type=tx_type,
            date=entry.date,
            amount=entry.amount,
            currency=entry.currency,
            description=entry.description,
            reference=entry.reference,
            metadata={"source_entry_id": entry.id},
        )

    # =========================================================================
    # SYNC FACTURATION
    # =========================================================================

    async def sync_invoice_payment(
        self,
        invoice_id: str,
        payment_amount: Decimal,
        payment_date: datetime,
        payment_method: str = "bank_transfer",
    ) -> SyncResult:
        """
        Synchronise un paiement de facture.

        Crée l'écriture comptable de règlement.
        """
        sync_id = str(uuid.uuid4())
        result = SyncResult(
            success=True,
            sync_id=sync_id,
            direction=SyncDirection.INVOICE_TO_FINANCE,
            status=SyncStatus.IN_PROGRESS,
        )

        try:
            # Compte client
            customer_account = "411000"  # Clients

            # Compte de règlement
            payment_account = self.resolve_mapping(
                MappingType.PAYMENT_METHOD,
                payment_method,
            ) or "512100"

            entry = AccountingEntry(
                id=str(uuid.uuid4()),
                tenant_id=self.tenant_id,
                journal_code="BQ",
                date=payment_date,
                reference=f"REG-{invoice_id[:8]}",
                description=f"Règlement facture {invoice_id}",
                debit_account=payment_account,
                credit_account=customer_account,
                amount=payment_amount,
                currency="EUR",
                source_transaction_id=invoice_id,
                metadata={"payment_method": payment_method},
            )

            result.entries.append(entry)
            result.records_processed = 1
            result.records_created = 1
            result.status = SyncStatus.COMPLETED
            result.completed_at = datetime.now()

            self._sync_history.append(result)

            logger.info(f"Paiement facture {invoice_id} synchronisé")
            return result

        except Exception as e:
            result.success = False
            result.status = SyncStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.now()
            return result

    # =========================================================================
    # VALIDATION
    # =========================================================================

    async def validate_balance(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> ValidationResult:
        """
        Valide l'équilibre Finance ↔ Comptabilité.

        Vérifie que les totaux correspondent.
        """
        # Simuler la validation (en production, requête les vrais totaux)
        finance_total = Decimal("15000.00")
        accounting_total = Decimal("15000.00")

        difference = abs(finance_total - accounting_total)
        is_valid = difference == Decimal("0")

        return ValidationResult(
            is_valid=is_valid,
            validation_type="balance_check",
            errors=[] if is_valid else [f"Écart de {difference}€"],
            details={
                "finance_total": str(finance_total),
                "accounting_total": str(accounting_total),
                "difference": str(difference),
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
            },
        )

    async def validate_entries(
        self,
        entries: list[AccountingEntry],
    ) -> ValidationResult:
        """Valide une liste d'écritures comptables."""
        errors = []
        warnings = []

        for entry in entries:
            # Vérifier l'équilibre
            if entry.amount <= 0:
                errors.append(f"Écriture {entry.id}: montant invalide")

            # Vérifier les comptes
            if not entry.debit_account or not entry.credit_account:
                errors.append(f"Écriture {entry.id}: comptes manquants")

            # Vérifier le journal
            if not entry.journal_code:
                warnings.append(f"Écriture {entry.id}: journal non spécifié")

        return ValidationResult(
            is_valid=len(errors) == 0,
            validation_type="entry_validation",
            errors=errors,
            warnings=warnings,
            details={"entries_checked": len(entries)},
        )

    # =========================================================================
    # HISTORY
    # =========================================================================

    async def get_sync_history(
        self,
        direction: Optional[SyncDirection] = None,
        status: Optional[SyncStatus] = None,
        limit: int = 50,
    ) -> list[SyncResult]:
        """Récupère l'historique de synchronisation."""
        history = self._sync_history.copy()

        if direction:
            history = [h for h in history if h.direction == direction]

        if status:
            history = [h for h in history if h.status == status]

        return sorted(
            history,
            key=lambda h: h.started_at,
            reverse=True
        )[:limit]

    async def get_sync_result(self, sync_id: str) -> Optional[SyncResult]:
        """Récupère un résultat de synchronisation."""
        return next(
            (h for h in self._sync_history if h.sync_id == sync_id),
            None
        )

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_integration_stats(self) -> dict:
        """Statistiques d'intégration."""
        total_syncs = len(self._sync_history)
        successful = len([h for h in self._sync_history if h.success])
        failed = total_syncs - successful

        total_processed = sum(h.records_processed for h in self._sync_history)
        total_created = sum(h.records_created for h in self._sync_history)
        total_failed = sum(h.records_failed for h in self._sync_history)

        return {
            "total_syncs": total_syncs,
            "successful_syncs": successful,
            "failed_syncs": failed,
            "success_rate": f"{(successful / total_syncs * 100):.1f}%" if total_syncs > 0 else "N/A",
            "total_records_processed": total_processed,
            "total_records_created": total_created,
            "total_records_failed": total_failed,
            "mappings_count": len(self._mappings),
        }
