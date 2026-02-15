/**
 * AZALSCORE - SmartField
 * ======================
 *
 * Composant universel qui gère automatiquement:
 * - Mode LECTURE (view) : affiche la valeur
 * - Mode ÉDITION (edit) : champ modifiable
 * - Mode CRÉATION (create) : champ vide modifiable
 *
 * Les permissions utilisateur contrôlent les modes disponibles.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, X, Search, Check } from 'lucide-react';
import { api } from '@core/api-client';
import { useModulePermissions, type FieldMode } from './useFieldMode';

export { useModulePermissions, useFieldMode, MODULE_CAPABILITIES } from './useFieldMode';
export type { FieldMode, ContextMode, ModuleKey } from './useFieldMode';

// ============================================================
// TYPES
// ============================================================

export type FieldType =
  | 'text'
  | 'number'
  | 'date'
  | 'select'
  | 'textarea'
  | 'email'
  | 'tel'
  | 'entity';

export interface SelectOption {
  value: string;
  label: string;
}

export interface EntityConfig {
  endpoint: string;           // ex: '/v3/partners/clients'
  displayField: string;       // ex: 'name'
  secondaryField?: string;    // ex: 'code'
  searchField?: string;       // ex: 'search'
  createFields?: CreateField[]; // champs pour création inline
}

export interface CreateField {
  key: string;
  label: string;
  type?: 'text' | 'email' | 'tel';
  required?: boolean;
  autoGenerate?: boolean;     // génère automatiquement (ex: code)
}

export interface SmartFieldProps {
  // Core
  label: string;
  value: any;
  onChange?: (value: any) => void;

  // Type & Mode
  type?: FieldType;
  mode?: FieldMode;

  // Options
  options?: SelectOption[];   // pour type='select'
  entity?: EntityConfig;      // pour type='entity'

  // Display
  icon?: React.ReactNode;
  placeholder?: string;
  full?: boolean;             // pleine largeur

  // Validation
  required?: boolean;
  min?: number;
  max?: number;
  step?: number;

  // Formatters
  formatValue?: (value: any) => string;
}

// ============================================================
// ENTITY SELECT (sélecteur d'entité avec création inline)
// ============================================================

interface EntitySelectProps {
  value: string;
  onChange: (id: string, displayValue: string) => void;
  config: EntityConfig;
  mode: FieldMode;
  placeholder?: string;
}

const EntitySelect: React.FC<EntitySelectProps> = ({
  value,
  onChange,
  config,
  mode,
  placeholder = 'Sélectionner...'
}) => {
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState<Record<string, string>>({});
  const [search, setSearch] = useState('');

  // Charger les entités
  const { data: items = [], isLoading } = useQuery({
    queryKey: [config.endpoint, search],
    queryFn: async () => {
      const params = new URLSearchParams({ page_size: '100' });
      if (search && config.searchField) {
        params.set(config.searchField, search);
      }
      const res = await api.get(`${config.endpoint}?${params}`);
      return (res as any).items || [];
    },
  });

  // Mutation création
  const createMutation = useMutation({
    mutationFn: async (data: Record<string, string>) => {
      return api.post(config.endpoint, data);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [config.endpoint] });
    },
  });

  // Mode lecture seule
  if (mode === 'view') {
    const item = items.find((i: any) => i.id === value);
    const display = item ? item[config.displayField] : '-';
    return <span className="azals-sf-value">{display}</span>;
  }

  // Création inline
  const handleCreate = async () => {
    if (!config.createFields) return;

    // Générer les champs auto
    const payload: Record<string, string> = { ...createForm };
    for (const field of config.createFields) {
      if (field.autoGenerate && !payload[field.key]) {
        payload[field.key] = `${field.key.toUpperCase()}-${Date.now().toString(36).toUpperCase()}`;
      }
    }

    const res = await createMutation.mutateAsync(payload);
    const created = res as any;
    onChange(created.id, created[config.displayField]);
    setShowCreate(false);
    setCreateForm({});
  };

  // Formulaire création
  if (showCreate && config.createFields) {
    return (
      <div className="azals-sf-create">
        <div className="azals-sf-create__header">
          <span>Nouveau</span>
          <button type="button" onClick={() => setShowCreate(false)}>
            <X size={16} />
          </button>
        </div>
        <div className="azals-sf-create__fields">
          {config.createFields.filter(f => !f.autoGenerate).map(field => (
            <input
              key={field.key}
              type={field.type || 'text'}
              placeholder={field.label + (field.required ? ' *' : '')}
              value={createForm[field.key] || ''}
              onChange={(e) => setCreateForm({ ...createForm, [field.key]: e.target.value })}
              className="azals-sf-input"
            />
          ))}
        </div>
        <div className="azals-sf-create__actions">
          <button type="button" className="azals-sf-btn azals-sf-btn--ghost" onClick={() => setShowCreate(false)}>
            Annuler
          </button>
          <button
            type="button"
            className="azals-sf-btn azals-sf-btn--primary"
            onClick={handleCreate}
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? '...' : 'Créer'}
          </button>
        </div>
      </div>
    );
  }

  // Sélecteur
  return (
    <div className="azals-sf-entity">
      <select
        className="azals-sf-select"
        value={value || ''}
        onChange={(e) => {
          const item = items.find((i: any) => i.id === e.target.value);
          if (item) onChange(item.id, item[config.displayField]);
        }}
        disabled={isLoading}
      >
        <option value="">{isLoading ? 'Chargement...' : placeholder}</option>
        {items.map((item: any) => (
          <option key={item.id} value={item.id}>
            {config.secondaryField && item[config.secondaryField]
              ? `${item[config.secondaryField]} - ${item[config.displayField]}`
              : item[config.displayField]
            }
          </option>
        ))}
      </select>
      {config.createFields && (
        <button
          type="button"
          className="azals-sf-entity__add"
          onClick={() => setShowCreate(true)}
          title="Créer nouveau"
        >
          <Plus size={18} />
        </button>
      )}
    </div>
  );
};

// ============================================================
// SMART FIELD
// ============================================================

export const SmartField: React.FC<SmartFieldProps> = ({
  label,
  value,
  onChange,
  type = 'text',
  mode = 'view',
  options,
  entity,
  icon,
  placeholder,
  full,
  required,
  min,
  max,
  step,
  formatValue,
}) => {
  // Formatage de la valeur pour affichage
  const displayValue = () => {
    if (formatValue) return formatValue(value);
    if (value === undefined || value === null || value === '') return '-';
    if (type === 'date' && value) {
      return new Date(value).toLocaleDateString('fr-FR');
    }
    if (type === 'number' && typeof value === 'number') {
      return value.toLocaleString('fr-FR');
    }
    if (type === 'select' && options) {
      const opt = options.find(o => o.value === value);
      return opt?.label || value;
    }
    return String(value);
  };

  // Rendu du champ selon le mode
  const renderField = () => {
    // Mode lecture
    if (mode === 'view') {
      if (type === 'entity' && entity) {
        return <EntitySelect value={value} onChange={() => {}} config={entity} mode="view" />;
      }
      return <span className="azals-sf-value">{displayValue()}</span>;
    }

    // Mode édition/création
    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
      if (!onChange) return;

      let newValue: any = e.target.value;
      if (type === 'number') {
        newValue = e.target.value === '' ? '' : parseFloat(e.target.value);
      }
      onChange(newValue);
    };

    // Entity select
    if (type === 'entity' && entity) {
      return (
        <EntitySelect
          value={value}
          onChange={(id, display) => onChange?.(id)}
          config={entity}
          mode={mode}
          placeholder={placeholder}
        />
      );
    }

    // Select
    if (type === 'select' && options) {
      return (
        <select className="azals-sf-select" value={value || ''} onChange={handleChange}>
          {!required && <option value="">--</option>}
          {options.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      );
    }

    // Textarea
    if (type === 'textarea') {
      return (
        <textarea
          className="azals-sf-textarea"
          value={value || ''}
          onChange={handleChange}
          placeholder={placeholder}
          rows={3}
        />
      );
    }

    // Input standard
    const inputType = type === 'number' ? 'number' : type === 'date' ? 'date' : type === 'email' ? 'email' : type === 'tel' ? 'tel' : 'text';

    return (
      <input
        type={inputType}
        className="azals-sf-input"
        value={value ?? ''}
        onChange={handleChange}
        placeholder={placeholder}
        required={required}
        min={min}
        max={max}
        step={step}
      />
    );
  };

  return (
    <div className={`azals-sf-field ${full ? 'azals-sf-field--full' : ''}`}>
      <label className="azals-sf-label">
        {icon && <span className="azals-sf-icon">{icon}</span>}
        {label}
        {required && mode !== 'view' && <span className="azals-sf-required">*</span>}
      </label>
      {renderField()}
    </div>
  );
};

// ============================================================
// SMART FORM (conteneur de formulaire)
// ============================================================

interface SmartFormProps {
  mode: FieldMode;
  children: React.ReactNode;
  onSubmit?: () => void;
  onCancel?: () => void;
  submitLabel?: string;
  loading?: boolean;
  success?: boolean;
}

export const SmartForm: React.FC<SmartFormProps> = ({
  mode,
  children,
  onSubmit,
  onCancel,
  submitLabel = 'Enregistrer',
  loading,
  success,
}) => {
  return (
    <div className="azals-sf-form">
      <div className="azals-sf-form__fields">
        {children}
      </div>
      {mode !== 'view' && onSubmit && (
        <div className="azals-sf-form__actions">
          {onCancel && (
            <button type="button" className="azals-sf-btn azals-sf-btn--ghost" onClick={onCancel}>
              Annuler
            </button>
          )}
          <button
            type="button"
            className={`azals-sf-btn azals-sf-btn--primary ${success ? 'azals-sf-btn--success' : ''}`}
            onClick={onSubmit}
            disabled={loading}
          >
            {loading ? '...' : success ? <><Check size={16} /> OK</> : submitLabel}
          </button>
        </div>
      )}
    </div>
  );
};

// ============================================================
// EXPORTS
// ============================================================

export default SmartField;
