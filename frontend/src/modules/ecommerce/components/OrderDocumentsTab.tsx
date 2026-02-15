/**
 * AZALSCORE Module - E-commerce - Order Documents Tab
 * Onglet documents de la commande
 */

import React from 'react';
import { FileText, Download, Printer, Receipt, Package } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Order } from '../types';
import { formatFileSize } from '../types';
import { formatDateTime } from '@/utils/formatters';

/**
 * OrderDocumentsTab - Documents
 */
export const OrderDocumentsTab: React.FC<TabContentProps<Order>> = ({ data: order }) => {
  const handlePrintInvoice = () => {
    window.print();
  };

  const handleDownloadInvoice = () => {
    window.dispatchEvent(new CustomEvent('azals:download', { detail: { module: 'ecommerce', type: 'invoice', orderId: order.id } }));
  };

  const handlePrintDeliveryNote = () => {
    window.print();
  };

  return (
    <div className="azals-std-tab-content">
      {/* Facture */}
      <Card title="Facture" icon={<Receipt size={18} />}>
        <div className="flex items-center gap-4 p-4 bg-green-50 rounded border border-green-200">
          <Receipt size={32} className="text-green-500" />
          <div className="flex-1">
            <div className="font-medium">Facture {order.number}</div>
            <div className="text-sm text-muted">
              Commande du {formatDateTime(order.created_at)}
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" leftIcon={<Download size={14} />} onClick={handleDownloadInvoice}>
              PDF
            </Button>
            <Button variant="secondary" size="sm" leftIcon={<Printer size={14} />} onClick={handlePrintInvoice}>
              Imprimer
            </Button>
          </div>
        </div>
      </Card>

      {/* Bon de livraison */}
      <Card title="Bon de livraison" icon={<Package size={18} />} className="mt-4">
        <div className="flex items-center gap-4 p-4 bg-blue-50 rounded border border-blue-200">
          <Package size={32} className="text-blue-500" />
          <div className="flex-1">
            <div className="font-medium">Bon de livraison {order.number}</div>
            <div className="text-sm text-muted">
              {order.items.length} article(s) - {order.items.reduce((sum, i) => sum + i.quantity, 0)} unite(s)
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" leftIcon={<Download size={14} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:download', { detail: { module: 'ecommerce', type: 'delivery-note', orderId: order.id } })); }}>
              PDF
            </Button>
            <Button variant="secondary" size="sm" leftIcon={<Printer size={14} />} onClick={handlePrintDeliveryNote}>
              Imprimer
            </Button>
          </div>
        </div>
      </Card>

      {/* Documents attaches */}
      <Card title="Documents" icon={<FileText size={18} />} className="mt-4">
        {order.documents && order.documents.length > 0 ? (
          <div className="space-y-2">
            {order.documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
              >
                <FileText size={20} className="text-blue-500" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{doc.name}</div>
                  <div className="text-sm text-muted">
                    {doc.type} - {formatFileSize(doc.size)} - {formatDateTime(doc.created_at)}
                  </div>
                </div>
                <Button variant="ghost" size="sm" leftIcon={<Download size={14} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:download', { detail: { module: 'ecommerce', type: 'document', documentId: doc.id } })); }}>
                  Telecharger
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <FileText size={32} className="text-muted" />
            <p className="text-muted">Aucun document supplementaire</p>
          </div>
        )}
      </Card>

      {/* Actions documents (ERP only) */}
      <Card title="Generer des documents" className="mt-4 azals-std-field--secondary">
        <Grid cols={3} gap="md">
          <Button variant="secondary" className="justify-start" leftIcon={<Receipt size={16} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:generate', { detail: { module: 'ecommerce', type: 'invoice', orderId: order.id } })); }}>
            Generer facture
          </Button>
          <Button variant="secondary" className="justify-start" leftIcon={<Package size={16} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:generate', { detail: { module: 'ecommerce', type: 'delivery-note', orderId: order.id } })); }}>
            Generer bon de livraison
          </Button>
          <Button variant="secondary" className="justify-start" leftIcon={<FileText size={16} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:generate', { detail: { module: 'ecommerce', type: 'return-label', orderId: order.id } })); }}>
            Generer etiquette retour
          </Button>
        </Grid>
      </Card>

      {/* Tracabilite */}
      <Card title="Tracabilite" icon={<FileText size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Creee par</label>
            <div className="azals-field__value">{order.created_by_name || 'Client'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Creee le</label>
            <div className="azals-field__value">{formatDateTime(order.created_at)}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Modifiee le</label>
            <div className="azals-field__value">{formatDateTime(order.updated_at)}</div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default OrderDocumentsTab;
