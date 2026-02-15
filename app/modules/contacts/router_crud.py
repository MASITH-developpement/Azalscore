"""
AZALS - Contacts Router (CRUDRouter v3)
======================================

Router minimaliste utilisant CRUDRouter.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from app.modules.contacts.schemas import (
    ContactPersonBase,
    ContactPersonCreate,
    ContactPersonUpdate,
    ContactPersonResponse,
    ContactAddressBase,
    ContactAddressCreate,
    ContactAddressUpdate,
    ContactAddressResponse,
    ContactBase,
    ContactCreate,
    ContactUpdate,
    ContactResponse,
)
from app.modules.contacts.service import ContactsService

# =============================================================================
# ROUTER PRINCIPAL
# =============================================================================

router = APIRouter(prefix="/contacts", tags=["Contacts"])


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/status")
async def get_module_status():
    """Statut du module Contacts."""
    return {
        "module": "contacts",
        "version": "v3",
        "status": "active"
    }


@router.get("/contactpersons", response_model=List[ContactPersonResponse])
async def list_contactpersons(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les contactpersons."""
    # TODO: Implementer avec service
    return []

@router.get("/contactaddress", response_model=List[ContactAddressResponse])
async def list_contactaddress(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les contactaddress."""
    # TODO: Implementer avec service
    return []

@router.get("/contacts", response_model=List[ContactResponse])
async def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les contacts."""
    # TODO: Implementer avec service
    return []

