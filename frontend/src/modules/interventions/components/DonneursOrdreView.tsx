/**
 * AZALSCORE Module - INTERVENTIONS - Donneurs d'Ordre View
 * Gestion des donneurs d'ordre avec CRUD complet
 */

import React, { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Edit, Trash2 } from 'lucide-react';
import { api } from '@core/api-client';
import { Button, Modal } from '@ui/actions';
import { Card } from '@ui/layout';
import { Badge } from '@ui/simple';
import { DataTable } from '@ui/tables';
import type { TableColumn, ApiMutationError } from '@/types';
import {
  useDonneursOrdre,
  useUpdateDonneurOrdre,
  useDeleteDonneurOrdre,
  interventionKeys,
} from '../api';
import type { DonneurOrdre } from '../types';

export interface DonneursOrdreViewProps {
  // No props required
}

export const DonneursOrdreView: React.FC<DonneursOrdreViewProps> = () => {
  const { data: donneursOrdre = [], isLoading, error: donneursError, refetch: refetchDonneurs } = useDonneursOrdre();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [editingDonneur, setEditingDonneur] = useState<DonneurOrdre | null>(null);
  const [formData, setFormData] = useState({
    code: '', nom: '', email: '', telephone: '', type: '', adresse: '', client_id: '',
    adresse_facturation: '', delai_paiement: '30', email_rapport: '',
    contact_commercial_nom: '', contact_commercial_email: '', contact_commercial_telephone: '',
    contact_comptabilite_nom: '', contact_comptabilite_email: '', contact_comptabilite_telephone: '',
    contact_technique_nom: '', contact_technique_email: '', contact_technique_telephone: ''
  });
  const [createError, setCreateError] = useState('');

  const updateFormField = useCallback((field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const closeCreateModal = useCallback(() => {
    setShowCreate(false);
    setCreateError('');
  }, []);

  const closeEditModal = useCallback(() => {
    setShowEdit(false);
    setEditingDonneur(null);
  }, []);

  const [editFormData, setEditFormData] = useState({
    nom: '', code: '', email: '', telephone: '', type: '', adresse: '', client_id: '',
    adresse_facturation: '', delai_paiement: '30', email_rapport: '',
    contact_commercial_nom: '', contact_commercial_email: '', contact_commercial_telephone: '',
    contact_comptabilite_nom: '', contact_comptabilite_email: '', contact_comptabilite_telephone: '',
    contact_technique_nom: '', contact_technique_email: '', contact_technique_telephone: ''
  });
  const updateEditFormField = useCallback((field: string, value: string) => {
    setEditFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const updateDonneur = useUpdateDonneurOrdre();
  const deleteDonneur = useDeleteDonneurOrdre();

  const handleEdit = (donneur: DonneurOrdre) => {
    setEditingDonneur(donneur);
    setEditFormData({
      nom: donneur.nom || '',
      code: donneur.code || '',
      email: donneur.email || '',
      telephone: donneur.telephone || '',
      type: donneur.type || '',
      adresse: donneur.adresse || '',
      client_id: donneur.client_id || '',
      adresse_facturation: donneur.adresse_facturation || '',
      delai_paiement: String(donneur.delai_paiement ?? 30),
      email_rapport: donneur.email_rapport || '',
      contact_commercial_nom: donneur.contact_commercial_nom || '',
      contact_commercial_email: donneur.contact_commercial_email || '',
      contact_commercial_telephone: donneur.contact_commercial_telephone || '',
      contact_comptabilite_nom: donneur.contact_comptabilite_nom || '',
      contact_comptabilite_email: donneur.contact_comptabilite_email || '',
      contact_comptabilite_telephone: donneur.contact_comptabilite_telephone || '',
      contact_technique_nom: donneur.contact_technique_nom || '',
      contact_technique_email: donneur.contact_technique_email || '',
      contact_technique_telephone: donneur.contact_technique_telephone || '',
    });
    setShowEdit(true);
  };

  const handleDelete = async (donneur: DonneurOrdre) => {
    if (window.confirm(`Supprimer le donneur d'ordre "${donneur.nom}" ?`)) {
      try {
        await deleteDonneur.mutateAsync(donneur.id);
      } catch (error: unknown) {
        const err = error as ApiMutationError;
        alert(`Erreur lors de la suppression: ${err?.response?.data?.detail || err?.message || 'Erreur inconnue'}`);
      }
    }
  };

  const handleSaveEdit = async () => {
    if (!editingDonneur) return;
    const dataToSend = {
      ...editFormData,
      delai_paiement: editFormData.delai_paiement ? parseInt(editFormData.delai_paiement, 10) : undefined,
    };
    await updateDonneur.mutateAsync({ id: editingDonneur.id, data: dataToSend });
    setShowEdit(false);
    setEditingDonneur(null);
  };

  const createDonneur = useMutation({
    mutationFn: async (data: typeof formData) => {
      const dataToSend = {
        ...data,
        delai_paiement: data.delai_paiement ? parseInt(data.delai_paiement, 10) : 30,
      };
      return api.post('/interventions/donneurs-ordre', dataToSend);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: interventionKeys.donneursOrdre() });
      setShowCreate(false);
      setFormData({
        nom: '', code: '', email: '', telephone: '', type: '', adresse: '', client_id: '',
        adresse_facturation: '', delai_paiement: '30', email_rapport: '',
        contact_commercial_nom: '', contact_commercial_email: '', contact_commercial_telephone: '',
        contact_comptabilite_nom: '', contact_comptabilite_email: '', contact_comptabilite_telephone: '',
        contact_technique_nom: '', contact_technique_email: '', contact_technique_telephone: ''
      });
      setCreateError('');
    },
    onError: (error: ApiMutationError) => {
      setCreateError(error?.response?.data?.detail || error?.message || 'Erreur lors de la création');
    },
  });

  const handleCreate = () => {
    if (!formData.nom.trim()) {
      setCreateError('Le nom est obligatoire');
      return;
    }
    setCreateError('');
    // Le code sera auto-généré par le backend si non fourni
    createDonneur.mutate(formData);
  };

  const columns: TableColumn<DonneurOrdre>[] = [
    { id: 'code', header: 'Code', accessor: 'code' },
    { id: 'nom', header: 'Nom', accessor: 'nom' },
    { id: 'email', header: 'Email', accessor: 'email', render: (v) => (v as string) || '-' },
    { id: 'telephone', header: 'Téléphone', accessor: 'telephone', render: (v) => (v as string) || '-' },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge variant={(v as boolean) ? 'green' : 'default'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_v, row) => (
      <div className="flex gap-1 items-center">
        <button
          className="p-1 hover:bg-gray-100 rounded"
          onClick={() => handleEdit(row)}
          title="Modifier"
        >
          <Edit size={14} className="text-gray-600" />
        </button>
        <button
          className="p-1 hover:bg-red-100 rounded"
          onClick={() => handleDelete(row)}
          title="Supprimer"
        >
          <Trash2 size={14} className="text-red-500" />
        </button>
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Donneurs d'ordre</h3>
        <Button onClick={() => setShowCreate(true)}>Nouveau donneur d'ordre</Button>
      </div>
      <DataTable columns={columns} data={donneursOrdre} isLoading={isLoading} keyField="id"
          filterable error={donneursError instanceof Error ? donneursError : null} onRetry={() => refetchDonneurs()} />

      {showCreate && (
        <Modal isOpen onClose={closeCreateModal} title="Nouveau donneur d'ordre">
          <div className="azals-modal__body">
            {createError && (
              <div className="azals-alert azals-alert--error mb-4">
                {createError}
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div className="azals-field">
                <label className="azals-field__label" htmlFor="donneur-nom">Nom <span className="azals-field__required">*</span></label>
                <input id="donneur-nom" className="azals-input" value={formData.nom} onChange={e => updateFormField('nom', e.target.value)} placeholder="Nom du donneur d'ordre" autoFocus />
              </div>
              <div className="azals-field">
                <label className="azals-field__label" htmlFor="donneur-code">Code <span className="text-gray-400 text-xs">(auto si vide)</span></label>
                <input id="donneur-code" className="azals-input" value={formData.code} onChange={e => updateFormField('code', e.target.value)} placeholder="Auto: DO-0001" />
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="donneur-type">Type</label>
              <select id="donneur-type" className="azals-select" value={formData.type} onChange={e => updateFormField('type', e.target.value)}>
                <option value="">-- Sélectionner un type --</option>
                <option value="ASSURANCE">Assurance</option>
                <option value="SYNDIC">Syndic</option>
                <option value="BAILLEUR">Bailleur</option>
                <option value="PARTICULIER">Particulier</option>
                <option value="ENTREPRISE">Entreprise</option>
                <option value="COLLECTIVITE">Collectivité</option>
                <option value="AUTRE">Autre</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="azals-field">
                <label className="azals-field__label" htmlFor="donneur-email">Email</label>
                <input id="donneur-email" className="azals-input" type="email" value={formData.email} onChange={e => updateFormField('email', e.target.value)} placeholder="email@example.com" />
              </div>
              <div className="azals-field">
                <label className="azals-field__label" htmlFor="donneur-telephone">Téléphone</label>
                <input id="donneur-telephone" className="azals-input" type="tel" value={formData.telephone} onChange={e => updateFormField('telephone', e.target.value)} placeholder="0612345678" />
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="donneur-adresse">Adresse</label>
              <textarea id="donneur-adresse" className="azals-input" rows={2} value={formData.adresse} onChange={e => updateFormField('adresse', e.target.value)} placeholder="Adresse complète" />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="donneur-adresse-fact">Adresse de facturation <span className="text-gray-400 text-xs">(si différente)</span></label>
              <textarea id="donneur-adresse-fact" className="azals-input" rows={2} value={formData.adresse_facturation} onChange={e => updateFormField('adresse_facturation', e.target.value)} placeholder="Adresse de facturation" />
            </div>

            {/* Facturation */}
            <div className="border-t pt-4 mt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Facturation & Rapports</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="donneur-delai">Délai de paiement (jours)</label>
                  <input id="donneur-delai" className="azals-input" type="number" min="0" max="365" value={formData.delai_paiement} onChange={e => updateFormField('delai_paiement', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="donneur-email-rapport">Email rapports d'intervention</label>
                  <input id="donneur-email-rapport" className="azals-input" type="email" value={formData.email_rapport} onChange={e => updateFormField('email_rapport', e.target.value)} placeholder="rapports@example.com" />
                </div>
              </div>
            </div>

            {/* Contact Commercial */}
            <div className="border-t pt-4 mt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Contact Commercial</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="donneur-comm-nom">Nom</label>
                  <input id="donneur-comm-nom" className="azals-input" value={formData.contact_commercial_nom} onChange={e => updateFormField('contact_commercial_nom', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="donneur-comm-email">Email</label>
                  <input id="donneur-comm-email" className="azals-input" type="email" value={formData.contact_commercial_email} onChange={e => updateFormField('contact_commercial_email', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="donneur-comm-tel">Téléphone</label>
                  <input id="donneur-comm-tel" className="azals-input" type="tel" value={formData.contact_commercial_telephone} onChange={e => updateFormField('contact_commercial_telephone', e.target.value)} />
                </div>
              </div>
            </div>

            {/* Contact Comptabilité */}
            <div className="border-t pt-4 mt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Contact Comptabilité</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="donneur-compta-nom">Nom</label>
                  <input id="donneur-compta-nom" className="azals-input" value={formData.contact_comptabilite_nom} onChange={e => updateFormField('contact_comptabilite_nom', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="donneur-compta-email">Email</label>
                  <input id="donneur-compta-email" className="azals-input" type="email" value={formData.contact_comptabilite_email} onChange={e => updateFormField('contact_comptabilite_email', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="donneur-compta-tel">Téléphone</label>
                  <input id="donneur-compta-tel" className="azals-input" type="tel" value={formData.contact_comptabilite_telephone} onChange={e => updateFormField('contact_comptabilite_telephone', e.target.value)} />
                </div>
              </div>
            </div>

            {/* Contact Technique */}
            <div className="border-t pt-4 mt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Contact Technique / Chantier</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="donneur-tech-nom">Nom</label>
                  <input id="donneur-tech-nom" className="azals-input" value={formData.contact_technique_nom} onChange={e => updateFormField('contact_technique_nom', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="donneur-tech-email">Email</label>
                  <input id="donneur-tech-email" className="azals-input" type="email" value={formData.contact_technique_email} onChange={e => updateFormField('contact_technique_email', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="donneur-tech-tel">Téléphone</label>
                  <input id="donneur-tech-tel" className="azals-input" type="tel" value={formData.contact_technique_telephone} onChange={e => updateFormField('contact_technique_telephone', e.target.value)} />
                </div>
              </div>
            </div>
          </div>
          <div className="azals-modal__footer">
            <Button variant="secondary" onClick={closeCreateModal}>Annuler</Button>
            <Button onClick={handleCreate} disabled={createDonneur.isPending}>
              {createDonneur.isPending ? 'Création...' : 'Créer'}
            </Button>
          </div>
        </Modal>
      )}

      {/* Modal édition */}
      {showEdit && editingDonneur && (
        <Modal isOpen onClose={closeEditModal} title="Modifier le donneur d'ordre">
          <div className="azals-modal__body max-h-[70vh] overflow-y-auto">
            <div className="grid grid-cols-2 gap-4">
              <div className="azals-field">
                <label className="azals-field__label" htmlFor="edit-donneur-code">Code</label>
                <input id="edit-donneur-code" className="azals-input bg-gray-100" value={editFormData.code} disabled />
              </div>
              <div className="azals-field">
                <label className="azals-field__label" htmlFor="edit-donneur-nom">Nom <span className="azals-field__required">*</span></label>
                <input id="edit-donneur-nom" className="azals-input" value={editFormData.nom} onChange={e => updateEditFormField('nom', e.target.value)} autoFocus />
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="edit-donneur-type">Type</label>
              <select id="edit-donneur-type" className="azals-select" value={editFormData.type} onChange={e => updateEditFormField('type', e.target.value)}>
                <option value="">-- Sélectionner un type --</option>
                <option value="ASSURANCE">Assurance</option>
                <option value="SYNDIC">Syndic</option>
                <option value="BAILLEUR">Bailleur</option>
                <option value="PARTICULIER">Particulier</option>
                <option value="ENTREPRISE">Entreprise</option>
                <option value="COLLECTIVITE">Collectivité</option>
                <option value="AUTRE">Autre</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="azals-field">
                <label className="azals-field__label" htmlFor="edit-donneur-email">Email</label>
                <input id="edit-donneur-email" className="azals-input" type="email" value={editFormData.email} onChange={e => updateEditFormField('email', e.target.value)} />
              </div>
              <div className="azals-field">
                <label className="azals-field__label" htmlFor="edit-donneur-telephone">Téléphone</label>
                <input id="edit-donneur-telephone" className="azals-input" type="tel" value={editFormData.telephone} onChange={e => updateEditFormField('telephone', e.target.value)} />
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="edit-donneur-adresse">Adresse</label>
              <textarea id="edit-donneur-adresse" className="azals-input" rows={2} value={editFormData.adresse} onChange={e => updateEditFormField('adresse', e.target.value)} />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="edit-donneur-adresse-fact">Adresse de facturation</label>
              <textarea id="edit-donneur-adresse-fact" className="azals-input" rows={2} value={editFormData.adresse_facturation} onChange={e => updateEditFormField('adresse_facturation', e.target.value)} />
            </div>

            {/* Facturation */}
            <div className="border-t pt-4 mt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Facturation & Rapports</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="edit-donneur-delai">Délai de paiement (jours)</label>
                  <input id="edit-donneur-delai" className="azals-input" type="number" min="0" max="365" value={editFormData.delai_paiement} onChange={e => updateEditFormField('delai_paiement', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="edit-donneur-email-rapport">Email rapports</label>
                  <input id="edit-donneur-email-rapport" className="azals-input" type="email" value={editFormData.email_rapport} onChange={e => updateEditFormField('email_rapport', e.target.value)} />
                </div>
              </div>
            </div>

            {/* Contact Commercial */}
            <div className="border-t pt-4 mt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Contact Commercial</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="edit-contact-comm-nom">Nom</label>
                  <input id="edit-contact-comm-nom" className="azals-input" value={editFormData.contact_commercial_nom} onChange={e => updateEditFormField('contact_commercial_nom', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="edit-contact-comm-email">Email</label>
                  <input id="edit-contact-comm-email" className="azals-input" type="email" value={editFormData.contact_commercial_email} onChange={e => updateEditFormField('contact_commercial_email', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="edit-contact-comm-tel">Téléphone</label>
                  <input id="edit-contact-comm-tel" className="azals-input" type="tel" value={editFormData.contact_commercial_telephone} onChange={e => updateEditFormField('contact_commercial_telephone', e.target.value)} />
                </div>
              </div>
            </div>

            {/* Contact Comptabilité */}
            <div className="border-t pt-4 mt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Contact Comptabilité</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="edit-contact-compta-nom">Nom</label>
                  <input id="edit-contact-compta-nom" className="azals-input" value={editFormData.contact_comptabilite_nom} onChange={e => updateEditFormField('contact_comptabilite_nom', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="edit-contact-compta-email">Email</label>
                  <input id="edit-contact-compta-email" className="azals-input" type="email" value={editFormData.contact_comptabilite_email} onChange={e => updateEditFormField('contact_comptabilite_email', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="edit-contact-compta-tel">Téléphone</label>
                  <input id="edit-contact-compta-tel" className="azals-input" type="tel" value={editFormData.contact_comptabilite_telephone} onChange={e => updateEditFormField('contact_comptabilite_telephone', e.target.value)} />
                </div>
              </div>
            </div>

            {/* Contact Technique */}
            <div className="border-t pt-4 mt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Contact Technique / Chantier</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="edit-contact-tech-nom">Nom</label>
                  <input id="edit-contact-tech-nom" className="azals-input" value={editFormData.contact_technique_nom} onChange={e => updateEditFormField('contact_technique_nom', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="edit-contact-tech-email">Email</label>
                  <input id="edit-contact-tech-email" className="azals-input" type="email" value={editFormData.contact_technique_email} onChange={e => updateEditFormField('contact_technique_email', e.target.value)} />
                </div>
                <div className="azals-field">
                  <label className="azals-field__label" htmlFor="edit-contact-tech-tel">Téléphone</label>
                  <input id="edit-contact-tech-tel" className="azals-input" type="tel" value={editFormData.contact_technique_telephone} onChange={e => updateEditFormField('contact_technique_telephone', e.target.value)} />
                </div>
              </div>
            </div>
          </div>
          <div className="azals-modal__footer">
            <Button variant="secondary" onClick={closeEditModal}>Annuler</Button>
            <Button onClick={handleSaveEdit} disabled={updateDonneur.isPending}>
              {updateDonneur.isPending ? 'Enregistrement...' : 'Enregistrer'}
            </Button>
          </div>
        </Modal>
      )}
    </Card>
  );
};

export default DonneursOrdreView;
