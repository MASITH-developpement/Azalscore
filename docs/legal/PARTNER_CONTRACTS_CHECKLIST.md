# AZALS - Checklist Contrats Partenaires (#27)

**Statut:** EN ATTENTE D'ACTION
**Responsable:** Direction
**Date création:** 2026-02-17

---

## Vue d'ensemble

Ce document liste tous les contrats partenaires requis pour l'exploitation commerciale d'AZALSCORE.

## 1. Partenaires Paiement (OBLIGATOIRES)

### 1.1 Stripe

| Élément | Statut | Notes |
|---------|--------|-------|
| Compte Stripe Connect créé | ⬜ | Mode Platform pour marketplace |
| Contrat de service signé | ⬜ | |
| KYC entreprise validé | ⬜ | SIRET, Kbis, RIB |
| Clés API production | ⬜ | Après validation KYC |
| Webhook secret configuré | ⬜ | |
| Conformité PCI-DSS | ⬜ | Via Stripe (SAQ-A) |

**Contact:** https://dashboard.stripe.com/register

**Intégration technique:** `app/modules/stripe_integration/`

### 1.2 PayPal (Optionnel)

| Élément | Statut | Notes |
|---------|--------|-------|
| Compte Business PayPal | ⬜ | |
| API credentials production | ⬜ | |
| Webhook configuré | ⬜ | |

**Contact:** https://developer.paypal.com/

---

## 2. Partenaires Données Entreprise

### 2.1 Pappers (France)

| Élément | Statut | Notes |
|---------|--------|-------|
| Compte API créé | ⬜ | pappers.fr |
| Contrat API signé | ⬜ | Plan selon volume |
| Clé API production | ⬜ | |
| Conformité RGPD vérifiée | ⬜ | DPA signé |

**Intégration technique:** `app/modules/enrichment/providers/pappers.py`

**Tarification estimée:**
- Startup: 49€/mois (1000 req)
- Business: 199€/mois (10000 req)
- Enterprise: Sur devis

### 2.2 INSEE SIRENE (Gratuit)

| Élément | Statut | Notes |
|---------|--------|-------|
| Compte api.insee.fr créé | ⬜ | Gratuit |
| Token API obtenu | ⬜ | |

**Intégration technique:** `app/modules/enrichment/providers/sirene.py`

### 2.3 OpenCorporates (International)

| Élément | Statut | Notes |
|---------|--------|-------|
| Compte API créé | ⬜ | opencorporates.com |
| Contrat signé | ⬜ | Si > 500 req/mois |
| Clé API production | ⬜ | |

**Intégration technique:** `app/modules/enrichment/providers/opencorporates.py`

---

## 3. Partenaires Email/SMS

### 3.1 SendGrid / Mailgun / SES

| Élément | Statut | Notes |
|---------|--------|-------|
| Compte créé | ⬜ | |
| Domaine vérifié | ⬜ | DKIM, SPF, DMARC |
| Clé API production | ⬜ | |
| Templates validés | ⬜ | Anti-spam compliance |

### 3.2 Twilio (SMS - Optionnel)

| Élément | Statut | Notes |
|---------|--------|-------|
| Compte créé | ⬜ | Pour 2FA SMS |
| Numéro émetteur | ⬜ | |
| Contrat signé | ⬜ | |

---

## 4. Partenaires Stockage/Cloud

### 4.1 AWS / GCP / Azure

| Élément | Statut | Notes |
|---------|--------|-------|
| Compte entreprise créé | ⬜ | |
| Contrat enterprise signé | ⬜ | Support + SLA |
| IAM configuré | ⬜ | Least privilege |
| Région EU sélectionnée | ⬜ | RGPD compliance |

### 4.2 Backblaze B2 (Backups)

| Élément | Statut | Notes |
|---------|--------|-------|
| Compte créé | ⬜ | Alternative S3 économique |
| Bucket créé | ⬜ | Région EU |
| Clés API | ⬜ | |

---

## 5. Partenaires Sécurité

### 5.1 Sentry (Error Monitoring)

| Élément | Statut | Notes |
|---------|--------|-------|
| Compte créé | ⬜ | sentry.io |
| Projet configuré | ⬜ | |
| DSN obtenu | ⬜ | |
| Data residency EU | ⬜ | Plan Team+ |

### 5.2 Let's Encrypt / ZeroSSL

| Élément | Statut | Notes |
|---------|--------|-------|
| Certificat wildcard | ⬜ | *.azals.io |
| Auto-renewal configuré | ⬜ | Certbot |

---

## 6. Partenaires Conformité

### 6.1 Organisme de Certification NF525

| Élément | Statut | Notes |
|---------|--------|-------|
| Organisme sélectionné | ⬜ | AFNOR, LNE, Infocert |
| Dossier de certification soumis | ⬜ | |
| Audit programmé | ⬜ | |
| Certificat obtenu | ⬜ | Obligatoire si module POS |

**Note:** Certification obligatoire pour tout logiciel de caisse vendu en France (BOI-TVA-DECLA-30-10-30).

### 6.2 DPO Externe (Optionnel)

| Élément | Statut | Notes |
|---------|--------|-------|
| DPO désigné | ⬜ | Interne ou externe |
| Déclaration CNIL | ⬜ | |
| Registre des traitements | ⬜ | Déjà implémenté dans app |

---

## 7. Contrats Juridiques

### 7.1 CGV/CGU

| Élément | Statut | Notes |
|---------|--------|-------|
| CGV rédigées | ⬜ | Par avocat |
| CGU rédigées | ⬜ | |
| Politique confidentialité | ⬜ | |
| Mentions légales | ⬜ | |

**Fichiers existants:**
- `app/static/website/legal/cgv.html`
- `app/static/website/legal/privacy.html`
- `app/static/website/legal/mentions.html`

### 7.2 DPA (Data Processing Agreement)

| Élément | Statut | Notes |
|---------|--------|-------|
| Template DPA créé | ⬜ | Pour clients B2B |
| DPA avec sous-traitants | ⬜ | Stripe, AWS, etc. |

---

## 8. Assurances

### 8.1 RC Professionnelle

| Élément | Statut | Notes |
|---------|--------|-------|
| Assurance RC Pro souscrite | ⬜ | Obligatoire |
| Couverture cyber-risques | ⬜ | Recommandé |
| Attestation obtenue | ⬜ | |

---

## Prochaines Étapes

1. [ ] Prioriser les partenaires selon roadmap produit
2. [ ] Contacter les partenaires prioritaires (Stripe, Pappers)
3. [ ] Faire valider les contrats par avocat
4. [ ] Signer et archiver les contrats
5. [ ] Configurer les intégrations techniques
6. [ ] Documenter les credentials dans le gestionnaire de secrets

---

## Contacts Internes

- **Direction:** [À compléter]
- **Juridique:** [À compléter]
- **Technique:** [À compléter]

---

*Document de suivi - Tâche #27 Phase 0*
