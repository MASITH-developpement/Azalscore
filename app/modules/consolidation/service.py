"""
Module de Consolidation Comptable - GAP-026

Fonctionnalités de consolidation pour groupes de sociétés:
- Consolidation par intégration globale
- Consolidation par intégration proportionnelle
- Consolidation par mise en équivalence
- Élimination des opérations intra-groupe
- Écarts d'acquisition (goodwill)
- Conversion des devises (méthode du cours de clôture)
- Tableaux de variation des capitaux propres

Normes supportées:
- Règlement ANC 2020-01 (France)
- IFRS 10, 11, 12 (international)
- US GAAP ASC 810 (États-Unis)

Architecture multi-tenant avec isolation stricte.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class ConsolidationMethod(Enum):
    """Méthode de consolidation."""
    FULL_INTEGRATION = "full_integration"  # Intégration globale (>50% contrôle)
    PROPORTIONAL = "proportional"  # Intégration proportionnelle (co-entreprises)
    EQUITY_METHOD = "equity_method"  # Mise en équivalence (20-50% influence notable)
    NOT_CONSOLIDATED = "not_consolidated"  # Non consolidé (<20%)


class ControlType(Enum):
    """Type de contrôle."""
    EXCLUSIVE = "exclusive"  # Contrôle exclusif
    JOINT = "joint"  # Contrôle conjoint
    SIGNIFICANT_INFLUENCE = "significant_influence"  # Influence notable
    NONE = "none"  # Pas de contrôle


class CurrencyConversionMethod(Enum):
    """Méthode de conversion des devises."""
    CLOSING_RATE = "closing_rate"  # Cours de clôture (actifs/passifs)
    AVERAGE_RATE = "average_rate"  # Cours moyen (compte de résultat)
    HISTORICAL_RATE = "historical_rate"  # Cours historique (capitaux propres)


class EliminationType(Enum):
    """Type d'élimination intra-groupe."""
    INTERCOMPANY_SALES = "intercompany_sales"  # Ventes intra-groupe
    INTERCOMPANY_RECEIVABLES = "intercompany_receivables"  # Créances/dettes
    INTERCOMPANY_DIVIDENDS = "intercompany_dividends"  # Dividendes
    INTERCOMPANY_PROVISIONS = "intercompany_provisions"  # Provisions
    INTERNAL_MARGIN = "internal_margin"  # Marges sur stocks
    INTERNAL_FIXED_ASSETS = "internal_fixed_assets"  # Plus-values immos


class AccountingStandard(Enum):
    """Référentiel comptable."""
    FRENCH_GAAP = "french_gaap"  # PCG / Règlement ANC
    IFRS = "ifrs"  # Normes internationales
    US_GAAP = "us_gaap"  # Normes américaines


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Entity:
    """Entité juridique du groupe."""
    id: str
    code: str
    name: str
    country: str
    currency: str
    tenant_id: str  # Lien vers le tenant AZALSCORE

    # Dates
    fiscal_year_end_month: int = 12  # Mois de clôture
    acquisition_date: Optional[date] = None
    disposal_date: Optional[date] = None

    # Classification
    is_parent: bool = False
    parent_id: Optional[str] = None
    consolidation_method: ConsolidationMethod = ConsolidationMethod.NOT_CONSOLIDATED

    # Participation
    ownership_percentage: Decimal = Decimal("0")  # % détention directe
    voting_rights_percentage: Decimal = Decimal("0")  # % droits de vote
    control_type: ControlType = ControlType.NONE

    # Métadonnées
    sector: Optional[str] = None
    registration_number: Optional[str] = None  # SIREN, etc.
    is_active: bool = True


@dataclass
class Participation:
    """Lien de participation entre entités."""
    id: str
    parent_entity_id: str
    subsidiary_entity_id: str

    # Pourcentages
    direct_ownership: Decimal  # Détention directe
    indirect_ownership: Decimal = Decimal("0")  # Via autres filiales
    total_ownership: Decimal = Decimal("0")  # Total

    voting_rights: Decimal = Decimal("0")

    # Acquisition
    acquisition_date: date = field(default_factory=date.today)
    acquisition_cost: Decimal = Decimal("0")
    fair_value_at_acquisition: Decimal = Decimal("0")

    # Goodwill
    goodwill_amount: Decimal = Decimal("0")
    goodwill_impairment: Decimal = Decimal("0")

    def __post_init__(self):
        if self.total_ownership == 0:
            self.total_ownership = self.direct_ownership + self.indirect_ownership


