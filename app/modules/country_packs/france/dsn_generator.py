"""
AZALSCORE - Générateur DSN (Déclaration Sociale Nominative)
============================================================

Génération de fichiers DSN conformes aux normes NEORAU (Net-Entreprises).

Références:
- Cahier technique DSN Phase 3
- Norme NEODeS (DSN en XML/CSV)
- Guide URSSAF DSN

Types de DSN:
- DSN mensuelle (tous les mois)
- DSN événementielle (arrêt maladie, fin de contrat, etc.)

Structures principales:
- S10: Envoi
- S20: Entreprise
- S21: Établissement
- S30: Salarié
- S40: Cotisations
- S60: Paiement
"""

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional
from xml.etree import ElementTree as ET

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTES DSN
# ============================================================================

DSN_VERSION = "P23V01"  # Version DSN Phase 3
DSN_NORME = "NEODeS"


class TypeDSN(str, Enum):
    """Types de déclaration DSN."""
    MENSUELLE = "01"          # DSN mensuelle normale
    SIGNALETIQUE = "02"       # DSN signalétique (annulation/remplacement)
    ARRET_TRAVAIL = "03"      # Signalement arrêt de travail
    FIN_CONTRAT = "04"        # Signalement fin de contrat
    REPRISE_TRAVAIL = "05"    # Signalement reprise anticipée


class NatureDSN(str, Enum):
    """Nature de la déclaration."""
    NORMALE = "01"            # Déclaration normale
    ANNULE_REMPLACE = "02"    # Annule et remplace
    NEANT = "03"              # Déclaration néant (aucun salarié)


class MotifArret(str, Enum):
    """Motifs d'arrêt de travail."""
    MALADIE = "01"
    MATERNITE = "02"
    PATERNITE = "03"
    ADOPTION = "04"
    ACCIDENT_TRAVAIL = "05"
    ACCIDENT_TRAJET = "06"
    MALADIE_PRO = "07"


class MotifRupture(str, Enum):
    """Motifs de rupture de contrat."""
    LICENCIEMENT_ECO = "011"
    LICENCIEMENT_PERS = "012"
    LICENCIEMENT_FAUTE = "014"
    DEMISSION = "020"
    FIN_CDD = "031"
    RUPTURE_CONV = "043"
    DEPART_RETRAITE = "059"
    MISE_RETRAITE = "060"
    DECES = "065"
    FIN_PERIODE_ESSAI = "091"


class TypeContrat(str, Enum):
    """Types de contrat DSN."""
    CDI = "01"
    CDD = "02"
    CTT = "03"        # Contrat de travail temporaire
    APPRENTISSAGE = "07"
    PROFESSIONNALISATION = "08"


class CategorieEmploi(str, Enum):
    """Catégories socioprofessionnelles (PCS-ESE)."""
    OUVRIER = "60"
    EMPLOYE = "50"
    TECHNICIEN = "40"
    AGENT_MAITRISE = "30"
    CADRE = "20"
    CADRE_DIRIGEANT = "10"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class EntrepriseDSN:
    """Données entreprise pour DSN (bloc S20)."""
    siren: str
    nic_siege: str
    raison_sociale: str
    adresse: str
    code_postal: str
    ville: str
    code_apet: str  # Code APE établissement
    effectif_mensuel: int
    effectif_fin_periode: int


@dataclass
class EtablissementDSN:
    """Données établissement pour DSN (bloc S21)."""
    nic: str  # NIC de l'établissement
    code_apet: str
    adresse: str
    code_postal: str
    ville: str
    effectif: int
    code_risque_at: str  # Code risque AT/MP
    taux_at: Decimal


@dataclass
class SalarieDSN:
    """Données salarié pour DSN (bloc S30)."""
    nir: str                      # Numéro de Sécurité Sociale
    nom: str
    prenom: str
    date_naissance: date
    lieu_naissance: str
    code_pays_naissance: str = "99100"  # France
    sexe: str = "01"              # 01=H, 02=F
    adresse: str = ""
    code_postal: str = ""
    ville: str = ""
    code_pays: str = "FR"

    # Contrat
    numero_contrat: str = ""
    date_debut_contrat: date = None
    date_fin_contrat: date = None
    type_contrat: TypeContrat = TypeContrat.CDI
    nature_contrat: str = "01"    # 01=temps plein
    quotite: Decimal = Decimal("1")  # Temps partiel: 0.5, etc.

    # Emploi
    code_emploi: str = ""
    libelle_emploi: str = ""
    categorie: CategorieEmploi = CategorieEmploi.EMPLOYE
    coefficient: int = 0
    echelon: str = ""
    convention_collective: str = ""  # IDCC

    # Statut
    statut_cadre: bool = False
    statut_pro_particulier: str = ""  # Apprenti, stagiaire, etc.


