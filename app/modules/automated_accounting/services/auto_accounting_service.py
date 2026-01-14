"""
AZALS MODULE M2A - Service Comptabilisation Automatique
========================================================

Service de génération automatique des écritures comptables.
ZÉRO saisie manuelle - l'humain valide par exception uniquement.
"""

import logging
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..models import (
    AccountingDocument,
    AIClassification,
    AutoEntry,
    ChartMapping,
    ConfidenceLevel,
    DocumentStatus,
    DocumentType,
)
from ..schemas import ProposedEntryLine

# Import des modèles Finance existants
try:
    from app.modules.finance.models import (
        Account,
        EntryStatus,
        FiscalPeriod,
        FiscalYear,
        Journal,
        JournalEntry,
        JournalEntryLine,
        JournalType,
    )
    FINANCE_MODULE_AVAILABLE = True
except ImportError:
    FINANCE_MODULE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Finance module not available - using standalone mode")

logger = logging.getLogger(__name__)


# ============================================================================
# ACCOUNTING RULES ENGINE
# ============================================================================

class AccountingRulesEngine:
    """Moteur de règles comptables pour génération automatique."""

    # Templates d'écritures par type de document
    ENTRY_TEMPLATES = {
        DocumentType.INVOICE_RECEIVED: {
            "journal": "PURCHASES",
            "template": "purchase_invoice",
            "lines": [
                {"type": "expense", "side": "debit"},      # Compte de charge
                {"type": "vat_deductible", "side": "debit"},  # TVA déductible
                {"type": "supplier", "side": "credit"},    # Fournisseur
            ]
        },
        DocumentType.INVOICE_SENT: {
            "journal": "SALES",
            "template": "sales_invoice",
            "lines": [
                {"type": "customer", "side": "debit"},     # Client
                {"type": "revenue", "side": "credit"},     # Produit
                {"type": "vat_collected", "side": "credit"},  # TVA collectée
            ]
        },
        DocumentType.EXPENSE_NOTE: {
            "journal": "PURCHASES",
            "template": "expense_note",
            "lines": [
                {"type": "expense", "side": "debit"},      # Compte de charge
                {"type": "vat_deductible", "side": "debit"},  # TVA déductible
                {"type": "employee", "side": "credit"},    # Salarié à rembourser
            ]
        },
        DocumentType.CREDIT_NOTE_RECEIVED: {
            "journal": "PURCHASES",
            "template": "purchase_credit",
            "lines": [
                {"type": "supplier", "side": "debit"},     # Fournisseur
                {"type": "expense", "side": "credit"},     # Contre-passation charge
                {"type": "vat_deductible", "side": "credit"},  # TVA déductible
            ]
        },
        DocumentType.CREDIT_NOTE_SENT: {
            "journal": "SALES",
            "template": "sales_credit",
            "lines": [
                {"type": "revenue", "side": "debit"},      # Contre-passation produit
                {"type": "vat_collected", "side": "debit"},  # TVA collectée
                {"type": "customer", "side": "credit"},    # Client
            ]
        },
    }

    # Comptes par défaut par type
    DEFAULT_ACCOUNTS = {
        "expense": "607000",        # Achats marchandises
        "revenue": "707000",        # Ventes marchandises
        "supplier": "401000",       # Fournisseurs
        "customer": "411000",       # Clients
        "employee": "421000",       # Personnel - Rémunérations dues
        "vat_deductible": "445660", # TVA déductible
        "vat_collected": "445710",  # TVA collectée
        "bank": "512000",           # Banque
    }

    # Taux de TVA par défaut (France)
    DEFAULT_VAT_RATES = {
        "normal": Decimal("20.00"),
        "intermediate": Decimal("10.00"),
        "reduced": Decimal("5.50"),
        "super_reduced": Decimal("2.10"),
    }

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self._account_cache: dict[str, str] = {}
        self._load_account_mappings()

    def _load_account_mappings(self):
        """Charge les mappings de comptes pour le tenant."""
        mappings = self.db.query(ChartMapping).filter(
            ChartMapping.tenant_id == self.tenant_id,
            ChartMapping.is_active
        ).all()

        for mapping in mappings:
            self._account_cache[mapping.universal_code] = mapping.local_account_code

    def get_account_code(self, account_type: str, universal_code: str = None) -> str:
        """Obtient le code compte approprié."""
        # Priorité: mapping local > code universel > défaut
        if universal_code and universal_code in self._account_cache:
            return self._account_cache[universal_code]

        if universal_code:
            return universal_code

        return self.DEFAULT_ACCOUNTS.get(account_type, "471000")  # Compte d'attente

    def generate_entry_lines(
        self,
        document: AccountingDocument,
        classification: AIClassification | None = None
    ) -> list[ProposedEntryLine]:
        """Génère les lignes d'écriture pour un document.

        Args:
            document: Document source
            classification: Classification IA (optionnel)

        Returns:
            Liste des lignes d'écriture proposées
        """
        doc_type = document.document_type
        if doc_type not in self.ENTRY_TEMPLATES:
            logger.warning(f"No template for document type {doc_type}")
            return []

        template = self.ENTRY_TEMPLATES[doc_type]
        lines = []

        # Montants
        amount_ht = document.amount_untaxed or Decimal("0")
        amount_tva = document.amount_tax or Decimal("0")
        amount_ttc = document.amount_total or (amount_ht + amount_tva)

        # Si on n'a que le TTC, on calcule le HT
        if amount_ttc and not amount_ht:
            vat_rate = self._detect_vat_rate(document, classification)
            amount_ht = amount_ttc / (1 + vat_rate / 100)
            amount_tva = amount_ttc - amount_ht

        # Compte de charge/produit suggéré par l'IA
        suggested_account = None
        if classification and classification.suggested_account_code:
            suggested_account = classification.suggested_account_code

        # Génération des lignes selon le template
        for line_template in template["lines"]:
            line_type = line_template["type"]
            side = line_template["side"]

            # Détermination du compte
            if line_type == "expense" and suggested_account or line_type == "revenue" and suggested_account:
                account_code = suggested_account
            else:
                account_code = self.get_account_code(line_type)

            # Détermination du montant
            if line_type in ["expense", "revenue"]:
                amount = amount_ht
            elif line_type in ["vat_deductible", "vat_collected"]:
                amount = amount_tva
            else:  # supplier, customer, employee
                amount = amount_ttc

            # Skip si montant = 0
            if amount == 0:
                continue

            # Création de la ligne
            line = ProposedEntryLine(
                account_code=account_code,
                account_name=self._get_account_name(account_code),
                debit=amount if side == "debit" else Decimal("0"),
                credit=amount if side == "credit" else Decimal("0"),
                label=self._generate_line_label(document, line_type)
            )
            lines.append(line)

        # Validation: débit = crédit
        total_debit = sum(l.debit for l in lines)
        total_credit = sum(l.credit for l in lines)

        if abs(total_debit - total_credit) > Decimal("0.01"):
            logger.warning(
                f"Entry imbalance: debit={total_debit}, credit={total_credit}"
            )
            # Ajout d'une ligne d'écart si nécessaire
            diff = total_debit - total_credit
            if diff > 0:
                lines.append(ProposedEntryLine(
                    account_code="658000",  # Charges diverses
                    account_name="Écart de rapprochement",
                    debit=Decimal("0"),
                    credit=diff,
                    label="Écart d'arrondi"
                ))
            else:
                lines.append(ProposedEntryLine(
                    account_code="758000",  # Produits divers
                    account_name="Écart de rapprochement",
                    debit=abs(diff),
                    credit=Decimal("0"),
                    label="Écart d'arrondi"
                ))

        return lines

    def _detect_vat_rate(
        self,
        document: AccountingDocument,
        classification: AIClassification | None
    ) -> Decimal:
        """Détecte le taux de TVA applicable."""
        # Priorité: classification IA > analyse du texte > défaut
        if classification and classification.tax_rates:
            rates = classification.tax_rates
            if rates and len(rates) > 0:
                return Decimal(str(rates[0].get("rate", 20)))

        # Par défaut: TVA normale
        return self.DEFAULT_VAT_RATES["normal"]

    def _get_account_name(self, account_code: str) -> str | None:
        """Récupère le libellé d'un compte."""
        if FINANCE_MODULE_AVAILABLE:
            account = self.db.query(Account).filter(
                Account.tenant_id == self.tenant_id,
                Account.code == account_code
            ).first()
            if account:
                return account.name

        # Libellés par défaut
        default_names = {
            "401000": "Fournisseurs",
            "411000": "Clients",
            "421000": "Personnel",
            "445660": "TVA déductible",
            "445710": "TVA collectée",
            "512000": "Banque",
            "607000": "Achats de marchandises",
            "707000": "Ventes de marchandises",
        }
        return default_names.get(account_code)

    def _generate_line_label(self, document: AccountingDocument, line_type: str) -> str:
        """Génère le libellé d'une ligne d'écriture."""
        parts = []

        if document.reference:
            parts.append(document.reference)

        if document.partner_name:
            parts.append(document.partner_name[:50])

        if not parts:
            type_labels = {
                "expense": "Achat",
                "revenue": "Vente",
                "supplier": "Fournisseur",
                "customer": "Client",
                "vat_deductible": "TVA déductible",
                "vat_collected": "TVA collectée",
            }
            parts.append(type_labels.get(line_type, "Écriture"))

        return " - ".join(parts)


