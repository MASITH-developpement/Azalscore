# MODULE ACHATS V1 - CHECKLIST PASS/FAIL

**Version**: 1.0 - CONCEPTION
**Date**: 8 janvier 2026
**Statut**: CONCEPTION - AUCUNE IMPLEMENTATION

---

## AVERTISSEMENT

> **CE DOCUMENT EST UNE CHECKLIST DE VALIDATION UNIQUEMENT.**
>
> Elle sera utilisee pour valider l'implementation future de ACHATS V1.
> AUCUNE implementation n'est autorisee a ce stade.
> Tous les criteres doivent etre PASS avant activation.

---

## 1. RESUME VALIDATION

### 1.1 Criteres de Passage

| Categorie | Tests Requis | Seuil PASS |
|-----------|--------------|------------|
| Backend Unit Tests | X tests | 100% |
| Backend Integration | X tests | 100% |
| Frontend E2E | X tests | 100% |
| RBAC Tests | X tests | 100% |
| Performance | Benchmarks | < 1s response |
| Security | Audit | 0 critical, 0 high |

### 1.2 Dependances

| Dependance | Statut Requis | Statut Actuel |
|------------|---------------|---------------|
| VENTES V1 Module | PASS | **PASS** |
| CRM T0 Module | PASS | **PASS** |
| RBAC System | OPERATIONNEL | **OPERATIONNEL** |
| Multi-tenant | VALIDE | **VALIDE** |
| Audit System | ACTIF | **ACTIF** |

---

## 2. CHECKLIST FONCTIONNELLE

### 2.1 Fournisseurs (SUPPLIER)

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| S-001 | Creer un fournisseur | [ ] PENDING | |
| S-002 | Code unique FRN-XXXX automatique | [ ] PENDING | |
| S-003 | Modifier un fournisseur | [ ] PENDING | |
| S-004 | Consulter un fournisseur | [ ] PENDING | |
| S-005 | Bloquer un fournisseur | [ ] PENDING | |
| S-006 | Liste des fournisseurs avec pagination | [ ] PENDING | |
| S-007 | Filtrage par statut (APPROVED/BLOCKED) | [ ] PENDING | |
| S-008 | Recherche par nom/code | [ ] PENDING | |

### 2.2 Commandes Fournisseurs (PURCHASE_ORDER)

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| O-001 | Creer une commande brouillon | [ ] PENDING | |
| O-002 | Numero auto CMD-AAAA-XXXX | [ ] PENDING | |
| O-003 | Associer un fournisseur existant | [ ] PENDING | |
| O-004 | Ajouter des lignes a la commande | [ ] PENDING | |
| O-005 | Modifier les lignes | [ ] PENDING | |
| O-006 | Supprimer des lignes | [ ] PENDING | |
| O-007 | Calcul automatique HT/TVA/TTC | [ ] PENDING | |
| O-008 | Modifier une commande brouillon | [ ] PENDING | |
| O-009 | Supprimer une commande brouillon | [ ] PENDING | |
| O-010 | Valider une commande (DRAFT->VALIDATED) | [ ] PENDING | |
| O-011 | Commande validee non modifiable | [ ] PENDING | |
| O-012 | Commande validee non supprimable | [ ] PENDING | |
| O-013 | Liste des commandes avec pagination | [ ] PENDING | |
| O-014 | Filtrage par statut | [ ] PENDING | |
| O-015 | Filtrage par fournisseur | [ ] PENDING | |
| O-016 | Recherche par numero/fournisseur | [ ] PENDING | |
| O-017 | Export CSV liste commandes | [ ] PENDING | |

