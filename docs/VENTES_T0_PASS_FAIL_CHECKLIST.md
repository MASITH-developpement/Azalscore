# MODULE VENTES T0 - CHECKLIST PASS/FAIL

**Version**: 1.0 - CONCEPTION
**Date**: 8 janvier 2026
**Statut**: CONCEPTION - AUCUNE IMPLEMENTATION

---

## AVERTISSEMENT

> **CE DOCUMENT EST UNE CHECKLIST DE VALIDATION UNIQUEMENT.**
>
> Elle sera utilisee pour valider l'implementation future de VENTES T0.
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
| CRM T0 Module | PASS | **PASS** |
| RBAC System | OPERATIONNEL | **OPERATIONNEL** |
| Multi-tenant | VALIDE | **VALIDE** |
| Audit System | ACTIF | **ACTIF** |

---

## 2. CHECKLIST FONCTIONNELLE

### 2.1 Devis (QUOTE)

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| Q-001 | Creer un devis brouillon | [ ] PENDING | |
| Q-002 | Numero auto DEV-AAAA-XXXX | [ ] PENDING | |
| Q-003 | Associer un client existant | [ ] PENDING | |
| Q-004 | Ajouter des lignes au devis | [ ] PENDING | |
| Q-005 | Modifier les lignes | [ ] PENDING | |
| Q-006 | Supprimer des lignes | [ ] PENDING | |
| Q-007 | Calcul automatique HT/TVA/TTC | [ ] PENDING | |
| Q-008 | Modifier un devis brouillon | [ ] PENDING | |
| Q-009 | Supprimer un devis brouillon | [ ] PENDING | |
| Q-010 | Valider un devis (DRAFT->VALIDATED) | [ ] PENDING | |
| Q-011 | Devis valide non modifiable | [ ] PENDING | |
| Q-012 | Devis valide non supprimable | [ ] PENDING | |
| Q-013 | Liste des devis avec pagination | [ ] PENDING | |
| Q-014 | Filtrage par statut | [ ] PENDING | |
| Q-015 | Recherche par numero/client | [ ] PENDING | |
| Q-016 | Export CSV liste devis | [ ] PENDING | |

### 2.2 Factures (INVOICE)

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| I-001 | Creer une facture directe | [ ] PENDING | |
| I-002 | Numero auto FAC-AAAA-XXXX | [ ] PENDING | |
| I-003 | Associer un client existant | [ ] PENDING | |
| I-004 | Creer facture depuis devis valide | [ ] PENDING | |
| I-005 | Copie lignes devis vers facture | [ ] PENDING | |
| I-006 | Lien parent_id devis -> facture | [ ] PENDING | |
| I-007 | Ajouter des lignes a la facture | [ ] PENDING | |
| I-008 | Modifier les lignes | [ ] PENDING | |
| I-009 | Supprimer des lignes | [ ] PENDING | |
| I-010 | Calcul automatique HT/TVA/TTC | [ ] PENDING | |
| I-011 | Modifier une facture brouillon | [ ] PENDING | |
| I-012 | Supprimer une facture brouillon | [ ] PENDING | |
| I-013 | Valider une facture (DRAFT->VALIDATED) | [ ] PENDING | |
| I-014 | Facture validee non modifiable | [ ] PENDING | |
| I-015 | Facture validee non supprimable | [ ] PENDING | |
| I-016 | Liste des factures avec pagination | [ ] PENDING | |
| I-017 | Filtrage par statut | [ ] PENDING | |
| I-018 | Recherche par numero/client | [ ] PENDING | |
| I-019 | Export CSV liste factures | [ ] PENDING | |

### 2.3 Lignes de Document

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
| API-001 | GET /api/v1/invoicing/quotes | [ ] PENDING | |
| API-002 | GET /api/v1/invoicing/quotes/{id} | [ ] PENDING | |
| API-003 | POST /api/v1/invoicing/quotes | [ ] PENDING | |
| API-004 | PUT /api/v1/invoicing/quotes/{id} | [ ] PENDING | |
| API-005 | DELETE /api/v1/invoicing/quotes/{id} | [ ] PENDING | |
| API-006 | POST /api/v1/invoicing/quotes/{id}/validate | [ ] PENDING | |
| API-007 | POST /api/v1/invoicing/quotes/{id}/convert | [ ] PENDING | |
| API-008 | GET /api/v1/invoicing/invoices | [ ] PENDING | |
| API-009 | GET /api/v1/invoicing/invoices/{id} | [ ] PENDING | |
| API-010 | POST /api/v1/invoicing/invoices | [ ] PENDING | |
| API-011 | PUT /api/v1/invoicing/invoices/{id} | [ ] PENDING | |
| API-012 | DELETE /api/v1/invoicing/invoices/{id} | [ ] PENDING | |
| API-013 | POST /api/v1/invoicing/invoices/{id}/validate | [ ] PENDING | |
| API-014 | GET /api/v1/invoicing/quotes/export | [ ] PENDING | |
| API-015 | GET /api/v1/invoicing/invoices/export | [ ] PENDING | |

