/**
 * AZALSCORE Module - Invoicing - InvoicingDetailView
 * Vue detail BaseViewStandard pour les documents
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FileText, ShoppingCart, DollarSign, Shield, Link2, Clock, Sparkles } from 'lucide-react';
import { LoadingState, ErrorState } from '@ui/components/StateViews';
import { PageWrapper } from '@ui/layout';
import {
  BaseViewStandard,
  type TabDefinition,
  type InfoBarItem,
  type SidebarSection,
  type ActionDefinition,
  type SemanticColor
} from '@ui/standards';
import { formatCurrency, formatDate } from '@/utils/formatters';
import type { Document, DocumentType } from '../types';
import {
  DOCUMENT_TYPE_CONFIG, DOCUMENT_STATUS_CONFIG, TRANSFORM_WORKFLOW,
  getDaysUntilDue, isDocumentOverdue, canTransformDocument
} from '../types';
import { useDocument } from '../hooks';
import {
  InvoicingInfoTab, InvoicingLinesTab, InvoicingFinancialTab,
  InvoicingDocumentsTab, InvoicingHistoryTab, InvoicingIATab, InvoicingRiskTab
} from './index';

interface InvoicingDetailViewProps {
  type: DocumentType;
}

const InvoicingDetailView: React.FC<InvoicingDetailViewProps> = ({ type }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: document, isLoading, error, refetch } = useDocument(id || '');

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <LoadingState onRetry={() => refetch()} message="Chargement du document..." />
      </PageWrapper>
    );
  }

  if (error || !document) {
    return (
      <PageWrapper title="Erreur">
        <ErrorState
          message="Document introuvable"
          onRetry={() => refetch()}
          onBack={() => navigate(-1)}
        />
      </PageWrapper>
    );
  }

  const typeConfig = DOCUMENT_TYPE_CONFIG[document.type] || { label: document.type, color: 'gray' };
  const statusConfig = DOCUMENT_STATUS_CONFIG[document.status] || { label: document.status, color: 'gray' };

  // Configuration des onglets
  const tabs: TabDefinition<Document>[] = [
    { id: 'info', label: 'Informations', icon: <FileText size={16} />, component: InvoicingInfoTab },
    { id: 'lines', label: 'Lignes', icon: <ShoppingCart size={16} />, badge: document.lines?.length, component: InvoicingLinesTab },
    { id: 'financial', label: 'Financier', icon: <DollarSign size={16} />, component: InvoicingFinancialTab },
    { id: 'risk', label: 'Risque Client', icon: <Shield size={16} />, component: InvoicingRiskTab },
    { id: 'documents', label: 'Documents', icon: <Link2 size={16} />, component: InvoicingDocumentsTab },
    { id: 'history', label: 'Historique', icon: <Clock size={16} />, component: InvoicingHistoryTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={16} />, component: InvoicingIATab }
  ];

  // Barre d'info KPIs
  const infoBarItems: InfoBarItem[] = [
    { id: 'type', label: 'Type', value: typeConfig.label, valueColor: typeConfig.color as SemanticColor },
    { id: 'status', label: 'Statut', value: statusConfig.label, valueColor: statusConfig.color as SemanticColor },
    { id: 'lines', label: 'Lignes', value: String(document.lines?.length || 0), valueColor: 'blue' },
    { id: 'total', label: 'Total TTC', value: formatCurrency(document.total, document.currency), valueColor: 'green' }
  ];

  // Ajouter alerte retard si applicable
  if (isDocumentOverdue(document)) {
    const days = Math.abs(getDaysUntilDue(document) || 0);
    infoBarItems.push({ id: 'overdue', label: 'Retard', value: `${days}j`, valueColor: 'red' });
  }

  // Sidebar
  const sidebarSections: SidebarSection[] = [
    {
      id: 'summary',
      title: 'Resume',
      items: [
        { id: 'number', label: 'Numero', value: document.number },
        { id: 'date', label: 'Date', value: formatDate(document.date) },
        { id: 'customer', label: 'Client', value: document.customer_name || '-' },
        { id: 'currency', label: 'Devise', value: document.currency }
      ]
    },
    {
      id: 'totals',
      title: 'Montants',
      items: [
        { id: 'subtotal', label: 'Total HT', value: formatCurrency(document.subtotal, document.currency) },
        { id: 'tax', label: 'TVA', value: formatCurrency(document.tax_amount, document.currency) },
        { id: 'total', label: 'Total TTC', value: formatCurrency(document.total, document.currency), highlight: true }
      ]
    }
  ];

  // Ajouter section echeance si applicable
  if (document.due_date) {
    const daysUntil = getDaysUntilDue(document);
    sidebarSections.push({
      id: 'payment',
      title: 'Echeance',
      items: [
        { id: 'due_date', label: 'Date', value: formatDate(document.due_date) },
        {
          id: 'days',
          label: 'Statut',
          value: daysUntil !== null
            ? (daysUntil < 0 ? `En retard (${Math.abs(daysUntil)}j)` : `${daysUntil}j restants`)
            : '-',
          highlight: daysUntil !== null && daysUntil < 0
        }
      ]
    });
  }

  // Actions header
  const headerActions: ActionDefinition[] = [];

  if (document.status === 'DRAFT') {
    headerActions.push({
      id: 'edit',
      label: 'Modifier',
      variant: 'secondary',
      capability: 'invoicing.edit',
      onClick: () => navigate(`/invoicing/${type.toLowerCase()}s/${id}/edit`)
    });
  }

  if (canTransformDocument(document)) {
    const transformConfig = TRANSFORM_WORKFLOW[document.type];
    if (transformConfig) {
      headerActions.push({
        id: 'transform',
        label: transformConfig.label,
        variant: 'primary',
        onClick: () => {
          window.dispatchEvent(new CustomEvent('azals:action', {
            detail: { type: 'transformDocument', documentId: document.id, targetType: transformConfig.target }
          }));
        },
      });
    }
  }

  const status = {
    label: statusConfig.label,
    color: statusConfig.color as SemanticColor
  };

  return (
    <BaseViewStandard<Document>
      title={`${typeConfig.label} ${document.number}`}
      subtitle={document.customer_name || undefined}
      status={status}
      data={document}
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

export default InvoicingDetailView;
