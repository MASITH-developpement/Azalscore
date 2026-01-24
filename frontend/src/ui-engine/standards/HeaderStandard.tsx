/**
 * AZALSCORE UI Standards - HeaderStandard Component
 * En-tête standardisé avec titre, statut et actions
 */

import React from 'react';
import { clsx } from 'clsx';
import { ArrowLeft, Loader2 } from 'lucide-react';
import type { HeaderStandardProps, ActionDefinition, SemanticColor } from './types';

/**
 * Mapping des couleurs sémantiques vers les classes CSS
 */
const colorClasses: Record<SemanticColor, string> = {
  gray: 'azals-badge--gray',
  blue: 'azals-badge--blue',
  green: 'azals-badge--green',
  orange: 'azals-badge--orange',
  red: 'azals-badge--red',
  purple: 'azals-badge--purple',
  yellow: 'azals-badge--yellow',
  cyan: 'azals-badge--cyan',
};

/**
 * Mapping des variantes de bouton vers les classes CSS
 */
const buttonVariantClasses = {
  primary: 'azals-btn--primary',
  secondary: 'azals-btn--secondary',
  danger: 'azals-btn--danger',
  warning: 'azals-btn--warning',
  ghost: 'azals-btn--ghost',
  success: 'azals-btn--success',
};

/**
 * HeaderStandard - En-tête standardisé pour les vues
 *
 * Caractéristiques:
 * - Titre et sous-titre
 * - Badge de statut avec couleur sémantique
 * - Actions avec support async et confirmation
 * - Bouton de retour optionnel
 */
export const HeaderStandard: React.FC<HeaderStandardProps> = ({
  title,
  subtitle,
  status,
  actions = [],
  backAction,
  className,
  children,
}) => {
  return (
    <header className={clsx('azals-std-header', className)}>
      <div className="azals-std-header__info">
        {backAction && (
          <button
            type="button"
            className="azals-btn azals-btn--ghost azals-std-header__back"
            onClick={backAction.onClick}
          >
            <ArrowLeft size={16} />
            <span>{backAction.label}</span>
          </button>
        )}

        <div className="azals-std-header__title-row">
          <h1 className="azals-std-header__title">{title}</h1>
          {status && (
            <span
              className={clsx(
                'azals-std-header__status',
                colorClasses[status.color]
              )}
            >
              {status.icon && (
                <span className="azals-std-header__status-icon">
                  {status.icon}
                </span>
              )}
              {status.label}
            </span>
          )}
        </div>

        {subtitle && <p className="azals-std-header__subtitle">{subtitle}</p>}

        {children}
      </div>

      {actions.length > 0 && (
        <div className="azals-std-header__actions">
          {actions
            .filter((action) => !action.hidden)
            .map((action) => (
              <ActionButton key={action.id} action={action} />
            ))}
        </div>
      )}
    </header>
  );
};

/**
 * Composant bouton d'action avec support async
 */
interface ActionButtonProps {
  action: ActionDefinition;
}

const ActionButton: React.FC<ActionButtonProps> = ({ action }) => {
  const [isLoading, setIsLoading] = React.useState(false);

  const handleClick = async () => {
    if (action.disabled || isLoading) return;

    // Gérer la confirmation si nécessaire
    if (action.confirm) {
      const confirmed = window.confirm(
        `${action.confirm.title}\n\n${action.confirm.message}`
      );
      if (!confirmed) return;
    }

    // Gérer le onClick async
    if (action.onClick) {
      const result = action.onClick();
      if (result instanceof Promise) {
        setIsLoading(true);
        try {
          await result;
        } finally {
          setIsLoading(false);
        }
      }
    }
  };

  const loading = isLoading || action.loading;

  // Si c'est un lien
  if (action.href && !action.onClick) {
    return (
      <a
        href={action.href}
        className={clsx(
          'azals-btn',
          buttonVariantClasses[action.variant || 'secondary'],
          { 'azals-btn--disabled': action.disabled }
        )}
      >
        {action.icon && <span className="azals-btn__icon">{action.icon}</span>}
        <span>{action.label}</span>
      </a>
    );
  }

  return (
    <button
      type="button"
      className={clsx(
        'azals-btn',
        buttonVariantClasses[action.variant || 'secondary'],
        { 'azals-btn--loading': loading }
      )}
      onClick={handleClick}
      disabled={action.disabled || loading}
    >
      {loading ? (
        <Loader2 size={16} className="azals-spin" />
      ) : (
        action.icon && <span className="azals-btn__icon">{action.icon}</span>
      )}
      <span>{action.label}</span>
    </button>
  );
};

export default HeaderStandard;
