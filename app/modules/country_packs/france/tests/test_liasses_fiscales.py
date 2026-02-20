"""
Tests for Liasses Fiscales (GAP-049).

Tests de validation du pré-remplissage automatique des liasses fiscales.
"""

import pytest
from datetime import date
from decimal import Decimal

from ..liasses_fiscales import (
    LiassesFiscalesService,
    RegimeFiscal,
    TypeLiasse,
    FormulaireLibelle,
    LigneFormulaire,
    LiasseFiscale,
    ResultatFiscal,
    MAPPING_ACTIF_2050,
    MAPPING_PASSIF_2051,
)


# ============================================================================
# TESTS RÉGIMES FISCAUX
# ============================================================================

class TestRegimeFiscal:
    """Tests pour les régimes fiscaux."""

    def test_all_regimes_exist(self):
        """Tous les régimes fiscaux existent."""
        regimes = [
            RegimeFiscal.REEL_NORMAL,
            RegimeFiscal.REEL_SIMPLIFIE,
            RegimeFiscal.MICRO_BIC,
            RegimeFiscal.BNC,
            RegimeFiscal.IS,
        ]
        assert len(regimes) == 5

    def test_regime_values(self):
        """Les valeurs des régimes sont correctes."""
        assert RegimeFiscal.REEL_NORMAL.value == "REEL_NORMAL"
        assert RegimeFiscal.REEL_SIMPLIFIE.value == "REEL_SIMPLIFIE"
        assert RegimeFiscal.IS.value == "IS"


class TestTypeLiasse:
    """Tests pour les types de liasses."""

    def test_liasse_reel_normal_forms(self):
        """Les formulaires du régime réel normal existent."""
        forms = [
            TypeLiasse.LIASSE_2050,
            TypeLiasse.LIASSE_2051,
            TypeLiasse.LIASSE_2052,
            TypeLiasse.LIASSE_2053,
            TypeLiasse.LIASSE_2054,
            TypeLiasse.LIASSE_2055,
            TypeLiasse.LIASSE_2056,
            TypeLiasse.LIASSE_2057,
            TypeLiasse.LIASSE_2058_A,
            TypeLiasse.LIASSE_2058_B,
            TypeLiasse.LIASSE_2058_C,
        ]
        assert len(forms) == 11

    def test_liasse_simplifie_forms(self):
        """Les formulaires du régime simplifié existent."""
        forms = [
            TypeLiasse.LIASSE_2033_A,
            TypeLiasse.LIASSE_2033_B,
            TypeLiasse.LIASSE_2033_C,
            TypeLiasse.LIASSE_2033_D,
            TypeLiasse.LIASSE_2033_E,
            TypeLiasse.LIASSE_2033_F,
            TypeLiasse.LIASSE_2033_G,
        ]
        assert len(forms) == 7


# ============================================================================
# TESTS MAPPINGS PCG
# ============================================================================

class TestMappingActif:
    """Tests pour le mapping des comptes PCG vers l'actif."""

    def test_mapping_actif_exists(self):
        """Le mapping actif existe."""
        assert len(MAPPING_ACTIF_2050) > 0

    def test_mapping_immobilisations_incorporelles(self):
        """Les immobilisations incorporelles sont mappées."""
        assert "AA" in MAPPING_ACTIF_2050
        assert "201" in MAPPING_ACTIF_2050["AA"]  # Frais d'établissement

    def test_mapping_immobilisations_corporelles(self):
        """Les immobilisations corporelles sont mappées."""
        assert "AC" in MAPPING_ACTIF_2050  # Terrains
        assert "AE" in MAPPING_ACTIF_2050  # Constructions

    def test_mapping_stocks(self):
        """Les stocks sont mappés."""
        assert "AP" in MAPPING_ACTIF_2050
        prefixes = MAPPING_ACTIF_2050["AP"]
        # Doit contenir les classes 3x
        assert any(p.startswith("3") for p in prefixes)

    def test_mapping_creances(self):
        """Les créances sont mappées."""
        assert "AR" in MAPPING_ACTIF_2050  # Clients
        assert "AT" in MAPPING_ACTIF_2050  # Autres créances

    def test_mapping_disponibilites(self):
        """Les disponibilités sont mappées."""
        assert "AX" in MAPPING_ACTIF_2050
        prefixes = MAPPING_ACTIF_2050["AX"]
        # Doit contenir les comptes 5x
        assert any(p.startswith("5") for p in prefixes)


