# MODULE VENTES T0 - MODELE DE DONNEES

**Version**: 1.0 - CONCEPTION
**Date**: 8 janvier 2026
**Statut**: CONCEPTION - AUCUNE IMPLEMENTATION

---

## AVERTISSEMENT

> **CE DOCUMENT EST UNE CONCEPTION UNIQUEMENT.**
>
> Les modeles decrits ci-dessous sont EXISTANTS dans le codebase.
> Ce document definit leur UTILISATION dans le cadre de VENTES T0.
> AUCUNE modification de schema n'est autorisee.

---

## 1. MODELES UTILISES

### 1.1 Vue d'Ensemble

```
+-------------------+     +-------------------+
|   CommercialDocument   |---->|   DocumentLine    |
|   (commercial_documents)   |     |   (document_lines)|
+-------------------+     +-------------------+
         |
         v
+-------------------+
|     Customer      |
|    (customers)    |
+-------------------+
         |
         v
+-------------------+
|     Contact       |
| (customer_contacts)|
+-------------------+
```

### 1.2 Tables Impliquees

| Table | Usage VENTES T0 | Acces |
|-------|-----------------|-------|
| commercial_documents | Devis et Factures | LECTURE/ECRITURE |
| document_lines | Lignes de documents | LECTURE/ECRITURE |
| customers | Clients associes | LECTURE SEULE |
| customer_contacts | Contacts associes | LECTURE SEULE |

---

## 2. TABLE: commercial_documents

### 2.1 Schema Complet

