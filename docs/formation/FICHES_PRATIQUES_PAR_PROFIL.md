# Fiches Pratiques AZALSCORE par Profil

## Guide de Reference Rapide

---

# Profil 1 : Commercial / Force de Vente

## Vos Modules Principaux
- CRM / Clients
- Devis
- Commandes
- Factures (consultation)
- Saisie rapide

## Taches Quotidiennes

### Matin : Preparation
1. **Consultez le Cockpit** (si acces)
   - Pipeline commercial
   - Devis en attente de reponse
   - Relances a effectuer

2. **Verifiez vos notifications**
   - Nouveaux leads
   - Devis acceptes/refuses
   - Demandes clients

### En clientele : Saisie Rapide
1. Accedez a **Saisie** > **Nouvelle saisie**
2. Recherchez ou creez le client
3. Ajoutez les articles du catalogue
4. Generez le devis instantanement
5. Envoyez par email sur place

### Fin de journee : Suivi
1. Mettez a jour les statuts des opportunites
2. Ajoutez des notes sur les rendez-vous
3. Planifiez les relances

## Procedures Detaillees

### Creer un Nouveau Client
```
CRM > + Nouveau client
├── Raison sociale : [Nom entreprise]
├── Type : Entreprise / Particulier
├── Email : [email]
├── Telephone : [tel]
├── Adresse : [adresse complete]
└── Commercial assigne : [vous-meme]
→ Enregistrer
```

### Creer un Devis
```
Devis > + Nouveau devis
├── Client : [selectionner]
├── Date validite : [J+30 par defaut]
├── Lignes :
│   ├── Produit/Service : [rechercher]
│   ├── Quantite : [X]
│   ├── Prix : [auto ou personnalise]
│   └── Remise : [% optionnel]
├── Conditions : [texte libre]
└── Actions :
    ├── Enregistrer (brouillon)
    └── Envoyer (email direct)
```

### Convertir Devis en Commande
```
Devis [ACCEPTE] > Ouvrir
└── Convertir en commande
    ├── Verifier les informations
    ├── Ajouter date livraison souhaitee
    └── Confirmer
→ Commande creee automatiquement
```

### Relancer un Devis
```
Devis > Filtrer : En attente > 7 jours
├── Selectionner les devis
├── Actions > Relancer
├── Choisir modele de relance
└── Envoyer
```

## Indicateurs a Suivre

| KPI | Objectif Typique | Ou le trouver |
|-----|------------------|---------------|
| Taux de conversion | > 30% | Cockpit > Commercial |
| Delai moyen signature | < 15 jours | BI > Rapports |
| CA mensuel | Variable | Cockpit |
| Nombre devis envoyes | > 20/mois | Devis > Stats |

## Astuces

1. **Favoris** : Ajoutez vos clients frequents en favoris (etoile)
2. **Modeles** : Utilisez des modeles de devis pour gagner du temps
3. **Recherche** : Tapez `@` puis le nom client pour recherche rapide
4. **Mobile** : L'interface est responsive, utilisez-la sur tablette en clientele

---

# Profil 2 : Comptable

## Vos Modules Principaux
- Comptabilite
- Tresorerie
- Factures (fournisseurs)
- Immobilisations
- Notes de frais

## Taches Quotidiennes

### Matin : Verification
1. **Consultez la tresorerie**
   - Soldes bancaires
   - Previsions J+7

2. **Traitez les factures fournisseurs**
   - Nouvelles factures recues
   - Validation et comptabilisation

3. **Rapprochement bancaire**
   - Import du releve
   - Pointage des operations

### Semaine : Travaux Periodiques
- Lundi : Cloture semaine precedente
- Mercredi : Declarations TVA (si periode)
- Vendredi : Reporting direction

### Mois : Cloture Mensuelle
1. Verifier toutes les ecritures
2. Passer les OD de fin de mois
3. Generer les etats (balance, grand livre)
4. Valider avec la direction

## Procedures Detaillees

### Saisir une Ecriture
```
Comptabilite > Journal > + Nouvelle ecriture
├── Date : [date piece]
├── Journal : [ACH/VTE/BQ/OD]
├── Reference : [numero facture]
├── Lignes :
│   ├── Compte debit : [6XXXXX] Montant : [X.XX]
│   └── Compte credit : [4XXXXX] Montant : [X.XX]
├── Verification : Debit = Credit ✓
└── Valider
```

