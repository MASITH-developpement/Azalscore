# AZALSCORE Frontend - Erreurs ESLint à corriger

**Date:** 2026-02-17
**Total erreurs:** 2036

## Résumé par type d'erreur

| Règle | Nombre | Description |
|-------|--------|-------------|
| jsx-a11y/label-has-associated-control | 872 | Labels formulaires non associés aux contrôles |
| @typescript-eslint/no-unused-vars | 469 | Variables déclarées mais non utilisées |
| react/no-unescaped-entities | 326 | Apostrophes/guillemets non échappés (texte français) |
| @typescript-eslint/no-explicit-any | 145 | Usage de `any` au lieu de types spécifiques |
| jsx-a11y/click-events-have-key-events | 78 | Éléments cliquables sans gestionnaire clavier |
| jsx-a11y/no-static-element-interactions | 66 | Éléments statiques avec événements onClick |
| import/order | 24 | Ordre des imports incorrect |
| jsx-a11y/no-autofocus | 15 | Utilisation de autoFocus (accessibilité) |
| no-case-declarations | 7 | Déclarations dans les blocs case |
| jsx-a11y/no-noninteractive-element-interactions | 6 | Interactions sur éléments non-interactifs |
| Parsing errors | 6 | Erreurs de parsing |

## Actions à effectuer

### Priorité 1 - Sécurité et Types
- [ ] Remplacer tous les `any` par des types appropriés (145 occurrences)
- [ ] Supprimer ou préfixer avec `_` les variables non utilisées (469 occurrences)

### Priorité 2 - Accessibilité (WCAG)
- [ ] Associer les labels aux contrôles avec `htmlFor` ou `aria-labelledby` (872 occurrences)
- [ ] Ajouter `onKeyDown` et `role` aux éléments cliquables (144 occurrences)
- [ ] Revoir l'utilisation de `autoFocus` (15 occurrences)

### Priorité 3 - Qualité code
- [ ] Échapper les apostrophes françaises avec `&apos;` (326 occurrences)
- [ ] Corriger l'ordre des imports (24 occurrences)
- [ ] Corriger les déclarations dans les switch/case (7 occurrences)

## Fichier détaillé

Voir `ESLINT_ERRORS_TODO.txt` pour la liste complète des erreurs avec fichiers et lignes.

## Commandes utiles

```bash
# Relancer l'analyse
npm run lint

# Auto-fix ce qui peut l'être
npm run lint:fix

# Vérifier les types TypeScript
npm run type-check
```
