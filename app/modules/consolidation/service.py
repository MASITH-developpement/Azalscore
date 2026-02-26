"""
AZALS MODULE - CONSOLIDATION: Service
=======================================

Service metier principal pour le module de consolidation
comptable multi-entites.

Fonctionnalites:
- Gestion du perimetre de consolidation
- Collecte des paquets de consolidation
- Eliminations intra-groupe automatiques
- Conversion des devises
- Calcul des interets minoritaires
- Calcul des ecarts d'acquisition (goodwill)
- Generation des etats consolides
- Reconciliation inter-societes
- Retraitements de consolidation

Normes supportees:
- Reglement ANC 2020-01 (France)
- IFRS 10, 11, 12 (international)
- US GAAP ASC 810 (Etats-Unis)

REGLES CRITIQUES:
- tenant_id obligatoire
- Isolation multi-tenant stricte

Auteur: AZALSCORE Team
Version: 2.0.0
"""
from __future__ import annotations


from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
import uuid

from sqlalchemy.orm import Session

from .models import (
    AccountingStandard,
    ConsolidationMethod,
    ConsolidationStatus,
    ControlType,
    CurrencyConversionMethod,
    EliminationType,
    PackageStatus,
    ReportType,
    RestatementType,
    ConsolidationPerimeter,
    ConsolidationEntity,
    Participation,
    ExchangeRate,
    Consolidation,
    ConsolidationPackage,
    EliminationEntry,
    Restatement,
    IntercompanyReconciliation,
    GoodwillCalculation,
    MinorityInterest,
    ConsolidatedReport,
)
from .repository import (
    ConsolidationPerimeterRepository,
    ConsolidationEntityRepository,
    ParticipationRepository,
    ExchangeRateRepository,
    ConsolidationRepository,
    ConsolidationPackageRepository,
    EliminationRepository,
    IntercompanyReconciliationRepository,
    ConsolidatedReportRepository,
    ConsolidationAuditLogRepository,
)
from .schemas import (
    ConsolidationPerimeterCreate,
    ConsolidationPerimeterUpdate,
    ConsolidationEntityCreate,
    ConsolidationEntityUpdate,
    ConsolidationCreate,
    ConsolidationUpdate,
    ConsolidationPackageCreate,
    ConsolidationPackageUpdate,
    EliminationEntryCreate,
    RestatementCreate,
    GenerateReportRequest,
    ConsolidationFilters,
    EntityFilters,
    PackageFilters,
    ReconciliationFilters,
    TrialBalanceEntry,
)
from .exceptions import (
    PerimeterNotFoundError,
    PerimeterDuplicateError,
    EntityNotFoundError,
    EntityDuplicateError,
    EntityCircularReferenceError,
    ParentEntityRequiredError,
    ConsolidationNotFoundError,
    ConsolidationDuplicateError,
    ConsolidationStatusError,
    ConsolidationIncompleteError,
    PackageNotFoundError,
    PackageDuplicateError,
    PackageStatusError,
    ExchangeRateNotFoundError,
    MissingExchangeRatesError,
    EliminationImbalanceError,
    ReconciliationMismatchError,
)


# ============================================================================
# MAPPING COMPTES PCG -> POSTES CONSOLIDES
# ============================================================================

