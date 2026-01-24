# PLAN D'IMPLÉMENTATION - MODULE TREASURY
## Trésorerie : Comptes Bancaires, Transactions, Rapprochement, Prévisions
## Durée : 3 Semaines (15-20 jours)

---

## 🎯 OBJECTIF

Implémenter le backend complet du module Treasury pour aligner avec le frontend existant.

**Frontend existant :** `/frontend/src/modules/treasury/index.tsx` + 5 composants tabs
**Backend actuel :** `/app/api/treasury.py` (seulement 2 endpoints forecast)
**Backend à créer :** Gestion bancaire complète

**Endpoints à implémenter :** 6 endpoints
- Summary (résumé trésorerie)
- Bank accounts (comptes bancaires CRUD)
- Transactions (mouvements bancaires)
- Rapprochement bancaire

---

## 🏗️ ARCHITECTURE BACKEND

### Structure Module

```
/app/modules/treasury/
├── __init__.py           # Exports publics
├── models.py             # Modèles SQLAlchemy (BankAccount, Transaction, Reconciliation)
├── schemas.py            # Schémas Pydantic
├── router.py             # Endpoints FastAPI (6 endpoints)
├── service.py            # Logique métier
└── utils.py              # Utilitaires (parsing relevés, calculs)
```

---

## 📊 MODÈLES DE DONNÉES

### 1. BankAccount (Compte Bancaire)

```python
# app/modules/treasury/models.py

from sqlalchemy import Column, String, Text, Enum as SQLEnum, Numeric, Boolean, Date
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantMixin, TimestampMixin
from decimal import Decimal
import enum

class AccountType(str, enum.Enum):
    """Types de comptes bancaires."""
    CHECKING = "CHECKING"        # Compte courant
    SAVINGS = "SAVINGS"          # Compte épargne
    CREDIT_CARD = "CREDIT_CARD"  # Carte de crédit
    LOAN = "LOAN"                # Prêt
    CASH = "CASH"                # Caisse


class AccountStatus(str, enum.Enum):
    """Statuts compte bancaire."""
    ACTIVE = "ACTIVE"      # Actif
    INACTIVE = "INACTIVE"  # Inactif (fermé)
    BLOCKED = "BLOCKED"    # Bloqué temporairement


class BankAccount(Base, TenantMixin, TimestampMixin):
    """Compte bancaire."""
    __tablename__ = "treasury_bank_accounts"

    # Identification
    name = Column(String(255), nullable=False)  # Ex: "BNP Compte Courant"
    account_number = Column(String(100))        # Numéro compte
    iban = Column(String(34))                   # IBAN (optionnel)
    bic = Column(String(11))                    # BIC/SWIFT (optionnel)

    # Classification
    account_type = Column(SQLEnum(AccountType), nullable=False, default=AccountType.CHECKING)
    bank_name = Column(String(255))             # Nom banque
    currency = Column(String(3), default="EUR")

    # État
    status = Column(SQLEnum(AccountStatus), default=AccountStatus.ACTIVE, nullable=False)

    # Soldes
    initial_balance = Column(Numeric(15, 2), default=Decimal("0.00"))  # Solde initial
    current_balance = Column(Numeric(15, 2), default=Decimal("0.00"))  # Solde actuel (calculé)
    last_reconciled_balance = Column(Numeric(15, 2), default=Decimal("0.00"))
    last_reconciled_date = Column(Date)

    # Statistiques (cache)
    transactions_count = Column(Integer, default=0)
    unreconciled_count = Column(Integer, default=0)

    # Notes
    notes = Column(Text)

    # Relations
    transactions = relationship("BankTransaction", back_populates="account", lazy="dynamic")
```

### 2. BankTransaction (Transaction Bancaire)

```python
class TransactionType(str, enum.Enum):
    """Types de transactions."""
    DEBIT = "DEBIT"    # Débit (sortie d'argent)
    CREDIT = "CREDIT"  # Crédit (entrée d'argent)


class TransactionStatus(str, enum.Enum):
    """Statuts transaction."""
    PENDING = "PENDING"          # En attente
    CLEARED = "CLEARED"          # Compensée
    RECONCILED = "RECONCILED"    # Rapprochée (liée à document)
    CANCELLED = "CANCELLED"      # Annulée


class BankTransaction(Base, TenantMixin, TimestampMixin):
    """Transaction bancaire."""
    __tablename__ = "treasury_transactions"

    # Compte
    account_id = Column(String(36), ForeignKey("treasury_bank_accounts.id"), nullable=False, index=True)

    # Dates
    transaction_date = Column(Date, nullable=False, index=True)  # Date opération
    value_date = Column(Date)                                    # Date valeur

    # Transaction
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EUR")

    # Description
    label = Column(Text, nullable=False)  # Libellé opération
    reference = Column(String(100))       # Référence banque

    # Catégorie (optionnel)
    category = Column(String(100))  # Ex: "Fournisseurs", "Salaires", "Ventes"

    # Statut
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, index=True)

    # Rapprochement (optionnel)
    reconciled_at = Column(DateTime)
    reconciled_document_type = Column(String(50))  # "invoice", "purchase_invoice", etc.
    reconciled_document_id = Column(String(36))

    # Notes
    notes = Column(Text)

    # Relations
    account = relationship("BankAccount", back_populates="transactions")
```

### 3. TreasurySummary (Résumé - Vue calculée)

**Note :** Pas de table, calcul à la volée depuis BankAccount + Transactions

```python
# Schéma Pydantic uniquement
class TreasurySummary(BaseModel):
    """Résumé trésorerie."""
    total_balance: Decimal  # Somme soldes tous comptes actifs
    total_pending: Decimal  # Somme transactions en attente
    total_unreconciled: int # Nombre transactions non rapprochées

    # Par type de compte
    checking_balance: Decimal
    savings_balance: Decimal
    credit_card_balance: Decimal

    # Tendance
    inflow_30d: Decimal   # Entrées 30 derniers jours
    outflow_30d: Decimal  # Sorties 30 derniers jours

    currency: str = "EUR"
```

---

## 🔌 ENDPOINTS API

### Base URL
`/v1/treasury`

### 1. Summary (Résumé Trésorerie)

```python
# app/modules/treasury/router.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.dependencies import get_tenant_id
from app.core.models import User

from .schemas import (
    TreasurySummary,
    BankAccountCreate, BankAccountUpdate, BankAccountResponse, BankAccountList,
    TransactionCreate, TransactionUpdate, TransactionResponse, TransactionList,
    ReconcileRequest
)
from .service import get_treasury_service

router = APIRouter(prefix="/treasury", tags=["Trésorerie - Treasury"])


@router.get("/summary", response_model=TreasurySummary)
async def get_treasury_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Résumé trésorerie : Soldes comptes, transactions en attente, flux 30j.

    Calculs :
    - total_balance = Somme current_balance (comptes actifs)
    - total_pending = Somme transactions PENDING
    - inflow_30d = Somme transactions CREDIT des 30 derniers jours
    - outflow_30d = Somme transactions DEBIT des 30 derniers jours
    """
    service = get_treasury_service(db, tenant_id)
    return service.get_summary()
```

### 2. Bank Accounts (Comptes Bancaires)

```python
@router.post("/accounts", response_model=BankAccountResponse, status_code=201)
async def create_bank_account(
    data: BankAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Créer un compte bancaire."""
    service = get_treasury_service(db, tenant_id)
    return service.create_account(data, current_user.id)


@router.get("/accounts", response_model=BankAccountList)
async def list_bank_accounts(
    status: Optional[str] = None,
    account_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Lister les comptes bancaires."""
    service = get_treasury_service(db, tenant_id)
    items = service.list_accounts(status, account_type)
    return BankAccountList(items=items, total=len(items))


@router.get("/accounts/{account_id}", response_model=BankAccountResponse)
async def get_bank_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Récupérer un compte bancaire."""
    service = get_treasury_service(db, tenant_id)
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte bancaire non trouvé")
    return account


@router.put("/accounts/{account_id}", response_model=BankAccountResponse)
async def update_bank_account(
    account_id: UUID,
    data: BankAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Mettre à jour un compte bancaire."""
    service = get_treasury_service(db, tenant_id)
    account = service.update_account(account_id, data)
    if not account:
        raise HTTPException(status_code=404, detail="Compte bancaire non trouvé")
    return account


@router.delete("/accounts/{account_id}", status_code=204)
async def delete_bank_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Supprimer un compte bancaire (soft delete → status INACTIVE)."""
    service = get_treasury_service(db, tenant_id)
    if not service.delete_account(account_id):
        raise HTTPException(status_code=404, detail="Compte bancaire non trouvé")
```

