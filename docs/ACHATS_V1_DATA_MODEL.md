# MODULE ACHATS V1 - MODELE DE DONNEES

**Version**: 1.0 - CONCEPTION
**Date**: 8 janvier 2026
**Statut**: CONCEPTION - AUCUNE IMPLEMENTATION

---

## AVERTISSEMENT

> **CE DOCUMENT EST UNE CONCEPTION UNIQUEMENT.**
>
> Les modeles decrits ci-dessous sont EXISTANTS dans le codebase.
> Ce document definit leur UTILISATION dans le cadre de ACHATS V1.
> AUCUNE modification de schema n'est autorisee.

---

## 1. MODELES UTILISES

### 1.1 Vue d'Ensemble

```
+-------------------+     +-------------------+
|     Supplier      |<----|   PurchaseOrder   |
| (procurement_     |     | (procurement_     |
|   suppliers)      |     |   orders)         |
+-------------------+     +-------------------+
         ^                        |
         |                        v
         |                +-------------------+
         |                | PurchaseOrderLine |
         |                | (procurement_     |
         |                |   order_lines)    |
         |                +-------------------+
         |
+-------------------+     +-------------------+
|  PurchaseInvoice  |---->|PurchaseInvoiceLine|
| (procurement_     |     | (procurement_     |
|   invoices)       |     |   invoice_lines)  |
+-------------------+     +-------------------+
```

### 1.2 Tables Impliquees

| Table | Usage ACHATS V1 | Acces |
|-------|-----------------|-------|
| procurement_suppliers | Fournisseurs | LECTURE/ECRITURE |
| procurement_orders | Commandes fournisseurs | LECTURE/ECRITURE |
| procurement_order_lines | Lignes de commande | LECTURE/ECRITURE |
| procurement_invoices | Factures fournisseurs | LECTURE/ECRITURE |
| procurement_invoice_lines | Lignes de facture | LECTURE/ECRITURE |

### 1.3 Tables NON Utilisees en V1

| Table | Raison |
|-------|--------|
| procurement_requisitions | Demandes d'achat V2+ |
| procurement_requisition_lines | Demandes d'achat V2+ |
| procurement_quotations | Devis fournisseurs V2+ |
| procurement_quotation_lines | Devis fournisseurs V2+ |
| procurement_receipts | Receptions V2+ |
| procurement_receipt_lines | Receptions V2+ |
| procurement_payments | Paiements M2 |
| procurement_payment_allocations | Paiements M2 |
| procurement_evaluations | Evaluation V2+ |
| procurement_supplier_contacts | Contacts V2+ |

---

## 2. TABLE: procurement_suppliers

### 2.1 Schema Complet

```python
class Supplier(Base):
    __tablename__ = "procurement_suppliers"

    # Cle primaire
    id = Column(UniversalUUID(), primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    type = Column(SQLEnum(SupplierType), default=SupplierType.OTHER)
    status = Column(SQLEnum(SupplierStatus), default=SupplierStatus.PROSPECT)

    # Identification legale
    tax_id = Column(String(50), nullable=True)  # SIRET/SIREN
    vat_number = Column(String(50), nullable=True)

    # Contact principal
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Adresse
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    postal_code = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), default="France")

    # Conditions commerciales
    payment_terms = Column(String(50), default="NET30")
    currency = Column(String(3), default="EUR")

    # Metadonnees
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2.2 Champs Utilises en V1

| Champ | Type | Usage V1 | Obligatoire |
|-------|------|----------|-------------|
| id | UUID | Identifiant unique | OUI |
| tenant_id | String(50) | Isolation multi-tenant | OUI |
| code | String(50) | Code unique fournisseur | OUI |
| name | String(255) | Nom commercial | OUI |
| type | Enum | Type fournisseur | NON |
| status | Enum | Statut (APPROVED...) | OUI |
| tax_id | String(50) | SIRET/SIREN | NON |
| vat_number | String(50) | Numero TVA | NON |
| email | String(255) | Email contact | NON |
| phone | String(50) | Telephone | NON |
| address_line1 | String(255) | Adresse ligne 1 | NON |
| postal_code | String(20) | Code postal | NON |
| city | String(100) | Ville | NON |
| country | String(100) | Pays | OUI (defaut) |
| payment_terms | String(50) | Conditions paiement | NON |
| notes | Text | Notes | NON |
| is_active | Boolean | Actif | OUI |
| created_at | DateTime | Date creation | OUI |
| updated_at | DateTime | Date modification | OUI |

### 2.3 Champs NON Utilises en V1

| Champ | Raison Exclusion |
|-------|------------------|
| legal_name | Simplification V1 |
| registration_number | Avance |
| fax | Obsolete |
| website | V2+ |
| credit_limit | Finance M2 |
| discount_rate | V2+ |
| bank_name/iban/bic | Finance M2 |
| category | V2+ |
| tags | V2+ |
| rating | Evaluation V2+ |
| account_id | Comptabilite M2 |
| custom_fields | V2+ |
| approved_by/at | V2+ |

---

## 3. TABLE: procurement_orders

### 3.1 Schema Complet

```python
class PurchaseOrder(Base):
    __tablename__ = "procurement_orders"

    # Cle primaire
    id = Column(UniversalUUID(), primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    number = Column(String(50), nullable=False)
    supplier_id = Column(UniversalUUID(), ForeignKey("procurement_suppliers.id"), nullable=False)
    status = Column(SQLEnum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT)

    # Dates
    order_date = Column(Date, nullable=False)
    expected_date = Column(Date, nullable=True)

    # Montants
    currency = Column(String(3), default="EUR")
    subtotal = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)

    # Notes
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)

    # Audit
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 3.2 Champs Utilises en V1

