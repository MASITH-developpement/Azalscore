/**
 * AZALS - Application JavaScript
 * Gestion des interactions, bulles d'aide, et appels API
 */

// ==================== CONFIGURATION API ====================

const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000'
    : window.location.origin;

// ==================== GESTION DE L'AUTHENTIFICATION ====================

/**
 * Récupère le token JWT depuis sessionStorage
 */
function getToken() {
    return sessionStorage.getItem('azals_token');
}

/**
 * Récupère le tenant ID depuis sessionStorage
 */
function getTenantId() {
    return sessionStorage.getItem('azals_tenant_id');
}

/**
 * Stocke les informations d'authentification
 */
function setAuth(token, tenantId, userEmail) {
    sessionStorage.setItem('azals_token', token);
    sessionStorage.setItem('azals_tenant_id', tenantId);
    sessionStorage.setItem('azals_user_email', userEmail);
}

/**
 * Supprime les informations d'authentification
 */
function clearAuth() {
    sessionStorage.removeItem('azals_token');
    sessionStorage.removeItem('azals_tenant_id');
    sessionStorage.removeItem('azals_user_email');
}

/**
 * Vérifie si l'utilisateur est authentifié
 */
function isAuthenticated() {
    return !!(getToken() && getTenantId());
}

/**
 * Déconnexion
 */
function logout() {
    clearAuth();
    window.location.href = '/';
}

/**
 * Vérifie l'authentification au chargement d'une page protégée
 */
function checkAuth() {
    if (document.body.dataset.requireAuth === 'true' && !isAuthenticated()) {
        window.location.href = '/';
        return false;
    }
    return true;
}

/**
 * Fetch avec headers d'authentification automatiques
 */
async function authenticatedFetch(url, options = {}) {
    const token = getToken();
    const tenantId = getTenantId();
    
    if (!token || !tenantId) {
        throw new Error('Non authentifié');
    }
    
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': tenantId,
        ...options.headers
    };
    
    const response = await fetch(url, {
        ...options,
        headers
    });
    
    if (response.status === 401) {
        clearAuth();
        window.location.href = '/';
        throw new Error('Session expirée');
    }
    
    return response;
}

// ==================== GESTION DES BULLES D'AIDE ====================

/**
 * Affiche une bulle d'aide contextuelle au survol des icônes ⓘ
 */
function initHelpBubbles() {
    const helpIcons = document.querySelectorAll('.help-icon');
    const helpBubble = document.getElementById('helpBubble');
    
    if (!helpBubble) return;
    
    helpIcons.forEach(icon => {
        icon.addEventListener('mouseenter', (e) => {
            const helpText = icon.getAttribute('data-help');
            if (!helpText) return;
            
            // Afficher la bulle
            helpBubble.textContent = helpText;
            helpBubble.classList.remove('hidden');
            
            // Positionner la bulle
            const rect = icon.getBoundingClientRect();
            const bubbleHeight = helpBubble.offsetHeight;
            
            helpBubble.style.left = `${rect.left + window.scrollX}px`;
            helpBubble.style.top = `${rect.top + window.scrollY - bubbleHeight - 8}px`;
        });
        
        icon.addEventListener('mouseleave', () => {
            helpBubble.classList.add('hidden');
        });
    });
}

// ==================== FORMULAIRE DE CONNEXION ====================

/**
 * Gère la soumission du formulaire de connexion
 */
function initLoginForm() {
    const form = document.getElementById('loginForm');
    if (!form) return;
    
    const errorDiv = document.getElementById('errorMessage');
    const submitBtn = document.getElementById('loginButton');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const tenantId = document.getElementById('tenantId').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        
        if (!tenantId || !email || !password) {
            showError('Tous les champs sont requis');
            return;
        }
        
        // Désactiver le bouton
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Connexion...</span>';
        
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Tenant-ID': tenantId
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Échec de la connexion');
            }
            
            const data = await response.json();
            
            // Stocker le token et les infos
            setAuth(data.access_token, tenantId, email);
            
            // Redirection
            window.location.href = '/dashboard';
            
        } catch (error) {
            console.error('Erreur de connexion:', error);
            showError(error.message || 'Erreur de connexion. Vérifiez vos identifiants.');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Se connecter</span><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M7 3L14 10L7 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
        }
    });
    
    function showError(message) {
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }
}

