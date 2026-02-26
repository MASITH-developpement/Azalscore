"""
AZALSCORE Finance Auto Categorization Service
==============================================

Service de catégorisation automatique des opérations bancaires.

Fonctionnalités:
- Moteur de règles personnalisables
- Pattern matching sur libellés
- Apprentissage des associations utilisateur
- Suggestions de comptes comptables
"""
from __future__ import annotations


import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# =============================================================================
# TYPES
# =============================================================================


class RuleType(str, Enum):
    """Type de règle de catégorisation."""

    KEYWORD = "keyword"  # Mot-clé dans le libellé
    PATTERN = "pattern"  # Expression régulière
    AMOUNT_RANGE = "amount_range"  # Plage de montant
    VENDOR = "vendor"  # Correspondance fournisseur
    CUSTOMER = "customer"  # Correspondance client
    IBAN = "iban"  # Correspondance IBAN
    COMBINED = "combined"  # Combinaison de règles


class MatchConfidence(str, Enum):
    """Niveau de confiance du match."""

    HIGH = "high"  # > 90%
    MEDIUM = "medium"  # 70-90%
    LOW = "low"  # 50-70%
    SUGGESTED = "suggested"  # < 50% (suggestion)


class TransactionType(str, Enum):
    """Type de transaction."""

    DEBIT = "debit"  # Sortie d'argent
    CREDIT = "credit"  # Entrée d'argent


@dataclass
class CategorizationRule:
    """Règle de catégorisation."""

    id: str
    tenant_id: str
    name: str
    rule_type: RuleType
    priority: int = 0  # Plus haut = plus prioritaire

    # Critères
    keywords: list[str] = field(default_factory=list)
    pattern: Optional[str] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    transaction_type: Optional[TransactionType] = None
    iban: Optional[str] = None
    partner_id: Optional[str] = None

    # Actions
    account_code: Optional[str] = None
    account_id: Optional[str] = None
    category: Optional[str] = None
    tax_code: Optional[str] = None
    journal_id: Optional[str] = None

    # Métadonnées
    is_active: bool = True
    auto_apply: bool = False  # Si True, applique sans confirmation
    usage_count: int = 0
    last_used: Optional[datetime] = None


@dataclass
class CategorySuggestion:
    """Suggestion de catégorie."""

    account_code: str
    account_name: str
    category: Optional[str] = None
    confidence: float = 0.0
    match_confidence: MatchConfidence = MatchConfidence.SUGGESTED
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    reason: str = ""


@dataclass
class CategorizationResult:
    """Résultat de catégorisation."""

    success: bool
    transaction_id: Optional[str] = None

    # Catégorie appliquée
    auto_applied: bool = False
    applied_account_code: Optional[str] = None
    applied_account_name: Optional[str] = None
    applied_category: Optional[str] = None
    applied_rule_id: Optional[str] = None

    # Suggestions
    suggestions: list[CategorySuggestion] = field(default_factory=list)

    # Confiance
    confidence: float = 0.0
    match_confidence: MatchConfidence = MatchConfidence.SUGGESTED

    # Erreur
    error: Optional[str] = None


@dataclass
class Transaction:
    """Transaction à catégoriser."""

    id: str
    label: str
    amount: Decimal
    date: datetime
    transaction_type: TransactionType

    # Informations optionnelles
    reference: Optional[str] = None
    counterpart_name: Optional[str] = None
    counterpart_iban: Optional[str] = None
    bank_account_id: Optional[str] = None

    # Catégorisation existante
    current_account_code: Optional[str] = None
    current_category: Optional[str] = None


# =============================================================================
# PATTERNS PRÉDÉFINIS
# =============================================================================


class DefaultPatterns:
    """Patterns par défaut pour la catégorisation française."""

    # Salaires et charges sociales
    SALARY = [
        r"salaire|virement\s*sal|paie|payroll",
        r"urssaf|pole\s*emploi|prevoyance|mutuelle",
        r"retraite|pension|charges\s*sociales",
    ]

    # Loyers et charges
    RENT = [
        r"loyer|bail|location|immobili",
        r"charges\s*locatives|provision\s*charges",
    ]

    # Achats et fournisseurs
    PURCHASES = [
        r"achat|fourniture|materiel",
        r"amazon|amazon\s*eu|amz",
        r"carrefour|leclerc|auchan|metro",
    ]

    # Frais bancaires
    BANK_FEES = [
        r"frais\s*bancaires?|commission|agios?",
        r"cotisation\s*carte|frais\s*cb",
        r"interets\s*debiteurs",
    ]

    # Télécommunications
    TELECOM = [
        r"orange|sfr|bouygues|free|ovh|sosh",
        r"telephone|mobile|internet|fibre",
    ]

    # Énergie
    ENERGY = [
        r"edf|engie|total\s*energie|direct\s*energie",
        r"electricite|gaz|energie",
    ]

    # Assurances
    INSURANCE = [
        r"assurance|axa|maif|macif|matmut|allianz",
        r"prime\s*assurance|cotisation\s*assurance",
    ]

    # Impôts et taxes
    TAXES = [
        r"impot|taxe|tva|cfe|cvae",
        r"tresor\s*public|dgfip|urssaf",
    ]

    # Ventes et clients
    SALES = [
        r"vente|facturation|reglement\s*client",
        r"encaissement|paiement\s*recu",
    ]

    # Mapping compte PCG
    ACCOUNT_MAPPING = {
        "salary": "641100",  # Salaires
        "social_charges": "645000",  # Charges sociales
        "rent": "613200",  # Loyers
        "purchases": "607100",  # Achats marchandises
        "bank_fees": "627100",  # Frais bancaires
        "telecom": "626200",  # Télécommunications
        "energy": "606100",  # Énergie
        "insurance": "616100",  # Assurances
        "taxes": "631000",  # Impôts et taxes
        "sales": "706000",  # Ventes
    }


# =============================================================================
# SERVICE PRINCIPAL
# =============================================================================