### 3. Transactions (Mouvements Bancaires)

```python
@router.get("/transactions", response_model=TransactionList)
async def list_all_transactions(
    account_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Lister toutes les transactions (tous comptes ou filtrées).

    Filtres :
    - account_id : Filtrer par compte
    - date_from/date_to : Période
    - transaction_type : DEBIT ou CREDIT
    - status : PENDING, CLEARED, RECONCILED
    """
    service = get_treasury_service(db, tenant_id)
    items, total = service.list_transactions(
        account_id, date_from, date_to, transaction_type, status, page, page_size
    )
    return TransactionList(items=items, total=total, page=page, page_size=page_size)


@router.get("/accounts/{account_id}/transactions", response_model=TransactionList)
async def list_account_transactions(
    account_id: UUID,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Lister les transactions d'un compte spécifique."""
    service = get_treasury_service(db, tenant_id)
    items, total = service.list_transactions(
        account_id, date_from, date_to, None, None, page, page_size
    )
    return TransactionList(items=items, total=total, page=page, page_size=page_size)


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Créer une transaction bancaire manuelle."""
    service = get_treasury_service(db, tenant_id)
    return service.create_transaction(data, current_user.id)


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Mettre à jour une transaction."""
    service = get_treasury_service(db, tenant_id)
    transaction = service.update_transaction(transaction_id, data)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    return transaction


@router.delete("/transactions/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Supprimer une transaction."""
    service = get_treasury_service(db, tenant_id)
    if not service.delete_transaction(transaction_id):
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
```

### 4. Rapprochement Bancaire

```python
@router.post("/transactions/{transaction_id}/reconcile", response_model=TransactionResponse)
async def reconcile_transaction(
    transaction_id: UUID,
    data: ReconcileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Rapprocher une transaction avec un document (facture, etc.).

    Body :
    - document_type : "invoice", "purchase_invoice", etc.
    - document_id : UUID du document
    """
    service = get_treasury_service(db, tenant_id)
    transaction = service.reconcile_transaction(
        transaction_id,
        data.document_type,
        data.document_id,
        current_user.id
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    return transaction


@router.post("/transactions/{transaction_id}/unreconcile", response_model=TransactionResponse)
async def unreconcile_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Annuler le rapprochement d'une transaction."""
    service = get_treasury_service(db, tenant_id)
    transaction = service.unreconcile_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    return transaction
```

---

## 📅 PLAN SEMAINE PAR SEMAINE

### SEMAINE 1 - Comptes Bancaires + Transactions CRUD

**Jour 1-2 : Modèles & Migration**
- [ ] Créer modèles BankAccount, BankTransaction
- [ ] Créer migration Alembic (2 tables)
- [ ] Appliquer migration dev

**Jour 3-4 : Endpoints Comptes Bancaires**
- [ ] Créer schémas Pydantic (AccountCreate, Update, Response)
- [ ] Implémenter service.py (CRUD comptes)
- [ ] Implémenter router.py (5 endpoints comptes)
- [ ] Tests unitaires comptes

**Jour 5 : Endpoints Transactions**
- [ ] Créer schémas Pydantic (TransactionCreate, etc.)
- [ ] Implémenter service.py (CRUD transactions)
- [ ] Endpoints POST/PUT/DELETE transactions
- [ ] Tests unitaires transactions

**Livrable S1 :**
✅ Comptes bancaires + Transactions CRUD fonctionnels

---

### SEMAINE 2 - Liste Transactions + Rapprochement

**Jour 6-7 : Liste Transactions**
- [ ] Endpoint GET /transactions (toutes transactions)
- [ ] Endpoint GET /accounts/{id}/transactions (par compte)
- [ ] Filtres (date, type, status)
- [ ] Calcul solde progressif
- [ ] Tests unitaires listes

**Jour 8-9 : Rapprochement Bancaire**
- [ ] Endpoint POST /transactions/{id}/reconcile
- [ ] Endpoint POST /transactions/{id}/unreconcile
- [ ] Logique rapprochement (lier transaction → document)
- [ ] Mise à jour compteurs (unreconciled_count)
- [ ] Tests unitaires rapprochement

