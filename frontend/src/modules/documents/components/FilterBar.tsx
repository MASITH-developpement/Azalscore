/**
 * AZALSCORE - Module Documents Unifié
 * Barre de filtres universelle
 */

import React, { useState, useCallback, memo } from 'react';
import { Search, Filter, X, FileSpreadsheet } from 'lucide-react';
import { useTranslation } from '@core/i18n';
import { Button } from '@ui/actions';
import { CapabilityGuard } from '@core/capabilities';
import { STATUS_CONFIG, getStatusesForType } from '../constants';
import type { DocumentType, DocumentFilters, DocumentStatus, Partner } from '../types';

// ============================================================
// TYPES
// ============================================================

interface FilterBarProps {
  documentType: DocumentType;
  filters: DocumentFilters;
  onChange: (filters: DocumentFilters) => void;
  partners?: Partner[];
  onExport?: () => void;
  isExporting?: boolean;
  exportCapability?: string;
}

// ============================================================
// COMPOSANT
// ============================================================

export const FilterBar: React.FC<FilterBarProps> = memo(({
  documentType,
  filters,
  onChange,
  partners = [],
  onExport,
  isExporting,
  exportCapability = 'invoicing.export',
}) => {
  const { t } = useTranslation();
  const [showFilters, setShowFilters] = useState(false);

  // Vérifier si des filtres sont actifs
  const hasActiveFilters = !!(
    filters.status ||
    filters.partner_id ||
    filters.date_from ||
    filters.date_to
  );

  // Réinitialiser les filtres
  const clearFilters = useCallback(() => {
    onChange({ search: filters.search });
  }, [filters.search, onChange]);

  // Mettre à jour un filtre
  const updateFilter = useCallback(
    (key: keyof DocumentFilters, value: string | undefined) => {
      onChange({ ...filters, [key]: value || undefined });
    },
    [filters, onChange]
  );

  // Obtenir les statuts disponibles pour ce type de document
  const availableStatuses = getStatusesForType(documentType);

  return (
    <div className="azals-filter-bar">
      {/* Recherche */}
      <div className="azals-filter-bar__search">
        <Search size={16} />
        <input
          type="text"
          placeholder={t('documents.searchPlaceholder')}
          value={filters.search || ''}
          onChange={(e) => updateFilter('search', e.target.value)}
          className="azals-input"
        />
        {filters.search && (
          <button
            className="azals-filter-bar__clear"
            onClick={() => updateFilter('search', undefined)}
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Actions */}
      <div className="azals-filter-bar__actions">
        <Button
          variant="ghost"
          leftIcon={<Filter size={16} />}
          onClick={() => setShowFilters(!showFilters)}
        >
          {t('common.filters')}
          {hasActiveFilters && <span className="azals-filter-bar__badge">!</span>}
        </Button>

        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X size={14} /> {t('common.clear')}
          </Button>
        )}

        {onExport && (
          <CapabilityGuard capability={exportCapability}>
            <Button
              variant="ghost"
              leftIcon={<FileSpreadsheet size={16} />}
              onClick={onExport}
              isLoading={isExporting}
            >
              {t('documents.actions.exportCSV')}
            </Button>
          </CapabilityGuard>
        )}
      </div>

      {/* Panneau de filtres */}
      {showFilters && (
        <div className="azals-filter-bar__panel">
          <div className="azals-filter-bar__grid">
            {/* Statut */}
            <div className="azals-field">
              <label className="azals-field__label">{t('filters.status')}</label>
              <select
                className="azals-select"
                value={filters.status || ''}
                onChange={(e) => updateFilter('status', e.target.value)}
              >
                <option value="">{t('filters.allStatuses')}</option>
                {availableStatuses.map((status) => (
                  <option key={status} value={status}>
                    {t(STATUS_CONFIG[status]?.labelKey || status)}
                  </option>
                ))}
              </select>
            </div>

            {/* Partenaire */}
            {partners.length > 0 && (
              <div className="azals-field">
                <label className="azals-field__label">{t('filters.partner')}</label>
                <select
                  className="azals-select"
                  value={filters.partner_id || ''}
                  onChange={(e) => updateFilter('partner_id', e.target.value)}
                >
                  <option value="">{t('filters.allPartners')}</option>
                  {partners.map((partner) => (
                    <option key={partner.id} value={partner.id}>
                      {partner.code} - {partner.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Date début */}
            <div className="azals-field">
              <label className="azals-field__label">{t('filters.dateFrom')}</label>
              <input
                type="date"
                className="azals-input"
                value={filters.date_from || ''}
                onChange={(e) => updateFilter('date_from', e.target.value)}
              />
            </div>

            {/* Date fin */}
            <div className="azals-field">
              <label className="azals-field__label">{t('filters.dateTo')}</label>
              <input
                type="date"
                className="azals-input"
                value={filters.date_to || ''}
                onChange={(e) => updateFilter('date_to', e.target.value)}
              />
            </div>
          </div>

          <Button variant="ghost" size="sm" onClick={clearFilters}>
            {t('filters.reset')}
          </Button>
        </div>
      )}
    </div>
  );
});

FilterBar.displayName = 'FilterBar';

export default FilterBar;