// ==================== APPEL API SANTÉ ====================

/**
 * Vérifie l'état de santé de l'API backend
 * @returns {Promise<Object>} État de santé
 */
async function checkAPIHealth() {
    try {
        // Appel vers l'API backend (adapter l'URL selon l'environnement)
        const apiUrl = window.location.hostname === 'localhost' 
            ? 'http://localhost:8000/health'
            : 'https://azalscore-wlm15q.fly.dev/health';
        
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
        
    } catch (error) {
        console.error('Erreur lors de la vérification de l\'API:', error);
        // Retourner un état dégradé en cas d'erreur
        return {
            status: 'degraded',
            api: false,
            database: false
        };
    }
}

// ==================== GRAPHIQUE CANVAS ====================

/**
 * Dessine un graphique simple sur canvas
 */
function drawEvolutionChart() {
    const canvas = document.getElementById('evolutionChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Données simulées (CA et charges sur 6 mois)
    const months = ['Juil', 'Août', 'Sept', 'Oct', 'Nov', 'Déc'];
    const revenue = [45000, 52000, 48000, 61000, 58000, 67000];
    const expenses = [32000, 35000, 33000, 38000, 36000, 41000];
    
    // Configuration
    const padding = 40;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;
    const maxValue = Math.max(...revenue, ...expenses) * 1.1;
    const stepX = chartWidth / (months.length - 1);
    
    // Fond
    ctx.clearRect(0, 0, width, height);
    
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
    
    // Fonction pour convertir les valeurs en coordonnées Y
    function getY(value) {
        return height - padding - (value / maxValue) * chartHeight;
    }
    
    // Dessiner la courbe des charges (gris)
    ctx.strokeStyle = '#9ca3af';
    ctx.lineWidth = 2;
    ctx.beginPath();
    expenses.forEach((value, index) => {
        const x = padding + index * stepX;
        const y = getY(value);
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();
    
    // Points des charges
    ctx.fillStyle = '#9ca3af';
    expenses.forEach((value, index) => {
        const x = padding + index * stepX;
        const y = getY(value);
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, 2 * Math.PI);
        ctx.fill();
    });
    
    // Dessiner la courbe du CA (bleu)
    ctx.strokeStyle = '#4a90e2';
    ctx.lineWidth = 3;
    ctx.beginPath();
    revenue.forEach((value, index) => {
        const x = padding + index * stepX;
        const y = getY(value);
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();
    
    // Points du CA
    ctx.fillStyle = '#4a90e2';
    revenue.forEach((value, index) => {
        const x = padding + index * stepX;
        const y = getY(value);
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, 2 * Math.PI);
        ctx.fill();
    });
    
    // Labels des mois
    ctx.fillStyle = '#6b7280';
    ctx.font = '12px -apple-system, BlinkMacSystemFont, sans-serif';
    ctx.textAlign = 'center';
    months.forEach((month, index) => {
        const x = padding + index * stepX;
        ctx.fillText(month, x, height - 10);
    });
    
    // Légende
    const legendY = 20;
    
    // CA
    ctx.fillStyle = '#4a90e2';
    ctx.fillRect(padding, legendY, 12, 12);
    ctx.fillStyle = '#1a1f2e';
    ctx.font = '13px -apple-system, BlinkMacSystemFont, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Chiffre d\'affaires', padding + 20, legendY + 10);
    
    // Charges
    ctx.fillStyle = '#9ca3af';
    ctx.fillRect(padding + 150, legendY, 12, 12);
    ctx.fillStyle = '#1a1f2e';
    ctx.fillText('Charges', padding + 170, legendY + 10);
}

// ==================== INITIALISATION ====================

/**
 * Charge les données utilisateur dans le dashboard
 */
async function loadUserData() {
    const userEmail = sessionStorage.getItem('azals_user_email');
    
    if (userEmail) {
        const initials = userEmail.substring(0, 2).toUpperCase();
        document.getElementById('userAvatar').textContent = initials;
        document.getElementById('userName').textContent = userEmail;
        document.getElementById('userRole').textContent = 'Utilisateur';
    }
    
    // Charger les données protégées (exemple)
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/protected/me`);
        if (response.ok) {
            const data = await response.json();
            console.log('Données utilisateur:', data);
        }
    } catch (error) {
        console.error('Erreur chargement utilisateur:', error);
    }
}

// ==================== COCKPIT DIRIGEANT ====================

/**
 * Charge les données de trésorerie réelles
 */
async function loadTreasuryData() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/treasury/latest`);
        
        if (!response.ok) {
            throw new Error('Impossible de charger les données de trésorerie');
        }
        
        const data = await response.json();
        
        if (!data) {
            return {
                module: 'treasury',
                status: 'warning',
                priority: 2,
                data: null,
                error: 'Aucune donnée de trésorerie disponible'
            };
        }
        
        // Déterminer le statut (🟢🟠🔴)
        let status, priority;
        if (data.forecast_balance < 0) {
            status = 'critical';
            priority = 0;
        } else if (data.opening_balance < 10000) {
            status = 'warning';
            priority = 1;
        } else {
            status = 'healthy';
            priority = 2;
        }
        
        return {
            module: 'treasury',
            status: status,
            priority: priority,
            data: data,
            decisionRequired: data.forecast_balance < 0
        };
        
    } catch (error) {
        console.error('Erreur chargement trésorerie:', error);
        return {
            module: 'treasury',
            status: 'error',
            priority: 3,
            data: null,
            error: error.message
        };
    }
}