@dataclass
class ExchangeRate:
    """Cours de change."""
    from_currency: str
    to_currency: str
    rate_date: date
    closing_rate: Decimal  # Cours de clôture
    average_rate: Decimal  # Cours moyen période
    historical_rate: Optional[Decimal] = None  # Cours historique si pertinent


@dataclass
class TrialBalanceEntry:
    """Ligne de balance."""
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal
    balance: Decimal
    currency: str


@dataclass
class EntityTrialBalance:
    """Balance d'une entité."""
    entity_id: str
    period_start: date
    period_end: date
    entries: List[TrialBalanceEntry]
    currency: str
    is_audited: bool = False


@dataclass
class IntercompanyTransaction:
    """Transaction intra-groupe."""
    id: str
    entity1_id: str
    entity2_id: str
    transaction_date: date

    # Montants
    amount_entity1: Decimal  # Montant chez entité 1
    amount_entity2: Decimal  # Montant chez entité 2
    currency: str

    # Type
    elimination_type: EliminationType
    description: str

    # Comptes
    account_code_entity1: str
    account_code_entity2: str

    # Écart éventuel (doit être 0 si correctement rapproché)
    difference: Decimal = Decimal("0")
    is_reconciled: bool = False


@dataclass
class EliminationEntry:
    """Écriture d'élimination."""
    id: str
    consolidation_id: str
    elimination_type: EliminationType

    # Journal
    description: str
    entries: List[Dict[str, Any]]  # [{account, debit, credit, entity_id}, ...]

    # Traçabilité
    source_transaction_id: Optional[str] = None
    is_automatic: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GoodwillCalculation:
    """Calcul de l'écart d'acquisition."""
    participation_id: str
    calculation_date: date

    # Coût d'acquisition
    acquisition_cost: Decimal

    # Quote-part actif net à la juste valeur
    net_assets_fair_value: Decimal
    ownership_percentage: Decimal
    group_share_net_assets: Decimal

    # Goodwill
    goodwill: Decimal

    # Détails actif net
    assets_fair_value: Decimal = Decimal("0")
    liabilities_fair_value: Decimal = Decimal("0")
    revaluation_adjustments: List[Dict[str, Decimal]] = field(default_factory=list)


@dataclass
class MinorityInterest:
    """Intérêts minoritaires."""
    entity_id: str
    period_end: date

    # Capitaux propres
    total_equity: Decimal
    minority_percentage: Decimal
    minority_share: Decimal

    # Résultat
    net_income: Decimal
    minority_income: Decimal


@dataclass
class CurrencyTranslation:
    """Conversion d'une balance en devise de consolidation."""
    entity_id: str
    source_currency: str
    target_currency: str
    period_end: date

    # Cours utilisés
    closing_rate: Decimal
    average_rate: Decimal

    # Montants
    assets_original: Decimal
    assets_converted: Decimal
    liabilities_original: Decimal
    liabilities_converted: Decimal
    equity_original: Decimal
    equity_converted: Decimal
    income_original: Decimal
    income_converted: Decimal

    # Écart de conversion
    translation_difference: Decimal


@dataclass
class ConsolidationPackage:
    """Paquet de consolidation (données d'une entité)."""
    entity_id: str
    period_start: date
    period_end: date

    # Données comptables
    trial_balance: EntityTrialBalance

    # Transactions intra-groupe
    intercompany_transactions: List[IntercompanyTransaction] = field(default_factory=list)

    # Informations complémentaires
    goodwill_impairment: Decimal = Decimal("0")
    dividend_paid_to_parent: Decimal = Decimal("0")

    # Statut
    is_submitted: bool = False
    submitted_at: Optional[datetime] = None
    is_validated: bool = False
    validated_at: Optional[datetime] = None


@dataclass
class ConsolidationResult:
    """Résultat d'une consolidation."""
    id: str
    tenant_id: str
    period_start: date
    period_end: date
    consolidation_currency: str
    accounting_standard: AccountingStandard

    # Entités incluses
    entities: List[Entity]
    participations: List[Participation]

    # Balances
    entity_balances: Dict[str, EntityTrialBalance]
    currency_translations: Dict[str, CurrencyTranslation]

    # Éliminations
    elimination_entries: List[EliminationEntry]

    # Résultats
    consolidated_trial_balance: List[TrialBalanceEntry]
    minority_interests: List[MinorityInterest]
    goodwill_calculations: List[GoodwillCalculation]

    # Écart de conversion
    total_translation_difference: Decimal = Decimal("0")

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    is_final: bool = False


