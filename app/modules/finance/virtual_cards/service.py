"""
AZALSCORE Finance Virtual Cards Service
=======================================

Service pour la gestion des cartes bancaires virtuelles.

Fonctionnalités:
- Création de cartes virtuelles avec limites configurables
- Gestion des limites (par transaction, quotidienne, mensuelle)
- Blocage/déblocage temporaire ou permanent
- Cartes à usage unique
- Historique et statistiques des transactions
"""

import logging
import secrets
import string
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class CardStatus(str, Enum):
    """Statut d'une carte virtuelle."""
    ACTIVE = "active"
    BLOCKED = "blocked"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class CardType(str, Enum):
    """Type de carte virtuelle."""
    STANDARD = "standard"           # Carte réutilisable
    SINGLE_USE = "single_use"       # Usage unique
    RECURRING = "recurring"         # Pour abonnements
    TEAM = "team"                   # Partagée équipe
    EXPENSE = "expense"             # Notes de frais


class CardLimitType(str, Enum):
    """Type de limite."""
    PER_TRANSACTION = "per_transaction"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    TOTAL = "total"


class TransactionStatus(str, Enum):
    """Statut d'une transaction."""
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    REVERSED = "reversed"


class DeclineReason(str, Enum):
    """Raison de refus d'une transaction."""
    INSUFFICIENT_LIMIT = "insufficient_limit"
    CARD_BLOCKED = "card_blocked"
    CARD_EXPIRED = "card_expired"
    SINGLE_USE_EXHAUSTED = "single_use_exhausted"
    MERCHANT_RESTRICTED = "merchant_restricted"
    AMOUNT_EXCEEDED = "amount_exceeded"


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class CardLimit:
    """Limite de carte."""
    limit_type: CardLimitType
    amount: Decimal
    used: Decimal = Decimal("0")
    reset_at: Optional[datetime] = None

    @property
    def remaining(self) -> Decimal:
        """Montant restant disponible."""
        return max(Decimal("0"), self.amount - self.used)

    @property
    def usage_percent(self) -> Decimal:
        """Pourcentage d'utilisation."""
        if self.amount == 0:
            return Decimal("100")
        return (self.used / self.amount * 100).quantize(Decimal("0.01"))


@dataclass
class VirtualCard:
    """Carte virtuelle."""
    id: str
    tenant_id: str
    card_number: str               # Masqué: **** **** **** 1234
    card_number_full: str          # Complet: 4532 xxxx xxxx 1234
    expiry_month: int
    expiry_year: int
    cvv: str
    holder_name: str
    card_type: CardType
    status: CardStatus
    limits: list[CardLimit] = field(default_factory=list)
    merchant_categories: list[str] = field(default_factory=list)  # MCC codes autorisés
    blocked_merchants: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    used_count: int = 0
    total_spent: Decimal = Decimal("0")
    metadata: dict = field(default_factory=dict)

    @property
    def masked_number(self) -> str:
        """Numéro de carte masqué."""
        if len(self.card_number_full) >= 4:
            return f"**** **** **** {self.card_number_full[-4:]}"
        return "**** **** **** ****"

    @property
    def expiry_date(self) -> str:
        """Date d'expiration formatée."""
        return f"{self.expiry_month:02d}/{str(self.expiry_year)[-2:]}"

    @property
    def is_active(self) -> bool:
        """Vérifie si la carte est utilisable."""
        if self.status != CardStatus.ACTIVE:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True


@dataclass
class CardTransaction:
    """Transaction sur une carte virtuelle."""
    id: str
    tenant_id: str
    card_id: str
    amount: Decimal
    currency: str
    merchant_name: str
    merchant_category: str          # MCC code
    merchant_country: str
    status: TransactionStatus
    decline_reason: Optional[DeclineReason] = None
    authorization_code: Optional[str] = None
    transaction_date: datetime = field(default_factory=datetime.now)
    settled_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class CardStats:
    """Statistiques d'une carte."""
    card_id: str
    total_transactions: int
    approved_transactions: int
    declined_transactions: int
    total_spent: Decimal
    average_transaction: Decimal
    most_used_merchant: Optional[str] = None
    most_used_category: Optional[str] = None
    spending_by_category: dict = field(default_factory=dict)
    spending_by_day: dict = field(default_factory=dict)