**Jour 10 : Validation Frontend**
- [ ] Tester frontend page Comptes bancaires
- [ ] Tester frontend Liste transactions
- [ ] Tester frontend Rapprochement bancaire
- [ ] Vérifier calculs soldes corrects

**Livrable S2 :**
✅ Transactions + Rapprochement opérationnels

---

### SEMAINE 3 - Summary + Intégration + Déploiement

**Jour 11-12 : Summary Trésorerie**
- [ ] Implémenter service.py (get_summary)
- [ ] Calcul total_balance (somme comptes actifs)
- [ ] Calcul flux 30 jours (inflow/outflow)
- [ ] Endpoint GET /summary
- [ ] Tests unitaires summary

**Jour 13 : Intégration Automatique**
- [ ] Créer transactions auto depuis paiements factures
- [ ] Synchronisation soldes comptes
- [ ] Tests intégration

**Jour 14 : Tests & Documentation**
- [ ] Tests E2E complets
- [ ] Documentation API (Swagger)
- [ ] Guide utilisateur trésorerie
- [ ] Validation Product Owner

**Jour 15 : Déploiement Production**
- [ ] Deploy staging + tests smoke
- [ ] Deploy production
- [ ] Monitoring 48h
- [ ] Communication équipe

**Livrable S3 :**
✅ Module Treasury 100% déployé en production

---

## 📂 STRUCTURE FICHIERS

```
/app/modules/treasury/
│
├── __init__.py           # Exports
├── models.py             # BankAccount, BankTransaction
├── schemas.py            # Pydantic schemas
├── router.py             # 6 endpoints
├── service.py            # Logique métier + calculs
└── utils.py              # Parsing relevés (optionnel Phase 2)

/alembic/versions/
└── xxxx_create_treasury_tables.py
```

---

## ✅ CHECKLIST VALIDATION

### Semaine 1 - Comptes + Transactions CRUD
- [ ] 2 tables créées (bank_accounts, transactions)
- [ ] 5 endpoints comptes bancaires fonctionnels
- [ ] CRUD transactions fonctionnel
- [ ] Frontend : Créer/Modifier compte OK
- [ ] Frontend : Saisir transaction manuelle OK

### Semaine 2 - Listes + Rapprochement
- [ ] Endpoint GET /transactions fonctionnel
- [ ] Endpoint GET /accounts/{id}/transactions fonctionnel
- [ ] Filtres date/type/status OK
- [ ] Rapprochement transaction → document OK
- [ ] Frontend : Liste transactions + rapprochement OK

### Semaine 3 - Summary + Intégration
- [ ] Endpoint GET /summary fonctionnel
- [ ] Calculs soldes/flux corrects
- [ ] Transactions auto depuis paiements OK
- [ ] Tests E2E PASS
- [ ] Documentation complète
- [ ] Production déployée

---

## 🎯 MÉTRIQUES SUCCÈS

| Métrique | Cible | Validation |
|----------|-------|------------|
| Endpoints fonctionnels | 6/6 | 100% |
| Calculs soldes | Corrects | Tests unitaires |
| Rapprochement | Fonctionnel | Tests manuels |
| Frontend fonctionnel | 100% | Tests manuels |
| Performance | <250ms | Load test |
| Coverage tests | ≥75% | pytest --cov |

---

## 📊 LIVRABLE FINAL

À la fin de la Semaine 3, vous aurez :

✅ **Module Treasury 100% opérationnel**
- Gestion comptes bancaires (CRUD)
- Transactions bancaires complètes
- Rapprochement bancaire manuel
- Dashboard trésorerie (soldes, flux)

✅ **Intégration automatique**
- Transactions créées depuis paiements
- Synchronisation soldes temps réel
- Alertes trésorerie négative (réutiliser forecast RED existant)

✅ **Pilotage financier**
- Vision cash flow immédiate
- Prévisions trésorerie 30-60-90 jours
- Rapprochement facile (drag & drop frontend)

---

**Créé le :** 2026-01-23
**Par :** QA Lead - Audit Fonctionnel
**Durée estimée :** 3 semaines (15 jours dev)
**Next :** Implémenter après Accounting (Semaine 8-10)

---

**🚀 Module Treasury - Prêt pour implémentation !**
