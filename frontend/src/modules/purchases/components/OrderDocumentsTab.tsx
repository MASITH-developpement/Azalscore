/**
 * AZALSCORE Module - Purchases - Order Documents Tab
 * Onglet documents de la commande
 */

import React from 'react';
import { Paperclip, Upload, FileText, Download, Printer } from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatDate } from '@/utils/formatters';
import type { PurchaseOrder } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * OrderDocumentsTab - Documents
 */
export const OrderDocumentsTab: React.FC<TabContentProps<PurchaseOrder>> = ({ data: order }) => {
  const handleUpload = () => {
  };

  const handlePrint = () => {
  };

  const handleDownloadPDF = () => {
  };

  return (
    <div className="azals-std-tab-content">
      {/* Actions document */}
      <Card title="Bon de commande" icon={<FileText size={18} />}>
        <div className="flex items-center gap-4 p-4 bg-blue-50 rounded border border-blue-200">
          <FileText size={32} className="text-blue-500" />
          <div className="flex-1">
            <div className="font-medium">Bon de commande {order.number}</div>
            <div className="text-sm text-muted">
              Document officiel de commande fournisseur
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
            <span className="azals-field__label">Cree par</span>
            <div className="azals-field__value">{order.created_by_name || '-'}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Cree le</span>
            <div className="azals-field__value">{formatDate(order.created_at)}</div>
          </div>
          {order.validated_by_name && (
            <>
              <div className="azals-field">
                <span className="azals-field__label">Valide par</span>
                <div className="azals-field__value">{order.validated_by_name}</div>
              </div>
              <div className="azals-field">
                <span className="azals-field__label">Valide le</span>
                <div className="azals-field__value">{order.validated_at ? formatDate(order.validated_at) : '-'}</div>
              </div>
            </>
          )}
        </Grid>
      </Card>
    </div>
  );
};

export default OrderDocumentsTab;
