"""
AZALSCORE - Service Liasses Fiscales France
============================================
Génération automatique des liasses fiscales françaises.

Formulaires gérés:
- 2050 à 2059-G: Liasse BIC/IS (Régime réel normal)
- 2033-A à 2033-G: Liasse BIC (Régime simplifié)
- 2065: Déclaration de résultats IS
- 2031: Déclaration BIC
- 2035: Déclaration BNC
- 2067: Relevé de solde IS
- 2572: Acomptes IS

Références:
- CGI articles 38-54, 209-223
- BOI-IS-DECLA et BOI-BIC-DECLA
"""
from __future__ import annotations


import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.accounting.models import (
    AccountingFiscalYear,
    AccountingJournalEntry,
    AccountingJournalEntryLine,
    ChartOfAccounts,
    EntryStatus,
)

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS ET CONSTANTES
# ============================================================================

class RegimeFiscal(str, Enum):
    """Régimes fiscaux France."""
    REEL_NORMAL = "REEL_NORMAL"       # BIC/IS Réel Normal (CA > 789 000 EUR services)
    REEL_SIMPLIFIE = "REEL_SIMPLIFIE" # BIC Réel Simplifié
    MICRO_BIC = "MICRO_BIC"           # Micro-BIC
    BNC = "BNC"                        # Bénéfices Non Commerciaux
    IS = "IS"                          # Impôt sur les sociétés


class TypeLiasse(str, Enum):
    """Types de liasses fiscales."""
    # Liasse BIC/IS Réel Normal
    LIASSE_2050 = "2050"  # Bilan Actif
    LIASSE_2051 = "2051"  # Bilan Passif
    LIASSE_2052 = "2052"  # Compte de résultat de l'exercice (en liste) - Charges
    LIASSE_2053 = "2053"  # Compte de résultat de l'exercice (en liste) - Produits
    LIASSE_2054 = "2054"  # Immobilisations
    LIASSE_2055 = "2055"  # Amortissements
    LIASSE_2056 = "2056"  # Provisions
    LIASSE_2057 = "2057"  # État des échéances des créances et des dettes
    LIASSE_2058_A = "2058-A"  # Détermination du résultat fiscal
    LIASSE_2058_B = "2058-B"  # Déficits, indemnités pour congés à payer et provisions non déductibles
    LIASSE_2058_C = "2058-C"  # Tableau d'affectation du résultat et renseignements divers
    LIASSE_2059_A = "2059-A"  # Plus-values et moins-values
    LIASSE_2059_B = "2059-B"  # Affectation des plus-values à court terme
    LIASSE_2059_C = "2059-C"  # Suivi des moins-values à long terme
    LIASSE_2059_D = "2059-D"  # Réserve spéciale des plus-values à long terme
    LIASSE_2059_E = "2059-E"  # Détermination de la valeur ajoutée
    LIASSE_2059_F = "2059-F"  # Composition du capital social
    LIASSE_2059_G = "2059-G"  # Filiales et participations

    # Liasse Simplifiée
    LIASSE_2033_A = "2033-A"  # Bilan simplifié
    LIASSE_2033_B = "2033-B"  # Compte de résultat simplifié
    LIASSE_2033_C = "2033-C"  # Immobilisations, amortissements, plus-values
    LIASSE_2033_D = "2033-D"  # Relevé de provisions, amortissements dérogatoires
    LIASSE_2033_E = "2033-E"  # Détermination du résultat fiscal
    LIASSE_2033_F = "2033-F"  # Composition du capital social
    LIASSE_2033_G = "2033-G"  # Filiales et participations

    # Déclarations de résultats
    DECL_2065 = "2065"  # IS - Déclaration de résultats
    DECL_2031 = "2031"  # BIC - Déclaration
    DECL_2035 = "2035"  # BNC - Déclaration

    # Paiements
    RELEVE_2067 = "2067"  # Relevé de solde IS
    ACOMPTE_2572 = "2572"  # Acomptes IS


# Mapping comptes PCG vers rubriques liasse 2050 (Actif)
MAPPING_ACTIF_2050 = {
    # Actif immobilisé - Immobilisations incorporelles
    "AA": ["201", "203", "205", "206", "207", "208"],  # Frais établissement, R&D, brevets, fonds commercial
    "AB": ["2801", "2803", "2805", "2806", "2807", "2808", "2905"],  # Amortissements

    # Actif immobilisé - Immobilisations corporelles
    "AC": ["211", "212"],  # Terrains
    "AD": ["2811", "2812", "2911", "2912"],  # Amortissements terrains
    "AE": ["213"],  # Constructions
    "AF": ["2813", "2913"],  # Amortissements constructions
    "AG": ["214", "215"],  # Installations techniques, matériel
    "AH": ["2814", "2815", "2914", "2915"],  # Amortissements
    "AI": ["218"],  # Autres immobilisations corporelles
    "AJ": ["2818", "2918"],  # Amortissements autres
    "AK": ["231", "232", "237", "238"],  # Immobilisations en cours

    # Actif immobilisé - Immobilisations financières
    "AL": ["261", "262", "263", "266", "267", "268"],  # Participations
    "AM": ["2961", "2962", "2963", "2966", "2967", "2968"],  # Provisions participations
    "AN": ["271", "272", "273", "274", "275", "276"],  # Autres immobilisations financières
    "AO": ["2971", "2972", "2974", "2975", "2976"],  # Provisions autres

    # Actif circulant - Stocks
    "AP": ["31", "32", "33", "34", "35", "37"],  # Stocks matières, en-cours, produits
    "AQ": ["391", "392", "393", "394", "395", "397"],  # Provisions stocks

    # Actif circulant - Créances
    "AR": ["409", "411", "413", "416", "417", "418"],  # Avances, clients
    "AS": ["491"],  # Provisions clients
    "AT": ["42", "43", "44", "45", "46", "47"],  # Autres créances
    "AU": ["495", "496"],  # Provisions autres créances

    # Actif circulant - Divers
    "AV": ["50"],  # VMP
    "AW": ["590"],  # Provisions VMP
    "AX": ["51", "52", "53", "54", "58"],  # Disponibilités
    "AY": ["486"],  # Charges constatées d'avance

    # Total actif
    "AZ": [],  # TOTAL ACTIF (calculé)
}

