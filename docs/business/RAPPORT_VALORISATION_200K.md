# RAPPORT DE VALORISATION
## AZALSCORE ERP DECISIONNEL

**Date**: 13 Fevrier 2026
**Version**: 1.0
**Confidentialite**: Confidentiel - Usage interne

---

## RESUME EXECUTIF

| Critere | Valeur |
|---------|--------|
| **Nom du produit** | AZALSCORE |
| **Type** | ERP SaaS Multi-tenant Decisionnel |
| **Cible** | PME/TPE francaises |
| **Valorisation proposee** | 200,000 EUR |
| **Methode** | Cout de remplacement + Potentiel ARR |

---

## 1. PRESENTATION DU PRODUIT

### 1.1 Vision

AZALSCORE est un ERP SaaS francais qui se differencie par son approche
**decisionnelle native**. La ou les ERP traditionnels se contentent de stocker
des transactions, AZALSCORE transforme ces donnees en intelligence business.

### 1.2 Stack Technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Python 3.11, FastAPI, SQLAlchemy |
| Frontend | React 18, TypeScript, TanStack Query |
| Base de donnees | PostgreSQL 15 |
| Cache | Redis |
| Deploiement | Docker, Kubernetes-ready |
| CI/CD | GitHub Actions |

### 1.3 Metriques Code

| Metrique | Valeur |
|----------|--------|
| Lignes de code backend | ~45,000 |
| Lignes de code frontend | ~38,000 |
| Couverture tests | >75% |
| Modules metier | 12 |
| Endpoints API | 180+ |

---

## 2. ACTIFS LOGICIELS

### 2.1 Core SaaS Multi-tenant

**Description**: Architecture complete permettant d'heberger plusieurs clients
sur une meme instance avec isolation totale des donnees.

**Caracteristiques**:
- Isolation par `tenant_id` sur toutes les tables
- Authentification JWT avec refresh tokens
- RBAC granulaire (roles et permissions)
- Audit trail complet

**Cout de developpement estime**: 40,000 EUR

### 2.2 Modules Metier

| Module | Fonctionnalites | Cout estime |
|--------|-----------------|-------------|
| CRM | Clients, prospects, pipeline, scoring | 8,000 EUR |
| Ventes | Devis, commandes, factures, avoirs | 10,000 EUR |
| Achats | Fournisseurs, commandes, receptions | 8,000 EUR |
| Affaires | Projets, budgets, suivi rentabilite | 7,000 EUR |
| Stock | Mouvements, inventaires, valorisation | 6,000 EUR |
| Tresorerie | Banques, rapprochements, previsions | 5,000 EUR |
| Comptabilite | Journaux, grand livre, balances | 8,000 EUR |
| RH | Employes, contrats, absences | 5,000 EUR |
| **Total modules** | | **57,000 EUR** |

### 2.3 Cockpit Decisional

**Description**: Tableau de bord centralisant les KPIs strategiques
avec alertes intelligentes et suivi des decisions.

**Fonctionnalites**:
- Dashboard temps reel
- 5 KPIs strategiques (cf. section 3)
- Systeme d'alertes avec acquittement
- Historique des decisions

**Cout de developpement estime**: 20,000 EUR

### 2.4 Module BI Natif

**Description**: Outil d'analyse integre permettant des requetes SQL
directes sur les donnees metier.

**Fonctionnalites**:
- Editeur SQL avec autocompletion
- Visualisations (graphiques, tableaux)
- Sauvegarde et partage de rapports
- Export multi-format

**Cout de developpement estime**: 25,000 EUR

### 2.5 API RESTful

**Description**: API complete documentee OpenAPI 3.0 permettant
l'integration avec systemes tiers.

**Caracteristiques**:
- 180+ endpoints
- Documentation Swagger
- Rate limiting
- Webhooks

**Cout de developpement estime**: 15,000 EUR

### 2.6 Frontend React

**Description**: Interface utilisateur moderne et responsive
construite avec React et TypeScript.

**Caracteristiques**:
- Design system coherent
- PWA (Progressive Web App)
- Optimisations performance
- Accessibilite WCAG 2.1

**Cout de developpement estime**: 30,000 EUR

### 2.7 Transformers Registry

**Description**: Bibliotheque de sous-programmes metier reutilisables
et testes.

**Exemples**:
- text/slugify: Generation de slugs SEO
- Validations, calculs, formatages

**Cout de developpement estime**: 8,000 EUR

---

## 3. KPIS STRATEGIQUES (NOUVEAU)

Les 5 KPIs strategiques ajoutes representent une valeur significative
car ils transforment l'ERP en outil de pilotage.

### 3.1 Cash Runway

| Attribut | Valeur |
|----------|--------|
| Definition | Mois de tresorerie restante |
| Calcul | Tresorerie / Depenses mensuelles |
| Seuils | >12 (vert), 6-12 (orange), <6 (rouge) |
| Endpoint | `/v1/cockpit/helpers/cash-runway` |

### 3.2 Profit Margin

| Attribut | Valeur |
|----------|--------|
| Definition | Marge nette en % |
| Calcul | (CA - Charges) / CA x 100 |
| Benchmark | Services >15%, Commerce >8% |
| Endpoint | `/v1/cockpit/helpers/profit-margin` |

### 3.3 Customer Concentration

| Attribut | Valeur |
|----------|--------|
| Definition | Part du CA des 3 plus gros clients |
| Calcul | CA Top3 / CA Total x 100 |
| Risque | <30% (vert), 30-50% (orange), >50% (rouge) |
| Endpoint | `/v1/cockpit/helpers/customer-concentration` |

