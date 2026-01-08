# AZALSCORE - Guide du Testeur Bêta
## BETA_TESTER_PATH.md

**Version**: 1.0-BETA
**Date**: 2026-01-08

---

## Bienvenue dans le Programme Bêta AZALSCORE !

Merci de participer à l'amélioration d'AZALSCORE. Ce guide vous accompagne dans vos tests.

---

## 1. PRÉREQUIS

### 1.1 Matériel

- Navigateur moderne (Chrome, Firefox, Safari, Edge)
- Connexion internet stable
- Application authenticator (Google Authenticator, Authy) pour 2FA

### 1.2 Accès

Vous avez reçu :
- URL de l'application : `https://beta.azalscore.com`
- Identifiant tenant : `votre-tenant-id`
- Email de connexion : `votre@email.com`
- Mot de passe temporaire : À changer lors de la première connexion

---

## 2. PREMIÈRE CONNEXION

### Étape 1 : Accès

1. Ouvrez `https://beta.azalscore.com`
2. Cliquez sur "Connexion"

### Étape 2 : Authentification

1. Entrez votre email et mot de passe temporaire
2. Changez votre mot de passe (minimum 12 caractères)
3. Configurez la 2FA (fortement recommandé)

### Étape 3 : Configuration 2FA

1. Scannez le QR code avec Google Authenticator
2. Entrez le code à 6 chiffres
3. **SAUVEGARDEZ vos codes de secours** (10 codes)

---

## 3. FONCTIONNALITÉS À TESTER

### 3.1 Socle Technique (Actif)

| Fonctionnalite | Actions a Tester |
|----------------|------------------|
| **Connexion** | Login, logout, changement mot de passe |
| **2FA** | Activation, desactivation, codes de secours |
| **Dashboard** | Affichage KPIs, navigation |
| **Profil** | Modification informations |

### 3.2 Module CRM T0 (ACTIVE - 8 janvier 2026)

| Fonctionnalite | Actions a Tester |
|----------------|------------------|
| **Clients** | Creer, modifier, lister, supprimer |
| **Contacts** | Creer, modifier, lister |
| **Export CSV** | Exporter clients et contacts |
| **RBAC** | Verifier les droits selon votre role |

### 3.2 Scénarios de Test Prioritaires

#### Test 1 : Cycle d'Authentification Complet

```
1. Se connecter avec email/password
2. Activer 2FA
3. Se déconnecter
4. Se reconnecter (doit demander le code 2FA)
5. Utiliser un code de secours
6. Régénérer les codes de secours
```

#### Test 2 : Navigation de Base

```
1. Accéder au dashboard
2. Vérifier les KPIs affichés
3. Naviguer dans les menus
4. Vérifier la réactivité (responsive)
```

#### Test 3 : Gestion de Session

```
1. Se connecter
2. Attendre 35 minutes (expiration token)
3. Effectuer une action
4. Vérifier le refresh automatique ou la reconnexion
```

---

## 4. COMMENT SIGNALER UN BUG

### 4.1 Informations Requises

Chaque rapport de bug doit inclure :

```markdown
## Titre du Bug
[Description courte]

## Environnement
- Navigateur : Chrome 120 / Firefox 122 / Safari 17
- OS : Windows 11 / macOS 14 / Linux
- Date/Heure : 2026-01-08 14:30

## Étapes pour Reproduire
1. Aller sur [page]
2. Cliquer sur [bouton]
3. ...

## Comportement Attendu
[Ce qui devrait se passer]

## Comportement Observé
[Ce qui s'est passé]

## Screenshots / Vidéos
[Joindre si possible]

## Sévérité
- [ ] Bloquant (impossible de continuer)
- [ ] Majeur (fonctionnalité cassée)
- [ ] Mineur (gêne légère)
- [ ] Cosmétique (visuel)
```

### 4.2 Où Signaler

- **Email** : beta-bugs@azalscore.com
- **Formulaire** : `https://beta.azalscore.com/feedback`

---

## 5. LIMITATIONS CONNUES

### 5.1 Fonctionnalites Non Disponibles

| Fonctionnalite | Statut |
|----------------|--------|
| Module CRM T0 | **ACTIVE** (8 janvier 2026) |
| Opportunites avancees | Non disponible (T1) |
| Module Finance | Non active |
| Export PDF/Excel | Non disponible |
| Application mobile | PWA uniquement |
| Multi-langue | Francais uniquement |
| Webhooks | Non disponible |

### 5.2 Limitations Techniques

- Performance peut varier
- Sessions expirent après 30 min d'inactivité
- Pas de support temps réel (chat)

---

## 6. BONNES PRATIQUES

### À Faire ✅

- Testez dans différents navigateurs
- Notez chaque anomalie rencontrée
- Testez les cas limites (champs vides, caractères spéciaux...)
- Vérifiez la cohérence des données
- Testez la navigation au clavier

### À Ne Pas Faire ❌

- N'utilisez PAS de données réelles sensibles
- Ne partagez PAS vos accès
- Ne tentez PAS de contourner la sécurité (sauf si explicitement demandé)
- N'effectuez PAS de tests de charge sans coordination

---

## 7. CALENDRIER DES TESTS

### Semaine 1 : Authentification

- Connexion / Déconnexion
- 2FA
- Gestion de session

### Semaine 2 : Navigation

- Dashboard
- Menus
- Responsive

### Semaine 3 : Intégration

- Flux complets
- Cas limites
- Performance subjective

### Semaine 4 : Retours

- Synthèse des bugs
- Suggestions d'amélioration
- Questionnaire satisfaction

---

## 8. FAQ

### Q: J'ai perdu mes codes de secours 2FA

**R**: Contactez beta-support@azalscore.com avec une preuve d'identité pour reset.

### Q: Mon compte est bloqué

**R**: Attendez 15 minutes (blocage temporaire après 5 échecs) ou contactez le support.

### Q: L'application est lente

**R**: Notez l'heure et l'action, et signalez-le. Nous analysons les performances.

### Q: Je trouve une faille de sécurité

**R**: Signalez-la IMMÉDIATEMENT à security@azalscore.com. Ne l'exploitez pas.

---

## 9. REMERCIEMENTS

Votre participation est précieuse pour améliorer AZALSCORE. En retour, les testeurs bêta bénéficieront de :

- 🎁 3 mois gratuits sur la version finale
- 🏆 Badge "Beta Tester" sur leur compte
- 📢 Mention dans les crédits (optionnel)

---

## 10. CONTACTS

| Sujet | Contact |
|-------|---------|
| Support technique | beta-support@azalscore.com |
| Rapport de bugs | beta-bugs@azalscore.com |
| Sécurité | security@azalscore.com |
| Questions générales | beta@azalscore.com |

---

**Merci pour votre contribution !**

L'équipe AZALSCORE
