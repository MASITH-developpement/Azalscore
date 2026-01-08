# MODULE VENTES T0 - PERIMETRE FONCTIONNEL

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

Le module **VENTES T0** est le premier niveau fonctionnel du sous-module
commercial de facturation. Il fournit les fonctionnalites minimales
pour creer des devis et factures simples.

### Objectif

Permettre aux utilisateurs beta de:
- Creer des devis simples
- Convertir des devis en factures
- Gerer des factures directes
- Suivre les statuts (brouillon/valide)

---

## 2. PERIMETRE INCLUS

### 2.1 Devis Simples (QUOTE)

| Fonctionnalite | Description | Statut |
|----------------|-------------|--------|
| Creation devis | Creer un devis avec client et lignes | INCLUS |
| Modification devis | Modifier un devis en brouillon | INCLUS |
| Suppression devis | Supprimer un devis brouillon | INCLUS |
| Validation devis | Passer de brouillon a valide | INCLUS |
| Liste devis | Afficher les devis du tenant | INCLUS |
| Numerotation | Numero automatique DEV-AAAA-XXXX | INCLUS |

### 2.2 Factures Simples (INVOICE)

| Fonctionnalite | Description | Statut |
|----------------|-------------|--------|
| Creation facture | Creer une facture directe | INCLUS |
| Depuis devis | Convertir devis valide en facture | INCLUS |
| Modification facture | Modifier une facture brouillon | INCLUS |
| Validation facture | Passer de brouillon a valide | INCLUS |
| Liste factures | Afficher les factures du tenant | INCLUS |
| Numerotation | Numero automatique FAC-AAAA-XXXX | INCLUS |

### 2.3 Lignes de Document

| Fonctionnalite | Description | Statut |
|----------------|-------------|--------|
| Ajout ligne | Ajouter une ligne produit/service | INCLUS |
| Modification ligne | Modifier quantite, prix, description | INCLUS |
| Suppression ligne | Supprimer une ligne | INCLUS |
| Calcul automatique | Total HT, TVA, TTC | INCLUS |

### 2.4 Statuts

| Statut | Code | Description |
|--------|------|-------------|
| Brouillon | DRAFT | Document en cours de redaction |
| Valide | VALIDATED | Document finalise et verrouille |

### 2.5 Export

| Fonctionnalite | Description | Statut |
|----------------|-------------|--------|
| Export CSV devis | Exporter la liste des devis | INCLUS |
| Export CSV factures | Exporter la liste des factures | INCLUS |

---

## 3. PERIMETRE EXCLU

### 3.1 Fonctionnalites Exclues (T1+)

| Fonctionnalite | Raison | Version Cible |
|----------------|--------|---------------|
| Avoirs | Complexite comptable | T1 |
| Commandes | Workflow intermediaire | T1 |
| Bons de livraison | Logistique | T1 |
| Pro forma | Usage limite | T1 |
| Paiements | Module Finance | M2 |
| Rappels automatiques | Automatisation | T2 |
| Export PDF | Generation PDF | T1 |
| Envoi email | Notification | T1 |
| Signature electronique | Legal | T2 |
| Multi-devise | Complexite | T2 |
| Remises en cascade | Calculs complexes | T1 |

### 3.2 Integrations Exclues

| Integration | Raison |
|-------------|--------|
| Comptabilite | Module M2 (Finance) |
| Stock | Module Inventaire |
| CRM Pipeline | Dependance Opportunites |
| Webhooks | Infrastructure |
| API externe | Securite |

---

## 4. DEPENDANCES

### 4.1 Dependances CRM T0

| Dependance | Type | Description |
|------------|------|-------------|
| Customer | OBLIGATOIRE | Un document doit etre lie a un client |
| Contact | OPTIONNEL | Un contact peut etre associe |

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
| Client obligatoire | Tout document doit avoir un client |
| Validation irreversible | Un document valide ne peut plus etre modifie |
| Suppression restreinte | Seuls les brouillons peuvent etre supprimes |
| Numerotation sequentielle | Les numeros ne doivent pas avoir de trous |

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
Format Devis:    DEV-{ANNEE}-{SEQUENCE}
Format Facture:  FAC-{ANNEE}-{SEQUENCE}

Exemples:
- DEV-2026-0001
- DEV-2026-0002
- FAC-2026-0001
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

### 6.3 Workflow

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
              v (Devis uniquement)
         +----------+
         | INVOICE  |
         +----------+
```

---

## 7. INTERFACE UTILISATEUR

### 7.1 Ecrans Prevus

| Ecran | Description | Route |
|-------|-------------|-------|
| Liste devis | Tableau des devis | /invoicing/quotes |
| Detail devis | Vue/Edition devis | /invoicing/quotes/{id} |
| Creation devis | Formulaire creation | /invoicing/quotes/new |
| Liste factures | Tableau des factures | /invoicing/invoices |
| Detail facture | Vue/Edition facture | /invoicing/invoices/{id} |
| Creation facture | Formulaire creation | /invoicing/invoices/new |

### 7.2 Actions UI

| Action | Role Minimum | Description |
|--------|--------------|-------------|
| Voir liste | readonly | Consulter la liste |
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

### 8.2 Risques Techniques

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Performance liste | MOYEN | Pagination obligatoire |
| Fuite inter-tenant | CRITIQUE | Triple validation tenant_id |
| Concurrence edition | MOYEN | Optimistic locking |

---

## 9. CRITERES D'ACCEPTATION

### 9.1 Fonctionnels

- [ ] CRUD complet devis (brouillon)
- [ ] CRUD complet factures (brouillon)
- [ ] Validation documents
- [ ] Conversion devis -> facture
- [ ] Numerotation sequentielle
- [ ] Calculs TVA corrects

### 9.2 Non-Fonctionnels

- [ ] Isolation tenant testee
- [ ] RBAC respecte
- [ ] Performance < 1s sur liste
- [ ] Tests E2E passent

---

## 10. HORS PERIMETRE EXPLICITE

Les elements suivants sont **EXPLICITEMENT EXCLUS** de VENTES T0:

1. ❌ Gestion des paiements
2. ❌ Avoirs et remboursements
3. ❌ Commandes
4. ❌ Bons de livraison
5. ❌ Generation PDF
6. ❌ Envoi par email
7. ❌ Rappels automatiques
8. ❌ Multi-devise
9. ❌ Escomptes
10. ❌ Acomptes

---

**Document de conception - Version 1.0**
**Date: 8 janvier 2026**
**Statut: CONCEPTION - PAS D'IMPLEMENTATION**
