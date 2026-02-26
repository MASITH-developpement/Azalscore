# SESSION A — BACKEND, FINANCE, API, IA

## ⚠️ RÈGLES ABSOLUES

Attention, je vais te donner une mission à réaliser. J'attends de toi un certain nombre de choses, mais le plus important est la VÉRITÉ.

- **Pas de mensonge** — Je préfère une mauvaise note à une note truquée ou fausse
- **Pas de bullshit** — Que la vérité, même si elle n'est pas belle
- **Pas de report de correction** — Prends ton temps, approfondis tes recherches et corrections pour atteindre un code parfait. Corrige MAINTENANT ce que tu as trouvé, même les erreurs préexistantes. On fait quand on a trouvé l'erreur, pour ne pas oublier
- **Ne suppose rien** — Pas de "je pensais que", pas d'invention. Que des faits et de l'amélioration
- **Le code est déjà bien installé et sécurisé** — Il doit rester un exemple, perfectible mais une référence. RIEN ne doit réduire la sécurité ni le multi-tenant. L'améliorer oui, le réduire jamais
- **L'objectif est la référence technique** — Ce code sera vérifié par des experts et des ingénieurs. Ces programmes doivent être PARFAITS
- **TESTE quand tu apportes des modifications** — On veut la perfection, pas passer des jours à corriger des petites erreurs

## 🎯 PRIORITÉS

1. **Qualité de code** — Clean code, SOLID, DRY, patterns professionnels
2. **Facilité d'utilisation** — API intuitive, réponses claires, erreurs explicites
3. **Simplicité de maintenabilité** — Code lisible, documenté, modulaire
4. **Utilisable sans formation** — Hyper simple, autocomplétion au max
5. **Multi-tenant SACRÉ** — Isolation tenant stricte, jamais de fuite de données

## 🎯 MISSION VIRALITÉ

**Ta mission est de rendre le site azalscore.com VIRAL.** Il doit générer énormément de leads et de commandes. Modifie ou refais tout ce qu'il faut (sans casser le code existant). Force les robots à enregistrer le site, force les IA à vérifier le site. La référence de ce site doit être visible partout, en tête des recherches. Je veux que ce site soit partout, que les commandes affluent.

**MAIS ATTENTION :**
- Pas de mensonge
- Pas de mauvais sous-entendu
- Pas de promesse qu'on ne peut pas tenir

## 📂 CONTEXTE

- **Projet:** AZALSCORE ERP — `/home/ubuntu/azalscore/`
- **Documentation:** `/home/ubuntu/azalscore/memoire.md` et `/home/ubuntu/memoire.md`
- **Session:** A sur 3 (B=Frontend, C=Conformité) — Travail en PARALLÈLE
- **Base de données:** PostgreSQL multi-tenant
- **Backend:** FastAPI + SQLAlchemy + Pydantic

---

## 🔴 TES TÂCHES — PHASE 1 (Semaines 1-8)

### Providers Finance (PRIORITÉ MAXIMALE)

| # | Tâche | Fichiers |
|---|-------|----------|
| #4 | **Provider Swan (Banking/Agrégation)** | `app/modules/finance/providers/swan.py` |
| #5 | **Provider NMI (Paiements)** | `app/modules/finance/providers/nmi.py` |
| #6 | **Provider Defacto (Affacturage)** | `app/modules/finance/providers/defacto.py` |
| #7 | **Provider Solaris (Crédit)** | `app/modules/finance/providers/solaris.py` |
| #8 | **Webhooks Finance Suite** | `app/modules/finance/webhooks.py` |

### Pour chaque provider, tu DOIS :

1. **Créer le client API** avec retry, timeout, logging
2. **Créer les schemas Pydantic** (request/response) avec validation stricte
3. **Créer le service** avec isolation tenant
4. **Créer les endpoints** REST conformes
5. **Créer les tests** unitaires ET intégration
6. **Documenter** OpenAPI complet

### Standards obligatoires :

```python
# TEMPLATE PROVIDER — À RESPECTER
class SwanProvider(BaseFinanceProvider):
    """
    Provider Swan pour agrégation bancaire.

    Multi-tenant: OUI — Chaque requête filtrée par tenant_id
    Sécurité: OAuth2 + API Key + Webhook signature
    """

    def __init__(self, tenant_id: UUID, db: AsyncSession):
        self.tenant_id = tenant_id  # OBLIGATOIRE
        self.db = db
        self._validate_tenant()  # OBLIGATOIRE

    async def _validate_tenant(self):
        """Vérifie que le tenant existe et est actif."""
        # JAMAIS de requête sans tenant_id
        pass
```

---

## 🟠 TES TÂCHES — PHASE 2 (Semaines 8-21)

