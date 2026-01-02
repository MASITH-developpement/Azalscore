# CORE AZALS — Documentation de référence

**Version Core :** 1.0 (Gelée)  
**Date de gel :** 2 janvier 2026  
**Statut :** FIGÉ — Toute modification nécessite une décision d'architecture consciente

---

## 📋 Table des matières

1. [Philosophie AZALS](#philosophie-azals)
2. [Architecture du cockpit dirigeant](#architecture-du-cockpit-dirigeant)
3. [Système de priorisation 🔴🟠🟢](#système-de-priorisation-)
4. [Règles de priorisation strictes](#règles-de-priorisation-strictes)
5. [Pattern 🔴 (Plan Dominant)](#pattern--plan-dominant)
6. [Souveraineté du dirigeant](#souveraineté-du-dirigeant)
7. [Modules du core](#modules-du-core)
8. [Ce qui est figé vs ce qui peut évoluer](#ce-qui-est-figé-vs-ce-qui-peut-évoluer)
9. [Justification des choix](#justification-des-choix)
10. [Maintenance et évolution](#maintenance-et-évolution)

---

## Philosophie AZALS

### ERP de décision, pas de gestion

**AZALS n'est PAS un logiciel de gestion.**

AZALS est un **ERP de direction** conçu pour :
- Éclairer les **décisions stratégiques** du dirigeant
- Détecter les **risques critiques** avant qu'ils ne deviennent des crises
- Prioriser **automatiquement** ce qui nécessite l'attention du dirigeant
- Garantir la **souveraineté décisionnelle** (aucune action automatique)

### Principe fondamental : "3 secondes pour comprendre"

Le dirigeant doit pouvoir identifier **instantanément** :
- Le niveau de risque global (🔴🟠🟢)
- Le domaine en alerte
- L'action attendue de lui

**Si le cockpit affiche 15 indicateurs, le dirigeant ne regarde rien.**  
**Si le cockpit affiche le risque prioritaire, il agit.**

---

## Architecture du cockpit dirigeant

### Vue unique et exclusive

Le cockpit AZALS applique une **règle absolue** :

> **Un seul niveau de risque affiché à la fois**

- Si au moins un 🔴 existe → **UNIQUEMENT le 🔴 prioritaire est affiché**
- Si aucun 🔴 mais des 🟠 → Afficher **tous les 🟠** classés par impact
- Si aucun 🔴 ni 🟠 → Afficher **tous les 🟢**

### Pourquoi cette exclusivité ?

1. **Clarté cognitive** : Le dirigeant ne doit pas arbitrer entre 3 alertes critiques
2. **Hiérarchie stricte** : Certains risques sont TOUJOURS prioritaires sur d'autres
3. **Action immédiate** : En mode 🔴, toute l'attention doit être sur CE risque

### Zones d'affichage

```
┌─────────────────────────────────────────────┐
│  ZONE CRITIQUE 🔴                           │
│  (visible uniquement si au moins un 🔴)     │
│  - Affiche LE module prioritaire            │
│  - Masque tous les autres (🟠 et 🟢)        │
│  - Message : "X indicateurs masqués"        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  ZONE TENSION 🟠                            │
│  (visible si aucun 🔴)                      │
│  - Affiche tous les modules en tension      │
│  - Classés par priorité de domaine          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  ZONE NORMALE 🟢                            │
│  (visible si aucun 🔴 ni 🟠)                │
│  - Affiche tous les indicateurs             │
│  - Vue complète du cockpit                  │
└─────────────────────────────────────────────┘
```

---

## Système de priorisation 🔴🟠🟢

### Niveaux de risque

| Statut | Signification | Comportement cockpit |
|--------|--------------|---------------------|
| **🔴 Critique** | Risque immédiat nécessitant décision dirigeant | Affichage exclusif du 🔴 prioritaire |
| **🟠 Attention** | Point de vigilance nécessitant suivi | Affichage de tous les 🟠 si aucun 🔴 |
| **🟢 Normal** | Situation maîtrisée | Affichage complet si aucun 🔴🟠 |

### Déclenchement des alertes

**🔴 Critique (priority = 0)** :
- Trésorerie : Déficit prévu sous seuil RED
- Juridique : Non-conformité statutaire OU risques identifiés
- Fiscalité : Retard déclaration TVA/IS + montant > 10k
- RH : Paie non conforme OU DSN en retard
- Comptabilité : (pas de 🔴 actuellement)

**🟠 Attention (priority = 1)** :
- Trésorerie : Solde sous seuil orange
- Juridique : Révision statutaire à revoir (>18 mois) OU contrats expirant
- Fiscalité : TVA à risque OU IS à vérifier
- RH : DSN à surveiller OU contrats CDD nombreux
- Comptabilité : Clôture comptable en retard

**🟢 Normal (priority = 2)** :
- Tous les indicateurs dans les seuils acceptables

---

## Règles de priorisation strictes

### RÈGLE ABSOLUE : Un seul 🔴 visible à la fois

Si plusieurs modules sont en état 🔴, **seul le plus prioritaire est affiché**.

### Ordre de priorité des domaines (NON MODIFIABLE)

```
1. Financier (Trésorerie)        → priority = 1
2. Juridique / Structurel        → priority = 2
3. Fiscalité                     → priority = 3
4. Ressources Humaines           → priority = 4
5. Comptabilité                  → priority = 5
```

### Justification de cet ordre

**1. Financier (Trésorerie)** : Sans trésorerie, l'entreprise meurt **immédiatement**  
**2. Juridique** : Responsabilité personnelle du dirigeant engagée  
**3. Fiscalité** : Risques pénaux + pénalités exponentielles  
**4. RH** : Risques URSSAF + contentieux prud'homaux  
**5. Comptabilité** : Risque indirect (certification, audit)

### Exemple de priorisation

**Situation :**
- Trésorerie : 🔴 (déficit prévu -50k€)
- Juridique : 🔴 (non-conformité statutaire)
- Fiscalité : 🟠 (TVA à risque)
- RH : 🟢 (tout normal)
- Comptabilité : 🟢 (tout normal)

**Affichage AZALS :**
- **UNIQUEMENT Trésorerie 🔴** (priorité 1)
- Message : "3 autres indicateurs masqués"
- Juridique 🔴, Fiscalité 🟠, RH 🟢, Comptabilité 🟢 → **MASQUÉS**

**Raison :**  
Sans trésorerie, l'entreprise ne peut pas traiter les autres problèmes.

---

## Pattern 🔴 (Plan Dominant)

### Qu'est-ce que le pattern 🔴 ?

Le **pattern 🔴** est l'affichage exclusif d'une alerte critique qui :
- Occupe toute la zone d'attention du dirigeant
- Masque tous les autres indicateurs
- Bloque (visuellement) toute autre information
- Force le traitement du risque prioritaire

### Quand s'active le pattern 🔴 ?

**Déclenchement automatique dès qu'AU MOINS UN module passe en 🔴.**

Le module affiché est déterminé par l'ordre de priorité des domaines.

### Comment s'affiche le pattern 🔴 ?

```
╔═══════════════════════════════════════════════╗
║  🔴 SITUATION CRITIQUE                        ║
║                                               ║
║  Trésorerie                                   ║
║  Déficit prévu : -50 000 €                    ║
║                                               ║
║  Détails :                                    ║
║  - Solde actuel : 25 000 €                    ║
║  - Entrées prévues : +10 000 €                ║
║  - Sorties prévues : -85 000 €                ║
║  - Prévision : -50 000 €                      ║
║                                               ║
║  ⚠️ 3 autres indicateurs masqués              ║
║  Traitez d'abord cette situation critique.    ║
║                                               ║
║  [📊 Consulter le rapport RED]                ║
║  [🖨️ Imprimer]                                ║
╚═══════════════════════════════════════════════╝
```

### Ce que le pattern 🔴 interdit

- ❌ Afficher d'autres indicateurs en même temps
- ❌ Permettre la navigation vers d'autres modules
- ❌ Autoriser des actions sur d'autres domaines
- ❌ Minimiser ou cacher l'alerte critique

### Ce que le pattern 🔴 autorise

- ✅ Consulter le rapport détaillé (rapport RED pour trésorerie)
- ✅ Imprimer la situation pour réunion
- ✅ Accéder aux données brutes (lecture seule)
- ✅ Se déconnecter (l'alerte persiste au prochain login)

### Sortie du pattern 🔴

Le pattern 🔴 **ne se désactive QUE** si :
1. Le module critique repasse en 🟠 ou 🟢 (données actualisées)
2. Le workflow de décision est validé (ex: rapport RED signé)

**AUCUNE action de "masquage" ou "ignorer" n'est permise.**

---

## Souveraineté du dirigeant

### Principe fondamental

> **AZALS ne prend AUCUNE décision, AZALS ne lance AUCUNE action automatique.**

### Ce qu'AZALS fait

- ✅ Détecte les situations critiques
- ✅ Alerte le dirigeant avec priorisation stricte
- ✅ Fournit les données nécessaires à la décision
- ✅ Trace les décisions prises (journal décisionnel)
- ✅ Présente les options possibles (sans en imposer)

### Ce qu'AZALS ne fait JAMAIS

- ❌ Envoyer automatiquement un email
- ❌ Déclencher un paiement
- ❌ Bloquer une opération
- ❌ Modifier des données sans validation dirigeant
- ❌ Prendre une décision "par défaut"

### Responsabilité

**Le dirigeant reste responsable** :
- De ses décisions (éclairées par AZALS)
- De l'inaction (AZALS alerte, le dirigeant décide d'agir ou non)
- Des conséquences (AZALS trace, le dirigeant assume)

**AZALS est un outil d'aide à la décision, PAS un décideur.**

---

## Modules du core

### 1. Trésorerie (Financier)

**Rôle :** Détecter les risques de rupture de trésorerie  
**Priorité domaine :** 1 (la plus haute)  
**Déclenchement 🔴 :**  
- Déficit prévu sous seuil RED (défini dans configuration)
- Workflow RED non validé

**Données surveillées :**
- Solde bancaire actuel
- Prévision J+30
- Entrées/sorties attendues
- Seuils RED/ORANGE

**API :** `/treasury/status`

---

### 2. Juridique / Structurel

**Rôle :** Protéger le dirigeant des risques juridiques engageant sa responsabilité personnelle  
**Priorité domaine :** 2  
**Déclenchement 🔴 :**  
- Non-conformité statutaire (révision > 36 mois)
- Risques juridiques identifiés > 0

**Données surveillées :**
- Conformité statutaire
- Date dernière révision
- Contrats sensibles
- Contrats expirant prochainement
- Risques identifiés

**API :** `/legal/status`

---

### 3. Fiscalité

**Rôle :** Anticiper les risques fiscaux (pénalités, redressements)  
**Priorité domaine :** 3  
**Déclenchement 🔴 :**  
- Retard déclaration TVA/IS + montant > 10 000 €

**Données surveillées :**
- TVA mensuelle (statut, montant, échéance)
- IS annuel (statut, montant, échéance)
- Dates limites de déclaration

**API :** `/tax/status`

---

### 4. Ressources Humaines (RH)

**Rôle :** Détecter les non-conformités sociales  
**Priorité domaine :** 4  
**Déclenchement 🔴 :**  
- Paie non conforme
- DSN en retard

**Données surveillées :**
- Conformité paie
- DSN (Déclaration Sociale Nominative)
- Effectif total
- Contrats CDD

**API :** `/hr/status`

---

### 5. Comptabilité

**Rôle :** Surveiller la conformité comptable  
**Priorité domaine :** 5  
**Déclenchement 🔴 :** (aucun actuellement)  
**Déclenchement 🟠 :**  
- Clôture comptable en retard

**Données surveillées :**
- Nombre d'écritures en attente
- Statut clôture comptable

**API :** `/accounting/status`

---

## Ce qui est figé vs ce qui peut évoluer

### ✅ CE QUI EST FIGÉ (CORE AZALS)

**Ne peut être modifié sans décision d'architecture consciente et documentée.**

#### Philosophie
- ✅ AZALS = ERP de décision, pas de gestion
- ✅ Principe "3 secondes pour comprendre"
- ✅ Souveraineté du dirigeant (aucune action automatique)

#### Priorisation
- ✅ Ordre des domaines : Financier > Juridique > Fiscal > RH > Comptabilité
- ✅ Règle "un seul 🔴 visible à la fois"
- ✅ Niveaux : 🔴 Critique / 🟠 Attention / 🟢 Normal

#### Pattern 🔴
- ✅ Affichage exclusif du risque prioritaire
- ✅ Masquage de tous les autres indicateurs
- ✅ Sortie uniquement si résolution ou validation workflow

#### Architecture technique
- ✅ Fonction `collectStates()` : collecte les états des modules
- ✅ Fonction `resolvePriority()` : applique les 3 règles strictes
- ✅ Fonction `renderCockpit()` : affiche selon la décision
- ✅ Constante `DOMAIN_PRIORITY` : ordre strict des domaines

---

### 🔧 CE QUI PEUT ÉVOLUER (V2/V3)

**Peut être modifié sans impacter le core.**

#### Modules métier
- 🔧 Ajouter de nouveaux modules (ex: Achats, Stocks)
- 🔧 Modifier les seuils de déclenchement (RED/ORANGE)
- 🔧 Enrichir les données affichées par module
- 🔧 Ajouter des visualisations (graphiques, tableaux)

#### Workflows décisionnels
- 🔧 Ajouter de nouveaux workflows (type rapport RED)
- 🔧 Personnaliser les étapes de validation
- 🔧 Intégrer des approbations multi-niveaux

#### Interface utilisateur
- 🔧 Améliorer le design (couleurs, polices, espacements)
- 🔧 Ajouter des animations (transitions, feedbacks)
- 🔧 Optimiser pour mobile/tablette
- 🔧 Thèmes clairs/sombres

#### Fonctionnalités annexes
- 🔧 Exports PDF/Excel personnalisés
- 🔧 Notifications par email (avec désactivation possible)
- 🔧 Tableau de bord personnalisable (hors mode 🔴)
- 🔧 Historique des décisions enrichi

#### Intégrations
- 🔧 Connexion avec outils externes (CRM, comptabilité)
- 🔧 API publique pour partenaires
- 🔧 Webhooks pour événements critiques

#### Multi-tenant
- 🔧 Personnalisation par client (logo, couleurs)
- 🔧 Seuils RED/ORANGE configurables par tenant
- 🔧 Modules activables/désactivables par tenant

---

## Justification des choix

### Pourquoi l'ordre Financier > Juridique > Fiscal > RH > Comptabilité ?

#### 1. Financier en priorité absolue

**Sans trésorerie, l'entreprise cesse d'exister immédiatement.**

- Impossibilité de payer les salaires → risque social majeur
- Impossibilité de payer les fournisseurs → rupture d'activité
- Risque de cessation de paiement → dépôt de bilan

**Tous les autres problèmes deviennent secondaires si l'entreprise n'a plus de trésorerie.**

#### 2. Juridique en 2e position

**La responsabilité personnelle du dirigeant est engagée.**

- Non-conformité statutaire → faute de gestion (art. L. 223-22 C. com.)
- Risques juridiques → responsabilité civile/pénale du dirigeant
- Contrats non renouvelés → pertes commerciales/financières

**Le dirigeant peut être personnellement poursuivi et condamné.**

#### 3. Fiscalité en 3e position

**Risques pénaux + pénalités exponentielles.**

- Retard déclaration TVA/IS → pénalités 10-80%
- Redressement fiscal → majoration 40-80%
- Risque pénal (fraude fiscale) → prison + amendes

**Les pénalités peuvent doubler la dette initiale.**

#### 4. RH en 4e position

**Risques URSSAF + contentieux prud'homaux.**

- Paie non conforme → redressement URSSAF (5 ans rétroactif)
- DSN en retard → pénalités + contrôle URSSAF
- Contentieux prud'homal → condamnations + image

**Les contentieux sociaux sont longs et coûteux.**

#### 5. Comptabilité en 5e position

**Risque indirect (certification, audit).**

- Clôture en retard → impossibilité de certifier les comptes
- Écritures en attente → vision trésorerie faussée
- Non-conformité comptable → rejet par CAC

**La comptabilité informe les autres risques, mais n'en crée pas directement.**

---

### Pourquoi "un seul 🔴 visible à la fois" ?

#### Problème : La paralysie décisionnelle

Si le dirigeant voit :
- Trésorerie 🔴 : -50k€
- Juridique 🔴 : Non-conformité
- Fiscalité 🔴 : Retard déclaration

**Il ne sait pas par où commencer.**

#### Solution : Priorisation stricte

AZALS décide **pour le dirigeant** quel risque traiter **en premier**.

**Résultat :**
- Clarté cognitive
- Action immédiate
- Pas de paralysie
- Traitement séquentiel des risques

**Analogie :** Dans un incendie, on éteint le feu **avant** de réparer le toit.

---

### Pourquoi aucune action automatique ?

#### Problème : La perte de souveraineté

Un logiciel qui "décide à la place" du dirigeant :
- Déresponsabilise
- Crée une dépendance
- Peut prendre de mauvaises décisions (contexte incomplet)

#### Solution : AZALS alerte, le dirigeant décide

**AZALS fournit :**
- La détection des risques
- Les données nécessaires
- Les options possibles

**Le dirigeant reste maître :**
- De ses décisions
- De leur timing
- De leur mise en œuvre

**Responsabilité assumée, pas déléguée à un algorithme.**

---

## Maintenance et évolution

### Modifications du CORE

**TOUTE modification du CORE nécessite :**

1. **Décision d'architecture documentée**
   - Raison de la modification
   - Impact sur les règles existantes
   - Validation par l'architecte ERP senior

2. **Tests de non-régression complets**
   - Vérifier que la priorisation fonctionne toujours
   - Tester les 3 règles (critique/tension/normal)
   - Valider l'ordre des domaines

3. **Mise à jour de cette documentation**
   - README_CORE_AZALS.md
   - Commentaires dans le code
   - Changelog versioning

### Ajout de nouveaux modules

**Procédure pour ajouter un module (ex: Achats) :**

1. **Définir la priorité de domaine**
   - Où se situe-t-il dans l'ordre ?
   - Justifier ce positionnement

2. **Définir les seuils 🔴🟠🟢**
   - Quand déclencher une alerte critique ?
   - Quand déclencher une attention ?

3. **Créer l'API backend**
   - Endpoint `/module/status`
   - Respect du format de réponse

4. **Intégrer dans collectStates()**
   - Ajouter dans AZALS_FORCED_STATES (si mode test)
   - Ajouter dans la liste des modules

5. **Tester la priorisation**
   - Vérifier que le module s'insère correctement
   - Valider le comportement en mode 🔴

### Support et contact

**Pour toute question sur le CORE AZALS :**

- 📧 Email : architecture@azals.com
- 📚 Documentation : /docs
- 🔧 Issues : GitHub Issues

---

## Historique des versions

| Version | Date | Description |
|---------|------|-------------|
| **1.0** | 2 janvier 2026 | Gel du CORE AZALS après validation complète |
| 0.9 | 1 janvier 2026 | Intégration module Juridique + mode test |
| 0.8 | 31 décembre 2025 | Priorisation transverse implémentée |
| 0.7 | 30 décembre 2025 | Modules Fiscalité et RH intégrés |
| 0.6 | 29 décembre 2025 | Module Comptabilité intégré |
| 0.5 | 28 décembre 2025 | Pattern 🔴 finalisé |

---

## Signature

**Document rédigé par :** Architecte ERP Senior AZALS  
**Date de gel :** 2 janvier 2026  
**Statut :** CORE FIGÉ

**Toute modification du CORE AZALS nécessite une décision d'architecture consciente, documentée et validée.**

---

**FIN DU DOCUMENT**