### 2.3 Factures Fournisseurs (PURCHASE_INVOICE)

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| I-001 | Creer une facture directe | [ ] PENDING | |
| I-002 | Numero auto FAF-AAAA-XXXX | [ ] PENDING | |
| I-003 | Associer un fournisseur existant | [ ] PENDING | |
| I-004 | Creer facture depuis commande validee | [ ] PENDING | |
| I-005 | Copie lignes commande vers facture | [ ] PENDING | |
| I-006 | Lien order_id commande -> facture | [ ] PENDING | |
| I-007 | Saisie numero facture fournisseur | [ ] PENDING | |
| I-008 | Saisie date facture fournisseur | [ ] PENDING | |
| I-009 | Ajouter des lignes a la facture | [ ] PENDING | |
| I-010 | Modifier les lignes | [ ] PENDING | |
| I-011 | Supprimer des lignes | [ ] PENDING | |
| I-012 | Calcul automatique HT/TVA/TTC | [ ] PENDING | |
| I-013 | Modifier une facture brouillon | [ ] PENDING | |
| I-014 | Supprimer une facture brouillon | [ ] PENDING | |
| I-015 | Valider une facture (DRAFT->VALIDATED) | [ ] PENDING | |
| I-016 | Facture validee non modifiable | [ ] PENDING | |
| I-017 | Facture validee non supprimable | [ ] PENDING | |
| I-018 | Liste des factures avec pagination | [ ] PENDING | |
| I-019 | Filtrage par statut | [ ] PENDING | |
| I-020 | Filtrage par fournisseur | [ ] PENDING | |
| I-021 | Recherche par numero/fournisseur | [ ] PENDING | |
| I-022 | Export CSV liste factures | [ ] PENDING | |

### 2.4 Lignes de Document

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| L-001 | Ajouter ligne avec description | [ ] PENDING | |
| L-002 | Quantite obligatoire | [ ] PENDING | |
| L-003 | Prix unitaire obligatoire | [ ] PENDING | |
| L-004 | Taux TVA par defaut 20% | [ ] PENDING | |
| L-005 | Taux TVA modifiable (0%, 5.5%, 10%, 20%) | [ ] PENDING | |
| L-006 | Remise ligne en pourcentage | [ ] PENDING | |
| L-007 | Calcul subtotal correct | [ ] PENDING | |
| L-008 | Calcul tax_amount correct | [ ] PENDING | |
| L-009 | Calcul total ligne correct | [ ] PENDING | |
| L-010 | Ordre des lignes (line_number) | [ ] PENDING | |

---

## 3. CHECKLIST TECHNIQUE

### 3.1 API Backend

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| API-001 | GET /api/v1/purchases/suppliers | [ ] PENDING | |
| API-002 | GET /api/v1/purchases/suppliers/{id} | [ ] PENDING | |
| API-003 | POST /api/v1/purchases/suppliers | [ ] PENDING | |
| API-004 | PUT /api/v1/purchases/suppliers/{id} | [ ] PENDING | |
| API-005 | GET /api/v1/purchases/orders | [ ] PENDING | |
| API-006 | GET /api/v1/purchases/orders/{id} | [ ] PENDING | |
| API-007 | POST /api/v1/purchases/orders | [ ] PENDING | |
| API-008 | PUT /api/v1/purchases/orders/{id} | [ ] PENDING | |
| API-009 | DELETE /api/v1/purchases/orders/{id} | [ ] PENDING | |
| API-010 | POST /api/v1/purchases/orders/{id}/validate | [ ] PENDING | |
| API-011 | GET /api/v1/purchases/invoices | [ ] PENDING | |
| API-012 | GET /api/v1/purchases/invoices/{id} | [ ] PENDING | |
| API-013 | POST /api/v1/purchases/invoices | [ ] PENDING | |
| API-014 | PUT /api/v1/purchases/invoices/{id} | [ ] PENDING | |
| API-015 | DELETE /api/v1/purchases/invoices/{id} | [ ] PENDING | |
| API-016 | POST /api/v1/purchases/invoices/{id}/validate | [ ] PENDING | |
| API-017 | POST /api/v1/purchases/orders/{id}/to-invoice | [ ] PENDING | |
| API-018 | GET /api/v1/purchases/orders/export | [ ] PENDING | |
| API-019 | GET /api/v1/purchases/invoices/export | [ ] PENDING | |

### 3.2 Base de Donnees

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| DB-001 | Table procurement_suppliers existe | [ ] PENDING | |
| DB-002 | Table procurement_orders existe | [ ] PENDING | |
| DB-003 | Table procurement_order_lines existe | [ ] PENDING | |
| DB-004 | Table procurement_invoices existe | [ ] PENDING | |
| DB-005 | Table procurement_invoice_lines existe | [ ] PENDING | |
| DB-006 | Index tenant_id performant | [ ] PENDING | |
| DB-007 | Index numero unique | [ ] PENDING | |
| DB-008 | FK supplier_id valide | [ ] PENDING | |
| DB-009 | CASCADE delete lignes | [ ] PENDING | |
| DB-010 | Precision monetaire 2 decimales | [ ] PENDING | |