class CategorizationService:
    """
    Service de catégorisation automatique des opérations.

    Utilise un système de règles et patterns pour suggérer
    ou appliquer automatiquement des comptes comptables.

    Usage:
        service = CategorizationService(db, tenant_id)

        # Catégoriser une transaction
        result = await service.categorize_transaction(transaction)

        # Avec application automatique
        result = await service.categorize_transaction(
            transaction,
            auto_apply=True
        )
    """

    # Seuils de confiance
    HIGH_CONFIDENCE_THRESHOLD = 90
    MEDIUM_CONFIDENCE_THRESHOLD = 70
    LOW_CONFIDENCE_THRESHOLD = 50
    AUTO_APPLY_THRESHOLD = 95

    def __init__(
        self,
        db: Session,
        tenant_id: str,
    ):
        """
        Initialise le service de catégorisation.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant (obligatoire)
        """
        if not tenant_id:
            raise ValueError("tenant_id est obligatoire")

        self.db = db
        self.tenant_id = tenant_id
        self._rules_cache: list[CategorizationRule] = []
        self._rules_loaded = False

        self._logger = logging.LoggerAdapter(
            logger,
            extra={"tenant_id": tenant_id, "service": "CategorizationService"},
        )

    # =========================================================================
    # CATÉGORISATION PRINCIPALE
    # =========================================================================

    async def categorize_transaction(
        self,
        transaction: Transaction,
        auto_apply: bool = False,
    ) -> CategorizationResult:
        """
        Catégorise une transaction.

        Args:
            transaction: Transaction à catégoriser
            auto_apply: Appliquer automatiquement si confiance suffisante

        Returns:
            CategorizationResult avec suggestions et/ou application
        """
        self._logger.info(
            f"Catégorisation: {transaction.label[:50]}...",
            extra={"transaction_id": transaction.id, "amount": str(transaction.amount)},
        )

        try:
            # 1. Charger les règles du tenant
            await self._load_rules()

            # 2. Chercher les correspondances par règles personnalisées
            suggestions = await self._match_rules(transaction)

            # 3. Chercher les correspondances par patterns par défaut
            default_suggestions = self._match_default_patterns(transaction)
            suggestions.extend(default_suggestions)

            # 4. Chercher les correspondances historiques
            history_suggestions = await self._match_history(transaction)
            suggestions.extend(history_suggestions)

            # 5. Dédoublonner et trier par confiance
            suggestions = self._deduplicate_and_sort(suggestions)

            # 6. Déterminer la confiance globale
            confidence = suggestions[0].confidence if suggestions else 0.0
            match_confidence = self._get_match_confidence(confidence)

            # 7. Appliquer automatiquement si conditions remplies
            auto_applied = False
            applied_account_code = None
            applied_account_name = None
            applied_category = None
            applied_rule_id = None

            if auto_apply and confidence >= self.AUTO_APPLY_THRESHOLD and suggestions:
                best = suggestions[0]
                if best.rule_id:
                    rule = self._get_rule_by_id(best.rule_id)
                    if rule and rule.auto_apply:
                        auto_applied = True
                        applied_account_code = best.account_code
                        applied_account_name = best.account_name
                        applied_category = best.category
                        applied_rule_id = best.rule_id

                        # Mettre à jour l'usage de la règle
                        await self._update_rule_usage(rule.id)

            return CategorizationResult(
                success=True,
                transaction_id=transaction.id,
                auto_applied=auto_applied,
                applied_account_code=applied_account_code,
                applied_account_name=applied_account_name,
                applied_category=applied_category,
                applied_rule_id=applied_rule_id,
                suggestions=suggestions[:5],  # Max 5 suggestions
                confidence=confidence,
                match_confidence=match_confidence,
            )

        except Exception as e:
            self._logger.error(f"Erreur catégorisation: {e}", exc_info=True)
            return CategorizationResult(
                success=False,
                transaction_id=transaction.id,
                error=str(e),
            )

    async def categorize_batch(
        self,
        transactions: list[Transaction],
        auto_apply: bool = False,
    ) -> list[CategorizationResult]:
        """
        Catégorise un lot de transactions.

        Args:
            transactions: Liste de transactions
            auto_apply: Appliquer automatiquement si confiance suffisante

        Returns:
            Liste de résultats
        """
        results = []
        for transaction in transactions:
            result = await self.categorize_transaction(transaction, auto_apply)
            results.append(result)
        return results

    # =========================================================================
    # MATCHING PAR RÈGLES
    # =========================================================================

    async def _load_rules(self) -> None:
        """Charge les règles du tenant."""
        if self._rules_loaded:
            return

        # NOTE: Phase 2 - Charger depuis CategorizationRule table
        # Pour l'instant: règles par défaut
        self._rules_cache = self._get_default_rules()
        self._rules_loaded = True

    def _get_default_rules(self) -> list[CategorizationRule]:
        """Retourne les règles par défaut."""
        rules = [
            CategorizationRule(
                id="rule-salary",
                tenant_id=self.tenant_id,
                name="Salaires",
                rule_type=RuleType.PATTERN,
                pattern="|".join(DefaultPatterns.SALARY),
                transaction_type=TransactionType.DEBIT,
                account_code="641100",
                category="salaires",
                priority=100,
                auto_apply=True,
            ),
            CategorizationRule(
                id="rule-rent",
                tenant_id=self.tenant_id,
                name="Loyers",
                rule_type=RuleType.PATTERN,
                pattern="|".join(DefaultPatterns.RENT),
                transaction_type=TransactionType.DEBIT,
                account_code="613200",
                category="loyers",
                priority=90,
                auto_apply=True,
            ),
            CategorizationRule(
                id="rule-bank-fees",
                tenant_id=self.tenant_id,
                name="Frais bancaires",
                rule_type=RuleType.PATTERN,
                pattern="|".join(DefaultPatterns.BANK_FEES),
                transaction_type=TransactionType.DEBIT,
                account_code="627100",
                category="frais_bancaires",
                priority=95,
                auto_apply=True,
            ),
            CategorizationRule(
                id="rule-telecom",
                tenant_id=self.tenant_id,
                name="Télécommunications",
                rule_type=RuleType.PATTERN,
                pattern="|".join(DefaultPatterns.TELECOM),
                transaction_type=TransactionType.DEBIT,
                account_code="626200",
                category="telecom",
                priority=80,
                auto_apply=False,
            ),
            CategorizationRule(
                id="rule-energy",
                tenant_id=self.tenant_id,
                name="Énergie",
                rule_type=RuleType.PATTERN,
                pattern="|".join(DefaultPatterns.ENERGY),
                transaction_type=TransactionType.DEBIT,
                account_code="606100",
                category="energie",
                priority=80,
                auto_apply=False,
            ),
            CategorizationRule(
                id="rule-insurance",
                tenant_id=self.tenant_id,
                name="Assurances",
                rule_type=RuleType.PATTERN,
                pattern="|".join(DefaultPatterns.INSURANCE),
                transaction_type=TransactionType.DEBIT,
                account_code="616100",
                category="assurances",
                priority=85,
                auto_apply=False,
            ),
            CategorizationRule(
                id="rule-taxes",
                tenant_id=self.tenant_id,
                name="Impôts et taxes",
                rule_type=RuleType.PATTERN,
                pattern="|".join(DefaultPatterns.TAXES),
                transaction_type=TransactionType.DEBIT,
                account_code="631000",
                category="impots",
                priority=90,
                auto_apply=False,
            ),
        ]
        return rules

    async def _match_rules(
        self,
        transaction: Transaction,
    ) -> list[CategorySuggestion]:
        """Trouve les correspondances par règles."""
        suggestions = []

        for rule in sorted(self._rules_cache, key=lambda r: -r.priority):
            if not rule.is_active:
                continue

            match_score = self._evaluate_rule(transaction, rule)
            if match_score > 0:
                suggestions.append(CategorySuggestion(
                    account_code=rule.account_code or "",
                    account_name=self._get_account_name(rule.account_code),
                    category=rule.category,
                    confidence=match_score,
                    match_confidence=self._get_match_confidence(match_score),
                    rule_id=rule.id,
                    rule_name=rule.name,
                    reason=f"Règle: {rule.name}",
                ))

        return suggestions

    def _evaluate_rule(
        self,
        transaction: Transaction,
        rule: CategorizationRule,
    ) -> float:
        """Évalue une règle sur une transaction."""
        score = 0.0
        matches = 0
        criteria = 0

        # Vérifier le type de transaction
        if rule.transaction_type:
            criteria += 1
            if transaction.transaction_type == rule.transaction_type:
                matches += 1
            else:
                return 0  # Type incorrect, règle ne s'applique pas

        # Vérifier le pattern
        if rule.pattern:
            criteria += 1
            if self._match_pattern(transaction.label, rule.pattern):
                matches += 1
                score += 50  # Bonus pour match pattern

        # Vérifier les mots-clés
        if rule.keywords:
            criteria += 1
            label_lower = transaction.label.lower()
            keyword_matches = sum(1 for kw in rule.keywords if kw.lower() in label_lower)
            if keyword_matches > 0:
                matches += 1
                score += min(30, keyword_matches * 10)

        # Vérifier la plage de montant
        if rule.amount_min is not None or rule.amount_max is not None:
            criteria += 1
            amount = abs(transaction.amount)
            in_range = True
            if rule.amount_min and amount < rule.amount_min:
                in_range = False
            if rule.amount_max and amount > rule.amount_max:
                in_range = False
            if in_range:
                matches += 1

        # Vérifier l'IBAN
        if rule.iban and transaction.counterpart_iban:
            criteria += 1
            if rule.iban == transaction.counterpart_iban:
                matches += 1
                score += 40  # Fort bonus pour IBAN exact

        # Calculer le score final
        if criteria == 0:
            return 0

        base_score = (matches / criteria) * 100
        return min(100, base_score + score)

    def _match_pattern(self, text: str, pattern: str) -> bool:
        """Vérifie si le texte correspond au pattern."""
        try:
            return bool(re.search(pattern, text, re.IGNORECASE))
        except re.error:
            return False

    # =========================================================================
    # MATCHING PAR PATTERNS PAR DÉFAUT
    # =========================================================================

    def _match_default_patterns(
        self,
        transaction: Transaction,
    ) -> list[CategorySuggestion]:
        """Trouve les correspondances par patterns par défaut."""
        suggestions = []
        label = transaction.label.lower()

        # Mapping pattern -> catégorie
        pattern_mapping = [
            (DefaultPatterns.SALARY, "salary", "641100", "Salaires bruts"),
            (DefaultPatterns.RENT, "rent", "613200", "Locations immobilières"),
            (DefaultPatterns.BANK_FEES, "bank_fees", "627100", "Frais bancaires"),
            (DefaultPatterns.TELECOM, "telecom", "626200", "Frais postaux et télécommunications"),
            (DefaultPatterns.ENERGY, "energy", "606100", "Fournitures non stockables"),
            (DefaultPatterns.INSURANCE, "insurance", "616100", "Assurances multirisques"),
            (DefaultPatterns.TAXES, "taxes", "631000", "Impôts et taxes"),
            (DefaultPatterns.SALES, "sales", "706000", "Prestations de services"),
        ]

        for patterns, category, account_code, account_name in pattern_mapping:
            for pattern in patterns:
                if self._match_pattern(label, pattern):
                    # Vérifier cohérence débit/crédit
                    if category == "sales" and transaction.transaction_type == TransactionType.DEBIT:
                        continue
                    if category != "sales" and transaction.transaction_type == TransactionType.CREDIT:
                        continue

                    suggestions.append(CategorySuggestion(
                        account_code=account_code,
                        account_name=account_name,
                        category=category,
                        confidence=75.0,  # Confiance moyenne pour pattern par défaut
                        match_confidence=MatchConfidence.MEDIUM,
                        reason=f"Pattern par défaut: {category}",
                    ))
                    break  # Un seul match par catégorie

        return suggestions

    # =========================================================================
    # MATCHING HISTORIQUE
    # =========================================================================

    async def _match_history(
        self,
        transaction: Transaction,
    ) -> list[CategorySuggestion]:
        """Trouve les correspondances basées sur l'historique."""
        # NOTE: Phase 2 - Matching ML basé sur transactions similaires
        return []

    # =========================================================================
    # GESTION DES RÈGLES
    # =========================================================================

    async def create_rule(
        self,
        rule: CategorizationRule,
    ) -> CategorizationRule:
        """
        Crée une nouvelle règle de catégorisation.

        Args:
            rule: Règle à créer

        Returns:
            Règle créée avec ID
        """
        rule.id = str(uuid4())
        rule.tenant_id = self.tenant_id

        # NOTE: Phase 2 - Persister en table CategorizationRule
        self._rules_cache.append(rule)

        self._logger.info(f"Règle créée: {rule.name}", extra={"rule_id": rule.id})
        return rule

    async def update_rule(
        self,
        rule_id: str,
        updates: dict,
    ) -> Optional[CategorizationRule]:
        """
        Met à jour une règle existante.

        Args:
            rule_id: ID de la règle
            updates: Champs à mettre à jour

        Returns:
            Règle mise à jour ou None
        """
        for rule in self._rules_cache:
            if rule.id == rule_id:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                return rule
        return None

    async def delete_rule(self, rule_id: str) -> bool:
        """
        Supprime une règle.

        Args:
            rule_id: ID de la règle

        Returns:
            True si supprimée
        """
        for i, rule in enumerate(self._rules_cache):
            if rule.id == rule_id:
                self._rules_cache.pop(i)
                return True
        return False

    async def list_rules(
        self,
        active_only: bool = True,
    ) -> list[CategorizationRule]:
        """
        Liste les règles du tenant.

        Args:
            active_only: Ne retourner que les règles actives

        Returns:
            Liste de règles
        """
        await self._load_rules()
        if active_only:
            return [r for r in self._rules_cache if r.is_active]
        return self._rules_cache.copy()

    def _get_rule_by_id(self, rule_id: str) -> Optional[CategorizationRule]:
        """Récupère une règle par son ID."""
        for rule in self._rules_cache:
            if rule.id == rule_id:
                return rule
        return None

    async def _update_rule_usage(self, rule_id: str) -> None:
        """Met à jour les statistiques d'usage d'une règle."""
        rule = self._get_rule_by_id(rule_id)
        if rule:
            rule.usage_count += 1
            rule.last_used = datetime.utcnow()

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _get_account_name(self, account_code: Optional[str]) -> str:
        """Retourne le nom du compte depuis le code."""
        if not account_code:
            return ""

        # Mapping simplifié - TODO: charger depuis la base
        account_names = {
            "641100": "Salaires bruts",
            "645000": "Charges sociales",
            "613200": "Locations immobilières",
            "607100": "Achats de marchandises",
            "627100": "Frais bancaires",
            "626200": "Frais postaux et télécommunications",
            "606100": "Fournitures non stockables",
            "616100": "Assurances multirisques",
            "631000": "Impôts et taxes",
            "706000": "Prestations de services",
        }
        return account_names.get(account_code, f"Compte {account_code}")

    def _get_match_confidence(self, score: float) -> MatchConfidence:
        """Détermine le niveau de confiance depuis le score."""
        if score >= self.HIGH_CONFIDENCE_THRESHOLD:
            return MatchConfidence.HIGH
        elif score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return MatchConfidence.MEDIUM
        elif score >= self.LOW_CONFIDENCE_THRESHOLD:
            return MatchConfidence.LOW
        else:
            return MatchConfidence.SUGGESTED

    def _deduplicate_and_sort(
        self,
        suggestions: list[CategorySuggestion],
    ) -> list[CategorySuggestion]:
        """Dédoublonne et trie les suggestions par confiance."""
        # Dédoublonner par account_code (garder le meilleur score)
        seen = {}
        for s in suggestions:
            key = s.account_code
            if key not in seen or s.confidence > seen[key].confidence:
                seen[key] = s

        # Trier par confiance décroissante
        return sorted(seen.values(), key=lambda x: -x.confidence)

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    async def get_stats(self) -> dict:
        """
        Retourne les statistiques de catégorisation.

        Returns:
            Dict avec statistiques
        """
        await self._load_rules()

        return {
            "total_rules": len(self._rules_cache),
            "active_rules": len([r for r in self._rules_cache if r.is_active]),
            "auto_apply_rules": len([r for r in self._rules_cache if r.auto_apply]),
            "most_used_rules": sorted(
                [{"id": r.id, "name": r.name, "count": r.usage_count}
                 for r in self._rules_cache],
                key=lambda x: -x["count"],
            )[:5],
        }
