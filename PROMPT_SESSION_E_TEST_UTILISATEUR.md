# SESSION E — TEST UTILISATEUR RÉEL (Port 80/443)

## ⚠️ RÈGLES ABSOLUES — VÉRITÉ UNIQUEMENT

**Cette mission exige une HONNÊTETÉ TOTALE sur l'expérience utilisateur RÉELLE.**

- **JAMAIS de mensonge** — Je préfère un logiciel qui ne marche pas à un rapport qui dit que tout va bien
- **JAMAIS de "ça marche chez moi"** — Teste en conditions RÉELLES (port 80, HTTPS, navigateur)
- **JAMAIS de supposition** — Clique VRAIMENT, remplis VRAIMENT, soumets VRAIMENT
- **JAMAIS de complaisance** — Si l'UX est mauvaise, dis-le
- **JAMAIS de raccourci** — Teste CHAQUE fonctionnalité comme un vrai utilisateur

### Notation HONNÊTE :

```
✅ PARFAIT — Fonctionne sans aucun problème, UX excellente
✅ BON — Fonctionne bien, petites améliorations possibles
⚠️ ACCEPTABLE — Fonctionne mais UX à améliorer
⚠️ MÉDIOCRE — Fonctionne difficilement, frustrant pour l'utilisateur
❌ ÉCHOUE — Ne fonctionne pas ou inutilisable
🔴 BLOQUANT — Empêche l'utilisateur de continuer
```

---

## 🎯 MISSION

**Tester le logiciel AZALSCORE exactement comme un VRAI utilisateur :**

1. **Accès via navigateur** — URL publique, port 80/443
2. **Parcours utilisateur complets** — De l'inscription à l'utilisation quotidienne
3. **Tous les modules** — Chaque fonctionnalité testée manuellement
4. **Autocomplétion** — Vérifier que CHAQUE champ de recherche/sélection fonctionne
5. **Performance** — Temps de chargement, réactivité
6. **Mobile** — Test sur mobile/tablette (responsive)
7. **Erreurs** — Tester les cas d'erreur (mauvaises saisies, etc.)

---

## 📂 CONTEXTE

- **URL Production:** `https://azalscore.com` (ou URL de staging)
- **URL Locale:** `http://localhost:80` ou `http://localhost:3000`
- **Navigateurs à tester:** Chrome, Firefox, Safari, Edge
- **Devices:** Desktop, Tablette, Mobile

---

## 🔍 PHASE 1 — ACCÈS ET PREMIÈRE IMPRESSION

### 1.1 Test d'accès (Port 80/443)

```markdown
## Test Accès Site

**URL testée:** https://azalscore.com
**Date/Heure:** YYYY-MM-DD HH:MM
**Navigateur:** Chrome 121

### Résultats

| Test | Attendu | Résultat | Statut |
|------|---------|----------|--------|
| Accès HTTP (port 80) | Redirection HTTPS | [Résultat] | ✅/❌ |
| Accès HTTPS (port 443) | Page chargée | [Résultat] | ✅/❌ |
| Certificat SSL | Valide, pas d'erreur | [Résultat] | ✅/❌ |
| Temps chargement initial | < 3 secondes | [X.XX sec] | ✅/❌ |
| Page d'accueil affichée | Contenu visible | [Résultat] | ✅/❌ |

### Erreurs Console

```
[Copier TOUTES les erreurs de la console navigateur]
```

### Capture d'écran

[Prendre une capture si erreur]
```

### 1.2 Première impression utilisateur

```markdown
## Première Impression (Point de vue utilisateur naïf)

### Questions à répondre HONNÊTEMENT :

1. **Est-ce que je comprends immédiatement ce que fait ce logiciel ?**
   - [ ] Oui, en moins de 5 secondes
   - [ ] Oui, après avoir lu
   - [ ] Non, c'est confus
   Commentaire: [Détailler]

2. **Est-ce que je sais comment commencer ?**
   - [ ] Oui, CTA évident
   - [ ] Oui, après recherche
   - [ ] Non, je suis perdu
   Commentaire: [Détailler]

3. **Est-ce que le design inspire confiance ?**
   - [ ] Oui, professionnel
   - [ ] Moyen, amateur
   - [ ] Non, méfiance
   Commentaire: [Détailler]

4. **Est-ce que ça charge vite ?**
   - [ ] Instantané (< 1s)
   - [ ] Acceptable (1-3s)
   - [ ] Lent (> 3s)
   - [ ] Très lent (> 5s)
   Mesure réelle: [X.XX secondes]

### Score Première Impression: X/10
```

