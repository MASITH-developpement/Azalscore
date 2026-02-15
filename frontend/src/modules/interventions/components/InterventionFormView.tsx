/**
 * AZALSCORE - Formulaire Intervention (Field Service)
 * Formulaire de création/édition : Client + Intervention + Description
 */

import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { unwrapApiResponse } from '@/types';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import { Select, Input, TextArea } from '@ui/forms';
import { SmartSelector } from '@/components/SmartSelector';
import type { FieldConfig } from '@/components/SmartSelector';
import {
  Building2, Wrench, FileText, MapPin,
  ChevronLeft, Users
} from 'lucide-react';

import type { Intervention, InterventionFormData, DonneurOrdre } from '../types';

// ============================================================================
// CONSTANTES
// ============================================================================

const TYPES_INTERVENTION = [
  { value: '', label: 'Sélectionner...' },
  { value: 'INSTALLATION', label: 'Installation' },
  { value: 'MAINTENANCE', label: 'Maintenance' },
  { value: 'REPARATION', label: 'Réparation' },
  { value: 'INSPECTION', label: 'Inspection' },
  { value: 'FORMATION', label: 'Formation' },
  { value: 'CONSULTATION', label: 'Consultation' },
  { value: 'AUTRE', label: 'Autre' }
];

const PRIORITES = [
  { value: 'LOW', label: 'Basse' },
  { value: 'NORMAL', label: 'Normale' },
  { value: 'HIGH', label: 'Haute' },
  { value: 'URGENT', label: 'Urgente' }
];

const CORPS_ETAT_OPTIONS = [
  { value: '', label: 'Sélectionner...' },
  { value: 'ELECTRICITE', label: 'Électricité' },
  { value: 'PLOMBERIE', label: 'Plomberie' },
  { value: 'ELECTRICITE_PLOMBERIE', label: 'Électricité + Plomberie' }
];

const FACTURATION_OPTIONS = [
  { value: 'donneur_ordre', label: "Donneur d'ordre" },
  { value: 'client_final', label: 'Client final' }
];

// SmartSelector field configs
const CLIENT_CREATE_FIELDS: FieldConfig[] = [
  { key: 'code', label: 'Code client', type: 'text', required: true },
  { key: 'name', label: 'Nom / Raison sociale', type: 'text', required: true },
  { key: 'email', label: 'Email', type: 'email' },
  { key: 'phone', label: 'Téléphone', type: 'tel' },
  { key: 'address_line1', label: 'Adresse', type: 'text' },
  { key: 'city', label: 'Ville', type: 'text' },
  { key: 'postal_code', label: 'Code postal', type: 'text' },
];

const DONNEUR_ORDRE_CREATE_FIELDS: FieldConfig[] = [
  { key: 'nom', label: 'Nom', type: 'text', required: true },
  { key: 'code', label: 'Code', type: 'text', required: true },
  { key: 'email', label: 'Email', type: 'email' },
  { key: 'telephone', label: 'Téléphone', type: 'tel' },
];

// ============================================================================
// HOOKS API
// ============================================================================

const useClients = () => {
  return useQuery({
    queryKey: ['clients'],
    queryFn: async () => {
      const response = await api.get<{ items: { id: string; name: string; code?: string }[] }>('/commercial/customers');
      const data = unwrapApiResponse<{ items: { id: string; name: string; code?: string }[] }>(response);
      return data?.items || [];
    }
  });
};

const useDonneursOrdre = () => {
  return useQuery({
    queryKey: ['interventions', 'donneurs-ordre'],
    queryFn: async () => {
      const response = await api.get<DonneurOrdre[]>('/interventions/donneurs-ordre');
      return unwrapApiResponse<DonneurOrdre[]>(response);
    }
  });
};

const useIntervenants = () => {
  return useQuery({
    queryKey: ['intervenants'],
    queryFn: async () => {
      const response = await api.get<{ items: { id: string; first_name: string; last_name: string }[] }>('/hr/employees');
      const data = unwrapApiResponse<{ items: { id: string; first_name: string; last_name: string }[] }>(response);
      return data?.items || [];
    }
  });
};

