"""
AZALS MODULE HR - Router Unifié
================================
Router unifié compatible v1/v2 avec get_context().
Migration: Remplace router.py et router_v2.py.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from .models import DocumentType, EmployeeStatus, EvaluationStatus, LeaveStatus, LeaveType, TrainingStatus, TrainingType
from .schemas import (
    ContractCreate,
    ContractResponse,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    EmployeeCreate,
    EmployeeList,
    EmployeeResponse,
    EmployeeSkillCreate,
    EmployeeSkillResponse,
    EmployeeUpdate,
    EvaluationCreate,
    EvaluationResponse,
    EvaluationUpdate,
    HRDashboard,
    HRDocumentCreate,
    HRDocumentResponse,
    LeaveBalanceResponse,
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveRequestUpdate,
    PayrollPeriodCreate,
    PayrollPeriodResponse,
    PayslipCreate,
    PayslipResponse,
    PositionCreate,
    PositionResponse,
    PositionUpdate,
    SkillCreate,
    SkillResponse,
    TimeEntryCreate,
    TimeEntryResponse,
    TrainingCreate,
    TrainingParticipantCreate,
    TrainingParticipantResponse,
    TrainingResponse,
)
from .service import get_hr_service, HRDashboardError

router = APIRouter(prefix="/hr", tags=["RH - Ressources Humaines"])

# =============================================================================
# SERVICE DEPENDENCY
# =============================================================================

def get_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
) -> object:
    """Factory service avec SaaSContext unifié."""
    return get_hr_service(db, context.tenant_id)

# =============================================================================
# DÉPARTEMENTS
# =============================================================================

@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un département."""
    service = get_hr_service(db, context.tenant_id)
    return service.create_department(data)

