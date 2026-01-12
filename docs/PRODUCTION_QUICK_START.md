# 🚀 AZALSCORE - Guide de Mise en Production Express

## Objectif : Être opérationnel et pouvoir vendre en 48h

---

## 📋 CHECKLIST RAPIDE

### Étape 1 : Paiements (2h)
- [ ] Créer compte Stripe → https://dashboard.stripe.com/register
- [ ] Créer les produits/prix dans Stripe
- [ ] Configurer le webhook
- [ ] Tester un paiement

### Étape 2 : Hébergement (1h)
- [ ] Choisir : Railway.app (recommandé) ou Render.com
- [ ] Déployer l'API
- [ ] Configurer le domaine

### Étape 3 : Site Web (30min)
- [ ] Déployer la landing page sur Vercel/Netlify
- [ ] Configurer le domaine commercial

### Étape 4 : Emails (30min)
- [ ] Créer compte Resend → https://resend.com
- [ ] Configurer le domaine d'envoi
- [ ] Tester l'envoi

### Étape 5 : Go Live (1h)
- [ ] Vérifier les tests
- [ ] Configurer les secrets production
- [ ] Déployer
- [ ] Tester le parcours complet

---

## 1️⃣ CONFIGURATION STRIPE (DÉTAILLÉE)

### A. Créer les Produits

Dans le Dashboard Stripe → Produits → Créer un produit :

**Produit 1 : Starter**
- Nom : AZALSCORE Starter
- Prix mensuel : 49€
- Prix annuel : 490€ (créer un second prix)
- Metadata : `plan=starter`

**Produit 2 : Professional**
- Nom : AZALSCORE Professional
- Prix mensuel : 149€
- Prix annuel : 1490€
- Metadata : `plan=professional`

**Produit 3 : Enterprise**
- Nom : AZALSCORE Enterprise
- Prix mensuel : 499€
- Prix annuel : 4990€
- Metadata : `plan=enterprise`

### B. Créer le Webhook

Dashboard Stripe → Developers → Webhooks → Add endpoint

URL : `https://api.azalscore.com/webhooks/stripe`

Événements à écouter :
- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`

**Copiez le Webhook Secret (whsec_...)** → à mettre dans .env

### C. Variables d'environnement

```bash
STRIPE_API_KEY_LIVE=sk_live_...
STRIPE_PUBLISHABLE_KEY_LIVE=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_LIVE_MODE=true
```

---

## 2️⃣ DÉPLOIEMENT RAILWAY (RECOMMANDÉ)

### Pourquoi Railway ?
- PostgreSQL inclus gratuitement
- Redis inclus
- Déploiement automatique depuis GitHub
- SSL automatique
- 5$/mois pour commencer

### Étapes

1. **Créer un compte** : https://railway.app

2. **Nouveau projet** : New Project → Deploy from GitHub

3. **Ajouter PostgreSQL** :
   - Add → Database → PostgreSQL
   - Railway configure automatiquement DATABASE_URL

4. **Ajouter Redis** :
   - Add → Database → Redis
   - Railway configure automatiquement REDIS_URL

5. **Variables d'environnement** :
   Dans Settings → Variables, ajouter :
   ```
   ENVIRONMENT=production
   DEBUG=false
   SECRET_KEY=<générer avec le script>
   BOOTSTRAP_SECRET=<générer avec le script>
   ENCRYPTION_KEY=<générer avec le script>
   CORS_ORIGINS=https://app.azalscore.com,https://azalscore.com
   STRIPE_API_KEY_LIVE=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   RESEND_API_KEY=re_...
   ```

6. **Domaine personnalisé** :
   Settings → Domains → Add Custom Domain
   - api.azalscore.com

7. **Déployer** :
   Push sur main = déploiement automatique

---

## 3️⃣ SITE WEB COMMERCIAL

### Option A : Vercel (Gratuit)

1. Créer compte : https://vercel.com
2. Import Git → Sélectionner le repo
3. Root Directory : `website`
4. Deploy
5. Ajouter domaine : azalscore.com

### Option B : Netlify (Gratuit)

1. Créer compte : https://netlify.com
2. Add new site → Import from Git
3. Publish directory : `website`
4. Deploy
5. Domain settings → azalscore.com

---

## 4️⃣ CONFIGURATION EMAILS

### Resend (Recommandé)

1. **Créer compte** : https://resend.com

2. **Ajouter domaine** :
   Settings → Domains → Add Domain
   Ajouter les enregistrements DNS fournis

3. **API Key** :
   API Keys → Create API Key
   Copier dans RESEND_API_KEY

4. **Tester** :
   ```bash
   curl -X POST 'https://api.resend.com/emails' \
     -H 'Authorization: Bearer re_...' \
     -H 'Content-Type: application/json' \
     -d '{
       "from": "test@azalscore.com",
       "to": "votre@email.com",
       "subject": "Test AZALSCORE",
       "html": "<p>Ça marche !</p>"
     }'
   ```

---

## 5️⃣ GÉNÉRATION DES SECRETS

Exécutez ce script Python :

```python
import secrets
print("SECRET_KEY=" + secrets.token_urlsafe(64))
print("BOOTSTRAP_SECRET=" + secrets.token_urlsafe(64))

