# AZALSCORE - Charte d'Usage du Logo

## 1. Logo Officiel

Le logo AZALSCORE combine un triangle gradient symbolisant la croissance et la stabilité, entouré d'arcs représentant la protection et l'écosystème.

### Éléments constitutifs
- **Triangle central** : Gradient cyan (#2DD4BF) vers violet (#8B5CF6)
- **Arcs latéraux** : Blanc, symbolisant protection et encadrement
- **Cercle externe** : Ligne fine représentant l'écosystème global
- **Points décoratifs** : Éléments de modernité (usage sobre)

## 2. Règles d'Usage

### 2.1 Tailles Minimales

| Contexte | Taille minimale |
|----------|-----------------|
| Favicon | 16x16 px |
| Header compact | 24x24 px |
| Header standard | 32x32 px |
| Page de connexion | 64x64 px |
| Écran de chargement | 96x96 px |
| Documentation | 48x48 px minimum |

### 2.2 Marges de Sécurité

- **Zone de protection** : Minimum 25% de la largeur du logo autour
- **Espacement texte** : Minimum 8px entre le logo et tout texte adjacent
- **Bord d'écran** : Minimum 16px des bords sur mobile, 24px sur desktop

### 2.3 Fonds Autorisés

| Type de fond | Autorisé | Notes |
|--------------|----------|-------|
| Blanc (#FFFFFF) | OUI | Usage principal |
| Gris clair (#F9FAFB à #E5E7EB) | OUI | Contextes secondaires |
| Bleu foncé (#1E3A8A à #1E40AF) | OUI | Mode sombre, utiliser variant "darkMode" |
| Gris foncé (#1F2937 à #374151) | OUI | Mode sombre |
| Noir (#000000 à #111827) | OUI | Mode sombre uniquement |
| Couleurs vives/saturées | NON | Interdit |
| Images/photos en fond | NON | Interdit |
| Gradients colorés | NON | Interdit |

### 2.4 Usages Interdits

- Déformation (étirement, compression)
- Rotation autre que 0°
- Recoloration du triangle gradient
- Ajout d'effets (ombre portée, lueur, 3D)
- Superposition sur images
- Usage répétitif/pattern
- Animation gratuite (sauf loading spinner intégré)
- Modification des proportions des éléments
- Suppression d'éléments (arcs, points)

## 3. Emplacements Obligatoires

### 3.1 Application (OBLIGATOIRE)

| Écran | Format | Taille |
|-------|--------|--------|
| Login | Full (icon + texte) | 64-96px |
| Loading/Splash | Full (icon + texte) | 96px |
| Header principal | Horizontal (icon + texte) | 32px |
| Sidebar (si présent) | Icon seul | 24px |
| Footer applicatif | Horizontal | 24px |
| Page "À propos" | Full | 64px |
| Pages erreur (403/404/500) | Full | 48-64px |
| Exports PDF | Icon ou Horizontal | 24-32px |
| Emails transactionnels | Horizontal | 32px (footer) |
| Admin/Tenant management | Horizontal | 32px |

### 3.2 Emplacements Interdits

| Zone | Raison |
|------|--------|
| Dashboards (corps) | Pollution visuelle |
| Graphiques | Lisibilité des données |
| Tableaux de données | Distraction |
| Formulaires | Focus utilisateur |
| Modales (corps) | Espace restreint |
| Répétition décorative | Sur-branding |

## 4. Variantes du Composant

### 4.1 Code d'utilisation

```tsx
import { AzalscoreLogo } from '@/components/Logo';

// Logo complet (icon + texte vertical)
<AzalscoreLogo size="lg" variant="full" />

// Logo horizontal (icon + texte côte à côte)
<AzalscoreLogo size="md" variant="horizontal" />

// Icône seule
<AzalscoreLogo size="sm" variant="icon" />

// Mode sombre
<AzalscoreLogo size="md" darkMode />

// Taille personnalisée
<AzalscoreLogo size={72} />
```

### 4.2 Propriétés

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| size | 'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl' \| '2xl' \| number | 'md' | Taille du logo |
| variant | 'full' \| 'icon' \| 'horizontal' | 'full' | Disposition |
| darkMode | boolean | false | Couleurs pour fond sombre |
| className | string | '' | Classes CSS additionnelles |
| alt | string | 'AZALSCORE' | Texte alternatif |

## 5. Accessibilité

### 5.1 Exigences WCAG

- **Contraste** : Ratio minimum 4.5:1 pour le texte
- **Alternative texte** : Attribut `alt` systématique
- **Role ARIA** : `role="img"` avec `aria-label`
- **Focus** : Ne pas inclure dans la navigation clavier si décoratif

### 5.2 Bonnes pratiques

```tsx
// Correct - Logo informatif
<AzalscoreLogo alt="Retour à l'accueil AZALSCORE" />

// Correct - Logo décoratif (texte adjacent)
<AzalscoreLogo aria-hidden="true" />
<span>AZALSCORE</span>
```

## 6. Responsive

### 6.1 Breakpoints

| Écran | Comportement |
|-------|-------------|
| Mobile (< 640px) | Header: icon seul 24px |
| Tablet (640-1024px) | Header: horizontal 28px |
| Desktop (> 1024px) | Header: horizontal 32px |

### 6.2 Mode sombre

Le composant détecte automatiquement `[data-theme="dark"]` ou accepte la prop `darkMode` pour adapter les couleurs.

## 7. Fichiers et Assets

### 7.1 Chemins

| Asset | Chemin |
|-------|--------|
| Composant React | `@/components/Logo/AzalscoreLogo.tsx` |
| Favicon 16x16 | `/favicon-16x16.png` |
| Favicon 32x32 | `/favicon.png` |
| Favicon 48x48 | `/favicon-48x48.png` |
| PWA 192x192 | `/pwa-192x192.png` |
| PWA 512x512 | `/pwa-512x512.png` |
| Apple Touch Icon | `/apple-touch-icon.png` |

### 7.2 Couleurs de référence

```css
/* Palette logo */
--azals-logo-cyan: #2DD4BF;
--azals-logo-blue: #3B82F6;
--azals-logo-violet: #8B5CF6;
--azals-logo-text: #1E40AF;
--azals-logo-text-dark: #FFFFFF;
```

## 8. Validation

Avant chaque release, vérifier :

- [ ] Logo présent sur tous les écrans obligatoires
- [ ] Aucun logo dans les zones interdites
- [ ] Tailles conformes aux minimums
- [ ] Marges de sécurité respectées
- [ ] Contraste WCAG respecté
- [ ] Texte alternatif présent
- [ ] Responsive fonctionnel
- [ ] Mode sombre correct

---

**Version** : 1.0.0
**Dernière mise à jour** : Janvier 2026
**Contact** : branding@azalscore.com
