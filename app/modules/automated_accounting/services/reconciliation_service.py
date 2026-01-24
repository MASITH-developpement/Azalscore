"""
AZALS MODULE M2A - Service Rapprochement Automatique
=====================================================

Service de rapprochement automatique IA entre:
- Transactions bancaires
- Factures
- Notes de frais
- Écritures comptables
"""

import logging
import re
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..models import (
    AccountingDocument,
    DocumentType,
    PaymentStatus,
    ReconciliationHistory,
    ReconciliationRule,
    ReconciliationStatusAuto,
    SyncedTransaction,
)

logger = logging.getLogger(__name__)


# ============================================================================
# MATCHING ENGINE
# ============================================================================

class MatchingEngine:
    """Moteur de matching pour le rapprochement automatique."""

    # Seuils de confiance
    THRESHOLDS = {
        "amount_exact": Decimal("0.01"),        # Tolérance montant exact
        "amount_tolerance_percent": Decimal("1"),  # Tolérance 1%
        "date_tolerance_days": 7,                # Tolérance jours
        "min_confidence_auto": Decimal("90"),    # Confiance min pour auto-rapprochement
    }

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self._rules_cache: list[ReconciliationRule] | None = None

    def find_matches(
        self,
        transaction: SyncedTransaction
    ) -> list[dict[str, Any]]:
        """Trouve les correspondances possibles pour une transaction.

        Args:
            transaction: Transaction bancaire à matcher

        Returns:
            Liste des correspondances avec scores de confiance
        """
        matches = []

        # 1. Recherche par règles personnalisées
        rule_matches = self._apply_custom_rules(transaction)
        matches.extend(rule_matches)

        # 2. Recherche par montant et date dans les documents
        document_matches = self._find_document_matches(transaction)
        matches.extend(document_matches)

        # 3. Tri par confiance décroissante
        matches.sort(key=lambda x: x["confidence"], reverse=True)

        # Dédoublonnage (garder le meilleur match par document)
        seen_docs = set()
        unique_matches = []
        for match in matches:
            doc_id = match.get("document_id")
            if doc_id and doc_id not in seen_docs:
                seen_docs.add(doc_id)
                unique_matches.append(match)
            elif not doc_id:
                unique_matches.append(match)

        return unique_matches[:10]  # Max 10 suggestions

    def _apply_custom_rules(
        self,
        transaction: SyncedTransaction
    ) -> list[dict[str, Any]]:
        """Applique les règles de rapprochement personnalisées."""
        if self._rules_cache is None:
            self._rules_cache = self.db.query(ReconciliationRule).filter(
                ReconciliationRule.tenant_id == self.tenant_id,
                ReconciliationRule.is_active
            ).order_by(ReconciliationRule.priority.desc()).all()

        matches = []

        for rule in self._rules_cache:
            match_result = self._evaluate_rule(transaction, rule)
            if match_result:
                matches.append(match_result)

        return matches

    def _evaluate_rule(
        self,
        transaction: SyncedTransaction,
        rule: ReconciliationRule
    ) -> dict[str, Any] | None:
        """Évalue si une règle correspond à la transaction."""
        criteria = rule.match_criteria or {}
        confidence = Decimal("100")
        match_reasons = []

        # Critère: Pattern sur le libellé
        if "description_patterns" in criteria:
            patterns = criteria["description_patterns"]
            desc = (transaction.description or "").lower()
            merchant = (transaction.merchant_name or "").lower()

            pattern_matched = False
            for pattern in patterns:
                if re.search(pattern.lower(), desc) or re.search(pattern.lower(), merchant):
                    pattern_matched = True
                    match_reasons.append(f"Pattern '{pattern}' matched")
                    break

            if not pattern_matched:
                return None

        # Critère: Montant min/max
        if "amount_min" in criteria and abs(transaction.amount) < Decimal(str(criteria["amount_min"])):
            return None

        if "amount_max" in criteria and abs(transaction.amount) > Decimal(str(criteria["amount_max"])):
            return None

        # Critère: Type de transaction (débit/crédit)
        if "transaction_type" in criteria:
            if criteria["transaction_type"] == "debit" and transaction.amount >= 0:
                return None
            if criteria["transaction_type"] == "credit" and transaction.amount <= 0:
                return None

        # Critère: Catégorie marchand
        if "merchant_categories" in criteria:
            if transaction.merchant_category not in criteria["merchant_categories"]:
                confidence -= Decimal("20")

        # Si tous les critères sont satisfaits
        if confidence >= Decimal("50"):
            return {
                "type": "rule",
                "rule_id": rule.id,
                "rule_name": rule.name,
                "confidence": float(confidence),
                "match_reasons": match_reasons,
                "suggested_account": rule.default_account_code,
                "auto_reconcile": rule.auto_reconcile and confidence >= rule.min_confidence,
            }

        return None

    def _find_document_matches(
        self,
        transaction: SyncedTransaction
    ) -> list[dict[str, Any]]:
        """Recherche les documents correspondants à la transaction."""
        matches = []
        txn_amount = abs(transaction.amount)
        txn_date = transaction.transaction_date

        # Définit les types de documents à chercher
        if transaction.amount < 0:
            # Débit = facture fournisseur ou note de frais
            doc_types = [
                DocumentType.INVOICE_RECEIVED,
                DocumentType.EXPENSE_NOTE
            ]
        else:
            # Crédit = facture client ou avoir
            doc_types = [
                DocumentType.INVOICE_SENT,
                DocumentType.CREDIT_NOTE_RECEIVED
            ]

        # Recherche avec tolérance sur le montant
        tolerance = txn_amount * self.THRESHOLDS["amount_tolerance_percent"] / 100
        amount_min = txn_amount - tolerance
        amount_max = txn_amount + tolerance

        # Recherche avec tolérance sur la date
        txn_date - timedelta(days=self.THRESHOLDS["date_tolerance_days"])
        txn_date + timedelta(days=self.THRESHOLDS["date_tolerance_days"])

        documents = self.db.query(AccountingDocument).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.document_type.in_(doc_types),
            AccountingDocument.payment_status.in_([
                PaymentStatus.UNPAID,
                PaymentStatus.PARTIALLY_PAID
            ]),
            or_(
                # Match sur TTC
                and_(
                    AccountingDocument.amount_total >= amount_min,
                    AccountingDocument.amount_total <= amount_max
                ),
                # Match sur reste à payer
                and_(
                    AccountingDocument.amount_remaining >= amount_min,
                    AccountingDocument.amount_remaining <= amount_max
                )
            )
        ).all()

        for doc in documents:
            confidence = self._calculate_match_confidence(transaction, doc)
            if confidence >= 50:
                matches.append({
                    "type": "document",
                    "document_id": doc.id,
                    "document_type": doc.document_type.value,
                    "document_reference": doc.reference,
                    "document_amount": float(doc.amount_total or 0),
                    "partner_name": doc.partner_name,
                    "confidence": confidence,
                    "match_reasons": self._get_match_reasons(transaction, doc),
                    "auto_reconcile": confidence >= float(self.THRESHOLDS["min_confidence_auto"]),
                })

        return matches

    def _calculate_match_confidence(
        self,
        transaction: SyncedTransaction,
        document: AccountingDocument
    ) -> float:
        """Calcule le score de confiance d'un match."""
        confidence = 50.0  # Base

        txn_amount = abs(transaction.amount)
        doc_amount = document.amount_total or document.amount_remaining or Decimal("0")

        # Score sur le montant (0-30 points)
        amount_diff = abs(txn_amount - doc_amount)
        if amount_diff < Decimal("0.01"):
            confidence += 30  # Montant exact
        elif amount_diff < txn_amount * Decimal("0.01"):
            confidence += 25  # Écart < 1%
        elif amount_diff < txn_amount * Decimal("0.05"):
            confidence += 15  # Écart < 5%

        # Score sur la date (0-20 points)
        if document.due_date:
            days_diff = abs((transaction.transaction_date - document.due_date).days)
            if days_diff == 0:
                confidence += 20
            elif days_diff <= 3:
                confidence += 15
            elif days_diff <= 7:
                confidence += 10

        # Score sur le partenaire (0-20 points)
        if document.partner_name and transaction.merchant_name:
            partner_lower = document.partner_name.lower()
            merchant_lower = transaction.merchant_name.lower()

            # Recherche de similarité
            if partner_lower in merchant_lower or merchant_lower in partner_lower:
                confidence += 20
            elif any(word in merchant_lower for word in partner_lower.split()[:2]):
                confidence += 10

        # Score sur la référence (0-10 points)
        if document.reference and transaction.description and document.reference in transaction.description:
            confidence += 10

        return min(100.0, confidence)

    def _get_match_reasons(
        self,
        transaction: SyncedTransaction,
        document: AccountingDocument
    ) -> list[str]:
        """Génère les raisons du match."""
        reasons = []

        txn_amount = abs(transaction.amount)
        doc_amount = document.amount_total or Decimal("0")

        if abs(txn_amount - doc_amount) < Decimal("0.01"):
            reasons.append("Montant exact")
        else:
            reasons.append(f"Montant proche ({doc_amount}€ vs {txn_amount}€)")

        if document.due_date:
            days_diff = abs((transaction.transaction_date - document.due_date).days)
            if days_diff == 0:
                reasons.append("Date d'échéance exacte")
            elif days_diff <= 7:
                reasons.append(f"Proche de l'échéance ({days_diff}j)")

        if document.partner_name:
            reasons.append(f"Partenaire: {document.partner_name}")

        return reasons


