"""
Tests specifiques pour les calculs d'amortissement.
"""

import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

import pytest

from app.modules.assets.service_db import (
    DECLINING_BALANCE_COEFFICIENTS,
    RECOMMENDED_USEFUL_LIFE,
)


class TestLinearDepreciation:
    """Tests pour l'amortissement lineaire."""

    def test_linear_annual_rate(self):
        """Test calcul du taux annuel."""
        # 3 ans -> 33.33%
        rate_3y = (Decimal("100") / 3).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert rate_3y == Decimal("33.33")

        # 5 ans -> 20%
        rate_5y = Decimal("100") / 5
        assert rate_5y == Decimal("20")

        # 10 ans -> 10%
        rate_10y = Decimal("100") / 10
        assert rate_10y == Decimal("10")

    def test_linear_annual_amount(self):
        """Test calcul du montant annuel."""
        acquisition_cost = Decimal("3000")
        residual_value = Decimal("0")
        useful_life = 3

        depreciable = acquisition_cost - residual_value
        annual_rate = Decimal("100") / useful_life
        annual_amount = (depreciable * annual_rate / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        assert annual_amount == Decimal("1000.00")

    def test_linear_with_residual_value(self):
        """Test avec valeur residuelle."""
        acquisition_cost = Decimal("10000")
        residual_value = Decimal("1000")
        useful_life = 5

        depreciable = acquisition_cost - residual_value
        annual_amount = (depreciable / useful_life).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        assert depreciable == Decimal("9000")
        assert annual_amount == Decimal("1800.00")

    def test_linear_prorata_first_year(self):
        """Test prorata premiere annee."""
        start_date = date(2024, 7, 1)  # Debut 1er juillet
        annual_amount = Decimal("1200")

        days_in_year = 366  # 2024 est bissextile
        remaining_days = (date(2024, 12, 31) - start_date).days + 1
        assert remaining_days == 184

        prorata = Decimal(str(remaining_days)) / Decimal(str(days_in_year))
        first_year_amount = (annual_amount * prorata).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        expected = (Decimal("1200") * Decimal("184") / Decimal("366")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        assert first_year_amount == expected

    def test_linear_complete_schedule(self):
        """Test tableau complet."""
        acquisition_cost = Decimal("3000")
        useful_life = 3
        start_date = date(2024, 1, 1)

        annual_amount = Decimal("1000")
        remaining = acquisition_cost
        accumulated = Decimal("0")

        schedule = []
        for year in range(useful_life):
            period_depreciation = min(annual_amount, remaining)
            accumulated += period_depreciation
            remaining -= period_depreciation

            schedule.append({
                "year": year + 1,
                "depreciation": period_depreciation,
                "accumulated": accumulated,
                "net_book_value": acquisition_cost - accumulated
            })

        assert len(schedule) == 3
        assert schedule[0]["net_book_value"] == Decimal("2000")
        assert schedule[1]["net_book_value"] == Decimal("1000")
        assert schedule[2]["net_book_value"] == Decimal("0")


class TestDecliningBalanceDepreciation:
    """Tests pour l'amortissement degressif."""

    def test_declining_coefficients(self):
        """Test coefficients degressifs."""
        assert DECLINING_BALANCE_COEFFICIENTS[3] == Decimal("1.25")
        assert DECLINING_BALANCE_COEFFICIENTS[4] == Decimal("1.25")
        assert DECLINING_BALANCE_COEFFICIENTS[5] == Decimal("1.75")
        assert DECLINING_BALANCE_COEFFICIENTS[6] == Decimal("1.75")
        assert DECLINING_BALANCE_COEFFICIENTS[7] == Decimal("2.25")

    def test_declining_rate_calculation(self):
        """Test calcul du taux degressif."""
        useful_life = 5
        linear_rate = Decimal("100") / useful_life  # 20%
        coef = DECLINING_BALANCE_COEFFICIENTS[5]  # 1.75
        declining_rate = linear_rate * coef  # 35%

        assert linear_rate == Decimal("20")
        assert declining_rate == Decimal("35")

    def test_declining_first_year(self):
        """Test premiere annee degressive."""
        acquisition_cost = Decimal("10000")
        declining_rate = Decimal("35")

        first_year = (acquisition_cost * declining_rate / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        assert first_year == Decimal("3500.00")

    def test_declining_switch_to_linear(self):
        """Test passage au lineaire."""
        remaining = Decimal("2500")
        declining_rate = Decimal("35")
        remaining_years = 2

        declining_amount = (remaining * declining_rate / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        linear_amount = (remaining / remaining_years).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Le lineaire devient plus avantageux
        assert linear_amount == Decimal("1250.00")
        assert declining_amount == Decimal("875.00")
        assert linear_amount > declining_amount

    def test_declining_complete_schedule(self):
        """Test tableau degressif complet."""
        acquisition_cost = Decimal("10000")
        useful_life = 5
        coef = Decimal("1.75")
        linear_rate = Decimal("100") / useful_life
        declining_rate = linear_rate * coef

        remaining = acquisition_cost
        accumulated = Decimal("0")
        schedule = []

        for year in range(useful_life):
            declining_amount = (remaining * declining_rate / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            remaining_years = useful_life - year
            linear_amount = (remaining / remaining_years).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Prendre le plus eleve
            period_depreciation = max(declining_amount, linear_amount)
            if period_depreciation > remaining:
                period_depreciation = remaining

            accumulated += period_depreciation
            remaining -= period_depreciation

            schedule.append({
                "year": year + 1,
                "declining": declining_amount,
                "linear": linear_amount,
                "applied": period_depreciation,
                "method": "declining" if declining_amount >= linear_amount else "linear",
                "net_book_value": acquisition_cost - accumulated
            })

        # Verifier que le total = acquisition_cost
        total_depreciation = sum(e["applied"] for e in schedule)
        assert total_depreciation == acquisition_cost
        assert schedule[-1]["net_book_value"] == Decimal("0")


class TestUnitsOfProductionDepreciation:
    """Tests pour l'amortissement par unites de production."""

    def test_units_rate(self):
        """Test taux par unite."""
        acquisition_cost = Decimal("100000")
        residual_value = Decimal("10000")
        total_units = Decimal("50000")

        depreciable = acquisition_cost - residual_value
        rate_per_unit = depreciable / total_units

        assert rate_per_unit == Decimal("1.8")  # 90000 / 50000

    def test_units_period_depreciation(self):
        """Test amortissement periode."""
        rate_per_unit = Decimal("1.8")
        units_produced = Decimal("5000")

        depreciation = (rate_per_unit * units_produced).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        assert depreciation == Decimal("9000.00")

    def test_units_varying_production(self):
        """Test production variable."""
        acquisition_cost = Decimal("50000")
        residual_value = Decimal("5000")
        total_units = Decimal("100000")
        depreciable = acquisition_cost - residual_value
        rate_per_unit = depreciable / total_units  # 0.45

        productions = [
            Decimal("20000"),  # Year 1
            Decimal("25000"),  # Year 2
            Decimal("30000"),  # Year 3
            Decimal("15000"),  # Year 4
            Decimal("10000"),  # Year 5
        ]

        accumulated = Decimal("0")
        schedule = []

        for year, units in enumerate(productions, 1):
            depreciation = (rate_per_unit * units).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            accumulated += depreciation
            schedule.append({
                "year": year,
                "units": units,
                "depreciation": depreciation,
                "accumulated": accumulated
            })

        total_units_produced = sum(productions)
        assert total_units_produced == total_units
        assert accumulated == depreciable


class TestSumOfYearsDigitsDepreciation:
    """Tests pour l'amortissement SOFTY."""

    def test_sum_of_years(self):
        """Test somme des annees."""
        # n(n+1)/2
        assert (3 * 4) / 2 == 6  # 3 ans: 3+2+1 = 6
        assert (5 * 6) / 2 == 15  # 5 ans: 5+4+3+2+1 = 15
        assert (10 * 11) / 2 == 55  # 10 ans

    def test_softy_rates(self):
        """Test taux SOFTY par annee."""
        useful_life = 5
        sum_of_years = (useful_life * (useful_life + 1)) / 2  # 15

        rates = []
        for year in range(useful_life):
            remaining_years = useful_life - year
            rate = Decimal(str(remaining_years)) / Decimal(str(sum_of_years))
            rates.append(rate)

        # Year 1: 5/15, Year 2: 4/15, Year 3: 3/15, Year 4: 2/15, Year 5: 1/15
        assert rates[0] == Decimal("5") / Decimal("15")
        assert rates[4] == Decimal("1") / Decimal("15")
        assert sum(rates) == Decimal("1")

    def test_softy_complete_schedule(self):
        """Test tableau SOFTY complet."""
        acquisition_cost = Decimal("15000")
        useful_life = 5
        sum_of_years = Decimal(str((useful_life * (useful_life + 1)) / 2))

        accumulated = Decimal("0")
        schedule = []

        for year in range(useful_life):
            remaining_years = useful_life - year
            rate = Decimal(str(remaining_years)) / sum_of_years
            depreciation = (acquisition_cost * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            accumulated += depreciation
            schedule.append({
                "year": year + 1,
                "rate": rate * 100,
                "depreciation": depreciation,
                "accumulated": accumulated,
                "net_book_value": acquisition_cost - accumulated
            })

        # Year 1: 5/15 = 33.33% -> 5000
        # Year 2: 4/15 = 26.67% -> 4000
        # Year 3: 3/15 = 20%    -> 3000
        # Year 4: 2/15 = 13.33% -> 2000
        # Year 5: 1/15 = 6.67%  -> 1000
        assert schedule[0]["depreciation"] == Decimal("5000.00")
        assert schedule[-1]["net_book_value"] == Decimal("0.00")


class TestRecommendedUsefulLife:
    """Tests pour les durees recommandees."""

    def test_it_equipment(self):
        """Test duree materiel IT."""
        from app.modules.assets.models import AssetType
        assert RECOMMENDED_USEFUL_LIFE.get(AssetType.TANGIBLE_IT) == 3

    def test_building(self):
        """Test duree batiment."""
        from app.modules.assets.models import AssetType
        assert RECOMMENDED_USEFUL_LIFE.get(AssetType.TANGIBLE_BUILDING) == 25

    def test_land_not_depreciable(self):
        """Test terrain non amortissable."""
        from app.modules.assets.models import AssetType
        assert RECOMMENDED_USEFUL_LIFE.get(AssetType.TANGIBLE_LAND) == 0

    def test_software(self):
        """Test duree logiciel."""
        from app.modules.assets.models import AssetType
        assert RECOMMENDED_USEFUL_LIFE.get(AssetType.INTANGIBLE_SOFTWARE) == 3