| Champ | Type | Usage V1 | Obligatoire |
|-------|------|----------|-------------|
| id | UUID | Identifiant unique | OUI |
| tenant_id | String(50) | Isolation | OUI |
| number | String(50) | Numero CMD-AAAA-XXXX | OUI |
| supplier_id | UUID FK | Fournisseur | OUI |
| status | Enum | DRAFT ou VALIDATED | OUI |
| order_date | Date | Date commande | OUI |
| expected_date | Date | Date livraison prevue | NON |
| currency | String(3) | Devise (EUR fixe) | OUI |
| subtotal | Decimal(15,2) | Total HT | OUI |
| discount_amount | Decimal(15,2) | Remise globale | NON |
| tax_amount | Decimal(15,2) | Total TVA | OUI |
| total | Decimal(15,2) | Total TTC | OUI |
| notes | Text | Notes fournisseur | NON |
| internal_notes | Text | Notes internes | NON |
| created_by | UUID | Createur | OUI |
| created_at | DateTime | Date creation | OUI |
| updated_at | DateTime | Date modification | OUI |

### 3.3 Champs NON Utilises en V1

| Champ | Raison Exclusion |
|-------|------------------|
| requisition_id | Demandes V2+ |
| quotation_id | Devis V2+ |
| confirmed_date | Workflow avance V2+ |
| delivery_address | Logistique V2+ |
| delivery_contact | Logistique V2+ |
| shipping_cost | Logistique V2+ |
| payment_terms | Finance M2 |
| incoterms | Avance V2+ |
| received_amount | Receptions V2+ |
| invoiced_amount | Calcule automatique |
| supplier_reference | V2+ |
| attachments | V2+ |
| sent_at | V2+ |
| confirmed_at | V2+ |

---

## 4. TABLE: procurement_order_lines

### 4.1 Schema

