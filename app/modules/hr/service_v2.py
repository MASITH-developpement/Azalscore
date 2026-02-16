"""
AZALS - Hr Service (v2 - CRUDRouter Compatible)
====================================================

Service compatible avec BaseService et CRUDRouter.
Migration automatique depuis service.py.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.base_service import BaseService
from app.core.saas_context import Result, SaaSContext

from app.modules.hr.models import (
    Department,
    Position,
    Employee,
    Contract,
    LeaveRequest,
    LeaveBalance,
    PayrollPeriod,
    Payslip,
    PayslipLine,
    HRTimeEntry,
    Skill,
    EmployeeSkill,
    Training,
    TrainingParticipant,
    Evaluation,
    HRDocument,
)
from app.modules.hr.schemas import (
    ContractBase,
    ContractCreate,
    ContractResponse,
    DepartmentBase,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    EmployeeBase,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeSkillCreate,
    EmployeeSkillResponse,
    EmployeeUpdate,
    EvaluationBase,
    EvaluationCreate,
    EvaluationResponse,
    EvaluationUpdate,
    HRDocumentCreate,
    HRDocumentResponse,
    LeaveBalanceResponse,
    LeaveRequestBase,
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveRequestUpdate,
    PayrollPeriodBase,
    PayrollPeriodCreate,
    PayrollPeriodResponse,
    PayslipCreate,
    PayslipLineCreate,
    PayslipLineResponse,
    PayslipResponse,
    PositionBase,
    PositionCreate,
    PositionResponse,
    PositionUpdate,
    SkillBase,
    SkillCreate,
    SkillResponse,
    TimeEntryBase,
    TimeEntryCreate,
    TimeEntryResponse,
    TrainingBase,
    TrainingCreate,
    TrainingParticipantCreate,
    TrainingParticipantResponse,
    TrainingResponse,
)

logger = logging.getLogger(__name__)



class DepartmentService(BaseService[Department, Any, Any]):
    """Service CRUD pour department."""

    model = Department

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Department]
    # - get_or_fail(id) -> Result[Department]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Department]
    # - update(id, data) -> Result[Department]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class PositionService(BaseService[Position, Any, Any]):
    """Service CRUD pour position."""

    model = Position

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Position]
    # - get_or_fail(id) -> Result[Position]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Position]
    # - update(id, data) -> Result[Position]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class EmployeeService(BaseService[Employee, Any, Any]):
    """Service CRUD pour employee."""

    model = Employee

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Employee]
    # - get_or_fail(id) -> Result[Employee]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Employee]
    # - update(id, data) -> Result[Employee]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ContractService(BaseService[Contract, Any, Any]):
    """Service CRUD pour contract."""

    model = Contract

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Contract]
    # - get_or_fail(id) -> Result[Contract]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Contract]
    # - update(id, data) -> Result[Contract]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class LeaveRequestService(BaseService[LeaveRequest, Any, Any]):
    """Service CRUD pour leaverequest."""

    model = LeaveRequest

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[LeaveRequest]
    # - get_or_fail(id) -> Result[LeaveRequest]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[LeaveRequest]
    # - update(id, data) -> Result[LeaveRequest]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class LeaveBalanceService(BaseService[LeaveBalance, Any, Any]):
    """Service CRUD pour leavebalance."""

    model = LeaveBalance

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[LeaveBalance]
    # - get_or_fail(id) -> Result[LeaveBalance]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[LeaveBalance]
    # - update(id, data) -> Result[LeaveBalance]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class PayrollPeriodService(BaseService[PayrollPeriod, Any, Any]):
    """Service CRUD pour payrollperiod."""

    model = PayrollPeriod

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[PayrollPeriod]
    # - get_or_fail(id) -> Result[PayrollPeriod]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[PayrollPeriod]
    # - update(id, data) -> Result[PayrollPeriod]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class PayslipService(BaseService[Payslip, Any, Any]):
    """Service CRUD pour payslip."""

    model = Payslip

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Payslip]
    # - get_or_fail(id) -> Result[Payslip]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Payslip]
    # - update(id, data) -> Result[Payslip]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class PayslipLineService(BaseService[PayslipLine, Any, Any]):
    """Service CRUD pour payslipline."""

    model = PayslipLine

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[PayslipLine]
    # - get_or_fail(id) -> Result[PayslipLine]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[PayslipLine]
    # - update(id, data) -> Result[PayslipLine]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class HRTimeEntryService(BaseService[HRTimeEntry, Any, Any]):
    """Service CRUD pour hrtimeentry."""

    model = HRTimeEntry

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[HRTimeEntry]
    # - get_or_fail(id) -> Result[HRTimeEntry]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[HRTimeEntry]
    # - update(id, data) -> Result[HRTimeEntry]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class SkillService(BaseService[Skill, Any, Any]):
    """Service CRUD pour skill."""

    model = Skill

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Skill]
    # - get_or_fail(id) -> Result[Skill]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Skill]
    # - update(id, data) -> Result[Skill]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class EmployeeSkillService(BaseService[EmployeeSkill, Any, Any]):
    """Service CRUD pour employeeskill."""

    model = EmployeeSkill

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[EmployeeSkill]
    # - get_or_fail(id) -> Result[EmployeeSkill]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[EmployeeSkill]
    # - update(id, data) -> Result[EmployeeSkill]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class TrainingService(BaseService[Training, Any, Any]):
    """Service CRUD pour training."""

    model = Training

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Training]
    # - get_or_fail(id) -> Result[Training]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Training]
    # - update(id, data) -> Result[Training]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class TrainingParticipantService(BaseService[TrainingParticipant, Any, Any]):
    """Service CRUD pour trainingparticipant."""

    model = TrainingParticipant

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[TrainingParticipant]
    # - get_or_fail(id) -> Result[TrainingParticipant]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[TrainingParticipant]
    # - update(id, data) -> Result[TrainingParticipant]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class EvaluationService(BaseService[Evaluation, Any, Any]):
    """Service CRUD pour evaluation."""

    model = Evaluation

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Evaluation]
    # - get_or_fail(id) -> Result[Evaluation]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Evaluation]
    # - update(id, data) -> Result[Evaluation]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class HRDocumentService(BaseService[HRDocument, Any, Any]):
    """Service CRUD pour hrdocument."""

    model = HRDocument

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[HRDocument]
    # - get_or_fail(id) -> Result[HRDocument]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[HRDocument]
    # - update(id, data) -> Result[HRDocument]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques

