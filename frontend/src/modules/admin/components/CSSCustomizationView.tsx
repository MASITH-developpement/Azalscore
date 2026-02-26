/**
 * AZALSCORE - CSS Customization View
 * ===================================
 * Configuration des variables CSS pour personnaliser les vues du logiciel
 * par tenant. Permet de modifier couleurs, espacements, typographie, etc.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Palette, Type, Layout, Sliders, Save, RotateCcw, Check,
  Loader2, Eye, EyeOff, Copy, Download, Code, Square, Circle,
  CheckCircle, AlertCircle
} from 'lucide-react';
import { api } from '@core/api-client';
import { applyTenantCSS, type TenantCSS } from '@core/css-theme';
import { useErrorStore } from '@core/error-handling';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';

// ============================================================================
// TYPES
// ============================================================================

interface CSSVariable {
  name: string;
  value: string;
  category: 'colors' | 'spacing' | 'typography' | 'borders' | 'shadows' | 'custom';
  label: string;
  description: string;
  example: string;
  type: 'color' | 'size' | 'font' | 'number' | 'text';
}

// TenantCSS importe depuis @core/css-theme

// ============================================================================
// CONSTANTES - Variables personnalisables avec descriptions detaillees
// ============================================================================

const CUSTOMIZABLE_VARIABLES: CSSVariable[] = [
  // ===== COULEURS =====
  {
    name: '--azals-primary-500',
    value: '#1E6EFF',
    category: 'colors',
    label: 'Couleur principale',
    description: 'Couleur des boutons principaux, liens, et elements actifs. C\'est la couleur dominante de votre interface.',
    example: 'Boutons "Enregistrer", "Valider", onglets actifs',
    type: 'color'
  },
  {
    name: '--azals-primary-700',
    value: '#1A5FDB',
    category: 'colors',
    label: 'Couleur principale (survol)',
    description: 'Couleur affichee quand la souris passe sur un bouton principal ou un lien.',
    example: 'Bouton au survol de la souris',
    type: 'color'
  },
  {
    name: '--azals-primary-50',
    value: '#EFF6FF',
    category: 'colors',
    label: 'Couleur principale (fond clair)',
    description: 'Version tres claire utilisee en arriere-plan pour mettre en evidence une zone selectionnee.',
    example: 'Fond d\'une ligne selectionnee dans un tableau',
    type: 'color'
  },
  {
    name: '--azals-success',
    value: '#10b981',
    category: 'colors',
    label: 'Couleur de succes (vert)',
    description: 'Couleur pour les messages de confirmation, validations reussies, et statuts positifs.',
    example: '"Enregistrement reussi", badge "Actif", icone de validation',
    type: 'color'
  },
  {
    name: '--azals-warning',
    value: '#f59e0b',
    category: 'colors',
    label: 'Couleur d\'avertissement (orange)',
    description: 'Couleur pour les alertes non-critiques qui necessitent attention.',
    example: '"Attention: champ obligatoire", badge "En attente"',
    type: 'color'
  },
  {
    name: '--azals-danger',
    value: '#ef4444',
    category: 'colors',
    label: 'Couleur de danger (rouge)',
    description: 'Couleur pour les erreurs, suppressions, et actions irreversibles.',
    example: 'Bouton "Supprimer", message d\'erreur, badge "Annule"',
    type: 'color'
  },
  {
    name: '--azals-bg',
    value: '#ffffff',
    category: 'colors',
    label: 'Fond de page',
    description: 'Couleur de fond principale de l\'application. Blanc par defaut.',
    example: 'Arriere-plan general de toutes les pages',
    type: 'color'
  },
  {
    name: '--azals-bg-secondary',
    value: '#f9fafb',
    category: 'colors',
    label: 'Fond des cartes',
    description: 'Couleur de fond des cartes, panneaux lateraux et zones secondaires.',
    example: 'Fond des cartes, sidebar, zones de formulaire',
    type: 'color'
  },
  {
    name: '--azals-text',
    value: '#111827',
    category: 'colors',
    label: 'Texte principal',
    description: 'Couleur du texte principal : titres, contenus importants.',
    example: 'Titres de page, texte des boutons, contenu principal',
    type: 'color'
  },
  {
    name: '--azals-text-secondary',
    value: '#6b7280',
    category: 'colors',
    label: 'Texte secondaire (gris)',
    description: 'Couleur du texte moins important : descriptions, labels, informations complementaires.',
    example: 'Labels de formulaire, descriptions, dates',
    type: 'color'
  },
  {
    name: '--azals-border',
    value: '#e5e7eb',
    category: 'colors',
    label: 'Couleur des bordures',
    description: 'Couleur des lignes de separation et contours des elements.',
    example: 'Bordures des cartes, separateurs, contours des champs',
    type: 'color'
  },

  // ===== BORDURES / ARRONDIS =====
  {
    name: '--azals-radius-sm',
    value: '0.25rem',
    category: 'borders',
    label: 'Arrondi petit (4px)',
    description: 'Arrondi des petits elements comme les badges, tags et puces.',
    example: 'Badges de statut, etiquettes, petits boutons',
    type: 'size'
  },
  {
    name: '--azals-radius-md',
    value: '0.375rem',
    category: 'borders',
    label: 'Arrondi standard (6px)',
    description: 'Arrondi par defaut pour la plupart des elements.',
    example: 'Champs de formulaire, boutons standards',
    type: 'size'
  },
  {
    name: '--azals-radius-lg',
    value: '0.5rem',
    category: 'borders',
    label: 'Arrondi grand (8px)',
    description: 'Arrondi des cartes et conteneurs principaux.',
    example: 'Cartes, panneaux, zones de contenu',
    type: 'size'
  },
  {
    name: '--azals-radius-xl',
    value: '0.75rem',
    category: 'borders',
    label: 'Arrondi tres grand (12px)',
    description: 'Arrondi des fenetres modales et grands conteneurs.',
    example: 'Fenetres de dialogue, modales, grands panneaux',
    type: 'size'
  },

  // ===== ESPACEMENTS =====
  {
    name: '--azals-spacing-xs',
    value: '0.25rem',
    category: 'spacing',
    label: 'Espacement minimal (4px)',
    description: 'Plus petit espacement entre elements tres proches.',
    example: 'Espace entre icone et texte dans un bouton',
    type: 'size'
  },
  {
    name: '--azals-spacing-sm',
    value: '0.5rem',
    category: 'spacing',
    label: 'Espacement petit (8px)',
    description: 'Petit espacement entre elements relies.',
    example: 'Espace entre champs de formulaire sur une ligne',
    type: 'size'
  },
  {
    name: '--azals-spacing-md',
    value: '1rem',
    category: 'spacing',
    label: 'Espacement standard (16px)',
    description: 'Espacement par defaut entre la plupart des elements.',
    example: 'Marges interieures des cartes, espace entre sections',
    type: 'size'
  },
  {
    name: '--azals-spacing-lg',
    value: '1.5rem',
    category: 'spacing',
    label: 'Espacement grand (24px)',
    description: 'Grand espacement pour separer les sections distinctes.',
    example: 'Espace entre le titre et le contenu d\'une carte',
    type: 'size'
  },
  {
    name: '--azals-spacing-xl',
    value: '2rem',
    category: 'spacing',
    label: 'Espacement tres grand (32px)',
    description: 'Tres grand espacement pour les separations majeures.',
    example: 'Marge autour du contenu principal de la page',
    type: 'size'
  },

  // ===== TYPOGRAPHIE =====
  {
    name: '--azals-font-family',
    value: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    category: 'typography',
    label: 'Police de caracteres',
    description: 'Police utilisee pour tout le texte de l\'application. Inter est moderne et lisible.',
    example: 'Tout le texte visible dans l\'application',
    type: 'font'
  },
  {
    name: '--azals-font-size-xs',
    value: '0.75rem',
    category: 'typography',
    label: 'Taille tres petite (12px)',
    description: 'Texte tres petit pour les mentions legales, notes de bas de page.',
    example: 'Copyright, mentions, texte d\'aide contextuelle',
    type: 'size'
  },
  {
    name: '--azals-font-size-sm',
    value: '0.875rem',
    category: 'typography',
    label: 'Taille petite (14px)',
    description: 'Texte courant dans les tableaux, formulaires et listes.',
    example: 'Contenu des tableaux, labels de formulaire',
    type: 'size'
  },
  {
    name: '--azals-font-size-md',
    value: '1rem',
    category: 'typography',
    label: 'Taille standard (16px)',
    description: 'Taille de base pour le texte principal.',
    example: 'Paragraphes, descriptions, texte courant',
    type: 'size'
  },
  {
    name: '--azals-font-size-lg',
    value: '1.125rem',
    category: 'typography',
    label: 'Taille grande (18px)',
    description: 'Texte legerement plus grand pour les sous-titres.',
    example: 'Titres de cartes, sous-titres de section',
    type: 'size'
  },

  // ===== OMBRES =====
  {
    name: '--azals-shadow-sm',
    value: '0 1px 2px rgba(0, 0, 0, 0.05)',
    category: 'shadows',
    label: 'Ombre subtile',
    description: 'Ombre tres legere pour un effet de profondeur discret.',
    example: 'Boutons au repos, petits elements',
    type: 'text'
  },
  {
    name: '--azals-shadow-md',
    value: '0 4px 6px rgba(0, 0, 0, 0.1)',
    category: 'shadows',
    label: 'Ombre moyenne',
    description: 'Ombre standard pour les cartes et elements sureleves.',
    example: 'Cartes, menus deroulants',
    type: 'text'
  },
  {
    name: '--azals-shadow-lg',
    value: '0 10px 15px rgba(0, 0, 0, 0.1)',
    category: 'shadows',
    label: 'Ombre prononcee',
    description: 'Ombre forte pour les elements au premier plan.',
    example: 'Modales, fenetres de dialogue, menus contextuels',
    type: 'text'
  },
];

const CATEGORIES = [
  { id: 'colors', label: 'Couleurs', icon: Palette, description: 'Personnalisez les couleurs de l\'interface' },
  { id: 'borders', label: 'Arrondis', icon: Square, description: 'Ajustez les coins arrondis des elements' },
  { id: 'spacing', label: 'Espacements', icon: Layout, description: 'Modifiez les marges et espacements' },
  { id: 'typography', label: 'Texte', icon: Type, description: 'Configurez la police et les tailles' },
  { id: 'shadows', label: 'Ombres', icon: Circle, description: 'Ajustez les effets d\'ombre' },
  { id: 'custom', label: 'CSS Avance', icon: Code, description: 'Ajoutez du code CSS personnalise' },
];

// ============================================================================
// HOOKS
// ============================================================================

// Valeurs par defaut
const getDefaultCSS = (): TenantCSS => {
  const defaults: Record<string, string> = {};
  CUSTOMIZABLE_VARIABLES.forEach(v => {
    defaults[v.name] = v.value;
  });
  return { tenant_id: '', variables: defaults, custom_css: '' };
};

const useTenantCSS = () => {
  return useQuery({
    queryKey: ['admin', 'tenant-css'],
    queryFn: async (): Promise<TenantCSS> => {
      try {
        const response = await api.get<TenantCSS>('/admin/tenant/css');
        return response?.data || getDefaultCSS();
      } catch {
        return getDefaultCSS();
      }
    },
    staleTime: 60 * 1000,
  });
};

const useSaveTenantCSS = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { variables: Record<string, string>; custom_css?: string }) => {
      const response = await api.put<TenantCSS>('/admin/tenant/css', data);
      return response;
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'tenant-css'] });

      // Emettre un evenement pour appliquer immediatement les changements
      if (typeof window !== 'undefined' && result?.data) {
        window.dispatchEvent(new CustomEvent('azals:css:updated', {
          detail: result.data
        }));
      }
    },
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

interface ColorInputProps {
  value: string;
  onChange: (value: string) => void;
}

const ColorInput: React.FC<ColorInputProps> = ({ value, onChange }) => (
  <div className="azals-css-color-input">
    <input
      type="color"
      value={value.startsWith('#') ? value : '#000000'}
      onChange={(e) => onChange(e.target.value)}
      className="azals-css-color-input__picker"
    />
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="azals-css-color-input__text"
      placeholder="#000000"
    />
  </div>
);

interface VariableCardProps {
  variable: CSSVariable;
  value: string;
  onChange: (name: string, value: string) => void;
}

const VariableCard: React.FC<VariableCardProps> = ({ variable, value, onChange }) => {
  const renderInput = () => {
    switch (variable.type) {
      case 'color':
        return (
          <ColorInput
            value={value}
            onChange={(v) => onChange(variable.name, v)}
          />
        );
      case 'size':
      case 'font':
      case 'text':
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(variable.name, e.target.value)}
            className="azals-input"
            style={{ width: '100%' }}
          />
        );
    }
  };

  return (
    <div className="azals-css-var-card">
      <div className="azals-css-var-card__header">
        <span className="azals-css-var-card__label">{variable.label}</span>
        {variable.type === 'color' && (
          <span
            className="azals-css-var-card__preview"
            style={{ backgroundColor: value }}
          />
        )}
      </div>
      <p className="azals-css-var-card__desc">{variable.description}</p>
      <p className="azals-css-var-card__example">
        <strong>Exemple :</strong> {variable.example}
      </p>
      <div className="azals-css-var-card__input">
        {renderInput()}
      </div>
    </div>
  );
};

// ============================================================================
// VUE PRINCIPALE
// ============================================================================

const CSSCustomizationView: React.FC = () => {
  const { data: tenantCSS, isLoading } = useTenantCSS();
  const saveMutation = useSaveTenantCSS();
  const { addError } = useErrorStore();

  const [variables, setVariables] = useState<Record<string, string>>({});
  const [customCSS, setCustomCSS] = useState('');
  const [activeCategory, setActiveCategory] = useState('colors');
  const [previewEnabled, setPreviewEnabled] = useState(true);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    if (tenantCSS) {
      const initialVars: Record<string, string> = {};
      CUSTOMIZABLE_VARIABLES.forEach(v => {
        initialVars[v.name] = tenantCSS.variables?.[v.name] || v.value;
      });
      setVariables(initialVars);
      setCustomCSS(tenantCSS.custom_css || '');
    }
  }, [tenantCSS]);

  useEffect(() => {
    if (previewEnabled) {
      const root = document.documentElement;
      Object.entries(variables).forEach(([name, value]) => {
        root.style.setProperty(name, value);
      });
    }
  }, [variables, previewEnabled]);

  const handleVariableChange = useCallback((name: string, value: string) => {
    setVariables(prev => ({ ...prev, [name]: value }));
    setSaved(false);
    setSaveError(null);
  }, []);

  const handleSave = async () => {
    setSaveError(null);
    try {
      await saveMutation.mutateAsync({ variables, custom_css: customCSS });
      setSaved(true);

      addError({
        code: 'CSS_SAVED',
        message: 'Apparence enregistree ! Les changements sont appliques immediatement.',
        severity: 'info',
        dismissible: true,
        autoDismiss: 4000
      });
      setTimeout(() => setSaved(false), 3000);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue';
      setSaveError('Impossible d\'enregistrer. Verifiez votre connexion.');
      addError({
        code: 'CSS_SAVE_ERROR',
        message: 'Erreur lors de la sauvegarde de l\'apparence',
        context: errorMessage,
        severity: 'error',
        dismissible: true,
        autoDismiss: 6000
      });
      console.error('Erreur lors de la sauvegarde CSS:', err);
    }
  };

  const handleReset = async () => {
    const defaults: Record<string, string> = {};
    CUSTOMIZABLE_VARIABLES.forEach(v => {
      defaults[v.name] = v.value;
    });
    setVariables(defaults);
    setCustomCSS('');
    setSaved(false);
    setSaveError(null);

    // Appliquer immediatement
    const root = document.documentElement;
    Object.entries(defaults).forEach(([name, value]) => {
      root.style.setProperty(name, value);
    });

    // Sauvegarder sur le serveur
    try {
      await saveMutation.mutateAsync({ variables: defaults, custom_css: '' });
      addError({
        code: 'CSS_RESET',
        message: 'Apparence reinitalisee et sauvegardee',
        severity: 'info',
        dismissible: true,
        autoDismiss: 3000
      });
    } catch {
      addError({
        code: 'CSS_RESET',
        message: 'Apparence reinitalisee (sauvegarde echouee)',
        severity: 'warning',
        dismissible: true,
        autoDismiss: 3000
      });
    }
  };

  const handleExport = () => {
    const cssContent = `:root {\n${Object.entries(variables)
      .map(([name, value]) => `  ${name}: ${value};`)
      .join('\n')}\n}\n\n/* CSS Personnalise */\n${customCSS}`;

    const blob = new Blob([cssContent], { type: 'text/css' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'theme-personnalise.css';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCopy = () => {
    const cssContent = Object.entries(variables)
      .map(([name, value]) => `${name}: ${value};`)
      .join('\n');
    navigator.clipboard.writeText(cssContent);
    addError({
      code: 'CSS_COPIED',
      message: 'Configuration copiee dans le presse-papiers',
      severity: 'info',
      dismissible: true,
      autoDismiss: 2000
    });
  };

  const filteredVariables = CUSTOMIZABLE_VARIABLES.filter(v => v.category === activeCategory);
  const currentCategory = CATEGORIES.find(c => c.id === activeCategory);

  if (isLoading) {
    return (
      <div className="azals-loading">
        <Loader2 className="animate-spin" size={24} />
        <span>Chargement...</span>
      </div>
    );
  }

  return (
    <div className="azals-css-customization">
      {/* Header avec actions */}
      <Card className="azals-css-customization__header-card">
        <div className="azals-css-customization__header">
          <div>
            <h2 className="azals-css-customization__title">
              <Palette size={24} />
              Personnalisation de l'Apparence
            </h2>
            <p className="azals-css-customization__subtitle">
              Modifiez les couleurs et styles de votre espace de travail. Les changements sont visibles en temps reel.
            </p>
          </div>
          <div className="azals-css-customization__actions">
            <Button
              variant={previewEnabled ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setPreviewEnabled(!previewEnabled)}
            >
              {previewEnabled ? <Eye size={16} /> : <EyeOff size={16} />}
              Apercu {previewEnabled ? 'actif' : 'inactif'}
            </Button>
            <Button variant="ghost" size="sm" onClick={handleCopy}>
              <Copy size={16} /> Copier
            </Button>
            <Button variant="ghost" size="sm" onClick={handleExport}>
              <Download size={16} /> Exporter
            </Button>
            <Button variant="ghost" size="sm" onClick={handleReset}>
              <RotateCcw size={16} /> Reinitialiser
            </Button>
            <Button
              variant={saved ? 'success' : 'primary'}
              size="sm"
              onClick={handleSave}
              disabled={saveMutation.isPending}
            >
              {saveMutation.isPending ? (
                <><Loader2 size={16} className="animate-spin" /> Sauvegarde...</>
              ) : saved ? (
                <><Check size={16} /> Enregistre !</>
              ) : (
                <><Save size={16} /> Enregistrer</>
              )}
            </Button>
          </div>
        </div>
      </Card>

      {/* Message d'erreur */}
      {saveError && (
        <div className="azals-css-customization__error">
          <AlertCircle size={18} />
          <span>{saveError}</span>
        </div>
      )}

      {/* Navigation par categories */}
      <div className="azals-css-customization__nav">
        {CATEGORIES.map(cat => {
          const Icon = cat.icon;
          const isActive = activeCategory === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              className={`azals-css-customization__nav-btn ${isActive ? 'azals-css-customization__nav-btn--active' : ''}`}
              onClick={() => setActiveCategory(cat.id)}
            >
              <Icon size={18} />
              <span>{cat.label}</span>
            </button>
          );
        })}
      </div>

      {/* Description de la categorie */}
      {currentCategory && (
        <p className="azals-css-customization__cat-desc">
          {currentCategory.description}
        </p>
      )}

      {/* Contenu selon la categorie */}
      {activeCategory === 'custom' ? (
        <Card className="azals-css-customization__custom">
          <h3 className="azals-css-customization__custom-title">
            <Code size={20} />
            CSS Personnalise Avance
          </h3>
          <p className="azals-css-customization__custom-desc">
            Pour les utilisateurs avances : ajoutez du code CSS supplementaire.
            Ce code sera applique apres les variables ci-dessus.
          </p>
          <div className="azals-css-customization__custom-warning">
            <strong>Attention :</strong> Un CSS incorrect peut casser l'affichage.
            Utilisez "Reinitialiser" en cas de probleme.
          </div>
          <textarea
            value={customCSS}
            onChange={(e) => {
              setCustomCSS(e.target.value);
              setSaved(false);
            }}
            className="azals-css-customization__textarea"
            placeholder={`/* Exemple */
.azals-btn--primary {
  background: linear-gradient(135deg, #1E6EFF, #1A5FDB);
}

.azals-card {
  border-left: 4px solid var(--azals-primary-500);
}`}
            rows={12}
          />
        </Card>
      ) : (
        <div className="azals-css-customization__grid">
          {filteredVariables.map(variable => (
            <VariableCard
              key={variable.name}
              variable={variable}
              value={variables[variable.name] || variable.value}
              onChange={handleVariableChange}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default CSSCustomizationView;
