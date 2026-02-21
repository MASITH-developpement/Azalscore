"""
Module Requisition / Demandes d'achat - GAP-085
================================================

Gestion des demandes d'achat:
- Catalogue interne (catégories et articles)
- Fournisseurs préférés
- Allocations budgétaires
- Demandes d'achat avec workflow
- Approbation multi-niveaux
- Templates réutilisables
"""

# Models
from .models import (
    RequisitionType,
    RequisitionStatus,
    LineStatus,
    Priority,
    CatalogItemStatus,
    ApprovalStatus,
    CatalogCategory,
    CatalogItem,
    PreferredVendor,
    BudgetAllocation,
    Requisition,
    RequisitionLine,
    ApprovalStep,
    RequisitionComment,
    RequisitionTemplate,
)

# Schemas
from .schemas import (
    # Category
    CatalogCategoryCreate,
    CatalogCategoryUpdate,
    CatalogCategoryResponse,
    CatalogCategoryListResponse,
    # Item
    CatalogItemCreate,
    CatalogItemUpdate,
    CatalogItemResponse,
    CatalogItemListResponse,
    # Vendor
    PreferredVendorCreate,
    PreferredVendorUpdate,
    PreferredVendorResponse,
    PreferredVendorListResponse,
    # Budget
    BudgetAllocationCreate,
    BudgetAllocationUpdate,
    BudgetAllocationResponse,
    BudgetAllocationListResponse,
    BudgetCheckResult,
    # Requisition
    RequisitionCreate,
    RequisitionUpdate,
    RequisitionResponse,
    RequisitionDetailResponse,
    RequisitionListResponse,
    RequisitionFilters,
    # Line
    RequisitionLineCreate,
    RequisitionLineUpdate,
    RequisitionLineResponse,
    # Approval
    ApprovalStepCreate,
    ApprovalStepResponse,
    ApprovalDecision,
    # Comment
    CommentCreate,
    CommentResponse,
    # Template
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    # Stats
    RequisitionStats,
    # Common
    AutocompleteResponse,
    BulkResult,
)

# Exceptions
from .exceptions import (
    RequisitionError,
    CatalogCategoryNotFoundError,
    CatalogCategoryDuplicateError,
    CatalogCategoryValidationError,
    CatalogItemNotFoundError,
    CatalogItemDuplicateError,
    CatalogItemValidationError,
    CatalogItemInactiveError,
    PreferredVendorNotFoundError,
    PreferredVendorDuplicateError,
    PreferredVendorValidationError,
    BudgetAllocationNotFoundError,
    BudgetAllocationDuplicateError,
    BudgetAllocationValidationError,
    BudgetExceededError,
    InsufficientBudgetError,
    RequisitionNotFoundError,
    RequisitionDuplicateError,
    RequisitionValidationError,
    RequisitionStateError,
    RequisitionClosedError,
    RequisitionEmptyError,
    RequisitionLineNotFoundError,
    RequisitionLineValidationError,
    ApprovalStepNotFoundError,
    ApprovalNotAuthorizedError,
    ApprovalAlreadyProcessedError,
    ApprovalPendingError,
    NoApproverError,
    TemplateNotFoundError,
    TemplateDuplicateError,
    TemplateValidationError,
    OrderGenerationError,
    OrderAlreadyGeneratedError,
)

# Repository
from .repository import (
    CatalogCategoryRepository,
    CatalogItemRepository,
    PreferredVendorRepository,
    BudgetAllocationRepository,
    RequisitionRepository,
    RequisitionLineRepository,
    ApprovalStepRepository,
    CommentRepository,
    TemplateRepository,
)

# Service
from .service import RequisitionService

# Router
from .router import router


__all__ = [
    # Enums
    "RequisitionType",
    "RequisitionStatus",
    "LineStatus",
    "Priority",
    "CatalogItemStatus",
    "ApprovalStatus",
    # Models
    "CatalogCategory",
    "CatalogItem",
    "PreferredVendor",
    "BudgetAllocation",
    "Requisition",
    "RequisitionLine",
    "ApprovalStep",
    "RequisitionComment",
    "RequisitionTemplate",
    # Category Schemas
    "CatalogCategoryCreate",
    "CatalogCategoryUpdate",
    "CatalogCategoryResponse",
    "CatalogCategoryListResponse",
    # Item Schemas
    "CatalogItemCreate",
    "CatalogItemUpdate",
    "CatalogItemResponse",
    "CatalogItemListResponse",
    # Vendor Schemas
    "PreferredVendorCreate",
    "PreferredVendorUpdate",
    "PreferredVendorResponse",
    "PreferredVendorListResponse",
    # Budget Schemas
    "BudgetAllocationCreate",
    "BudgetAllocationUpdate",
    "BudgetAllocationResponse",
    "BudgetAllocationListResponse",
    "BudgetCheckResult",
    # Requisition Schemas
    "RequisitionCreate",
    "RequisitionUpdate",
    "RequisitionResponse",
    "RequisitionDetailResponse",
    "RequisitionListResponse",
    "RequisitionFilters",
    # Line Schemas
    "RequisitionLineCreate",
    "RequisitionLineUpdate",
    "RequisitionLineResponse",
    # Approval Schemas
    "ApprovalStepCreate",
    "ApprovalStepResponse",
    "ApprovalDecision",
    # Comment Schemas
    "CommentCreate",
    "CommentResponse",
    # Template Schemas
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateResponse",
    "TemplateListResponse",
    # Stats Schemas
    "RequisitionStats",
    # Common Schemas
    "AutocompleteResponse",
    "BulkResult",
    # Exceptions
    "RequisitionError",
    "CatalogCategoryNotFoundError",
    "CatalogCategoryDuplicateError",
    "CatalogCategoryValidationError",
    "CatalogItemNotFoundError",
    "CatalogItemDuplicateError",
    "CatalogItemValidationError",
    "CatalogItemInactiveError",
    "PreferredVendorNotFoundError",
    "PreferredVendorDuplicateError",
    "PreferredVendorValidationError",
    "BudgetAllocationNotFoundError",
    "BudgetAllocationDuplicateError",
    "BudgetAllocationValidationError",
    "BudgetExceededError",
    "InsufficientBudgetError",
    "RequisitionNotFoundError",
    "RequisitionDuplicateError",
    "RequisitionValidationError",
    "RequisitionStateError",
    "RequisitionClosedError",
    "RequisitionEmptyError",
    "RequisitionLineNotFoundError",
    "RequisitionLineValidationError",
    "ApprovalStepNotFoundError",
    "ApprovalNotAuthorizedError",
    "ApprovalAlreadyProcessedError",
    "ApprovalPendingError",
    "NoApproverError",
    "TemplateNotFoundError",
    "TemplateDuplicateError",
    "TemplateValidationError",
    "OrderGenerationError",
    "OrderAlreadyGeneratedError",
    # Repository
    "CatalogCategoryRepository",
    "CatalogItemRepository",
    "PreferredVendorRepository",
    "BudgetAllocationRepository",
    "RequisitionRepository",
    "RequisitionLineRepository",
    "ApprovalStepRepository",
    "CommentRepository",
    "TemplateRepository",
    # Service
    "RequisitionService",
    # Router
    "router",
]
