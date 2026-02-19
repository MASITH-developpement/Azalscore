# SESSION C — CONFORMITÉ, TESTS, SÉCURITÉ, LÉGAL

## ⚠️ RÈGLES ABSOLUES

Attention, je vais te donner une mission à réaliser. J'attends de toi un certain nombre de choses, mais le plus important est la VÉRITÉ.

- **Pas de mensonge** — Je préfère une mauvaise note à une note truquée ou fausse
- **Pas de bullshit** — Que la vérité, même si elle n'est pas belle
- **Pas de report de correction** — Prends ton temps, approfondis tes recherches et corrections pour atteindre un code parfait. Corrige MAINTENANT ce que tu as trouvé, même les erreurs préexistantes. On fait quand on a trouvé l'erreur, pour ne pas oublier
- **Ne suppose rien** — Pas de "je pensais que", pas d'invention. Que des faits et de l'amélioration
- **Le code est déjà bien installé et sécurisé** — Il doit rester un exemple, perfectible mais une référence. RIEN ne doit réduire la sécurité ni le multi-tenant. L'améliorer oui, le réduire JAMAIS
- **L'objectif est la référence technique** — Ce code sera vérifié par des experts et des ingénieurs. PARFAIT
- **TESTE quand tu apportes des modifications** — Perfection absolue

## 🎯 MISSION VIRALITÉ

**Ta mission est de rendre le site azalscore.com VIRAL.** Il doit générer énormément de leads et de commandes. La conformité parfaite et la sécurité irréprochable sont des arguments de vente majeurs. Documente tout pour que ce soit vérifiable par des experts.

**MAIS ATTENTION :**
- Pas de mensonge sur les certifications
- Pas de fausse conformité
- Que la vérité vérifiable

## 🎯 PRIORITÉS

1. **Conformité légale France** — Deadline SEPTEMBRE 2026
2. **Sécurité OWASP** — Zéro vulnérabilité critique
3. **Tests 80%+ couverture** — Unitaires + Intégration + E2E
4. **Multi-tenant SACRÉ** — Auditer et renforcer l'isolation
5. **Documentation** — Complète, à jour, vérifiable

## 📂 CONTEXTE

- **Projet:** AZALSCORE ERP — `/home/ubuntu/azalscore/`
- **Documentation:** `/home/ubuntu/azalscore/memoire.md` et `/home/ubuntu/memoire.md`
- **Session:** C sur 3 (A=Backend, B=Frontend) — Travail en PARALLÈLE
- **Deadline légale:** Septembre 2026 (Facturation électronique obligatoire)

---

## 🔴 TES TÂCHES — PHASE 1 (Semaines 1-18) — CONFORMITÉ LÉGALE ⚠️ CRITIQUE

### Obligations légales France — DEADLINE SEPT 2026

| # | Tâche | GAP | Fichiers concernés |
|---|-------|-----|-------------------|
| #49 | **Facturation Électronique PDP** | GAP-006 | `app/modules/accounting/einvoicing/` |
| #52 | **Export FEC 2025** | GAP-041 | `app/modules/accounting/fec/` |
| #37 | **PCG 2025** (ANC 2022-6) | GAP-018 | `app/modules/accounting/chart_of_accounts/` |
| #50 | **EDI-TVA automatique** | GAP-040 | `app/modules/accounting/tax/` |
| #51 | **Liasses Fiscales** | - | `app/modules/accounting/fiscal/` |
| #104 | **Audit Conformité RGPD** | - | Tous les modules |
| #106 | **NF525 Caisse** | GAP-061 | `app/modules/pos/` |
| #108 | **Conformité Normes AZALSCORE** | - | Vérification globale |
| #128 | **Archivage Légal 10 ans** | GAP-022 | `app/modules/archive/` |

### Facturation Électronique PDP — Spécifications OBLIGATOIRES

