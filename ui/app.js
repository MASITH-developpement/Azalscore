/**
 * AZALS - Application Frontend
 * ERP Premium - Interface décisionnelle
 * 
 * Vanilla JS uniquement - Aucune dépendance externe
 * 
 * ══════════════════════════════════════════════════════════════════════════════════
 * CORE AZALS V1.0 — FIGÉ LE 2 JANVIER 2026
 * 
 * Ce fichier contient le CORE du système de priorisation AZALS.
 * Toute modification nécessite une décision d'architecture consciente.
 * 
 * RÈGLES FONDAMENTALES :
 * - Un seul 🔴 visible à la fois
 * - Ordre de priorité : Financier > Juridique > Fiscal > RH > Comptabilité
 * - Souveraineté du dirigeant (aucune action automatique)
 * - Pattern 🔴 (plan dominant) : affichage exclusif du risque prioritaire
 * 
 * DOCUMENTATION : /README_CORE_AZALS.md
 * ══════════════════════════════════════════════════════════════════════════════════
 */

// =============================================
// CONFIGURATION
// =============================================

const API_BASE = '/v1';

// =============================================
// BRANDING CONFIGURATION
// Titre et favicon Azalscore - Multi-tenant prêt mais désactivé
// =============================================

const BRANDING = {
    defaultTitle: 'Azalscore',
    faviconPath: '/favicon.png',
    enableTenantBranding: false
};

/**
 * Initialise le branding (titre d'onglet)
 * Multi-tenant désactivé par défaut
 */
function initBranding() {
    document.title = BRANDING.defaultTitle;
}

// =============================================
// MODE TEST AZALS (TEMPORAIRE)
// =============================================

/**
 * MODE TEST INTERNE - TEMPORAIRE
 * Permet de forcer les états des modules pour tester la priorisation
 * 
 * DÉSACTIVATION : mettre à false
 * SUPPRESSION : supprimer ce bloc + panneau HTML + logique dans collectStates()
 */
// PRODUCTION: Mode test desactive
// Pour reactiver en dev, mettre a true
const AZALS_TEST_MODE = false;

/**
 * États forcés par le mode test
 * Valeurs possibles : 'green' | 'orange' | 'red' | null
 */
const AZALS_FORCED_STATES = {
    treasury: null,
    legal: null,
    tax: null,
    hr: null,
    accounting: null
};

/**
 * Applique un état forcé à un module (mode test uniquement)
 */
function azalsForceState(moduleId, state) {
    if (!AZALS_TEST_MODE) return;
    
    AZALS_FORCED_STATES[moduleId] = state;
    console.log(`[AZALS TEST] État forcé : ${moduleId} → ${state}`);
    
    // Rafraîchir le cockpit
    buildCockpit();
}

/**
 * Initialise le panneau de test AZALS
 */
function initAzalsTestPanel() {
    if (!AZALS_TEST_MODE) return;
    
    const panel = document.getElementById('azalsTestPanel');
    if (!panel) return;
    
    // Afficher le panneau
    panel.style.display = 'block';
    
    // Gestionnaires d'événements pour les selects
    const modules = ['treasury', 'legal', 'tax', 'hr', 'accounting'];
    modules.forEach(moduleId => {
        const select = document.getElementById(`azalsTest_${moduleId}`);
        if (select) {
            select.addEventListener('change', (e) => {
                const value = e.target.value === 'default' ? null : e.target.value;
                azalsForceState(moduleId, value);
            });
        }
    });
    
    console.log('[AZALS TEST] Panneau de test activé');
}

// =============================================
// JOURNALISATION COCKPIT
// =============================================

/**
 * Journal des décisions de priorisation
 * Trace toutes les règles appliquées pour audit
 */
const cockpitLog = [];

// ══════════════════════════════════════════════════════════════════════════════════
// CORE AZALS — NE PAS MODIFIER SANS DÉCISION D'ARCHITECTURE
// ══════════════════════════════════════════════════════════════════════════════════

/**
 * ORDRE DE PRIORITÉ STRICT (non modifiable)
 * Définit l'ordre absolu de traitement des alertes critiques
 * 
 * JUSTIFICATION :
 * 1. Trésorerie : Sans liquidité, l'entreprise meurt immédiatement
 * 2. Juridique : Responsabilité personnelle du dirigeant engagée
 * 3. Fiscalité : Risques pénaux + pénalités exponentielles
 * 4. RH : Risques URSSAF + contentieux prud'homaux
 * 5. Comptabilité : Risque indirect (certification, audit)
 * 
 * ⚠️ MODIFICATION INTERDITE sans validation architecte ERP senior
 * Documentation : /README_CORE_AZALS.md section "Règles de priorisation strictes"
 */
const DOMAIN_PRIORITY = {
    'treasury': 1,      // Financier (Trésorerie)
    'legal': 2,         // Juridique / Structurel
    'tax': 3,           // Fiscalité
    'hr': 4,            // Ressources Humaines
    'accounting': 5     // Comptabilité
};

/**
 * Journaliser une décision de priorisation
 */
function logPriorityDecision(module, level, rule, details = {}) {
    const entry = {
        timestamp: new Date().toISOString(),
        module: module,
        level: level,
        rule: rule,
        details: details
    };
    cockpitLog.push(entry);
    console.log(`[COCKPIT] ${rule} → ${module} (${level})`, details);
}

// =============================================
// AUTHENTIFICATION
// =============================================

/**
 * Vérifie si l'utilisateur est authentifié
 */
function checkAuth() {
    const token = sessionStorage.getItem('token');
    if (!token) {
        window.location.href = '/';
        return false;
    }
    return true;
}

/**
 * Fetch authentifié avec gestion du tenant
 */
async function authenticatedFetch(url, options = {}) {
    const token = sessionStorage.getItem('token');
    const tenantId = sessionStorage.getItem('tenant_id');
    
    if (!token) {
        window.location.href = '/';
        throw new Error('Non authentifié');
    }
    
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (tenantId) {
        headers['X-Tenant-ID'] = tenantId;
    }
    
    const response = await fetch(url, { ...options, headers });
    
    if (response.status === 401) {
        sessionStorage.clear();
        window.location.href = '/';
        throw new Error('Session expirée');
    }
    
    return response;
}

// =============================================
// PAGE LOGIN
// =============================================

/**
 * Gestion du formulaire de connexion
 */
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const tenantId = document.getElementById('tenant_id')?.value || 'default';
    const errorDiv = document.getElementById('error');
    
    if (errorDiv) errorDiv.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenantId
            },
            body: JSON.stringify({ email, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Identifiants invalides');
        }
        
        const data = await response.json();
        sessionStorage.setItem('token', data.access_token);
        sessionStorage.setItem('tenant_id', tenantId);
        sessionStorage.setItem('user_email', email);
        
        window.location.href = '/dashboard';
        
    } catch (error) {
        if (errorDiv) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    }
}

/**
 * Déconnexion
 */
function handleLogout() {
    sessionStorage.clear();
    window.location.href = '/';
}

// =============================================
// DASHBOARD - COCKPIT
// =============================================

/**
 * Initialisation du dashboard
 */
async function initDashboard() {
    if (!checkAuth()) return;
    
    // Afficher le nom utilisateur
    const userEmail = sessionStorage.getItem('user_email') || 'Utilisateur';
    const userNameEl = document.getElementById('userName');
    if (userNameEl) {
        userNameEl.textContent = userEmail;
    }
    
    // Initialiser les bulles d'aide
    initHelpBubbles();
    
    // Initialiser le panneau de test AZALS (si mode test actif)
    initAzalsTestPanel();
    
    // Construire le cockpit
    await buildCockpit();
}

/**
 * COCKPIT DIRIGEANT - Vue décisionnelle exclusive
 * 
 * RÈGLE ABSOLUE : Un seul 🔴 visible à la fois
 * ORDRE DE PRIORITÉ : Trésorerie > Juridique > Fiscalité > RH > Comptabilité
 * 
 * COMPORTEMENT :
 * - Si au moins un 🔴 → afficher UNIQUEMENT le 🔴 prioritaire, masquer tout le reste
 * - Si aucun 🔴 → afficher les 🟠 classés par impact, puis les 🟢
 * - Traçabilité : journalisation de chaque décision
 * - Robustesse : module non répondant = 🟠 par défaut
 */