/**
 * Charge les données de comptabilité (placeholder)
 */
async function loadAccountingData() {
    return {
        module: 'accounting',
        status: 'healthy',
        priority: 2,
        data: {
            pending_entries: 12,
            reconciliation: '87%',
            lettrage: '92%'
        }
    };
}

/**
 * Charge les données fiscales (placeholder)
 */
async function loadTaxData() {
    const nextDeadline = new Date();
    nextDeadline.setDate(nextDeadline.getDate() + 15);
    
    return {
        module: 'tax',
        status: nextDeadline.getDate() < 10 ? 'warning' : 'healthy',
        priority: nextDeadline.getDate() < 10 ? 1 : 2,
        data: {
            next_deadline: nextDeadline.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' }),
            tva: 'À jour',
            is: 'Acompte prévu'
        }
    };
}

/**
 * Charge les données RH (placeholder)
 */
async function loadHRData() {
    return {
        module: 'hr',
        status: 'healthy',
        priority: 2,
        data: {
            headcount: 23,
            payroll: 'En cours',
            leaves: '8 validés'
        }
    };
}

/**
 * Charge la décision critique liée à la trésorerie
 */
async function loadCriticalDecision(treasuryStatus) {
    if (treasuryStatus.status !== 'critical') {
        return null;
    }
    
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/decision/latest?status=RED`);
        
        if (!response.ok) {
            return {
                module: 'decision',
                status: 'critical',
                priority: -1,
                data: {
                    title: 'Trésorerie critique',
                    description: `Solde prévisionnel : ${formatEuros(treasuryStatus.data.forecast_balance)}`,
                    red_report_id: null
                }
            };
        }
        
        const decision = await response.json();
        
        return {
            module: 'decision',
            status: 'critical',
            priority: -1,
            data: {
                title: decision.title || 'Décision critique',
                description: decision.context || `Solde : ${formatEuros(treasuryStatus.data.forecast_balance)}`,
                red_report_id: decision.red_report_id
            }
        };
        
    } catch (error) {
        console.error('Erreur chargement décision critique:', error);
        return null;
    }
}

/**
 * Construit le cockpit dirigeant complet
 */
async function buildCockpit() {
    const grid = document.getElementById('cockpitGrid');
    if (!grid) return;
    
    // Charger toutes les données en parallèle
    const [treasury, accounting, tax, hr] = await Promise.all([
        loadTreasuryData(),
        loadAccountingData(),
        loadTaxData(),
        loadHRData()
    ]);
    
    // Charger les décisions critiques si nécessaire
    let criticalDecision = null;
    if (treasury.decisionRequired) {
        criticalDecision = await loadCriticalDecision(treasury);
    }
    
    // Créer la liste des modules
    const modules = [treasury, accounting, tax, hr];
    if (criticalDecision) {
        modules.push(criticalDecision);
    }
    
    // Trier par priorité (0 = 🔴, 1 = 🟠, 2 = 🟢, -1 = décision critique en premier)
    modules.sort((a, b) => a.priority - b.priority);
    
    // Vider la grille
    grid.innerHTML = '';
    
    // Afficher chaque module
    modules.forEach(module => {
        const card = renderModuleCard(module);
        if (card) {
            grid.appendChild(card);
        }
    });
    
    // Ajouter le graphique à la fin
    const chartCard = renderChartCard();
    grid.appendChild(chartCard);
    
    // Réinitialiser les bulles d'aide
    initHelpBubbles();
    
    // Dessiner le graphique
    setTimeout(drawEvolutionChart, 100);
}

/**
 * Rend une carte de module
 */
function renderModuleCard(module) {
    let template;
    
    switch(module.module) {
        case 'treasury':
            template = document.getElementById('treasuryCardTemplate');
            break;
        case 'accounting':
            template = document.getElementById('accountingCardTemplate');
            break;
        case 'tax':
            template = document.getElementById('taxCardTemplate');
            break;
        case 'hr':
            template = document.getElementById('hrCardTemplate');
            break;
        case 'decision':
            template = document.getElementById('criticalDecisionTemplate');
            break;
        default:
            return null;
    }
    
    const card = template.content.cloneNode(true).querySelector('.card');
    
    // Remplir selon le type
    if (module.module === 'treasury') {
        fillTreasuryCard(card, module);
    } else if (module.module === 'decision') {
        fillDecisionCard(card, module);
    } else {
        fillGenericCard(card, module);
    }
    
    return card;
}

/**
 * Remplit une carte trésorerie
 */
function fillTreasuryCard(card, module) {
    const statusIndicator = card.querySelector('.status-indicator');
    const metricValue = card.querySelector('.metric-value');
    const metricSmallValues = card.querySelectorAll('.metric-small-value');
    const actionsDiv = card.querySelector('.card-actions');
    const errorDiv = card.querySelector('.card-error');
    
    if (module.error) {
        metricValue.textContent = '-- €';
        metricSmallValues[0].textContent = '-- €';
        metricSmallValues[1].textContent = 'Indisponible';
        statusIndicator.textContent = '⚠️';
        errorDiv.textContent = '⚠️ ' + module.error;
        errorDiv.style.display = 'block';
    } else {
        const data = module.data;
        metricValue.textContent = formatEuros(data.opening_balance);
        metricSmallValues[0].textContent = formatEuros(data.forecast_balance);
        metricSmallValues[0].className = `metric-small-value ${data.forecast_balance >= 0 ? 'positive' : 'negative'}`;
        
        const updateDate = new Date(data.created_at);
        metricSmallValues[1].textContent = updateDate.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
        
        if (module.status === 'critical') {
            statusIndicator.textContent = '🔴';
            actionsDiv.innerHTML = '<button class="btn-alert" onclick="examineDecision()">⚠️ Examiner la décision</button>';
            actionsDiv.style.display = 'block';
        } else if (module.status === 'warning') {
            statusIndicator.textContent = '🟠';
        } else {
            statusIndicator.textContent = '🟢';
        }
    }
}

/**
 * Remplit une carte décision critique
 */
function fillDecisionCard(card, module) {
    const title = card.querySelector('.alert-title');
    const description = card.querySelector('.alert-description');
    const actions = card.querySelector('.card-actions');
    
    title.textContent = module.data.title;
    description.textContent = module.data.description;
    
    actions.innerHTML = '';
    if (module.data.red_report_id) {
        actions.innerHTML = `
            <button class="btn-alert" onclick="viewRedReport(${module.data.red_report_id})">Voir le rapport RED</button>
            <button class="btn-ghost" onclick="buildCockpit()">Actualiser</button>
        `;
    } else {
        actions.innerHTML = '<button class="btn-ghost" onclick="buildCockpit()">Actualiser</button>';
    }
}

/**
 * Remplit une carte générique
 */
function fillGenericCard(card, module) {
    const statusIndicator = card.querySelector('.status-indicator');
    const metricValue = card.querySelector('.metric-value');
    const metricSmallValues = card.querySelectorAll('.metric-small-value');
    
    statusIndicator.textContent = module.status === 'critical' ? '🔴' : 
                                  module.status === 'warning' ? '🟠' : '🟢';
    
    if (module.module === 'accounting') {
        metricValue.textContent = module.data.pending_entries;
        metricSmallValues[0].textContent = module.data.lettrage;
        metricSmallValues[1].textContent = module.data.reconciliation;
    } else if (module.module === 'tax') {
        metricValue.textContent = module.data.next_deadline;
        metricSmallValues[0].textContent = module.data.tva;
        metricSmallValues[1].textContent = module.data.is;
    } else if (module.module === 'hr') {
        metricValue.textContent = module.data.headcount;
        metricSmallValues[0].textContent = module.data.payroll;
        metricSmallValues[1].textContent = module.data.leaves;
    }
}

/**
 * Rend la carte graphique
 */
function renderChartCard() {
    const template = document.getElementById('chartCardTemplate');
    return template.content.cloneNode(true).querySelector('.card');
}

/**
 * Examine la décision liée à la trésorerie
 */
function examineDecision() {
    // Rediriger vers la section décisions ou afficher un modal
    alert('🔴 Décision critique détectée\n\nLa trésorerie a franchi le seuil critique.\nConsultez le rapport RED pour les actions recommandées.');
}

/**
 * Affiche un rapport RED
 */
function viewRedReport(reportId) {
    // Pour l'instant, afficher un message
    // Plus tard, ouvrir une modale ou une page dédiée
    alert(`📊 Rapport RED #${reportId}\n\nFonctionnalité en développement.\nLe rapport détaillé sera affiché ici.`);
}

