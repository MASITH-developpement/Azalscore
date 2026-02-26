"""
AZALSCORE - Service de Paie France
===================================
Calcul des cotisations sociales et génération des bulletins de paie
conformément à la législation française.

Références:
- Code de la Sécurité Sociale
- Code du Travail
- Convention Collective applicable
- BOI-RSA-BASE-30
- Bulletins officiels de la Sécurité Sociale

Taux 2024-2025:
- PMSS (Plafond Mensuel Sécurité Sociale): 3 864 EUR (2024)
- SMIC horaire: 11,65 EUR (2024)
"""
from __future__ import annotations


import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTES ET BARÈMES 2024-2025
# ============================================================================

class BaremesPayeFrance:
    """Barèmes de paie France - Mis à jour janvier 2024."""

    # Plafonds Sécurité Sociale
    PMSS_2024 = Decimal("3864")   # Plafond Mensuel SS 2024
    PASS_2024 = Decimal("46368")  # Plafond Annuel SS 2024

    # SMIC
    SMIC_HORAIRE_2024 = Decimal("11.65")
    SMIC_MENSUEL_2024 = Decimal("1766.92")  # 151.67h * 11.65

    # Durée légale du travail
    HEURES_MENSUELLES = Decimal("151.67")
    HEURES_HEBDO = Decimal("35")

    # Majorations heures supplémentaires
    MAJORATION_HS_8_PREMIERES = Decimal("0.25")  # 25% pour les 8 premières heures
    MAJORATION_HS_SUIVANTES = Decimal("0.50")    # 50% au-delà


# ============================================================================
# COTISATIONS SOCIALES FRANCE 2024
# ============================================================================

@dataclass
class TauxCotisation:
    """Définition d'une cotisation sociale."""
    code: str
    libelle: str
    taux_salarial: Decimal
    taux_patronal: Decimal
    plafond: Decimal | None = None  # None = pas de plafond (totalité)
    plancher: Decimal | None = None  # Pour cotisations à tranches
    base: str = "brut"  # brut, plafonne, tranche_1, tranche_2, etc.
    categorie: str = "general"  # general, cadre, non_cadre