async function buildCockpit() {
    // ============================================
    // RÉCUPÉRATION DES ZONES HTML
    // ============================================
    const zoneCritical = document.getElementById('zoneCritical');
    const zoneTension = document.getElementById('zoneTension');
    const zoneNormal = document.getElementById('zoneNormal');
    const zoneAnalysis = document.getElementById('zoneAnalysis');
    
    const criticalContainer = document.getElementById('criticalAlertContainer');
    const tensionContainer = document.getElementById('tensionCardsContainer');
    const normalContainer = document.getElementById('normalCardsContainer');
    const analysisContainer = document.getElementById('analysisContainer');
    
    // Loader pendant le chargement
    if (normalContainer) {
        normalContainer.innerHTML = '<div class="loading-state">Analyse des risques...</div>';
    }
    
    // Masquer toutes les zones par défaut
    if (zoneCritical) zoneCritical.style.display = 'none';
    if (zoneTension) zoneTension.style.display = 'none';
    if (zoneNormal) zoneNormal.style.display = 'none';
    if (zoneAnalysis) zoneAnalysis.style.display = 'none';
    
    try {
        // ============================================
        // PHASE 1 : COLLECTE DES ÉTATS
        // ============================================
        const states = await collectStates();
        
        // ============================================
        // PHASE 2 : RÉSOLUTION DE PRIORITÉ
        // ============================================
        const priority = resolvePriority(states);
        
        // ============================================
        // PHASE 3 : RENDU DU COCKPIT
        // ============================================
        renderCockpit(priority, states);
        
        // Réinitialiser les bulles d'aide
        initHelpBubbles();
        
        // Hook pour extensions futures
        onCockpitReady({
            displayMode: priority.mode,
            primaryModule: priority.primaryModule,
            visibleModules: priority.visibleModules,
            hiddenCount: priority.hiddenModules?.length || 0
        });
        
    } catch (error) {
        console.error('Erreur cockpit:', error);
        logPriorityDecision('system', 'error', 'BUILD_COCKPIT_ERROR', { error: error.message });
        
        const errorHtml = `
            <div class="card card-alert">
                <div class="card-header">
                    <h3 class="card-title">Erreur de chargement</h3>
                    <span class="status-indicator">⚠️</span>
                </div>
                <div class="card-body">
                    <p>${error.message}</p>
                </div>
            </div>
        `;
        if (normalContainer) {
            normalContainer.innerHTML = errorHtml;
        } else if (legacyGrid) {
            legacyGrid.innerHTML = errorHtml;
        }
    }
}

// ══════════════════════════════════════════════════════════════════════════════════
// CORE AZALS — PRIORISATION TRANSVERSE (FIGÉE)
// ══════════════════════════════════════════════════════════════════════════════════
//
// Les 3 fonctions suivantes constituent le CŒUR du système AZALS :
// - collectStates()    : Charge les états de tous les modules
// - resolvePriority()  : Applique les 3 règles strictes de priorisation
// - renderCockpit()    : Affiche le cockpit selon la décision
//
// RÈGLE ABSOLUE : Un seul 🔴 visible à la fois
//
// COMPORTEMENT :
// - Si au moins un 🔴 → afficher UNIQUEMENT le 🔴 prioritaire (masquer tout le reste)
// - Si aucun 🔴 → afficher les 🟠 classés par impact + les 🟢
// - Traçabilité : journalisation de chaque décision
// - Robustesse : module non répondant = 🟠 par défaut
//
// ⚠️ MODIFICATION INTERDITE sans validation architecte ERP senior
// Documentation : /README_CORE_AZALS.md section "Système de priorisation"
//
// ══════════════════════════════════════════════════════════════════════════════════

// =============================================
// PRIORISATION TRANSVERSE - FONCTIONS ISOLÉES
// =============================================

/**
 * PHASE 1 : COLLECTE DES ÉTATS
 * Charge toutes les données des modules avec gestion d'erreurs robuste
 * Si un module échoue → état 🟠 par défaut + journalisation
 * 
 * MODE TEST AZALS : Si AZALS_TEST_MODE est actif, les états forcés
 * depuis le panneau de test écrasent les données réelles de l'API.
 * 
 * @returns {Object} États de tous les modules avec leurs données
 */
async function collectStates() {
    logPriorityDecision('system', 'info', 'COLLECTE_ETATS_START', { 
        timestamp: new Date().toISOString(),
        testMode: AZALS_TEST_MODE 
    });
    
    const states = {
        treasury: { loaded: false, error: null, data: null, module: null },
        accounting: { loaded: false, error: null, data: null, module: null },
        legal: { loaded: false, error: null, data: null, module: null },
        tax: { loaded: false, error: null, data: null, module: null },
        hr: { loaded: false, error: null, data: null, module: null }
    };
    
    // Charger toutes les données en parallèle avec gestion d'erreurs individuelles
    const loadingPromises = [
        // Trésorerie
        (async () => {
            try {
                const treasuryData = await loadTreasuryData();
                
                // Vérifier workflow RED si nécessaire
                let isWorkflowCompleted = false;
                if (treasuryData && treasuryData.red_triggered && treasuryData.id) {
                    try {
                        const statusResponse = await authenticatedFetch(`${API_BASE}/decision/red/status/${treasuryData.id}`);
                        if (statusResponse.ok) {
                            const workflowStatus = await statusResponse.json();
                            isWorkflowCompleted = workflowStatus.is_fully_validated || false;
                        }
                    } catch (error) {
                        console.error('Erreur workflow status:', error);
                    }
                }
                
                states.treasury.data = treasuryData;
                states.treasury.module = buildTreasuryModule(treasuryData, isWorkflowCompleted);
                states.treasury.loaded = true;
                logPriorityDecision('treasury', 'info', 'MODULE_LOADED', { 
                    status: states.treasury.module?.status,
                    priority: states.treasury.module?.priority 
                });
            } catch (error) {
                states.treasury.error = error.message;
                states.treasury.module = {
                    id: 'treasury',
                    name: 'Trésorerie',
                    priority: 1,  // 🟠 par défaut en cas d'erreur
                    status: '🟠',
                    data: { error: 'unavailable' },
                    createCard: () => createTreasuryCard({ error: 'unavailable' }, '🟠', null),
                    criticalMessage: '⚠️ Données temporairement indisponibles'
                };
                logPriorityDecision('treasury', '🟠', 'MODULE_ERROR_FALLBACK', { error: error.message });
            }
        })(),
        
        // Comptabilité
        (async () => {
            try {
                const accountingData = await loadAccountingData();
                states.accounting.data = accountingData;
                states.accounting.module = buildAccountingModule(accountingData);
                states.accounting.loaded = true;
                logPriorityDecision('accounting', 'info', 'MODULE_LOADED', { 
                    status: states.accounting.module?.status,
                    priority: states.accounting.module?.priority 
                });
            } catch (error) {
                states.accounting.error = error.message;
                states.accounting.module = {
                    id: 'accounting',
                    name: 'Comptabilité',
                    priority: 1,
                    status: '🟠',
                    data: { error: 'unavailable' },
                    createCard: () => createAccountingCard({ error: 'unavailable' }, '🟠'),
                    criticalMessage: '⚠️ Données temporairement indisponibles'
                };
                logPriorityDecision('accounting', '🟠', 'MODULE_ERROR_FALLBACK', { error: error.message });
            }
        })(),
        
        // Juridique
        (async () => {
            try {
                const legalData = await loadLegalData();
                states.legal.data = legalData;
                states.legal.module = buildLegalModule(legalData);
                states.legal.loaded = true;
                logPriorityDecision('legal', 'info', 'MODULE_LOADED', { 
                    status: states.legal.module?.status,
                    priority: states.legal.module?.priority 
                });
            } catch (error) {
                states.legal.error = error.message;
                states.legal.module = {
                    id: 'legal',
                    name: 'Juridique',
                    priority: 1,
                    status: '🟠',
                    data: { error: 'unavailable' },
                    createCard: () => createLegalCard({ error: 'unavailable' }, '🟠'),
                    criticalMessage: '⚠️ Données temporairement indisponibles'
                };
                logPriorityDecision('legal', '🟠', 'MODULE_ERROR_FALLBACK', { error: error.message });
            }
        })(),
        
        // Fiscalité
        (async () => {
            try {
                const taxData = await loadTaxData();
                states.tax.data = taxData;
                states.tax.module = buildTaxModule(taxData);
                states.tax.loaded = true;
                logPriorityDecision('tax', 'info', 'MODULE_LOADED', { 
                    status: states.tax.module?.status,
                    priority: states.tax.module?.priority 
                });
            } catch (error) {
                states.tax.error = error.message;
                states.tax.module = {
                    id: 'tax',
                    name: 'Fiscalité',
                    priority: 1,
                    status: '🟠',
                    data: { error: 'unavailable' },
                    createCard: () => createTaxCard({ error: 'unavailable' }, '🟠'),
                    criticalMessage: '⚠️ Données temporairement indisponibles'
                };
                logPriorityDecision('tax', '🟠', 'MODULE_ERROR_FALLBACK', { error: error.message });
            }
        })(),
        
        // RH
        (async () => {
            try {
                const hrData = await loadHRData();
                states.hr.data = hrData;
                states.hr.module = buildHRModule(hrData);
                states.hr.loaded = true;
                logPriorityDecision('hr', 'info', 'MODULE_LOADED', { 
                    status: states.hr.module?.status,
                    priority: states.hr.module?.priority 
                });
            } catch (error) {
                states.hr.error = error.message;
                states.hr.module = {
                    id: 'hr',
                    name: 'RH',
                    priority: 1,
                    status: '🟠',
                    data: { error: 'unavailable' },
                    createCard: () => createHRCard({ error: 'unavailable' }, '🟠'),
                    criticalMessage: '⚠️ Données temporairement indisponibles'
                };
                logPriorityDecision('hr', '🟠', 'MODULE_ERROR_FALLBACK', { error: error.message });
            }
        })()
    ];
    
    // Attendre toutes les promesses
    await Promise.all(loadingPromises);
    
    // ═══════════════════════════════════════════════════════════
    // MODE TEST AZALS : Surcharger les états si forcés
    // ═══════════════════════════════════════════════════════════
    if (AZALS_TEST_MODE) {
        Object.keys(AZALS_FORCED_STATES).forEach(moduleId => {
            const forcedState = AZALS_FORCED_STATES[moduleId];
            if (forcedState && states[moduleId]?.module) {
                const module = states[moduleId].module;
                
                // Mapper état test vers priorité/status
                let priority, status;
                switch (forcedState) {
                    case 'red':
                        priority = 0;
                        status = '🔴';
                        module.criticalMessage = `[TEST] Alerte critique forcée`;
                        break;
                    case 'orange':
                        priority = 1;
                        status = '🟠';
                        module.criticalMessage = `[TEST] Attention forcée`;
                        break;
                    case 'green':
                        priority = 2;
                        status = '🟢';
                        module.criticalMessage = null;
                        break;
                }
                
                // Appliquer l'état forcé
                module.priority = priority;
                module.status = status;
                
                logPriorityDecision(moduleId, status, 'AZALS_TEST_FORCE', { 
                    forcedState,
                    originalPriority: states[moduleId].module.priority,
                    newPriority: priority
                });
            }
        });
    }
    // ═══════════════════════════════════════════════════════════
    
    logPriorityDecision('system', 'info', 'COLLECTE_ETATS_COMPLETE', {
        loaded: Object.values(states).filter(s => s.loaded).length,
        errors: Object.values(states).filter(s => s.error).length,
        testModeActive: AZALS_TEST_MODE,
        forcedStates: AZALS_TEST_MODE ? Object.entries(AZALS_FORCED_STATES).filter(([k,v]) => v).length : 0
    });
    
    return states;
}