```python
# OBLIGATOIRE — Formats à supporter
class EInvoiceFormat(str, Enum):
    FACTUR_X_MINIMUM = "factur-x-minimum"
    FACTUR_X_BASIC = "factur-x-basic"
    FACTUR_X_BASIC_WL = "factur-x-basic-wl"
    FACTUR_X_EN16931 = "factur-x-en16931"
    FACTUR_X_EXTENDED = "factur-x-extended"
    UBL_21 = "ubl-2.1"
    CII_D16B = "cii-d16b"

# OBLIGATOIRE — Validation XML Schema
async def validate_einvoice(invoice_xml: str, format: EInvoiceFormat) -> ValidationResult:
    """
    Valide une facture électronique contre le schéma officiel.

    Validation:
    - Schéma XSD officiel (EN16931, Factur-X)
    - Règles métier CHORUS PRO
    - SIRET/SIREN valides
    - TVA intracommunautaire si applicable

    Returns:
        ValidationResult avec statut, erreurs, warnings
    """
    pass

# OBLIGATOIRE — Génération PDF/A-3 avec XML embarqué
async def generate_facturx_pdf(invoice: Invoice, profile: str = "EN16931") -> bytes:
    """
    Génère un PDF/A-3 conforme Factur-X avec XML embarqué.

    Conformité:
    - PDF/A-3b minimum
    - XML embarqué en pièce jointe
    - Métadonnées XMP correctes
    - Signature optionnelle
    """
    pass

# OBLIGATOIRE — Envoi vers PDP
async def send_to_pdp(invoice: Invoice, pdp: str = "chorus") -> PDPResponse:
    """
    Envoie la facture vers la Plateforme de Dématérialisation Partenaire.

    PDP supportées:
    - Chorus Pro (secteur public)
    - Autres PDP agréées DGFiP
    """
    pass
```

### Export FEC — Spécifications OBLIGATOIRES

```python
# Format FEC 2025 — 18 colonnes obligatoires (Article A.47 A-1 LPF)
FEC_COLUMNS = [
    "JournalCode",    # Code journal
    "JournalLib",     # Libellé journal
    "EcritureNum",    # Numéro écriture
    "EcritureDate",   # Date écriture (YYYYMMDD)
    "CompteNum",      # Numéro compte
    "CompteLib",      # Libellé compte
    "CompAuxNum",     # Numéro compte auxiliaire
    "CompAuxLib",     # Libellé compte auxiliaire
    "PieceRef",       # Référence pièce
    "PieceDate",      # Date pièce (YYYYMMDD)
    "EcritureLib",    # Libellé écriture
    "Debit",          # Montant débit
    "Credit",         # Montant crédit
    "EcritureLet",    # Lettrage
    "DateLet",        # Date lettrage
    "ValidDate",      # Date validation
    "Montantdevise",  # Montant en devise
    "Idevise"         # Code devise ISO
]

async def export_fec(
    tenant_id: UUID,
    fiscal_year: int,
    siren: str,
    format: Literal["txt", "xml"] = "txt"
) -> FECExportResult:
    """
    Exporte le FEC conforme Article A.47 A-1 du LPF.

    Validation obligatoire:
    - Équilibre débit/crédit par écriture
    - Dates cohérentes (écriture >= pièce)
    - Comptes existants dans le PCG
    - Numérotation continue sans rupture
    - Encodage UTF-8 ou ISO-8859-15
    - Séparateur TAB ou pipe

    Fichier nommé: {SIREN}FEC{YYYYMMDD}.txt
    """
    pass

async def validate_fec(fec_content: bytes) -> FECValidationResult:
    """
    Valide un fichier FEC selon les règles DGFiP.

    Tests:
    - Structure 18 colonnes
    - Types de données
    - Équilibre comptable
    - Cohérence dates
    - Absence de doublons
    """
    pass
```

### PCG 2025 — Plan Comptable Général ANC 2022-6

```python
# Règlement ANC 2022-6 applicable au 1er janvier 2025
PCG_2025_CHANGES = {
    "new_accounts": [
        # Nouveaux comptes créés
    ],
    "renamed_accounts": [
        # Comptes renommés
    ],
    "deleted_accounts": [
        # Comptes supprimés
    ],
    "reclassified_accounts": [
        # Comptes reclassés
    ]
}

async def migrate_to_pcg_2025(tenant_id: UUID) -> MigrationResult:
    """
    Migre le plan comptable du tenant vers PCG 2025.

    Actions:
    - Créer nouveaux comptes
    - Renommer comptes existants
    - Archiver comptes supprimés (pas de suppression)
    - Reclasser écritures si nécessaire
    - Générer rapport de migration
    """
    pass
```

