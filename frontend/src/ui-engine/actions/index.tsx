/**
 * AZALSCORE UI Engine - Actions System
 * Boutons et actions avec confirmation et capacités
 * AUCUNE décision métier - exécution uniquement
 */

import React, { useState, useCallback } from 'react';
import { clsx } from 'clsx';
import { X, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';
import { CapabilityGuard, useHasCapability } from '@core/capabilities';
import { trackAction } from '@core/audit-ui';
import type { ActionButton } from '@/types';

// ============================================================
// TYPES
// ============================================================

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'warning' | 'ghost' | 'success';
type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  isDisabled?: boolean;
  disabled?: boolean; // Alias pour isDisabled
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  onClick?: () => void | Promise<void>;
  type?: 'button' | 'submit' | 'reset';
  children: React.ReactNode;
  className?: string;
}

// ============================================================
// BUTTON COMPONENT
// ============================================================

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading,
  isDisabled,
  disabled,
  leftIcon,
  rightIcon,
  fullWidth,
  onClick,
  type = 'button',
  children,
  className,
}) => {
  const [isExecuting, setIsExecuting] = useState(false);
  const isButtonDisabled = isDisabled ?? disabled;

  const handleClick = useCallback(async () => {
    if (!onClick || isLoading || isButtonDisabled || isExecuting) return;

    const result = onClick();
    if (result instanceof Promise) {
      setIsExecuting(true);
      try {
        await result;
      } finally {
        setIsExecuting(false);
      }
    }
  }, [onClick, isLoading, isButtonDisabled, isExecuting]);

  const loading = isLoading || isExecuting;

  return (
    <button
      type={type}
      onClick={handleClick}
      disabled={isButtonDisabled || loading}
      className={clsx(
        'azals-btn',
        `azals-btn--${variant}`,
        `azals-btn--${size}`,
        {
          'azals-btn--loading': loading,
          'azals-btn--full-width': fullWidth,
        },
        className
      )}
    >
      {loading ? (
        <Loader2 className="azals-btn__spinner" size={16} />
      ) : leftIcon ? (
        <span className="azals-btn__icon azals-btn__icon--left">{leftIcon}</span>
      ) : null}
      <span className="azals-btn__text">{children}</span>
      {rightIcon && !loading && (
        <span className="azals-btn__icon azals-btn__icon--right">{rightIcon}</span>
      )}
    </button>
  );
};

// ============================================================
// ICON BUTTON
// ============================================================

interface IconButtonProps {
  icon: React.ReactNode;
  onClick?: () => void | Promise<void>;
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  isDisabled?: boolean;
  ariaLabel: string;
  className?: string;
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  onClick,
  variant = 'ghost',
  size = 'md',
  isLoading,
  isDisabled,
  ariaLabel,
  className,
}) => {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isDisabled || isLoading}
      aria-label={ariaLabel}
      className={clsx(
        'azals-btn',
        'azals-btn--icon-only',
        `azals-btn--${variant}`,
        `azals-btn--${size}`,
        className
      )}
    >
      {isLoading ? <Loader2 className="azals-spin" size={16} /> : icon}
    </button>
  );
};

// ============================================================
// ACTION BUTTON WITH CAPABILITY
// ============================================================

interface CapabilityActionProps {
  action: ActionButton;
  className?: string;
}

export const CapabilityAction: React.FC<CapabilityActionProps> = ({
  action,
  className,
}) => {
  const [showConfirm, setShowConfirm] = useState(false);
  const hasCapability = useHasCapability(action.capability || '');

  if (action.capability && !hasCapability) {
    return null;
  }

  const handleClick = async () => {
    if (action.requiresConfirmation) {
      setShowConfirm(true);
    } else {
      trackAction('action_button', action.id);
      await action.onClick();
    }
  };

  const handleConfirm = async () => {
    setShowConfirm(false);
    trackAction('action_button', action.id, { confirmed: true });
    await action.onClick();
  };

  return (
    <>
      <Button
        variant={action.variant}
        onClick={handleClick}
        isLoading={action.isLoading}
        isDisabled={action.isDisabled}
        className={className}
      >
        {action.label}
      </Button>

      {showConfirm && (
        <ConfirmDialog
          title="Confirmation requise"
          message={action.confirmationMessage || 'Êtes-vous sûr de vouloir effectuer cette action ?'}
          onConfirm={handleConfirm}
          onCancel={() => setShowConfirm(false)}
          variant={action.variant === 'danger' ? 'danger' : 'warning'}
        />
      )}
    </>
  );
};

