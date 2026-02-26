# Guide de Formation Utilisateur AZALSCORE

## ERP Decisionnel Nouvelle Generation

**Version** : 2.0
**Date** : Fevrier 2026
**Public cible** : Utilisateurs finaux, Managers, Administrateurs

---

# Table des Matieres

1. [Introduction a AZALSCORE](#1-introduction-a-azalscore)
2. [Premiers Pas](#2-premiers-pas)
3. [Navigation et Interface](#3-navigation-et-interface)
4. [Modules de Gestion Commerciale](#4-modules-de-gestion-commerciale)
5. [Modules Financiers](#5-modules-financiers)
6. [Modules Operations et Logistique](#6-modules-operations-et-logistique)
7. [Modules Ressources Humaines](#7-modules-ressources-humaines)
8. [Modules Intelligence et IA](#8-modules-intelligence-et-ia)
9. [Modules Communication et Digital](#9-modules-communication-et-digital)
10. [Administration et Securite](#10-administration-et-securite)
11. [Workflows et Automatisations](#11-workflows-et-automatisations)
12. [Annexes](#12-annexes)

---

# 1. Introduction a AZALSCORE

## 1.1 Presentation Generale

AZALSCORE est un **ERP decisionnel SaaS** de nouvelle generation concu pour les PME et ETI. Il combine les fonctionnalites classiques d'un ERP avec des outils d'intelligence artificielle pour automatiser les taches repetitives et faciliter la prise de decision.

### Caracteristiques Principales

| Caracteristique | Description |
|-----------------|-------------|
| **Multi-tenant** | Chaque entreprise dispose de son espace isole et securise |
| **Multi-langue** | Interface disponible en 60+ langues |
| **Multi-pays** | Conformite legale et fiscale par pays (France, etc.) |
| **IA Integree** | Assistants intelligents Theo et Marceau |
| **Temps reel** | Donnees synchronisees instantanement |
| **Mobile-ready** | Interface responsive, accessible sur tous appareils |

### Architecture Modulaire

AZALSCORE est compose de **82+ modules** organises en categories :

```
AZALSCORE
├── Gestion Commerciale (CRM, Devis, Factures, Commandes)
├── Finance (Comptabilite, Tresorerie, Immobilisations)
├── Operations (Stock, Production, Maintenance, Qualite)
├── Ressources Humaines (Employes, Paie, Conges)
├── Intelligence (BI, Cockpit, IA)
├── Digital (Site Web, E-commerce, Reseaux Sociaux)
├── Support (Helpdesk, Reclamations)
└── Administration (Utilisateurs, Securite, Audit)
```

## 1.2 Concepts Cles

### Tenant (Locataire)
Votre entreprise dispose d'un espace dedie appele "tenant". Toutes vos donnees sont isolees des autres entreprises.

### Roles et Permissions
Chaque utilisateur a un ou plusieurs roles qui determinent ses droits d'acces. Les roles predefinies incluent :

| Role | Description | Acces typique |
|------|-------------|---------------|
| **Dirigeant** | Direction generale | Cockpit, Finance, tous rapports |
| **DAF** | Directeur Financier | Comptabilite, Tresorerie, Budget |
| **DRH** | Directeur RH | RH, Paie, Recrutement |
| **Commercial** | Force de vente | CRM, Devis, Commandes |
| **Comptable** | Service comptable | Ecritures, Rapprochement |
| **Magasinier** | Gestion stocks | Inventaire, Mouvements |
| **Technicien** | Service terrain | Interventions, Rapports |

### Documents
AZALSCORE gere plusieurs types de documents commerciaux :
- **Devis** : Propositions commerciales
- **Commandes** : Bons de commande clients/fournisseurs
- **Factures** : Documents de facturation
- **Avoirs** : Notes de credit

---

# 2. Premiers Pas

## 2.1 Connexion

### Acces a l'Application

1. Ouvrez votre navigateur (Chrome, Firefox, Edge recommandes)
2. Rendez-vous sur **https://azalscore.com**
3. Cliquez sur **"Se connecter"**

### Ecran de Connexion

![Login](images/login.png)

1. **Email** : Saisissez votre adresse email professionnelle
2. **Mot de passe** : Entrez votre mot de passe
3. Cliquez sur **"Connexion"**

### Authentification a Deux Facteurs (2FA)

Si active, vous recevrez un code par :
- **Email** : Code envoye a votre adresse
- **SMS** : Code envoye sur votre telephone
- **Application** : Code genere par une app d'authentification

Saisissez le code a 6 chiffres pour continuer.

### Mot de Passe Oublie

1. Cliquez sur **"Mot de passe oublie ?"**
2. Entrez votre email
3. Cliquez sur **"Reinitialiser"**
4. Consultez votre boite mail pour le lien de reinitialisation

## 2.2 Premier Lancement

Lors de votre premiere connexion :

1. **Acceptation des CGU** : Lisez et acceptez les conditions
2. **Configuration du profil** : Verifiez vos informations
3. **Tutoriel interactif** : Suivez le guide de bienvenue (optionnel)

## 2.3 Deconnexion

Pour vous deconnecter en securite :

1. Cliquez sur votre **avatar** (coin superieur droit)
2. Selectionnez **"Deconnexion"**

> **Securite** : Deconnectez-vous toujours sur un ordinateur partage.

---

# 3. Navigation et Interface

## 3.1 Modes d'Affichage

AZALSCORE propose **deux modes d'interface** :

### Mode AZALSCORE (Simplifie)

Interface epuree avec menu horizontal, ideale pour :
- Utilisateurs occasionnels
- Acces rapide aux fonctions principales
- Ecrans de petite taille

**Menu principal** :
- **Cockpit** : Tableau de bord executif
- **Actions** : Acces rapides (nouvelle facture, nouveau client...)
- **Vue d'ensemble** : Acces aux sections principales
- **Parametres** : Configuration

### Mode ERP (Complet)

Interface complete avec barre laterale, pour :
- Utilisateurs intensifs
- Acces a tous les modules
- Navigation hierarchique

**Changer de mode** :
1. Cliquez sur votre avatar
2. Selectionnez **"Basculer en mode ERP"** ou **"Basculer en mode AZALSCORE"**

## 3.2 Elements de l'Interface

### En-tete (Header)

```
┌─────────────────────────────────────────────────────────────────┐
│ [Logo AZALSCORE]  [Mode Badge]  [Recherche]  [🔔]  [Avatar ▼]  │
└─────────────────────────────────────────────────────────────────┘
```

| Element | Fonction |
|---------|----------|
| Logo | Retour a l'accueil |
| Mode Badge | Indique le mode actuel (AZALSCORE/ERP) |
| Recherche | Recherche globale (clients, documents, produits) |
| Cloche | Notifications non lues |
| Avatar | Menu utilisateur |

### Menu Lateral (Mode ERP)

Le menu est organise en **10 sections** :

1. **PRINCIPAL** : Cockpit, Assistant IA
2. **GESTION** : Partenaires, Facturation, Achats, RH
3. **FINANCE** : Tresorerie, Comptabilite
4. **LOGISTIQUE** : Stock, Production, Qualite, Maintenance
5. **OPERATIONS** : Projets, Interventions, Support
6. **VENTES** : POS, E-commerce, Abonnements
7. **DIGITAL** : Site Web, BI, Conformite
8. **COMMUNICATION** : Email, Signature electronique
9. **IMPORT** : Migration depuis autres systemes
10. **ADMINISTRATION** : Utilisateurs, Securite, Audit

### Zone de Contenu

La zone principale affiche le contenu du module selectionne :
- **Listes** : Tableaux avec tri, filtres, pagination
- **Formulaires** : Saisie et modification de donnees
- **Tableaux de bord** : Graphiques et indicateurs
- **Details** : Fiches completes d'un element

## 3.3 Recherche Globale

### Utilisation

1. Cliquez dans la barre de recherche ou appuyez sur **`/`** ou **`Cmd+K`**
2. Tapez votre recherche (nom client, numero facture, produit...)
3. Les resultats s'affichent en temps reel
4. Cliquez sur un resultat pour y acceder

### Types de Recherche

| Prefixe | Type | Exemple |
|---------|------|---------|
| (aucun) | Global | `Martin` |
| `@` | Client | `@Martin` |
| `#` | Document | `#FAC-2026-001` |
| `$` | Produit | `$Climatisation` |

## 3.4 Raccourcis Clavier

| Raccourci | Action |
|-----------|--------|
| `/` ou `Cmd+K` | Ouvrir la recherche |
| `Escape` | Fermer dialogue/modal |
| `Cmd+S` | Sauvegarder (dans formulaires) |
| `Cmd+N` | Nouveau (selon contexte) |
| `?` | Aide contextuelle |

## 3.5 Notifications

### Types de Notifications

| Icone | Type | Description |
|-------|------|-------------|
| 🔵 | Information | Message informatif |
| 🟢 | Succes | Action reussie |
| 🟡 | Avertissement | Attention requise |
| 🔴 | Erreur | Probleme a corriger |

### Gerer les Notifications

1. Cliquez sur la **cloche** 🔔
2. Consultez la liste des notifications
3. Cliquez sur une notification pour voir les details
4. **"Tout marquer comme lu"** pour effacer

---

# 4. Modules de Gestion Commerciale

## 4.1 CRM - Gestion de la Relation Client

### Acces
Menu > **Modules** > **CRM / Clients**

### Fonctionnalites

#### Liste des Clients
- Vue tableau de tous les clients
- Filtres par statut, secteur, commercial
- Recherche par nom, email, telephone
- Export Excel/CSV

#### Fiche Client

| Section | Contenu |
|---------|---------|
| **Identite** | Raison sociale, SIRET, adresse |
| **Contacts** | Personnes de contact |
| **Commercial** | Commercial assigne, conditions |
| **Historique** | Devis, commandes, factures |
| **Notes** | Commentaires internes |

#### Actions Disponibles
- **Nouveau client** : Creer une fiche client
- **Modifier** : Mettre a jour les informations
- **Archiver** : Desactiver sans supprimer
- **Fusion** : Fusionner des doublons
- **Export** : Telecharger la fiche

### Creer un Nouveau Client

1. Cliquez sur **"+ Nouveau client"**
2. Remplissez les champs obligatoires (*) :
   - Raison sociale*
   - Type (Entreprise/Particulier)*
   - Email*
3. Completez les informations optionnelles
4. Cliquez sur **"Enregistrer"**

## 4.2 Devis

### Acces
Menu > **Gestion** > **Devis**

### Cycle de Vie d'un Devis

```
Brouillon → Envoye → Accepte → Converti en Commande
                  ↘ Refuse
                  ↘ Expire
```

### Creer un Devis

1. Cliquez sur **"+ Nouveau devis"**
2. Selectionnez le **client**
3. Ajoutez les **lignes** :
   - Produit ou service
   - Quantite
   - Prix unitaire
   - Remise (optionnel)
4. Verifiez les **totaux** (HT, TVA, TTC)
5. Ajoutez des **conditions** (validite, delai...)
6. **Enregistrez** ou **Envoyez** directement

### Convertir en Commande

1. Ouvrez un devis **Accepte**
2. Cliquez sur **"Convertir en commande"**
3. Verifiez les informations
4. Confirmez la creation

## 4.3 Commandes

### Acces
Menu > **Gestion** > **Commandes**

### Types de Commandes

| Type | Description |
|------|-------------|
| **Client** | Commande recue d'un client |
| **Fournisseur** | Commande passee a un fournisseur |

### Statuts

| Statut | Signification |
|--------|---------------|
| Brouillon | En cours de creation |
| Confirmee | Validee, en attente traitement |
| En cours | Traitement en cours |
| Livree | Marchandises expediees/recues |
| Facturee | Facture emise |
| Annulee | Commande annulee |

### Suivi des Commandes

1. Accedez a la liste des commandes
2. Utilisez les **filtres** par statut
3. Cliquez sur une commande pour les details
4. Consultez l'**historique** des actions

## 4.4 Factures

### Acces
Menu > **Gestion** > **Factures**

### Creer une Facture

#### Depuis une Commande
1. Ouvrez une commande **Livree**
2. Cliquez sur **"Generer facture"**
3. Verifiez et validez

#### Facture Libre
1. Cliquez sur **"+ Nouvelle facture"**
2. Selectionnez le client
3. Ajoutez les lignes
4. Enregistrez

### Envoyer une Facture

1. Ouvrez la facture
2. Cliquez sur **"Envoyer"**
3. Choisissez le mode :
   - **Email** : Envoi par email avec PDF
   - **Chorus Pro** : Transmission electronique (secteur public)
   - **Telecharger** : PDF a envoyer manuellement

### Suivi des Paiements

| Statut | Description |
|--------|-------------|
| A payer | En attente de reglement |
| Partiellement payee | Paiement partiel recu |
| Payee | Integralement reglee |
| En retard | Echeance depassee |

### Relances

1. Filtrez les factures **En retard**
2. Selectionnez les factures
3. Cliquez sur **"Relancer"**
4. Choisissez le modele de relance
5. Envoyez

## 4.5 Saisie Rapide

### Acces
Menu > **Saisie** > **Nouvelle saisie**

### Fonctionnalite

La **saisie rapide** permet de creer un devis en quelques clics :

1. **Recherchez** ou creez un client
2. **Ajoutez** les articles depuis le catalogue
3. **Validez** les quantites et prix
4. **Creez** le devis instantanement

Ideal pour les ventes en clientele ou au telephone.

---

# 5. Modules Financiers

## 5.1 Tresorerie

### Acces
Menu > **Finance** > **Tresorerie**

### Tableau de Bord Tresorerie

| Indicateur | Description |
|------------|-------------|
| **Solde total** | Cumul de tous les comptes |
| **A recevoir** | Factures clients non payees |
| **A payer** | Factures fournisseurs dues |
| **Prevision J+30** | Solde prevu a 30 jours |

### Comptes Bancaires

#### Ajouter un Compte
1. Cliquez sur **"+ Nouveau compte"**
2. Renseignez :
   - Nom du compte
   - Banque
   - IBAN
   - Solde initial
3. Enregistrez

#### Rapprochement Bancaire
1. Importez le releve bancaire (CSV, OFX, QIF)
2. AZALSCORE propose des **correspondances automatiques**
3. Validez ou corrigez les associations
4. Marquez les operations rapprochees

### Previsions de Tresorerie

Le module genere des previsions basees sur :
- Factures a encaisser (clients)
- Factures a payer (fournisseurs)
- Echeances recurrentes (loyers, salaires...)
- Tendances historiques

## 5.2 Comptabilite

### Acces
Menu > **Finance** > **Comptabilite**

### Plan Comptable

AZALSCORE integre le **Plan Comptable General (PCG)** francais avec possibilite de personnalisation.

| Classe | Description |
|--------|-------------|
| 1 | Comptes de capitaux |
| 2 | Comptes d'immobilisations |
| 3 | Comptes de stocks |
| 4 | Comptes de tiers |
| 5 | Comptes financiers |
| 6 | Comptes de charges |
| 7 | Comptes de produits |

### Saisie d'Ecritures

1. Accedez au **Journal**
2. Cliquez sur **"+ Nouvelle ecriture"**
3. Renseignez :
   - Date
   - Journal (Achats, Ventes, Banque...)
   - Libelle
   - Lignes debit/credit
4. Verifiez l'equilibre (Debit = Credit)
5. Validez

### Etats Comptables

| Etat | Description |
|------|-------------|
| **Balance** | Soldes de tous les comptes |
| **Grand Livre** | Detail des mouvements par compte |
| **Journal** | Ecritures chronologiques |
| **Bilan** | Situation patrimoniale |
| **Compte de resultat** | Performances de l'exercice |

### Cloture d'Exercice

1. Verifiez que toutes les ecritures sont validees
2. Lancez les controles de coherence
3. Generez les etats de cloture
4. Passez les ecritures de cloture
5. Ouvrez le nouvel exercice

## 5.3 Immobilisations

### Acces
Menu > **Finance** > **Immobilisations**

### Gerer les Actifs

#### Creer une Immobilisation
1. Cliquez sur **"+ Nouvelle immobilisation"**
2. Renseignez :
   - Designation
   - Date d'acquisition
   - Valeur d'origine
   - Compte comptable
   - Duree d'amortissement
   - Mode (lineaire, degressif)
3. Enregistrez

#### Calcul des Amortissements
AZALSCORE calcule automatiquement :
- Dotations mensuelles/annuelles
- Valeur nette comptable
- Echeancier d'amortissement

#### Sortie d'Actif
1. Selectionnez l'immobilisation
2. Cliquez sur **"Sortir"**
3. Indiquez le motif (cession, mise au rebut)
4. Renseignez le prix de cession si applicable
5. Validez la sortie

## 5.4 Notes de Frais

### Acces
Menu > **Finance** > **Notes de Frais**

### Soumettre une Note de Frais

1. Cliquez sur **"+ Nouvelle note"**
2. Ajoutez les depenses :
   - Date
   - Type (transport, repas, hebergement...)
   - Montant
   - Justificatif (photo/scan)
3. Soumettez pour validation

### Workflow de Validation

```
Brouillon → Soumise → En validation → Approuvee → Remboursee
                              ↘ Refusee
```

### Approbation (Managers)

1. Accedez aux notes **En attente**
2. Examinez les depenses et justificatifs
3. **Approuvez** ou **Refusez** avec commentaire

---

# 6. Modules Operations et Logistique

## 6.1 Gestion des Stocks

### Acces
Menu > **Logistique** > **Stock**

### Catalogue Produits

#### Structure
```
Categories
└── Sous-categories
    └── Produits
        └── Variantes
```

#### Fiche Produit

| Champ | Description |
|-------|-------------|
| **Reference** | Code unique |
| **Designation** | Nom du produit |
| **Categorie** | Classification |
| **Prix d'achat** | Cout d'acquisition |
| **Prix de vente** | Prix public HT |
| **Stock minimum** | Seuil de reapprovisionnement |
| **Emplacement** | Localisation entrepot |

### Mouvements de Stock

| Type | Description |
|------|-------------|
| **Entree** | Reception marchandises |
| **Sortie** | Expedition, consommation |
| **Transfert** | Entre entrepots |
| **Ajustement** | Correction inventaire |

### Inventaire

1. Accedez a **Stock** > **Inventaire**
2. Creez une **session d'inventaire**
3. Scannez ou saisissez les quantites
4. Validez les ecarts
5. Generez les ecritures d'ajustement

## 6.2 Production

### Acces
Menu > **Logistique** > **Production**

### Nomenclatures (BOM)

Une **nomenclature** definit les composants necessaires pour fabriquer un produit :

```
Produit fini
├── Composant A (Qte: 2)
├── Composant B (Qte: 1)
└── Sous-ensemble C (Qte: 1)
    ├── Piece X (Qte: 3)
    └── Piece Y (Qte: 2)
```

### Ordres de Fabrication (OF)

1. Creez un **nouvel OF**
2. Selectionnez le produit a fabriquer
3. Indiquez la quantite
4. Planifiez les dates
5. Lancez la production
6. Suivez l'avancement
7. Declarez la production terminee

### Planning de Production

Vue calendrier des ordres de fabrication avec :
- Capacite par poste de travail
- Conflits de ressources
- Optimisation automatique

## 6.3 Qualite

### Acces
Menu > **Logistique** > **Qualite**

### Controles Qualite

#### Types de Controles

| Type | Moment | Description |
|------|--------|-------------|
| **Reception** | A l'arrivee | Verification des livraisons |
| **En-cours** | Production | Controle intermediaire |
| **Final** | Avant expedition | Validation produit fini |

#### Realiser un Controle

1. Accedez a **Qualite** > **Controles**
2. Selectionnez le lot/produit
3. Renseignez les mesures
4. Comparez aux specifications
5. Validez ou declarez une non-conformite

### Non-Conformites

1. Declarez la non-conformite
2. Analysez les causes (methode 5 Pourquoi, Ishikawa)
3. Definissez les actions correctives
4. Suivez la mise en oeuvre
5. Cloturez apres verification

## 6.4 Maintenance (GMAO)

### Acces
Menu > **Logistique** > **Maintenance**

### Equipements

Enregistrez tous vos equipements avec :
- Identification (numero serie, localisation)
- Documentation technique
- Historique des interventions
- Contrats de maintenance

### Types de Maintenance

| Type | Description |
|------|-------------|
| **Preventive** | Planifiee selon calendrier/compteur |
| **Corrective** | Suite a une panne |
| **Ameliorative** | Amelioration des performances |

### Demandes d'Intervention

1. Creez une **demande**
2. Decrivez le probleme
3. Assignez a un technicien
4. Suivez l'avancement
5. Validez la cloture

---

# 7. Modules Ressources Humaines

## 7.1 Gestion des Employes

### Acces
Menu > **Modules** > **Ressources Humaines**

### Dossier Employe

| Section | Contenu |
|---------|---------|
| **Identite** | Nom, prenom, photo, coordonnees |
| **Contrat** | Type, dates, poste, remuneration |
| **Competences** | Formations, certifications |
| **Documents** | Contrat signe, diplomes |
| **Absences** | Historique des conges |

### Actions RH

- **Embauche** : Creation du dossier, contrat
- **Avenant** : Modification de contrat
- **Promotion** : Changement de poste
- **Sortie** : Depart (demission, licenciement, retraite)

## 7.2 Gestion des Conges

### Soumettre une Demande

1. Accedez a **RH** > **Mes conges**
2. Cliquez sur **"+ Nouvelle demande"**
3. Selectionnez le type :
   - Conges payes
   - RTT
   - Maladie
   - Sans solde
4. Indiquez les dates
5. Ajoutez un commentaire si necessaire
6. Soumettez

### Validation (Manager)

1. Consultez les demandes **En attente**
2. Verifiez les soldes et le planning equipe
3. **Approuvez** ou **Refusez** avec motif

### Calendrier d'Equipe

Vue d'ensemble des presences/absences de l'equipe pour planifier sans conflits.

## 7.3 Feuilles de Temps

### Acces
Menu > **Modules** > **Feuilles de Temps**

### Saisie du Temps

1. Selectionnez la **semaine**
2. Pour chaque jour, renseignez :
   - Projet/Activite
   - Heures travaillees
3. Ajoutez des commentaires si necessaire
4. Soumettez pour validation

### Validation (Manager)

1. Consultez les feuilles **En attente**
2. Verifiez les heures declarees
3. Comparez aux plannings projets
4. Validez ou demandez des corrections

## 7.4 Coffre-Fort RH

### Acces
Menu > **Systeme** > **Coffre-Fort RH**

Espace securise pour les donnees sensibles :
- Bulletins de paie
- Evaluations annuelles
- Dossiers disciplinaires
- Informations medicales

> **Acces restreint** : Reserve aux personnes habilitees (DRH, Direction).

---

# 8. Modules Intelligence et IA

## 8.1 Cockpit Dirigeant

### Acces
Menu > **Principal** > **Cockpit Dirigeant**

### Vue d'Ensemble

Tableau de bord executif presentant :

| Indicateur | Description |
|------------|-------------|
| **CA du mois** | Chiffre d'affaires mensuel |
| **Pipeline** | Opportunites en cours |
| **Tresorerie** | Position de cash |
| **Rentabilite** | Marge operationnelle |
| **RH** | Effectifs, absences |
| **Alertes** | Points d'attention |

### Personnalisation

1. Cliquez sur **"Personnaliser"**
2. Ajoutez/supprimez des widgets
3. Reordonnez par glisser-deposer
4. Enregistrez votre configuration

### Drill-down

Cliquez sur n'importe quel indicateur pour acceder aux details et comprendre les chiffres.

## 8.2 Assistant IA - Theo

### Acces
Menu > **IA** > **Assistant IA** ou icone 💬 en bas a droite

### Fonctionnalites

Theo peut :
- **Repondre a vos questions** sur les donnees
- **Analyser des documents** (factures, contrats)
- **Generer des rapports** personnalises
- **Suggerer des actions** basees sur les tendances
- **Automatiser des taches** repetitives

### Exemples de Questions

| Question | Reponse de Theo |
|----------|-----------------|
| "Quel est mon CA du mois ?" | Affiche le chiffre avec graphique |
| "Liste les factures en retard" | Tableau des impayes |
| "Analyse ce contrat" | Resume et points d'attention |
| "Envoie une relance au client X" | Execute l'envoi apres confirmation |

### Conseils d'Utilisation

- Soyez **precis** dans vos demandes
- Utilisez des **dates specifiques** si necessaire
- Demandez des **formats** particuliers (tableau, graphique)
- **Confirmez** avant les actions irreversibles

## 8.3 Marceau IA (Automatisation)

### Acces
Menu > **IA** > **Marceau IA**

### Presentation

Marceau est un agent IA specialise dans :
- **Telephonie** : Gestion des appels entrants
- **Commercial** : Suivi automatise des devis
- **Support** : Reponses aux tickets
- **Marketing** : Publications sur reseaux sociaux
- **Comptabilite** : Traitement des factures

### Tableau de Bord Marceau

| Element | Description |
|---------|-------------|
| **Actions du jour** | Nombre d'actions automatisees |
| **En attente** | Actions necessitant validation humaine |
| **Confiance moyenne** | Score de confiance des decisions |
| **Modules actifs** | Liste des modules en service |

### Validation Humaine

Certaines actions necessitent votre approbation :

1. Consultez les actions **En attente**
2. Examinez la proposition de Marceau
3. **Approuvez** ou **Rejetez** avec commentaire

> Marceau apprend de vos decisions pour s'ameliorer.

## 8.4 Reporting et BI

### Acces
Menu > **Digital** > **Reporting & BI**

### Rapports Predéfinis

| Categorie | Rapports |
|-----------|----------|
| **Commercial** | CA par client, par produit, par commercial |
| **Finance** | Tresorerie, rentabilite, budget vs reel |
| **Operations** | Stock, production, qualite |
| **RH** | Effectifs, absenteisme, formation |

### Creer un Rapport Personnalise

1. Cliquez sur **"+ Nouveau rapport"**
2. Selectionnez la **source de donnees**
3. Choisissez les **colonnes** a afficher
4. Definissez les **filtres**
5. Ajoutez des **graphiques** si souhaite
6. Enregistrez et partagez

### Tableaux de Bord

Combinez plusieurs rapports dans un tableau de bord interactif :
- Widgets personnalisables
- Actualisation automatique
- Partage avec l'equipe

---

# 9. Modules Communication et Digital

## 9.1 Email

### Acces
Menu > **Communication** > **Emails**

### Modeles d'Email

Creez des modeles reutilisables :
1. Accedez a **Modeles**
2. Cliquez sur **"+ Nouveau modele"**
3. Definissez :
   - Nom du modele
   - Objet
   - Contenu (editeur visuel)
   - Variables dynamiques ({client.nom}, {facture.numero}...)
4. Enregistrez

### Envoi d'Emails

#### Email Unitaire
1. Ouvrez un document (facture, devis)
2. Cliquez sur **"Envoyer par email"**
3. Selectionnez le modele
4. Personnalisez si necessaire
5. Envoyez

#### Email de Masse
1. Accedez a **Emails** > **Campagnes**
2. Creez une nouvelle campagne
3. Definissez les destinataires
4. Choisissez le modele
5. Planifiez ou envoyez

## 9.2 Signature Electronique

### Acces
Menu > **Communication** > **Signature Electronique**

### Envoyer un Document a Signer

1. Selectionnez le document (contrat, devis)
2. Cliquez sur **"Faire signer"**
3. Ajoutez les signataires (email)
4. Positionnez les zones de signature
5. Envoyez

### Suivi

| Statut | Description |
|--------|-------------|
| Envoye | En attente de signature |
| Vu | Document consulte |
| Signe | Signature apposee |
| Refuse | Signataire a refuse |
| Expire | Delai depasse |

## 9.3 Site Web

### Acces
Menu > **Digital** > **Site Web**

### Editeur de Pages

Creez des pages web sans code :
1. Selectionnez un modele
2. Glissez-deposez des blocs :
   - Texte, Images
   - Formulaires
   - Galeries
   - Cartes
3. Personnalisez les styles
4. Publiez

### Blog

1. Accedez a **Blog** > **Articles**
2. Creez un nouvel article
3. Redigez avec l'editeur
4. Ajoutez des medias
5. Optimisez le SEO
6. Publiez ou planifiez

## 9.4 Reseaux Sociaux

### Acces
Menu > **Digital** > **Reseaux Sociaux**

### Connexion des Comptes

1. Accedez aux **Parametres**
2. Connectez vos comptes :
   - Facebook
   - LinkedIn
   - Instagram
3. Autorisez AZALSCORE

### Publication

1. Creez un **nouveau post**
2. Redigez le contenu
3. Ajoutez des medias
4. Selectionnez les reseaux cibles
5. Publiez immediatement ou planifiez

### Statistiques

Suivez les performances :
- Portee
- Engagement
- Clics
- Tendances

---

# 10. Administration et Securite

## 10.1 Gestion des Utilisateurs

### Acces
Menu > **Administration** > **Utilisateurs**

### Creer un Utilisateur

1. Cliquez sur **"+ Nouvel utilisateur"**
2. Renseignez :
   - Nom, Prenom
   - Email*
   - Role(s)
   - Mot de passe temporaire
3. Enregistrez
4. L'utilisateur recoit un email d'invitation

### Modifier les Droits

1. Selectionnez l'utilisateur
2. Accedez a l'onglet **Roles**
3. Ajoutez ou retirez des roles
4. Enregistrez

### Desactiver un Utilisateur

1. Selectionnez l'utilisateur
2. Cliquez sur **"Desactiver"**
3. Confirmez

> L'utilisateur ne peut plus se connecter mais ses donnees sont conservees.

## 10.2 Roles et Permissions

### Acces
Menu > **Administration** > **Roles**

### Structure des Permissions

Format : `module.ressource.action`

Exemples :
- `invoicing.invoice.create` : Creer des factures
- `hr.employee.read` : Voir les employes
- `treasury.bank.reconcile` : Rapprocher les banques

### Creer un Role Personnalise

1. Cliquez sur **"+ Nouveau role"**
2. Nommez le role
3. Selectionnez les permissions
4. Enregistrez
5. Assignez aux utilisateurs

## 10.3 Audit et Tracabilite

### Acces
Menu > **Administration** > **Audit**

### Journal d'Audit

Chaque action est enregistree :
- **Qui** : Utilisateur
- **Quoi** : Action effectuee
- **Quand** : Date et heure
- **Ou** : Module concerne
- **Donnees** : Avant/Apres modification

### Recherche dans les Logs

1. Definissez la **periode**
2. Filtrez par **utilisateur**
3. Filtrez par **module**
4. Filtrez par **type d'action**
5. Consultez les resultats

### Export de Conformite

Generez des rapports pour :
- Audits externes
- Conformite RGPD
- Enquetes internes

## 10.4 Securite

### Politique de Mots de Passe

Regles par defaut :
- Minimum 8 caracteres
- Au moins 1 majuscule
- Au moins 1 chiffre
- Expiration tous les 90 jours

### Authentification a Deux Facteurs (2FA)

1. Accedez a **Parametres** > **Securite**
2. Activez la 2FA
3. Choisissez la methode :
   - Email
   - SMS
   - Application (recommande)
4. Suivez les instructions

### Sessions Actives

1. Accedez a **Parametres** > **Sessions**
2. Consultez les connexions actives
3. **Revoquez** les sessions suspectes

## 10.5 Sauvegardes

### Acces
Menu > **Administration** > **Sauvegardes**

### Sauvegardes Automatiques

AZALSCORE effectue des sauvegardes automatiques :
- **Quotidiennes** : Conservation 30 jours
- **Hebdomadaires** : Conservation 12 semaines
- **Mensuelles** : Conservation 12 mois

### Restauration

1. Selectionnez le point de restauration
2. Choisissez le scope :
   - Restauration complete
   - Module specifique
   - Donnees specifiques
3. Confirmez

> **Attention** : La restauration ecrase les donnees actuelles.

---

# 11. Workflows et Automatisations

## 11.1 Workflows de Validation

### Principe

Certaines actions necessitent une approbation :
- Validation de depenses
- Approbation de conges
- Signature de contrats

### Statuts

```
Brouillon → Soumis → En validation → Approuve → Traite
                            ↘ Rejete → Brouillon
```

### Approbation

1. Consultez vos **taches en attente**
2. Examinez la demande
3. Consultez les pieces jointes
4. **Approuvez** ou **Rejetez**
5. Ajoutez un commentaire si necessaire

## 11.2 Automatisations (Triggers)

### Acces
Menu > **Administration** > **Automatisations**

### Creer une Automatisation

1. Cliquez sur **"+ Nouvelle automatisation"**
2. Definissez le **declencheur** :
   - Creation d'un document
   - Changement de statut
   - Date/Heure (planifie)
   - Seuil atteint
3. Definissez les **actions** :
   - Envoyer un email
   - Creer une tache
   - Modifier un champ
   - Appeler un webhook
4. Definissez les **conditions** (optionnel)
5. Activez

### Exemples

| Declencheur | Action |
|-------------|--------|
| Facture en retard > 15 jours | Envoyer relance automatique |
| Stock < minimum | Creer commande fournisseur |
| Nouveau client cree | Envoyer email de bienvenue |
| Devis signe | Creer commande + notifier equipe |

## 11.3 Guardian (Surveillance)

### Acces
Menu > **Administration** > **Guardian**

### Fonctionnalites

Guardian surveille votre systeme et :
- Detecte les anomalies (transactions inhabituelles)
- Corrige automatiquement certains problemes
- Alerte les administrateurs
- Genere des rapports de sante

### Tableau de Bord Guardian

| Indicateur | Description |
|------------|-------------|
| **Sante systeme** | Etat global (Vert/Orange/Rouge) |
| **Anomalies detectees** | Nombre et severite |
| **Corrections auto** | Actions prises automatiquement |
| **Alertes actives** | Points necessitant attention |

---

# 12. Annexes

## 12.1 Glossaire

| Terme | Definition |
|-------|------------|
| **Tenant** | Espace client isole dans AZALSCORE |
| **Workflow** | Processus de validation en plusieurs etapes |
| **Dashboard** | Tableau de bord avec indicateurs |
| **Widget** | Element visuel d'un tableau de bord |
| **2FA** | Authentification a deux facteurs |
| **RBAC** | Controle d'acces base sur les roles |
| **BOM** | Nomenclature de fabrication |
| **OF** | Ordre de fabrication |
| **GMAO** | Gestion de maintenance assistee par ordinateur |
| **BI** | Business Intelligence (informatique decisionnelle) |
| **API** | Interface de programmation |
| **SSO** | Authentification unique |
| **RGPD** | Reglement general sur la protection des donnees |

## 12.2 Raccourcis Clavier Complets

| Raccourci | Action |
|-----------|--------|
| `/` | Recherche globale |
| `Cmd+K` | Palette de commandes |
| `Cmd+S` | Sauvegarder |
| `Cmd+N` | Nouveau |
| `Cmd+P` | Imprimer |
| `Escape` | Fermer/Annuler |
| `Tab` | Champ suivant |
| `Shift+Tab` | Champ precedent |
| `Enter` | Valider |
| `?` | Aide |

## 12.3 Formats de Fichiers Acceptes

| Type | Extensions |
|------|------------|
| **Documents** | PDF, DOC, DOCX, ODT |
| **Tableurs** | XLS, XLSX, CSV, ODS |
| **Images** | JPG, PNG, GIF, WEBP |
| **Archives** | ZIP, RAR |
| **Import comptable** | FEC, OFX, QIF |

## 12.4 Contacts Support

| Canal | Acces |
|-------|-------|
| **Documentation** | https://docs.azalscore.com |
| **Support technique** | support@azalscore.com |
| **Telephone** | +33 1 XX XX XX XX |
| **Chat en ligne** | Icone 💬 dans l'application |

## 12.5 Mises a Jour

AZALSCORE est mis a jour regulierement :
- **Corrections** : Deploiees automatiquement
- **Nouvelles fonctionnalites** : Annoncees par notification
- **Evolutions majeures** : Communication par email

Consultez le **changelog** dans Parametres > A propos.

---

## Notes de Version

| Version | Date | Modifications |
|---------|------|---------------|
| 2.0 | Fevrier 2026 | Version initiale du guide |

---

*Document de formation AZALSCORE - Tous droits reserves*
*Pour usage interne - Ne pas diffuser*
