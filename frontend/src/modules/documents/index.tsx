/**
 * AZALSCORE - Module Documents Unifié
 * ====================================
 *
 * Vue unique pour tous les documents commerciaux:
 * - Devis (QUOTE)
 * - Factures (INVOICE)
 * - Avoirs (CREDIT_NOTE)
 * - Commandes fournisseurs (PURCHASE_ORDER)
 * - Factures fournisseurs (PURCHASE_INVOICE)
 * - Clients
 * - Fournisseurs
 *
 * Le type de document est géré par état (URL params), pas par routes distinctes.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, useNavigate, useParams, useSearchParams, Link } from 'react-router-dom';
import {
  Plus, FileText, Check, Eye, Edit, Trash2, ArrowRight, RefreshCw,
  AlertCircle, CheckCircle2, ArrowLeft, Users, ShoppingCart
} from 'lucide-react';
import { useTranslation } from '@core/i18n';
import { CapabilityGuard, useHasCapability } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup, ConfirmDialog } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import type { TableColumn, TableAction, DashboardKPI } from '@/types';

// Local imports
import {
  LineEditor,
  DocumentStatusBadge,
  PartnerStatusBadge,
  FilterBar,
  PartnerSelector,
  DocumentTypeSelector,
  CategoryTabs,
} from './components';
import {
  useSalesDocuments,
  useSalesDocument,
  useCreateSalesDocument,
  useUpdateSalesDocument,
  useDeleteSalesDocument,
  useValidateSalesDocument,
  useConvertQuoteToInvoice,
  usePurchaseOrders,
  usePurchaseOrder,
  useCreatePurchaseOrder,
  useUpdatePurchaseOrder,
  useDeletePurchaseOrder,
  useValidatePurchaseOrder,
  usePurchaseInvoices,
  usePurchaseInvoice,
  useCreatePurchaseInvoice,
  useUpdatePurchaseInvoice,
  useDeletePurchaseInvoice,
  useValidatePurchaseInvoice,
  useCreateInvoiceFromOrder,
  useCustomers,
  useCustomer,
  useCreateCustomer,
  useUpdateCustomer,
  useDeleteCustomer,
  useSuppliers,
  useSupplier,
  useCreateSupplier,
  useUpdateSupplier,
  useDeleteSupplier,
  useDocumentsSummary,
  useExportDocuments,
  useCustomersLookup,
  useSuppliersLookup,
} from './hooks';
import {
  DOCUMENT_TYPE_CONFIG,
  STATUS_CONFIG,
  PARTNER_STATUS_CONFIG,
  PAYMENT_TERMS,
  formatCurrency,
  formatDate,
  canEditDocument,
  canValidateDocument,
  canConvertDocument,
  getDocumentCategory,
} from './constants';
import type {
  DocumentType,
  DocumentCategory,
  DocumentStatus,
  DocumentFilters,
  PartnerFilters,
  UnifiedDocument,
  SalesDocument,
  PurchaseOrder,
  PurchaseInvoice,
  Partner,
  Customer,
  Supplier,
  LineFormData,
  PartnerStatus,
} from './types';

// ============================================================
// DASHBOARD
// ============================================================

const DocumentsDashboard: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data: summary, isLoading } = useDocumentsSummary();

  const salesKPIs: DashboardKPI[] = summary
    ? [
        { id: 'quotes', label: t('documents.types.quotes'), value: summary.draft_quotes },
        { id: 'invoices', label: t('documents.types.invoices'), value: summary.draft_invoices },
        { id: 'customers', label: t('partners.customers'), value: summary.active_customers },
      ]
    : [];

  const purchasesKPIs: DashboardKPI[] = summary
    ? [
        { id: 'orders', label: t('documents.types.purchaseOrders'), value: summary.pending_orders },
        { id: 'value', label: t('common.amount'), value: formatCurrency(summary.pending_orders_value) },
        { id: 'suppliers', label: t('partners.suppliers'), value: summary.active_suppliers },
      ]
    : [];

  if (isLoading) {
    return (
      <PageWrapper title={t('documents.title')}>
        <div className="azals-loading">
          <RefreshCw className="animate-spin" size={24} />
          <span>{t('common.loading')}</span>
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper title={t('documents.title')} subtitle={t('documents.subtitle')}>
      {/* Section Ventes */}
      <section className="azals-section">
        <h2 className="azals-section__title">{t('documents.categories.sales')}</h2>
        <Grid cols={3} gap="md">
          {salesKPIs.map((kpi) => (
            <KPICard key={kpi.id} kpi={kpi} />
          ))}
        </Grid>
        <Grid cols={4} gap="md" className="mt-4">
          <Card className="azals-dashboard-card" onClick={() => navigate('/documents/list?type=QUOTE')}>
            <FileText size={24} />
            <span>{t('documents.types.quotes')}</span>
          </Card>
          <Card className="azals-dashboard-card" onClick={() => navigate('/documents/list?type=INVOICE')}>
            <FileText size={24} />
            <span>{t('documents.types.invoices')}</span>
          </Card>
          <Card className="azals-dashboard-card" onClick={() => navigate('/documents/list?type=CREDIT_NOTE')}>
            <FileText size={24} />
            <span>{t('documents.types.creditNotes')}</span>
          </Card>
          <Card className="azals-dashboard-card" onClick={() => navigate('/documents/partners?type=CUSTOMER')}>
            <Users size={24} />
            <span>{t('partners.customers')}</span>
          </Card>
        </Grid>
      </section>

      {/* Section Achats */}
      <section className="azals-section mt-6">
        <h2 className="azals-section__title">{t('documents.categories.purchases')}</h2>
        <Grid cols={3} gap="md">
          {purchasesKPIs.map((kpi) => (
            <KPICard key={kpi.id} kpi={kpi} />
          ))}
        </Grid>
        <Grid cols={3} gap="md" className="mt-4">
          <Card className="azals-dashboard-card" onClick={() => navigate('/documents/list?type=PURCHASE_ORDER')}>
            <ShoppingCart size={24} />
            <span>{t('documents.types.purchaseOrders')}</span>
          </Card>
          <Card className="azals-dashboard-card" onClick={() => navigate('/documents/list?type=PURCHASE_INVOICE')}>
            <FileText size={24} />
            <span>{t('documents.types.purchaseInvoices')}</span>
          </Card>
          <Card className="azals-dashboard-card" onClick={() => navigate('/documents/partners?type=SUPPLIER')}>
            <Users size={24} />
            <span>{t('partners.suppliers')}</span>
          </Card>
        </Grid>
      </section>
    </PageWrapper>
  );
};

