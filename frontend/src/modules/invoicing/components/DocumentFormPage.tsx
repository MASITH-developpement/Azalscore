/**
 * AZALSCORE Module - Invoicing - DocumentFormPage
 * Formulaire de creation/edition de document
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Check, AlertCircle, UserPlus } from 'lucide-react';
import { Button } from '@ui/actions';
import { LoadingState } from '@ui/components/StateViews';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { SmartSelector, FieldConfig } from '@/components/SmartSelector';
import type { DocumentType, LineFormData } from '../types';
import { DOCUMENT_TYPE_CONFIG } from '../types';
import { useDocument, useCustomers, useCreateDocument, useUpdateDocument } from '../hooks';
import LinesEditor from './LinesEditor';

const CUSTOMER_CREATE_FIELDS: FieldConfig[] = [
  { key: 'name', label: 'Nom', type: 'text', required: true },
  { key: 'email', label: 'Email', type: 'email' },
  { key: 'phone', label: 'Telephone', type: 'tel' },
];

interface DocumentFormPageProps {
  type: DocumentType;
}

const DocumentFormPage: React.FC<DocumentFormPageProps> = ({ type }) => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id && id !== 'new';

  const { data: document, isLoading: loadingDocument } = useDocument(id || '');
  const { data: customers, isLoading: loadingCustomers } = useCustomers();
  const createDocument = useCreateDocument();
  const updateDocument = useUpdateDocument();

  const typeConfig = DOCUMENT_TYPE_CONFIG[type] || { label: type, labelPlural: type, prefix: 'DOC', color: 'gray' };

  // Form state
  const [customerId, setCustomerId] = useState('');
  const [docDate, setDocDate] = useState(new Date().toISOString().split('T')[0]);
  const [dueDate, setDueDate] = useState('');
  const [validityDate, setValidityDate] = useState('');
  const [notes, setNotes] = useState('');
  const [lines, setLines] = useState<LineFormData[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Load existing document data
  useEffect(() => {
    if (document) {
      setCustomerId(document.customer_id);
      setDocDate(document.date);
      setDueDate(document.due_date || '');
      setValidityDate(document.validity_date || '');
      setNotes(document.notes || '');
      setLines(document.lines.map((l) => ({
        id: l.id,
        description: l.description,
        quantity: l.quantity,
        unit: l.unit,
        unit_price: l.unit_price,
        discount_percent: l.discount_percent,
        tax_rate: l.tax_rate,
      })));
    }
  }, [document]);

  // Redirect if document is validated (not editable)
  useEffect(() => {
    if (isEdit && document && document.status !== 'DRAFT') {
      navigate(`/invoicing/${type.toLowerCase()}s/${id}`);
    }
  }, [document, isEdit, type, id, navigate]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!customerId) {
      newErrors.customer = 'Veuillez selectionner un client';
    }
    if (!docDate) {
      newErrors.date = 'La date est requise';
    }
    if (lines.length === 0) {
      newErrors.lines = 'Ajoutez au moins une ligne';
    }
    if (lines.some((l) => !l.description.trim())) {
      newErrors.lines = 'Toutes les lignes doivent avoir une description';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    try {
      if (isEdit) {
        await updateDocument.mutateAsync({
          id: id!,
          data: {
            date: docDate,
            due_date: dueDate || undefined,
            validity_date: validityDate || undefined,
            notes: notes || undefined,
            lines,
          },
        });
      } else {
        await createDocument.mutateAsync({
          type,
          customer_id: customerId,
          date: docDate,
          due_date: dueDate || undefined,
          validity_date: validityDate || undefined,
          notes: notes || undefined,
          lines: lines.map(({ id: _, ...line }) => line),
        });
      }
      navigate(`/invoicing/${type.toLowerCase()}s`);
    } catch (err) {
      console.error('Save failed:', err);
    }
  };

  if ((isEdit && loadingDocument) || loadingCustomers) {
    return (
      <PageWrapper title={`${isEdit ? 'Modifier' : 'Nouveau'} ${typeConfig.label}`}>
        <LoadingState message="Chargement du formulaire..." />
      </PageWrapper>
    );
  }

  const isSubmitting = createDocument.isPending || updateDocument.isPending;

  return (
    <PageWrapper
      title={`${isEdit ? 'Modifier' : 'Nouveau'} ${typeConfig.label}`}
      actions={
        <Button variant="ghost" onClick={() => navigate(`/invoicing/${type.toLowerCase()}s`)}>
          Annuler
        </Button>
      }
    >
      <form onSubmit={handleSubmit}>
        <Card className="mb-4">
          <h3 className="mb-4">Informations generales</h3>

          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <SmartSelector
                items={(customers || []).map(c => ({ ...c, id: c.id, name: c.name }))}
                value={customerId}
                onChange={(value) => setCustomerId(value)}
                label="Client *"
                placeholder="Selectionner un client..."
                displayField="name"
                secondaryField="code"
                entityName="client"
                entityIcon={<UserPlus size={16} />}
                createEndpoint="/partners/clients"
                createFields={CUSTOMER_CREATE_FIELDS}
                createUrl="/partners/clients/new"
                queryKeys={['customers', 'clients']}
                disabled={isEdit}
                error={errors.customer}
                allowCreate={!isEdit}
              />
            </div>

            <div className="azals-form-field">
              <label htmlFor="date">Date *</label>
              <input
                type="date"
                id="date"
                value={docDate}
                onChange={(e) => setDocDate(e.target.value)}
                className={`azals-input ${errors.date ? 'azals-input--error' : ''}`}
              />
              {errors.date && <span className="azals-form-error">{errors.date}</span>}
            </div>

            {type === 'QUOTE' && (
              <div className="azals-form-field">
                <label htmlFor="validity">Date de validite</label>
                <input
                  type="date"
                  id="validity"
                  value={validityDate}
                  onChange={(e) => setValidityDate(e.target.value)}
                  className="azals-input"
                />
              </div>
            )}

            {type === 'INVOICE' && (
              <div className="azals-form-field">
                <label htmlFor="due">Date d&apos;echeance</label>
                <input
                  type="date"
                  id="due"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="azals-input"
                />
              </div>
            )}
          </Grid>

          <div className="azals-form-field mt-4">
            <label htmlFor="notes">Notes</label>
            <textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="azals-textarea"
              rows={3}
              placeholder="Notes visibles sur le document..."
            />
          </div>
        </Card>

        <Card className="mb-4">
          {errors.lines && (
            <div className="azals-alert azals-alert--error mb-4">
              <AlertCircle size={16} />
              <span>{errors.lines}</span>
            </div>
          )}
          <LinesEditor
            lines={lines}
            onChange={setLines}
          />
        </Card>

        <div className="azals-form-actions">
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate(`/invoicing/${type.toLowerCase()}s`)}
          >
            Annuler
          </Button>
          <Button
            type="submit"
            isLoading={isSubmitting}
            leftIcon={<Check size={16} />}
          >
            {isEdit ? 'Enregistrer' : `Creer le ${typeConfig.label.toLowerCase()}`}
          </Button>
        </div>
      </form>
    </PageWrapper>
  );
};

export default DocumentFormPage;
