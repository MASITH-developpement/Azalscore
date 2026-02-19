# Guide de Migration Axonaut → AzalScore

**Version** : 1.0  
**Date** : 13 février 2026  
**Public** : Clients Axonaut, Équipes commerciales, Équipes techniques

---

## 📋 Table des Matières

1. [Introduction](#introduction)
2. [Pourquoi Migrer vers AzalScore](#pourquoi-migrer)
3. [Tableau de Correspondance des Fonctionnalités](#correspondances)
4. [Avantages d'AzalScore](#avantages)
5. [Étapes de Migration](#etapes)
6. [Guide Technique de Migration](#guide-technique)
7. [Formation et Support](#formation)
8. [FAQ](#faq)

---

## 1. Introduction {#introduction}

Ce guide accompagne les clients Axonaut dans leur migration vers AzalScore, une plateforme ERP SaaS nouvelle génération offrant toutes les fonctionnalités d'Axonaut et bien plus encore.

### Objectifs du Guide

- Faciliter la compréhension des équivalences fonctionnelles
- Démontrer les avantages compétitifs d'AzalScore
- Fournir un plan de migration étape par étape
- Assurer une transition fluide sans interruption d'activité

### Promesse Migration

✅ **Zéro perte de données**  
✅ **Formation incluse**  
✅ **Support dédié pendant 3 mois**  
✅ **Migration en <48h**  
✅ **Période de test gratuite de 30 jours**

---

## 2. Pourquoi Migrer vers AzalScore ? {#pourquoi-migrer}

### 2.1 Parité Fonctionnelle Garantie

AzalScore couvre **100% des fonctionnalités essentielles d'Axonaut** :

- ✅ CRM et Pipeline commercial
- ✅ Facturation complète (devis, factures, avoirs)
- ✅ Gestion achats fournisseurs
- ✅ Comptabilité et exports FEC
- ✅ Trésorerie et prévisions
- ✅ Multi-utilisateurs et RBAC
- ✅ API complète

### 2.2 Fonctionnalités Exclusives AzalScore

| Fonctionnalité | Axonaut | AzalScore | Impact Business |
|----------------|---------|-----------|-----------------|
| **Assistant IA (Theo)** | ❌ | ✅ | Automatisation workflows, gain 30% temps |
| **Auto-healing (Guardian)** | ❌ | ✅ | Détection anomalies automatique, -80% incidents |
| **Production/MRP** | ❌ | ✅ | Gestion complète fabrication |
| **E-commerce intégré** | ❌ | ✅ | Synchronisation automatique boutiques |
| **Field Service Management** | ⚠️ Limité | ✅ Complet | Planification techniciens optimisée |
| **Quality Control** | ❌ | ✅ | Contrôle qualité industriel |
| **Maintenance préventive** | ❌ | ✅ | Planning maintenance équipements |
| **Marketplace** | ❌ | ✅ | Extensions et intégrations |
| **API GraphQL** | ❌ REST | ✅ REST + GraphQL | Requêtes flexibles pour intégrations |

### 2.3 Avantages Techniques

#### Architecture Moderne
- **Multi-tenant natif** avec isolation stricte
- **API versionnée** (v1 et v2)
- **Performance optimisée** (PostgreSQL 15, Redis)
- **Scalabilité horizontale**

#### Sécurité Renforcée
- **Chiffrement end-to-end** des données sensibles
- **Audit trail complet** de toutes les actions
- **Conformité RGPD** avancée
- **Sauvegarde automatique** quotidienne

#### Intelligence Artificielle
- **Comptabilité automatique** via IA
- **Prédictions trésorerie** machine learning
- **Détection fraude** automatique
- **Suggestions smart** dans workflows

### 2.4 Tarification Compétitive

| Offre | Axonaut | AzalScore | Économie |
|-------|---------|-----------|----------|
| **Starter (1-3 users)** | 40€/mois | 35€/mois | -12% |
| **Business (4-10 users)** | 80€/mois | 70€/mois | -12% |
| **Enterprise (>10 users)** | Sur devis | Sur devis | -15% en moyenne |

**Offre spéciale migration** : **-25% la 1ère année** pour les clients Axonaut

---

## 3. Tableau de Correspondance des Fonctionnalités {#correspondances}

### 3.1 CRM & Commercial

| Fonction Axonaut | Équivalent AzalScore | Notes |
|------------------|----------------------|-------|
| Contacts clients | `/v2/commercial/contacts` | ✅ Identique |
| Pipeline ventes | `/v2/commercial/opportunities` | ✅ + Scoring IA |
| Devis | `/v2/commercial/documents?type=QUOTE` | ✅ + Templates avancés |
| Factures | `/v2/commercial/documents?type=INVOICE` | ✅ + Signature électronique |
| Avoirs | `/v2/commercial/documents?type=CREDIT_NOTE` | ✅ Identique |
| Catalogue produits | `/v2/commercial/products` | ✅ + Variantes |
| Remises | Champ `discount` dans DocumentLine | ✅ Identique |

### 3.2 Facturation & Paiements

| Fonction Axonaut | Équivalent AzalScore | Nouveautés |
|------------------|----------------------|------------|
| Numérotation auto | `SequenceGenerator` | ✅ + Personnalisation avancée |
| Multi-TVA | Gestion TVA par ligne | ✅ + Règles complexes |
| Multi-devises | Module `finance/currency` | ✅ + Taux auto + 150 devises |
| Échéancier paiement | `payment_terms` | ✅ Identique |
| Rappels factures | `/v1/notifications/reminders` | ✅ **NOUVEAU** - Automatique |
| Signature électronique | `/v1/esignature` | ✅ **NOUVEAU** - Yousign/DocuSign |

### 3.3 Trésorerie & Banque

| Fonction Axonaut | Équivalent AzalScore | Nouveautés |
|------------------|----------------------|------------|
| Comptes bancaires | `/v2/finance/accounts?type=BANK` | ✅ Identique |
| Rapprochement bancaire | `/v2/finance/bank-statements/reconcile` | ✅ + IA |
| Prévisions trésorerie | `/v2/finance/cash-forecasts` | ✅ + ML |
| Synchro bancaire | `/v1/banking-sync` | ✅ **NOUVEAU** - Auto via Budget Insight |

### 3.4 Comptabilité

| Fonction Axonaut | Équivalent AzalScore | Notes |
|------------------|----------------------|-------|
| Plan comptable | `/v2/finance/accounts` | ✅ + PCG français pré-configuré |
| Écritures comptables | `/v2/finance/entries` | ✅ + Comptabilité auto IA |
| Exercices fiscaux | `/v2/finance/fiscal-years` | ✅ Identique |
| Export FEC | `/v2/accounting/export/fec` | ✅ + Autres formats |
| Bilan/Compte résultat | `/v2/bi/financial-reports` | ✅ + Tableaux personnalisables |

### 3.5 Achats & Fournisseurs

| Fonction Axonaut | Équivalent AzalScore | Notes |
|------------------|----------------------|-------|
| Fournisseurs | `/v2/purchases/suppliers` | ✅ + Évaluation fournisseurs |
| Commandes fournisseurs | `/v2/purchases/orders` | ✅ + Workflow validation |
| Factures fournisseurs | `/v2/purchases/invoices` | ✅ + OCR automatique |
| Notes de frais | `/v2/hr/expenses` | ✅ + Validation mobile |

### 3.6 Stock & Inventaire

| Fonction Axonaut | Équivalent AzalScore | Nouveautés |
|------------------|----------------------|------------|
| Articles | `/v2/inventory/products` | ✅ + Variantes + Séries |
| Mouvements stock | `/v2/inventory/movements` | ✅ Identique |
| Inventaires | `/v2/inventory/physical-inventories` | ✅ + Mobile |
| Alertes seuils | `/v2/inventory/alerts` | ✅ **NOUVEAU** - Notifications auto |
| Multi-dépôts | Support natif | ✅ **NOUVEAU** |

### 3.7 RH & Administration

| Fonction Axonaut | Équivalent AzalScore | Notes |
|------------------|----------------------|-------|
| Employés | `/v2/hr/employees` | ✅ + Documents GED |
| Congés/absences | `/v2/hr/leaves` | ✅ + Workflow validation |
| Annuaire | `/v2/hr/directory` | ✅ + Organigramme |
| Utilisateurs | `/v1/iam/users` | ✅ + RBAC granulaire |
| Rôles/permissions | `/v1/iam/roles` | ✅ + Permissions par module |

---

## 4. Avantages Détaillés d'AzalScore {#avantages}

### 4.1 Intelligence Artificielle Intégrée

#### Assistant Theo
- **Génération automatique** de devis/factures par conversation
- **Analyse prédictive** des ventes et trésorerie
- **Suggestions contextuelles** dans tous les workflows
- **Réponses instantanées** aux questions métier

**Exemple d'usage** :
```
Utilisateur: "Crée une facture pour le client Acme Corp avec les produits du dernier devis"
Theo: "Facture F-2026-0042 créée, montant 1 250€ HT, échéance 30 jours. Envoi par email ?"
```

#### Guardian Auto-Healing
- **Détection automatique** des anomalies (doublons, incohérences)
- **Correction proactive** avant impact business
- **Alertes intelligentes** sur incidents
- **Tableau de bord santé** en temps réel

**ROI mesuré** : -80% incidents, -60% temps résolution

### 4.2 Modules Métier Avancés

#### Production & MRP
- Ordres de fabrication
- Nomenclatures multi-niveaux
- Gestion ateliers
- Calcul besoins matières

**Cas d'usage** : PME industrielles, artisans

#### Field Service Management
- Planning techniciens optimisé par IA
- Géolocalisation temps réel
- Application mobile interventions
- Suivi SLA

**Cas d'usage** : Maintenance, SAV, installations

#### E-commerce Intégré
- Synchronisation automatique Shopify, WooCommerce, PrestaShop
- Gestion stocks multicanaux
- Commandes web → ERP automatique
- Facturation automatisée

**Cas d'usage** : Commerce B2B/B2C

### 4.3 API & Intégrations

#### API REST + GraphQL
```graphql
# Exemple requête GraphQL
query {
  customer(id: "123") {
    name
    invoices(status: UNPAID) {
      number
      amount
      dueDate
    }
  }
}
```

#### Webhooks Sortants
- Événements temps réel (facture créée, paiement reçu, etc.)
- Configuration par tenant
- Retry automatique

#### Marketplace
- 50+ extensions disponibles
- Intégrations natives (Stripe, PayPal, Docusign, etc.)
- API ouverte pour développeurs

---

## 5. Étapes de Migration {#etapes}

### Phase 1 - Préparation (J-14 à J-7)

#### Actions Client
- [ ] Exporter données Axonaut (contacts, factures, produits)
- [ ] Lister utilisateurs et leurs rôles
- [ ] Identifier workflows critiques
- [ ] Valider date de migration

#### Actions AzalScore
- [ ] Créer tenant AzalScore
- [ ] Configurer paramètres (TVA, numérotation, etc.)
- [ ] Préparer mapping données
- [ ] Programmer session formation

**Livrables** : Plan de migration validé, accès tenant test

### Phase 2 - Migration Données (J-7 à J-1)

#### Import Automatisé
```bash
# Script d'import fourni par AzalScore
python migrate_from_axonaut.py \
  --source axonaut_export.json \
  --tenant-id "votre-tenant-id" \
  --dry-run  # Test sans import
```

#### Données Migrées
- ✅ Clients et prospects (+ historique)
- ✅ Fournisseurs
- ✅ Produits et services
- ✅ Factures (toutes)
- ✅ Devis en cours
- ✅ Paiements
- ✅ Plan comptable
- ✅ Écritures comptables (exercice en cours)
- ✅ Utilisateurs et rôles

#### Validation
- [ ] Vérifier compteurs de migration (clients, factures, etc.)
- [ ] Tester workflows critiques
- [ ] Valider exports comptables
- [ ] Revue par expert comptable

**Durée** : 2-4 heures selon volume

### Phase 3 - Formation Équipes (J-3 à J-1)

#### Session 1 - Utilisateurs Finaux (2h)
- Navigation interface
- CRM et facturation
- Consultation tableaux de bord
- Application mobile

#### Session 2 - Administrateurs (3h)
- Configuration avancée
- Gestion utilisateurs/permissions
- Personnalisation workflows
- Intégrations API

#### Session 3 - Comptables (2h)
- Écritures comptables
- Rapprochements bancaires
- Exports FEC/comptables
- Clôture exercice

**Format** : Visioconférence + Documentation + Vidéos

### Phase 4 - Bascule (J-Day)

#### Matin (9h-12h)
1. Dernière synchronisation données Axonaut
2. Import final dans AzalScore
3. Validation exhaustive
4. Activation comptes utilisateurs

#### Après-midi (14h-17h)
1. Connexion équipes
2. Tests opérationnels
3. Premier devis/facture
4. Support en direct

**Hotline dédiée** : Disponible 8h-20h

### Phase 5 - Accompagnement (J+1 à J+90)

#### Semaine 1
- Support quotidien
- Résolution questions/blocages
- Ajustements configuration

#### Mois 1
- Points hebdomadaires
- Optimisation workflows
- Formation complémentaire si besoin

#### Mois 2-3
- Support standard
- Revue satisfaction
- Identification améliorations

**SLA** : Réponse <4h, résolution critique <24h

---

## 6. Guide Technique de Migration {#guide-technique}

### 6.1 Export Données Axonaut

#### Via API Axonaut
```bash
# Endpoint export global
GET https://api.axonaut.com/v2/export/full

# Authentification
Authorization: Bearer YOUR_AXONAUT_API_KEY
```

#### Via Interface Web
1. Aller dans **Paramètres > Données**
2. Cliquer sur **Exporter mes données**
3. Sélectionner modules à exporter
4. Télécharger archive ZIP

**Format** : JSON ou CSV selon modules

### 6.2 Mapping des Données

#### Structure Axonaut → AzalScore

```json
{
  "axonaut_customer": {
    "id": "ax_123",
    "name": "Acme Corp",
    "email": "contact@acme.com"
  },
  "azalscore_customer": {
    "id": "uuid-generated",
    "tenant_id": "your-tenant",
    "name": "Acme Corp",
    "email": "contact@acme.com",
    "customer_type": "CUSTOMER"
  }
}
```

#### Champs Spécifiques

| Axonaut | AzalScore | Transformation |
|---------|-----------|----------------|
| `customer_id` | `id` (UUID) | Nouveau UUID généré |
| `invoice_number` | `document_number` | Préfixe ajouté si besoin |
| `amount` | `total_with_tax` | Conversion si devise |
| `status` | `status` (Enum) | Mapping statuts |

### 6.3 Script de Migration

```python
# Exemple script Python
import requests
import json
from datetime import datetime

AXONAUT_API = "https://api.axonaut.com/v2"
AZALSCORE_API = "https://api.azalscore.com/v2"

def migrate_customers(axonaut_token, azalscore_token, tenant_id):
    """Migre les clients d'Axonaut vers AzalScore."""
    
    # 1. Récupérer clients Axonaut
    response = requests.get(
        f"{AXONAUT_API}/customers",
        headers={"Authorization": f"Bearer {axonaut_token}"}
    )
    axonaut_customers = response.json()
    
    # 2. Créer dans AzalScore
    for customer in axonaut_customers:
        azal_customer = {
            "name": customer["name"],
            "email": customer.get("email"),
            "phone": customer.get("phone"),
            "address": customer.get("address"),
            "customer_type": "CUSTOMER",
            "metadata": {
                "axonaut_id": customer["id"],
                "migrated_at": datetime.utcnow().isoformat()
            }
        }
        
        response = requests.post(
            f"{AZALSCORE_API}/commercial/customers",
            headers={
                "Authorization": f"Bearer {azalscore_token}",
                "X-Tenant-ID": tenant_id
            },
            json=azal_customer
        )
        
        if response.status_code == 201:
            print(f"✅ Migré: {customer['name']}")
        else:
            print(f"❌ Erreur: {customer['name']} - {response.text}")

# Utilisation
migrate_customers(
    axonaut_token="YOUR_AXONAUT_TOKEN",
    azalscore_token="YOUR_AZALSCORE_TOKEN",
    tenant_id="your-tenant-id"
)
```

### 6.4 Validation Post-Migration

#### Checklist Technique

```sql
-- Vérifier nombre de clients
SELECT COUNT(*) FROM customers WHERE tenant_id = 'your-tenant';

-- Vérifier factures avec montants
SELECT 
    COUNT(*) as total_invoices,
    SUM(total_with_tax) as total_amount,
    MIN(document_date) as oldest_invoice,
    MAX(document_date) as newest_invoice
FROM commercial_documents
WHERE tenant_id = 'your-tenant' 
  AND document_type = 'INVOICE';

-- Vérifier écritures comptables
SELECT 
    fiscal_year,
    COUNT(*) as entry_count,
    SUM(CASE WHEN debit > 0 THEN debit ELSE 0 END) as total_debit,
    SUM(CASE WHEN credit > 0 THEN credit ELSE 0 END) as total_credit
FROM finance_entries
WHERE tenant_id = 'your-tenant'
GROUP BY fiscal_year;
```

#### Tests Fonctionnels

- [ ] Créer un devis
- [ ] Transformer devis en facture
- [ ] Enregistrer un paiement
- [ ] Générer un export FEC
- [ ] Créer une commande fournisseur
- [ ] Effectuer un rapprochement bancaire
- [ ] Consulter tableaux de bord

---

## 7. Formation et Support {#formation}

### 7.1 Ressources de Formation

#### Documentation
- **Guide utilisateur complet** : https://docs.azalscore.com
- **Tutoriels vidéo** : 50+ vidéos (3-10 min chacune)
- **Base de connaissances** : 200+ articles

#### Certification
- **Programme certification AzalScore** (optionnel)
- 3 niveaux : Utilisateur, Expert, Administrateur
- Badges numériques

### 7.2 Support Client

#### Canaux
- **Email** : support@azalscore.com (réponse <4h)
- **Chat** : Disponible dans l'application (9h-18h)
- **Téléphone** : +33 1 XX XX XX XX (urgences)
- **Ticketing** : Via module Helpdesk intégré

#### SLA Migration
- **Réponse** : <2h pendant période migration
- **Résolution P0** : <4h (blocant)
- **Résolution P1** : <24h (majeur)
- **Résolution P2** : <72h (mineur)

### 7.3 Communauté

- **Forum utilisateurs** : forum.azalscore.com
- **Webinaires mensuels** : Nouveautés et best practices
- **Newsletter** : Conseils et astuces hebdomadaires

---

## 8. FAQ {#faq}

### Questions Générales

**Q: Combien de temps prend la migration ?**  
R: 48h en moyenne (2h technique + 46h validation/formation).

**Q: Y a-t-il une interruption de service ?**  
R: Non, vous pouvez continuer sur Axonaut pendant la préparation. Bascule en <2h.

**Q: Mes données sont-elles sécurisées ?**  
R: Oui, chiffrement AES-256, hébergement certifié ISO 27001, sauvegarde quotidienne.

**Q: Puis-je revenir à Axonaut après migration ?**  
R: Oui pendant 90 jours, export complet des données possible.

### Questions Techniques

**Q: Les intégrations Axonaut fonctionnent-elles avec AzalScore ?**  
R: La plupart oui (Stripe, PayPal, etc.). Notre équipe vérifie et configure.

**Q: Mon expert-comptable pourra-t-il accéder aux données ?**  
R: Oui, accès RBAC configuré + export FEC compatible tous logiciels.

**Q: Les numéros de factures sont-ils conservés ?**  
R: Oui, préfixe ajouté si conflit avec séquences AzalScore.

**Q: La synchro bancaire remplace-t-elle l'import manuel ?**  
R: Oui, connexion OAuth2 à votre banque pour import automatique quotidien.

### Questions Commerciales

**Q: Quel est le coût de migration ?**  
R: Gratuit pour les abonnements annuels, 500€ pour abonnements mensuels.

**Q: Y a-t-il des frais cachés ?**  
R: Non, tout est inclus (migration, formation, support 3 mois).

**Q: Puis-je tester avant de migrer ?**  
R: Oui, 30 jours gratuits avec données de démonstration ou vos données réelles.

**Q: L'offre de réduction est-elle valable combien de temps ?**  
R: -25% la 1ère année, offre limitée aux 100 premiers clients migrés.

---

## 📞 Contact

### Équipe Migration
- **Email** : migration@azalscore.com
- **Téléphone** : +33 1 XX XX XX XX
- **Calendly** : https://calendly.com/azalscore/migration

### Demande de Devis
Remplissez le formulaire : https://azalscore.com/demande-migration-axonaut

---

**AzalScore** - ERP Nouvelle Génération  
*Votre succès, notre technologie* 🚀
