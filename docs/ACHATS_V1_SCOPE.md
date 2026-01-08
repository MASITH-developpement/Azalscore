# MODULE ACHATS V1 - PERIMETRE FONCTIONNEL

**Version**: 1.0 - CONCEPTION
**Date**: 8 janvier 2026
**Statut**: CONCEPTION - AUCUNE IMPLEMENTATION

---

## AVERTISSEMENT

> **CE DOCUMENT EST UNE CONCEPTION UNIQUEMENT.**
>
> AUCUN code production n'est autorise.
> AUCUNE activation n'est prevue.
> AUCUN endpoint n'est expose.

---

## 1. RESUME EXECUTIF

Le module **ACHATS V1** est le premier niveau fonctionnel du sous-module
gestion des achats. Il permet au dirigeant de gerer ses achats du quotidien
sans saisie lourde, sans jargon comptable, et sans outil externe.

### Objectif

Permettre aux utilisateurs de:
- Gerer leurs fournisseurs
- Creer et valider des commandes fournisseurs
- Creer et valider des factures fournisseurs
- Avoir une vision claire des engagements

### Vision Dirigeant

> "Je veux voir mes engagements fournisseurs et saisir mes factures
> d'achat en moins de 2 minutes, sans formation comptable."

---

## 2. PERIMETRE INCLUS

### 2.1 Fournisseurs (SUPPLIER)

| Fonctionnalite | Description | Statut |
|----------------|-------------|--------|
| Creation fournisseur | Creer un fournisseur avec infos de base | INCLUS |
| Modification fournisseur | Modifier un fournisseur existant | INCLUS |
| Consultation fournisseur | Voir les details d'un fournisseur | INCLUS |
| Liste fournisseurs | Afficher les fournisseurs du tenant | INCLUS |
| Code unique | Code automatique par tenant | INCLUS |
| Statuts fournisseur | APPROVED, BLOCKED, etc. | INCLUS |

### 2.2 Commandes Fournisseurs (PURCHASE_ORDER)

| Fonctionnalite | Description | Statut |
|----------------|-------------|--------|
| Creation commande | Creer une commande avec fournisseur et lignes | INCLUS |
| Modification commande | Modifier une commande brouillon | INCLUS |
| Suppression commande | Supprimer une commande brouillon | INCLUS |
| Validation commande | Passer de DRAFT a VALIDATED | INCLUS |
| Liste commandes | Afficher les commandes du tenant | INCLUS |
| Numerotation | Numero automatique CMD-AAAA-XXXX | INCLUS |

### 2.3 Factures Fournisseurs (PURCHASE_INVOICE)

| Fonctionnalite | Description | Statut |
|----------------|-------------|--------|
| Creation facture | Creer une facture directe | INCLUS |
| Depuis commande | Creer facture depuis commande validee | INCLUS |
| Modification facture | Modifier une facture brouillon | INCLUS |
| Suppression facture | Supprimer une facture brouillon | INCLUS |
| Validation facture | Passer de DRAFT a VALIDATED | INCLUS |
| Liste factures | Afficher les factures du tenant | INCLUS |
| Numerotation | Numero automatique FAF-AAAA-XXXX | INCLUS |
| Reference fournisseur | Saisie numero facture fournisseur | INCLUS |

### 2.4 Lignes de Document

| Fonctionnalite | Description | Statut |
|----------------|-------------|--------|
| Ajout ligne | Ajouter une ligne produit/service | INCLUS |
| Modification ligne | Modifier quantite, prix, description | INCLUS |
| Suppression ligne | Supprimer une ligne | INCLUS |
| Calcul automatique | Total HT, TVA, TTC | INCLUS |

### 2.5 Statuts Documents

| Statut | Code | Description |
|--------|------|-------------|
| Brouillon | DRAFT | Document en cours de redaction |
| Valide | VALIDATED | Document finalise et verrouille |

### 2.6 Export

| Fonctionnalite | Description | Statut |
|----------------|-------------|--------|
| Export CSV commandes | Exporter la liste des commandes | INCLUS |
| Export CSV factures | Exporter la liste des factures fournisseurs | INCLUS |

---

## 3. PERIMETRE EXCLU

### 3.1 Fonctionnalites Exclues (V2+)

| Fonctionnalite | Raison | Version Cible |
|----------------|--------|---------------|
| Demandes d'achat | Workflow complexe | V2 |
| Devis fournisseurs | Workflow intermediaire | V2 |
| Receptions | Logistique | V2 |
| Paiements | Module Finance | M2 |
| Multi-devise | Complexite | V2 |
| Comptabilite | Ecritures | M2 |
| Export PDF | Generation PDF | V2 |
| Envoi email | Notification | V2 |
| Rapprochement bancaire | Finance | M2 |
| Evaluation fournisseurs | QC avance | V2 |

### 3.2 Integrations Exclues

| Integration | Raison |
|-------------|--------|
| Comptabilite generale | Module M2 (Finance) |
| Stock/Inventaire | Module Inventaire |
| Tresorerie | Module Finance |
| Webhooks | Infrastructure |
| API externe | Securite |

---

## 4. DEPENDANCES

### 4.1 Aucune Dependance Externe

Le module ACHATS V1 est **autonome**:

| Element | Type | Description |
|---------|------|-------------|
| Fournisseurs | PROPRE | Gestion propre des fournisseurs |
| Commandes | PROPRE | Documents commandes internes |
| Factures | PROPRE | Documents factures internes |

### 4.2 Dependances Techniques

| Dependance | Type | Description |
|------------|------|-------------|
| tenant_id | OBLIGATOIRE | Isolation multi-tenant |
| RBAC | OBLIGATOIRE | Controle des permissions |
| Audit | OBLIGATOIRE | Tracabilite des actions |