@dataclass
class RemunerationDSN:
    """Données de rémunération pour DSN (blocs S21.G00.50/51)."""
    date_debut: date
    date_fin: date

    # Montants
    brut_soumis: Decimal = Decimal("0")
    brut_non_soumis: Decimal = Decimal("0")
    net_imposable: Decimal = Decimal("0")
    net_verse: Decimal = Decimal("0")

    # Heures
    heures_travaillees: Decimal = Decimal("0")
    heures_supplementaires: Decimal = Decimal("0")
    heures_complementaires: Decimal = Decimal("0")

    # Primes et indemnités
    primes: list = field(default_factory=list)
    avantages_nature: Decimal = Decimal("0")


@dataclass
class CotisationDSN:
    """Cotisation individuelle pour DSN (bloc S21.G00.78)."""
    code_cotisation: str
    identifiant_organisme: str  # URSSAF, AGIRC-ARRCO, etc.
    montant_assiette: Decimal
    montant_cotisation: Decimal
    taux: Decimal
    type_assiette: str = "02"  # 02=assiette brute


@dataclass
class PaiementDSN:
    """Données de paiement pour DSN (bloc S21.G00.55)."""
    date_versement: date
    montant: Decimal
    mode_paiement: str = "05"  # 05=virement


@dataclass
class ArretTravailDSN:
    """Signalement arrêt de travail (DSN événementielle)."""
    salarie_nir: str
    motif: MotifArret
    date_debut: date
    date_fin_prevue: date = None
    date_reprise: date = None
    subrogation: bool = False
    date_debut_subrogation: date = None
    date_fin_subrogation: date = None
    iban_subrogation: str = ""


@dataclass
class FinContratDSN:
    """Signalement fin de contrat (DSN événementielle)."""
    salarie_nir: str
    date_fin: date
    motif: MotifRupture
    date_notification: date = None
    date_dernier_jour_travaille: date = None

    # Indemnités
    indemnite_licenciement: Decimal = Decimal("0")
    indemnite_preavis: Decimal = Decimal("0")
    indemnite_conges_payes: Decimal = Decimal("0")
    indemnite_non_concurrence: Decimal = Decimal("0")

    # Portabilité
    portabilite_sante: bool = True
    portabilite_prevoyance: bool = True


# ============================================================================
# GÉNÉRATEUR DSN
# ============================================================================

