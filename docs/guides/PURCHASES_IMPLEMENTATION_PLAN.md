# PLAN D'IMPLÉMENTATION - MODULE PURCHASES
## Achats : Fournisseurs, Commandes, Factures Fournisseurs
## Durée : 4 Semaines (20-25 jours)

---

## 🎯 OBJECTIF

Implémenter le backend complet du module Purchases pour aligner avec le frontend existant.

**Frontend existant :** `/frontend/src/modules/purchases/index.tsx` + 18 composants tabs
**Backend à créer :** `/app/modules/purchases/` (INEXISTANT actuellement)

**Endpoints à implémenter :** 19 endpoints
- Fournisseurs : 6 endpoints
- Commandes achat : 7 endpoints
- Factures fournisseurs : 6 endpoints

---

## 📋 TABLE DES MATIÈRES

1. [Architecture Backend](#architecture-backend)
2. [Modèles de Données](#modèles-de-données)
3. [Endpoints API](#endpoints-api)
4. [Plan Semaine par Semaine](#plan-semaine-par-semaine)
5. [Structure Fichiers](#structure-fichiers)
6. [Checklist Validation](#checklist-validation)

---

## 🏗️ ARCHITECTURE BACKEND

### Structure Module

```
/app/modules/purchases/
├── __init__.py           # Exports publics
├── models.py             # Modèles SQLAlchemy (Supplier, PurchaseOrder, PurchaseInvoice)
├── schemas.py            # Schémas Pydantic (Create, Update, Response)
├── router.py             # Endpoints FastAPI
├── service.py            # Logique métier
└── enums.py              # Enums (SupplierStatus, OrderStatus, InvoiceStatus)
```

### Dépendances Externes

**Modules AZALSCORE utilisés :**
- `app.core.database` → Session DB
- `app.core.auth` → get_current_user
- `app.core.dependencies` → get_tenant_id
- `app.core.models` → User, base classes

**Modules liés :**
- `app.modules.commercial` → Intégration clients/fournisseurs (optional)
- `app.modules.accounting` → Génération écritures comptables (Phase 2)

---

## 📊 MODÈLES DE DONNÉES

### 1. Supplier (Fournisseur)

```python
# app/modules/purchases/models.py

from sqlalchemy import Column, String, Text, Enum as SQLEnum, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantMixin, TimestampMixin, AuditMixin
import enum
from decimal import Decimal

class SupplierStatus(str, enum.Enum):
    """Statuts fournisseur."""
    PROSPECT = "PROSPECT"      # Prospect (pas encore fournisseur)
    PENDING = "PENDING"        # En attente validation
    APPROVED = "APPROVED"      # Approuvé et actif
    BLOCKED = "BLOCKED"        # Bloqué (litiges, paiements)
    INACTIVE = "INACTIVE"      # Inactif (archivé)


class Supplier(Base, TenantMixin, TimestampMixin, AuditMixin):
    """Fournisseur."""
    __tablename__ = "purchases_suppliers"

    # Identification
    code = Column(String(50), nullable=False, index=True)  # Code fournisseur unique
    name = Column(String(255), nullable=False, index=True)  # Raison sociale

    # Contact
    contact_name = Column(String(255))  # Nom contact principal
    email = Column(String(255))
    phone = Column(String(50))

    # Adresse
    address = Column(Text)
    city = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="France")

    # Informations légales
    tax_id = Column(String(50))  # SIRET/VAT

    # Conditions commerciales
    payment_terms = Column(String(100))  # Ex: "30 jours fin de mois"
    currency = Column(String(3), default="EUR")

    # Statut
    status = Column(SQLEnum(SupplierStatus), default=SupplierStatus.PENDING, nullable=False)

    # Notes
    notes = Column(Text)

    # Relations
    orders = relationship("PurchaseOrder", back_populates="supplier", lazy="dynamic")
    invoices = relationship("PurchaseInvoice", back_populates="supplier", lazy="dynamic")

    # Contraintes
    __table_args__ = (
        # Code unique par tenant
        {"schema": None},  # Utiliser schéma par défaut
    )
```

### 2. PurchaseOrder (Commande Achat)

```python
class OrderStatus(str, enum.Enum):
    """Statuts commande achat."""
    DRAFT = "DRAFT"          # Brouillon (éditable)
    SENT = "SENT"            # Envoyée au fournisseur
    CONFIRMED = "CONFIRMED"  # Confirmée par fournisseur
    PARTIAL = "PARTIAL"      # Partiellement reçue
    RECEIVED = "RECEIVED"    # Entièrement reçue
    INVOICED = "INVOICED"    # Facturée (liée à facture)
    CANCELLED = "CANCELLED"  # Annulée


class PurchaseOrder(Base, TenantMixin, TimestampMixin, AuditMixin):
    """Commande d'achat fournisseur."""
    __tablename__ = "purchases_orders"

    # Identification
    number = Column(String(50), nullable=False, unique=True, index=True)  # CA-2024-001
    supplier_id = Column(String(36), ForeignKey("purchases_suppliers.id"), nullable=False, index=True)

    # Dates
    date = Column(DateTime, nullable=False)  # Date commande
    expected_date = Column(DateTime)  # Date livraison prévue

    # Statut
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.DRAFT, nullable=False, index=True)

    # Référence externe
    reference = Column(String(100))  # Référence fournisseur (si fournie)

    # Notes
    notes = Column(Text)

    # Totaux (calculés depuis lignes)
    total_ht = Column(Numeric(15, 2), default=Decimal("0.00"))
    total_tax = Column(Numeric(15, 2), default=Decimal("0.00"))
    total_ttc = Column(Numeric(15, 2), default=Decimal("0.00"))
    currency = Column(String(3), default="EUR")

    # Validation
    validated_at = Column(DateTime)
    validated_by = Column(String(36), ForeignKey("core_users.id"))

    # Relations
    supplier = relationship("Supplier", back_populates="orders")
    lines = relationship("PurchaseOrderLine", back_populates="order", cascade="all, delete-orphan")
    invoices = relationship("PurchaseInvoice", back_populates="order")
    validator = relationship("User", foreign_keys=[validated_by])


class PurchaseOrderLine(Base, TenantMixin, TimestampMixin):
    """Ligne de commande achat."""
    __tablename__ = "purchases_order_lines"

    order_id = Column(String(36), ForeignKey("purchases_orders.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)  # Numéro de ligne (1, 2, 3...)

    # Produit/Service
    description = Column(Text, nullable=False)  # Description article
    quantity = Column(Numeric(15, 3), nullable=False, default=Decimal("1.000"))
    unit = Column(String(20), default="unité")  # unité, kg, m, etc.

    # Prix
    unit_price = Column(Numeric(15, 2), nullable=False)  # Prix unitaire HT
    discount_percent = Column(Numeric(5, 2), default=Decimal("0.00"))  # Remise %
    tax_rate = Column(Numeric(5, 2), default=Decimal("20.00"))  # TVA %

    # Totaux calculés
    discount_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"))  # HT après remise
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    total = Column(Numeric(15, 2), default=Decimal("0.00"))  # TTC

    # Notes
    notes = Column(Text)

    # Relation
    order = relationship("PurchaseOrder", back_populates="lines")
```

### 3. PurchaseInvoice (Facture Fournisseur)

```python
class InvoiceStatus(str, enum.Enum):
    """Statuts facture fournisseur."""
    DRAFT = "DRAFT"        # Brouillon (saisie en cours)
    VALIDATED = "VALIDATED"  # Validée (comptabilisée)
    PAID = "PAID"          # Payée
    CANCELLED = "CANCELLED"  # Annulée


class PurchaseInvoice(Base, TenantMixin, TimestampMixin, AuditMixin):
    """Facture fournisseur."""
    __tablename__ = "purchases_invoices"

    # Identification
    number = Column(String(50), nullable=False, index=True)  # Numéro facture fournisseur
    supplier_id = Column(String(36), ForeignKey("purchases_suppliers.id"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("purchases_orders.id"), index=True)  # Optionnel

    # Dates
    invoice_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime)

    # Statut
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False, index=True)

    # Référence
    reference = Column(String(100))  # Référence interne

    # Notes
    notes = Column(Text)

    # Totaux (calculés depuis lignes)
    total_ht = Column(Numeric(15, 2), default=Decimal("0.00"))
    total_tax = Column(Numeric(15, 2), default=Decimal("0.00"))
    total_ttc = Column(Numeric(15, 2), default=Decimal("0.00"))
    currency = Column(String(3), default="EUR")

    # Validation
    validated_at = Column(DateTime)
    validated_by = Column(String(36), ForeignKey("core_users.id"))

    # Paiement
    paid_at = Column(DateTime)
    payment_method = Column(String(50))  # Virement, chèque, etc.

    # Relations
    supplier = relationship("Supplier", back_populates="invoices")
    order = relationship("PurchaseOrder", back_populates="invoices")
    lines = relationship("PurchaseInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    validator = relationship("User", foreign_keys=[validated_by])


class PurchaseInvoiceLine(Base, TenantMixin, TimestampMixin):
    """Ligne de facture fournisseur."""
    __tablename__ = "purchases_invoice_lines"

    invoice_id = Column(String(36), ForeignKey("purchases_invoices.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)

    # Produit/Service
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False, default=Decimal("1.000"))
    unit = Column(String(20), default="unité")

    # Prix
    unit_price = Column(Numeric(15, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=Decimal("0.00"))
    tax_rate = Column(Numeric(5, 2), default=Decimal("20.00"))

    # Totaux calculés
    discount_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"))
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    total = Column(Numeric(15, 2), default=Decimal("0.00"))

    # Notes
    notes = Column(Text)

    # Relation
    invoice = relationship("PurchaseInvoice", back_populates="lines")
```

---

## 🔌 ENDPOINTS API

### Base URL
`/v1/purchases`

### 1. Fournisseurs (6 endpoints)

```python
# app/modules/purchases/router.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.dependencies import get_tenant_id
from app.core.models import User

from .models import SupplierStatus, OrderStatus, InvoiceStatus
from .schemas import (
    SupplierCreate, SupplierUpdate, SupplierResponse, SupplierList,
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse, OrderList,
    PurchaseInvoiceCreate, PurchaseInvoiceUpdate, PurchaseInvoiceResponse, InvoiceList,
    PurchaseSummary
)
from .service import get_purchases_service

router = APIRouter(prefix="/purchases", tags=["Achats - Purchases"])


# ============================================================================
# FOURNISSEURS
# ============================================================================

@router.post("/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Créer un nouveau fournisseur."""
    service = get_purchases_service(db, tenant_id)

    # Vérifier unicité du code
    existing = service.get_supplier_by_code(data.code)
    if existing:
        raise HTTPException(status_code=400, detail="Code fournisseur déjà utilisé")

    return service.create_supplier(data, current_user.id)


@router.get("/suppliers", response_model=SupplierList)
async def list_suppliers(
    status: Optional[SupplierStatus] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Lister les fournisseurs avec filtres."""
    service = get_purchases_service(db, tenant_id)
    items, total = service.list_suppliers(status, search, page, page_size)
    return SupplierList(items=items, total=total, page=page, page_size=page_size)


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Récupérer un fournisseur."""
    service = get_purchases_service(db, tenant_id)
    supplier = service.get_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return supplier


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: UUID,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Mettre à jour un fournisseur."""
    service = get_purchases_service(db, tenant_id)
    supplier = service.update_supplier(supplier_id, data)
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return supplier


@router.delete("/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Supprimer un fournisseur (soft delete)."""
    service = get_purchases_service(db, tenant_id)
    if not service.delete_supplier(supplier_id):
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")


@router.get("/summary", response_model=PurchaseSummary)
async def get_purchase_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Obtenir le résumé des achats (dashboard)."""
    service = get_purchases_service(db, tenant_id)
    return service.get_summary()
```

### 2. Commandes Achat (7 endpoints)

```python
# ============================================================================
# COMMANDES ACHAT
# ============================================================================

@router.post("/orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Créer une commande d'achat."""
    service = get_purchases_service(db, tenant_id)

    # Vérifier que le fournisseur existe
    supplier = service.get_supplier(data.supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")

    return service.create_order(data, current_user.id)


@router.get("/orders", response_model=OrderList)
async def list_orders(
    status: Optional[OrderStatus] = None,
    supplier_id: Optional[UUID] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Lister les commandes d'achat."""
    service = get_purchases_service(db, tenant_id)
    items, total = service.list_orders(status, supplier_id, search, page, page_size)
    return OrderList(items=items, total=total, page=page, page_size=page_size)


@router.get("/orders/{order_id}", response_model=PurchaseOrderResponse)
async def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Récupérer une commande d'achat."""
    service = get_purchases_service(db, tenant_id)
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return order


@router.put("/orders/{order_id}", response_model=PurchaseOrderResponse)
async def update_order(
    order_id: UUID,
    data: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Mettre à jour une commande d'achat (brouillon uniquement)."""
    service = get_purchases_service(db, tenant_id)
    order = service.update_order(order_id, data)
    if not order:
        raise HTTPException(status_code=400, detail="Commande non modifiable")
    return order


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Supprimer une commande (brouillon uniquement)."""
    service = get_purchases_service(db, tenant_id)
    if not service.delete_order(order_id):
        raise HTTPException(status_code=400, detail="Commande non supprimable")


@router.post("/orders/{order_id}/validate", response_model=PurchaseOrderResponse)
async def validate_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Valider une commande (DRAFT → SENT)."""
    service = get_purchases_service(db, tenant_id)
    order = service.validate_order(order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=400, detail="Commande non validable")
    return order


@router.post("/orders/{order_id}/invoice", response_model=PurchaseInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice_from_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Créer une facture fournisseur à partir d'une commande."""
    service = get_purchases_service(db, tenant_id)
    invoice = service.create_invoice_from_order(order_id, current_user.id)
    if not invoice:
        raise HTTPException(status_code=400, detail="Impossible de créer la facture")
    return invoice
```

### 3. Factures Fournisseurs (6 endpoints)

```python
# ============================================================================
# FACTURES FOURNISSEURS
# ============================================================================

@router.post("/invoices", response_model=PurchaseInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: PurchaseInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Créer une facture fournisseur."""
    service = get_purchases_service(db, tenant_id)

    # Vérifier que le fournisseur existe
    supplier = service.get_supplier(data.supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")

    return service.create_invoice(data, current_user.id)


@router.get("/invoices", response_model=InvoiceList)
async def list_invoices(
    status: Optional[InvoiceStatus] = None,
    supplier_id: Optional[UUID] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Lister les factures fournisseurs."""
    service = get_purchases_service(db, tenant_id)
    items, total = service.list_invoices(status, supplier_id, search, page, page_size)
    return InvoiceList(items=items, total=total, page=page, page_size=page_size)


@router.get("/invoices/{invoice_id}", response_model=PurchaseInvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Récupérer une facture fournisseur."""
    service = get_purchases_service(db, tenant_id)
    invoice = service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    return invoice


@router.put("/invoices/{invoice_id}", response_model=PurchaseInvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    data: PurchaseInvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Mettre à jour une facture fournisseur (brouillon uniquement)."""
    service = get_purchases_service(db, tenant_id)
    invoice = service.update_invoice(invoice_id, data)
    if not invoice:
        raise HTTPException(status_code=400, detail="Facture non modifiable")
    return invoice


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Supprimer une facture (brouillon uniquement)."""
    service = get_purchases_service(db, tenant_id)
    if not service.delete_invoice(invoice_id):
        raise HTTPException(status_code=400, detail="Facture non supprimable")


@router.post("/invoices/{invoice_id}/validate", response_model=PurchaseInvoiceResponse)
async def validate_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Valider une facture (DRAFT → VALIDATED, comptabilisation)."""
    service = get_purchases_service(db, tenant_id)
    invoice = service.validate_invoice(invoice_id, current_user.id)
    if not invoice:
        raise HTTPException(status_code=400, detail="Facture non validable")
    return invoice
```

---

## 📅 PLAN SEMAINE PAR SEMAINE

### SEMAINE 1 - Fournisseurs CRUD + Validation

**Jour 1-2 : Setup Infrastructure**
- [ ] Créer structure `/app/modules/purchases/`
- [ ] Créer modèles SQLAlchemy (Supplier)
- [ ] Créer migration Alembic
- [ ] Appliquer migration en dev

**Jour 3-4 : Endpoints Fournisseurs**
- [ ] Créer schémas Pydantic (SupplierCreate, Update, Response)
- [ ] Implémenter service.py (CRUD fournisseurs)
- [ ] Implémenter router.py (6 endpoints fournisseurs)
- [ ] Enregistrer router dans main.py

**Jour 5 : Tests & Validation**
- [ ] Tests unitaires service fournisseurs
- [ ] Tests API endpoints fournisseurs (pytest)
- [ ] Validation frontend (créer/modifier/supprimer fournisseur)

**Livrable S1 :**
✅ Module fournisseurs 100% opérationnel

---

### SEMAINE 2 - Commandes Achat CRUD + Workflow

**Jour 6-7 : Modèles Commandes**
- [ ] Créer modèles PurchaseOrder + PurchaseOrderLine
- [ ] Créer migration Alembic (tables + relations)
- [ ] Appliquer migration

**Jour 8-9 : Endpoints Commandes**
- [ ] Créer schémas Pydantic (OrderCreate, Update, Response)
- [ ] Implémenter service.py (CRUD + calculs lignes)
- [ ] Implémenter router.py (7 endpoints commandes)
- [ ] Logique validation (DRAFT → SENT)

**Jour 10 : Tests & Validation**
- [ ] Tests unitaires service commandes
- [ ] Tests API endpoints commandes
- [ ] Validation frontend (workflow commande complète)

**Livrable S2 :**
✅ Module commandes 100% opérationnel

---

### SEMAINE 3 - Factures Fournisseurs CRUD + Validation

**Jour 11-12 : Modèles Factures**
- [ ] Créer modèles PurchaseInvoice + PurchaseInvoiceLine
- [ ] Créer migration Alembic
- [ ] Appliquer migration

**Jour 13-14 : Endpoints Factures**
- [ ] Créer schémas Pydantic (InvoiceCreate, Update, Response)
- [ ] Implémenter service.py (CRUD factures)
- [ ] Implémenter router.py (6 endpoints factures)
- [ ] Logique validation + création depuis commande

**Jour 15 : Tests & Validation**
- [ ] Tests unitaires service factures
- [ ] Tests API endpoints factures
- [ ] Validation frontend (workflow facture complète)

**Livrable S3 :**
✅ Module factures 100% opérationnel

---

### SEMAINE 4 - Tests Intégration + Déploiement

**Jour 16-17 : Tests End-to-End**
- [ ] Scénario complet : Créer fournisseur → Commande → Facture
- [ ] Tests avec données réelles (seed data)
- [ ] Validation UI complète (tous composants frontend)
- [ ] Vérification dashboard résumé achats

**Jour 18 : Documentation**
- [ ] Documenter API (Swagger auto-généré)
- [ ] Créer guide utilisateur (workflow achats)
- [ ] Documenter schéma DB (diagramme ER)

**Jour 19 : Pre-Production**
- [ ] Deploy staging
- [ ] Tests smoke staging
- [ ] Validation Product Owner
- [ ] Corrections bugs mineurs

**Jour 20 : Production**
- [ ] Deploy production
- [ ] Monitoring renforcé 48h
- [ ] Communication équipe (module disponible)

**Livrable S4 :**
✅ Module Purchases 100% déployé en production

---

## 📂 STRUCTURE FICHIERS COMPLÈTE

```
/app/modules/purchases/
│
├── __init__.py                    # Exports publics
│   ```python
│   from .models import Supplier, PurchaseOrder, PurchaseInvoice
│   from .schemas import SupplierCreate, PurchaseOrderCreate, PurchaseInvoiceCreate
│   from .service import PurchasesService, get_purchases_service
│   from .router import router
│   ```
│
├── enums.py                       # Enums
│   ```python
│   from enum import Enum
│
│   class SupplierStatus(str, Enum):
│       PROSPECT = "PROSPECT"
│       PENDING = "PENDING"
│       APPROVED = "APPROVED"
│       BLOCKED = "BLOCKED"
│       INACTIVE = "INACTIVE"
│
│   class OrderStatus(str, Enum):
│       DRAFT = "DRAFT"
│       SENT = "SENT"
│       CONFIRMED = "CONFIRMED"
│       PARTIAL = "PARTIAL"
│       RECEIVED = "RECEIVED"
│       INVOICED = "INVOICED"
│       CANCELLED = "CANCELLED"
│
│   class InvoiceStatus(str, Enum):
│       DRAFT = "DRAFT"
│       VALIDATED = "VALIDATED"
│       PAID = "PAID"
│       CANCELLED = "CANCELLED"
│   ```
│
├── models.py                      # Modèles SQLAlchemy (voir section précédente)
│
├── schemas.py                     # Schémas Pydantic
│   - SupplierCreate, SupplierUpdate, SupplierResponse, SupplierList
│   - PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse, OrderList
│   - PurchaseInvoiceCreate, PurchaseInvoiceUpdate, PurchaseInvoiceResponse, InvoiceList
│   - PurchaseSummary
│
├── service.py                     # Logique métier
│   - PurchasesService (CRUD + logique métier)
│   - get_purchases_service() (factory)
│
└── router.py                      # Endpoints FastAPI (voir section précédente)

/app/tests/purchases/              # Tests
├── test_suppliers.py
├── test_orders.py
└── test_invoices.py

/alembic/versions/                 # Migrations
└── xxxx_create_purchases_tables.py
```

---

## ✅ CHECKLIST VALIDATION

### Par Semaine

**Semaine 1 - Fournisseurs**
- [ ] Modèle Supplier créé + migration appliquée
- [ ] 6 endpoints fournisseurs fonctionnels
- [ ] Tests unitaires PASS (coverage ≥80%)
- [ ] Frontend : Créer/Modifier/Supprimer fournisseur OK
- [ ] Frontend : Liste fournisseurs + filtres OK

**Semaine 2 - Commandes**
- [ ] Modèles PurchaseOrder + Lines créés + migration
- [ ] 7 endpoints commandes fonctionnels
- [ ] Calcul automatique totaux lignes OK
- [ ] Workflow DRAFT → SENT fonctionnel
- [ ] Tests unitaires PASS (coverage ≥80%)
- [ ] Frontend : Créer commande avec lignes OK
- [ ] Frontend : Valider commande OK

**Semaine 3 - Factures**
- [ ] Modèles PurchaseInvoice + Lines créés + migration
- [ ] 6 endpoints factures fonctionnels
- [ ] Création facture depuis commande OK
- [ ] Workflow DRAFT → VALIDATED → PAID OK
- [ ] Tests unitaires PASS (coverage ≥80%)
- [ ] Frontend : Créer facture manuelle OK
- [ ] Frontend : Créer facture depuis commande OK

**Semaine 4 - Déploiement**
- [ ] Tests E2E complets PASS
- [ ] Documentation API complète (Swagger)
- [ ] Guide utilisateur créé
- [ ] Deploy staging OK + tests smoke
- [ ] Validation Product Owner
- [ ] Deploy production OK
- [ ] Monitoring 48h sans erreurs

### Validation Globale Module

- [ ] 19/19 endpoints implémentés et testés
- [ ] Frontend 100% fonctionnel (toutes pages)
- [ ] Performance : < 200ms par requête CRUD
- [ ] Sécurité : Isolation tenant stricte
- [ ] Logs : Audit trail complet
- [ ] Documentation : Complète et à jour

---

## 🔧 COMMANDES UTILES

### Créer Migration
```bash
cd /home/ubuntu/azalscore
alembic revision --autogenerate -m "Create purchases tables"
alembic upgrade head
```

### Tests
```bash
pytest app/tests/purchases/ -v
pytest app/tests/purchases/ --cov=app/modules/purchases --cov-report=html
```

### Enregistrer Router
```python
# app/main.py

from app.modules.purchases.router import router as purchases_router

app.include_router(purchases_router, prefix="/v1")
```

### Seed Data Dev
```bash
python scripts/seed_purchases_data.py
```

---

## 📊 MÉTRIQUES SUCCÈS

| Métrique | Cible | Validation |
|----------|-------|------------|
| Endpoints fonctionnels | 19/19 | 100% |
| Coverage tests | ≥80% | pytest --cov |
| Performance API | <200ms | Locust load test |
| Frontend fonctionnel | 100% | Tests manuels |
| Bugs production | 0 | Monitoring 48h |
| Documentation | Complète | Review PO |

---

## 🎯 LIVRABLE FINAL

À la fin de la Semaine 4, vous aurez :

✅ **Module Purchases 100% opérationnel**
- 3 entités (Supplier, Order, Invoice)
- 19 endpoints REST API
- Frontend entièrement connecté
- Tests automatisés (≥80% coverage)
- Documentation complète
- Déployé en production

✅ **Capacités business**
- Gérer fournisseurs (CRUD complet)
- Créer commandes achat avec lignes
- Workflow validation commandes
- Saisir factures fournisseurs
- Créer factures depuis commandes
- Dashboard résumé achats

✅ **Prêt Phase 2 (Accounting)**
- Données purchases prêtes pour comptabilisation
- Écritures comptables générables depuis factures validées

---

**Créé le :** 2026-01-23
**Par :** QA Lead - Audit Fonctionnel
**Durée estimée :** 4 semaines (20 jours dev)
**Next :** Démarrer implémentation Semaine 1

---

**🚀 Prêt à démarrer l'implémentation !**
