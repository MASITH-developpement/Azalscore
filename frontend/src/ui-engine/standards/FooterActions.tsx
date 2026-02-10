/**
 * AZALSCORE UI Standards - FooterActions Component
 * Zone d'actions en bas de page
 */

import React, { useState } from 'react';
import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';
import type { FooterActionsProps, ActionDefinition } from './types';

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
 * FooterActions - Zone d'actions en bas de page
 *
 * Caractéristiques:
 * - Actions secondaires à gauche
 * - Actions primaires à droite
 * - Support async avec état de chargement
 * - Confirmation optionnelle
 */
export const FooterActions: React.FC<FooterActionsProps> = ({
  secondaryActions = [],
  primaryActions = [],
  className,
}) => {
  // Ne pas afficher si aucune action
  if (secondaryActions.length === 0 && primaryActions.length === 0) {
    return null;
  }

  const visibleSecondary = secondaryActions.filter((a) => !a.hidden);
  const visiblePrimary = primaryActions.filter((a) => !a.hidden);

  return (
    <footer className={clsx('azals-std-footer', className)}>
      <div className="azals-std-footer__secondary">
        {visibleSecondary.map((action) => (
          <FooterActionButton key={action.id} action={action} />
        ))}
      </div>

      <div className="azals-std-footer__primary">
        {visiblePrimary.map((action) => (
          <FooterActionButton key={action.id} action={action} />
        ))}
      </div>
    </footer>
  );
};

/**
 * Composant bouton d'action du footer
 */
interface FooterActionButtonProps {
  action: ActionDefinition;
}

const FooterActionButton: React.FC<FooterActionButtonProps> = ({ action }) => {
  const [isLoading, setIsLoading] = useState(false);

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

export default FooterActions;
