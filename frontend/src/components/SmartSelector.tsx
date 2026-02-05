/**
 * AZALSCORE - SmartSelector Component
 * ====================================
 *
 * Composant réutilisable pour sélectionner ou créer des entités.
 *
 * Fonctionnalités:
 * - "Nouveau X" en premier dans le dropdown
 * - Recherche intégrée
 * - Formulaire de création inline
 * - Auto-sélection après création
 */

import React, { useState, useMemo, useRef, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ChevronDown, Plus, Check, Loader2, X, Search } from 'lucide-react';
import { api } from '@core/api-client';

// ============================================================
// TYPES
// ============================================================

export interface SelectorItem {
  id: string;
  name: string;
  code?: string;
  email?: string;
  [key: string]: any;
}

export interface FieldConfig {
  key: string;
  label: string;
  type?: 'text' | 'email' | 'tel' | 'number';
  required?: boolean;
  placeholder?: string;
}

export interface SmartSelectorProps<T extends SelectorItem> {
  // Data
  items: T[];
  value: string;
  onChange: (value: string, item?: T) => void;

  // Display
  label?: string;
  placeholder?: string;
  displayField?: keyof T;
  secondaryField?: keyof T;

  // Creation
  entityName: string;
  entityIcon?: React.ReactNode;
  createEndpoint: string;
  createFields: FieldConfig[];
  onCreated?: (item: T) => void;

  // Options
  disabled?: boolean;
  error?: string;
  allowCreate?: boolean;
  queryKeys?: string[];
}

// ============================================================
// COMPONENT
// ============================================================

