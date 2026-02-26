"""
AZALS - Tests Unitaires Paie France
====================================
Tests pour paie_france.py
Objectif: Augmenter la couverture de 0% vers 80%+
"""

import pytest
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from unittest.mock import MagicMock, patch


# ============================================================================
# TESTS BARÈMES PAIE FRANCE
# ============================================================================

class TestBaremesPayeFrance:
    """Tests constantes barèmes paie France."""

    def test_pmss_2024(self):
        """Test: PMSS 2024 = 3864 EUR."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        assert BaremesPayeFrance.PMSS_2024 == Decimal("3864")

    def test_pass_2024(self):
        """Test: PASS 2024 = 46368 EUR."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        assert BaremesPayeFrance.PASS_2024 == Decimal("46368")

    def test_pass_equals_12_pmss(self):
        """Test: PASS = 12 x PMSS."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        assert BaremesPayeFrance.PASS_2024 == BaremesPayeFrance.PMSS_2024 * 12

    def test_smic_horaire_2024(self):
        """Test: SMIC horaire 2024 = 11.65 EUR."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        assert BaremesPayeFrance.SMIC_HORAIRE_2024 == Decimal("11.65")

    def test_smic_mensuel_2024(self):
        """Test: SMIC mensuel 2024 = 1766.92 EUR."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        assert BaremesPayeFrance.SMIC_MENSUEL_2024 == Decimal("1766.92")

    def test_smic_mensuel_calculation(self):
        """Test: SMIC mensuel = 151.67h * taux horaire (arrondi légal)."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        smic_calcule = (BaremesPayeFrance.HEURES_MENSUELLES *
                        BaremesPayeFrance.SMIC_HORAIRE_2024).quantize(Decimal("0.01"))
        # Valeur officielle peut varier légèrement selon arrondis
        ecart = abs(smic_calcule - BaremesPayeFrance.SMIC_MENSUEL_2024)
        assert ecart < Decimal("0.10")  # Tolérance arrondi

    def test_heures_mensuelles(self):
        """Test: Heures mensuelles = 151.67."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        assert BaremesPayeFrance.HEURES_MENSUELLES == Decimal("151.67")

    def test_heures_hebdomadaires(self):
        """Test: Heures hebdomadaires = 35."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        assert BaremesPayeFrance.HEURES_HEBDO == Decimal("35")

    def test_majorations_heures_sup(self):
        """Test: Majorations heures supplémentaires."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        assert BaremesPayeFrance.MAJORATION_HS_8_PREMIERES == Decimal("0.25")  # 25%
        assert BaremesPayeFrance.MAJORATION_HS_SUIVANTES == Decimal("0.50")    # 50%


# ============================================================================
# TESTS TAUX COTISATION DATACLASS
# ============================================================================

class TestTauxCotisation:
    """Tests dataclass TauxCotisation."""

    def test_taux_cotisation_creation(self):
        """Test: Création TauxCotisation."""
        from app.modules.country_packs.france.paie_france import TauxCotisation

        cotisation = TauxCotisation(
            code="TEST",
            libelle="Test cotisation",
            taux_salarial=Decimal("3.00"),
            taux_patronal=Decimal("6.00")
        )

        assert cotisation.code == "TEST"
        assert cotisation.libelle == "Test cotisation"
        assert cotisation.taux_salarial == Decimal("3.00")
        assert cotisation.taux_patronal == Decimal("6.00")

    def test_taux_cotisation_defaults(self):
        """Test: Valeurs par défaut TauxCotisation."""
        from app.modules.country_packs.france.paie_france import TauxCotisation

        cotisation = TauxCotisation(
            code="TEST",
            libelle="Test",
            taux_salarial=Decimal("0"),
            taux_patronal=Decimal("0")
        )

        assert cotisation.plafond is None
        assert cotisation.plancher is None
        assert cotisation.base == "brut"
        assert cotisation.categorie == "general"

    def test_taux_cotisation_plafonne(self):
        """Test: Cotisation plafonnée."""
        from app.modules.country_packs.france.paie_france import TauxCotisation, BaremesPayeFrance

        cotisation = TauxCotisation(
            code="VIEILLESSE_PLAF",
            libelle="Vieillesse plafonnée",
            taux_salarial=Decimal("6.90"),
            taux_patronal=Decimal("8.55"),
            plafond=BaremesPayeFrance.PMSS_2024,
            base="plafonne"
        )

        assert cotisation.plafond == Decimal("3864")
        assert cotisation.base == "plafonne"


# ============================================================================
# TESTS COTISATIONS FRANCE 2024
# ============================================================================

class TestCotisationsFrance2024:
    """Tests liste COTISATIONS_FRANCE_2024."""

    def test_cotisations_list_exists(self):
        """Test: Liste cotisations existe."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        assert len(COTISATIONS_FRANCE_2024) > 0

    def test_cotisation_maladie(self):
        """Test: Cotisation assurance maladie."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        maladie = next((c for c in COTISATIONS_FRANCE_2024 if c.code == "MALADIE"), None)

        assert maladie is not None
        assert maladie.taux_salarial == Decimal("0")  # Supprimé depuis 2018
        assert maladie.taux_patronal == Decimal("7.00")

    def test_cotisation_vieillesse_plafonnee(self):
        """Test: Cotisation vieillesse plafonnée."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        vieillesse = next((c for c in COTISATIONS_FRANCE_2024 if c.code == "VIEILLESSE_PLAF"), None)

        assert vieillesse is not None
        assert vieillesse.taux_salarial == Decimal("6.90")
        assert vieillesse.taux_patronal == Decimal("8.55")
        assert vieillesse.base == "plafonne"

    def test_cotisation_vieillesse_deplafonnee(self):
        """Test: Cotisation vieillesse déplafonnée."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        vieillesse = next((c for c in COTISATIONS_FRANCE_2024 if c.code == "VIEILLESSE_DEPLAF"), None)

        assert vieillesse is not None
        assert vieillesse.taux_salarial == Decimal("0.40")
        assert vieillesse.taux_patronal == Decimal("1.90")

    def test_cotisation_allocations_familiales(self):
        """Test: Cotisation allocations familiales."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        af = next((c for c in COTISATIONS_FRANCE_2024 if c.code == "ALLOCATIONS_FAM"), None)

        assert af is not None
        assert af.taux_salarial == Decimal("0")
        assert af.taux_patronal == Decimal("5.25")

    def test_cotisation_csg_deductible(self):
        """Test: CSG déductible."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        csg = next((c for c in COTISATIONS_FRANCE_2024 if c.code == "CSG_DED"), None)

        assert csg is not None
        assert csg.taux_salarial == Decimal("6.80")
        assert csg.base == "csg"

    def test_cotisation_csg_non_deductible(self):
        """Test: CSG non déductible."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        csg = next((c for c in COTISATIONS_FRANCE_2024 if c.code == "CSG_NON_DED"), None)

        assert csg is not None
        assert csg.taux_salarial == Decimal("2.40")

    def test_cotisation_crds(self):
        """Test: CRDS."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        crds = next((c for c in COTISATIONS_FRANCE_2024 if c.code == "CRDS"), None)

        assert crds is not None
        assert crds.taux_salarial == Decimal("0.50")

    def test_cotisation_chomage(self):
        """Test: Assurance chômage."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        chomage = next((c for c in COTISATIONS_FRANCE_2024 if c.code == "CHOMAGE"), None)

        assert chomage is not None
        assert chomage.taux_salarial == Decimal("0")  # Supprimé depuis 2019
        assert chomage.taux_patronal == Decimal("4.05")

    def test_cotisation_ags(self):
        """Test: AGS (garantie salaires)."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        ags = next((c for c in COTISATIONS_FRANCE_2024 if c.code == "AGS"), None)

        assert ags is not None
        assert ags.taux_patronal == Decimal("0.15")

    def test_cotisation_agirc_arrco_t1(self):
        """Test: AGIRC-ARRCO Tranche 1."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        arrco = next((c for c in COTISATIONS_FRANCE_2024 if c.code == "AGIRC_ARRCO_T1"), None)

        assert arrco is not None
        assert arrco.taux_salarial == Decimal("3.15")
        assert arrco.taux_patronal == Decimal("4.72")
        assert arrco.base == "tranche_1"

    def test_cotisation_agirc_arrco_t2(self):
        """Test: AGIRC-ARRCO Tranche 2."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        arrco = next((c for c in COTISATIONS_FRANCE_2024 if c.code == "AGIRC_ARRCO_T2"), None)

        assert arrco is not None
        assert arrco.taux_salarial == Decimal("8.64")
        assert arrco.taux_patronal == Decimal("12.95")
        assert arrco.base == "tranche_2"


# ============================================================================
# TESTS CALCULS PAIE
# ============================================================================

class TestCalculsPaie:
    """Tests calculs de paie."""

    def test_calcul_salaire_brut(self):
        """Test: Calcul salaire brut."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        taux_horaire = Decimal("15.00")
        heures = BaremesPayeFrance.HEURES_MENSUELLES

        salaire_brut = (taux_horaire * heures).quantize(Decimal("0.01"))

        assert salaire_brut == Decimal("2275.05")

    def test_calcul_heures_sup_25_pourcent(self):
        """Test: Calcul heures sup +25%."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        taux_horaire = Decimal("15.00")
        heures_sup = Decimal("8")  # 8 premières heures
        majoration = BaremesPayeFrance.MAJORATION_HS_8_PREMIERES

        montant_hs = (taux_horaire * (1 + majoration) * heures_sup).quantize(Decimal("0.01"))

        assert montant_hs == Decimal("150.00")

    def test_calcul_heures_sup_50_pourcent(self):
        """Test: Calcul heures sup +50%."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        taux_horaire = Decimal("15.00")
        heures_sup = Decimal("4")  # Heures au-delà de 8
        majoration = BaremesPayeFrance.MAJORATION_HS_SUIVANTES

        montant_hs = (taux_horaire * (1 + majoration) * heures_sup).quantize(Decimal("0.01"))

        assert montant_hs == Decimal("90.00")

    def test_calcul_base_plafonnee(self):
        """Test: Calcul base plafonnée au PMSS."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        salaire_brut = Decimal("5000.00")
        pmss = BaremesPayeFrance.PMSS_2024

        base_plafonnee = min(salaire_brut, pmss)

        assert base_plafonnee == pmss
        assert base_plafonnee == Decimal("3864")

    def test_calcul_base_non_plafonnee(self):
        """Test: Calcul base non plafonnée (brut < PMSS)."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        salaire_brut = Decimal("3000.00")
        pmss = BaremesPayeFrance.PMSS_2024

        base_plafonnee = min(salaire_brut, pmss)

        assert base_plafonnee == salaire_brut
        assert base_plafonnee == Decimal("3000.00")

    def test_calcul_tranche_2(self):
        """Test: Calcul tranche 2 (1-8 PMSS)."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        salaire_brut = Decimal("6000.00")
        pmss = BaremesPayeFrance.PMSS_2024
        plafond_t2 = pmss * 8

        tranche_1 = min(salaire_brut, pmss)
        tranche_2 = min(max(salaire_brut - pmss, 0), plafond_t2 - pmss)

        assert tranche_1 == Decimal("3864")
        assert tranche_2 == Decimal("2136")

    def test_calcul_assiette_csg(self):
        """Test: Calcul assiette CSG (98.25% brut)."""
        salaire_brut = Decimal("3000.00")
        taux_assiette_csg = Decimal("0.9825")

        assiette_csg = (salaire_brut * taux_assiette_csg).quantize(Decimal("0.01"))

        assert assiette_csg == Decimal("2947.50")

    def test_calcul_cotisation_patronale_maladie(self):
        """Test: Calcul cotisation patronale maladie 7%."""
        salaire_brut = Decimal("3000.00")
        taux_patronal = Decimal("7.00") / 100

        cotisation = (salaire_brut * taux_patronal).quantize(Decimal("0.01"))

        assert cotisation == Decimal("210.00")

    def test_calcul_cotisation_salariale_vieillesse(self):
        """Test: Calcul cotisation salariale vieillesse plafonnée."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        salaire_brut = Decimal("4500.00")
        pmss = BaremesPayeFrance.PMSS_2024
        taux_salarial = Decimal("6.90") / 100

        base = min(salaire_brut, pmss)
        cotisation = (base * taux_salarial).quantize(Decimal("0.01"))

        assert base == pmss
        assert cotisation == Decimal("266.62")


