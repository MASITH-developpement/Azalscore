/**
 * AZALS - Application JavaScript
 * Gestion des interactions, bulles d'aide, et appels API
 */

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
 * Gère la soumission du formulaire d'entrée
 */
function initLoginForm() {
    const form = document.getElementById('loginForm');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const intentInput = document.getElementById('userIntent');
        const intent = intentInput.value.trim();
        
        // Simulation d'une entrée dans le système
        console.log('Intention utilisateur:', intent);
        
        // Vérifier la santé de l'API (appel réel)
        try {
            const health = await checkAPIHealth();
            console.log('État API:', health);
            
            if (health.status === 'ok') {
                // Redirection vers le dashboard
                window.location.href = '/dashboard';
            } else {
                alert('Le système est temporairement indisponible. Veuillez réessayer.');
            }
        } catch (error) {
            console.error('Erreur de connexion:', error);
            // En mode développement, rediriger quand même
            window.location.href = '/dashboard';
        }
    });
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
 * Initialise l'application au chargement de la page
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 AZALS - Application chargée');
    
    // Initialiser les bulles d'aide
    initHelpBubbles();
    
    // Initialiser le formulaire de connexion (si présent)
    initLoginForm();
    
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
