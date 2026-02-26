# Documentation de Formation AZALSCORE

## ERP Decisionnel Nouvelle Generation

---

## Vue d'Ensemble

Cette documentation de formation complete permet aux utilisateurs de prendre en main l'ERP AZALSCORE de maniere progressive et exhaustive. Elle comprend trois volets complementaires :

1. **Documentation PDF/Markdown** : Guides complets a lire et imprimer
2. **Formation E-Learning** : Modules video interactifs (SCORM compatible)
3. **Formation In-App** : Tutoriels integres directement dans l'application

---

### Documents Disponibles

| Document | Public Cible | Contenu |
|----------|--------------|---------|
| [Guide Utilisateur](GUIDE_UTILISATEUR_AZALSCORE.md) | Tous | Guide complet de 450+ pages couvrant l'ensemble des modules |
| [Fiches Pratiques](FICHES_PRATIQUES_PAR_PROFIL.md) | Par metier | Procedures detaillees par profil (Commercial, Comptable, RH, etc.) |
| [Reference Rapide](REFERENCE_RAPIDE.md) | Tous | Carte de reference a imprimer - raccourcis et operations courantes |
| [Exercices Pratiques](EXERCICES_PRATIQUES.md) | Formation | 7 modules d'exercices guides avec quiz final |
| [Guide Administrateur](GUIDE_ADMINISTRATEUR.md) | Admins | Configuration, securite, maintenance |

---

## Parcours de Formation Recommandes

### Nouvel Utilisateur (4 heures)

1. **Guide Utilisateur** - Chapitres 1 a 3 (1h)
   - Introduction
   - Premiers pas
   - Navigation

2. **Exercices Pratiques** - Modules 1 et 2 (1h30)
   - Prise en main
   - Gestion clients

3. **Fiches Pratiques** - Votre profil (1h)
   - Procedures specifiques a votre role

4. **Reference Rapide** (30min)
   - A garder sur le bureau

### Utilisateur Avance (2 heures)

1. **Guide Utilisateur** - Chapitres 4 a 7 (1h)
   - Modules metier specifiques

2. **Exercices Pratiques** - Modules 3 a 5 (1h)
   - Devis/Facturation
   - Stocks
   - Comptabilite

### Administrateur (3 heures)

1. **Guide Administrateur** - Complet (2h)
   - Configuration
   - Securite
   - Maintenance

2. **Guide Utilisateur** - Chapitres 10-11 (1h)
   - Administration
   - Workflows

---

## Structure Pedagogique

### Niveaux de Competence

| Niveau | Objectif | Duree |
|--------|----------|-------|
| **Debutant** | Naviguer, saisir des donnees | 4h |
| **Intermediaire** | Utiliser tous les modules de son perimetre | 8h |
| **Avance** | Creer des rapports, automatiser | 4h |
| **Expert** | Administrer, configurer | 4h |

### Certification (Optionnelle)

Apres completion des exercices :
1. Quiz de connaissances (20 questions)
2. Exercice pratique supervise
3. Certificat de competence AZALSCORE

---

## Modules Couverts

### Gestion Commerciale
- CRM et gestion des clients
- Devis et propositions
- Commandes clients et fournisseurs
- Facturation et relances
- Paiements et encaissements

### Finance
- Tresorerie et previsions
- Comptabilite generale
- Rapprochement bancaire
- Immobilisations
- Notes de frais

### Operations
- Gestion des stocks
- Production et nomenclatures
- Controle qualite
- Maintenance (GMAO)
- Interventions terrain

### Ressources Humaines
- Dossiers employes
- Gestion des conges
- Feuilles de temps
- Paie (export)

### Intelligence
- Cockpit dirigeant
- Business Intelligence
- Assistant IA (Theo)
- Agent IA (Marceau)

### Administration
- Gestion des utilisateurs
- Roles et permissions
- Securite
- Audit
- Sauvegardes

---

## Support de Formation

### Ressources Additionnelles

| Ressource | Acces |
|-----------|-------|
| Documentation en ligne | docs.azalscore.com |
| Videos tutorielles | videos.azalscore.com |
| FAQ | faq.azalscore.com |
| Support chat | Dans l'application (💬) |
| Support email | support@azalscore.com |

### Formation en Entreprise

Pour organiser une session de formation en entreprise :
1. Contactez votre commercial AZALSCORE
2. Definissez les modules a couvrir
3. Planifiez les sessions (sur site ou distanciel)

---

## Mises a Jour

Cette documentation est mise a jour a chaque release majeure d'AZALSCORE.

| Version | Date | Modifications |
|---------|------|---------------|
| 2.0 | Fevrier 2026 | Version initiale complete |

---

## Conventions Utilisees

### Icones et Symboles

| Symbole | Signification |
|---------|---------------|
| ⚠️ | Attention / Important |
| 💡 | Conseil / Astuce |
| ✓ | Validation / Succes |
| → | Navigation / Etape suivante |
| * | Champ obligatoire |

### Formats

- **Gras** : Elements d'interface, boutons
- `Code` : Commandes, codes, references
- *Italique* : Termes techniques

### Navigation

```
Menu > Section > Sous-section > Action
```

Exemple : `CRM > Clients > + Nouveau client`

---

## Contact

Pour toute question sur cette documentation :
- Email : formation@azalscore.com
- Support : support@azalscore.com

---

---

## Structure Complete des Fichiers

### Documentation (Markdown/PDF)

```
docs/formation/
├── README.md                           # Ce fichier - Index general
├── DEMARRAGE_RAPIDE.md                # Guide 15 minutes pour nouveaux utilisateurs
├── GUIDE_UTILISATEUR_AZALSCORE.md     # Guide complet (1600+ lignes)
├── FICHES_PRATIQUES_PAR_PROFIL.md     # Procedures par role metier
├── GUIDE_ADMINISTRATEUR.md            # Administration et securite
├── REFERENCE_RAPIDE.md                # Carte de reference a imprimer
├── EXERCICES_PRATIQUES.md             # 7 modules d'exercices guides
└── images/
    └── README.md                      # Instructions pour les captures
```

### Formation E-Learning (SCORM)

```
docs/formation/elearning/
├── README.md                          # Vue d'ensemble e-learning
├── SCRIPTS_VIDEOS.md                  # Scripts complets pour production video
├── QUIZ_INTERACTIFS.md                # 38+ questions avec reponses
├── scorm/
│   └── imsmanifest.xml               # Manifest SCORM 1.2 (8 modules)
└── videos/
    └── README.md                      # Specifications techniques video
```

### Formation In-App (React)

```
frontend/src/modules/onboarding/
├── index.tsx                          # Module principal + Provider + Exports
├── types.ts                           # Types TypeScript
├── i18n/                              # Internationalisation
│   ├── index.ts                       # Provider i18n + Hook useI18n
│   ├── translations.ts                # Traductions (FR, EN, ES, DE, AR)
│   └── examQuestions.ts               # Questions d'examens traduites
├── training/                          # Systeme de formation modulaire
│   ├── index.ts                       # Exports du systeme
│   ├── types.ts                       # Types pour contenus de formation
│   ├── registry.ts                    # Registre central des modules
│   ├── hooks.ts                       # Hooks React (useTraining, etc.)
│   └── MODULE_TRAINING_TEMPLATE.md    # Guide creation de formation
└── components/
    ├── Tooltips.tsx                   # Systeme de tooltips intelligents
    ├── KnowledgeBase.tsx              # Base de connaissances integree
    ├── Gamification.tsx               # Systeme XP, badges, leaderboard, defis
    ├── InteractiveGames.tsx           # Mini-jeux educatifs (quiz, memory, drag-drop)
    ├── MicroLearning.tsx              # Micro-lecons courtes avec slides animes
    └── TrainingHub.tsx                # Hub central unifiant tous les systemes
```

### Contenu de formation par module (OBLIGATOIRE)

Chaque module AZALSCORE doit inclure son contenu de formation :

```
app/modules/[nom_module]/
└── training/
    ├── index.ts                       # Export + enregistrement
    ├── content.ts                     # Contenu de formation
    └── i18n/
        ├── fr.ts                      # Francais (obligatoire)
        └── en.ts                      # Anglais (obligatoire)
```

**Modules avec formation :**
- `crm/training/` - Gestion clients (CRM)
- `commercial/training/` - Devis et factures
- `accounting/training/` - Comptabilite
- `inventory/training/` - Gestion des stocks
- `hr/training/` - Ressources humaines
- `production/training/` - Production
- `helpdesk/training/` - Support client
- `marceau/training/` - Agent IA Marceau

---

## Deploiement

### Documentation PDF

1. Convertir les fichiers Markdown en PDF :
   ```bash
   npx markdown-pdf docs/formation/GUIDE_UTILISATEUR_AZALSCORE.md
   ```

2. Publier sur le portail documentation

### E-Learning

1. Produire les videos selon les scripts
2. Creer les pages HTML pour chaque lecon
3. Zipper le dossier SCORM
4. Importer dans votre LMS (Moodle, 360Learning, etc.)

### In-App

1. Ajouter le provider dans `App.tsx` :
   ```tsx
   import { OnboardingProvider, HelpWidget } from '@/modules/onboarding';

   function App() {
     return (
       <OnboardingProvider>
         <YourApp />
         <HelpWidget />
       </OnboardingProvider>
     );
   }
   ```

2. Ajouter les attributs `data-tour` aux elements cibles :
   ```tsx
   <SearchBar data-tour="search-bar" />
   <NavMenu data-tour="main-menu" />
   ```

3. Declencher les tours manuellement si besoin :
   ```tsx
   const { startTour } = useOnboarding();
   startTour('welcome');
   ```

---

## Metriques de Formation

| Metrique | Valeur |
|----------|--------|
| Lignes de documentation | 4500+ |
| Modules e-learning | 8 |
| Lecons video | 25+ |
| Questions quiz | 38+ |
| Tours interactifs | 4 |
| Articles d'aide | 6+ |
| Composants React | 25+ |
| Mini-jeux interactifs | 5 |
| Badges/Achievements | 15+ |
| Micro-lecons | 10+ |

---

*Documentation de Formation AZALSCORE*
*Version 2.0 - Fevrier 2026*
*Tous droits reserves*
