/**
 * AZALSCORE Module - HR - DepartmentForm
 * Formulaire de creation/edition de departement
 */

import React, { useState } from 'react';
import { Button } from '@ui/actions';
import { Select } from '@ui/forms';
import { Grid } from '@ui/layout';
import type { Department, Employee } from '../types';

interface DepartmentFormProps {
  onSubmit: (data: Partial<Department>) => Promise<void>;
  onCancel: () => void;
  isLoading: boolean;
  employees: Employee[];
  departments: Department[];
  initialData?: Department;
}

const DepartmentForm: React.FC<DepartmentFormProps> = ({ onSubmit, onCancel, isLoading, employees, departments, initialData }) => {
  const [code, setCode] = useState(initialData?.code || '');
  const [name, setName] = useState(initialData?.name || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [parentId, setParentId] = useState(initialData?.parent_id || '');
  const [managerId, setManagerId] = useState(initialData?.manager_id || '');
  const [costCenter, setCostCenter] = useState(initialData?.cost_center || '');
  const [isActive, setIsActive] = useState(initialData?.is_active ?? true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      code,
      name,
      description: description || undefined,
      parent_id: parentId || undefined,
      manager_id: managerId || undefined,
      cost_center: costCenter || undefined,
      is_active: isActive,
    });
  };

  // Filtrer les departements pour eviter les references circulaires
  const availableParents = departments.filter(d => !initialData || d.id !== initialData.id);

  return (
    <form onSubmit={handleSubmit}>
      <Grid cols={2}>
        <div className="azals-field">
          <label htmlFor="dept-form-code">Code *</label>
          <input
            id="dept-form-code"
            type="text"
            className="azals-input"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="Ex: IT, RH, COMPTA"
            required
          />
        </div>
        <div className="azals-field">
          <label htmlFor="dept-form-name">Nom *</label>
          <input
            id="dept-form-name"
            type="text"
            className="azals-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ex: Informatique"
            required
          />
        </div>
      </Grid>
      <div className="azals-field">
        <label htmlFor="dept-form-desc">Description</label>
        <textarea
          id="dept-form-desc"
          className="azals-input"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description du departement"
          rows={2}
        />
      </div>
      <div className="azals-field">
        <label>Departement parent (hierarchie)</label>
        <Select
          value={parentId}
          onChange={(v) => setParentId(v)}
          options={[{ value: '', label: 'Aucun (departement racine)' }, ...availableParents.map(d => ({ value: d.id, label: `${d.code} - ${d.name}` }))]}
        />
      </div>
      <Grid cols={2}>
        <div className="azals-field">
          <label>Responsable</label>
          <Select
            value={managerId}
            onChange={(v) => setManagerId(v)}
            options={[{ value: '', label: 'Aucun (a definir plus tard)' }, ...employees.map(e => ({ value: e.id, label: `${e.first_name} ${e.last_name}` }))]}
          />
        </div>
        <div className="azals-field">
          <label htmlFor="dept-form-cost-center">Centre de cout</label>
          <input
            id="dept-form-cost-center"
            type="text"
            className="azals-input"
            value={costCenter}
            onChange={(e) => setCostCenter(e.target.value)}
            placeholder="Ex: CC-001"
          />
        </div>
      </Grid>
      {initialData && (
        <div className="azals-field">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              className="azals-checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
            />
            <span>Departement actif</span>
          </label>
        </div>
      )}
      <div className="flex justify-end gap-2 mt-4">
        <Button variant="secondary" type="button" onClick={onCancel}>Annuler</Button>
        <Button type="submit" isLoading={isLoading}>{initialData ? 'Enregistrer' : 'Creer'}</Button>
      </div>
    </form>
  );
};

export default DepartmentForm;