@dataclass
class CreateCardResult:
    """Résultat de création de carte."""
    success: bool
    card: Optional[VirtualCard] = None
    error: Optional[str] = None


@dataclass
class TransactionResult:
    """Résultat d'une tentative de transaction."""
    success: bool
    transaction: Optional[CardTransaction] = None
    decline_reason: Optional[DeclineReason] = None
    error: Optional[str] = None


# =============================================================================
# SERVICE
# =============================================================================


class VirtualCardService:
    """
    Service de gestion des cartes virtuelles.

    Multi-tenant: OUI - Chaque carte liée à un tenant_id
    Sécurité: Génération sécurisée, numéros masqués
    """

    # BIN pour les cartes virtuelles (test)
    CARD_BIN = "453223"  # Visa test BIN

    # Catégories de marchands par défaut
    DEFAULT_MERCHANT_CATEGORIES = [
        "5411",  # Grocery stores
        "5812",  # Restaurants
        "5814",  # Fast food
        "5912",  # Drug stores
        "5941",  # Sporting goods
        "5942",  # Book stores
        "5999",  # Misc retail
    ]

    def __init__(
        self,
        db: Session,
        tenant_id: str,
    ):
        if not tenant_id:
            raise ValueError("tenant_id est requis")

        self.db = db
        self.tenant_id = tenant_id
        self._cards: dict[str, VirtualCard] = {}
        self._transactions: list[CardTransaction] = []

        logger.info(f"VirtualCardService initialisé pour tenant {tenant_id}")

    # =========================================================================
    # CARD GENERATION
    # =========================================================================

    def _generate_card_number(self) -> str:
        """Génère un numéro de carte valide (Luhn)."""
        # Générer 9 chiffres aléatoires après le BIN
        middle = "".join(secrets.choice(string.digits) for _ in range(9))
        partial = self.CARD_BIN + middle

        # Calculer le chiffre de contrôle Luhn
        check_digit = self._luhn_checksum(partial)

        return partial + str(check_digit)

    def _luhn_checksum(self, number: str) -> int:
        """Calcule le chiffre de contrôle Luhn."""
        digits = [int(d) for d in number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]

        checksum = sum(odd_digits)
        for d in even_digits:
            doubled = d * 2
            checksum += doubled if doubled < 10 else doubled - 9

        return (10 - (checksum % 10)) % 10

    def _generate_cvv(self) -> str:
        """Génère un CVV."""
        return "".join(secrets.choice(string.digits) for _ in range(3))

    def _generate_expiry(self, months: int = 36) -> tuple[int, int]:
        """Génère une date d'expiration."""
        expiry_date = date.today() + timedelta(days=months * 30)
        return expiry_date.month, expiry_date.year

    # =========================================================================
    # CARD MANAGEMENT
    # =========================================================================

    async def create_card(
        self,
        holder_name: str,
        card_type: CardType = CardType.STANDARD,
        limit_per_transaction: Optional[Decimal] = None,
        limit_daily: Optional[Decimal] = None,
        limit_monthly: Optional[Decimal] = None,
        limit_total: Optional[Decimal] = None,
        merchant_categories: Optional[list[str]] = None,
        expires_in_days: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> CreateCardResult:
        """
        Crée une nouvelle carte virtuelle.

        Args:
            holder_name: Nom du titulaire
            card_type: Type de carte
            limit_per_transaction: Limite par transaction
            limit_daily: Limite quotidienne
            limit_monthly: Limite mensuelle
            limit_total: Limite totale (budget)
            merchant_categories: MCC codes autorisés
            expires_in_days: Jours avant expiration
            metadata: Métadonnées additionnelles
        """
        try:
            card_id = str(uuid.uuid4())
            card_number = self._generate_card_number()
            cvv = self._generate_cvv()
            expiry_month, expiry_year = self._generate_expiry()

            # Construire les limites
            limits = []
            if limit_per_transaction:
                limits.append(CardLimit(
                    limit_type=CardLimitType.PER_TRANSACTION,
                    amount=limit_per_transaction,
                ))
            if limit_daily:
                limits.append(CardLimit(
                    limit_type=CardLimitType.DAILY,
                    amount=limit_daily,
                    reset_at=datetime.now() + timedelta(days=1),
                ))
            if limit_monthly:
                limits.append(CardLimit(
                    limit_type=CardLimitType.MONTHLY,
                    amount=limit_monthly,
                    reset_at=datetime.now() + timedelta(days=30),
                ))
            if limit_total:
                limits.append(CardLimit(
                    limit_type=CardLimitType.TOTAL,
                    amount=limit_total,
                ))

            # Expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now() + timedelta(days=expires_in_days)
            elif card_type == CardType.SINGLE_USE:
                expires_at = datetime.now() + timedelta(days=1)  # 24h par défaut

            card = VirtualCard(
                id=card_id,
                tenant_id=self.tenant_id,
                card_number=f"**** **** **** {card_number[-4:]}",
                card_number_full=card_number,
                expiry_month=expiry_month,
                expiry_year=expiry_year,
                cvv=cvv,
                holder_name=holder_name,
                card_type=card_type,
                status=CardStatus.ACTIVE,
                limits=limits,
                merchant_categories=merchant_categories or [],
                expires_at=expires_at,
                metadata=metadata or {},
            )

            self._cards[card_id] = card

            logger.info(
                f"Carte virtuelle créée: {card.masked_number} "
                f"({card_type.value}) pour tenant {self.tenant_id}"
            )

            return CreateCardResult(success=True, card=card)

        except Exception as e:
            logger.error(f"Erreur création carte: {e}")
            return CreateCardResult(success=False, error=str(e))

    async def get_card(self, card_id: str) -> Optional[VirtualCard]:
        """Récupère une carte par son ID."""
        card = self._cards.get(card_id)
        if card and card.tenant_id == self.tenant_id:
            return card
        return None

    async def list_cards(
        self,
        status: Optional[CardStatus] = None,
        card_type: Optional[CardType] = None,
    ) -> list[VirtualCard]:
        """Liste les cartes du tenant."""
        cards = [
            card for card in self._cards.values()
            if card.tenant_id == self.tenant_id
        ]

        if status:
            cards = [c for c in cards if c.status == status]

        if card_type:
            cards = [c for c in cards if c.card_type == card_type]

        return sorted(cards, key=lambda c: c.created_at, reverse=True)

    async def block_card(
        self,
        card_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Bloque une carte."""
        card = await self.get_card(card_id)
        if not card:
            return False

        card.status = CardStatus.BLOCKED
        card.updated_at = datetime.now()
        card.metadata["block_reason"] = reason or "Manual block"
        card.metadata["blocked_at"] = datetime.now().isoformat()

        logger.info(f"Carte {card.masked_number} bloquée: {reason}")
        return True

    async def unblock_card(self, card_id: str) -> bool:
        """Débloque une carte."""
        card = await self.get_card(card_id)
        if not card:
            return False

        if card.status != CardStatus.BLOCKED:
            return False

        card.status = CardStatus.ACTIVE
        card.updated_at = datetime.now()
        card.metadata.pop("block_reason", None)
        card.metadata["unblocked_at"] = datetime.now().isoformat()

        logger.info(f"Carte {card.masked_number} débloquée")
        return True

    async def cancel_card(
        self,
        card_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Annule définitivement une carte."""
        card = await self.get_card(card_id)
        if not card:
            return False

        card.status = CardStatus.CANCELLED
        card.updated_at = datetime.now()
        card.metadata["cancel_reason"] = reason or "Manual cancellation"
        card.metadata["cancelled_at"] = datetime.now().isoformat()

        logger.info(f"Carte {card.masked_number} annulée: {reason}")
        return True

    async def update_limits(
        self,
        card_id: str,
        limit_per_transaction: Optional[Decimal] = None,
        limit_daily: Optional[Decimal] = None,
        limit_monthly: Optional[Decimal] = None,
        limit_total: Optional[Decimal] = None,
    ) -> bool:
        """Met à jour les limites d'une carte."""
        card = await self.get_card(card_id)
        if not card:
            return False

        # Mise à jour des limites existantes ou ajout de nouvelles
        limit_updates = {
            CardLimitType.PER_TRANSACTION: limit_per_transaction,
            CardLimitType.DAILY: limit_daily,
            CardLimitType.MONTHLY: limit_monthly,
            CardLimitType.TOTAL: limit_total,
        }

        for limit_type, new_amount in limit_updates.items():
            if new_amount is not None:
                # Chercher limite existante
                existing = next(
                    (l for l in card.limits if l.limit_type == limit_type),
                    None
                )
                if existing:
                    existing.amount = new_amount
                else:
                    card.limits.append(CardLimit(
                        limit_type=limit_type,
                        amount=new_amount,
                    ))

        card.updated_at = datetime.now()

        logger.info(f"Limites mises à jour pour carte {card.masked_number}")
        return True

    async def add_blocked_merchant(
        self,
        card_id: str,
        merchant_id: str,
    ) -> bool:
        """Ajoute un marchand bloqué."""
        card = await self.get_card(card_id)
        if not card:
            return False

        if merchant_id not in card.blocked_merchants:
            card.blocked_merchants.append(merchant_id)
            card.updated_at = datetime.now()

        return True

    async def remove_blocked_merchant(
        self,
        card_id: str,
        merchant_id: str,
    ) -> bool:
        """Retire un marchand de la liste bloquée."""
        card = await self.get_card(card_id)
        if not card:
            return False

        if merchant_id in card.blocked_merchants:
            card.blocked_merchants.remove(merchant_id)
            card.updated_at = datetime.now()

        return True

    # =========================================================================
    # TRANSACTIONS
    # =========================================================================

    async def authorize_transaction(
        self,
        card_id: str,
        amount: Decimal,
        currency: str,
        merchant_name: str,
        merchant_category: str,
        merchant_country: str = "FR",
        metadata: Optional[dict] = None,
    ) -> TransactionResult:
        """
        Autorise une transaction sur une carte.

        Vérifie:
        - Statut de la carte
        - Limites
        - Marchand autorisé
        - Catégorie autorisée
        """
        card = await self.get_card(card_id)
        if not card:
            return TransactionResult(
                success=False,
                decline_reason=DeclineReason.CARD_BLOCKED,
                error="Carte non trouvée",
            )

        # Vérification usage unique déjà utilisé (avant statut car carte bloquée après usage)
        if card.card_type == CardType.SINGLE_USE and card.used_count > 0:
            return TransactionResult(
                success=False,
                decline_reason=DeclineReason.SINGLE_USE_EXHAUSTED,
                error="Carte à usage unique déjà utilisée",
            )

        # Vérification statut
        if card.status == CardStatus.BLOCKED:
            return TransactionResult(
                success=False,
                decline_reason=DeclineReason.CARD_BLOCKED,
                error="Carte bloquée",
            )

        if card.status == CardStatus.EXPIRED or (
            card.expires_at and datetime.now() > card.expires_at
        ):
            card.status = CardStatus.EXPIRED
            return TransactionResult(
                success=False,
                decline_reason=DeclineReason.CARD_EXPIRED,
                error="Carte expirée",
            )

        if card.status != CardStatus.ACTIVE:
            return TransactionResult(
                success=False,
                decline_reason=DeclineReason.CARD_BLOCKED,
                error=f"Carte non active: {card.status.value}",
            )

        # Vérification marchand bloqué
        if merchant_name in card.blocked_merchants:
            return TransactionResult(
                success=False,
                decline_reason=DeclineReason.MERCHANT_RESTRICTED,
                error="Marchand bloqué",
            )

        # Vérification catégorie autorisée
        if card.merchant_categories and merchant_category not in card.merchant_categories:
            return TransactionResult(
                success=False,
                decline_reason=DeclineReason.MERCHANT_RESTRICTED,
                error="Catégorie de marchand non autorisée",
            )

        # Vérification des limites
        for limit in card.limits:
            if limit.limit_type == CardLimitType.PER_TRANSACTION:
                if amount > limit.amount:
                    return TransactionResult(
                        success=False,
                        decline_reason=DeclineReason.AMOUNT_EXCEEDED,
                        error=f"Montant dépasse la limite par transaction ({limit.amount})",
                    )
            else:
                if amount > limit.remaining:
                    return TransactionResult(
                        success=False,
                        decline_reason=DeclineReason.INSUFFICIENT_LIMIT,
                        error=f"Limite {limit.limit_type.value} insuffisante ({limit.remaining} restant)",
                    )

        # Transaction approuvée
        transaction = CardTransaction(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            card_id=card_id,
            amount=amount,
            currency=currency,
            merchant_name=merchant_name,
            merchant_category=merchant_category,
            merchant_country=merchant_country,
            status=TransactionStatus.APPROVED,
            authorization_code=self._generate_auth_code(),
            metadata=metadata or {},
        )

        # Mise à jour des limites
        for limit in card.limits:
            if limit.limit_type != CardLimitType.PER_TRANSACTION:
                limit.used += amount

        # Mise à jour carte
        card.used_count += 1
        card.total_spent += amount
        card.updated_at = datetime.now()

        # Si usage unique, bloquer après utilisation
        if card.card_type == CardType.SINGLE_USE:
            card.status = CardStatus.BLOCKED
            card.metadata["single_use_completed"] = datetime.now().isoformat()

        self._transactions.append(transaction)

        logger.info(
            f"Transaction autorisée: {amount} {currency} "
            f"sur carte {card.masked_number} chez {merchant_name}"
        )

        return TransactionResult(success=True, transaction=transaction)

    def _generate_auth_code(self) -> str:
        """Génère un code d'autorisation."""
        return "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    async def decline_transaction(
        self,
        card_id: str,
        amount: Decimal,
        currency: str,
        merchant_name: str,
        merchant_category: str,
        reason: DeclineReason,
        merchant_country: str = "FR",
    ) -> CardTransaction:
        """Enregistre une transaction refusée."""
        transaction = CardTransaction(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            card_id=card_id,
            amount=amount,
            currency=currency,
            merchant_name=merchant_name,
            merchant_category=merchant_category,
            merchant_country=merchant_country,
            status=TransactionStatus.DECLINED,
            decline_reason=reason,
        )

        self._transactions.append(transaction)

        logger.warning(
            f"Transaction refusée: {amount} {currency} "
            f"sur carte {card_id} - {reason.value}"
        )

        return transaction

    async def get_transactions(
        self,
        card_id: Optional[str] = None,
        status: Optional[TransactionStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[CardTransaction]:
        """Récupère les transactions."""
        transactions = [
            t for t in self._transactions
            if t.tenant_id == self.tenant_id
        ]

        if card_id:
            transactions = [t for t in transactions if t.card_id == card_id]

        if status:
            transactions = [t for t in transactions if t.status == status]

        if start_date:
            transactions = [t for t in transactions if t.transaction_date >= start_date]

        if end_date:
            transactions = [t for t in transactions if t.transaction_date <= end_date]

        return sorted(
            transactions,
            key=lambda t: t.transaction_date,
            reverse=True
        )[:limit]

    async def reverse_transaction(
        self,
        transaction_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Annule une transaction (remboursement)."""
        transaction = next(
            (t for t in self._transactions
             if t.id == transaction_id and t.tenant_id == self.tenant_id),
            None
        )

        if not transaction:
            return False

        if transaction.status != TransactionStatus.APPROVED:
            return False

        # Restaurer les limites
        card = await self.get_card(transaction.card_id)
        if card:
            for limit in card.limits:
                if limit.limit_type != CardLimitType.PER_TRANSACTION:
                    limit.used -= transaction.amount
            card.total_spent -= transaction.amount

        transaction.status = TransactionStatus.REVERSED
        transaction.metadata["reverse_reason"] = reason or "Manual reversal"
        transaction.metadata["reversed_at"] = datetime.now().isoformat()

        logger.info(f"Transaction {transaction_id} annulée: {reason}")
        return True

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_card_stats(self, card_id: str) -> Optional[CardStats]:
        """Calcule les statistiques d'une carte."""
        card = await self.get_card(card_id)
        if not card:
            return None

        transactions = await self.get_transactions(card_id=card_id)

        approved = [t for t in transactions if t.status == TransactionStatus.APPROVED]
        declined = [t for t in transactions if t.status == TransactionStatus.DECLINED]

        total_spent = sum(t.amount for t in approved)
        avg_transaction = total_spent / len(approved) if approved else Decimal("0")

        # Spending by category
        spending_by_category: dict[str, Decimal] = {}
        for t in approved:
            cat = t.merchant_category
            spending_by_category[cat] = spending_by_category.get(cat, Decimal("0")) + t.amount

        # Most used merchant
        merchant_counts: dict[str, int] = {}
        for t in approved:
            merchant_counts[t.merchant_name] = merchant_counts.get(t.merchant_name, 0) + 1
        most_used_merchant = max(merchant_counts, key=merchant_counts.get) if merchant_counts else None

        # Most used category
        most_used_category = max(spending_by_category, key=spending_by_category.get) if spending_by_category else None

        return CardStats(
            card_id=card_id,
            total_transactions=len(transactions),
            approved_transactions=len(approved),
            declined_transactions=len(declined),
            total_spent=total_spent,
            average_transaction=avg_transaction,
            most_used_merchant=most_used_merchant,
            most_used_category=most_used_category,
            spending_by_category={k: str(v) for k, v in spending_by_category.items()},
        )

    async def get_spending_alerts(
        self,
        threshold_percent: Decimal = Decimal("80"),
    ) -> list[dict]:
        """Retourne les alertes de dépassement de limites."""
        alerts = []

        cards = await self.list_cards(status=CardStatus.ACTIVE)

        for card in cards:
            for limit in card.limits:
                if limit.usage_percent >= threshold_percent:
                    alerts.append({
                        "card_id": card.id,
                        "card_number": card.masked_number,
                        "limit_type": limit.limit_type.value,
                        "limit_amount": str(limit.amount),
                        "used": str(limit.used),
                        "remaining": str(limit.remaining),
                        "usage_percent": str(limit.usage_percent),
                        "alert_level": "critical" if limit.usage_percent >= 95 else "warning",
                    })

        return sorted(alerts, key=lambda a: float(a["usage_percent"]), reverse=True)

    # =========================================================================
    # UTILITIES
    # =========================================================================

    async def reset_daily_limits(self):
        """Réinitialise les limites quotidiennes."""
        now = datetime.now()
        cards = await self.list_cards()

        for card in cards:
            for limit in card.limits:
                if limit.limit_type == CardLimitType.DAILY:
                    if limit.reset_at and now >= limit.reset_at:
                        limit.used = Decimal("0")
                        limit.reset_at = now + timedelta(days=1)

    async def reset_monthly_limits(self):
        """Réinitialise les limites mensuelles."""
        now = datetime.now()
        cards = await self.list_cards()

        for card in cards:
            for limit in card.limits:
                if limit.limit_type == CardLimitType.MONTHLY:
                    if limit.reset_at and now >= limit.reset_at:
                        limit.used = Decimal("0")
                        limit.reset_at = now + timedelta(days=30)

    def get_card_types(self) -> list[dict]:
        """Liste les types de cartes disponibles."""
        return [
            {
                "type": CardType.STANDARD.value,
                "name": "Carte Standard",
                "description": "Carte réutilisable avec limites configurables",
            },
            {
                "type": CardType.SINGLE_USE.value,
                "name": "Usage Unique",
                "description": "Carte utilisable une seule fois",
            },
            {
                "type": CardType.RECURRING.value,
                "name": "Abonnement",
                "description": "Carte pour paiements récurrents",
            },
            {
                "type": CardType.TEAM.value,
                "name": "Équipe",
                "description": "Carte partagée entre membres d'équipe",
            },
            {
                "type": CardType.EXPENSE.value,
                "name": "Notes de Frais",
                "description": "Carte pour dépenses professionnelles",
            },
        ]