### 3.3 Frontend

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| FE-001 | Route /purchases/suppliers accessible | [ ] PENDING | |
| FE-002 | Route /purchases/suppliers/new accessible | [ ] PENDING | |
| FE-003 | Route /purchases/suppliers/{id} accessible | [ ] PENDING | |
| FE-004 | Route /purchases/orders accessible | [ ] PENDING | |
| FE-005 | Route /purchases/orders/new accessible | [ ] PENDING | |
| FE-006 | Route /purchases/orders/{id} accessible | [ ] PENDING | |
| FE-007 | Route /purchases/invoices accessible | [ ] PENDING | |
| FE-008 | Route /purchases/invoices/new accessible | [ ] PENDING | |
| FE-009 | Route /purchases/invoices/{id} accessible | [ ] PENDING | |
| FE-010 | Formulaire creation fournisseur fonctionne | [ ] PENDING | |
| FE-011 | Formulaire creation commande fonctionne | [ ] PENDING | |
| FE-012 | Formulaire creation facture fonctionne | [ ] PENDING | |
| FE-013 | Boutons conditionnels selon RBAC | [ ] PENDING | |
| FE-014 | Messages erreur utilisateur | [ ] PENDING | |
| FE-015 | Responsive mobile | [ ] PENDING | |
| FE-016 | data-app-ready="true" respecte | [ ] PENDING | |

---

## 4. CHECKLIST SECURITE

### 4.1 RBAC

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| RBAC-001 | Admin peut creer fournisseur | [ ] PENDING | |
| RBAC-002 | Admin peut creer commande | [ ] PENDING | |
| RBAC-003 | Admin peut valider commande | [ ] PENDING | |
| RBAC-004 | Admin peut valider facture | [ ] PENDING | |
| RBAC-005 | Admin peut supprimer brouillon | [ ] PENDING | |
| RBAC-006 | Manager peut creer commande | [ ] PENDING | |
| RBAC-007 | Manager peut valider commande | [ ] PENDING | |
| RBAC-008 | Manager ne peut pas supprimer | [ ] PENDING | |
| RBAC-009 | User ne peut pas creer | [ ] PENDING | |
| RBAC-010 | User voit uniquement ses documents | [ ] PENDING | |
| RBAC-011 | Readonly ne peut rien modifier | [ ] PENDING | |
| RBAC-012 | Readonly peut consulter | [ ] PENDING | |

### 4.2 Isolation Tenant

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| TENANT-001 | tenant_id obligatoire creation | [ ] PENDING | |
| TENANT-002 | tenant_id filtre sur liste | [ ] PENDING | |
| TENANT-003 | tenant_id verifie sur detail | [ ] PENDING | |
| TENANT-004 | Acces cross-tenant refuse | [ ] PENDING | |
| TENANT-005 | Log tentative cross-tenant | [ ] PENDING | |

### 4.3 Validation Donnees

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| VAL-001 | supplier_id obligatoire | [ ] PENDING | |
| VAL-002 | supplier_id doit exister | [ ] PENDING | |
| VAL-003 | supplier appartient au tenant | [ ] PENDING | |
| VAL-004 | supplier doit etre APPROVED | [ ] PENDING | |
| VAL-005 | Au moins 1 ligne pour valider | [ ] PENDING | |
| VAL-006 | Total > 0 pour valider | [ ] PENDING | |
| VAL-007 | Numero non modifiable | [ ] PENDING | |
| VAL-008 | Status non modifiable directement | [ ] PENDING | |

---

## 5. CHECKLIST PERFORMANCE

### 5.1 Temps de Reponse

| ID | Critere | Seuil | Statut | Mesure |
|----|---------|-------|--------|--------|
| PERF-001 | Liste fournisseurs (100 items) | < 500ms | [ ] PENDING | |
| PERF-002 | Liste commandes (100 items) | < 500ms | [ ] PENDING | |
| PERF-003 | Liste factures (100 items) | < 500ms | [ ] PENDING | |
| PERF-004 | Detail commande (20 lignes) | < 200ms | [ ] PENDING | |
| PERF-005 | Creation commande | < 300ms | [ ] PENDING | |
| PERF-006 | Validation commande | < 500ms | [ ] PENDING | |
| PERF-007 | Conversion commande->facture | < 500ms | [ ] PENDING | |
| PERF-008 | Export CSV (1000 docs) | < 5s | [ ] PENDING | |

### 5.2 Charge