# Mapping comptes PCG vers rubriques liasse 2051 (Passif)
MAPPING_PASSIF_2051 = {
    # Capitaux propres
    "DA": ["101"],  # Capital social
    "DB": ["1041", "1042"],  # Primes d'émission, de fusion
    "DC": ["105"],  # Écarts de réévaluation
    "DD": ["1061", "1063"],  # Réserve légale
    "DE": ["1064"],  # Réserves statutaires
    "DF": ["1068"],  # Autres réserves
    "DG": ["11"],  # Report à nouveau
    "DH": ["12"],  # Résultat de l'exercice
    "DI": ["13"],  # Subventions d'investissement
    "DJ": ["14"],  # Provisions réglementées

    # Provisions pour risques et charges
    "DK": ["151", "153", "155", "156", "157", "158"],  # Provisions pour risques
    "DL": ["15"],  # Total provisions

    # Dettes
    "DM": ["161", "162", "163", "164", "165", "166", "167", "168"],  # Emprunts obligataires
    "DN": ["164", "165", "166", "167", "168"],  # Emprunts et dettes établissements crédit
    "DO": ["17"],  # Emprunts et dettes financières divers
    "DP": ["269", "279"],  # Avances et acomptes reçus
    "DQ": ["401", "403", "404", "405", "408"],  # Dettes fournisseurs
    "DR": ["42", "43", "44", "45", "46", "47"],  # Dettes fiscales et sociales
    "DS": ["16", "17", "269", "4191", "4196", "4197"],  # Autres dettes
    "DT": ["487"],  # Produits constatés d'avance

    # Total passif
    "DU": [],  # TOTAL PASSIF (calculé)
}