const useIntervention = (id?: string) => {
  return useQuery({
    queryKey: ['interventions', 'detail', id],
    queryFn: async () => {
      const response = await api.get<Intervention>(`/interventions/${id}`);
      return response as unknown as Intervention;
    },
    enabled: !!id
  });
};

// ============================================================================
// COMPOSANT SECTION
// ============================================================================

const FormSection: React.FC<{
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  collapsible?: boolean;
}> = ({ title, icon, children }) => (
  <Card>
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
      <span style={{ color: 'var(--azals-primary, #1E6EFF)' }}>{icon}</span>
      <h3 style={{ fontSize: '16px', fontWeight: 600, margin: 0 }}>{title}</h3>
    </div>
    {children}
  </Card>
);

// ============================================================================
// COMPOSANT PRINCIPAL
// ============================================================================

interface InterventionFormViewProps {
  interventionId?: string;
  onBack: () => void;
  onSaved?: (id: string) => void;
}

export const InterventionFormView: React.FC<InterventionFormViewProps> = ({
  interventionId,
  onBack,
  onSaved
}) => {
  const isEdit = !!interventionId;
  const queryClient = useQueryClient();

  // Data fetching
  const { data: clients = [] } = useClients();
  const { data: donneursOrdre = [] } = useDonneursOrdre();
  const { data: intervenants = [] } = useIntervenants();
  const { data: existingIntervention } = useIntervention(interventionId);

  // Form state
  const [formData, setFormData] = useState<InterventionFormData>({
    client_id: '',
    donneur_ordre_id: '',
    reference_externe: '',
    facturer_a: 'client_final',
    adresse_ligne1: '',
    adresse_ligne2: '',
    code_postal: '',
    ville: '',
    type_intervention: 'AUTRE',
    priorite: 'NORMAL',
    corps_etat: undefined,
    titre: '',
    date_prevue_debut: '',
    duree_prevue_heures: undefined,
    intervenant_id: '',
    description: ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Populate form in edit mode
  useEffect(() => {
    if (existingIntervention && isEdit) {
      const dateDebut = existingIntervention.date_prevue_debut
        ? existingIntervention.date_prevue_debut.slice(0, 16)
        : '';

      let dureeHeures: number | undefined;
      if (existingIntervention.duree_prevue_minutes) {
        dureeHeures = existingIntervention.duree_prevue_minutes / 60;
      }

      setFormData({
        client_id: existingIntervention.client_id || '',
        donneur_ordre_id: existingIntervention.donneur_ordre_id || '',
        reference_externe: '',
        facturer_a: existingIntervention.donneur_ordre_id ? 'donneur_ordre' : 'client_final',
        adresse_ligne1: existingIntervention.adresse_ligne1 || '',
        adresse_ligne2: existingIntervention.adresse_ligne2 || '',
        code_postal: existingIntervention.code_postal || '',
        ville: existingIntervention.ville || '',
        type_intervention: existingIntervention.type_intervention || 'AUTRE',
        priorite: existingIntervention.priorite || 'NORMAL',
        corps_etat: existingIntervention.corps_etat || undefined,
        titre: existingIntervention.titre || '',
        date_prevue_debut: dateDebut,
        duree_prevue_heures: dureeHeures,
        intervenant_id: existingIntervention.intervenant_id || '',
        description: existingIntervention.description || ''
      });
    }
  }, [existingIntervention, isEdit]);

  // Update field helper
  const updateField = (field: keyof InterventionFormData, value: string | number | undefined) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  // Validation
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!formData.client_id) {
      newErrors.client_id = 'Le client est obligatoire';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);

    // Compute date_prevue_fin from debut + duration
    let date_prevue_fin: string | undefined;
    if (formData.date_prevue_debut && formData.duree_prevue_heures) {
      const debut = new Date(formData.date_prevue_debut);
      const fin = new Date(debut.getTime() + formData.duree_prevue_heures * 60 * 60 * 1000);
      date_prevue_fin = fin.toISOString();
    }

    const apiData = {
      client_id: formData.client_id,
      donneur_ordre_id: formData.donneur_ordre_id || undefined,
      reference_externe: formData.reference_externe || undefined,
      type_intervention: formData.type_intervention || 'AUTRE',
      priorite: formData.priorite || 'NORMAL',
      corps_etat: formData.corps_etat || undefined,
      titre: formData.titre || undefined,
      description: formData.description || undefined,
      adresse_ligne1: formData.adresse_ligne1 || undefined,
      adresse_ligne2: formData.adresse_ligne2 || undefined,
      code_postal: formData.code_postal || undefined,
      ville: formData.ville || undefined,
      date_prevue_debut: formData.date_prevue_debut ? new Date(formData.date_prevue_debut).toISOString() : undefined,
      date_prevue_fin: date_prevue_fin,
      intervenant_id: formData.intervenant_id || undefined,
    };

    try {
      let result: any;
      if (isEdit && interventionId) {
        result = await api.put(`/interventions/${interventionId}`, apiData);
      } else {
        result = await api.post('/interventions', apiData);
      }

      queryClient.invalidateQueries({ queryKey: ['interventions'] });

      if (onSaved) {
        onSaved(result?.id || interventionId || '');
      } else {
        onBack();
      }
    } catch (err) {
      console.error('Erreur sauvegarde intervention:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Date/Time helpers
  const now = new Date();
  const defaultDate = now.toISOString().slice(0, 16);

  return (
    <PageWrapper
      title={isEdit ? `Modifier ${existingIntervention?.reference || 'intervention'}` : 'Nouvelle intervention'}
      subtitle={isEdit ? existingIntervention?.titre : 'Intervention terrain'}
    >
      {/* Back button */}
      <div style={{ marginBottom: '16px' }}>
        <Button variant="ghost" onClick={onBack}>
          <ChevronLeft size={16} />
          Retour aux interventions
        </Button>
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* ============================================================ */}
          {/* SECTION 1 : INFORMATIONS CLIENT                              */}
          {/* ============================================================ */}
          <FormSection title="Informations Client" icon={<Building2 size={20} />}>
            <Grid cols={2} gap="md">
              <div className="azals-field">
                <SmartSelector
                  items={(donneursOrdre || []).map((d: DonneurOrdre) => ({ id: d.id, name: d.nom, email: d.email }))}
                  value={formData.donneur_ordre_id || ''}
                  onChange={(value) => updateField('donneur_ordre_id', value)}
                  label="Donneur d'ordre"
                  placeholder="Sélectionner un donneur d'ordre..."
                  displayField="name"
                  entityName="donneur d'ordre"
                  entityIcon={<Users size={16} />}
                  createEndpoint="/interventions/donneurs-ordre"
                  createFields={DONNEUR_ORDRE_CREATE_FIELDS}
                  queryKeys={['interventions', 'donneurs-ordre']}
                  allowCreate={true}
                />
              </div>

              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">N° donneur d'ordre</label>
                <Input
                  value={formData.reference_externe || ''}
                  onChange={(v) => updateField('reference_externe', v)}
                  placeholder="Ex: REF-2025-001, CMD-12345..."
                />
              </div>

              <div className="azals-field">
                <SmartSelector
                  items={(clients || []).map((c: any) => ({ id: c.id, name: c.name, code: c.code }))}
                  value={formData.client_id}
                  onChange={(value) => updateField('client_id', value)}
                  label="Client final *"
                  placeholder="Sélectionner un client..."
                  displayField="name"
                  secondaryField="code"
                  entityName="client"
                  entityIcon={<Building2 size={16} />}
                  createEndpoint="/commercial/customers"
                  createFields={CLIENT_CREATE_FIELDS}
                  queryKeys={['clients', 'commercial', 'customers']}
                  allowCreate={true}
                  error={errors.client_id}
                />
              </div>

              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">Facturer à</label>
                <Select
                  value={formData.facturer_a}
                  onChange={(v) => updateField('facturer_a', v)}
                  options={FACTURATION_OPTIONS}
                />
              </div>
            </Grid>

            {/* Adresse d'intervention */}
            <div style={{ marginTop: '16px' }}>
              <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px', color: 'var(--azals-text-secondary, #6b7280)' }}>
                <MapPin size={14} style={{ display: 'inline', marginRight: '4px' }} />
                Adresse d'intervention
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <Input
                  value={formData.adresse_ligne1 || ''}
                  onChange={(v) => updateField('adresse_ligne1', v)}
                  placeholder="Adresse ligne 1"
                />
                <Input
                  value={formData.adresse_ligne2 || ''}
                  onChange={(v) => updateField('adresse_ligne2', v)}
                  placeholder="Adresse ligne 2 (complément)"
                />
                <Grid cols={2} gap="md">
                  <Input
                    value={formData.code_postal || ''}
                    onChange={(v) => updateField('code_postal', v)}
                    placeholder="Code postal"
                  />
                  <Input
                    value={formData.ville || ''}
                    onChange={(v) => updateField('ville', v)}
                    placeholder="Ville"
                  />
                </Grid>
              </div>
            </div>
          </FormSection>

          {/* ============================================================ */}
          {/* SECTION 2 : INTERVENTION                                     */}
          {/* ============================================================ */}
          <FormSection title="Intervention" icon={<Wrench size={20} />}>
            <Grid cols={2} gap="md">
              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">Type d'intervention</label>
                <Select
                  value={formData.type_intervention}
                  onChange={(v) => updateField('type_intervention', v)}
                  options={TYPES_INTERVENTION}
                />
              </div>

              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">Priorité</label>
                <Select
                  value={formData.priorite}
                  onChange={(v) => updateField('priorite', v)}
                  options={PRIORITES}
                />
              </div>

              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">Corps d'état</label>
                <Select
                  value={formData.corps_etat || ''}
                  onChange={(v) => updateField('corps_etat', v || undefined)}
                  options={CORPS_ETAT_OPTIONS}
                />
              </div>
            </Grid>

            <div className="azals-field" style={{ marginTop: '12px' }}>
              <label className="block text-sm font-medium mb-1">Titre</label>
              <Input
                value={formData.titre || ''}
                onChange={(v) => updateField('titre', v)}
                placeholder="Titre de l'intervention"
              />
            </div>

            <Grid cols={3} gap="md">
              <div className="azals-field" style={{ marginTop: '12px' }}>
                <label className="block text-sm font-medium mb-1">Date prévue</label>
                <input
                  type="datetime-local"
                  className="azals-input"
                  value={formData.date_prevue_debut || ''}
                  onChange={(e) => updateField('date_prevue_debut', e.target.value)}
                />
              </div>

              <div className="azals-field" style={{ marginTop: '12px' }}>
                <label className="block text-sm font-medium mb-1">Durée prévue (h)</label>
                <input
                  type="number"
                  className="azals-input"
                  step="0.25"
                  min="0"
                  value={formData.duree_prevue_heures ?? ''}
                  onChange={(e) => updateField('duree_prevue_heures', e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="1,00"
                />
              </div>

              <div className="azals-field" style={{ marginTop: '12px' }}>
                <label className="block text-sm font-medium mb-1">Intervenant</label>
                <Select
                  value={formData.intervenant_id || ''}
                  onChange={(v) => updateField('intervenant_id', v)}
                  options={[
                    { value: '', label: 'Non assigné' },
                    ...intervenants.map((i: any) => ({ value: i.id, label: `${i.first_name} ${i.last_name}` }))
                  ]}
                />
              </div>
            </Grid>

          </FormSection>

          {/* ============================================================ */}
          {/* SECTION 4 : TRAVAUX                                          */}
          {/* ============================================================ */}
          <FormSection title="Travaux" icon={<FileText size={20} />}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">Description du problème</label>
                <TextArea
                  value={formData.description || ''}
                  onChange={(v) => updateField('description', v)}
                  rows={3}
                  placeholder="Décrivez le problème à résoudre..."
                />
              </div>

            </div>
          </FormSection>

          {/* ============================================================ */}
          {/* ACTIONS                                                      */}
          {/* ============================================================ */}
          <div style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '12px',
            padding: '16px 0'
          }}>
            <Button type="button" variant="secondary" onClick={onBack}>
              Annuler
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting
                ? 'Enregistrement...'
                : isEdit
                  ? 'Enregistrer les modifications'
                  : "Créer l'intervention"
              }
            </Button>
          </div>
        </div>
      </form>
    </PageWrapper>
  );
};