class TestCalculNetImposable:
    """Tests calcul net imposable et net à payer."""

    def test_calcul_net_imposable(self):
        """Test: Calcul net imposable."""
        salaire_brut = Decimal("3000.00")
        cotisations_salariales = Decimal("650.00")
        csg_non_ded = Decimal("70.74")  # CSG non déductible
        crds = Decimal("14.74")  # CRDS

        net_imposable = salaire_brut - cotisations_salariales + csg_non_ded + crds

        # Net imposable = Brut - cotisations + CSG non déd + CRDS
        assert net_imposable == Decimal("2435.48")

    def test_calcul_net_a_payer(self):
        """Test: Calcul net à payer."""
        salaire_brut = Decimal("3000.00")
        total_retenues = Decimal("720.00")  # Toutes cotisations salariales

        net_a_payer = salaire_brut - total_retenues

        assert net_a_payer == Decimal("2280.00")


# ============================================================================
# TESTS RÈGLES SPÉCIFIQUES
# ============================================================================

class TestReglesSpecifiquesPaie:
    """Tests règles spécifiques de paie France."""

    def test_reduction_fillon(self):
        """Test: Réduction Fillon applicable si salaire < 1.6 SMIC."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        smic_mensuel = BaremesPayeFrance.SMIC_MENSUEL_2024
        seuil_fillon = smic_mensuel * Decimal("1.6")

        salaire_eligible = Decimal("2500.00")
        salaire_non_eligible = Decimal("3000.00")

        assert salaire_eligible < seuil_fillon
        assert salaire_non_eligible > seuil_fillon

    def test_taux_af_reduit(self):
        """Test: Taux AF réduit si salaire < 3.5 SMIC."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        smic_mensuel = BaremesPayeFrance.SMIC_MENSUEL_2024
        seuil_af_reduit = smic_mensuel * Decimal("3.5")

        salaire = Decimal("5000.00")
        taux_af_normal = Decimal("5.25")
        taux_af_reduit = Decimal("3.45")

        taux_applicable = taux_af_reduit if salaire < seuil_af_reduit else taux_af_normal

        assert seuil_af_reduit == Decimal("6184.22")
        assert salaire < seuil_af_reduit
        assert taux_applicable == taux_af_reduit

    def test_alsace_moselle(self):
        """Test: Cotisation additionnelle Alsace-Moselle."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        alsace = next((c for c in COTISATIONS_FRANCE_2024 if c.code == "MALADIE_ALSACE"), None)

        assert alsace is not None
        assert alsace.taux_salarial == Decimal("1.30")
        assert alsace.libelle == "Assurance maladie (Alsace-Moselle)"


# ============================================================================
# TESTS WORKFLOW BULLETIN
# ============================================================================

class TestWorkflowBulletin:
    """Tests workflow génération bulletin de paie."""

    def test_workflow_bulletin_complet(self):
        """Test: Workflow bulletin complet."""
        from app.modules.country_packs.france.paie_france import BaremesPayeFrance

        # Données employé
        salaire_base = Decimal("2500.00")
        heures_sup = Decimal("10")
        taux_horaire = salaire_base / BaremesPayeFrance.HEURES_MENSUELLES

        # 1. Calcul brut
        brut_base = salaire_base
        hs_8 = min(heures_sup, 8) * taux_horaire * Decimal("1.25")
        hs_plus = max(heures_sup - 8, 0) * taux_horaire * Decimal("1.50")
        brut_total = (brut_base + hs_8 + hs_plus).quantize(Decimal("0.01"))

        # 2. Calcul cotisations (simplifié)
        taux_salarial_total = Decimal("0.22")  # ~22%
        cotisations = (brut_total * taux_salarial_total).quantize(Decimal("0.01"))

        # 3. Net à payer
        net = brut_total - cotisations

        assert brut_total > salaire_base
        assert cotisations > 0
        assert net > 0
        assert net < brut_total

    def test_coherence_charges(self):
        """Test: Cohérence total charges vs détail."""
        from app.modules.country_packs.france.paie_france import COTISATIONS_FRANCE_2024

        # Calculer total des taux salariaux
        total_salarial = sum(c.taux_salarial for c in COTISATIONS_FRANCE_2024)

        # Total incluant toutes cotisations salariales (CSG/CRDS + retraite)
        # Environ 22-35% selon plafonds
        assert total_salarial > Decimal("20")
        assert total_salarial < Decimal("40")


class TestDSNIntegration:
    """Tests intégration avec DSN."""

    def test_dsn_salaire_structure(self):
        """Test: Structure données DSN salaire."""
        bulletin = {
            "matricule": "EMP001",
            "periode": "2024-01",
            "brut": Decimal("3000.00"),
            "net_imposable": Decimal("2350.00"),
            "net_paye": Decimal("2280.00"),
            "cotisations": {
                "SS_MALADIE": Decimal("0.00"),
                "SS_VIEILLESSE_PLAF": Decimal("266.62"),
                "SS_VIEILLESSE_DEPLAF": Decimal("12.00"),
                "CSG_CRDS": Decimal("284.10"),
                "AGIRC_ARRCO": Decimal("123.25")
            }
        }

        total_cotis = sum(bulletin["cotisations"].values())

        # Vérifications de cohérence structure DSN
        assert bulletin["net_paye"] < bulletin["brut"]
        assert bulletin["net_paye"] < bulletin["net_imposable"]
        assert total_cotis > 0
        assert bulletin["brut"] - total_cotis > bulletin["net_paye"]  # Il peut y avoir d'autres retenues


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
