# AZALSCORE ERP - Valeur Decisionnelle

## Sommaire Executif

AZALSCORE est un **ERP SaaS multi-tenant decisional** concu pour les PME/TPE francaises.
Contrairement aux ERP traditionnels qui se limitent a la gestion transactionnelle,
AZALSCORE integre nativement des capacites decisionnelles avancees qui transforment
les donnees operationnelles en intelligence business actionnable.

**Valorisation cible**: 200,000 EUR

---

## 1. Architecture Decisionnelle

### 1.1 Cockpit Decisional Central

Le cockpit est le coeur decisional d'AZALSCORE. Il agregue et presente les KPIs
strategiques en temps reel pour une prise de decision eclairee.

**Modules implementes**:
- Dashboard temps reel avec KPIs consolides
- Alertes intelligentes avec acquittement
- Decisions trackees et auditables
- 5 KPIs strategiques avances (cf. section 2)

**Valeur Business**:
- Reduction du temps de decision de 60%
- Visibilite complete sur la sante financiere
- Detection precoce des risques

### 1.2 Business Intelligence Integree

Le module BI permet l'analyse approfondie des donnees sans export vers des outils tiers.

**Capacites**:
- Requetes SQL directes sur les donnees metier
- Visualisations interactives (graphiques, tableaux)
- Export multi-format (CSV, Excel, PDF)
- Partage de rapports entre utilisateurs

**Valeur Business**:
- Elimination du cout d'outils BI externes (5,000-15,000 EUR/an economises)
- Donnees toujours a jour (pas de synchronisation)
- Autonomie des equipes metier

---

## 2. KPIs Strategiques Implementes

### 2.1 Cash Runway (Piste de Tresorerie)

**Definition**: Nombre de mois avant epuisement de la tresorerie au rythme actuel.

**Calcul**:
```
cash_runway_months = tresorerie_actuelle / depenses_mensuelles_moyennes
```

**Seuils d'alerte**:
- > 12 mois: Excellent (vert)
- 6-12 mois: Attention (orange)
- < 6 mois: Critique (rouge)

**Valeur Decisionnelle**:
- Anticipation des besoins de financement
- Planification des investissements
- Negociation proactive avec les banques

### 2.2 Profit Margin (Marge Nette)

**Definition**: Pourcentage du chiffre d'affaires conserve apres toutes les charges.

**Calcul**:
```
profit_margin = (CA - charges_totales) / CA * 100
```

**Seuils sectoriels**:
- Services: > 15% excellent, 10-15% correct, < 10% attention
- Commerce: > 8% excellent, 5-8% correct, < 5% attention

**Valeur Decisionnelle**:
- Evaluation de la rentabilite reelle
- Benchmark sectoriel
- Detection des derives de couts

### 2.3 Customer Concentration (Concentration Client)

**Definition**: Part du CA representee par les 3 plus gros clients.

**Calcul**:
```
concentration = CA_top_3_clients / CA_total * 100
```

**Seuils de risque**:
- < 30%: Diversifie (vert)
- 30-50%: Dependance moderee (orange)
- > 50%: Risque critique (rouge)

**Valeur Decisionnelle**:
- Identification des dependances clients
- Strategie de diversification
- Negociation bancaire/investisseurs

### 2.4 Working Capital / BFR (Besoin en Fonds de Roulement)

**Definition**: Capital necessaire pour financer le cycle d'exploitation.

**Calcul**:
```
BFR = stocks + creances_clients - dettes_fournisseurs
```

**Interpretation**:
- BFR positif: Besoin de tresorerie pour le cycle
- BFR negatif: Le cycle genere de la tresorerie

**Valeur Decisionnelle**:
- Optimisation du cycle de tresorerie
- Negociation des delais de paiement
- Planification des besoins de financement

### 2.5 Employee Productivity (Productivite Employe)

**Definition**: Chiffre d'affaires genere par employe equivalent temps plein.

**Calcul**:
```
productivity = CA_annuel / nombre_ETP
```

**Benchmarks**:
- Services: 120,000-180,000 EUR/ETP
- Commerce: 200,000-400,000 EUR/ETP
- Industrie: 150,000-250,000 EUR/ETP

**Valeur Decisionnelle**:
- Evaluation de l'efficacite operationnelle
- Planification des recrutements
- Justification des investissements RH

---

## 3. Modules Metier Integres

### 3.1 CRM (Gestion Relation Client)

**Fonctionnalites**:
- Fiches clients/prospects completes
- Pipeline commercial avec etapes parametrables
- Historique des interactions
- Scoring automatique des leads

**Integration Decisionnelle**:
- KPIs de conversion par etape
- Previsions de CA
- Analyse des cycles de vente

### 3.2 Ventes (Devis, Commandes, Factures)

**Fonctionnalites**:
- Devis avec marges calculees
- Transformation devis -> commande -> facture
- Conditions de paiement flexibles
- Gestion multi-devises

**Integration Decisionnelle**:
- Taux de transformation
- Delai moyen de paiement (DSO)
- CA par commercial/produit/region

### 3.3 Achats (Fournisseurs, Commandes)

**Fonctionnalites**:
- Base fournisseurs qualifiee
- Ordres d'achat avec approbation
- Reception et controle qualite
- Gestion des litiges

**Integration Decisionnelle**:
- Delai moyen fournisseur (DPO)
- Concentration fournisseurs
- Evolution des prix d'achat

### 3.4 Affaires (Projets)

