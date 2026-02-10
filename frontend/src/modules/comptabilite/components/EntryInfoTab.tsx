/**
 * AZALSCORE Module - Comptabilite - Entry Info Tab
 * Onglet informations generales de l'ecriture
 */

import React from 'react';
import { FileText, Calendar, Book, User, Link2 } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Entry } from '../types';
import { formatDate, formatDateTime } from '@/utils/formatters';
import {
  ENTRY_STATUS_CONFIG, JOURNAL_TYPE_CONFIG, getJournalTypeLabel
} from '../types';

/**
 * EntryInfoTab - Informations generales
 */
export const EntryInfoTab: React.FC<TabContentProps<Entry>> = ({ data: entry }) => {
  const statusConfig = ENTRY_STATUS_CONFIG[entry.status];

  return (
    <div className="azals-std-tab-content">
      {/* Informations principales */}
      <Card title="Informations de l'ecriture" icon={<FileText size={18} />}>
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Numero</label>
            <div className="azals-field__value font-mono font-medium">{entry.number}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Statut</label>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                {statusConfig.label}
              </span>
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Description</label>
            <div className="azals-field__value">{entry.description || '-'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Reference</label>
            <div className="azals-field__value">{entry.reference || '-'}</div>
          </div>
        </Grid>
      </Card>

      {/* Journal */}
      <Card title="Journal" icon={<Book size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Code</label>
            <div className="azals-field__value font-mono">{entry.journal_code || '-'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Nom</label>
            <div className="azals-field__value">{entry.journal_name || '-'}</div>
          </div>
        </Grid>
      </Card>

      {/* Dates */}
      <Card title="Dates" icon={<Calendar size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Date comptable</label>
            <div className="azals-field__value font-medium">{formatDate(entry.date)}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Periode</label>
            <div className="azals-field__value">{entry.period || '-'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Exercice</label>
            <div className="azals-field__value">{entry.fiscal_year || '-'}</div>
          </div>
        </Grid>
      </Card>

      {/* Document source */}
      {entry.source_document_id && (
        <Card title="Document source" icon={<Link2 size={18} />} className="mt-4">
          <Grid cols={2} gap="md">
            <div className="azals-field">
              <label className="azals-field__label">Type</label>
              <div className="azals-field__value">{entry.source_document_type || '-'}</div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Numero</label>
              <div className="azals-field__value font-mono">{entry.source_document_number || '-'}</div>
            </div>
          </Grid>
        </Card>
      )}

      {/* Validation (ERP only) */}
      {entry.validated_at && (
        <Card
          title="Validation"
          icon={<User size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <Grid cols={2} gap="md">
            <div className="azals-field">
              <label className="azals-field__label">Valide le</label>
              <div className="azals-field__value">{formatDateTime(entry.validated_at)}</div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Valide par</label>
              <div className="azals-field__value">{entry.validated_by_name || '-'}</div>
            </div>
          </Grid>
        </Card>
      )}

      {/* Comptabilisation (ERP only) */}
      {entry.posted_at && (
        <Card
          title="Comptabilisation"
          icon={<User size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <Grid cols={2} gap="md">
            <div className="azals-field">
              <label className="azals-field__label">Comptabilise le</label>
              <div className="azals-field__value">{formatDateTime(entry.posted_at)}</div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Comptabilise par</label>
              <div className="azals-field__value">{entry.posted_by_name || '-'}</div>
            </div>
          </Grid>
        </Card>
      )}

      {/* Annulation */}
      {entry.cancelled_at && (
        <Card title="Annulation" icon={<User size={18} />} className="mt-4">
          <Grid cols={2} gap="md">
            <div className="azals-field">
              <label className="azals-field__label">Annule le</label>
              <div className="azals-field__value text-danger">{formatDateTime(entry.cancelled_at)}</div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Raison</label>
              <div className="azals-field__value">{entry.cancelled_reason || '-'}</div>
            </div>
          </Grid>
        </Card>
      )}
    </div>
  );
};

export default EntryInfoTab;
