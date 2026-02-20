"""
Module de Gestion des Notes de Frais - GAP-033

Fonctionnalités complètes de gestion des frais professionnels:
- Saisie mobile des dépenses avec OCR
- Workflow de validation multi-niveaux
- Politiques de dépenses configurables
- Gestion des indemnités kilométriques
- Per diem et forfaits
- Export comptable automatique
- Détection des anomalies
- Rapports et analytics

Conformité:
- URSSAF (barème kilométrique)
- Obligations justificatifs
- TVA récupérable
- Limites déductibilité fiscale

Architecture multi-tenant avec isolation stricte.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
import re


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class ExpenseCategory(Enum):
    """Catégorie de dépense."""
    # Transport
    MILEAGE = "mileage"  # Indemnités kilométriques
    PUBLIC_TRANSPORT = "public_transport"  # Transports en commun
    TAXI_RIDE = "taxi"  # Taxi/VTC
    PARKING = "parking"  # Stationnement
    TOLL = "toll"  # Péages
    RENTAL_CAR = "rental_car"  # Location véhicule
    FUEL = "fuel"  # Carburant

    # Hébergement
    HOTEL = "hotel"  # Hôtel
    AIRBNB = "airbnb"  # Location courte durée

    # Restauration
    RESTAURANT = "restaurant"  # Restaurant
    MEAL_SOLO = "meal_solo"  # Repas seul
    MEAL_BUSINESS = "meal_business"  # Repas d'affaires
    MEAL_TEAM = "meal_team"  # Repas équipe

    # Voyage
    FLIGHT = "flight"  # Billet d'avion
    TRAIN = "train"  # Train
    VISA = "visa"  # Visa
    TRAVEL_INSURANCE = "travel_insurance"  # Assurance voyage

    # Télécommunications
    PHONE = "phone"  # Téléphone
    INTERNET = "internet"  # Internet

    # Fournitures
    OFFICE_SUPPLIES = "office_supplies"  # Fournitures bureau
    IT_EQUIPMENT = "it_equipment"  # Matériel informatique
    BOOKS = "books"  # Livres/formation

    # Divers
    REPRESENTATION = "representation"  # Frais de représentation
    SUBSCRIPTION = "subscription"  # Abonnements
    OTHER = "other"  # Autres


class ExpenseStatus(Enum):
    """Statut d'une note de frais."""
    DRAFT = "draft"  # Brouillon
    SUBMITTED = "submitted"  # Soumise
    PENDING_APPROVAL = "pending_approval"  # En attente validation
    APPROVED = "approved"  # Approuvée
    REJECTED = "rejected"  # Rejetée
    PAID = "paid"  # Remboursée
    CANCELLED = "cancelled"  # Annulée


class PaymentMethod(Enum):
    """Mode de paiement."""
    PERSONAL_CARD = "personal_card"  # Carte personnelle
    COMPANY_CARD = "company_card"  # Carte entreprise
    CASH = "cash"  # Espèces
    COMPANY_ACCOUNT = "company_account"  # Compte entreprise
    MILEAGE = "mileage"  # Indemnité (pas de paiement direct)


class VehicleType(Enum):
    """Type de véhicule pour indemnités kilométriques."""
    CAR_3CV = "car_3cv"  # Auto 3 CV et moins
    CAR_4CV = "car_4cv"  # Auto 4 CV
    CAR_5CV = "car_5cv"  # Auto 5 CV
    CAR_6CV = "car_6cv"  # Auto 6 CV
    CAR_7CV_PLUS = "car_7cv_plus"  # Auto 7 CV et plus
    MOTORCYCLE_50CC = "moto_50cc"  # Moto/scooter <= 50cc
    MOTORCYCLE_125CC = "moto_125cc"  # Moto 51-125cc
    MOTORCYCLE_3_5CV = "moto_3_5cv"  # Moto 3-5 CV
    MOTORCYCLE_5CV_PLUS = "moto_5cv_plus"  # Moto > 5 CV
    BICYCLE = "bicycle"  # Vélo
    ELECTRIC_BICYCLE = "electric_bicycle"  # VAE


