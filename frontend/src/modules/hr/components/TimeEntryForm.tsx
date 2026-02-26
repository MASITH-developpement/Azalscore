/**
 * AZALSCORE Module - HR - TimeEntryForm
 * Formulaire de saisie de temps
 */

import React, { useRef } from 'react';
import { Button } from '@ui/actions';
import type { Employee } from '../types';
import { getFullName } from '../types';
import type { TimeEntryCreateData } from '../hooks';

interface TimeEntryFormProps {
  onSubmit: (data: { employee_id: string; data: TimeEntryCreateData }) => Promise<void>;
  onCancel: () => void;
  isLoading: boolean;
  employees: Employee[];
}

const TimeEntryForm: React.FC<TimeEntryFormProps> = ({ onSubmit, onCancel, isLoading, employees }) => {
  const formRef = useRef<HTMLFormElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const form = formRef.current;
    if (!form) return;

    const formData = new FormData(form);
    const employee_id = formData.get('employee_id') as string;
    const data: TimeEntryCreateData = {
      date: formData.get('date') as string,
      worked_hours: parseFloat(formData.get('worked_hours') as string) || 0,
      overtime_hours: parseFloat(formData.get('overtime_hours') as string) || 0,
      break_duration: parseInt(formData.get('break_duration') as string) || 0,
      project_id: (formData.get('project_id') as string) || undefined,
      task_description: (formData.get('task_description') as string) || undefined
    };

    await onSubmit({ employee_id, data });
  };

  return (
    <form ref={formRef} onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="time-form-employee" className="block text-sm font-medium mb-1">Employe *</label>
        <select id="time-form-employee" name="employee_id" required className="w-full border rounded px-3 py-2">
          <option value="">Selectionnez un employe</option>
          {employees.map(emp => (
            <option key={emp.id} value={emp.id}>{getFullName(emp)}</option>
          ))}
        </select>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="time-form-date" className="block text-sm font-medium mb-1">Date *</label>
          <input id="time-form-date" type="date" name="date" required defaultValue={new Date().toISOString().split('T')[0]} className="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label htmlFor="time-form-worked" className="block text-sm font-medium mb-1">Heures travaillees *</label>
          <input id="time-form-worked" type="number" name="worked_hours" required step={0.5} min={0} max={24} defaultValue={8} className="w-full border rounded px-3 py-2" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="time-form-overtime" className="block text-sm font-medium mb-1">Heures supplementaires</label>
          <input id="time-form-overtime" type="number" name="overtime_hours" step={0.5} min={0} max={24} defaultValue={0} className="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label htmlFor="time-form-break" className="block text-sm font-medium mb-1">Pause (minutes)</label>
          <input id="time-form-break" type="number" name="break_duration" min={0} max={480} defaultValue={60} className="w-full border rounded px-3 py-2" />
        </div>
      </div>
      <div>
        <label htmlFor="time-form-task-desc" className="block text-sm font-medium mb-1">Description tache</label>
        <textarea id="time-form-task-desc" name="task_description" className="w-full border rounded px-3 py-2" rows={3} placeholder="Description du travail effectue..." />
      </div>
      <div className="flex justify-end gap-2 pt-4">
        <Button variant="secondary" onClick={onCancel} disabled={isLoading}>Annuler</Button>
        <Button type="submit" disabled={isLoading}>{isLoading ? 'Enregistrement...' : 'Creer'}</Button>
      </div>
    </form>
  );
};

export default TimeEntryForm;
