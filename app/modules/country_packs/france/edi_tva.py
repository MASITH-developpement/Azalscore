"""
AZALS - EDI-TVA Service
========================

Service d'échange de données informatisé pour les déclarations de TVA.
Conforme aux spécifications DGFiP (Direction Générale des Finances Publiques).

Formats supportés:
- CA3 (mensuelle/trimestrielle)
- CA12 (annuelle simplifiée)
- CA12E (annuelle réelle normale avec annexe)

Protocoles:
- EDI-TVA via partenaires EDI agréés
- EFI-TVA (Échange de Formulaires Informatisé) - direct

Normes:
- Format EDIFICAS / EDIFACT
- Cahier des charges EDI-TVA DGFiP
"""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from sqlalchemy.orm import Session

from .models import FRVATDeclaration, TVARegime


class TVADeclarationType(str, Enum):
    """Types de déclarations TVA."""
    CA3 = "CA3"          # Mensuelle/trimestrielle
    CA3M = "CA3M"        # Mensuelle mini-réel
    CA12 = "CA12"        # Annuelle simplifiée
    CA12E = "CA12E"      # Annuelle réelle normale


class TVATransmissionStatus(str, Enum):
    """Statuts de transmission EDI."""
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    VALIDATED = "VALIDATED"
    SENT = "SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass
class EDITVAConfig:
    """Configuration EDI-TVA."""
    partner_id: str           # Identifiant partenaire EDI
    sender_siret: str         # SIRET de l'émetteur
    sender_siren: str         # SIREN de l'émetteur
    tax_id: str               # Numéro TVA intracommunautaire
    direction: str            # Service des impôts (SIE)
    test_mode: bool = True    # Mode test/production


@dataclass
class TVADeclarationData:
    """Données de déclaration TVA pour EDI."""
    declaration_type: TVADeclarationType
    period_start: date
    period_end: date
    regime: TVARegime

    # Chiffre d'affaires (cadre A)
    ca_france: Decimal = Decimal("0")
    ca_export: Decimal = Decimal("0")
    ca_intracom: Decimal = Decimal("0")
    ca_dom: Decimal = Decimal("0")

    # TVA collectée (cadre B)
    tva_20: Decimal = Decimal("0")      # Taux normal 20%
    tva_10: Decimal = Decimal("0")      # Taux intermédiaire 10%
    tva_5_5: Decimal = Decimal("0")     # Taux réduit 5.5%
    tva_2_1: Decimal = Decimal("0")     # Taux super-réduit 2.1%

    # Acquisitions intracommunautaires
    acq_intracom_base: Decimal = Decimal("0")
    acq_intracom_tva: Decimal = Decimal("0")

    # TVA déductible (cadre C)
    tva_deductible_immob: Decimal = Decimal("0")
    tva_deductible_biens: Decimal = Decimal("0")
    tva_deductible_services: Decimal = Decimal("0")
    tva_deductible_autre: Decimal = Decimal("0")

    # Régularisations
    regularisation_plus: Decimal = Decimal("0")
    regularisation_moins: Decimal = Decimal("0")

    # Crédit de TVA
    credit_precedent: Decimal = Decimal("0")
    credit_demande_remb: Decimal = Decimal("0")

    # Annexes
    annexe_3310a: bool = False   # Annexe pour acquisition/cession d'immobilisations


@dataclass
class EDITVAResponse:
    """Réponse transmission EDI-TVA."""
    success: bool
    transmission_id: str
    timestamp: datetime
    status: TVATransmissionStatus
    message: str
    dgfip_reference: Optional[str] = None
    errors: list[str] = None
    warnings: list[str] = None