# ============================================================================
# MAPPING COMPTES PCG -> POSTES CONSOLIDÉS
# ============================================================================

ACCOUNT_MAPPING_PCG = {
    # Actif immobilisé
    "20": "immobilisations_incorporelles",
    "21": "immobilisations_corporelles",
    "22": "immobilisations_mises_en_concession",
    "23": "immobilisations_en_cours",
    "26": "participations",
    "27": "autres_immobilisations_financieres",

    # Actif circulant
    "31": "matieres_premieres",
    "33": "en_cours_production",
    "35": "produits_finis",
    "37": "marchandises",
    "40": "fournisseurs",
    "41": "clients",
    "42": "personnel",
    "43": "securite_sociale",
    "44": "etat",
    "45": "groupe_associes",
    "46": "debiteurs_divers",
    "47": "comptes_attente",
    "48": "charges_repartir",
    "49": "provisions_depreciation_comptes_tiers",
    "50": "valeurs_mobilieres_placement",
    "51": "banques",
    "53": "caisse",

    # Capitaux propres
    "10": "capital",
    "11": "report_nouveau",
    "12": "resultat_exercice",
    "13": "subventions_investissement",
    "14": "provisions_reglementees",
    "15": "provisions_risques_charges",

    # Dettes
    "16": "emprunts",
    "17": "dettes_rattachees_participations",
    "18": "comptes_liaison",
    "19": "ecarts_conversion_passif",

    # Charges
    "60": "achats",
    "61": "services_exterieurs",
    "62": "autres_services_exterieurs",
    "63": "impots_taxes",
    "64": "charges_personnel",
    "65": "autres_charges_gestion",
    "66": "charges_financieres",
    "67": "charges_exceptionnelles",
    "68": "dotations_amortissements",
    "69": "participation_impots",

    # Produits
    "70": "ventes_produits",
    "71": "production_stockee",
    "72": "production_immobilisee",
    "73": "produits_nets_partiels",
    "74": "subventions_exploitation",
    "75": "autres_produits_gestion",
    "76": "produits_financiers",
    "77": "produits_exceptionnels",
    "78": "reprises_provisions",
    "79": "transferts_charges",
}


# ============================================================================
# SERVICE DE CONSOLIDATION
# ============================================================================

