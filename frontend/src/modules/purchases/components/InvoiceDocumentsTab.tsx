/**
 * AZALSCORE Module - Purchases - Invoice Documents Tab
 * Onglet documents de la facture fournisseur
 */

import React from 'react';
import { Paperclip, Upload, FileText, Download, Printer, ShoppingCart } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { PurchaseInvoice } from '../types';
import { formatDate } from '@/utils/formatters';

/**
 * InvoiceDocumentsTab - Documents
 */
export const InvoiceDocumentsTab: React.FC<TabContentProps<PurchaseInvoice>> = ({ data: invoice }) => {
  const handleUpload = () => {
    console.log('Upload document for invoice:', invoice.id);
  };

  const handlePrint = () => {
    console.log('Print invoice:', invoice.id);
  };

  const handleDownloadPDF = () => {
    console.log('Download PDF for invoice:', invoice.id);
  };

  return (
    <div className="azals-std-tab-content">
      {/* Commande liee */}
      {invoice.order_id && (
        <Card title="Commande liee" icon={<ShoppingCart size={18} />}>
          <div className="flex items-center gap-4 p-4 bg-blue-50 rounded border border-blue-200">
            <ShoppingCart size={24} className="text-blue-500" />
            <div className="flex-1">
              <div className="font-medium font-mono">{invoice.order_number}</div>
              <div className="text-sm text-muted">
                Cette facture est liee a une commande fournisseur
              </div>
            </div>
            <Button variant="ghost" size="sm">
              Voir la commande
            </Button>
          </div>
        </Card>
      )}

      {/* Actions document */}
      <Card title="Facture" icon={<FileText size={18} />} className={invoice.order_id ? 'mt-4' : ''}>
        <div className="flex items-center gap-4 p-4 bg-green-50 rounded border border-green-200">
          <FileText size={32} className="text-green-500" />
          <div className="flex-1">
            <div className="font-medium">Facture {invoice.number}</div>
            <div className="text-sm text-muted">
              {invoice.supplier_reference
                ? `Ref. fournisseur: ${invoice.supplier_reference}`
                : 'Document de facturation fournisseur'}
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" leftIcon={<Download size={14} />} onClick={handleDownloadPDF}>
              PDF
            </Button>
            <Button variant="secondary" size="sm" leftIcon={<Printer size={14} />} onClick={handlePrint}>
              Imprimer
            </Button>
          </div>
        </div>
      </Card>

      {/* Pieces jointes */}
      <Card
        title="Pieces jointes"
        icon={<Paperclip size={18} />}
        className="mt-4"
        actions={
          <Button variant="secondary" size="sm" leftIcon={<Upload size={14} />} onClick={handleUpload}>
            Ajouter
          </Button>
        }
      >
        <div className="azals-empty azals-empty--sm">
          <Paperclip size={32} className="text-muted" />
          <p className="text-muted">Aucune piece jointe</p>
          <Button variant="secondary" size="sm" leftIcon={<Upload size={14} />} onClick={handleUpload} className="mt-2">
            Ajouter un document
          </Button>
        </div>
      </Card>

      {/* Zone de depot (ERP only) */}
      <Card className="mt-4 azals-std-field--secondary">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <Upload size={48} className="text-muted mx-auto mb-4" />
          <p className="text-muted mb-2">Glissez-deposez vos documents ici</p>
          <p className="text-sm text-muted mb-4">ou</p>
          <Button variant="secondary" onClick={handleUpload}>
            Parcourir
          </Button>
          <p className="text-xs text-muted mt-4">
            Formats acceptes: PDF, JPG, PNG (max 10 Mo)
          </p>
        </div>
      </Card>

      {/* Tracabilite */}
      <Card title="Tracabilite" icon={<FileText size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Cree par</label>
            <div className="azals-field__value">{invoice.created_by_name || '-'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Cree le</label>
            <div className="azals-field__value">{formatDate(invoice.created_at)}</div>
          </div>
          {invoice.validated_by_name && (
            <>
              <div className="azals-field">
                <label className="azals-field__label">Valide par</label>
                <div className="azals-field__value">{invoice.validated_by_name}</div>
              </div>
              <div className="azals-field">
                <label className="azals-field__label">Valide le</label>
                <div className="azals-field__value">{invoice.validated_at ? formatDate(invoice.validated_at) : '-'}</div>
              </div>
            </>
          )}
        </Grid>
      </Card>
    </div>
  );
};

export default InvoiceDocumentsTab;
