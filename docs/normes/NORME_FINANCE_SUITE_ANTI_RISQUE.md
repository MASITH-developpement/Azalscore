# AZALSCORE - Norme de Gestion des Risques Finance Suite

**Reference:** AZA-NF-060
**Version:** 1.1.1
**Date:** 2026-02-15
**Classification:** CONFIDENTIEL - USAGE INTERNE
**Conformite:** Droit francais, Droit europeen, Reglementation ACPR, LCB-FT, RGPD, PCI DSS

---

## PREAMBULE

La presente norme definit le cadre de gestion des risques applicable a l'integration des services financiers au sein de la plateforme AZALSCORE. Elle etablit les principes fondamentaux, les obligations contractuelles et les procedures operationnelles garantissant une protection maximale de la societe AZALSCORE et de ses utilisateurs.

Cette norme est opposable a l'ensemble des collaborateurs, prestataires et partenaires intervenant sur les services financiers de la plateforme.

---

## CADRE JURIDIQUE APPLICABLE

### Droit Applicable

La presente norme et l'ensemble des relations contractuelles avec les partenaires financiers sont regies par le droit francais, sans prejudice des dispositions imperatives du droit de l'Union europeenne directement applicables.

La hierarchie des normes applicables s'etablit comme suit :

**Premier niveau - Droit de l'Union europeenne**

Le Reglement UE 2016/679 du vingt-sept avril deux mille seize relatif a la protection des personnes physiques a l'egard du traitement des donnees a caractere personnel dit RGPD s'applique directement.

La Directive UE 2015/2366 du vingt-cinq novembre deux mille quinze concernant les services de paiement dans le marche interieur dite DSP2 s'applique telle que transposee en droit francais.

Le Reglement UE 2022/2554 du quatorze decembre deux mille vingt-deux sur la resilience operationnelle numerique du secteur financier dit DORA s'applique directement.

**Deuxieme niveau - Droit francais**

Le Code Monetaire et Financier s'applique, notamment :

- Livre V, Titre I relatif aux prestataires de services de paiement, articles L. 521-1 a L. 526-35
- Livre V, Titre II relatif aux prestataires de services bancaires, articles L. 531-1 a L. 533-31
- Livre V, Titre VI relatif aux obligations relatives a la lutte contre le blanchiment des capitaux, articles L. 561-1 a L. 561-50

Le Code Civil s'applique, notamment :

- Livre III, Titre III relatif aux contrats, articles 1101 a 1231-7
- Livre III, Titre IV bis relatif de la responsabilite extracontractuelle, articles 1240 a 1244

Le Code de Commerce s'applique, notamment :

- Livre I, Titre II relatif aux commercants, articles L. 121-1 a L. 128-1
- Livre IV, Titre IV relatif a la transparence et aux pratiques restrictives, articles L. 441-1 a L. 443-8

Le Code de la Consommation s'applique pour les relations avec les utilisateurs finaux personnes physiques agissant a des fins non professionnelles.

**Troisieme niveau - Reglementation sectorielle**

Les instructions et recommandations de l'Autorite de Controle Prudentiel et de Resolution s'appliquent.

Les deliberations de la Commission Nationale de l'Informatique et des Libertes s'appliquent.

Le standard PCI DSS dans sa version en vigueur s'applique pour les operations impliquant des donnees de cartes bancaires.

### Juridiction Competente

**Principe general**

Tout litige relatif a l'interpretation ou a l'execution de la presente norme, ainsi que tout litige avec les partenaires financiers, releve de la competence exclusive des juridictions francaises.

**Juridictions competentes selon la nature du litige**

Pour les litiges commerciaux avec les partenaires, le Tribunal de Commerce de Digne-les-Bains est seul competent, nonobstant toute clause contraire.

Pour les litiges impliquant des consommateurs au sens du Code de la Consommation, les regles de competence territoriale de droit commun s'appliquent, sans possibilite de derogation contractuelle conformement a l'article R. 631-3 du Code de la Consommation.

Pour les litiges relatifs a la protection des donnees personnelles, la Commission Nationale de l'Informatique et des Libertes et les juridictions competentes en matiere de donnees personnelles sont saisies.

Pour les litiges relatifs aux agrements et a la conformite reglementaire, l'Autorite de Controle Prudentiel et de Resolution est l'autorite competente.

**Clause attributive de juridiction obligatoire**

Tous les contrats conclus avec des partenaires financiers doivent imperativement inclure la clause suivante :

Les parties conviennent expressement que tout litige relatif a la validite, l'interpretation, l'execution ou la resiliation du present contrat sera soumis a la competence exclusive des tribunaux francais, et plus precisement du Tribunal de Commerce de Digne-les-Bains pour les litiges de nature commerciale. Les parties renoncent expressement a toute autre juridiction qui pourrait etre competente en vertu de leur domicile, de leur siege social ou de toute autre regle de competence.

### Langue des Contrats

Tous les contrats conclus avec les partenaires financiers doivent etre rediges en langue francaise, conformement a la loi du quatre aout mille neuf cent quatre-vingt-quatorze relative a l'emploi de la langue francaise dite loi Toubon.

Lorsqu'un partenaire exige une version en langue etrangere, cette version ne peut avoir qu'une valeur informative. Seule la version francaise fait foi en cas de divergence d'interpretation.

### Notifications et Communications Officielles

Toutes les notifications officielles entre AZALSCORE et ses partenaires financiers doivent etre effectuees par lettre recommandee avec accuse de reception adressee au siege social de chaque partie, ou par tout autre moyen permettant de conferer date certaine a l'envoi.

Les adresses de notification sont les suivantes :

Pour AZALSCORE : siege social tel qu'inscrit au Registre du Commerce et des Societes.

Pour les partenaires : adresse designee dans chaque contrat de partenariat.

---

## 1. PRINCIPES FONDAMENTAUX

### 1.1 Principe de Non-Transit des Fonds

AZALSCORE n'effectue en aucun cas de manipulation directe des flux financiers. L'ensemble des operations de paiement, virement, encaissement et decaissement sont realisees exclusivement par les partenaires agrees disposant des agrements reglementaires requis.

Ce principe implique que :
- Aucun compte bancaire n'est ouvert au nom d'AZALSCORE pour le transit de fonds clients
- Aucune tresorerie client ne transite par les comptes de la societe
- Les flux financiers s'effectuent directement entre les utilisateurs et les etablissements agrees

### 1.2 Principe de Marque Blanche

AZALSCORE opere exclusivement en qualite de distributeur technique sous regime de marque blanche. Les services financiers sont fournis sous les agrements et licences des partenaires regulateurs.

Ce positionnement implique que :
- AZALSCORE ne detient aucun agrement de service de paiement
- AZALSCORE ne detient aucun agrement d'etablissement de credit
- AZALSCORE n'exerce aucune activite reglementee au sens du Code Monetaire et Financier

### 1.3 Principe de Responsabilite Delimitee

AZALSCORE assume exclusivement la responsabilite de l'intermediation technique. La responsabilite des operations financieres incombe integralement aux partenaires agrees.

La delimitation s'etablit comme suit :
- AZALSCORE : interface utilisateur, transmission des ordres, affichage des informations
- Partenaires : execution des operations, conformite reglementaire, gestion des litiges financiers

### 1.4 Principe d'Isolation Multi-Tenant

L'architecture technique garantit une segregation stricte des donnees financieres entre les differents tenants de la plateforme. Aucune donnee financiere d'un tenant ne peut etre accessible par un autre tenant.

---

## 2. ARCHITECTURE DES PARTENARIATS

### 2.1 Cartographie des Services et Partenaires

| Service | Partenaire Recommande | Type d'Agrement | Juridiction |
|---------|----------------------|-----------------|-------------|
| Compte bancaire integre | Swan | Etablissement de Paiement agree ACPR | France |
| Paiements en ligne | NMI | Payment Facilitator | International |
| Terminal de paiement mobile | NMI | Payment Facilitator | International |
| Affacturage | Defacto | Societe de Financement | France |
| Credit aux entreprises | Solaris | Etablissement de Credit | Allemagne et Union Europeenne |

### 2.2 Repartition des Responsabilites

| Fonction | AZALSCORE | Partenaire |
|----------|-----------|------------|
| Interface utilisateur | Responsable | Non concerne |
| Transmission des ordres | Responsable | Non concerne |
| Verification d'identite KYC et KYB | Non concerne | Responsable |
| Execution des paiements | Non concerne | Responsable |
| Conformite LCB-FT | Non concerne | Responsable |
| Decisions d'octroi de credit | Non concerne | Responsable |
| Gestion des litiges financiers | Non concerne | Responsable |
| Stockage des donnees de carte | Non concerne | Responsable |
| Disponibilite de l'interface | Responsable | Non concerne |
| Disponibilite des services financiers | Non concerne | Responsable |

---

## 3. GESTION DES RISQUES REGLEMENTAIRES

### 3.1 Risque d'Exercice Illegal d'Activite Reglementee

**Description du risque**

Requalification de l'activite d'AZALSCORE en service de paiement ou etablissement de credit non agree par l'Autorite de Controle Prudentiel et de Resolution.

**Mesures de mitigation**

Une validation juridique prealable par un cabinet specialise en droit bancaire et fintech est obligatoire avant tout lancement de service. Un audit annuel de conformite par un tiers independant doit etre realise. Chaque contrat partenaire doit inclure une clause explicite de marque blanche. Une documentation ecrite du perimetre exact des prestations AZALSCORE doit etre maintenue et mise a jour.

**Indicateurs de surveillance**

Le nombre de reclamations clients mentionnant AZALSCORE comme prestataire de paiement doit etre suivi. Les alertes de non-conformite emises par les partenaires doivent etre tracees. Une veille sur l'evolution de la jurisprudence applicable doit etre assuree.

### 3.2 Risque de Non-Conformite LCB-FT

**Description du risque**

Mise en cause d'AZALSCORE pour complicite de blanchiment de capitaux ou defaut de vigilance au titre de la lutte contre le blanchiment et le financement du terrorisme.

**Mesures de mitigation**

La delegation contractuelle integrale de la conformite LCB-FT aux partenaires agrees est obligatoire. Une clause de garantie et d'indemnisation par le partenaire en cas de mise en cause d'AZALSCORE doit figurer dans chaque contrat. Toute information suspecte doit etre transmise immediatement au partenaire concerne. Une formation annuelle des equipes aux signaux d'alerte est obligatoire.

**Indicateurs de surveillance**

Le nombre de signalements transmis aux partenaires, le delai moyen de transmission des alertes et les demandes d'information des autorites concernant des clients doivent etre suivis.

### 3.3 Risque de Non-Conformite RGPD

**Description du risque**

Non-conformite au Reglement General sur la Protection des Donnees pour les donnees financieres traitees par la plateforme.

**Mesures de mitigation**

Une qualification juridique de chaque partenaire en tant que responsable de traitement ou sous-traitant doit etre etablie. Un contrat de traitement des donnees conforme a l'article vingt-huit du RGPD doit etre signe avec chaque partenaire. Le droit a la portabilite des donnees financieres doit etre operationnel. Une procedure de notification des violations de donnees doit etre documentee et testee.

**Indicateurs de surveillance**

Le nombre de demandes d'exercice de droits concernant les donnees financieres, les incidents de securite impliquant des donnees financieres et les resultats des audits de conformite RGPD doivent etre suivis.

### 3.4 Risque de Non-Conformite PCI DSS

**Description du risque**

Compromission de donnees de cartes bancaires entrainant la responsabilite d'AZALSCORE au titre du standard PCI DSS.

**Mesures de mitigation**

Le stockage de donnees de carte sur les systemes AZALSCORE est strictement interdit. Seule la tokenisation fournie par le partenaire de paiement peut etre utilisee. L'integration doit s'effectuer exclusivement via les composants certifies fournis par le partenaire. Un audit de securite annuel de l'integration doit etre realise.

**Indicateurs de surveillance**

La presence de donnees de carte dans les journaux applicatifs doit etre verifiee. Les resultats des tests de penetration doivent etre analyses. La validite du certificat PCI DSS du partenaire doit etre controlee.

---

## 4. GESTION DES RISQUES FINANCIERS

### 4.1 Risque de Fraude

**Description du risque**

Utilisation frauduleuse des services de paiement par des tiers malveillants entrainant des pertes financieres.

**Mesures de mitigation**

La detection et la prevention de la fraude sont deleguees au partenaire de paiement. Une clause contractuelle de responsabilite integrale du partenaire pour les fraudes doit figurer dans chaque contrat. L'authentification forte de type 3D Secure est obligatoire pour les paiements en ligne. Des limites de montant par operation sont definies contractuellement.

**Indicateurs de surveillance**

Le taux de fraude communique par le partenaire, le nombre de contestations clients et l'evolution du taux de rejets de paiement doivent etre suivis.

### 4.2 Risque de Contestations de Paiement

**Description du risque**

Contestations de paiements par les titulaires de carte entrainant des penalites financieres pour AZALSCORE.

**Mesures de mitigation**

Une clause contractuelle de prise en charge des contestations par le partenaire doit figurer dans chaque contrat. Les pieces justificatives doivent etre transmises immediatement au partenaire en cas de contestation. Les utilisateurs doivent etre formes aux bonnes pratiques de documentation des ventes. Un seuil d'alerte est defini contractuellement.

**Indicateurs de surveillance**

Le taux de contestation par tenant, le delai moyen de resolution des contestations et le montant cumule des contestations doivent etre suivis.

### 4.3 Risque de Credit

**Description du risque**

Defaillance d'emprunteurs pour les services de credit et d'affacturage entrainant des pertes pour AZALSCORE.

**Mesures de mitigation**

Une clause contractuelle de garantie zero pour AZALSCORE est obligatoire dans tous les contrats de credit et d'affacturage. La decision d'octroi releve exclusivement du partenaire agree. Aucune caution ni garantie ne peut etre accordee par AZALSCORE. L'absence de recours possible contre AZALSCORE par le partenaire doit etre stipulee contractuellement.

**Indicateurs de surveillance**

Le taux de defaut communique par le partenaire, l'evolution des criteres d'octroi du partenaire et les reclamations eventuelles du partenaire concernant la qualite des dossiers doivent etre suivis.

### 4.4 Risque de Tresorerie

**Description du risque**

Impact negatif sur la tresorerie d'AZALSCORE en cas de litige financier avec un partenaire ou un utilisateur.

**Mesures de mitigation**

Aucune retenue ou compensation ne peut etre operee par le partenaire sur les commissions dues a AZALSCORE au titre des operations clients. Une separation stricte des flux de commissions et des flux clients doit etre assuree. Une clause de preavis minimum de trente jours pour toute modification des conditions commerciales doit figurer dans chaque contrat. Une reserve de tresorerie minimale doit etre maintenue.

**Indicateurs de surveillance**

La regularite des versements de commissions, les litiges en cours avec les partenaires et l'evolution des conditions commerciales doivent etre suivis.

---

## 5. GESTION DES RISQUES TECHNIQUES

### 5.1 Risque de Securite Informatique

**Description du risque**

Compromission des systemes AZALSCORE affectant les services financiers et les donnees des utilisateurs.

**Mesures de mitigation**

Toutes les communications avec les partenaires doivent etre chiffrees. L'authentification forte est obligatoire pour l'acces aux fonctions financieres. Une journalisation complete des operations financieres doit etre assuree avec une conservation de cinq ans. Un test de penetration annuel sur les modules financiers doit etre realise.

**Indicateurs de surveillance**

Les alertes de securite sur les modules financiers, les tentatives d'acces non autorises et les vulnerabilites identifiees avec leur delai de correction doivent etre suivis.

### 5.2 Risque de Disponibilite

**Description du risque**

Indisponibilite des services financiers impactant les utilisateurs et l'activite commerciale.

**Mesures de mitigation**

Un niveau de service minimum de quatre-vingt-dix-neuf virgule neuf pour cent doit etre garanti contractuellement par chaque partenaire. Un mecanisme de repli doit etre prevu en cas d'indisponibilite du partenaire principal. Une notification proactive des utilisateurs doit etre effectuee en cas d'incident. Une procedure de compensation doit etre definie contractuellement.

**Indicateurs de surveillance**

Le taux de disponibilite reel des services financiers, le nombre et la duree des incidents et le respect des engagements de niveau de service par les partenaires doivent etre suivis.

### 5.3 Risque d'Integration Technique

**Description du risque**

Dysfonctionnement de l'integration technique avec les partenaires entrainant des erreurs dans les operations financieres.

**Mesures de mitigation**

Un environnement de test permanent doit etre maintenu avec chaque partenaire. Une procedure de validation avant mise en production est obligatoire. La version minimale des interfaces de programmation doit etre documentee et maintenue. Un plan de migration doit etre etabli en cas de changement majeur.

**Indicateurs de surveillance**

Le taux d'erreur des appels aux interfaces des partenaires, les alertes de depreciation des interfaces et les incidents lies aux mises a jour doivent etre suivis.

---

## 6. GESTION DES RISQUES OPERATIONNELS

### 6.1 Risque de Support Client

**Description du risque**

Incapacite a traiter les demandes clients concernant les services financiers dans des delais acceptables.

**Mesures de mitigation**

Une procedure d'escalade claire vers le support du partenaire doit etre definie. Une documentation des cas d'usage et des procedures de resolution doit etre maintenue. Une formation reguliere des equipes support est obligatoire. Un suivi des indicateurs de qualite de service doit etre assure.

**Indicateurs de surveillance**

Le delai moyen de resolution des tickets relatifs aux services financiers, le taux de satisfaction client sur les services financiers et le nombre d'escalades vers les partenaires doivent etre suivis.

### 6.2 Risque de Dependance Partenaire

**Description du risque**

Defaillance ou retrait d'un partenaire strategique compromettant la continuite des services financiers.

**Mesures de mitigation**

Une clause de preavis minimum de six mois en cas de resiliation doit figurer dans chaque contrat. Une clause de portabilite des donnees vers un nouveau partenaire est obligatoire. Des partenaires alternatifs doivent etre identifies pour chaque service. Une revue annuelle de la sante financiere des partenaires doit etre effectuee.

**Indicateurs de surveillance**

La notation financiere des partenaires, les communications officielles des partenaires et l'evolution des conditions commerciales doivent etre suivis.

---

## 7. CLAUSES CONTRACTUELLES OBLIGATOIRES

### 7.1 Clauses Communes a Tous les Partenaires

Chaque contrat de partenariat doit imperativement inclure les clauses suivantes.

**Clause de Marque Blanche**

Le Partenaire reconnait qu'AZALSCORE opere exclusivement en qualite de distributeur technique sous regime de marque blanche. Le Partenaire garantit qu'AZALSCORE n'exerce aucune activite reglementee au titre du present contrat et que l'ensemble des services financiers sont fournis sous les agrements et licences du Partenaire.

**Clause de Non-Transit des Fonds**

Les parties conviennent expressement qu'aucun fonds appartenant aux utilisateurs finaux ne transitera par les comptes d'AZALSCORE. L'ensemble des flux financiers s'effectuera directement entre les utilisateurs et les comptes du Partenaire ou des etablissements designes par celui-ci.

**Clause de Responsabilite**

Le Partenaire assume l'entiere responsabilite de la conformite reglementaire des services financiers fournis aux utilisateurs finaux. AZALSCORE ne saurait etre tenu responsable des decisions d'octroi, des operations de paiement, ou de tout litige financier impliquant les utilisateurs finaux.

**Clause de Garantie et Indemnisation**

Le Partenaire s'engage a garantir et indemniser AZALSCORE contre toute reclamation, action, poursuite ou condamnation resultant de l'execution des services financiers, y compris les frais de defense et honoraires d'avocats.

**Clause de Niveau de Service**

Le Partenaire s'engage a maintenir un niveau de disponibilite de ses services d'au minimum quatre-vingt-dix-neuf virgule neuf pour cent calcule sur une base mensuelle. En cas de non-respect, les penalites prevues a l'annexe technique s'appliqueront.

**Clause de Portabilite**

En cas de resiliation du contrat, le Partenaire s'engage a fournir a AZALSCORE l'ensemble des donnees clients dans un format standard et exploitable, dans un delai maximum de trente jours suivant la date de resiliation.

**Clause de Preavis**

Toute resiliation du contrat par l'une ou l'autre des parties doit respecter un preavis minimum de six mois notifie par lettre recommandee avec accuse de reception.

**Clause de Droit Applicable et Juridiction Competente**

Le present contrat est regi par le droit francais. Tout litige relatif a sa validite, son interpretation, son execution ou sa resiliation sera soumis a la competence exclusive des tribunaux francais, et plus precisement du Tribunal de Commerce de Digne-les-Bains. Les parties renoncent expressement a toute autre juridiction qui pourrait etre competente.

**Clause de Langue**

Le present contrat est redige en langue francaise. En cas de traduction dans une autre langue, seule la version francaise fait foi.

**Clause de Conformite au Droit Francais**

Le Partenaire s'engage a respecter l'ensemble des dispositions du droit francais applicables a l'execution du present contrat, notamment le Code Monetaire et Financier, le Code Civil, le Code de Commerce et le Code de la Consommation. Le Partenaire garantit AZALSCORE contre toute consequence resultant d'un manquement a cette obligation.

### 7.2 Clauses Specifiques aux Services Bancaires

Les contrats avec les partenaires de services bancaires tels que Swan doivent inclure les clauses specifiques suivantes.

La delegation integrale de la verification d'identite des clients et des entreprises doit etre stipulee. La responsabilite exclusive du Partenaire pour la conformite LCB-FT doit etre affirmee. L'impossibilite pour le Partenaire d'operer toute retention sur les commissions dues a AZALSCORE au titre des operations clients doit etre garantie.

### 7.3 Clauses Specifiques aux Services de Paiement

Les contrats avec les partenaires de services de paiement tels que NMI doivent inclure les clauses specifiques suivantes.

La responsabilite exclusive du Partenaire pour la gestion des fraudes et des contestations de paiement doit etre stipulee. L'obligation de tokenisation excluant tout stockage de donnees de carte par AZALSCORE doit etre affirmee. Le modele de tarification doit etre transparent et de type interchange plus marge.

### 7.4 Clauses Specifiques aux Services d'Affacturage

Les contrats avec les partenaires de services d'affacturage tels que Defacto doivent inclure les clauses specifiques suivantes.

Le risque de credit doit etre porte integralement par le Partenaire. Aucune garantie ni caution ne peut etre accordee par AZALSCORE. La remuneration d'AZALSCORE doit etre exclusivement sous forme de commission sur les operations realisees.

### 7.5 Clauses Specifiques aux Services de Credit

Les contrats avec les partenaires de services de credit tels que Solaris doivent inclure les clauses specifiques suivantes. Ces clauses sont qualifiees d'essentielles et leur absence rend le contrat nul et non avenu.

L'autonomie complete du Partenaire sur les decisions d'octroi de credit doit etre affirmee. La clause de garantie zero pour AZALSCORE est une clause essentielle dont la violation entraine la nullite du contrat. L'absence de tout recours contre AZALSCORE en cas de defaillance d'emprunteur doit etre stipulee expressement.

---

## 8. PROCEDURES DE CONTROLE

### 8.1 Controles Quotidiens

| Controle | Responsable | Documentation |
|----------|-------------|---------------|
| Verification des reconciliations de paiements | Equipe Finance | Rapport automatise |
| Surveillance des alertes de securite | Equipe Technique | Journal des alertes |
| Verification de la disponibilite des services | Equipe Technique | Tableau de bord |
| Traitement des reclamations urgentes | Equipe Support | Ticket de suivi |

### 8.2 Controles Hebdomadaires

| Controle | Responsable | Documentation |
|----------|-------------|---------------|
| Analyse des taux de fraude | Equipe Finance | Rapport d'analyse |
| Revue des contestations de paiement | Equipe Finance | Tableau de suivi |
| Verification des niveaux de service | Equipe Technique | Rapport de niveau de service |
| Point de coordination avec les partenaires | Responsable Partenariats | Compte-rendu de reunion |

### 8.3 Controles Mensuels

| Controle | Responsable | Documentation |
|----------|-------------|---------------|
| Revue des indicateurs de risque | Direction | Tableau de bord des risques |
| Analyse des tendances de fraude | Equipe Finance | Rapport mensuel |
| Verification de la conformite contractuelle | Service Juridique | Liste de controle |
| Reconciliation des commissions | Equipe Finance | Rapport comptable |

### 8.4 Controles Annuels

| Controle | Responsable | Documentation |
|----------|-------------|---------------|
| Audit de conformite reglementaire | Cabinet externe agree | Rapport d'audit |
| Test de penetration des modules financiers | Prestataire de securite certifie | Rapport de test |
| Revue des contrats partenaires | Service Juridique | Analyse contractuelle |
| Formation conformite des equipes | Ressources Humaines | Attestation de formation |
| Test de continuite d'activite | Direction Technique | Proces-verbal de test |

---

## 9. PROCEDURE D'ESCALADE DES INCIDENTS

### 9.1 Classification des Incidents

| Niveau | Description | Exemples | Delai de Resolution |
|--------|-------------|----------|---------------------|
| Critique | Impact majeur sur les operations financieres | Indisponibilite complete des paiements ou fuite de donnees | Quatre heures |
| Majeur | Impact significatif sur une partie des utilisateurs | Echecs de paiement recurrents ou retards de virement | Huit heures |
| Modere | Impact limite sur quelques utilisateurs | Erreur d'affichage de solde ou delai inhabituel | Vingt-quatre heures |
| Mineur | Impact negligeable | Question utilisateur ou demande d'information | Quarante-huit heures |

### 9.2 Matrice d'Escalade

| Niveau | Premier Contact | Escalade Niveau Un | Escalade Niveau Deux | Escalade Niveau Trois |
|--------|-----------------|-------------------|---------------------|----------------------|
| Critique | Support Partenaire | Direction Technique | Direction Generale | Conseil Juridique |
| Majeur | Support Partenaire | Responsable Technique | Direction Technique | Non applicable |
| Modere | Support Interne | Support Partenaire | Responsable Technique | Non applicable |
| Mineur | Support Interne | Non applicable | Non applicable | Non applicable |

### 9.3 Procedure de Notification

En cas d'incident critique ou majeur, la procedure de notification suivante s'applique.

Une notification immediate aux utilisateurs concernes doit etre effectuee via l'interface de la plateforme. Une communication par courrier electronique doit etre envoyee dans un delai de deux heures. Des mises a jour regulieres doivent etre communiquees toutes les heures jusqu'a resolution de l'incident. Un rapport post-incident doit etre redige et diffuse dans les soixante-douze heures suivant la resolution.

---

## 10. AUDIT ET CONFORMITE

### 10.1 Audits Internes

| Type d'Audit | Frequence | Perimetre | Responsable |
|--------------|-----------|-----------|-------------|
| Conformite contractuelle | Trimestriel | Respect des clauses partenaires | Service Juridique |
| Securite des integrations | Semestriel | Tests techniques | Direction Technique |
| Procedures operationnelles | Annuel | Ensemble des procedures | Service Qualite |

### 10.2 Audits Externes

| Type d'Audit | Frequence | Perimetre | Prestataire |
|--------------|-----------|-----------|-------------|
| Conformite reglementaire | Annuel | ACPR, RGPD, PCI DSS | Cabinet agree |
| Securite informatique | Annuel | Tests de penetration | Prestataire certifie |
| Certification des comptes | Annuel | Comptes annuels | Commissaire aux comptes |

### 10.3 Conservation des Preuves

| Type de Document | Duree de Conservation | Support |
|------------------|----------------------|---------|
| Contrats partenaires | Dix ans apres fin de contrat | Numerique signe electroniquement |
| Journaux des operations financieres | Cinq ans | Base de donnees securisee |
| Rapports d'audit | Dix ans | Archive numerique |
| Reclamations clients | Cinq ans | Systeme de gestion des tickets |
| Correspondances partenaires | Cinq ans | Messagerie archivee |

---

## 11. PROCESSUS DE VALIDATION JURIDIQUE

### 11.1 Validation Initiale

Avant tout lancement de service financier, la validation juridique suivante est obligatoire.

**Phase Un - Selection du Cabinet Juridique**

Cette phase d'une duree d'une semaine comprend l'identification d'un cabinet specialise en droit bancaire et fintech, la verification des references en matiere de services de paiement et la signature du contrat de mission.

**Phase Deux - Analyse Reglementaire**

Cette phase d'une duree de deux semaines comprend l'analyse du positionnement juridique d'AZALSCORE, la verification de l'absence de necessite d'agrement, l'identification des risques specifiques et les recommandations sur la structure contractuelle.

**Phase Trois - Redaction des Contrats**

Cette phase d'une duree de deux semaines comprend la redaction ou la revue des contrats partenaires, l'integration des clauses obligatoires et la negociation des points juridiques sensibles.

**Phase Quatre - Validation Finale**

Cette phase d'une duree d'une semaine comprend la delivrance de l'attestation de conformite par le cabinet, l'archivage de l'ensemble de la documentation juridique et le briefing des equipes concernees.

### 11.2 Validations Periodiques

| Evenement Declencheur | Action Requise | Responsable |
|----------------------|----------------|-------------|
| Nouveau partenaire | Validation juridique complete | Service Juridique |
| Modification contractuelle majeure | Revue juridique | Service Juridique |
| Evolution reglementaire | Analyse d'impact | Cabinet externe |
| Incident de conformite | Audit de conformite | Cabinet externe |

---

## 12. DISPOSITIONS FINALES

### 12.1 Entree en Vigueur

La presente norme entre en vigueur a compter de sa date d'approbation par la Direction Generale. Elle s'applique a l'ensemble des services financiers existants et futurs de la plateforme AZALSCORE.

### 12.2 Revisions

Cette norme fait l'objet d'une revue annuelle ou en cas d'evolution reglementaire significative. Toute modification doit etre approuvee par la Direction Generale apres avis du service juridique.

### 12.3 Diffusion

Cette norme est diffusee a l'ensemble des collaborateurs concernes par les services financiers. Une formation specifique est dispensee lors de l'integration de tout nouveau collaborateur.

### 12.4 Non-Respect

Tout manquement aux dispositions de la presente norme expose son auteur a des sanctions disciplinaires pouvant aller jusqu'au licenciement pour faute grave, sans prejudice des eventuelles poursuites civiles ou penales.

---

## ANNEXE A - GLOSSAIRE

| Terme | Definition |
|-------|------------|
| ACPR | Autorite de Controle Prudentiel et de Resolution, autorite de supervision bancaire francaise |
| Contestation de paiement | Demande de remboursement initiee par le titulaire d'une carte bancaire aupres de sa banque |
| KYC | Know Your Customer, procedures de verification d'identite des clients |
| KYB | Know Your Business, procedures de verification d'identite des entreprises |
| LCB-FT | Lutte Contre le Blanchiment et le Financement du Terrorisme |
| Marque Blanche | Distribution de services sous licence du fournisseur sans mention de celui-ci |
| PCI DSS | Payment Card Industry Data Security Standard, norme de securite des donnees de carte |
| RGPD | Reglement General sur la Protection des Donnees, reglement europeen |
| SLA | Service Level Agreement, accord de niveau de service |
| Tokenisation | Remplacement des donnees sensibles par un jeton securise non reversible |

---

## ANNEXE B - REFERENCES JURIDIQUES

Les textes suivants constituent le cadre juridique applicable a la presente norme.

### Droit de l'Union Europeenne

Reglement UE 2016/679 du Parlement europeen et du Conseil du vingt-sept avril deux mille seize relatif a la protection des personnes physiques a l'egard du traitement des donnees a caractere personnel et a la libre circulation de ces donnees, dit Reglement General sur la Protection des Donnees.

Directive UE 2015/2366 du Parlement europeen et du Conseil du vingt-cinq novembre deux mille quinze concernant les services de paiement dans le marche interieur, dite Directive sur les Services de Paiement 2.

Reglement UE 2022/2554 du Parlement europeen et du Conseil du quatorze decembre deux mille vingt-deux sur la resilience operationnelle numerique du secteur financier, dit DORA.

Directive UE 2015/849 du Parlement europeen et du Conseil du vingt mai deux mille quinze relative a la prevention de l'utilisation du systeme financier aux fins du blanchiment de capitaux ou du financement du terrorisme.

### Droit Francais

**Code Monetaire et Financier**

Articles L. 521-1 a L. 521-10 relatifs aux conditions d'acces a la profession de prestataire de services de paiement.

Articles L. 522-1 a L. 522-19 relatifs aux etablissements de paiement.

Articles L. 523-1 a L. 523-6 relatifs aux agents de prestataires de services de paiement.

Articles L. 561-1 a L. 561-50 relatifs aux obligations de vigilance et de declaration pour la lutte contre le blanchiment des capitaux et le financement du terrorisme.

Articles L. 314-1 a L. 314-18 relatifs aux services de paiement.

**Code Civil**

Articles 1101 a 1231-7 relatifs au droit des contrats.

Articles 1240 a 1244 relatifs a la responsabilite extracontractuelle.

**Code de Commerce**

Articles L. 441-1 a L. 443-8 relatifs a la transparence et aux pratiques restrictives de concurrence.

**Code de la Consommation**

Articles L. 221-1 a L. 221-29 relatifs aux contrats conclus a distance.

Articles L. 312-1 a L. 312-94 relatifs au credit a la consommation.

Articles R. 631-3 relatif a la competence juridictionnelle.

**Loi du quatre aout mille neuf cent quatre-vingt-quatorze**

Loi relative a l'emploi de la langue francaise dite loi Toubon.

### Reglementation Sectorielle

Instructions de l'Autorite de Controle Prudentiel et de Resolution relatives aux etablissements de paiement et aux etablissements de monnaie electronique.

Recommandations de l'ACPR sur les dispositifs de maitrise des risques lies aux activites d'externalisation.

Recommandations de l'ACPR sur les partenariats entre etablissements de paiement et distributeurs.

Deliberations de la Commission Nationale de l'Informatique et des Libertes relatives au secteur bancaire et financier.

Standard PCI DSS version 4.0 relatif a la securite des donnees de l'industrie des cartes de paiement.

---

## ANNEXE C - CONTACTS

| Role | Service | Adresse electronique |
|------|---------|---------------------|
| Responsable Conformite | Direction Juridique | conformite@azals.io |
| Responsable Securite | Direction Technique | securite@azals.io |
| Responsable Partenariats | Direction Commerciale | partenariats@azals.io |
| Support Finance Suite | Service Client | support-finance@azals.io |

---

## HISTORIQUE DES REVISIONS

| Version | Date | Auteur | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-15 | Direction Technique | Creation initiale |
| 1.1.0 | 2026-02-15 | Direction Technique | Ajout du cadre juridique applicable, references au droit francais et europeen, clauses de juridiction competente |
| 1.1.1 | 2026-02-15 | Direction Technique | Juridiction competente: Tribunal de Commerce de Digne-les-Bains (siege social Alpes-de-Haute-Provence) |

---

## APPROBATIONS

| Fonction | Nom | Date | Signature |
|----------|-----|------|-----------|
| Directeur General | | | |
| Directeur Technique | | | |
| Responsable Juridique | | | |
| Responsable Conformite | | | |

---

**Prochaine revision prevue :** 2027-02-15

**Document reference :** AZA-NF-060-v1.1.1

---

*Ce document est la propriete exclusive de la societe AZALSCORE. Toute reproduction ou diffusion non autorisee est interdite.*