export function SmartSelector<T extends SelectorItem>({
  items,
  value,
  onChange,
  label,
  placeholder = 'Sélectionner...',
  displayField = 'name' as keyof T,
  secondaryField,
  entityName,
  entityIcon,
  createEndpoint,
  createFields,
  onCreated,
  disabled = false,
  error,
  allowCreate = true,
  queryKeys = [],
}: SmartSelectorProps<T>) {
  const queryClient = useQueryClient();
  const containerRef = useRef<HTMLDivElement>(null);

  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [createError, setCreateError] = useState('');

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setShowCreate(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter items based on search
  const filtered = useMemo(() => {
    if (!search) return items.slice(0, 30);
    const lower = search.toLowerCase();
    return items.filter(item =>
      String(item[displayField] || '').toLowerCase().includes(lower) ||
      (item.code && item.code.toLowerCase().includes(lower)) ||
      (item.email && item.email.toLowerCase().includes(lower))
    ).slice(0, 30);
  }, [items, search, displayField]);

  // Get selected item
  const selectedItem = useMemo(() =>
    items.find(item => item.id === value),
    [items, value]
  );

  // Create mutation
  const createMutation = useMutation({
    mutationFn: async (data: Record<string, any>) => {
      const payload: Record<string, any> = { ...data };
      // Convert number fields
      createFields.forEach(field => {
        if (field.type === 'number' && data[field.key]) {
          payload[field.key] = parseFloat(data[field.key]);
        }
      });
      const response = await api.post<T>(createEndpoint, payload);
      return response as unknown as T;
    },
    onSuccess: (newItem) => {
      // Invalidate caches
      queryKeys.forEach(key => {
        queryClient.invalidateQueries({ queryKey: [key] });
      });
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.invalidateQueries({ queryKey: ['suppliers'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      queryClient.invalidateQueries({ queryKey: ['partners'] });

      // Select the new item
      onChange(newItem.id, newItem);
      onCreated?.(newItem);

      // Reset form
      setShowCreate(false);
      setIsOpen(false);
      setFormData({});
      setCreateError('');
    },
    onError: (err: any) => {
      setCreateError(err.message || `Erreur lors de la création`);
    },
  });

  const handleCreate = () => {
    // Validate required fields
    const missingFields = createFields
      .filter(f => f.required && !formData[f.key]?.trim())
      .map(f => f.label);

    if (missingFields.length > 0) {
      setCreateError(`Champs obligatoires : ${missingFields.join(', ')}`);
      return;
    }

    setCreateError('');
    createMutation.mutate(formData);
  };

  const handleSelect = (item: T) => {
    onChange(item.id, item);
    setIsOpen(false);
    setSearch('');
  };

  return (
    <div className="azals-smart-selector" ref={containerRef}>
      {label && <label className="azals-smart-selector__label">{label}</label>}

      {/* Selected value display */}
      <div
        className={`azals-smart-selector__trigger ${disabled ? 'azals-smart-selector__disabled' : ''} ${error ? 'azals-smart-selector__error' : ''}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        role="combobox"
        tabIndex={0}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        onKeyDown={(e) => {
          if (disabled) return;
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsOpen(!isOpen);
          } else if (e.key === 'Escape') {
            setIsOpen(false);
          } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            setIsOpen(true);
          }
        }}
      >
        {selectedItem ? (
          <div className="azals-smart-selector__value">
            <span className="azals-smart-selector__name">{String(selectedItem[displayField])}</span>
            {secondaryField && selectedItem[secondaryField] && (
              <span className="azals-smart-selector__secondary">{String(selectedItem[secondaryField])}</span>
            )}
          </div>
        ) : (
          <span className="azals-smart-selector__placeholder">{placeholder}</span>
        )}
        <ChevronDown size={18} className={isOpen ? 'azals-smart-selector__rotate' : ''} />
      </div>

      {error && <span className="azals-smart-selector__error">{error}</span>}

      {/* Dropdown */}
      {isOpen && (
        <div className="azals-smart-selector__dropdown">
          {/* Create new option */}
          {allowCreate && (
            <button
              type="button"
              className="azals-smart-selector__new"
              onClick={() => setShowCreate(!showCreate)}
            >
              {entityIcon || <Plus size={16} />}
              <span>Nouveau {entityName}</span>
              <Plus size={14} className="azals-smart-selector__plus" />
            </button>
          )}

          {/* Create form */}
          {showCreate && (
            <div className="azals-smart-selector__create">
              {createError && (
                <div className="azals-smart-selector__create-error">{createError}</div>
              )}

              {createFields.map((field, index) => (
                <input
                  key={field.key}
                  type={field.type || 'text'}
                  placeholder={`${field.label}${field.required ? ' *' : ''}`}
                  value={formData[field.key] || ''}
                  onChange={e => setFormData({ ...formData, [field.key]: e.target.value })}
                  autoFocus={index === 0}
                />
              ))}

              <div className="azals-smart-selector__create-actions">
                <button
                  type="button"
                  onClick={() => { setShowCreate(false); setCreateError(''); setFormData({}); }}
                >
                  Annuler
                </button>
                <button
                  type="button"
                  className="azals-smart-selector__primary"
                  onClick={handleCreate}
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending ? (
                    <Loader2 size={14} className="azals-smart-selector__spin" />
                  ) : (
                    <Check size={14} />
                  )}
                  Créer
                </button>
              </div>
            </div>
          )}

          {/* Search */}
          {!showCreate && (
            <>
              <div className="azals-smart-selector__search">
                <Search size={14} />
                <input
                  type="text"
                  placeholder="Rechercher..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  autoFocus
                />
                {search && (
                  <button onClick={() => setSearch('')}>
                    <X size={14} />
                  </button>
                )}
              </div>

              {/* Items list */}
              <div className="azals-smart-selector__list" role="listbox">
                {filtered.length === 0 ? (
                  <div className="azals-smart-selector__empty">
                    Aucun résultat
                  </div>
                ) : (
                  filtered.map(item => (
                    <button
                      type="button"
                      key={item.id}
                      role="option"
                      aria-selected={item.id === value}
                      className={`azals-smart-selector__item ${item.id === value ? 'azals-smart-selector__selected' : ''}`}
                      onClick={() => handleSelect(item)}
                    >
                      <span className="azals-smart-selector__name">{String(item[displayField])}</span>
                      {item.code && <span className="azals-smart-selector__code">{item.code}</span>}
                      {item.id === value && <Check size={14} className="azals-smart-selector__check" />}
                    </button>
                  ))
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default SmartSelector;
