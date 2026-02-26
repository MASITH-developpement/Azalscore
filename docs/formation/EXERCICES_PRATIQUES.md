# AZALSCORE - Exercices Pratiques de Formation

## Parcours d'Apprentissage Guides

---

# Module 1 : Prise en Main (30 minutes)

## Objectifs
- Se connecter a AZALSCORE
- Naviguer dans l'interface
- Utiliser la recherche
- Personnaliser son espace

## Exercice 1.1 : Premiere Connexion

### Instructions
1. Ouvrez votre navigateur web
2. Accedez a l'adresse : **https://azalscore.com**
3. Cliquez sur "Se connecter"
4. Entrez vos identifiants :
   - Email : `[votre.email@entreprise.com]`
   - Mot de passe : `[fourni par l'administrateur]`
5. Validez

### Verification
- [ ] L'ecran d'accueil s'affiche
- [ ] Votre nom apparait dans le coin superieur droit
- [ ] Le menu est accessible

## Exercice 1.2 : Exploration de l'Interface

### Instructions
1. Identifiez les elements suivants :
   - Logo AZALSCORE (coin superieur gauche)
   - Barre de recherche
   - Icone de notifications (cloche)
   - Menu utilisateur (avatar)

2. Cliquez sur votre avatar et explorez :
   - Mon profil
   - Parametres
   - Mode (AZALSCORE/ERP)

3. Changez de mode d'affichage :
   - Passez en mode ERP
   - Observez le menu lateral
   - Repassez en mode AZALSCORE

### Questions
1. Quelle est la difference entre les deux modes ?
2. Quel mode preferez-vous ? Pourquoi ?

## Exercice 1.3 : Recherche Globale

### Instructions
1. Cliquez dans la barre de recherche (ou appuyez sur `/`)
2. Tapez "facture"
3. Observez les suggestions qui apparaissent
4. Fermez avec `Escape`

5. Tapez maintenant `@` puis un nom de client (ex: `@Martin`)
6. Observez les resultats filtres

