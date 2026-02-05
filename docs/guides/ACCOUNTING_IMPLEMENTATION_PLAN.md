# PLAN D'IMPLÉMENTATION - MODULE ACCOUNTING
## Comptabilité : Journal, Grand Livre, Balance, États Financiers
## Durée : 3 Semaines (15-20 jours)

---

## 🎯 OBJECTIF

Implémenter le backend complet du module Accounting pour aligner avec le frontend existant.

**Frontend existant :** `/frontend/src/modules/accounting/index.tsx`
**Backend actuel :** `/app/api/accounting.py` (seulement 1 endpoint status cockpit)
**Backend à créer :** Module complet comptabilité

**Endpoints à implémenter :** 5 endpoints
- Summary (résumé comptable)
- Journal (écritures comptables)
- Grand livre (comptes)
- Balance (soldes comptes)
- États financiers (optionnel Phase 2)

---

## 📊 CONTEXTE COMPTABLE AZALSCORE

### Principe Comptabilité

**Comptabilité française :**
- Plan comptable général (PCG) : Comptes classe 1-8
- Partie double : Débit = Crédit
- Écritures comptables : Date + Pièce + Libellé + Débit/Crédit

**Intégration AZALSCORE :**
- Les factures clients/fournisseurs génèrent des écritures automatiques
- Module commercial → Écritures ventes (classe 7)
- Module purchases → Écritures achats (classe 6)
- Module treasury → Écritures banque (classe 5)

### Ce qui existe déjà

✅ **Table `core_audit_journal`** - Journal audit système (existe dans DB)
❌ **Tables comptables manquantes** - À créer (accounts, entries, etc.)

**Stratégie :** Créer module comptable autonome avec référence vers documents sources.

---

## 🏗️ ARCHITECTURE BACKEND

### Structure Module

```
/app/modules/accounting/
├── __init__.py           # Exports publics
├── models.py             # Modèles SQLAlchemy (Account, Entry, EntryLine)
├── schemas.py            # Schémas Pydantic
├── router.py             # Endpoints FastAPI (5 endpoints)
├── service.py            # Logique métier + calculs
└── utils.py              # Utilitaires comptables (validation débit/crédit)
```

---

## 📊 MODÈLES DE DONNÉES

### 1. Account (Compte Comptable)

```python
# app/modules/accounting/models.py

from sqlalchemy import Column, String, Text, Enum as SQLEnum, Numeric, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantMixin, TimestampMixin
from decimal import Decimal
import enum

class AccountType(str, enum.Enum):
    """Types de comptes selon PCG."""
    ASSET = "ASSET"              # Classe 1-2 : Actif (Capitaux, Immobilisations)
    LIABILITY = "LIABILITY"      # Classe 1 : Passif (Dettes)
    EQUITY = "EQUITY"           # Classe 1 : Capitaux propres
    REVENUE = "REVENUE"         # Classe 7 : Produits
    EXPENSE = "EXPENSE"         # Classe 6 : Charges
    BANK = "BANK"               # Classe 5 : Comptes financiers
    CUSTOMER = "CUSTOMER"       # Classe 4 : Tiers - Clients
    SUPPLIER = "SUPPLIER"       # Classe 4 : Tiers - Fournisseurs


class Account(Base, TenantMixin, TimestampMixin):
    """Compte comptable du plan comptable."""
    __tablename__ = "accounting_accounts"

    # Identification
    number = Column(String(20), nullable=False, index=True)  # Ex: 411000, 601000
    label = Column(String(255), nullable=False)  # Ex: "Clients", "Achats matières"

    # Classification
    account_type = Column(SQLEnum(AccountType), nullable=False, index=True)
    parent_number = Column(String(20), index=True)  # Compte parent (hiérarchie)

    # État
    is_active = Column(Boolean, default=True)
    allow_manual_entry = Column(Boolean, default=True)  # Autoriser saisies manuelles

    # Solde calculé (cache)
    balance_debit = Column(Numeric(15, 2), default=Decimal("0.00"))
    balance_credit = Column(Numeric(15, 2), default=Decimal("0.00"))

    # Relations
    entry_lines = relationship("AccountingEntryLine", back_populates="account", lazy="dynamic")

    __table_args__ = (
        # Number unique par tenant
        # Index (tenant_id, number)
    )
```

### 2. AccountingEntry (Écriture Comptable)