try:
    from cryptography.fernet import Fernet
    print("ENCRYPTION_KEY=" + Fernet.generate_key().decode())
except ImportError:
    print("# pip install cryptography pour ENCRYPTION_KEY")
```

---

## 6️⃣ TEST DU PARCOURS CLIENT

### Scénario complet à tester :

1. **Landing Page**
   - [ ] Page s'affiche correctement
   - [ ] Liens fonctionnent
   - [ ] Bouton "Essai gratuit" redirige

2. **Inscription**
   - [ ] Formulaire d'inscription fonctionne
   - [ ] Email de bienvenue reçu
   - [ ] Redirection vers onboarding

3. **Onboarding**
   - [ ] Configuration entreprise
   - [ ] Premier utilisateur créé
   - [ ] Accès au dashboard

4. **Paiement**
   - [ ] Bouton upgrade fonctionne
   - [ ] Redirection Stripe checkout
   - [ ] Paiement test accepté (carte 4242 4242 4242 4242)
   - [ ] Webhook reçu
   - [ ] Abonnement activé

5. **Utilisation**
   - [ ] Modules accessibles selon le plan
   - [ ] Création de données fonctionne
   - [ ] Export/rapports fonctionnent

---

## 7️⃣ PAGES LÉGALES OBLIGATOIRES

### CGV (Conditions Générales de Vente)
Créer `/website/legal/cgv.html` avec :
- Identité du vendeur
- Description des services
- Prix et paiement
- Droit de rétractation
- Résiliation
- Responsabilité
- Données personnelles
- Droit applicable

### Mentions Légales
Créer `/website/legal/mentions.html` avec :
- Raison sociale, SIRET
- Adresse du siège
- Directeur de publication
- Hébergeur
- CNIL (si applicable)

### Politique de Confidentialité
Créer `/website/legal/privacy.html` avec :
- Données collectées
- Finalités
- Durée de conservation
- Droits des utilisateurs
- Contact DPO

**Conseil** : Utilisez un générateur comme Iubenda ou faites valider par un juriste.

---

## 8️⃣ MONITORING

### Grafana Cloud (Gratuit jusqu'à 10k séries)

1. Créer compte : https://grafana.com/products/cloud/
2. Intégrer avec Prometheus
3. Importer les dashboards depuis `/monitoring/grafana/dashboards/`

### Sentry (Erreurs)

1. Créer compte : https://sentry.io
2. Créer projet Python/FastAPI
3. Ajouter `SENTRY_DSN` dans les variables

### UptimeRobot (Uptime)

1. Créer compte : https://uptimerobot.com
2. Ajouter moniteur HTTP(s)
3. URL : `https://api.azalscore.com/health`
4. Intervalle : 5 minutes

---

## 📞 SUPPORT CLIENT

### Outils recommandés :

1. **Crisp** (gratuit jusqu'à 2 opérateurs)
   - Chat en direct sur le site
   - Helpdesk email
   - Base de connaissances

2. **Calendly** (gratuit)
   - Prise de RDV démo
   - Intégrer sur la page pricing

---

## ⚠️ ERREURS FRÉQUENTES À ÉVITER

1. **Oublier le webhook Stripe** → Pas d'activation automatique
2. **Secrets en clair dans Git** → Fuite de données
3. **Pas de backup DB** → Activer les backups Railway
4. **Pas de monitoring** → Problèmes non détectés
5. **CGV manquantes** → Illégal en France

---

## 🎯 RÉCAPITULATIF COÛTS MENSUELS

| Service | Coût | Gratuit jusqu'à |
|---------|------|-----------------|
| Railway | ~5€ | 5$/mois inclus |
| Vercel | 0€ | Illimité |
| Resend | 0€ | 3000 emails/mois |
| Stripe | 1.4% + 0.25€ | Par transaction |
| Domaine | ~15€/an | - |
| **TOTAL** | **~10-20€/mois** | + commissions Stripe |

---

## 🚀 COMMANDES RAPIDES

```bash
# Générer les secrets
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"

# Tester l'API locale
curl http://localhost:8000/health

# Lancer les tests
pytest tests/ -v

# Build Docker
docker build -f Dockerfile.prod -t azalscore:latest .

# Déployer Railway
railway up

# Logs Railway
railway logs
```

---

## ✅ PRÊT À VENDRE !

Une fois toutes les cases cochées, vous pouvez :

1. **Annoncer le lancement** sur LinkedIn/Twitter
2. **Contacter vos premiers prospects**
3. **Offrir des réductions early-bird**
4. **Collecter les feedbacks**
5. **Itérer rapidement**

Bon courage et bonnes ventes ! 🎉
