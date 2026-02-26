/**
 * AZALSCORE Module - Comptabilite - Entry Documents Tab
 * Onglet documents lies et pieces justificatives
 */

import React from 'react';
import { FileText, Link2, Upload, ArrowRight, File } from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatDate, formatCurrency } from '@/utils/formatters';
import type { Entry } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * EntryDocumentsTab - Documents lies
 */
export const EntryDocumentsTab: React.FC<TabContentProps<Entry>> = ({ data: entry }) => {
  const relatedEntries = entry.related_entries || [];

  const handleUpload = () => {
    window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'addJustificatif', entryId: entry.id } }));
  };

  return (
    <div className="azals-std-tab-content">
      {/* Document source */}
      {entry.source_document_id && (
        <Card title="Document source" icon={<Link2 size={18} />}>
          <div className="flex items-center gap-4 p-4 bg-blue-50 rounded border border-blue-200">
            <FileText size={24} className="text-blue-500" />
            <div className="flex-1">
              <div className="font-medium">{entry.source_document_number || 'Document'}</div>
              <div className="text-sm text-muted">
                {entry.source_document_type || 'Document commercial'}
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={() => { window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view: 'invoicing', params: { documentId: entry.source_document_id } } })); }}>
              Voir
            </Button>
          </div>
          <div className="mt-2 text-sm text-muted">
            Cette ecriture a ete generee automatiquement a partir de ce document.
          </div>
        </Card>
      )}

      {/* Ecritures liees */}
      {relatedEntries.length > 0 && (
        <Card
          title="Ecritures liees"
          icon={<ArrowRight size={18} />}
          className={entry.source_document_id ? 'mt-4' : ''}
        >
          <div className="space-y-2">
            {relatedEntries.map((related) => (
              <div
                key={related.id}
                className="flex items-center gap-4 p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
              >
                <FileText size={20} className="text-gray-500" />
                <div className="flex-1">
                  <div className="font-mono font-medium">{related.number}</div>
                  <div className="text-sm text-muted">
                    {related.description} - {formatDate(related.date)}
                  </div>
                </div>
                <div className="text-right">
                  <span className={`azals-badge azals-badge--${related.relation === 'reversal' ? 'red' : related.relation === 'adjustment' ? 'orange' : 'blue'}`}>
                    {related.relation === 'reversal' ? 'Extourne' : related.relation === 'adjustment' ? 'Ajustement' : 'Liee'}
                  </span>
                </div>
                <div className="text-right font-medium">
                  {formatCurrency(related.total_debit)}
                </div>
                <Button variant="ghost" size="sm" onClick={() => { window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view: 'comptabilite', params: { entryId: related.id } } })); }}>
                  Voir
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Pieces justificatives */}
      <Card
        title="Pieces justificatives"
        icon={<File size={18} />}
        className="mt-4"
        actions={
          <Button variant="secondary" size="sm" leftIcon={<Upload size={14} />} onClick={handleUpload}>
            Ajouter
          </Button>
        }
      >
        <div className="azals-empty azals-empty--sm">
          <File size={32} className="text-muted" />
          <p className="text-muted">Aucune piece justificative</p>
          <Button variant="ghost" size="sm" leftIcon={<Upload size={14} />} onClick={handleUpload} className="mt-2">
            Ajouter un justificatif
          </Button>
        </div>
      </Card>

      {/* Zone de depot (ERP only) */}
      <Card className="mt-4 azals-std-field--secondary">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <Upload size={48} className="text-muted mx-auto mb-4" />
          <p className="text-muted mb-2">Glissez-deposez vos pieces justificatives ici</p>
          <p className="text-sm text-muted mb-4">ou</p>
          <Button variant="secondary" onClick={handleUpload}>
            Parcourir
          </Button>
          <p className="text-xs text-muted mt-4">
            Formats acceptes: PDF, JPG, PNG (max 10 Mo)
          </p>
        </div>
      </Card>

      {/* Informations de tracabilite */}
      <Card
        title="Tracabilite"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Cree par</span>
            <div className="azals-field__value">{entry.created_by_name || '-'}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Cree le</span>
            <div className="azals-field__value">{formatDate(entry.created_at)}</div>
          </div>
          {entry.updated_at && entry.updated_at !== entry.created_at && (
            <>
              <div className="azals-field">
                <span className="azals-field__label">Modifie le</span>
                <div className="azals-field__value">{formatDate(entry.updated_at)}</div>
              </div>
            </>
          )}
        </Grid>
      </Card>
    </div>
  );
};

export default EntryDocumentsTab;