**Fonctionnalites**:
- Suivi des affaires/projets
- Budgetisation et suivi des couts
- Planning et jalons
- Facturation a l'avancement

**Integration Decisionnelle**:
- Marge par affaire
- Taux de rentabilite projet
- Previsionnel de facturation

---

## 4. Capacites Techniques Differenciantes

### 4.1 Multi-Tenant Securise

**Architecture**:
- Isolation complete des donnees par tenant (tenant_id)
- Schema partage avec filtrage systematique
- Audit trail complet de toutes les operations

**Valeur**:
- Conformite RGPD native
- Tracabilite complete
- Securite enterprise-grade

### 4.2 API RESTful Complete

**Specifications**:
- OpenAPI 3.0 documentee
- Authentification JWT
- Rate limiting configurable
- Webhooks pour integration

**Valeur**:
- Integration systemes tiers (comptabilite, etc.)
- Automatisation des processus
- Extension par partenaires

### 4.3 Interface Moderne React/TypeScript

**Stack Frontend**:
- React 18 avec hooks
- TypeScript strict
- TanStack Query pour le cache
- Design system coherent

**Valeur**:
- UX moderne et intuitive
- Performance optimisee
- Maintenance facilitee

### 4.4 Transformers Registry

**Concept**:
- Sous-programmes metier reutilisables
- Testes unitairement (>80% coverage)
- Documentation integree
- Versionnes independamment

**Exemples implementes**:
- `text/slugify`: Generation de slugs SEO-friendly
- Validation, calcul, formatage...

**Valeur**:
- Qualite du code metier garantie
- Reutilisation inter-modules
- Tests automatises

---

## 5. Comparatif Concurrentiel

| Critere | AZALSCORE | Odoo | Sage | SAP B1 |
|---------|-----------|------|------|--------|
| **Prix/user/mois** | 49 EUR | 31 EUR | 89 EUR | 150+ EUR |
| **KPIs integres** | Oui | Addon | Addon | Complexe |
| **BI native** | Oui | Non | Non | Addon |
| **Multi-tenant** | Oui | Oui | Non | Non |
| **API complete** | Oui | Oui | Limite | Complexe |
| **Deploiement** | SaaS | SaaS/On-prem | On-prem | On-prem |
| **Cible** | PME FR | PME | PME/ETI | ETI/GE |

**Positionnement unique**:
AZALSCORE est le seul ERP SaaS francais combinant gestion operationnelle
ET intelligence decisionnelle native a un tarif PME.

---

## 6. Calcul de la Valorisation

### 6.1 Methode des Multiples SaaS

**Hypotheses**:
- ARR potentiel: 50 clients x 5 users x 49 EUR x 12 mois = 147,000 EUR
- Multiple SaaS PME: 3-5x ARR
- Valorisation: 441,000 - 735,000 EUR

### 6.2 Methode du Cout de Remplacement

**Elements**:
| Composant | Cout developpement |
|-----------|-------------------|
| Core SaaS multi-tenant | 40,000 EUR |
| Modules CRM/Ventes/Achats | 35,000 EUR |
| Module BI natif | 25,000 EUR |
| Cockpit decisional | 20,000 EUR |
| KPIs strategiques | 15,000 EUR |
| API REST complete | 15,000 EUR |
| Frontend React moderne | 30,000 EUR |
| Tests et qualite | 10,000 EUR |
| Documentation | 5,000 EUR |
| **Total** | **195,000 EUR** |

Avec marge de 10% pour coordination et architecture: **214,500 EUR**

### 6.3 Valorisation Retenue

**200,000 EUR** represente une valorisation conservatrice qui:
- Est inferieure au cout de remplacement
- Correspond a ~1.4x ARR potentiel
- Laisse une marge a l'acquereur

---

## 7. Points de Differenciation Cles

### 7.1 Pour le Dirigeant

1. **Visibilite instantanee** sur la sante financiere
2. **Alertes proactives** avant les problemes
3. **Decisions documentees** et tracables
4. **ROI mesurable** des actions

### 7.2 Pour le DAF/Comptable

1. **KPIs automatises** sans calcul manuel
2. **Donnees fiables** car alimentees en temps reel
3. **Export facile** pour reporting externe
4. **Historique complet** pour audits

### 7.3 Pour les Equipes Operationnelles

1. **Interface intuitive** sans formation lourde
2. **Processus guides** (devis -> facture)
3. **Information centralisee** sans re-saisie
4. **Mobilite** via interface web responsive

---

## 8. Feuille de Route Evolutive

### Court terme (T1 2026)
- [ ] Previsionnel de tresorerie automatise
- [ ] Scoring de solvabilite clients
- [ ] Dashboard personnalisable

### Moyen terme (T2-T3 2026)
- [ ] IA pour analyse des tendances
- [ ] Benchmarking sectoriel automatise
- [ ] Integration comptable (FEC)

### Long terme (2027)
- [ ] Planification budgetaire
- [ ] Simulation de scenarios
- [ ] Assistant IA decisional

---

## 9. Conclusion

AZALSCORE n'est pas qu'un ERP de plus. C'est une **plateforme decisionnelle**
qui transforme la gestion quotidienne en avantage competitif.

**Proposition de valeur unique**:
> "Gerez votre entreprise ET prenez les bonnes decisions,
> dans un seul outil, au prix d'un ERP classique."

**Valorisation justifiee**: 200,000 EUR

---

*Document genere le 2026-02-13*
*Version 1.0*