class ApprovalLevel(Enum):
    """Niveau d'approbation."""
    MANAGER = "manager"  # Manager direct
    DEPARTMENT_HEAD = "department_head"  # Chef de département
    FINANCE = "finance"  # Direction financière
    CEO = "ceo"  # Direction générale


# ============================================================================
# BARÈMES FISCAUX 2024
# ============================================================================

# Barème kilométrique automobile 2024 (URSSAF)
MILEAGE_RATES_CAR_2024 = {
    VehicleType.CAR_3CV: {
        "up_to_5000": Decimal("0.529"),
        "5001_to_20000": Decimal("0.316"),
        "fixed_5001_to_20000": Decimal("1065"),
        "above_20000": Decimal("0.370"),
    },
    VehicleType.CAR_4CV: {
        "up_to_5000": Decimal("0.606"),
        "5001_to_20000": Decimal("0.340"),
        "fixed_5001_to_20000": Decimal("1330"),
        "above_20000": Decimal("0.407"),
    },
    VehicleType.CAR_5CV: {
        "up_to_5000": Decimal("0.636"),
        "5001_to_20000": Decimal("0.357"),
        "fixed_5001_to_20000": Decimal("1395"),
        "above_20000": Decimal("0.427"),
    },
    VehicleType.CAR_6CV: {
        "up_to_5000": Decimal("0.665"),
        "5001_to_20000": Decimal("0.374"),
        "fixed_5001_to_20000": Decimal("1457"),
        "above_20000": Decimal("0.447"),
    },
    VehicleType.CAR_7CV_PLUS: {
        "up_to_5000": Decimal("0.697"),
        "5001_to_20000": Decimal("0.394"),
        "fixed_5001_to_20000": Decimal("1515"),
        "above_20000": Decimal("0.470"),
    },
}

# Barème vélo
MILEAGE_RATE_BICYCLE = Decimal("0.25")  # Forfait mobilité durable

# Limites repas URSSAF 2024
MEAL_LIMITS_2024 = {
    "meal_solo_limit": Decimal("20.20"),  # Repas seul au restaurant
    "meal_business_limit": Decimal("50.00"),  # Repas d'affaires
    "meal_deduction_minimum": Decimal("5.35"),  # Avantage en nature repas
}

