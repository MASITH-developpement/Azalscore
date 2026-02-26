/**
 * AZALSCORE Module - Purchases - Supplier Form
 * =============================================
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save, Trash2 } from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { SiretLookup, AddressAutocomplete, CompanyAutocomplete } from '@/modules/enrichment';
import type { EnrichedContactFields, AddressSuggestion, RiskData } from '@/modules/enrichment';
import { useSupplier, useCreateSupplier, useUpdateSupplier, useDeleteSupplier } from '../../hooks';
import { PAYMENT_TERMS_OPTIONS, type SupplierCreate } from '../../types';

// ============================================================================
// Component
// ============================================================================

export const SupplierFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isNew = !id;

  const { data: supplier, isLoading } = useSupplier(id || '');
  const createMutation = useCreateSupplier();
  const updateMutation = useUpdateSupplier();
  const deleteMutation = useDeleteSupplier();

  const handleDelete = async () => {
    if (!supplier) return;

    if (window.confirm(`Supprimer le fournisseur "${supplier.name}" ?\n\nCette action est irreversible.`)) {
      try {
        await deleteMutation.mutateAsync(supplier.id);
        navigate('/purchases/suppliers');
      } catch (error) {
        console.error('[SUPPLIER_DELETE] Echec:', error);
      }
    }
  };

  const [form, setForm] = useState<SupplierCreate>({
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

  const [riskData, setRiskData] = useState<RiskData | null>(null);

  useEffect(() => {
    if (supplier) {
      setForm({
        name: supplier.name,
        contact_name: supplier.contact_name || '',
        email: supplier.email || '',
        phone: supplier.phone || '',
        address: supplier.address || '',
        city: supplier.city || '',
        postal_code: supplier.postal_code || '',
        country: supplier.country || 'France',
        tax_id: supplier.tax_id || '',
        payment_terms: supplier.payment_terms || 'NET30',
        notes: supplier.notes || '',
      });
    }
  }, [supplier]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isNew) {
      const result = await createMutation.mutateAsync(form);
      if (result?.id) navigate(`/purchases/suppliers/${result.id}`);
    } else {
      await updateMutation.mutateAsync({ id: id!, data: form });
      navigate(`/purchases/suppliers/${id}`);
    }
  };

  const handleCompanySelect = (fields: EnrichedContactFields) => {
    setForm((prev) => ({
      ...prev,
      name: fields.name || fields.company_name || prev.name,
      address: fields.address_line1 || fields.address || prev.address,
      city: fields.city || prev.city,
      postal_code: fields.postal_code || prev.postal_code,
      tax_id: fields.siret || fields.siren || prev.tax_id,
    }));

    if (fields._bodacc_risk_level || fields._risk_level) {
      setRiskData({
        level: fields._bodacc_risk_level || fields._risk_level,
        label: fields._bodacc_risk_label || fields._risk_label,
        reason: fields._bodacc_risk_reason || fields._risk_reason,
        score: fields._bodacc_risk_score ?? fields._risk_score,
        alerts: fields._bodacc_critical_alerts || [],
      });
    } else {
      setRiskData(null);
    }
  };

  const handleSiretEnrich = handleCompanySelect;

  const handleAddressSelect = (suggestion: AddressSuggestion) => {
    setForm((prev) => ({
      ...prev,
      address: suggestion.address_line1 || suggestion.label.split(',')[0] || prev.address,
      postal_code: suggestion.postal_code || prev.postal_code,
      city: suggestion.city || prev.city,
    }));
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  if (!isNew && isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={isNew ? 'Nouveau fournisseur' : `Modifier ${supplier?.name}`}
      actions={
        <Button variant="ghost" leftIcon={<ArrowLeft size={16} />} onClick={() => navigate(-1)}>
          Retour
        </Button>
      }
    >
      <form onSubmit={handleSubmit}>
        <Card title="Informations generales">
          <Grid cols={2} gap="md">
            <div className="azals-field">
              <label className="azals-field__label">Nom * (autocomplete entreprise)</label>
              <CompanyAutocomplete
                value={form.name}
                onChange={(value: string) => setForm({ ...form, name: value })}
                onSelect={handleCompanySelect}
                onRiskData={setRiskData}
                placeholder="Tapez le nom d'une entreprise..."
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Contact</label>
              <input
                type="text"
                className="azals-input"
                value={form.contact_name}
                onChange={(e) => setForm({ ...form, contact_name: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Email</label>
              <input
                type="email"
                className="azals-input"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Telephone</label>
              <input
                type="text"
                className="azals-input"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">N TVA / SIRET - Remplissage auto INSEE</label>
              <SiretLookup
                value={form.tax_id}
                onEnrich={handleSiretEnrich}
                onRiskData={setRiskData}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Conditions de paiement</label>
              <select
                className="azals-select"
                value={form.payment_terms}
                onChange={(e) => setForm({ ...form, payment_terms: e.target.value })}
              >
                {PAYMENT_TERMS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </Grid>
        </Card>

        <Card title="Adresse">
          <Grid cols={2} gap="md">
            <div className="azals-field" style={{ gridColumn: 'span 2' }}>
              <label className="azals-field__label">Adresse - Autocomplete France</label>
              <AddressAutocomplete
                value={form.address}
                onChange={(value) => setForm({ ...form, address: value })}
                onSelect={handleAddressSelect}
                placeholder="Rechercher une adresse..."
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Code postal</label>
              <input
                type="text"
                className="azals-input"
                value={form.postal_code}
                onChange={(e) => setForm({ ...form, postal_code: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Ville</label>
              <input
                type="text"
                className="azals-input"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Pays</label>
              <input
                type="text"
                className="azals-input"
                value={form.country}
                onChange={(e) => setForm({ ...form, country: e.target.value })}
              />
            </div>
          </Grid>
        </Card>

        <Card title="Notes">
          <div className="azals-field">
            <textarea
              className="azals-textarea"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              rows={4}
              placeholder="Notes internes sur ce fournisseur..."
            />
          </div>
        </Card>

        {riskData && (
          <Card
            title="Analyse de risque"
            className={riskData.level === 'critical' ? 'azals-card--danger' : riskData.level === 'high' ? 'azals-card--warning' : ''}
          >
            <div style={{
              padding: '1rem',
              borderRadius: '0.5rem',
              background: riskData.level === 'critical' ? 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)' :
                         riskData.level === 'high' ? 'linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)' : '#f0fdf4',
              border: riskData.level === 'critical' ? '2px solid #ef4444' :
                     riskData.level === 'high' ? '2px solid #f59e0b' : '2px solid #22c55e'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '1.5rem' }}>
                  {riskData.level === 'critical' ? '⛔' : riskData.level === 'high' ? '⚠️' : '✅'}
                </span>
                <div>
                  <div style={{
                    fontWeight: 700,
                    color: riskData.level === 'critical' ? '#dc2626' : riskData.level === 'high' ? '#d97706' : '#16a34a'
                  }}>
                    {riskData.level === 'critical' ? 'RISQUE CRITIQUE' :
                     riskData.level === 'high' ? 'RISQUE ELEVE' : 'RISQUE FAIBLE'}
                  </div>
                  <div style={{ fontWeight: 500, color: '#374151' }}>
                    {riskData.reason || riskData.label}
                  </div>
                </div>
              </div>
              {riskData.alerts && riskData.alerts.length > 0 && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#6b7280' }}>
                  {riskData.alerts.map((alert, idx) => (
                    <div key={idx}>• {alert.type} ({alert.date})</div>
                  ))}
                </div>
              )}
              <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: '#9ca3af' }}>
                Sources: {riskData.sources && riskData.sources.length > 0
                  ? riskData.sources.join(', ')
                  : 'INSEE, BODACC'}
              </div>
            </div>
          </Card>
        )}

        <div className="azals-form__actions" style={{ display: 'flex', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Button variant="secondary" onClick={() => navigate(-1)}>
              Annuler
            </Button>
            <Button
              type="submit"
              leftIcon={<Save size={16} />}
              isLoading={isSubmitting}
            >
              {isNew ? 'Creer le fournisseur' : 'Enregistrer'}
            </Button>
          </div>
          {!isNew && (
            <Button
              type="button"
              variant="danger"
              leftIcon={<Trash2 size={16} />}
              onClick={handleDelete}
              isLoading={deleteMutation.isPending}
            >
              Supprimer
            </Button>
          )}
        </div>
      </form>
    </PageWrapper>
  );
};

export default SupplierFormPage;
