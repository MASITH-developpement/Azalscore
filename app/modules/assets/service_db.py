"""
AZALS MODULE ASSETS - Service avec Base de Donnees
===================================================

Service de gestion des immobilisations avec persistance SQLAlchemy.
Integre toutes les fonctionnalites des ERP leaders:
- Sage, Odoo, Microsoft Dynamics 365, Pennylane, Axonaut

Fonctionnalites:
- Gestion du cycle de vie complet
- Calcul des amortissements (lineaire, degressif, unites de production, SOFTY)
- Suivi maintenance et garantie
- Cessions et mises au rebut
- Inventaire physique avec codes-barres/QR
- Valorisation et reporting
- Integration comptable
"""

import calendar
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from .exceptions import (
    AssetAlreadyDisposedError,
    AssetAlreadyInServiceError,
    AssetCodeExistsError,
    AssetHasComponentsError,
    AssetNotFoundError,
    AssetNotInServiceError,
    CategoryCodeExistsError,
    CategoryHasAssetsError,
    CategoryHasChildrenError,
    CategoryNotFoundError,
    DateValidationError,
    DepreciationAlreadyPostedError,
    DepreciationCalculationError,
    DepreciationRunNotFoundError,
    DisposalDateBeforeAcquisitionError,
    InServiceDateBeforeAcquisitionError,
    InventoryAlreadyCompletedError,
    InventoryInProgressError,
    InventoryNotFoundError,
    InvalidDepreciationMethodError,
    MaintenanceAlreadyCompletedError,
    MaintenanceNotFoundError,
    TransferNotFoundError,
    UsefulLifeNotSetError,
)
from .models import (
    AssetStatus,
    AssetType,
    DepreciationMethod,
    DisposalType,
    InventoryStatus,
    MaintenanceStatus,
    MaintenanceType,
    MovementType,
)
from .repository import (
    AssetCategoryRepository,
    AssetInsurancePolicyRepository,
    AssetInventoryRepository,
    AssetMaintenanceRepository,
    AssetMovementRepository,
    AssetTransferRepository,
    DepreciationRunRepository,
    DepreciationScheduleRepository,
    FixedAssetRepository,
)
from .schemas import (
    AssetCategoryCreate,
    AssetCategoryUpdate,
    AssetFilters,
    AssetInventoryCreate,
    AssetInventoryItemUpdate,
    AssetMaintenanceComplete,
    AssetMaintenanceCreate,
    AssetMaintenanceUpdate,
    AssetMovementCreate,
    AssetTransferCreate,
    DepreciationRunCreate,
    DisposeAssetRequest,
    FixedAssetCreate,
    FixedAssetUpdate,
    PutInServiceRequest,
)


# ============================================================================
# CONSTANTES - COEFFICIENTS DEGRESSIFS (CGI Francais)
# ============================================================================

DECLINING_BALANCE_COEFFICIENTS = {
    3: Decimal("1.25"),
    4: Decimal("1.25"),
    5: Decimal("1.75"),
    6: Decimal("1.75"),
    7: Decimal("2.25"),
}

# Durees d'amortissement recommandees (PCG)
RECOMMENDED_USEFUL_LIFE = {
    AssetType.INTANGIBLE_SOFTWARE: 3,
    AssetType.INTANGIBLE_PATENT: 5,
    AssetType.INTANGIBLE_LICENSE: 5,
    AssetType.INTANGIBLE_TRADEMARK: 10,
    AssetType.INTANGIBLE_GOODWILL: 10,
    AssetType.INTANGIBLE_RD: 5,
    AssetType.TANGIBLE_LAND: 0,  # Non amortissable
    AssetType.TANGIBLE_BUILDING: 25,
    AssetType.TANGIBLE_TECHNICAL: 10,
    AssetType.TANGIBLE_INDUSTRIAL: 10,
    AssetType.TANGIBLE_TRANSPORT: 5,
    AssetType.TANGIBLE_OFFICE: 5,
    AssetType.TANGIBLE_IT: 3,
    AssetType.TANGIBLE_FURNITURE: 10,
    AssetType.TANGIBLE_FIXTURE: 10,
    AssetType.TANGIBLE_TOOLS: 5,
}

# Comptes comptables par defaut (PCG)
ACCOUNTING_ACCOUNTS = {
    AssetType.INTANGIBLE_GOODWILL: {"asset": "207000", "depreciation": "280700", "expense": "681100"},
    AssetType.INTANGIBLE_PATENT: {"asset": "205000", "depreciation": "280500", "expense": "681100"},
    AssetType.INTANGIBLE_LICENSE: {"asset": "205000", "depreciation": "280500", "expense": "681100"},
    AssetType.INTANGIBLE_SOFTWARE: {"asset": "205000", "depreciation": "280500", "expense": "681100"},
    AssetType.INTANGIBLE_TRADEMARK: {"asset": "206000", "depreciation": "280600", "expense": "681100"},
    AssetType.INTANGIBLE_RD: {"asset": "203000", "depreciation": "280300", "expense": "681100"},
    AssetType.TANGIBLE_LAND: {"asset": "211000", "depreciation": None, "expense": None},
    AssetType.TANGIBLE_BUILDING: {"asset": "213000", "depreciation": "281300", "expense": "681120"},
    AssetType.TANGIBLE_TECHNICAL: {"asset": "215100", "depreciation": "281510", "expense": "681120"},
    AssetType.TANGIBLE_INDUSTRIAL: {"asset": "215400", "depreciation": "281540", "expense": "681120"},
    AssetType.TANGIBLE_TRANSPORT: {"asset": "218200", "depreciation": "281820", "expense": "681120"},
    AssetType.TANGIBLE_OFFICE: {"asset": "218300", "depreciation": "281830", "expense": "681120"},
    AssetType.TANGIBLE_IT: {"asset": "218300", "depreciation": "281830", "expense": "681120"},
    AssetType.TANGIBLE_FURNITURE: {"asset": "218400", "depreciation": "281840", "expense": "681120"},
    AssetType.TANGIBLE_FIXTURE: {"asset": "218100", "depreciation": "281810", "expense": "681120"},
    AssetType.TANGIBLE_TOOLS: {"asset": "215500", "depreciation": "281550", "expense": "681120"},
    AssetType.FINANCIAL_PARTICIPATION: {"asset": "261000", "depreciation": "296100", "expense": "686100"},
    AssetType.FINANCIAL_LOAN: {"asset": "274000", "depreciation": "297400", "expense": "686600"},
    AssetType.FINANCIAL_DEPOSIT: {"asset": "275000", "depreciation": None, "expense": None},
}