### Lettrage Comptes Tiers
```
Comptabilite > Grand Livre > Compte 411XXX
├── Selectionner les lignes a lettrer
│   ├── Facture : +1000.00
│   └── Reglement : -1000.00
├── Verifier solde = 0
└── Lettrer (code automatique)
```

### Rapprochement Bancaire
```
Tresorerie > Comptes > [Compte] > Rapprochement
├── Importer releve (CSV/OFX)
├── Pour chaque ligne :
│   ├── Correspondance trouvee : Valider ✓
│   ├── Pas de correspondance :
│   │   ├── Creer ecriture manquante
│   │   └── OU Ignorer (temporaire)
├── Verifier ecart de rapprochement = 0
└── Valider le rapprochement
```

### Cloture de Periode
```
Comptabilite > Periodes > [Mois]
├── Verifier : Toutes ecritures validees
├── Controles automatiques :
│   ├── Equilibre journaux ✓
│   ├── Comptes lettres ✓
│   └── Anomalies corrigees ✓
├── Generer etats de cloture
├── Archiver
└── Cloturer (irreversible)
```

## Etats et Rapports

| Etat | Frequence | Usage |
|------|-----------|-------|
| Balance generale | Quotidien | Verification rapide |
| Grand livre | Sur demande | Detail des mouvements |
| Balance agee clients | Hebdomadaire | Suivi encaissements |
| Balance agee fournisseurs | Hebdomadaire | Gestion paiements |
| TVA collectee/deductible | Mensuel | Declaration |
| Bilan/Compte resultat | Mensuel/Annuel | Reporting |

## Astuces

1. **Modeles d'ecritures** : Creez des modeles pour les ecritures recurrentes
2. **Import massif** : Utilisez l'import CSV pour les gros volumes
3. **Raccourcis** : `Tab` pour passer au champ suivant, `Enter` pour valider
4. **Recherche compte** : Tapez les premiers chiffres pour filtrer

---

# Profil 3 : Responsable RH

## Vos Modules Principaux
- Ressources Humaines
- Feuilles de temps
- Notes de frais
- Coffre-fort RH

## Taches Quotidiennes

### Matin
1. **Validation des demandes**
   - Conges en attente
   - Notes de frais soumises
   - Feuilles de temps

2. **Suivi des absences**
   - Calendrier equipe
   - Retours de conges

### Hebdomadaire
- Revue des effectifs
- Suivi des recrutements
- Mise a jour des dossiers

### Mensuel
- Preparation paie
- Declarations sociales
- Reporting direction

## Procedures Detaillees

### Creer un Employe
```
RH > Employes > + Nouvel employe
├── Identite :
│   ├── Nom, Prenom
│   ├── Date naissance
│   ├── Numero SS
│   └── Coordonnees
├── Contrat :
│   ├── Type (CDI/CDD/Stage)
│   ├── Date debut
│   ├── Poste
│   ├── Departement
│   └── Manager
├── Remuneration :
│   ├── Salaire brut
│   └── Avantages
├── Documents :
│   └── Joindre contrat signe
└── Enregistrer
```

### Traiter une Demande de Conges
```
RH > Conges > En attente
├── Ouvrir la demande
├── Verifier :
│   ├── Solde suffisant
│   ├── Planning equipe
│   └── Periode (pas de conflit)
├── Decision :
│   ├── Approuver → Confirmer
│   └── Refuser → Motif obligatoire
```

### Preparation de la Paie
```
RH > Paie > Nouveau cycle
├── Selectionner periode
├── Importer les elements variables :
│   ├── Heures supplementaires
│   ├── Primes
│   ├── Absences
│   └── Avantages nature
├── Calculer les bulletins
├── Verifier (controle coherence)
├── Valider
└── Exporter vers logiciel paie
```

### Onboarding Nouvel Arrivant
```
Checklist :
□ Creer le dossier employe
□ Generer les acces AZALSCORE
□ Assigner le role et les droits
□ Creer les equipements (PC, badge...)
□ Informer les services (IT, Compta...)
□ Planifier l'integration
□ Envoyer le welcome pack
```

## Indicateurs RH

| KPI | Formule | Cible |
|-----|---------|-------|
| Taux d'absenteisme | Jours absence / Jours travailles | < 5% |
| Turnover | Departs / Effectif moyen | < 15% |
| Delai recrutement | Date embauche - Date ouverture poste | < 45 jours |
| Satisfaction | Score enquete annuelle | > 7/10 |