# Cotisations 2024 (taux en pourcentage - à diviser par 100 pour calcul)
COTISATIONS_FRANCE_2024 = [
    # ===============================================
    # SÉCURITÉ SOCIALE
    # ===============================================

    # Assurance maladie, maternité, invalidité, décès
    TauxCotisation(
        code="MALADIE",
        libelle="Assurance maladie",
        taux_salarial=Decimal("0"),  # Supprimé depuis 2018
        taux_patronal=Decimal("7.00"),
        base="brut"
    ),
    TauxCotisation(
        code="MALADIE_ALSACE",
        libelle="Assurance maladie (Alsace-Moselle)",
        taux_salarial=Decimal("1.30"),  # Cotisation additionnelle Alsace-Moselle
        taux_patronal=Decimal("0"),
        base="brut"
    ),

    # Contribution solidarité autonomie (CSA)
    TauxCotisation(
        code="CSA",
        libelle="Contribution Solidarité Autonomie",
        taux_salarial=Decimal("0"),
        taux_patronal=Decimal("0.30"),
        base="brut"
    ),

    # Assurance vieillesse plafonnée
    TauxCotisation(
        code="VIEILLESSE_PLAF",
        libelle="Assurance vieillesse plafonnée",
        taux_salarial=Decimal("6.90"),
        taux_patronal=Decimal("8.55"),
        plafond=BaremesPayeFrance.PMSS_2024,
        base="plafonne"
    ),

    # Assurance vieillesse déplafonnée
    TauxCotisation(
        code="VIEILLESSE_DEPLAF",
        libelle="Assurance vieillesse déplafonnée",
        taux_salarial=Decimal("0.40"),
        taux_patronal=Decimal("1.90"),
        base="brut"
    ),

    # Allocations familiales
    TauxCotisation(
        code="ALLOCATIONS_FAM",
        libelle="Allocations familiales",
        taux_salarial=Decimal("0"),
        taux_patronal=Decimal("5.25"),  # Taux réduit 3.45% si salaire < 3.5 SMIC
        base="brut"
    ),

    # Accidents du travail (taux variable par entreprise)
    TauxCotisation(
        code="AT_MP",
        libelle="Accidents du travail / Maladies prof.",
        taux_salarial=Decimal("0"),
        taux_patronal=Decimal("2.00"),  # Taux moyen - variable selon entreprise
        base="brut"
    ),

    # ===============================================
    # CSG / CRDS
    # ===============================================

    # CSG déductible (98.25% de l'assiette)
    TauxCotisation(
        code="CSG_DED",
        libelle="CSG déductible",
        taux_salarial=Decimal("6.80"),
        taux_patronal=Decimal("0"),
        base="csg"  # 98.25% du brut + patronales
    ),

    # CSG non déductible
    TauxCotisation(
        code="CSG_NON_DED",
        libelle="CSG non déductible",
        taux_salarial=Decimal("2.40"),
        taux_patronal=Decimal("0"),
        base="csg"
    ),

    # CRDS
    TauxCotisation(
        code="CRDS",
        libelle="CRDS",
        taux_salarial=Decimal("0.50"),
        taux_patronal=Decimal("0"),
        base="csg"
    ),

    # ===============================================
    # CHÔMAGE
    # ===============================================

    # Assurance chômage
    TauxCotisation(
        code="CHOMAGE",
        libelle="Assurance chômage",
        taux_salarial=Decimal("0"),  # Supprimé depuis 2019
        taux_patronal=Decimal("4.05"),
        plafond=Decimal("4") * BaremesPayeFrance.PMSS_2024,
        base="plafonne"
    ),

    # AGS (Assurance Garantie des Salaires)
    TauxCotisation(
        code="AGS",
        libelle="AGS (Garantie des salaires)",
        taux_salarial=Decimal("0"),
        taux_patronal=Decimal("0.15"),
        plafond=Decimal("4") * BaremesPayeFrance.PMSS_2024,
        base="plafonne"
    ),

    # ===============================================
    # RETRAITE COMPLÉMENTAIRE AGIRC-ARRCO
    # ===============================================

    # Tranche 1 (jusqu'à 1 PMSS)
    TauxCotisation(
        code="AGIRC_ARRCO_T1",
        libelle="Retraite complémentaire T1",
        taux_salarial=Decimal("3.15"),
        taux_patronal=Decimal("4.72"),
        plafond=BaremesPayeFrance.PMSS_2024,
        base="tranche_1"
    ),

    # Tranche 2 (de 1 à 8 PMSS)
    TauxCotisation(
        code="AGIRC_ARRCO_T2",
        libelle="Retraite complémentaire T2",
        taux_salarial=Decimal("8.64"),
        taux_patronal=Decimal("12.95"),
        plancher=BaremesPayeFrance.PMSS_2024,
        plafond=Decimal("8") * BaremesPayeFrance.PMSS_2024,
        base="tranche_2"
    ),

    # Contribution d'Équilibre Général (CEG) T1
    TauxCotisation(
        code="CEG_T1",
        libelle="CEG Tranche 1",
        taux_salarial=Decimal("0.86"),
        taux_patronal=Decimal("1.29"),
        plafond=BaremesPayeFrance.PMSS_2024,
        base="tranche_1"
    ),

    # CEG T2
    TauxCotisation(
        code="CEG_T2",
        libelle="CEG Tranche 2",
        taux_salarial=Decimal("1.08"),
        taux_patronal=Decimal("1.62"),
        plancher=BaremesPayeFrance.PMSS_2024,
        plafond=Decimal("8") * BaremesPayeFrance.PMSS_2024,
        base="tranche_2"
    ),

    # Contribution d'Équilibre Technique (CET) - si salaire > PMSS
    TauxCotisation(
        code="CET",
        libelle="Contribution Équilibre Technique",
        taux_salarial=Decimal("0.14"),
        taux_patronal=Decimal("0.21"),
        plancher=BaremesPayeFrance.PMSS_2024,
        base="cet"  # Totalité si > PMSS
    ),

    # ===============================================
    # PRÉVOYANCE CADRES (Article 4bis CCN 1947)
    # ===============================================

    TauxCotisation(
        code="PREVOYANCE_CADRE",
        libelle="Prévoyance cadres (art. 4bis)",
        taux_salarial=Decimal("0"),
        taux_patronal=Decimal("1.50"),
        plafond=BaremesPayeFrance.PMSS_2024,
        base="tranche_1",
        categorie="cadre"
    ),

    # ===============================================
    # CONTRIBUTION AU DIALOGUE SOCIAL
    # ===============================================

    TauxCotisation(
        code="CDS",
        libelle="Contribution au dialogue social",
        taux_salarial=Decimal("0"),
        taux_patronal=Decimal("0.016"),
        base="brut"
    ),

    # ===============================================
    # FORMATION PROFESSIONNELLE
    # ===============================================

    TauxCotisation(
        code="FORMATION_PRO",
        libelle="Formation professionnelle",
        taux_salarial=Decimal("0"),
        taux_patronal=Decimal("1.00"),  # 0.55% si < 11 salariés
        base="brut"
    ),

    # Taxe d'apprentissage
    TauxCotisation(
        code="TAXE_APPRENTISSAGE",
        libelle="Taxe d'apprentissage",
        taux_salarial=Decimal("0"),
        taux_patronal=Decimal("0.68"),
        base="brut"
    ),

    # CPF-CDD (1% sur CDD)
    TauxCotisation(
        code="CPF_CDD",
        libelle="CPF CDD",
        taux_salarial=Decimal("0"),
        taux_patronal=Decimal("1.00"),
        base="brut",
        categorie="cdd"
    ),

    # ===============================================
    # VERSEMENT MOBILITÉ (ex-transport)
    # ===============================================

    TauxCotisation(
        code="VERSEMENT_MOBILITE",
        libelle="Versement mobilité",
        taux_salarial=Decimal("0"),
        taux_patronal=Decimal("2.95"),  # Taux IDF Paris - variable selon zone
        base="brut"
    ),

    # ===============================================
    # FNAL (Fonds National d'Aide au Logement)
    # ===============================================

    TauxCotisation(
        code="FNAL_PLAF",
        libelle="FNAL plafonné",
        taux_salarial=Decimal("0"),
        taux_patronal=Decimal("0.10"),  # Entreprises < 50 salariés
        plafond=BaremesPayeFrance.PMSS_2024,
        base="plafonne"
    ),

    TauxCotisation(
        code="FNAL_DEPLAF",
        libelle="FNAL déplafonné",
        taux_salarial=Decimal("0"),
        taux_patronal=Decimal("0.50"),  # Entreprises >= 50 salariés
        base="brut"
    ),
]


