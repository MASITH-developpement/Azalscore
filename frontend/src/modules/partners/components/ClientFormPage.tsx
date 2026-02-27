/**
 * AZALSCORE Module - Partners - ClientFormPage
 * Formulaire de création/édition client avec enrichissement
 * (CompanyAutocomplete, AddressAutocomplete, RiskAnalysis, InternalScore)
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Shield, ShieldCheck, ShieldAlert, ShieldX,
  AlertCircle, Loader2, TrendingUp, TrendingDown, History
} from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import {
  CompanyAutocomplete,
  AddressAutocomplete,
  useRiskAnalysis,
  useInternalScore,
  ScoreGauge
} from '@/modules/enrichment';
import type { EnrichedContactFields, AddressSuggestion } from '@/modules/enrichment';
import { useClient, useCreateClient, useUpdateClient } from '../hooks';
import type { ClientFormData } from '../types';

export const ClientFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isNew = !id || id === 'new';

  const { data: client, isLoading } = useClient(id || '');
  const createMutation = useCreateClient();
  const updateMutation = useUpdateClient();

  // Hook pour l'analyse de risque externe (SIRET)
  const {
    analysis: riskAnalysis,
    isLoading: riskLoading,
    error: riskError,
    analyze: analyzeRisk,
    reset: resetRisk
  } = useRiskAnalysis();

  // Hook pour le scoring interne (historique client)
  const {
    score: internalScore,
    isLoading: internalLoading,
    error: internalError,
    analyze: analyzeInternal,
    reset: resetInternal
  } = useInternalScore();

  const [form, setForm] = useState<ClientFormData>({
    code: '',
    name: '',
    type: 'CUSTOMER',
    email: '',
    phone: '',
    address_line1: '',
    city: '',
    postal_code: '',
    country_code: 'FR',
    tax_id: '',
    notes: '',
  });

  useEffect(() => {
    if (client) {
      setForm({
        code: client.code || '',
        name: client.name || '',
        type: client.client_type || 'CUSTOMER',
        email: client.email || '',
        phone: client.phone || '',
        address_line1: client.address_line1 || client.address || '',
        city: client.city || '',
        postal_code: client.postal_code || '',
        country_code: client.country_code || 'FR',
        tax_id: client.tax_id || '',
        notes: client.notes || '',
      });
    }
  }, [client]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isNew) {
        const result = await createMutation.mutateAsync(form);
        if (result?.id) navigate(`/partners/clients/${result.id}`);
      } else {
        await updateMutation.mutateAsync({ id: id!, data: form });
        navigate(`/partners/clients/${id}`);
      }
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
    }
  };

  // Handler pour l'enrichissement depuis recherche par nom
  const handleCompanySelect = (fields: EnrichedContactFields) => {
    setForm((prev) => ({
      ...prev,
      name: fields.name || fields.company_name || prev.name,
      address_line1: fields.address_line1 || fields.address || prev.address_line1,
      city: fields.city || prev.city,
      postal_code: fields.postal_code || prev.postal_code,
      tax_id: fields.siret || fields.siren || prev.tax_id,
    }));
  };

  // Handler pour l'autocomplete adresse
  const handleAddressSelect = (suggestion: AddressSuggestion) => {
    setForm((prev) => ({
      ...prev,
      address_line1: suggestion.address_line1 || suggestion.label.split(',')[0] || prev.address_line1,
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
      title={isNew ? 'Nouveau client' : `Modifier ${client?.name}`}
      actions={
        <Button variant="ghost" leftIcon={<ArrowLeft size={16} />} onClick={() => navigate(-1)}>
          Retour
        </Button>
      }
    >
      <form onSubmit={handleSubmit}>
        <Card title="Informations générales">
          <Grid cols={2} gap="md">
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="partner-code">Code (auto-généré)</label>
              <input
                id="partner-code"
                type="text"
                className="azals-input"
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value })}
                maxLength={50}
                placeholder="Généré automatiquement"
                disabled={!form.code}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="partner-type">Type</label>
              <select
                id="partner-type"
                className="azals-input"
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
              >
                <option value="PROSPECT">Prospect</option>
                <option value="LEAD">Lead</option>
                <option value="CUSTOMER">Client</option>
                <option value="VIP">VIP</option>
                <option value="PARTNER">Partenaire</option>
              </select>
            </div>
            <div className="azals-field" style={{ gridColumn: 'span 2' }}>
              <span className="azals-field__label">Nom / Raison sociale * (autocomplete entreprise)</span>
              <CompanyAutocomplete
                value={form.name}
                onChange={(value: string) => setForm({ ...form, name: value })}
                onSelect={handleCompanySelect}
                placeholder="Tapez le nom d'une entreprise..."
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="partner-email">Email</label>
              <input
                id="partner-email"
                type="email"
                className="azals-input"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="partner-phone">Téléphone</label>
              <input
                id="partner-phone"
                type="text"
                className="azals-input"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
          </Grid>
        </Card>

        <Card title="Adresse" className="mt-4">
          <Grid cols={2} gap="md">
            <div className="azals-field" style={{ gridColumn: 'span 2' }}>
              <span className="azals-field__label">Adresse (autocomplete)</span>
              <AddressAutocomplete
                value={form.address_line1}
                onChange={(value: string) => setForm({ ...form, address_line1: value })}
                onSelect={handleAddressSelect}
                placeholder="Tapez une adresse..."
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="partner-postal">Code postal</label>
              <input
                id="partner-postal"
                type="text"
                className="azals-input"
                value={form.postal_code}
                onChange={(e) => setForm({ ...form, postal_code: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="partner-city">Ville</label>
              <input
                id="partner-city"
                type="text"
                className="azals-input"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="partner-country">Pays</label>
              <input
                id="partner-country"
                type="text"
                className="azals-input"
                value={form.country_code}
                onChange={(e) => setForm({ ...form, country_code: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="partner-tax">N° SIRET / TVA</label>
              <input
                id="partner-tax"
                type="text"
                className="azals-input"
                value={form.tax_id}
                onChange={(e) => setForm({ ...form, tax_id: e.target.value })}
              />
            </div>
          </Grid>
        </Card>

        <Card title="Notes" className="mt-4">
          <textarea
            className="azals-input w-full"
            rows={4}
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            placeholder="Notes sur ce client..."
          />
        </Card>

        {/* Analyse de Risque - Section combinée */}
        <Card title="Analyse de Risque" className="mt-4" icon={<Shield size={18} />}>
          <Grid cols={2} gap="md">
            {/* Colonne 1: Risque Externe (SIRET) */}
            <div className="border-r pr-4">
              <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                <Shield size={16} />
                Risque Entreprise
                <span className="text-xs text-gray-400">(données publiques)</span>
              </h4>

              {!form.tax_id || form.tax_id.length < 9 ? (
                <div className="flex items-center gap-2 text-gray-400 text-sm py-2">
                  <AlertCircle size={16} />
                  <span>SIRET requis</span>
                </div>
              ) : riskLoading ? (
                <div className="flex items-center gap-2 text-blue-600 py-2">
                  <Loader2 size={16} className="animate-spin" />
                  <span className="text-sm">Analyse...</span>
                </div>
              ) : riskAnalysis ? (
                <div>
                  <div className="flex items-center gap-4 mb-3">
                    <ScoreGauge score={riskAnalysis.score} size="sm" />
                    <div>
                      <div className="flex items-center gap-1">
                        {riskAnalysis.level === 'low' && <ShieldCheck className="text-green-500" size={16} />}
                        {riskAnalysis.level === 'medium' && <Shield className="text-yellow-500" size={16} />}
                        {riskAnalysis.level === 'elevated' && <ShieldAlert className="text-orange-500" size={16} />}
                        {riskAnalysis.level === 'high' && <ShieldX className="text-red-500" size={16} />}
                        <span className="font-medium">{riskAnalysis.level_label}</span>
                      </div>
                      {riskAnalysis.cotation_bdf && (
                        <div className="text-xs text-gray-500">BDF: {riskAnalysis.cotation_bdf}</div>
                      )}
                    </div>
                  </div>

                  {riskAnalysis.alerts && riskAnalysis.alerts.length > 0 && (
                    <div className="text-xs text-red-600 mb-2">
                      {riskAnalysis.alerts.slice(0, 2).map((a, i) => (
                        <div key={i} className="flex items-center gap-1">
                          <AlertCircle size={12} />
                          {a}
                        </div>
                      ))}
                    </div>
                  )}

                  <Button variant="ghost" size="sm" onClick={() => { resetRisk(); analyzeRisk(form.tax_id); }}>
                    Actualiser
                  </Button>
                </div>
              ) : riskError ? (
                <div className="text-sm text-red-500">
                  {riskError}
                  <Button variant="ghost" size="sm" onClick={() => analyzeRisk(form.tax_id)}>Réessayer</Button>
                </div>
              ) : (
                <Button variant="secondary" size="sm" leftIcon={<Shield size={14} />} onClick={() => analyzeRisk(form.tax_id)}>
                  Analyser
                </Button>
              )}
            </div>

            {/* Colonne 2: Scoring Interne (Historique) */}
            <div className="pl-4">
              <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                <History size={16} />
                Score Interne
                <span className="text-xs text-gray-400">(historique client)</span>
              </h4>

              {isNew ? (
                <div className="flex items-center gap-2 text-gray-400 text-sm py-2">
                  <AlertCircle size={16} />
                  <span>Nouveau client - pas d'historique</span>
                </div>
              ) : internalLoading ? (
                <div className="flex items-center gap-2 text-blue-600 py-2">
                  <Loader2 size={16} className="animate-spin" />
                  <span className="text-sm">Calcul...</span>
                </div>
              ) : internalScore ? (
                <div>
                  <div className="flex items-center gap-4 mb-3">
                    <ScoreGauge score={internalScore.score} size="sm" />
                    <div>
                      <div className="flex items-center gap-1">
                        {internalScore.level === 'low' && <TrendingUp className="text-green-500" size={16} />}
                        {internalScore.level === 'medium' && <History className="text-yellow-500" size={16} />}
                        {internalScore.level === 'elevated' && <TrendingDown className="text-orange-500" size={16} />}
                        {internalScore.level === 'high' && <TrendingDown className="text-red-500" size={16} />}
                        <span className="font-medium">{internalScore.level_label}</span>
                      </div>
                      {internalScore.metrics && (
                        <div className="text-xs text-gray-500">
                          {internalScore.metrics.total_invoices} factures | {internalScore.metrics.overdue_invoices} en retard
                        </div>
                      )}
                    </div>
                  </div>

                  {internalScore.alerts && internalScore.alerts.length > 0 && (
                    <div className="text-xs text-red-600 mb-2">
                      {internalScore.alerts.slice(0, 2).map((a, i) => (
                        <div key={i} className="flex items-center gap-1">
                          <AlertCircle size={12} />
                          {a}
                        </div>
                      ))}
                    </div>
                  )}

                  {internalScore.recommendation && (
                    <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded mb-2">
                      {internalScore.recommendation}
                    </div>
                  )}

                  <Button variant="ghost" size="sm" onClick={() => { resetInternal(); analyzeInternal(id!); }}>
                    Actualiser
                  </Button>
                </div>
              ) : internalError ? (
                <div className="text-sm text-red-500">
                  {internalError}
                  <Button variant="ghost" size="sm" onClick={() => analyzeInternal(id!)}>Réessayer</Button>
                </div>
              ) : (
                <Button variant="secondary" size="sm" leftIcon={<History size={14} />} onClick={() => analyzeInternal(id!)}>
                  Calculer le score
                </Button>
              )}
            </div>
          </Grid>
        </Card>

        <div className="flex justify-end gap-3 mt-6">
          <Button variant="ghost" onClick={() => navigate(-1)} disabled={isSubmitting}>
            Annuler
          </Button>
          <Button type="submit" disabled={isSubmitting || !form.name}>
            {isSubmitting ? 'Enregistrement...' : isNew ? 'Créer le client' : 'Enregistrer'}
          </Button>
        </div>
      </form>
    </PageWrapper>
  );
};

export default ClientFormPage;