ACCOUNT_MAPPING_PCG = {
    # Actif immobilise
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
    "74": "subventions_exploitation",
    "75": "autres_produits_gestion",
    "76": "produits_financiers",
    "77": "produits_exceptionnels",
    "78": "reprises_provisions",
}


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class ConsolidationService:
    """
    Service principal de consolidation comptable.

    Gere l'ensemble du processus de consolidation multi-entites:
    - Structure du groupe et perimetre
    - Collecte des paquets de consolidation
    - Eliminations intra-groupe
    - Conversion des devises
    - Calcul des minoritaires et goodwill
    - Production des etats consolides
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        user_id: str = None
    ):
        """
        Initialise le service de consolidation.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant (isolation multi-tenant)
            user_id: ID de l'utilisateur (pour audit trail)
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

        # Repositories
        self.perimeter_repo = ConsolidationPerimeterRepository(db, tenant_id)
        self.entity_repo = ConsolidationEntityRepository(db, tenant_id)
        self.participation_repo = ParticipationRepository(db, tenant_id)
        self.exchange_rate_repo = ExchangeRateRepository(db, tenant_id)
        self.consolidation_repo = ConsolidationRepository(db, tenant_id)
        self.package_repo = ConsolidationPackageRepository(db, tenant_id)
        self.elimination_repo = EliminationRepository(db, tenant_id)
        self.reconciliation_repo = IntercompanyReconciliationRepository(db, tenant_id)
        self.report_repo = ConsolidatedReportRepository(db, tenant_id)
        self.audit_repo = ConsolidationAuditLogRepository(db, tenant_id)

    # ========================================================================
    # PERIMETRE DE CONSOLIDATION
    # ========================================================================

    def create_perimeter(
        self,
        data: ConsolidationPerimeterCreate,
        created_by: UUID = None
    ) -> ConsolidationPerimeter:
        """Creer un nouveau perimetre de consolidation."""
        # Verifier unicite
        if self.perimeter_repo.code_exists(data.code, data.fiscal_year):
            raise PerimeterDuplicateError(data.code, data.fiscal_year)

        perimeter = self.perimeter_repo.create(
            data.model_dump(),
            created_by=created_by or (UUID(self.user_id) if self.user_id else None)
        )

        # Audit
        self._log_action(
            "create_perimeter",
            target_type="ConsolidationPerimeter",
            target_id=perimeter.id,
            new_values=data.model_dump()
        )

        return perimeter

    def get_perimeter(self, perimeter_id: UUID) -> ConsolidationPerimeter:
        """Recuperer un perimetre par ID."""
        perimeter = self.perimeter_repo.get_by_id(perimeter_id)
        if not perimeter:
            raise PerimeterNotFoundError(str(perimeter_id))
        return perimeter

    def update_perimeter(
        self,
        perimeter_id: UUID,
        data: ConsolidationPerimeterUpdate,
        updated_by: UUID = None
    ) -> ConsolidationPerimeter:
        """Mettre a jour un perimetre."""
        perimeter = self.get_perimeter(perimeter_id)

        old_values = {"name": perimeter.name, "status": perimeter.status.value}

        perimeter = self.perimeter_repo.update(
            perimeter,
            data.model_dump(exclude_unset=True),
            updated_by=updated_by or (UUID(self.user_id) if self.user_id else None)
        )

        self._log_action(
            "update_perimeter",
            target_type="ConsolidationPerimeter",
            target_id=perimeter.id,
            old_values=old_values,
            new_values=data.model_dump(exclude_unset=True)
        )

        return perimeter

    def list_perimeters(
        self,
        fiscal_year: int = None,
        status: List[ConsolidationStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ConsolidationPerimeter], int]:
        """Lister les perimetres de consolidation."""
        return self.perimeter_repo.list(
            fiscal_year=fiscal_year,
            status=status,
            page=page,
            page_size=page_size
        )

    def delete_perimeter(self, perimeter_id: UUID, deleted_by: UUID = None) -> bool:
        """Supprimer un perimetre (soft delete)."""
        perimeter = self.get_perimeter(perimeter_id)
        return self.perimeter_repo.soft_delete(
            perimeter,
            deleted_by=deleted_by or (UUID(self.user_id) if self.user_id else None)
        )

    # ========================================================================
    # ENTITES DU GROUPE
    # ========================================================================

    def create_entity(
        self,
        data: ConsolidationEntityCreate,
        created_by: UUID = None
    ) -> ConsolidationEntity:
        """Creer une nouvelle entite dans le perimetre."""
        # Verifier que le perimetre existe
        perimeter = self.get_perimeter(data.perimeter_id)

        # Verifier unicite du code
        if self.entity_repo.code_exists(data.code, data.perimeter_id):
            raise EntityDuplicateError(data.code, str(data.perimeter_id))

        # Verifier parent si specifie
        if data.parent_entity_id:
            parent = self.entity_repo.get_by_id(data.parent_entity_id)
            if not parent:
                raise EntityNotFoundError(str(data.parent_entity_id))
            if parent.perimeter_id != data.perimeter_id:
                raise EntityCircularReferenceError(data.code, str(data.parent_entity_id))

        entity = self.entity_repo.create(
            data.model_dump(),
            created_by=created_by or (UUID(self.user_id) if self.user_id else None)
        )

        self._log_action(
            "create_entity",
            target_type="ConsolidationEntity",
            target_id=entity.id,
            entity_id=entity.id,
            new_values=data.model_dump()
        )

        return entity

    def get_entity(self, entity_id: UUID) -> ConsolidationEntity:
        """Recuperer une entite par ID."""
        entity = self.entity_repo.get_by_id(entity_id)
        if not entity:
            raise EntityNotFoundError(str(entity_id))
        return entity

    def update_entity(
        self,
        entity_id: UUID,
        data: ConsolidationEntityUpdate,
        updated_by: UUID = None
    ) -> ConsolidationEntity:
        """Mettre a jour une entite."""
        entity = self.get_entity(entity_id)

        # Verifier reference circulaire si parent change
        if data.parent_entity_id:
            if str(data.parent_entity_id) == str(entity_id):
                raise EntityCircularReferenceError(entity.code, str(data.parent_entity_id))

        return self.entity_repo.update(
            entity,
            data.model_dump(exclude_unset=True),
            updated_by=updated_by or (UUID(self.user_id) if self.user_id else None)
        )

    def list_entities(
        self,
        filters: EntityFilters = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ConsolidationEntity], int]:
        """Lister les entites."""
        return self.entity_repo.list(filters=filters, page=page, page_size=page_size)

    def get_entities_by_perimeter(
        self,
        perimeter_id: UUID,
        include_inactive: bool = False
    ) -> List[ConsolidationEntity]:
        """Recuperer les entites d'un perimetre."""
        return self.entity_repo.get_by_perimeter(perimeter_id, include_inactive)

    def get_consolidation_scope(
        self,
        perimeter_id: UUID,
        as_of_date: date
    ) -> List[ConsolidationEntity]:
        """Obtenir le perimetre de consolidation effectif a une date."""
        return self.entity_repo.get_entities_to_consolidate(perimeter_id, as_of_date)

    def calculate_indirect_ownership(
        self,
        perimeter_id: UUID
    ) -> Dict[str, Decimal]:
        """Calculer les pourcentages de detention indirecte."""
        entities = self.entity_repo.get_by_perimeter(perimeter_id)
        parent = self.entity_repo.get_parent_entity(perimeter_id)

        if not parent:
            raise ParentEntityRequiredError(str(perimeter_id))

        result = {}
        visited = set()
        stack = [(parent.id, Decimal("100.000"))]

        while stack:
            entity_id, cumulative_pct = stack.pop()
            if entity_id in visited:
                continue
            visited.add(entity_id)
            result[str(entity_id)] = cumulative_pct

            # Trouver les participations directes
            participations = self.participation_repo.get_by_parent(entity_id)
            for part in participations:
                child_pct = cumulative_pct * part.direct_ownership / Decimal("100")
                stack.append((part.subsidiary_id, child_pct))

        return result

    def determine_consolidation_method(
        self,
        ownership_pct: Decimal,
        voting_rights_pct: Decimal,
        control_type: ControlType = None
    ) -> ConsolidationMethod:
        """Determiner la methode de consolidation selon les participations."""
        # Controle conjoint explicite
        if control_type == ControlType.JOINT:
            return ConsolidationMethod.PROPORTIONAL

        # Controle exclusif (plus de 50% ou controle de fait)
        if voting_rights_pct > Decimal("50") or ownership_pct > Decimal("50"):
            return ConsolidationMethod.FULL_INTEGRATION

        # Influence notable (20-50%)
        if ownership_pct >= Decimal("20"):
            return ConsolidationMethod.EQUITY_METHOD

        return ConsolidationMethod.NOT_CONSOLIDATED

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
        historical_rate: Decimal = None,
        source: str = None
    ) -> ExchangeRate:
        """Definir ou mettre a jour un cours de change."""
        return self.exchange_rate_repo.create({
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate_date": rate_date,
            "closing_rate": closing_rate,
            "average_rate": average_rate,
            "historical_rate": historical_rate,
            "source": source
        })

    def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate_date: date
    ) -> ExchangeRate:
        """Recuperer un cours de change."""
        rate = self.exchange_rate_repo.get_rate(from_currency, to_currency, rate_date)
        if not rate:
            raise ExchangeRateNotFoundError(from_currency, to_currency, str(rate_date))
        return rate

    def check_required_exchange_rates(
        self,
        perimeter_id: UUID,
        rate_date: date,
        target_currency: str
    ) -> List[str]:
        """Verifier la disponibilite des cours de change requis."""
        entities = self.entity_repo.get_by_perimeter(perimeter_id)
        currencies = set(e.currency for e in entities if e.currency != target_currency)

        missing = []
        for currency in currencies:
            rate = self.exchange_rate_repo.get_rate(currency, target_currency, rate_date)
            if not rate:
                missing.append(f"{currency}/{target_currency}")

        return missing

    # ========================================================================
    # CONSOLIDATION
    # ========================================================================

    def create_consolidation(
        self,
        data: ConsolidationCreate,
        created_by: UUID = None
    ) -> Consolidation:
        """Creer une nouvelle consolidation."""
        # Verifier que le perimetre existe
        perimeter = self.get_perimeter(data.perimeter_id)

        # Verifier unicite du code
        if self.consolidation_repo.code_exists(data.code):
            raise ConsolidationDuplicateError(data.code)

        consolidation = self.consolidation_repo.create(
            data.model_dump(),
            created_by=created_by or (UUID(self.user_id) if self.user_id else None)
        )

        self._log_action(
            "create_consolidation",
            consolidation_id=consolidation.id,
            target_type="Consolidation",
            target_id=consolidation.id,
            new_values=data.model_dump()
        )

        return consolidation

    def get_consolidation(self, consolidation_id: UUID) -> Consolidation:
        """Recuperer une consolidation par ID."""
        consolidation = self.consolidation_repo.get_by_id(consolidation_id)
        if not consolidation:
            raise ConsolidationNotFoundError(str(consolidation_id))
        return consolidation

    def update_consolidation(
        self,
        consolidation_id: UUID,
        data: ConsolidationUpdate,
        updated_by: UUID = None
    ) -> Consolidation:
        """Mettre a jour une consolidation."""
        consolidation = self.get_consolidation(consolidation_id)

        # Verifier le statut permet la modification
        if consolidation.status in [ConsolidationStatus.PUBLISHED, ConsolidationStatus.ARCHIVED]:
            raise ConsolidationStatusError(
                consolidation.status.value,
                action="update"
            )

        return self.consolidation_repo.update(
            consolidation,
            data.model_dump(exclude_unset=True),
            updated_by=updated_by or (UUID(self.user_id) if self.user_id else None)
        )

    def list_consolidations(
        self,
        filters: ConsolidationFilters = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Consolidation], int]:
        """Lister les consolidations."""
        return self.consolidation_repo.list(filters=filters, page=page, page_size=page_size)

    def submit_consolidation(
        self,
        consolidation_id: UUID,
        submitted_by: UUID = None
    ) -> Consolidation:
        """Soumettre une consolidation pour revue."""
        consolidation = self.get_consolidation(consolidation_id)

        if consolidation.status != ConsolidationStatus.DRAFT:
            raise ConsolidationStatusError(
                consolidation.status.value,
                ConsolidationStatus.DRAFT.value,
                "submit"
            )

        # Verifier que tous les paquets sont valides
        packages = self.package_repo.get_by_consolidation(consolidation_id)
        pending = [p for p in packages if p.status != PackageStatus.VALIDATED]
        if pending:
            raise ConsolidationIncompleteError(
                f"{len(pending)} paquets non valides",
                [str(p.entity_id) for p in pending]
            )

        return self.consolidation_repo.change_status(
            consolidation,
            ConsolidationStatus.PENDING_REVIEW,
            submitted_by or (UUID(self.user_id) if self.user_id else None)
        )

    def validate_consolidation(
        self,
        consolidation_id: UUID,
        validated_by: UUID = None
    ) -> Consolidation:
        """Valider une consolidation."""
        consolidation = self.get_consolidation(consolidation_id)

        if consolidation.status != ConsolidationStatus.PENDING_REVIEW:
            raise ConsolidationStatusError(
                consolidation.status.value,
                ConsolidationStatus.PENDING_REVIEW.value,
                "validate"
            )

        return self.consolidation_repo.change_status(
            consolidation,
            ConsolidationStatus.VALIDATED,
            validated_by or (UUID(self.user_id) if self.user_id else None)
        )

    def publish_consolidation(
        self,
        consolidation_id: UUID,
        published_by: UUID = None
    ) -> Consolidation:
        """Publier une consolidation."""
        consolidation = self.get_consolidation(consolidation_id)

        if consolidation.status != ConsolidationStatus.VALIDATED:
            raise ConsolidationStatusError(
                consolidation.status.value,
                ConsolidationStatus.VALIDATED.value,
                "publish"
            )

        return self.consolidation_repo.change_status(
            consolidation,
            ConsolidationStatus.PUBLISHED,
            published_by or (UUID(self.user_id) if self.user_id else None)
        )

    # ========================================================================
    # PAQUETS DE CONSOLIDATION
    # ========================================================================

    def create_package(
        self,
        data: ConsolidationPackageCreate,
        created_by: UUID = None
    ) -> ConsolidationPackage:
        """Creer un paquet de consolidation pour une entite."""
        # Verifier que la consolidation et l'entite existent
        consolidation = self.get_consolidation(data.consolidation_id)
        entity = self.get_entity(data.entity_id)

        # Verifier qu'un paquet n'existe pas deja
        if self.package_repo.exists(data.consolidation_id, data.entity_id):
            raise PackageDuplicateError(str(data.consolidation_id), str(data.entity_id))

        # Ajouter la devise de reporting
        package_data = data.model_dump()
        package_data["reporting_currency"] = consolidation.consolidation_currency

        # Recuperer les cours de change si devise differente
        if entity.currency != consolidation.consolidation_currency:
            rate = self.exchange_rate_repo.get_rate(
                entity.currency,
                consolidation.consolidation_currency,
                consolidation.period_end
            )
            if rate:
                package_data["closing_rate"] = rate.closing_rate
                package_data["average_rate"] = rate.average_rate

        return self.package_repo.create(
            package_data,
            created_by=created_by or (UUID(self.user_id) if self.user_id else None)
        )

    def get_package(self, package_id: UUID) -> ConsolidationPackage:
        """Recuperer un paquet par ID."""
        package = self.package_repo.get_by_id(package_id)
        if not package:
            raise PackageNotFoundError(str(package_id))
        return package

    def update_package(
        self,
        package_id: UUID,
        data: ConsolidationPackageUpdate,
        updated_by: UUID = None
    ) -> ConsolidationPackage:
        """Mettre a jour un paquet."""
        package = self.get_package(package_id)

        if package.status in [PackageStatus.VALIDATED]:
            raise PackageStatusError(package.status.value, "update")

        return self.package_repo.update(
            package,
            data.model_dump(exclude_unset=True),
            updated_by=updated_by or (UUID(self.user_id) if self.user_id else None)
        )

    def submit_package(
        self,
        package_id: UUID,
        submitted_by: UUID = None
    ) -> ConsolidationPackage:
        """Soumettre un paquet pour validation."""
        package = self.get_package(package_id)

        if package.status not in [PackageStatus.NOT_STARTED, PackageStatus.IN_PROGRESS, PackageStatus.REJECTED]:
            raise PackageStatusError(package.status.value, "submit")

        return self.package_repo.submit(
            package,
            submitted_by or (UUID(self.user_id) if self.user_id else None)
        )

    def validate_package(
        self,
        package_id: UUID,
        validated_by: UUID = None
    ) -> ConsolidationPackage:
        """Valider un paquet."""
        package = self.get_package(package_id)

        if package.status != PackageStatus.SUBMITTED:
            raise PackageStatusError(package.status.value, "validate")

        # Convertir les montants si necessaire
        package = self._convert_package_amounts(package)

        return self.package_repo.validate(
            package,
            validated_by or (UUID(self.user_id) if self.user_id else None)
        )

    def reject_package(
        self,
        package_id: UUID,
        reason: str,
        rejected_by: UUID = None
    ) -> ConsolidationPackage:
        """Rejeter un paquet."""
        package = self.get_package(package_id)

        if package.status != PackageStatus.SUBMITTED:
            raise PackageStatusError(package.status.value, "reject")

        return self.package_repo.reject(
            package,
            rejected_by or (UUID(self.user_id) if self.user_id else None),
            reason
        )

    def _convert_package_amounts(
        self,
        package: ConsolidationPackage
    ) -> ConsolidationPackage:
        """Convertir les montants d'un paquet en devise de consolidation."""
        if package.local_currency == package.reporting_currency:
            package.total_assets_converted = package.total_assets_local
            package.total_liabilities_converted = package.total_liabilities_local
            package.total_equity_converted = package.total_equity_local
            package.net_income_converted = package.net_income_local
            package.translation_difference = Decimal("0.00")
            return package

        if not package.closing_rate or not package.average_rate:
            raise ExchangeRateNotFoundError(
                package.local_currency,
                package.reporting_currency,
                "periode"
            )

        # Conversion bilan au cours de cloture
        package.total_assets_converted = (
            package.total_assets_local * package.closing_rate
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        package.total_liabilities_converted = (
            package.total_liabilities_local * package.closing_rate
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Conversion resultat au cours moyen
        package.net_income_converted = (
            package.net_income_local * package.average_rate
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Conversion capitaux propres (simplifiee - cours historique)
        package.total_equity_converted = (
            package.total_equity_local * package.closing_rate
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Ecart de conversion
        package.translation_difference = (
            package.total_assets_converted -
            package.total_liabilities_converted -
            package.total_equity_converted
        )

        self.db.commit()
        self.db.refresh(package)
        return package

    # ========================================================================
    # ELIMINATIONS INTRA-GROUPE
    # ========================================================================

    def generate_eliminations(
        self,
        consolidation_id: UUID,
        elimination_types: List[EliminationType] = None
    ) -> List[EliminationEntry]:
        """Generer les ecritures d'elimination automatiques."""
        consolidation = self.get_consolidation(consolidation_id)
        packages = self.package_repo.get_by_consolidation(
            consolidation_id,
            status=[PackageStatus.VALIDATED]
        )

        eliminations = []

        # Types a traiter
        types_to_process = elimination_types or [
            EliminationType.CAPITAL_ELIMINATION,
            EliminationType.INTERCOMPANY_RECEIVABLES,
            EliminationType.INTERCOMPANY_SALES,
            EliminationType.INTERCOMPANY_DIVIDENDS,
            EliminationType.INTERNAL_MARGIN,
        ]

        # 1. Eliminations titres/capitaux propres
        if EliminationType.CAPITAL_ELIMINATION in types_to_process:
            eliminations.extend(
                self._generate_capital_eliminations(consolidation, packages)
            )

        # 2. Eliminations creances/dettes
        if EliminationType.INTERCOMPANY_RECEIVABLES in types_to_process:
            eliminations.extend(
                self._generate_intercompany_balance_eliminations(consolidation, packages)
            )

        # 3. Eliminations ventes/achats
        if EliminationType.INTERCOMPANY_SALES in types_to_process:
            eliminations.extend(
                self._generate_intercompany_sales_eliminations(consolidation, packages)
            )

        # 4. Eliminations dividendes
        if EliminationType.INTERCOMPANY_DIVIDENDS in types_to_process:
            eliminations.extend(
                self._generate_dividend_eliminations(consolidation, packages)
            )

        # 5. Eliminations marges internes
        if EliminationType.INTERNAL_MARGIN in types_to_process:
            eliminations.extend(
                self._generate_margin_eliminations(consolidation, packages)
            )

        return eliminations

    def _generate_capital_eliminations(
        self,
        consolidation: Consolidation,
        packages: List[ConsolidationPackage]
    ) -> List[EliminationEntry]:
        """Generer les eliminations titres vs capitaux propres."""
        eliminations = []
        perimeter_id = consolidation.perimeter_id
        entities = {str(e.id): e for e in self.entity_repo.get_by_perimeter(perimeter_id)}
        participations = self.participation_repo._base_query().all()

        for part in participations:
            parent = entities.get(str(part.parent_id))
            subsidiary = entities.get(str(part.subsidiary_id))

            if not parent or not subsidiary:
                continue

            if subsidiary.consolidation_method != ConsolidationMethod.FULL_INTEGRATION:
                continue

            # Trouver le paquet de la filiale
            sub_package = next(
                (p for p in packages if str(p.entity_id) == str(subsidiary.id)),
                None
            )
            if not sub_package:
                continue

            # Calculer les capitaux propres de la filiale
            equity = sub_package.total_equity_converted

            # Quote-part groupe
            group_share = (equity * part.total_ownership / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Quote-part minoritaires
            minority_share = equity - group_share

            # Goodwill
            goodwill = part.acquisition_cost - group_share

            journal_entries = [
                {
                    "account": "101_ELIM",
                    "debit": float(equity),
                    "credit": 0,
                    "label": f"Elimination capital {subsidiary.name}",
                    "entity_id": str(subsidiary.id)
                },
                {
                    "account": "261_ELIM",
                    "debit": 0,
                    "credit": float(part.acquisition_cost),
                    "label": f"Elimination titres {subsidiary.name}",
                    "entity_id": str(parent.id)
                }
            ]

            if goodwill > 0:
                journal_entries.append({
                    "account": "207_GOODWILL",
                    "debit": float(goodwill),
                    "credit": 0,
                    "label": "Ecart d'acquisition",
                    "entity_id": "CONSO"
                })

            if minority_share > 0:
                journal_entries.append({
                    "account": "105_MINORITAIRES",
                    "debit": 0,
                    "credit": float(minority_share),
                    "label": "Interets minoritaires",
                    "entity_id": "CONSO"
                })

            elim = self.elimination_repo.create({
                "consolidation_id": consolidation.id,
                "elimination_type": EliminationType.CAPITAL_ELIMINATION,
                "description": f"Elimination titres/capitaux {subsidiary.name}",
                "amount": equity,
                "currency": consolidation.consolidation_currency,
                "entity1_id": parent.id,
                "entity2_id": subsidiary.id,
                "journal_entries": journal_entries,
                "is_automatic": True
            })
            eliminations.append(elim)

        return eliminations

    def _generate_intercompany_balance_eliminations(
        self,
        consolidation: Consolidation,
        packages: List[ConsolidationPackage]
    ) -> List[EliminationEntry]:
        """Generer les eliminations creances/dettes intercompany."""
        eliminations = []

        # Collecter les soldes intercompany
        interco_balances = {}
        for package in packages:
            for detail in (package.intercompany_details or []):
                key = tuple(sorted([str(package.entity_id), str(detail.get("counterparty_entity_id"))]))
                if key not in interco_balances:
                    interco_balances[key] = {"receivables": Decimal("0"), "payables": Decimal("0")}

                if detail.get("transaction_type") == "receivable":
                    interco_balances[key]["receivables"] += Decimal(str(detail.get("amount", 0)))
                elif detail.get("transaction_type") == "payable":
                    interco_balances[key]["payables"] += Decimal(str(detail.get("amount", 0)))

        for (entity1_id, entity2_id), balances in interco_balances.items():
            amount = min(balances["receivables"], balances["payables"])
            if amount <= 0:
                continue

            journal_entries = [
                {
                    "account": "401_ELIM",
                    "debit": float(amount),
                    "credit": 0,
                    "label": "Elimination dette IG",
                    "entity_id": entity2_id
                },
                {
                    "account": "411_ELIM",
                    "debit": 0,
                    "credit": float(amount),
                    "label": "Elimination creance IG",
                    "entity_id": entity1_id
                }
            ]

            elim = self.elimination_repo.create({
                "consolidation_id": consolidation.id,
                "elimination_type": EliminationType.INTERCOMPANY_RECEIVABLES,
                "description": f"Elimination creances/dettes {entity1_id} - {entity2_id}",
                "amount": amount,
                "currency": consolidation.consolidation_currency,
                "entity1_id": UUID(entity1_id),
                "entity2_id": UUID(entity2_id),
                "journal_entries": journal_entries,
                "is_automatic": True
            })
            eliminations.append(elim)

        return eliminations

    def _generate_intercompany_sales_eliminations(
        self,
        consolidation: Consolidation,
        packages: List[ConsolidationPackage]
    ) -> List[EliminationEntry]:
        """Generer les eliminations ventes/achats intercompany."""
        eliminations = []

        for package in packages:
            if package.intercompany_sales > 0:
                # Elimination simplifiee basee sur les totaux declares
                journal_entries = [
                    {
                        "account": "707_ELIM",
                        "debit": float(package.intercompany_sales),
                        "credit": 0,
                        "label": "Elimination ventes IG",
                        "entity_id": str(package.entity_id)
                    },
                    {
                        "account": "607_ELIM",
                        "debit": 0,
                        "credit": float(package.intercompany_sales),
                        "label": "Elimination achats IG",
                        "entity_id": "CONSO"
                    }
                ]

                elim = self.elimination_repo.create({
                    "consolidation_id": consolidation.id,
                    "elimination_type": EliminationType.INTERCOMPANY_SALES,
                    "description": f"Elimination CA IG entite {package.entity_id}",
                    "amount": package.intercompany_sales,
                    "currency": consolidation.consolidation_currency,
                    "entity1_id": package.entity_id,
                    "journal_entries": journal_entries,
                    "is_automatic": True
                })
                eliminations.append(elim)

        return eliminations

    def _generate_dividend_eliminations(
        self,
        consolidation: Consolidation,
        packages: List[ConsolidationPackage]
    ) -> List[EliminationEntry]:
        """Generer les eliminations de dividendes intercompany."""
        eliminations = []

        for package in packages:
            if package.dividends_to_parent > 0:
                entity = self.entity_repo.get_by_id(package.entity_id)
                if not entity or not entity.parent_entity_id:
                    continue

                journal_entries = [
                    {
                        "account": "761_ELIM",
                        "debit": float(package.dividends_to_parent),
                        "credit": 0,
                        "label": "Elimination dividendes recus",
                        "entity_id": str(entity.parent_entity_id)
                    },
                    {
                        "account": "110_ELIM",
                        "debit": 0,
                        "credit": float(package.dividends_to_parent),
                        "label": "Reconstitution reserves",
                        "entity_id": str(package.entity_id)
                    }
                ]

                elim = self.elimination_repo.create({
                    "consolidation_id": consolidation.id,
                    "elimination_type": EliminationType.INTERCOMPANY_DIVIDENDS,
                    "description": f"Elimination dividendes {entity.name}",
                    "amount": package.dividends_to_parent,
                    "currency": consolidation.consolidation_currency,
                    "entity1_id": entity.parent_entity_id,
                    "entity2_id": package.entity_id,
                    "journal_entries": journal_entries,
                    "is_automatic": True
                })
                eliminations.append(elim)

        return eliminations

    def _generate_margin_eliminations(
        self,
        consolidation: Consolidation,
        packages: List[ConsolidationPackage]
    ) -> List[EliminationEntry]:
        """Generer les eliminations de marges internes sur stocks."""
        # Implementation simplifiee - a enrichir selon les besoins metier
        return []

    # ========================================================================
    # RECONCILIATION INTER-SOCIETES
    # ========================================================================

    def create_reconciliation(
        self,
        consolidation_id: UUID,
        entity1_id: UUID,
        entity2_id: UUID,
        transaction_type: str,
        amount_entity1: Decimal,
        amount_entity2: Decimal,
        tolerance_amount: Decimal = Decimal("0"),
        tolerance_pct: Decimal = Decimal("0"),
        created_by: UUID = None
    ) -> IntercompanyReconciliation:
        """Creer une reconciliation intercompany."""
        return self.reconciliation_repo.create({
            "consolidation_id": consolidation_id,
            "entity1_id": entity1_id,
            "entity2_id": entity2_id,
            "transaction_type": transaction_type,
            "amount_entity1": amount_entity1,
            "amount_entity2": amount_entity2,
            "tolerance_amount": tolerance_amount,
            "tolerance_pct": tolerance_pct,
            "currency": "EUR"
        }, created_by=created_by or (UUID(self.user_id) if self.user_id else None))

    def auto_reconcile_intercompany(
        self,
        consolidation_id: UUID
    ) -> Dict[str, Any]:
        """Reconcilier automatiquement les soldes intercompany."""
        packages = self.package_repo.get_by_consolidation(
            consolidation_id,
            status=[PackageStatus.VALIDATED]
        )

        reconciliations_created = 0
        warnings = []

        # Construire une matrice des soldes intercompany
        interco_matrix = {}
        for package in packages:
            for detail in (package.intercompany_details or []):
                key = (str(package.entity_id), str(detail.get("counterparty_entity_id")), detail.get("transaction_type"))
                if key not in interco_matrix:
                    interco_matrix[key] = Decimal("0")
                interco_matrix[key] += Decimal(str(detail.get("amount", 0)))

        # Identifier les paires et reconcilier
        processed = set()
        for key, amount in interco_matrix.items():
            entity1, entity2, tx_type = key
            pair_key = tuple(sorted([entity1, entity2]))

            if pair_key in processed:
                continue

            # Trouver le montant inverse
            reverse_type = "payable" if tx_type == "receivable" else "receivable"
            reverse_key = (entity2, entity1, reverse_type)
            reverse_amount = interco_matrix.get(reverse_key, Decimal("0"))

            recon = self.reconciliation_repo.create({
                "consolidation_id": consolidation_id,
                "entity1_id": UUID(entity1),
                "entity2_id": UUID(entity2),
                "transaction_type": tx_type,
                "amount_entity1": amount,
                "amount_entity2": reverse_amount,
                "currency": "EUR",
                "tolerance_amount": Decimal("1.00"),
                "tolerance_pct": Decimal("0.01")
            })

            reconciliations_created += 1
            processed.add(pair_key)

            if not recon.is_within_tolerance:
                warnings.append(
                    f"Ecart hors tolerance entre {entity1} et {entity2}: {recon.difference}"
                )

        return {
            "reconciliations_created": reconciliations_created,
            "warnings": warnings
        }

    def get_reconciliation_summary(
        self,
        consolidation_id: UUID
    ) -> Dict[str, Any]:
        """Obtenir le resume des reconciliations."""
        return self.reconciliation_repo.get_summary(consolidation_id)

    # ========================================================================
    # CALCUL DES MINORITAIRES
    # ========================================================================

    def calculate_minority_interests(
        self,
        consolidation_id: UUID
    ) -> List[MinorityInterest]:
        """Calculer les interets minoritaires."""
        consolidation = self.get_consolidation(consolidation_id)
        perimeter_id = consolidation.perimeter_id
        packages = self.package_repo.get_by_consolidation(
            consolidation_id,
            status=[PackageStatus.VALIDATED]
        )

        interests = []
        entities = {str(e.id): e for e in self.entity_repo.get_by_perimeter(perimeter_id)}

        for package in packages:
            entity = entities.get(str(package.entity_id))
            if not entity:
                continue

            # Seulement pour les filiales non detenues a 100%
            if entity.total_ownership_pct >= Decimal("100"):
                continue

            group_pct = entity.total_ownership_pct
            minority_pct = Decimal("100") - group_pct

            equity = package.total_equity_converted
            net_income = package.net_income_converted

            minority = MinorityInterest(
                tenant_id=self.tenant_id,
                consolidation_id=consolidation_id,
                entity_id=entity.id,
                period_end=consolidation.period_end,
                group_ownership_pct=group_pct,
                minority_pct=minority_pct,
                total_equity=equity,
                group_share_equity=(equity * group_pct / Decimal("100")).quantize(Decimal("0.01")),
                minority_share_equity=(equity * minority_pct / Decimal("100")).quantize(Decimal("0.01")),
                net_income=net_income,
                group_share_income=(net_income * group_pct / Decimal("100")).quantize(Decimal("0.01")),
                minority_share_income=(net_income * minority_pct / Decimal("100")).quantize(Decimal("0.01")),
                currency=consolidation.consolidation_currency
            )
            self.db.add(minority)
            interests.append(minority)

        self.db.commit()
        return interests

    # ========================================================================
    # EXECUTION DE LA CONSOLIDATION
    # ========================================================================

    def execute_consolidation(
        self,
        consolidation_id: UUID
    ) -> Dict[str, Any]:
        """
        Executer le processus de consolidation complet.

        1. Verifier les prerequis (paquets, cours de change)
        2. Convertir les devises
        3. Generer les eliminations
        4. Calculer les minoritaires
        5. Agreger les soldes
        6. Mettre a jour les totaux
        """
        consolidation = self.get_consolidation(consolidation_id)

        if consolidation.status not in [ConsolidationStatus.DRAFT, ConsolidationStatus.IN_PROGRESS]:
            raise ConsolidationStatusError(consolidation.status.value, action="execute")

        # Passer en statut IN_PROGRESS
        self.consolidation_repo.change_status(
            consolidation,
            ConsolidationStatus.IN_PROGRESS,
            UUID(self.user_id) if self.user_id else None
        )

        results = {
            "packages_processed": 0,
            "eliminations_generated": 0,
            "minority_interests": 0,
            "warnings": [],
            "errors": []
        }

        try:
            # 1. Verifier les cours de change
            missing_rates = self.check_required_exchange_rates(
                consolidation.perimeter_id,
                consolidation.period_end,
                consolidation.consolidation_currency
            )
            if missing_rates:
                results["warnings"].append(f"Cours manquants: {', '.join(missing_rates)}")

            # 2. Traiter les paquets
            packages = self.package_repo.get_by_consolidation(
                consolidation_id,
                status=[PackageStatus.VALIDATED]
            )
            results["packages_processed"] = len(packages)

            # 3. Generer les eliminations
            eliminations = self.generate_eliminations(consolidation_id)
            results["eliminations_generated"] = len(eliminations)

            # 4. Calculer les minoritaires
            minorities = self.calculate_minority_interests(consolidation_id)
            results["minority_interests"] = len(minorities)

            # 5. Calculer les totaux
            totals = self._calculate_consolidated_totals(consolidation_id)

            # 6. Mettre a jour la consolidation
            self.consolidation_repo.update_totals(
                consolidation,
                totals,
                UUID(self.user_id) if self.user_id else None
            )

            # Log
            self._log_action(
                "execute_consolidation",
                consolidation_id=consolidation_id,
                target_type="Consolidation",
                target_id=consolidation_id,
                new_values=results
            )

        except Exception as e:
            results["errors"].append(str(e))
            # Remettre en DRAFT en cas d'erreur
            self.consolidation_repo.change_status(
                consolidation,
                ConsolidationStatus.DRAFT,
                UUID(self.user_id) if self.user_id else None
            )

        return results

    def _calculate_consolidated_totals(
        self,
        consolidation_id: UUID
    ) -> Dict[str, Decimal]:
        """Calculer les totaux consolides."""
        packages = self.package_repo.get_by_consolidation(
            consolidation_id,
            status=[PackageStatus.VALIDATED]
        )
        eliminations = self.elimination_repo.list_by_consolidation(consolidation_id)
        minorities = self.db.query(MinorityInterest).filter(
            MinorityInterest.tenant_id == self.tenant_id,
            MinorityInterest.consolidation_id == consolidation_id
        ).all()

        # Sommes brutes
        total_assets = sum(p.total_assets_converted for p in packages)
        total_liabilities = sum(p.total_liabilities_converted for p in packages)
        total_equity = sum(p.total_equity_converted for p in packages)
        total_revenue = Decimal("0")  # A calculer depuis les balances
        net_income = sum(p.net_income_converted for p in packages)
        translation_diff = sum(p.translation_difference for p in packages)

        # Appliquer les eliminations
        for elim in eliminations:
            for entry in (elim.journal_entries or []):
                amount = Decimal(str(entry.get("debit", 0))) - Decimal(str(entry.get("credit", 0)))
                account = entry.get("account", "")

                if account.startswith("1"):  # Capitaux propres
                    total_equity -= amount
                elif account.startswith(("2", "3", "5")):  # Actifs
                    total_assets -= amount
                elif account.startswith("4"):  # Dettes
                    total_liabilities -= amount
                elif account.startswith("7"):  # Produits
                    total_revenue -= amount
                elif account.startswith("6"):  # Charges
                    net_income += amount

        # Calcul des parts
        minority_equity = sum(m.minority_share_equity for m in minorities)
        minority_income = sum(m.minority_share_income for m in minorities)
        group_equity = total_equity - minority_equity
        group_income = net_income - minority_income

        # Goodwill
        goodwill_query = self.db.query(GoodwillCalculation).filter(
            GoodwillCalculation.tenant_id == self.tenant_id,
            GoodwillCalculation.consolidation_id == consolidation_id
        )
        total_goodwill = sum(g.carrying_value for g in goodwill_query.all())

        return {
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "group_equity": group_equity,
            "minority_interests": minority_equity,
            "consolidated_revenue": total_revenue,
            "consolidated_net_income": net_income,
            "group_net_income": group_income,
            "minority_net_income": minority_income,
            "translation_difference": translation_diff,
            "total_goodwill": total_goodwill
        }

    # ========================================================================
    # RAPPORTS CONSOLIDES
    # ========================================================================

    def generate_report(
        self,
        request: GenerateReportRequest
    ) -> ConsolidatedReport:
        """Generer un rapport consolide."""
        consolidation = self.get_consolidation(request.consolidation_id)

        # Construire les donnees du rapport
        report_data = {}

        if request.report_type == ReportType.BALANCE_SHEET:
            report_data = self._build_balance_sheet(consolidation)
        elif request.report_type == ReportType.INCOME_STATEMENT:
            report_data = self._build_income_statement(consolidation)
        elif request.report_type == ReportType.EQUITY_VARIATION:
            report_data = self._build_equity_variation(consolidation)
        elif request.report_type == ReportType.CONSOLIDATION_PACKAGE:
            report_data = self._build_consolidation_package(consolidation)

        # Donnees comparatives
        comparative_data = {}
        if request.include_comparative and request.comparative_consolidation_id:
            comparative = self.consolidation_repo.get_by_id(request.comparative_consolidation_id)
            if comparative:
                if request.report_type == ReportType.BALANCE_SHEET:
                    comparative_data = self._build_balance_sheet(comparative)
                elif request.report_type == ReportType.INCOME_STATEMENT:
                    comparative_data = self._build_income_statement(comparative)

        return self.report_repo.create({
            "consolidation_id": consolidation.id,
            "report_type": request.report_type,
            "name": f"{request.report_type.value} - {consolidation.name}",
            "period_start": consolidation.period_start,
            "period_end": consolidation.period_end,
            "report_data": report_data,
            "comparative_data": comparative_data,
            "parameters": request.parameters
        }, created_by=UUID(self.user_id) if self.user_id else None)

    def _build_balance_sheet(self, consolidation: Consolidation) -> Dict[str, Any]:
        """Construire les donnees du bilan consolide."""
        return {
            "assets": {
                "non_current": {
                    "goodwill": str(consolidation.total_goodwill),
                    "intangible_assets": "0.00",
                    "tangible_assets": "0.00",
                    "financial_assets": "0.00",
                    "total": str(consolidation.total_goodwill)
                },
                "current": {
                    "inventories": "0.00",
                    "receivables": "0.00",
                    "cash": "0.00",
                    "total": str(consolidation.total_assets - consolidation.total_goodwill)
                },
                "total": str(consolidation.total_assets)
            },
            "liabilities": {
                "equity": {
                    "share_capital": "0.00",
                    "reserves": "0.00",
                    "retained_earnings": "0.00",
                    "net_income_group": str(consolidation.group_net_income),
                    "translation_reserve": str(consolidation.translation_difference),
                    "group_equity": str(consolidation.group_equity),
                    "minority_interests": str(consolidation.minority_interests),
                    "total": str(consolidation.total_equity)
                },
                "non_current": {
                    "long_term_debt": "0.00",
                    "provisions": "0.00",
                    "total": "0.00"
                },
                "current": {
                    "short_term_debt": "0.00",
                    "payables": "0.00",
                    "total": str(consolidation.total_liabilities)
                },
                "total": str(consolidation.total_liabilities + consolidation.total_equity)
            },
            "currency": consolidation.consolidation_currency,
            "period_end": str(consolidation.period_end)
        }

    def _build_income_statement(self, consolidation: Consolidation) -> Dict[str, Any]:
        """Construire les donnees du compte de resultat consolide."""
        return {
            "revenue": str(consolidation.consolidated_revenue),
            "cost_of_sales": "0.00",
            "gross_profit": "0.00",
            "operating_expenses": "0.00",
            "operating_income": "0.00",
            "financial_result": "0.00",
            "income_before_tax": "0.00",
            "income_tax": "0.00",
            "net_income": str(consolidation.consolidated_net_income),
            "attributable_to": {
                "owners_of_parent": str(consolidation.group_net_income),
                "minority_interests": str(consolidation.minority_net_income)
            },
            "currency": consolidation.consolidation_currency,
            "period": {
                "start": str(consolidation.period_start),
                "end": str(consolidation.period_end)
            }
        }

    def _build_equity_variation(self, consolidation: Consolidation) -> Dict[str, Any]:
        """Construire le tableau de variation des capitaux propres."""
        return {
            "opening_balance": {
                "group_equity": "0.00",
                "minority_interests": "0.00",
                "total": "0.00"
            },
            "movements": {
                "net_income": {
                    "group": str(consolidation.group_net_income),
                    "minority": str(consolidation.minority_net_income)
                },
                "dividends": "0.00",
                "scope_changes": "0.00",
                "translation_differences": str(consolidation.translation_difference),
                "other": "0.00"
            },
            "closing_balance": {
                "group_equity": str(consolidation.group_equity),
                "minority_interests": str(consolidation.minority_interests),
                "total": str(consolidation.total_equity)
            },
            "currency": consolidation.consolidation_currency
        }

    def _build_consolidation_package(self, consolidation: Consolidation) -> Dict[str, Any]:
        """Construire la liasse de consolidation."""
        packages = self.package_repo.get_by_consolidation(consolidation.id)
        eliminations = self.elimination_repo.list_by_consolidation(consolidation.id)

        return {
            "perimeter": {
                "entities_count": len(packages),
                "consolidation_currency": consolidation.consolidation_currency,
                "accounting_standard": consolidation.accounting_standard.value
            },
            "packages": [
                {
                    "entity_id": str(p.entity_id),
                    "status": p.status.value,
                    "local_currency": p.local_currency,
                    "total_assets": str(p.total_assets_converted),
                    "total_equity": str(p.total_equity_converted),
                    "net_income": str(p.net_income_converted)
                }
                for p in packages
            ],
            "eliminations": {
                "count": len(eliminations),
                "total_amount": str(sum(e.amount for e in eliminations)),
                "by_type": {}
            },
            "consolidated_totals": {
                "total_assets": str(consolidation.total_assets),
                "total_equity": str(consolidation.total_equity),
                "group_equity": str(consolidation.group_equity),
                "minority_interests": str(consolidation.minority_interests),
                "net_income": str(consolidation.consolidated_net_income)
            }
        }

    # ========================================================================
    # DASHBOARD
    # ========================================================================

    def get_dashboard(self) -> Dict[str, Any]:
        """Obtenir les statistiques du dashboard."""
        # Perimetres actifs
        perimeters, _ = self.perimeter_repo.list(is_active=True, page_size=1000)

        # Entites par methode
        entities, _ = self.entity_repo.list(page_size=1000)
        entities_by_method = {}
        for e in entities:
            method = e.consolidation_method.value
            entities_by_method[method] = entities_by_method.get(method, 0) + 1

        # Consolidations en cours
        consos_progress, _ = self.consolidation_repo.list(
            ConsolidationFilters(status=[ConsolidationStatus.DRAFT, ConsolidationStatus.IN_PROGRESS]),
            page_size=1000
        )
        consos_validated, _ = self.consolidation_repo.list(
            ConsolidationFilters(status=[ConsolidationStatus.VALIDATED, ConsolidationStatus.PUBLISHED]),
            page_size=1000
        )

        # Paquets
        packages_pending, _ = self.package_repo.list(
            PackageFilters(status=[PackageStatus.SUBMITTED]),
            page_size=1000
        )
        packages_validated, _ = self.package_repo.list(
            PackageFilters(status=[PackageStatus.VALIDATED]),
            page_size=1000
        )

        return {
            "active_perimeters": len(perimeters),
            "total_entities": len(entities),
            "entities_by_method": entities_by_method,
            "consolidations_in_progress": len(consos_progress),
            "consolidations_validated": len(consos_validated),
            "packages_pending": len(packages_pending),
            "packages_validated": len(packages_validated),
            "packages_rejected": 0,  # A calculer
            "total_intercompany_balance": Decimal("0"),  # A calculer
            "unreconciled_items": 0,  # A calculer
            "reconciliation_rate": Decimal("0"),
            "total_eliminations": 0,
            "elimination_amount": Decimal("0"),
            "total_goodwill": Decimal("0"),
            "total_impairment": Decimal("0")
        }

    # ========================================================================
    # AUDIT
    # ========================================================================

    def _log_action(
        self,
        action: str,
        consolidation_id: UUID = None,
        entity_id: UUID = None,
        target_type: str = None,
        target_id: UUID = None,
        old_values: Dict = None,
        new_values: Dict = None,
        description: str = None
    ):
        """Enregistrer une action dans le journal d'audit."""
        if self.user_id:
            self.audit_repo.create(
                action=action,
                user_id=UUID(self.user_id),
                consolidation_id=consolidation_id,
                entity_id=entity_id,
                target_type=target_type,
                target_id=target_id,
                old_values=old_values,
                new_values=new_values,
                description=description,
                action_category="consolidation"
            )


# ============================================================================
# FACTORY
# ============================================================================

def create_consolidation_service(
    db: Session,
    tenant_id: str,
    user_id: str = None
) -> ConsolidationService:
    """Creer un service de consolidation configure."""
    return ConsolidationService(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id
    )
