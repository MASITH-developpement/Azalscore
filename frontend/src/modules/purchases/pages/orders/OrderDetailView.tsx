/**
 * AZALSCORE Module - Purchases - Order Detail View
 * ==================================================
 * Vue detail commande avec BaseViewStandard
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
  usePurchaseOrder,
  useDeletePurchaseOrder,
  useValidatePurchaseOrder,
  useCreateInvoiceFromOrder,
} from '../../hooks';
import {
  OrderInfoTab,
  OrderLinesTab,
  OrderFinancialTab,
  OrderDocumentsTab,
  OrderHistoryTab,
  OrderIATab,
} from '../../components';
import {
  ORDER_STATUS_CONFIG,
  canEditOrder,
  canValidateOrder,
  canCreateInvoiceFromOrder,
  type PurchaseOrder,
} from '../../types';

// ============================================================================
// Component
// ============================================================================

export const OrderDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: order, isLoading, error, refetch } = usePurchaseOrder(id || '');
  const deleteMutation = useDeletePurchaseOrder();
  const validateMutation = useValidatePurchaseOrder();
  const createInvoiceMutation = useCreateInvoiceFromOrder();

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">Chargement de la commande...</div>
      </PageWrapper>
    );
  }

  if (error || !order) {
    return (
      <PageWrapper title="Erreur">
        <Card>
          <p className="text-danger">Commande non trouvee</p>
          <Button className="mt-4" onClick={() => navigate('/purchases/orders')}>
            Retour
          </Button>
        </Card>
      </PageWrapper>
    );
  }

  const statusConfig = ORDER_STATUS_CONFIG[order.status] || { label: order.status, color: 'gray' };

  const tabs: TabDefinition<PurchaseOrder>[] = [
    { id: 'info', label: 'Informations', icon: <FileText size={16} />, component: OrderInfoTab },
    { id: 'lines', label: 'Lignes', icon: <List size={16} />, badge: order.lines.length, component: OrderLinesTab },
    { id: 'financial', label: 'Financier', icon: <Euro size={16} />, component: OrderFinancialTab },
    { id: 'documents', label: 'Documents', icon: <Paperclip size={16} />, component: OrderDocumentsTab },
    { id: 'history', label: 'Historique', icon: <Clock size={16} />, component: OrderHistoryTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={16} />, component: OrderIATab },
  ];

  const infoBarItems: InfoBarItem[] = [
    { id: 'status', label: 'Statut', value: statusConfig.label, valueColor: statusConfig.color as 'gray' | 'blue' | 'orange' | 'yellow' | 'green' | 'purple' | 'red' },
    { id: 'supplier', label: 'Fournisseur', value: order.supplier_name },
    { id: 'date', label: 'Date', value: formatDate(order.date) },
    { id: 'total', label: 'Total TTC', value: formatCurrency(order.total_ttc, order.currency) },
  ];

  const sidebarSections: SidebarSection[] = [
    {
      id: 'totals',
      title: 'Totaux',
      items: [
        { id: 'ht', label: 'Total HT', value: formatCurrency(order.total_ht, order.currency) },
        { id: 'tax', label: 'TVA', value: formatCurrency(order.total_tax, order.currency) },
        { id: 'ttc', label: 'Total TTC', value: formatCurrency(order.total_ttc, order.currency), highlight: true },
      ],
    },
    {
      id: 'details',
      title: 'Details',
      items: [
        { id: 'lines', label: 'Lignes', value: `${order.lines.length}` },
        { id: 'reference', label: 'Reference', value: order.reference || '-' },
      ],
    },
  ];

  const headerActions = [
    { id: 'back', label: 'Retour', icon: <ArrowLeft size={16} />, variant: 'ghost' as const, onClick: () => navigate('/purchases/orders') },
    ...(canEditOrder(order) ? [{ id: 'edit', label: 'Modifier', icon: <Edit size={16} />, variant: 'secondary' as const, onClick: () => navigate(`/purchases/orders/${id}/edit`) }] : []),
    ...(canValidateOrder(order) ? [{ id: 'validate', label: 'Valider', icon: <CheckCircle2 size={16} />, variant: 'primary' as const, onClick: () => validateMutation.mutate(id!) }] : []),
    ...(canCreateInvoiceFromOrder(order) ? [{
      id: 'invoice',
      label: 'Creer facture',
      icon: <FileText size={16} />,
      variant: 'secondary' as const,
      onClick: async () => {
        const inv = await createInvoiceMutation.mutateAsync(id!);
        navigate(`/purchases/invoices/${inv.id}`);
      },
    }] : []),
    ...(canEditOrder(order) ? [{
      id: 'delete',
      label: 'Supprimer',
      icon: <Trash2 size={16} />,
      variant: 'danger' as const,
      onClick: async () => {
        if (window.confirm('Supprimer cette commande ?')) {
          await deleteMutation.mutateAsync(id!);
          navigate('/purchases/orders');
        }
      },
    }] : []),
  ];

  return (
    <BaseViewStandard<PurchaseOrder>
      title={`Commande ${order.number}`}
      subtitle={`${order.supplier_code} - ${order.supplier_name}`}
      status={{ label: statusConfig.label, color: statusConfig.color as 'gray' | 'green' | 'yellow' | 'red' }}
      data={order}
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

export default OrderDetailView;