# ============================================================================
# AUTO ACCOUNTING SERVICE
# ============================================================================

class AutoAccountingService:
    """Service de comptabilisation automatique.

    Principe clé: La comptabilité est produite AVANT toute intervention humaine.
    """

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.rules_engine = AccountingRulesEngine(db, tenant_id)

    def process_document(
        self,
        document_id: UUID,
        force_validation: bool = False
    ) -> AutoEntry:
        """Traite un document et génère l'écriture comptable.

        Args:
            document_id: ID du document à traiter
            force_validation: Si True, requiert validation même si haute confiance

        Returns:
            AutoEntry avec l'écriture proposée
        """
        # Récupère le document
        document = self.db.query(AccountingDocument).filter(
            AccountingDocument.id == document_id,
            AccountingDocument.tenant_id == self.tenant_id
        ).first()

        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Récupère la classification IA
        classification = self.db.query(AIClassification).filter(
            AIClassification.document_id == document_id,
            AIClassification.tenant_id == self.tenant_id
        ).order_by(AIClassification.created_at.desc()).first()

        # Génère les lignes d'écriture
        proposed_lines = self.rules_engine.generate_entry_lines(
            document, classification
        )

        if not proposed_lines:
            raise ValueError(f"Cannot generate entry for document {document_id}")

        # Calcule la confiance de l'écriture
        confidence_score, confidence_level = self._calculate_entry_confidence(
            document, classification, proposed_lines
        )

        # Détermine si validation requise
        requires_review = force_validation or confidence_level in [
            ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW
        ]
        auto_validated = confidence_level == ConfidenceLevel.HIGH and not force_validation

        # Règles comptables appliquées
        rules_applied = self._get_applied_rules(document, classification)

        # Création de l'AutoEntry
        auto_entry = AutoEntry(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            document_id=document_id,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            entry_template=self._get_template_name(document.document_type),
            accounting_rules_applied=rules_applied,
            proposed_lines=[line.dict() for line in proposed_lines],
            auto_validated=auto_validated,
            requires_review=requires_review,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(auto_entry)

        # Si auto-validé et module Finance disponible, crée l'écriture
        if auto_validated and FINANCE_MODULE_AVAILABLE:
            journal_entry = self._create_journal_entry(document, auto_entry, proposed_lines)
            if journal_entry:
                auto_entry.journal_entry_id = journal_entry.id
                auto_entry.is_posted = True
                auto_entry.posted_at = datetime.utcnow()
                document.journal_entry_id = journal_entry.id
                document.status = DocumentStatus.ACCOUNTED

        # Met à jour le statut du document
        if not auto_validated:
            document.status = DocumentStatus.PENDING_VALIDATION
            document.requires_validation = True

        self.db.commit()
        self.db.refresh(auto_entry)

        logger.info(
            f"Auto entry created for document {document_id} "
            f"with confidence {confidence_level.value} "
            f"(auto_validated={auto_validated})"
        )

        return auto_entry

    def validate_entry(
        self,
        auto_entry_id: UUID,
        validated_by: UUID,
        approved: bool,
        modified_lines: list[ProposedEntryLine] | None = None,
        modification_reason: str | None = None
    ) -> AutoEntry:
        """Valide ou rejette une écriture automatique.

        Args:
            auto_entry_id: ID de l'écriture à valider
            validated_by: ID de l'utilisateur qui valide
            approved: True pour approuver, False pour rejeter
            modified_lines: Lignes modifiées (optionnel)
            modification_reason: Raison de la modification
        """
        auto_entry = self.db.query(AutoEntry).filter(
            AutoEntry.id == auto_entry_id,
            AutoEntry.tenant_id == self.tenant_id
        ).first()

        if not auto_entry:
            raise ValueError(f"AutoEntry {auto_entry_id} not found")

        if auto_entry.is_posted:
            raise ValueError("Entry already posted")

        document = self.db.query(AccountingDocument).filter(
            AccountingDocument.id == auto_entry.document_id
        ).first()

        if not approved:
            # Rejet
            auto_entry.requires_review = False
            auto_entry.reviewed_by = validated_by
            auto_entry.reviewed_at = datetime.utcnow()
            document.status = DocumentStatus.REJECTED
            self.db.commit()
            return auto_entry

        # Approbation
        if modified_lines:
            auto_entry.original_lines = auto_entry.proposed_lines
            auto_entry.proposed_lines = [line.dict() for line in modified_lines]
            auto_entry.was_modified = True
            auto_entry.modification_reason = modification_reason

        auto_entry.requires_review = False
        auto_entry.reviewed_by = validated_by
        auto_entry.reviewed_at = datetime.utcnow()

        # Création de l'écriture comptable
        if FINANCE_MODULE_AVAILABLE:
            lines = [ProposedEntryLine(**l) for l in auto_entry.proposed_lines]
            journal_entry = self._create_journal_entry(document, auto_entry, lines)
            if journal_entry:
                auto_entry.journal_entry_id = journal_entry.id
                auto_entry.is_posted = True
                auto_entry.posted_at = datetime.utcnow()
                document.journal_entry_id = journal_entry.id
                document.status = DocumentStatus.ACCOUNTED

        self.db.commit()
        self.db.refresh(auto_entry)

        return auto_entry

    def bulk_validate(
        self,
        auto_entry_ids: list[UUID],
        validated_by: UUID
    ) -> dict[str, Any]:
        """Validation en masse des écritures.

        Args:
            auto_entry_ids: Liste des IDs à valider
            validated_by: ID de l'utilisateur

        Returns:
            Dict avec le résultat de la validation
        """
        results = {
            "validated": 0,
            "failed": 0,
            "failed_ids": [],
            "errors": {}
        }

        for entry_id in auto_entry_ids:
            try:
                self.validate_entry(
                    auto_entry_id=entry_id,
                    validated_by=validated_by,
                    approved=True
                )
                results["validated"] += 1
            except Exception as e:
                results["failed"] += 1
                results["failed_ids"].append(str(entry_id))
                results["errors"][str(entry_id)] = str(e)

        return results

    def get_pending_entries(
        self,
        confidence_filter: ConfidenceLevel | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[AutoEntry], int]:
        """Récupère les écritures en attente de validation.

        Args:
            confidence_filter: Filtrer par niveau de confiance
            limit: Nombre max de résultats
            offset: Offset pour pagination

        Returns:
            Tuple[List[AutoEntry], int]: (écritures, total)
        """
        query = self.db.query(AutoEntry).filter(
            AutoEntry.tenant_id == self.tenant_id,
            AutoEntry.requires_review,
            not AutoEntry.is_posted
        )

        if confidence_filter:
            query = query.filter(AutoEntry.confidence_level == confidence_filter)

        total = query.count()

        entries = query.order_by(
            AutoEntry.confidence_level.asc(),  # Plus basse confiance en premier
            AutoEntry.created_at.asc()
        ).offset(offset).limit(limit).all()

        return entries, total

    def _calculate_entry_confidence(
        self,
        document: AccountingDocument,
        classification: AIClassification | None,
        proposed_lines: list[ProposedEntryLine]
    ) -> tuple[Decimal, ConfidenceLevel]:
        """Calcule la confiance de l'écriture générée."""
        scores = []

        # Score basé sur la classification IA
        if classification:
            scores.append(float(classification.overall_confidence_score))

        # Score basé sur la complétude du document
        completeness_score = 50.0
        if document.reference:
            completeness_score += 10
        if document.document_date:
            completeness_score += 10
        if document.partner_name:
            completeness_score += 10
        if document.amount_total:
            completeness_score += 10
        if document.amount_untaxed and document.amount_tax:
            completeness_score += 10
        scores.append(completeness_score)

        # Score basé sur l'équilibre des lignes
        total_debit = sum(l.debit for l in proposed_lines)
        total_credit = sum(l.credit for l in proposed_lines)
        if abs(total_debit - total_credit) < Decimal("0.01"):
            scores.append(100.0)
        else:
            scores.append(50.0)

        # Score global
        avg_score = sum(scores) / len(scores) if scores else 50.0

        # Détermination du niveau
        if avg_score >= 95:
            level = ConfidenceLevel.HIGH
        elif avg_score >= 80:
            level = ConfidenceLevel.MEDIUM
        elif avg_score >= 60:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.VERY_LOW

        return Decimal(str(round(avg_score, 2))), level

    def _get_template_name(self, doc_type: DocumentType) -> str:
        """Obtient le nom du template appliqué."""
        templates = AccountingRulesEngine.ENTRY_TEMPLATES
        if doc_type in templates:
            return templates[doc_type]["template"]
        return "generic"

    def _get_applied_rules(
        self,
        document: AccountingDocument,
        classification: AIClassification | None
    ) -> list[str]:
        """Liste les règles comptables appliquées."""
        rules = []

        if document.document_type:
            rules.append(f"template:{self._get_template_name(document.document_type)}")

        if classification:
            if classification.suggested_account_code:
                rules.append(f"ai_account:{classification.suggested_account_code}")
            if classification.expense_category:
                rules.append(f"category:{classification.expense_category}")

        return rules

    def _create_journal_entry(
        self,
        document: AccountingDocument,
        auto_entry: AutoEntry,
        proposed_lines: list[ProposedEntryLine]
    ) -> Optional["JournalEntry"]:
        """Crée l'écriture comptable dans le module Finance."""
        if not FINANCE_MODULE_AVAILABLE:
            return None

        try:
            # Récupère le journal
            journal_code = document.ai_suggested_journal or "PURCHASES"
            journal = self.db.query(Journal).filter(
                Journal.tenant_id == self.tenant_id,
                Journal.code == journal_code
            ).first()

            if not journal:
                logger.error(f"Journal {journal_code} not found")
                return None

            # Récupère l'exercice fiscal en cours
            today = date.today()
            fiscal_year = self.db.query(FiscalYear).filter(
                FiscalYear.tenant_id == self.tenant_id,
                FiscalYear.start_date <= today,
                FiscalYear.end_date >= today
            ).first()

            if not fiscal_year:
                logger.error("No active fiscal year found")
                return None

            # Génère le numéro de pièce
            entry_number = self._generate_entry_number(journal)

            # Crée l'écriture
            journal_entry = JournalEntry(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                journal_id=journal.id,
                fiscal_year_id=fiscal_year.id,
                number=entry_number,
                date=document.document_date or date.today(),
                reference=document.reference,
                description=f"Auto: {document.partner_name or 'Document'} - {document.reference or ''}",
                status=EntryStatus.POSTED,
                source_type="document",
                source_id=document.id,
                created_by=None,  # Système
                created_at=datetime.utcnow(),
                posted_by=None,
                posted_at=datetime.utcnow()
            )
            self.db.add(journal_entry)

            # Crée les lignes
            total_debit = Decimal("0")
            total_credit = Decimal("0")

            for i, line in enumerate(proposed_lines):
                # Récupère le compte
                account = self.db.query(Account).filter(
                    Account.tenant_id == self.tenant_id,
                    Account.code == line.account_code
                ).first()

                if not account:
                    logger.warning(f"Account {line.account_code} not found, creating...")
                    # Crée le compte si nécessaire
                    account = self._create_account_if_needed(line.account_code, line.account_name)

                entry_line = JournalEntryLine(
                    id=uuid.uuid4(),
                    tenant_id=self.tenant_id,
                    entry_id=journal_entry.id,
                    account_id=account.id if account else None,
                    line_number=i + 1,
                    debit=line.debit,
                    credit=line.credit,
                    label=line.label,
                    partner_id=document.partner_id,
                    created_at=datetime.utcnow()
                )
                self.db.add(entry_line)

                total_debit += line.debit
                total_credit += line.credit

            # Met à jour les totaux
            journal_entry.total_debit = total_debit
            journal_entry.total_credit = total_credit

            return journal_entry

        except Exception as e:
            logger.error(f"Failed to create journal entry: {e}")
            return None

    def _generate_entry_number(self, journal: "Journal") -> str:
        """Génère le numéro de pièce."""
        prefix = journal.sequence_prefix or journal.code[:2]
        year = date.today().strftime("%Y")
        sequence = journal.next_sequence or 1

        # Incrémente la séquence
        journal.next_sequence = sequence + 1

        return f"{prefix}{year}{sequence:06d}"

    def _create_account_if_needed(
        self,
        code: str,
        name: str | None
    ) -> Optional["Account"]:
        """Crée un compte s'il n'existe pas."""
        if not FINANCE_MODULE_AVAILABLE:
            return None

        # Détermine le type de compte selon le code
        first_digit = code[0] if code else "4"
        account_types = {
            "1": "EQUITY",
            "2": "ASSET",
            "3": "ASSET",
            "4": "LIABILITY",
            "5": "ASSET",
            "6": "EXPENSE",
            "7": "REVENUE",
        }

        from app.modules.finance.models import AccountType

        account = Account(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            code=code,
            name=name or f"Compte {code}",
            type=AccountType(account_types.get(first_digit, "ASSET")),
            is_active=True,
            allow_posting=True,
            created_at=datetime.utcnow()
        )
        self.db.add(account)
        return account
