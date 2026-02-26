"""
Service Expense Management / Notes de frais - GAP-084

Gestion des notes de frais:
- Saisie des dépenses
- Justificatifs et OCR
- Politiques de dépenses
- Workflow d'approbation
- Remboursements
- Cartes corporate
- Rapports et analytics
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4


# ============== Énumérations ==============

class ExpenseCategory(str, Enum):
    """Catégories de dépenses"""
    TRAVEL = "travel"
    ACCOMMODATION = "accommodation"
    MEALS = "meals"
    TRANSPORT = "transport"
    FUEL = "fuel"
    PARKING = "parking"
    TOLL = "toll"
    OFFICE_SUPPLIES = "office_supplies"
    EQUIPMENT = "equipment"
    SOFTWARE = "software"
    TRAINING = "training"
    ENTERTAINMENT = "entertainment"
    COMMUNICATION = "communication"
    SUBSCRIPTION = "subscription"
    OTHER = "other"


class ExpenseStatus(str, Enum):
    """Statuts de dépense"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    REIMBURSED = "reimbursed"
    CANCELLED = "cancelled"


class ReportStatus(str, Enum):
    """Statuts de rapport"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Méthodes de paiement"""
    CASH = "cash"
    PERSONAL_CARD = "personal_card"
    CORPORATE_CARD = "corporate_card"
    BANK_TRANSFER = "bank_transfer"
    COMPANY_ACCOUNT = "company_account"


class MileageType(str, Enum):
    """Types de kilométrage"""
    CAR = "car"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"
    PUBLIC_TRANSPORT = "public_transport"


class CardStatus(str, Enum):
    """Statuts carte"""
    ACTIVE = "active"
    BLOCKED = "blocked"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# ============== Data Classes ==============

@dataclass
class ExpensePolicy:
    """Politique de dépenses"""
    id: str
    tenant_id: str
    name: str
    code: str
    description: str = ""

    # Limites par catégorie
    category_limits: Dict[str, Decimal] = field(default_factory=dict)

    # Limites globales
    daily_limit: Optional[Decimal] = None
    monthly_limit: Optional[Decimal] = None
    single_expense_limit: Optional[Decimal] = None

    # Règles
    require_receipt_above: Decimal = Decimal("25")
    require_approval_above: Decimal = Decimal("100")
    auto_approve_below: Optional[Decimal] = None
    allowed_categories: List[ExpenseCategory] = field(default_factory=list)
    blocked_categories: List[ExpenseCategory] = field(default_factory=list)

    # Kilométrage
    mileage_rate_car: Decimal = Decimal("0.55")
    mileage_rate_motorcycle: Decimal = Decimal("0.35")

    # Per diem
    per_diem_domestic: Decimal = Decimal("50")
    per_diem_international: Decimal = Decimal("100")

    # Métadonnées
    applies_to_roles: List[str] = field(default_factory=list)
    applies_to_departments: List[str] = field(default_factory=list)
    is_default: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Receipt:
    """Justificatif"""
    id: str
    filename: str
    file_url: str
    file_type: str
    file_size: int = 0

    # OCR
    ocr_processed: bool = False
    ocr_vendor: str = ""
    ocr_amount: Optional[Decimal] = None
    ocr_date: Optional[date] = None
    ocr_tax_amount: Optional[Decimal] = None
    ocr_confidence: Decimal = Decimal("0")

    uploaded_at: datetime = field(default_factory=datetime.now)


