"""
AZALSCORE - Conformité Fiscale Avancée France
==============================================
Règles fiscales avancées pour la France et l'Union Européenne.

Fonctionnalités:
- Règles de territorialité TVA
- Autoliquidation TVA
- Échanges intracommunautaires (DEB/DES)
- OSS/IOSS (One-Stop-Shop)
- Retenue à la source (RAS)
- Prix de transfert
- CbCR (Country-by-Country Reporting)

Références:
- CGI articles 256-298
- Directive TVA 2006/112/CE
- BOI-TVA-CHAMP
- BOI-TVA-DECLA-20
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class TypeOperation(str, Enum):
    """Types d'opérations TVA."""
    VENTE_FRANCE = "VENTE_FRANCE"
    VENTE_UE_B2B = "VENTE_UE_B2B"
    VENTE_UE_B2C = "VENTE_UE_B2C"
    VENTE_EXPORT = "VENTE_EXPORT"
    ACHAT_FRANCE = "ACHAT_FRANCE"
    ACHAT_UE = "ACHAT_UE"
    IMPORT = "IMPORT"
    PRESTATION_SERVICE_UE = "PRESTATION_SERVICE_UE"
    AUTOLIQUIDATION = "AUTOLIQUIDATION"


class TypeBien(str, Enum):
    """Types de biens pour DEB."""
    MARCHANDISE = "MARCHANDISE"
    TRAVAIL_A_FACON = "TRAVAIL_A_FACON"
    REPARATION = "REPARATION"
    LOCATION = "LOCATION"
    LEASING = "LEASING"


class RegimeTVA(str, Enum):
    """Régimes TVA."""
    REEL_NORMAL = "REEL_NORMAL"
    REEL_SIMPLIFIE = "REEL_SIMPLIFIE"
    FRANCHISE_BASE = "FRANCHISE_BASE"
    AUTO_ENTREPRENEUR = "AUTO_ENTREPRENEUR"


class NatureTransaction(str, Enum):
    """Nature de transaction pour DEB."""
    ACHAT_VENTE = "11"
    RETOUR = "21"
    ECHANGE_GRATUIT = "31"
    TRAVAIL_A_FACON = "41"
    REPARATION = "51"
    LOCATION = "71"
    LEASING = "72"
    TRANSFERT_STOCK = "90"


# ============================================================================
# CODES PAYS UE
# ============================================================================

PAYS_UE = {
    "AT": "Autriche",
    "BE": "Belgique",
    "BG": "Bulgarie",
    "CY": "Chypre",
    "CZ": "République tchèque",
    "DE": "Allemagne",
    "DK": "Danemark",
    "EE": "Estonie",
    "ES": "Espagne",
    "FI": "Finlande",
    "FR": "France",
    "GR": "Grèce",
    "HR": "Croatie",
    "HU": "Hongrie",
    "IE": "Irlande",
    "IT": "Italie",
    "LT": "Lituanie",
    "LU": "Luxembourg",
    "LV": "Lettonie",
    "MT": "Malte",
    "NL": "Pays-Bas",
    "PL": "Pologne",
    "PT": "Portugal",
    "RO": "Roumanie",
    "SE": "Suède",
    "SI": "Slovénie",
    "SK": "Slovaquie",
}

# Seuils ventes à distance B2C par pays (EUR)
SEUILS_VENTE_DISTANCE = {
    "AT": 35000, "BE": 35000, "BG": 35000, "CY": 35000, "CZ": 35000,
    "DE": 100000, "DK": 35000, "EE": 35000, "ES": 35000, "FI": 35000,
    "FR": 35000, "GR": 35000, "HR": 35000, "HU": 35000, "IE": 35000,
    "IT": 35000, "LT": 35000, "LU": 35000, "LV": 35000, "MT": 35000,
    "NL": 100000, "PL": 35000, "PT": 35000, "RO": 35000, "SE": 35000,
    "SI": 35000, "SK": 35000,
}