# ============================================================================
# PRÉLÈVEMENT À LA SOURCE (PAS)
# ============================================================================

@dataclass
class BaremePAS:
    """Barème du prélèvement à la source 2024."""
    # Taux neutre mensuel (base 0% - valeurs mensuelles)
    TRANCHES_TAUX_NEUTRE = [
        (Decimal("1591"), Decimal("0")),
        (Decimal("1653"), Decimal("0.005")),
        (Decimal("1759"), Decimal("0.013")),
        (Decimal("1877"), Decimal("0.024")),
        (Decimal("2006"), Decimal("0.035")),
        (Decimal("2113"), Decimal("0.044")),
        (Decimal("2253"), Decimal("0.056")),
        (Decimal("2564"), Decimal("0.075")),
        (Decimal("2998"), Decimal("0.102")),
        (Decimal("3453"), Decimal("0.130")),
        (Decimal("4029"), Decimal("0.161")),
        (Decimal("4830"), Decimal("0.195")),
        (Decimal("6043"), Decimal("0.234")),
        (Decimal("7780"), Decimal("0.276")),
        (Decimal("10562"), Decimal("0.323")),
        (Decimal("14795"), Decimal("0.366")),
        (Decimal("22620"), Decimal("0.405")),
        (Decimal("48292"), Decimal("0.430")),
        (Decimal("999999999"), Decimal("0.430")),  # Au-delà
    ]


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class LigneBulletinPaie:
    """Ligne d'un bulletin de paie."""
    code: str
    libelle: str
    base: Decimal
    taux_salarial: Decimal
    montant_salarial: Decimal
    taux_patronal: Decimal
    montant_patronal: Decimal
    categorie: str = "cotisation"  # cotisation, gain, retenue, info