// ============================================================
// BUTTON GROUP
// ============================================================

interface ButtonGroupProps {
  children: React.ReactNode;
  align?: 'left' | 'center' | 'right';
  className?: string;
}

export const ButtonGroup: React.FC<ButtonGroupProps> = ({
  children,
  align = 'left',
  className,
}) => {
  return (
    <div className={clsx('azals-btn-group', `azals-btn-group--${align}`, className)}>
      {children}
    </div>
  );
};

// ============================================================
// CONFIRM DIALOG
// ============================================================

interface ConfirmDialogProps {
  title: string;
  message: React.ReactNode;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'warning' | 'danger';
  isLoading?: boolean;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  title,
  message,
  onConfirm,
  onCancel,
  confirmLabel = 'Confirmer',
  cancelLabel = 'Annuler',
  variant = 'warning',
  isLoading,
}) => {
  const Icon = variant === 'danger' ? AlertTriangle : AlertTriangle;

  return (
    <div className="azals-modal-overlay" onClick={onCancel}>
      <div
        className="azals-modal azals-modal--confirm"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className={clsx('azals-modal__icon', `azals-modal__icon--${variant}`)}>
          <Icon size={24} />
        </div>

        <h2 className="azals-modal__title">{title}</h2>
        <p className="azals-modal__message">{message}</p>

        <div className="azals-modal__actions">
          <Button variant="secondary" onClick={onCancel} isDisabled={isLoading}>
            {cancelLabel}
          </Button>
          <Button
            variant={variant === 'danger' ? 'danger' : 'primary'}
            onClick={onConfirm}
            isLoading={isLoading}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
};

// ============================================================
// MODAL
// ============================================================

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
}) => {
  if (!isOpen) return null;

  return (
    <div className="azals-modal-overlay" onClick={onClose}>
      <div
        className={clsx('azals-modal', `azals-modal--${size}`)}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className="azals-modal__header">
          <h2 className="azals-modal__title">{title}</h2>
          <IconButton
            icon={<X size={20} />}
            onClick={onClose}
            ariaLabel="Fermer"
            variant="ghost"
          />
        </div>

        <div className="azals-modal__body">{children}</div>

        {footer && <div className="azals-modal__footer">{footer}</div>}
      </div>
    </div>
  );
};

// ============================================================
// DROPDOWN MENU
// ============================================================

interface DropdownItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  onClick: () => void;
  capability?: string;
  variant?: 'default' | 'danger';
  disabled?: boolean;
}

interface DropdownMenuProps {
  trigger: React.ReactNode;
  items: DropdownItem[];
  align?: 'left' | 'right';
}

export const DropdownMenu: React.FC<DropdownMenuProps> = ({
  trigger,
  items,
  align = 'right',
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="azals-dropdown">
      <div onClick={() => setIsOpen(!isOpen)}>{trigger}</div>

      {isOpen && (
        <>
          <div
            className="azals-dropdown__overlay"
            onClick={() => setIsOpen(false)}
          />
          <div className={clsx('azals-dropdown__menu', `azals-dropdown__menu--${align}`)}>
            {items.map((item) => (
              <CapabilityGuard key={item.id} capability={item.capability}>
                <button
                  className={clsx('azals-dropdown__item', {
                    'azals-dropdown__item--danger': item.variant === 'danger',
                  })}
                  onClick={() => {
                    item.onClick();
                    setIsOpen(false);
                  }}
                  disabled={item.disabled}
                >
                  {item.icon && <span className="azals-dropdown__item-icon">{item.icon}</span>}
                  <span>{item.label}</span>
                </button>
              </CapabilityGuard>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

// ============================================================
// SUCCESS TOAST (Temporary feedback)
// ============================================================

interface ToastProps {
  message: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({
  message,
  type = 'success',
  onClose,
}) => {
  React.useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const Icon = type === 'success' ? CheckCircle : AlertTriangle;

  return (
    <div className={clsx('azals-toast', `azals-toast--${type}`)}>
      <Icon size={20} />
      <span>{message}</span>
      <IconButton
        icon={<X size={16} />}
        onClick={onClose}
        ariaLabel="Fermer"
        variant="ghost"
        size="sm"
      />
    </div>
  );
};

// ============================================================
// EXPORTS
// ============================================================

export default {
  Button,
  IconButton,
  CapabilityAction,
  ButtonGroup,
  ConfirmDialog,
  Modal,
  DropdownMenu,
  Toast,
};
