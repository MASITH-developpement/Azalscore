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
 * COCKPIT DIRIGEANT - Vue décisionnelle exclusive
 * 
 * RÈGLE FONDAMENTALE : Le dirigeant voit UN SEUL niveau à la fois
 * - Si 🔴 présent → UNIQUEMENT zone critique (masque tout le reste)
 * - Si 🟠 présent (sans 🔴) → UNIQUEMENT zone tension
 * - Sinon → Zone normale avec tous les indicateurs
 * 
 * PRIORISATION DOMAINES : Financier > Juridique > Fiscal > Social > Structurel
 * 
 * OBJECTIF : Comprendre le risque principal en 3 secondes
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
        // CHARGEMENT DES DONNÉES
        // ============================================
        const [journalData, treasuryData, accountingData, taxData, hrData] = await Promise.all([
            loadJournalData(),
            loadTreasuryData(),
            loadAccountingData(),
            loadTaxData(),
            loadHRData()
        ]);
        
        // Vérifier si le workflow RED est complété (si trésorerie en déficit)
        let isWorkflowCompleted = false;
        if (treasuryData && treasuryData.red_triggered && treasuryData.id) {
            try {
                const statusResponse = await authenticatedFetch(`${API_BASE}/decision/red/status/${treasuryData.id}`);
                if (statusResponse.ok) {
                    const workflowStatus = await statusResponse.json();
                    isWorkflowCompleted = workflowStatus.is_fully_validated || false;
                }
            } catch (error) {
                console.error('Erreur chargement workflow status:', error);
            }
        }
        
        // ============================================
        // CONSTRUCTION DES MODULES AVEC DOMAINE
        // Priorisation : Financier(0) > Juridique(1) > Fiscal(2) > Social(3) > Structurel(4)
        // ============================================
        const modules = [
            { ...buildTreasuryModule(treasuryData, isWorkflowCompleted), domain: 'Financier', domainPriority: 0 },
            { ...buildAccountingModule(accountingData), domain: 'Financier', domainPriority: 0 },
            { ...buildTaxModule(taxData), domain: 'Fiscal', domainPriority: 2 },
            { ...buildHRModule(hrData), domain: 'Social', domainPriority: 3 }
        ];
        
        // Tri par domaine puis par priorité de risque
        modules.sort((a, b) => {
            if (a.priority !== b.priority) return a.priority - b.priority;
            return a.domainPriority - b.domainPriority;
        });
        
        // Séparer par niveau de risque
        const criticalModules = modules.filter(m => m.priority === 0); // 🔴
        const tensionModules = modules.filter(m => m.priority === 1);  // 🟠
        const normalModules = modules.filter(m => m.priority === 2);   // 🟢
        
        // ============================================
        // LOGIQUE D'AFFICHAGE EXCLUSIF
        // Un seul niveau visible à la fois
        // ============================================
        
        const hasCritical = criticalModules.length > 0;
        const hasTension = tensionModules.length > 0;
        
        if (hasCritical) {
            // ══════════════════════════════════════════
            // MODE CRITIQUE 🔴 - Affichage prioritaire
            // Les modules critiques sont affichés EN PREMIER au-dessus des autres
            // Les autres zones sont visibles mais inactives (atténuées)
            // ══════════════════════════════════════════
            if (zoneCritical && criticalContainer) {
                zoneCritical.style.display = 'block';
                criticalContainer.innerHTML = '';
                
                // Créer la carte d'alerte critique avec accès rapport
                const criticalCard = createCockpitCriticalView(criticalModules);
                if (criticalCard) criticalContainer.appendChild(criticalCard);
            }
            
            // AFFICHER les autres zones mais en mode inactif (atténuées)
            if (zoneTension && tensionContainer && hasTension) {
                zoneTension.style.display = 'block';
                zoneTension.classList.add('zone-inactive');
                tensionContainer.innerHTML = '';
                for (const mod of tensionModules) {
                    const card = mod.createCard();
                    if (card) tensionContainer.appendChild(card);
                }
            }
            
            if (zoneNormal && normalContainer && normalModules.length > 0) {
                zoneNormal.style.display = 'block';
                zoneNormal.classList.add('zone-inactive');
                normalContainer.innerHTML = '';
                for (const mod of normalModules) {
                    const card = mod.createCard();
                    if (card) normalContainer.appendChild(card);
                }
            }
            
            if (zoneAnalysis && analysisContainer) {
                zoneAnalysis.style.display = 'block';
                zoneAnalysis.classList.add('zone-inactive');
                analysisContainer.innerHTML = '';
                const chartCard = createChartCard();
                if (chartCard) analysisContainer.appendChild(chartCard);
            }
            
        } else if (hasTension) {
            // ══════════════════════════════════════════
            // MODE TENSION 🟠 - Points d'attention
            // Pas de critique, mais vigilance requise
            // ══════════════════════════════════════════
            if (zoneTension && tensionContainer) {
                zoneTension.style.display = 'block';
                zoneTension.classList.remove('zone-inactive');
                tensionContainer.innerHTML = '';
                
                for (const mod of tensionModules) {
                    const card = mod.createCard();
                    if (card) tensionContainer.appendChild(card);
                }
            }
            
            // Zone normale visible aussi (informations complémentaires)
            if (zoneNormal && normalContainer) {
                zoneNormal.style.display = 'block';
                zoneNormal.classList.remove('zone-inactive');
                normalContainer.innerHTML = '';
                for (const mod of normalModules) {
                    const card = mod.createCard();
                    if (card) normalContainer.appendChild(card);
                }
            }
            
            // Graphiques visibles
            if (zoneAnalysis && analysisContainer) {
                zoneAnalysis.style.display = 'block';
                zoneAnalysis.classList.remove('zone-inactive');
                analysisContainer.innerHTML = '';
                const chartCard = createChartCard();
                if (chartCard) analysisContainer.appendChild(chartCard);
            }
            
        } else {
            // ══════════════════════════════════════════
            // MODE NORMAL 🟢 - Tout va bien
            // Affichage complet des indicateurs
            // ══════════════════════════════════════════
            if (zoneNormal && normalContainer) {
                zoneNormal.style.display = 'block';
                zoneNormal.classList.remove('zone-inactive');
                normalContainer.innerHTML = '';
                
                for (const mod of modules) {
                    const card = mod.createCard();
                    if (card) normalContainer.appendChild(card);
                }
            }
            
            // Graphiques visibles
            if (zoneAnalysis && analysisContainer) {
                zoneAnalysis.style.display = 'block';
                zoneAnalysis.classList.remove('zone-inactive');
                analysisContainer.innerHTML = '';
                const chartCard = createChartCard();
                if (chartCard) analysisContainer.appendChild(chartCard);
            }
        }
        
        // Réinitialiser les bulles d'aide
        initHelpBubbles();
        
        // Hook pour extensions futures
        onCockpitReady({ criticalModules, tensionModules, normalModules, displayMode: hasCritical ? 'critical' : hasTension ? 'tension' : 'normal' });
        
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