---

## 🔍 PHASE 2 — PARCOURS INSCRIPTION / CONNEXION

### 2.1 Inscription nouvel utilisateur

```markdown
## Test Inscription

**Scénario:** Nouvel utilisateur qui découvre AZALSCORE

### Étapes testées

| # | Action | Attendu | Résultat | Temps | Statut |
|---|--------|---------|----------|-------|--------|
| 1 | Clic "S'inscrire" / "Essai gratuit" | Formulaire affiché | [Résultat] | [Xs] | ✅/❌ |
| 2 | Remplir email | Validation temps réel | [Résultat] | - | ✅/❌ |
| 3 | Remplir mot de passe | Indicateur force | [Résultat] | - | ✅/❌ |
| 4 | Remplir nom entreprise | Champ accepté | [Résultat] | - | ✅/❌ |
| 5 | Remplir SIRET | Autocomplétion INSEE? | [Résultat] | - | ✅/❌ |
| 6 | Soumettre formulaire | Compte créé | [Résultat] | [Xs] | ✅/❌ |
| 7 | Email confirmation reçu | Email reçu < 1min | [Résultat] | [Xs] | ✅/❌ |
| 8 | Clic lien confirmation | Compte activé | [Résultat] | - | ✅/❌ |
| 9 | Redirection dashboard | Dashboard affiché | [Résultat] | [Xs] | ✅/❌ |

### Problèmes rencontrés

```
[Décrire TOUT problème, même mineur]
```

### Autocomplétion testée

| Champ | Autocomplétion | Fonctionne | Résultats pertinents |
|-------|----------------|------------|----------------------|
| Pays | Oui/Non | ✅/❌ | ✅/❌ |
| Ville | Oui/Non | ✅/❌ | ✅/❌ |
| SIRET | Oui/Non (API INSEE) | ✅/❌ | ✅/❌ |
| Secteur activité | Oui/Non | ✅/❌ | ✅/❌ |

### Score Inscription: X/10
```

### 2.2 Connexion utilisateur existant

```markdown
## Test Connexion

### Scénarios testés

| Scénario | Action | Attendu | Résultat | Statut |
|----------|--------|---------|----------|--------|
| Connexion valide | Email + MDP corrects | Accès dashboard | [Résultat] | ✅/❌ |
| Email invalide | Format incorrect | Erreur claire | [Résultat] | ✅/❌ |
| MDP incorrect | Mauvais mot de passe | Erreur claire (pas "email ou mdp") | [Résultat] | ✅/❌ |
| Compte inexistant | Email non inscrit | Erreur appropriée | [Résultat] | ✅/❌ |
| Mot de passe oublié | Clic lien | Email reçu | [Résultat] | ✅/❌ |
| Session expirée | Après timeout | Redirection login | [Résultat] | ✅/❌ |
| "Se souvenir de moi" | Checkbox cochée | Session persistante | [Résultat] | ✅/❌ |

### Temps de connexion

- Soumission formulaire → Dashboard: [X.XX secondes]
- Acceptable si < 2 secondes

### Score Connexion: X/10
```

---

## 🔍 PHASE 3 — TEST DE CHAQUE MODULE (Utilisateur réel)

### Template pour CHAQUE module :

```markdown
## Module: [NOM DU MODULE]

**Chemin:** Dashboard → [Navigation]
**Rôle testé:** [Admin/User/Comptable/etc.]

### 3.X.1 Accès au module

| Test | Résultat | Temps | Statut |
|------|----------|-------|--------|
| Menu visible | [Oui/Non] | - | ✅/❌ |
| Clic menu | [Page chargée] | [Xs] | ✅/❌ |
| Breadcrumb correct | [Oui/Non] | - | ✅/❌ |
| Titre page correct | [Oui/Non] | - | ✅/❌ |

### 3.X.2 Liste des éléments

| Test | Résultat | Statut |
|------|----------|--------|
| Liste affichée | [X éléments] | ✅/❌ |
| Pagination fonctionne | [Oui/Non] | ✅/❌ |
| Tri par colonnes | [Oui/Non] | ✅/❌ |
| Recherche/Filtre | [Oui/Non] | ✅/❌ |
| Temps chargement | [X.XX sec] | ✅/❌ |

### 3.X.3 Création nouvel élément

| Étape | Action | Autocomplétion | Résultat | Statut |
|-------|--------|----------------|----------|--------|
| 1 | Clic "Nouveau" / "+" | - | [Résultat] | ✅/❌ |
| 2 | Formulaire affiché | - | [Résultat] | ✅/❌ |
| 3 | Champ [nom] | [Oui/Non] | [Résultat] | ✅/❌ |
| 4 | Champ [client] | [Oui/Non] | [Résultat] | ✅/❌ |
| 5 | Champ [produit] | [Oui/Non] | [Résultat] | ✅/❌ |
| 6 | Champ [montant] | - | [Résultat] | ✅/❌ |
| 7 | Soumission | - | [Résultat] | ✅/❌ |
| 8 | Message succès | - | [Résultat] | ✅/❌ |
| 9 | Élément dans liste | - | [Résultat] | ✅/❌ |

### 3.X.4 Modification élément

| Test | Résultat | Statut |
|------|----------|--------|
| Clic sur élément | [Détail affiché] | ✅/❌ |
| Bouton "Modifier" visible | [Oui/Non] | ✅/❌ |
| Formulaire pré-rempli | [Oui/Non] | ✅/❌ |
| Modification champ | [Acceptée] | ✅/❌ |
| Sauvegarde | [Succès] | ✅/❌ |
| Données mises à jour | [Oui/Non] | ✅/❌ |

### 3.X.5 Suppression élément

| Test | Résultat | Statut |
|------|----------|--------|
| Bouton "Supprimer" visible | [Oui/Non] | ✅/❌ |
| Confirmation demandée | [Oui/Non] | ✅/❌ |
| Suppression effective | [Oui/Non] | ✅/❌ |
| Élément disparu de liste | [Oui/Non] | ✅/❌ |
| Message confirmation | [Oui/Non] | ✅/❌ |

### 3.X.6 Autocomplétion détaillée

| Champ | Type | Endpoint appelé | Temps réponse | Résultats | Statut |
|-------|------|-----------------|---------------|-----------|--------|
| Client | Combobox | /contacts/search | [Xms] | [Pertinents?] | ✅/❌ |
| Produit | Combobox | /products/search | [Xms] | [Pertinents?] | ✅/❌ |
| Compte | Select | /accounts/search | [Xms] | [Pertinents?] | ✅/❌ |
| Adresse | Input | API Adresse? | [Xms] | [Pertinents?] | ✅/❌ |

### 3.X.7 Erreurs et edge cases

| Cas | Action | Attendu | Résultat | Statut |
|-----|--------|---------|----------|--------|
| Champ obligatoire vide | Soumettre | Erreur claire | [Résultat] | ✅/❌ |
| Format invalide | Email mal formé | Erreur claire | [Résultat] | ✅/❌ |
| Doublon | Créer existant | Erreur claire | [Résultat] | ✅/❌ |
| Connexion perdue | Débrancher réseau | Message offline | [Résultat] | ✅/❌ |
| Session expirée | Attendre timeout | Redirection login | [Résultat] | ✅/❌ |

### Score Module [NOM]: X/10

**Points forts:**
- ...

**Points faibles:**
- ...

**Bugs trouvés:**
1. ...
2. ...
```

---

## 🔍 PHASE 4 — MODULES CRITIQUES À TESTER EN PRIORITÉ

### 4.1 Module FACTURATION (Critique business)

```markdown
## Module Facturation — Test Complet

### Scénario: Créer une facture de A à Z

| # | Étape | Action détaillée | Autocomplétion | Résultat | Statut |
|---|-------|------------------|----------------|----------|--------|
| 1 | Accès | Dashboard → Facturation → Factures | - | | |
| 2 | Nouvelle facture | Clic bouton "Nouvelle facture" | - | | |
| 3 | Sélection client | Taper nom client | ✅ Obligatoire | | |
| 4 | Autocomplétion client | Résultats en < 300ms | ✅ Obligatoire | | |
| 5 | Sélection client | Clic sur suggestion | - | | |
| 6 | Infos client auto-remplies | Adresse, SIRET, TVA | - | | |
| 7 | Ajouter ligne | Clic "Ajouter article" | - | | |
| 8 | Recherche produit | Taper nom/référence | ✅ Obligatoire | | |
| 9 | Autocomplétion produit | Résultats pertinents | ✅ Obligatoire | | |
| 10 | Sélection produit | Clic sur suggestion | - | | |
| 11 | Prix auto-rempli | Prix du produit affiché | - | | |
| 12 | Modifier quantité | Changer quantité | - | | |
| 13 | Total ligne calculé | Prix × Quantité | - | | |
| 14 | Ajouter 2ème ligne | Répéter 7-13 | - | | |
| 15 | Total HT calculé | Somme des lignes | - | | |
| 16 | TVA calculée | Selon taux applicable | - | | |
| 17 | Total TTC calculé | HT + TVA | - | | |
| 18 | Sélection date | Datepicker fonctionnel | - | | |
| 19 | Conditions paiement | Select avec options | - | | |
| 20 | Notes/Commentaires | Champ texte libre | - | | |
| 21 | Prévisualisation | Aperçu PDF | - | | |
| 22 | Sauvegarde brouillon | Bouton "Enregistrer" | - | | |
| 23 | Validation facture | Bouton "Valider" | - | | |
| 24 | Numéro attribué | Numéro automatique | - | | |
| 25 | PDF généré | Téléchargement possible | - | | |
| 26 | Envoi par email | Bouton "Envoyer" | - | | |
| 27 | Email reçu (test) | Vérifier réception | - | | |
| 28 | Statut mis à jour | "Envoyée" | - | | |

### Calculs à vérifier

| Calcul | Formule | Valeur attendue | Valeur affichée | Statut |
|--------|---------|-----------------|-----------------|--------|
| Ligne 1 | 100 × 2 | 200,00 € | [Valeur] | ✅/❌ |
| Ligne 2 | 50 × 3 | 150,00 € | [Valeur] | ✅/❌ |
| Total HT | 200 + 150 | 350,00 € | [Valeur] | ✅/❌ |
| TVA 20% | 350 × 0.20 | 70,00 € | [Valeur] | ✅/❌ |
| Total TTC | 350 + 70 | 420,00 € | [Valeur] | ✅/❌ |

### Score Facturation: X/10
```

### 4.2 Module COMPTABILITÉ

```markdown
## Module Comptabilité — Test Complet

### Scénario: Saisie écriture comptable

| # | Étape | Autocomplétion | Résultat | Statut |
|---|-------|----------------|----------|--------|
| 1 | Accès journal | - | | |
| 2 | Nouvelle écriture | - | | |
| 3 | Date écriture | Datepicker | | |
| 4 | Sélection journal | Select | | |
| 5 | Compte débit | ✅ Recherche PCG | | |
| 6 | Compte crédit | ✅ Recherche PCG | | |
| 7 | Libellé | Suggestions? | | |
| 8 | Montant | Calcul équilibre | | |
| 9 | Pièce justificative | Upload fichier | | |
| 10 | Validation | Équilibre vérifié | | |

### Autocomplétion comptes comptables

| Action | Saisie | Attendu | Résultat | Temps |
|--------|--------|---------|----------|-------|
| Taper "411" | 411 | Comptes clients 411xxx | [Résultat] | [Xms] |
| Taper "client" | client | Comptes avec "client" | [Résultat] | [Xms] |
| Taper "DUPON" | DUPON | Compte aux. Dupont | [Résultat] | [Xms] |

### Score Comptabilité: X/10
```

### 4.3 Module CRM / CONTACTS

```markdown
## Module CRM — Test Complet

### Scénario: Création et gestion contact

[Détailler comme ci-dessus]

### Autocomplétion adresse

| Champ | API utilisée | Fonctionne | Temps |
|-------|--------------|------------|-------|
| Adresse | API Adresse gouv.fr | ✅/❌ | [Xms] |
| Code postal | Auto depuis adresse | ✅/❌ | - |
| Ville | Auto depuis CP | ✅/❌ | - |
| Pays | Liste ISO | ✅/❌ | - |

### Score CRM: X/10
```

### 4.4 Module INTERVENTIONS