# Seuil global OSS (10 000 EUR depuis 2021)
SEUIL_OSS_GLOBAL = Decimal("10000")


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ReglesTerritoralite:
    """Résultat de l'analyse de territorialité TVA."""
    operation_type: TypeOperation
    lieu_imposition: str  # Code pays
    tva_applicable: bool
    taux_tva: Decimal
    autoliquidation: bool
    mention_facture: str
    code_regime: str
    explication: str


@dataclass
class LigneDEB:
    """Ligne de Déclaration d'Échanges de Biens."""
    flux: str  # "INTRODUCTION" ou "EXPEDITION"
    periode: str  # YYYYMM
    pays_partenaire: str  # Code ISO 2
    valeur_fiscale: Decimal
    valeur_statistique: Decimal | None = None
    masse_nette: Decimal | None = None  # kg
    unites_supplementaires: Decimal | None = None
    nature_transaction: str = "11"
    mode_transport: str = "3"  # 3 = route
    departement: str | None = None
    pays_origine: str | None = None
    regime: str = "21"  # 21 = régime normal
    nomenclature_nc8: str | None = None
    numero_tva_partenaire: str | None = None


@dataclass
class LigneESL:
    """Ligne de European Sales List (État récapitulatif)."""
    periode: str  # YYYYMM
    pays_client: str
    numero_tva_client: str
    montant_ht: Decimal
    type_operation: str  # "B" = biens, "S" = services, "T" = triangulaire


@dataclass
class DeclarationDEB:
    """Déclaration d'Échanges de Biens complète."""
    siren: str
    periode: str
    flux: str
    niveau: str  # "1" simplifié, "4" détaillé
    lignes: list[LigneDEB] = field(default_factory=list)
    total_valeur_fiscale: Decimal = Decimal("0")
    total_valeur_statistique: Decimal = Decimal("0")
    date_generation: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DeclarationOSS:
    """Déclaration OSS (One-Stop-Shop)."""
    numero_oss: str
    periode_trimestre: str  # YYYYQ1, YYYYQ2, etc.
    pays_identification: str = "FR"
    lignes_par_pays: dict = field(default_factory=dict)
    total_tva: Decimal = Decimal("0")
    date_generation: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AnalysePrixTransfert:
    """Résultat d'analyse prix de transfert."""
    transaction_id: str
    entite_source: str
    entite_cible: str
    pays_source: str
    pays_cible: str
    montant_transaction: Decimal
    methode_appliquee: str  # CUP, TNMM, Cost+, Resale-, PSM
    marge_calculee: Decimal
    dans_plage_pleine_concurrence: bool
    ajustement_suggere: Decimal
    risques: list[str] = field(default_factory=list)


# ============================================================================
# SERVICE CONFORMITÉ FISCALE AVANCÉE
# ============================================================================