// ============================================================
// LISTE DES DOCUMENTS
// ============================================================

const DocumentListPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // État
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<DocumentFilters>({});
  const [deleteTarget, setDeleteTarget] = useState<UnifiedDocument | null>(null);
  const [validateTarget, setValidateTarget] = useState<UnifiedDocument | null>(null);
  const [convertTarget, setConvertTarget] = useState<UnifiedDocument | null>(null);

  // Type de document depuis URL
  const documentType = (searchParams.get('type') as DocumentType) || 'QUOTE';
  const config = DOCUMENT_TYPE_CONFIG[documentType];
  const category = getDocumentCategory(documentType);
  const isSales = category === 'SALES';

  // Données
  const salesQuery = useSalesDocuments(
    documentType as 'QUOTE' | 'INVOICE' | 'CREDIT_NOTE',
    page,
    pageSize,
    filters
  );
  const ordersQuery = usePurchaseOrders(page, pageSize, filters);
  const purchaseInvoicesQuery = usePurchaseInvoices(page, pageSize, filters);

  // Sélectionner la bonne query
  const getActiveQuery = () => {
    if (isSales) return salesQuery;
    if (documentType === 'PURCHASE_ORDER') return ordersQuery;
    return purchaseInvoicesQuery;
  };
  const { data, isLoading, refetch } = getActiveQuery();

  // Mutations
  const deleteSales = useDeleteSalesDocument();
  const deletePurchaseOrder = useDeletePurchaseOrder();
  const deletePurchaseInvoice = useDeletePurchaseInvoice();
  const validateSales = useValidateSalesDocument();
  const validatePurchaseOrder = useValidatePurchaseOrder();
  const validatePurchaseInvoice = useValidatePurchaseInvoice();
  const convertQuote = useConvertQuoteToInvoice();
  const createInvoiceFromOrder = useCreateInvoiceFromOrder();
  const exportDocuments = useExportDocuments();

  // Partenaires pour les filtres
  const { data: customers } = useCustomersLookup('');
  const { data: suppliers } = useSuppliersLookup('');
  const partners = isSales ? (customers || []) : (suppliers || []);

  // Permissions
  const canCreate = useHasCapability(isSales ? 'invoicing.create' : 'purchases.create');
  const canEdit = useHasCapability(isSales ? 'invoicing.edit' : 'purchases.edit');
  const canDelete = useHasCapability(isSales ? 'invoicing.delete' : 'purchases.delete');

  // Changer le type
  const handleTypeChange = (type: DocumentType) => {
    setSearchParams({ type });
    setPage(1);
    setFilters({});
  };

  // Export
  const handleExport = async () => {
    try {
      const blob = await exportDocuments.mutateAsync({ type: documentType, filters });
      const url = window.URL.createObjectURL(new Blob([blob as unknown as BlobPart]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${documentType.toLowerCase()}_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  // Supprimer
  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      if (isSales) {
        await deleteSales.mutateAsync({
          id: deleteTarget.id,
          type: documentType as 'QUOTE' | 'INVOICE' | 'CREDIT_NOTE',
        });
      } else if (documentType === 'PURCHASE_ORDER') {
        await deletePurchaseOrder.mutateAsync(deleteTarget.id);
      } else {
        await deletePurchaseInvoice.mutateAsync(deleteTarget.id);
      }
      setDeleteTarget(null);
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  // Valider
  const handleValidate = async () => {
    if (!validateTarget) return;
    try {
      if (isSales) {
        await validateSales.mutateAsync({ id: validateTarget.id });
      } else if (documentType === 'PURCHASE_ORDER') {
        await validatePurchaseOrder.mutateAsync(validateTarget.id);
      } else {
        await validatePurchaseInvoice.mutateAsync(validateTarget.id);
      }
      setValidateTarget(null);
    } catch (error) {
      console.error('Validate failed:', error);
    }
  };

  // Convertir
  const handleConvert = async () => {
    if (!convertTarget) return;
    try {
      if (documentType === 'QUOTE') {
        const invoice = await convertQuote.mutateAsync({ quoteId: convertTarget.id });
        setConvertTarget(null);
        navigate(`/documents/${invoice.id}?type=INVOICE`);
      } else if (documentType === 'PURCHASE_ORDER') {
        const invoice = await createInvoiceFromOrder.mutateAsync(convertTarget.id);
        setConvertTarget(null);
        navigate(`/documents/${invoice.id}?type=PURCHASE_INVOICE`);
      }
    } catch (error) {
      console.error('Convert failed:', error);
    }
  };

  // Colonnes du tableau
  const columns: TableColumn<UnifiedDocument>[] = [
    {
      id: 'number',
      header: t('partners.fields.code'),
      accessor: 'number',
      sortable: true,
      render: (value, row) => (
        <Link to={`/documents/${row.id}?type=${documentType}`} className="azals-link">
          {value as string}
        </Link>
      ),
    },
    {
      id: 'partner',
      header: isSales ? t('documents.form.customer') : t('documents.form.supplier'),
      accessor: isSales ? 'customer_name' : 'supplier_name',
      sortable: true,
    },
    {
      id: 'date',
      header: t('common.date'),
      accessor: 'date',
      sortable: true,
      render: (value) => formatDate(value as string),
    },
    {
      id: 'status',
      header: t('common.status'),
      accessor: 'status',
      render: (value) => <DocumentStatusBadge status={value as DocumentStatus} />,
    },
    {
      id: 'total',
      header: t('common.total'),
      accessor: 'total',
      align: 'right',
      render: (value, row) => formatCurrency(value as number, row.currency),
    },
  ];

  // Actions du tableau
  const actions: TableAction<UnifiedDocument>[] = [
    {
      id: 'view',
      label: t('common.view'),
      icon: 'eye',
      onClick: (row) => navigate(`/documents/${row.id}?type=${documentType}`),
    },
    {
      id: 'edit',
      label: t('common.edit'),
      icon: 'edit',
      onClick: (row) => navigate(`/documents/${row.id}/edit?type=${documentType}`),
      isHidden: (row) => !canEditDocument(row.status) || !canEdit,
    },
    {
      id: 'validate',
      label: t('common.validate'),
      icon: 'check',
      onClick: (row) => setValidateTarget(row),
      isHidden: (row) => !canValidateDocument(row.status) || !canEdit,
    },
    {
      id: 'convert',
      label: t('documents.actions.convert'),
      icon: 'arrow-right',
      onClick: (row) => setConvertTarget(row),
      isHidden: (row) => !canConvertDocument(documentType, row.status),
    },
    {
      id: 'delete',
      label: t('common.delete'),
      icon: 'trash',
      variant: 'danger',
      onClick: (row) => setDeleteTarget(row),
      isHidden: (row) => !canEditDocument(row.status) || !canDelete,
    },
  ];

  return (
    <PageWrapper
      title={t(config.labelPluralKey)}
      actions={
        canCreate && (
          <Button
            leftIcon={<Plus size={16} />}
            onClick={() => navigate(`/documents/new?type=${documentType}`)}
          >
            {t('documents.newDocument')}
          </Button>
        )
      }
    >
      {/* Sélecteur de type */}
      <DocumentTypeSelector
        value={documentType}
        onChange={handleTypeChange}
      />

      <Card className="mt-4">
        <FilterBar
          documentType={documentType}
          filters={filters}
          onChange={setFilters}
          partners={partners as Partner[]}
          onExport={handleExport}
          isExporting={exportDocuments.isPending}
          exportCapability={isSales ? 'invoicing.export' : 'purchases.export'}
        />

        <DataTable
          columns={columns}
          data={(data?.items || []) as UnifiedDocument[]}
          keyField="id"
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
          emptyMessage={t('documents.noDocuments')}
        />
      </Card>

      {/* Dialogs */}
      {deleteTarget && (
        <ConfirmDialog
          title={t('common.confirm')}
          message={t('documents.messages.confirmDelete')}
          variant="danger"
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
          isLoading={deleteSales.isPending || deletePurchaseOrder.isPending || deletePurchaseInvoice.isPending}
        />
      )}

      {validateTarget && (
        <ConfirmDialog
          title={t('documents.actions.validate')}
          message={
            <>
              <p>{t('documents.messages.confirmValidate')}</p>
              <p className="text-warning mt-2">
                <AlertCircle size={14} className="inline mr-1" />
                {t('documents.messages.validateWarning')}
              </p>
            </>
          }
          variant="warning"
          confirmLabel={t('common.validate')}
          onConfirm={handleValidate}
          onCancel={() => setValidateTarget(null)}
          isLoading={validateSales.isPending || validatePurchaseOrder.isPending || validatePurchaseInvoice.isPending}
        />
      )}

      {convertTarget && (
        <ConfirmDialog
          title={t('documents.actions.convert')}
          message={
            <>
              <p>{t('documents.messages.convertConfirm')}</p>
              <p className="text-muted mt-2">{t('documents.messages.convertInfo')}</p>
            </>
          }
          confirmLabel={t('documents.actions.createInvoice')}
          onConfirm={handleConvert}
          onCancel={() => setConvertTarget(null)}
          isLoading={convertQuote.isPending || createInvoiceFromOrder.isPending}
        />
      )}
    </PageWrapper>
  );
};

// ============================================================
// FORMULAIRE DE DOCUMENT
// ============================================================

const DocumentFormPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const isNew = !id || id === 'new';

  // Type de document
  const documentType = (searchParams.get('type') as DocumentType) || 'QUOTE';
  const config = DOCUMENT_TYPE_CONFIG[documentType];
  const category = getDocumentCategory(documentType);
  const isSales = category === 'SALES';

  // Queries pour charger le document existant
  const salesDocQuery = useSalesDocument(isSales ? (id || '') : '');
  const purchaseOrderQuery = usePurchaseOrder(documentType === 'PURCHASE_ORDER' ? (id || '') : '');
  const purchaseInvoiceQuery = usePurchaseInvoice(documentType === 'PURCHASE_INVOICE' ? (id || '') : '');

  const getDocumentQuery = () => {
    if (isSales) return salesDocQuery;
    if (documentType === 'PURCHASE_ORDER') return purchaseOrderQuery;
    return purchaseInvoiceQuery;
  };
  const { data: existingDoc, isLoading: loadingDoc } = getDocumentQuery();

  // Mutations
  const createSales = useCreateSalesDocument();
  const updateSales = useUpdateSalesDocument();
  const createPurchaseOrder = useCreatePurchaseOrder();
  const updatePurchaseOrder = useUpdatePurchaseOrder();
  const createPurchaseInvoice = useCreatePurchaseInvoice();
  const updatePurchaseInvoice = useUpdatePurchaseInvoice();

  // État du formulaire
  const [partnerId, setPartnerId] = useState('');
  const [docDate, setDocDate] = useState(new Date().toISOString().split('T')[0]);
  const [dueDate, setDueDate] = useState('');
  const [validityDate, setValidityDate] = useState('');
  const [expectedDate, setExpectedDate] = useState('');
  const [reference, setReference] = useState('');
  const [notes, setNotes] = useState('');
  const [lines, setLines] = useState<LineFormData[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Charger les données existantes
  useEffect(() => {
    if (existingDoc) {
      setDocDate(existingDoc.date?.split('T')[0] || '');
      setNotes(existingDoc.notes || '');
      setLines(
        existingDoc.lines.map((l) => ({
          id: l.id,
          description: l.description,
          quantity: l.quantity,
          unit: l.unit,
          unit_price: l.unit_price,
          discount_percent: l.discount_percent,
          tax_rate: l.tax_rate,
        }))
      );

      if (isSales) {
        const doc = existingDoc as SalesDocument;
        setPartnerId(doc.customer_id);
        setDueDate(doc.due_date?.split('T')[0] || '');
        setValidityDate(doc.validity_date?.split('T')[0] || '');
      } else if (documentType === 'PURCHASE_ORDER') {
        const doc = existingDoc as PurchaseOrder;
        setPartnerId(doc.supplier_id);
        setExpectedDate(doc.expected_date?.split('T')[0] || '');
        setReference(doc.reference || '');
      } else {
        const doc = existingDoc as PurchaseInvoice;
        setPartnerId(doc.supplier_id);
        setDueDate(doc.due_date?.split('T')[0] || '');
        setReference(doc.supplier_reference || '');
      }
    }
  }, [existingDoc, isSales, documentType]);

  // Rediriger si le document n'est pas modifiable
  useEffect(() => {
    if (!isNew && existingDoc && !canEditDocument(existingDoc.status)) {
      navigate(`/documents/${id}?type=${documentType}`);
    }
  }, [existingDoc, isNew, id, documentType, navigate]);

  // Validation
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!partnerId) {
      newErrors.partner = isSales
        ? t('documents.errors.selectCustomer')
        : t('documents.errors.selectSupplier');
    }
    if (!docDate) {
      newErrors.date = t('documents.errors.dateRequired');
    }
    if (lines.length === 0) {
      newErrors.lines = t('documents.errors.addLine');
    }
    if (lines.some((l) => !l.description.trim())) {
      newErrors.lines = t('documents.errors.lineDescription');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Soumission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      const cleanedLines = lines.map(({ id: lineId, ...rest }) => rest);

      if (isSales) {
        const data = {
          type: documentType as 'QUOTE' | 'INVOICE' | 'CREDIT_NOTE',
          customer_id: partnerId,
          date: docDate,
          due_date: dueDate || undefined,
          validity_date: validityDate || undefined,
          notes: notes || undefined,
          lines: cleanedLines,
        };

        if (isNew) {
          await createSales.mutateAsync(data);
        } else {
          await updateSales.mutateAsync({ id: id!, data: { ...data, lines } });
        }
      } else if (documentType === 'PURCHASE_ORDER') {
        const data = {
          supplier_id: partnerId,
          date: docDate,
          expected_date: expectedDate || undefined,
          reference: reference || undefined,
          notes: notes || undefined,
          lines: cleanedLines,
        };

        if (isNew) {
          await createPurchaseOrder.mutateAsync(data);
        } else {
          await updatePurchaseOrder.mutateAsync({ id: id!, data: { ...data, lines } });
        }
      } else {
        const data = {
          supplier_id: partnerId,
          date: docDate,
          due_date: dueDate || undefined,
          supplier_reference: reference || undefined,
          notes: notes || undefined,
          lines: cleanedLines,
        };

        if (isNew) {
          await createPurchaseInvoice.mutateAsync(data);
        } else {
          await updatePurchaseInvoice.mutateAsync({ id: id!, data: { ...data, lines } });
        }
      }

      navigate(`/documents/list?type=${documentType}`);
    } catch (error) {
      console.error('Save failed:', error);
    }
  };

  const isSubmitting =
    createSales.isPending ||
    updateSales.isPending ||
    createPurchaseOrder.isPending ||
    updatePurchaseOrder.isPending ||
    createPurchaseInvoice.isPending ||
    updatePurchaseInvoice.isPending;

  if (!isNew && loadingDoc) {
    return (
      <PageWrapper title={t('common.loading')}>
        <div className="azals-loading">
          <RefreshCw className="animate-spin" size={24} />
          <span>{t('common.loading')}</span>
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={`${isNew ? t('common.create') : t('common.edit')} ${t(config.labelKey)}`}
      actions={
        <Button
          variant="ghost"
          leftIcon={<ArrowLeft size={16} />}
          onClick={() => navigate(`/documents/list?type=${documentType}`)}
        >
          {t('common.back')}
        </Button>
      }
    >
      <form onSubmit={handleSubmit}>
        <Card className="mb-4">
          <h3 className="mb-4">{t('documents.form.generalInfo')}</h3>

          <Grid cols={2} gap="md">
            {/* Sélecteur de partenaire */}
            <PartnerSelector
              type={config.partnerType}
              value={partnerId}
              onChange={setPartnerId}
              disabled={!isNew}
              error={errors.partner}
              required
            />

            {/* Date */}
            <div className="azals-form-field">
              <label htmlFor="date">{t('documents.form.date')} *</label>
              <input
                type="date"
                id="date"
                value={docDate}
                onChange={(e) => setDocDate(e.target.value)}
                className={`azals-input ${errors.date ? 'azals-input--error' : ''}`}
              />
              {errors.date && <span className="azals-form-error">{errors.date}</span>}
            </div>

            {/* Date de validité (devis) */}
            {config.hasValidityDate && (
              <div className="azals-form-field">
                <label htmlFor="validity">{t('documents.form.validityDate')}</label>
                <input
                  type="date"
                  id="validity"
                  value={validityDate}
                  onChange={(e) => setValidityDate(e.target.value)}
                  className="azals-input"
                />
              </div>
            )}

            {/* Date d'échéance */}
            {config.hasDueDate && (
              <div className="azals-form-field">
                <label htmlFor="due">{t('documents.form.dueDate')}</label>
                <input
                  type="date"
                  id="due"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="azals-input"
                />
              </div>
            )}

            {/* Date de livraison prévue (commandes) */}
            {config.hasExpectedDate && (
              <div className="azals-form-field">
                <label htmlFor="expected">{t('documents.form.expectedDate')}</label>
                <input
                  type="date"
                  id="expected"
                  value={expectedDate}
                  onChange={(e) => setExpectedDate(e.target.value)}
                  className="azals-input"
                />
              </div>
            )}

            {/* Référence fournisseur */}
            {config.hasSupplierReference && (
              <div className="azals-form-field">
                <label htmlFor="reference">{t('documents.form.supplierReference')}</label>
                <input
                  type="text"
                  id="reference"
                  value={reference}
                  onChange={(e) => setReference(e.target.value)}
                  className="azals-input"
                />
              </div>
            )}
          </Grid>

          {/* Notes */}
          <div className="azals-form-field mt-4">
            <label htmlFor="notes">{t('documents.form.notes')}</label>
            <textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="azals-textarea"
              rows={3}
            />
          </div>
        </Card>

        {/* Lignes */}
        <Card className="mb-4">
          {errors.lines && (
            <div className="azals-alert azals-alert--error mb-4">
              <AlertCircle size={16} />
              <span>{errors.lines}</span>
            </div>
          )}
          <LineEditor lines={lines} onChange={setLines} />
        </Card>

        {/* Actions */}
        <div className="azals-form-actions">
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate(`/documents/list?type=${documentType}`)}
          >
            {t('common.cancel')}
          </Button>
          <Button type="submit" isLoading={isSubmitting} leftIcon={<Check size={16} />}>
            {isNew ? t('documents.actions.create') : t('common.save')}
          </Button>
        </div>
      </form>
    </PageWrapper>
  );
};

// ============================================================
// DÉTAIL DU DOCUMENT
// ============================================================

const DocumentDetailPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const [validateModal, setValidateModal] = useState(false);
  const [convertModal, setConvertModal] = useState(false);

  // Type de document
  const documentType = (searchParams.get('type') as DocumentType) || 'QUOTE';
  const config = DOCUMENT_TYPE_CONFIG[documentType];
  const category = getDocumentCategory(documentType);
  const isSales = category === 'SALES';

  // Queries
  const salesDocQuery = useSalesDocument(isSales ? (id || '') : '');
  const purchaseOrderQuery = usePurchaseOrder(documentType === 'PURCHASE_ORDER' ? (id || '') : '');
  const purchaseInvoiceQuery = usePurchaseInvoice(documentType === 'PURCHASE_INVOICE' ? (id || '') : '');

  const getDocumentQuery = () => {
    if (isSales) return salesDocQuery;
    if (documentType === 'PURCHASE_ORDER') return purchaseOrderQuery;
    return purchaseInvoiceQuery;
  };
  const { data: document, isLoading } = getDocumentQuery();

  // Mutations
  const validateSales = useValidateSalesDocument();
  const validatePurchaseOrder = useValidatePurchaseOrder();
  const validatePurchaseInvoice = useValidatePurchaseInvoice();
  const convertQuote = useConvertQuoteToInvoice();
  const createInvoiceFromOrder = useCreateInvoiceFromOrder();

  // Permissions
  const canEdit = useHasCapability(isSales ? 'invoicing.edit' : 'purchases.edit');

  if (isLoading) {
    return (
      <PageWrapper title={t(config.labelKey)}>
        <div className="azals-loading">
          <RefreshCw className="animate-spin" size={24} />
          <span>{t('common.loading')}</span>
        </div>
      </PageWrapper>
    );
  }

  if (!document) {
    return (
      <PageWrapper title={t(config.labelKey)}>
        <Card>
          <div className="azals-empty">
            <AlertCircle size={48} />
            <h3>{t('documents.messages.notFound')}</h3>
            <p>{t('documents.messages.notFoundDesc')}</p>
            <Button onClick={() => navigate(`/documents/list?type=${documentType}`)}>
              {t('common.back')}
            </Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  const isDraft = canEditDocument(document.status);
  const canConvert = canConvertDocument(documentType, document.status);

  // Nom du partenaire
  const partnerName = isSales
    ? (document as SalesDocument).customer_name
    : documentType === 'PURCHASE_ORDER'
      ? (document as PurchaseOrder).supplier_name
      : (document as PurchaseInvoice).supplier_name;

  const handleValidate = async () => {
    try {
      if (isSales) {
        await validateSales.mutateAsync({ id: document.id });
      } else if (documentType === 'PURCHASE_ORDER') {
        await validatePurchaseOrder.mutateAsync(document.id);
      } else {
        await validatePurchaseInvoice.mutateAsync(document.id);
      }
      setValidateModal(false);
    } catch (error) {
      console.error('Validate failed:', error);
    }
  };

  const handleConvert = async () => {
    try {
      if (documentType === 'QUOTE') {
        const invoice = await convertQuote.mutateAsync({ quoteId: document.id });
        setConvertModal(false);
        navigate(`/documents/${invoice.id}?type=INVOICE`);
      } else if (documentType === 'PURCHASE_ORDER') {
        const invoice = await createInvoiceFromOrder.mutateAsync(document.id);
        setConvertModal(false);
        navigate(`/documents/${invoice.id}?type=PURCHASE_INVOICE`);
      }
    } catch (error) {
      console.error('Convert failed:', error);
    }
  };

  return (
    <PageWrapper
      title={`${t(config.labelKey)} ${document.number}`}
      actions={
        <ButtonGroup>
          <Button
            variant="ghost"
            leftIcon={<ArrowLeft size={16} />}
            onClick={() => navigate(`/documents/list?type=${documentType}`)}
          >
            {t('common.back')}
          </Button>
          {isDraft && canEdit && (
            <>
              <Button
                variant="ghost"
                leftIcon={<Edit size={16} />}
                onClick={() => navigate(`/documents/${id}/edit?type=${documentType}`)}
              >
                {t('common.edit')}
              </Button>
              <Button leftIcon={<Check size={16} />} onClick={() => setValidateModal(true)}>
                {t('common.validate')}
              </Button>
            </>
          )}
          {canConvert && (
            <Button leftIcon={<ArrowRight size={16} />} onClick={() => setConvertModal(true)}>
              {t('documents.actions.convert')}
            </Button>
          )}
        </ButtonGroup>
      }
    >
      {/* KPIs */}
      <Grid cols={3} gap="md" className="mb-4">
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">{t('common.status')}</span>
            <DocumentStatusBadge status={document.status} />
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">{t('documents.lines.totalHT')}</span>
            <span className="azals-stat__value">{formatCurrency(document.subtotal, document.currency)}</span>
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">{t('documents.lines.totalTTC')}</span>
            <span className="azals-stat__value azals-stat__value--primary">
              {formatCurrency(document.total, document.currency)}
            </span>
          </div>
        </Card>
      </Grid>

      {/* Informations */}
      <Card className="mb-4">
        <div className="azals-document-header">
          <div>
            <h2>{partnerName}</h2>
            <p className="text-muted">N° {document.number}</p>
          </div>
          <div className="text-right">
            <p>
              <strong>{t('documents.form.date')}:</strong> {formatDate(document.date)}
            </p>
            {document.validated_at && (
              <p className="text-success">
                <CheckCircle2 size={14} className="inline mr-1" />
                {t('common.validated')} {formatDate(document.validated_at)}
              </p>
            )}
          </div>
        </div>
      </Card>

      {/* Lignes */}
      <Card className="mb-4">
        <LineEditor
          lines={document.lines.map((l) => ({
            id: l.id,
            description: l.description,
            quantity: l.quantity,
            unit: l.unit,
            unit_price: l.unit_price,
            discount_percent: l.discount_percent,
            tax_rate: l.tax_rate,
          }))}
          onChange={() => {}}
          readOnly
          currency={document.currency}
        />
      </Card>

      {/* Notes */}
      {document.notes && (
        <Card>
          <h4>{t('documents.form.notes')}</h4>
          <p className="text-muted">{document.notes}</p>
        </Card>
      )}

      {/* Modals */}
      {validateModal && (
        <ConfirmDialog
          title={t('documents.actions.validate')}
          message={
            <>
              <p>{t('documents.messages.confirmValidate')}</p>
              <p className="text-warning mt-2">
                <AlertCircle size={14} className="inline mr-1" />
                {t('documents.messages.validateWarning')}
              </p>
            </>
          }
          variant="warning"
          confirmLabel={t('common.validate')}
          onConfirm={handleValidate}
          onCancel={() => setValidateModal(false)}
          isLoading={validateSales.isPending || validatePurchaseOrder.isPending || validatePurchaseInvoice.isPending}
        />
      )}

      {convertModal && (
        <ConfirmDialog
          title={t('documents.actions.convert')}
          message={
            <>
              <p>{t('documents.messages.convertConfirm')}</p>
              <p className="text-muted mt-2">{t('documents.messages.convertInfo')}</p>
            </>
          }
          confirmLabel={t('documents.actions.createInvoice')}
          onConfirm={handleConvert}
          onCancel={() => setConvertModal(false)}
          isLoading={convertQuote.isPending || createInvoiceFromOrder.isPending}
        />
      )}
    </PageWrapper>
  );
};

// ============================================================
// LISTE DES PARTENAIRES (Clients / Fournisseurs)
// ============================================================

const PartnersListPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const partnerType = (searchParams.get('type') as 'CUSTOMER' | 'SUPPLIER') || 'CUSTOMER';
  const isCustomer = partnerType === 'CUSTOMER';

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<PartnerFilters>({});
  const [deleteTarget, setDeleteTarget] = useState<Partner | null>(null);

  // Queries
  const customersQuery = useCustomers(page, pageSize, filters);
  const suppliersQuery = useSuppliers(page, pageSize, filters);
  const { data, isLoading, refetch } = isCustomer ? customersQuery : suppliersQuery;

  // Mutations
  const deleteCustomer = useDeleteCustomer();
  const deleteSupplier = useDeleteSupplier();

  // Permissions
  const canCreate = useHasCapability(isCustomer ? 'partners.create' : 'purchases.create');
  const canDelete = useHasCapability(isCustomer ? 'partners.delete' : 'purchases.delete');

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      if (isCustomer) {
        await deleteCustomer.mutateAsync(deleteTarget.id);
      } else {
        await deleteSupplier.mutateAsync(deleteTarget.id);
      }
      setDeleteTarget(null);
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  const columns: TableColumn<Partner>[] = [
    { id: 'code', header: t('partners.fields.code'), accessor: 'code', sortable: true },
    { id: 'name', header: t('partners.fields.name'), accessor: 'name', sortable: true },
    { id: 'contact', header: t('partners.fields.contact'), accessor: 'contact_name' },
    { id: 'email', header: t('partners.fields.email'), accessor: 'email' },
    { id: 'phone', header: t('partners.fields.phone'), accessor: 'phone' },
    {
      id: 'status',
      header: t('common.status'),
      accessor: 'status',
      render: (value) => <PartnerStatusBadge status={value as PartnerStatus} />,
    },
  ];

  const actions: TableAction<Partner>[] = [
    {
      id: 'view',
      label: t('common.view'),
      onClick: (row) => navigate(`/documents/partners/${row.id}?type=${partnerType}`),
    },
    {
      id: 'edit',
      label: t('common.edit'),
      onClick: (row) => navigate(`/documents/partners/${row.id}/edit?type=${partnerType}`),
    },
    {
      id: 'delete',
      label: t('common.delete'),
      variant: 'danger',
      onClick: (row) => setDeleteTarget(row),
      isHidden: () => !canDelete,
    },
  ];

  return (
    <PageWrapper
      title={isCustomer ? t('partners.customers') : t('partners.suppliers')}
      actions={
        canCreate && (
          <Button
            leftIcon={<Plus size={16} />}
            onClick={() => navigate(`/documents/partners/new?type=${partnerType}`)}
          >
            {isCustomer ? t('partners.newCustomer') : t('partners.newSupplier')}
          </Button>
        )
      }
    >
      {/* Tabs Clients / Fournisseurs */}
      <div className="azals-category-tabs mb-4">
        <button
          className={`azals-category-tabs__tab ${isCustomer ? 'azals-category-tabs__tab--active' : ''}`}
          onClick={() => setSearchParams({ type: 'CUSTOMER' })}
        >
          {t('partners.customers')}
        </button>
        <button
          className={`azals-category-tabs__tab ${!isCustomer ? 'azals-category-tabs__tab--active' : ''}`}
          onClick={() => setSearchParams({ type: 'SUPPLIER' })}
        >
          {t('partners.suppliers')}
        </button>
      </div>

      <Card>
        {/* Recherche simple */}
        <div className="azals-filter-bar mb-4">
          <div className="azals-filter-bar__search">
            <input
              type="text"
              placeholder={t('partners.searchPlaceholder')}
              value={filters.search || ''}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="azals-input"
            />
          </div>
        </div>

        <DataTable
          columns={columns}
          data={(data?.items || []) as Partner[]}
          keyField="id"
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
          emptyMessage={t('partners.noPartners')}
        />
      </Card>

      {deleteTarget && (
        <ConfirmDialog
          title={t('common.confirm')}
          message={t('documents.messages.confirmDelete')}
          variant="danger"
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
          isLoading={deleteCustomer.isPending || deleteSupplier.isPending}
        />
      )}
    </PageWrapper>
  );
};

// ============================================================
// FORMULAIRE PARTENAIRE
// ============================================================

const PartnerFormPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const isNew = !id || id === 'new';

  const partnerType = (searchParams.get('type') as 'CUSTOMER' | 'SUPPLIER') || 'CUSTOMER';
  const isCustomer = partnerType === 'CUSTOMER';

  // Queries
  const customerQuery = useCustomer(isCustomer ? (id || '') : '');
  const supplierQuery = useSupplier(!isCustomer ? (id || '') : '');
  const { data: existingPartner, isLoading } = isCustomer ? customerQuery : supplierQuery;

  // Mutations
  const createCustomer = useCreateCustomer();
  const updateCustomer = useUpdateCustomer();
  const createSupplier = useCreateSupplier();
  const updateSupplier = useUpdateSupplier();

  // État du formulaire
  const [form, setForm] = useState({
    name: '',
    contact_name: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    postal_code: '',
    country: 'France',
    tax_id: '',
    payment_terms: 'NET30',
    notes: '',
  });

  useEffect(() => {
    if (existingPartner) {
      setForm({
        name: existingPartner.name || '',
        contact_name: existingPartner.contact_name || '',
        email: existingPartner.email || '',
        phone: existingPartner.phone || '',
        address: existingPartner.address || '',
        city: existingPartner.city || '',
        postal_code: existingPartner.postal_code || '',
        country: existingPartner.country || 'France',
        tax_id: existingPartner.tax_id || '',
        payment_terms: existingPartner.payment_terms || 'NET30',
        notes: existingPartner.notes || '',
      });
    }
  }, [existingPartner]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isCustomer) {
        if (isNew) {
          const result = await createCustomer.mutateAsync(form as any);
          navigate(`/documents/partners/${result.id}?type=CUSTOMER`);
        } else {
          await updateCustomer.mutateAsync({ id: id!, data: form });
          navigate(`/documents/partners/${id}?type=CUSTOMER`);
        }
      } else {
        if (isNew) {
          const result = await createSupplier.mutateAsync(form as any);
          navigate(`/documents/partners/${result.id}?type=SUPPLIER`);
        } else {
          await updateSupplier.mutateAsync({ id: id!, data: form });
          navigate(`/documents/partners/${id}?type=SUPPLIER`);
        }
      }
    } catch (error) {
      console.error('Save failed:', error);
    }
  };

  const isSubmitting =
    createCustomer.isPending ||
    updateCustomer.isPending ||
    createSupplier.isPending ||
    updateSupplier.isPending;

  if (!isNew && isLoading) {
    return (
      <PageWrapper title={t('common.loading')}>
        <div className="azals-loading">
          <RefreshCw className="animate-spin" size={24} />
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={
        isNew
          ? isCustomer
            ? t('partners.newCustomer')
            : t('partners.newSupplier')
          : `${t('common.edit')} ${existingPartner?.name || ''}`
      }
      actions={
        <Button
          variant="ghost"
          leftIcon={<ArrowLeft size={16} />}
          onClick={() => navigate(`/documents/partners?type=${partnerType}`)}
        >
          {t('common.back')}
        </Button>
      }
    >
      <form onSubmit={handleSubmit}>
        <Card className="mb-4">
          <h3 className="mb-4">{t('documents.form.generalInfo')}</h3>
          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <label>{t('partners.fields.name')} *</label>
              <input
                type="text"
                className="azals-input"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="azals-form-field">
              <label>{t('partners.fields.contact')}</label>
              <input
                type="text"
                className="azals-input"
                value={form.contact_name}
                onChange={(e) => setForm({ ...form, contact_name: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>{t('partners.fields.email')}</label>
              <input
                type="email"
                className="azals-input"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>{t('partners.fields.phone')}</label>
              <input
                type="text"
                className="azals-input"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>{t('partners.fields.taxId')}</label>
              <input
                type="text"
                className="azals-input"
                value={form.tax_id}
                onChange={(e) => setForm({ ...form, tax_id: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>{t('partners.fields.paymentTerms')}</label>
              <select
                className="azals-select"
                value={form.payment_terms}
                onChange={(e) => setForm({ ...form, payment_terms: e.target.value })}
              >
                {PAYMENT_TERMS.map((term) => (
                  <option key={term.value} value={term.value}>
                    {t(term.labelKey)}
                  </option>
                ))}
              </select>
            </div>
          </Grid>
        </Card>

        <Card className="mb-4">
          <h3 className="mb-4">{t('partners.fields.address')}</h3>
          <Grid cols={2} gap="md">
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>{t('partners.fields.address')}</label>
              <input
                type="text"
                className="azals-input"
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>{t('partners.fields.postalCode')}</label>
              <input
                type="text"
                className="azals-input"
                value={form.postal_code}
                onChange={(e) => setForm({ ...form, postal_code: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>{t('partners.fields.city')}</label>
              <input
                type="text"
                className="azals-input"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>{t('partners.fields.country')}</label>
              <input
                type="text"
                className="azals-input"
                value={form.country}
                onChange={(e) => setForm({ ...form, country: e.target.value })}
              />
            </div>
          </Grid>
        </Card>

        <Card className="mb-4">
          <h3 className="mb-4">{t('partners.fields.notes')}</h3>
          <textarea
            className="azals-textarea"
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            rows={4}
          />
        </Card>

        <div className="azals-form-actions">
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate(`/documents/partners?type=${partnerType}`)}
          >
            {t('common.cancel')}
          </Button>
          <Button type="submit" isLoading={isSubmitting} leftIcon={<Check size={16} />}>
            {isNew ? t('common.create') : t('common.save')}
          </Button>
        </div>
      </form>
    </PageWrapper>
  );
};

// ============================================================
// DÉTAIL PARTENAIRE
// ============================================================

const PartnerDetailPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();

  const partnerType = (searchParams.get('type') as 'CUSTOMER' | 'SUPPLIER') || 'CUSTOMER';
  const isCustomer = partnerType === 'CUSTOMER';

  const customerQuery = useCustomer(isCustomer ? (id || '') : '');
  const supplierQuery = useSupplier(!isCustomer ? (id || '') : '');
  const { data: partner, isLoading } = isCustomer ? customerQuery : supplierQuery;

  if (isLoading) {
    return (
      <PageWrapper title={t('common.loading')}>
        <div className="azals-loading">
          <RefreshCw className="animate-spin" size={24} />
        </div>
      </PageWrapper>
    );
  }

  if (!partner) {
    return (
      <PageWrapper title={t('partners.title')}>
        <Card>
          <div className="azals-empty">
            <AlertCircle size={48} />
            <p>{t('partners.noPartners')}</p>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={`${partner.code} - ${partner.name}`}
      actions={
        <ButtonGroup>
          <Button
            variant="ghost"
            leftIcon={<ArrowLeft size={16} />}
            onClick={() => navigate(`/documents/partners?type=${partnerType}`)}
          >
            {t('common.back')}
          </Button>
          <Button
            variant="ghost"
            leftIcon={<Edit size={16} />}
            onClick={() => navigate(`/documents/partners/${id}/edit?type=${partnerType}`)}
          >
            {t('common.edit')}
          </Button>
        </ButtonGroup>
      }
    >
      <Grid cols={2} gap="md">
        <Card>
          <h3 className="mb-4">{t('documents.form.generalInfo')}</h3>
          <dl className="azals-detail-list">
            <dt>{t('partners.fields.code')}</dt>
            <dd>{partner.code}</dd>
            <dt>{t('partners.fields.name')}</dt>
            <dd>{partner.name}</dd>
            <dt>{t('partners.fields.contact')}</dt>
            <dd>{partner.contact_name || '-'}</dd>
            <dt>{t('partners.fields.email')}</dt>
            <dd>{partner.email || '-'}</dd>
            <dt>{t('partners.fields.phone')}</dt>
            <dd>{partner.phone || '-'}</dd>
            <dt>{t('partners.fields.taxId')}</dt>
            <dd>{partner.tax_id || '-'}</dd>
            <dt>{t('common.status')}</dt>
            <dd><PartnerStatusBadge status={partner.status as PartnerStatus} /></dd>
          </dl>
        </Card>

        <Card>
          <h3 className="mb-4">{t('partners.fields.address')}</h3>
          <dl className="azals-detail-list">
            <dt>{t('partners.fields.address')}</dt>
            <dd>{partner.address || '-'}</dd>
            <dt>{t('partners.fields.postalCode')}</dt>
            <dd>{partner.postal_code || '-'}</dd>
            <dt>{t('partners.fields.city')}</dt>
            <dd>{partner.city || '-'}</dd>
            <dt>{t('partners.fields.country')}</dt>
            <dd>{partner.country || '-'}</dd>
          </dl>
        </Card>
      </Grid>

      {partner.notes && (
        <Card className="mt-4">
          <h3 className="mb-4">{t('partners.fields.notes')}</h3>
          <p className="text-muted">{partner.notes}</p>
        </Card>
      )}
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

export const DocumentsRoutes: React.FC = () => (
  <Routes>
    <Route index element={<DocumentsDashboard />} />
    <Route path="list" element={<DocumentListPage />} />
    <Route path="new" element={<DocumentFormPage />} />
    <Route path=":id" element={<DocumentDetailPage />} />
    <Route path=":id/edit" element={<DocumentFormPage />} />
    <Route path="partners" element={<PartnersListPage />} />
    <Route path="partners/new" element={<PartnerFormPage />} />
    <Route path="partners/:id" element={<PartnerDetailPage />} />
    <Route path="partners/:id/edit" element={<PartnerFormPage />} />
  </Routes>
);

export default DocumentsRoutes;