/**
 * PHASE 2 : RÉSOLUTION DE PRIORITÉ
 * Applique les règles de priorisation strictes
 * 
 * RÈGLE ABSOLUE : Un seul 🔴 visible à la fois
 * ORDRE : Trésorerie > Juridique > Fiscalité > RH > Comptabilité
 * 
 * @param {Object} states - États collectés
 * @returns {Object} Décision de priorisation avec modules à afficher/masquer
 */
function resolvePriority(states) {
    logPriorityDecision('system', 'info', 'RESOLUTION_PRIORITE_START');
    
    // Construire la liste des modules avec priorité de domaine
    const modules = [
        { ...states.treasury.module, domain: 'Financier', domainPriority: DOMAIN_PRIORITY.treasury },
        { ...states.accounting.module, domain: 'Financier', domainPriority: DOMAIN_PRIORITY.accounting },
        { ...states.legal.module, domain: 'Juridique', domainPriority: DOMAIN_PRIORITY.legal },
        { ...states.tax.module, domain: 'Fiscal', domainPriority: DOMAIN_PRIORITY.tax },
        { ...states.hr.module, domain: 'Social', domainPriority: DOMAIN_PRIORITY.hr }
    ];
    
    // Séparer par niveau de risque
    const criticalModules = modules.filter(m => m.priority === 0);  // 🔴
    const tensionModules = modules.filter(m => m.priority === 1);   // 🟠
    const normalModules = modules.filter(m => m.priority === 2);    // 🟢
    
    logPriorityDecision('system', 'info', 'MODULES_REPARTITION', {
        critical: criticalModules.length,
        tension: tensionModules.length,
        normal: normalModules.length
    });
    
    let decision;
    
    if (criticalModules.length > 0) {
        // ══════════════════════════════════════════
        // RÈGLE 1 : AU MOINS UN 🔴 PRÉSENT
        // → Afficher UNIQUEMENT le 🔴 prioritaire
        // → Masquer TOUS les 🟠 et 🟢
        // ══════════════════════════════════════════
        
        // Trier les critiques par priorité de domaine
        criticalModules.sort((a, b) => a.domainPriority - b.domainPriority);
        
        const primaryModule = criticalModules[0];
        const hiddenCriticals = criticalModules.slice(1);
        
        logPriorityDecision(primaryModule.id, '🔴', 'REGLE_CRITIQUE_UNIQUE', {
            primaryModule: primaryModule.name,
            domainPriority: primaryModule.domainPriority,
            hiddenCriticals: hiddenCriticals.map(m => m.name),
            hiddenTension: tensionModules.length,
            hiddenNormal: normalModules.length
        });
        
        decision = {
            mode: 'critical',
            rule: 'REGLE_CRITIQUE_UNIQUE',
            primaryModule: primaryModule,
            visibleModules: [primaryModule],
            hiddenModules: [...hiddenCriticals, ...tensionModules, ...normalModules],
            message: `⚠️ ${hiddenCriticals.length + tensionModules.length + normalModules.length} autres indicateurs masqués`
        };
        
    } else if (tensionModules.length > 0) {
        // ══════════════════════════════════════════
        // RÈGLE 2 : AUCUN 🔴, AU MOINS UN 🟠
        // → Afficher les 🟠 classés par impact
        // → Afficher les 🟢 en complément
        // ══════════════════════════════════════════
        
        // Trier par priorité de domaine
        tensionModules.sort((a, b) => a.domainPriority - b.domainPriority);
        
        logPriorityDecision('system', '🟠', 'REGLE_TENSION_MULTIPLE', {
            tensionCount: tensionModules.length,
            tensionModules: tensionModules.map(m => ({ name: m.name, priority: m.domainPriority })),
            normalCount: normalModules.length
        });
        
        decision = {
            mode: 'tension',
            rule: 'REGLE_TENSION_MULTIPLE',
            primaryModule: tensionModules[0],
            visibleModules: [...tensionModules, ...normalModules],
            hiddenModules: [],
            message: `${tensionModules.length} point${tensionModules.length > 1 ? 's' : ''} d'attention`
        };
        
    } else {
        // ══════════════════════════════════════════
        // RÈGLE 3 : AUCUN 🔴, AUCUN 🟠
        // → Afficher tous les 🟢
        // → Mode normal complet
        // ══════════════════════════════════════════
        
        logPriorityDecision('system', '🟢', 'REGLE_NORMAL_COMPLET', {
            normalCount: normalModules.length,
            modules: normalModules.map(m => m.name)
        });
        
        decision = {
            mode: 'normal',
            rule: 'REGLE_NORMAL_COMPLET',
            primaryModule: null,
            visibleModules: normalModules,
            hiddenModules: [],
            message: 'Tous les indicateurs sont normaux'
        };
    }
    
    logPriorityDecision('system', 'info', 'RESOLUTION_PRIORITE_COMPLETE', {
        mode: decision.mode,
        rule: decision.rule,
        visible: decision.visibleModules.length,
        hidden: decision.hiddenModules.length
    });
    
    return decision;
}

/**
 * PHASE 3 : RENDU DU COCKPIT
 * Affiche le cockpit selon la décision de priorisation
 * 
 * @param {Object} priority - Décision de priorisation
 * @param {Object} states - États des modules
 */
