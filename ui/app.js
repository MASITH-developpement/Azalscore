/**
 * AZALS - Application Frontend
 * ERP Premium - Interface décisionnelle
 * 
 * Vanilla JS uniquement - Aucune dépendance externe
 */

// =============================================
// CONFIGURATION
// =============================================

const API_BASE = '';

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
    
    // Construire le cockpit
    await buildCockpit();
}

/**
 * Construction du cockpit dirigeant avec zones segmentées
 * Structure : Zone Critique (🔴) → Zone Tension (🟠) → Zone Normale (🟢) → Zone Analyse
 * Priorisation automatique et affichage conditionnel
 */
async function buildCockpit() {
    // Récupérer les containers de zone
    const zoneCritical = document.getElementById('zoneCritical');
    const zoneTension = document.getElementById('zoneTension');
    const zoneNormal = document.getElementById('zoneNormal');
    const zoneAnalysis = document.getElementById('zoneAnalysis');
    
    const criticalContainer = document.getElementById('criticalAlertContainer');
    const tensionContainer = document.getElementById('tensionCardsContainer');
    const normalContainer = document.getElementById('normalCardsContainer');
    const analysisContainer = document.getElementById('analysisContainer');
    
    // Fallback pour ancienne structure (compatibilité)
    const legacyGrid = document.getElementById('cockpitGrid');
    
    // Afficher le loader
    if (normalContainer) {
        normalContainer.innerHTML = '<div class="loading-state">Chargement des données...</div>';
    } else if (legacyGrid) {
        legacyGrid.innerHTML = '<div class="loading-state">Chargement des données...</div>';
    }
    
    try {
        // Charger les données en parallèle
        const [treasuryData, journalData] = await Promise.all([
            loadTreasuryData(),
            loadJournalData()
        ]);
        
        // Construire les modules avec leur statut
        const modules = [
            buildTreasuryModule(treasuryData),
            buildAccountingModule(journalData),
            buildTaxModule(),
            buildHRModule()
        ];
        
        // Séparer par priorité
        const criticalModules = modules.filter(m => m.priority === 0); // 🔴
        const tensionModules = modules.filter(m => m.priority === 1);  // 🟠
        const normalModules = modules.filter(m => m.priority === 2);   // 🟢
        
        // ============================================
        // ZONE CRITIQUE (🔴) - Alerte dominante unique
        // ============================================
        if (zoneCritical && criticalContainer) {
            criticalContainer.innerHTML = '';
            if (criticalModules.length > 0) {
                // Afficher la zone critique
                zoneCritical.style.display = 'block';
                const alertCard = createCriticalCard(criticalModules);
                if (alertCard) criticalContainer.appendChild(alertCard);
            } else {
                // Masquer si aucun RED
                zoneCritical.style.display = 'none';
            }
        }
        
        // ============================================
        // ZONE TENSION (🟠) - Points d'attention
        // ============================================
        if (zoneTension && tensionContainer) {
            tensionContainer.innerHTML = '';
            if (tensionModules.length > 0) {
                zoneTension.style.display = 'block';
                for (const mod of tensionModules) {
                    const card = mod.createCard();
                    if (card) tensionContainer.appendChild(card);
                }
            } else {
                zoneTension.style.display = 'none';
            }
        }
        
        // ============================================
        // ZONE NORMALE (🟢) - Indicateurs standards
        // ============================================
        if (normalContainer) {
            normalContainer.innerHTML = '';
            
            // Inclure aussi les modules critiques et tension dans leurs cartes
            // (ils ont déjà leur alerte en haut, mais la carte reste visible)
            const allBusinessModules = [...criticalModules, ...tensionModules, ...normalModules];
            
            for (const mod of allBusinessModules) {
                const card = mod.createCard();
                if (card) normalContainer.appendChild(card);
            }
        } else if (legacyGrid) {
            // Fallback ancienne structure
            legacyGrid.innerHTML = '';
            modules.sort((a, b) => a.priority - b.priority);
            
            if (criticalModules.length > 0) {
                const alertCard = createCriticalCard(criticalModules);
                if (alertCard) legacyGrid.appendChild(alertCard);
            }
            
            for (const mod of modules) {
                const card = mod.createCard();
                if (card) legacyGrid.appendChild(card);
            }
        }
        
        // ============================================
        // ZONE ANALYSE - Graphiques
        // ============================================
        if (analysisContainer) {
            analysisContainer.innerHTML = '';
            const chartCard = createChartCard();
            if (chartCard) analysisContainer.appendChild(chartCard);
        } else if (legacyGrid) {
            const chartCard = createChartCard();
            if (chartCard) legacyGrid.appendChild(chartCard);
        }
        
        // Réinitialiser les bulles d'aide
        initHelpBubbles();
        
        // Hook pour extensions futures
        onCockpitReady({ criticalModules, tensionModules, normalModules });
        
    } catch (error) {
        console.error('Erreur cockpit:', error);
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

/**
 * Hook appelé quand le cockpit est prêt
 * Permet d'ajouter des comportements sans modifier buildCockpit
 * @param {Object} data - { criticalModules, tensionModules, normalModules }
 */
function onCockpitReady(data) {
    // Hook pour extensions futures
    // Exemple : analytics, notifications, auto-refresh
    console.log('Cockpit ready:', {
        critical: data.criticalModules.length,
        tension: data.tensionModules.length,
        normal: data.normalModules.length
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
 */
function buildTreasuryModule(data) {
    let priority = 2; // 🟢 par défaut
    let status = '🟢';
    let decisionId = null;
    
    if (data) {
        // Utiliser red_triggered du backend (source de vérité)
        if (data.red_triggered) {
            priority = 0; // 🔴
            status = '🔴';
            decisionId = data.id; // L'ID pour le rapport RED
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
        criticalMessage: data?.red_triggered 
            ? `Déficit prévu : ${formatCurrency(data.forecast_balance)}` 
            : null
    };
}

/**
 * Module Comptabilité
 */
function buildAccountingModule(data) {
    // Placeholder : toujours 🟢 pour l'instant
    return {
        id: 'accounting',
        name: 'Comptabilité',
        priority: 2,
        status: '🟢',
        data,
        createCard: () => createAccountingCard(data, '🟢'),
        criticalMessage: null
    };
}

/**
 * Module Fiscalité
 */
function buildTaxModule() {
    // Placeholder : toujours 🟢 pour l'instant
    return {
        id: 'tax',
        name: 'Fiscalité',
        priority: 2,
        status: '🟢',
        data: { next_deadline: '15 Fév 2026' },
        createCard: () => createTaxCard('🟢'),
        criticalMessage: null
    };
}

/**
 * Module RH
 */
function buildHRModule() {
    // Placeholder : toujours 🟢 pour l'instant
    return {
        id: 'hr',
        name: 'RH',
        priority: 2,
        status: '🟢',
        data: { status: 'À jour' },
        createCard: () => createHRCard('🟢'),
        criticalMessage: null
    };
}

// =============================================
// CRÉATION DES CARTES (via templates)
// =============================================

/**
 * Carte Alerte Critique (liste des problèmes urgents)
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
function createTreasuryCard(data, status, decisionId) {
    const template = document.getElementById('treasuryCardTemplate');
    if (!template) return null;
    
    const card = template.content.cloneNode(true);
    const cardEl = card.querySelector('.card');
    
    // Appliquer classes visuelles selon priorité
    if (status === '🔴') cardEl.classList.add('card-critical');
    if (status === '🟠') cardEl.classList.add('card-warning');
    
    card.querySelector('.status-indicator').textContent = status || '⚪';
    
    if (data) {
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
        card.querySelector('.metric-value').textContent = '—';
        card.querySelectorAll('.metric-small-value')[0].textContent = '—';
        card.querySelectorAll('.metric-small-value')[1].textContent = '—';
        
        // Afficher message "Aucune donnée"
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
    
    if (status === '🔴') cardEl.classList.add('card-critical');
    if (status === '🟠') cardEl.classList.add('card-warning');
    
    card.querySelector('.status-indicator').textContent = status || '🟢';
    card.querySelector('.metric-value').textContent = data?.count || '0';
    card.querySelector('.metric-label').textContent = 'Écritures ce mois';
    
    const smallValues = card.querySelectorAll('.metric-small-value');
    smallValues[0].textContent = 'OK';
    smallValues[1].textContent = 'À jour';
    
    return card;
}

/**
 * Carte Fiscalité (accepte status en paramètre)
 */
function createTaxCard(status) {
    const template = document.getElementById('taxCardTemplate');
    if (!template) return null;
    
    const card = template.content.cloneNode(true);
    const cardEl = card.querySelector('.card');
    
    if (status === '🔴') cardEl.classList.add('card-critical');
    if (status === '🟠') cardEl.classList.add('card-warning');
    
    card.querySelector('.status-indicator').textContent = status || '🟢';
    card.querySelector('.metric-value').textContent = '15 Fév';
    
    const smallValues = card.querySelectorAll('.metric-small-value');
    smallValues[0].textContent = 'À jour';
    smallValues[1].textContent = 'À jour';
    
    return card;
}

/**
 * Carte RH (accepte status en paramètre)
 */
function createHRCard(status) {
    const template = document.getElementById('hrCardTemplate');
    if (!template) return null;
    
    const card = template.content.cloneNode(true);
    const cardEl = card.querySelector('.card');
    
    if (status === '🔴') cardEl.classList.add('card-critical');
    if (status === '🟠') cardEl.classList.add('card-warning');
    
    card.querySelector('.status-indicator').textContent = status || '🟢';
    card.querySelector('.metric-value').textContent = '—';
    
    const smallValues = card.querySelectorAll('.metric-small-value');
    smallValues[0].textContent = 'À jour';
    smallValues[1].textContent = '0';
    
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
            bubble.style.top = (rect.bottom + 8) + 'px';
            bubble.style.left = rect.left + 'px';
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
 * Affiche le déficit et les options de financement
 */
function showTreasuryRedPanel(data) {
    const deficit = Math.abs(data.forecast_balance);
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content" style="max-width:520px;background:#1a1f2e;border-radius:0.75rem;padding:1.5rem;box-shadow:0 25px 50px -12px rgba(0,0,0,0.6);border:1px solid #2d3548;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
                <h2 style="margin:0;color:#f1f5f9;font-size:1.25rem;">⚠ Alerte Trésorerie</h2>
                <button onclick="this.closest('.modal-overlay').remove()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:#64748b;">×</button>
            </div>
            
            <div style="margin-bottom:1.25rem;padding:1rem;background:#2a1215;border-radius:0.5rem;border-left:4px solid #7f1d1d;">
                <p style="margin:0 0 0.75rem 0;color:#fecaca;font-weight:600;font-size:1.1rem;">
                    Déficit anticipé : ${formatCurrency(deficit)}
                </p>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;font-size:0.875rem;color:#94a3b8;">
                    <div>Solde actuel : <strong style="color:#e2e8f0">${formatCurrency(data.opening_balance)}</strong></div>
                    <div>Prévision J+30 : <strong style="color:#dc2626">${formatCurrency(data.forecast_balance)}</strong></div>
                    <div>Entrées prévues : <strong style="color:#4ade80">+${formatCurrency(data.inflows)}</strong></div>
                    <div>Sorties prévues : <strong style="color:#dc2626">-${formatCurrency(data.outflows)}</strong></div>
                </div>
            </div>
            
            <div style="margin-bottom:1.25rem;">
                <p style="margin:0 0 0.75rem 0;color:#e2e8f0;font-weight:500;">Options de financement :</p>
                <ul style="margin:0;padding-left:1.25rem;color:#94a3b8;font-size:0.875rem;line-height:1.8;">
                    <li>Ligne de crédit court terme</li>
                    <li>Affacturage (cession de créances)</li>
                    <li>Négociation délais fournisseurs</li>
                    <li>Accélération recouvrement clients</li>
                </ul>
            </div>
            
            <div style="display:flex;gap:0.75rem;">
                <button onclick="alert('Contact expert-comptable recommandé pour mise en place.')" style="flex:1;padding:0.75rem;background:#7f1d1d;color:#fecaca;border:none;border-radius:0.5rem;cursor:pointer;font-weight:500;">
                    Contacter un expert
                </button>
                <button onclick="this.closest('.modal-overlay').remove()" style="flex:1;padding:0.75rem;background:#334155;color:#e2e8f0;border:none;border-radius:0.5rem;cursor:pointer;">
                    Fermer
                </button>
            </div>
        </div>
    `;
    modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.85);display:flex;align-items:center;justify-content:center;z-index:1000;';
    document.body.appendChild(modal);
}

// =============================================
// INITIALISATION
// =============================================

document.addEventListener('DOMContentLoaded', () => {
    const page = document.body.dataset.page;
    
    switch (page) {
        case 'login':
            const loginForm = document.getElementById('loginForm');
            if (loginForm) {
                loginForm.addEventListener('submit', handleLogin);
            }
            break;
            
        case 'dashboard':
            initDashboard();
            break;
    }
});