@dataclass
class BulletinPaie:
    """Bulletin de paie calculé."""
    # Identifiants
    employe_id: str
    periode: str  # YYYY-MM
    date_paiement: date

    # Éléments de salaire
    salaire_base: Decimal = Decimal("0")
    heures_travaillees: Decimal = Decimal("0")
    heures_supplementaires: Decimal = Decimal("0")
    primes: Decimal = Decimal("0")
    avantages_nature: Decimal = Decimal("0")
    indemnites: Decimal = Decimal("0")

    # Bruts
    salaire_brut: Decimal = Decimal("0")
    salaire_brut_abattu: Decimal = Decimal("0")  # Pour CSG/CRDS (98.25%)

    # Cotisations
    cotisations_salariales: Decimal = Decimal("0")
    cotisations_patronales: Decimal = Decimal("0")

    # Net
    net_imposable: Decimal = Decimal("0")
    net_avant_pas: Decimal = Decimal("0")
    prelevement_source: Decimal = Decimal("0")
    taux_pas: Decimal = Decimal("0")
    net_a_payer: Decimal = Decimal("0")

    # Coût employeur
    cout_total_employeur: Decimal = Decimal("0")

    # Détail des lignes
    lignes: list[LigneBulletinPaie] = field(default_factory=list)

    # Cumuls annuels
    cumul_brut: Decimal = Decimal("0")
    cumul_net_imposable: Decimal = Decimal("0")
    cumul_pas: Decimal = Decimal("0")

    # Informations
    convention_collective: str = ""
    qualification: str = ""
    coefficient: int = 0
    anciennete: str = ""


@dataclass
class SimulationPaie:
    """Résultat de simulation de paie."""
    salaire_brut: Decimal
    salaire_net: Decimal
    salaire_net_imposable: Decimal
    cotisations_salariales: Decimal
    cotisations_patronales: Decimal
    cout_employeur: Decimal
    taux_charges_salariales: Decimal
    taux_charges_patronales: Decimal
    detail_cotisations: list[LigneBulletinPaie]


# ============================================================================
# SERVICE DE PAIE FRANCE
# ============================================================================