```python
class PurchaseOrderLine(Base):
    __tablename__ = "procurement_order_lines"

    id = Column(UniversalUUID(), primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    order_id = Column(UniversalUUID(), ForeignKey("procurement_orders.id"), nullable=False)

    line_number = Column(Integer, nullable=False)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit = Column(String(20), default="UNIT")
    unit_price = Column(Numeric(15, 4), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=20)
    total = Column(Numeric(15, 2), nullable=False)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 4.2 Champs Utilises en V1

| Champ | Type | Usage V1 | Obligatoire |
|-------|------|----------|-------------|
| id | UUID | Identifiant unique | OUI |
| tenant_id | String(50) | Isolation | OUI |
| order_id | UUID FK | Commande parente | OUI |
| line_number | Integer | Ordre affichage | OUI |
| description | String(500) | Description ligne | OUI |
| quantity | Decimal(15,4) | Quantite | OUI |
| unit | String(20) | Unite de mesure | NON |
| unit_price | Decimal(15,4) | Prix unitaire HT | OUI |
| discount_percent | Decimal(5,2) | Remise ligne % | NON |
| tax_rate | Decimal(5,2) | Taux TVA % | OUI |
| total | Decimal(15,2) | Total ligne TTC | OUI |
| notes | Text | Notes ligne | NON |
| created_at | DateTime | Date creation | OUI |

### 4.3 Champs NON Utilises en V1

| Champ | Raison |
|-------|--------|
| product_id | Catalogue V2+ |
| product_code | Catalogue V2+ |
| expected_date | Logistique V2+ |
| received_quantity | Receptions V2+ |
| invoiced_quantity | Calcul auto |
| requisition_line_id | Demandes V2+ |

---

## 5. TABLE: procurement_invoices

### 5.1 Schema

```python
class PurchaseInvoice(Base):
    __tablename__ = "procurement_invoices"

    id = Column(UniversalUUID(), primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    number = Column(String(50), nullable=False)
    supplier_id = Column(UniversalUUID(), ForeignKey("procurement_suppliers.id"), nullable=False)
    order_id = Column(UniversalUUID(), ForeignKey("procurement_orders.id"), nullable=True)

    status = Column(SQLEnum(PurchaseInvoiceStatus), default=PurchaseInvoiceStatus.DRAFT)

    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    supplier_invoice_number = Column(String(100), nullable=True)
    supplier_invoice_date = Column(Date, nullable=True)

    currency = Column(String(3), default="EUR")
    subtotal = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)

    notes = Column(Text, nullable=True)

    validated_by = Column(UniversalUUID(), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 5.2 Champs Utilises en V1

| Champ | Type | Usage V1 | Obligatoire |
|-------|------|----------|-------------|
| id | UUID | Identifiant unique | OUI |
| tenant_id | String(50) | Isolation | OUI |
| number | String(50) | Numero FAF-AAAA-XXXX | OUI |
| supplier_id | UUID FK | Fournisseur | OUI |
| order_id | UUID FK | Commande source | NON |
| status | Enum | DRAFT ou VALIDATED | OUI |
| invoice_date | Date | Date facture interne | OUI |
| due_date | Date | Echeance | NON |
| supplier_invoice_number | String(100) | Numero facture fournisseur | NON |
| supplier_invoice_date | Date | Date facture fournisseur | NON |
| currency | String(3) | Devise (EUR fixe) | OUI |
| subtotal | Decimal(15,2) | Total HT | OUI |
| discount_amount | Decimal(15,2) | Remise globale | NON |
| tax_amount | Decimal(15,2) | Total TVA | OUI |
| total | Decimal(15,2) | Total TTC | OUI |
| notes | Text | Notes | NON |
| validated_by | UUID | Validateur | NON |
| validated_at | DateTime | Date validation | NON |
| created_by | UUID | Createur | OUI |
| created_at | DateTime | Date creation | OUI |
| updated_at | DateTime | Date modification | OUI |

### 5.3 Champs NON Utilises en V1

| Champ | Raison |
|-------|--------|
| paid_amount | Paiements M2 |
| remaining_amount | Paiements M2 |
| payment_terms | Finance M2 |
| payment_method | Paiements M2 |
| journal_entry_id | Comptabilite M2 |
| posted_at | Comptabilite M2 |
| attachments | V2+ |

---

## 6. TABLE: procurement_invoice_lines

### 6.1 Schema

```python
class PurchaseInvoiceLine(Base):
    __tablename__ = "procurement_invoice_lines"

    id = Column(UniversalUUID(), primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    invoice_id = Column(UniversalUUID(), ForeignKey("procurement_invoices.id"), nullable=False)
    order_line_id = Column(UniversalUUID(), nullable=True)

    line_number = Column(Integer, nullable=False)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit = Column(String(20), default="UNIT")
    unit_price = Column(Numeric(15, 4), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=20)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), nullable=False)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 6.2 Champs Utilises en V1

| Champ | Type | Usage V1 | Obligatoire |
|-------|------|----------|-------------|
| id | UUID | Identifiant unique | OUI |
| tenant_id | String(50) | Isolation | OUI |
| invoice_id | UUID FK | Facture parente | OUI |
| order_line_id | UUID FK | Ligne commande source | NON |
| line_number | Integer | Ordre affichage | OUI |
| description | String(500) | Description ligne | OUI |
| quantity | Decimal(15,4) | Quantite | OUI |
| unit | String(20) | Unite de mesure | NON |
| unit_price | Decimal(15,4) | Prix unitaire HT | OUI |
| discount_percent | Decimal(5,2) | Remise ligne % | NON |
| tax_rate | Decimal(5,2) | Taux TVA % | OUI |
| tax_amount | Decimal(15,2) | Montant TVA | OUI |
| total | Decimal(15,2) | Total ligne TTC | OUI |
| notes | Text | Notes ligne | NON |
| created_at | DateTime | Date creation | OUI |

### 6.3 Champs NON Utilises en V1

| Champ | Raison |
|-------|--------|
| product_id | Catalogue V2+ |
| product_code | Catalogue V2+ |
| account_id | Comptabilite M2 |
| analytic_code | Analytique M2 |

---

## 7. ENUMERATIONS

### 7.1 SupplierStatus (V1)

```python
class SupplierStatus(str, enum.Enum):
    PROSPECT = "PROSPECT"    # NON UTILISE V1
    PENDING = "PENDING"      # NON UTILISE V1
    APPROVED = "APPROVED"    # Utilise V1 (defaut)
    BLOCKED = "BLOCKED"      # Utilise V1
    INACTIVE = "INACTIVE"    # NON UTILISE V1
```

**Valeurs V1**: `APPROVED`, `BLOCKED`

### 7.2 SupplierType

```python
class SupplierType(str, enum.Enum):
    MANUFACTURER = "MANUFACTURER"  # Utilise V1
    DISTRIBUTOR = "DISTRIBUTOR"    # Utilise V1
    SERVICE = "SERVICE"            # Utilise V1
    FREELANCE = "FREELANCE"        # Utilise V1
    OTHER = "OTHER"                # Utilise V1 (defaut)
```

### 7.3 PurchaseOrderStatus (V1)

```python
class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"          # Utilise V1
    SENT = "SENT"            # NON UTILISE V1
    CONFIRMED = "CONFIRMED"  # NON UTILISE V1
    PARTIAL = "PARTIAL"      # NON UTILISE V1
    RECEIVED = "RECEIVED"    # NON UTILISE V1
    INVOICED = "INVOICED"    # NON UTILISE V1
    CANCELLED = "CANCELLED"  # NON UTILISE V1
```

**Valeurs V1**: `DRAFT`, `VALIDATED` (note: VALIDATED est ajoute)

### 7.4 PurchaseInvoiceStatus (V1)

```python
class PurchaseInvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"          # Utilise V1
    VALIDATED = "VALIDATED"  # Utilise V1
    PAID = "PAID"            # NON UTILISE V1 (Paiements M2)
    PARTIAL = "PARTIAL"      # NON UTILISE V1 (Paiements M2)
    CANCELLED = "CANCELLED"  # NON UTILISE V1
```

**Valeurs V1**: `DRAFT`, `VALIDATED`

---

## 8. INDEX UTILISES

### 8.1 Index procurement_suppliers

| Index | Colonnes | Usage |
|-------|----------|-------|
| idx_suppliers_tenant | tenant_id | Filtrage par tenant |
| idx_suppliers_status | tenant_id, status | Filtrage par statut |
| unique_supplier_code | tenant_id, code | Code unique (UNIQUE) |

### 8.2 Index procurement_orders

| Index | Colonnes | Usage |
|-------|----------|-------|
| idx_orders_tenant | tenant_id | Filtrage par tenant |
| idx_orders_supplier | tenant_id, supplier_id | Filtrage par fournisseur |
| idx_orders_status | tenant_id, status | Filtrage par statut |
| idx_orders_date | tenant_id, order_date | Tri chronologique |
| unique_order_number | tenant_id, number | Numero unique (UNIQUE) |

### 8.3 Index procurement_invoices

| Index | Colonnes | Usage |
|-------|----------|-------|
| idx_purchase_invoices_tenant | tenant_id | Filtrage par tenant |
| idx_purchase_invoices_supplier | tenant_id, supplier_id | Filtrage par fournisseur |
| idx_purchase_invoices_status | tenant_id, status | Filtrage par statut |
| idx_purchase_invoices_due | tenant_id, due_date | Tri echeance |
| unique_purchase_invoice_number | tenant_id, number | Numero unique (UNIQUE) |

---

## 9. REGLES DE CALCUL

### 9.1 Calcul Ligne

```python
def calculate_line(line) -> None:
    # Sous-total HT avec remise
    discount_factor = 1 - (line.discount_percent / 100)
    subtotal = round(line.quantity * line.unit_price * discount_factor, 2)

    # TVA
    line.tax_amount = round(subtotal * (line.tax_rate / 100), 2)

    # Total TTC
    line.total = round(subtotal + line.tax_amount, 2)
```

### 9.2 Calcul Document

```python
def calculate_document(doc) -> None:
    # Somme des lignes
    subtotals = [calculate_line_subtotal(line) for line in doc.lines]
    doc.subtotal = sum(subtotals)
    doc.tax_amount = sum(line.tax_amount for line in doc.lines)

    # Remise globale (si applicable)
    if doc.discount_amount > 0:
        doc.subtotal = round(doc.subtotal - doc.discount_amount, 2)

    # Total TTC
    doc.total = round(doc.subtotal + doc.tax_amount, 2)
```

---

## 10. NUMEROTATION

### 10.1 Format

```
Type              Format                  Exemple
----              ------                  -------
SUPPLIER          FRN-{XXXX}             FRN-0001
PURCHASE_ORDER    CMD-{AAAA}-{XXXX}      CMD-2026-0001
PURCHASE_INVOICE  FAF-{AAAA}-{XXXX}      FAF-2026-0001
```

### 10.2 Algorithme

```python
def generate_number(tenant_id: str, doc_type: str, year: int) -> str:
    # Prefixe selon type
    prefix = "CMD" if doc_type == "ORDER" else "FAF"

    # Recherche du dernier numero pour ce tenant/type/annee
    last = db.query(Model).filter(
        Model.tenant_id == tenant_id,
        Model.number.like(f"{prefix}-{year}-%")
    ).order_by(Model.number.desc()).first()

    # Increment
    if last:
        seq = int(last.number.split("-")[-1]) + 1
    else:
        seq = 1

    return f"{prefix}-{year}-{seq:04d}"
```

---

## 11. WORKFLOW DONNEES

### 11.1 Creation Commande

```
1. Validation supplier_id existe et actif
2. Generation numero CMD-AAAA-XXXX
3. Status = DRAFT
4. Insertion procurement_orders
5. Insertion procurement_order_lines
6. Calcul totaux
7. Commit transaction
```

### 11.2 Validation Commande

```
1. Verification status == DRAFT
2. Verification au moins 1 ligne
3. Verification total > 0
4. Update status = VALIDATED
5. Commit (document verrouille)
```

### 11.3 Creation Facture depuis Commande

```
1. Verification commande status == VALIDATED
2. Generation numero FAF-AAAA-XXXX
3. Copie header -> nouvelle facture
4. Set facture.order_id = commande.id
5. Status facture = DRAFT
6. Copie lignes commande -> nouvelles lignes facture
7. Set order_line_id sur chaque ligne
8. Commit transaction
```

---

## 12. MIGRATION

### 12.1 Aucune Migration Requise

Les tables `procurement_*` existent deja.
ACHATS V1 utilise le schema existant sans modification.

### 12.2 Donnees de Test (Dev Only)

```python
# Donnees de demo pour environnement developpement
DEMO_SUPPLIERS = [
    {"code": "FRN-0001", "name": "Fournisseur Demo", "status": "APPROVED"},
    {"code": "FRN-0002", "name": "Tech Supplies", "status": "APPROVED"},
]

DEMO_ORDERS = [
    {"number": "CMD-2026-0001", "supplier": "FRN-0001", "total": 2500.00},
]

DEMO_INVOICES = [
    {"number": "FAF-2026-0001", "supplier": "FRN-0001", "total": 2500.00},
]
```

---

**Document de conception - Version 1.0**
**Date: 8 janvier 2026**
**Statut: CONCEPTION - PAS D'IMPLEMENTATION**