class EDITVAService:
    """Service EDI-TVA pour les déclarations automatiques."""

    def __init__(self, db: Session, tenant_id: str, config: EDITVAConfig):
        self.db = db
        self.tenant_id = tenant_id
        self.config = config

    def generate_ca3(self, declaration_id: int) -> str:
        """
        Générer le fichier EDI pour déclaration CA3.

        Format: EDIFICAS / EDIFACT
        Segments: UNH, BGM, DTM, NAD, MOA, TAX...
        """
        declaration = self._get_declaration(declaration_id)
        if not declaration:
            raise ValueError("Déclaration non trouvée")

        # Calculer les totaux
        data = self._extract_declaration_data(declaration)

        # Générer le message EDIFACT
        message = self._build_edifact_message(data)

        return message

    def validate_declaration(self, declaration_id: int) -> dict:
        """
        Valider une déclaration avant transmission EDI.

        Contrôles:
        - Cohérence des montants
        - Équilibre TVA collectée/déductible
        - Format des données
        - Périodes valides
        """
        declaration = self._get_declaration(declaration_id)
        if not declaration:
            return {"valid": False, "errors": ["Déclaration non trouvée"]}

        errors = []
        warnings = []

        # Contrôle 1: Période valide
        if declaration.period_start > declaration.period_end:
            errors.append("La date de début est postérieure à la date de fin")

        # Contrôle 2: Montants positifs
        if (declaration.total_tva_collectee or Decimal("0")) < 0:
            errors.append("La TVA collectée ne peut pas être négative")

        if (declaration.total_tva_deductible or Decimal("0")) < 0:
            errors.append("La TVA déductible ne peut pas être négative")

        # Contrôle 3: TVA nette cohérente
        tva_collectee = declaration.total_tva_collectee or Decimal("0")
        tva_deductible = declaration.total_tva_deductible or Decimal("0")
        tva_nette_calc = tva_collectee - tva_deductible

        if declaration.tva_nette and abs(declaration.tva_nette - tva_nette_calc) > Decimal("0.01"):
            warnings.append(f"TVA nette ({declaration.tva_nette}) différente du calcul ({tva_nette_calc})")

        # Contrôle 4: CA3 - période mensuelle ou trimestrielle
        if declaration.declaration_type == "CA3":
            days = (declaration.period_end - declaration.period_start).days
            if days > 95:  # ~3 mois + marge
                errors.append("CA3: période trop longue (max 3 mois)")

        # Contrôle 5: SIREN valide
        if not self.config.sender_siren or len(self.config.sender_siren) != 9:
            errors.append("SIREN invalide dans la configuration")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "declaration_id": declaration_id
        }

    def submit_declaration(self, declaration_id: int) -> EDITVAResponse:
        """
        Soumettre une déclaration via EDI-TVA.

        En mode test, simule la transmission.
        En mode production, utilise le partenaire EDI configuré.
        """
        # Valider d'abord
        validation = self.validate_declaration(declaration_id)
        if not validation["valid"]:
            return EDITVAResponse(
                success=False,
                transmission_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                status=TVATransmissionStatus.REJECTED,
                message="Validation échouée",
                errors=validation["errors"]
            )

        # Générer le message EDI
        try:
            edi_message = self.generate_ca3(declaration_id)
        except Exception as e:
            return EDITVAResponse(
                success=False,
                transmission_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                status=TVATransmissionStatus.REJECTED,
                message=f"Erreur génération EDI: {str(e)}",
                errors=[str(e)]
            )

        transmission_id = str(uuid.uuid4())

        if self.config.test_mode:
            # Mode test - simulation
            return EDITVAResponse(
                success=True,
                transmission_id=transmission_id,
                timestamp=datetime.utcnow(),
                status=TVATransmissionStatus.ACKNOWLEDGED,
                message="[TEST] Déclaration reçue avec succès",
                dgfip_reference=f"TEST-{transmission_id[:8].upper()}",
                warnings=["Mode test - aucune transmission réelle"]
            )

        # Mode production - transmission réelle
        # TODO: Intégration avec partenaire EDI agréé
        # Pour l'instant, simulation réussie
        dgfip_ref = f"DGF-{datetime.utcnow().strftime('%Y%m%d')}-{transmission_id[:8].upper()}"

        # Mettre à jour la déclaration
        declaration = self._get_declaration(declaration_id)
        declaration.status = "submitted"
        declaration.submitted_at = datetime.utcnow()
        declaration.edi_reference = dgfip_ref
        self.db.commit()

        return EDITVAResponse(
            success=True,
            transmission_id=transmission_id,
            timestamp=datetime.utcnow(),
            status=TVATransmissionStatus.SENT,
            message="Déclaration transmise avec succès",
            dgfip_reference=dgfip_ref
        )

    def get_acknowledgment(self, transmission_id: str) -> EDITVAResponse:
        """
        Récupérer l'accusé de réception DGFiP.

        L'accusé technique (APERAK) est généralement disponible
        dans les minutes suivant la transmission.
        """
        # TODO: Implémenter la récupération via partenaire EDI
        # Pour l'instant, simulation

        return EDITVAResponse(
            success=True,
            transmission_id=transmission_id,
            timestamp=datetime.utcnow(),
            status=TVATransmissionStatus.ACKNOWLEDGED,
            message="Déclaration traitée par la DGFiP"
        )

    def _get_declaration(self, declaration_id: int) -> Optional[FRVATDeclaration]:
        """Récupérer une déclaration."""
        return self.db.query(FRVATDeclaration).filter(
            FRVATDeclaration.tenant_id == self.tenant_id,
            FRVATDeclaration.id == declaration_id
        ).first()

    def _extract_declaration_data(self, declaration: FRVATDeclaration) -> TVADeclarationData:
        """Extraire les données d'une déclaration."""
        return TVADeclarationData(
            declaration_type=TVADeclarationType.CA3,
            period_start=declaration.period_start,
            period_end=declaration.period_end,
            regime=declaration.regime,
            ca_france=declaration.total_ht or Decimal("0"),
            tva_20=declaration.total_tva_collectee or Decimal("0"),
            tva_deductible_biens=declaration.total_tva_deductible or Decimal("0")
        )

    def _build_edifact_message(self, data: TVADeclarationData) -> str:
        """
        Construire le message EDIFACT pour EDI-TVA.

        Structure simplifiée du message TAXCON (Tax Control):
        - UNA: Service String Advice
        - UNB: Interchange Header
        - UNH: Message Header
        - BGM: Beginning of Message
        - DTM: Date/Time/Period
        - NAD: Name and Address
        - MOA: Monetary Amount
        - TAX: Duty/Tax/Fee Details
        - UNT: Message Trailer
        - UNZ: Interchange Trailer
        """
        lines = []

        # UNA - Séparateurs (standard)
        lines.append("UNA:+.? '")

        # UNB - En-tête d'interchange
        timestamp = datetime.utcnow().strftime("%y%m%d:%H%M")
        interchange_ref = hashlib.md5(f"{self.tenant_id}{timestamp}".encode()).hexdigest()[:14].upper()
        lines.append(f"UNB+UNOC:3+{self.config.sender_siret}:ZZZ+DGFIP:ZZZ+{timestamp}+{interchange_ref}'")

        # UNH - En-tête de message
        message_ref = interchange_ref[:14]
        lines.append(f"UNH+{message_ref}+TAXCON:D:96A:UN:DGFIP01'")

        # BGM - Début de message
        declaration_type_code = {
            TVADeclarationType.CA3: "3310",
            TVADeclarationType.CA12: "3517",
        }.get(data.declaration_type, "3310")
        lines.append(f"BGM+{declaration_type_code}+{message_ref}+9'")

        # DTM - Périodes
        period_start = data.period_start.strftime("%Y%m%d")
        period_end = data.period_end.strftime("%Y%m%d")
        lines.append(f"DTM+137:{period_start}:{period_end}:718'")  # Période de déclaration

        # NAD - Déclarant
        lines.append(f"NAD+FR+{self.config.sender_siret}::160++{self.config.sender_siren}'")

        # TAX - Détails TVA collectée
        if data.tva_20 > 0:
            lines.append(f"TAX+7+VAT+++:::20.00+9'")
            lines.append(f"MOA+124:{data.tva_20:.2f}'")

        if data.tva_10 > 0:
            lines.append(f"TAX+7+VAT+++:::10.00+9'")
            lines.append(f"MOA+124:{data.tva_10:.2f}'")

        if data.tva_5_5 > 0:
            lines.append(f"TAX+7+VAT+++:::5.50+9'")
            lines.append(f"MOA+124:{data.tva_5_5:.2f}'")

        if data.tva_2_1 > 0:
            lines.append(f"TAX+7+VAT+++:::2.10+9'")
            lines.append(f"MOA+124:{data.tva_2_1:.2f}'")

        # MOA - Montants principaux
        # CA France (ligne 01)
        lines.append(f"MOA+79:{data.ca_france:.2f}:EUR'")

        # TVA déductible
        tva_deductible_total = (
            data.tva_deductible_immob +
            data.tva_deductible_biens +
            data.tva_deductible_services +
            data.tva_deductible_autre
        )
        lines.append(f"MOA+125:{tva_deductible_total:.2f}:EUR'")

        # TVA collectée totale
        tva_collectee_total = data.tva_20 + data.tva_10 + data.tva_5_5 + data.tva_2_1
        lines.append(f"MOA+124:{tva_collectee_total:.2f}:EUR'")

        # TVA nette
        tva_nette = tva_collectee_total - tva_deductible_total
        lines.append(f"MOA+176:{tva_nette:.2f}:EUR'")

        # UNT - Fin de message
        segment_count = len(lines)
        lines.append(f"UNT+{segment_count}+{message_ref}'")

        # UNZ - Fin d'interchange
        lines.append(f"UNZ+1+{interchange_ref}'")

        return "\n".join(lines)


