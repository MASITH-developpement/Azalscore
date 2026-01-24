/**
 * AZALSCORE - Composants Simples Réutilisables
 * =============================================
 *
 * Un seul fichier avec tous les composants de base.
 * Style unifié comme la page Saisie.
 */

import React from 'react';
import { Loader2, ArrowLeft, Search, Plus, Eye, Edit, Trash2, Check } from 'lucide-react';

// ============================================================
// LOADING
// ============================================================

export const Loading: React.FC<{ text?: string }> = ({ text = 'Chargement...' }) => (
  <div className="azals-ws-loading">
    <Loader2 className="azals-ws-loading__spinner" size={32} />
    <span>{text}</span>
  </div>
);

// ============================================================
// PAGE HEADER
// ============================================================

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  onBack?: () => void;
  actions?: React.ReactNode;
  date?: boolean;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  icon,
  onBack,
  actions,
  date = false,
}) => (
  <header className="azals-ws-header">
    {onBack && (
      <button className="azals-ws-btn-back" onClick={onBack}>
        <ArrowLeft size={20} />
        Retour
      </button>
    )}
    <div className="azals-ws-title">
      {icon}
      <div>
        {subtitle && <span className="azals-ws-ref">{subtitle}</span>}
        <h1>{title}</h1>
      </div>
    </div>
    {date && (
      <div className="azals-ws-date">
        {new Date().toLocaleDateString('fr-FR', {
          weekday: 'long',
          day: 'numeric',
          month: 'long',
          year: 'numeric'
        })}
      </div>
    )}
    {actions && <div className="azals-ws-header__actions">{actions}</div>}
  </header>
);

// ============================================================
// STATS
// ============================================================

interface StatItem {
  label: string;
  value: string | number;
  variant?: 'default' | 'warning' | 'success' | 'danger';
}

export const Stats: React.FC<{ items: StatItem[] }> = ({ items }) => (
  <section className="azals-ws-stats">
    {items.map((item, i) => (
      <div key={i} className="azals-ws-stat">
        <span className="azals-ws-stat__label">{item.label}</span>
        <span className={`azals-ws-stat__value ${item.variant ? `azals-ws-stat__value--${item.variant}` : ''}`}>
          {item.value}
        </span>
      </div>
    ))}
  </section>
);

// ============================================================
// SEARCH BAR
// ============================================================

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  placeholder = 'Rechercher...',
}) => (
  <div className="azals-ws-search">
    <Search size={18} />
    <input
      type="text"
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  </div>
);

// ============================================================
// SIMPLE TABLE
// ============================================================

interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (row: T) => React.ReactNode;
  align?: 'left' | 'right' | 'center';
}

interface SimpleTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyField: keyof T;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
}

