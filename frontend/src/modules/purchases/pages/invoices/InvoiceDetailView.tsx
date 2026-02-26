/**
 * AZALSCORE Module - Purchases - Invoice Detail View
 * ====================================================
 * Vue detail facture avec BaseViewStandard
 */

import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Edit,
  Trash2,
  CheckCircle2,
  FileText,
  List,
  Euro,
  Paperclip,
  Clock,
  Sparkles,
} from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { BaseViewStandard } from '@ui/standards';
import type { InfoBarItem, SidebarSection, TabDefinition } from '@ui/standards';
import { formatCurrency, formatDate } from '@/utils/formatters';
import {
  usePurchaseInvoice,
  useDeletePurchaseInvoice,
  useValidatePurchaseInvoice,
} from '../../hooks';
import {
  InvoiceInfoTab,
  InvoiceLinesTab,
  InvoiceFinancialTab,
  InvoiceDocumentsTab,
  InvoiceHistoryTab,
  InvoiceIATab,
} from '../../components';
import {
  INVOICE_STATUS_CONFIG,
  canEditInvoice,
  canValidateInvoice,
  isOverdue,
  type PurchaseInvoice,
} from '../../types';

// ============================================================================
// Component
// ============================================================================

export const InvoiceDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: invoice, isLoading, error, refetch } = usePurchaseInvoice(id || '');
  const deleteMutation = useDeletePurchaseInvoice();
  const validateMutation = useValidatePurchaseInvoice();

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">Chargement de la facture...</div>
      </PageWrapper>
    );
  }

  if (error || !invoice) {
    return (
      <PageWrapper title="Erreur">
        <Card>
          <p className="text-danger">Facture non trouvee</p>
          <Button className="mt-4" onClick={() => navigate('/purchases/invoices')}>
            Retour
          </Button>
        </Card>
      </PageWrapper>
    );
  }

  const statusConfig = INVOICE_STATUS_CONFIG[invoice.status] || { label: invoice.status, color: 'gray' };
  const overdue = isOverdue(invoice.due_date);

  const tabs: TabDefinition<PurchaseInvoice>[] = [
    { id: 'info', label: 'Informations', icon: <FileText size={16} />, component: InvoiceInfoTab },
    { id: 'lines', label: 'Lignes', icon: <List size={16} />, badge: invoice.lines.length, component: InvoiceLinesTab },
    { id: 'financial', label: 'Financier', icon: <Euro size={16} />, component: InvoiceFinancialTab },
    { id: 'documents', label: 'Documents', icon: <Paperclip size={16} />, component: InvoiceDocumentsTab },
    { id: 'history', label: 'Historique', icon: <Clock size={16} />, component: InvoiceHistoryTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={16} />, component: InvoiceIATab },
  ];

  const infoBarItems: InfoBarItem[] = [
    { id: 'status', label: 'Statut', value: statusConfig.label, valueColor: statusConfig.color as 'gray' | 'blue' | 'green' | 'yellow' | 'red' },
    { id: 'supplier', label: 'Fournisseur', value: invoice.supplier_name },
    { id: 'date', label: 'Date', value: formatDate(invoice.date) },
    { id: 'due', label: 'Echeance', value: invoice.due_date ? formatDate(invoice.due_date) : '-', valueColor: overdue ? 'red' : undefined },
  ];

  const amountRemaining = invoice.amount_remaining || invoice.total_ttc - (invoice.amount_paid || 0);

  const sidebarSections: SidebarSection[] = [
    {
      id: 'totals',
      title: 'Totaux',
      items: [
        { id: 'ht', label: 'Total HT', value: formatCurrency(invoice.total_ht, invoice.currency) },
        { id: 'tax', label: 'TVA', value: formatCurrency(invoice.total_tax, invoice.currency) },
        { id: 'ttc', label: 'Total TTC', value: formatCurrency(invoice.total_ttc, invoice.currency), highlight: true },
      ],
    },
    {
      id: 'payment',
      title: 'Paiement',
      items: [
        { id: 'paid', label: 'Paye', value: formatCurrency(invoice.amount_paid || 0, invoice.currency) },
        { id: 'remaining', label: 'Reste', value: formatCurrency(amountRemaining, invoice.currency), highlight: amountRemaining > 0 },
      ],
    },
  ];

  const headerActions = [
    { id: 'back', label: 'Retour', icon: <ArrowLeft size={16} />, variant: 'ghost' as const, onClick: () => navigate('/purchases/invoices') },
    ...(canEditInvoice(invoice) ? [{ id: 'edit', label: 'Modifier', icon: <Edit size={16} />, variant: 'secondary' as const, onClick: () => navigate(`/purchases/invoices/${id}/edit`) }] : []),
    ...(canValidateInvoice(invoice) ? [{ id: 'validate', label: 'Valider', icon: <CheckCircle2 size={16} />, variant: 'primary' as const, onClick: () => validateMutation.mutate(id!) }] : []),
    ...(canEditInvoice(invoice) ? [{
      id: 'delete',
      label: 'Supprimer',
      icon: <Trash2 size={16} />,
      variant: 'danger' as const,
      onClick: async () => {
        if (window.confirm('Supprimer cette facture ?')) {
          await deleteMutation.mutateAsync(id!);
          navigate('/purchases/invoices');
        }
      },
    }] : []),
  ];

  return (
    <BaseViewStandard<PurchaseInvoice>
      title={`Facture ${invoice.number}`}
      subtitle={`${invoice.supplier_code} - ${invoice.supplier_name}`}
      status={{ label: statusConfig.label, color: statusConfig.color as 'gray' | 'green' | 'yellow' | 'red' }}
      data={invoice}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
      onRetry={() => refetch()}
    />
  );
};

export default InvoiceDetailView;