### 3.4 Working Capital (BFR)

| Attribut | Valeur |
|----------|--------|
| Definition | Besoin en Fonds de Roulement |
| Calcul | Stocks + Creances - Dettes fournisseurs |
| Interpretation | Positif = besoin de cash |
| Endpoint | `/v1/cockpit/helpers/working-capital` |

### 3.5 Employee Productivity

| Attribut | Valeur |
|----------|--------|
| Definition | CA par employe |
| Calcul | CA Annuel / Nombre ETP |
| Benchmark | Services 120-180k, Commerce 200-400k |
| Endpoint | `/v1/cockpit/helpers/employee-productivity` |

**Cout de developpement KPIs**: 15,000 EUR

---

## 4. CALCUL DE VALORISATION

### 4.1 Methode 1: Cout de Remplacement

| Composant | Cout |
|-----------|------|
| Core SaaS multi-tenant | 40,000 EUR |
| Modules metier (7) | 57,000 EUR |
| Cockpit decisional | 20,000 EUR |
| Module BI | 25,000 EUR |
| API REST | 15,000 EUR |
| Frontend React | 30,000 EUR |
| Transformers Registry | 8,000 EUR |
| KPIs strategiques | 15,000 EUR |
| Tests et qualite | 10,000 EUR |
| Documentation | 5,000 EUR |
| **Sous-total** | **225,000 EUR** |
| Coordination (-10%) | -22,500 EUR |
| **Total** | **202,500 EUR** |

### 4.2 Methode 2: Potentiel ARR

**Hypotheses**:
- Prix: 49 EUR/user/mois
- Client moyen: 5 users
- Objectif: 50 clients

**Calcul**:
```
ARR = 50 clients x 5 users x 49 EUR x 12 mois
ARR = 147,000 EUR/an
```

**Multiple SaaS PME**: 2-4x ARR
**Valorisation**: 294,000 - 588,000 EUR

### 4.3 Valorisation Retenue

**200,000 EUR** est une valorisation **conservatrice** qui:

1. Est legerement inferieure au cout de remplacement
2. Correspond a 1.36x ARR potentiel
3. Offre une marge de negotiation a l'acquereur
4. Reflete la maturite du produit (beta avancee)

---

## 5. AVANTAGES COMPETITIFS

### 5.1 Positionnement Unique

AZALSCORE est le **seul ERP SaaS francais** combinant:
- Gestion operationnelle complete
- Intelligence decisionnelle native
- Prix accessible aux PME (49 EUR/user/mois)

### 5.2 Comparatif

| | AZALSCORE | Odoo | Sage | SAP B1 |
|---|-----------|------|------|--------|
| KPIs natifs | OUI | Non | Non | Addon |
| BI integre | OUI | Non | Non | Addon |
| Multi-tenant | OUI | Oui | Non | Non |
| Prix/user | 49 EUR | 31 EUR | 89 EUR | 150+ EUR |
| Cible | PME FR | Global | PME/ETI | ETI |

### 5.3 Barrieres a l'Entree

1. **Complexite technique**: 83,000+ lignes de code
2. **Temps de developpement**: 18+ mois
3. **Expertise metier**: Connaissance ERP + BI + SaaS
4. **Tests**: Suite complete (>75% coverage)

---

## 6. RISQUES ET MITIGATIONS

| Risque | Niveau | Mitigation |
|--------|--------|------------|
| Dependance technologique | Faible | Stack mainstream |
| Documentation incomplete | Moyen | Docs en cours |
| Equipe de dev | Moyen | Code bien structure |
| Concurrence | Moyen | Positionnement unique |
| Scalabilite | Faible | Architecture cloud-native |

---

## 7. OPPORTUNITES DE CROISSANCE

### Court terme (6 mois)
- Ajout modules: Paie, Production
- IA predictive sur les KPIs
- Marketplace d'extensions

### Moyen terme (12-18 mois)
- Expansion marche francophone (BE, CH, CA)
- Certifications (ISO 27001)
- Partenariats integrateurs

### Long terme (24+ mois)
- Version internationale
- Edition entreprise
- IPO/acquisition

---

## 8. CONCLUSION

AZALSCORE represente une opportunite d'acquisition attractive:

- **Produit mature**: Architecture solide, tests complets
- **Marche porteur**: ERP SaaS PME en croissance
- **Differenciation**: BI + KPIs integres = unique
- **Valorisation juste**: 200,000 EUR

**Recommandation**: Acquisition strategique pour groupe souhaitant
entrer sur le marche ERP SaaS PME avec un produit differencie.

---

## ANNEXES

### A. Architecture Technique

```
+------------------+     +------------------+
|    Frontend      |     |    Mobile PWA    |
|    React/TS      |     |    (Future)      |
+--------+---------+     +--------+---------+
         |                        |
         +------------+-----------+
                      |
              +-------v-------+
              |   API REST    |
              |   FastAPI     |
              +-------+-------+
                      |
         +------------+------------+
         |            |            |
   +-----v----+ +-----v----+ +-----v----+
   | Business | |  BI/SQL  | | Workers  |
   | Modules  | |  Engine  | | Celery   |
   +-----+----+ +-----+----+ +-----+----+
         |            |            |
         +------------+------------+
                      |
              +-------v-------+
              |  PostgreSQL   |
              |  Multi-tenant |
              +---------------+
```

### B. Liste des Endpoints API

Voir `/docs/api/openapi.json` pour la specification complete.

### C. Captures d'Ecran

Voir `/docs/screenshots/` pour les captures de l'interface.

---

*Document prepare le 13 Fevrier 2026*
*Contact: direction@azalscore.com*
