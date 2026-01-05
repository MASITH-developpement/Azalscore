"""
AZALS MODULE M3 - Router RH
===========================

Endpoints API pour la gestion des ressources humaines.
"""

from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user, get_tenant_id

from .models import (
    EmployeeStatus, LeaveStatus,
    TrainingType, TrainingStatus,
    EvaluationStatus, DocumentType
)
from .schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    PositionCreate, PositionUpdate, PositionResponse,
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeList,
    ContractCreate, ContractResponse,
    LeaveRequestCreate, LeaveRequestResponse, LeaveBalanceResponse,
    PayrollPeriodCreate, PayrollPeriodResponse, PayslipCreate, PayslipResponse,
    TimeEntryCreate, TimeEntryResponse,
    SkillCreate, SkillResponse, EmployeeSkillCreate, EmployeeSkillResponse,
    TrainingCreate, TrainingResponse, TrainingParticipantCreate, TrainingParticipantResponse,
    EvaluationCreate, EvaluationUpdate, EvaluationResponse,
    HRDocumentCreate, HRDocumentResponse,
    HRDashboard
)
from .service import get_hr_service

router = APIRouter(prefix="/hr", tags=["RH - Ressources Humaines"])


# =============================================================================
# DÉPARTEMENTS
# =============================================================================

@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer un département."""
    service = get_hr_service(db, tenant_id)
    return service.create_department(data)


@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(
    is_active: bool = True,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les départements."""
    service = get_hr_service(db, tenant_id)
    return service.list_departments(is_active)


