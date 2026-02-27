/**
 * AZALSCORE Module - HR Vault - Upload Document Modal
 * Modal pour deposer un nouveau document
 */

import React, { useState } from 'react';
import { Button, Modal } from '@ui/actions';
import { Input, Select, TextArea } from '@ui/forms';
import { hrVaultApi } from '../api';
import { DOCUMENT_TYPE_CONFIG } from '../types';
import type { VaultDocumentType } from '../types';

export interface UploadDocumentModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export const UploadDocumentModal: React.FC<UploadDocumentModalProps> = ({ onClose, onSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [documentType, setDocumentType] = useState<VaultDocumentType>('OTHER');
  const [employeeId, setEmployeeId] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title || !employeeId) {
      setError('Veuillez remplir tous les champs obligatoires');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      formData.append('document_type', documentType);
      formData.append('employee_id', employeeId);
      if (description) formData.append('description', description);

      await hrVaultApi.uploadDocument(formData);
      onSuccess();
    } catch (err) {
      setError('Erreur lors du depot du document');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const documentTypeOptions = Object.entries(DOCUMENT_TYPE_CONFIG).map(([value, config]) => ({
    value,
    label: config.label,
  }));

  return (
    <Modal title="Deposer un document" isOpen onClose={onClose} size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-50 text-red-700 rounded">{error}</div>
        )}

        <div>
          <label className="block text-sm font-medium mb-1">Fichier *</label>
          <input
            type="file"
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full border rounded p-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Titre *</label>
          <Input
            value={title}
            onChange={setTitle}
            placeholder="Titre du document"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Type de document *</label>
          <Select
            value={documentType}
            onChange={(v) => setDocumentType(v as VaultDocumentType)}
            options={documentTypeOptions}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">ID Employe *</label>
          <Input
            value={employeeId}
            onChange={setEmployeeId}
            placeholder="UUID de l'employe"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <TextArea
            value={description}
            onChange={setDescription}
            placeholder="Description optionnelle"
            rows={3}
          />
        </div>

        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Depot en cours...' : 'Deposer'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default UploadDocumentModal;