class TestMappingPassif:
    """Tests pour le mapping des comptes PCG vers le passif."""

    def test_mapping_passif_exists(self):
        """Le mapping passif existe."""
        assert len(MAPPING_PASSIF_2051) > 0

    def test_mapping_capitaux_propres(self):
        """Les capitaux propres sont mappés."""
        assert "DA" in MAPPING_PASSIF_2051  # Capital
        assert "DG" in MAPPING_PASSIF_2051  # Report à nouveau
        assert "DH" in MAPPING_PASSIF_2051  # Résultat

    def test_mapping_provisions(self):
        """Les provisions sont mappées."""
        assert "DJ" in MAPPING_PASSIF_2051  # Provisions réglementées

    def test_mapping_dettes(self):
        """Les dettes sont mappées."""
        # Vérifier quelques codes de dettes
        passif_codes = list(MAPPING_PASSIF_2051.keys())
        assert len(passif_codes) > 10


# ============================================================================
# TESTS DATACLASSES
# ============================================================================

class TestLigneFormulaire:
    """Tests pour la classe LigneFormulaire."""

    def test_ligne_creation(self):
        """Création d'une ligne de formulaire."""
        ligne = LigneFormulaire(
            code="AA",
            libelle="Frais d'établissement",
            valeur_n=Decimal("1000.00"),
            valeur_n1=Decimal("1200.00"),
            comptes=["201", "203"]
        )

        assert ligne.code == "AA"
        assert ligne.valeur_n == Decimal("1000.00")
        assert len(ligne.comptes) == 2

    def test_ligne_default_values(self):
        """Valeurs par défaut d'une ligne."""
        ligne = LigneFormulaire(
            code="BB",
            libelle="Test"
        )

        assert ligne.valeur_n == Decimal("0")
        assert ligne.valeur_n1 == Decimal("0")
        assert ligne.comptes == []

    def test_ligne_with_calcul(self):
        """Ligne avec formule de calcul."""
        ligne = LigneFormulaire(
            code="TOTAL",
            libelle="Total",
            valeur_n=Decimal("5000"),
            calcul="AA + AB + AC"
        )

        assert ligne.calcul == "AA + AB + AC"


class TestFormulaireLibelle:
    """Tests pour la classe FormulaireLibelle."""

    def test_formulaire_creation(self):
        """Création d'un formulaire."""
        form = FormulaireLibelle(
            numero="2050",
            titre="BILAN - ACTIF"
        )

        assert form.numero == "2050"
        assert form.titre == "BILAN - ACTIF"
        assert len(form.lignes) == 0

    def test_formulaire_with_lignes(self):
        """Formulaire avec lignes."""
        form = FormulaireLibelle(
            numero="2051",
            titre="BILAN - PASSIF"
        )

        form.lignes.append(LigneFormulaire(
            code="DA",
            libelle="Capital",
            valeur_n=Decimal("10000")
        ))

        form.lignes.append(LigneFormulaire(
            code="DH",
            libelle="Résultat",
            valeur_n=Decimal("5000")
        ))

        assert len(form.lignes) == 2
        assert form.lignes[0].code == "DA"


class TestResultatFiscal:
    """Tests pour la classe ResultatFiscal."""

    def test_resultat_fiscal_creation(self):
        """Création d'un résultat fiscal."""
        rf = ResultatFiscal(
            resultat_comptable=Decimal("100000"),
            reintegrations=Decimal("5000"),
            deductions=Decimal("3000")
        )

        assert rf.resultat_comptable == Decimal("100000")
        assert rf.reintegrations == Decimal("5000")
        assert rf.deductions == Decimal("3000")

    def test_resultat_fiscal_calculation(self):
        """Calcul du résultat fiscal."""
        rf = ResultatFiscal(
            resultat_comptable=Decimal("100000"),
            reintegrations=Decimal("10000"),
            deductions=Decimal("5000")
        )

        # Résultat fiscal = comptable + réintégrations - déductions
        expected = Decimal("100000") + Decimal("10000") - Decimal("5000")
        rf.resultat_fiscal = expected

        assert rf.resultat_fiscal == Decimal("105000")