@router.get("/departments/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer un département."""
    service = get_hr_service(db, tenant_id)
    dept = service.get_department(department_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


@router.put("/departments/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: UUID,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Mettre à jour un département."""
    service = get_hr_service(db, tenant_id)
    dept = service.update_department(department_id, data)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


# =============================================================================
# POSTES
# =============================================================================

@router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
def create_position(
    data: PositionCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer un poste."""
    service = get_hr_service(db, tenant_id)
    return service.create_position(data)


@router.get("/positions", response_model=List[PositionResponse])
def list_positions(
    department_id: Optional[UUID] = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les postes."""
    service = get_hr_service(db, tenant_id)
    return service.list_positions(department_id, is_active)


@router.get("/positions/{position_id}", response_model=PositionResponse)
def get_position(
    position_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer un poste."""
    service = get_hr_service(db, tenant_id)
    position = service.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.put("/positions/{position_id}", response_model=PositionResponse)
def update_position(
    position_id: UUID,
    data: PositionUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Mettre à jour un poste."""
    service = get_hr_service(db, tenant_id)
    position = service.update_position(position_id, data)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


# =============================================================================
# EMPLOYÉS
# =============================================================================

@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer un employé."""
    service = get_hr_service(db, tenant_id)
    existing = service.get_employee_by_number(data.employee_number)
    if existing:
        raise HTTPException(status_code=409, detail="Employee number already exists")
    return service.create_employee(data)


@router.get("/employees", response_model=EmployeeList)
def list_employees(
    department_id: Optional[UUID] = None,
    status: Optional[EmployeeStatus] = None,
    manager_id: Optional[UUID] = None,
    search: Optional[str] = None,
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les employés."""
    service = get_hr_service(db, tenant_id)
    items, total = service.list_employees(
        department_id=department_id,
        status=status,
        manager_id=manager_id,
        search=search,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return EmployeeList(items=items, total=total)


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer un employé."""
    service = get_hr_service(db, tenant_id)
    employee = service.get_employee(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: UUID,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Mettre à jour un employé."""
    service = get_hr_service(db, tenant_id)
    employee = service.update_employee(employee_id, data)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.post("/employees/{employee_id}/terminate", response_model=EmployeeResponse)
def terminate_employee(
    employee_id: UUID,
    end_date: date,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Terminer le contrat d'un employé."""
    service = get_hr_service(db, tenant_id)
    employee = service.terminate_employee(employee_id, end_date, reason)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


# =============================================================================
# CONTRATS
# =============================================================================

@router.post("/contracts", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    data: ContractCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer un contrat."""
    service = get_hr_service(db, tenant_id)
    return service.create_contract(data, current_user.id)


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer un contrat."""
    service = get_hr_service(db, tenant_id)
    contract = service.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.get("/employees/{employee_id}/contracts", response_model=List[ContractResponse])
def list_employee_contracts(
    employee_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les contrats d'un employé."""
    service = get_hr_service(db, tenant_id)
    return service.list_employee_contracts(employee_id)


# =============================================================================
# CONGÉS
# =============================================================================

@router.post("/employees/{employee_id}/leave-requests", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def create_leave_request(
    employee_id: UUID,
    data: LeaveRequestCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une demande de congé."""
    service = get_hr_service(db, tenant_id)
    return service.create_leave_request(employee_id, data)


@router.get("/leave-requests")
def list_leave_requests(
    employee_id: Optional[UUID] = None,
    leave_status: Optional[LeaveStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les demandes de congé."""
    service = get_hr_service(db, tenant_id)
    items, total = service.list_leave_requests(
        employee_id=employee_id,
        status=leave_status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return {"items": items, "total": total}


@router.post("/leave-requests/{leave_id}/approve", response_model=LeaveRequestResponse)
def approve_leave_request(
    leave_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Approuver une demande de congé."""
    service = get_hr_service(db, tenant_id)
    leave = service.approve_leave_request(leave_id, current_user.id)
    if not leave:
        raise HTTPException(status_code=400, detail="Leave request not found or not pending")
    return leave


@router.post("/leave-requests/{leave_id}/reject", response_model=LeaveRequestResponse)
def reject_leave_request(
    leave_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Rejeter une demande de congé."""
    service = get_hr_service(db, tenant_id)
    leave = service.reject_leave_request(leave_id, current_user.id, reason)
    if not leave:
        raise HTTPException(status_code=400, detail="Leave request not found or not pending")
    return leave


@router.get("/employees/{employee_id}/leave-balance", response_model=List[LeaveBalanceResponse])
def get_employee_leave_balance(
    employee_id: UUID,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer les soldes de congés d'un employé."""
    service = get_hr_service(db, tenant_id)
    return service.get_employee_leave_balance(employee_id, year)


# =============================================================================
# PAIE
# =============================================================================

@router.post("/payroll-periods", response_model=PayrollPeriodResponse, status_code=status.HTTP_201_CREATED)
def create_payroll_period(
    data: PayrollPeriodCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une période de paie."""
    service = get_hr_service(db, tenant_id)
    return service.create_payroll_period(data)


@router.get("/payroll-periods", response_model=List[PayrollPeriodResponse])
def list_payroll_periods(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les périodes de paie."""
    service = get_hr_service(db, tenant_id)
    return service.list_payroll_periods(year)


@router.get("/payroll-periods/{period_id}", response_model=PayrollPeriodResponse)
def get_payroll_period(
    period_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer une période de paie."""
    service = get_hr_service(db, tenant_id)
    period = service.get_payroll_period(period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Payroll period not found")
    return period


@router.post("/payslips", response_model=PayslipResponse, status_code=status.HTTP_201_CREATED)
def create_payslip(
    data: PayslipCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer un bulletin de paie."""
    service = get_hr_service(db, tenant_id)
    try:
        return service.create_payslip(data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payslips/{payslip_id}/validate", response_model=PayslipResponse)
def validate_payslip(
    payslip_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Valider un bulletin de paie."""
    service = get_hr_service(db, tenant_id)
    payslip = service.validate_payslip(payslip_id, current_user.id)
    if not payslip:
        raise HTTPException(status_code=400, detail="Payslip not found or already validated")
    return payslip


@router.get("/employees/{employee_id}/payslips", response_model=List[PayslipResponse])
def get_employee_payslips(
    employee_id: UUID,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer les bulletins d'un employé."""
    service = get_hr_service(db, tenant_id)
    return service.get_employee_payslips(employee_id, year)


# =============================================================================
# TEMPS DE TRAVAIL
# =============================================================================

@router.post("/employees/{employee_id}/time-entries", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
def create_time_entry(
    employee_id: UUID,
    data: TimeEntryCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une entrée de temps."""
    service = get_hr_service(db, tenant_id)
    return service.create_time_entry(employee_id, data)


@router.get("/time-entries", response_model=List[TimeEntryResponse])
def list_time_entries(
    employee_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les entrées de temps."""
    service = get_hr_service(db, tenant_id)
    return service.list_time_entries(employee_id, start_date, end_date)


# =============================================================================
# COMPÉTENCES
# =============================================================================

@router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(
    data: SkillCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une compétence."""
    service = get_hr_service(db, tenant_id)
    return service.create_skill(data)


@router.get("/skills", response_model=List[SkillResponse])
def list_skills(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les compétences."""
    service = get_hr_service(db, tenant_id)
    return service.list_skills(category)


@router.post("/employees/{employee_id}/skills", response_model=EmployeeSkillResponse, status_code=status.HTTP_201_CREATED)
def add_employee_skill(
    employee_id: UUID,
    data: EmployeeSkillCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Ajouter une compétence à un employé."""
    service = get_hr_service(db, tenant_id)
    return service.add_employee_skill(employee_id, data)


@router.get("/employees/{employee_id}/skills", response_model=List[EmployeeSkillResponse])
def get_employee_skills(
    employee_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer les compétences d'un employé."""
    service = get_hr_service(db, tenant_id)
    return service.get_employee_skills(employee_id)


# =============================================================================
# FORMATIONS
# =============================================================================

@router.post("/trainings", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED)
def create_training(
    data: TrainingCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une formation."""
    service = get_hr_service(db, tenant_id)
    return service.create_training(data, current_user.id)


@router.get("/trainings", response_model=List[TrainingResponse])
def list_trainings(
    training_status: Optional[TrainingStatus] = None,
    training_type: Optional[TrainingType] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les formations."""
    service = get_hr_service(db, tenant_id)
    return service.list_trainings(training_status, training_type)


@router.get("/trainings/{training_id}", response_model=TrainingResponse)
def get_training(
    training_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer une formation."""
    service = get_hr_service(db, tenant_id)
    training = service.get_training(training_id)
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    return training


@router.post("/trainings/{training_id}/enroll", response_model=TrainingParticipantResponse, status_code=status.HTTP_201_CREATED)
def enroll_in_training(
    training_id: UUID,
    data: TrainingParticipantCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Inscrire un employé à une formation."""
    service = get_hr_service(db, tenant_id)
    return service.enroll_in_training(training_id, data.employee_id)


# =============================================================================
# ÉVALUATIONS
# =============================================================================

@router.post("/evaluations", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    data: EvaluationCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer une évaluation."""
    service = get_hr_service(db, tenant_id)
    return service.create_evaluation(data)


@router.get("/evaluations", response_model=List[EvaluationResponse])
def list_evaluations(
    employee_id: Optional[UUID] = None,
    evaluation_status: Optional[EvaluationStatus] = None,
    evaluator_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Lister les évaluations."""
    service = get_hr_service(db, tenant_id)
    return service.list_evaluations(employee_id, evaluation_status, evaluator_id)


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation(
    evaluation_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer une évaluation."""
    service = get_hr_service(db, tenant_id)
    evaluation = service.get_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


@router.put("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def update_evaluation(
    evaluation_id: UUID,
    data: EvaluationUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Mettre à jour une évaluation."""
    service = get_hr_service(db, tenant_id)
    evaluation = service.update_evaluation(evaluation_id, data)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


# =============================================================================
# DOCUMENTS
# =============================================================================

@router.post("/documents", response_model=HRDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    data: HRDocumentCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Créer un document RH."""
    service = get_hr_service(db, tenant_id)
    return service.create_document(data, current_user.id)


@router.get("/employees/{employee_id}/documents", response_model=List[HRDocumentResponse])
def get_employee_documents(
    employee_id: UUID,
    doc_type: Optional[DocumentType] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer les documents d'un employé."""
    service = get_hr_service(db, tenant_id)
    return service.get_employee_documents(employee_id, doc_type)


# =============================================================================
# DASHBOARD
# =============================================================================

@router.get("/dashboard", response_model=HRDashboard)
def get_hr_dashboard(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user = Depends(get_current_user)
):
    """Récupérer le dashboard RH."""
    service = get_hr_service(db, tenant_id)
    return service.get_dashboard()