```markdown
## Module Interventions — Test Complet

### Scénario: Planifier et réaliser une intervention

[Détailler]

### Score Interventions: X/10
```

### 4.5 Module STOCK / INVENTAIRE

```markdown
## Module Stock — Test Complet

### Scénario: Gestion des articles et mouvements

[Détailler]

### Score Stock: X/10
```

---

## 🔍 PHASE 5 — TEST AUTOCOMPLÉTION GLOBAL

### 5.1 Inventaire TOUS les champs avec autocomplétion

```markdown
## Audit Autocomplétion Complet

### Par module

| Module | Champ | Type | API | Temps | Pertinent | Statut |
|--------|-------|------|-----|-------|-----------|--------|
| **Facturation** | | | | | | |
| | Client | Combobox | /contacts/search | [Xms] | ✅/❌ | ✅/❌ |
| | Produit | Combobox | /products/search | [Xms] | ✅/❌ | ✅/❌ |
| | Adresse livraison | Input | API Adresse | [Xms] | ✅/❌ | ✅/❌ |
| **Comptabilité** | | | | | | |
| | Compte | Combobox | /accounts/search | [Xms] | ✅/❌ | ✅/❌ |
| | Compte auxiliaire | Combobox | /accounts/aux | [Xms] | ✅/❌ | ✅/❌ |
| | Journal | Select | /journals | [Xms] | ✅/❌ | ✅/❌ |
| **CRM** | | | | | | |
| | Contact | Combobox | /contacts/search | [Xms] | ✅/❌ | ✅/❌ |
| | Entreprise | Combobox | /companies/search | [Xms] | ✅/❌ | ✅/❌ |
| | Adresse | Input | API Adresse | [Xms] | ✅/❌ | ✅/❌ |
| | SIRET | Input | API INSEE | [Xms] | ✅/❌ | ✅/❌ |
| **Interventions** | | | | | | |
| | Client | Combobox | /contacts/search | [Xms] | ✅/❌ | ✅/❌ |
| | Technicien | Combobox | /employees/search | [Xms] | ✅/❌ | ✅/❌ |
| | Équipement | Combobox | /equipment/search | [Xms] | ✅/❌ | ✅/❌ |
| | Adresse | Input | API Adresse | [Xms] | ✅/❌ | ✅/❌ |
| **Stock** | | | | | | |
| | Article | Combobox | /products/search | [Xms] | ✅/❌ | ✅/❌ |
| | Fournisseur | Combobox | /suppliers/search | [Xms] | ✅/❌ | ✅/❌ |
| | Emplacement | Select | /locations | [Xms] | ✅/❌ | ✅/❌ |

### Critères de validation

- ✅ **Temps réponse** : < 300ms
- ✅ **Minimum caractères** : 2-3 caractères avant recherche
- ✅ **Résultats pertinents** : Les premiers résultats correspondent à la recherche
- ✅ **Navigation clavier** : Flèches + Entrée fonctionnent
- ✅ **Sélection souris** : Clic sélectionne
- ✅ **Fermeture** : Échap ou clic extérieur ferme
- ✅ **Chargement** : Indicateur pendant la recherche

### Score Autocomplétion Global: X/10
```

### 5.2 APIs externes à vérifier

```markdown
## APIs Externes pour Autocomplétion

| API | Usage | Configurée | Fonctionne | Clé API |
|-----|-------|------------|------------|---------|
| API Adresse (gouv.fr) | Adresses France | ✅/❌ | ✅/❌ | Gratuite |
| API INSEE/SIRENE | SIRET/Entreprises | ✅/❌ | ✅/❌ | [Statut] |
| API TVA VIES | N° TVA UE | ✅/❌ | ✅/❌ | Gratuite |
| Google Places | Adresses monde | ✅/❌ | ✅/❌ | [Statut] |

### À implémenter si manquant

1. **API Adresse France** (gratuite)
   ```
   https://api-adresse.data.gouv.fr/search/?q={query}
   ```

2. **API SIRENE** (token requis)
   ```
   https://api.insee.fr/entreprises/sirene/V3/siret/{siret}
   ```
```

---

## 🔍 PHASE 6 — TEST PERFORMANCE UTILISATEUR

### 6.1 Temps de chargement