### Verification
- [ ] La recherche globale fonctionne
- [ ] Les prefixes (@, #, $) filtrent les resultats
- [ ] Les raccourcis clavier fonctionnent

## Exercice 1.4 : Parametres du Profil

### Instructions
1. Accedez a votre profil (Avatar > Mon profil)
2. Verifiez vos informations :
   - Nom et prenom
   - Email
   - Telephone
3. Modifiez votre photo de profil (optionnel)
4. Enregistrez les modifications

### Verification
- [ ] Les informations sont correctes
- [ ] Les modifications sont enregistrees

---

# Module 2 : Gestion des Clients (45 minutes)

## Objectifs
- Consulter la liste des clients
- Creer un nouveau client
- Modifier les informations
- Rechercher efficacement

## Exercice 2.1 : Consultation du CRM

### Instructions
1. Accedez a **CRM** (ou Menu > Modules > CRM / Clients)
2. Observez la liste des clients existants
3. Utilisez les filtres :
   - Par statut (Actif/Inactif)
   - Par commercial
4. Triez par nom, puis par date de creation
5. Changez le nombre d'elements par page

### Questions
1. Combien de clients actifs y a-t-il ?
2. Quel est le client le plus recent ?

## Exercice 2.2 : Creation d'un Client (Entreprise)

### Scenario
Un nouveau prospect vous contacte. Ses coordonnees :
- Raison sociale : **ABC Industrie**
- SIRET : 12345678901234
- Adresse : 10 rue de l'Usine, 75001 Paris
- Contact : Jean MARTIN, Directeur
- Tel : 01 23 45 67 89
- Email : j.martin@abc-industrie.fr

### Instructions
1. Cliquez sur **"+ Nouveau client"**
2. Remplissez les champs :
   - Type : Entreprise
   - Raison sociale : ABC Industrie
   - SIRET : 12345678901234
3. Ajoutez l'adresse
4. Ajoutez le contact principal
5. Enregistrez

### Verification
- [ ] Le client apparait dans la liste
- [ ] Toutes les informations sont presentes
- [ ] Le client est marque comme "Actif"

## Exercice 2.3 : Creation d'un Client (Particulier)

### Scenario
Nouveau client particulier :
- Nom : DUPONT Marie
- Adresse : 5 avenue des Fleurs, 69001 Lyon
- Tel : 06 12 34 56 78
- Email : marie.dupont@email.com

### Instructions
1. Creez ce client avec le type "Particulier"
2. Notez les differences avec une entreprise

### Verification
- [ ] Le client est cree
- [ ] Les champs sont adaptes au type particulier

## Exercice 2.4 : Modification et Recherche

### Instructions
1. Recherchez le client "ABC Industrie" (utilisez `@ABC`)
2. Ouvrez sa fiche
3. Modifiez son numero de telephone
4. Ajoutez une note : "Premier contact le [date]"
5. Enregistrez

### Verification
- [ ] La recherche fonctionne
- [ ] Les modifications sont enregistrees
- [ ] La note est visible dans l'historique

---

# Module 3 : Devis et Facturation (60 minutes)

## Objectifs
- Creer un devis complet
- Envoyer un devis par email
- Convertir en commande
- Generer une facture

## Exercice 3.1 : Creation d'un Devis

### Scenario
Le client ABC Industrie demande un devis pour :
- 5 Climatiseurs Split (ref: CLIM-001) a 800 EUR HT/unite
- Installation : 1500 EUR HT forfait
- Remise commerciale : 5%
- Validite : 30 jours

### Instructions
1. Accedez a **Devis** > **+ Nouveau devis**
2. Selectionnez le client : ABC Industrie
3. Ajoutez les lignes :

   | Article | Qte | Prix Unit. HT | Total HT |
   |---------|-----|---------------|----------|
   | CLIM-001 | 5 | 800.00 | 4000.00 |
   | Installation | 1 | 1500.00 | 1500.00 |

4. Appliquez la remise de 5%
5. Verifiez les totaux :
   - Sous-total HT : 5500.00
   - Remise (5%) : -275.00
   - Total HT : 5225.00
   - TVA (20%) : 1045.00
   - Total TTC : 6270.00
6. Definissez la validite : 30 jours
7. Enregistrez en brouillon

### Verification
- [ ] Le devis est cree avec le bon numero
- [ ] Les calculs sont corrects
- [ ] Le statut est "Brouillon"

## Exercice 3.2 : Envoi du Devis

### Instructions
1. Ouvrez le devis cree
2. Cliquez sur **"Envoyer"**
3. Verifiez :
   - Destinataire : j.martin@abc-industrie.fr
   - Objet du mail
   - Corps du message
4. Visualisez le PDF joint
5. Envoyez

### Verification
- [ ] Le statut passe a "Envoye"
- [ ] La date d'envoi est enregistree
- [ ] L'email apparait dans l'historique

## Exercice 3.3 : Acceptation et Conversion

### Scenario
Le client accepte le devis par telephone.

### Instructions
1. Ouvrez le devis
2. Cliquez sur **"Marquer comme accepte"**
3. Ajoutez une note : "Accepte par telephone le [date]"
4. Cliquez sur **"Convertir en commande"**
5. Verifiez les informations
6. Confirmez la commande

### Verification
- [ ] Le devis est marque "Accepte"
- [ ] Une commande est creee
- [ ] Les lignes sont identiques

## Exercice 3.4 : Facturation

### Instructions
1. Accedez a la commande creee
2. Simulez la livraison (Statut > Livree)
3. Cliquez sur **"Generer facture"**
4. Verifiez la facture generee
5. Envoyez la facture au client

### Verification
- [ ] La facture reprend les memes montants
- [ ] Le numero de facture est genere
- [ ] Le statut est "A payer"

## Exercice 3.5 : Encaissement

### Instructions
1. Ouvrez la facture
2. Cliquez sur **"Enregistrer paiement"**
3. Renseignez :
   - Date : aujourd'hui
   - Montant : 6270.00
   - Mode : Virement
   - Reference : VIR-12345
4. Validez

### Verification
- [ ] La facture passe en statut "Payee"
- [ ] Le solde client est mis a jour

---

# Module 4 : Gestion des Stocks (45 minutes)

## Objectifs
- Consulter l'etat des stocks
- Enregistrer une reception
- Effectuer un mouvement
- Realiser un inventaire

## Exercice 4.1 : Consultation du Stock

### Instructions
1. Accedez a **Stock** > **Produits**
2. Consultez la liste des articles
3. Identifiez :
   - Articles en stock
   - Articles sous le seuil minimum (alerte)
   - Articles en rupture
4. Ouvrez une fiche produit et observez :
   - Stock actuel
   - Historique des mouvements
   - Emplacements

### Questions
1. Combien d'articles sont en alerte ?
2. Quel est le produit avec le plus de stock ?

## Exercice 4.2 : Reception de Marchandises

### Scenario
Vous recevez une livraison :
- Ref: CLIM-001 : 10 unites
- Ref: FILT-002 : 50 unites

### Instructions
1. Accedez a **Stock** > **Mouvements** > **+ Entree**
2. Selectionnez le type : Reception fournisseur
3. Ajoutez les lignes :
   - CLIM-001 : 10
   - FILT-002 : 50
4. Indiquez l'emplacement de rangement
5. Validez la reception

### Verification
- [ ] Les stocks sont mis a jour
- [ ] Le mouvement apparait dans l'historique

## Exercice 4.3 : Sortie de Stock

### Scenario
Un technicien preleve pour une intervention :
- 2 x CLIM-001
- 5 x FILT-002

### Instructions
1. Creez un mouvement de **Sortie**
2. Motif : Intervention client
3. Ajoutez les articles et quantites
4. Validez

### Verification
- [ ] Les quantites sont deduites
- [ ] Le motif est enregistre

## Exercice 4.4 : Inventaire Partiel

### Instructions
1. Accedez a **Stock** > **Inventaire**
2. Creez une nouvelle session pour la categorie "Climatisation"
3. Pour chaque article, saisissez le comptage reel
4. Analysez les ecarts
5. Validez les ajustements

### Verification
- [ ] Les ecarts sont calcules
- [ ] Les ajustements sont passes
- [ ] Les nouveaux stocks sont corrects

---

# Module 5 : Comptabilite de Base (60 minutes)

## Objectifs
- Comprendre le plan comptable
- Saisir une ecriture simple
- Effectuer un rapprochement
- Generer un etat

## Exercice 5.1 : Exploration du Plan Comptable

### Instructions
1. Accedez a **Comptabilite** > **Plan comptable**
2. Parcourez les classes :
   - Classe 4 : Comptes de tiers
   - Classe 5 : Comptes financiers
   - Classe 6 : Charges
   - Classe 7 : Produits
3. Recherchez le compte "411000" (Clients)
4. Consultez les mouvements

### Questions
1. Quel est le solde du compte 411000 ?
2. Combien d'ecritures ce mois-ci ?

## Exercice 5.2 : Saisie d'une Ecriture

### Scenario
Enregistrer l'achat de fournitures de bureau :
- Montant HT : 150.00
- TVA : 30.00
- TTC : 180.00
- Paye par carte bancaire

### Instructions
1. Accedez au **Journal** > **+ Nouvelle ecriture**
2. Renseignez :
   - Date : aujourd'hui
   - Journal : ACH (Achats)
   - Libelle : Fournitures bureau
3. Saisissez les lignes :

   | Compte | Libelle | Debit | Credit |
   |--------|---------|-------|--------|
   | 606100 | Fournitures | 150.00 | |
   | 445660 | TVA deductible | 30.00 | |
   | 512000 | Banque | | 180.00 |

4. Verifiez l'equilibre (Total Debit = Total Credit)
5. Validez

### Verification
- [ ] L'ecriture est equilibree
- [ ] Elle apparait dans le journal

## Exercice 5.3 : Rapprochement Bancaire

### Instructions
1. Accedez a **Tresorerie** > **Rapprochement**
2. Selectionnez le compte bancaire
3. Pour chaque operation du releve :
   - Recherchez la correspondance
   - Validez le pointage
4. Verifiez l'ecart de rapprochement

### Verification
- [ ] Les operations sont pointees
- [ ] L'ecart est explique ou nul

## Exercice 5.4 : Generation d'une Balance

### Instructions
1. Accedez a **Comptabilite** > **Etats** > **Balance**
2. Selectionnez la periode (mois en cours)
3. Generez l'etat
4. Exportez en PDF
5. Analysez :
   - Total des debits
   - Total des credits
   - Ecart (doit etre 0)

### Verification
- [ ] La balance est equilibree
- [ ] L'export PDF fonctionne

---

# Module 6 : Ressources Humaines (30 minutes)

## Objectifs
- Consulter les dossiers employes
- Gerer une demande de conges
- Valider une note de frais

## Exercice 6.1 : Consultation RH

### Instructions
1. Accedez a **RH** > **Employes**
2. Consultez la liste des employes
3. Ouvrez un dossier et examinez :
   - Informations personnelles
   - Contrat
   - Conges
   - Historique

### Questions
1. Combien d'employes dans l'entreprise ?
2. Quels sont les types de contrats presents ?

## Exercice 6.2 : Demande de Conges (Employe)

### Instructions
1. Accedez a **RH** > **Mes conges**
2. Cliquez sur **"+ Nouvelle demande"**
3. Remplissez :
   - Type : Conges payes
   - Du : [date debut]
   - Au : [date fin]
   - Commentaire : Vacances ete
4. Soumettez la demande

### Verification
- [ ] La demande apparait en "En attente"
- [ ] Le solde previsionnel est calcule

## Exercice 6.3 : Validation Conges (Manager)

### Instructions
1. Accedez a **RH** > **Validations**
2. Consultez les demandes en attente
3. Pour une demande :
   - Examinez les dates
   - Verifiez le solde
   - Approuvez ou refusez

### Verification
- [ ] Le statut est mis a jour
- [ ] Le demandeur est notifie

## Exercice 6.4 : Note de Frais

### Instructions
1. Accedez a **Finance** > **Notes de frais**
2. Creez une nouvelle note :
   - Date : aujourd'hui
   - Type : Deplacement
   - Montant : 45.50
   - Justificatif : joindre photo/scan
3. Soumettez

### Verification
- [ ] La note est creee
- [ ] Le justificatif est joint

---

# Module 7 : Assistant IA - Theo (20 minutes)

## Objectifs
- Utiliser l'assistant IA
- Poser des questions sur les donnees
- Obtenir des rapports

## Exercice 7.1 : Premiere Interaction

### Instructions
1. Cliquez sur l'icone 💬 (coin inferieur droit)
2. L'assistant Theo s'ouvre
3. Tapez : "Bonjour"
4. Observez la reponse

## Exercice 7.2 : Questions sur les Donnees

### Instructions
Posez les questions suivantes et observez les reponses :

1. "Quel est le chiffre d'affaires de ce mois ?"
2. "Liste les 5 derniers devis crees"
3. "Combien de factures sont en retard ?"
4. "Quel est le client avec le plus de CA ?"

### Verification
- [ ] Theo repond avec des donnees
- [ ] Les chiffres semblent coherents

## Exercice 7.3 : Demande d'Action

### Instructions
1. Demandez : "Envoie une relance au client ABC Industrie"
2. Theo vous propose l'action
3. Verifiez les details
4. Confirmez ou annulez

### Verification
- [ ] Theo demande confirmation
- [ ] L'action est executee (ou non) selon votre choix

---

# Evaluation Finale

## Quiz de Connaissances

### Questions (cochez la bonne reponse)

1. Pour rechercher rapidement un client, j'utilise :
   - [ ] a) Le menu CRM
   - [ ] b) Le prefixe @ dans la recherche
   - [ ] c) Les deux methodes sont valides