# Mapping comptes PCG vers rubriques 2052-2053 (Résultat)
MAPPING_RESULTAT = {
    # Produits d'exploitation (2053)
    "FA": ["701", "702", "703", "704", "705", "706", "707", "708", "709"],  # Ventes
    "FB": ["713"],  # Production stockée
    "FC": ["72"],  # Production immobilisée
    "FD": ["74"],  # Subventions d'exploitation
    "FE": ["781"],  # Reprises sur amortissements et provisions
    "FF": ["791"],  # Transferts de charges
    "FG": ["75"],  # Autres produits

    # Charges d'exploitation (2052)
    "FH": ["601", "602", "604", "605", "606", "607", "608", "609"],  # Achats marchandises, MP
    "FI": ["6031", "6032"],  # Variation de stock
    "FJ": ["61", "62"],  # Autres achats et charges externes
    "FK": ["63"],  # Impôts, taxes
    "FL": ["641", "642", "643", "644", "645", "646", "647", "648"],  # Salaires et traitements
    "FM": ["645"],  # Charges sociales
    "FN": ["681"],  # Dotations aux amortissements
    "FO": ["6811", "6812", "6815", "6816", "6817"],  # Dotations aux amortissements
    "FP": ["6866", "6868", "686"],  # Dotations aux provisions
    "FQ": ["65"],  # Autres charges

    # Résultat d'exploitation
    "FR": [],  # RESULTAT D'EXPLOITATION (calculé)

    # Produits financiers
    "FS": ["761", "762", "763", "764", "765", "766", "767", "768", "769"],  # Produits financiers
    "FT": ["786"],  # Reprises sur provisions financières

    # Charges financières
    "FU": ["661", "664", "665", "666", "667", "668"],  # Charges financières
    "FV": ["686"],  # Dotations provisions financières

    # Résultat financier
    "FW": [],  # RESULTAT FINANCIER (calculé)

    # Produits exceptionnels
    "FX": ["771", "772", "775", "778"],  # Produits exceptionnels
    "FY": ["787"],  # Reprises provisions exceptionnelles

    # Charges exceptionnelles
    "FZ": ["671", "672", "675", "678"],  # Charges exceptionnelles
    "GA": ["687"],  # Dotations provisions exceptionnelles

    # Résultat exceptionnel
    "GB": [],  # RESULTAT EXCEPTIONNEL (calculé)

    # IS et résultat
    "GC": ["695", "696", "697", "698", "699"],  # Participation, IS
    "GD": [],  # RESULTAT NET (calculé)
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class LigneFormulaire:
    """Ligne d'un formulaire de liasse fiscale."""
    code: str
    libelle: str
    valeur_n: Decimal = Decimal("0")
    valeur_n1: Decimal = Decimal("0")
    comptes: list[str] = field(default_factory=list)
    calcul: str | None = None  # Formule si calculé


@dataclass
class FormulaireLibelle:
    """Formulaire de liasse fiscale."""
    numero: str
    titre: str
    lignes: list[LigneFormulaire] = field(default_factory=list)
    total_n: Decimal = Decimal("0")
    total_n1: Decimal = Decimal("0")


@dataclass
class LiasseFiscale:
    """Liasse fiscale complète."""
    tenant_id: str
    exercice_id: str
    exercice_code: str
    date_debut: date
    date_fin: date
    regime: RegimeFiscal
    formulaires: list[FormulaireLibelle] = field(default_factory=list)
    resultat_fiscal: Decimal = Decimal("0")
    impot_du: Decimal = Decimal("0")
    genere_le: datetime = field(default_factory=datetime.utcnow)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ResultatFiscal:
    """Résultat fiscal calculé."""
    resultat_comptable: Decimal = Decimal("0")
    reintegrations: Decimal = Decimal("0")
    deductions: Decimal = Decimal("0")
    resultat_fiscal: Decimal = Decimal("0")
    deficits_anterieurs: Decimal = Decimal("0")
    resultat_imposable: Decimal = Decimal("0")
    detail_reintegrations: dict = field(default_factory=dict)
    detail_deductions: dict = field(default_factory=dict)


# ============================================================================
# SERVICE LIASSES FISCALES
# ============================================================================

class LiassesFiscalesService:
    """Service de génération des liasses fiscales françaises."""

    # Taux IS 2024-2025
    TAUX_IS_NORMAL = Decimal("0.25")
    TAUX_IS_REDUIT = Decimal("0.15")  # PME jusqu'à 42 500 EUR
    PLAFOND_IS_REDUIT = Decimal("42500")

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # RÉCUPÉRATION DES SOLDES
    # ========================================================================

    def _get_account_balance(
        self,
        account_prefix: str,
        fiscal_year_id: str,
        balance_type: str = "solde"  # solde, debit, credit
    ) -> Decimal:
        """
        Récupérer le solde d'un compte ou groupe de comptes.

        Args:
            account_prefix: Préfixe du compte (ex: "41", "701")
            fiscal_year_id: ID de l'exercice
            balance_type: Type de solde (solde, debit, credit)
        """
        query = self.db.query(
            func.coalesce(func.sum(AccountingJournalEntryLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(AccountingJournalEntryLine.credit), 0).label("total_credit")
        ).join(
            AccountingJournalEntry,
            AccountingJournalEntryLine.entry_id == AccountingJournalEntry.id
        ).filter(
            AccountingJournalEntryLine.tenant_id == self.tenant_id,
            AccountingJournalEntry.fiscal_year_id == fiscal_year_id,
            AccountingJournalEntry.status == EntryStatus.POSTED,
            AccountingJournalEntryLine.account_number.like(f"{account_prefix}%")
        )

        result = query.first()

        if not result:
            return Decimal("0")

        total_debit = result.total_debit or Decimal("0")
        total_credit = result.total_credit or Decimal("0")

        if balance_type == "debit":
            return total_debit
        elif balance_type == "credit":
            return total_credit
        else:  # solde
            return total_debit - total_credit

    def _get_balance_by_prefixes(
        self,
        prefixes: list[str],
        fiscal_year_id: str,
        is_credit_nature: bool = False
    ) -> Decimal:
        """
        Récupérer le solde total pour une liste de préfixes de comptes.

        Args:
            prefixes: Liste de préfixes (ex: ["701", "702", "703"])
            fiscal_year_id: ID de l'exercice
            is_credit_nature: True si comptes de nature créditrice (passif, produits)
        """
        total = Decimal("0")

        for prefix in prefixes:
            balance = self._get_account_balance(prefix, fiscal_year_id)
            if is_credit_nature:
                balance = -balance  # Inverser pour avoir une valeur positive
            total += balance

        return total

    # ========================================================================
    # GÉNÉRATION FORMULAIRE 2050 - BILAN ACTIF
    # ========================================================================

    def _generer_2050_actif(
        self,
        fiscal_year_id: str,
        fiscal_year_n1_id: str | None = None
    ) -> FormulaireLibelle:
        """Générer le formulaire 2050 - Bilan Actif."""
        formulaire = FormulaireLibelle(
            numero="2050",
            titre="BILAN - ACTIF"
        )

        # Labels des lignes
        labels = {
            "AA": "Frais d'établissement",
            "AB": "Frais de recherche et développement",
            "AC": "Concessions, brevets, licences, logiciels",
            "AD": "Fonds commercial",
            "AE": "Autres immobilisations incorporelles",
            "AF": "Avances et acomptes sur immobilisations incorporelles",
            "AH": "Terrains",
            "AI": "Constructions",
            "AJ": "Installations techniques, matériel et outillage",
            "AK": "Autres immobilisations corporelles",
            "AL": "Immobilisations en cours",
            "AM": "Avances et acomptes",
            "AN": "Participations évaluées selon mise en équivalence",
            "AO": "Autres participations",
            "AP": "Créances rattachées à des participations",
            "AQ": "Autres titres immobilisés",
            "AR": "Prêts",
            "AS": "Autres immobilisations financières",
            "AT": "Total ACTIF IMMOBILISE",
            "AV": "Matières premières, approvisionnements",
            "AW": "En-cours de production de biens",
            "AX": "En-cours de production de services",
            "AY": "Produits intermédiaires et finis",
            "AZ": "Marchandises",
            "BA": "Avances et acomptes versés sur commandes",
            "BB": "Clients et comptes rattachés",
            "BC": "Autres créances",
            "BD": "Capital souscrit et appelé, non versé",
            "BE": "Valeurs mobilières de placement",
            "BF": "Disponibilités",
            "BG": "Charges constatées d'avance",
            "BH": "Total ACTIF CIRCULANT",
            "BI": "Charges à répartir sur plusieurs exercices",
            "BJ": "Primes de remboursement des obligations",
            "BK": "Écarts de conversion actif",
            "BL": "TOTAL GENERAL"
        }

        # Mapping simplifié comptes -> rubriques
        mapping_comptes = {
            "AA": ["201"],
            "AB": ["203"],
            "AC": ["205", "206"],
            "AD": ["207"],
            "AE": ["208"],
            "AF": ["237"],
            "AH": ["211", "212"],
            "AI": ["213"],
            "AJ": ["214", "215"],
            "AK": ["218"],
            "AL": ["231", "232"],
            "AM": ["238"],
            "AN": ["261"],
            "AO": ["262", "263", "266"],
            "AP": ["267"],
            "AQ": ["271", "272", "273"],
            "AR": ["274"],
            "AS": ["275", "276", "277"],
            "AV": ["31", "32"],
            "AW": ["33", "34"],
            "AX": ["345"],
            "AY": ["35"],
            "AZ": ["37"],
            "BA": ["409"],
            "BB": ["411", "413", "416", "417", "418"],
            "BC": ["42", "43", "44", "45", "46", "47"],
            "BD": ["109"],
            "BE": ["50"],
            "BF": ["51", "52", "53", "54", "58"],
            "BG": ["486"],
        }

        total_immobilise = Decimal("0")
        total_circulant = Decimal("0")

        for code, libelle in labels.items():
            if code in ["AT", "BH", "BL"]:
                continue  # Lignes de total

            prefixes = mapping_comptes.get(code, [])
            valeur = self._get_balance_by_prefixes(prefixes, fiscal_year_id, is_credit_nature=False)
            valeur_n1 = Decimal("0")

            if fiscal_year_n1_id:
                valeur_n1 = self._get_balance_by_prefixes(prefixes, fiscal_year_n1_id, is_credit_nature=False)

            ligne = LigneFormulaire(
                code=code,
                libelle=libelle,
                valeur_n=valeur,
                valeur_n1=valeur_n1,
                comptes=prefixes
            )
            formulaire.lignes.append(ligne)

            # Accumulation totaux
            if code <= "AS":
                total_immobilise += valeur
            elif code <= "BG":
                total_circulant += valeur

        # Ajouter lignes de total
        formulaire.lignes.append(LigneFormulaire(
            code="AT",
            libelle="Total ACTIF IMMOBILISE",
            valeur_n=total_immobilise,
            calcul="Somme AA à AS"
        ))

        formulaire.lignes.append(LigneFormulaire(
            code="BH",
            libelle="Total ACTIF CIRCULANT",
            valeur_n=total_circulant,
            calcul="Somme AV à BG"
        ))

        formulaire.lignes.append(LigneFormulaire(
            code="BL",
            libelle="TOTAL GENERAL",
            valeur_n=total_immobilise + total_circulant,
            calcul="AT + BH + BI + BJ + BK"
        ))

        formulaire.total_n = total_immobilise + total_circulant
        return formulaire

    # ========================================================================
    # GÉNÉRATION FORMULAIRE 2051 - BILAN PASSIF
    # ========================================================================

    def _generer_2051_passif(
        self,
        fiscal_year_id: str,
        fiscal_year_n1_id: str | None = None
    ) -> FormulaireLibelle:
        """Générer le formulaire 2051 - Bilan Passif."""
        formulaire = FormulaireLibelle(
            numero="2051",
            titre="BILAN - PASSIF"
        )

        labels = {
            "DA": "Capital social ou individuel",
            "DB": "Primes d'émission, de fusion, d'apport",
            "DC": "Écarts de réévaluation",
            "DD": "Réserve légale",
            "DE": "Réserves statutaires ou contractuelles",
            "DF": "Réserves réglementées",
            "DG": "Autres réserves",
            "DH": "Report à nouveau",
            "DI": "Résultat de l'exercice",
            "DJ": "Subventions d'investissement",
            "DK": "Provisions réglementées",
            "DL": "Total CAPITAUX PROPRES",
            "DM": "Produits des émissions de titres participatifs",
            "DN": "Avances conditionnées",
            "DO": "Total AUTRES FONDS PROPRES",
            "DP": "Provisions pour risques",
            "DQ": "Provisions pour charges",
            "DR": "Total PROVISIONS",
            "DS": "Emprunts obligataires convertibles",
            "DT": "Autres emprunts obligataires",
            "DU": "Emprunts et dettes auprès des établissements de crédit",
            "DV": "Emprunts et dettes financières diverses",
            "DW": "Avances et acomptes reçus sur commandes",
            "DX": "Dettes fournisseurs et comptes rattachés",
            "DY": "Dettes fiscales et sociales",
            "DZ": "Dettes sur immobilisations",
            "EA": "Autres dettes",
            "EB": "Produits constatés d'avance",
            "EC": "Total DETTES",
            "ED": "Écarts de conversion passif",
            "EE": "TOTAL GENERAL"
        }

        mapping_comptes = {
            "DA": ["101", "108"],
            "DB": ["1041", "1042", "1043"],
            "DC": ["105"],
            "DD": ["1061"],
            "DE": ["1062", "1063"],
            "DF": ["1064"],
            "DG": ["1068"],
            "DH": ["11"],
            "DI": ["12"],
            "DJ": ["13"],
            "DK": ["14"],
            "DM": ["1671"],
            "DN": ["1674"],
            "DP": ["151"],
            "DQ": ["153", "155", "156", "157", "158"],
            "DS": ["161"],
            "DT": ["163"],
            "DU": ["164", "165", "166", "519"],
            "DV": ["167", "168", "17"],
            "DW": ["4191"],
            "DX": ["401", "403", "404", "405", "408"],
            "DY": ["42", "43", "44"],
            "DZ": ["269", "279"],
            "EA": ["45", "46", "47"],
            "EB": ["487"],
            "ED": ["477"],
        }

        total_capitaux = Decimal("0")
        total_provisions = Decimal("0")
        total_dettes = Decimal("0")

        for code, libelle in labels.items():
            if code in ["DL", "DO", "DR", "EC", "EE"]:
                continue

            prefixes = mapping_comptes.get(code, [])
            # Passif = nature créditrice
            valeur = self._get_balance_by_prefixes(prefixes, fiscal_year_id, is_credit_nature=True)
            valeur_n1 = Decimal("0")

            if fiscal_year_n1_id:
                valeur_n1 = self._get_balance_by_prefixes(prefixes, fiscal_year_n1_id, is_credit_nature=True)

            ligne = LigneFormulaire(
                code=code,
                libelle=libelle,
                valeur_n=valeur,
                valeur_n1=valeur_n1,
                comptes=prefixes
            )
            formulaire.lignes.append(ligne)

            if code <= "DK":
                total_capitaux += valeur
            elif code in ["DP", "DQ"]:
                total_provisions += valeur
            elif code <= "ED":
                total_dettes += valeur

        # Totaux
        formulaire.lignes.append(LigneFormulaire(
            code="DL",
            libelle="Total CAPITAUX PROPRES",
            valeur_n=total_capitaux,
            calcul="Somme DA à DK"
        ))

        formulaire.lignes.append(LigneFormulaire(
            code="DR",
            libelle="Total PROVISIONS",
            valeur_n=total_provisions,
            calcul="DP + DQ"
        ))

        formulaire.lignes.append(LigneFormulaire(
            code="EC",
            libelle="Total DETTES",
            valeur_n=total_dettes,
            calcul="Somme DS à EB"
        ))

        total_general = total_capitaux + total_provisions + total_dettes
        formulaire.lignes.append(LigneFormulaire(
            code="EE",
            libelle="TOTAL GENERAL",
            valeur_n=total_general,
            calcul="DL + DO + DR + EC + ED"
        ))

        formulaire.total_n = total_general
        return formulaire

    # ========================================================================
    # GÉNÉRATION FORMULAIRES 2052-2053 - COMPTE DE RÉSULTAT
    # ========================================================================

    def _generer_2052_2053_resultat(
        self,
        fiscal_year_id: str,
        fiscal_year_n1_id: str | None = None
    ) -> tuple[FormulaireLibelle, FormulaireLibelle]:
        """Générer les formulaires 2052 (Charges) et 2053 (Produits)."""

        # 2052 - Charges
        form_2052 = FormulaireLibelle(
            numero="2052",
            titre="COMPTE DE RESULTAT DE L'EXERCICE - CHARGES"
        )

        charges_labels = {
            "FA": "Achats de marchandises",
            "FB": "Variation de stock (marchandises)",
            "FC": "Achats de matières premières",
            "FD": "Variation de stock (matières premières)",
            "FE": "Autres achats et charges externes",
            "FF": "Impôts, taxes et versements assimilés",
            "FG": "Salaires et traitements",
            "FH": "Charges sociales",
            "FI": "Dotations aux amortissements sur immobilisations",
            "FJ": "Dotations aux provisions sur actif circulant",
            "FK": "Dotations aux provisions pour risques et charges",
            "FL": "Autres charges",
            "FM": "Total des charges d'exploitation",
            "FN": "Charges financières d'intérêts",
            "FO": "Pertes de change",
            "FP": "Charges nettes sur cessions VMP",
            "FQ": "Dotations aux provisions financières",
            "FR": "Total des charges financières",
            "FS": "Charges exceptionnelles sur opérations de gestion",
            "FT": "Charges exceptionnelles sur opérations en capital",
            "FU": "Dotations aux provisions exceptionnelles",
            "FV": "Total des charges exceptionnelles",
            "FW": "Participation des salariés",
            "FX": "Impôt sur les bénéfices",
            "FY": "TOTAL DES CHARGES",
            "FZ": "Solde créditeur = bénéfice"
        }

        charges_mapping = {
            "FA": ["607"],
            "FB": ["6037"],
            "FC": ["601", "602"],
            "FD": ["6031", "6032"],
            "FE": ["604", "605", "606", "61", "62"],
            "FF": ["63"],
            "FG": ["641", "644", "645", "648"],
            "FH": ["645", "646", "647"],
            "FI": ["6811", "6812", "6871"],
            "FJ": ["6816", "6817"],
            "FK": ["6815"],
            "FL": ["65"],
            "FN": ["661", "664", "665", "666"],
            "FO": ["666"],
            "FP": ["667"],
            "FQ": ["686"],
            "FS": ["671"],
            "FT": ["675", "678"],
            "FU": ["687"],
            "FW": ["691"],
            "FX": ["695", "696", "697", "698", "699"],
        }

        total_charges_expl = Decimal("0")
        total_charges_fin = Decimal("0")
        total_charges_exc = Decimal("0")

        for code, libelle in charges_labels.items():
            if code in ["FM", "FR", "FV", "FY", "FZ"]:
                continue

            prefixes = charges_mapping.get(code, [])
            # Charges = nature débitrice
            valeur = self._get_balance_by_prefixes(prefixes, fiscal_year_id, is_credit_nature=False)

            ligne = LigneFormulaire(
                code=code,
                libelle=libelle,
                valeur_n=max(valeur, Decimal("0")),
                comptes=prefixes
            )
            form_2052.lignes.append(ligne)

            if code <= "FL":
                total_charges_expl += max(valeur, Decimal("0"))
            elif code <= "FQ":
                total_charges_fin += max(valeur, Decimal("0"))
            elif code <= "FU":
                total_charges_exc += max(valeur, Decimal("0"))

        # Totaux charges
        form_2052.lignes.append(LigneFormulaire(
            code="FM", libelle="Total des charges d'exploitation",
            valeur_n=total_charges_expl, calcul="Somme FA à FL"
        ))
        form_2052.lignes.append(LigneFormulaire(
            code="FR", libelle="Total des charges financières",
            valeur_n=total_charges_fin, calcul="Somme FN à FQ"
        ))
        form_2052.lignes.append(LigneFormulaire(
            code="FV", libelle="Total des charges exceptionnelles",
            valeur_n=total_charges_exc, calcul="Somme FS à FU"
        ))

        # 2053 - Produits
        form_2053 = FormulaireLibelle(
            numero="2053",
            titre="COMPTE DE RESULTAT DE L'EXERCICE - PRODUITS"
        )

        produits_labels = {
            "GA": "Ventes de marchandises",
            "GB": "Production vendue de biens",
            "GC": "Production vendue de services",
            "GD": "Chiffre d'affaires net",
            "GE": "Production stockée",
            "GF": "Production immobilisée",
            "GG": "Subventions d'exploitation",
            "GH": "Reprises sur provisions et amortissements",
            "GI": "Transferts de charges",
            "GJ": "Autres produits",
            "GK": "Total des produits d'exploitation",
            "GL": "Produits financiers de participations",
            "GM": "Produits des autres VMP et créances de l'actif immobilisé",
            "GN": "Autres intérêts et produits assimilés",
            "GO": "Reprises sur provisions financières",
            "GP": "Différences positives de change",
            "GQ": "Produits nets sur cessions VMP",
            "GR": "Total des produits financiers",
            "GS": "Produits exceptionnels sur opérations de gestion",
            "GT": "Produits exceptionnels sur opérations en capital",
            "GU": "Reprises sur provisions exceptionnelles",
            "GV": "Total des produits exceptionnels",
            "GW": "TOTAL DES PRODUITS",
            "GX": "Solde débiteur = perte"
        }

        produits_mapping = {
            "GA": ["707"],
            "GB": ["701", "702", "703"],
            "GC": ["704", "705", "706", "708"],
            "GE": ["713"],
            "GF": ["72"],
            "GG": ["74"],
            "GH": ["781", "791"],
            "GI": ["791"],
            "GJ": ["75", "79"],
            "GL": ["761"],
            "GM": ["762"],
            "GN": ["763", "764", "765", "768"],
            "GO": ["786", "796"],
            "GP": ["766"],
            "GQ": ["767"],
            "GS": ["771"],
            "GT": ["775", "778"],
            "GU": ["787", "797"],
        }

        total_produits_expl = Decimal("0")
        total_produits_fin = Decimal("0")
        total_produits_exc = Decimal("0")

        for code, libelle in produits_labels.items():
            if code in ["GD", "GK", "GR", "GV", "GW", "GX"]:
                continue

            prefixes = produits_mapping.get(code, [])
            # Produits = nature créditrice
            valeur = self._get_balance_by_prefixes(prefixes, fiscal_year_id, is_credit_nature=True)

            ligne = LigneFormulaire(
                code=code,
                libelle=libelle,
                valeur_n=max(valeur, Decimal("0")),
                comptes=prefixes
            )
            form_2053.lignes.append(ligne)

            if code <= "GJ":
                total_produits_expl += max(valeur, Decimal("0"))
            elif code <= "GQ":
                total_produits_fin += max(valeur, Decimal("0"))
            elif code <= "GU":
                total_produits_exc += max(valeur, Decimal("0"))

        # Totaux produits
        ca_net = self._get_balance_by_prefixes(
            ["701", "702", "703", "704", "705", "706", "707", "708", "709"],
            fiscal_year_id, is_credit_nature=True
        )
        form_2053.lignes.insert(3, LigneFormulaire(
            code="GD", libelle="Chiffre d'affaires net",
            valeur_n=ca_net, calcul="GA + GB + GC"
        ))

        form_2053.lignes.append(LigneFormulaire(
            code="GK", libelle="Total des produits d'exploitation",
            valeur_n=total_produits_expl, calcul="Somme GA à GJ"
        ))
        form_2053.lignes.append(LigneFormulaire(
            code="GR", libelle="Total des produits financiers",
            valeur_n=total_produits_fin, calcul="Somme GL à GQ"
        ))
        form_2053.lignes.append(LigneFormulaire(
            code="GV", libelle="Total des produits exceptionnels",
            valeur_n=total_produits_exc, calcul="Somme GS à GU"
        ))

        total_produits = total_produits_expl + total_produits_fin + total_produits_exc
        total_charges = total_charges_expl + total_charges_fin + total_charges_exc

        # Récupérer participation et IS
        participation = self._get_balance_by_prefixes(["691"], fiscal_year_id, is_credit_nature=False)
        impot = self._get_balance_by_prefixes(["695", "696", "697", "698", "699"], fiscal_year_id, is_credit_nature=False)

        total_charges_complet = total_charges + max(participation, Decimal("0")) + max(impot, Decimal("0"))

        form_2052.lignes.append(LigneFormulaire(
            code="FY", libelle="TOTAL DES CHARGES",
            valeur_n=total_charges_complet, calcul="FM + FR + FV + FW + FX"
        ))

        form_2053.lignes.append(LigneFormulaire(
            code="GW", libelle="TOTAL DES PRODUITS",
            valeur_n=total_produits, calcul="GK + GR + GV"
        ))

        # Résultat
        resultat = total_produits - total_charges_complet
        if resultat > 0:
            form_2052.lignes.append(LigneFormulaire(
                code="FZ", libelle="Solde créditeur = bénéfice",
                valeur_n=resultat, calcul="GW - FY si positif"
            ))
        else:
            form_2053.lignes.append(LigneFormulaire(
                code="GX", libelle="Solde débiteur = perte",
                valeur_n=abs(resultat), calcul="FY - GW si positif"
            ))

        form_2052.total_n = total_charges_complet
        form_2053.total_n = total_produits

        return form_2052, form_2053

    # ========================================================================
    # GÉNÉRATION FORMULAIRE 2058-A - RÉSULTAT FISCAL
    # ========================================================================

    def _generer_2058a_resultat_fiscal(
        self,
        fiscal_year_id: str,
        resultat_comptable: Decimal
    ) -> tuple[FormulaireLibelle, ResultatFiscal]:
        """Générer le formulaire 2058-A - Détermination du résultat fiscal."""

        formulaire = FormulaireLibelle(
            numero="2058-A",
            titre="DETERMINATION DU RESULTAT FISCAL"
        )

        resultat_fiscal = ResultatFiscal(resultat_comptable=resultat_comptable)

        # I - RÉINTÉGRATIONS (augmentation du résultat fiscal)
        reintegrations = {
            "WA": ("Rémunération du travail de l'exploitant", ["108"]),
            "WB": ("Avantages personnels non déductibles", []),
            "WC": ("Impôts et taxes non déductibles", ["6351", "6358"]),
            "WD": ("Charges non déductibles (amortissements excédentaires, etc.)", ["6871"]),
            "WE": ("Provisions non déductibles", ["6815", "6875"]),
            "WF": ("Charges à payer non déductibles", []),
            "WG": ("Amendes et pénalités", ["6712"]),
            "WH": ("Dons et cotisations non déductibles", []),
            "WI": ("Participation des salariés (si non déductible)", []),
            "WJ": ("Jetons de présence non déductibles", []),
            "WK": ("Charges financières non déductibles (art. 212 bis)", []),
            "WL": ("Quote-part de frais et charges sur dividendes", []),
            "WM": ("Autres réintégrations", []),
        }

        total_reintegrations = Decimal("0")

        for code, (libelle, comptes) in reintegrations.items():
            valeur = Decimal("0")
            if comptes:
                valeur = self._get_balance_by_prefixes(comptes, fiscal_year_id, is_credit_nature=False)
                valeur = max(valeur, Decimal("0"))

            if valeur > 0:
                resultat_fiscal.detail_reintegrations[code] = valeur
                total_reintegrations += valeur

            formulaire.lignes.append(LigneFormulaire(
                code=code, libelle=libelle, valeur_n=valeur, comptes=comptes
            ))

        formulaire.lignes.append(LigneFormulaire(
            code="WN", libelle="Total des réintégrations",
            valeur_n=total_reintegrations, calcul="Somme WA à WM"
        ))

        # II - DÉDUCTIONS (diminution du résultat fiscal)
        deductions = {
            "WO": ("Produits non imposables", []),
            "WP": ("Plus-values à long terme", ["775"]),
            "WQ": ("Déduction pour investissement", []),
            "WR": ("Mécénat et dons (art. 238 bis)", []),
            "WS": ("Créances nées de reports en arrière de déficits", []),
            "WT": ("Produits de participations (régime mère-fille)", ["761"]),
            "WU": ("Quote-part de bénéfice de sociétés de personnes", []),
            "WV": ("Autres déductions", []),
        }

        total_deductions = Decimal("0")

        for code, (libelle, comptes) in deductions.items():
            valeur = Decimal("0")
            if comptes:
                valeur = self._get_balance_by_prefixes(comptes, fiscal_year_id, is_credit_nature=True)
                valeur = max(valeur, Decimal("0"))

            if valeur > 0:
                resultat_fiscal.detail_deductions[code] = valeur
                total_deductions += valeur

            formulaire.lignes.append(LigneFormulaire(
                code=code, libelle=libelle, valeur_n=valeur, comptes=comptes
            ))

        formulaire.lignes.append(LigneFormulaire(
            code="WW", libelle="Total des déductions",
            valeur_n=total_deductions, calcul="Somme WO à WV"
        ))

        # III - RÉSULTAT FISCAL
        resultat_fiscal.reintegrations = total_reintegrations
        resultat_fiscal.deductions = total_deductions
        resultat_fiscal.resultat_fiscal = (
            resultat_comptable + total_reintegrations - total_deductions
        )

        formulaire.lignes.append(LigneFormulaire(
            code="XA", libelle="Résultat comptable",
            valeur_n=resultat_comptable
        ))
        formulaire.lignes.append(LigneFormulaire(
            code="XB", libelle="RÉSULTAT FISCAL (bénéfice ou déficit)",
            valeur_n=resultat_fiscal.resultat_fiscal,
            calcul="XA + WN - WW"
        ))

        # IV - IMPUTATION DES DÉFICITS ANTÉRIEURS
        # (à implémenter avec historique des déficits)
        resultat_fiscal.resultat_imposable = max(
            resultat_fiscal.resultat_fiscal - resultat_fiscal.deficits_anterieurs,
            Decimal("0")
        )

        formulaire.lignes.append(LigneFormulaire(
            code="XC", libelle="Déficits antérieurs imputés",
            valeur_n=resultat_fiscal.deficits_anterieurs
        ))
        formulaire.lignes.append(LigneFormulaire(
            code="XD", libelle="RÉSULTAT IMPOSABLE",
            valeur_n=resultat_fiscal.resultat_imposable,
            calcul="XB - XC"
        ))

        formulaire.total_n = resultat_fiscal.resultat_imposable
        return formulaire, resultat_fiscal

    # ========================================================================
    # CALCUL IS
    # ========================================================================

    def calculer_is(
        self,
        resultat_imposable: Decimal,
        est_pme: bool = True
    ) -> tuple[Decimal, dict]:
        """
        Calculer l'impôt sur les sociétés.

        Args:
            resultat_imposable: Base imposable
            est_pme: True si PME (taux réduit applicable)

        Returns:
            Tuple (IS total, détail du calcul)
        """
        detail = {
            "base_imposable": resultat_imposable,
            "est_pme": est_pme,
            "tranches": []
        }

        if resultat_imposable <= 0:
            detail["is_total"] = Decimal("0")
            return Decimal("0"), detail

        is_total = Decimal("0")

        if est_pme and resultat_imposable > 0:
            # Tranche à taux réduit (15% jusqu'à 42 500 EUR)
            base_reduit = min(resultat_imposable, self.PLAFOND_IS_REDUIT)
            is_reduit = base_reduit * self.TAUX_IS_REDUIT

            detail["tranches"].append({
                "base": base_reduit,
                "taux": float(self.TAUX_IS_REDUIT),
                "is": is_reduit,
                "description": "Taux réduit PME (15%)"
            })

            is_total += is_reduit

            # Tranche à taux normal (25% au-delà)
            if resultat_imposable > self.PLAFOND_IS_REDUIT:
                base_normal = resultat_imposable - self.PLAFOND_IS_REDUIT
                is_normal = base_normal * self.TAUX_IS_NORMAL

                detail["tranches"].append({
                    "base": base_normal,
                    "taux": float(self.TAUX_IS_NORMAL),
                    "is": is_normal,
                    "description": "Taux normal (25%)"
                })

                is_total += is_normal
        else:
            # Tout au taux normal
            is_total = resultat_imposable * self.TAUX_IS_NORMAL

            detail["tranches"].append({
                "base": resultat_imposable,
                "taux": float(self.TAUX_IS_NORMAL),
                "is": is_total,
                "description": "Taux normal (25%)"
            })

        detail["is_total"] = is_total
        return is_total, detail

    # ========================================================================
    # GÉNÉRATION LIASSE COMPLÈTE
    # ========================================================================

    def generer_liasse_complete(
        self,
        fiscal_year_id: str,
        regime: RegimeFiscal = RegimeFiscal.REEL_NORMAL,
        fiscal_year_n1_id: str | None = None
    ) -> LiasseFiscale:
        """
        Générer la liasse fiscale complète pour un exercice.

        Args:
            fiscal_year_id: ID de l'exercice comptable
            regime: Régime fiscal
            fiscal_year_n1_id: ID de l'exercice N-1 (optionnel)

        Returns:
            LiasseFiscale complète
        """
        logger.info(
            "Generating fiscal statements | tenant=%s fiscal_year=%s regime=%s",
            self.tenant_id, fiscal_year_id, regime.value
        )

        # Récupérer exercice
        fiscal_year = self.db.query(AccountingFiscalYear).filter(
            AccountingFiscalYear.tenant_id == self.tenant_id,
            AccountingFiscalYear.id == fiscal_year_id
        ).first()

        if not fiscal_year:
            raise ValueError(f"Exercice {fiscal_year_id} introuvable")

        liasse = LiasseFiscale(
            tenant_id=self.tenant_id,
            exercice_id=str(fiscal_year.id),
            exercice_code=fiscal_year.code,
            date_debut=fiscal_year.start_date.date(),
            date_fin=fiscal_year.end_date.date(),
            regime=regime
        )

        try:
            if regime == RegimeFiscal.REEL_NORMAL or regime == RegimeFiscal.IS:
                # 2050 - Bilan Actif
                form_2050 = self._generer_2050_actif(fiscal_year_id, fiscal_year_n1_id)
                liasse.formulaires.append(form_2050)

                # 2051 - Bilan Passif
                form_2051 = self._generer_2051_passif(fiscal_year_id, fiscal_year_n1_id)
                liasse.formulaires.append(form_2051)

                # Vérifier équilibre bilan
                if abs(form_2050.total_n - form_2051.total_n) > Decimal("0.01"):
                    liasse.warnings.append(
                        f"Bilan non équilibré: Actif={form_2050.total_n}, Passif={form_2051.total_n}"
                    )

                # 2052-2053 - Compte de résultat
                form_2052, form_2053 = self._generer_2052_2053_resultat(
                    fiscal_year_id, fiscal_year_n1_id
                )
                liasse.formulaires.append(form_2052)
                liasse.formulaires.append(form_2053)

                # Calculer résultat comptable
                resultat_comptable = form_2053.total_n - form_2052.total_n

                # 2058-A - Résultat fiscal
                form_2058a, resultat_fiscal = self._generer_2058a_resultat_fiscal(
                    fiscal_year_id, resultat_comptable
                )
                liasse.formulaires.append(form_2058a)

                liasse.resultat_fiscal = resultat_fiscal.resultat_imposable

                # Calculer IS
                is_du, detail_is = self.calculer_is(resultat_fiscal.resultat_imposable)
                liasse.impot_du = is_du

            elif regime == RegimeFiscal.REEL_SIMPLIFIE:
                # Liasse simplifiée 2033
                liasse.warnings.append("Liasse simplifiée 2033 - génération partielle")
                # À implémenter: 2033-A à 2033-G

            logger.info(
                "Fiscal statements generated | tenant=%s forms=%s result=%s is=%s",
                self.tenant_id, len(liasse.formulaires),
                liasse.resultat_fiscal, liasse.impot_du
            )

        except Exception as e:
            logger.error(
                "Error generating fiscal statements | tenant=%s error=%s",
                self.tenant_id, str(e)
            )
            liasse.errors.append(f"Erreur de génération: {str(e)}")

        return liasse

    # ========================================================================
    # EXPORT
    # ========================================================================

    def export_liasse_dict(self, liasse: LiasseFiscale) -> dict:
        """Exporter la liasse fiscale en dictionnaire."""
        return {
            "metadata": {
                "tenant_id": liasse.tenant_id,
                "exercice_id": liasse.exercice_id,
                "exercice_code": liasse.exercice_code,
                "date_debut": liasse.date_debut.isoformat(),
                "date_fin": liasse.date_fin.isoformat(),
                "regime": liasse.regime.value,
                "genere_le": liasse.genere_le.isoformat()
            },
            "resultats": {
                "resultat_fiscal": str(liasse.resultat_fiscal),
                "impot_du": str(liasse.impot_du)
            },
            "formulaires": [
                {
                    "numero": f.numero,
                    "titre": f.titre,
                    "total_n": str(f.total_n),
                    "total_n1": str(f.total_n1),
                    "lignes": [
                        {
                            "code": l.code,
                            "libelle": l.libelle,
                            "valeur_n": str(l.valeur_n),
                            "valeur_n1": str(l.valeur_n1),
                            "comptes": l.comptes,
                            "calcul": l.calcul
                        }
                        for l in f.lignes
                    ]
                }
                for f in liasse.formulaires
            ],
            "errors": liasse.errors,
            "warnings": liasse.warnings
        }

    def export_liasse_edi(self, liasse: LiasseFiscale) -> str:
        """
        Exporter la liasse fiscale au format EDI-TDFC.
        Format utilisé pour la télétransmission à la DGFiP.
        """
        # Structure EDI-TDFC simplifiée
        lines = []

        # En-tête
        lines.append(f"ISI0|{liasse.exercice_code}|{liasse.date_debut}|{liasse.date_fin}")

        # Pour chaque formulaire
        for form in liasse.formulaires:
            lines.append(f"F|{form.numero}")

            for ligne in form.lignes:
                if ligne.valeur_n != 0:
                    lines.append(f"L|{ligne.code}|{ligne.valeur_n}")

        # Pied
        lines.append(f"FIN|{len(liasse.formulaires)}")

        return "\n".join(lines)
