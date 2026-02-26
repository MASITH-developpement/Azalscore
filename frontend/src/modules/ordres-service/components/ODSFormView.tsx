/**
 * AZALSCORE Module - Ordres de Service - Form View
 * Formulaire de creation/modification d'intervention
 */

import React, { useState, useEffect } from 'react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { TYPES_INTERVENTION, PRIORITES, CORPS_ETATS, CANAUX_DEMANDE } from '../types';
import type { Intervention, InterventionPriorite, TypeIntervention, CorpsEtat, CanalDemande } from '../types';
import {
  useIntervention, useDonneursOrdre, useClients, useIntervenants,
  useCreateIntervention, useUpdateIntervention
} from '../hooks';

export interface ODSFormViewProps {
  interventionId?: string;
  onBack: () => void;
  onSaved: (id: string) => void;
}

export const ODSFormView: React.FC<ODSFormViewProps> = ({ interventionId, onBack, onSaved }) => {
  const isNew = !interventionId;
  const { data: intervention } = useIntervention(interventionId || '');
  const { data: donneursOrdre } = useDonneursOrdre();
  const { data: clients } = useClients();
  const { data: intervenants } = useIntervenants();
  const createIntervention = useCreateIntervention();
  const updateIntervention = useUpdateIntervention();

  const [form, setForm] = useState({
    client_id: '',
    type_intervention: 'AUTRE' as TypeIntervention,
    priorite: 'NORMAL' as InterventionPriorite,
    corps_etat: '' as CorpsEtat | '',
    canal_demande: '' as CanalDemande | '',
    reference_externe: '',
    titre: '',
    description: '',
    notes_internes: '',
    notes_client: '',
    donneur_ordre_id: '',
    projet_id: '',
    affaire_id: '',
    adresse_ligne1: '',
    adresse_ligne2: '',
    ville: '',
    code_postal: '',
    contact_sur_place: '',
    telephone_contact: '',
    email_contact: '',
    date_prevue_debut: '',
    date_prevue_fin: '',
    duree_prevue_minutes: 60,
    intervenant_id: '',
    materiel_necessaire: '',
    facturable: true,
    montant_ht: 0,
    montant_ttc: 0,
  });

  useEffect(() => {
    if (intervention) {
      setForm({
        client_id: intervention.client_id || '',
        type_intervention: intervention.type_intervention || 'AUTRE',
        priorite: intervention.priorite || 'NORMAL',
        corps_etat: intervention.corps_etat || '',
        canal_demande: intervention.canal_demande || '',
        reference_externe: intervention.reference_externe || '',
        titre: intervention.titre || '',
        description: intervention.description || '',
        notes_internes: intervention.notes_internes || '',
        notes_client: intervention.notes_client || '',
        donneur_ordre_id: intervention.donneur_ordre_id || '',
        projet_id: intervention.projet_id || '',
        affaire_id: intervention.affaire_id || '',
        adresse_ligne1: intervention.adresse_ligne1 || '',
        adresse_ligne2: intervention.adresse_ligne2 || '',
        ville: intervention.ville || '',
        code_postal: intervention.code_postal || '',
        contact_sur_place: intervention.contact_sur_place || '',
        telephone_contact: intervention.telephone_contact || '',
        email_contact: intervention.email_contact || '',
        date_prevue_debut: intervention.date_prevue_debut ? intervention.date_prevue_debut.slice(0, 16) : '',
        date_prevue_fin: intervention.date_prevue_fin ? intervention.date_prevue_fin.slice(0, 16) : '',
        duree_prevue_minutes: intervention.duree_prevue_minutes || 60,
        intervenant_id: intervention.intervenant_id || '',
        materiel_necessaire: intervention.materiel_necessaire || '',
        facturable: intervention.facturable !== false,
        montant_ht: intervention.montant_ht || 0,
        montant_ttc: intervention.montant_ttc || 0,
      });
    }
  }, [intervention]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.titre) {
      alert('Veuillez saisir un titre');
      return;
    }
    const submitData: Partial<Intervention> = {
      ...form,
      corps_etat: form.corps_etat || undefined,
      canal_demande: form.canal_demande || undefined,
    };
    try {
      if (isNew) {
        const result = await createIntervention.mutateAsync(submitData);
        onSaved(result.id);
      } else {
        await updateIntervention.mutateAsync({ id: interventionId!, data: submitData });
        onSaved(interventionId!);
      }
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
    }
  };

  const isSubmitting = createIntervention.isPending || updateIntervention.isPending;

  return (
    <PageWrapper
      title={isNew ? 'Nouvel ordre de service' : 'Modifier l\'intervention'}
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <form onSubmit={handleSubmit}>
        <Card title="Classification">
          <Grid cols={3} gap="md">
            <div className="azals-form-field">
              <label>Client *</label>
              <select className="azals-select" value={form.client_id} onChange={(e) => setForm({ ...form, client_id: e.target.value })} required>
                <option value="">-- Selectionner --</option>
                {clients?.map(c => <option key={c.id} value={c.id}>{c.name} ({c.code})</option>)}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Donneur d'ordre</label>
              <select className="azals-select" value={form.donneur_ordre_id} onChange={(e) => setForm({ ...form, donneur_ordre_id: e.target.value })}>
                <option value="">-- Selectionner --</option>
                {donneursOrdre?.map(d => <option key={d.id} value={d.id}>{d.nom}</option>)}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Reference externe</label>
              <input type="text" className="azals-input" value={form.reference_externe} onChange={(e) => setForm({ ...form, reference_externe: e.target.value })} placeholder="Ref. client..." />
            </div>
            <div className="azals-form-field">
              <label>Type d'intervention</label>
              <select className="azals-select" value={form.type_intervention} onChange={(e) => setForm({ ...form, type_intervention: e.target.value as TypeIntervention })}>
                {TYPES_INTERVENTION.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Priorite</label>
              <select className="azals-select" value={form.priorite} onChange={(e) => setForm({ ...form, priorite: e.target.value as InterventionPriorite })}>
                {PRIORITES.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Corps d'etat</label>
              <select className="azals-select" value={form.corps_etat} onChange={(e) => setForm({ ...form, corps_etat: e.target.value as CorpsEtat })}>
                <option value="">-- Selectionner --</option>
                {CORPS_ETATS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Canal de demande</label>
              <select className="azals-select" value={form.canal_demande} onChange={(e) => setForm({ ...form, canal_demande: e.target.value as CanalDemande })}>
                <option value="">-- Selectionner --</option>
                {CANAUX_DEMANDE.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
          </Grid>
        </Card>

        <Card title="Details">
          <Grid cols={2} gap="md">
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Titre</label>
              <input type="text" className="azals-input" value={form.titre} onChange={(e) => setForm({ ...form, titre: e.target.value })} />
            </div>
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Description</label>
              <textarea className="azals-textarea" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} />
            </div>
            <div className="azals-form-field">
              <label>Notes internes</label>
              <textarea className="azals-textarea" value={form.notes_internes} onChange={(e) => setForm({ ...form, notes_internes: e.target.value })} rows={2} placeholder="Notes visibles uniquement en interne..." />
            </div>
            <div className="azals-form-field">
              <label>Notes client</label>
              <textarea className="azals-textarea" value={form.notes_client} onChange={(e) => setForm({ ...form, notes_client: e.target.value })} rows={2} placeholder="Notes visibles par le client..." />
            </div>
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Materiel necessaire</label>
              <textarea className="azals-textarea" value={form.materiel_necessaire} onChange={(e) => setForm({ ...form, materiel_necessaire: e.target.value })} rows={2} placeholder="Liste du materiel a prevoir..." />
            </div>
          </Grid>
        </Card>

        <Card title="Lieu d'intervention">
          <Grid cols={3} gap="md">
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Adresse ligne 1</label>
              <input type="text" className="azals-input" value={form.adresse_ligne1} onChange={(e) => setForm({ ...form, adresse_ligne1: e.target.value })} />
            </div>
            <div className="azals-form-field">
              <label>Adresse ligne 2</label>
              <input type="text" className="azals-input" value={form.adresse_ligne2} onChange={(e) => setForm({ ...form, adresse_ligne2: e.target.value })} placeholder="Batiment, etage..." />
            </div>
            <div className="azals-form-field">
              <label>Code postal</label>
              <input type="text" className="azals-input" value={form.code_postal} onChange={(e) => setForm({ ...form, code_postal: e.target.value })} />
            </div>
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Ville</label>
              <input type="text" className="azals-input" value={form.ville} onChange={(e) => setForm({ ...form, ville: e.target.value })} />
            </div>
          </Grid>
        </Card>

        <Card title="Contact sur place">
          <Grid cols={3} gap="md">
            <div className="azals-form-field">
              <label>Nom du contact</label>
              <input type="text" className="azals-input" value={form.contact_sur_place} onChange={(e) => setForm({ ...form, contact_sur_place: e.target.value })} />
            </div>
            <div className="azals-form-field">
              <label>Telephone</label>
              <input type="tel" className="azals-input" value={form.telephone_contact} onChange={(e) => setForm({ ...form, telephone_contact: e.target.value })} />
            </div>
            <div className="azals-form-field">
              <label>Email</label>
              <input type="email" className="azals-input" value={form.email_contact} onChange={(e) => setForm({ ...form, email_contact: e.target.value })} />
            </div>
          </Grid>
        </Card>

        <Card title="Planification">
          <Grid cols={3} gap="md">
            <div className="azals-form-field">
              <label>Date/heure debut</label>
              <input type="datetime-local" className="azals-input" value={form.date_prevue_debut} onChange={(e) => setForm({ ...form, date_prevue_debut: e.target.value })} />
            </div>
            <div className="azals-form-field">
              <label>Date/heure fin</label>
              <input type="datetime-local" className="azals-input" value={form.date_prevue_fin} onChange={(e) => setForm({ ...form, date_prevue_fin: e.target.value })} />
            </div>
            <div className="azals-form-field">
              <label>Duree prevue (minutes)</label>
              <input type="number" className="azals-input" value={form.duree_prevue_minutes} onChange={(e) => setForm({ ...form, duree_prevue_minutes: parseInt(e.target.value) || 0 })} min="0" step="15" />
            </div>
            <div className="azals-form-field" style={{ gridColumn: 'span 3' }}>
              <label>Intervenant</label>
              <select className="azals-select" value={form.intervenant_id} onChange={(e) => setForm({ ...form, intervenant_id: e.target.value })}>
                <option value="">-- Non assigne --</option>
                {intervenants?.map(i => <option key={i.id} value={i.id}>{i.first_name} {i.last_name}</option>)}
              </select>
            </div>
          </Grid>
        </Card>

        <Card title="Facturation">
          <Grid cols={3} gap="md">
            <div className="azals-form-field">
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={form.facturable} onChange={(e) => setForm({ ...form, facturable: e.target.checked })} />
                Intervention facturable
              </label>
            </div>
            <div className="azals-form-field">
              <label>Montant HT (EUR)</label>
              <input type="number" className="azals-input" value={form.montant_ht} onChange={(e) => setForm({ ...form, montant_ht: parseFloat(e.target.value) || 0 })} min="0" step="10" disabled={!form.facturable} />
            </div>
            <div className="azals-form-field">
              <label>Montant TTC (EUR)</label>
              <input type="number" className="azals-input" value={form.montant_ttc} onChange={(e) => setForm({ ...form, montant_ttc: parseFloat(e.target.value) || 0 })} min="0" step="10" disabled={!form.facturable} />
            </div>
          </Grid>
        </Card>

        <div className="azals-form-actions">
          <Button type="button" variant="ghost" onClick={onBack}>Annuler</Button>
          <Button type="submit" isLoading={isSubmitting}>{isNew ? 'Creer' : 'Enregistrer'}</Button>
        </div>
      </form>
    </PageWrapper>
  );
};

export default ODSFormView;
