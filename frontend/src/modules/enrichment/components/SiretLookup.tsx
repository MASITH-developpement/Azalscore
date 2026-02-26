/**
 * AZALS Module - Auto-Enrichment - SiretLookup Component
 * =======================================================
 * Composant de recherche d'entreprise par SIRET/SIREN ou par nom.
 * Supporte l'autocomplete pour la recherche par nom.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { acceptEnrichment, searchCompanyByName } from '../api';
import { useSiretLookup, isValidSiret, isValidSiren } from '../hooks';
import type { CompanySuggestion , EnrichedContactFields, SiretLookupProps, RiskData } from '../types';

// ============================================================================
// COMPONENT
// ============================================================================

export function SiretLookup({
  value = '',
  onEnrich,
  onHistoryId,
  onRiskData,
  disabled = false,
  className = '',
}: SiretLookupProps): JSX.Element {
  const [inputValue, setInputValue] = useState(value ?? '');
  const [showPreview, setShowPreview] = useState(false);
  const [searchMode, setSearchMode] = useState<'siret' | 'name'>('siret');

  // Name search state
  const [suggestions, setSuggestions] = useState<CompanySuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const hookResult = useSiretLookup({
      debounceMs: 500,
      minLength: 9,
    });

  // Defensive: ensure hook result is properly destructured
  const {
    fields = null,
    isLoading = false,
    error = null,
    historyId = null,
    lookup = async () => {},
    reset = () => {},
    validationType = null
  } = hookResult ?? {};

  // Sync with external value
  useEffect(() => {
    if (value !== inputValue) {
      setInputValue(value);
    }
  }, [value]);

  // Notify parent of history ID
  useEffect(() => {
    if (historyId && onHistoryId) {
      onHistoryId(historyId);
    }
  }, [historyId, onHistoryId]);

  // Show preview when we have fields
  useEffect(() => {
    if (fields && Object.keys(fields).length > 0) {
      setShowPreview(true);
    }
  }, [fields]);

  // Notifier automatiquement le parent quand les données de risque arrivent
  useEffect(() => {
    if (fields && onRiskData) {
      if (fields._bodacc_risk_level || fields._risk_level) {
        onRiskData({
          level: fields._bodacc_risk_level || fields._risk_level,
          label: fields._bodacc_risk_label || fields._risk_label,
          reason: fields._bodacc_risk_reason || fields._risk_reason,
          score: fields._bodacc_risk_score ?? fields._risk_score,
          alerts: fields._bodacc_critical_alerts || [],
          sources: fields._sources || [],
        });
      } else {
        onRiskData(null);
      }
    }
  }, [fields, onRiskData]);

  // Close suggestions when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Detect search mode based on input
  const detectSearchMode = useCallback((val: string): 'siret' | 'name' => {
    const clean = val.replace(/\s/g, '');
    // If it starts with digits or is all digits, treat as SIRET/SIREN
    if (/^\d+$/.test(clean) && clean.length <= 14) {
      return 'siret';
    }
    // Otherwise treat as name search
    return 'name';
  }, []);

  const handleChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setInputValue(newValue);

      const mode = detectSearchMode(newValue);
      setSearchMode(mode);

      if (mode === 'siret') {
        // SIRET/SIREN mode
        setShowSuggestions(false);
        setSuggestions([]);
        lookup(newValue);
      } else {
        // Name search mode
        reset();
        setShowPreview(false);

        // Debounce name search
        if (searchTimeoutRef.current) {
          clearTimeout(searchTimeoutRef.current);
        }

        if (newValue.length >= 2) {
          setIsSearching(true);
          searchTimeoutRef.current = setTimeout(async () => {
            try {
              const results = await searchCompanyByName(newValue);
              const validResults = Array.isArray(results) ? results : [];
              setSuggestions(validResults);
              setShowSuggestions(validResults.length > 0);
            } catch (err) {
              console.error('Error searching companies:', err);
              setSuggestions([]);
            } finally {
              setIsSearching(false);
            }
          }, 300);
        } else {
          setSuggestions([]);
          setShowSuggestions(false);
        }
      }
    },
    [lookup, reset, detectSearchMode]
  );

  const handleSelectSuggestion = useCallback((suggestion: CompanySuggestion) => {
    const siretValue = suggestion.siret || suggestion.siren;
    setInputValue(siretValue);
    setShowSuggestions(false);
    setSuggestions([]);
    setSearchMode('siret');

    // Declencher un lookup SIRET pour obtenir les donnees BODACC
    // Le lookup appellera le backend qui verifie BODACC automatiquement
    if (siretValue) {
      lookup(siretValue);
    }
  }, [lookup]);

  const handleAccept = useCallback(async () => {
    if (fields && historyId) {
      try {
        await acceptEnrichment(historyId, {
          accepted_fields: Object.keys(fields),
          rejected_fields: [],
        });
        onEnrich?.(fields);
        setShowPreview(false);
        reset();
      } catch (err) {
        console.error('Error accepting enrichment:', err);
      }
    }
  }, [fields, historyId, onEnrich, reset]);

  const handleReject = useCallback(() => {
    setShowPreview(false);
    reset();
  }, [reset]);

  // Validation status
  const getValidationStatus = (): 'valid' | 'invalid' | 'pending' | null => {
    if (searchMode === 'name') return null;
    if (!inputValue || (inputValue?.length ?? 0) < 9) return null;
    if (isLoading) return 'pending';

    const clean = inputValue.replace(/\s/g, '');
    if (clean.length === 14 && isValidSiret(clean)) return 'valid';
    if (clean.length === 9 && isValidSiren(clean)) return 'valid';
    if (clean.length >= 9) return 'invalid';

    return null;
  };

  const validationStatus = getValidationStatus();

  return (
    <div className={`siret-lookup ${className}`} ref={wrapperRef}>
      {/* Input Field */}
      <div className="siret-lookup__input-wrapper">
        <input
          type="text"
          value={inputValue}
          onChange={handleChange}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          placeholder="SIRET, SIREN ou nom d'entreprise"
          disabled={disabled}
          className={`
            siret-lookup__input
            ${validationStatus === 'valid' ? 'siret-lookup__input--valid' : ''}
            ${validationStatus === 'invalid' ? 'siret-lookup__input--invalid' : ''}
            ${isLoading || isSearching ? 'siret-lookup__input--loading' : ''}
          `}
        />

        {/* Status Indicator */}
        <div className="siret-lookup__status">
          {(isLoading || isSearching) && (
            <span className="siret-lookup__spinner" title="Recherche en cours...">
              &#8635;
            </span>
          )}
          {validationStatus === 'valid' && !isLoading && (
            <span className="siret-lookup__check" title={validationType?.toUpperCase()}>
              &#10003;
            </span>
          )}
          {validationStatus === 'invalid' && !isLoading && (
            <span className="siret-lookup__error" title="Numero invalide">
              &#10007;
            </span>
          )}
          {searchMode === 'name' && !isSearching && (inputValue?.length ?? 0) >= 2 && (
            <span className="siret-lookup__search-icon" title="Recherche par nom">
              &#128269;
            </span>
          )}
        </div>
      </div>

      {/* Suggestions Dropdown (Name Search) */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="siret-lookup__suggestions">
          {suggestions.map((suggestion, index) => (
            <div
              key={`${suggestion.siret}-${index}`}
              className="siret-lookup__suggestion"
              onClick={() => handleSelectSuggestion(suggestion)}
            >
              <div className="siret-lookup__suggestion-name">
                {suggestion.name}
              </div>
              <div className="siret-lookup__suggestion-details">
                <span>{suggestion.siret}</span>
                {suggestion.city && <span> • {suggestion.postal_code} {suggestion.city}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="siret-lookup__error-message">
          {error.message}
        </div>
      )}

      {/* ALERTE RISQUE BODACC */}
      {showPreview && fields && (fields._bodacc_risk_level === 'critical' || fields._bodacc_risk_level === 'high' || fields._risk_level === 'critical' || fields._risk_level === 'high') && (
        <div className={`siret-lookup__risk-alert siret-lookup__risk-alert--${fields._bodacc_risk_level || fields._risk_level}`}>
          <div className="siret-lookup__risk-icon">
            {(fields._bodacc_risk_level === 'critical' || fields._risk_level === 'critical') ? '⛔' : '⚠️'}
          </div>
          <div className="siret-lookup__risk-content">
            <div className="siret-lookup__risk-title">
              {(fields._bodacc_risk_level === 'critical' || fields._risk_level === 'critical')
                ? 'RISQUE CRITIQUE - Ne pas travailler avec cette entreprise'
                : 'RISQUE ELEVE - Vigilance requise'}
            </div>
            <div className="siret-lookup__risk-reason">
              {fields._bodacc_risk_reason || fields._risk_reason || 'Alerte BODACC detectee'}
            </div>
            {fields._bodacc_critical_alerts && fields._bodacc_critical_alerts.length > 0 && (
              <div className="siret-lookup__risk-details">
                {fields._bodacc_critical_alerts.map((alert: any, idx: number) => (
                  <div key={idx} className="siret-lookup__risk-detail">
                    • {alert.type} ({alert.date})
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Preview Panel */}
      {showPreview && fields && (
        <div className="siret-lookup__preview">
          <div className="siret-lookup__preview-header">
            <span>Donnees trouvees</span>
            <span className="siret-lookup__preview-source">
              Source: INSEE + BODACC
            </span>
          </div>

          <div className="siret-lookup__preview-fields">
            {fields.name && (
              <div className="siret-lookup__preview-field">
                <label>Raison sociale</label>
                <span>{fields.name}</span>
              </div>
            )}
            {fields.legal_form && (
              <div className="siret-lookup__preview-field">
                <label>Forme juridique</label>
                <span>{fields.legal_form}</span>
              </div>
            )}
            {fields.address_line1 && (
              <div className="siret-lookup__preview-field">
                <label>Adresse</label>
                <span>
                  {fields.address_line1}
                  {fields.postal_code && fields.city && (
                    <>, {fields.postal_code} {fields.city}</>
                  )}
                </span>
              </div>
            )}
            {fields.naf_code && (
              <div className="siret-lookup__preview-field">
                <label>Code NAF</label>
                <span>{fields.naf_code} - {fields.naf_label}</span>
              </div>
            )}
            {/* Score de risque */}
            {(fields._bodacc_risk_level || fields._risk_level) && (
              <div className="siret-lookup__preview-field">
                <label>Score risque</label>
                <span className={`siret-lookup__risk-badge siret-lookup__risk-badge--${fields._bodacc_risk_level || fields._risk_level}`}>
                  {fields._bodacc_risk_label || fields._risk_label || (fields._bodacc_risk_level || fields._risk_level)}
                </span>
              </div>
            )}
          </div>

          <div className="siret-lookup__preview-actions">
            <button
              type="button"
              onClick={handleAccept}
              className="siret-lookup__btn siret-lookup__btn--accept"
            >
              Utiliser ces donnees
            </button>
            <button
              type="button"
              onClick={handleReject}
              className="siret-lookup__btn siret-lookup__btn--reject"
            >
              Ignorer
            </button>
          </div>
        </div>
      )}

      <style>{`
        .siret-lookup {
          position: relative;
        }

        .siret-lookup__input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .siret-lookup__input {
          width: 100%;
          padding: 0.5rem 2.5rem 0.5rem 0.75rem;
          border: 1px solid #d1d5db;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          transition: border-color 0.15s, box-shadow 0.15s;
        }

        .siret-lookup__input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .siret-lookup__input--valid {
          border-color: #10b981;
        }

        .siret-lookup__input--invalid {
          border-color: #ef4444;
        }

        .siret-lookup__input--loading {
          background-color: #f9fafb;
        }

        .siret-lookup__status {
          position: absolute;
          right: 0.75rem;
          display: flex;
          align-items: center;
        }

        .siret-lookup__spinner {
          animation: spin 1s linear infinite;
          color: #6b7280;
        }

        .siret-lookup__check {
          color: #10b981;
          font-weight: bold;
        }

        .siret-lookup__error {
          color: #ef4444;
          font-weight: bold;
        }

        .siret-lookup__search-icon {
          color: #6b7280;
          font-size: 0.875rem;
        }

        .siret-lookup__error-message {
          margin-top: 0.25rem;
          font-size: 0.75rem;
          color: #ef4444;
        }

        /* Suggestions Dropdown */
        .siret-lookup__suggestions {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          z-index: 50;
          margin-top: 0.25rem;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          max-height: 300px;
          overflow-y: auto;
        }

        .siret-lookup__suggestion {
          padding: 0.75rem;
          cursor: pointer;
          border-bottom: 1px solid #f3f4f6;
          transition: background-color 0.15s;
        }

        .siret-lookup__suggestion:last-child {
          border-bottom: none;
        }

        .siret-lookup__suggestion:hover {
          background-color: #f3f4f6;
        }

        .siret-lookup__suggestion-name {
          font-weight: 500;
          font-size: 0.875rem;
          color: #111827;
        }

        .siret-lookup__suggestion-details {
          font-size: 0.75rem;
          color: #6b7280;
          margin-top: 0.25rem;
        }

        .siret-lookup__preview {
          margin-top: 0.5rem;
          padding: 1rem;
          background: #f9fafb;
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
        }

        .siret-lookup__preview-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.75rem;
          font-weight: 600;
          font-size: 0.875rem;
        }

        .siret-lookup__preview-source {
          font-size: 0.75rem;
          color: #6b7280;
          font-weight: normal;
        }

        .siret-lookup__preview-fields {
          display: grid;
          gap: 0.5rem;
        }

        .siret-lookup__preview-field {
          display: grid;
          grid-template-columns: 8rem 1fr;
          gap: 0.5rem;
          font-size: 0.875rem;
        }

        .siret-lookup__preview-field label {
          color: #6b7280;
        }

        .siret-lookup__preview-actions {
          display: flex;
          gap: 0.5rem;
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #e5e7eb;
        }

        .siret-lookup__btn {
          padding: 0.5rem 1rem;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: background-color 0.15s;
        }

        .siret-lookup__btn--accept {
          background: #3b82f6;
          color: white;
          border: none;
        }

        .siret-lookup__btn--accept:hover {
          background: #2563eb;
        }

        .siret-lookup__btn--reject {
          background: white;
          color: #374151;
          border: 1px solid #d1d5db;
        }

        .siret-lookup__btn--reject:hover {
          background: #f3f4f6;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        /* Risk Alert Styles */
        .siret-lookup__risk-alert {
          display: flex;
          gap: 0.75rem;
          margin-top: 0.5rem;
          padding: 1rem;
          border-radius: 0.5rem;
          animation: pulse-alert 2s infinite;
        }

        .siret-lookup__risk-alert--critical {
          background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
          border: 2px solid #ef4444;
        }

        .siret-lookup__risk-alert--high {
          background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
          border: 2px solid #f59e0b;
        }

        .siret-lookup__risk-icon {
          font-size: 1.5rem;
          flex-shrink: 0;
        }

        .siret-lookup__risk-content {
          flex: 1;
        }

        .siret-lookup__risk-title {
          font-weight: 700;
          font-size: 0.875rem;
          margin-bottom: 0.25rem;
        }

        .siret-lookup__risk-alert--critical .siret-lookup__risk-title {
          color: #dc2626;
        }

        .siret-lookup__risk-alert--high .siret-lookup__risk-title {
          color: #d97706;
        }

        .siret-lookup__risk-reason {
          font-size: 0.875rem;
          color: #374151;
          font-weight: 500;
        }

        .siret-lookup__risk-details {
          margin-top: 0.5rem;
          font-size: 0.75rem;
          color: #6b7280;
        }

        .siret-lookup__risk-detail {
          margin-top: 0.125rem;
        }

        .siret-lookup__risk-badge {
          display: inline-block;
          padding: 0.125rem 0.5rem;
          border-radius: 9999px;
          font-size: 0.75rem;
          font-weight: 600;
        }

        .siret-lookup__risk-badge--critical {
          background: #fee2e2;
          color: #dc2626;
        }

        .siret-lookup__risk-badge--high {
          background: #fef3c7;
          color: #d97706;
        }

        .siret-lookup__risk-badge--none,
        .siret-lookup__risk-badge--low {
          background: #d1fae5;
          color: #059669;
        }

        @keyframes pulse-alert {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.85; }
        }
      `}</style>
    </div>
  );
}

export default SiretLookup;