```markdown
## Mesures Performance

### Pages principales

| Page | Temps chargement | LCP | FID | CLS | Statut |
|------|------------------|-----|-----|-----|--------|
| Accueil | [X.XX s] | [X.X s] | [X ms] | [0.XX] | ✅/❌ |
| Login | [X.XX s] | [X.X s] | [X ms] | [0.XX] | ✅/❌ |
| Dashboard | [X.XX s] | [X.X s] | [X ms] | [0.XX] | ✅/❌ |
| Liste factures | [X.XX s] | [X.X s] | [X ms] | [0.XX] | ✅/❌ |
| Création facture | [X.XX s] | [X.X s] | [X ms] | [0.XX] | ✅/❌ |
| Liste clients | [X.XX s] | [X.X s] | [X ms] | [0.XX] | ✅/❌ |

### Critères Core Web Vitals

- ✅ **LCP** (Largest Contentful Paint): < 2.5s
- ✅ **FID** (First Input Delay): < 100ms
- ✅ **CLS** (Cumulative Layout Shift): < 0.1

### Outils utilisés

- Chrome DevTools → Performance
- Lighthouse
- WebPageTest
```

### 6.2 Réactivité interface

```markdown
## Réactivité UI

| Action | Temps réponse | Feedback visuel | Statut |
|--------|---------------|-----------------|--------|
| Clic bouton | < 100ms | Effet visuel | ✅/❌ |
| Soumission form | < 200ms | Loading spinner | ✅/❌ |
| Navigation menu | < 100ms | Highlight actif | ✅/❌ |
| Ouverture modal | < 150ms | Animation fluide | ✅/❌ |
| Fermeture modal | < 150ms | Animation fluide | ✅/❌ |
| Scroll liste | 60 fps | Pas de saccade | ✅/❌ |
| Recherche auto | < 300ms | Résultats affichés | ✅/❌ |
```

---

## 🔍 PHASE 7 — TEST MOBILE / RESPONSIVE

### 7.1 Test sur différentes tailles

```markdown
## Test Responsive

### Devices testés

| Device | Résolution | Orientation | Résultat | Statut |
|--------|------------|-------------|----------|--------|
| iPhone 12 | 390×844 | Portrait | [Détail] | ✅/❌ |
| iPhone 12 | 844×390 | Paysage | [Détail] | ✅/❌ |
| iPad | 768×1024 | Portrait | [Détail] | ✅/❌ |
| iPad | 1024×768 | Paysage | [Détail] | ✅/❌ |
| Android | 360×800 | Portrait | [Détail] | ✅/❌ |
| Desktop | 1920×1080 | - | [Détail] | ✅/❌ |
| Desktop | 1366×768 | - | [Détail] | ✅/❌ |

### Problèmes responsive trouvés

| Page | Problème | Device | Capture |
|------|----------|--------|---------|
| [Page] | [Description] | [Device] | [Screenshot] |

### Score Mobile: X/10
```

### 7.2 Navigation tactile

```markdown
## Navigation Tactile

| Élément | Taille tactile | Espacement | Statut |
|---------|----------------|------------|--------|
| Boutons | ≥ 44×44px | ≥ 8px | ✅/❌ |
| Liens | ≥ 44×44px | ≥ 8px | ✅/❌ |
| Inputs | ≥ 44px hauteur | - | ✅/❌ |
| Menu items | ≥ 44px | ≥ 8px | ✅/❌ |
| Checkboxes | ≥ 44×44px zone | - | ✅/❌ |
```

---

## 🔍 PHASE 8 — TEST ACCESSIBILITÉ

```markdown
## Test Accessibilité (WCAG 2.1 AA)

### Navigation clavier

| Test | Résultat | Statut |
|------|----------|--------|
| Tab navigue tous les éléments | [Oui/Non] | ✅/❌ |
| Ordre de tabulation logique | [Oui/Non] | ✅/❌ |
| Focus visible | [Oui/Non] | ✅/❌ |
| Échap ferme les modals | [Oui/Non] | ✅/❌ |
| Entrée valide les formulaires | [Oui/Non] | ✅/❌ |

### Contraste couleurs

| Élément | Ratio | Minimum | Statut |
|---------|-------|---------|--------|
| Texte principal | [X:1] | 4.5:1 | ✅/❌ |
| Texte secondaire | [X:1] | 4.5:1 | ✅/❌ |
| Boutons | [X:1] | 3:1 | ✅/❌ |
| Liens | [X:1] | 4.5:1 | ✅/❌ |
| Erreurs | [X:1] | 4.5:1 | ✅/❌ |

### Labels et ARIA

| Test | Résultat | Statut |
|------|----------|--------|
| Tous les inputs ont un label | [Oui/Non] | ✅/❌ |
| Images ont un alt | [Oui/Non] | ✅/❌ |
| Landmarks ARIA présents | [Oui/Non] | ✅/❌ |
| Erreurs annoncées (aria-live) | [Oui/Non] | ✅/❌ |

### Score Accessibilité: X/10
```