# ============================================================================
# RECONCILIATION SERVICE
# ============================================================================

class ReconciliationService:
    """Service de rapprochement automatique."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.matching_engine = MatchingEngine(db, tenant_id)

    # =========================================================================
    # RAPPROCHEMENT AUTOMATIQUE
    # =========================================================================

    def auto_reconcile_all(self) -> dict[str, Any]:
        """Lance le rapprochement automatique sur toutes les transactions en attente.

        Returns:
            Dict avec les statistiques de rapprochement
        """
        # Récupère les transactions non rapprochées
        pending_transactions = self.db.query(SyncedTransaction).filter(
            SyncedTransaction.tenant_id == self.tenant_id,
            SyncedTransaction.reconciliation_status == ReconciliationStatusAuto.PENDING
        ).all()

        results = {
            "total_processed": len(pending_transactions),
            "auto_matched": 0,
            "suggestions_found": 0,
            "no_match": 0,
            "errors": 0,
        }

        for transaction in pending_transactions:
            match_result = self.reconcile_transaction(transaction.id, auto_mode=True)

            if match_result.get("auto_reconciled"):
                results["auto_matched"] += 1
            elif match_result.get("suggestions"):
                results["suggestions_found"] += 1
            else:
                results["no_match"] += 1

        self.db.commit()
        return results

    def reconcile_transaction(
        self,
        transaction_id: UUID,
        auto_mode: bool = True
    ) -> dict[str, Any]:
        """Tente de rapprocher une transaction.

        Args:
            transaction_id: ID de la transaction
            auto_mode: Si True, rapproche automatiquement si confiance suffisante

        Returns:
            Dict avec le résultat du rapprochement
        """
        transaction = self.db.query(SyncedTransaction).filter(
            SyncedTransaction.id == transaction_id,
            SyncedTransaction.tenant_id == self.tenant_id
        ).first()

        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        # Trouve les correspondances
        matches = self.matching_engine.find_matches(transaction)

        result = {
            "transaction_id": str(transaction_id),
            "suggestions": matches,
            "auto_reconciled": False,
            "reconciliation_id": None,
        }

        if not matches:
            transaction.reconciliation_status = ReconciliationStatusAuto.UNMATCHED
            return result

        # Vérifie si on peut auto-rapprocher
        best_match = matches[0]
        if auto_mode and best_match.get("auto_reconcile"):
            # Rapprochement automatique
            if best_match["type"] == "document":
                recon = self._create_reconciliation(
                    transaction=transaction,
                    document_id=UUID(best_match["document_id"]),
                    confidence=Decimal(str(best_match["confidence"])),
                    reconciliation_type="auto",
                    match_details=best_match
                )
                result["auto_reconciled"] = True
                result["reconciliation_id"] = str(recon.id)

            elif best_match["type"] == "rule":
                # Marque comme rapproché via règle
                transaction.reconciliation_status = ReconciliationStatusAuto.MATCHED
                transaction.ai_category = best_match.get("suggested_account")
                result["auto_reconciled"] = True

        return result

    def manual_reconcile(
        self,
        transaction_id: UUID,
        document_id: UUID | None = None,
        entry_line_id: UUID | None = None,
        validated_by: UUID | None = None
    ) -> ReconciliationHistory:
        """Rapprochement manuel.

        Args:
            transaction_id: ID de la transaction
            document_id: ID du document à rapprocher (optionnel)
            entry_line_id: ID de la ligne d'écriture (optionnel)
            validated_by: ID de l'utilisateur

        Returns:
            ReconciliationHistory créé
        """
        transaction = self.db.query(SyncedTransaction).filter(
            SyncedTransaction.id == transaction_id,
            SyncedTransaction.tenant_id == self.tenant_id
        ).first()

        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        if document_id:
            self.db.query(AccountingDocument).filter(
                AccountingDocument.id == document_id,
                AccountingDocument.tenant_id == self.tenant_id
            ).first()

        recon = self._create_reconciliation(
            transaction=transaction,
            document_id=document_id,
            entry_line_id=entry_line_id,
            confidence=Decimal("100"),  # Manuel = 100%
            reconciliation_type="manual",
            validated_by=validated_by,
            match_details={"type": "manual", "validated_by": str(validated_by)}
        )

        self.db.commit()
        return recon

    def cancel_reconciliation(
        self,
        reconciliation_id: UUID,
        cancelled_by: UUID,
        reason: str | None = None
    ):
        """Annule un rapprochement.

        Args:
            reconciliation_id: ID du rapprochement
            cancelled_by: ID de l'utilisateur
            reason: Raison de l'annulation
        """
        recon = self.db.query(ReconciliationHistory).filter(
            ReconciliationHistory.id == reconciliation_id,
            ReconciliationHistory.tenant_id == self.tenant_id
        ).first()

        if not recon:
            raise ValueError(f"Reconciliation {reconciliation_id} not found")

        recon.is_cancelled = True
        recon.cancelled_by = cancelled_by
        recon.cancelled_at = datetime.utcnow()
        recon.cancellation_reason = reason

        # Remet la transaction en attente
        if recon.transaction_id:
            transaction = self.db.query(SyncedTransaction).filter(
                SyncedTransaction.id == recon.transaction_id
            ).first()
            if transaction:
                transaction.reconciliation_status = ReconciliationStatusAuto.PENDING
                transaction.matched_document_id = None
                transaction.matched_at = None

        # Remet le document en attente
        if recon.document_id:
            document = self.db.query(AccountingDocument).filter(
                AccountingDocument.id == recon.document_id
            ).first()
            if document:
                document.payment_status = PaymentStatus.UNPAID
                document.amount_paid = Decimal("0")

        self.db.commit()

    def _create_reconciliation(
        self,
        transaction: SyncedTransaction,
        document_id: UUID | None,
        confidence: Decimal,
        reconciliation_type: str,
        match_details: dict[str, Any],
        entry_line_id: UUID | None = None,
        rule_id: UUID | None = None,
        validated_by: UUID | None = None
    ) -> ReconciliationHistory:
        """Crée un enregistrement de rapprochement."""
        document = None
        doc_amount = None

        if document_id:
            document = self.db.query(AccountingDocument).filter(
                AccountingDocument.id == document_id
            ).first()
            if document:
                doc_amount = document.amount_total

        recon = ReconciliationHistory(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            transaction_id=transaction.id,
            document_id=document_id,
            entry_line_id=entry_line_id,
            reconciliation_type=reconciliation_type,
            rule_id=rule_id,
            confidence_score=confidence,
            match_details=match_details,
            transaction_amount=transaction.amount,
            document_amount=doc_amount,
            difference=abs(transaction.amount) - doc_amount if doc_amount else None,
            validated_by=validated_by,
            validated_at=datetime.utcnow() if validated_by else None,
            created_at=datetime.utcnow()
        )
        self.db.add(recon)

        # Met à jour la transaction
        transaction.reconciliation_status = ReconciliationStatusAuto.MATCHED
        transaction.matched_document_id = document_id
        transaction.matched_at = datetime.utcnow()
        transaction.match_confidence = confidence

        # Met à jour le document
        if document:
            document.payment_status = PaymentStatus.PAID
            document.amount_paid = doc_amount
            document.amount_remaining = Decimal("0")

        return recon

    # =========================================================================
    # RÈGLES DE RAPPROCHEMENT
    # =========================================================================

    def create_rule(
        self,
        name: str,
        match_criteria: dict[str, Any],
        created_by: UUID,
        description: str | None = None,
        auto_reconcile: bool = False,
        min_confidence: Decimal = Decimal("90"),
        default_account_code: str | None = None,
        default_tax_code: str | None = None,
        priority: int = 0
    ) -> ReconciliationRule:
        """Crée une règle de rapprochement."""
        rule = ReconciliationRule(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            match_criteria=match_criteria,
            auto_reconcile=auto_reconcile,
            min_confidence=min_confidence,
            default_account_code=default_account_code,
            default_tax_code=default_tax_code,
            priority=priority,
            is_active=True,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        # Invalide le cache
        self.matching_engine._rules_cache = None

        return rule

    def update_rule(
        self,
        rule_id: UUID,
        **updates
    ) -> ReconciliationRule:
        """Met à jour une règle de rapprochement."""
        rule = self.db.query(ReconciliationRule).filter(
            ReconciliationRule.id == rule_id,
            ReconciliationRule.tenant_id == self.tenant_id
        ).first()

        if not rule:
            raise ValueError(f"Rule {rule_id} not found")

        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        rule.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(rule)

        # Invalide le cache
        self.matching_engine._rules_cache = None

        return rule

    def delete_rule(self, rule_id: UUID):
        """Supprime une règle de rapprochement."""
        rule = self.db.query(ReconciliationRule).filter(
            ReconciliationRule.id == rule_id,
            ReconciliationRule.tenant_id == self.tenant_id
        ).first()

        if rule:
            self.db.delete(rule)
            self.db.commit()
            self.matching_engine._rules_cache = None

    def get_rules(self, active_only: bool = True) -> list[ReconciliationRule]:
        """Récupère les règles de rapprochement."""
        query = self.db.query(ReconciliationRule).filter(
            ReconciliationRule.tenant_id == self.tenant_id
        )

        if active_only:
            query = query.filter(ReconciliationRule.is_active)

        return query.order_by(ReconciliationRule.priority.desc()).all()

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def get_reconciliation_stats(self) -> dict[str, Any]:
        """Calcule les statistiques de rapprochement."""
        # Compte total des transactions
        total = self.db.query(SyncedTransaction).filter(
            SyncedTransaction.tenant_id == self.tenant_id
        ).count()

        # Par statut
        matched_auto = self.db.query(ReconciliationHistory).filter(
            ReconciliationHistory.tenant_id == self.tenant_id,
            ReconciliationHistory.reconciliation_type == "auto",
            not ReconciliationHistory.is_cancelled
        ).count()

        matched_manual = self.db.query(ReconciliationHistory).filter(
            ReconciliationHistory.tenant_id == self.tenant_id,
            ReconciliationHistory.reconciliation_type == "manual",
            not ReconciliationHistory.is_cancelled
        ).count()

        unmatched = self.db.query(SyncedTransaction).filter(
            SyncedTransaction.tenant_id == self.tenant_id,
            SyncedTransaction.reconciliation_status.in_([
                ReconciliationStatusAuto.PENDING,
                ReconciliationStatusAuto.UNMATCHED
            ])
        ).count()

        match_rate = Decimal("0")
        if total > 0:
            match_rate = Decimal(str(round((matched_auto + matched_manual) / total * 100, 2)))

        return {
            "total_transactions": total,
            "matched_auto": matched_auto,
            "matched_manual": matched_manual,
            "unmatched": unmatched,
            "match_rate": match_rate,
        }

    def get_reconciliation_history(
        self,
        document_id: UUID | None = None,
        transaction_id: UUID | None = None,
        limit: int = 50
    ) -> list[ReconciliationHistory]:
        """Récupère l'historique des rapprochements."""
        query = self.db.query(ReconciliationHistory).filter(
            ReconciliationHistory.tenant_id == self.tenant_id
        )

        if document_id:
            query = query.filter(ReconciliationHistory.document_id == document_id)

        if transaction_id:
            query = query.filter(ReconciliationHistory.transaction_id == transaction_id)

        return query.order_by(
            ReconciliationHistory.created_at.desc()
        ).limit(limit).all()
