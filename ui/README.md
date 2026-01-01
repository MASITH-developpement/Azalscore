# AZALS - Interface Frontend

Interface ERP premium moderne en HTML/CSS/JS vanilla.

## 🎯 Objectif

Fournir une interface de pilotage décisionnel critique pour dirigeants, experts-comptables et juristes, avec une esthétique premium, sobre et professionnelle.

## 📁 Structure

```
ui/
├── index.html       # Page d'entrée (authentification)
├── dashboard.html   # Cockpit ERP principal
├── styles.css       # Feuilles de style (CSS variables)
├── app.js          # JavaScript vanilla (interactions + API)
└── README.md       # Ce fichier
```

## 🚀 Démarrage rapide

### Option 1 : Ouvrir directement dans le navigateur

1. Ouvrir `index.html` dans votre navigateur :
   ```bash
   cd /workspaces/Azalscore/ui
   open index.html  # macOS
   xdg-open index.html  # Linux
   start index.html  # Windows
   ```

2. Ou utiliser le navigateur depuis VS Code :
   - Clic droit sur `index.html`
   - "Open with Live Server" (si extension installée)

### Option 2 : Serveur HTTP simple

Pour éviter les problèmes CORS avec les appels API :

```bash
cd /workspaces/Azalscore/ui
python3 -m http.server 8080
```

Puis ouvrir : http://localhost:8080

## 🎨 Caractéristiques visuelles

- **Palette de couleurs** : Bleu nuit (#1a2332) / Graphite (#2a3647)
- **Accent** : Bleu moderne (#4a90e2)
- **Statuts** : 🟢 Bon / 🟠 Attention / 🔴 Critique
- **Typographie** : System UI (Inter-like)
- **Design** : Premium, contrasté, lisible

## 🔧 Personnalisation

### Modifier les couleurs

Éditer les CSS variables dans `styles.css` :

```css
:root {
    --color-primary: #1a2332;
    --color-accent: #4a90e2;
    --color-success: #10b981;
    --color-danger: #ef4444;
    /* ... */
}
```

### Ajouter une page

1. Dupliquer `dashboard.html`
2. Modifier le contenu de `.main-content`
3. Ajouter un lien dans la `.sidebar-nav`

### Modifier le graphique

Éditer la fonction `drawEvolutionChart()` dans `app.js` :

```javascript
const revenue = [45000, 52000, 48000, 61000, 58000, 67000];
const expenses = [32000, 35000, 33000, 38000, 36000, 41000];
```

## 🔌 Intégration avec l'API

L'application appelle automatiquement `/health` au chargement.

### Configuration des URLs

Dans `app.js`, modifier selon votre environnement :

```javascript
const apiUrl = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/health'
    : 'https://azalscore-wlm15q.fly.dev/health';
```

### Ajouter des appels API

Exemple dans `app.js` :

```javascript
async function fetchTreasury() {
    const response = await fetch('/api/treasury');
    const data = await response.json();
    return data;
}
```

## 📱 Responsive

- **Desktop** : Layout complet avec sidebar
- **Tablette** : Cards en grille adaptative
- **Mobile** : Sidebar escamotable, cards en colonne unique

## 🎯 Bulles d'aide

Ajouter `data-help` sur les icônes ⓘ :

```html
<span class="help-icon" data-help="Votre texte d'aide">ⓘ</span>
```

## 🚫 Contraintes techniques

- **Aucun framework** : Vanilla JS uniquement
- **Aucune dépendance** : Pas de npm, pas de CDN
- **Isolation complète** : Supprimable sans impact backend
- **Compatibilité** : Navigateurs modernes (Chrome, Firefox, Safari, Edge)

## 📝 Prochaines étapes suggérées

1. ✅ Ajouter l'authentification réelle
2. ✅ Connecter les données du dashboard à l'API
3. ✅ Implémenter les pages Trésorerie, Comptabilité, etc.
4. ✅ Ajouter la gestion des erreurs UI
5. ✅ Implémenter les notifications temps réel

## 🎓 Philosophie du code

- **Lisible** : Code commenté, noms explicites
- **Maintenable** : Structure claire, séparation des responsabilités
- **Performant** : Pas de dépendances lourdes
- **Évolutif** : Facile d'ajouter des fonctionnalités

## 📞 Support

Pour toute question sur l'interface :
- Consulter les commentaires dans le code
- Vérifier les CSS variables pour les personnalisations
- Tester avec les DevTools du navigateur

---

**AZALS** - ERP Décisionnel Premium © 2026