class AssetService:
    """
    Service de gestion des immobilisations.

    Fonctionnalites completes:
    - CRUD categories et actifs
    - Mise en service
    - Calcul et generation des amortissements
    - Cessions et mises au rebut
    - Maintenance
    - Inventaire physique
    - Transferts
    - Assurances
    - Reporting et statistiques
    """

    def __init__(self, db: Session, tenant_id: UUID, user_id: UUID = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

        # Repositories
        self.category_repo = AssetCategoryRepository(db, tenant_id)
        self.asset_repo = FixedAssetRepository(db, tenant_id)
        self.schedule_repo = DepreciationScheduleRepository(db, tenant_id)
        self.movement_repo = AssetMovementRepository(db, tenant_id)
        self.maintenance_repo = AssetMaintenanceRepository(db, tenant_id)
        self.inventory_repo = AssetInventoryRepository(db, tenant_id)
        self.depreciation_run_repo = DepreciationRunRepository(db, tenant_id)
        self.insurance_repo = AssetInsurancePolicyRepository(db, tenant_id)
        self.transfer_repo = AssetTransferRepository(db, tenant_id)

    # ========================================================================
    # CATEGORIES
    # ========================================================================

    def create_category(self, data: AssetCategoryCreate):
        """Creer une categorie d'immobilisation."""
        if self.category_repo.code_exists(data.code):
            raise CategoryCodeExistsError(data.code)

        return self.category_repo.create(data.model_dump(), self.user_id)

    def update_category(self, category_id: UUID, data: AssetCategoryUpdate):
        """Mettre a jour une categorie."""
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise CategoryNotFoundError(str(category_id))

        update_data = data.model_dump(exclude_unset=True)
        return self.category_repo.update(category, update_data, self.user_id)

    def delete_category(self, category_id: UUID):
        """Supprimer une categorie (soft delete)."""
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise CategoryNotFoundError(str(category_id))

        # Verifier pas d'actifs
        count = self.category_repo.count_assets(category_id)
        if count > 0:
            raise CategoryHasAssetsError(str(category_id), count)

        # Verifier pas d'enfants
        children = self.category_repo.count_children(category_id)
        if children > 0:
            raise CategoryHasChildrenError(str(category_id), children)

        return self.category_repo.soft_delete(category, self.user_id)

    def get_category(self, category_id: UUID):
        """Recuperer une categorie."""
        return self.category_repo.get_by_id(category_id)

    def list_categories(self, parent_id: UUID = None, active_only: bool = True, skip: int = 0, limit: int = 100):
        """Lister les categories."""
        return self.category_repo.list(parent_id, active_only, skip, limit)

    # ========================================================================
    # IMMOBILISATIONS - CRUD
    # ========================================================================

    def create_asset(self, data: FixedAssetCreate):
        """Creer une immobilisation."""
        # Verifier code unique si fourni
        if data.asset_code and self.asset_repo.code_exists(data.asset_code):
            raise AssetCodeExistsError(data.asset_code)

        # Verifier barcode unique si fourni
        if data.barcode and self.asset_repo.barcode_exists(data.barcode):
            raise AssetCodeExistsError(f"Barcode {data.barcode}")

        # Preparer les donnees
        asset_data = data.model_dump()

        # Appliquer comptes comptables par defaut
        asset_type = AssetType(data.asset_type.value)
        if asset_type in ACCOUNTING_ACCOUNTS and not data.asset_account:
            accounts = ACCOUNTING_ACCOUNTS[asset_type]
            asset_data["asset_account"] = accounts.get("asset")
            asset_data["depreciation_account"] = accounts.get("depreciation")
            asset_data["expense_account"] = accounts.get("expense")

        # Appliquer duree par defaut
        if not data.useful_life_years and asset_type in RECOMMENDED_USEFUL_LIFE:
            asset_data["useful_life_years"] = RECOMMENDED_USEFUL_LIFE[asset_type]

        # Definir methode si non amortissable
        if asset_type == AssetType.TANGIBLE_LAND:
            asset_data["depreciation_method"] = DepreciationMethod.NONE

        asset = self.asset_repo.create(asset_data, self.user_id)

        # Enregistrer mouvement d'acquisition
        self._create_acquisition_movement(asset)

        return asset

    def update_asset(self, asset_id: UUID, data: FixedAssetUpdate):
        """Mettre a jour une immobilisation."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundError(str(asset_id))

        update_data = data.model_dump(exclude_unset=True)
        return self.asset_repo.update(asset, update_data, self.user_id)

    def delete_asset(self, asset_id: UUID):
        """Supprimer une immobilisation (soft delete)."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundError(str(asset_id))

        # Verifier pas de composants
        comp_count = self.asset_repo.count_components(asset_id)
        if comp_count > 0:
            raise AssetHasComponentsError(str(asset_id), comp_count)

        return self.asset_repo.soft_delete(asset, self.user_id)

    def get_asset(self, asset_id: UUID):
        """Recuperer une immobilisation."""
        return self.asset_repo.get_by_id(asset_id)

    def get_asset_by_code(self, code: str):
        """Recuperer une immobilisation par code."""
        return self.asset_repo.get_by_code(code)

    def get_asset_by_barcode(self, barcode: str):
        """Recuperer une immobilisation par code-barres."""
        return self.asset_repo.get_by_barcode(barcode)

    def list_assets(
        self,
        filters: AssetFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ):
        """Lister les immobilisations avec filtres."""
        return self.asset_repo.list(filters, page, page_size, sort_by, sort_dir)

    def autocomplete_assets(self, query: str, limit: int = 10):
        """Recherche pour autocomplete."""
        return self.asset_repo.autocomplete(query, limit)

    # ========================================================================
    # MISE EN SERVICE
    # ========================================================================

    def put_in_service(self, asset_id: UUID, data: PutInServiceRequest):
        """Mettre en service une immobilisation."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundError(str(asset_id))

        if asset.status not in [AssetStatus.DRAFT, AssetStatus.RECEIVED]:
            raise AssetAlreadyInServiceError(str(asset_id))

        # Verifier coherence dates
        if data.in_service_date < asset.acquisition_date:
            raise InServiceDateBeforeAcquisitionError(
                str(asset.acquisition_date),
                str(data.in_service_date)
            )

        # Mettre a jour l'actif
        update_data = {
            "status": AssetStatus.IN_SERVICE,
            "in_service_date": data.in_service_date,
            "depreciation_start_date": data.depreciation_start_date or data.in_service_date,
        }

        if data.location_id:
            update_data["location_id"] = data.location_id
        if data.site_name:
            update_data["site_name"] = data.site_name
        if data.responsible_id:
            update_data["responsible_id"] = data.responsible_id
        if data.responsible_name:
            update_data["responsible_name"] = data.responsible_name

        asset = self.asset_repo.update(asset, update_data, self.user_id)

        # Generer le tableau d'amortissement
        self._generate_depreciation_schedule(asset)

        return asset

    # ========================================================================
    # CALCUL DES AMORTISSEMENTS
    # ========================================================================

    def _generate_depreciation_schedule(self, asset):
        """Generer le tableau d'amortissement previsionnel."""
        if asset.depreciation_method == DepreciationMethod.NONE:
            return

        if not asset.depreciation_start_date:
            raise DepreciationCalculationError(str(asset.id), "Date de debut non definie")

        if not asset.useful_life_years or asset.useful_life_years == 0:
            raise UsefulLifeNotSetError(str(asset.id))

        # Supprimer ancien tableau
        self.schedule_repo.delete_by_asset(asset.id)

        # Calculer selon la methode
        if asset.depreciation_method == DepreciationMethod.LINEAR:
            entries = self._calculate_linear_depreciation(asset)
        elif asset.depreciation_method == DepreciationMethod.DECLINING_BALANCE:
            entries = self._calculate_declining_balance(asset)
        elif asset.depreciation_method == DepreciationMethod.SUM_OF_YEARS_DIGITS:
            entries = self._calculate_sum_of_years(asset)
        else:
            entries = self._calculate_linear_depreciation(asset)

        if entries:
            self.schedule_repo.create_bulk(entries)

    def _calculate_linear_depreciation(self, asset) -> list[dict]:
        """Calcul amortissement lineaire."""
        entries = []
        start_date = asset.depreciation_start_date
        depreciable_amount = asset.acquisition_cost - asset.residual_value

        # Taux annuel
        annual_rate = Decimal("100") / asset.useful_life_years
        annual_amount = (depreciable_amount * annual_rate / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        remaining = depreciable_amount
        accumulated = Decimal("0")

        for year in range(asset.useful_life_years + 1):
            if remaining <= 0:
                break

            if year == 0:
                # Premiere annee: prorata temporis
                days_in_year = 366 if calendar.isleap(start_date.year) else 365
                remaining_days = (date(start_date.year, 12, 31) - start_date).days + 1
                prorata = Decimal(str(remaining_days)) / Decimal(str(days_in_year))
                period_depreciation = (annual_amount * prorata).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                period_start = start_date
                period_end = date(start_date.year, 12, 31)
            else:
                period_start = date(start_date.year + year, 1, 1)
                period_end = date(start_date.year + year, 12, 31)
                period_depreciation = min(annual_amount, remaining)

            if remaining <= 0:
                break

            opening_accumulated = accumulated
            accumulated += period_depreciation
            remaining -= period_depreciation

            entries.append({
                "asset_id": asset.id,
                "period_number": year + 1,
                "period_start": period_start,
                "period_end": period_end,
                "fiscal_year": period_start.year,
                "opening_gross_value": asset.acquisition_cost,
                "opening_accumulated_depreciation": opening_accumulated,
                "opening_net_book_value": asset.acquisition_cost - opening_accumulated,
                "depreciation_rate": annual_rate,
                "depreciation_base": depreciable_amount,
                "depreciation_amount": period_depreciation,
                "prorata_days": remaining_days if year == 0 else days_in_year,
                "closing_accumulated_depreciation": accumulated,
                "closing_net_book_value": asset.acquisition_cost - accumulated,
            })

        return entries

    def _calculate_declining_balance(self, asset) -> list[dict]:
        """Calcul amortissement degressif."""
        entries = []
        start_date = asset.depreciation_start_date
        depreciable_amount = asset.acquisition_cost - asset.residual_value

        # Coefficient degressif
        coef = DECLINING_BALANCE_COEFFICIENTS.get(
            asset.useful_life_years,
            Decimal("2.25")
        )
        if asset.declining_balance_rate:
            coef = asset.declining_balance_rate

        linear_rate = Decimal("100") / asset.useful_life_years
        declining_rate = linear_rate * coef

        remaining = depreciable_amount
        accumulated = Decimal("0")

        for year in range(asset.useful_life_years + 1):
            if remaining <= 0:
                break

            if year == 0:
                # Prorata premiere annee
                days_in_year = 366 if calendar.isleap(start_date.year) else 365
                remaining_days = (date(start_date.year, 12, 31) - start_date).days + 1
                prorata = Decimal(str(remaining_days)) / Decimal(str(days_in_year))
                period_depreciation = (remaining * declining_rate / 100 * prorata).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                period_start = start_date
                period_end = date(start_date.year, 12, 31)
            else:
                period_start = date(start_date.year + year, 1, 1)
                period_end = date(start_date.year + year, 12, 31)
                days_in_year = 366 if calendar.isleap(period_start.year) else 365

                # Comparer degressif vs lineaire
                declining_amount = (remaining * declining_rate / 100).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                remaining_years = asset.useful_life_years - year
                if remaining_years > 0:
                    linear_amount = (remaining / remaining_years).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                else:
                    linear_amount = remaining

                # Prendre le plus eleve (passage au lineaire)
                period_depreciation = max(declining_amount, linear_amount)

            if period_depreciation > remaining:
                period_depreciation = remaining

            opening_accumulated = accumulated
            accumulated += period_depreciation
            remaining -= period_depreciation

            entries.append({
                "asset_id": asset.id,
                "period_number": year + 1,
                "period_start": period_start,
                "period_end": period_end,
                "fiscal_year": period_start.year,
                "opening_gross_value": asset.acquisition_cost,
                "opening_accumulated_depreciation": opening_accumulated,
                "opening_net_book_value": asset.acquisition_cost - opening_accumulated,
                "depreciation_rate": declining_rate,
                "depreciation_base": remaining + period_depreciation,
                "depreciation_amount": period_depreciation,
                "closing_accumulated_depreciation": accumulated,
                "closing_net_book_value": asset.acquisition_cost - accumulated,
            })

        return entries

    def _calculate_sum_of_years(self, asset) -> list[dict]:
        """Calcul amortissement SOFTY (Sum Of Years Digits)."""
        entries = []
        start_date = asset.depreciation_start_date
        depreciable_amount = asset.acquisition_cost - asset.residual_value

        # Somme des annees
        n = asset.useful_life_years
        sum_of_years = (n * (n + 1)) / 2

        accumulated = Decimal("0")

        for year in range(asset.useful_life_years):
            remaining_years = n - year
            rate = Decimal(str(remaining_years)) / Decimal(str(sum_of_years))
            period_depreciation = (depreciable_amount * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            if year == 0:
                period_start = start_date
            else:
                period_start = date(start_date.year + year, 1, 1)
            period_end = date(start_date.year + year, 12, 31)

            opening_accumulated = accumulated
            accumulated += period_depreciation

            entries.append({
                "asset_id": asset.id,
                "period_number": year + 1,
                "period_start": period_start,
                "period_end": period_end,
                "fiscal_year": period_start.year,
                "opening_gross_value": asset.acquisition_cost,
                "opening_accumulated_depreciation": opening_accumulated,
                "opening_net_book_value": asset.acquisition_cost - opening_accumulated,
                "depreciation_rate": rate * 100,
                "depreciation_base": depreciable_amount,
                "depreciation_amount": period_depreciation,
                "closing_accumulated_depreciation": accumulated,
                "closing_net_book_value": asset.acquisition_cost - accumulated,
            })

        return entries

    def get_depreciation_schedule(self, asset_id: UUID):
        """Recuperer le tableau d'amortissement d'un actif."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundError(str(asset_id))

        entries = self.schedule_repo.get_by_asset(asset_id)

        return {
            "asset_id": asset.id,
            "asset_code": asset.asset_code,
            "asset_name": asset.name,
            "depreciation_method": asset.depreciation_method,
            "useful_life_years": asset.useful_life_years,
            "useful_life_months": asset.useful_life_months,
            "acquisition_cost": asset.acquisition_cost,
            "residual_value": asset.residual_value,
            "entries": entries
        }

    # ========================================================================
    # EXECUTION DES AMORTISSEMENTS
    # ========================================================================

    def run_depreciation(self, data: DepreciationRunCreate):
        """Executer le calcul des amortissements pour une periode."""
        # Verifier si deja execute
        if self.depreciation_run_repo.period_exists(data.period_start, data.period_end):
            raise DepreciationAlreadyPostedError(f"{data.period_start} - {data.period_end}")

        # Creer l'execution
        run_data = {
            "run_date": date.today(),
            "period_start": data.period_start,
            "period_end": data.period_end,
            "fiscal_year": data.fiscal_year or data.period_start.year,
            "period_number": data.period_number,
            "description": data.description,
        }
        run = self.depreciation_run_repo.create(run_data, self.user_id)

        # Recuperer les actifs amortissables
        assets = self.asset_repo.get_depreciable()
        entries = []
        errors = []
        total_depreciation = Decimal("0")

        for asset in assets:
            try:
                # Trouver l'amortissement de la periode
                schedule_entries = self.schedule_repo.get_by_asset(asset.id)

                for entry in schedule_entries:
                    if entry.period_start <= data.period_end and entry.period_end >= data.period_start:
                        if entry.is_posted:
                            continue

                        # Calculer prorata si periode partielle
                        depreciation = self._calculate_period_depreciation(
                            entry, data.period_start, data.period_end
                        )

                        if depreciation > 0:
                            # Mettre a jour l'actif
                            asset.accumulated_depreciation = (
                                (asset.accumulated_depreciation or Decimal("0")) + depreciation
                            )
                            asset.net_book_value = asset.acquisition_cost - asset.accumulated_depreciation

                            # Verifier si totalement amorti
                            if asset.net_book_value <= asset.residual_value:
                                asset.status = AssetStatus.FULLY_DEPRECIATED

                            # Enregistrer le mouvement
                            self._create_depreciation_movement(asset, depreciation, data.period_end)

                            # Preparer l'ecriture comptable
                            accounts = ACCOUNTING_ACCOUNTS.get(AssetType(asset.asset_type.value), {})
                            entries.append({
                                "asset_id": str(asset.id),
                                "asset_code": asset.asset_code,
                                "asset_name": asset.name,
                                "depreciation_amount": float(depreciation),
                                "debit_account": asset.expense_account or accounts.get("expense"),
                                "credit_account": asset.depreciation_account or accounts.get("depreciation"),
                                "schedule_entry_id": str(entry.id),
                            })

                            total_depreciation += depreciation

            except Exception as e:
                errors.append({
                    "asset_id": str(asset.id),
                    "asset_code": asset.asset_code,
                    "error": str(e)
                })

        # Mettre a jour l'execution
        run.assets_processed = len(assets) - len(errors)
        run.total_depreciation = total_depreciation
        run.errors_count = len(errors)
        run.entries = entries
        run.errors = errors
        run.status = "VALIDATED"
        run.validated_at = datetime.utcnow()
        run.validated_by = self.user_id

        self.db.commit()
        self.db.refresh(run)

        return run

    def _calculate_period_depreciation(self, entry, period_start: date, period_end: date) -> Decimal:
        """Calculer l'amortissement pour une periode donnee."""
        entry_days = (entry.period_end - entry.period_start).days + 1
        overlap_start = max(period_start, entry.period_start)
        overlap_end = min(period_end, entry.period_end)
        overlap_days = (overlap_end - overlap_start).days + 1

        if overlap_days >= entry_days:
            return entry.depreciation_amount
        else:
            prorata = Decimal(str(overlap_days)) / Decimal(str(entry_days))
            return (entry.depreciation_amount * prorata).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

    def get_depreciation_run(self, run_id: UUID):
        """Recuperer une execution d'amortissement."""
        return self.depreciation_run_repo.get_by_id(run_id)

    def list_depreciation_runs(self, fiscal_year: int = None, status: str = None, page: int = 1, page_size: int = 20):
        """Lister les executions d'amortissement."""
        return self.depreciation_run_repo.list(fiscal_year, status, page, page_size)

    # ========================================================================
    # CESSIONS
    # ========================================================================

    def dispose_asset(self, asset_id: UUID, data: DisposeAssetRequest):
        """Ceder ou mettre au rebut une immobilisation."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundError(str(asset_id))

        if asset.status in [AssetStatus.DISPOSED, AssetStatus.SCRAPPED]:
            raise AssetAlreadyDisposedError(str(asset_id))

        if data.disposal_date < asset.acquisition_date:
            raise DisposalDateBeforeAcquisitionError(
                str(asset.acquisition_date),
                str(data.disposal_date)
            )

        # Verifier pas de composants
        comp_count = self.asset_repo.count_components(asset_id)
        if comp_count > 0:
            raise AssetHasComponentsError(str(asset_id), comp_count)

        # Calculer amortissement complementaire jusqu'a la cession
        if asset.in_service_date and asset.status == AssetStatus.IN_SERVICE:
            # TODO: Calculer et comptabiliser l'amortissement complementaire
            pass

        # Calculer plus/moins-value
        net_proceeds = data.disposal_proceeds - data.disposal_costs
        gain_loss = net_proceeds - (asset.net_book_value or Decimal("0"))

        # Mettre a jour l'actif
        update_data = {
            "status": AssetStatus.DISPOSED if data.disposal_type == DisposalType.SALE else AssetStatus.SCRAPPED,
            "disposal_date": data.disposal_date,
            "disposal_type": data.disposal_type,
            "disposal_proceeds": data.disposal_proceeds,
            "disposal_costs": data.disposal_costs,
            "disposal_gain_loss": gain_loss,
            "buyer_name": data.buyer_name,
            "buyer_id": data.buyer_id,
        }

        asset = self.asset_repo.update(asset, update_data, self.user_id)

        # Enregistrer le mouvement
        self._create_disposal_movement(asset, data, gain_loss)

        # Generer les ecritures comptables
        accounting_entries = self._generate_disposal_entries(asset, data, gain_loss)

        return {
            "asset_id": asset.id,
            "asset_code": asset.asset_code,
            "disposal_date": data.disposal_date,
            "disposal_type": data.disposal_type,
            "gross_value": asset.acquisition_cost,
            "accumulated_depreciation": asset.accumulated_depreciation,
            "net_book_value": asset.acquisition_cost - (asset.accumulated_depreciation or Decimal("0")),
            "disposal_proceeds": data.disposal_proceeds,
            "disposal_costs": data.disposal_costs,
            "gain_loss": gain_loss,
            "accounting_entries": accounting_entries
        }

    def _generate_disposal_entries(self, asset, data, gain_loss: Decimal) -> list[dict]:
        """Generer les ecritures comptables de cession."""
        entries = []
        accounts = ACCOUNTING_ACCOUNTS.get(AssetType(asset.asset_type.value), {})

        # Sortie de l'amortissement cumule
        if asset.accumulated_depreciation:
            entries.append({
                "account": asset.depreciation_account or accounts.get("depreciation"),
                "debit": float(asset.accumulated_depreciation),
                "credit": 0,
                "label": f"Sortie amortissement {asset.name}"
            })

        # Sortie de l'immobilisation
        entries.append({
            "account": asset.asset_account or accounts.get("asset"),
            "debit": 0,
            "credit": float(asset.acquisition_cost),
            "label": f"Sortie immobilisation {asset.name}"
        })

        # Prix de cession (si vente)
        if data.disposal_proceeds > 0:
            entries.append({
                "account": "462000",  # Creances sur cessions
                "debit": float(data.disposal_proceeds),
                "credit": 0,
                "label": f"Cession {asset.name}"
            })

        # Plus ou moins-value
        if gain_loss >= 0:
            entries.append({
                "account": "775000",  # Produits cessions
                "debit": 0,
                "credit": float(data.disposal_proceeds),
                "label": f"Plus-value cession {asset.name}"
            })
            entries.append({
                "account": "675000",  # VNC cessions
                "debit": float(asset.net_book_value or 0),
                "credit": 0,
                "label": f"VNC sortie {asset.name}"
            })
        else:
            entries.append({
                "account": "675000",
                "debit": float(asset.net_book_value or 0),
                "credit": 0,
                "label": f"VNC sortie {asset.name}"
            })
            if data.disposal_proceeds > 0:
                entries.append({
                    "account": "775000",
                    "debit": 0,
                    "credit": float(data.disposal_proceeds),
                    "label": f"Prix cession {asset.name}"
                })

        return entries

    # ========================================================================
    # MOUVEMENTS
    # ========================================================================

    def _create_acquisition_movement(self, asset):
        """Creer le mouvement d'acquisition."""
        self.movement_repo.create({
            "asset_id": asset.id,
            "movement_type": MovementType.ACQUISITION,
            "movement_date": asset.acquisition_date,
            "amount": asset.acquisition_cost,
            "previous_value": Decimal("0"),
            "new_value": asset.acquisition_cost,
            "description": f"Acquisition de {asset.name}",
            "reference": asset.invoice_reference,
        }, self.user_id)

    def _create_depreciation_movement(self, asset, amount: Decimal, movement_date: date):
        """Creer le mouvement d'amortissement."""
        self.movement_repo.create({
            "asset_id": asset.id,
            "movement_type": MovementType.DEPRECIATION,
            "movement_date": movement_date,
            "amount": amount,
            "previous_value": asset.net_book_value + amount,
            "new_value": asset.net_book_value,
            "description": f"Amortissement periodique",
        }, self.user_id)

    def _create_disposal_movement(self, asset, data, gain_loss: Decimal):
        """Creer le mouvement de cession."""
        self.movement_repo.create({
            "asset_id": asset.id,
            "movement_type": MovementType.DISPOSAL,
            "movement_date": data.disposal_date,
            "amount": asset.net_book_value or Decimal("0"),
            "previous_value": asset.net_book_value,
            "new_value": Decimal("0"),
            "description": f"Cession: {data.disposal_type.value}" + (f" - {data.buyer_name}" if data.buyer_name else ""),
        }, self.user_id)

    def get_asset_movements(self, asset_id: UUID):
        """Recuperer les mouvements d'un actif."""
        return self.movement_repo.get_by_asset(asset_id)

    def list_movements(
        self,
        asset_id: UUID = None,
        movement_type: str = None,
        date_from: date = None,
        date_to: date = None,
        page: int = 1,
        page_size: int = 20
    ):
        """Lister les mouvements."""
        return self.movement_repo.list(asset_id, movement_type, date_from, date_to, page, page_size)

    # ========================================================================
    # MAINTENANCE
    # ========================================================================

    def create_maintenance(self, asset_id: UUID, data: AssetMaintenanceCreate):
        """Creer une maintenance."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundError(str(asset_id))

        maint_data = data.model_dump()
        maint_data["asset_id"] = asset_id

        return self.maintenance_repo.create(maint_data, self.user_id)

    def update_maintenance(self, maintenance_id: UUID, data: AssetMaintenanceUpdate):
        """Mettre a jour une maintenance."""
        maintenance = self.maintenance_repo.get_by_id(maintenance_id)
        if not maintenance:
            raise MaintenanceNotFoundError(str(maintenance_id))

        update_data = data.model_dump(exclude_unset=True)
        return self.maintenance_repo.update(maintenance, update_data, self.user_id)

    def complete_maintenance(self, maintenance_id: UUID, data: AssetMaintenanceComplete):
        """Terminer une maintenance."""
        maintenance = self.maintenance_repo.get_by_id(maintenance_id)
        if not maintenance:
            raise MaintenanceNotFoundError(str(maintenance_id))

        if maintenance.status == MaintenanceStatus.COMPLETED:
            raise MaintenanceAlreadyCompletedError(str(maintenance_id))

        update_data = data.model_dump(exclude_unset=True)
        update_data["status"] = MaintenanceStatus.COMPLETED
        update_data["actual_end_date"] = data.actual_end_date or datetime.utcnow()

        maintenance = self.maintenance_repo.update(maintenance, update_data, self.user_id)

        # Mettre a jour l'actif
        asset_updates = {"last_maintenance_date": date.today()}
        if data.next_maintenance_date:
            asset_updates["next_maintenance_date"] = data.next_maintenance_date
        if data.counter_reading:
            asset_updates["counter_current"] = data.counter_reading

        self.asset_repo.update(
            self.asset_repo.get_by_id(maintenance.asset_id),
            asset_updates,
            self.user_id
        )

        return maintenance

    def get_maintenance(self, maintenance_id: UUID):
        """Recuperer une maintenance."""
        return self.maintenance_repo.get_by_id(maintenance_id)

    def list_maintenances(
        self,
        asset_id: UUID = None,
        status: MaintenanceStatus = None,
        date_from: date = None,
        date_to: date = None,
        page: int = 1,
        page_size: int = 20
    ):
        """Lister les maintenances."""
        return self.maintenance_repo.list(asset_id, status, date_from, date_to, page, page_size)

    def get_upcoming_maintenances(self, days: int = 30):
        """Recuperer les maintenances a venir."""
        return self.maintenance_repo.get_upcoming(days)

    def get_overdue_maintenances(self):
        """Recuperer les maintenances en retard."""
        return self.maintenance_repo.get_overdue()

    # ========================================================================
    # INVENTAIRE PHYSIQUE
    # ========================================================================

    def create_inventory(self, data: AssetInventoryCreate):
        """Creer un inventaire physique."""
        # Verifier pas d'inventaire en cours
        if self.inventory_repo.has_in_progress(data.location_id):
            raise InventoryInProgressError(data.location_name)

        inv_data = data.model_dump()
        inventory = self.inventory_repo.create(inv_data, self.user_id)

        return inventory

    def start_inventory(self, inventory_id: UUID):
        """Demarrer un inventaire (generer les lignes)."""
        inventory = self.inventory_repo.get_by_id(inventory_id)
        if not inventory:
            raise InventoryNotFoundError(str(inventory_id))

        # Recuperer les actifs attendus
        assets = self.asset_repo.get_in_service()

        # Filtrer par localisation si specifie
        if inventory.location_id:
            assets = [a for a in assets if a.location_id == inventory.location_id]

        # Creer les lignes
        items = []
        for asset in assets:
            items.append({
                "asset_id": asset.id,
                "asset_code": asset.asset_code,
                "asset_name": asset.name,
                "expected_location": asset.site_name,
                "expected_barcode": asset.barcode,
                "found": None,
                "is_unexpected": False,
                "location_mismatch": False,
            })

        self.inventory_repo.add_items(inventory_id, items)

        # Mettre a jour l'inventaire
        inventory.assets_expected = len(items)
        inventory.status = InventoryStatus.IN_PROGRESS
        inventory.started_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(inventory)

        return inventory

    def scan_inventory_item(self, inventory_id: UUID, item_id: UUID, data: AssetInventoryItemUpdate):
        """Scanner un element d'inventaire."""
        inventory = self.inventory_repo.get_by_id(inventory_id)
        if not inventory:
            raise InventoryNotFoundError(str(inventory_id))

        if inventory.status != InventoryStatus.IN_PROGRESS:
            raise InventoryAlreadyCompletedError(str(inventory_id))

        item = self.inventory_repo.get_item(item_id)
        if not item:
            from .exceptions import InventoryItemNotFoundError
            raise InventoryItemNotFoundError(str(item_id))

        update_data = data.model_dump(exclude_unset=True)
        update_data["scanned_at"] = datetime.utcnow()
        update_data["scanned_by"] = self.user_id

        # Detecter ecart de localisation
        if data.actual_location and item.expected_location:
            update_data["location_mismatch"] = data.actual_location != item.expected_location

        item = self.inventory_repo.update_item(item, update_data)

        # Recalculer les totaux
        self.inventory_repo.recalculate_counts(inventory)

        return item

    def complete_inventory(self, inventory_id: UUID):
        """Terminer un inventaire."""
        inventory = self.inventory_repo.get_by_id(inventory_id)
        if not inventory:
            raise InventoryNotFoundError(str(inventory_id))

        if inventory.status == InventoryStatus.COMPLETED:
            raise InventoryAlreadyCompletedError(str(inventory_id))

        inventory.status = InventoryStatus.COMPLETED
        inventory.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(inventory)

        return inventory

    def validate_inventory(self, inventory_id: UUID):
        """Valider un inventaire (appliquer les corrections)."""
        inventory = self.inventory_repo.get_by_id(inventory_id)
        if not inventory:
            raise InventoryNotFoundError(str(inventory_id))

        # Mettre a jour les localisations des actifs
        for item in inventory.items:
            if item.found and item.location_mismatch and item.actual_location:
                asset = self.asset_repo.get_by_id(item.asset_id)
                if asset:
                    self.asset_repo.update(asset, {
                        "site_name": item.actual_location
                    }, self.user_id)

        inventory.status = InventoryStatus.VALIDATED
        inventory.validated_at = datetime.utcnow()
        inventory.validated_by = self.user_id
        self.db.commit()
        self.db.refresh(inventory)

        return inventory

    def get_inventory(self, inventory_id: UUID):
        """Recuperer un inventaire."""
        return self.inventory_repo.get_by_id(inventory_id)

    def list_inventories(
        self,
        status: InventoryStatus = None,
        location_id: UUID = None,
        page: int = 1,
        page_size: int = 20
    ):
        """Lister les inventaires."""
        return self.inventory_repo.list(status, location_id, page, page_size)

    # ========================================================================
    # TRANSFERTS
    # ========================================================================

    def create_transfer(self, asset_id: UUID, data: AssetTransferCreate):
        """Creer un transfert d'actif."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundError(str(asset_id))

        if asset.status not in [AssetStatus.IN_SERVICE, AssetStatus.FULLY_DEPRECIATED]:
            raise AssetNotInServiceError(str(asset_id))

        transfer_data = data.model_dump()
        transfer_data["asset_id"] = asset_id
        transfer_data["from_location_id"] = asset.location_id
        transfer_data["from_location_name"] = asset.site_name
        transfer_data["from_responsible_id"] = asset.responsible_id
        transfer_data["from_responsible_name"] = asset.responsible_name
        transfer_data["from_department_id"] = asset.department_id
        transfer_data["from_cost_center"] = asset.cost_center

        return self.transfer_repo.create(transfer_data, self.user_id)

    def approve_transfer(self, transfer_id: UUID):
        """Approuver un transfert."""
        transfer = self.transfer_repo.get_by_id(transfer_id)
        if not transfer:
            raise TransferNotFoundError(str(transfer_id))

        transfer.status = "APPROVED"
        transfer.approved_by = self.user_id
        transfer.approved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(transfer)

        return transfer

    def complete_transfer(self, transfer_id: UUID):
        """Completer un transfert."""
        transfer = self.transfer_repo.get_by_id(transfer_id)
        if not transfer:
            raise TransferNotFoundError(str(transfer_id))

        # Mettre a jour l'actif
        asset = self.asset_repo.get_by_id(transfer.asset_id)
        if asset:
            self.asset_repo.update(asset, {
                "location_id": transfer.to_location_id,
                "site_name": transfer.to_location_name,
                "responsible_id": transfer.to_responsible_id,
                "responsible_name": transfer.to_responsible_name,
                "department_id": transfer.to_department_id,
                "cost_center": transfer.to_cost_center,
            }, self.user_id)

            # Creer le mouvement
            self.movement_repo.create({
                "asset_id": asset.id,
                "movement_type": MovementType.TRANSFER,
                "movement_date": transfer.transfer_date,
                "amount": Decimal("0"),
                "from_location_id": transfer.from_location_id,
                "to_location_id": transfer.to_location_id,
                "from_responsible_id": transfer.from_responsible_id,
                "to_responsible_id": transfer.to_responsible_id,
                "description": f"Transfert vers {transfer.to_location_name or transfer.to_responsible_name}",
            }, self.user_id)

        transfer.status = "COMPLETED"
        transfer.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(transfer)

        return transfer

    def get_transfer(self, transfer_id: UUID):
        """Recuperer un transfert."""
        return self.transfer_repo.get_by_id(transfer_id)

    def list_transfers(self, asset_id: UUID = None, status: str = None, page: int = 1, page_size: int = 20):
        """Lister les transferts."""
        return self.transfer_repo.list(asset_id, status, page, page_size)

    # ========================================================================
    # STATISTIQUES ET DASHBOARD
    # ========================================================================

    def get_statistics(self):
        """Recuperer les statistiques globales."""
        return self.asset_repo.get_statistics()

    def get_dashboard(self):
        """Recuperer les donnees du dashboard."""
        stats = self.get_statistics()

        # Acquisitions recentes
        recent_assets, _ = self.asset_repo.list(
            filters=AssetFilters(acquisition_date_from=date.today() - timedelta(days=30)),
            page=1,
            page_size=5,
            sort_by="acquisition_date",
            sort_dir="desc"
        )

        # Cessions recentes
        disposed_assets, _ = self.asset_repo.list(
            filters=AssetFilters(status=[AssetStatus.DISPOSED, AssetStatus.SCRAPPED]),
            page=1,
            page_size=5,
            sort_by="disposal_date",
            sort_dir="desc"
        )

        # Maintenances a venir
        upcoming_maint = self.maintenance_repo.get_upcoming(30)

        # Garanties expirant
        warranty_expiring = self.asset_repo.get_warranty_expiring(date.today() + timedelta(days=30))

        return {
            "statistics": stats,
            "recent_acquisitions": recent_assets,
            "recent_disposals": disposed_assets,
            "upcoming_maintenances": upcoming_maint[:5],
            "warranty_expiring": warranty_expiring[:5],
        }

    def get_valuation(self, as_of_date: date = None):
        """Recuperer la valorisation du parc."""
        if not as_of_date:
            as_of_date = date.today()

        stats = self.get_statistics()

        # Agreger par type
        by_type = {}
        assets = self.asset_repo.get_in_service()
        for asset in assets:
            t = asset.asset_type.value if asset.asset_type else "OTHER"
            if t not in by_type:
                by_type[t] = {
                    "count": 0,
                    "gross_value": Decimal("0"),
                    "accumulated_depreciation": Decimal("0"),
                    "net_book_value": Decimal("0"),
                }
            by_type[t]["count"] += 1
            by_type[t]["gross_value"] += asset.acquisition_cost or Decimal("0")
            by_type[t]["accumulated_depreciation"] += asset.accumulated_depreciation or Decimal("0")
            by_type[t]["net_book_value"] += asset.net_book_value or Decimal("0")

        # Convertir Decimal en float pour serialisation
        for t in by_type:
            by_type[t]["gross_value"] = float(by_type[t]["gross_value"])
            by_type[t]["accumulated_depreciation"] = float(by_type[t]["accumulated_depreciation"])
            by_type[t]["net_book_value"] = float(by_type[t]["net_book_value"])

        return {
            "valuation_date": as_of_date,
            "total_assets_count": stats["total_assets"],
            "total_gross_value": stats["total_gross_value"],
            "total_accumulated_depreciation": stats["total_accumulated_depreciation"],
            "total_net_book_value": stats["total_net_book_value"],
            "total_impairment": Decimal("0"),
            "total_revaluation_surplus": Decimal("0"),
            "by_asset_type": by_type,
            "currency": "EUR",
        }


# ============================================================================
# FACTORY
# ============================================================================

def get_asset_service(db: Session, tenant_id: UUID, user_id: UUID = None) -> AssetService:
    """Factory pour creer le service Assets."""
    return AssetService(db, tenant_id, user_id)
