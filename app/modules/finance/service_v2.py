"""
AZALS - Finance Service (v2 - CRUDRouter Compatible)
=========================================================

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

from app.modules.finance.models import (
    Account,
    Journal,
    FiscalYear,
    FiscalPeriod,
    JournalEntry,
    JournalEntryLine,
    BankAccount,
    BankStatement,
    BankStatementLine,
    BankTransaction,
    CashForecast,
    CashFlowCategory,
    FinancialReport,
)
from app.modules.finance.schemas import (
    AccountBase,
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    BankAccountBase,
    BankAccountCreate,
    BankAccountResponse,
    BankAccountUpdate,
    BankStatementBase,
    BankStatementCreate,
    BankStatementLineBase,
    BankStatementLineCreate,
    BankStatementLineResponse,
    BankStatementResponse,
    BankTransactionBase,
    BankTransactionCreate,
    BankTransactionResponse,
    CashFlowCategoryBase,
    CashFlowCategoryCreate,
    CashFlowCategoryResponse,
    CashForecastBase,
    CashForecastCreate,
    CashForecastResponse,
    CashForecastUpdate,
    EntryBase,
    EntryCreate,
    EntryLineBase,
    EntryLineCreate,
    EntryLineResponse,
    EntryResponse,
    EntryUpdate,
    FinancialReportCreate,
    FinancialReportResponse,
    FiscalPeriodResponse,
    FiscalYearBase,
    FiscalYearCreate,
    FiscalYearResponse,
    JournalBase,
    JournalCreate,
    JournalResponse,
    JournalUpdate,
)

logger = logging.getLogger(__name__)



class AccountService(BaseService[Account, Any, Any]):
    """Service CRUD pour account."""

    model = Account

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Account]
    # - get_or_fail(id) -> Result[Account]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Account]
    # - update(id, data) -> Result[Account]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class JournalService(BaseService[Journal, Any, Any]):
    """Service CRUD pour journal."""

    model = Journal

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Journal]
    # - get_or_fail(id) -> Result[Journal]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Journal]
    # - update(id, data) -> Result[Journal]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class FiscalYearService(BaseService[FiscalYear, Any, Any]):
    """Service CRUD pour fiscalyear."""

    model = FiscalYear

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[FiscalYear]
    # - get_or_fail(id) -> Result[FiscalYear]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[FiscalYear]
    # - update(id, data) -> Result[FiscalYear]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class FiscalPeriodService(BaseService[FiscalPeriod, Any, Any]):
    """Service CRUD pour fiscalperiod."""

    model = FiscalPeriod

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[FiscalPeriod]
    # - get_or_fail(id) -> Result[FiscalPeriod]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[FiscalPeriod]
    # - update(id, data) -> Result[FiscalPeriod]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class JournalEntryService(BaseService[JournalEntry, Any, Any]):
    """Service CRUD pour journalentry."""

    model = JournalEntry

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[JournalEntry]
    # - get_or_fail(id) -> Result[JournalEntry]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[JournalEntry]
    # - update(id, data) -> Result[JournalEntry]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class JournalEntryLineService(BaseService[JournalEntryLine, Any, Any]):
    """Service CRUD pour journalentryline."""

    model = JournalEntryLine

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[JournalEntryLine]
    # - get_or_fail(id) -> Result[JournalEntryLine]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[JournalEntryLine]
    # - update(id, data) -> Result[JournalEntryLine]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class BankAccountService(BaseService[BankAccount, Any, Any]):
    """Service CRUD pour bankaccount."""

    model = BankAccount

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[BankAccount]
    # - get_or_fail(id) -> Result[BankAccount]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[BankAccount]
    # - update(id, data) -> Result[BankAccount]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class BankStatementService(BaseService[BankStatement, Any, Any]):
    """Service CRUD pour bankstatement."""

    model = BankStatement

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[BankStatement]
    # - get_or_fail(id) -> Result[BankStatement]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[BankStatement]
    # - update(id, data) -> Result[BankStatement]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class BankStatementLineService(BaseService[BankStatementLine, Any, Any]):
    """Service CRUD pour bankstatementline."""

    model = BankStatementLine

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[BankStatementLine]
    # - get_or_fail(id) -> Result[BankStatementLine]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[BankStatementLine]
    # - update(id, data) -> Result[BankStatementLine]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class BankTransactionService(BaseService[BankTransaction, Any, Any]):
    """Service CRUD pour banktransaction."""

    model = BankTransaction

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[BankTransaction]
    # - get_or_fail(id) -> Result[BankTransaction]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[BankTransaction]
    # - update(id, data) -> Result[BankTransaction]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class CashForecastService(BaseService[CashForecast, Any, Any]):
    """Service CRUD pour cashforecast."""

    model = CashForecast

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[CashForecast]
    # - get_or_fail(id) -> Result[CashForecast]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[CashForecast]
    # - update(id, data) -> Result[CashForecast]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class CashFlowCategoryService(BaseService[CashFlowCategory, Any, Any]):
    """Service CRUD pour cashflowcategory."""

    model = CashFlowCategory

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[CashFlowCategory]
    # - get_or_fail(id) -> Result[CashFlowCategory]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[CashFlowCategory]
    # - update(id, data) -> Result[CashFlowCategory]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class FinancialReportService(BaseService[FinancialReport, Any, Any]):
    """Service CRUD pour financialreport."""

    model = FinancialReport

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[FinancialReport]
    # - get_or_fail(id) -> Result[FinancialReport]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[FinancialReport]
    # - update(id, data) -> Result[FinancialReport]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques

