/**
 * AZALSCORE Module - Invoicing - FilterBar
 * Barre de filtres pour les listes de documents
 */

import React, { useState } from 'react';
import { Search, Filter, FileSpreadsheet, X } from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button } from '@ui/actions';
import type { DocumentStatus } from '../types';
import type { DocumentFilters } from '../hooks';

interface FilterBarProps {
  filters: DocumentFilters;
  onChange: (filters: DocumentFilters) => void;
  onExport: () => void;
  isExporting?: boolean;
}

const FilterBar: React.FC<FilterBarProps> = ({ filters, onChange, onExport, isExporting }) => {
  const [showFilters, setShowFilters] = useState(false);

  return (
    <div className="azals-filter-bar">
      <div className="azals-filter-bar__search">
        <Search size={16} />
        <input
          type="text"
          placeholder="Rechercher par numero ou client..."
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
          Filtres
          {(filters.status || filters.date_from) && (
            <span className="azals-filter-bar__badge">!</span>
          )}
        </Button>

        <CapabilityGuard capability="invoicing.export">
          <Button
            variant="ghost"
            leftIcon={<FileSpreadsheet size={16} />}
            onClick={onExport}
            isLoading={isExporting}
          >
            Export CSV
          </Button>
        </CapabilityGuard>
      </div>

      {showFilters && (
        <div className="azals-filter-bar__panel">
          <div className="azals-filter-bar__field">
            <label htmlFor="inv-filter-status">Statut</label>
            <select
              id="inv-filter-status"
              value={filters.status || ''}
              onChange={(e) => onChange({
                ...filters,
                status: e.target.value as DocumentStatus || undefined
              })}
              className="azals-select"
            >
              <option value="">Tous</option>
              <option value="DRAFT">Brouillon</option>
              <option value="VALIDATED">Valide</option>
            </select>
          </div>

          <div className="azals-filter-bar__field">
            <label htmlFor="inv-filter-date-from">Date debut</label>
            <input
              id="inv-filter-date-from"
              type="date"
              value={filters.date_from || ''}
              onChange={(e) => onChange({ ...filters, date_from: e.target.value })}
              className="azals-input"
            />
          </div>

          <div className="azals-filter-bar__field">
            <label htmlFor="inv-filter-date-to">Date fin</label>
            <input
              id="inv-filter-date-to"
              type="date"
              value={filters.date_to || ''}
              onChange={(e) => onChange({ ...filters, date_to: e.target.value })}
              className="azals-input"
            />
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => onChange({})}
          >
            Reinitialiser
          </Button>
        </div>
      )}
    </div>
  );
};

export default FilterBar;
