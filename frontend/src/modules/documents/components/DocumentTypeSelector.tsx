/**
 * AZALSCORE - Module Documents Unifié
 * Sélecteur de type de document
 */

import React, { memo } from 'react';
import { FileText, ShoppingCart, Receipt, CreditCard, FileCheck } from 'lucide-react';
import { useTranslation } from '@core/i18n';
import { DOCUMENT_TYPE_CONFIG } from '../constants';
import type { DocumentType, DocumentCategory } from '../types';

// ============================================================
// TYPES
// ============================================================

interface DocumentTypeSelectorProps {
  value: DocumentType;
  onChange: (type: DocumentType) => void;
  category?: DocumentCategory;
  disabled?: boolean;
}

// ============================================================
// ICÔNES PAR TYPE
// ============================================================

const TYPE_ICONS: Record<DocumentType, React.ReactNode> = {
  QUOTE: <FileText size={20} />,
  INVOICE: <Receipt size={20} />,
  CREDIT_NOTE: <CreditCard size={20} />,
  PURCHASE_ORDER: <ShoppingCart size={20} />,
  PURCHASE_INVOICE: <FileCheck size={20} />,
};

// ============================================================
// COMPOSANT
// ============================================================

export const DocumentTypeSelector: React.FC<DocumentTypeSelectorProps> = memo(({
  value,
  onChange,
  category,
  disabled = false,
}) => {
  const { t } = useTranslation();

  // Filtrer les types par catégorie si spécifiée
  const types = Object.entries(DOCUMENT_TYPE_CONFIG).filter(([, config]) => {
    if (!category) return true;
    return config.category === category;
  });

  return (
    <div className="azals-document-type-selector">
      <div className="azals-document-type-selector__tabs">
        {types.map(([type, config]) => {
          const isActive = type === value;
          const Icon = TYPE_ICONS[type as DocumentType];

          return (
            <button
              key={type}
              type="button"
              className={`azals-document-type-selector__tab ${
                isActive ? 'azals-document-type-selector__tab--active' : ''
              }`}
              onClick={() => !disabled && onChange(type as DocumentType)}
              disabled={disabled}
            >
              {Icon}
              <span>{t(config.labelKey)}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
});

DocumentTypeSelector.displayName = 'DocumentTypeSelector';

// ============================================================
// COMPOSANT - CategoryTabs (Ventes / Achats)
// ============================================================

interface CategoryTabsProps {
  value: DocumentCategory;
  onChange: (category: DocumentCategory) => void;
}

export const CategoryTabs: React.FC<CategoryTabsProps> = memo(({ value, onChange }) => {
  const { t } = useTranslation();

  return (
    <div className="azals-category-tabs">
      <button
        type="button"
        className={`azals-category-tabs__tab ${
          value === 'SALES' ? 'azals-category-tabs__tab--active' : ''
        }`}
        onClick={() => onChange('SALES')}
      >
        {t('documents.categories.sales')}
      </button>
      <button
        type="button"
        className={`azals-category-tabs__tab ${
          value === 'PURCHASES' ? 'azals-category-tabs__tab--active' : ''
        }`}
        onClick={() => onChange('PURCHASES')}
      >
        {t('documents.categories.purchases')}
      </button>
    </div>
  );
});

CategoryTabs.displayName = 'CategoryTabs';

export default DocumentTypeSelector;