### 3.2 Base de Donnees

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| DB-001 | Table commercial_documents existe | [ ] PENDING | |
| DB-002 | Table document_lines existe | [ ] PENDING | |
| DB-003 | Index tenant_id performant | [ ] PENDING | |
| DB-004 | Index numero unique | [ ] PENDING | |
| DB-005 | FK customer_id valide | [ ] PENDING | |
| DB-006 | CASCADE delete lignes | [ ] PENDING | |
| DB-007 | Precision monetaire 2 decimales | [ ] PENDING | |

### 3.3 Frontend

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| FE-001 | Route /invoicing/quotes accessible | [ ] PENDING | |
| FE-002 | Route /invoicing/quotes/new accessible | [ ] PENDING | |
| FE-003 | Route /invoicing/quotes/{id} accessible | [ ] PENDING | |
| FE-004 | Route /invoicing/invoices accessible | [ ] PENDING | |
| FE-005 | Route /invoicing/invoices/new accessible | [ ] PENDING | |
| FE-006 | Route /invoicing/invoices/{id} accessible | [ ] PENDING | |
| FE-007 | Formulaire creation devis fonctionne | [ ] PENDING | |
| FE-008 | Formulaire creation facture fonctionne | [ ] PENDING | |
| FE-009 | Boutons conditionnels selon RBAC | [ ] PENDING | |
| FE-010 | Messages erreur utilisateur | [ ] PENDING | |
| FE-011 | Responsive mobile | [ ] PENDING | |
| FE-012 | Accessibilite WCAG 2.1 AA | [ ] PENDING | |

---

## 4. CHECKLIST SECURITE

### 4.1 RBAC

| ID | Critere | Statut | Commentaire |
|----|---------|--------|-------------|
| RBAC-001 | Admin peut creer devis | [ ] PENDING | |
| RBAC-002 | Admin peut valider devis | [ ] PENDING | |
| RBAC-003 | Admin peut supprimer brouillon | [ ] PENDING | |
| RBAC-004 | Manager peut creer devis | [ ] PENDING | |
| RBAC-005 | Manager ne peut pas supprimer | [ ] PENDING | |
| RBAC-006 | User ne peut pas creer devis | [ ] PENDING | |
| RBAC-007 | User voit uniquement ses documents | [ ] PENDING | |
| RBAC-008 | Readonly ne peut rien modifier | [ ] PENDING | |
| RBAC-009 | Readonly peut consulter | [ ] PENDING | |

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
| VAL-001 | customer_id obligatoire | [ ] PENDING | |
| VAL-002 | customer_id doit exister | [ ] PENDING | |
| VAL-003 | customer appartient au tenant | [ ] PENDING | |
| VAL-004 | Au moins 1 ligne pour valider | [ ] PENDING | |
| VAL-005 | Total > 0 pour valider | [ ] PENDING | |
| VAL-006 | Numero non modifiable | [ ] PENDING | |
| VAL-007 | Status non modifiable directement | [ ] PENDING | |

---

## 5. CHECKLIST PERFORMANCE

### 5.1 Temps de Reponse

| ID | Critere | Seuil | Statut | Mesure |
|----|---------|-------|--------|--------|
| PERF-001 | Liste devis (100 items) | < 500ms | [ ] PENDING | |
| PERF-002 | Detail devis (20 lignes) | < 200ms | [ ] PENDING | |
| PERF-003 | Creation devis | < 300ms | [ ] PENDING | |
| PERF-004 | Validation devis | < 500ms | [ ] PENDING | |
| PERF-005 | Conversion devis->facture | < 500ms | [ ] PENDING | |
| PERF-006 | Export CSV (1000 docs) | < 5s | [ ] PENDING | |

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
| UT-001 | test_quote_service.py | X/X | [ ] PENDING |
| UT-002 | test_invoice_service.py | X/X | [ ] PENDING |
| UT-003 | test_document_line_service.py | X/X | [ ] PENDING |
| UT-004 | test_numbering_service.py | X/X | [ ] PENDING |
| UT-005 | test_calculation_service.py | X/X | [ ] PENDING |