| ID | Critere | Seuil | Statut | Mesure |
|----|---------|-------|--------|--------|
| LOAD-001 | 100 utilisateurs simultanes | OK | [ ] PENDING | |
| LOAD-002 | 10 creations/seconde | OK | [ ] PENDING | |
| LOAD-003 | Database connections | < 80% pool | [ ] PENDING | |

---

## 6. CHECKLIST TESTS

### 6.1 Tests Unitaires Backend

| ID | Fichier Test | Couverture | Statut |
|----|--------------|------------|--------|
| UT-001 | test_supplier_service.py | X/X | [ ] PENDING |
| UT-002 | test_order_service.py | X/X | [ ] PENDING |
| UT-003 | test_invoice_service.py | X/X | [ ] PENDING |
| UT-004 | test_line_service.py | X/X | [ ] PENDING |
| UT-005 | test_numbering_service.py | X/X | [ ] PENDING |
| UT-006 | test_calculation_service.py | X/X | [ ] PENDING |

### 6.2 Tests Integration Backend

| ID | Fichier Test | Couverture | Statut |
|----|--------------|------------|--------|
| IT-001 | test_suppliers_api.py | X/X | [ ] PENDING |
| IT-002 | test_orders_api.py | X/X | [ ] PENDING |
| IT-003 | test_invoices_api.py | X/X | [ ] PENDING |
| IT-004 | test_conversion_api.py | X/X | [ ] PENDING |
| IT-005 | test_export_api.py | X/X | [ ] PENDING |

### 6.3 Tests E2E Frontend

| ID | Fichier Test | Couverture | Statut |
|----|--------------|------------|--------|
| E2E-001 | achats-v1.spec.ts | X/X | [ ] PENDING |
| E2E-002 | achats-v1-suppliers.spec.ts | X/X | [ ] PENDING |
| E2E-003 | achats-v1-orders.spec.ts | X/X | [ ] PENDING |
| E2E-004 | achats-v1-invoices.spec.ts | X/X | [ ] PENDING |
| E2E-005 | achats-v1-rbac.spec.ts | X/X | [ ] PENDING |

---

## 7. CHECKLIST E2E OBLIGATOIRES

### 7.1 Parcours Critiques

| ID | Parcours | Statut | Commentaire |
|----|----------|--------|-------------|
| E2E-P01 | Creation fournisseur | [ ] PENDING | |
| E2E-P02 | Creation commande fournisseur | [ ] PENDING | |
| E2E-P03 | Validation commande | [ ] PENDING | |
| E2E-P04 | Creation facture fournisseur | [ ] PENDING | |
| E2E-P05 | Creation facture depuis commande | [ ] PENDING | |
| E2E-P06 | Validation facture | [ ] PENDING | |
| E2E-P07 | Export CSV commandes | [ ] PENDING | |
| E2E-P08 | Export CSV factures | [ ] PENDING | |
| E2E-P09 | Acces refuse par role | [ ] PENDING | |
| E2E-P10 | Acces refuse autre tenant | [ ] PENDING | |

### 7.2 Regles E2E

| Regle | Description | Statut |
|-------|-------------|--------|
| data-app-ready="true" | Attendre indicateur avant action | [ ] PENDING |
| Aucun timeout arbitraire | Pas de sleeps/waits fixes | [ ] PENDING |
| Aucun mock backend | Tests sur vrai backend | [ ] PENDING |

---

## 8. CHECKLIST DOCUMENTATION

| ID | Document | Statut | Commentaire |
|----|----------|--------|-------------|
| DOC-001 | ACHATS_V1_SCOPE.md | [X] COMPLETE | Perimetre fonctionnel |
| DOC-002 | ACHATS_V1_DATA_MODEL.md | [X] COMPLETE | Modele de donnees |
| DOC-003 | ACHATS_V1_RBAC.md | [X] COMPLETE | Matrice permissions |
| DOC-004 | ACHATS_V1_PASS_FAIL_CHECKLIST.md | [X] COMPLETE | Ce document |
| DOC-005 | API Documentation (OpenAPI) | [ ] PENDING | Auto-genere |
| DOC-006 | Guide Utilisateur | [ ] PENDING | Pour beta testers |

---

## 9. CRITERES BLOQUANTS

### 9.1 Criteres FAIL Immediat

Si UN de ces criteres echoue, ACHATS V1 est **FAIL**:

| ID | Critere Bloquant | Justification |
|----|------------------|---------------|
| BLOCK-001 | Acces cross-tenant possible | Securite critique |
| BLOCK-002 | Document valide modifiable | Integrite donnees |
| BLOCK-003 | Calculs TVA incorrects | Legal/Comptable |
| BLOCK-004 | Numerotation avec trous | Tracabilite fiscal |
| BLOCK-005 | Fournisseur bloque utilisable | Integrite metier |
| BLOCK-006 | Tests unitaires < 100% | Qualite code |
| BLOCK-007 | Tests E2E < 100% | Experience utilisateur |
| BLOCK-008 | Performance > 2s | Utilisabilite |

### 9.2 Criteres WARNING

Ces criteres generent un WARNING mais n'empechent pas le PASS:

| ID | Critere Warning | Action |
|----|-----------------|--------|
| WARN-001 | Couverture code < 90% | Ameliorer avant V2 |
| WARN-002 | Accessibilite partielle | Ameliorer avant GA |
| WARN-003 | Documentation incomplete | Completer en beta |

---

## 10. PROCESSUS DE VALIDATION

### 10.1 Etapes de Validation

```
1. [ ] Code Review - Tous les PR merges
2. [ ] Tests Unitaires - 100% PASS
3. [ ] Tests Integration - 100% PASS
4. [ ] Tests E2E - 100% PASS (Chromium + Firefox)
5. [ ] Security Audit - 0 critical, 0 high
6. [ ] Performance Benchmark - Dans les seuils
7. [ ] Documentation Complete
8. [ ] QA Manual Testing - Scenario valides
9. [ ] Product Owner Validation
10. [ ] BETA ACTIVATION AUTORISEE
```

### 10.2 Signatures de Validation

| Role | Nom | Date | Signature |
|------|-----|------|-----------|
| Tech Lead | ____________ | ____/____/____ | ________ |
| QA Lead | ____________ | ____/____/____ | ________ |
| Security Lead | ____________ | ____/____/____ | ________ |
| Product Owner | ____________ | ____/____/____ | ________ |

---

## 11. STATUT FINAL

### 11.1 Resultat Global

| Categorie | PASS | FAIL | PENDING |
|-----------|------|------|---------|
| Fonctionnel (Fournisseurs) | 0 | 0 | 8 |
| Fonctionnel (Commandes) | 0 | 0 | 17 |
| Fonctionnel (Factures) | 0 | 0 | 22 |
| Fonctionnel (Lignes) | 0 | 0 | 10 |
| Technique (API) | 0 | 0 | 19 |
| Technique (DB) | 0 | 0 | 10 |
| Technique (Frontend) | 0 | 0 | 16 |
| Securite (RBAC) | 0 | 0 | 12 |
| Securite (Tenant) | 0 | 0 | 5 |
| Securite (Validation) | 0 | 0 | 8 |
| Performance | 0 | 0 | 11 |
| Tests | 0 | 0 | 11 |
| E2E Parcours | 0 | 0 | 10 |
| Documentation | 4 | 0 | 2 |
| **TOTAL** | **4** | **0** | **151** |

### 11.2 Decision Finale

```
[ ] PASS - ACHATS V1 PRET POUR ACTIVATION BETA
[ ] FAIL - CORRECTIONS REQUISES
[X] PENDING - EN ATTENTE D'IMPLEMENTATION
```

---

## 12. DEFINITION DE "TERMINE"

### 12.1 Critere Dirigeant

Le module ACHATS V1 est considere comme **TERMINE** uniquement si:

> Un dirigeant peut gerer ses achats du quotidien:
> - Sans saisie lourde
> - Sans jargon comptable
> - Sans outil externe
> - Avec une vision claire des engagements et des factures

### 12.2 Rapport Final

SI TOUS LES CRITERES SONT PASS:

➡️ Generer: `MODULE_ACHATS_V1_PASS_REPORT.md`

➡️ Declarer: "MODULE ACHATS - TERMINE & UTILISABLE DANS UN PRODUIT FINI"

SI AU MOINS UN CRITERE EST FAIL:

➡️ Generer: `MODULE_ACHATS_V1_FAIL_REPORT.md`

Le rapport FAIL doit contenir:
1. Fonctionnalite manquante
2. Impact dirigeant
3. Correction precise
4. Tests a ajouter
5. Conditions de revalidation

---

**Document de conception - Version 1.0**
**Date: 8 janvier 2026**
**Statut: CONCEPTION - PAS D'IMPLEMENTATION**