---

## 5. CONTRAINTES

### 5.1 Contraintes Metier

| Contrainte | Description |
|------------|-------------|
| Fournisseur obligatoire | Tout document doit avoir un fournisseur |
| Validation irreversible | Un document valide ne peut plus etre modifie |
| Suppression restreinte | Seuls les brouillons peuvent etre supprimes |
| Numerotation sequentielle | Les numeros ne doivent pas avoir de trous |
| Reference facture unique | Pas de doublon numero facture fournisseur |

### 5.2 Contraintes Techniques

| Contrainte | Description |
|------------|-------------|
| tenant_id obligatoire | Toutes les tables/queries filtrees |
| Precision monetaire | 2 decimales pour les montants |
| TVA configurable | Taux par defaut: 20% |

---

## 6. REGLES DE GESTION

### 6.1 Numerotation

```
Format Commande:     CMD-{ANNEE}-{SEQUENCE}
Format Facture:      FAF-{ANNEE}-{SEQUENCE}

Exemples:
- CMD-2026-0001
- CMD-2026-0002
- FAF-2026-0001
```

### 6.2 Calculs

```
Ligne:
  subtotal = quantity * unit_price * (1 - discount_percent / 100)
  tax_amount = subtotal * (tax_rate / 100)
  total = subtotal + tax_amount

Document:
  subtotal = SUM(lignes.subtotal)
  tax_amount = SUM(lignes.tax_amount)
  total = subtotal + tax_amount
```

### 6.3 Workflow Commande

```
         +----------+
         | DRAFT    |
         +----------+
              |
              v
         +----------+
         | VALIDATED|
         +----------+
              |
              v (optionnel)
         +----------+
         | INVOICE  |
         +----------+
```

### 6.4 Workflow Facture

```
         +----------+
         | DRAFT    |
         +----------+
              |
              v
         +----------+
         | VALIDATED|
         +----------+
```

---

## 7. INTERFACE UTILISATEUR

### 7.1 Ecrans Prevus

| Ecran | Description | Route |
|-------|-------------|-------|
| Liste fournisseurs | Tableau des fournisseurs | /purchases/suppliers |
| Detail fournisseur | Vue/Edition fournisseur | /purchases/suppliers/{id} |
| Creation fournisseur | Formulaire creation | /purchases/suppliers/new |
| Liste commandes | Tableau des commandes | /purchases/orders |
| Detail commande | Vue/Edition commande | /purchases/orders/{id} |
| Creation commande | Formulaire creation | /purchases/orders/new |
| Liste factures | Tableau des factures | /purchases/invoices |
| Detail facture | Vue/Edition facture | /purchases/invoices/{id} |
| Creation facture | Formulaire creation | /purchases/invoices/new |

### 7.2 Actions UI - Menu du Haut

| Action | Description | Permission |
|--------|-------------|------------|
| + Commande fournisseur | Creation rapide | purchases.create |
| + Facture fournisseur | Creation rapide | purchases.create |

### 7.3 Actions UI - Role Minimum

| Action | Role Minimum | Description |
|--------|--------------|-------------|
| Voir liste | readonly | Consulter les listes |
| Voir detail | readonly | Consulter un document |
| Creer | user | Creer un nouveau document |
| Modifier | user | Modifier un brouillon |
| Valider | manager | Valider un document |
| Supprimer | admin | Supprimer un brouillon |

---

## 8. RISQUES IDENTIFIES

### 8.1 Risques Fonctionnels

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Numerotation duplicata | ELEVE | Sequence atomique par tenant |
| Modification post-validation | ELEVE | Verrou status dans service |
| Calculs TVA incorrects | MOYEN | Tests unitaires exhaustifs |
| Doublon facture fournisseur | MOYEN | Controle unicite ref |

### 8.2 Risques Techniques

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Performance liste | MOYEN | Pagination obligatoire |
| Fuite inter-tenant | CRITIQUE | Triple validation tenant_id |
| Concurrence edition | MOYEN | Optimistic locking |

---

## 9. CRITERES D'ACCEPTATION

### 9.1 Fonctionnels

- [ ] CRUD complet fournisseurs
- [ ] CRUD complet commandes (brouillon)
- [ ] CRUD complet factures (brouillon)
- [ ] Validation documents
- [ ] Conversion commande -> facture
- [ ] Numerotation sequentielle
- [ ] Calculs TVA corrects
- [ ] Export CSV

### 9.2 Non-Fonctionnels

- [ ] Isolation tenant testee
- [ ] RBAC respecte
- [ ] Performance < 1s sur liste
- [ ] Tests E2E passent a 100%

---

## 10. HORS PERIMETRE EXPLICITE

Les elements suivants sont **EXPLICITEMENT EXCLUS** de ACHATS V1:

1. Demandes d'achat (requisitions)
2. Devis fournisseurs (quotations)
3. Receptions de marchandises
4. Paiements fournisseurs
5. Comptabilite / Ecritures
6. Rapprochement bancaire
7. Generation PDF
8. Envoi par email
9. Multi-devise
10. Evaluation fournisseurs

---

## 11. DEFINITION DE "TERMINE"

Le module ACHATS V1 est considere comme **TERMINE** uniquement si:

> Un dirigeant peut gerer ses achats du quotidien:
> - Sans saisie lourde
> - Sans jargon comptable
> - Sans outil externe
> - Avec une vision claire des engagements et des factures

---

**Document de conception - Version 1.0**
**Date: 8 janvier 2026**
**Statut: CONCEPTION - PAS D'IMPLEMENTATION**