export function SimpleTable<T extends Record<string, any>>({
  columns,
  data,
  keyField,
  onRowClick,
  emptyMessage = 'Aucune donnée',
}: SimpleTableProps<T>) {
  return (
    <table className="azals-ws-table">
      <thead>
        <tr>
          {columns.map((col) => (
            <th key={String(col.key)} style={{ textAlign: col.align || 'left' }}>
              {col.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.length === 0 ? (
          <tr>
            <td colSpan={columns.length} className="azals-ws-table__empty">
              {emptyMessage}
            </td>
          </tr>
        ) : (
          data.map((row) => (
            <tr
              key={String(row[keyField])}
              onClick={() => onRowClick?.(row)}
              style={{ cursor: onRowClick ? 'pointer' : 'default' }}
            >
              {columns.map((col) => (
                <td key={String(col.key)} style={{ textAlign: col.align || 'left' }}>
                  {col.render ? col.render(row) : row[col.key as keyof T]}
                </td>
              ))}
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}

// ============================================================
// FORM FIELD
// ============================================================

interface FieldProps {
  label: string;
  icon?: React.ReactNode;
  full?: boolean;
  children: React.ReactNode;
}

export const Field: React.FC<FieldProps> = ({ label, icon, full, children }) => (
  <div className={`azals-ws-field ${full ? 'azals-ws-field--full' : ''}`}>
    <label>
      {icon}
      {label}
    </label>
    {children}
  </div>
);

// ============================================================
// INPUT
// ============================================================

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  variant?: 'default' | 'number';
}

export const Input: React.FC<InputProps> = ({ variant = 'default', className, ...props }) => (
  <input
    className={`azals-ws-input ${variant === 'number' ? 'azals-ws-input--number' : ''} ${className || ''}`}
    {...props}
  />
);

// ============================================================
// SELECT
// ============================================================

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  options: SelectOption[];
}

export const Select: React.FC<SelectProps> = ({ options, className, ...props }) => (
  <select className={`azals-ws-select ${className || ''}`} {...props}>
    {options.map((opt) => (
      <option key={opt.value} value={opt.value}>
        {opt.label}
      </option>
    ))}
  </select>
);

// ============================================================
// TEXTAREA
// ============================================================

export const Textarea: React.FC<React.TextareaHTMLAttributes<HTMLTextAreaElement>> = ({
  className,
  ...props
}) => (
  <textarea className={`azals-ws-textarea ${className || ''}`} {...props} />
);

// ============================================================
// VALUE DISPLAY
// ============================================================

interface ValueProps {
  children: React.ReactNode;
  variant?: 'default' | 'amount' | 'negative';
}

export const Value: React.FC<ValueProps> = ({ children, variant = 'default' }) => (
  <span className={`azals-ws-value ${variant !== 'default' ? `azals-ws-value--${variant}` : ''}`}>
    {children}
  </span>
);

// ============================================================
// BADGE
// ============================================================

interface BadgeProps {
  children: React.ReactNode;
  variant?: string;
  size?: 'sm' | 'lg';
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'default', size }) => (
  <span className={`azals-ws-badge azals-ws-badge--${variant} ${size === 'lg' ? 'azals-ws-badge--lg' : ''}`}>
    {children}
  </span>
);

// ============================================================
// PROGRESS BAR
// ============================================================

interface ProgressProps {
  value: number;
  size?: 'sm' | 'lg';
  showLabel?: boolean;
}

export const Progress: React.FC<ProgressProps> = ({ value, size, showLabel = true }) => (
  <div className={`azals-ws-progress ${size === 'lg' ? 'azals-ws-progress--lg' : ''}`}>
    <div className="azals-ws-progress__bar" style={{ width: `${Math.min(value, 100)}%` }} />
    {showLabel && <span>{Math.round(value)}%</span>}
  </div>
);

// ============================================================
// TOTALS
// ============================================================

interface TotalRow {
  label: string;
  value: string | number;
  isMain?: boolean;
  isNegative?: boolean;
}

export const Totals: React.FC<{ rows: TotalRow[] }> = ({ rows }) => (
  <section className="azals-ws-totals">
    {rows.map((row, i) => (
      <div
        key={i}
        className={`azals-ws-totals__row ${row.isMain ? 'azals-ws-totals__row--main' : ''}`}
      >
        <span>{row.label}</span>
        <span className={row.isNegative ? 'azals-ws-value--negative' : ''}>
          {row.value}
        </span>
      </div>
    ))}
  </section>
);

// ============================================================
// BUTTONS
// ============================================================

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'icon';
  icon?: React.ReactNode;
  loading?: boolean;
  success?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  icon,
  loading,
  success,
  children,
  className,
  disabled,
  ...props
}) => {
  const baseClass = variant === 'icon' ? 'azals-ws-btn-icon' : `azals-ws-btn-${variant}`;
  const successClass = success ? 'azals-ws-save--success' : '';

  return (
    <button
      className={`${baseClass} ${successClass} ${className || ''}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <Loader2 className="azals-ws-save__spinner" size={20} />
      ) : success ? (
        <Check size={20} />
      ) : (
        icon
      )}
      {children}
    </button>
  );
};

// ============================================================
// SECTION & GRID
// ============================================================

export const Section: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => <section className={`azals-ws-section ${className || ''}`}>{children}</section>;

export const Grid: React.FC<{ children: React.ReactNode; cols?: 2 | 3 | 4 }> = ({
  children,
  cols = 2,
}) => (
  <div className="azals-ws-grid" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
    {children}
  </div>
);

// ============================================================
// PAGE WRAPPER
// ============================================================

export const Page: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="azals-worksheet">{children}</div>
);

// ============================================================
// FOOTER
// ============================================================

export const Footer: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <footer className="azals-ws-footer">{children}</footer>
);

// ============================================================
// FORMATTERS (réexportés pour faciliter l'import)
// ============================================================

export const formatCurrency = (value?: number) => {
  if (value === undefined || value === null) return '0,00 €';
  return value.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' });
};

export const formatDate = (date?: string) => {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('fr-FR');
};

export const formatPercent = (value?: number) => {
  if (value === undefined || value === null) return '0%';
  return `${Math.round(value)}%`;
};

// ============================================================
// SMART FIELD SYSTEM (réexportés)
// ============================================================

export { SmartField, SmartForm } from './SmartField';
export type { SmartFieldProps, EntityConfig, CreateField, SelectOption } from './SmartField';
export { useFieldMode, useModulePermissions, MODULE_CAPABILITIES } from './useFieldMode';
export type { FieldMode, ContextMode, ModuleKey } from './useFieldMode';
export { PermissionsManager } from './PermissionsManager';