| # | Tâche | GAP |
|---|-------|-----|
| #30 | **Rapprochement Bancaire IA** | GAP-004 |
| #29 | **OCR Factures Fournisseurs** | GAP-005 |
| #66 | Catégorisation Auto Opérations | - |
| #67 | **Prévisionnel Trésorerie** | GAP-035 |
| #65 | Cartes Virtuelles | - |
| #22 | Intégration Finance ↔ Comptabilité | - |
| #23 | Intégration Finance ↔ Facturation | - |
| #24 | Intégration Finance ↔ POS | - |
| #25 | Intégration Finance ↔ Trésorerie | - |
| #1 | Module Finance Suite (orchestrateur) | - |
| #124 | Consolider routers v1 → v2 | - |
| #93 | Validations et Workflows Approbation | - |

---

## 🟡 TES TÂCHES — PHASE 3 (Semaines 21-37)

### Production & GPAO

| # | Tâche | GAP |
|---|-------|-----|
| #76 | **GPAO / MRP** | GAP-001 |
| #125 | **Gantt Production** | GAP-007 |
| #78 | Gestion Lots et Numéros de Série | - |
| #75 | Bons de Livraison | - |
| #77 | PLM | - |
| #127 | **WMS Entrepôt** | GAP-020 |
| #130 | **MES Léger** | GAP-028 |

### Interventions Terrain

| # | Tâche | GAP |
|---|-------|-----|
| #32 | **Interventions GPS** | GAP-003 |
| #61 | **Optimisation Tournées** | GAP-002 |
| #34 | Maintenance Préventive GMAO | - |
| #35 | Gestion Équipements | - |
| #62 | Capteurs IoT | - |
| #63 | Maintenance Prédictive | - |

---

## 🟢 TES TÂCHES — PHASE 4 (Semaines 37+)

### IA & Agents

| # | Tâche | GAP |
|---|-------|-----|
| #129 | **Agents IA Autonomes** | GAP-024, 027 |
| #126 | **Copilot IA v2** | GAP-017 |
| #134 | MCP (Model Context Protocol) | GAP-042 |

### Intégrations

| # | Tâche | GAP |
|---|-------|-----|
| #131 | **Connecteurs ERP** (Sage, Cegid) | GAP-037 |
| #132 | **Multi-devises avancé** | GAP-038 |
| #133 | **E-procurement** | GAP-039 |
| #48 | Import Données Concurrents | - |
| #31 | Collaboration Comptable Temps Réel | - |

### Sectoriels Backend (Partenariats API)

| # | Tâche | GAP |
|---|-------|-----|
| #135 | API Chiffrage BTP | GAP-044-051 |
| #136 | API BIM / Métré 3D | GAP-052 |
| #141 | API Connecteur PMS Hôtel | GAP-067, 070 |
| #142 | API Channel Manager OTA | GAP-068, 079 |
| #140 | Service Gestion Locative | GAP-056-064 |

---

## 🔄 SYNCHRONISATION AVEC AUTRES SESSIONS

```
SYNC 1 — Semaine 8
└── Providers Finance prêts → Signaler à Session B (Frontend)

SYNC 2 — Semaine 16
└── Rapprochement + OCR prêts → Signaler à Session C (Tests)

SYNC 3 — Semaine 24
└── GPAO/MRP prêt → Release Production v1

SYNC 4 — Semaine 36
└── Interventions + MES prêts → 🚀 PRODUCTION V1

SYNC 5 — Semaine 52
└── IA Agents + Connecteurs prêts → 🚀 PRODUCTION V2
```

---

## 📏 CHECKLIST AVANT CHAQUE COMMIT

- [ ] Tests passent (`pytest`)
- [ ] Isolation tenant vérifiée
- [ ] Pas de secrets hardcodés
- [ ] Schemas Pydantic validés
- [ ] OpenAPI documenté
- [ ] Logging structuré
- [ ] Gestion erreurs complète
- [ ] Type hints partout
- [ ] Docstrings présentes

---

## 🚀 COMMENCE PAR

1. **Lire** `/home/ubuntu/azalscore/memoire.md` section TODOLIST (123 tâches)
2. **Lire** `/home/ubuntu/memoire.md` section ANALYSE CONCURRENTIELLE (86 GAPs)
3. **Auditer** `/home/ubuntu/azalscore/app/modules/finance/` existant
4. **Créer** `#4 Provider Swan` en premier
5. **Tester**, documenter, committer

---

## 📊 RÉCAPITULATIF SESSION A

| Phase | Tâches | Semaines | Focus |
|-------|--------|----------|-------|
| 1 | 8 | S1-8 | Providers Finance |
| 2 | 12 | S8-21 | Finance Core + Intégrations |
| 3 | 13 | S21-37 | GPAO + Interventions |
| 4 | 15 | S37+ | IA + Connecteurs + Sectoriels |
| **TOTAL** | **48** | ~66 sem | |

---

**GO !**