function renderCockpit(priority, states) {
    logPriorityDecision('system', 'info', 'RENDER_COCKPIT_START', { mode: priority.mode });
    
    const zoneCritical = document.getElementById('zoneCritical');
    const zoneTension = document.getElementById('zoneTension');
    const zoneNormal = document.getElementById('zoneNormal');
    const zoneAnalysis = document.getElementById('zoneAnalysis');
    
    const criticalContainer = document.getElementById('criticalAlertContainer');
    const tensionContainer = document.getElementById('tensionCardsContainer');
    const normalContainer = document.getElementById('normalCardsContainer');
    const analysisContainer = document.getElementById('analysisContainer');
    
    // Réinitialiser toutes les zones
    if (zoneCritical) {
        zoneCritical.style.display = 'none';
        zoneCritical.classList.remove('zone-inactive');
    }
    if (zoneTension) {
        zoneTension.style.display = 'none';
        zoneTension.classList.remove('zone-inactive');
    }
    if (zoneNormal) {
        zoneNormal.style.display = 'none';
        zoneNormal.classList.remove('zone-inactive');
    }
    if (zoneAnalysis) {
        zoneAnalysis.style.display = 'none';
        zoneAnalysis.classList.remove('zone-inactive');
    }
    
    if (criticalContainer) criticalContainer.innerHTML = '';
    if (tensionContainer) tensionContainer.innerHTML = '';
    if (normalContainer) normalContainer.innerHTML = '';
    if (analysisContainer) analysisContainer.innerHTML = '';
    
    if (priority.mode === 'critical') {
        // ══════════════════════════════════════════
        // MODE CRITIQUE 🔴
        // Afficher UNIQUEMENT le module prioritaire
        // ══════════════════════════════════════════
        
        if (zoneCritical && criticalContainer && priority.primaryModule) {
            zoneCritical.style.display = 'block';
            
            // Créer vue critique avec un seul module
            const criticalCard = createCockpitCriticalView([priority.primaryModule]);
            if (criticalCard) {
                criticalContainer.appendChild(criticalCard);
            }
            
            // Ajouter message d'avertissement pour modules masqués
            if (priority.hiddenModules.length > 0) {
                const warningDiv = document.createElement('div');
                warningDiv.className = 'priority-warning';
                warningDiv.innerHTML = `
                    <div style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); 
                                border-radius: 8px; padding: 16px; margin-top: 16px; color: rgba(255,255,255,0.9);">
                        <strong>⚠️ ${priority.hiddenModules.length} indicateur${priority.hiddenModules.length > 1 ? 's' : ''} masqué${priority.hiddenModules.length > 1 ? 's' : ''}</strong><br>
                        <small>Traitez d'abord cette situation critique. Les autres indicateurs seront visibles ensuite.</small>
                    </div>
                `;
                criticalContainer.appendChild(warningDiv);
            }
            
            logPriorityDecision('render', 'info', 'AFFICHAGE_CRITIQUE_UNIQUE', {
                visible: priority.primaryModule.name,
                hidden: priority.hiddenModules.length
            });
        }
        
    } else if (priority.mode === 'tension') {
        // ══════════════════════════════════════════
        // MODE TENSION 🟠
        // Afficher tous les modules en tension + normaux
        // ══════════════════════════════════════════
        
        const tensionModules = priority.visibleModules.filter(m => m.priority === 1);
        const normalModules = priority.visibleModules.filter(m => m.priority === 2);
        
        if (zoneTension && tensionContainer && tensionModules.length > 0) {
            zoneTension.style.display = 'block';
            
            for (const mod of tensionModules) {
                const card = mod.createCard();
                if (card) tensionContainer.appendChild(card);
            }
            
            logPriorityDecision('render', 'info', 'AFFICHAGE_TENSION', {
                count: tensionModules.length
            });
        }
        
        if (zoneNormal && normalContainer && normalModules.length > 0) {
            zoneNormal.style.display = 'block';
            
            for (const mod of normalModules) {
                const card = mod.createCard();
                if (card) normalContainer.appendChild(card);
            }
            
            logPriorityDecision('render', 'info', 'AFFICHAGE_NORMAL_COMPLEMENTAIRE', {
                count: normalModules.length
            });
        }
        
        // Graphiques
        if (zoneAnalysis && analysisContainer) {
            zoneAnalysis.style.display = 'block';
            const chartCard = createChartCard();
            if (chartCard) analysisContainer.appendChild(chartCard);
        }
        
    } else {
        // ══════════════════════════════════════════
        // MODE NORMAL 🟢
        // Afficher tous les modules
        // ══════════════════════════════════════════
        
        if (zoneNormal && normalContainer) {
            zoneNormal.style.display = 'block';
            
            for (const mod of priority.visibleModules) {
                const card = mod.createCard();
                if (card) normalContainer.appendChild(card);
            }
            
            logPriorityDecision('render', 'info', 'AFFICHAGE_NORMAL_COMPLET', {
                count: priority.visibleModules.length
            });
        }
        
        // Graphiques
        if (zoneAnalysis && analysisContainer) {
            zoneAnalysis.style.display = 'block';
            const chartCard = createChartCard();
            if (chartCard) analysisContainer.appendChild(chartCard);
        }
    }
    
    logPriorityDecision('system', 'info', 'RENDER_COCKPIT_COMPLETE', { mode: priority.mode });
}

/**
 * Hook appelé quand le cockpit est prêt
 * Permet d'ajouter des comportements sans modifier buildCockpit
 * @param {Object} data - { criticalModules, tensionModules, normalModules }
 */
function onCockpitReady(data) {
    // Hook pour extensions futures
    // Exemple : analytics, notifications, auto-refresh
    console.log('Cockpit ready:', {
        displayMode: data.displayMode,
        primaryModule: data.primaryModule?.name || null,
        visibleCount: data.visibleModules?.length || 0,
        hiddenCount: data.hiddenCount || 0
    });
}

/**
 * Afficher/masquer une zone du cockpit
 * @param {string} zoneId - ID de la zone (zoneCritical, zoneTension, zoneNormal, zoneAnalysis)
 * @param {boolean} visible - true pour afficher, false pour masquer
 */
function toggleCockpitZone(zoneId, visible) {
    const zone = document.getElementById(zoneId);
    if (zone) {
        zone.style.display = visible ? 'block' : 'none';
    }
}

/**
 * Obtenir l'état actuel du cockpit
 * @returns {Object} État des zones et modules
 */
function getCockpitState() {
    return {
        zones: {
            critical: document.getElementById('zoneCritical')?.style.display !== 'none',
            tension: document.getElementById('zoneTension')?.style.display !== 'none',
            normal: document.getElementById('zoneNormal')?.style.display !== 'none',
            analysis: document.getElementById('zoneAnalysis')?.style.display !== 'none'
        }
    };
}

// =============================================
// MODULES COCKPIT (structure extensible)
// =============================================

/**
 * Module Trésorerie
 * Utilise red_triggered du backend pour déterminer l'état
 * Si workflow complété, passe en 🟢 même si red_triggered = true
 */
function buildTreasuryModule(data, isWorkflowCompleted = false) {
    let priority = 2; // 🟢 par défaut
    let status = '🟢';
    let decisionId = null;
    
    // Gérer les erreurs API (objet avec .error)
    if (data && data.error) {
        // Erreur API : rester en zone normale (🟢) mais afficher l'erreur
        return {
            id: 'treasury',
            name: 'Trésorerie',
            priority: 2,
            status: '⚪',
            data,
            decisionId: null,
            createCard: () => createTreasuryCard(data, '⚪', null),
            criticalMessage: null
        };
    }
    
    if (data) {
        // Utiliser red_triggered du backend (source de vérité)
        // MAIS si workflow complété, considérer comme traité (🟢)
        if (data.red_triggered && !isWorkflowCompleted) {
            priority = 0; // 🔴
            status = '🔴';
            decisionId = data.id; // L'ID pour le rapport RED
        } else if (data.red_triggered && isWorkflowCompleted) {
            // RED validé → retour en normal avec indicateur
            priority = 2; // 🟢
            status = '✅'; // Indicateur validation complète
        } else if (data.opening_balance < 10000) {
            priority = 1; // 🟠
            status = '🟠';
        }
    }
    
    return {
        id: 'treasury',
        name: 'Trésorerie',
        priority,
        status,
        data,
        decisionId,
        createCard: () => createTreasuryCard(data, status, decisionId),
        criticalMessage: data?.red_triggered && !isWorkflowCompleted
            ? `Déficit prévu : ${formatCurrency(data.forecast_balance)}` 
            : null
    };
}

/**
 * Module Comptabilité
 */
function buildAccountingModule(data) {
    // Déterminer la priorité basée sur le statut
    let priority = 2; // 🟢 par défaut
    let status = '🟢';
    
    // Gestion des erreurs
    if (data && data.error) {
        return {
            id: 'accounting',
            name: 'Comptabilité',
            priority: 2,
            status: '⚪',
            data,
            createCard: () => createAccountingCard(data, '⚪'),
            criticalMessage: null
        };
    }
    
    // Utiliser le statut fourni par l'API
    if (data && data.status) {
        status = data.status; // '🟢' ou '🟠'
        priority = status === '🟠' ? 1 : 2;
    }
    
    return {
        id: 'accounting',
        name: 'Comptabilité',
        priority,
        status,
        data,
        createCard: () => createAccountingCard(data, status),
        criticalMessage: status === '🟠' ? '⚠️ Audit comptable recommandé' : null
    };
}

/**
 * Module Fiscalité
 * Priorité: 🔴 Fiscal < 🔴 Financier mais > 🔴 Social
 * Domaine: Fiscal (priorité 2)
 */
function buildTaxModule(data) {
    // Gérer les erreurs
    if (!data || data.error) {
        return {
            id: 'tax',
            name: 'Fiscalité',
            priority: 2, // Pas critique si erreur
            status: '🟢',
            data: data || {},
            createCard: () => createTaxCard(data, '🟢'),
            criticalMessage: null
        };
    }
    
    const status = data.status || '🟢';
    
    // Déterminer la priorité
    let priority = 2; // Normal par défaut
    if (status === '🔴') {
        priority = 0; // Critique : retard fiscal
    } else if (status === '🟠') {
        priority = 1; // Tension : échéance proche
    }
    
    // Message critique si retard
    let criticalMessage = null;
    if (status === '🔴') {
        const deadlineType = data.next_deadline_type || 'fiscale';
        criticalMessage = `⚠️ RETARD DÉCLARATION ${deadlineType.toUpperCase()} - Conformité fiscale compromise. Risques : pénalités, contrôle fiscal, responsabilité dirigeant.`;
    }
    
    return {
        id: 'tax',
        name: 'Fiscalité',
        priority: priority,
        status: status,
        data: data,
        createCard: () => createTaxCard(data, status),
        criticalMessage: criticalMessage
    };
}

/**
 * Module RH
 * Priorité: 🔴 RH < 🔴 Financier et Fiscal mais > Comptabilité normale
 * Domaine: Social (priorité 3)
 */