```python
class JournalType(str, enum.Enum):
    """Types de journaux comptables."""
    PURCHASE = "PURCHASE"  # Journal achats (AC)
    SALE = "SALE"          # Journal ventes (VE)
    BANK = "BANK"          # Journal banque (BQ)
    OD = "OD"              # Journal opérations diverses
    AN = "AN"              # Journal à-nouveaux


class AccountingEntry(Base, TenantMixin, TimestampMixin):
    """Écriture comptable."""
    __tablename__ = "accounting_entries"

    # Identification
    number = Column(String(50), nullable=False, unique=True, index=True)  # Auto-généré
    date = Column(Date, nullable=False, index=True)  # Date comptable
    journal_type = Column(SQLEnum(JournalType), nullable=False, index=True)

    # Référence pièce
    piece_number = Column(String(100), index=True)  # Numéro facture, etc.
    piece_date = Column(Date)

    # Libellé
    label = Column(Text, nullable=False)  # "Facture client ABC-123"

    # Référence document source (optionnel)
    source_type = Column(String(50))  # "invoice", "purchase_invoice", etc.
    source_id = Column(String(36))     # UUID document

    # Validation
    is_validated = Column(Boolean, default=False, index=True)
    validated_at = Column(DateTime)
    validated_by = Column(String(36), ForeignKey("core_users.id"))

    # Totaux (calculés depuis lignes)
    total_debit = Column(Numeric(15, 2), default=Decimal("0.00"))
    total_credit = Column(Numeric(15, 2), default=Decimal("0.00"))

    # Relations
    lines = relationship("AccountingEntryLine", back_populates="entry", cascade="all, delete-orphan")


class AccountingEntryLine(Base, TenantMixin, TimestampMixin):
    """Ligne d'écriture comptable."""
    __tablename__ = "accounting_entry_lines"

    entry_id = Column(String(36), ForeignKey("accounting_entries.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)  # Ordre dans l'écriture

    # Compte
    account_number = Column(String(20), ForeignKey("accounting_accounts.number"), nullable=False, index=True)

    # Montants (principe partie double : soit débit, soit crédit)
    debit = Column(Numeric(15, 2), default=Decimal("0.00"))
    credit = Column(Numeric(15, 2), default=Decimal("0.00"))

    # Libellé ligne (optionnel, sinon hérite de l'écriture)
    label = Column(Text)

    # Relations
    entry = relationship("AccountingEntry", back_populates="lines")
    account = relationship("Account", back_populates="entry_lines")
```

---

## 🔌 ENDPOINTS API

### Base URL
`/v1/accounting`

### 1. Summary (Résumé Comptable)

```python
# app/modules/accounting/router.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.dependencies import get_tenant_id
from app.core.models import User

from .schemas import (
    AccountingSummary,
    JournalEntryResponse, JournalEntryList,
    LedgerAccountResponse, LedgerList,
    BalanceEntryResponse, BalanceList
)
from .service import get_accounting_service

router = APIRouter(prefix="/accounting", tags=["Comptabilité - Accounting"])


@router.get("/summary", response_model=AccountingSummary)
async def get_accounting_summary(
    period: Optional[str] = None,  # Format: "2024-01" ou "2024"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Résumé comptable : Actif, Passif, Capitaux propres, Résultat.

    Calculs :
    - Total Actif = Somme comptes classe 1-2 (solde débiteur)
    - Total Passif = Somme comptes classe 1 (solde créditeur - dettes)
    - Total Capitaux propres = Classe 1 (capitaux)
    - Produits = Classe 7 (crédit)
    - Charges = Classe 6 (débit)
    - Résultat = Produits - Charges
    """
    service = get_accounting_service(db, tenant_id)
    return service.get_summary(period)
```

### 2. Journal (Écritures Comptables)

```python
@router.get("/journal", response_model=JournalEntryList)
async def get_journal_entries(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    journal_type: Optional[str] = None,
    account_number: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Journal comptable : Liste des écritures avec lignes.

    Filtres :
    - date_from/date_to : Période
    - journal_type : PURCHASE, SALE, BANK, OD, AN
    - account_number : Filtrer par compte
    - search : Recherche sur libellé ou pièce
    """
    service = get_accounting_service(db, tenant_id)
    items, total = service.get_journal_entries(
        date_from, date_to, journal_type, account_number, search, page, page_size
    )
    return JournalEntryList(items=items, total=total, page=page, page_size=page_size)
```

### 3. Grand Livre (Ledger)

