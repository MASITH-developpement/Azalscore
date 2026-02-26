# Guide Administrateur AZALSCORE

## Administration et Configuration du Systeme

---

# Table des Matieres

1. [Role de l'Administrateur](#1-role-de-ladministrateur)
2. [Gestion des Utilisateurs](#2-gestion-des-utilisateurs)
3. [Roles et Permissions](#3-roles-et-permissions)
4. [Configuration des Modules](#4-configuration-des-modules)
5. [Securite](#5-securite)
6. [Audit et Conformite](#6-audit-et-conformite)
7. [Sauvegardes et Restauration](#7-sauvegardes-et-restauration)
8. [Integrations](#8-integrations)
9. [Maintenance](#9-maintenance)
10. [Resolution de Problemes](#10-resolution-de-problemes)

---

# 1. Role de l'Administrateur

## Responsabilites

L'administrateur AZALSCORE est responsable de :

| Domaine | Responsabilites |
|---------|-----------------|
| **Utilisateurs** | Creation, modification, desactivation des comptes |
| **Acces** | Attribution des roles et permissions |
| **Configuration** | Parametrage des modules et workflows |
| **Securite** | Politiques de securite, 2FA, audit |
| **Donnees** | Sauvegardes, import/export |
| **Support** | Assistance niveau 1 aux utilisateurs |

## Acces Administrateur

L'administrateur dispose des droits suivants :
- `admin.users.*` - Gestion complete des utilisateurs
- `admin.roles.*` - Gestion des roles
- `admin.settings.*` - Configuration systeme
- `audit.read` - Consultation des logs
- `backup.*` - Gestion des sauvegardes

## Interface d'Administration

Acces : **Menu** > **Administration**

Sections disponibles :
- Utilisateurs
- Roles et Permissions
- Modules
- Parametres
- Audit
- Sauvegardes
- Guardian (Securite)

---

# 2. Gestion des Utilisateurs

## Liste des Utilisateurs

### Acces
Administration > Utilisateurs

### Vue d'Ensemble
| Colonne | Description |
|---------|-------------|
| Nom | Nom complet |
| Email | Adresse email (identifiant) |
| Roles | Roles attribues |
| Statut | Actif / Inactif / Verrouille |
| Derniere connexion | Date et heure |

### Filtres
- Par statut (Actif/Inactif)
- Par role
- Par date de creation
- Par derniere connexion

## Creer un Utilisateur

### Procedure

1. Cliquez sur **"+ Nouvel utilisateur"**

2. **Informations obligatoires** :
   ```
   Nom* : [Nom complet]
   Email* : [email@entreprise.com]
   Role(s)* : [Selectionner au moins un role]
   ```

3. **Informations optionnelles** :
   ```
   Telephone : [numero]
   Departement : [service]
   Manager : [superieur hierarchique]
   ```

4. **Options de securite** :
   ```
   [ ] Forcer changement mot de passe a la premiere connexion
   [ ] Activer 2FA obligatoire
   [ ] Definir une date d'expiration
   ```

5. Cliquez sur **"Creer"**

6. L'utilisateur recoit un email avec :
   - Lien d'activation
   - Instructions de premiere connexion

### Mot de Passe Initial

Deux options :
1. **Genere automatiquement** : Envoye par email
2. **Defini manuellement** : Vous le communiquez

> **Recommandation** : Utilisez la generation automatique + changement obligatoire.

## Modifier un Utilisateur

### Informations Modifiables

| Champ | Modifiable | Notes |
|-------|------------|-------|
| Nom | Oui | Mise a jour immediate |
| Email | Oui | Verification requise |
| Telephone | Oui | - |
| Roles | Oui | Effet immediat |
| Departement | Oui | - |
| Statut | Oui | Voir "Desactiver" |

### Reinitialiser le Mot de Passe

1. Ouvrez la fiche utilisateur
2. Cliquez sur **"Reinitialiser mot de passe"**
3. Options :
   - Envoyer un email de reinitialisation
   - Definir un mot de passe temporaire
4. Confirmez

## Desactiver un Utilisateur

### Quand Desactiver

- Depart de l'entreprise
- Changement de poste (avant nouvelle config)
- Suspension temporaire
- Probleme de securite

### Procedure

1. Ouvrez la fiche utilisateur
2. Cliquez sur **"Desactiver"**
3. Choisissez :
   - **Desactivation immediate** : Deconnexion forcee
   - **Desactivation planifiee** : A une date future
4. Ajoutez un motif (obligatoire)
5. Confirmez

### Effets de la Desactivation

- L'utilisateur ne peut plus se connecter
- Les sessions actives sont fermees
- Les donnees sont conservees
- Les documents attribues restent accessibles
- Le compte peut etre reactive

## Supprimer un Utilisateur

> **Attention** : La suppression est irreversible.

### Conditions
- Compte desactive depuis 30+ jours
- Aucun document en attente
- Validation par super-admin

### Procedure
1. Utilisateur desactive
2. Administration > Utilisateurs > Supprimes
3. Selectionnez l'utilisateur
4. Cliquez sur **"Supprimer definitivement"**
5. Double confirmation requise

### Alternative : Anonymisation
Pour conformite RGPD, preferez l'anonymisation :
1. Ouvrez la fiche
2. Actions > Anonymiser
3. Les donnees personnelles sont effacees
4. L'historique est conserve (sans identification)

---

# 3. Roles et Permissions

## Comprendre le Modele RBAC

AZALSCORE utilise le modele **Role-Based Access Control** :

```
Utilisateur → Roles → Permissions → Ressources
```

### Exemple
```
Jean DUPONT
└── Role: Commercial
    └── Permissions:
        ├── crm.customer.create
        ├── crm.customer.read
        ├── crm.customer.update
        ├── invoicing.quote.create
        ├── invoicing.quote.read
        └── invoicing.quote.send
```

## Roles Predefinies

| Role | Description | Niveau |
|------|-------------|--------|
| **SUPER_ADMIN** | Acces total | Systeme |
| **TENANT_ADMIN** | Admin du tenant | Tenant |
| **DIRIGEANT** | Direction | Strategique |
| **DAF** | Directeur Financier | Strategique |
| **DRH** | Directeur RH | Strategique |
| **RESPONSABLE_COMMERCIAL** | Manager ventes | Tactique |
| **COMPTABLE** | Service comptable | Operationnel |
| **COMMERCIAL** | Force de vente | Operationnel |
| **MAGASINIER** | Gestion stocks | Operationnel |
| **TECHNICIEN** | Interventions | Operationnel |
| **CONSULTANT** | Lecture seule | Consultation |
| **AUDITEUR** | Audit | Compliance |

## Structure des Permissions

Format : `module.ressource.action`

### Modules Principaux
```
iam         - Gestion identites
invoicing   - Facturation
treasury    - Tresorerie
accounting  - Comptabilite
hr          - Ressources humaines
inventory   - Stocks
production  - Production
projects    - Projets
crm         - Relation client
admin       - Administration
audit       - Audit
```

### Actions Standards
```
create  - Creer
read    - Lire
update  - Modifier
delete  - Supprimer
export  - Exporter
validate - Valider
admin   - Administrer
```

### Exemples de Permissions
```
invoicing.invoice.create    - Creer des factures
hr.employee.read           - Voir les employes
treasury.bank.reconcile    - Rapprocher les banques
audit.logs.read            - Consulter les logs
admin.users.create         - Creer des utilisateurs
```

## Creer un Role Personnalise

### Procedure

1. Accedez a **Administration** > **Roles**
2. Cliquez sur **"+ Nouveau role"**
3. Definissez :
   ```
   Nom : [Nom du role]
   Code : [CODE_ROLE]
   Description : [Usage prevu]
   ```
4. Selectionnez les permissions :
   - Parcourez par module
   - Cochez les permissions necessaires
5. Definissez la hierarchie :
   - Ce role herite de : [Role parent optionnel]
6. Enregistrez

### Bonnes Pratiques

1. **Principe du moindre privilege** : N'accordez que les permissions necessaires
2. **Nommage clair** : Le nom doit refleter la fonction
3. **Documentation** : Decrivez l'usage dans la description
4. **Heritage** : Utilisez l'heritage pour eviter la duplication
5. **Revue reguliere** : Auditez les roles periodiquement

## Attribuer des Roles

### A un Utilisateur

1. Ouvrez la fiche utilisateur
2. Onglet **Roles**
3. Cliquez sur **"+ Ajouter role"**
4. Selectionnez le(s) role(s)
5. Optionnel : Definissez une date d'expiration
6. Enregistrez

### En Masse

1. Administration > Utilisateurs
2. Selectionnez plusieurs utilisateurs
3. Actions > Attribuer role
4. Selectionnez le role
5. Appliquez

## Matrice des Permissions

Pour visualiser qui a acces a quoi :

1. Administration > Roles > Matrice
2. Lignes : Roles
3. Colonnes : Permissions
4. Intersection : ✓ = autorise

Export disponible en Excel pour audit.

---

# 4. Configuration des Modules

## Activer/Desactiver un Module

### Procedure

1. Administration > Modules
2. Localisez le module
3. Basculez l'interrupteur ON/OFF
4. Confirmez

### Effets
- **Activation** : Module accessible selon permissions
- **Desactivation** :
  - Menu masque
  - API desactivees
  - Donnees conservees

## Parametres par Module

### Acces
Administration > Modules > [Module] > Parametres

### Parametres Communs

| Parametre | Description |
|-----------|-------------|
| Numerotation | Format des numeros (ex: FAC-{YYYY}-{####}) |
| Validation | Workflows d'approbation |
| Notifications | Alertes email/push |
| Integration | Connexions externes |
| Retention | Duree de conservation |

### Exemple : Facturation

```yaml
Numerotation:
  Prefixe: FAC
  Format: {ANNEE}-{SEQUENCE:4}
  Exemple: FAC-2026-0001

Validation:
  Seuil_validation: 10000 EUR
  Valideur: Responsable Commercial

Email:
  Template_envoi: facture_client_v2
  Relance_auto: true
  Delai_relance: 15 jours
```

## Configuration des Workflows

### Types de Workflows

1. **Approbation** : Validation avant action
2. **Notification** : Alerte sur evenement
3. **Automatisation** : Action automatique

### Creer un Workflow d'Approbation

1. Administration > Workflows > + Nouveau
2. Configurez :
   ```
   Nom: Validation devis > 5000 EUR
   Module: Devis
   Declencheur: Creation
   Condition: montant_total > 5000
   Action: Demande approbation
   Approbateur: Responsable Commercial
   ```
3. Testez avec un cas reel
4. Activez

---

# 5. Securite

## Politique de Mots de Passe

### Configuration

Administration > Securite > Mots de passe

| Parametre | Valeur Recommandee |
|-----------|-------------------|
| Longueur minimale | 12 caracteres |
| Majuscules requises | Oui (1+) |
| Minuscules requises | Oui (1+) |
| Chiffres requis | Oui (1+) |
| Caracteres speciaux | Oui (1+) |
| Expiration | 90 jours |
| Historique | 5 derniers |
| Verrouillage apres | 5 echecs |
| Duree verrouillage | 15 minutes |

### Application

Les regles s'appliquent :
- A la creation de compte
- Au changement de mot de passe
- A la reinitialisation

## Authentification a Deux Facteurs (2FA)

### Configuration Globale

Administration > Securite > 2FA

Options :
- **Desactive** : Pas de 2FA
- **Optionnel** : L'utilisateur choisit
- **Obligatoire** : Tous les utilisateurs
- **Par role** : Obligatoire pour certains roles

### Methodes Disponibles

| Methode | Securite | Facilite |
|---------|----------|----------|
| Application (TOTP) | ★★★★★ | ★★★☆☆ |
| SMS | ★★★☆☆ | ★★★★★ |
| Email | ★★☆☆☆ | ★★★★★ |

> **Recommandation** : Application TOTP (Google Authenticator, Authy)

### Forcer 2FA pour un Utilisateur

1. Ouvrez la fiche utilisateur
2. Securite > Activer 2FA obligatoire
3. L'utilisateur devra configurer a la prochaine connexion

## Sessions et Connexions

### Parametres de Session

| Parametre | Description | Defaut |
|-----------|-------------|--------|
| Duree session | Temps avant deconnexion auto | 8 heures |
| Inactivite | Deconnexion apres inactivite | 30 min |
| Sessions simultanees | Nombre max par utilisateur | 3 |
| IP fixe | Restreindre a certaines IP | Non |

### Surveiller les Sessions

Administration > Securite > Sessions actives

Affiche :
- Utilisateurs connectes
- Adresse IP
- Navigateur
- Duree

Action : **Forcer deconnexion** si necessaire

## Restrictions IP

### Whitelist IP

Pour restreindre l'acces a certaines adresses :

1. Administration > Securite > Restrictions IP
2. Mode : Liste blanche
3. Ajoutez les IP/plages autorisees :
   ```
   192.168.1.0/24
   203.0.113.50
   ```
4. Activez

> **Attention** : Testez avant d'activer pour eviter de vous bloquer.

---

# 6. Audit et Conformite

## Journal d'Audit

### Acces
Administration > Audit > Journal

### Informations Enregistrees

Chaque action genere une entree :
```json
{
  "timestamp": "2026-02-23T14:30:00Z",
  "user_id": "uuid",
  "user_email": "jean@entreprise.com",
  "action": "UPDATE",
  "resource": "invoice",
  "resource_id": "uuid",
  "ip_address": "192.168.1.100",
  "user_agent": "Chrome/...",
  "changes": {
    "status": {"old": "draft", "new": "sent"}
  }
}
```

### Recherche dans les Logs

Filtres disponibles :
- Periode
- Utilisateur
- Type d'action
- Module/Ressource
- Adresse IP

### Export

1. Definissez vos filtres
2. Cliquez sur **Exporter**
3. Format : CSV ou JSON
4. Usage : Audit externe, conformite

## Rapports de Conformite

### RGPD

Administration > Conformite > RGPD

Fonctionnalites :
- **Registre des traitements** : Liste des donnees personnelles
- **Droits des personnes** : Gestion des demandes (acces, rectification, suppression)
- **Consentements** : Suivi des consentements
- **Violations** : Registre des incidents

### SOC2 / ISO27001

Rapports pre-formates pour :
- Controle d'acces
- Gestion des incidents
- Continuite d'activite
- Cryptographie

## Alertes de Securite

### Configuration

Administration > Guardian > Alertes

Types d'alertes :
- Connexions echouees multiples
- Connexion depuis nouvelle IP
- Acces hors horaires
- Export massif de donnees
- Modification de permissions

### Destinataires

Definissez qui recoit les alertes :
- Administrateurs
- Equipe securite
- Webhook externe (SIEM)

---

# 7. Sauvegardes et Restauration

## Politique de Sauvegarde

### Sauvegardes Automatiques

AZALSCORE effectue :

| Type | Frequence | Retention |
|------|-----------|-----------|
| Complete | Quotidienne (02:00) | 30 jours |
| Incrementale | Toutes les heures | 7 jours |
| Logs | Temps reel | 90 jours |

### Stockage

- Stockage principal : Serveurs AZALSCORE
- Replique : Zone geographique secondaire
- Chiffrement : AES-256

## Sauvegarde Manuelle

### Procedure

1. Administration > Sauvegardes > + Nouvelle
2. Selectionnez le scope :
   - [ ] Tout
   - [ ] Configuration uniquement
   - [ ] Donnees metier
   - [ ] Fichiers joints
3. Lancez la sauvegarde
4. Attendez la completion
5. Telechargez si necessaire

## Restauration

### Types de Restauration

| Type | Usage | Impact |
|------|-------|--------|
| Complete | Catastrophe | Ecrase tout |
| Module | Probleme module | Module specifique |
| Document | Erreur utilisateur | Document unique |

### Procedure de Restauration Complete

> **Attention** : Operation critique. Contactez le support.

1. Administration > Sauvegardes > Restaurer
2. Selectionnez le point de restauration
3. Validez les avertissements
4. Entrez le code de confirmation
5. La restauration demarre
6. Temps estime affiche
7. Verification post-restauration

### Restauration Granulaire

Pour restaurer un element specifique :

1. Administration > Sauvegardes > Historique
2. Selectionnez la date
3. Parcourez les donnees
4. Selectionnez l'element
5. Cliquez sur **Restaurer**
6. Choisissez : Ecraser ou Creer copie

## Test de Restauration

### Bonne Pratique

Testez la restauration periodiquement :

1. Exportez une sauvegarde
2. Restaurez dans un environnement de test
3. Verifiez l'integrite des donnees
4. Documentez le resultat

Frequence recommandee : Trimestrielle

---

# 8. Integrations

## API et Webhooks

### Cles API

Administration > Integrations > API

#### Creer une Cle API

1. Cliquez sur **"+ Nouvelle cle"**
2. Renseignez :
   - Nom : [Usage prevu]
   - Permissions : [Scope limite]
   - Expiration : [Date optionnelle]
3. Generez
4. **Copiez immediatement** (affichee une seule fois)

#### Bonnes Pratiques API

- Une cle par integration
- Permissions minimales
- Rotation reguliere (90 jours)
- Surveillance des usages

### Webhooks

Administration > Integrations > Webhooks

#### Configurer un Webhook

1. Cliquez sur **"+ Nouveau webhook"**
2. Configurez :
   ```
   URL: https://votre-serveur.com/webhook
   Evenements:
     [x] invoice.created
     [x] invoice.paid
   Secret: [genere automatiquement]
   ```
3. Testez avec **"Envoyer test"**
4. Activez

## Integrations Natives

### Email (SMTP)

Administration > Integrations > Email

```yaml
Serveur SMTP: smtp.entreprise.com
Port: 587
Securite: STARTTLS
Utilisateur: notifications@entreprise.com
Mot de passe: ****
Email expediteur: noreply@entreprise.com
```

### Stockage Cloud

Connexion a :
- Google Drive
- OneDrive
- Dropbox
- S3 compatible

### Comptabilite

Export vers :
- Sage
- Cegid
- QuickBooks
- Format FEC

### CRM

Synchronisation avec :
- Salesforce
- HubSpot
- Pipedrive

## Import de Donnees

### Sources Supportees

| Source | Type | Disponibilite |
|--------|------|---------------|
| Odoo | Migration complete | Natif |
| Axonaut | Migration complete | Natif |
| Pennylane | Comptabilite | Natif |
| Sage | Comptabilite | Via CSV |
| Excel/CSV | Donnees generiques | Universel |

### Procedure d'Import

1. Administration > Import > [Source]
2. Telechargez le modele ou connectez l'API
3. Mappez les champs
4. Previsualisation
5. Importez (par lots si volumineux)
6. Rapport d'import

---

# 9. Maintenance

## Surveillance Systeme

### Tableau de Bord Guardian

Administration > Guardian > Dashboard

Indicateurs :
- Sante globale : Vert/Orange/Rouge
- Temps de reponse API
- Erreurs recentes
- Utilisation ressources

### Alertes Automatiques

Guardian detecte :
- Degradation performances
- Erreurs recurrentes
- Tentatives d'intrusion
- Anomalies donnees

## Taches de Maintenance

### Quotidiennes (Automatiques)
- Sauvegarde incrementale
- Nettoyage sessions expirees
- Rotation logs

### Hebdomadaires (Automatiques)
- Sauvegarde complete
- Optimisation indexes
- Rapport d'activite

### Mensuelles (Manuelles Recommandees)
- [ ] Revue des utilisateurs inactifs
- [ ] Audit des permissions
- [ ] Test de restauration
- [ ] Revue des alertes securite

### Annuelles
- [ ] Revue complete des roles
- [ ] Mise a jour politique securite
- [ ] Formation utilisateurs
- [ ] Audit externe

## Mise a Jour

### Cycle de Release

AZALSCORE publie :
- **Patches** : Corrections critiques (immediat)
- **Minor** : Fonctionnalites (mensuel)
- **Major** : Evolutions (semestriel)

### Notification

Vous etes informe par :
- Email administrateur
- Banner dans l'interface
- Changelog disponible

### Application

Les mises a jour sont appliquees automatiquement avec :
- Fenetre de maintenance annoncee
- Rollback automatique si probleme

---

# 10. Resolution de Problemes

## Problemes Courants

### Utilisateur ne peut pas se connecter

**Diagnostic :**
1. Verifiez le statut (actif ?)
2. Compte verrouille ?
3. Mot de passe expire ?
4. 2FA problematique ?

**Solutions :**
- Reactiver le compte
- Deverrouiller (Administration > Utilisateurs)
- Reinitialiser mot de passe
- Desactiver temporairement 2FA

### Permission refusee

**Diagnostic :**
1. L'utilisateur a-t-il le role necessaire ?
2. La permission est-elle dans le role ?
3. Le module est-il actif ?

**Solution :**
- Ajoutez le role ou la permission manquante
- Verifiez l'activation du module

### Lenteur du systeme

**Diagnostic :**
1. Consultez Guardian > Performances
2. Verifiez les logs d'erreur
3. Identifiez les requetes lentes

**Solutions :**
- Contactez le support si infrastructure
- Optimisez les rapports lourds
- Planifiez les exports en heure creuse

### Donnees manquantes

**Diagnostic :**
1. Donnees supprimees ? (Audit)
2. Filtres actifs ?
3. Permissions insuffisantes ?

**Solutions :**
- Restauration depuis sauvegarde
- Verifiez les filtres
- Ajustez les permissions

## Escalade Support

### Niveaux de Support

| Niveau | Qui | Delai |
|--------|-----|-------|
| N1 | Admin interne | Immediat |
| N2 | Support AZALSCORE | < 4h |
| N3 | Equipe technique | < 24h |

### Comment Contacter le Support

1. **Chat** : Icone 💬 (heures ouvrables)
2. **Email** : support@azalscore.com
3. **Telephone** : Numero d'urgence (critiques)

### Informations a Fournir

```
- Description du probleme
- Etapes pour reproduire
- Messages d'erreur (captures)
- Utilisateurs impactes
- Date/heure de debut
- Actions deja tentees
```

## Logs Techniques

### Acces aux Logs

Administration > Audit > Logs techniques

### Types de Logs

| Log | Contenu | Retention |
|-----|---------|-----------|
| Application | Erreurs, warnings | 30 jours |
| Acces | Connexions, API calls | 90 jours |
| Securite | Alertes, incidents | 1 an |
| Performance | Temps reponse, lenteurs | 7 jours |

### Export pour Analyse

1. Selectionnez le type de log
2. Definissez la periode
3. Exportez en JSON
4. Analysez ou transmettez au support

---

# Checklist Administrateur

## Setup Initial

- [ ] Configurer la politique de mots de passe
- [ ] Activer 2FA pour les admins
- [ ] Creer les roles necessaires
- [ ] Importer les utilisateurs
- [ ] Configurer les modules actifs
- [ ] Parametrer les workflows
- [ ] Configurer les emails
- [ ] Tester une sauvegarde/restauration

## Maintenance Reguliere

### Quotidien
- [ ] Verifier les alertes Guardian
- [ ] Traiter les demandes utilisateurs

### Hebdomadaire
- [ ] Revue des connexions echouees
- [ ] Verifier les sauvegardes

### Mensuel
- [ ] Audit des utilisateurs inactifs
- [ ] Revue des permissions
- [ ] Mise a jour documentation

### Trimestriel
- [ ] Test de restauration
- [ ] Formation nouveaux arrivants
- [ ] Revue politique securite

---

*Guide Administrateur AZALSCORE v2.0*
*Fevrier 2026*