```python
class CommercialDocument(Base):
    __tablename__ = "commercial_documents"

    # Cle primaire
    id = Column(UniversalUUID(), primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Relations
    customer_id = Column(UniversalUUID(), ForeignKey("customers.id"), nullable=False)
    opportunity_id = Column(UniversalUUID())  # NON UTILISE EN T0

    # Identification
    type = Column(Enum(DocumentType), nullable=False)
    number = Column(String(50), nullable=False)
    reference = Column(String(100))
    status = Column(Enum(DocumentStatus), default=DocumentStatus.DRAFT)

    # Dates
    date = Column(Date, nullable=False, default=date.today)
    due_date = Column(Date)
    validity_date = Column(Date)
    delivery_date = Column(Date)  # NON UTILISE EN T0

    # Adresses (JSON)
    billing_address = Column(JSON)
    shipping_address = Column(JSON)  # NON UTILISE EN T0

    # Montants
    subtotal = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    discount_percent = Column(Float, default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)
    currency = Column(String(3), default="EUR")

    # Paiement - NON UTILISE EN T0
    payment_terms = Column(Enum(PaymentTerms))
    payment_method = Column(Enum(PaymentMethod))
    paid_amount = Column(Numeric(15, 2), default=0)
    remaining_amount = Column(Numeric(15, 2))

    # Livraison - NON UTILISE EN T0
    shipping_method = Column(String(100))
    shipping_cost = Column(Numeric(10, 2), default=0)
    tracking_number = Column(String(100))

    # Notes
    notes = Column(Text)
    internal_notes = Column(Text)
    terms = Column(Text)

    # Liens documents
    parent_id = Column(UniversalUUID())  # Devis source pour facture
    invoice_id = Column(UniversalUUID())  # NON UTILISE EN T0

    # PDF - NON UTILISE EN T0
    pdf_url = Column(String(500))

    # Attribution
    assigned_to = Column(UniversalUUID())
    validated_by = Column(UniversalUUID())
    validated_at = Column(DateTime)

    # Audit
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2.2 Champs Utilises en T0

| Champ | Type | Usage T0 | Obligatoire |
|-------|------|----------|-------------|
| id | UUID | Identifiant unique | OUI |
| tenant_id | String(50) | Isolation multi-tenant | OUI |
| customer_id | UUID FK | Client associe | OUI |
| type | Enum | QUOTE ou INVOICE | OUI |
| number | String(50) | Numero automatique | OUI |
| status | Enum | DRAFT ou VALIDATED | OUI |
| date | Date | Date du document | OUI |
| due_date | Date | Echeance (facture) | NON |
| validity_date | Date | Validite (devis) | NON |
| subtotal | Decimal(15,2) | Total HT | OUI |
| discount_percent | Float | Remise globale % | NON |
| discount_amount | Decimal(15,2) | Remise en valeur | NON |
| tax_amount | Decimal(15,2) | Total TVA | OUI |
| total | Decimal(15,2) | Total TTC | OUI |
| currency | String(3) | Devise (EUR fixe) | OUI |
| notes | Text | Notes client | NON |
| internal_notes | Text | Notes internes | NON |
| parent_id | UUID | Lien devis->facture | NON |
| assigned_to | UUID | Commercial | NON |
| validated_by | UUID | Validateur | NON |
| validated_at | DateTime | Date validation | NON |
| created_by | UUID | Createur | OUI |
| created_at | DateTime | Date creation | OUI |
| updated_at | DateTime | Date modification | OUI |

### 2.3 Champs NON Utilises en T0

| Champ | Raison Exclusion |
|-------|------------------|
| opportunity_id | Pipeline non inclus |
| delivery_date | Logistique T1+ |
| shipping_address | Logistique T1+ |
| payment_terms | Paiements M2 |
| payment_method | Paiements M2 |
| paid_amount | Paiements M2 |
| remaining_amount | Paiements M2 |
| shipping_method | Logistique T1+ |
| shipping_cost | Logistique T1+ |
| tracking_number | Logistique T1+ |
| invoice_id | Workflow avance T1+ |
| pdf_url | Export PDF T1+ |

---

## 3. TABLE: document_lines

### 3.1 Schema Complet

```python
class DocumentLine(Base):
    __tablename__ = "document_lines"

    # Cle primaire
    id = Column(UniversalUUID(), primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    document_id = Column(UniversalUUID(), ForeignKey("commercial_documents.id"), nullable=False)

    # Position
    line_number = Column(Integer, nullable=False)

    # Produit/Service
    product_id = Column(UniversalUUID())
    product_code = Column(String(50))
    description = Column(Text, nullable=False)

    # Quantites
    quantity = Column(Numeric(10, 3), default=1)
    unit = Column(String(20))

    # Prix
    unit_price = Column(Numeric(15, 4), default=0)
    discount_percent = Column(Float, default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    subtotal = Column(Numeric(15, 2), default=0)

    # TVA
    tax_rate = Column(Float, default=20.0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)

    # Notes
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 3.2 Champs Utilises en T0

| Champ | Type | Usage T0 | Obligatoire |
|-------|------|----------|-------------|
| id | UUID | Identifiant unique | OUI |
| tenant_id | String(50) | Isolation | OUI |
| document_id | UUID FK | Document parent | OUI |
| line_number | Integer | Ordre affichage | OUI |
| description | Text | Description ligne | OUI |
| quantity | Decimal(10,3) | Quantite | OUI |
| unit | String(20) | Unite de mesure | NON |
| unit_price | Decimal(15,4) | Prix unitaire HT | OUI |
| discount_percent | Float | Remise ligne % | NON |
| subtotal | Decimal(15,2) | Sous-total HT | OUI |
| tax_rate | Float | Taux TVA % | OUI |
| tax_amount | Decimal(15,2) | Montant TVA | OUI |
| total | Decimal(15,2) | Total ligne TTC | OUI |
| notes | Text | Notes ligne | NON |
| created_at | DateTime | Date creation | OUI |

### 3.3 Champs NON Utilises en T0

| Champ | Raison Exclusion |
|-------|------------------|
| product_id | Catalogue produits T1+ |
| product_code | Catalogue produits T1+ |
| discount_amount | Remise valeur T1+ |

---

## 4. ENUMERATIONS

### 4.1 DocumentType

```python
class DocumentType(str, enum.Enum):
    QUOTE = "QUOTE"        # Utilise T0
    ORDER = "ORDER"        # Exclu T0
    INVOICE = "INVOICE"    # Utilise T0
    CREDIT_NOTE = "CREDIT_NOTE"  # Exclu T0
    PROFORMA = "PROFORMA"  # Exclu T0
    DELIVERY = "DELIVERY"  # Exclu T0
```

**Valeurs T0**: `QUOTE`, `INVOICE`

### 4.2 DocumentStatus

```python
class DocumentStatus(str, enum.Enum):
    DRAFT = "DRAFT"           # Utilise T0
    PENDING = "PENDING"       # Exclu T0
    VALIDATED = "VALIDATED"   # Utilise T0
    SENT = "SENT"             # Exclu T0
    ACCEPTED = "ACCEPTED"     # Exclu T0
    REJECTED = "REJECTED"     # Exclu T0
    DELIVERED = "DELIVERED"   # Exclu T0
    INVOICED = "INVOICED"     # Exclu T0
    PAID = "PAID"             # Exclu T0
    CANCELLED = "CANCELLED"   # Exclu T0
```

**Valeurs T0**: `DRAFT`, `VALIDATED`

---

## 5. INDEX UTILISES

### 5.1 Index commercial_documents

| Index | Colonnes | Usage |
|-------|----------|-------|
| ix_documents_tenant_number | tenant_id, type, number | Recherche par numero (UNIQUE) |
| ix_documents_tenant_customer | tenant_id, customer_id | Filtrage par client |
| ix_documents_tenant_type | tenant_id, type | Filtrage devis/factures |
| ix_documents_tenant_status | tenant_id, status | Filtrage par statut |
| ix_documents_tenant_date | tenant_id, date | Tri chronologique |

### 5.2 Index document_lines

| Index | Colonnes | Usage |
|-------|----------|-------|
| ix_doc_lines_tenant_document | tenant_id, document_id | Jointure document->lignes |

---

## 6. CONTRAINTES DE DONNEES

### 6.1 Contraintes d'Integrite

| Contrainte | Table | Description |
|------------|-------|-------------|
| PK | commercial_documents | id unique |
| PK | document_lines | id unique |
| FK customer_id | commercial_documents | Vers customers.id |
| FK document_id | document_lines | Vers commercial_documents.id CASCADE |
| UNIQUE | commercial_documents | (tenant_id, type, number) |

### 6.2 Contraintes Metier (Service Layer)

| Contrainte | Description | Enforcement |
|------------|-------------|-------------|
| tenant_id obligatoire | Toutes les tables | NOT NULL + Service |
| customer_id requis | Document doit avoir un client | Service validation |
| number unique par type | DEV-2026-0001 != FAC-2026-0001 | Index unique |
| status immutable | VALIDATED -> pas de modification | Service guard |
| calculs coherents | total = subtotal + tax_amount | Service recalcul |

---

## 7. REGLES DE CALCUL

### 7.1 Calcul Ligne

```python
def calculate_line(line: DocumentLine) -> None:
    # Sous-total HT avec remise
    discount_factor = 1 - (line.discount_percent / 100)
    line.subtotal = round(line.quantity * line.unit_price * discount_factor, 2)

    # TVA
    line.tax_amount = round(line.subtotal * (line.tax_rate / 100), 2)

    # Total TTC
    line.total = round(line.subtotal + line.tax_amount, 2)
```

### 7.2 Calcul Document

```python
def calculate_document(doc: CommercialDocument) -> None:
    # Somme des lignes
    doc.subtotal = sum(line.subtotal for line in doc.lines)
    doc.tax_amount = sum(line.tax_amount for line in doc.lines)

    # Remise globale (si applicable)
    if doc.discount_percent > 0:
        discount = doc.subtotal * (doc.discount_percent / 100)
        doc.discount_amount = round(discount, 2)
        doc.subtotal = round(doc.subtotal - doc.discount_amount, 2)
        # Recalcul TVA sur base remisee
        doc.tax_amount = round(doc.subtotal * 0.20, 2)  # Taux moyen

    # Total TTC
    doc.total = round(doc.subtotal + doc.tax_amount, 2)
```

---

## 8. NUMEROTATION

### 8.1 Format

```
Type        Format              Exemple
----        ------              -------
QUOTE       DEV-{AAAA}-{XXXX}   DEV-2026-0001
INVOICE     FAC-{AAAA}-{XXXX}   FAC-2026-0001
```

### 8.2 Algorithme

```python
def generate_number(tenant_id: str, doc_type: DocumentType, year: int) -> str:
    # Prefixe selon type
    prefix = "DEV" if doc_type == DocumentType.QUOTE else "FAC"

    # Recherche du dernier numero pour ce tenant/type/annee
    last = db.query(CommercialDocument).filter(
        CommercialDocument.tenant_id == tenant_id,
        CommercialDocument.type == doc_type,
        CommercialDocument.number.like(f"{prefix}-{year}-%")
    ).order_by(CommercialDocument.number.desc()).first()

    # Increment
    if last:
        seq = int(last.number.split("-")[-1]) + 1
    else:
        seq = 1

    return f"{prefix}-{year}-{seq:04d}"
```

### 8.3 Contraintes Numerotation

| Contrainte | Description |
|------------|-------------|
| Unicite | Numero unique par tenant + type |
| Sequentiel | Pas de trous dans la sequence |
| Immutable | Numero non modifiable apres creation |
| Par annee | Sequence reinitialise chaque annee |

---

## 9. WORKFLOW DONNEES

### 9.1 Creation Devis

```
1. Validation client_id existe
2. Generation numero DEV-AAAA-XXXX
3. Status = DRAFT
4. Insertion commercial_documents
5. Insertion document_lines
6. Calcul totaux
7. Commit transaction
```

### 9.2 Validation Document

```
1. Verification status == DRAFT
2. Verification au moins 1 ligne
3. Verification total > 0
4. Update status = VALIDATED
5. Update validated_by, validated_at
6. Commit (document verrouille)
```

### 9.3 Conversion Devis -> Facture

```
1. Verification devis status == VALIDATED
2. Generation numero FAC-AAAA-XXXX
3. Copie header -> nouvelle facture
4. Set facture.parent_id = devis.id
5. Status facture = DRAFT
6. Copie lignes -> nouvelles lignes
7. Commit transaction
```

---

## 10. REQUETES TYPES

### 10.1 Liste Devis par Tenant

```sql
SELECT * FROM commercial_documents
WHERE tenant_id = :tenant_id
  AND type = 'QUOTE'
ORDER BY date DESC, number DESC
LIMIT :limit OFFSET :offset
```

### 10.2 Detail Document avec Lignes

```sql
SELECT d.*, l.*
FROM commercial_documents d
LEFT JOIN document_lines l ON l.document_id = d.id
WHERE d.id = :document_id
  AND d.tenant_id = :tenant_id
ORDER BY l.line_number
```

### 10.3 Export CSV

```sql
SELECT
    d.number AS "Numero",
    d.date AS "Date",
    c.name AS "Client",
    d.subtotal AS "HT",
    d.tax_amount AS "TVA",
    d.total AS "TTC",
    d.status AS "Statut"
FROM commercial_documents d
JOIN customers c ON c.id = d.customer_id
WHERE d.tenant_id = :tenant_id
  AND d.type = :type
ORDER BY d.date DESC
```

---

## 11. MIGRATION

### 11.1 Aucune Migration Requise

Les tables `commercial_documents` et `document_lines` existent deja.
VENTES T0 utilise le schema existant sans modification.

### 11.2 Donnees de Test (Dev Only)

```python
# Donnees de demo pour environnement developpement
DEMO_QUOTES = [
    {"number": "DEV-2026-0001", "customer": "Client Demo", "total": 1200.00},
    {"number": "DEV-2026-0002", "customer": "Client Test", "total": 3500.00},
]
```

---

**Document de conception - Version 1.0**
**Date: 8 janvier 2026**
**Statut: CONCEPTION - PAS D'IMPLEMENTATION**
