# AZALSCORE - Guide Utilisateur Module CRM T0

**Version:** 1.0.0
**Date:** 8 janvier 2026
**Statut:** VALIDÉ (PASS)

---

## Table des matières

1. [Présentation](#1-présentation)
2. [Fonctionnalités disponibles](#2-fonctionnalités-disponibles)
3. [Gestion des Clients](#3-gestion-des-clients)
4. [Gestion des Contacts](#4-gestion-des-contacts)
5. [Gestion des Opportunités](#5-gestion-des-opportunités)
6. [Historique des activités](#6-historique-des-activités)
7. [Export CSV](#7-export-csv)
8. [Sécurité et Droits](#8-sécurité-et-droits)
9. [Limitations connues](#9-limitations-connues)

---

## 1. Présentation

Le module **CRM T0** est le premier module métier d'AZALSCORE. Il fournit les fonctionnalités essentielles de gestion de la relation client (CRM) dans un environnement multi-tenant sécurisé.

### Périmètre CRM T0

Le module CRM T0 offre un périmètre fonctionnel **strict et validé** :

| Fonctionnalité | Statut |
|----------------|--------|
| Gestion des clients (CRUD) | ✅ Disponible |
| Gestion des contacts | ✅ Disponible |
| Opportunités simples | ✅ Disponible |
| Historique basique | ✅ Disponible |
| Export CSV | ✅ Disponible |
| Automatisations | ❌ Non disponible (T1+) |
| Scoring avancé | ❌ Non disponible (T1+) |
| Intelligence artificielle | ❌ Non disponible (T1+) |
| Synchronisations externes | ❌ Non disponible (T1+) |

---

## 2. Fonctionnalités disponibles

### Vue d'ensemble des API

Base URL: `/v1/commercial/`

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/customers` | GET | Liste des clients |
| `/customers` | POST | Créer un client |
| `/customers/{id}` | GET | Détail d'un client |
| `/customers/{id}` | PUT | Modifier un client |
| `/customers/{id}` | DELETE | Supprimer un client |
| `/contacts` | GET/POST | Gestion des contacts |
| `/contacts/{id}` | GET/PUT/DELETE | Contact spécifique |
| `/opportunities` | GET/POST | Gestion des opportunités |
| `/opportunities/{id}` | GET/PUT | Opportunité spécifique |
| `/opportunities/{id}/win` | POST | Marquer comme gagnée |
| `/opportunities/{id}/lose` | POST | Marquer comme perdue |
| `/activities` | GET/POST | Historique d'activités |
| `/export/customers` | GET | Export CSV clients |
| `/export/contacts` | GET | Export CSV contacts |
| `/export/opportunities` | GET | Export CSV opportunités |

---

## 3. Gestion des Clients

### Créer un client

```bash
POST /v1/commercial/customers
X-Tenant-ID: votre-tenant
Authorization: Bearer <token>

{
  "code": "CLI001",
  "name": "Entreprise Exemple SA",
  "type": "PROSPECT",
  "email": "contact@exemple.com",
  "phone": "0123456789",
  "city": "Paris",
  "country_code": "FR"
}
```

### Types de clients

| Type | Description |
|------|-------------|
| `PROSPECT` | Contact initial, pas encore qualifié |
| `LEAD` | Prospect qualifié avec intérêt |
| `CUSTOMER` | Client avec au moins une commande |
| `VIP` | Client privilégié |
| `PARTNER` | Partenaire commercial |
| `CHURNED` | Client perdu |

### Liste des clients avec filtres

```bash
GET /v1/commercial/customers?type=CUSTOMER&is_active=true&search=exemple&page=1&page_size=20
```

### Convertir un prospect en client

```bash
POST /v1/commercial/customers/{customer_id}/convert
```

---

## 4. Gestion des Contacts

### Créer un contact

```bash
POST /v1/commercial/contacts

{
  "customer_id": "uuid-du-client",
  "first_name": "Jean",
  "last_name": "Dupont",
  "email": "jean.dupont@exemple.com",
  "job_title": "Directeur Commercial",
  "is_primary": true,
  "is_decision_maker": true
}
```

### Attributs spéciaux

| Attribut | Description |
|----------|-------------|
| `is_primary` | Contact principal du client |
| `is_billing` | Contact pour la facturation |
| `is_shipping` | Contact pour les livraisons |
| `is_decision_maker` | Décideur dans le processus d'achat |

---

## 5. Gestion des Opportunités

### Créer une opportunité

```bash
POST /v1/commercial/opportunities

{
  "customer_id": "uuid-du-client",
  "code": "OPP-2026-001",
  "name": "Projet ERP",
  "amount": 50000.00,
  "probability": 30,
  "status": "NEW",
  "expected_close_date": "2026-03-31"
}
```

### Statuts des opportunités

| Statut | Description | Probabilité typique |
|--------|-------------|---------------------|
| `NEW` | Nouvelle opportunité | 10% |
| `QUALIFIED` | Besoin qualifié | 25% |
| `PROPOSAL` | Devis envoyé | 50% |
| `NEGOTIATION` | En négociation | 75% |
| `WON` | Gagnée | 100% |
| `LOST` | Perdue | 0% |

### Calcul du montant pondéré

Le montant pondéré est calculé automatiquement :

```
Montant pondéré = Montant × (Probabilité / 100)
```

Exemple : 50 000 € à 30% = 15 000 € pondéré

### Marquer une opportunité comme gagnée

```bash
POST /v1/commercial/opportunities/{opp_id}/win

{
  "reason": "Meilleure offre technique"
}
```

### Marquer une opportunité comme perdue

```bash
POST /v1/commercial/opportunities/{opp_id}/lose

{
  "reason": "Budget insuffisant"
}
```

---

## 6. Historique des activités

### Types d'activités

| Type | Description |
|------|-------------|
| `CALL` | Appel téléphonique |
| `EMAIL` | Email envoyé/reçu |
| `MEETING` | Réunion |
| `TASK` | Tâche à effectuer |
| `NOTE` | Note interne |
| `FOLLOW_UP` | Relance |

### Créer une activité

```bash
POST /v1/commercial/activities

{
  "customer_id": "uuid-du-client",
  "type": "CALL",
  "subject": "Appel de qualification",
  "description": "Discussion sur les besoins..."
}
```

### Marquer comme terminée

```bash
POST /v1/commercial/activities/{activity_id}/complete
```

---

## 7. Export CSV

### Exporter les clients

```bash
GET /v1/commercial/export/customers?type=CUSTOMER&is_active=true
```

Retourne un fichier CSV avec séparateur `;` contenant :
- Code, Nom, Type, Email, Téléphone, etc.

### Exporter les contacts

```bash
GET /v1/commercial/export/contacts?customer_id=uuid-optionnel
```

### Exporter les opportunités

```bash
GET /v1/commercial/export/opportunities?status=WON
```

**Important** : Les exports sont **strictement filtrés par tenant**. Un tenant ne peut exporter que ses propres données.

---

## 8. Sécurité et Droits

### Isolation Multi-Tenant

AZALSCORE garantit une isolation stricte entre tenants :

1. **Header obligatoire** : `X-Tenant-ID` requis sur toutes les requêtes
2. **Validation JWT** : Le token contient le tenant_id
3. **Filtrage SQL** : Toutes les requêtes filtrent par tenant_id

**Garantie** : Aucune donnée cross-tenant n'est accessible.

### Matrice des droits RBAC

| Action | Admin | Manager | User | Readonly |
|--------|-------|---------|------|----------|
| Lire clients | ✅ | ✅ | ✅ | ✅ |
| Créer clients | ✅ | ✅ | ✅ | ❌ |
| Modifier clients | ✅ | ✅ | Limité | ❌ |
| Supprimer clients | ✅ | ❌ | ❌ | ❌ |
| Export CSV | ✅ | ✅ | Limité | ❌ |

### Authentification

```bash
# Obtenir un token
POST /v1/auth/login
Content-Type: application/json

{
  "email": "utilisateur@exemple.com",
  "password": "motdepasse",
  "tenant_id": "votre-tenant"
}

# Utiliser le token
GET /v1/commercial/customers
Authorization: Bearer <token>
X-Tenant-ID: votre-tenant
```

---

## 9. Limitations connues

### Limitations CRM T0 (Version Bêta)

| Limitation | Description |
|------------|-------------|
| Pas d'automatisations | Les workflows automatiques ne sont pas disponibles |
| Pas de scoring IA | Le lead scoring automatique sera ajouté en T1 |
| Pas d'intégrations | Pas de sync Mailchimp, HubSpot, etc. |
| Pipeline basique | Les étapes sont fixes, pas personnalisables |
| Pas de rapports avancés | Exports CSV uniquement |

### Limites techniques bêta

| Paramètre | Limite |
|-----------|--------|
| Clients par tenant | 10 000 |
| Contacts par client | 100 |
| Opportunités actives | 1 000 |
| Export CSV max lignes | 10 000 |

### Prochaines versions

- **T1** : Scoring automatique, workflows basiques
- **T2** : Intégrations email, pipeline personnalisable
- **GA** : Version production complète

---

## Support

En cas de problème :
1. Vérifiez le header `X-Tenant-ID`
2. Vérifiez l'expiration de votre token JWT
3. Consultez les logs dans `/v1/audit/logs`

Pour signaler un bug : https://github.com/anthropics/claude-code/issues

---

**Document validé le 8 janvier 2026**
**Module CRM T0 : PASS**
