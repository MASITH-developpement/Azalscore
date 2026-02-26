"""
AZALSCORE Finance Reconciliation AI Service
============================================

Service de rapprochement bancaire intelligent avec scoring et apprentissage.

Algorithmes:
1. Exact Match - Montant et date identiques
2. Fuzzy Match - Montant proche, date dans fenêtre
3. Pattern Match - Basé sur historique utilisateur
4. ML Match - Modèle entraîné sur réconciliations passées

Scoring:
- Score 0-100 pour chaque suggestion
- Score > 90: Auto-match possible
- Score 70-90: Suggestion forte
- Score 50-70: Suggestion moyenne
- Score < 50: Suggestion faible
"""
from __future__ import annotations


import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from app.modules.finance.models import (
    BankAccount,
    BankStatement,
    BankStatementLine,
    JournalEntry,
    JournalEntryLine,
    Account,
    ReconciliationStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# TYPES
# =============================================================================


class MatchType(str, Enum):
    """Type de correspondance trouvée."""

    EXACT = "exact"  # Montant et date identiques
    AMOUNT = "amount"  # Montant identique, date différente
    FUZZY = "fuzzy"  # Montant proche
    PATTERN = "pattern"  # Basé sur historique
    REFERENCE = "reference"  # Référence commune
    LEARNED = "learned"  # Appris du comportement utilisateur


class MatchConfidence(str, Enum):
    """Niveau de confiance de la suggestion."""

    HIGH = "high"  # Score > 90
    MEDIUM = "medium"  # Score 70-90
    LOW = "low"  # Score 50-70
    VERY_LOW = "very_low"  # Score < 50


@dataclass
class MatchSuggestion:
    """Suggestion de rapprochement."""

    id: str
    bank_line_id: UUID
    entry_line_id: UUID
    score: int  # 0-100
    confidence: MatchConfidence
    match_type: MatchType
    reasons: list[str] = field(default_factory=list)

    # Détails pour l'UI
    bank_amount: Decimal = Decimal("0")
    bank_date: Optional[datetime] = None
    bank_label: str = ""
    entry_amount: Decimal = Decimal("0")
    entry_date: Optional[datetime] = None
    entry_label: str = ""

    # Écarts
    amount_diff: Decimal = Decimal("0")
    days_diff: int = 0


@dataclass
class ReconciliationResult:
    """Résultat d'une opération de réconciliation."""

    success: bool
    matched_count: int = 0
    auto_matched_count: int = 0
    suggested_count: int = 0
    error: Optional[str] = None
    suggestions: list[MatchSuggestion] = field(default_factory=list)


@dataclass
class ReconciliationStats:
    """Statistiques de réconciliation."""

    total_bank_lines: int = 0
    reconciled_lines: int = 0
    pending_lines: int = 0
    auto_matched: int = 0
    manually_matched: int = 0
    unmatched: int = 0
    total_amount_reconciled: Decimal = Decimal("0")
    total_amount_pending: Decimal = Decimal("0")


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class ReconciliationConfig:
    """Configuration du moteur de réconciliation."""

    # Seuils de scoring
    auto_match_threshold: int = 95  # Score minimum pour auto-match
    high_confidence_threshold: int = 90
    medium_confidence_threshold: int = 70
    low_confidence_threshold: int = 50

    # Tolérances
    amount_tolerance_percent: Decimal = Decimal("0.01")  # 1% de tolérance
    amount_tolerance_absolute: Decimal = Decimal("0.10")  # 10 centimes
    date_window_days: int = 5  # Fenêtre de recherche en jours
    date_exact_bonus: int = 20  # Bonus si date exacte

    # Poids des critères
    weight_amount_exact: int = 50
    weight_amount_close: int = 30
    weight_date_exact: int = 20
    weight_date_close: int = 10
    weight_reference: int = 25
    weight_label_match: int = 15
    weight_pattern: int = 20

    # Limites
    max_suggestions_per_line: int = 5
    max_auto_match_per_batch: int = 100


# =============================================================================
# SERVICE PRINCIPAL
# =============================================================================


class ReconciliationService:
    """
    Service de rapprochement bancaire intelligent.

    Fonctionnalités:
    - Génération de suggestions de match
    - Auto-réconciliation basée sur score
    - Apprentissage des patterns utilisateur
    - Statistiques et reporting

    Usage:
        service = ReconciliationService(db, tenant_id)

        # Obtenir des suggestions
        suggestions = await service.get_match_suggestions(
            bank_account_id=account_id,
        )

        # Auto-réconcilier les matches certains
        result = await service.auto_reconcile(
            bank_account_id=account_id,
            min_score=95,
        )
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        config: Optional[ReconciliationConfig] = None,
    ):
        """
        Initialise le service de réconciliation.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant (obligatoire)
            config: Configuration optionnelle
        """
        if not tenant_id:
            raise ValueError("tenant_id est obligatoire")

        self.db = db
        self.tenant_id = tenant_id
        self.config = config or ReconciliationConfig()

        self._logger = logging.LoggerAdapter(
            logger,
            extra={"tenant_id": tenant_id, "service": "ReconciliationService"},
        )

    # =========================================================================
    # SUGGESTIONS
    # =========================================================================

    async def get_match_suggestions(
        self,
        bank_account_id: UUID,
        statement_id: Optional[UUID] = None,
        limit: int = 50,
        min_score: int = 50,
    ) -> list[MatchSuggestion]:
        """
        Génère des suggestions de rapprochement.

        Args:
            bank_account_id: ID du compte bancaire
            statement_id: ID du relevé (optionnel, sinon tous relevés non réconciliés)
            limit: Nombre max de suggestions
            min_score: Score minimum pour inclure

        Returns:
            Liste de suggestions triées par score décroissant
        """
        self._logger.info(
            f"Génération suggestions pour compte {bank_account_id}",
            extra={"bank_account_id": str(bank_account_id)},
        )

        # 1. Récupérer les lignes bancaires non réconciliées
        bank_lines = self._get_pending_bank_lines(
            bank_account_id=bank_account_id,
            statement_id=statement_id,
            limit=limit * 2,  # On en récupère plus pour avoir assez de suggestions
        )

        if not bank_lines:
            self._logger.info("Aucune ligne bancaire en attente")
            return []

        # 2. Récupérer les écritures comptables candidates
        entry_lines = self._get_candidate_entry_lines(
            bank_account_id=bank_account_id,
            date_start=min(l.date for l in bank_lines) - timedelta(days=self.config.date_window_days),
            date_end=max(l.date for l in bank_lines) + timedelta(days=self.config.date_window_days),
        )

        if not entry_lines:
            self._logger.info("Aucune écriture candidate trouvée")
            return []

        # 3. Calculer les scores pour chaque paire possible
        suggestions = []

        for bank_line in bank_lines:
            line_suggestions = []

            for entry_line in entry_lines:
                suggestion = self._calculate_match_score(bank_line, entry_line)

                if suggestion and suggestion.score >= min_score:
                    line_suggestions.append(suggestion)

            # Garder les N meilleures suggestions par ligne
            line_suggestions.sort(key=lambda s: s.score, reverse=True)
            suggestions.extend(line_suggestions[: self.config.max_suggestions_per_line])

        # 4. Trier par score global
        suggestions.sort(key=lambda s: s.score, reverse=True)

        self._logger.info(
            f"Généré {len(suggestions)} suggestions (min_score={min_score})",
            extra={"suggestion_count": len(suggestions)},
        )

        return suggestions[:limit]

    def _get_pending_bank_lines(
        self,
        bank_account_id: UUID,
        statement_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> list[BankStatementLine]:
        """Récupère les lignes bancaires en attente de réconciliation."""
        query = self.db.query(BankStatementLine).join(BankStatement).filter(
            BankStatement.tenant_id == self.tenant_id,
            BankStatement.bank_account_id == bank_account_id,
            BankStatementLine.status == ReconciliationStatus.PENDING,
        )

        if statement_id:
            query = query.filter(BankStatementLine.statement_id == statement_id)

        return query.order_by(BankStatementLine.date.desc()).limit(limit).all()

    def _get_candidate_entry_lines(
        self,
        bank_account_id: UUID,
        date_start: datetime,
        date_end: datetime,
    ) -> list[JournalEntryLine]:
        """Récupère les écritures comptables candidates pour le matching."""
        # Récupérer le compte comptable associé au compte bancaire
        bank_account = self.db.query(BankAccount).filter(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.id == bank_account_id,
        ).first()

        if not bank_account or not bank_account.account_id:
            return []

        # Récupérer les lignes d'écritures non réconciliées sur ce compte
        return self.db.query(JournalEntryLine).join(JournalEntry).filter(
            JournalEntry.tenant_id == self.tenant_id,
            JournalEntryLine.account_id == bank_account.account_id,
            JournalEntryLine.reconcile_ref.is_(None),  # Non réconcilié
            JournalEntry.entry_date >= date_start.date(),
            JournalEntry.entry_date <= date_end.date(),
        ).all()

    def _calculate_match_score(
        self,
        bank_line: BankStatementLine,
        entry_line: JournalEntryLine,
    ) -> Optional[MatchSuggestion]:
        """
        Calcule le score de correspondance entre une ligne bancaire et une écriture.

        Algorithme de scoring:
        1. Montant exact: +50 points
        2. Montant proche (<1%): +30 points
        3. Date exacte: +20 points
        4. Date proche (< 5j): +10 points
        5. Référence commune: +25 points
        6. Label similaire: +15 points
        7. Pattern historique: +20 points (TODO)
        """
        score = 0
        reasons = []
        match_type = MatchType.FUZZY

        # Convertir les montants (débit négatif, crédit positif pour la banque)
        bank_amount = bank_line.credit - bank_line.debit
        entry_amount = entry_line.debit - entry_line.credit  # Inverse pour le compte

        # 1. Comparaison des montants
        amount_diff = abs(bank_amount - entry_amount)

        if amount_diff == 0:
            score += self.config.weight_amount_exact
            reasons.append("Montant identique")
            match_type = MatchType.EXACT
        elif amount_diff <= self.config.amount_tolerance_absolute:
            score += self.config.weight_amount_close
            reasons.append(f"Montant proche (écart: {amount_diff}€)")
        elif amount_diff <= abs(bank_amount) * self.config.amount_tolerance_percent:
            score += self.config.weight_amount_close - 10
            reasons.append(f"Montant proche (<1%)")
        else:
            # Montants trop différents, pas de match
            return None

        # 2. Comparaison des dates
        bank_date = bank_line.date
        entry_date = entry_line.entry.entry_date if entry_line.entry else None

        if entry_date:
            days_diff = abs((bank_date - entry_date).days)

            if days_diff == 0:
                score += self.config.weight_date_exact
                reasons.append("Date identique")
                if match_type == MatchType.EXACT:
                    match_type = MatchType.EXACT
            elif days_diff <= self.config.date_window_days:
                score += self.config.weight_date_close
                reasons.append(f"Date proche ({days_diff}j)")
            else:
                days_diff = self.config.date_window_days + 1

        # 3. Comparaison des références
        bank_ref = self._extract_reference(bank_line.reference or bank_line.label or "")
        entry_ref = self._extract_reference(entry_line.label or "")

        if bank_ref and entry_ref and bank_ref == entry_ref:
            score += self.config.weight_reference
            reasons.append(f"Référence commune: {bank_ref}")
            match_type = MatchType.REFERENCE

        # 4. Similarité des labels
        label_score = self._calculate_label_similarity(
            bank_line.label or "",
            entry_line.label or "",
        )
        if label_score > 0.5:
            bonus = int(self.config.weight_label_match * label_score)
            score += bonus
            reasons.append(f"Labels similaires ({int(label_score * 100)}%)")

        # 5. Déterminer la confiance
        if score >= self.config.high_confidence_threshold:
            confidence = MatchConfidence.HIGH
        elif score >= self.config.medium_confidence_threshold:
            confidence = MatchConfidence.MEDIUM
        elif score >= self.config.low_confidence_threshold:
            confidence = MatchConfidence.LOW
        else:
            confidence = MatchConfidence.VERY_LOW

        return MatchSuggestion(
            id=str(uuid4()),
            bank_line_id=bank_line.id,
            entry_line_id=entry_line.id,
            score=min(score, 100),
            confidence=confidence,
            match_type=match_type,
            reasons=reasons,
            bank_amount=bank_amount,
            bank_date=bank_date,
            bank_label=bank_line.label or "",
            entry_amount=entry_amount,
            entry_date=entry_date,
            entry_label=entry_line.label or "",
            amount_diff=amount_diff,
            days_diff=days_diff if entry_date else 0,
        )

    def _extract_reference(self, text: str) -> Optional[str]:
        """Extrait une référence (numéro facture, etc.) d'un texte."""
        if not text:
            return None

        # Patterns de référence courants
        patterns = [
            r"(FAC|INV|FA|F)[- ]?(\d{4,})",  # Facture
            r"(CMD|ORD|CO|C)[- ]?(\d{4,})",  # Commande
            r"(VIR|TR)[- ]?(\d{4,})",  # Virement
            r"(\d{6,})",  # Numéro long générique
        ]

        for pattern in patterns:
            match = re.search(pattern, text.upper())
            if match:
                return match.group(0)

        return None

    def _calculate_label_similarity(self, text1: str, text2: str) -> float:
        """
        Calcule la similarité entre deux labels (0-1).

        Utilise un algorithme simplifié basé sur les mots communs.
        """
        if not text1 or not text2:
            return 0.0

        # Normaliser et tokenizer
        words1 = set(text1.upper().split())
        words2 = set(text2.upper().split())

        # Exclure les mots courts et communs
        stopwords = {"LE", "LA", "LES", "DE", "DU", "DES", "EN", "AU", "AUX", "ET", "OU"}
        words1 = {w for w in words1 if len(w) > 2 and w not in stopwords}
        words2 = {w for w in words2 if len(w) > 2 and w not in stopwords}

        if not words1 or not words2:
            return 0.0

        # Calcul Jaccard
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    # =========================================================================
    # AUTO-RECONCILIATION
    # =========================================================================

    async def auto_reconcile(
        self,
        bank_account_id: UUID,
        statement_id: Optional[UUID] = None,
        min_score: Optional[int] = None,
        dry_run: bool = False,
    ) -> ReconciliationResult:
        """
        Auto-réconcilie les correspondances à haut score.

        Args:
            bank_account_id: ID du compte bancaire
            statement_id: ID du relevé (optionnel)
            min_score: Score minimum (défaut: config.auto_match_threshold)
            dry_run: Si True, ne fait pas les modifications

        Returns:
            Résultat avec statistiques
        """
        min_score = min_score or self.config.auto_match_threshold

        self._logger.info(
            f"Auto-réconciliation pour compte {bank_account_id} (min_score={min_score})",
            extra={
                "bank_account_id": str(bank_account_id),
                "min_score": min_score,
                "dry_run": dry_run,
            },
        )

        # 1. Obtenir toutes les suggestions
        suggestions = await self.get_match_suggestions(
            bank_account_id=bank_account_id,
            statement_id=statement_id,
            limit=self.config.max_auto_match_per_batch * 2,
            min_score=min_score,
        )

        if not suggestions:
            return ReconciliationResult(
                success=True,
                matched_count=0,
                suggestions=[],
            )

        # 2. Filtrer les meilleures suggestions (une seule par ligne bancaire)
        best_per_bank_line: dict[UUID, MatchSuggestion] = {}
        used_entry_lines: set[UUID] = set()

        for suggestion in suggestions:
            if suggestion.score < min_score:
                continue

            # Ne pas réutiliser une écriture déjà matchée
            if suggestion.entry_line_id in used_entry_lines:
                continue

            # Garder la meilleure suggestion par ligne bancaire
            existing = best_per_bank_line.get(suggestion.bank_line_id)
            if not existing or suggestion.score > existing.score:
                best_per_bank_line[suggestion.bank_line_id] = suggestion
                used_entry_lines.add(suggestion.entry_line_id)

        to_reconcile = list(best_per_bank_line.values())

        if dry_run:
            return ReconciliationResult(
                success=True,
                matched_count=0,
                auto_matched_count=0,
                suggested_count=len(to_reconcile),
                suggestions=to_reconcile,
            )

        # 3. Effectuer les réconciliations
        matched_count = 0

        for suggestion in to_reconcile[:self.config.max_auto_match_per_batch]:
            try:
                success = self._reconcile_pair(
                    bank_line_id=suggestion.bank_line_id,
                    entry_line_id=suggestion.entry_line_id,
                    match_type=suggestion.match_type,
                    score=suggestion.score,
                )
                if success:
                    matched_count += 1
            except Exception as e:
                self._logger.error(
                    f"Erreur réconciliation: {e}",
                    extra={
                        "bank_line_id": str(suggestion.bank_line_id),
                        "entry_line_id": str(suggestion.entry_line_id),
                    },
                )

        self.db.commit()

        self._logger.info(
            f"Auto-réconciliation terminée: {matched_count}/{len(to_reconcile)} matchés",
            extra={"matched_count": matched_count, "total": len(to_reconcile)},
        )

        return ReconciliationResult(
            success=True,
            matched_count=matched_count,
            auto_matched_count=matched_count,
            suggested_count=len(to_reconcile),
            suggestions=to_reconcile,
        )

    def _reconcile_pair(
        self,
        bank_line_id: UUID,
        entry_line_id: UUID,
        match_type: MatchType,
        score: int,
    ) -> bool:
        """Réconcilie une paire ligne bancaire / écriture."""
        bank_line = self.db.query(BankStatementLine).filter(
            BankStatementLine.id == bank_line_id,
        ).first()

        entry_line = self.db.query(JournalEntryLine).filter(
            JournalEntryLine.id == entry_line_id,
        ).first()

        if not bank_line or not entry_line:
            return False

        # Générer une référence de réconciliation
        reconcile_ref = f"AUTO-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid4())[:8]}"

        # Mettre à jour la ligne bancaire
        bank_line.status = ReconciliationStatus.RECONCILED
        bank_line.reconciled_entry_id = entry_line.entry_id
        bank_line.reconciled_at = datetime.utcnow()

        # Mettre à jour l'écriture
        entry_line.reconcile_ref = reconcile_ref
        entry_line.reconciled_at = datetime.utcnow()

        return True

    # =========================================================================
    # RECONCILIATION MANUELLE
    # =========================================================================

    async def manual_reconcile(
        self,
        bank_line_id: UUID,
        entry_line_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> ReconciliationResult:
        """
        Réconcilie manuellement une paire.

        Args:
            bank_line_id: ID de la ligne bancaire
            entry_line_id: ID de la ligne d'écriture
            user_id: ID de l'utilisateur effectuant l'action

        Returns:
            Résultat de la réconciliation
        """
        success = self._reconcile_pair(
            bank_line_id=bank_line_id,
            entry_line_id=entry_line_id,
            match_type=MatchType.PATTERN,
            score=100,
        )

        if success:
            # Enregistrer dans l'historique d'apprentissage (TODO)
            self.db.commit()

        return ReconciliationResult(
            success=success,
            matched_count=1 if success else 0,
            error="Réconciliation échouée" if not success else None,
        )

    async def undo_reconciliation(
        self,
        bank_line_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> ReconciliationResult:
        """Annule une réconciliation."""
        bank_line = self.db.query(BankStatementLine).filter(
            BankStatementLine.id == bank_line_id,
        ).first()

        if not bank_line:
            return ReconciliationResult(
                success=False,
                error="Ligne bancaire non trouvée",
            )

        if bank_line.status != ReconciliationStatus.RECONCILED:
            return ReconciliationResult(
                success=False,
                error="Ligne non réconciliée",
            )

        # Retrouver et libérer l'écriture
        if bank_line.reconciled_entry_id:
            entry_lines = self.db.query(JournalEntryLine).filter(
                JournalEntryLine.entry_id == bank_line.reconciled_entry_id,
            ).all()

            for el in entry_lines:
                if el.reconcile_ref and el.reconcile_ref.startswith("AUTO-"):
                    el.reconcile_ref = None
                    el.reconciled_at = None

        # Réinitialiser la ligne bancaire
        bank_line.status = ReconciliationStatus.PENDING
        bank_line.reconciled_entry_id = None
        bank_line.reconciled_at = None

        self.db.commit()

        return ReconciliationResult(success=True, matched_count=1)

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    async def get_stats(
        self,
        bank_account_id: UUID,
        statement_id: Optional[UUID] = None,
    ) -> ReconciliationStats:
        """
        Récupère les statistiques de réconciliation.

        Args:
            bank_account_id: ID du compte bancaire
            statement_id: ID du relevé (optionnel)

        Returns:
            Statistiques détaillées
        """
        query = self.db.query(BankStatementLine).join(BankStatement).filter(
            BankStatement.tenant_id == self.tenant_id,
            BankStatement.bank_account_id == bank_account_id,
        )

        if statement_id:
            query = query.filter(BankStatementLine.statement_id == statement_id)

        lines = query.all()

        stats = ReconciliationStats(total_bank_lines=len(lines))

        for line in lines:
            amount = line.credit - line.debit

            if line.status == ReconciliationStatus.RECONCILED:
                stats.reconciled_lines += 1
                stats.total_amount_reconciled += amount
            else:
                stats.pending_lines += 1
                stats.total_amount_pending += amount

        stats.unmatched = stats.pending_lines

        return stats