# Limites cadeaux et représentation
GIFT_LIMITS_2024 = {
    "gift_per_event": Decimal("73.00"),  # Cadeau par événement
    "gift_annual_per_person": Decimal("171.00"),  # Cumul annuel/personne
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Receipt:
    """Justificatif de dépense."""
    id: str
    file_path: str
    file_name: str
    file_size: int
    mime_type: str
    uploaded_at: datetime = field(default_factory=datetime.now)

    # Données extraites par OCR
    ocr_processed: bool = False
    ocr_merchant: Optional[str] = None
    ocr_amount: Optional[Decimal] = None
    ocr_date: Optional[date] = None
    ocr_vat_amount: Optional[Decimal] = None
    ocr_confidence: Optional[float] = None


@dataclass
class MileageTrip:
    """Trajet pour indemnités kilométriques."""
    departure_address: str
    arrival_address: str
    distance_km: Decimal
    date: date
    purpose: str

    # Calcul automatique
    is_round_trip: bool = False
    calculated_distance: Optional[Decimal] = None
    route_details: Optional[Dict[str, Any]] = None


@dataclass
class ExpenseLine:
    """Ligne de dépense."""
    id: str
    category: ExpenseCategory
    description: str
    amount: Decimal
    currency: str = "EUR"
    date: date = field(default_factory=date.today)

    # TVA
    vat_rate: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    amount_excl_vat: Optional[Decimal] = None
    vat_recoverable: bool = True

    # Paiement
    payment_method: PaymentMethod = PaymentMethod.PERSONAL_CARD

    # Justificatif
    receipt: Optional[Receipt] = None
    receipt_required: bool = True

    # Kilométrique
    mileage_trip: Optional[MileageTrip] = None
    vehicle_type: Optional[VehicleType] = None
    mileage_rate: Optional[Decimal] = None

    # Invités (repas d'affaires)
    guests: List[str] = field(default_factory=list)
    guest_count: int = 0

    # Projet/Client
    project_id: Optional[str] = None
    client_id: Optional[str] = None
    billable: bool = False

    # Validation
    is_policy_compliant: bool = True
    policy_violation_reason: Optional[str] = None

    # Comptabilité
    accounting_code: Optional[str] = None
    cost_center: Optional[str] = None
    analytic_axis: Optional[Dict[str, str]] = None


@dataclass
class ExpenseReport:
    """Note de frais complète."""
    id: str
    tenant_id: str
    employee_id: str
    title: str

    # Lignes
    lines: List[ExpenseLine] = field(default_factory=list)

    # Période
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    mission_reference: Optional[str] = None

    # Totaux
    total_amount: Decimal = Decimal("0")
    total_vat: Decimal = Decimal("0")
    total_reimbursable: Decimal = Decimal("0")

    # Devise
    currency: str = "EUR"

    # Statut
    status: ExpenseStatus = ExpenseStatus.DRAFT
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    # Workflow
    current_approver_id: Optional[str] = None
    approval_history: List[Dict[str, Any]] = field(default_factory=list)

    # Dates système
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Export comptable
    exported_to_accounting: bool = False
    accounting_entry_id: Optional[str] = None

    def recalculate_totals(self):
        """Recalcule les totaux."""
        self.total_amount = sum(line.amount for line in self.lines)
        self.total_vat = sum(
            line.vat_amount or Decimal("0")
            for line in self.lines
            if line.vat_recoverable
        )

        # Montant remboursable (exclut carte entreprise)
        self.total_reimbursable = sum(
            line.amount for line in self.lines
            if line.payment_method not in [
                PaymentMethod.COMPANY_CARD,
                PaymentMethod.COMPANY_ACCOUNT
            ]
        )


@dataclass
class ExpensePolicy:
    """Politique de dépenses."""
    id: str
    tenant_id: str
    name: str
    is_active: bool = True

    # Limites par catégorie
    category_limits: Dict[str, Decimal] = field(default_factory=dict)

    # Limites générales
    single_expense_limit: Decimal = Decimal("500")  # Max par dépense
    daily_limit: Decimal = Decimal("200")  # Max par jour
    monthly_limit: Decimal = Decimal("2000")  # Max par mois

    # Règles justificatifs
    receipt_required_above: Decimal = Decimal("10")  # Justificatif requis au-dessus de
    receipt_required_categories: List[str] = field(default_factory=list)

    # Règles repas
    meal_solo_limit: Decimal = Decimal("20.20")
    meal_business_limit: Decimal = Decimal("50")
    meal_require_guests: bool = True  # Exiger liste invités

    # Règles transport
    mileage_max_daily_km: Decimal = Decimal("500")
    require_train_over_km: Decimal = Decimal("300")  # Train obligatoire > X km

    # Approbation
    approval_thresholds: Dict[str, Decimal] = field(default_factory=dict)

    # Catégories interdites
    blocked_categories: List[str] = field(default_factory=list)

    # Règles avancées
    rules: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ApprovalRequest:
    """Demande d'approbation."""
    id: str
    expense_report_id: str
    approver_id: str
    approval_level: ApprovalLevel

    # Statut
    status: str = "pending"  # pending, approved, rejected
    decision_at: Optional[datetime] = None
    comments: Optional[str] = None

    # Délégation
    delegated_from: Optional[str] = None
    delegated_at: Optional[datetime] = None

    created_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class ExpenseService:
    """
    Service de gestion des notes de frais.

    Gère:
    - Création et modification des notes
    - Calcul des indemnités kilométriques
    - Application des politiques
    - Workflow d'approbation
    - Export comptable
    """

    def __init__(
        self,
        tenant_id: str,
        default_currency: str = "EUR"
    ):
        self.tenant_id = tenant_id
        self.default_currency = default_currency

        # Stockage (à remplacer par DB)
        self._reports: Dict[str, ExpenseReport] = {}
        self._policies: Dict[str, ExpensePolicy] = {}
        self._approval_requests: Dict[str, ApprovalRequest] = {}
        self._employee_vehicles: Dict[str, Dict[str, Any]] = {}

        # Charger la politique par défaut
        self._init_default_policy()

    def _init_default_policy(self):
        """Initialise la politique par défaut."""
        policy = ExpensePolicy(
            id="default",
            tenant_id=self.tenant_id,
            name="Politique standard",
            category_limits={
                ExpenseCategory.HOTEL.value: Decimal("150"),
                ExpenseCategory.RESTAURANT.value: Decimal("30"),
                ExpenseCategory.MEAL_BUSINESS.value: Decimal("50"),
                ExpenseCategory.TAXI_RIDE.value: Decimal("50"),
            },
            approval_thresholds={
                "manager": Decimal("0"),
                "department_head": Decimal("500"),
                "finance": Decimal("2000"),
                "ceo": Decimal("10000"),
            }
        )
        self._policies["default"] = policy

    # ========================================================================
    # GESTION DES NOTES DE FRAIS
    # ========================================================================

    def create_expense_report(
        self,
        employee_id: str,
        title: str,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        mission_reference: Optional[str] = None
    ) -> ExpenseReport:
        """Crée une nouvelle note de frais."""
        report = ExpenseReport(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            employee_id=employee_id,
            title=title,
            period_start=period_start,
            period_end=period_end,
            mission_reference=mission_reference
        )

        self._reports[report.id] = report
        return report

    def add_expense_line(
        self,
        report_id: str,
        category: ExpenseCategory,
        description: str,
        amount: Decimal,
        expense_date: date,
        payment_method: PaymentMethod = PaymentMethod.PERSONAL_CARD,
        vat_rate: Optional[Decimal] = None,
        receipt: Optional[Receipt] = None,
        project_id: Optional[str] = None,
        client_id: Optional[str] = None,
        guests: Optional[List[str]] = None
    ) -> ExpenseLine:
        """Ajoute une ligne de dépense."""
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Note de frais {report_id} non trouvée")

        if report.status != ExpenseStatus.DRAFT:
            raise ValueError("Impossible de modifier une note soumise")

        # Calculer la TVA si taux fourni
        vat_amount = None
        amount_excl_vat = None
        if vat_rate:
            vat_amount = (amount * vat_rate / (100 + vat_rate)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            amount_excl_vat = amount - vat_amount

        line = ExpenseLine(
            id=str(uuid.uuid4()),
            category=category,
            description=description,
            amount=amount,
            date=expense_date,
            payment_method=payment_method,
            vat_rate=vat_rate,
            vat_amount=vat_amount,
            amount_excl_vat=amount_excl_vat,
            receipt=receipt,
            project_id=project_id,
            client_id=client_id,
            guests=guests or [],
            guest_count=len(guests) if guests else 0,
            accounting_code=self._get_accounting_code(category)
        )

        # Vérifier la politique
        violations = self._check_policy_compliance(line, report)
        if violations:
            line.is_policy_compliant = False
            line.policy_violation_reason = "; ".join(violations)

        report.lines.append(line)
        report.recalculate_totals()
        report.updated_at = datetime.now()

        return line

    def add_mileage_expense(
        self,
        report_id: str,
        employee_id: str,
        trip: MileageTrip,
        vehicle_type: VehicleType = VehicleType.CAR_5CV,
        purpose: Optional[str] = None
    ) -> ExpenseLine:
        """Ajoute une dépense kilométrique."""
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Note de frais {report_id} non trouvée")

        # Récupérer le kilométrage annuel de l'employé
        annual_km = self._get_employee_annual_mileage(employee_id, trip.date.year)

        # Calculer le taux applicable
        mileage_rate = self._calculate_mileage_rate(
            vehicle_type,
            trip.distance_km,
            annual_km
        )

        # Calculer le montant
        distance = trip.distance_km * 2 if trip.is_round_trip else trip.distance_km
        amount = (distance * mileage_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        line = ExpenseLine(
            id=str(uuid.uuid4()),
            category=ExpenseCategory.MILEAGE,
            description=f"Trajet: {trip.departure_address} → {trip.arrival_address}",
            amount=amount,
            date=trip.date,
            payment_method=PaymentMethod.MILEAGE,
            receipt_required=False,
            mileage_trip=trip,
            vehicle_type=vehicle_type,
            mileage_rate=mileage_rate,
            accounting_code="625100"  # Frais de déplacement
        )

        # Vérifier la politique
        violations = self._check_policy_compliance(line, report)
        if violations:
            line.is_policy_compliant = False
            line.policy_violation_reason = "; ".join(violations)

        report.lines.append(line)
        report.recalculate_totals()
        report.updated_at = datetime.now()

        # Mettre à jour le kilométrage annuel
        self._update_employee_annual_mileage(
            employee_id,
            trip.date.year,
            distance
        )

        return line

    def _calculate_mileage_rate(
        self,
        vehicle_type: VehicleType,
        distance: Decimal,
        annual_km: Decimal
    ) -> Decimal:
        """Calcule le taux kilométrique applicable."""
        if vehicle_type == VehicleType.BICYCLE:
            return MILEAGE_RATE_BICYCLE

        if vehicle_type == VehicleType.ELECTRIC_BICYCLE:
            return MILEAGE_RATE_BICYCLE * Decimal("1.2")  # Majoration 20%

        rates = MILEAGE_RATES_CAR_2024.get(vehicle_type)
        if not rates:
            # Taux par défaut (5 CV)
            rates = MILEAGE_RATES_CAR_2024[VehicleType.CAR_5CV]

        new_annual = annual_km + distance

        if new_annual <= 5000:
            return rates["up_to_5000"]
        elif new_annual <= 20000:
            return rates["5001_to_20000"]
        else:
            return rates["above_20000"]

    def _get_employee_annual_mileage(
        self,
        employee_id: str,
        year: int
    ) -> Decimal:
        """Récupère le kilométrage annuel d'un employé."""
        key = f"{employee_id}_{year}"
        data = self._employee_vehicles.get(key, {})
        return Decimal(str(data.get("total_km", 0)))

    def _update_employee_annual_mileage(
        self,
        employee_id: str,
        year: int,
        additional_km: Decimal
    ):
        """Met à jour le kilométrage annuel."""
        key = f"{employee_id}_{year}"
        if key not in self._employee_vehicles:
            self._employee_vehicles[key] = {"total_km": Decimal("0")}
        self._employee_vehicles[key]["total_km"] += additional_km

    # ========================================================================
    # VÉRIFICATION DES POLITIQUES
    # ========================================================================

    def _check_policy_compliance(
        self,
        line: ExpenseLine,
        report: ExpenseReport,
        policy_id: str = "default"
    ) -> List[str]:
        """Vérifie la conformité avec la politique de dépenses."""
        violations = []
        policy = self._policies.get(policy_id)

        if not policy:
            return violations

        # Catégorie bloquée
        if line.category.value in policy.blocked_categories:
            violations.append(f"Catégorie {line.category.value} non autorisée")

        # Limite par catégorie
        category_limit = policy.category_limits.get(line.category.value)
        if category_limit and line.amount > category_limit:
            violations.append(
                f"Dépassement limite catégorie: {line.amount} > {category_limit}"
            )

        # Limite par dépense
        if line.amount > policy.single_expense_limit:
            violations.append(
                f"Dépassement limite unitaire: {line.amount} > {policy.single_expense_limit}"
            )

        # Justificatif requis
        if line.receipt_required and not line.receipt:
            if line.amount > policy.receipt_required_above:
                violations.append(
                    f"Justificatif requis pour montant > {policy.receipt_required_above}"
                )

        # Repas d'affaires sans invités
        if line.category == ExpenseCategory.MEAL_BUSINESS:
            if policy.meal_require_guests and not line.guests:
                violations.append("Liste des invités requise pour repas d'affaires")
            if line.amount > policy.meal_business_limit:
                violations.append(
                    f"Dépassement limite repas affaires: {line.amount} > {policy.meal_business_limit}"
                )

        # Repas seul
        if line.category == ExpenseCategory.MEAL_SOLO:
            if line.amount > policy.meal_solo_limit:
                violations.append(
                    f"Dépassement limite repas: {line.amount} > {policy.meal_solo_limit}"
                )

        # Kilométrage journalier
        if line.mileage_trip:
            if line.mileage_trip.distance_km > policy.mileage_max_daily_km:
                violations.append(
                    f"Kilométrage excessif: {line.mileage_trip.distance_km} km > {policy.mileage_max_daily_km} km/jour"
                )

        return violations

    def validate_report(
        self,
        report_id: str
    ) -> Dict[str, Any]:
        """Valide une note de frais avant soumission."""
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Note de frais {report_id} non trouvée")

        errors = []
        warnings = []

        # Vérifier les lignes
        for line in report.lines:
            # Justificatifs manquants
            if line.receipt_required and not line.receipt:
                errors.append(f"Justificatif manquant: {line.description}")

            # Violations de politique
            if not line.is_policy_compliant:
                warnings.append(f"Non-conformité: {line.policy_violation_reason}")

            # Dates hors période
            if report.period_start and line.date < report.period_start:
                warnings.append(
                    f"Date antérieure à la période: {line.description}"
                )
            if report.period_end and line.date > report.period_end:
                warnings.append(
                    f"Date postérieure à la période: {line.description}"
                )

        # Vérifier les totaux
        policy = self._policies.get("default")
        if policy:
            # Limite mensuelle
            if report.total_amount > policy.monthly_limit:
                warnings.append(
                    f"Dépassement limite mensuelle: {report.total_amount} > {policy.monthly_limit}"
                )

        # Doublons potentiels
        duplicates = self._detect_duplicates(report)
        if duplicates:
            for dup in duplicates:
                warnings.append(f"Doublon potentiel: {dup}")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_amount": float(report.total_amount),
            "line_count": len(report.lines)
        }

    def _detect_duplicates(
        self,
        report: ExpenseReport
    ) -> List[str]:
        """Détecte les doublons potentiels."""
        duplicates = []
        seen = set()

        for line in report.lines:
            key = (line.date, line.amount, line.category)
            if key in seen:
                duplicates.append(f"{line.date} - {line.amount} - {line.category.value}")
            seen.add(key)

        return duplicates

    # ========================================================================
    # WORKFLOW D'APPROBATION
    # ========================================================================

    def submit_report(
        self,
        report_id: str
    ) -> ExpenseReport:
        """Soumet une note de frais pour approbation."""
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Note de frais {report_id} non trouvée")

        if report.status != ExpenseStatus.DRAFT:
            raise ValueError("Note déjà soumise")

        # Valider avant soumission
        validation = self.validate_report(report_id)
        if not validation["is_valid"]:
            raise ValueError(f"Validation échouée: {validation['errors']}")

        # Déterminer le premier approbateur
        approver_id = self._get_first_approver(report)

        report.status = ExpenseStatus.SUBMITTED
        report.submitted_at = datetime.now()
        report.current_approver_id = approver_id
        report.updated_at = datetime.now()

        # Créer la demande d'approbation
        self._create_approval_request(report, approver_id)

        return report

    def _get_first_approver(
        self,
        report: ExpenseReport
    ) -> str:
        """Détermine le premier approbateur selon les seuils."""
        policy = self._policies.get("default")
        if not policy:
            return "manager_default"

        # Trouver le niveau d'approbation requis
        thresholds = sorted(
            policy.approval_thresholds.items(),
            key=lambda x: x[1]
        )

        for level, threshold in thresholds:
            if report.total_amount <= threshold:
                # Récupérer l'approbateur de ce niveau
                # En production: lookup dans org chart
                return f"{level}_{report.employee_id}"

        return "ceo"

    def _create_approval_request(
        self,
        report: ExpenseReport,
        approver_id: str
    ) -> ApprovalRequest:
        """Crée une demande d'approbation."""
        request = ApprovalRequest(
            id=str(uuid.uuid4()),
            expense_report_id=report.id,
            approver_id=approver_id,
            approval_level=ApprovalLevel.MANAGER
        )

        self._approval_requests[request.id] = request
        return request

    def approve_report(
        self,
        report_id: str,
        approver_id: str,
        comments: Optional[str] = None
    ) -> ExpenseReport:
        """Approuve une note de frais."""
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Note de frais {report_id} non trouvée")

        if report.current_approver_id != approver_id:
            raise ValueError("Vous n'êtes pas l'approbateur actuel")

        # Enregistrer l'approbation
        report.approval_history.append({
            "approver_id": approver_id,
            "action": "approved",
            "comments": comments,
            "timestamp": datetime.now().isoformat()
        })

        # Vérifier si approbation suivante nécessaire
        next_approver = self._get_next_approver(report)

        if next_approver:
            report.current_approver_id = next_approver
            self._create_approval_request(report, next_approver)
        else:
            # Approbation finale
            report.status = ExpenseStatus.APPROVED
            report.approved_at = datetime.now()
            report.current_approver_id = None

        report.updated_at = datetime.now()
        return report

    def reject_report(
        self,
        report_id: str,
        approver_id: str,
        reason: str
    ) -> ExpenseReport:
        """Rejette une note de frais."""
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Note de frais {report_id} non trouvée")

        report.approval_history.append({
            "approver_id": approver_id,
            "action": "rejected",
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })

        report.status = ExpenseStatus.REJECTED
        report.current_approver_id = None
        report.updated_at = datetime.now()

        return report

    def _get_next_approver(
        self,
        report: ExpenseReport
    ) -> Optional[str]:
        """Détermine le prochain approbateur si nécessaire."""
        # En production, implémenter la logique multi-niveau
        return None

    # ========================================================================
    # EXPORT COMPTABLE
    # ========================================================================

    def generate_accounting_entries(
        self,
        report_id: str
    ) -> List[Dict[str, Any]]:
        """Génère les écritures comptables."""
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Note de frais {report_id} non trouvée")

        if report.status != ExpenseStatus.APPROVED:
            raise ValueError("Note non approuvée")

        entries = []
        journal_date = date.today()

        # Créer une écriture par ligne
        for line in report.lines:
            # Compte de charge
            entries.append({
                "journal": "OD",  # Opérations diverses
                "date": journal_date.isoformat(),
                "account": line.accounting_code or self._get_accounting_code(line.category),
                "debit": float(line.amount_excl_vat or line.amount),
                "credit": 0,
                "label": line.description,
                "reference": report.id,
                "employee_id": report.employee_id,
                "analytic": line.analytic_axis
            })

            # TVA déductible si applicable
            if line.vat_amount and line.vat_recoverable:
                entries.append({
                    "journal": "OD",
                    "date": journal_date.isoformat(),
                    "account": "445660",  # TVA déductible
                    "debit": float(line.vat_amount),
                    "credit": 0,
                    "label": f"TVA {line.description}",
                    "reference": report.id
                })

        # Contrepartie: dette envers le salarié
        total_to_reimburse = sum(
            line.amount for line in report.lines
            if line.payment_method not in [
                PaymentMethod.COMPANY_CARD,
                PaymentMethod.COMPANY_ACCOUNT
            ]
        )

        if total_to_reimburse > 0:
            entries.append({
                "journal": "OD",
                "date": journal_date.isoformat(),
                "account": "421000",  # Personnel - rémunérations dues
                "debit": 0,
                "credit": float(total_to_reimburse),
                "label": f"Remboursement frais {report.title}",
                "reference": report.id,
                "employee_id": report.employee_id
            })

        report.exported_to_accounting = True
        report.updated_at = datetime.now()

        return entries

    def _get_accounting_code(
        self,
        category: ExpenseCategory
    ) -> str:
        """Retourne le code comptable pour une catégorie."""
        mapping = {
            ExpenseCategory.MILEAGE: "625100",  # Voyages et déplacements
            ExpenseCategory.PUBLIC_TRANSPORT: "625100",
            ExpenseCategory.TAXI_RIDE: "625100",
            ExpenseCategory.PARKING: "625100",
            ExpenseCategory.TOLL: "625100",
            ExpenseCategory.RENTAL_CAR: "613500",  # Location matériel transport
            ExpenseCategory.FUEL: "606100",  # Fournitures non stockées

            ExpenseCategory.HOTEL: "625600",  # Missions
            ExpenseCategory.AIRBNB: "625600",

            ExpenseCategory.RESTAURANT: "625700",  # Réceptions
            ExpenseCategory.MEAL_SOLO: "625700",
            ExpenseCategory.MEAL_BUSINESS: "625700",
            ExpenseCategory.MEAL_TEAM: "625700",

            ExpenseCategory.FLIGHT: "625100",
            ExpenseCategory.TRAIN: "625100",
            ExpenseCategory.VISA: "625100",
            ExpenseCategory.TRAVEL_INSURANCE: "616000",  # Assurances

            ExpenseCategory.PHONE: "626000",  # Frais postaux et télécoms
            ExpenseCategory.INTERNET: "626000",

            ExpenseCategory.OFFICE_SUPPLIES: "606400",  # Fournitures administratives
            ExpenseCategory.IT_EQUIPMENT: "606300",  # Petit équipement
            ExpenseCategory.BOOKS: "618500",  # Documentation

            ExpenseCategory.REPRESENTATION: "625700",
            ExpenseCategory.SUBSCRIPTION: "651800",  # Cotisations
            ExpenseCategory.OTHER: "628800",  # Divers
        }
        return mapping.get(category, "628800")

    # ========================================================================
    # STATISTIQUES
    # ========================================================================

    def get_employee_statistics(
        self,
        employee_id: str,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Statistiques de dépenses d'un employé."""
        year = year or date.today().year

        reports = [
            r for r in self._reports.values()
            if r.employee_id == employee_id
            and r.created_at.year == year
        ]

        total_submitted = sum(
            r.total_amount for r in reports
            if r.status in [ExpenseStatus.SUBMITTED, ExpenseStatus.APPROVED, ExpenseStatus.PAID]
        )

        total_approved = sum(
            r.total_amount for r in reports
            if r.status in [ExpenseStatus.APPROVED, ExpenseStatus.PAID]
        )

        total_paid = sum(
            r.total_amount for r in reports
            if r.status == ExpenseStatus.PAID
        )

        # Par catégorie
        by_category = {}
        for report in reports:
            for line in report.lines:
                cat = line.category.value
                if cat not in by_category:
                    by_category[cat] = Decimal("0")
                by_category[cat] += line.amount

        return {
            "employee_id": employee_id,
            "year": year,
            "report_count": len(reports),
            "total_submitted": float(total_submitted),
            "total_approved": float(total_approved),
            "total_paid": float(total_paid),
            "total_pending": float(total_submitted - total_approved),
            "by_category": {k: float(v) for k, v in by_category.items()},
            "average_per_report": float(total_submitted / len(reports)) if reports else 0
        }


# ============================================================================
# FACTORY
# ============================================================================

def create_expense_service(
    tenant_id: str,
    default_currency: str = "EUR"
) -> ExpenseService:
    """Crée un service de gestion des notes de frais."""
    return ExpenseService(
        tenant_id=tenant_id,
        default_currency=default_currency
    )
