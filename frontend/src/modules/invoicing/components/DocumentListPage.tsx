/**
 * AZALSCORE Module - Invoicing - DocumentListPage
 * Page de liste des documents (devis, commandes, factures)
 */

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Plus, ArrowRight, Copy, ShoppingCart, FileText } from 'lucide-react';
import { useHasCapability } from '@core/capabilities';
import { Button, ConfirmDialog } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn, TableAction } from '@/types';
import type { Document, DocumentType, DocumentStatus } from '../types';
import { DOCUMENT_TYPE_CONFIG, TRANSFORM_WORKFLOW } from '../types';
import {
  useDocuments, useDeleteDocument, useValidateDocument,
  useConvertQuoteToInvoice, useDuplicateDocument, useTransformDocument,
  useExportDocuments, type DocumentFilters
} from '../hooks';
import StatusBadge from './StatusBadge';
import FilterBar from './FilterBar';

const formatCurrency = (amount: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(amount);
};

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('fr-FR');
};

interface DocumentListPageProps {
  type: DocumentType;
}

const DocumentListPage: React.FC<DocumentListPageProps> = ({ type }) => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<DocumentFilters>({});
  const [deleteTarget, setDeleteTarget] = useState<Document | null>(null);
  const [validateTarget, setValidateTarget] = useState<Document | null>(null);
  const [convertTarget, setConvertTarget] = useState<Document | null>(null);
  const [duplicateTarget, setDuplicateTarget] = useState<Document | null>(null);
  const [transformTarget, setTransformTarget] = useState<Document | null>(null);

  const { data, isLoading, error, refetch } = useDocuments(type, page, pageSize, filters);
  const deleteDocument = useDeleteDocument();
  const validateDocument = useValidateDocument();
  const convertQuote = useConvertQuoteToInvoice();
  const duplicateDocument = useDuplicateDocument();
  const transformDocument = useTransformDocument();
  const exportDocuments = useExportDocuments();

  const typeConfig = DOCUMENT_TYPE_CONFIG[type] || { label: type, labelPlural: type, prefix: 'DOC', color: 'gray' };
  const canCreate = useHasCapability('invoicing.create');
  const canEdit = useHasCapability('invoicing.edit');
  const canDelete = useHasCapability('invoicing.delete');
  const canValidate = useHasCapability('invoicing.edit');

  const handleExport = async () => {
    try {
      const blob = await exportDocuments.mutateAsync({ type, filters });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${type.toLowerCase()}s_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const columns: TableColumn<Document>[] = [
    {
      id: 'number',
      header: 'Numero',
      accessor: 'number',
      sortable: true,
      render: (value, row) => (
        <Link to={`/invoicing/${type.toLowerCase()}s/${row.id}`} className="azals-link">
          {value as string}
        </Link>
      ),
    },
    { id: 'customer_name', header: 'Client', accessor: 'customer_name', sortable: true },
    {
      id: 'date',
      header: 'Date',
      accessor: 'date',
      sortable: true,
      render: (value) => formatDate(value as string),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => <StatusBadge status={value as DocumentStatus} />,
    },
    {
      id: 'total',
      header: 'Total TTC',
      accessor: 'total',
      align: 'right',
      render: (value, row) => formatCurrency(value as number, row.currency),
    },
  ];

  const transformConfig = TRANSFORM_WORKFLOW[type];

  const actions: TableAction<Document>[] = [
    {
      id: 'view',
      label: 'Voir',
      icon: 'eye',
      onClick: (row) => navigate(`/invoicing/${type.toLowerCase()}s/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      icon: 'edit',
      onClick: (row) => navigate(`/invoicing/${type.toLowerCase()}s/${row.id}/edit`),
      isHidden: (row) => row.status !== 'DRAFT' || !canEdit,
    },
    {
      id: 'duplicate',
      label: 'Dupliquer',
      icon: 'copy',
      onClick: (row) => setDuplicateTarget(row),
      isHidden: () => !canCreate,
    },
    {
      id: 'validate',
      label: 'Valider',
      icon: 'check',
      onClick: (row) => setValidateTarget(row),
      isHidden: (row) => row.status !== 'DRAFT' || !canValidate,
    },
    ...(transformConfig ? [{
      id: 'transform',
      label: transformConfig.label,
      icon: 'arrow-right',
      onClick: (row: Document) => setTransformTarget(row),
      isHidden: (row: Document) => row.status !== 'VALIDATED',
    }] : []),
    ...(type === 'QUOTE' ? [{
      id: 'convert',
      label: 'Convertir en facture',
      icon: 'arrow-right',
      onClick: (row: Document) => setConvertTarget(row),
      isHidden: (row: Document) => row.status !== 'VALIDATED',
    }] : []),
    {
      id: 'delete',
      label: 'Supprimer',
      icon: 'trash',
      variant: 'danger',
      onClick: (row) => setDeleteTarget(row),
      isHidden: (row) => row.status !== 'DRAFT' || !canDelete,
    },
  ];

  return (
    <PageWrapper
      title={typeConfig.labelPlural}
      actions={
        canCreate && (
          <Button
            leftIcon={<Plus size={16} />}
            onClick={() => navigate(`/invoicing/${type.toLowerCase()}s/new`)}
          >
            Nouveau {typeConfig.label.toLowerCase()}
          </Button>
        )
      }
    >
      <Card>
        <FilterBar
          filters={filters}
          onChange={setFilters}
          onExport={handleExport}
          isExporting={exportDocuments.isPending}
        />

        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          filterable
          actions={actions}
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          emptyMessage={`Aucun ${typeConfig.label.toLowerCase()}`}
          error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
          onRetry={() => refetch()}
        />
      </Card>

      {/* Delete Confirmation */}
      {deleteTarget && (
        <ConfirmDialog
          title="Confirmer la suppression"
          message={`Etes-vous sur de vouloir supprimer le ${typeConfig.label.toLowerCase()} ${deleteTarget.number} ?`}
          variant="danger"
          onConfirm={async () => {
            await deleteDocument.mutateAsync({ id: deleteTarget.id, type });
            setDeleteTarget(null);
          }}
          onCancel={() => setDeleteTarget(null)}
          isLoading={deleteDocument.isPending}
        />
      )}

      {/* Validate Confirmation */}
      {validateTarget && (
        <ConfirmDialog
          title="Confirmer la validation"
          message={`Voulez-vous valider le ${typeConfig.label.toLowerCase()} ${validateTarget.number} ? Un document valide ne peut plus etre modifie.`}
          variant="warning"
          confirmLabel="Valider"
          onConfirm={async () => {
            await validateDocument.mutateAsync({ id: validateTarget.id });
            setValidateTarget(null);
          }}
          onCancel={() => setValidateTarget(null)}
          isLoading={validateDocument.isPending}
        />
      )}

      {/* Convert Confirmation */}
      {convertTarget && (
        <ConfirmDialog
          title="Convertir en facture"
          message={`Voulez-vous creer une facture a partir du devis ${convertTarget.number} ?`}
          confirmLabel="Creer la facture"
          onConfirm={async () => {
            const invoice = await convertQuote.mutateAsync({ quoteId: convertTarget.id });
            setConvertTarget(null);
            navigate(`/invoicing/invoices/${invoice.id}`);
          }}
          onCancel={() => setConvertTarget(null)}
          isLoading={convertQuote.isPending}
        />
      )}

      {/* Duplicate Confirmation */}
      {duplicateTarget && (
        <ConfirmDialog
          title="Dupliquer le document"
          message={`Voulez-vous dupliquer le ${typeConfig.label.toLowerCase()} ${duplicateTarget.number} ?`}
          confirmLabel="Dupliquer"
          onConfirm={async () => {
            const newDoc = await duplicateDocument.mutateAsync({ document: duplicateTarget });
            setDuplicateTarget(null);
            navigate(`/invoicing/${type.toLowerCase()}s/${newDoc.id}`);
          }}
          onCancel={() => setDuplicateTarget(null)}
          isLoading={duplicateDocument.isPending}
        />
      )}

      {/* Transform Confirmation */}
      {transformTarget && transformConfig && (
        <ConfirmDialog
          title={transformConfig.label}
          message={`Voulez-vous transformer le ${typeConfig.label.toLowerCase()} ${transformTarget.number} en ${DOCUMENT_TYPE_CONFIG[transformConfig.target].label.toLowerCase()} ?`}
          confirmLabel={`Creer ${DOCUMENT_TYPE_CONFIG[transformConfig.target].label.toLowerCase()}`}
          onConfirm={async () => {
            const newDoc = await transformDocument.mutateAsync({
              document: transformTarget,
              targetType: transformConfig.target
            });
            setTransformTarget(null);
            navigate(`/invoicing/${transformConfig.target.toLowerCase()}s/${newDoc.id}`);
          }}
          onCancel={() => setTransformTarget(null)}
          isLoading={transformDocument.isPending}
        />
      )}
    </PageWrapper>
  );
};

export default DocumentListPage;