2. Un devis "Envoye" peut etre :
   - [ ] a) Modifie directement
   - [ ] b) Accepte, refuse ou expire
   - [ ] c) Supprime

3. Pour creer une facture, je dois d'abord :
   - [ ] a) Creer un devis obligatoirement
   - [ ] b) Avoir une commande livree ou creer directement
   - [ ] c) Appeler le support

4. Le rapprochement bancaire sert a :
   - [ ] a) Fermer le compte
   - [ ] b) Pointer les operations avec le releve
   - [ ] c) Changer de banque

5. Pour demander des conges, j'accede a :
   - [ ] a) Mon profil
   - [ ] b) RH > Mes conges
   - [ ] c) Parametres

### Reponses
1. c | 2. b | 3. b | 4. b | 5. b

## Exercice Pratique Final

### Scenario Complet
Un nouveau client (TECHNO SAS) vous contacte pour :
- Achat de 3 serveurs (ref: SRV-100) a 2500 EUR HT
- Maintenance annuelle : 1500 EUR HT
- Remise speciale : 10%

Realisez le cycle complet :
1. Creez le client
2. Creez le devis
3. Envoyez-le (email fictif)
4. Marquez comme accepte
5. Convertissez en commande
6. Generez la facture
7. Enregistrez le paiement

### Checklist
- [ ] Client cree correctement
- [ ] Devis avec les bonnes lignes
- [ ] Remise appliquee
- [ ] Totaux corrects
- [ ] Conversion en commande
- [ ] Facture generee
- [ ] Paiement enregistre
- [ ] Tout l'historique visible

---

# Felicitations !

Vous avez termine la formation AZALSCORE.

## Prochaines Etapes

1. **Pratiquez** quotidiennement avec les vrais donnees
2. **Explorez** les modules specifiques a votre role
3. **Consultez** la documentation en cas de doute
4. **Contactez** le support si besoin

## Ressources

- Documentation : docs.azalscore.com
- Support : support@azalscore.com
- Assistant IA : Theo (💬)

---

*Formation AZALSCORE v2.0 - Fevrier 2026*