```python
@router.get("/ledger", response_model=LedgerList)
async def get_ledger(
    account_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Grand livre : Liste des comptes avec soldes.

    Retourne tous les comptes avec :
    - Total débit
    - Total crédit
    - Solde (débit - crédit ou crédit - débit selon type compte)
    """
    service = get_accounting_service(db, tenant_id)
    items, total = service.get_ledger(account_type, search, page, page_size)
    return LedgerList(items=items, total=total, page=page, page_size=page_size)


@router.get("/ledger/{account_number}", response_model=LedgerAccountResponse)
async def get_ledger_account(
    account_number: str,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Grand livre d'un compte : Détail mouvements.

    Retourne :
    - Infos compte
    - Liste écritures affectant ce compte
    - Solde progressif
    """
    service = get_accounting_service(db, tenant_id)
    ledger = service.get_ledger_account(account_number, date_from, date_to)
    if not ledger:
        raise HTTPException(status_code=404, detail="Compte non trouvé")
    return ledger
```

### 4. Balance (Soldes Comptes)

```python
@router.get("/balance", response_model=BalanceList)
async def get_balance(
    period: Optional[str] = None,  # Format: "2024-01" (mois) ou "2024" (année)
    account_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Balance comptable : Soldes d'ouverture, mouvements période, soldes clôture.

    Colonnes :
    - Compte (numéro + libellé)
    - Solde d'ouverture (débit/crédit)
    - Mouvements période (débit/crédit)
    - Solde de clôture (débit/crédit)

    Vérification : Total débit = Total crédit
    """
    service = get_accounting_service(db, tenant_id)
    items, total = service.get_balance(period, account_type)
    return BalanceList(items=items, total=total)
```

---

## 📅 PLAN SEMAINE PAR SEMAINE

### SEMAINE 1 - Modèles + Plan Comptable + Journal

**Jour 1-2 : Modèles & Migration**
- [ ] Créer modèles Account, Entry, EntryLine
- [ ] Créer migration Alembic (3 tables)
- [ ] Appliquer migration dev
- [ ] Seed plan comptable de base (comptes principaux classe 1-7)

**Jour 3-4 : Journal Comptable**
- [ ] Créer schémas Pydantic (JournalEntryResponse, etc.)
- [ ] Implémenter service.py (get_journal_entries)
- [ ] Implémenter endpoint GET /journal avec filtres
- [ ] Tests unitaires journal

**Jour 5 : Validation Frontend Journal**
- [ ] Tester frontend page Journal
- [ ] Vérifier affichage écritures
- [ ] Vérifier filtres (date, journal, compte)

**Livrable S1 :**
✅ Journal comptable fonctionnel

---

### SEMAINE 2 - Grand Livre + Balance

**Jour 6-7 : Grand Livre**
- [ ] Implémenter service.py (get_ledger, get_ledger_account)
- [ ] Calcul soldes comptes (agrégation lignes)
- [ ] Endpoint GET /ledger (liste comptes)
- [ ] Endpoint GET /ledger/{account_number} (détail compte)
- [ ] Tests unitaires grand livre

**Jour 8-9 : Balance Comptable**
- [ ] Implémenter service.py (get_balance)
- [ ] Calcul soldes ouverture/clôture par période
- [ ] Vérification équilibre (total débit = total crédit)
- [ ] Endpoint GET /balance
- [ ] Tests unitaires balance

**Jour 10 : Validation Frontend**
- [ ] Tester frontend page Grand Livre
- [ ] Tester frontend page Balance
- [ ] Vérifier calculs corrects

**Livrable S2 :**
✅ Grand livre + Balance opérationnels

---

### SEMAINE 3 - Summary + Intégration + Déploiement

**Jour 11-12 : Summary Comptable**
- [ ] Implémenter service.py (get_summary)
- [ ] Calcul actif/passif/capitaux propres
- [ ] Calcul résultat (produits - charges)
- [ ] Endpoint GET /summary
- [ ] Tests unitaires summary

**Jour 13 : Intégration Modules**
- [ ] Créer écritures auto depuis factures clients (module commercial)
- [ ] Créer écritures auto depuis factures fournisseurs (module purchases)
- [ ] Tests intégration

**Jour 14 : Tests & Documentation**
- [ ] Tests E2E complets
- [ ] Documentation API (Swagger)
- [ ] Guide comptable utilisateur
- [ ] Validation Product Owner

**Jour 15 : Déploiement Production**
- [ ] Deploy staging + tests smoke
- [ ] Deploy production
- [ ] Monitoring 48h
- [ ] Communication équipe

**Livrable S3 :**
✅ Module Accounting 100% déployé en production

---

## 📂 STRUCTURE FICHIERS

```
/app/modules/accounting/
│
├── __init__.py           # Exports
├── models.py             # Account, Entry, EntryLine
├── schemas.py            # Pydantic schemas
├── router.py             # 5 endpoints
├── service.py            # Logique métier + calculs
└── utils.py              # Validation débit/crédit, équilibre

/scripts/
└── seed_accounting_plan.py  # Seed plan comptable de base

/alembic/versions/
└── xxxx_create_accounting_tables.py
```