## Astuces

1. **Alertes** : Configurez des alertes pour les fins de periode d'essai
2. **Templates** : Utilisez des modeles de contrats
3. **Export** : Exportez les donnees vers votre logiciel de paie
4. **Coffre-fort** : Stockez les documents sensibles de maniere securisee

---

# Profil 4 : Responsable Logistique / Magasinier

## Vos Modules Principaux
- Inventaire / Stock
- Achats
- Qualite
- Production (si applicable)
- Maintenance

## Taches Quotidiennes

### Matin : Etat des Stocks
1. **Verifier les alertes**
   - Articles sous seuil minimum
   - Commandes a recevoir aujourd'hui

2. **Preparer les expeditions**
   - Bons de livraison du jour
   - Controle des disponibilites

### Reception Marchandises
1. Verifier le bon de livraison
2. Controler les quantites et qualite
3. Enregistrer la reception
4. Ranger en stock

### Fin de Journee
1. Mettre a jour les mouvements
2. Signaler les anomalies
3. Preparer le lendemain

## Procedures Detaillees

### Recevoir une Commande Fournisseur
```
Achats > Commandes > [Commande] > Reception
├── Scanner ou saisir les references
├── Pour chaque ligne :
│   ├── Quantite attendue : [X]
│   ├── Quantite recue : [Y]
│   ├── Conformite : ✓ ou Non-conforme
│   └── Emplacement stockage
├── Si ecart : Signaler
├── Valider la reception
└── Stock mis a jour automatiquement
```

### Preparer une Expedition
```
Stock > Expeditions > [Commande client]
├── Imprimer le bon de preparation
├── Pour chaque ligne :
│   ├── Emplacement : [localisation]
│   ├── Quantite : [X]
│   └── Prelever ✓
├── Controle final
├── Emballer
├── Valider l'expedition
└── Generer bon de livraison
```

### Mouvement de Stock Manuel
```
Stock > Mouvements > + Nouveau
├── Type : Entree / Sortie / Transfert
├── Article : [reference]
├── Quantite : [X]
├── Entrepot origine : [si transfert]
├── Entrepot destination : [emplacement]
├── Motif : [justification]
└── Valider
```

### Realiser un Inventaire
```
Stock > Inventaire > + Nouvelle session
├── Scope : Tout / Zone / Categorie
├── Generer la liste de comptage
├── Comptage :
│   ├── Scanner les articles
│   ├── Saisir les quantites
│   └── Ou utiliser terminal mobile
├── Analyser les ecarts
├── Valider les ajustements
└── Cloturer l'inventaire
```

## Indicateurs Stock

| KPI | Description | Cible |
|-----|-------------|-------|
| Taux de service | Commandes livrees a temps | > 95% |
| Rotation stock | CA / Stock moyen | > 6/an |
| Ecarts inventaire | Valeur ecarts / Stock | < 1% |
| Ruptures | Nb articles en rupture | 0 |

## Astuces

1. **Code-barres** : Utilisez un scanner pour accelerer les operations
2. **Emplacements** : Codifiez vos emplacements (Allee-Rayon-Niveau)
3. **FIFO/LIFO** : Configurez la methode de sortie par article
4. **Alertes** : Definissez des seuils de reapprovisionnement automatique

---

# Profil 5 : Technicien / Service Terrain

## Vos Modules Principaux
- Interventions
- Service Terrain
- Feuilles de temps
- Fiches de travail

## Taches Quotidiennes

### Debut de Journee
1. **Consultez votre planning**
   - Interventions du jour
   - Adresses et contacts

2. **Preparez votre materiel**
   - Pieces necessaires
   - Documentation technique

### Sur le Terrain
1. Pointer l'arrivee
2. Realiser l'intervention
3. Saisir le rapport
4. Faire signer le client
5. Pointer le depart

### Fin de Journee
1. Synchroniser les donnees
2. Completer les feuilles de temps
3. Signaler les besoins en pieces

## Procedures Detaillees

### Consulter une Intervention
```
Interventions > Mes interventions > [Aujourd'hui]
├── Heure debut : [HH:MM]
├── Client : [Nom]
├── Adresse : [Adresse complete]
├── Contact : [Nom + Tel]
├── Description : [Travaux a realiser]
├── Pieces necessaires : [Liste]
└── Navigation GPS : [Bouton]
```