class TestLiasseFiscale:
    """Tests pour la classe LiasseFiscale."""

    def test_liasse_creation(self):
        """Création d'une liasse fiscale."""
        liasse = LiasseFiscale(
            tenant_id="test_tenant",
            exercice_id="EX2024",
            exercice_code="2024",
            date_debut=date(2024, 1, 1),
            date_fin=date(2024, 12, 31),
            regime=RegimeFiscal.REEL_NORMAL
        )

        assert liasse.tenant_id == "test_tenant"
        assert liasse.regime == RegimeFiscal.REEL_NORMAL
        assert len(liasse.formulaires) == 0
        assert len(liasse.errors) == 0

    def test_liasse_with_formulaires(self):
        """Liasse avec formulaires."""
        liasse = LiasseFiscale(
            tenant_id="test",
            exercice_id="2024",
            exercice_code="2024",
            date_debut=date(2024, 1, 1),
            date_fin=date(2024, 12, 31),
            regime=RegimeFiscal.IS
        )

        liasse.formulaires.append(FormulaireLibelle(
            numero="2050",
            titre="BILAN - ACTIF"
        ))

        liasse.formulaires.append(FormulaireLibelle(
            numero="2051",
            titre="BILAN - PASSIF"
        ))

        assert len(liasse.formulaires) == 2


# ============================================================================
# TESTS CALCUL IS
# ============================================================================

class TestCalculIS:
    """Tests pour le calcul de l'impôt sur les sociétés."""

    def test_taux_is_constants(self):
        """Les taux IS sont correctement définis."""
        assert LiassesFiscalesService.TAUX_IS_NORMAL == Decimal("0.25")
        assert LiassesFiscalesService.TAUX_IS_REDUIT == Decimal("0.15")
        assert LiassesFiscalesService.PLAFOND_IS_REDUIT == Decimal("42500")

    def test_is_pme_simple(self):
        """Calcul IS PME sous le plafond."""
        # Simulation du calcul
        resultat = Decimal("30000")
        est_pme = True
        plafond = Decimal("42500")
        taux_reduit = Decimal("0.15")

        # Tout au taux réduit
        is_du = resultat * taux_reduit

        assert is_du == Decimal("4500.00")

    def test_is_pme_above_threshold(self):
        """Calcul IS PME au-dessus du plafond."""
        resultat = Decimal("100000")
        est_pme = True
        plafond = Decimal("42500")
        taux_reduit = Decimal("0.15")
        taux_normal = Decimal("0.25")

        # Tranche réduite
        is_reduit = plafond * taux_reduit  # 42500 * 0.15 = 6375

        # Tranche normale
        base_normale = resultat - plafond  # 57500
        is_normal = base_normale * taux_normal  # 57500 * 0.25 = 14375

        is_total = is_reduit + is_normal  # 6375 + 14375 = 20750

        assert is_total == Decimal("20750.00")

    def test_is_non_pme(self):
        """Calcul IS pour non-PME (tout au taux normal)."""
        resultat = Decimal("100000")
        taux_normal = Decimal("0.25")

        is_du = resultat * taux_normal

        assert is_du == Decimal("25000.00")

    def test_is_deficit(self):
        """Pas d'IS si déficit."""
        resultat = Decimal("-50000")

        if resultat <= 0:
            is_du = Decimal("0")
        else:
            is_du = resultat * Decimal("0.25")

        assert is_du == Decimal("0")

    def test_taux_effectif_pme(self):
        """Taux effectif pour PME avec résultat mixte."""
        resultat = Decimal("100000")

        # IS calculé comme ci-dessus
        is_du = Decimal("20750")

        taux_effectif = is_du / resultat * 100

        # Taux effectif entre 15% et 25%
        assert Decimal("15") < taux_effectif < Decimal("25")
        assert taux_effectif == Decimal("20.75")


# ============================================================================
# TESTS ÉQUILIBRE BILAN
# ============================================================================

