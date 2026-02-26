/**
 * AZALSCORE Module - Purchases - Supplier Detail View
 * =====================================================
 * Vue detail fournisseur avec BaseViewStandard
 */

import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Edit,
  Trash2,
  Building2,
  ShoppingCart,
  FileText,
  Paperclip,
  Clock,
  Shield,
  Sparkles,
} from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { BaseViewStandard } from '@ui/standards';
import type { InfoBarItem, SidebarSection, TabDefinition } from '@ui/standards';
import { formatCurrency, formatDate } from '@/utils/formatters';
import { useSupplier, useDeleteSupplier } from '../../hooks';
import {
  SupplierInfoTab,
  SupplierOrdersTab,
  SupplierInvoicesTab,
  SupplierDocumentsTab,
  SupplierHistoryTab,
  SupplierRiskTab,
  SupplierIATab,
} from '../../components';
import { SUPPLIER_STATUS_CONFIG, type Supplier } from '../../types';

// ============================================================================
// Component
// ============================================================================

export const SupplierDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: supplier, isLoading, error, refetch } = useSupplier(id || '');
  const deleteMutation = useDeleteSupplier();

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">Chargement du fournisseur...</div>
      </PageWrapper>
    );
  }

  if (error || !supplier) {
    return (
      <PageWrapper title="Erreur">
        <Card>
          <p className="text-danger">Fournisseur non trouve</p>
          <Button className="mt-4" onClick={() => navigate('/purchases/suppliers')}>
            Retour
          </Button>
        </Card>
      </PageWrapper>
    );
  }

  const statusConfig = SUPPLIER_STATUS_CONFIG[supplier.status] || { label: supplier.status, color: 'gray' };

  const tabs: TabDefinition<Supplier>[] = [
    { id: 'info', label: 'Informations', icon: <Building2 size={16} />, component: SupplierInfoTab },
    { id: 'orders', label: 'Commandes', icon: <ShoppingCart size={16} />, badge: supplier.total_orders, component: SupplierOrdersTab },
    { id: 'invoices', label: 'Factures', icon: <FileText size={16} />, badge: supplier.total_invoices, component: SupplierInvoicesTab },
    { id: 'documents', label: 'Documents', icon: <Paperclip size={16} />, component: SupplierDocumentsTab },
    { id: 'history', label: 'Historique', icon: <Clock size={16} />, component: SupplierHistoryTab },
    { id: 'risk', label: 'Risque', icon: <Shield size={16} />, component: SupplierRiskTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={16} />, component: SupplierIATab },
  ];

  const infoBarItems: InfoBarItem[] = [
    { id: 'status', label: 'Statut', value: statusConfig.label, valueColor: statusConfig.color as 'gray' | 'green' | 'yellow' | 'red' },
    { id: 'contact', label: 'Contact', value: supplier.contact_name || '-' },
    { id: 'email', label: 'Email', value: supplier.email || '-' },
    { id: 'phone', label: 'Telephone', value: supplier.phone || '-' },
  ];

  const sidebarSections: SidebarSection[] = [
    {
      id: 'stats',
      title: 'Statistiques',
      items: [
        { id: 'orders', label: 'Commandes', value: `${supplier.total_orders || 0}` },
        { id: 'invoices', label: 'Factures', value: `${supplier.total_invoices || 0}` },
        { id: 'spent', label: 'Total depense', value: formatCurrency(supplier.total_spent || 0), highlight: true },
      ],
    },
  ];

  const headerActions = [
    { id: 'back', label: 'Retour', icon: <ArrowLeft size={16} />, variant: 'ghost' as const, onClick: () => navigate('/purchases/suppliers') },
    { id: 'edit', label: 'Modifier', icon: <Edit size={16} />, variant: 'secondary' as const, onClick: () => navigate(`/purchases/suppliers/${id}/edit`) },
    {
      id: 'delete',
      label: 'Supprimer',
      icon: <Trash2 size={16} />,
      variant: 'danger' as const,
      onClick: async () => {
        if (window.confirm('Supprimer ce fournisseur ?')) {
          await deleteMutation.mutateAsync(id!);
          navigate('/purchases/suppliers');
        }
      },
    },
  ];

  return (
    <BaseViewStandard<Supplier>
      title={`${supplier.code} - ${supplier.name}`}
      subtitle="Fiche fournisseur"
      status={{ label: statusConfig.label, color: statusConfig.color as 'gray' | 'green' | 'yellow' | 'red' }}
      data={supplier}
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

export default SupplierDetailView;