@router.get("/departments", response_model=list[DepartmentResponse])
def list_departments(
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les départements."""
    service = get_hr_service(db, context.tenant_id)
    return service.list_departments(is_active=is_active)

@router.get("/departments/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un département par son ID."""
    service = get_hr_service(db, context.tenant_id)
    department = service.get_department(department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Département non trouvé")
    return department

@router.put("/departments/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: UUID,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour un département."""
    service = get_hr_service(db, context.tenant_id)
    return service.update_department(department_id, data)

@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Supprimer un département (soft delete)."""
    if not context.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent supprimer des départements"
        )

    service = get_hr_service(db, context.tenant_id)
    try:
        success = service.delete_department(department_id)
        if not success:
            raise HTTPException(status_code=404, detail="Département non trouvé")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# POSTES
# =============================================================================

@router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
def create_position(
    data: PositionCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un poste."""
    service = get_hr_service(db, context.tenant_id)
    return service.create_position(data)

@router.get("/positions", response_model=list[PositionResponse])
def list_positions(
    department_id: UUID | None = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les postes."""
    service = get_hr_service(db, context.tenant_id)
    return service.list_positions(department_id=department_id, is_active=is_active)

@router.get("/positions/{position_id}", response_model=PositionResponse)
def get_position(
    position_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un poste par son ID."""
    service = get_hr_service(db, context.tenant_id)
    position = service.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Poste non trouvé")
    return position

@router.put("/positions/{position_id}", response_model=PositionResponse)
def update_position(
    position_id: UUID,
    data: PositionUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour un poste."""
    service = get_hr_service(db, context.tenant_id)
    return service.update_position(position_id, data)

@router.delete("/positions/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    position_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Supprimer un poste (soft delete)."""
    if not context.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent supprimer des postes"
        )

    service = get_hr_service(db, context.tenant_id)
    try:
        success = service.delete_position(position_id)
        if not success:
            raise HTTPException(status_code=404, detail="Poste non trouvé")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# EMPLOYÉS
# =============================================================================

@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un employé."""
    service = get_hr_service(db, context.tenant_id)
    return service.create_employee(data)

@router.get("/employees", response_model=EmployeeList)
def list_employees(
    department_id: UUID | None = None,
    position_id: UUID | None = None,
    status: EmployeeStatus | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les employés avec filtres et pagination."""
    service = get_hr_service(db, context.tenant_id)
    employees, total = service.list_employees(
        department_id=department_id,
        position_id=position_id,
        status=status,
        search=search,
        page=page,
        page_size=page_size
    )
    return EmployeeList(
        items=employees,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un employé par son ID."""
    service = get_hr_service(db, context.tenant_id)
    employee = service.get_employee(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employé non trouvé")
    return employee

@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: UUID,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour un employé."""
    service = get_hr_service(db, context.tenant_id)
    return service.update_employee(employee_id, data)

@router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Supprimer un employé (soft delete - désactivation)."""
    if not context.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent supprimer des employés"
        )

    service = get_hr_service(db, context.tenant_id)
    success = service.delete_employee(employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employé non trouvé")

@router.post("/employees/{employee_id}/terminate", response_model=EmployeeResponse)
def terminate_employee(
    employee_id: UUID,
    termination_date: date,
    termination_reason: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre fin au contrat d'un employé."""
    service = get_hr_service(db, context.tenant_id)
    return service.terminate_employee(
        employee_id=employee_id,
        termination_date=termination_date,
        termination_reason=termination_reason,
        terminated_by=context.user_id
    )

# =============================================================================
# CONTRATS
# =============================================================================

@router.post("/contracts", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    data: ContractCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un contrat."""
    service = get_hr_service(db, context.tenant_id)
    return service.create_contract(data, created_by=context.user_id)

@router.get("/contracts/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un contrat par son ID."""
    service = get_hr_service(db, context.tenant_id)
    contract = service.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")
    return contract

@router.get("/employees/{employee_id}/contracts", response_model=list[ContractResponse])
def get_employee_contracts(
    employee_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer les contrats d'un employé."""
    service = get_hr_service(db, context.tenant_id)
    return service.get_employee_contracts(employee_id)

# =============================================================================
# DEMANDES DE CONGÉS
# =============================================================================

class LeaveRequestSimpleCreate(PydanticBaseModel):
    """Schema simplifié pour création de congé via frontend."""
    employee_id: UUID
    type: str
    start_date: date
    end_date: date
    reason: str | None = None

@router.post("/leave-requests", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def create_leave_request_simple(
    data: LeaveRequestSimpleCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une demande de congé (endpoint simplifié)."""
    service = get_hr_service(db, context.tenant_id)
    try:
        leave_data = LeaveRequestCreate(
            leave_type=LeaveType(data.type),
            start_date=data.start_date,
            end_date=data.end_date,
            reason=data.reason
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Type de congé invalide: {data.type}. Valeurs acceptées: {[t.value for t in LeaveType]}"
        )
    return service.create_leave_request(data.employee_id, leave_data)

@router.post("/employees/{employee_id}/leave-requests", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def create_leave_request(
    employee_id: UUID,
    data: LeaveRequestCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une demande de congé."""
    service = get_hr_service(db, context.tenant_id)
    return service.create_leave_request(employee_id, data)

@router.get("/leave-requests")
def list_leave_requests(
    employee_id: UUID | None = None,
    status: LeaveStatus | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les demandes de congés."""
    service = get_hr_service(db, context.tenant_id)
    items, total = service.list_leave_requests(
        employee_id=employee_id,
        status=status,
        start_date=from_date,
        end_date=to_date
    )
    items_response = []
    for item in items:
        data = LeaveRequestResponse.model_validate(item)
        if item.employee:
            data.employee_name = f"{item.employee.first_name} {item.employee.last_name}"
        items_response.append(data.model_dump(by_alias=True))
    return {"items": items_response, "total": total}

@router.put("/leave-requests/{leave_id}", response_model=LeaveRequestResponse)
def update_leave_request(
    leave_id: UUID,
    data: LeaveRequestUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour une demande de congé."""
    service = get_hr_service(db, context.tenant_id)
    result = service.update_leave_request(leave_id, data)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Demande de congé introuvable ou ne peut pas être modifiée"
        )
    return result

@router.post("/leave-requests/{leave_id}/approve", response_model=LeaveRequestResponse)
def approve_leave_request(
    leave_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Approuver une demande de congé."""
    service = get_hr_service(db, context.tenant_id)
    result = service.approve_leave_request(leave_id, approver_id=context.user_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Demande de congé introuvable ou déjà traitée")
    return result

@router.post("/leave-requests/{leave_id}/reject", response_model=LeaveRequestResponse)
def reject_leave_request(
    leave_id: UUID,
    rejection_reason: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Rejeter une demande de congé."""
    service = get_hr_service(db, context.tenant_id)
    result = service.reject_leave_request(
        leave_id=leave_id,
        approver_id=context.user_id,
        reason=rejection_reason
    )
    if result is None:
        raise HTTPException(status_code=400, detail="Demande de congé introuvable ou déjà traitée")
    return result

@router.get("/employees/{employee_id}/leave-balance", response_model=list[LeaveBalanceResponse])
def get_employee_leave_balance(
    employee_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer le solde de congés d'un employé."""
    service = get_hr_service(db, context.tenant_id)
    return service.get_employee_leave_balance(employee_id)

# =============================================================================
# PÉRIODES DE PAIE
# =============================================================================

@router.post("/payroll-periods", response_model=PayrollPeriodResponse, status_code=status.HTTP_201_CREATED)
def create_payroll_period(
    data: PayrollPeriodCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une période de paie."""
    service = get_hr_service(db, context.tenant_id)
    return service.create_payroll_period(data, created_by=context.user_id)

@router.get("/payroll-periods", response_model=list[PayrollPeriodResponse])
def list_payroll_periods(
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les périodes de paie."""
    service = get_hr_service(db, context.tenant_id)
    return service.list_payroll_periods(year=year, month=month)

@router.get("/payroll-periods/{period_id}", response_model=PayrollPeriodResponse)
def get_payroll_period(
    period_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une période de paie par son ID."""
    service = get_hr_service(db, context.tenant_id)
    period = service.get_payroll_period(period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Période de paie non trouvée")
    return period

# =============================================================================
# BULLETINS DE PAIE
# =============================================================================

@router.get("/payslips", response_model=list[PayslipResponse])
def list_payslips(
    employee_id: UUID | None = None,
    period_id: UUID | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les bulletins de paie."""
    service = get_hr_service(db, context.tenant_id)
    return service.list_payslips(employee_id=employee_id, period_id=period_id)

@router.post("/payslips", response_model=PayslipResponse, status_code=status.HTTP_201_CREATED)
def create_payslip(
    data: PayslipCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un bulletin de paie."""
    service = get_hr_service(db, context.tenant_id)
    return service.create_payslip(data, created_by=context.user_id)

@router.post("/payslips/{payslip_id}/validate", response_model=PayslipResponse)
def validate_payslip(
    payslip_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Valider un bulletin de paie."""
    service = get_hr_service(db, context.tenant_id)
    return service.validate_payslip(payslip_id, validated_by=context.user_id)

@router.get("/employees/{employee_id}/payslips", response_model=list[PayslipResponse])
def get_employee_payslips(
    employee_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer les bulletins de paie d'un employé."""
    service = get_hr_service(db, context.tenant_id)
    return service.get_employee_payslips(employee_id)

# =============================================================================
# SAISIE DES TEMPS
# =============================================================================

@router.post("/employees/{employee_id}/time-entries", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
def create_time_entry(
    employee_id: UUID,
    data: TimeEntryCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une saisie de temps."""
    service = get_hr_service(db, context.tenant_id)
    return service.create_time_entry(employee_id, data)

@router.get("/time-entries", response_model=list[TimeEntryResponse])
def list_time_entries(
    employee_id: UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les saisies de temps."""
    service = get_hr_service(db, context.tenant_id)
    return service.list_time_entries(
        employee_id=employee_id,
        start_date=from_date,
        end_date=to_date
    )

@router.get("/timesheets", response_model=list[TimeEntryResponse])
def list_timesheets(
    employee_id: UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Alias de /time-entries pour compatibilité frontend."""
    service = get_hr_service(db, context.tenant_id)
    return service.list_time_entries(
        employee_id=employee_id,
        start_date=from_date,
        end_date=to_date
    )

# =============================================================================
# COMPÉTENCES
# =============================================================================

@router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(
    data: SkillCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une compétence."""
    service = get_hr_service(db, context.tenant_id)
    return service.create_skill(data)

@router.get("/skills", response_model=list[SkillResponse])
def list_skills(
    category: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les compétences."""
    service = get_hr_service(db, context.tenant_id)
    return service.list_skills(category=category)

@router.post("/employees/{employee_id}/skills", response_model=EmployeeSkillResponse, status_code=status.HTTP_201_CREATED)
def assign_skill_to_employee(
    employee_id: UUID,
    data: EmployeeSkillCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Assigner une compétence à un employé."""
    service = get_hr_service(db, context.tenant_id)
    return service.assign_skill_to_employee(employee_id, data)

@router.get("/employees/{employee_id}/skills", response_model=list[EmployeeSkillResponse])
def get_employee_skills(
    employee_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer les compétences d'un employé."""
    service = get_hr_service(db, context.tenant_id)
    return service.get_employee_skills(employee_id)

# =============================================================================
# FORMATIONS
# =============================================================================

@router.post("/trainings", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED)
def create_training(
    data: TrainingCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une formation."""
    service = get_hr_service(db, context.tenant_id)
    return service.create_training(data, created_by=context.user_id)

@router.get("/trainings", response_model=list[TrainingResponse])
def list_trainings(
    training_type: TrainingType | None = None,
    status: TrainingStatus | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les formations."""
    service = get_hr_service(db, context.tenant_id)
    return service.list_trainings(training_type=training_type, status=status)

@router.get("/trainings/{training_id}", response_model=TrainingResponse)
def get_training(
    training_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une formation par son ID."""
    service = get_hr_service(db, context.tenant_id)
    training = service.get_training(training_id)
    if not training:
        raise HTTPException(status_code=404, detail="Formation non trouvée")
    return training

@router.post("/trainings/{training_id}/enroll", response_model=TrainingParticipantResponse, status_code=status.HTTP_201_CREATED)
def enroll_in_training(
    training_id: UUID,
    data: TrainingParticipantCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Inscrire un employé à une formation."""
    service = get_hr_service(db, context.tenant_id)
    return service.enroll_in_training(training_id, data)

# =============================================================================
# ÉVALUATIONS
# =============================================================================

@router.post("/evaluations", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    data: EvaluationCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une évaluation."""
    service = get_hr_service(db, context.tenant_id)
    return service.create_evaluation(data, created_by=context.user_id)

@router.get("/evaluations", response_model=list[EvaluationResponse])
def list_evaluations(
    employee_id: UUID | None = None,
    evaluator_id: UUID | None = None,
    status: EvaluationStatus | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les évaluations."""
    service = get_hr_service(db, context.tenant_id)
    return service.list_evaluations(
        employee_id=employee_id,
        evaluator_id=evaluator_id,
        status=status
    )

@router.get("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation(
    evaluation_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une évaluation par son ID."""
    service = get_hr_service(db, context.tenant_id)
    evaluation = service.get_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Évaluation non trouvée")
    return evaluation

@router.put("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def update_evaluation(
    evaluation_id: UUID,
    data: EvaluationUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour une évaluation."""
    service = get_hr_service(db, context.tenant_id)
    return service.update_evaluation(evaluation_id, data, updated_by=context.user_id)

# =============================================================================
# DOCUMENTS RH
# =============================================================================

@router.post("/documents", response_model=HRDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_hr_document(
    data: HRDocumentCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un document RH."""
    service = get_hr_service(db, context.tenant_id)
    return service.create_hr_document(data, uploaded_by=context.user_id)

@router.get("/employees/{employee_id}/documents", response_model=list[HRDocumentResponse])
def get_employee_documents(
    employee_id: UUID,
    document_type: DocumentType | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer les documents d'un employé."""
    service = get_hr_service(db, context.tenant_id)
    return service.get_employee_documents(employee_id, document_type=document_type)

# =============================================================================
# DASHBOARD
# =============================================================================

@router.get("/dashboard", response_model=HRDashboard)
def get_hr_dashboard(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer le dashboard RH."""
    try:
        service = get_hr_service(db, context.tenant_id)
        return service.get_hr_dashboard()
    except HRDashboardError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": e.code,
                "message": e.message,
                "tenant_id": e.tenant_id
            }
        )