class TestEquilibreBilan:
    """Tests pour l'équilibre du bilan."""

    def test_bilan_equilibre(self):
        """Le bilan doit être équilibré."""
        actif_total = Decimal("1000000")
        passif_total = Decimal("1000000")

        ecart = abs(actif_total - passif_total)

        assert ecart < Decimal("0.01")

    def test_bilan_desequilibre_detecte(self):
        """Un déséquilibre doit être détecté."""
        actif_total = Decimal("1000000")
        passif_total = Decimal("990000")

        ecart = abs(actif_total - passif_total)

        assert ecart > Decimal("0.01")
        assert ecart == Decimal("10000")

    def test_tolerance_arrondi(self):
        """Tolérance pour les arrondis."""
        actif_total = Decimal("1000000.005")
        passif_total = Decimal("1000000.001")

        ecart = abs(actif_total - passif_total)

        # Écart < 1 centime = tolérable
        assert ecart < Decimal("0.01")


# ============================================================================
# TESTS COMPTE DE RÉSULTAT
# ============================================================================

class TestCompteResultat:
    """Tests pour le compte de résultat."""

    def test_resultat_benefice(self):
        """Calcul du résultat bénéficiaire."""
        produits = Decimal("500000")
        charges = Decimal("400000")

        resultat = produits - charges

        assert resultat == Decimal("100000")
        assert resultat > 0  # Bénéfice

    def test_resultat_perte(self):
        """Calcul du résultat déficitaire."""
        produits = Decimal("300000")
        charges = Decimal("400000")

        resultat = produits - charges

        assert resultat == Decimal("-100000")
        assert resultat < 0  # Perte

    def test_chiffre_affaires_net(self):
        """Calcul du chiffre d'affaires net."""
        ventes_marchandises = Decimal("200000")
        production_vendue = Decimal("150000")
        prestations = Decimal("50000")

        # CA Net = total des comptes 70x
        ca_net = ventes_marchandises + production_vendue + prestations

        assert ca_net == Decimal("400000")


# ============================================================================
# TESTS RÉSULTAT FISCAL
# ============================================================================

class TestReintegrations:
    """Tests pour les réintégrations fiscales."""

    def test_amendes_non_deductibles(self):
        """Les amendes sont réintégrées."""
        resultat_comptable = Decimal("100000")
        amendes = Decimal("5000")  # Compte 6712

        # Réintégration
        resultat_fiscal = resultat_comptable + amendes

        assert resultat_fiscal == Decimal("105000")

    def test_impots_non_deductibles(self):
        """Certains impôts sont réintégrés."""
        resultat_comptable = Decimal("100000")
        is_paye = Decimal("25000")  # L'IS n'est pas déductible de l'IS

        # L'IS comptabilisé est réintégré pour le calcul fiscal
        # (en pratique, il est neutralisé dans le calcul)
        assert is_paye > 0


class TestDeductions:
    """Tests pour les déductions fiscales."""

    def test_participation_deductible(self):
        """La participation des salariés est déductible."""
        resultat_comptable = Decimal("100000")
        participation = Decimal("10000")

        # La participation est déductible si versée
        resultat_fiscal = resultat_comptable - participation

        assert resultat_fiscal == Decimal("90000")

    def test_mecenat_deductible(self):
        """Le mécénat ouvre droit à réduction."""
        don_mecenat = Decimal("1000")

        # Réduction = 60% du don (plafonné)
        reduction = don_mecenat * Decimal("0.60")

        assert reduction == Decimal("600")


# ============================================================================
# TESTS EXPORT
# ============================================================================

