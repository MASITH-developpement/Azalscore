/**
 * AZALSCORE - Module Documents Unifié
 * Sélecteur de partenaire avec recherche paginée
 *
 * Optimisations:
 * - Recherche avec debounce (300ms)
 * - Chargement de 50 résultats max
 * - Mémorisation des résultats
 */

import React, { useState, useCallback, useEffect, memo } from 'react';
import { Search, X, RefreshCw, ChevronDown } from 'lucide-react';
import { useTranslation } from '@core/i18n';
import { useCustomersLookup, useSuppliersLookup } from '../hooks';
import type { Customer, Supplier, Partner } from '../types';

// ============================================================
// TYPES
// ============================================================

interface PartnerSelectorProps {
  type: 'customer' | 'supplier';
  value: string;
  onChange: (partnerId: string) => void;
  disabled?: boolean;
  error?: string;
  required?: boolean;
}

// ============================================================
// HOOK - Debounce
// ============================================================

const useDebounce = (value: string, delay: number): string => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// ============================================================
// COMPOSANT
// ============================================================

export const PartnerSelector: React.FC<PartnerSelectorProps> = memo(({
  type,
  value,
  onChange,
  disabled = false,
  error,
  required = false,
}) => {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [selectedPartner, setSelectedPartner] = useState<Partner | null>(null);

  // Debounce la recherche pour éviter trop de requêtes
  const debouncedSearch = useDebounce(search, 300);

  // Hooks de données selon le type
  const {
    data: customers,
    isLoading: loadingCustomers,
    refetch: refetchCustomers,
  } = useCustomersLookup(type === 'customer' ? debouncedSearch : '');

  const {
    data: suppliers,
    isLoading: loadingSuppliers,
    refetch: refetchSuppliers,
  } = useSuppliersLookup(type === 'supplier' ? debouncedSearch : '');

  // Données selon le type
  const partners = type === 'customer' ? customers : suppliers;
  const isLoading = type === 'customer' ? loadingCustomers : loadingSuppliers;
  const refetch = type === 'customer' ? refetchCustomers : refetchSuppliers;

  // Labels selon le type
  const labelKey = type === 'customer'
    ? 'documents.form.customer'
    : 'documents.form.supplier';
  const placeholderKey = type === 'customer'
    ? 'documents.form.selectCustomer'
    : 'documents.form.selectSupplier';

  // Mettre à jour le partenaire sélectionné quand la valeur change
  useEffect(() => {
    if (value && partners) {
      const found = partners.find((p) => p.id === value);
      if (found) {
        setSelectedPartner(found as Partner);
      }
    } else {
      setSelectedPartner(null);
    }
  }, [value, partners]);

  // Sélectionner un partenaire
  const handleSelect = useCallback((partner: Partner) => {
    onChange(partner.id);
    setSelectedPartner(partner);
    setIsOpen(false);
    setSearch('');
  }, [onChange]);

  // Effacer la sélection
  const handleClear = useCallback(() => {
    onChange('');
    setSelectedPartner(null);
    setSearch('');
  }, [onChange]);

  return (
    <div className="azals-partner-selector">
      <label className="azals-field__label">
        {t(labelKey)} {required && '*'}
      </label>

      <div className="azals-partner-selector__control">
        {/* Affichage de la sélection ou dropdown */}
        {!isOpen ? (
          <button
            type="button"
            className={`azals-partner-selector__button ${error ? 'azals-partner-selector__button--error' : ''}`}
            onClick={() => !disabled && setIsOpen(true)}
            disabled={disabled}
          >
            {selectedPartner ? (
              <span className="azals-partner-selector__selected">
                <span className="azals-partner-selector__code">{selectedPartner.code}</span>
                <span className="azals-partner-selector__name">{selectedPartner.name}</span>
              </span>
            ) : (
              <span className="azals-partner-selector__placeholder">
                {t(placeholderKey)}
              </span>
            )}
            <ChevronDown size={16} />
          </button>
        ) : (
          <div className="azals-partner-selector__dropdown">
            {/* Champ de recherche */}
            <div className="azals-partner-selector__search">
              <Search size={16} />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t('common.search')}
                autoFocus
                className="azals-input"
              />
              <button
                type="button"
                className="azals-partner-selector__close"
                onClick={() => {
                  setIsOpen(false);
                  setSearch('');
                }}
              >
                <X size={16} />
              </button>
            </div>

            {/* Liste des résultats */}
            <div className="azals-partner-selector__list">
              {isLoading ? (
                <div className="azals-partner-selector__loading">
                  <RefreshCw size={16} className="animate-spin" />
                  <span>{t('common.loading')}</span>
                </div>
              ) : partners && partners.length > 0 ? (
                partners.map((partner) => (
                  <button
                    key={partner.id}
                    type="button"
                    className={`azals-partner-selector__item ${
                      partner.id === value ? 'azals-partner-selector__item--selected' : ''
                    }`}
                    onClick={() => handleSelect(partner as Partner)}
                  >
                    <span className="azals-partner-selector__code">{partner.code}</span>
                    <span className="azals-partner-selector__name">{partner.name}</span>
                    {partner.email && (
                      <span className="azals-partner-selector__email">{partner.email}</span>
                    )}
                  </button>
                ))
              ) : (
                <div className="azals-partner-selector__empty">
                  {t('partners.noPartners')}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Bouton pour effacer */}
        {selectedPartner && !disabled && !isOpen && (
          <button
            type="button"
            className="azals-partner-selector__clear"
            onClick={handleClear}
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Message d'erreur */}
      {error && <span className="azals-form-error">{error}</span>}
    </div>
  );
});

PartnerSelector.displayName = 'PartnerSelector';

export default PartnerSelector;