/**
 * Initialise l'application au chargement de la page
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 AZALS - Application chargée');
    
    // Vérifier l'authentification pour les pages protégées
    if (!checkAuth()) {
        return;
    }
    
    // Initialiser les bulles d'aide
    initHelpBubbles();
    
    // Initialiser le formulaire de connexion (si présent)
    initLoginForm();
    
    // Charger les données utilisateur (si dashboard)
    if (document.body.dataset.requireAuth === 'true') {
        loadUserData();
    }
    
    // Dessiner le graphique (si présent)
    drawEvolutionChart();
    
    // Vérifier l'état de l'API en arrière-plan
    checkAPIHealth().then(health => {
        console.log('📊 État de l\'API:', health);
    });
});

// ==================== UTILITAIRES ====================

/**
 * Formate un nombre en euros
 * @param {number} value - Valeur à formater
 * @returns {string} Valeur formatée
 */
function formatEuros(value) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

/**
 * Formate une date en français
 * @param {Date|string} date - Date à formater
 * @returns {string} Date formatée
 */
function formatDate(date) {
    return new Intl.DateTimeFormat('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(new Date(date));
}

// ============================================================
// INITIALISATION
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialiser la page de login
    initLoginForm();
    
    // Charger les données utilisateur (si dashboard)
    if (document.body.dataset.requireAuth === 'true') {
        loadUserData();
        buildCockpit();
    }
    
    // Vérifier l'état de l'API en arrière-plan
    checkAPIHealth().then(health => {
        console.log('📊 État de l\'API:', health);
    });
});