---

## 📊 PHASE 9 — RAPPORT FINAL UTILISATEUR

```markdown
# RAPPORT TEST UTILISATEUR RÉEL

**Date:** YYYY-MM-DD
**Testeur:** Claude Code Session E
**URL testée:** https://azalscore.com
**Durée test:** X heures

---

## SCORE GLOBAL UTILISATEUR: XX/100

> ⚠️ Ce score reflète l'expérience utilisateur RÉELLE.
> Aucun trucage, aucune complaisance.

---

## RÉSUMÉ PAR CATÉGORIE

| Catégorie | Score | Poids | Pondéré |
|-----------|-------|-------|---------|
| Accès & Performance | X/10 | 15% | X.X |
| Inscription/Connexion | X/10 | 10% | X.X |
| Module Facturation | X/10 | 15% | X.X |
| Module Comptabilité | X/10 | 15% | X.X |
| Module CRM | X/10 | 10% | X.X |
| Module Interventions | X/10 | 10% | X.X |
| Autocomplétion globale | X/10 | 10% | X.X |
| Mobile/Responsive | X/10 | 10% | X.X |
| Accessibilité | X/10 | 5% | X.X |
| **TOTAL** | - | 100% | **XX/100** |

---

## 🔴 BUGS BLOQUANTS (Priorité immédiate)

| # | Module | Bug | Impact | Étapes reproduction |
|---|--------|-----|--------|---------------------|
| 1 | [Module] | [Description] | [Impact utilisateur] | [Étapes] |

---

## 🟠 BUGS MAJEURS (Cette semaine)

| # | Module | Bug | Impact | Étapes reproduction |
|---|--------|-----|--------|---------------------|
| 1 | [Module] | [Description] | [Impact utilisateur] | [Étapes] |

---

## 🟡 AMÉLIORATIONS UX (Ce mois)

| # | Module | Suggestion | Bénéfice |
|---|--------|------------|----------|
| 1 | [Module] | [Description] | [Bénéfice utilisateur] |

---

## ✅ POINTS POSITIFS

1. ...
2. ...
3. ...

---

## VERDICT HONNÊTE

> [Écrire un verdict SINCÈRE de l'expérience utilisateur]
>
> Est-ce que je recommanderais ce logiciel ?
> Est-ce que je l'utiliserais moi-même ?
> Qu'est-ce qui manque pour être excellent ?
```

---

## 🚀 COMMENCE PAR

1. **Vérifier que le site est accessible** sur l'URL de production/staging
2. **Ouvrir la console navigateur** (F12) pour capturer les erreurs
3. **Commencer par l'inscription** comme un nouvel utilisateur
4. **Tester CHAQUE module** méthodiquement
5. **Documenter TOUT** — captures d'écran, erreurs, temps

---

## ⚠️ RAPPELS CRITIQUES

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   👤 Tu es un UTILISATEUR, pas un développeur                    ║
║   👤 Si c'est confus pour toi, c'est confus pour les clients    ║
║   👤 Un clic de trop = UX à améliorer                            ║
║   👤 Une erreur non claire = bug                                 ║
║                                                                  ║
║   🚫 JAMAIS de "l'utilisateur comprendra"                        ║
║   🚫 JAMAIS de "c'est un détail"                                 ║
║   🚫 JAMAIS de score gonflé                                      ║
║                                                                  ║
║   ✅ TOUJOURS tester comme si c'était la première fois          ║
║   ✅ TOUJOURS noter le temps que ça prend                        ║
║   ✅ TOUJOURS capturer les erreurs                               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

**GO ! Sois un UTILISATEUR EXIGEANT. Sois HONNÊTE. Sois IMPITOYABLE.**