class DSNGenerator:
    """
    Générateur de fichiers DSN conformes NEORAU.

    Multi-tenant: OUI
    Formats: XML (NEODeS), CSV (pour import)
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        entreprise: EntrepriseDSN,
        etablissement: EtablissementDSN,
    ):
        if not tenant_id:
            raise ValueError("tenant_id est requis")

        self.db = db
        self.tenant_id = tenant_id
        self.entreprise = entreprise
        self.etablissement = etablissement
        self._sequence = 1

        logger.info(f"DSNGenerator initialisé pour tenant {tenant_id}")

    # =========================================================================
    # DSN MENSUELLE
    # =========================================================================

    def generer_dsn_mensuelle(
        self,
        periode: str,  # YYYY-MM
        salaries: list[SalarieDSN],
        remunerations: dict[str, RemunerationDSN],  # NIR -> RemunérationDSN
        cotisations: dict[str, list[CotisationDSN]],  # NIR -> [CotisationDSN]
        paiements: list[PaiementDSN],
        nature: NatureDSN = NatureDSN.NORMALE,
        ordre: int = 1,  # Numéro d'ordre dans le mois
    ) -> str:
        """
        Génère une DSN mensuelle complète.

        Args:
            periode: Période de paie (YYYY-MM)
            salaries: Liste des salariés
            remunerations: Dict NIR -> Rémunération
            cotisations: Dict NIR -> Liste de cotisations
            paiements: Liste des paiements
            nature: Nature de la déclaration
            ordre: Numéro d'ordre

        Returns:
            Contenu DSN au format XML
        """
        logger.info(f"Génération DSN mensuelle pour période {periode}")

        # Créer le document XML
        root = ET.Element("DSN")
        root.set("version", DSN_VERSION)

        # S10 - Envoi
        self._ajouter_bloc_envoi(root, periode, TypeDSN.MENSUELLE, nature, ordre)

        # S20 - Entreprise
        self._ajouter_bloc_entreprise(root)

        # S21 - Établissement
        etablissement_elem = self._ajouter_bloc_etablissement(root, periode)

        # Pour chaque salarié
        for salarie in salaries:
            # S30 - Salarié (individu)
            individu_elem = self._ajouter_bloc_salarie(etablissement_elem, salarie)

            # Rémunérations
            remun = remunerations.get(salarie.nir)
            if remun:
                self._ajouter_bloc_remuneration(individu_elem, remun)

            # Cotisations individuelles
            cotis_salarie = cotisations.get(salarie.nir, [])
            for cotis in cotis_salarie:
                self._ajouter_bloc_cotisation(individu_elem, cotis)

        # Cotisations agrégées établissement
        self._ajouter_cotisations_agregees(etablissement_elem, cotisations)

        # Paiements
        for paiement in paiements:
            self._ajouter_bloc_paiement(etablissement_elem, paiement)

        # Convertir en string
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    # =========================================================================
    # DSN ÉVÉNEMENTIELLE
    # =========================================================================

    def generer_dsn_arret_travail(
        self,
        arret: ArretTravailDSN,
        salarie: SalarieDSN,
    ) -> str:
        """
        Génère une DSN événementielle pour arrêt de travail.

        Délai: 5 jours après le début de l'arrêt.
        """
        logger.info(f"Génération DSN arrêt travail NIR={arret.salarie_nir[:6]}...")

        root = ET.Element("DSN")
        root.set("version", DSN_VERSION)

        # Envoi
        self._ajouter_bloc_envoi(
            root,
            arret.date_debut.strftime("%Y-%m"),
            TypeDSN.ARRET_TRAVAIL,
            NatureDSN.NORMALE,
            1
        )

        # Entreprise et établissement
        self._ajouter_bloc_entreprise(root)
        etablissement_elem = self._ajouter_bloc_etablissement(
            root, arret.date_debut.strftime("%Y-%m")
        )

        # Salarié
        individu_elem = self._ajouter_bloc_salarie(etablissement_elem, salarie)

        # Bloc arrêt (S21.G00.60)
        arret_elem = ET.SubElement(individu_elem, "S21.G00.60")
        self._ajouter_rubrique(arret_elem, "S21.G00.60.001", arret.motif.value)
        self._ajouter_rubrique(arret_elem, "S21.G00.60.002", arret.date_debut.strftime("%d%m%Y"))

        if arret.date_fin_prevue:
            self._ajouter_rubrique(arret_elem, "S21.G00.60.003", arret.date_fin_prevue.strftime("%d%m%Y"))

        if arret.subrogation:
            self._ajouter_rubrique(arret_elem, "S21.G00.60.010", "01")  # Oui
            if arret.date_debut_subrogation:
                self._ajouter_rubrique(arret_elem, "S21.G00.60.011", arret.date_debut_subrogation.strftime("%d%m%Y"))
            if arret.date_fin_subrogation:
                self._ajouter_rubrique(arret_elem, "S21.G00.60.012", arret.date_fin_subrogation.strftime("%d%m%Y"))
            if arret.iban_subrogation:
                self._ajouter_rubrique(arret_elem, "S21.G00.60.013", arret.iban_subrogation)

        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def generer_dsn_fin_contrat(
        self,
        fin: FinContratDSN,
        salarie: SalarieDSN,
    ) -> str:
        """
        Génère une DSN événementielle pour fin de contrat.

        Délai: 5 jours après la fin du contrat.
        """
        logger.info(f"Génération DSN fin contrat NIR={fin.salarie_nir[:6]}...")

        root = ET.Element("DSN")
        root.set("version", DSN_VERSION)

        # Envoi
        self._ajouter_bloc_envoi(
            root,
            fin.date_fin.strftime("%Y-%m"),
            TypeDSN.FIN_CONTRAT,
            NatureDSN.NORMALE,
            1
        )

        # Entreprise et établissement
        self._ajouter_bloc_entreprise(root)
        etablissement_elem = self._ajouter_bloc_etablissement(
            root, fin.date_fin.strftime("%Y-%m")
        )

        # Salarié
        individu_elem = self._ajouter_bloc_salarie(etablissement_elem, salarie)

        # Bloc fin de contrat (S21.G00.62)
        fin_elem = ET.SubElement(individu_elem, "S21.G00.62")
        self._ajouter_rubrique(fin_elem, "S21.G00.62.001", fin.date_fin.strftime("%d%m%Y"))
        self._ajouter_rubrique(fin_elem, "S21.G00.62.002", fin.motif.value)

        if fin.date_notification:
            self._ajouter_rubrique(fin_elem, "S21.G00.62.003", fin.date_notification.strftime("%d%m%Y"))

        if fin.date_dernier_jour_travaille:
            self._ajouter_rubrique(fin_elem, "S21.G00.62.004", fin.date_dernier_jour_travaille.strftime("%d%m%Y"))

        # Indemnités (bloc S21.G00.63)
        if fin.indemnite_licenciement > 0:
            self._ajouter_indemnite(individu_elem, "001", fin.indemnite_licenciement)
        if fin.indemnite_preavis > 0:
            self._ajouter_indemnite(individu_elem, "002", fin.indemnite_preavis)
        if fin.indemnite_conges_payes > 0:
            self._ajouter_indemnite(individu_elem, "003", fin.indemnite_conges_payes)
        if fin.indemnite_non_concurrence > 0:
            self._ajouter_indemnite(individu_elem, "004", fin.indemnite_non_concurrence)

        # Portabilité (bloc S21.G00.64)
        porta_elem = ET.SubElement(individu_elem, "S21.G00.64")
        self._ajouter_rubrique(porta_elem, "S21.G00.64.001", "01" if fin.portabilite_sante else "02")
        self._ajouter_rubrique(porta_elem, "S21.G00.64.002", "01" if fin.portabilite_prevoyance else "02")

        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    # =========================================================================
    # BLOCS XML
    # =========================================================================

    def _ajouter_bloc_envoi(
        self,
        root: ET.Element,
        periode: str,
        type_dsn: TypeDSN,
        nature: NatureDSN,
        ordre: int,
    ):
        """Ajoute le bloc S10 (Envoi)."""
        s10 = ET.SubElement(root, "S10.G00.00")

        # Identification envoi
        self._ajouter_rubrique(s10, "S10.G00.00.001", self.entreprise.siren)
        self._ajouter_rubrique(s10, "S10.G00.00.002", self.entreprise.nic_siege)
        self._ajouter_rubrique(s10, "S10.G00.00.003", self.entreprise.raison_sociale)

        # Période et type
        self._ajouter_rubrique(s10, "S10.G00.00.005", periode.replace("-", ""))
        self._ajouter_rubrique(s10, "S10.G00.00.006", type_dsn.value)
        self._ajouter_rubrique(s10, "S10.G00.00.007", nature.value)
        self._ajouter_rubrique(s10, "S10.G00.00.008", f"{ordre:02d}")

        # Date et heure de génération
        now = datetime.now()
        self._ajouter_rubrique(s10, "S10.G00.00.010", now.strftime("%d%m%Y"))
        self._ajouter_rubrique(s10, "S10.G00.00.011", now.strftime("%H%M%S"))

    def _ajouter_bloc_entreprise(self, root: ET.Element):
        """Ajoute le bloc S20 (Entreprise)."""
        s20 = ET.SubElement(root, "S20.G00.05")

        self._ajouter_rubrique(s20, "S20.G00.05.001", self.entreprise.siren)
        self._ajouter_rubrique(s20, "S20.G00.05.002", self.entreprise.nic_siege)
        self._ajouter_rubrique(s20, "S20.G00.05.003", self.entreprise.raison_sociale)
        self._ajouter_rubrique(s20, "S20.G00.05.004", self.entreprise.adresse)
        self._ajouter_rubrique(s20, "S20.G00.05.006", self.entreprise.code_postal)
        self._ajouter_rubrique(s20, "S20.G00.05.007", self.entreprise.ville)
        self._ajouter_rubrique(s20, "S20.G00.05.008", self.entreprise.code_apet)
        self._ajouter_rubrique(s20, "S20.G00.05.010", str(self.entreprise.effectif_mensuel))

    def _ajouter_bloc_etablissement(self, root: ET.Element, periode: str) -> ET.Element:
        """Ajoute le bloc S21 (Établissement)."""
        s21 = ET.SubElement(root, "S21.G00.06")

        self._ajouter_rubrique(s21, "S21.G00.06.001", self.etablissement.nic)
        self._ajouter_rubrique(s21, "S21.G00.06.002", self.etablissement.code_apet)
        self._ajouter_rubrique(s21, "S21.G00.06.003", self.etablissement.adresse)
        self._ajouter_rubrique(s21, "S21.G00.06.005", self.etablissement.code_postal)
        self._ajouter_rubrique(s21, "S21.G00.06.006", self.etablissement.ville)
        self._ajouter_rubrique(s21, "S21.G00.06.007", str(self.etablissement.effectif))

        return s21

    def _ajouter_bloc_salarie(self, parent: ET.Element, salarie: SalarieDSN) -> ET.Element:
        """Ajoute le bloc S30 (Individu/Salarié)."""
        s30 = ET.SubElement(parent, "S21.G00.30")

        # Identité
        self._ajouter_rubrique(s30, "S21.G00.30.001", salarie.nir)
        self._ajouter_rubrique(s30, "S21.G00.30.002", salarie.nom.upper())
        self._ajouter_rubrique(s30, "S21.G00.30.004", salarie.prenom)
        self._ajouter_rubrique(s30, "S21.G00.30.006", salarie.sexe)
        self._ajouter_rubrique(s30, "S21.G00.30.007", salarie.date_naissance.strftime("%d%m%Y"))
        self._ajouter_rubrique(s30, "S21.G00.30.008", salarie.lieu_naissance)

        # Adresse
        if salarie.adresse:
            self._ajouter_rubrique(s30, "S21.G00.30.010", salarie.adresse)
            self._ajouter_rubrique(s30, "S21.G00.30.012", salarie.code_postal)
            self._ajouter_rubrique(s30, "S21.G00.30.013", salarie.ville)

        # Contrat (bloc S21.G00.40)
        contrat = ET.SubElement(s30, "S21.G00.40")
        self._ajouter_rubrique(contrat, "S21.G00.40.001", salarie.date_debut_contrat.strftime("%d%m%Y") if salarie.date_debut_contrat else "")
        self._ajouter_rubrique(contrat, "S21.G00.40.007", salarie.type_contrat.value)
        self._ajouter_rubrique(contrat, "S21.G00.40.008", salarie.nature_contrat)
        self._ajouter_rubrique(contrat, "S21.G00.40.009", salarie.code_emploi)
        self._ajouter_rubrique(contrat, "S21.G00.40.010", salarie.libelle_emploi)
        self._ajouter_rubrique(contrat, "S21.G00.40.011", salarie.categorie.value)

        if salarie.convention_collective:
            self._ajouter_rubrique(contrat, "S21.G00.40.017", salarie.convention_collective)

        if salarie.statut_cadre:
            self._ajouter_rubrique(contrat, "S21.G00.40.026", "01")

        return s30

    def _ajouter_bloc_remuneration(self, parent: ET.Element, remun: RemunerationDSN):
        """Ajoute le bloc de rémunération (S21.G00.50/51/52)."""
        # Base (S21.G00.51)
        s51 = ET.SubElement(parent, "S21.G00.51")
        self._ajouter_rubrique(s51, "S21.G00.51.001", remun.date_debut.strftime("%d%m%Y"))
        self._ajouter_rubrique(s51, "S21.G00.51.002", remun.date_fin.strftime("%d%m%Y"))
        self._ajouter_rubrique(s51, "S21.G00.51.011", str(remun.heures_travaillees))

        # Rémunérations (S21.G00.52)
        s52 = ET.SubElement(parent, "S21.G00.52")
        self._ajouter_rubrique(s52, "S21.G00.52.001", "001")  # Type: rémunération brute
        self._ajouter_rubrique(s52, "S21.G00.52.002", str(remun.brut_soumis.quantize(Decimal("0.01"))))

        # Net fiscal
        s52_net = ET.SubElement(parent, "S21.G00.52")
        self._ajouter_rubrique(s52_net, "S21.G00.52.001", "002")  # Type: net imposable
        self._ajouter_rubrique(s52_net, "S21.G00.52.002", str(remun.net_imposable.quantize(Decimal("0.01"))))

    def _ajouter_bloc_cotisation(self, parent: ET.Element, cotis: CotisationDSN):
        """Ajoute un bloc de cotisation individuelle (S21.G00.78)."""
        s78 = ET.SubElement(parent, "S21.G00.78")
        self._ajouter_rubrique(s78, "S21.G00.78.001", cotis.code_cotisation)
        self._ajouter_rubrique(s78, "S21.G00.78.002", cotis.identifiant_organisme)
        self._ajouter_rubrique(s78, "S21.G00.78.003", str(cotis.montant_assiette.quantize(Decimal("0.01"))))
        self._ajouter_rubrique(s78, "S21.G00.78.004", str(cotis.montant_cotisation.quantize(Decimal("0.01"))))

    def _ajouter_cotisations_agregees(
        self,
        parent: ET.Element,
        cotisations: dict[str, list[CotisationDSN]],
    ):
        """Ajoute les cotisations agrégées établissement (S21.G00.22/23)."""
        # Agréger par organisme et code
        agregats = {}
        for nir, cotis_list in cotisations.items():
            for cotis in cotis_list:
                key = (cotis.identifiant_organisme, cotis.code_cotisation)
                if key not in agregats:
                    agregats[key] = {
                        "assiette": Decimal("0"),
                        "montant": Decimal("0"),
                    }
                agregats[key]["assiette"] += cotis.montant_assiette
                agregats[key]["montant"] += cotis.montant_cotisation

        # Écrire les agrégats
        for (org, code), vals in agregats.items():
            s22 = ET.SubElement(parent, "S21.G00.22")
            self._ajouter_rubrique(s22, "S21.G00.22.001", org)

            s23 = ET.SubElement(s22, "S21.G00.23")
            self._ajouter_rubrique(s23, "S21.G00.23.001", code)
            self._ajouter_rubrique(s23, "S21.G00.23.002", str(vals["assiette"].quantize(Decimal("0.01"))))
            self._ajouter_rubrique(s23, "S21.G00.23.004", str(vals["montant"].quantize(Decimal("0.01"))))

    def _ajouter_bloc_paiement(self, parent: ET.Element, paiement: PaiementDSN):
        """Ajoute un bloc de paiement (S21.G00.55)."""
        s55 = ET.SubElement(parent, "S21.G00.55")
        self._ajouter_rubrique(s55, "S21.G00.55.001", paiement.date_versement.strftime("%d%m%Y"))
        self._ajouter_rubrique(s55, "S21.G00.55.002", str(paiement.montant.quantize(Decimal("0.01"))))
        self._ajouter_rubrique(s55, "S21.G00.55.003", paiement.mode_paiement)

    def _ajouter_indemnite(self, parent: ET.Element, type_code: str, montant: Decimal):
        """Ajoute un bloc d'indemnité (S21.G00.63)."""
        s63 = ET.SubElement(parent, "S21.G00.63")
        self._ajouter_rubrique(s63, "S21.G00.63.001", type_code)
        self._ajouter_rubrique(s63, "S21.G00.63.002", str(montant.quantize(Decimal("0.01"))))

    def _ajouter_rubrique(self, parent: ET.Element, code: str, valeur: str):
        """Ajoute une rubrique DSN."""
        rubrique = ET.SubElement(parent, "Rubrique")
        rubrique.set("code", code)
        rubrique.text = valeur

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def valider_dsn(self, contenu_xml: str) -> tuple[bool, list[str]]:
        """
        Valide le contenu DSN généré.

        Returns:
            Tuple (est_valide, liste_erreurs)
        """
        erreurs = []

        try:
            root = ET.fromstring(contenu_xml)

            # Vérifier la présence des blocs obligatoires
            if root.find(".//S10.G00.00") is None:
                erreurs.append("Bloc S10 (Envoi) manquant")

            if root.find(".//S20.G00.05") is None:
                erreurs.append("Bloc S20 (Entreprise) manquant")

            if root.find(".//S21.G00.06") is None:
                erreurs.append("Bloc S21 (Établissement) manquant")

            # Valider NIR des salariés
            for s30 in root.findall(".//S21.G00.30"):
                nir_rubrique = s30.find("Rubrique[@code='S21.G00.30.001']")
                if nir_rubrique is not None:
                    nir = nir_rubrique.text
                    if not nir or len(nir.replace(" ", "")) != 15:
                        erreurs.append(f"NIR invalide: {nir}")

        except ET.ParseError as e:
            erreurs.append(f"Erreur XML: {e}")

        return len(erreurs) == 0, erreurs

    # =========================================================================
    # EXPORT
    # =========================================================================

    def exporter_fichier(
        self,
        contenu_xml: str,
        nom_fichier: str = None,
    ) -> tuple[str, str]:
        """
        Prépare le fichier DSN pour envoi.

        Returns:
            Tuple (nom_fichier, hash_md5)
        """
        if not nom_fichier:
            now = datetime.now()
            nom_fichier = f"DSN_{self.entreprise.siren}_{now.strftime('%Y%m%d_%H%M%S')}.xml"

        # Calculer le hash
        hash_md5 = hashlib.md5(contenu_xml.encode("utf-8")).hexdigest()

        return nom_fichier, hash_md5