function buildHRModule(data) {
    // Gérer les erreurs
    if (!data || data.error) {
        return {
            id: 'hr',
            name: 'RH',
            priority: 2, // Pas critique si erreur
            status: '🟢',
            data: data || {},
            createCard: () => createHRCard(data, '🟢'),
            criticalMessage: null
        };
    }
    
    const status = data.status || '🟢';
    
    // Déterminer la priorité
    let priority = 2; // Normal par défaut
    if (status === '🔴') {
        priority = 0; // Critique : risque social
    } else if (status === '🟠') {
        priority = 1; // Tension : paie à valider
    }
    
    // Message critique si risque social
    let criticalMessage = null;
    if (status === '🔴') {
        if (data.payroll_status === 'En retard') {
            criticalMessage = `⚠️ PAIE EN RETARD - Risque social majeur. Effectif: ${data.headcount}. Actions : valider et verser la paie immédiatement, vérifier DSN.`;
        } else if (data.dsn_status === 'En retard') {
            criticalMessage = `⚠️ DSN EN RETARD - Non-conformité sociale. Effectif: ${data.headcount}. Risques : pénalités URSSAF, contrôle social.`;
        } else {
            criticalMessage = `⚠️ ALERTE RH CRITIQUE - Effectif: ${data.headcount}. Situation sociale à traiter en urgence.`;
        }
    }
    
    return {
        id: 'hr',
        name: 'RH',
        priority: priority,
        status: status,
        data: data,
        createCard: () => createHRCard(data, status),
        criticalMessage: criticalMessage
    };
}

/**
 * Module Juridique
 * Priorité: 🔴 Juridique < 🔴 Financier mais > 🔴 Fiscal/RH
 * Domaine: Juridique (priorité 1)
 */
function buildLegalModule(data) {
    // Gérer les erreurs
    if (!data || data.error) {
        return {
            id: 'legal',
            name: 'Juridique',
            priority: 2, // Pas critique si erreur
            status: '🟢',
            data: data || {},
            createCard: () => createLegalCard(data, '🟢'),
            criticalMessage: null
        };
    }
    
    const status = data.status || '🟢';
    
    // Déterminer la priorité
    let priority = 2; // Normal par défaut
    if (status === '🔴') {
        priority = 0; // Critique : responsabilité dirigeant
    } else if (status === '🟠') {
        priority = 1; // Tension : élément à surveiller
    }
    
    // Message critique si non-conformité
    let criticalMessage = null;
    if (status === '🔴') {
        if (data.statutory_compliance === 'Non conforme') {
            criticalMessage = `⚠️ NON-CONFORMITÉ STATUTAIRE - Responsabilité dirigeant engagée. Forme juridique: ${data.legal_form || 'N/A'}. Action immédiate : révision statutaire et mise en conformité.`;
        } else if (data.identified_risks > 0) {
            criticalMessage = `⚠️ RISQUES JURIDIQUES IDENTIFIÉS (${data.identified_risks}) - Contentieux ou non-conformité réglementaire. Consultation juridique urgente requise.`;
        } else {
            criticalMessage = `⚠️ ALERTE JURIDIQUE CRITIQUE - Situation juridique à traiter en urgence. Responsabilité dirigeant.`;
        }
    }
    
    return {
        id: 'legal',
        name: 'Juridique',
        priority: priority,
        status: status,
        data: data,
        createCard: () => createLegalCard(data, status),
        criticalMessage: criticalMessage
    };
}

// =============================================
// CRÉATION DES CARTES (via templates)
// =============================================

/**
 * VUE CRITIQUE COCKPIT DIRIGEANT
 * Affichage exclusif et immersif pour décisions critiques
 * Le dirigeant comprend le risque en 3 secondes
 * 
 * @param {Array} criticalModules - Modules avec priority === 0
 * @returns {HTMLElement} Vue critique complète
 */
function createCockpitCriticalView(criticalModules) {
    if (!criticalModules.length) return null;
    
    // Trier par domaine (Financier en premier)
    criticalModules.sort((a, b) => a.domainPriority - b.domainPriority);
    
    // Module principal = premier critique (le plus prioritaire)
    const mainModule = criticalModules[0];
    
    // Créer le container de vue critique
    const view = document.createElement('div');
    view.className = 'cockpit-critical-view';
    
    // Générer la liste des risques
    const risksList = criticalModules
        .filter(m => m.criticalMessage)
        .map(m => `
            <div class="risk-item">
                <span class="risk-domain">${m.domain}</span>
                <span class="risk-name">${m.name}</span>
                <span class="risk-message">${m.criticalMessage}</span>
            </div>
        `).join('');
    
    // Données du module principal pour affichage détaillé
    const mainData = mainModule.data || {};
    const deficit = mainData.forecast_balance ? Math.abs(mainData.forecast_balance) : 0;
    
    view.innerHTML = `
        <!-- En-tête critique - Identification immédiate du risque -->
        <div class="critical-header">
            <div class="critical-icon">🔴</div>
            <div class="critical-title">
                <h2>Situation Critique</h2>
                <p class="critical-domain">${mainModule.domain} - ${mainModule.name}</p>
            </div>
            <div class="critical-timestamp">
                ${new Date().toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
            </div>
        </div>
        
        <!-- Métrique principale - Chiffre clé en 3 secondes -->
        <div class="critical-metric">
            <div class="metric-value-large">${formatCurrency(deficit)}</div>
            <div class="metric-label-large">Déficit anticipé J+30</div>
        </div>
        
        <!-- Détail des données -->
        <div class="critical-details">
            <div class="detail-item">
                <span class="detail-label">Solde actuel</span>
                <span class="detail-value">${formatCurrency(mainData.opening_balance || 0)}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Entrées prévues</span>
                <span class="detail-value positive">+${formatCurrency(mainData.inflows || 0)}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Sorties prévues</span>
                <span class="detail-value negative">-${formatCurrency(mainData.outflows || 0)}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Prévision</span>
                <span class="detail-value critical">${formatCurrency(mainData.forecast_balance || 0)}</span>
            </div>
        </div>
        
        <!-- Autres risques critiques (si plusieurs) -->
        ${criticalModules.length > 1 ? `
            <div class="other-risks">
                <h3>Autres points critiques</h3>
                <div class="risks-list">${risksList}</div>
            </div>
        ` : ''}
        
        <!-- Actions - Accès rapport RED uniquement (pas d'action risquée) -->
        <div class="critical-actions">
            <button class="btn-critical-primary" onclick="examineRedDecision('${mainModule.id}', ${mainModule.data?.id || 0})">
                📊 Consulter le rapport RED
            </button>
            <button class="btn-critical-secondary" onclick="window.print()">
                🖨️ Imprimer
            </button>
        </div>
        
        <!-- Message de guidance -->
        <div class="critical-guidance">
            <p>⚠️ Aucune autre information n'est affichée. Traitez cette situation en priorité.</p>
        </div>
    `;
    
    return view;
}

/**
 * Carte Alerte Critique (liste des problèmes urgents) - Legacy
 */
function createCriticalCard(criticalModules) {
    const template = document.getElementById('criticalDecisionTemplate');
    if (!template || !criticalModules.length) return null;
    
    const card = template.content.cloneNode(true);
    
    // Générer la liste des alertes
    const alertList = criticalModules
        .filter(m => m.criticalMessage)
        .map(m => `<li><strong>${m.name}</strong> : ${m.criticalMessage}</li>`)
        .join('');
    
    card.querySelector('.alert-title').textContent = 
        `${criticalModules.length} point${criticalModules.length > 1 ? 's' : ''} critique${criticalModules.length > 1 ? 's' : ''}`;
    card.querySelector('.alert-description').innerHTML = 
        `<ul class="alert-list">${alertList}</ul>`;
    
    const actions = card.querySelector('.card-actions');
    actions.innerHTML = `
        <a href="#decisions" class="btn-alert" onclick="showDecisionOptions()">Accéder aux décisions</a>
        <button class="btn-secondary" onclick="alert('Export en cours...')">Exporter le rapport</button>
    `;
    
    return card;
}

/**
 * Carte Trésorerie (accepte status et decisionId en paramètre)
 * Si red_triggered, affiche le bouton "Examiner la décision"
 */
/**
 * Créer une carte Comptabilité
 */
function createAccountingCard(data, status) {
    const template = document.getElementById('accountingCardTemplate');
    if (!template) return null;
    
    const card = template.content.cloneNode(true);
    const cardEl = card.querySelector('.card');
    
    // Appliquer classes visuelles selon statut
    if (status === '🟠') cardEl.classList.add('card-warning');
    if (status === '🟢') cardEl.classList.add('card-success');
    
    card.querySelector('.status-indicator').textContent = status || '⚪';
    
    // Gérer les erreurs API
    if (data && data.error) {
        card.querySelector('.entries-status').textContent = 'Indisponible';
        const metricsEl = card.querySelectorAll('.metric-small-value');
        metricsEl.forEach(el => el.textContent = '—');
        
        const errorDiv = card.querySelector('.card-error');
        if (errorDiv) {
            errorDiv.style.display = 'block';
            
            if (data.error === 'api_unavailable') {
                errorDiv.textContent = '⚠️ Service comptabilité indisponible';
            } else if (data.error === 'access_denied') {
                errorDiv.textContent = '🔒 Accès refusé aux données comptables';
            } else {
                errorDiv.textContent = data.message || 'Erreur inconnue';
            }
        }
        return card;
    }
    
    // Données valides
    if (data && !data.error) {
        // Afficher l'état des écritures
        const statusText = data.entries_up_to_date ? '✓ À jour' : '⚠️ Décalage détecté';
        card.querySelector('.entries-status').textContent = statusText;
        
        // Afficher les écritures en attente
        const metricsEl = card.querySelectorAll('.metric-small-value');
        metricsEl[0].textContent = `${data.pending_entries_count} écritures`;
        
        // Afficher la dernière clôture
        if (data.last_closure_date) {
            metricsEl[1].textContent = data.days_since_closure ? `${data.days_since_closure}j` : 'Récente';
            if (data.days_since_closure && data.days_since_closure > 30) {
                metricsEl[1].classList.add('negative');
            }
        } else {
            metricsEl[1].textContent = 'N/A';
        }
    }
    
    return card;
}

function createTreasuryCard(data, status, decisionId) {
    const template = document.getElementById('treasuryCardTemplate');
    if (!template) return null;
    
    const card = template.content.cloneNode(true);
    const cardEl = card.querySelector('.card');
    
    // Appliquer classes visuelles selon priorité
    if (status === '🔴') cardEl.classList.add('card-critical');
    if (status === '🟠') cardEl.classList.add('card-warning');
    
    card.querySelector('.status-indicator').textContent = status || '⚪';
    
    // Gérer les erreurs API
    if (data && data.error) {
        card.querySelector('.metric-value').textContent = '—';
        card.querySelectorAll('.metric-small-value')[0].textContent = '—';
        card.querySelectorAll('.metric-small-value')[1].textContent = '—';
        
        const errorDiv = card.querySelector('.card-error');
        if (errorDiv) {
            errorDiv.style.display = 'block';
            
            // Messages spécifiques selon le type d'erreur
            if (data.error === 'api_unavailable') {
                errorDiv.textContent = '⚠️ Service indisponible - L\'API Trésorerie ne répond pas. Réessayez dans quelques instants.';
            } else if (data.error === 'access_denied') {
                errorDiv.textContent = '🔒 Accès refusé - Vous n\'avez pas les droits pour consulter la trésorerie.';
            } else {
                errorDiv.textContent = data.message || 'Erreur inconnue';
            }
        }
        return card;
    }
    
    // Données valides présentes
    if (data && !data.error) {
        card.querySelector('.metric-value').textContent = formatCurrency(data.opening_balance);
        
        const forecastEl = card.querySelectorAll('.metric-small-value')[0];
        forecastEl.textContent = formatCurrency(data.forecast_balance);
        forecastEl.classList.add(data.forecast_balance < 0 ? 'negative' : 'positive');
        
        card.querySelectorAll('.metric-small-value')[1].textContent = 'Aujourd\'hui';
        
        // Si RED triggered, afficher le bouton d'examen
        const actionsDiv = card.querySelector('.card-actions');
        if (data.red_triggered && actionsDiv) {
            actionsDiv.style.display = 'block';
            actionsDiv.innerHTML = `
                <button class="btn-alert" onclick="examineRedDecision('treasury', ${data.id})">
                    Examiner la décision
                </button>
            `;
        }
    } else {
        // Aucune donnée (null)
        card.querySelector('.metric-value').textContent = '—';
        card.querySelectorAll('.metric-small-value')[0].textContent = '—';
        card.querySelectorAll('.metric-small-value')[1].textContent = '—';
        
        const errorDiv = card.querySelector('.card-error');
        if (errorDiv) {
            errorDiv.style.display = 'block';
            errorDiv.textContent = 'Aucune donnée de trésorerie disponible';
        }
    }
    
    return card;
}

/**
 * Carte Comptabilité (accepte status en paramètre)
 */
function createAccountingCard(data, status) {
    const template = document.getElementById('accountingCardTemplate');
    if (!template) return null;
    
    const card = template.content.cloneNode(true);
    const cardEl = card.querySelector('.card');
    
    // Appliquer les classes de statut
    if (status === '🔴') cardEl.classList.add('card-critical');
    if (status === '🟠') cardEl.classList.add('card-warning');
    if (status === '🟢') cardEl.classList.add('card-success');
    
    // Status indicator
    const statusIndicator = card.querySelector('.status-indicator');
    if (statusIndicator) statusIndicator.textContent = status || '🟢';
    
    // État des écritures
    const entriesStatus = card.querySelector('.entries-status');
    if (entriesStatus) {
        entriesStatus.textContent = data?.entries_up_to_date ? 'À jour' : 'En retard';
    }
    
    // Métriques dans l'ordre du template
    const smallValues = card.querySelectorAll('.metric-small-value');
    if (smallValues[0]) {
        smallValues[0].textContent = data?.pending_entries_count || '0';
    }
    if (smallValues[1]) {
        const lastClosureDate = data?.last_closure_date || 'Jamais';
        smallValues[1].textContent = lastClosureDate;
    }
    
    return card;
}

/**
 * Carte Fiscalité (accepte data et status en paramètres)
 */
function createTaxCard(data, status) {
    const template = document.getElementById('taxCardTemplate');
    if (!template) return null;
    
    const card = template.content.cloneNode(true);
    const cardEl = card.querySelector('.card');
    
    // Appliquer les classes de statut
    if (status === '🔴') cardEl.classList.add('card-critical');
    if (status === '🟠') cardEl.classList.add('card-warning');
    if (status === '🟢') cardEl.classList.add('card-success');
    
    // Status indicator
    const statusIndicator = card.querySelector('.status-indicator');
    if (statusIndicator) statusIndicator.textContent = status || '🟢';
    
    // Gérer les erreurs
    if (data?.error) {
        const errorDiv = card.querySelector('.card-error');
        if (errorDiv) {
            errorDiv.style.display = 'block';
            if (data.error === 'access_denied') {
                errorDiv.textContent = 'Accès refusé aux données fiscales';
            } else if (data.error === 'api_unavailable') {
                errorDiv.textContent = 'Service fiscal temporairement indisponible';
            } else {
                errorDiv.textContent = 'Erreur lors du chargement des données fiscales';
            }
        }
        return card;
    }
    
    // Prochaine échéance (valeur principale)
    const metricValue = card.querySelector('.metric-value');
    const metricLabel = card.querySelector('.metric-label');
    if (metricValue && data?.next_deadline) {
        const deadline = new Date(data.next_deadline);
        metricValue.textContent = deadline.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    } else if (metricValue) {
        metricValue.textContent = 'Non définie';
    }
    
    if (metricLabel && data?.next_deadline_type) {
        metricLabel.textContent = `Prochaine échéance ${data.next_deadline_type}`;
    } else if (metricLabel) {
        metricLabel.textContent = 'Prochaine échéance';
    }
    
    // Statut TVA
    const vatStatus = card.querySelector('.tax-vat-status');
    if (vatStatus) {
        vatStatus.textContent = data?.vat_status || 'N/A';
    }
    
    // Statut IS
    const corporateStatus = card.querySelector('.tax-corporate-status');
    if (corporateStatus) {
        corporateStatus.textContent = data?.corporate_tax_status || 'N/A';
    }
    
    return card;
}

/**
 * Carte RH (accepte data et status en paramètres)
 */
function createHRCard(data, status) {
    const template = document.getElementById('hrCardTemplate');
    if (!template) return null;
    
    const card = template.content.cloneNode(true);
    const cardEl = card.querySelector('.card');
    
    // Appliquer les classes de statut
    if (status === '🔴') cardEl.classList.add('card-critical');
    if (status === '🟠') cardEl.classList.add('card-warning');
    if (status === '🟢') cardEl.classList.add('card-success');
    
    // Status indicator
    const statusIndicator = card.querySelector('.status-indicator');
    if (statusIndicator) statusIndicator.textContent = status || '🟢';
    
    // Gérer les erreurs
    if (data?.error) {
        const errorDiv = card.querySelector('.card-error');
        if (errorDiv) {
            errorDiv.style.display = 'block';
            if (data.error === 'access_denied') {
                errorDiv.textContent = 'Accès refusé aux données RH';
            } else if (data.error === 'api_unavailable') {
                errorDiv.textContent = 'Service RH temporairement indisponible';
            } else {
                errorDiv.textContent = 'Erreur lors du chargement des données RH';
            }
        }
        return card;
    }
    
    // Effectif (valeur principale)
    const metricValue = card.querySelector('.metric-value');
    if (metricValue) {
        metricValue.textContent = data?.headcount?.toString() || '—';
    }
    
    // Statut paie
    const payrollStatus = card.querySelector('.hr-payroll-status');
    if (payrollStatus) {
        payrollStatus.textContent = data?.payroll_status || 'N/A';
    }
    
    // Absences critiques
    const absencesCount = card.querySelector('.hr-absences-count');
    if (absencesCount) {
        const count = data?.critical_absences || 0;
        absencesCount.textContent = count === 0 ? 'Aucune' : count.toString();
    }
    
    return card;
}

/**
 * Carte Juridique (accepte data et status en paramètres)
 */
function createLegalCard(data, status) {
    const template = document.getElementById('legalCardTemplate');
    if (!template) return null;
    
    const card = template.content.cloneNode(true);
    const cardEl = card.querySelector('.card');
    
    // Appliquer les classes de statut
    if (status === '🔴') cardEl.classList.add('card-critical');
    if (status === '🟠') cardEl.classList.add('card-warning');
    if (status === '🟢') cardEl.classList.add('card-success');
    
    // Status indicator
    const statusIndicator = card.querySelector('.status-indicator');
    if (statusIndicator) statusIndicator.textContent = status || '🟢';
    
    // Gérer les erreurs
    if (data?.error) {
        const errorDiv = card.querySelector('.card-error');
        if (errorDiv) {
            errorDiv.style.display = 'block';
            if (data.error === 'access_denied') {
                errorDiv.textContent = 'Accès refusé aux données juridiques';
            } else if (data.error === 'api_unavailable') {
                errorDiv.textContent = 'Service juridique temporairement indisponible';
            } else {
                errorDiv.textContent = 'Erreur lors du chargement des données juridiques';
            }
        }
        return card;
    }
    
    // Conformité statutaire (valeur principale)
    const metricValue = card.querySelector('.metric-value');
    if (metricValue) {
        metricValue.textContent = data?.statutory_compliance || 'N/A';
    }
    
    // Contrats sensibles
    const contractsCount = card.querySelector('.legal-contracts-count');
    if (contractsCount) {
        const count = data?.sensitive_contracts_count || 0;
        const expiring = data?.expiring_contracts_soon || 0;
        contractsCount.textContent = expiring > 0 ? `${count} (${expiring} expire)` : count.toString();
    }
    
    // Risques identifiés
    const risksCount = card.querySelector('.legal-risks-count');
    if (risksCount) {
        const count = data?.identified_risks || 0;
        risksCount.textContent = count === 0 ? 'Aucun' : count.toString();
    }
    
    return card;
}

/**
 * Carte Graphique
 */
function createChartCard() {
    const template = document.getElementById('chartCardTemplate');
    if (!template) return null;
    
    const card = template.content.cloneNode(true);
    
    // Le canvas sera initialisé après insertion dans le DOM
    setTimeout(() => {
        const canvas = document.getElementById('evolutionChart');
        if (canvas) {
            drawSimpleChart(canvas);
        }
    }, 100);
    
    return card;
}

// =============================================
// CHARGEMENT DES DONNÉES
// =============================================

/**
 * Charger les données comptables
 * Gère les erreurs : API indisponible, pas de données, accès refusé
 */
async function loadAccountingData() {
    try {
        const response = await authenticatedFetch(`${API_BASE}/accounting/status`);
        
        // Accès refusé
        if (response.status === 401 || response.status === 403) {
            console.error('Comptabilité: Accès refusé');
            return { error: 'access_denied', message: 'Accès refusé' };
        }
        
        // Erreur API
        if (!response.ok) {
            return { error: 'api_error', message: 'Erreur serveur' };
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('Erreur comptabilité (API indisponible):', error);
        return { error: 'api_unavailable', message: 'Service indisponible' };
    }
}

/**
 * Charger les données de trésorerie
 * Gère les erreurs : API indisponible, pas de données, accès refusé
 */
async function loadTreasuryData() {
    try {
        const response = await authenticatedFetch(`${API_BASE}/treasury/latest`);
        
        // Accès refusé
        if (response.status === 401 || response.status === 403) {
            console.error('Trésorerie: Accès refusé');
            return { error: 'access_denied', message: 'Accès refusé' };
        }
        
        // Pas de données (204 ou null)
        if (response.status === 204 || !response.ok) {
            return null;
        }
        
        const data = await response.json();
        
        // Réponse null du backend
        if (data === null) {
            return null;
        }
        
        return data;
        
    } catch (error) {
        console.error('Erreur trésorerie (API indisponible):', error);
        return { error: 'api_unavailable', message: 'Service indisponible' };
    }
}

/**
 * Charger les données du journal
 */
async function loadJournalData() {
    try {
        const response = await authenticatedFetch(`${API_BASE}/journal`);
        if (!response.ok) return { count: 0 };
        const entries = await response.json();
        return { count: entries.length };
    } catch (error) {
        console.error('Erreur journal:', error);
        return { count: 0 };
    }
}

/**
 * Charger les données fiscales
 * Gère les erreurs : API indisponible, pas de données, accès refusé
 */
async function loadTaxData() {
    try {
        const response = await authenticatedFetch(`${API_BASE}/tax/status`);
        
        // Accès refusé
        if (response.status === 401 || response.status === 403) {
            console.error('Fiscalité: Accès refusé');
            return { error: 'access_denied', message: 'Accès refusé' };
        }
        
        // Erreur API
        if (!response.ok) {
            return { error: 'api_error', message: 'Erreur serveur' };
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('Erreur fiscalité (API indisponible):', error);
        return { error: 'api_unavailable', message: 'Service indisponible' };
    }
}

/**
 * Charger les données RH
 * Gère les erreurs : API indisponible, pas de données, accès refusé
 */
async function loadHRData() {
    try {
        const response = await authenticatedFetch(`${API_BASE}/hr/status`);
        
        // Accès refusé
        if (response.status === 401 || response.status === 403) {
            console.error('RH: Accès refusé');
            return { error: 'access_denied', message: 'Accès refusé' };
        }
        
        // Erreur API
        if (!response.ok) {
            return { error: 'api_error', message: 'Erreur serveur' };
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('Erreur RH (API indisponible):', error);
        return { error: 'api_unavailable', message: 'Service indisponible' };
    }
}

/**
 * Charger les données juridiques
 * Gère les erreurs : API indisponible, pas de données, accès refusé
 */
async function loadLegalData() {
    try {
        const response = await authenticatedFetch(`${API_BASE}/legal/status`);
        
        // Accès refusé
        if (response.status === 401 || response.status === 403) {
            console.error('Juridique: Accès refusé');
            return { error: 'access_denied', message: 'Accès refusé' };
        }
        
        // Erreur API
        if (!response.ok) {
            return { error: 'api_error', message: 'Erreur serveur' };
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('Erreur juridique (API indisponible):', error);
        return { error: 'api_unavailable', message: 'Service indisponible' };
    }
}

// =============================================
// GRAPHIQUE SIMPLE (Canvas)
// =============================================

/**
 * Dessiner un graphique simple en courbe
 */
function drawSimpleChart(canvas) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Données exemple
    const data = [12000, 15000, 8500, 11000, 9000, 8500];
    const labels = ['Juil', 'Août', 'Sept', 'Oct', 'Nov', 'Déc'];
    
    const padding = 40;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    
    const maxVal = Math.max(...data) * 1.1;
    const minVal = Math.min(...data) * 0.9;
    
    // Fond
    ctx.fillStyle = '#f8f9fb';
    ctx.fillRect(0, 0, width, height);
    
    // Grille horizontale
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padding + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
    }
    
    // Courbe
    ctx.strokeStyle = '#4a90e2';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    data.forEach((val, i) => {
        const x = padding + (chartWidth / (data.length - 1)) * i;
        const y = padding + chartHeight - ((val - minVal) / (maxVal - minVal)) * chartHeight;
        
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();
    
    // Points
    ctx.fillStyle = '#4a90e2';
    data.forEach((val, i) => {
        const x = padding + (chartWidth / (data.length - 1)) * i;
        const y = padding + chartHeight - ((val - minVal) / (maxVal - minVal)) * chartHeight;
        
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
    });
    
    // Labels X
    ctx.fillStyle = '#6b7280';
    ctx.font = '12px system-ui';
    ctx.textAlign = 'center';
    labels.forEach((label, i) => {
        const x = padding + (chartWidth / (data.length - 1)) * i;
        ctx.fillText(label, x, height - 10);
    });
}

// =============================================
// BULLES D'AIDE CONTEXTUELLES
// =============================================

/**
 * Initialiser les bulles d'aide ⓘ
 */
function initHelpBubbles() {
    const bubble = document.getElementById('helpBubble');
    if (!bubble) return;
    
    document.querySelectorAll('.help-icon').forEach(icon => {
        icon.addEventListener('mouseenter', (e) => {
            const helpText = e.target.getAttribute('data-help');
            if (!helpText) return;
            
            bubble.textContent = helpText;
            bubble.classList.remove('hidden');
            
            const rect = e.target.getBoundingClientRect();
            bubble.setAttribute('data-top', rect.bottom + 8);
            bubble.setAttribute('data-left', rect.left);
            bubble.style.setProperty('--bubble-top', (rect.bottom + 8) + 'px');
            bubble.style.setProperty('--bubble-left', rect.left + 'px');
        });
        
        icon.addEventListener('mouseleave', () => {
            bubble.classList.add('hidden');
        });
    });
}

// =============================================
// UTILITAIRES
// =============================================

/**
 * Formater un montant en euros
 */
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '—';
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR',
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * Afficher les options de décision
 */
function showDecisionOptions() {
    alert('Options de financement :\n\n• Ligne de crédit court terme\n• Affacturage\n• Négociation délais fournisseurs\n• Accélération recouvrement clients');
}

/**
 * Examiner une décision RED - Affiche les détails du déficit
 * Utilise directement les données de trésorerie (red_triggered)
 * @param {string} entityType - Type d'entité (treasury, etc.)
 * @param {number} entityId - ID de l'entité concernée
 */
async function examineRedDecision(entityType, entityId) {
    try {
        // Pour la trésorerie, récupérer les données directement
        if (entityType === 'treasury') {
            const response = await authenticatedFetch(`${API_BASE}/treasury/latest`);
            
            if (!response.ok) {
                alert('Impossible de récupérer les données de trésorerie.');
                return;
            }
            
            const data = await response.json();
            
            if (!data || !data.red_triggered) {
                alert('La trésorerie n\'est pas en état critique.');
                return;
            }
            
            // Afficher le panneau avec les données de trésorerie
            showTreasuryRedPanel(data);
            return;
        }
        
        // Pour les autres types, utiliser l'API decision/status
        const statusResponse = await authenticatedFetch(
            `${API_BASE}/decision/status/${entityType}/${entityId}`
        );
        
        if (!statusResponse.ok) {
            alert('Impossible de récupérer le statut de la décision.');
            return;
        }
        
        const status = await statusResponse.json();
        
        if (!status.is_red) {
            alert('Cette entité n\'est pas en état RED.');
            return;
        }
        
        showRedDecisionPanel(entityType, entityId, status);
        
    } catch (error) {
        console.error('Erreur examination RED:', error);
        alert('Erreur lors de l\'accès à la décision RED.');
    }
}

/**
 * Afficher le panneau de décision RED pour la trésorerie
 * Affiche le déficit et les options de financement avec workflow de validation
 */
async function showTreasuryRedPanel(data) {
    const deficit = Math.abs(data.forecast_balance);
    
    // Récupérer le statut du workflow de validation
    let workflowStatus = null;
    try {
        const statusResponse = await authenticatedFetch(`${API_BASE}/decision/red/status/${data.id}`);
        if (statusResponse.ok) {
            workflowStatus = await statusResponse.json();
        }
    } catch (error) {
        console.error('Erreur récupération workflow:', error);
    }
    
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'redValidationModal';
    
    // Générer le contenu du workflow
    const workflowHtml = workflowStatus ? generateWorkflowSteps(data.id, workflowStatus) : '';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>🔴 Décision RED - Validation requise</h2>
                <button onclick="this.closest('.modal-overlay').remove()" class="btn-close">×</button>
            </div>
            
            <div class="alert-deficit">
                <p class="deficit-title">
                    Déficit anticipé : ${formatCurrency(deficit)}
                </p>
                <div class="deficit-grid">
                    <div>Solde actuel : <strong>${formatCurrency(data.opening_balance)}</strong></div>
                    <div>Prévision J+30 : <strong class="text-danger">${formatCurrency(data.forecast_balance)}</strong></div>
                    <div>Entrées prévues : <strong class="text-success">+${formatCurrency(data.inflows)}</strong></div>
                    <div>Sorties prévues : <strong class="text-danger">-${formatCurrency(data.outflows)}</strong></div>
                </div>
            </div>
            
            <div class="financing-options">
                <p class="options-title">Options de financement :</p>
                <ul class="options-list">
                    <li>Ligne de crédit court terme</li>
                    <li>Affacturage (cession de créances)</li>
                    <li>Négociation délais fournisseurs</li>
                    <li>Accélération recouvrement clients</li>
                </ul>
            </div>
            
            ${workflowHtml}
            
            <div class="modal-actions">
                <button onclick="this.closest('.modal-overlay').remove()" class="btn-secondary">
                    Fermer
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

/**
 * Générer les étapes du workflow de validation RED
 */
function generateWorkflowSteps(decisionId, status) {
    const steps = [
        { id: 'ACKNOWLEDGE', label: '1. Accusé de lecture des risques', endpoint: '/decision/red/acknowledge' },
        { id: 'COMPLETENESS', label: '2. Confirmation de complétude', endpoint: '/decision/red/confirm-completeness' },
        { id: 'FINAL', label: '3. Validation finale', endpoint: '/decision/red/confirm-final' }
    ];
    
    const completedSteps = status.completed_steps || [];
    const isFullyValidated = status.is_fully_validated || false;
    
    let html = '<div class="workflow-validation">';
    html += '<h3 class="workflow-title">Workflow de validation</h3>';
    html += '<div class="workflow-steps">';
    
    steps.forEach((step, index) => {
        const isCompleted = completedSteps.includes(step.id);
        const isPending = !isCompleted && (index === 0 || completedSteps.includes(steps[index - 1].id));
        
        html += `
            <div class="workflow-step ${isCompleted ? 'completed' : ''} ${isPending ? 'pending' : ''}">
                <div class="step-icon">${isCompleted ? '✓' : index + 1}</div>
                <div class="step-content">
                    <p class="step-label">${step.label}</p>
                    ${isPending ? `
                        <button class="btn-primary" onclick="validateRedStep(${decisionId}, '${step.endpoint}', '${step.id}')">
                            Valider cette étape
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    
    if (isFullyValidated) {
        html += `
            <div class="workflow-complete">
                <p>✓ Décision RED entièrement validée</p>
                <button class="btn-success" onclick="viewRedReport(${decisionId})">
                    📊 Consulter le rapport immutable
                </button>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

/**
 * Valider une étape du workflow RED
 */
async function validateRedStep(decisionId, endpoint, stepId) {
    try {
        const response = await authenticatedFetch(`${API_BASE}${endpoint}/${decisionId}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(`Erreur : ${error.detail || 'Validation impossible'}`);
            return;
        }
        
        const result = await response.json();
        alert(`✓ ${result.message}`);
        
        // Récupérer le statut mis à jour
        const statusResponse = await authenticatedFetch(`${API_BASE}/decision/red/status/${decisionId}`);
        if (statusResponse.ok) {
            const updatedStatus = await statusResponse.json();
            
            // Mettre à jour l'affichage du workflow avec le nouveau statut
            const workflowContainer = document.querySelector('.workflow-validation');
            if (workflowContainer) {
                workflowContainer.outerHTML = generateWorkflowSteps(decisionId, updatedStatus);
            }
        }
        
    } catch (error) {
        console.error('Erreur validation:', error);
        alert('Erreur lors de la validation');
    }
}

/**
 * Afficher le rapport RED immutable
 */
async function viewRedReport(decisionId) {
    try {
        const response = await authenticatedFetch(`${API_BASE}/decision/red/report/${decisionId}`);
        
        if (!response.ok) {
            alert('Rapport non accessible. La décision doit être entièrement validée.');
            return;
        }
        
        const report = await response.json();
        
        // Afficher le rapport dans un nouveau modal
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>📊 Rapport RED Immutable</h2>
                    <button onclick="this.closest('.modal-overlay').remove()" class="btn-close">×</button>
                </div>
                <div class="report-content">
                    <p><strong>ID Décision :</strong> ${report.decision_id}</p>
                    <p><strong>Motif :</strong> ${report.decision_reason}</p>
                    <p><strong>Validé le :</strong> ${new Date(report.validated_at).toLocaleString('fr-FR')}</p>
                    <p><strong>Données déclencheurs :</strong></p>
                    <pre>${JSON.stringify(report.trigger_data, null, 2)}</pre>
                </div>
                <div class="modal-actions">
                    <button onclick="this.closest('.modal-overlay').remove()" class="btn-secondary">
                        Fermer
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
    } catch (error) {
        console.error('Erreur consultation rapport:', error);
        alert('Erreur lors de la consultation du rapport');
    }
}

// =============================================
// PAGE TRÉSORERIE DÉDIÉE
// =============================================

/**
 * Initialisation de la page trésorerie dédiée
 */
async function initTreasuryPage() {
    if (!checkAuth()) return;
    
    // Afficher le nom utilisateur
    const userEmail = sessionStorage.getItem('user_email') || 'Utilisateur';
    const userNameEl = document.getElementById('userName');
    if (userNameEl) {
        userNameEl.textContent = userEmail;
    }
    
    // Initialiser les bulles d'aide
    initHelpBubbles();
    
    // Charger et afficher la trésorerie
    await loadAndDisplayTreasury();
}

/**
 * Charger et afficher les données de trésorerie
 */
async function loadAndDisplayTreasury() {
    const container = document.getElementById('treasuryContent');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-state">Chargement des données de trésorerie...</div>';
    
    try {
        const data = await loadTreasuryData();
        
        // Déterminer le statut
        let status = '🟢';
        if (data && data.error) {
            status = '⚪';
        } else if (data && data.red_triggered) {
            status = '🔴';
        } else if (data && data.opening_balance < 10000) {
            status = '🟠';
        }
        
        // Créer la carte
        const card = createTreasuryCard(data, status, data?.id);
        container.innerHTML = '';
        if (card) {
            container.appendChild(card);
        }
        
        // Réinitialiser les bulles d'aide
        initHelpBubbles();
        
    } catch (error) {
        console.error('Erreur chargement trésorerie:', error);
        container.innerHTML = `
            <div class="card card-alert">
                <div class="card-header">
                    <h3 class="card-title">Erreur de chargement</h3>
                    <span class="status-indicator">⚠️</span>
                </div>
                <div class="card-body">
                    <p>${error.message}</p>
                </div>
            </div>
        `;
    }
}

// =============================================
// INITIALISATION
// =============================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialiser le branding (titre d'onglet Azalscore)
    initBranding();

    const page = document.body.dataset.page;

    switch (page) {
        case 'login':
            // Si l'utilisateur est déjà connecté, rediriger vers le cockpit
            const token = sessionStorage.getItem('token');
            if (token) {
                window.location.href = '/dashboard';
                return;
            }
            
            const loginForm = document.getElementById('loginForm');
            if (loginForm) {
                loginForm.addEventListener('submit', handleLogin);
            }
            break;
            
        case 'dashboard':
            initDashboard();
            break;
            
        case 'treasury':
            initTreasuryPage();
            break;
    }
});
