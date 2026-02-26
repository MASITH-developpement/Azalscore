/**
 * AZALSCORE Module - Ordres de Service - Donneurs d'Ordre View
 * Gestion des donneurs d'ordre
 */

import React, { useState } from 'react';
import { Plus, Edit, Trash2 } from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import type { DonneurOrdre } from '../types';
import {
  useDonneursOrdre, useClients,
  useCreateDonneurOrdre, useUpdateDonneurOrdre, useDeleteDonneurOrdre
} from '../hooks';

export interface DonneursOrdreViewProps {
  onBack: () => void;
}

export const DonneursOrdreView: React.FC<DonneursOrdreViewProps> = ({ onBack }) => {
  const { data: donneursOrdre, isLoading, refetch } = useDonneursOrdre();
  const { data: clients } = useClients();
  const createDonneurOrdre = useCreateDonneurOrdre();
  const updateDonneurOrdre = useUpdateDonneurOrdre();
  const deleteDonneurOrdre = useDeleteDonneurOrdre();

  const [showModal, setShowModal] = useState(false);
  const [editingDonneur, setEditingDonneur] = useState<DonneurOrdre | null>(null);
  const [form, setForm] = useState({
    code: '',
    nom: '',
    type: '',
    client_id: '',
    email: '',
    telephone: '',
    adresse: '',
    is_active: true,
  });

  const resetForm = () => {
    setForm({ code: '', nom: '', type: '', client_id: '', email: '', telephone: '', adresse: '', is_active: true });
    setEditingDonneur(null);
  };

  const openCreate = () => {
    resetForm();
    setShowModal(true);
  };

  const openEdit = (donneur: DonneurOrdre) => {
    setEditingDonneur(donneur);
    setForm({
      code: donneur.code || '',
      nom: donneur.nom || '',
      type: donneur.type || '',
      client_id: donneur.client_id || '',
      email: donneur.email || '',
      telephone: donneur.telephone || '',
      adresse: donneur.adresse || '',
      is_active: donneur.is_active !== false,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.code || !form.nom) {
      alert('Veuillez remplir le code et le nom');
      return;
    }
    try {
      if (editingDonneur) {
        await updateDonneurOrdre.mutateAsync({ id: editingDonneur.id, data: form });
      } else {
        await createDonneurOrdre.mutateAsync(form);
      }
      setShowModal(false);
      resetForm();
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
    }
  };

  const handleDelete = async (donneur: DonneurOrdre) => {
    if (window.confirm(`Supprimer le donneur d'ordre "${donneur.nom}" ?`)) {
      await deleteDonneurOrdre.mutateAsync(donneur.id);
    }
  };

  const columns: TableColumn<DonneurOrdre>[] = [
    { id: 'code', header: 'Code', accessor: 'code', sortable: true },
    { id: 'nom', header: 'Nom', accessor: 'nom', sortable: true },
    { id: 'type', header: 'Type', accessor: 'type', render: (value) => (value ? String(value) : <span className="text-muted">-</span>) },
    { id: 'email', header: 'Email', accessor: 'email', render: (value) => (value ? String(value) : <span className="text-muted">-</span>) },
    { id: 'telephone', header: 'Telephone', accessor: 'telephone', render: (value) => (value ? String(value) : <span className="text-muted">-</span>) },
    {
      id: 'is_active',
      header: 'Actif',
      accessor: 'is_active',
      render: (value) => (
        <span className={`azals-badge azals-badge--${value !== false ? 'green' : 'gray'}`}>
          {value !== false ? 'Oui' : 'Non'}
        </span>
      ),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="azals-table-actions">
          <button className="azals-btn-icon" onClick={() => openEdit(row)} title="Modifier"><Edit size={16} /></button>
          <button className="azals-btn-icon azals-btn-icon--danger" onClick={() => handleDelete(row)} title="Supprimer"><Trash2 size={16} /></button>
        </div>
      ),
    },
  ];

  const isSubmitting = createDonneurOrdre.isPending || updateDonneurOrdre.isPending;

  return (
    <PageWrapper
      title="Donneurs d'ordre"
      subtitle="Gestion des donneurs d'ordre"
      backAction={{ label: 'Retour', onClick: onBack }}
      actions={<Button leftIcon={<Plus size={16} />} onClick={openCreate}>Nouveau donneur d'ordre</Button>}
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={donneursOrdre || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          onRefresh={refetch}
          emptyMessage="Aucun donneur d'ordre"
        />
      </Card>

      {showModal && (
        <div className="azals-modal-overlay">
          <div className="azals-modal">
            <h3>{editingDonneur ? 'Modifier le donneur d\'ordre' : 'Nouveau donneur d\'ordre'}</h3>
            <form onSubmit={handleSubmit}>
              <Grid cols={2} gap="md">
                <div className="azals-form-field">
                  <label>Code *</label>
                  <input type="text" className="azals-input" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} required disabled={!!editingDonneur} />
                </div>
                <div className="azals-form-field">
                  <label>Nom *</label>
                  <input type="text" className="azals-input" value={form.nom} onChange={(e) => setForm({ ...form, nom: e.target.value })} required />
                </div>
                <div className="azals-form-field">
                  <label>Type</label>
                  <select className="azals-select" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                    <option value="">-- Selectionner --</option>
                    <option value="client">Client</option>
                    <option value="fournisseur">Fournisseur</option>
                    <option value="partenaire">Partenaire</option>
                    <option value="autre">Autre</option>
                  </select>
                </div>
                <div className="azals-form-field">
                  <label>Client associe</label>
                  <select className="azals-select" value={form.client_id} onChange={(e) => setForm({ ...form, client_id: e.target.value })}>
                    <option value="">-- Aucun --</option>
                    {clients?.map(c => <option key={c.id} value={c.id}>{c.name} ({c.code})</option>)}
                  </select>
                </div>
                <div className="azals-form-field">
                  <label>Email</label>
                  <input type="email" className="azals-input" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                </div>
                <div className="azals-form-field">
                  <label>Telephone</label>
                  <input type="tel" className="azals-input" value={form.telephone} onChange={(e) => setForm({ ...form, telephone: e.target.value })} />
                </div>
                <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
                  <label>Adresse</label>
                  <textarea className="azals-textarea" value={form.adresse} onChange={(e) => setForm({ ...form, adresse: e.target.value })} rows={2} />
                </div>
                <div className="azals-form-field">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
                    Actif
                  </label>
                </div>
              </Grid>
              <div className="azals-modal__actions">
                <Button type="button" variant="ghost" onClick={() => { setShowModal(false); resetForm(); }}>Annuler</Button>
                <Button type="submit" isLoading={isSubmitting}>{editingDonneur ? 'Enregistrer' : 'Creer'}</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </PageWrapper>
  );
};

export default DonneursOrdreView;