class ConsolidationService:
    """
    Service principal de consolidation comptable.

    Gère:
    - Structure du groupe
    - Collecte des paquets de consolidation
    - Éliminations intra-groupe
    - Conversion des devises
    - Calcul des minoritaires
    - Production des états consolidés
    """

    def __init__(
        self,
        tenant_id: str,
        consolidation_currency: str = "EUR",
        accounting_standard: AccountingStandard = AccountingStandard.FRENCH_GAAP
    ):
        self.tenant_id = tenant_id
        self.consolidation_currency = consolidation_currency
        self.accounting_standard = accounting_standard

        # Données du groupe
        self.entities: Dict[str, Entity] = {}
        self.participations: Dict[str, Participation] = {}
        self.exchange_rates: Dict[Tuple[str, str, date], ExchangeRate] = {}

    # ========================================================================
    # GESTION DE LA STRUCTURE DU GROUPE
    # ========================================================================

    def add_entity(self, entity: Entity) -> Entity:
        """Ajoute une entité au groupe."""
        self.entities[entity.id] = entity
        return entity

    def add_participation(self, participation: Participation) -> Participation:
        """Ajoute un lien de participation."""
        self.participations[participation.id] = participation

        # Mettre à jour l'entité filiale
        subsidiary = self.entities.get(participation.subsidiary_entity_id)
        if subsidiary:
            subsidiary.parent_id = participation.parent_entity_id
            subsidiary.ownership_percentage = participation.total_ownership
            subsidiary.consolidation_method = self._determine_method(
                participation.total_ownership,
                participation.voting_rights
            )

        return participation

    def _determine_method(
        self,
        ownership: Decimal,
        voting_rights: Decimal
    ) -> ConsolidationMethod:
        """Détermine la méthode de consolidation selon les participations."""
        # Contrôle effectif (plus de 50% ou contrôle de fait)
        if voting_rights > Decimal("50") or ownership > Decimal("50"):
            return ConsolidationMethod.FULL_INTEGRATION

        # Influence notable (20-50%)
        if ownership >= Decimal("20"):
            return ConsolidationMethod.EQUITY_METHOD

        # Participation simple
        return ConsolidationMethod.NOT_CONSOLIDATED

    def get_consolidation_perimeter(
        self,
        as_of_date: date
    ) -> List[Entity]:
        """Retourne les entités à consolider à une date donnée."""
        perimeter = []

        for entity in self.entities.values():
            if not entity.is_active:
                continue

            # Vérifier dates d'acquisition/cession
            if entity.acquisition_date and entity.acquisition_date > as_of_date:
                continue
            if entity.disposal_date and entity.disposal_date <= as_of_date:
                continue

            # Vérifier méthode de consolidation
            if entity.consolidation_method != ConsolidationMethod.NOT_CONSOLIDATED:
                perimeter.append(entity)
            elif entity.is_parent:
                perimeter.append(entity)

        return perimeter

    def calculate_indirect_ownership(self) -> Dict[str, Decimal]:
        """Calcule les pourcentages de détention indirecte."""
        result = {}

        # Trouver la société mère
        parent = next(
            (e for e in self.entities.values() if e.is_parent),
            None
        )
        if not parent:
            return result

        # Algorithme de propagation
        visited = set()
        stack = [(parent.id, Decimal("100"))]

        while stack:
            entity_id, cumulative_pct = stack.pop()
            if entity_id in visited:
                continue
            visited.add(entity_id)

            result[entity_id] = cumulative_pct

            # Trouver les participations directes
            for part in self.participations.values():
                if part.parent_entity_id == entity_id:
                    child_pct = cumulative_pct * part.direct_ownership / Decimal("100")
                    stack.append((part.subsidiary_entity_id, child_pct))

        return result

    # ========================================================================
    # COURS DE CHANGE
    # ========================================================================

    def set_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate_date: date,
        closing_rate: Decimal,
        average_rate: Decimal,
        historical_rate: Optional[Decimal] = None
    ):
        """Définit un cours de change."""
        rate = ExchangeRate(
            from_currency=from_currency,
            to_currency=to_currency,
            rate_date=rate_date,
            closing_rate=closing_rate,
            average_rate=average_rate,
            historical_rate=historical_rate
        )
        key = (from_currency, to_currency, rate_date)
        self.exchange_rates[key] = rate

    def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate_date: date
    ) -> Optional[ExchangeRate]:
        """Récupère un cours de change."""
        if from_currency == to_currency:
            return ExchangeRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate_date=rate_date,
                closing_rate=Decimal("1"),
                average_rate=Decimal("1"),
                historical_rate=Decimal("1")
            )

        key = (from_currency, to_currency, rate_date)
        return self.exchange_rates.get(key)

    # ========================================================================
    # CONVERSION MONETAIRE
    # ========================================================================

    def convert_trial_balance(
        self,
        balance: EntityTrialBalance,
        target_currency: str,
        exchange_rate: ExchangeRate
    ) -> Tuple[EntityTrialBalance, CurrencyTranslation]:
        """Convertit une balance dans la devise de consolidation."""
        if balance.currency == target_currency:
            return balance, None

        converted_entries = []
        assets_orig = Decimal("0")
        assets_conv = Decimal("0")
        liabilities_orig = Decimal("0")
        liabilities_conv = Decimal("0")
        equity_orig = Decimal("0")
        equity_conv = Decimal("0")
        income_orig = Decimal("0")
        income_conv = Decimal("0")

        for entry in balance.entries:
            # Déterminer le type de compte et le cours applicable
            account_class = entry.account_code[0] if entry.account_code else "0"

            if account_class in ["1"]:  # Capitaux propres
                rate = exchange_rate.historical_rate or exchange_rate.closing_rate
                equity_orig += entry.balance
            elif account_class in ["6", "7"]:  # Résultat
                rate = exchange_rate.average_rate
                income_orig += entry.balance
            elif account_class in ["2", "3", "4", "5"]:  # Actif/Passif
                rate = exchange_rate.closing_rate
                if account_class in ["2", "3", "5"] or entry.balance >= 0:
                    assets_orig += abs(entry.balance)
                else:
                    liabilities_orig += abs(entry.balance)
            else:
                rate = exchange_rate.closing_rate

            # Conversion
            converted_balance = (entry.balance * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            converted_debit = (entry.debit * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            converted_credit = (entry.credit * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Cumuls convertis
            if account_class in ["1"]:
                equity_conv += converted_balance
            elif account_class in ["6", "7"]:
                income_conv += converted_balance
            elif account_class in ["2", "3", "5"] or entry.balance >= 0:
                assets_conv += abs(converted_balance)
            else:
                liabilities_conv += abs(converted_balance)

            converted_entries.append(TrialBalanceEntry(
                account_code=entry.account_code,
                account_name=entry.account_name,
                debit=converted_debit,
                credit=converted_credit,
                balance=converted_balance,
                currency=target_currency
            ))

        # Calcul écart de conversion
        translation_diff = (
            assets_conv - liabilities_conv - equity_conv - income_conv
        )

        converted_balance = EntityTrialBalance(
            entity_id=balance.entity_id,
            period_start=balance.period_start,
            period_end=balance.period_end,
            entries=converted_entries,
            currency=target_currency,
            is_audited=balance.is_audited
        )

        translation = CurrencyTranslation(
            entity_id=balance.entity_id,
            source_currency=balance.currency,
            target_currency=target_currency,
            period_end=balance.period_end,
            closing_rate=exchange_rate.closing_rate,
            average_rate=exchange_rate.average_rate,
            assets_original=assets_orig,
            assets_converted=assets_conv,
            liabilities_original=liabilities_orig,
            liabilities_converted=liabilities_conv,
            equity_original=equity_orig,
            equity_converted=equity_conv,
            income_original=income_orig,
            income_converted=income_conv,
            translation_difference=translation_diff
        )

        return converted_balance, translation

    # ========================================================================
    # ÉLIMINATIONS INTRA-GROUPE
    # ========================================================================

    def generate_eliminations(
        self,
        packages: List[ConsolidationPackage],
        consolidation_id: str
    ) -> List[EliminationEntry]:
        """Génère toutes les écritures d'élimination."""
        eliminations = []

        # 1. Élimination des titres de participation et capitaux propres
        eliminations.extend(
            self._eliminate_investments(packages, consolidation_id)
        )

        # 2. Élimination des créances/dettes intra-groupe
        eliminations.extend(
            self._eliminate_intercompany_balances(packages, consolidation_id)
        )

        # 3. Élimination des ventes/achats intra-groupe
        eliminations.extend(
            self._eliminate_intercompany_sales(packages, consolidation_id)
        )

        # 4. Élimination des dividendes intra-groupe
        eliminations.extend(
            self._eliminate_dividends(packages, consolidation_id)
        )

        # 5. Élimination des marges sur stocks
        eliminations.extend(
            self._eliminate_internal_margins(packages, consolidation_id)
        )

        return eliminations

    def _eliminate_investments(
        self,
        packages: List[ConsolidationPackage],
        consolidation_id: str
    ) -> List[EliminationEntry]:
        """Élimine les titres de participation contre les capitaux propres."""
        eliminations = []

        for participation in self.participations.values():
            parent = self.entities.get(participation.parent_entity_id)
            subsidiary = self.entities.get(participation.subsidiary_entity_id)

            if not parent or not subsidiary:
                continue

            # Intégration globale uniquement
            if subsidiary.consolidation_method != ConsolidationMethod.FULL_INTEGRATION:
                continue

            # Trouver les capitaux propres de la filiale
            subsidiary_package = next(
                (p for p in packages if p.entity_id == subsidiary.id),
                None
            )
            if not subsidiary_package:
                continue

            # Calculer les capitaux propres
            equity = Decimal("0")
            for entry in subsidiary_package.trial_balance.entries:
                if entry.account_code.startswith("1"):
                    equity += entry.balance

            # Quote-part groupe
            group_share = equity * participation.total_ownership / Decimal("100")

            # Quote-part minoritaires
            minority_share = equity - group_share

            # Écart d'acquisition (goodwill)
            goodwill = participation.acquisition_cost - group_share

            entries = [
                # Annulation capital filiale
                {"account": "101_ELIM", "debit": equity, "credit": Decimal("0"),
                 "entity_id": subsidiary.id, "label": "Élimination capital filiale"},
                # Annulation titres chez parent
                {"account": "261_ELIM", "debit": Decimal("0"),
                 "credit": participation.acquisition_cost,
                 "entity_id": parent.id, "label": "Élimination titres participation"},
            ]

            # Goodwill positif
            if goodwill > 0:
                entries.append({
                    "account": "207_GOODWILL", "debit": goodwill, "credit": Decimal("0"),
                    "entity_id": "CONSO", "label": "Écart d'acquisition"
                })

            # Intérêts minoritaires
            if minority_share > 0:
                entries.append({
                    "account": "105_MINORITAIRES", "debit": Decimal("0"),
                    "credit": minority_share,
                    "entity_id": "CONSO", "label": "Intérêts minoritaires"
                })

            eliminations.append(EliminationEntry(
                id=str(uuid.uuid4()),
                consolidation_id=consolidation_id,
                elimination_type=EliminationType.INTERCOMPANY_PROVISIONS,
                description=f"Élimination titres {subsidiary.name}",
                entries=entries,
                is_automatic=True
            ))

        return eliminations

    def _eliminate_intercompany_balances(
        self,
        packages: List[ConsolidationPackage],
        consolidation_id: str
    ) -> List[EliminationEntry]:
        """Élimine les créances et dettes intra-groupe."""
        eliminations = []

        # Collecter toutes les transactions intra-groupe
        transactions_by_pair = {}
        for package in packages:
            for tx in package.intercompany_transactions:
                if tx.elimination_type == EliminationType.INTERCOMPANY_RECEIVABLES:
                    key = tuple(sorted([tx.entity1_id, tx.entity2_id]))
                    if key not in transactions_by_pair:
                        transactions_by_pair[key] = []
                    transactions_by_pair[key].append(tx)

        # Créer les éliminations
        for (entity1_id, entity2_id), transactions in transactions_by_pair.items():
            total_amount = sum(tx.amount_entity1 for tx in transactions)

            if total_amount == 0:
                continue

            entries = [
                {"account": "401_ELIM", "debit": total_amount, "credit": Decimal("0"),
                 "entity_id": entity2_id, "label": "Élimination dette intra-groupe"},
                {"account": "411_ELIM", "debit": Decimal("0"), "credit": total_amount,
                 "entity_id": entity1_id, "label": "Élimination créance intra-groupe"},
            ]

            eliminations.append(EliminationEntry(
                id=str(uuid.uuid4()),
                consolidation_id=consolidation_id,
                elimination_type=EliminationType.INTERCOMPANY_RECEIVABLES,
                description=f"Élimination créances/dettes {entity1_id} - {entity2_id}",
                entries=entries,
                is_automatic=True
            ))

        return eliminations

    def _eliminate_intercompany_sales(
        self,
        packages: List[ConsolidationPackage],
        consolidation_id: str
    ) -> List[EliminationEntry]:
        """Élimine les ventes et achats intra-groupe."""
        eliminations = []

        for package in packages:
            for tx in package.intercompany_transactions:
                if tx.elimination_type != EliminationType.INTERCOMPANY_SALES:
                    continue

                entries = [
                    {"account": "707_ELIM", "debit": tx.amount_entity1,
                     "credit": Decimal("0"),
                     "entity_id": tx.entity1_id, "label": "Élimination ventes IG"},
                    {"account": "607_ELIM", "debit": Decimal("0"),
                     "credit": tx.amount_entity2,
                     "entity_id": tx.entity2_id, "label": "Élimination achats IG"},
                ]

                eliminations.append(EliminationEntry(
                    id=str(uuid.uuid4()),
                    consolidation_id=consolidation_id,
                    elimination_type=EliminationType.INTERCOMPANY_SALES,
                    description=f"Élimination CA/achats {tx.entity1_id} - {tx.entity2_id}",
                    entries=entries,
                    source_transaction_id=tx.id,
                    is_automatic=True
                ))

        return eliminations

    def _eliminate_dividends(
        self,
        packages: List[ConsolidationPackage],
        consolidation_id: str
    ) -> List[EliminationEntry]:
        """Élimine les dividendes intra-groupe."""
        eliminations = []

        for package in packages:
            if package.dividend_paid_to_parent == 0:
                continue

            entity = self.entities.get(package.entity_id)
            if not entity or not entity.parent_id:
                continue

            entries = [
                # Annulation produit chez le parent
                {"account": "761_ELIM", "debit": package.dividend_paid_to_parent,
                 "credit": Decimal("0"),
                 "entity_id": entity.parent_id,
                 "label": "Élimination dividendes reçus"},
                # Reconstitution des réserves filiale
                {"account": "110_ELIM", "debit": Decimal("0"),
                 "credit": package.dividend_paid_to_parent,
                 "entity_id": package.entity_id,
                 "label": "Reconstitution réserves"},
            ]

            eliminations.append(EliminationEntry(
                id=str(uuid.uuid4()),
                consolidation_id=consolidation_id,
                elimination_type=EliminationType.INTERCOMPANY_DIVIDENDS,
                description=f"Élimination dividendes {entity.name}",
                entries=entries,
                is_automatic=True
            ))

        return eliminations

    def _eliminate_internal_margins(
        self,
        packages: List[ConsolidationPackage],
        consolidation_id: str
    ) -> List[EliminationEntry]:
        """Élimine les marges internes sur stocks."""
        eliminations = []

        for package in packages:
            for tx in package.intercompany_transactions:
                if tx.elimination_type != EliminationType.INTERNAL_MARGIN:
                    continue

                # La marge est la différence entre prix de vente IG et coût
                margin = tx.amount_entity1 - tx.amount_entity2

                if margin <= 0:
                    continue

                entries = [
                    # Diminution du stock
                    {"account": "37_ELIM", "debit": Decimal("0"), "credit": margin,
                     "entity_id": tx.entity2_id, "label": "Élimination marge stock"},
                    # Impact résultat
                    {"account": "603_ELIM", "debit": margin, "credit": Decimal("0"),
                     "entity_id": "CONSO", "label": "Variation stocks marge IG"},
                ]

                eliminations.append(EliminationEntry(
                    id=str(uuid.uuid4()),
                    consolidation_id=consolidation_id,
                    elimination_type=EliminationType.INTERNAL_MARGIN,
                    description=f"Élimination marge stocks {tx.entity1_id} -> {tx.entity2_id}",
                    entries=entries,
                    source_transaction_id=tx.id,
                    is_automatic=True
                ))

        return eliminations

    # ========================================================================
    # CALCUL DES MINORITAIRES
    # ========================================================================

    def calculate_minority_interests(
        self,
        packages: List[ConsolidationPackage]
    ) -> List[MinorityInterest]:
        """Calcule les intérêts minoritaires."""
        interests = []

        for package in packages:
            entity = self.entities.get(package.entity_id)
            if not entity:
                continue

            # Seulement pour les filiales non détenues à 100%
            if entity.ownership_percentage >= Decimal("100"):
                continue

            minority_pct = Decimal("100") - entity.ownership_percentage

            # Calculer les capitaux propres et le résultat
            equity = Decimal("0")
            net_income = Decimal("0")

            for entry in package.trial_balance.entries:
                if entry.account_code.startswith("1"):
                    equity += entry.balance
                elif entry.account_code.startswith("12"):
                    net_income = entry.balance

            interests.append(MinorityInterest(
                entity_id=entity.id,
                period_end=package.period_end,
                total_equity=equity,
                minority_percentage=minority_pct,
                minority_share=equity * minority_pct / Decimal("100"),
                net_income=net_income,
                minority_income=net_income * minority_pct / Decimal("100")
            ))

        return interests

    # ========================================================================
    # CONSOLIDATION PRINCIPALE
    # ========================================================================

    def consolidate(
        self,
        period_start: date,
        period_end: date,
        packages: List[ConsolidationPackage]
    ) -> ConsolidationResult:
        """
        Effectue la consolidation complète.

        Args:
            period_start: Début de période
            period_end: Fin de période
            packages: Paquets de consolidation des entités

        Returns:
            Résultat de la consolidation
        """
        consolidation_id = str(uuid.uuid4())

        # 1. Déterminer le périmètre
        perimeter = self.get_consolidation_perimeter(period_end)
        entity_ids = {e.id for e in perimeter}

        # Filtrer les packages
        valid_packages = [
            p for p in packages
            if p.entity_id in entity_ids
        ]

        # 2. Conversion des devises
        converted_balances = {}
        currency_translations = {}

        for package in valid_packages:
            entity = self.entities.get(package.entity_id)
            if not entity:
                continue

            if entity.currency == self.consolidation_currency:
                converted_balances[entity.id] = package.trial_balance
            else:
                rate = self.get_exchange_rate(
                    entity.currency,
                    self.consolidation_currency,
                    period_end
                )
                if rate:
                    converted, translation = self.convert_trial_balance(
                        package.trial_balance,
                        self.consolidation_currency,
                        rate
                    )
                    converted_balances[entity.id] = converted
                    if translation:
                        currency_translations[entity.id] = translation

        # 3. Génération des éliminations
        eliminations = self.generate_eliminations(valid_packages, consolidation_id)

        # 4. Calcul des minoritaires
        minority_interests = self.calculate_minority_interests(valid_packages)

        # 5. Calcul des goodwills
        goodwill_calculations = self._calculate_goodwills(valid_packages, period_end)

        # 6. Agrégation de la balance consolidée
        consolidated_balance = self._aggregate_balances(
            converted_balances,
            eliminations
        )

        # 7. Calcul de l'écart de conversion total
        total_translation_diff = sum(
            t.translation_difference for t in currency_translations.values()
        )

        return ConsolidationResult(
            id=consolidation_id,
            tenant_id=self.tenant_id,
            period_start=period_start,
            period_end=period_end,
            consolidation_currency=self.consolidation_currency,
            accounting_standard=self.accounting_standard,
            entities=perimeter,
            participations=list(self.participations.values()),
            entity_balances=converted_balances,
            currency_translations=currency_translations,
            elimination_entries=eliminations,
            consolidated_trial_balance=consolidated_balance,
            minority_interests=minority_interests,
            goodwill_calculations=goodwill_calculations,
            total_translation_difference=total_translation_diff
        )

    def _calculate_goodwills(
        self,
        packages: List[ConsolidationPackage],
        period_end: date
    ) -> List[GoodwillCalculation]:
        """Calcule les écarts d'acquisition."""
        calculations = []

        for participation in self.participations.values():
            subsidiary = self.entities.get(participation.subsidiary_entity_id)
            if not subsidiary:
                continue

            if subsidiary.consolidation_method != ConsolidationMethod.FULL_INTEGRATION:
                continue

            # Trouver le package de la filiale
            package = next(
                (p for p in packages if p.entity_id == subsidiary.id),
                None
            )
            if not package:
                continue

            # Calculer l'actif net
            assets = Decimal("0")
            liabilities = Decimal("0")

            for entry in package.trial_balance.entries:
                account_class = entry.account_code[0] if entry.account_code else "0"
                if account_class in ["2", "3", "4", "5"]:
                    if entry.balance >= 0:
                        assets += entry.balance
                    else:
                        liabilities += abs(entry.balance)
                elif account_class == "1":
                    # Capitaux propres
                    pass

            net_assets = assets - liabilities
            group_share = net_assets * participation.total_ownership / Decimal("100")
            goodwill = participation.acquisition_cost - group_share

            calculations.append(GoodwillCalculation(
                participation_id=participation.id,
                calculation_date=period_end,
                acquisition_cost=participation.acquisition_cost,
                net_assets_fair_value=net_assets,
                ownership_percentage=participation.total_ownership,
                group_share_net_assets=group_share,
                goodwill=goodwill,
                assets_fair_value=assets,
                liabilities_fair_value=liabilities
            ))

        return calculations

    def _aggregate_balances(
        self,
        converted_balances: Dict[str, EntityTrialBalance],
        eliminations: List[EliminationEntry]
    ) -> List[TrialBalanceEntry]:
        """Agrège les balances avec les éliminations."""
        # Accumulateur par compte
        accounts: Dict[str, Dict[str, Decimal]] = {}

        # Ajouter les balances des entités
        for entity_id, balance in converted_balances.items():
            for entry in balance.entries:
                if entry.account_code not in accounts:
                    accounts[entry.account_code] = {
                        "name": entry.account_name,
                        "debit": Decimal("0"),
                        "credit": Decimal("0")
                    }
                accounts[entry.account_code]["debit"] += entry.debit
                accounts[entry.account_code]["credit"] += entry.credit

        # Appliquer les éliminations
        for elim in eliminations:
            for entry in elim.entries:
                account_code = entry.get("account", "")
                if account_code not in accounts:
                    accounts[account_code] = {
                        "name": entry.get("label", ""),
                        "debit": Decimal("0"),
                        "credit": Decimal("0")
                    }
                accounts[account_code]["debit"] += Decimal(str(entry.get("debit", 0)))
                accounts[account_code]["credit"] += Decimal(str(entry.get("credit", 0)))

        # Construire le résultat
        result = []
        for code, data in sorted(accounts.items()):
            balance = data["debit"] - data["credit"]
            result.append(TrialBalanceEntry(
                account_code=code,
                account_name=data["name"],
                debit=data["debit"],
                credit=data["credit"],
                balance=balance,
                currency=self.consolidation_currency
            ))

        return result


# ============================================================================
# FACTORY
# ============================================================================

def create_consolidation_service(
    tenant_id: str,
    consolidation_currency: str = "EUR",
    accounting_standard: AccountingStandard = AccountingStandard.FRENCH_GAAP
) -> ConsolidationService:
    """Crée un service de consolidation configuré."""
    return ConsolidationService(
        tenant_id=tenant_id,
        consolidation_currency=consolidation_currency,
        accounting_standard=accounting_standard
    )