### 6.2 Tests Integration Backend

| ID | Fichier Test | Couverture | Statut |
|----|--------------|------------|--------|
| IT-001 | test_quotes_api.py | X/X | [ ] PENDING |
| IT-002 | test_invoices_api.py | X/X | [ ] PENDING |
| IT-003 | test_conversion_api.py | X/X | [ ] PENDING |
| IT-004 | test_export_api.py | X/X | [ ] PENDING |

### 6.3 Tests E2E Frontend

| ID | Fichier Test | Couverture | Statut |
|----|--------------|------------|--------|
| E2E-001 | ventes-t0.spec.ts | X/X | [ ] PENDING |
| E2E-002 | ventes-t0-quotes.spec.ts | X/X | [ ] PENDING |
| E2E-003 | ventes-t0-invoices.spec.ts | X/X | [ ] PENDING |
| E2E-004 | ventes-t0-rbac.spec.ts | X/X | [ ] PENDING |

---

## 7. CHECKLIST DOCUMENTATION

| ID | Document | Statut | Commentaire |
|----|----------|--------|-------------|
| DOC-001 | VENTES_T0_SCOPE.md | [ ] COMPLETE | Perimetre fonctionnel |
| DOC-002 | VENTES_T0_DATA_MODEL.md | [ ] COMPLETE | Modele de donnees |
| DOC-003 | VENTES_T0_RBAC.md | [ ] COMPLETE | Matrice permissions |
| DOC-004 | VENTES_T0_PASS_FAIL_CHECKLIST.md | [ ] COMPLETE | Ce document |
| DOC-005 | API Documentation (OpenAPI) | [ ] PENDING | Auto-genere |
| DOC-006 | Guide Utilisateur | [ ] PENDING | Pour beta testers |

---

## 8. CRITERES BLOQUANTS

### 8.1 Criteres FAIL Immediat

Si UN de ces criteres echoue, VENTES T0 est **FAIL**:

| ID | Critere Bloquant | Justification |
|----|------------------|---------------|
| BLOCK-001 | Acces cross-tenant possible | Securite critique |
| BLOCK-002 | Document valide modifiable | Integrite donnees |
| BLOCK-003 | Calculs TVA incorrects | Legal/Comptable |
| BLOCK-004 | Numerotation avec trous | Tracabilite fiscal |
| BLOCK-005 | Tests unitaires < 100% | Qualite code |
| BLOCK-006 | Tests E2E < 100% | Experience utilisateur |
| BLOCK-007 | Performance > 2s | Utilisabilite |

### 8.2 Criteres WARNING

Ces criteres generent un WARNING mais n'empechent pas le PASS:

| ID | Critere Warning | Action |
|----|-----------------|--------|
| WARN-001 | Couverture code < 90% | Ameliorer avant T1 |
| WARN-002 | Accessibilite partielle | Ameliorer avant GA |
| WARN-003 | Documentation incomplete | Completer en beta |

---

## 9. PROCESSUS DE VALIDATION

### 9.1 Etapes de Validation

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

### 9.2 Signatures de Validation

| Role | Nom | Date | Signature |
|------|-----|------|-----------|
| Tech Lead | ____________ | ____/____/____ | ________ |
| QA Lead | ____________ | ____/____/____ | ________ |
| Security Lead | ____________ | ____/____/____ | ________ |
| Product Owner | ____________ | ____/____/____ | ________ |

---

## 10. STATUT FINAL

### 10.1 Resultat Global

| Categorie | PASS | FAIL | PENDING |
|-----------|------|------|---------|
| Fonctionnel | 0 | 0 | 35 |
| Technique | 0 | 0 | 24 |
| Securite | 0 | 0 | 16 |
| Performance | 0 | 0 | 9 |
| Tests | 0 | 0 | 8 |
| Documentation | 4 | 0 | 2 |
| **TOTAL** | **4** | **0** | **94** |

### 10.2 Decision Finale

```
[ ] PASS - VENTES T0 PRET POUR ACTIVATION BETA
[ ] FAIL - CORRECTIONS REQUISES
[X] PENDING - EN ATTENTE D'IMPLEMENTATION
```

---

**Document de conception - Version 1.0**
**Date: 8 janvier 2026**
**Statut: CONCEPTION - PAS D'IMPLEMENTATION**
