# CHARTE GÉNÉRALE AZALSCORE
## Constitution Fondatrice du Système

**Version:** 1.0.0
**Statut:** DOCUMENT FONDATEUR - PRÉVAUT SUR TOUT
**Date:** 2026-01-05
**Classification:** PUBLIC - OPPOSABLE

---

## 1. OBJECTIF

Cette charte constitue le document fondateur d'AZALSCORE. Elle définit les principes immuables, la philosophie architecturale et les règles de gouvernance qui régissent l'ensemble du système.

**RÈGLE ABSOLUE:** Cette charte prévaut sur tout autre document, y compris le code source. En cas de contradiction, cette charte fait autorité.

---

## 2. PÉRIMÈTRE

Cette charte s'applique à :
- L'ensemble du code source AZALSCORE
- Tous les modules présents et futurs
- Toute intelligence artificielle interagissant avec le système
- Tout développeur (humain ou IA) contribuant au projet
- Toute documentation technique ou fonctionnelle
- Tout processus de décision impliquant le système

---

## 3. VISION AZALSCORE

AZALSCORE est un **ERP de pilotage décisionnel critique** destiné aux dirigeants d'entreprise.

### 3.1 Mission
Fournir un système de gestion intégré permettant une prise de décision éclairée, traçable et sécurisée, avec une assistance IA encadrée.

### 3.2 Valeurs Fondamentales
- **Souveraineté du dirigeant:** Le système assiste, il ne décide jamais
- **Transparence totale:** Toute action est traçable et auditable
- **Sécurité by design:** La protection des données est native, non additionnelle
- **Modularité absolue:** Chaque composant est indépendant et remplaçable
- **Pérennité systémique:** Le système est conçu pour durer et évoluer

---

## 4. PRINCIPES ARCHITECTURAUX IMMUABLES

### 4.1 Backend-First
```
RÈGLE: Le backend est la source de vérité unique.
- Toute logique métier réside dans le backend
- Le frontend est une projection visuelle des API
- Aucune décision métier ne peut être prise côté client
```

### 4.2 API-First
```
RÈGLE: Toute fonctionnalité est exposée via API avant toute interface.
- OpenAPI comme contrat d'interface
- Versioning strict des endpoints
- Documentation automatique et exhaustive
```

### 4.3 Modularité Absolue
```
RÈGLE: Le système est composé de modules indépendants.
- Chaque module a un périmètre défini et limité
- Un module peut être ajouté/supprimé sans impact sur les autres
- Les dépendances inter-modules sont explicites et minimales
```

### 4.4 Séparation Core / Modules
```
RÈGLE SACRÉE: Le Core et les Modules sont strictement séparés.
- Le Core ne dépend d'AUCUN module
- Les modules dépendent du Core, JAMAIS l'inverse
- Le Core est INTOUCHABLE sauf procédure exceptionnelle
```

### 4.5 Multi-Tenant Native
```
RÈGLE: L'isolation des données entre tenants est garantie par architecture.
- Chaque requête porte un tenant_id
- Aucune donnée ne peut fuiter entre tenants
- L'isolation est vérifiée à chaque couche
```

---

## 5. GOUVERNANCE DU SYSTÈME

### 5.1 Hiérarchie des Chartes
```
ORDRE DE PRÉSÉANCE (du plus au moins prioritaire):

1. 00_charte_generale_azalscore.md     ← CONSTITUTION (ce document)
2. 01_charte_core_azalscore.md         ← PROTECTION DU CORE
3. 06_charte_securite_conformite.md    ← SÉCURITÉ
4. 05_charte_ia.md                     ← ENCADREMENT IA
5. 08_charte_gouvernance_decision.md   ← DÉCISIONS
6. Autres chartes                      ← OPÉRATIONNELLES
7. Documentation technique             ← RÉFÉRENCE
8. Code source                         ← IMPLÉMENTATION
```

### 5.2 Principe de Non-Régression
```
RÈGLE: Aucune modification ne peut dégrader le système.
- Toute évolution maintient ou améliore la sécurité
- Toute évolution maintient ou améliore la traçabilité
- Toute évolution respecte la compatibilité ascendante
- Les exceptions requièrent une validation gouvernance
```

### 5.3 Validation Humaine Obligatoire
```
RÈGLE: L'humain reste maître des décisions critiques.
- Aucune action financière automatique sans validation
- Aucune modification du Core sans autorisation explicite
- Aucune suppression de données sans confirmation
- L'IA propose, l'humain dispose
```

---

## 6. RÈGLES OBLIGATOIRES