---

## 🟠 TES TÂCHES — PHASE 2 (Semaines 18-38) — TESTS & SÉCURITÉ

### Tests — Objectif 80% couverture

| # | Tâche | Cible |
|---|-------|-------|
| #99 | **Tests Unitaires** | 80% couverture |
| #100 | **Tests Intégration API** | Tous endpoints critiques |
| #103 | **Tests Régression** | Suite automatisée CI/CD |
| #101 | **Tests E2E** | Parcours utilisateur complets |
| #102 | **Tests Charge** | 1000 users simultanés |
| #19 | Tests unitaires Finance Suite | 90% couverture |
| #20 | Tests intégration Finance Suite | Tous les flows |
| #116 | Tests Disaster Recovery | RTO < 4h, RPO < 1h |

### Sécurité — Zéro vulnérabilité

| # | Tâche | Standard |
|---|-------|----------|
| #94 | **Audit OWASP Top 10** | Zéro critique/high |
| #98 | Audit Auth/Autorisation | RBAC complet vérifié |
| #105 | **Audit PCI DSS** | Si paiements cartes |
| #95 | **Pentest** | Externe recommandé |
| #115 | **Monitoring/Alerting** | Prometheus + Grafana |
| #114 | **Plan Rollback** | Documenté et testé |
| #107 | Audit Accessibilité RGAA/WCAG | AA minimum |

### Checklist OWASP Top 10 — 2021

```markdown
## À VÉRIFIER ET CORRIGER

### A01:2021 - Broken Access Control
- [ ] Isolation tenant vérifiée sur TOUS les endpoints
- [ ] Tests d'accès cross-tenant (doivent échouer)
- [ ] RBAC appliqué partout
- [ ] Pas d'IDOR (Insecure Direct Object Reference)
- [ ] Rate limiting sur endpoints sensibles

### A02:2021 - Cryptographic Failures
- [ ] Secrets dans vault (pas en code, pas en .env commité)
- [ ] TLS 1.3 minimum en production
- [ ] Passwords hashés bcrypt/argon2 (coût >= 12)
- [ ] Données sensibles chiffrées au repos (AES-256)
- [ ] Pas de données sensibles dans logs

### A03:2021 - Injection
- [ ] SQLAlchemy ORM exclusivement (pas de raw SQL)
- [ ] Validation Pydantic sur toutes les entrées
- [ ] Parameterized queries si SQL nécessaire
- [ ] Échappement XSS côté frontend
- [ ] CSP headers configurés

### A04:2021 - Insecure Design
- [ ] Threat modeling documenté
- [ ] Security by design validé
- [ ] Revue architecture sécurité

### A05:2021 - Security Misconfiguration
- [ ] Headers sécurité (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- [ ] DEBUG=False en production
- [ ] Secrets pas exposés dans erreurs
- [ ] CORS restrictif
- [ ] Versions serveur masquées

### A06:2021 - Vulnerable Components
- [ ] pip-audit sans vulnérabilité high/critical
- [ ] npm audit sans vulnérabilité high/critical
- [ ] Dépendances à jour (< 6 mois)
- [ ] Scan automatique CI/CD

### A07:2021 - Authentication Failures
- [ ] Rate limiting login (5 tentatives/15min)
- [ ] MFA disponible
- [ ] Session timeout (30min inactivité)
- [ ] Logout invalide tous les tokens
- [ ] Password policy forte

### A08:2021 - Software Integrity
- [ ] CI/CD sécurisé (secrets protégés)
- [ ] Signatures dépendances vérifiées
- [ ] Déploiement reproductible

### A09:2021 - Logging Failures
- [ ] Audit trail complet (qui, quoi, quand)
- [ ] Pas de données sensibles dans logs
- [ ] Logs centralisés et protégés
- [ ] Alertes sur événements critiques

### A10:2021 - SSRF
- [ ] Validation URLs externes (whitelist)
- [ ] Pas d'accès réseau interne depuis user input
- [ ] Timeout sur requêtes externes
```

