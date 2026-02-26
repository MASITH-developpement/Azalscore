/**
 * AZALSCORE Module - Purchases - Invoice Form
 * ============================================
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save, AlertTriangle, Building2 } from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { SmartSelector, type FieldConfig } from '@/components/SmartSelector';
import { usePurchaseInvoice, useSuppliersLookup, useCreatePurchaseInvoice, useUpdatePurchaseInvoice } from '../../hooks';
import { LineEditor, type LineFormData } from '../../components';
import type { Supplier, PurchaseOrderLine } from '../../types';

// ============================================================================
// Constants
// ============================================================================

const SUPPLIER_CREATE_FIELDS: FieldConfig[] = [
  { key: 'code', label: 'Code (auto)', type: 'text', required: false },
  { key: 'name', label: 'Nom', type: 'text', required: true },
  { key: 'contact_name', label: 'Contact', type: 'text' },
  { key: 'email', label: 'Email', type: 'email' },
  { key: 'phone', label: 'Telephone', type: 'tel' },
];

// ============================================================================
// Component
// ============================================================================

export const InvoiceFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isNew = !id;

  const { data: invoice, isLoading } = usePurchaseInvoice(id || '');
  const { data: suppliers } = useSuppliersLookup();
  const createMutation = useCreatePurchaseInvoice();
  const updateMutation = useUpdatePurchaseInvoice();

  const [supplierId, setSupplierId] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [dueDate, setDueDate] = useState('');
  const [supplierReference, setSupplierReference] = useState('');
  const [notes, setNotes] = useState('');
  const [lines, setLines] = useState<LineFormData[]>([]);

  useEffect(() => {
    if (invoice) {
      setSupplierId(invoice.supplier_id);
      setDate(invoice.date.split('T')[0]);
      setDueDate(invoice.due_date?.split('T')[0] || '');
      setSupplierReference(invoice.supplier_reference || '');
      setNotes(invoice.notes || '');
      setLines(invoice.lines.map((l: PurchaseOrderLine) => ({
        id: l.id,
        description: l.description,
        quantity: l.quantity,
        unit_price: l.unit_price,
        tax_rate: l.tax_rate,
        discount_percent: l.discount_percent,
      })));
    }
  }, [invoice]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!supplierId) {
      alert('Veuillez selectionner un fournisseur');
      return;
    }
    if (lines.length === 0) {
      alert('Veuillez ajouter au moins une ligne');
      return;
    }

    const data = {
      supplier_id: supplierId,
      date,
      due_date: dueDate || undefined,
      supplier_reference: supplierReference || undefined,
      notes: notes || undefined,
      lines: lines.map((l) => ({
        description: l.description,
        quantity: l.quantity,
        unit_price: l.unit_price,
        tax_rate: l.tax_rate,
        discount_percent: l.discount_percent,
      })),
    };

    if (isNew) {
      const result = await createMutation.mutateAsync(data);
      navigate(`/purchases/invoices/${result.id}`);
    } else {
      await updateMutation.mutateAsync({ id: id!, data });
      navigate(`/purchases/invoices/${id}`);
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;
  const canEdit = isNew || invoice?.status === 'DRAFT';

  if (!isNew && isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  if (!isNew && invoice && invoice.status !== 'DRAFT') {
    return (
      <PageWrapper title="Modification impossible">
        <Card>
          <AlertTriangle size={48} className="azals-text--warning" />
          <p>Cette facture ne peut plus etre modifiee car elle a ete validee.</p>
          <Button onClick={() => navigate(`/purchases/invoices/${id}`)}>Voir la facture</Button>
        </Card>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={isNew ? 'Nouvelle facture' : `Modifier ${invoice?.number}`}
      actions={
        <Button variant="ghost" leftIcon={<ArrowLeft size={16} />} onClick={() => navigate(-1)}>
          Retour
        </Button>
      }
    >
      <form onSubmit={handleSubmit}>
        <Card title="Informations generales">
          <Grid cols={3} gap="md">
            <div className="azals-field">
              <SmartSelector
                items={(suppliers || []).map((s: Supplier) => ({ ...s, id: s.id, name: s.name }))}
                value={supplierId}
                onChange={(value) => setSupplierId(value)}
                label="Fournisseur *"
                placeholder="Selectionner un fournisseur..."
                displayField="name"
                secondaryField="code"
                entityName="fournisseur"
                entityIcon={<Building2 size={16} />}
                createEndpoint="/purchases/suppliers"
                createFields={SUPPLIER_CREATE_FIELDS}
                queryKeys={['purchases', 'suppliers']}
                disabled={!canEdit}
                allowCreate={canEdit}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Date *</label>
              <input
                type="date"
                className="azals-input"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
                disabled={!canEdit}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Date d'echeance</label>
              <input
                type="date"
                className="azals-input"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                disabled={!canEdit}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Ref. fournisseur</label>
              <input
                type="text"
                className="azals-input"
                value={supplierReference}
                onChange={(e) => setSupplierReference(e.target.value)}
                placeholder="N facture fournisseur"
                disabled={!canEdit}
              />
            </div>
          </Grid>
        </Card>

        <Card title="Lignes de facture">
          <LineEditor
            lines={lines}
            onChange={setLines}
            readOnly={!canEdit}
          />
        </Card>

        <Card title="Notes">
          <div className="azals-field">
            <textarea
              className="azals-textarea"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Notes internes sur cette facture..."
              disabled={!canEdit}
            />
          </div>
        </Card>

        {canEdit && (
          <div className="azals-form__actions">
            <Button variant="secondary" onClick={() => navigate(-1)}>
              Annuler
            </Button>
            <Button
              type="submit"
              leftIcon={<Save size={16} />}
              isLoading={isSubmitting}
            >
              {isNew ? 'Creer la facture' : 'Enregistrer'}
            </Button>
          </div>
        )}
      </form>
    </PageWrapper>
  );
};

export default InvoiceFormPage;
