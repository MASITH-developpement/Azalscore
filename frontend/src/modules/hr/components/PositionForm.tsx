/**
 * AZALSCORE Module - HR - PositionForm
 * Formulaire de creation/edition de poste
 */

import React, { useState } from 'react';
import { Button } from '@ui/actions';
import { Select } from '@ui/forms';
import { Grid } from '@ui/layout';
import type { Department, Position } from '../types';
import { POSITION_CATEGORIES } from '../constants';

interface PositionFormProps {
  onSubmit: (data: Partial<Position>) => Promise<void>;
  onCancel: () => void;
  isLoading: boolean;
  departments: Department[];
  initialData?: Position;
}

const PositionForm: React.FC<PositionFormProps> = ({ onSubmit, onCancel, isLoading, departments, initialData }) => {
  const [code, setCode] = useState(initialData?.code || '');
  const [title, setTitle] = useState(initialData?.title || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [departmentId, setDepartmentId] = useState(initialData?.department_id || '');
  const [category, setCategory] = useState(initialData?.category || '');
  const [level, setLevel] = useState(String(initialData?.level || 1));
  const [minSalary, setMinSalary] = useState(initialData?.min_salary ? String(initialData.min_salary) : '');
  const [maxSalary, setMaxSalary] = useState(initialData?.max_salary ? String(initialData.max_salary) : '');
  const [requirements, setRequirements] = useState(initialData?.requirements?.join('\n') || '');
  const [isActive, setIsActive] = useState(initialData?.is_active ?? true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const reqList = requirements.split('\n').map(r => r.trim()).filter(r => r.length > 0);
    onSubmit({
      code,
      title,
      description: description || undefined,
      department_id: departmentId || undefined,
      category: category || undefined,
      level: parseInt(level) || 1,
      min_salary: minSalary ? parseFloat(minSalary) : undefined,
      max_salary: maxSalary ? parseFloat(maxSalary) : undefined,
      requirements: reqList.length > 0 ? reqList : undefined,
      is_active: isActive,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <Grid cols={2}>
        <div className="azals-field">
          <label htmlFor="pos-form-code">Code *</label>
          <input
            id="pos-form-code"
            type="text"
            className="azals-input"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="Ex: DEV, TECH, COMPTA"
            required
          />
        </div>
        <div className="azals-field">
          <label htmlFor="pos-form-title">Intitule du poste *</label>
          <input
            id="pos-form-title"
            type="text"
            className="azals-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ex: Developpeur Senior"
            required
          />
        </div>
      </Grid>
      <div className="azals-field">
        <label htmlFor="pos-form-desc">Description</label>
        <textarea
          id="pos-form-desc"
          className="azals-input"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description du poste, missions principales..."
          rows={2}
        />
      </div>
      <Grid cols={3}>
        <div className="azals-field">
          <label>Departement</label>
          <Select
            value={departmentId}
            onChange={(v) => setDepartmentId(v)}
            options={[{ value: '', label: 'Aucun' }, ...departments.map(d => ({ value: d.id, label: d.name }))]}
          />
        </div>
        <div className="azals-field">
          <label>Categorie</label>
          <Select
            value={category}
            onChange={(v) => setCategory(v)}
            options={[{ value: '', label: 'Selectionner...' }, ...POSITION_CATEGORIES.map(c => ({ value: c.value, label: c.label }))]}
          />
        </div>
        <div className="azals-field">
          <label htmlFor="pos-form-level">Niveau hierarchique</label>
          <input
            id="pos-form-level"
            type="number"
            className="azals-input"
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            min={1}
            max={10}
          />
        </div>
      </Grid>
      <Grid cols={2}>
        <div className="azals-field">
          <label htmlFor="pos-form-min-salary">Salaire minimum</label>
          <input
            id="pos-form-min-salary"
            type="number"
            className="azals-input"
            value={minSalary}
            onChange={(e) => setMinSalary(e.target.value)}
            placeholder="Ex: 2500"
          />
        </div>
        <div className="azals-field">
          <label htmlFor="pos-form-max-salary">Salaire maximum</label>
          <input
            id="pos-form-max-salary"
            type="number"
            className="azals-input"
            value={maxSalary}
            onChange={(e) => setMaxSalary(e.target.value)}
            placeholder="Ex: 4500"
          />
        </div>
      </Grid>
      <div className="azals-field">
        <label htmlFor="pos-form-requirements">Competences requises (une par ligne)</label>
        <textarea
          id="pos-form-requirements"
          className="azals-input"
          value={requirements}
          onChange={(e) => setRequirements(e.target.value)}
          placeholder="Ex:&#10;Diplome Bac+5&#10;3 ans d&apos;experience&#10;Anglais courant"
          rows={3}
        />
      </div>
      {initialData && (
        <div className="azals-field">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              className="azals-checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
            />
            <span>Poste actif</span>
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

export default PositionForm;
