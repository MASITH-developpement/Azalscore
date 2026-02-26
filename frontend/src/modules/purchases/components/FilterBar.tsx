/**
 * AZALSCORE Module - Purchases - Filter Bar
 * ==========================================
 * Barre de filtres pour les listes d'achats
 */

import React, { useState } from 'react';
import { Search, Filter, X } from 'lucide-react';
import { Button } from '@ui/actions';
import type { Supplier } from '../types';

// ============================================================================
// Types
// ============================================================================

export interface FilterState {
  search?: string;
  status?: string;
  supplier_id?: string;
  date_from?: string;
  date_to?: string;
}

interface FilterBarProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  suppliers?: Supplier[];
  statusOptions: { value: string; label: string }[];
  showSupplierFilter?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  onChange,
  suppliers = [],
  statusOptions,
  showSupplierFilter = true,
}) => {
  const [showFilters, setShowFilters] = useState(false);

  const hasActiveFilters = !!(
    filters.status ||
    filters.supplier_id ||
    filters.date_from ||
    filters.date_to
  );

  const clearFilters = () => {
    onChange({ search: filters.search });
  };

  return (
    <div className="azals-filter-bar">
      <div className="azals-filter-bar__search">
        <Search size={16} />
        <input
          type="text"
          placeholder="Rechercher..."
          value={filters.search || ''}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          className="azals-input"
        />
        {filters.search && (
          <button
            className="azals-filter-bar__clear"
            onClick={() => onChange({ ...filters, search: '' })}
          >
            <X size={14} />
          </button>
        )}
      </div>

      <div className="azals-filter-bar__actions">
        <Button
          variant="ghost"
          leftIcon={<Filter size={16} />}
          onClick={() => setShowFilters(!showFilters)}
        >
          Filtres {hasActiveFilters && '•'}
        </Button>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X size={14} /> Effacer
          </Button>
        )}
      </div>

      {showFilters && (
        <div className="azals-filter-bar__panel">
          <div className="azals-filter-bar__grid">
            <div className="azals-field">
              <label className="azals-field__label">Statut</label>
              <select
                className="azals-select"
                value={filters.status || ''}
                onChange={(e) => onChange({ ...filters, status: e.target.value || undefined })}
              >
                <option value="">Tous les statuts</option>
                {statusOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            {showSupplierFilter && suppliers.length > 0 && (
              <div className="azals-field">
                <label className="azals-field__label">Fournisseur</label>
                <select
                  className="azals-select"
                  value={filters.supplier_id || ''}
                  onChange={(e) => onChange({ ...filters, supplier_id: e.target.value || undefined })}
                >
                  <option value="">Tous les fournisseurs</option>
                  {suppliers.map((s) => (
                    <option key={s.id} value={s.id}>{s.code} - {s.name}</option>
                  ))}
                </select>
              </div>
            )}
            <div className="azals-field">
              <label className="azals-field__label">Date du</label>
              <input
                type="date"
                className="azals-input"
                value={filters.date_from || ''}
                onChange={(e) => onChange({ ...filters, date_from: e.target.value || undefined })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Date au</label>
              <input
                type="date"
                className="azals-input"
                value={filters.date_to || ''}
                onChange={(e) => onChange({ ...filters, date_to: e.target.value || undefined })}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FilterBar;