---

## 🟡 TES TÂCHES — PHASE 3 (Semaines 38-54) — AUTOMATISATION

| # | Tâche | GAP |
|---|-------|-----|
| #43 | **Workflows illimités** | GAP-036 |
| #42 | **No-Code Formulaires** | GAP-031 |
| #44 | **Signature Électronique** | GAP-014 |
| #36 | **Multi-Sociétés Consolidation** | GAP-026 |
| #74 | VOIP intégrée | - |

---

## 🟢 TES TÂCHES — PHASE 4 (Semaines 54+) — DOCUMENTATION

| # | Tâche |
|---|-------|
| #111 | **Documentation Technique Complète** |
| #112 | **Gestion Dette Technique** |
| #27 | Contrats Partenaires (support juridique) |
| #28 | Validation Juridique Finance (support) |

---

## 🔄 SYNCHRONISATION AVEC AUTRES SESSIONS

```
SYNC 1 — Semaine 7
└── FEC + PCG prêts → Informer Session B (UI FEC)

SYNC 2 — Semaine 16
└── RGPD + NF525 + Archivage → Release Conformité

SYNC 3 — Semaine 36
└── Tests 80% + Sécurité OK → GO Production v1

SYNC 4 — Semaine 54
└── Multi-sociétés + Workflows → 🚀 PRODUCTION V2
```

---

## 🔍 AUDIT INITIAL — À EXÉCUTER EN PREMIER

```bash
# 1. Audit sécurité Python
bandit -r app/ -f json -o reports/security_bandit.json
bandit -r app/ -ll  # Affiche high/medium

# 2. Audit dépendances Python
pip-audit --format json -o reports/deps_python.json
pip-audit  # Affiche vulnérabilités

# 3. Audit dépendances JS
cd frontend && npm audit --json > ../reports/deps_npm.json
npm audit  # Affiche vulnérabilités

# 4. Couverture tests actuelle
pytest --cov=app --cov-report=html --cov-report=json tests/
# Ouvrir htmlcov/index.html

# 5. Vérification secrets
pip install detect-secrets
detect-secrets scan > reports/secrets_scan.json

# Alternative: trufflehog
trufflehog filesystem ./ --json > reports/secrets_trufflehog.json

# 6. Analyse statique
ruff check app/ --output-format=json > reports/lint_ruff.json
mypy app/ --json-report reports/types_mypy

# 7. Vérification OWASP headers (si serveur up)
curl -I https://azalscore.com | grep -E "^(Strict|Content-Security|X-)"
```

---

## 📏 CHECKLIST AVANT CHAQUE COMMIT

- [ ] Tests ajoutés pour le code modifié
- [ ] Couverture >= 80% maintenue
- [ ] `bandit` sans high/critical
- [ ] `pip-audit` / `npm audit` OK
- [ ] Isolation tenant vérifiée
- [ ] Documentation à jour
- [ ] Conformité légale respectée
- [ ] Logs sans données sensibles
- [ ] Pas de secrets hardcodés

---

## 🚀 COMMENCE PAR

1. **Exécuter l'audit initial** (commandes ci-dessus)
2. **Lire** `/home/ubuntu/azalscore/memoire.md` section TODOLIST (123 tâches)
3. **Lire** `/home/ubuntu/memoire.md` section ANALYSE CONCURRENTIELLE (86 GAPs)
4. **Corriger** les vulnérabilités trouvées IMMÉDIATEMENT
5. **Commencer** `#49 Facturation Électronique PDP` — PRIORITÉ #1

---

## 📊 RÉCAPITULATIF SESSION C

| Phase | Tâches | Semaines | Focus |
|-------|--------|----------|-------|
| 1 | 9 | S1-18 | Conformité Légale France |
| 2 | 16 | S18-38 | Tests 80% + Sécurité OWASP |
| 3 | 5 | S38-54 | Automatisation + Workflows |
| 4 | 4 | S54+ | Documentation + Qualité |
| **TOTAL** | **48** | ~75 sem | |

---

**GO !**