### 6.1 Pour le Développement
| Règle | Description |
|-------|-------------|
| R-DEV-01 | Tout code respecte les chartes avant d'être mergé |
| R-DEV-02 | Tout endpoint est documenté via OpenAPI |
| R-DEV-03 | Tout module a sa charte GOVERNANCE.md |
| R-DEV-04 | Les tests sont obligatoires pour le Core |
| R-DEV-05 | Le code est auditable et traçable |

### 6.2 Pour l'IA
| Règle | Description |
|-------|-------------|
| R-IA-01 | L'IA ne prend aucune décision finale |
| R-IA-02 | L'IA ne modifie pas le Core |
| R-IA-03 | Toute action IA est journalisée |
| R-IA-04 | L'IA est révocable à tout moment |
| R-IA-05 | L'IA respecte les limites de données |

### 6.3 Pour la Sécurité
| Règle | Description |
|-------|-------------|
| R-SEC-01 | Zero Trust : tout est vérifié |
| R-SEC-02 | Moindre privilège : accès minimum requis |
| R-SEC-03 | Secrets externalisés, jamais en code |
| R-SEC-04 | Journalisation inviolable |
| R-SEC-05 | Chiffrement des données sensibles |

---

## 7. INTERDICTIONS ABSOLUES

Les actions suivantes sont **STRICTEMENT INTERDITES** :

### 7.1 Interdictions Techniques
- ❌ Modifier le Core sans procédure validée
- ❌ Créer des dépendances Core → Module
- ❌ Hardcoder des secrets dans le code
- ❌ Désactiver l'audit ou la journalisation
- ❌ Contourner l'authentification ou l'autorisation

### 7.2 Interdictions Fonctionnelles
- ❌ Exécuter des actions financières sans validation humaine
- ❌ Supprimer des données sans traçabilité
- ❌ Permettre l'accès cross-tenant
- ❌ Masquer des erreurs ou exceptions

### 7.3 Interdictions IA
- ❌ IA décisionnaire autonome
- ❌ IA avec accès au Core en écriture
- ❌ IA sans journalisation
- ❌ IA non révocable

---

## 8. CLASSIFICATION DES ALERTES

### Système RED / ORANGE / GREEN

| Niveau | Signification | Action Requise |
|--------|---------------|----------------|
| 🔴 RED | Critique - Intervention immédiate | Blocage automatique + Alerte dirigeant |
| 🟠 ORANGE | Attention - Surveillance active | Notification + Suivi renforcé |
| 🟢 GREEN | Normal - Fonctionnement nominal | Monitoring standard |

**RÈGLE:** Un état RED ne peut JAMAIS être rétrogradé automatiquement. Seule une validation humaine peut lever un RED.

---

## 9. CONSÉQUENCES EN CAS DE NON-RESPECT

### 9.1 Pour le Code
- Rejet automatique du merge/commit
- Revue obligatoire avant correction
- Traçabilité de l'incident

### 9.2 Pour l'IA
- Révocation immédiate des droits
- Audit complet des actions passées
- Restriction permanente si récidive

### 9.3 Pour le Système
- Incident de sécurité déclaré
- Analyse post-mortem obligatoire
- Mise à jour des chartes si nécessaire

---

## 10. ÉVOLUTION DE CETTE CHARTE

### 10.1 Processus de Modification
1. Proposition écrite et motivée
2. Revue par la gouvernance
3. Validation unanime requise
4. Période de transition définie
5. Communication à tous les acteurs

### 10.2 Versioning
- Majeure (X.0.0) : Changement de principe fondamental
- Mineure (0.X.0) : Ajout de règle
- Patch (0.0.X) : Clarification

---

## 11. GLOSSAIRE

| Terme | Définition |
|-------|------------|
| **Core** | Noyau système intouchable (auth, permissions, audit, sécurité) |
| **Module** | Composant fonctionnel indépendant et remplaçable |
| **Tenant** | Organisation cliente isolée dans le système |
| **RED** | État critique nécessitant intervention humaine |
| **Gouvernance** | Ensemble des règles et processus de décision |

---

## 12. SIGNATURES ET APPLICABILITÉ

Cette charte est applicable dès sa publication et s'impose à :
- Tout code source présent et futur
- Tout contributeur humain ou IA
- Toute documentation et processus

**AZALSCORE v7.0 - Gouvernance Système**

---

*Document généré et validé le 2026-01-05*
*Classification: PUBLIC - OPPOSABLE*
*Référence: AZALS-GOV-00-v1.0.0*