### Realiser une Intervention
```
Intervention > Demarrer
├── Pointer arrivee : [Automatique ou manuel]
├── Diagnostic :
│   └── Description probleme constate
├── Travaux realises :
│   ├── Actions effectuees
│   ├── Pieces utilisees
│   └── Temps passe
├── Photos : [Avant/Apres]
├── Resultat : Resolu / A suivre / Escalade
├── Recommandations : [si applicable]
├── Signature client : [Capture]
├── Pointer depart
└── Valider
```

### Demander des Pieces
```
Interventions > [Intervention] > Pieces
├── Rechercher article : [reference ou nom]
├── Quantite necessaire : [X]
├── Urgence : Normal / Urgent
├── Commentaire : [precision]
└── Envoyer la demande
→ Notification au magasin
```

### Escalader une Intervention
```
Intervention > Escalader
├── Motif :
│   ├── Competence specifique requise
│   ├── Materiel specifique requis
│   └── Probleme complexe
├── Description detaillee
├── Photos/Documents
├── Destinataire : [Responsable technique]
└── Envoyer
```

## Application Mobile

L'interface mobile permet :
- Consultation du planning
- Navigation GPS vers le client
- Saisie du rapport
- Prise de photos
- Signature electronique
- Fonctionnement hors-ligne

### Mode Hors-Ligne
1. Les donnees du jour sont synchronisees le matin
2. Travaillez normalement sans connexion
3. La synchronisation se fait automatiquement au retour du reseau

## Astuces

1. **Photos** : Prenez toujours des photos avant/apres
2. **Signature** : Faites signer le client avant de partir
3. **Pieces** : Signalez les pieces utilisees immediatement
4. **Temps** : Soyez precis sur les temps passes

---

# Profil 6 : Dirigeant / Direction

## Vos Modules Principaux
- Cockpit Dirigeant
- BI / Reporting
- Finance (vue consolidee)
- Validation (workflows)

## Consultation Quotidienne

### Cockpit Dirigeant
Tableau de bord synthetique avec :

| Widget | Information |
|--------|-------------|
| CA | Chiffre d'affaires du mois, tendance |
| Pipeline | Opportunites en cours, valeur totale |
| Tresorerie | Position cash, prevision |
| Commandes | Carnet de commandes |
| Marge | Rentabilite operationnelle |
| Alertes | Points d'attention |

### Drill-Down
Cliquez sur n'importe quel chiffre pour :
- Voir le detail
- Comprendre l'origine
- Acceder aux documents sources

## Validations

### Workflow d'Approbation
1. **Notification** : Vous recevez une alerte
2. **Consultation** : Examinez la demande
3. **Decision** :
   - ✓ Approuver
   - ✗ Rejeter (avec motif)
   - → Deleguer

### Types de Validations
| Type | Seuil Typique |
|------|---------------|
| Devis | > 10 000 EUR |
| Commandes fournisseurs | > 5 000 EUR |
| Notes de frais | > 500 EUR |
| Recrutements | Tous |
| Investissements | > 20 000 EUR |

## Rapports Strategiques

### Rapports Mensuels
- **Compte de resultat** : P&L mensuel vs budget
- **Tresorerie** : Evolution et previsions
- **Commercial** : Performance par segment
- **RH** : Effectifs et couts

### Rapports Annuels
- **Bilan** : Situation patrimoniale
- **Budget** : Realise vs previsionnel
- **Tendances** : Evolution sur 3 ans

## Assistant IA - Theo

Posez vos questions directement :
- "Quel est le CA du trimestre ?"
- "Compare les ventes ce mois vs l'an dernier"
- "Liste les 10 plus gros clients"
- "Analyse les marges par produit"

## Astuces

1. **Favoris** : Ajoutez les rapports frequents aux favoris
2. **Export** : Exportez en PDF pour les CA ou reunion
3. **Delegation** : Configurez les delegations en cas d'absence
4. **Mobile** : Consultez le cockpit sur smartphone

---

# Resume : Navigation Rapide par Profil

| Profil | Acces Principal | Raccourci |
|--------|-----------------|-----------|
| Commercial | CRM, Devis | `@` + nom client |
| Comptable | Compta, Tresorerie | `#` + num facture |
| RH | Employes, Conges | Menu RH |
| Logistique | Stock, Achats | `$` + ref produit |
| Technicien | Interventions | Planning mobile |
| Direction | Cockpit | Cockpit bouton |

---

*Fiches Pratiques AZALSCORE - Version 2.0 - Fevrier 2026*