class ConformiteFiscaleAvanceeService:
    """Service de conformité fiscale avancée France."""

    # Seuils DEB (2024)
    SEUIL_DEB_INTRODUCTION = Decimal("460000")  # EUR/an
    SEUIL_DEB_EXPEDITION = Decimal("460000")    # EUR/an

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # TERRITORIALITÉ TVA
    # ========================================================================

    def analyser_territorialite(
        self,
        type_operation: str,
        pays_vendeur: str,
        pays_acheteur: str,
        type_bien_ou_service: str,
        acheteur_assujetti: bool,
        numero_tva_acheteur: str | None = None,
        montant_ht: Decimal = Decimal("0"),
        lieu_prestation: str | None = None
    ) -> ReglesTerritoralite:
        """
        Analyser la territorialité d'une opération TVA.

        Args:
            type_operation: "VENTE" ou "ACHAT"
            pays_vendeur: Code ISO 2 du pays vendeur
            pays_acheteur: Code ISO 2 du pays acheteur
            type_bien_ou_service: "BIEN" ou "SERVICE"
            acheteur_assujetti: True si l'acheteur est assujetti à la TVA
            numero_tva_acheteur: Numéro de TVA intracommunautaire
            montant_ht: Montant HT de l'opération
            lieu_prestation: Code pays du lieu de prestation (pour services)
        """
        # Vente de biens France -> France
        if type_operation == "VENTE" and pays_vendeur == "FR" and pays_acheteur == "FR":
            return ReglesTerritoralite(
                operation_type=TypeOperation.VENTE_FRANCE,
                lieu_imposition="FR",
                tva_applicable=True,
                taux_tva=Decimal("20.00"),
                autoliquidation=False,
                mention_facture="",
                code_regime="01",
                explication="Vente intérieure France - TVA française applicable"
            )

        # Livraison intracommunautaire (LIC) B2B
        if (type_operation == "VENTE" and pays_vendeur == "FR"
            and pays_acheteur in PAYS_UE and pays_acheteur != "FR"
            and acheteur_assujetti and numero_tva_acheteur):

            return ReglesTerritoralite(
                operation_type=TypeOperation.VENTE_UE_B2B,
                lieu_imposition=pays_acheteur,
                tva_applicable=False,
                taux_tva=Decimal("0"),
                autoliquidation=True,
                mention_facture="Exonération TVA - Art. 262 ter I CGI - Livraison intracommunautaire",
                code_regime="06",
                explication=f"Livraison intracommunautaire vers {PAYS_UE.get(pays_acheteur, pays_acheteur)} - TVA autoliquidée par l'acheteur"
            )

        # Vente à distance B2C UE (sous seuil OSS)
        if (type_operation == "VENTE" and pays_vendeur == "FR"
            and pays_acheteur in PAYS_UE and pays_acheteur != "FR"
            and not acheteur_assujetti):

            return ReglesTerritoralite(
                operation_type=TypeOperation.VENTE_UE_B2C,
                lieu_imposition=pays_acheteur,
                tva_applicable=True,
                taux_tva=self._get_taux_tva_pays(pays_acheteur),
                autoliquidation=False,
                mention_facture=f"TVA due dans le pays de destination ({pays_acheteur})",
                code_regime="21",
                explication=f"Vente à distance B2C vers {PAYS_UE.get(pays_acheteur)} - TVA du pays de destination via OSS"
            )

        # Export hors UE
        if (type_operation == "VENTE" and pays_vendeur == "FR"
            and pays_acheteur not in PAYS_UE):

            return ReglesTerritoralite(
                operation_type=TypeOperation.VENTE_EXPORT,
                lieu_imposition="",
                tva_applicable=False,
                taux_tva=Decimal("0"),
                autoliquidation=False,
                mention_facture="Exonération TVA - Art. 262 I CGI - Exportation",
                code_regime="04",
                explication=f"Exportation hors UE vers {pays_acheteur} - Exonération de TVA"
            )

        # Acquisition intracommunautaire (AIC)
        if (type_operation == "ACHAT" and pays_vendeur in PAYS_UE
            and pays_vendeur != "FR" and pays_acheteur == "FR"):

            return ReglesTerritoralite(
                operation_type=TypeOperation.ACHAT_UE,
                lieu_imposition="FR",
                tva_applicable=True,
                taux_tva=Decimal("20.00"),
                autoliquidation=True,
                mention_facture="Acquisition intracommunautaire - TVA autoliquidée",
                code_regime="19",
                explication=f"Acquisition intracommunautaire depuis {PAYS_UE.get(pays_vendeur, pays_vendeur)} - Autoliquidation en France"
            )

        # Import hors UE
        if (type_operation == "ACHAT" and pays_vendeur not in PAYS_UE
            and pays_acheteur == "FR"):

            return ReglesTerritoralite(
                operation_type=TypeOperation.IMPORT,
                lieu_imposition="FR",
                tva_applicable=True,
                taux_tva=Decimal("20.00"),
                autoliquidation=True,
                mention_facture="Import - TVA autoliquidée à la douane ou en déclaration",
                code_regime="11",
                explication=f"Importation depuis {pays_vendeur} - TVA autoliquidée"
            )

        # Prestation de services B2B UE
        if (type_operation == "VENTE" and type_bien_ou_service == "SERVICE"
            and pays_vendeur == "FR" and pays_acheteur in PAYS_UE
            and pays_acheteur != "FR" and acheteur_assujetti):

            return ReglesTerritoralite(
                operation_type=TypeOperation.PRESTATION_SERVICE_UE,
                lieu_imposition=pays_acheteur,
                tva_applicable=False,
                taux_tva=Decimal("0"),
                autoliquidation=True,
                mention_facture="TVA due par le preneur - Art. 283-2 CGI",
                code_regime="30",
                explication=f"Prestation de services B2B vers {PAYS_UE.get(pays_acheteur)} - Autoliquidation par le preneur"
            )

        # Défaut: vente intérieure
        return ReglesTerritoralite(
            operation_type=TypeOperation.VENTE_FRANCE,
            lieu_imposition="FR",
            tva_applicable=True,
            taux_tva=Decimal("20.00"),
            autoliquidation=False,
            mention_facture="",
            code_regime="01",
            explication="Opération par défaut - TVA française applicable"
        )

    def _get_taux_tva_pays(self, pays: str) -> Decimal:
        """Obtenir le taux TVA standard d'un pays UE."""
        taux_tva_ue = {
            "AT": Decimal("20.00"), "BE": Decimal("21.00"), "BG": Decimal("20.00"),
            "CY": Decimal("19.00"), "CZ": Decimal("21.00"), "DE": Decimal("19.00"),
            "DK": Decimal("25.00"), "EE": Decimal("22.00"), "ES": Decimal("21.00"),
            "FI": Decimal("24.00"), "FR": Decimal("20.00"), "GR": Decimal("24.00"),
            "HR": Decimal("25.00"), "HU": Decimal("27.00"), "IE": Decimal("23.00"),
            "IT": Decimal("22.00"), "LT": Decimal("21.00"), "LU": Decimal("17.00"),
            "LV": Decimal("21.00"), "MT": Decimal("18.00"), "NL": Decimal("21.00"),
            "PL": Decimal("23.00"), "PT": Decimal("23.00"), "RO": Decimal("19.00"),
            "SE": Decimal("25.00"), "SI": Decimal("22.00"), "SK": Decimal("20.00"),
        }
        return taux_tva_ue.get(pays, Decimal("20.00"))

    # ========================================================================
    # VALIDATION NUMÉRO TVA
    # ========================================================================

    def valider_numero_tva(self, numero_tva: str) -> dict:
        """
        Valider un numéro de TVA intracommunautaire.

        Args:
            numero_tva: Numéro de TVA à valider (ex: FR12345678901)

        Returns:
            Dict avec validité et informations
        """
        if not numero_tva or len(numero_tva) < 4:
            return {
                "valide": False,
                "numero": numero_tva,
                "erreur": "Numéro trop court"
            }

        pays = numero_tva[:2].upper()
        numero = numero_tva[2:]

        if pays not in PAYS_UE:
            return {
                "valide": False,
                "numero": numero_tva,
                "pays": pays,
                "erreur": f"Code pays {pays} non reconnu dans l'UE"
            }

        # Validation format par pays
        validations = {
            "FR": (lambda n: len(n) == 11 and n[:2].isalpha() or n[:2].isdigit(), "FRXX999999999"),
            "DE": (lambda n: len(n) == 9 and n.isdigit(), "DE999999999"),
            "BE": (lambda n: len(n) == 10 and n.isdigit(), "BE9999999999"),
            "ES": (lambda n: len(n) == 9, "ESX9999999X"),
            "IT": (lambda n: len(n) == 11 and n.isdigit(), "IT99999999999"),
            "NL": (lambda n: len(n) == 12, "NL999999999B99"),
        }

        if pays in validations:
            check_func, format_attendu = validations[pays]
            if not check_func(numero):
                return {
                    "valide": False,
                    "numero": numero_tva,
                    "pays": pays,
                    "erreur": f"Format invalide. Attendu: {format_attendu}"
                }

        # Pour une validation complète, il faudrait appeler le service VIES
        return {
            "valide": True,
            "numero": numero_tva,
            "pays": pays,
            "pays_nom": PAYS_UE.get(pays, pays),
            "note": "Validation de format OK. Pour validation complète, utilisez VIES."
        }

    # ========================================================================
    # DEB (DÉCLARATION D'ÉCHANGES DE BIENS)
    # ========================================================================

    def generer_deb(
        self,
        siren: str,
        periode: str,
        flux: str,
        operations: list[dict]
    ) -> DeclarationDEB:
        """
        Générer une Déclaration d'Échanges de Biens (DEB/EMEBI).

        Args:
            siren: SIREN de l'entreprise
            periode: Période YYYYMM
            flux: "INTRODUCTION" ou "EXPEDITION"
            operations: Liste des opérations à déclarer

        Returns:
            DeclarationDEB complète
        """
        logger.info(
            "Generating DEB | tenant=%s siren=%s period=%s flux=%s",
            self.tenant_id, siren, periode, flux
        )

        deb = DeclarationDEB(
            siren=siren,
            periode=periode,
            flux=flux,
            niveau="4"  # Niveau détaillé
        )

        for op in operations:
            ligne = LigneDEB(
                flux=flux,
                periode=periode,
                pays_partenaire=op.get("pays_partenaire", ""),
                valeur_fiscale=Decimal(str(op.get("valeur_fiscale", 0))),
                valeur_statistique=Decimal(str(op.get("valeur_statistique", 0))) if op.get("valeur_statistique") else None,
                masse_nette=Decimal(str(op.get("masse_nette", 0))) if op.get("masse_nette") else None,
                unites_supplementaires=Decimal(str(op.get("unites_sup", 0))) if op.get("unites_sup") else None,
                nature_transaction=op.get("nature_transaction", "11"),
                mode_transport=op.get("mode_transport", "3"),
                departement=op.get("departement"),
                pays_origine=op.get("pays_origine"),
                regime=op.get("regime", "21"),
                nomenclature_nc8=op.get("nomenclature_nc8"),
                numero_tva_partenaire=op.get("numero_tva")
            )

            deb.lignes.append(ligne)
            deb.total_valeur_fiscale += ligne.valeur_fiscale
            if ligne.valeur_statistique:
                deb.total_valeur_statistique += ligne.valeur_statistique

        logger.info(
            "DEB generated | lines=%s total_fiscal=%s",
            len(deb.lignes), deb.total_valeur_fiscale
        )

        return deb

    def exporter_deb_xml(self, deb: DeclarationDEB) -> str:
        """Exporter la DEB au format XML EMEBI."""
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<Declaration xmlns="http://www.douane.gouv.fr/emebi">',
            f'  <SIREN>{deb.siren}</SIREN>',
            f'  <Periode>{deb.periode}</Periode>',
            f'  <Flux>{deb.flux}</Flux>',
            f'  <Niveau>{deb.niveau}</Niveau>',
            '  <Lignes>'
        ]

        for i, ligne in enumerate(deb.lignes, 1):
            xml_lines.extend([
                f'    <Ligne numero="{i}">',
                f'      <PaysPartenaire>{ligne.pays_partenaire}</PaysPartenaire>',
                f'      <ValeurFiscale>{ligne.valeur_fiscale}</ValeurFiscale>',
            ])

            if ligne.valeur_statistique:
                xml_lines.append(f'      <ValeurStatistique>{ligne.valeur_statistique}</ValeurStatistique>')
            if ligne.masse_nette:
                xml_lines.append(f'      <MasseNette>{ligne.masse_nette}</MasseNette>')
            if ligne.nomenclature_nc8:
                xml_lines.append(f'      <NomenclatureNC8>{ligne.nomenclature_nc8}</NomenclatureNC8>')

            xml_lines.extend([
                f'      <NatureTransaction>{ligne.nature_transaction}</NatureTransaction>',
                f'      <ModeTransport>{ligne.mode_transport}</ModeTransport>',
                f'      <Regime>{ligne.regime}</Regime>',
                '    </Ligne>'
            ])

        xml_lines.extend([
            '  </Lignes>',
            f'  <TotalValeurFiscale>{deb.total_valeur_fiscale}</TotalValeurFiscale>',
            '</Declaration>'
        ])

        return '\n'.join(xml_lines)

    # ========================================================================
    # ÉTAT RÉCAPITULATIF TVA (ESL)
    # ========================================================================

    def generer_etat_recapitulatif(
        self,
        siren: str,
        periode: str,
        operations: list[dict]
    ) -> list[LigneESL]:
        """
        Générer l'État Récapitulatif des clients intracommunautaires.

        Args:
            siren: SIREN de l'entreprise
            periode: Période YYYYMM
            operations: Liste des opérations (livraisons + services B2B UE)

        Returns:
            Liste des lignes ESL
        """
        lignes = []

        # Agrégation par client
        totaux_par_client: dict[str, dict] = {}

        for op in operations:
            num_tva = op.get("numero_tva_client", "")
            if not num_tva:
                continue

            pays = num_tva[:2] if len(num_tva) >= 2 else ""
            type_op = "B" if op.get("type") == "BIEN" else "S"

            key = f"{num_tva}_{type_op}"
            if key not in totaux_par_client:
                totaux_par_client[key] = {
                    "pays": pays,
                    "numero_tva": num_tva,
                    "type": type_op,
                    "montant": Decimal("0")
                }

            totaux_par_client[key]["montant"] += Decimal(str(op.get("montant_ht", 0)))

        # Créer les lignes
        for data in totaux_par_client.values():
            lignes.append(LigneESL(
                periode=periode,
                pays_client=data["pays"],
                numero_tva_client=data["numero_tva"],
                montant_ht=data["montant"],
                type_operation=data["type"]
            ))

        logger.info(
            "ESL generated | period=%s lines=%s",
            periode, len(lignes)
        )

        return lignes

    # ========================================================================
    # OSS (ONE-STOP-SHOP)
    # ========================================================================

    def generer_declaration_oss(
        self,
        numero_oss: str,
        trimestre: str,
        ventes_par_pays: dict[str, list[dict]]
    ) -> DeclarationOSS:
        """
        Générer une déclaration OSS pour ventes à distance B2C UE.

        Args:
            numero_oss: Numéro d'identification OSS
            trimestre: Trimestre (YYYY-Q1, YYYY-Q2, etc.)
            ventes_par_pays: Dict {pays: [{montant_ht, taux_tva, montant_tva}]}

        Returns:
            DeclarationOSS complète
        """
        declaration = DeclarationOSS(
            numero_oss=numero_oss,
            periode_trimestre=trimestre
        )

        for pays, ventes in ventes_par_pays.items():
            if pays not in PAYS_UE or pays == "FR":
                continue

            total_ht = Decimal("0")
            total_tva = Decimal("0")
            lignes_pays = []

            for vente in ventes:
                ht = Decimal(str(vente.get("montant_ht", 0)))
                taux = Decimal(str(vente.get("taux_tva", self._get_taux_tva_pays(pays))))
                tva = ht * taux / 100

                total_ht += ht
                total_tva += tva

                lignes_pays.append({
                    "montant_ht": ht,
                    "taux_tva": taux,
                    "montant_tva": tva.quantize(Decimal("0.01"))
                })

            declaration.lignes_par_pays[pays] = {
                "pays_nom": PAYS_UE.get(pays, pays),
                "total_ht": total_ht,
                "total_tva": total_tva.quantize(Decimal("0.01")),
                "taux_standard": self._get_taux_tva_pays(pays),
                "lignes": lignes_pays
            }

            declaration.total_tva += total_tva

        declaration.total_tva = declaration.total_tva.quantize(Decimal("0.01"))

        logger.info(
            "OSS declaration generated | quarter=%s countries=%s total_vat=%s",
            trimestre, len(declaration.lignes_par_pays), declaration.total_tva
        )

        return declaration

    # ========================================================================
    # AUTOLIQUIDATION
    # ========================================================================

    def calculer_autoliquidation(
        self,
        montant_ht: Decimal,
        type_operation: TypeOperation,
        taux_tva: Decimal = Decimal("20.00")
    ) -> dict:
        """
        Calculer la TVA autoliquidée pour une opération.

        Args:
            montant_ht: Montant HT de l'opération
            type_operation: Type d'opération
            taux_tva: Taux de TVA applicable

        Returns:
            Dict avec montants et écritures comptables
        """
        montant_tva = (montant_ht * taux_tva / 100).quantize(Decimal("0.01"))

        # Selon le type d'opération, définir les comptes
        if type_operation == TypeOperation.ACHAT_UE:
            compte_tva_deductible = "44566"  # TVA déductible sur ABS
            compte_tva_collectee = "4452"     # TVA intracommunautaire
            libelle = "Acquisition intracommunautaire"
        elif type_operation == TypeOperation.IMPORT:
            compte_tva_deductible = "44566"
            compte_tva_collectee = "4455"     # TVA à décaisser
            libelle = "Importation"
        elif type_operation == TypeOperation.PRESTATION_SERVICE_UE:
            compte_tva_deductible = "44566"
            compte_tva_collectee = "4452"
            libelle = "Prestation de services UE"
        else:
            compte_tva_deductible = "44566"
            compte_tva_collectee = "4457"
            libelle = "Autoliquidation"

        return {
            "montant_ht": montant_ht,
            "taux_tva": taux_tva,
            "montant_tva": montant_tva,
            "type_operation": type_operation.value,
            "ecritures_comptables": [
                {
                    "compte": compte_tva_deductible,
                    "libelle": f"TVA déductible - {libelle}",
                    "debit": montant_tva,
                    "credit": Decimal("0")
                },
                {
                    "compte": compte_tva_collectee,
                    "libelle": f"TVA autoliquidée - {libelle}",
                    "debit": Decimal("0"),
                    "credit": montant_tva
                }
            ],
            "impact_ca3": {
                "ligne_08": montant_ht,  # AIC ligne 08
                "ligne_17": montant_tva,  # TVA sur AIC
                "ligne_20": montant_tva   # TVA déductible
            }
        }

    # ========================================================================
    # PRIX DE TRANSFERT
    # ========================================================================

    def analyser_prix_transfert(
        self,
        transaction_id: str,
        entite_source: str,
        entite_cible: str,
        pays_source: str,
        pays_cible: str,
        montant_transaction: Decimal,
        type_transaction: str,
        marge_realisee: Decimal,
        comparables: list[Decimal] | None = None
    ) -> AnalysePrixTransfert:
        """
        Analyser une transaction au regard des règles de prix de transfert.

        Args:
            transaction_id: ID de la transaction
            entite_source: Nom de l'entité source
            entite_cible: Nom de l'entité cible
            pays_source: Code pays source
            pays_cible: Code pays cible
            montant_transaction: Montant de la transaction
            type_transaction: Type (VENTE, SERVICE, LICENCE, etc.)
            marge_realisee: Marge brute ou nette réalisée (%)
            comparables: Liste de marges comparables du marché

        Returns:
            AnalysePrixTransfert
        """
        risques = []

        # Déterminer la méthode applicable
        if type_transaction == "VENTE":
            methode = "TNMM"  # Transactional Net Margin Method
        elif type_transaction == "SERVICE":
            methode = "Cost+"  # Cost Plus
        elif type_transaction == "LICENCE":
            methode = "CUP"   # Comparable Uncontrolled Price
        else:
            methode = "TNMM"

        # Calculer la plage de pleine concurrence
        if comparables and len(comparables) >= 4:
            comparables_sorted = sorted(comparables)
            q1 = comparables_sorted[len(comparables_sorted) // 4]
            q3 = comparables_sorted[3 * len(comparables_sorted) // 4]
            mediane = comparables_sorted[len(comparables_sorted) // 2]
        else:
            # Marges par défaut selon type
            defaults = {
                "VENTE": (Decimal("2"), Decimal("5"), Decimal("3.5")),
                "SERVICE": (Decimal("5"), Decimal("15"), Decimal("10")),
                "LICENCE": (Decimal("3"), Decimal("8"), Decimal("5")),
            }
            q1, q3, mediane = defaults.get(type_transaction, (Decimal("2"), Decimal("10"), Decimal("5")))

        # Vérifier si la marge est dans la plage
        dans_plage = q1 <= marge_realisee <= q3

        # Calculer l'ajustement suggéré
        ajustement = Decimal("0")
        if not dans_plage:
            # Ramener à la médiane
            ajustement_pct = mediane - marge_realisee
            ajustement = (montant_transaction * ajustement_pct / 100).quantize(Decimal("0.01"))

            risques.append(f"Marge hors plage de pleine concurrence ({q1}% - {q3}%)")

        # Autres risques
        if montant_transaction > Decimal("100000"):
            risques.append("Transaction significative nécessitant documentation")

        # Risque pays
        pays_risque = ["LU", "IE", "NL", "CH", "SG", "HK"]
        if pays_cible in pays_risque:
            risques.append(f"Pays à fiscalité avantageuse ({pays_cible})")

        return AnalysePrixTransfert(
            transaction_id=transaction_id,
            entite_source=entite_source,
            entite_cible=entite_cible,
            pays_source=pays_source,
            pays_cible=pays_cible,
            montant_transaction=montant_transaction,
            methode_appliquee=methode,
            marge_calculee=marge_realisee,
            dans_plage_pleine_concurrence=dans_plage,
            ajustement_suggere=ajustement,
            risques=risques
        )

    # ========================================================================
    # RETENUE À LA SOURCE
    # ========================================================================

    def calculer_retenue_source(
        self,
        type_revenu: str,
        pays_beneficiaire: str,
        montant_brut: Decimal,
        convention_applicable: bool = True
    ) -> dict:
        """
        Calculer la retenue à la source sur revenus versés à l'étranger.

        Args:
            type_revenu: DIVIDENDES, INTERETS, REDEVANCES, SERVICES
            pays_beneficiaire: Code pays du bénéficiaire
            montant_brut: Montant brut versé
            convention_applicable: Si convention fiscale applicable

        Returns:
            Dict avec montant RAS et références
        """
        # Taux de droit commun (sans convention)
        taux_droit_commun = {
            "DIVIDENDES": Decimal("25"),
            "INTERETS": Decimal("0"),  # Exonérés en général
            "REDEVANCES": Decimal("25"),
            "SERVICES": Decimal("25"),
        }

        # Taux conventionnels réduits (exemples)
        taux_conventionnels = {
            ("DIVIDENDES", "DE"): Decimal("15"),
            ("DIVIDENDES", "GB"): Decimal("15"),
            ("DIVIDENDES", "US"): Decimal("15"),
            ("REDEVANCES", "DE"): Decimal("0"),
            ("REDEVANCES", "GB"): Decimal("0"),
            ("REDEVANCES", "US"): Decimal("0"),
        }

        # Déterminer le taux applicable
        if convention_applicable and (type_revenu, pays_beneficiaire) in taux_conventionnels:
            taux = taux_conventionnels[(type_revenu, pays_beneficiaire)]
            source = f"Convention fiscale France-{pays_beneficiaire}"
        else:
            taux = taux_droit_commun.get(type_revenu, Decimal("25"))
            source = "Droit commun - CGI art. 119 bis"

        montant_ras = (montant_brut * taux / 100).quantize(Decimal("0.01"))
        montant_net = montant_brut - montant_ras

        return {
            "type_revenu": type_revenu,
            "pays_beneficiaire": pays_beneficiaire,
            "montant_brut": montant_brut,
            "taux_ras": taux,
            "montant_ras": montant_ras,
            "montant_net": montant_net,
            "base_legale": source,
            "declaration_requise": "Formulaire 2777 mensuel" if montant_ras > 0 else "Aucune"
        }