class PaieFranceService:
    """Service de calcul de paie conforme France."""

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        pmss: Decimal = BaremesPayeFrance.PMSS_2024,
        is_cadre: bool = False,
        is_cdd: bool = False,
        effectif_entreprise: int = 50,
        zone_transport: str = "IDF",
        taux_at: Decimal = Decimal("2.00"),  # Taux AT/MP spécifique
        alsace_moselle: bool = False
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.pmss = pmss
        self.is_cadre = is_cadre
        self.is_cdd = is_cdd
        self.effectif = effectif_entreprise
        self.zone_transport = zone_transport
        self.taux_at = taux_at
        self.alsace_moselle = alsace_moselle

        # Filtrer les cotisations applicables
        self._cotisations = self._get_cotisations_applicables()

    def _get_cotisations_applicables(self) -> list[TauxCotisation]:
        """Obtenir la liste des cotisations applicables selon le contexte."""
        cotisations = []

        for c in COTISATIONS_FRANCE_2024:
            # Filtrer par catégorie
            if c.categorie == "cadre" and not self.is_cadre:
                continue
            if c.categorie == "cdd" and not self.is_cdd:
                continue

            # FNAL selon effectif
            if c.code == "FNAL_PLAF" and self.effectif >= 50:
                continue
            if c.code == "FNAL_DEPLAF" and self.effectif < 50:
                continue

            # Formation pro selon effectif
            if c.code == "FORMATION_PRO":
                c = TauxCotisation(
                    code=c.code,
                    libelle=c.libelle,
                    taux_salarial=c.taux_salarial,
                    taux_patronal=Decimal("0.55") if self.effectif < 11 else Decimal("1.00"),
                    base=c.base
                )

            # Alsace-Moselle
            if c.code == "MALADIE_ALSACE" and not self.alsace_moselle:
                continue

            # Versement mobilité selon zone
            if c.code == "VERSEMENT_MOBILITE":
                taux_vm = self._get_taux_versement_mobilite()
                c = TauxCotisation(
                    code=c.code,
                    libelle=c.libelle,
                    taux_salarial=Decimal("0"),
                    taux_patronal=taux_vm,
                    base=c.base
                )

            # AT/MP taux spécifique
            if c.code == "AT_MP":
                c = TauxCotisation(
                    code=c.code,
                    libelle=c.libelle,
                    taux_salarial=Decimal("0"),
                    taux_patronal=self.taux_at,
                    base=c.base
                )

            cotisations.append(c)

        return cotisations

    def _get_taux_versement_mobilite(self) -> Decimal:
        """Obtenir le taux de versement mobilité selon la zone."""
        taux_vm = {
            "IDF": Decimal("2.95"),      # Paris
            "IDF_HORS_PARIS": Decimal("2.01"),
            "LYON": Decimal("2.00"),
            "MARSEILLE": Decimal("2.00"),
            "TOULOUSE": Decimal("2.00"),
            "BORDEAUX": Decimal("1.55"),
            "PROVINCE": Decimal("0.55"),
            "AUCUN": Decimal("0"),
        }
        return taux_vm.get(self.zone_transport, Decimal("0.55"))

    def _calculer_base(
        self,
        cotisation: TauxCotisation,
        brut: Decimal,
        brut_csg: Decimal
    ) -> Decimal:
        """Calculer la base de cotisation."""
        if cotisation.base == "brut":
            return brut

        elif cotisation.base == "csg":
            # Base CSG = 98.25% du (brut + patronales sur avantages)
            return brut_csg

        elif cotisation.base == "plafonne":
            return min(brut, cotisation.plafond or brut)

        elif cotisation.base == "tranche_1":
            return min(brut, self.pmss)

        elif cotisation.base == "tranche_2":
            if brut <= self.pmss:
                return Decimal("0")
            plafond_t2 = cotisation.plafond or (Decimal("8") * self.pmss)
            return min(brut, plafond_t2) - self.pmss

        elif cotisation.base == "cet":
            # CET: totalité du brut si > PMSS
            if brut > self.pmss:
                return brut
            return Decimal("0")

        return brut

    def calculer_cotisations(
        self,
        salaire_brut: Decimal
    ) -> tuple[list[LigneBulletinPaie], Decimal, Decimal]:
        """
        Calculer toutes les cotisations sociales.

        Args:
            salaire_brut: Salaire brut mensuel

        Returns:
            Tuple (lignes, total_salarial, total_patronal)
        """
        lignes = []
        total_salarial = Decimal("0")
        total_patronal = Decimal("0")

        # Base CSG/CRDS = 98.25% du brut (+ cotisations patronales de prévoyance)
        base_csg = salaire_brut * Decimal("0.9825")

        for cotisation in self._cotisations:
            base = self._calculer_base(cotisation, salaire_brut, base_csg)

            if base <= 0:
                continue

            # Calcul des montants
            montant_salarial = (base * cotisation.taux_salarial / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            montant_patronal = (base * cotisation.taux_patronal / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            if montant_salarial > 0 or montant_patronal > 0:
                lignes.append(LigneBulletinPaie(
                    code=cotisation.code,
                    libelle=cotisation.libelle,
                    base=base,
                    taux_salarial=cotisation.taux_salarial,
                    montant_salarial=montant_salarial,
                    taux_patronal=cotisation.taux_patronal,
                    montant_patronal=montant_patronal
                ))

                total_salarial += montant_salarial
                total_patronal += montant_patronal

        return lignes, total_salarial, total_patronal

    def calculer_pas(
        self,
        net_imposable: Decimal,
        taux_personnalise: Decimal | None = None
    ) -> tuple[Decimal, Decimal]:
        """
        Calculer le prélèvement à la source.

        Args:
            net_imposable: Revenu net imposable mensuel
            taux_personnalise: Taux PAS personnalisé transmis par la DGFIP

        Returns:
            Tuple (montant_pas, taux_applique)
        """
        if taux_personnalise is not None:
            taux = taux_personnalise
        else:
            # Appliquer le barème neutre
            taux = Decimal("0")
            for plafond, t in BaremePAS.TRANCHES_TAUX_NEUTRE:
                if net_imposable <= plafond:
                    taux = t
                    break

        montant = (net_imposable * taux).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return montant, taux

    def calculer_heures_supplementaires(
        self,
        heures_sup: Decimal,
        taux_horaire: Decimal
    ) -> tuple[Decimal, Decimal]:
        """
        Calculer la rémunération des heures supplémentaires.

        Args:
            heures_sup: Nombre d'heures supplémentaires
            taux_horaire: Taux horaire de base

        Returns:
            Tuple (montant_hs, exoneration_cotisations)
        """
        montant = Decimal("0")

        # 8 premières heures à +25%
        if heures_sup > 0:
            h25 = min(heures_sup, Decimal("8"))
            montant += h25 * taux_horaire * (1 + BaremesPayeFrance.MAJORATION_HS_8_PREMIERES)

        # Au-delà à +50%
        if heures_sup > 8:
            h50 = heures_sup - Decimal("8")
            montant += h50 * taux_horaire * (1 + BaremesPayeFrance.MAJORATION_HS_SUIVANTES)

        # Exonération de cotisations salariales sur HS (depuis 2019)
        # Plafond annuel d'exonération: 7 500 EUR
        exoneration = montant * Decimal("0.1125")  # Taux d'exonération

        return montant.quantize(Decimal("0.01")), exoneration.quantize(Decimal("0.01"))

    def calculer_bulletin(
        self,
        employe_id: str,
        periode: str,
        salaire_base: Decimal,
        heures_travaillees: Decimal = BaremesPayeFrance.HEURES_MENSUELLES,
        heures_supplementaires: Decimal = Decimal("0"),
        primes: Decimal = Decimal("0"),
        avantages_nature: Decimal = Decimal("0"),
        indemnites_non_soumises: Decimal = Decimal("0"),
        absences_deduction: Decimal = Decimal("0"),
        taux_pas: Decimal | None = None,
        cumuls: dict | None = None
    ) -> BulletinPaie:
        """
        Calculer un bulletin de paie complet.

        Args:
            employe_id: ID de l'employé
            periode: Période de paie (YYYY-MM)
            salaire_base: Salaire de base mensuel
            heures_travaillees: Heures travaillées
            heures_supplementaires: Heures supplémentaires
            primes: Primes soumises à cotisations
            avantages_nature: Avantages en nature (soumis)
            indemnites_non_soumises: Indemnités non soumises (transport, repas)
            absences_deduction: Montant des retenues pour absences
            taux_pas: Taux PAS personnalisé
            cumuls: Cumuls annuels précédents

        Returns:
            BulletinPaie complet
        """
        logger.info(
            "Calculating payslip | tenant=%s employee=%s period=%s base=%s",
            self.tenant_id, employe_id, periode, salaire_base
        )

        bulletin = BulletinPaie(
            employe_id=employe_id,
            periode=periode,
            date_paiement=date.today(),
            salaire_base=salaire_base,
            heures_travaillees=heures_travaillees,
            heures_supplementaires=heures_supplementaires,
            primes=primes,
            avantages_nature=avantages_nature,
            indemnites=indemnites_non_soumises
        )

        # Calcul du taux horaire
        taux_horaire = salaire_base / heures_travaillees if heures_travaillees > 0 else Decimal("0")

        # Calcul des heures supplémentaires
        montant_hs = Decimal("0")
        exo_hs = Decimal("0")
        if heures_supplementaires > 0:
            montant_hs, exo_hs = self.calculer_heures_supplementaires(
                heures_supplementaires, taux_horaire
            )

        # Salaire brut
        brut = (
            salaire_base +
            montant_hs +
            primes +
            avantages_nature -
            absences_deduction
        )
        bulletin.salaire_brut = brut.quantize(Decimal("0.01"))

        # Ajouter lignes de gains
        bulletin.lignes.append(LigneBulletinPaie(
            code="SALAIRE_BASE",
            libelle="Salaire de base",
            base=heures_travaillees,
            taux_salarial=taux_horaire,
            montant_salarial=salaire_base,
            taux_patronal=Decimal("0"),
            montant_patronal=Decimal("0"),
            categorie="gain"
        ))

        if montant_hs > 0:
            bulletin.lignes.append(LigneBulletinPaie(
                code="HEURES_SUP",
                libelle="Heures supplémentaires",
                base=heures_supplementaires,
                taux_salarial=taux_horaire * Decimal("1.25"),
                montant_salarial=montant_hs,
                taux_patronal=Decimal("0"),
                montant_patronal=Decimal("0"),
                categorie="gain"
            ))

        if primes > 0:
            bulletin.lignes.append(LigneBulletinPaie(
                code="PRIMES",
                libelle="Primes",
                base=Decimal("1"),
                taux_salarial=Decimal("100"),
                montant_salarial=primes,
                taux_patronal=Decimal("0"),
                montant_patronal=Decimal("0"),
                categorie="gain"
            ))

        # Calcul des cotisations
        lignes_cotis, total_salarial, total_patronal = self.calculer_cotisations(brut)
        bulletin.lignes.extend(lignes_cotis)

        # Réduction des cotisations sur HS
        if exo_hs > 0:
            total_salarial -= exo_hs
            bulletin.lignes.append(LigneBulletinPaie(
                code="EXO_HS",
                libelle="Exonération cotisations HS",
                base=montant_hs,
                taux_salarial=Decimal("-11.25"),
                montant_salarial=-exo_hs,
                taux_patronal=Decimal("0"),
                montant_patronal=Decimal("0"),
                categorie="retenue"
            ))

        bulletin.cotisations_salariales = total_salarial.quantize(Decimal("0.01"))
        bulletin.cotisations_patronales = total_patronal.quantize(Decimal("0.01"))

        # Net imposable
        # = Brut - cotisations salariales + CSG non déductible + CRDS
        csg_non_ded = Decimal("0")
        crds = Decimal("0")
        for ligne in lignes_cotis:
            if ligne.code == "CSG_NON_DED":
                csg_non_ded = ligne.montant_salarial
            elif ligne.code == "CRDS":
                crds = ligne.montant_salarial

        bulletin.net_imposable = (
            brut - total_salarial + csg_non_ded + crds
        ).quantize(Decimal("0.01"))

        # Net avant PAS
        bulletin.net_avant_pas = (brut - total_salarial).quantize(Decimal("0.01"))

        # Prélèvement à la source
        pas, taux_applique = self.calculer_pas(bulletin.net_imposable, taux_pas)
        bulletin.prelevement_source = pas
        bulletin.taux_pas = taux_applique

        # Net à payer
        bulletin.net_a_payer = (
            bulletin.net_avant_pas -
            pas +
            indemnites_non_soumises
        ).quantize(Decimal("0.01"))

        # Coût employeur
        bulletin.cout_total_employeur = (
            brut + total_patronal
        ).quantize(Decimal("0.01"))

        # Cumuls
        if cumuls:
            bulletin.cumul_brut = cumuls.get("brut", Decimal("0")) + brut
            bulletin.cumul_net_imposable = cumuls.get("net_imposable", Decimal("0")) + bulletin.net_imposable
            bulletin.cumul_pas = cumuls.get("pas", Decimal("0")) + pas
        else:
            bulletin.cumul_brut = brut
            bulletin.cumul_net_imposable = bulletin.net_imposable
            bulletin.cumul_pas = pas

        logger.info(
            "Payslip calculated | employee=%s brut=%s net=%s employer_cost=%s",
            employe_id, bulletin.salaire_brut, bulletin.net_a_payer,
            bulletin.cout_total_employeur
        )

        return bulletin

    def simuler_paie(
        self,
        salaire_brut: Decimal,
        taux_pas: Decimal = Decimal("0")
    ) -> SimulationPaie:
        """
        Simuler une paie pour un salaire brut donné.

        Args:
            salaire_brut: Salaire brut mensuel
            taux_pas: Taux PAS à appliquer

        Returns:
            SimulationPaie avec détail des cotisations
        """
        lignes, total_salarial, total_patronal = self.calculer_cotisations(salaire_brut)

        net_avant_pas = salaire_brut - total_salarial
        pas, _ = self.calculer_pas(net_avant_pas, taux_pas)

        return SimulationPaie(
            salaire_brut=salaire_brut,
            salaire_net=net_avant_pas - pas,
            salaire_net_imposable=net_avant_pas,
            cotisations_salariales=total_salarial,
            cotisations_patronales=total_patronal,
            cout_employeur=salaire_brut + total_patronal,
            taux_charges_salariales=(total_salarial / salaire_brut * 100).quantize(Decimal("0.01")),
            taux_charges_patronales=(total_patronal / salaire_brut * 100).quantize(Decimal("0.01")),
            detail_cotisations=lignes
        )

    def export_dsn_bulletin(self, bulletin: BulletinPaie) -> dict:
        """
        Exporter les données du bulletin au format DSN.
        Structure simplifiée pour intégration DSN.
        """
        return {
            "individu": {
                "identifiant": bulletin.employe_id,
                "periode": bulletin.periode
            },
            "remuneration": {
                "brutSoumis": str(bulletin.salaire_brut),
                "netImposable": str(bulletin.net_imposable),
                "netAPayer": str(bulletin.net_a_payer)
            },
            "cotisations": {
                "totalSalarial": str(bulletin.cotisations_salariales),
                "totalPatronal": str(bulletin.cotisations_patronales),
                "detail": [
                    {
                        "code": l.code,
                        "base": str(l.base),
                        "montantSalarial": str(l.montant_salarial),
                        "montantPatronal": str(l.montant_patronal)
                    }
                    for l in bulletin.lignes
                    if l.categorie == "cotisation"
                ]
            },
            "pas": {
                "montant": str(bulletin.prelevement_source),
                "taux": str(bulletin.taux_pas)
            },
            "cumuls": {
                "brutCumule": str(bulletin.cumul_brut),
                "netImposableCumule": str(bulletin.cumul_net_imposable),
                "pasCumule": str(bulletin.cumul_pas)
            }
        }