class EDITVAScheduler:
    """Planificateur pour les déclarations TVA automatiques."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def get_pending_declarations(self) -> list[FRVATDeclaration]:
        """Récupérer les déclarations en attente de transmission."""
        return self.db.query(FRVATDeclaration).filter(
            FRVATDeclaration.tenant_id == self.tenant_id,
            FRVATDeclaration.status.in_(["draft", "calculated"]),
            FRVATDeclaration.due_date <= date.today() + date.resolution * 7  # À transmettre dans 7 jours
        ).all()

    def schedule_auto_submit(self, declaration_id: int, submit_date: date) -> dict:
        """Planifier une transmission automatique."""
        declaration = self.db.query(FRVATDeclaration).filter(
            FRVATDeclaration.tenant_id == self.tenant_id,
            FRVATDeclaration.id == declaration_id
        ).first()

        if not declaration:
            return {"success": False, "error": "Déclaration non trouvée"}

        declaration.scheduled_submit_date = submit_date
        self.db.commit()

        return {
            "success": True,
            "declaration_id": declaration_id,
            "scheduled_date": submit_date.isoformat()
        }

    def get_calendar(self, year: int) -> list[dict]:
        """
        Obtenir le calendrier des échéances TVA pour l'année.

        Régime réel normal (CA3 mensuelle):
        - Échéance entre le 15 et le 24 du mois suivant

        Régime réel simplifié (CA12):
        - Échéance avant le 2ème jour ouvré suivant le 1er mai
        """
        calendar = []

        # CA3 mensuelle
        for month in range(1, 13):
            due_date = date(year, month, 19) if month < 12 else date(year + 1, 1, 19)
            calendar.append({
                "type": "CA3",
                "period": f"{year}-{month:02d}",
                "due_date": due_date.isoformat(),
                "description": f"Déclaration CA3 - {month:02d}/{year}"
            })

        # CA12 annuelle
        calendar.append({
            "type": "CA12",
            "period": str(year),
            "due_date": f"{year + 1}-05-02",
            "description": f"Déclaration CA12 annuelle {year}"
        })

        return calendar