---

## 🔧 SEED PLAN COMPTABLE DE BASE

```python
# scripts/seed_accounting_plan.py

"""
Plan comptable simplifié français (comptes principaux).
"""

PLAN_COMPTABLE = [
    # Classe 1 - Capitaux
    {"number": "101000", "label": "Capital", "type": "EQUITY"},
    {"number": "120000", "label": "Résultat de l'exercice", "type": "EQUITY"},
    {"number": "164000", "label": "Emprunts", "type": "LIABILITY"},

    # Classe 2 - Immobilisations
    {"number": "218000", "label": "Matériel informatique", "type": "ASSET"},

    # Classe 4 - Tiers
    {"number": "411000", "label": "Clients", "type": "CUSTOMER"},
    {"number": "401000", "label": "Fournisseurs", "type": "SUPPLIER"},
    {"number": "445710", "label": "TVA collectée", "type": "LIABILITY"},
    {"number": "445660", "label": "TVA déductible", "type": "ASSET"},

    # Classe 5 - Financiers
    {"number": "512000", "label": "Banque", "type": "BANK"},
    {"number": "530000", "label": "Caisse", "type": "BANK"},

    # Classe 6 - Charges
    {"number": "601000", "label": "Achats matières", "type": "EXPENSE"},
    {"number": "604000", "label": "Achats fournitures", "type": "EXPENSE"},
    {"number": "606000", "label": "Achats non stockés", "type": "EXPENSE"},
    {"number": "621000", "label": "Personnel", "type": "EXPENSE"},
    {"number": "626000", "label": "Frais postaux", "type": "EXPENSE"},

    # Classe 7 - Produits
    {"number": "707000", "label": "Ventes marchandises", "type": "REVENUE"},
    {"number": "706000", "label": "Prestations services", "type": "REVENUE"},
]


def seed_plan_comptable(db: Session, tenant_id: str):
    """Créer les comptes de base."""
    from app.modules.accounting.models import Account

    for compte in PLAN_COMPTABLE:
        account = Account(
            tenant_id=tenant_id,
            number=compte["number"],
            label=compte["label"],
            account_type=compte["type"],
            is_active=True,
            allow_manual_entry=True
        )
        db.add(account)

    db.commit()
```

---

## ✅ CHECKLIST VALIDATION

### Semaine 1 - Journal
- [ ] 3 tables créées (accounts, entries, entry_lines)
- [ ] Plan comptable seedé (15+ comptes de base)
- [ ] Endpoint GET /journal fonctionnel
- [ ] Filtres date/journal/compte OK
- [ ] Frontend Journal affiche écritures

### Semaine 2 - Grand Livre + Balance
- [ ] Endpoint GET /ledger fonctionnel
- [ ] Endpoint GET /ledger/{account_number} fonctionnel
- [ ] Calculs soldes corrects
- [ ] Endpoint GET /balance fonctionnel
- [ ] Équilibre débit = crédit vérifié
- [ ] Frontend Grand Livre + Balance OK

### Semaine 3 - Summary + Intégration
- [ ] Endpoint GET /summary fonctionnel
- [ ] Calculs actif/passif/résultat corrects
- [ ] Écritures auto factures clients OK
- [ ] Écritures auto factures fournisseurs OK
- [ ] Tests E2E PASS
- [ ] Documentation complète
- [ ] Production déployée

---

## 🎯 MÉTRIQUES SUCCÈS

| Métrique | Cible | Validation |
|----------|-------|------------|
| Endpoints fonctionnels | 5/5 | 100% |
| Plan comptable | ≥15 comptes | Seed script |
| Équilibre comptable | Débit = Crédit | Tests unitaires |
| Frontend fonctionnel | 100% | Tests manuels |
| Performance | <300ms | Load test |
| Coverage tests | ≥75% | pytest --cov |

---

## 📊 LIVRABLE FINAL

À la fin de la Semaine 3, vous aurez :

✅ **Module Accounting 100% opérationnel**
- Plan comptable français (PCG)
- Journal comptable complet
- Grand livre par compte
- Balance comptable
- États financiers (actif/passif/résultat)

✅ **Intégration automatique**
- Factures clients → Écritures ventes
- Factures fournisseurs → Écritures achats
- Validation workflow comptable

✅ **Conformité comptable**
- Principe partie double respecté
- Équilibre débit = crédit vérifié
- Traçabilité complète

---

**Créé le :** 2026-01-23
**Par :** QA Lead - Audit Fonctionnel
**Durée estimée :** 3 semaines (15 jours dev)
**Next :** Implémenter après Purchases (Semaine 5-7)

---

**🚀 Module Accounting - Prêt pour implémentation !**