@dataclass
class Expense:
    """Dépense individuelle"""
    id: str
    tenant_id: str
    report_id: Optional[str] = None
    employee_id: str = ""
    employee_name: str = ""

    # Détails
    expense_date: date = field(default_factory=date.today)
    category: ExpenseCategory = ExpenseCategory.OTHER
    description: str = ""
    vendor: str = ""

    # Montants
    amount: Decimal = Decimal("0")
    currency: str = "EUR"
    exchange_rate: Decimal = Decimal("1")
    amount_in_base_currency: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")

    # Paiement
    payment_method: PaymentMethod = PaymentMethod.PERSONAL_CARD
    card_id: Optional[str] = None
    is_reimbursable: bool = True
    is_billable: bool = False

    # Justificatifs
    receipts: List[Receipt] = field(default_factory=list)
    receipt_missing: bool = False
    receipt_missing_reason: str = ""

    # Kilométrage
    is_mileage: bool = False
    mileage_distance_km: Decimal = Decimal("0")
    mileage_type: Optional[MileageType] = None
    mileage_origin: str = ""
    mileage_destination: str = ""

    # Allocation
    project_id: Optional[str] = None
    project_name: str = ""
    cost_center_id: Optional[str] = None
    cost_center_name: str = ""
    department_id: Optional[str] = None

    # Statut
    status: ExpenseStatus = ExpenseStatus.DRAFT

    # Politique
    policy_violations: List[str] = field(default_factory=list)
    policy_warnings: List[str] = field(default_factory=list)

    # Métadonnées
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExpenseReport:
    """Rapport de dépenses"""
    id: str
    tenant_id: str
    report_number: str
    title: str
    description: str = ""

    # Employé
    employee_id: str = ""
    employee_name: str = ""
    department_id: str = ""
    department_name: str = ""

    # Période
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    trip_name: str = ""
    trip_purpose: str = ""

    # Dépenses
    expense_ids: List[str] = field(default_factory=list)
    expense_count: int = 0

    # Montants
    total_amount: Decimal = Decimal("0")
    reimbursable_amount: Decimal = Decimal("0")
    non_reimbursable_amount: Decimal = Decimal("0")
    billable_amount: Decimal = Decimal("0")
    personal_card_amount: Decimal = Decimal("0")
    corporate_card_amount: Decimal = Decimal("0")
    cash_amount: Decimal = Decimal("0")
    currency: str = "EUR"

    # Avance
    advance_amount: Decimal = Decimal("0")
    amount_due_employee: Decimal = Decimal("0")
    amount_due_company: Decimal = Decimal("0")

    # Statut
    status: ReportStatus = ReportStatus.DRAFT

    # Approbation
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: str = ""
    rejection_reason: str = ""

    # Paiement
    payment_date: Optional[date] = None
    payment_reference: str = ""
    payment_method: str = ""

    # Métadonnées
    attachments: List[str] = field(default_factory=list)
    comments: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CorporateCard:
    """Carte corporate"""
    id: str
    tenant_id: str
    card_number_masked: str  # **** **** **** 1234
    card_type: str = "visa"  # visa, mastercard, amex
    cardholder_id: str = ""
    cardholder_name: str = ""

    # Limites
    credit_limit: Decimal = Decimal("0")
    daily_limit: Decimal = Decimal("0")
    monthly_limit: Decimal = Decimal("0")
    single_transaction_limit: Decimal = Decimal("0")

    # Solde
    current_balance: Decimal = Decimal("0")
    available_credit: Decimal = Decimal("0")

    # Dates
    expiry_date: date = field(default_factory=date.today)
    issue_date: date = field(default_factory=date.today)

    # Statut
    status: CardStatus = CardStatus.ACTIVE
    blocked_reason: str = ""

    # Restrictions
    allowed_categories: List[ExpenseCategory] = field(default_factory=list)
    allowed_merchants: List[str] = field(default_factory=list)
    blocked_merchants: List[str] = field(default_factory=list)

    # Métadonnées
    last_transaction_date: Optional[date] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CardTransaction:
    """Transaction carte"""
    id: str
    tenant_id: str
    card_id: str
    card_number_masked: str
    cardholder_id: str

    # Transaction
    transaction_date: datetime
    merchant_name: str
    merchant_category: str
    merchant_location: str = ""

    # Montants
    amount: Decimal = Decimal("0")
    currency: str = "EUR"
    amount_in_base_currency: Decimal = Decimal("0")

    # Statut
    is_matched: bool = False
    expense_id: Optional[str] = None
    is_personal: bool = False
    personal_reason: str = ""

    # Métadonnées
    authorization_code: str = ""
    receipt_url: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExpenseStats:
    """Statistiques dépenses"""
    tenant_id: str
    period_start: date
    period_end: date
    total_expenses: int = 0
    total_amount: Decimal = Decimal("0")
    total_reimbursed: Decimal = Decimal("0")
    pending_amount: Decimal = Decimal("0")
    average_expense: Decimal = Decimal("0")
    by_category: Dict[str, Decimal] = field(default_factory=dict)
    by_department: Dict[str, Decimal] = field(default_factory=dict)
    by_employee: Dict[str, Dict] = field(default_factory=dict)
    by_project: Dict[str, Decimal] = field(default_factory=dict)
    policy_violations: int = 0
    top_vendors: List[Dict] = field(default_factory=list)