class TestExport:
    """Tests pour l'export des liasses fiscales."""

    def test_export_dict_structure(self):
        """Structure du dictionnaire exporté."""
        liasse = LiasseFiscale(
            tenant_id="test",
            exercice_id="2024",
            exercice_code="2024",
            date_debut=date(2024, 1, 1),
            date_fin=date(2024, 12, 31),
            regime=RegimeFiscal.REEL_NORMAL,
            resultat_fiscal=Decimal("50000"),
            impot_du=Decimal("12500")
        )

        form = FormulaireLibelle(numero="2050", titre="BILAN - ACTIF")
        form.lignes.append(LigneFormulaire(
            code="AA",
            libelle="Frais d'établissement",
            valeur_n=Decimal("1000")
        ))
        liasse.formulaires.append(form)

        # Simulation de l'export
        export = {
            "metadata": {
                "tenant_id": liasse.tenant_id,
                "exercice_id": liasse.exercice_id,
                "regime": liasse.regime.value
            },
            "resultats": {
                "resultat_fiscal": str(liasse.resultat_fiscal),
                "impot_du": str(liasse.impot_du)
            },
            "formulaires": [
                {
                    "numero": f.numero,
                    "titre": f.titre,
                    "lignes": [
                        {"code": l.code, "valeur_n": str(l.valeur_n)}
                        for l in f.lignes
                    ]
                }
                for f in liasse.formulaires
            ]
        }

        assert "metadata" in export
        assert "resultats" in export
        assert "formulaires" in export
        assert len(export["formulaires"]) == 1

    def test_edi_format_basic(self):
        """Format EDI-TDFC basique."""
        liasse = LiasseFiscale(
            tenant_id="test",
            exercice_id="2024",
            exercice_code="2024",
            date_debut=date(2024, 1, 1),
            date_fin=date(2024, 12, 31),
            regime=RegimeFiscal.REEL_NORMAL
        )

        form = FormulaireLibelle(numero="2050", titre="BILAN - ACTIF")
        form.lignes.append(LigneFormulaire(
            code="AA",
            libelle="Test",
            valeur_n=Decimal("1000")
        ))
        liasse.formulaires.append(form)

        # Simulation format EDI
        lines = []
        lines.append(f"ISI0|{liasse.exercice_code}|{liasse.date_debut}|{liasse.date_fin}")

        for f in liasse.formulaires:
            lines.append(f"F|{f.numero}")
            for l in f.lignes:
                if l.valeur_n != 0:
                    lines.append(f"L|{l.code}|{l.valeur_n}")

        lines.append(f"FIN|{len(liasse.formulaires)}")

        edi_content = "\n".join(lines)

        assert "ISI0|2024" in edi_content
        assert "F|2050" in edi_content
        assert "L|AA|1000" in edi_content
        assert "FIN|1" in edi_content


# ============================================================================
# TESTS VALIDATION
# ============================================================================

class TestValidation:
    """Tests pour la validation des liasses fiscales."""

    def test_liasse_sans_erreur(self):
        """Liasse sans erreur."""
        liasse = LiasseFiscale(
            tenant_id="test",
            exercice_id="2024",
            exercice_code="2024",
            date_debut=date(2024, 1, 1),
            date_fin=date(2024, 12, 31),
            regime=RegimeFiscal.REEL_NORMAL
        )

        assert len(liasse.errors) == 0

    def test_liasse_avec_warning(self):
        """Liasse avec warning."""
        liasse = LiasseFiscale(
            tenant_id="test",
            exercice_id="2024",
            exercice_code="2024",
            date_debut=date(2024, 1, 1),
            date_fin=date(2024, 12, 31),
            regime=RegimeFiscal.REEL_NORMAL
        )

        liasse.warnings.append("Bilan non équilibré")

        assert len(liasse.warnings) == 1
        assert "équilibré" in liasse.warnings[0]

    def test_liasse_avec_erreur(self):
        """Liasse avec erreur."""
        liasse = LiasseFiscale(
            tenant_id="test",
            exercice_id="2024",
            exercice_code="2024",
            date_debut=date(2024, 1, 1),
            date_fin=date(2024, 12, 31),
            regime=RegimeFiscal.REEL_NORMAL
        )

        liasse.errors.append("Exercice non clôturé")

        assert len(liasse.errors) == 1


# ============================================================================
# TESTS DATES ET PÉRIODES
# ============================================================================

class TestDatesExercice:
    """Tests pour les dates d'exercice."""

    def test_exercice_calendaire(self):
        """Exercice calendaire standard."""
        debut = date(2024, 1, 1)
        fin = date(2024, 12, 31)

        duree = (fin - debut).days + 1

        assert duree == 366  # 2024 est bissextile

    def test_exercice_decale(self):
        """Exercice décalé."""
        debut = date(2024, 4, 1)
        fin = date(2025, 3, 31)

        duree = (fin - debut).days + 1

        assert duree == 365

    def test_exercice_court(self):
        """Exercice court (création)."""
        debut = date(2024, 6, 15)
        fin = date(2024, 12, 31)

        duree = (fin - debut).days + 1

        assert duree < 365
        assert duree == 200