# ============== Service ==============

class ExpenseService:
    """
    Service de gestion des notes de frais.

    Fonctionnalités:
    - Saisie des dépenses
    - Justificatifs et OCR
    - Politiques et validations
    - Rapports de dépenses
    - Cartes corporate
    - Remboursements
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._policies: Dict[str, ExpensePolicy] = {}
        self._expenses: Dict[str, Expense] = {}
        self._reports: Dict[str, ExpenseReport] = {}
        self._cards: Dict[str, CorporateCard] = {}
        self._transactions: Dict[str, CardTransaction] = {}
        self._report_counter = 0

    # ========== Politiques ==========

    def create_policy(
        self,
        name: str,
        code: str,
        description: str = "",
        daily_limit: Optional[Decimal] = None,
        monthly_limit: Optional[Decimal] = None,
        single_expense_limit: Optional[Decimal] = None,
        require_receipt_above: Decimal = Decimal("25"),
        mileage_rate_car: Decimal = Decimal("0.55"),
        is_default: bool = False
    ) -> ExpensePolicy:
        """Créer politique de dépenses"""
        policy = ExpensePolicy(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            code=code.upper(),
            description=description,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit,
            single_expense_limit=single_expense_limit,
            require_receipt_above=require_receipt_above,
            mileage_rate_car=mileage_rate_car,
            is_default=is_default
        )
        self._policies[policy.id] = policy
        return policy

    def set_category_limit(
        self,
        policy_id: str,
        category: ExpenseCategory,
        limit: Decimal
    ) -> Optional[ExpensePolicy]:
        """Définir limite par catégorie"""
        policy = self._policies.get(policy_id)
        if not policy:
            return None

        policy.category_limits[category.value] = limit
        return policy

    def get_policy(self, policy_id: str) -> Optional[ExpensePolicy]:
        """Obtenir politique"""
        return self._policies.get(policy_id)

    def get_default_policy(self) -> Optional[ExpensePolicy]:
        """Obtenir politique par défaut"""
        for policy in self._policies.values():
            if policy.is_default and policy.is_active:
                return policy
        return None

    def get_applicable_policy(
        self,
        employee_id: str,
        department_id: Optional[str] = None,
        role: Optional[str] = None
    ) -> Optional[ExpensePolicy]:
        """Trouver politique applicable"""
        # Chercher politique spécifique
        for policy in self._policies.values():
            if not policy.is_active:
                continue
            if department_id and department_id in policy.applies_to_departments:
                return policy
            if role and role in policy.applies_to_roles:
                return policy

        # Retourner défaut
        return self.get_default_policy()

    # ========== Dépenses ==========

    def create_expense(
        self,
        employee_id: str,
        employee_name: str,
        expense_date: date,
        category: ExpenseCategory,
        amount: Decimal,
        description: str = "",
        vendor: str = "",
        currency: str = "EUR",
        payment_method: PaymentMethod = PaymentMethod.PERSONAL_CARD,
        is_reimbursable: bool = True,
        project_id: Optional[str] = None,
        cost_center_id: Optional[str] = None,
        department_id: Optional[str] = None
    ) -> Expense:
        """Créer une dépense"""
        expense = Expense(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            employee_id=employee_id,
            employee_name=employee_name,
            expense_date=expense_date,
            category=category,
            amount=amount,
            amount_in_base_currency=amount,
            description=description,
            vendor=vendor,
            currency=currency,
            payment_method=payment_method,
            is_reimbursable=is_reimbursable,
            project_id=project_id,
            cost_center_id=cost_center_id,
            department_id=department_id
        )

        # Vérifier politique
        policy = self.get_applicable_policy(employee_id, department_id)
        if policy:
            self._validate_against_policy(expense, policy)

        self._expenses[expense.id] = expense
        return expense

    def create_mileage_expense(
        self,
        employee_id: str,
        employee_name: str,
        expense_date: date,
        distance_km: Decimal,
        mileage_type: MileageType,
        origin: str,
        destination: str,
        description: str = "",
        project_id: Optional[str] = None,
        department_id: Optional[str] = None
    ) -> Expense:
        """Créer dépense kilométrique"""
        # Obtenir taux
        policy = self.get_applicable_policy(employee_id, department_id)
        rate = Decimal("0.55")
        if policy:
            if mileage_type == MileageType.CAR:
                rate = policy.mileage_rate_car
            elif mileage_type == MileageType.MOTORCYCLE:
                rate = policy.mileage_rate_motorcycle

        amount = distance_km * rate

        expense = Expense(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            employee_id=employee_id,
            employee_name=employee_name,
            expense_date=expense_date,
            category=ExpenseCategory.TRANSPORT,
            amount=amount,
            amount_in_base_currency=amount,
            description=description or f"Trajet {origin} - {destination}",
            is_mileage=True,
            mileage_distance_km=distance_km,
            mileage_type=mileage_type,
            mileage_origin=origin,
            mileage_destination=destination,
            project_id=project_id,
            department_id=department_id,
            is_reimbursable=True
        )
        self._expenses[expense.id] = expense
        return expense

    def add_receipt(
        self,
        expense_id: str,
        filename: str,
        file_url: str,
        file_type: str,
        file_size: int = 0
    ) -> Optional[Expense]:
        """Ajouter justificatif"""
        expense = self._expenses.get(expense_id)
        if not expense:
            return None

        receipt = Receipt(
            id=str(uuid4()),
            filename=filename,
            file_url=file_url,
            file_type=file_type,
            file_size=file_size
        )
        expense.receipts.append(receipt)
        expense.receipt_missing = False
        expense.updated_at = datetime.now()

        return expense

    def process_receipt_ocr(
        self,
        expense_id: str,
        receipt_id: str,
        ocr_vendor: str,
        ocr_amount: Optional[Decimal],
        ocr_date: Optional[date],
        ocr_tax_amount: Optional[Decimal] = None,
        confidence: Decimal = Decimal("0.9")
    ) -> Optional[Expense]:
        """Traiter OCR du justificatif"""
        expense = self._expenses.get(expense_id)
        if not expense:
            return None

        for receipt in expense.receipts:
            if receipt.id == receipt_id:
                receipt.ocr_processed = True
                receipt.ocr_vendor = ocr_vendor
                receipt.ocr_amount = ocr_amount
                receipt.ocr_date = ocr_date
                receipt.ocr_tax_amount = ocr_tax_amount
                receipt.ocr_confidence = confidence
                break

        expense.updated_at = datetime.now()
        return expense

    def mark_receipt_missing(
        self,
        expense_id: str,
        reason: str
    ) -> Optional[Expense]:
        """Marquer justificatif manquant"""
        expense = self._expenses.get(expense_id)
        if not expense:
            return None

        expense.receipt_missing = True
        expense.receipt_missing_reason = reason
        expense.updated_at = datetime.now()

        return expense

    def update_expense(
        self,
        expense_id: str,
        amount: Optional[Decimal] = None,
        description: Optional[str] = None,
        vendor: Optional[str] = None,
        category: Optional[ExpenseCategory] = None,
        project_id: Optional[str] = None,
        is_billable: Optional[bool] = None
    ) -> Optional[Expense]:
        """Modifier dépense"""
        expense = self._expenses.get(expense_id)
        if not expense or expense.status not in [ExpenseStatus.DRAFT, ExpenseStatus.REJECTED]:
            return None

        if amount is not None:
            expense.amount = amount
            expense.amount_in_base_currency = amount
        if description is not None:
            expense.description = description
        if vendor is not None:
            expense.vendor = vendor
        if category is not None:
            expense.category = category
        if project_id is not None:
            expense.project_id = project_id
        if is_billable is not None:
            expense.is_billable = is_billable

        # Revalider politique
        policy = self.get_applicable_policy(expense.employee_id, expense.department_id)
        if policy:
            expense.policy_violations = []
            expense.policy_warnings = []
            self._validate_against_policy(expense, policy)

        expense.updated_at = datetime.now()
        return expense

    def get_expense(self, expense_id: str) -> Optional[Expense]:
        """Obtenir dépense"""
        return self._expenses.get(expense_id)

    def list_expenses(
        self,
        employee_id: Optional[str] = None,
        status: Optional[ExpenseStatus] = None,
        category: Optional[ExpenseCategory] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        unattached_only: bool = False
    ) -> List[Expense]:
        """Lister dépenses"""
        expenses = list(self._expenses.values())

        if employee_id:
            expenses = [e for e in expenses if e.employee_id == employee_id]
        if status:
            expenses = [e for e in expenses if e.status == status]
        if category:
            expenses = [e for e in expenses if e.category == category]
        if date_from:
            expenses = [e for e in expenses if e.expense_date >= date_from]
        if date_to:
            expenses = [e for e in expenses if e.expense_date <= date_to]
        if unattached_only:
            expenses = [e for e in expenses if not e.report_id]

        return sorted(expenses, key=lambda x: x.expense_date, reverse=True)

    def _validate_against_policy(
        self,
        expense: Expense,
        policy: ExpensePolicy
    ) -> None:
        """Valider contre politique"""
        violations = []
        warnings = []

        # Limite unique
        if policy.single_expense_limit and expense.amount > policy.single_expense_limit:
            violations.append(
                f"Montant {expense.amount} dépasse la limite de {policy.single_expense_limit}"
            )

        # Limite par catégorie
        cat_limit = policy.category_limits.get(expense.category.value)
        if cat_limit and expense.amount > cat_limit:
            violations.append(
                f"Montant dépasse la limite de {cat_limit} pour {expense.category.value}"
            )

        # Catégories bloquées
        if expense.category in policy.blocked_categories:
            violations.append(f"Catégorie {expense.category.value} non autorisée")

        # Justificatif requis
        if expense.amount > policy.require_receipt_above and not expense.receipts:
            warnings.append(f"Justificatif requis pour montant > {policy.require_receipt_above}")

        expense.policy_violations = violations
        expense.policy_warnings = warnings

    # ========== Rapports ==========

    def create_report(
        self,
        title: str,
        employee_id: str,
        employee_name: str,
        expense_ids: List[str] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        trip_name: str = "",
        trip_purpose: str = "",
        department_id: str = "",
        department_name: str = ""
    ) -> ExpenseReport:
        """Créer rapport de dépenses"""
        self._report_counter += 1
        report_number = f"EXP-{datetime.now().year}-{self._report_counter:06d}"

        report = ExpenseReport(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            report_number=report_number,
            title=title,
            employee_id=employee_id,
            employee_name=employee_name,
            department_id=department_id,
            department_name=department_name,
            period_start=period_start,
            period_end=period_end,
            trip_name=trip_name,
            trip_purpose=trip_purpose
        )

        # Ajouter dépenses
        if expense_ids:
            for exp_id in expense_ids:
                self.add_expense_to_report(report.id, exp_id)

        self._reports[report.id] = report
        return report

    def add_expense_to_report(
        self,
        report_id: str,
        expense_id: str
    ) -> Optional[ExpenseReport]:
        """Ajouter dépense au rapport"""
        report = self._reports.get(report_id)
        expense = self._expenses.get(expense_id)

        if not report or not expense:
            return None
        if report.status != ReportStatus.DRAFT:
            return None
        if expense.report_id and expense.report_id != report_id:
            return None

        expense.report_id = report_id
        if expense_id not in report.expense_ids:
            report.expense_ids.append(expense_id)

        self._recalculate_report_totals(report)
        return report

    def remove_expense_from_report(
        self,
        report_id: str,
        expense_id: str
    ) -> Optional[ExpenseReport]:
        """Retirer dépense du rapport"""
        report = self._reports.get(report_id)
        expense = self._expenses.get(expense_id)

        if not report or not expense:
            return None
        if report.status != ReportStatus.DRAFT:
            return None

        expense.report_id = None
        if expense_id in report.expense_ids:
            report.expense_ids.remove(expense_id)

        self._recalculate_report_totals(report)
        return report

    def _recalculate_report_totals(self, report: ExpenseReport) -> None:
        """Recalculer totaux du rapport"""
        report.expense_count = len(report.expense_ids)
        report.total_amount = Decimal("0")
        report.reimbursable_amount = Decimal("0")
        report.non_reimbursable_amount = Decimal("0")
        report.billable_amount = Decimal("0")
        report.personal_card_amount = Decimal("0")
        report.corporate_card_amount = Decimal("0")
        report.cash_amount = Decimal("0")

        for exp_id in report.expense_ids:
            expense = self._expenses.get(exp_id)
            if not expense:
                continue

            report.total_amount += expense.amount_in_base_currency

            if expense.is_reimbursable:
                report.reimbursable_amount += expense.amount_in_base_currency
            else:
                report.non_reimbursable_amount += expense.amount_in_base_currency

            if expense.is_billable:
                report.billable_amount += expense.amount_in_base_currency

            if expense.payment_method == PaymentMethod.PERSONAL_CARD:
                report.personal_card_amount += expense.amount_in_base_currency
            elif expense.payment_method == PaymentMethod.CORPORATE_CARD:
                report.corporate_card_amount += expense.amount_in_base_currency
            elif expense.payment_method == PaymentMethod.CASH:
                report.cash_amount += expense.amount_in_base_currency

        # Calculer montant dû
        report.amount_due_employee = report.reimbursable_amount - report.advance_amount
        if report.amount_due_employee < 0:
            report.amount_due_company = abs(report.amount_due_employee)
            report.amount_due_employee = Decimal("0")
        else:
            report.amount_due_company = Decimal("0")

        report.updated_at = datetime.now()

    def submit_report(self, report_id: str) -> Optional[ExpenseReport]:
        """Soumettre rapport"""
        report = self._reports.get(report_id)
        if not report or report.status != ReportStatus.DRAFT:
            return None
        if not report.expense_ids:
            return None

        # Vérifier violations
        has_violations = False
        for exp_id in report.expense_ids:
            expense = self._expenses.get(exp_id)
            if expense and expense.policy_violations:
                has_violations = True
                break

        report.status = ReportStatus.SUBMITTED
        report.submitted_at = datetime.now()
        report.updated_at = datetime.now()

        # Mettre à jour statut des dépenses
        for exp_id in report.expense_ids:
            expense = self._expenses.get(exp_id)
            if expense:
                expense.status = ExpenseStatus.SUBMITTED

        return report

    def approve_report(
        self,
        report_id: str,
        approved_by: str
    ) -> Optional[ExpenseReport]:
        """Approuver rapport"""
        report = self._reports.get(report_id)
        if not report or report.status not in [ReportStatus.SUBMITTED, ReportStatus.UNDER_REVIEW]:
            return None

        report.status = ReportStatus.APPROVED
        report.approved_at = datetime.now()
        report.approved_by = approved_by
        report.updated_at = datetime.now()

        # Mettre à jour dépenses
        for exp_id in report.expense_ids:
            expense = self._expenses.get(exp_id)
            if expense:
                expense.status = ExpenseStatus.APPROVED

        return report

    def reject_report(
        self,
        report_id: str,
        rejected_by: str,
        reason: str
    ) -> Optional[ExpenseReport]:
        """Rejeter rapport"""
        report = self._reports.get(report_id)
        if not report or report.status not in [ReportStatus.SUBMITTED, ReportStatus.UNDER_REVIEW]:
            return None

        report.status = ReportStatus.REJECTED
        report.rejection_reason = reason
        report.updated_at = datetime.now()

        # Mettre à jour dépenses
        for exp_id in report.expense_ids:
            expense = self._expenses.get(exp_id)
            if expense:
                expense.status = ExpenseStatus.REJECTED

        return report

    def mark_report_paid(
        self,
        report_id: str,
        payment_date: date,
        payment_reference: str,
        payment_method: str = "bank_transfer"
    ) -> Optional[ExpenseReport]:
        """Marquer rapport comme payé"""
        report = self._reports.get(report_id)
        if not report or report.status != ReportStatus.APPROVED:
            return None

        report.status = ReportStatus.PAID
        report.payment_date = payment_date
        report.payment_reference = payment_reference
        report.payment_method = payment_method
        report.updated_at = datetime.now()

        # Mettre à jour dépenses
        for exp_id in report.expense_ids:
            expense = self._expenses.get(exp_id)
            if expense:
                expense.status = ExpenseStatus.REIMBURSED

        return report

    def get_report(self, report_id: str) -> Optional[ExpenseReport]:
        """Obtenir rapport"""
        return self._reports.get(report_id)

    def list_reports(
        self,
        employee_id: Optional[str] = None,
        status: Optional[ReportStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[ExpenseReport]:
        """Lister rapports"""
        reports = list(self._reports.values())

        if employee_id:
            reports = [r for r in reports if r.employee_id == employee_id]
        if status:
            reports = [r for r in reports if r.status == status]
        if date_from:
            reports = [r for r in reports if r.submitted_at and r.submitted_at.date() >= date_from]
        if date_to:
            reports = [r for r in reports if r.submitted_at and r.submitted_at.date() <= date_to]

        return sorted(reports, key=lambda x: x.created_at, reverse=True)

    def get_pending_reports(self) -> List[ExpenseReport]:
        """Obtenir rapports en attente d'approbation"""
        return [
            r for r in self._reports.values()
            if r.status in [ReportStatus.SUBMITTED, ReportStatus.UNDER_REVIEW]
        ]

    # ========== Cartes corporate ==========

    def create_corporate_card(
        self,
        card_number_masked: str,
        cardholder_id: str,
        cardholder_name: str,
        card_type: str = "visa",
        credit_limit: Decimal = Decimal("5000"),
        daily_limit: Decimal = Decimal("1000"),
        expiry_date: date = None
    ) -> CorporateCard:
        """Créer carte corporate"""
        card = CorporateCard(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            card_number_masked=card_number_masked,
            card_type=card_type,
            cardholder_id=cardholder_id,
            cardholder_name=cardholder_name,
            credit_limit=credit_limit,
            daily_limit=daily_limit,
            available_credit=credit_limit,
            expiry_date=expiry_date or date.today()
        )
        self._cards[card.id] = card
        return card

    def record_card_transaction(
        self,
        card_id: str,
        transaction_date: datetime,
        merchant_name: str,
        merchant_category: str,
        amount: Decimal,
        currency: str = "EUR"
    ) -> Optional[CardTransaction]:
        """Enregistrer transaction carte"""
        card = self._cards.get(card_id)
        if not card or card.status != CardStatus.ACTIVE:
            return None

        transaction = CardTransaction(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            card_id=card_id,
            card_number_masked=card.card_number_masked,
            cardholder_id=card.cardholder_id,
            transaction_date=transaction_date,
            merchant_name=merchant_name,
            merchant_category=merchant_category,
            amount=amount,
            currency=currency,
            amount_in_base_currency=amount
        )

        # Mettre à jour solde
        card.current_balance += amount
        card.available_credit = card.credit_limit - card.current_balance
        card.last_transaction_date = transaction_date.date()

        self._transactions[transaction.id] = transaction
        return transaction

    def match_transaction_to_expense(
        self,
        transaction_id: str,
        expense_id: str
    ) -> Optional[CardTransaction]:
        """Associer transaction à dépense"""
        transaction = self._transactions.get(transaction_id)
        expense = self._expenses.get(expense_id)

        if not transaction or not expense:
            return None

        transaction.is_matched = True
        transaction.expense_id = expense_id

        # Mettre à jour dépense
        expense.card_id = transaction.card_id
        expense.payment_method = PaymentMethod.CORPORATE_CARD

        return transaction

    def get_unmatched_transactions(
        self,
        cardholder_id: Optional[str] = None
    ) -> List[CardTransaction]:
        """Obtenir transactions non associées"""
        transactions = [
            t for t in self._transactions.values()
            if not t.is_matched and not t.is_personal
        ]

        if cardholder_id:
            transactions = [t for t in transactions if t.cardholder_id == cardholder_id]

        return sorted(transactions, key=lambda x: x.transaction_date, reverse=True)

    def block_card(
        self,
        card_id: str,
        reason: str
    ) -> Optional[CorporateCard]:
        """Bloquer carte"""
        card = self._cards.get(card_id)
        if not card:
            return None

        card.status = CardStatus.BLOCKED
        card.blocked_reason = reason
        return card

    # ========== Statistiques ==========

    def get_expense_stats(
        self,
        period_start: date,
        period_end: date,
        department_id: Optional[str] = None
    ) -> ExpenseStats:
        """Calculer statistiques"""
        stats = ExpenseStats(
            tenant_id=self.tenant_id,
            period_start=period_start,
            period_end=period_end
        )

        expenses = [
            e for e in self._expenses.values()
            if period_start <= e.expense_date <= period_end
        ]

        if department_id:
            expenses = [e for e in expenses if e.department_id == department_id]

        stats.total_expenses = len(expenses)
        stats.total_amount = sum(e.amount_in_base_currency for e in expenses)

        reimbursed = [e for e in expenses if e.status == ExpenseStatus.REIMBURSED]
        stats.total_reimbursed = sum(e.amount_in_base_currency for e in reimbursed)

        pending = [e for e in expenses if e.status in [
            ExpenseStatus.SUBMITTED, ExpenseStatus.PENDING_APPROVAL
        ]]
        stats.pending_amount = sum(e.amount_in_base_currency for e in pending)

        if expenses:
            stats.average_expense = stats.total_amount / len(expenses)

        # Par catégorie
        for expense in expenses:
            cat = expense.category.value
            stats.by_category[cat] = stats.by_category.get(cat, Decimal("0")) + expense.amount_in_base_currency

        # Par département
        for expense in expenses:
            if expense.department_id:
                stats.by_department[expense.department_id] = \
                    stats.by_department.get(expense.department_id, Decimal("0")) + expense.amount_in_base_currency

        # Violations
        stats.policy_violations = sum(
            1 for e in expenses if e.policy_violations
        )

        # Top vendors
        vendor_totals: Dict[str, Decimal] = {}
        for expense in expenses:
            if expense.vendor:
                vendor_totals[expense.vendor] = \
                    vendor_totals.get(expense.vendor, Decimal("0")) + expense.amount_in_base_currency

        stats.top_vendors = [
            {"vendor": k, "amount": v}
            for k, v in sorted(vendor_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        return stats

    def get_employee_balance(self, employee_id: str) -> Dict[str, Decimal]:
        """Obtenir solde employé"""
        pending = Decimal("0")
        approved = Decimal("0")
        reimbursed = Decimal("0")

        for expense in self._expenses.values():
            if expense.employee_id != employee_id:
                continue
            if not expense.is_reimbursable:
                continue

            if expense.status in [ExpenseStatus.SUBMITTED, ExpenseStatus.PENDING_APPROVAL]:
                pending += expense.amount_in_base_currency
            elif expense.status == ExpenseStatus.APPROVED:
                approved += expense.amount_in_base_currency
            elif expense.status == ExpenseStatus.REIMBURSED:
                reimbursed += expense.amount_in_base_currency

        return {
            "pending": pending,
            "approved_awaiting_payment": approved,
            "reimbursed": reimbursed,
            "total_due": pending + approved
        }


def create_expense_service(tenant_id: str) -> ExpenseService:
    """Factory function pour créer le service expense"""
    return ExpenseService(tenant_id)
