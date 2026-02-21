/**
 * AZALSCORE - Vue Administration des Sequences
 * =============================================
 * Interface de parametrage des numerotations automatiques.
 */

import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Hash, Settings, RotateCcw, Check } from 'lucide-react';
import { api } from '@core/api-client';
import { Button, Modal } from '@ui/actions';
import { Select, Input, CheckboxInput } from '@ui/forms';
import { Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { unwrapApiResponse } from '@/types';

// ============================================================================
// TYPES
// ============================================================================

interface SequenceConfig {
  entity_type: string;
  prefix: string;
  include_year: boolean;
  padding: number;
  separator: string;
  reset_yearly: boolean;
  current_year: number;
  current_number: number;
  configured: boolean;
  example?: string;
  description?: string;
  module?: string;
}

interface SequenceUpdateData {
  prefix?: string;
  include_year?: boolean;
  padding?: number;
  separator?: string;
  reset_yearly?: boolean;
}

interface PreviewResponse {
  entity_type: string;
  preview: string;
  next_number: number;
  config: {
    prefix: string;
    include_year: boolean;
    padding: number;
    separator: string;
  };
}

// ============================================================================
// CONSTANTES
// ============================================================================

const SEPARATORS = [
  { value: '-', label: 'Tiret (-)' },
  { value: '/', label: 'Slash (/)' },
  { value: '.', label: 'Point (.)' },
  { value: '_', label: 'Underscore (_)' }
];

const PADDING_OPTIONS = [
  { value: '3', label: '3 chiffres (001)' },
  { value: '4', label: '4 chiffres (0001)' },
  { value: '5', label: '5 chiffres (00001)' },
  { value: '6', label: '6 chiffres (000001)' }
];

const MODULE_COLORS: Record<string, string> = {
  'Commercial': 'blue',
  'Achats': 'purple',
  'RH': 'green',
  'Interventions': 'orange',
  'Projets': 'indigo',
  'Maintenance': 'yellow',
  'Qualite': 'red',
  'Helpdesk': 'pink',
  'Comptabilite': 'gray',
  'CRM': 'cyan'
};

// ============================================================================
// API HOOKS
// ============================================================================

const useSequences = () => {
  return useQuery({
    queryKey: ['admin', 'sequences'],
    queryFn: async (): Promise<SequenceConfig[]> => {
      try {
        const res = await api.get<{ items: SequenceConfig[]; total: number }>('/admin/sequences', {
          headers: { 'X-Silent-Error': 'true' }
        });
        // Gérer les deux formats possibles (réponse directe ou enveloppée dans data)
        const data = unwrapApiResponse<{ items: SequenceConfig[]; total: number }>(res);
        return data?.items || [];
      } catch {
        return [];
      }
    },
    retry: false
  });
};

const useUpdateSequence = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ entityType, data }: { entityType: string; data: SequenceUpdateData }) => {
      const res = await api.put<SequenceConfig>(`/admin/sequences/${entityType}`, data);
      return unwrapApiResponse(res);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'sequences'] });
    }
  });
};

const useResetSequence = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (entityType: string) => {
      const res = await api.post<SequenceConfig>(`/admin/sequences/${entityType}/reset`);
      return unwrapApiResponse(res);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'sequences'] });
    }
  });
};

const usePreviewSequence = (
  entityType: string,
  config: Partial<SequenceUpdateData>,
  enabled: boolean
) => {
  return useQuery({
    queryKey: ['admin', 'sequences', 'preview', entityType, config],
    queryFn: async (): Promise<PreviewResponse | null> => {
      try {
        const params = new URLSearchParams();
        if (config.prefix) params.append('prefix', config.prefix);
        if (config.include_year !== undefined) params.append('include_year', String(config.include_year));
        if (config.padding) params.append('padding', String(config.padding));
        if (config.separator) params.append('separator', config.separator);
        const queryString = params.toString();
        const res = await api.get<PreviewResponse>(`/admin/sequences/${entityType}/preview${queryString ? `?${queryString}` : ''}`);
        return unwrapApiResponse(res);
      } catch {
        return null;
      }
    },
    enabled: enabled && !!entityType
  });
};

// ============================================================================
// COMPOSANTS LOCAUX
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface EditModalProps {
  sequence: SequenceConfig | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (entityType: string, data: SequenceUpdateData) => void;
  onReset: (entityType: string) => void;
  isLoading: boolean;
}

const EditModal: React.FC<EditModalProps> = ({
  sequence,
  isOpen,
  onClose,
  onSave,
  onReset,
  isLoading
}) => {
  const [formData, setFormData] = useState<SequenceUpdateData>({});
  const [previewEnabled, setPreviewEnabled] = useState(false);

  // Reset form quand la sequence change
  React.useEffect(() => {
    if (sequence) {
      setFormData({
        prefix: sequence.prefix,
        include_year: sequence.include_year,
        padding: sequence.padding,
        separator: sequence.separator,
        reset_yearly: sequence.reset_yearly
      });
      setPreviewEnabled(false);
    }
  }, [sequence]);

  // Preview
  const { data: preview } = usePreviewSequence(
    sequence?.entity_type || '',
    formData,
    previewEnabled && isOpen
  );

  const handleChange = useCallback((field: keyof SequenceUpdateData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setPreviewEnabled(true);
  }, []);

  const handleSave = useCallback(() => {
    if (sequence) {
      onSave(sequence.entity_type, formData);
    }
  }, [sequence, formData, onSave]);

  const handleReset = useCallback(() => {
    if (sequence && window.confirm('Reinitialiser aux valeurs par defaut ?')) {
      onReset(sequence.entity_type);
    }
  }, [sequence, onReset]);

  const handleClose = useCallback(() => {
    onClose();
  }, [onClose]);

  if (!sequence) return null;

  const currentExample = preview?.preview || sequence.example;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title={`Parametrer: ${sequence.description || sequence.entity_type}`}>
      <div className="space-y-4">
        {/* Info */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <Hash size={16} />
            <span>Type: <strong>{sequence.entity_type}</strong></span>
            <span className="mx-2">|</span>
            <span>Module: <Badge color={MODULE_COLORS[sequence.module || 'Autre'] || 'gray'}>{sequence.module}</Badge></span>
          </div>
        </div>

        {/* Preview */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="text-sm text-blue-600 dark:text-blue-400 mb-1">Apercu de la prochaine reference:</div>
          <div className="text-2xl font-mono font-bold text-blue-800 dark:text-blue-200">
            {currentExample}
          </div>
          <div className="text-xs text-blue-500 mt-1">
            Compteur actuel: {sequence.current_number} | Annee: {sequence.current_year}
          </div>
        </div>

        {/* Formulaire */}
        <Grid cols={2}>
          <div className="azals-field">
            <label htmlFor={`seq-prefix-${sequence.entity_type}`}>Prefixe</label>
            <Input
              id={`seq-prefix-${sequence.entity_type}`}
              value={formData.prefix || ''}
              onChange={(v: string) => handleChange('prefix', v)}
              placeholder="CLI, FV, etc."
            />
          </div>
          <div className="azals-field">
            <label htmlFor={`seq-separator-${sequence.entity_type}`}>Separateur</label>
            <Select
              id={`seq-separator-${sequence.entity_type}`}
              value={formData.separator || '-'}
              onChange={(v) => handleChange('separator', v)}
              options={SEPARATORS}
            />
          </div>
        </Grid>

        <Grid cols={2}>
          <div className="azals-field">
            <label htmlFor={`seq-padding-${sequence.entity_type}`}>Nombre de chiffres</label>
            <Select
              id={`seq-padding-${sequence.entity_type}`}
              value={String(formData.padding || 4)}
              onChange={(v) => handleChange('padding', parseInt(v))}
              options={PADDING_OPTIONS}
            />
          </div>
          <div className="azals-field pt-6">
            <CheckboxInput
              name="include_year"
              checked={formData.include_year || false}
              onChange={(v: boolean) => handleChange('include_year', v)}
              label="Inclure l'annee"
            />
          </div>
        </Grid>

        <div className="azals-field">
          <CheckboxInput
            name="reset_yearly"
            checked={formData.reset_yearly || false}
            onChange={(v: boolean) => handleChange('reset_yearly', v)}
            label="Reinitialiser le compteur chaque annee"
          />
          <p className="text-xs text-gray-500 mt-1">
            Si active, le compteur repart a 1 au 1er janvier de chaque annee.
          </p>
        </div>

        {/* Actions */}
        <div className="flex justify-between pt-4 border-t">
          <Button
            variant="secondary"
            onClick={handleReset}
            disabled={isLoading}
          >
            <RotateCcw size={16} className="mr-2" />
            Valeurs par defaut
          </Button>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={handleClose}>
              Annuler
            </Button>
            <Button onClick={handleSave} isLoading={isLoading}>
              <Check size={16} className="mr-2" />
              Enregistrer
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};

// ============================================================================
// COMPOSANT PRINCIPAL
// ============================================================================

const SequencesView: React.FC = () => {
  const { data: sequences = [], isLoading } = useSequences();
  const updateSequence = useUpdateSequence();
  const resetSequence = useResetSequence();

  const [selectedSequence, setSelectedSequence] = useState<SequenceConfig | null>(null);
  const [filterModule, setFilterModule] = useState<string>('');

  // Extraire les modules uniques
  const modules = [...new Set(sequences.map(s => s.module).filter(Boolean))].sort();

  // Filtrer les sequences
  const filteredSequences = filterModule
    ? sequences.filter(s => s.module === filterModule)
    : sequences;

  const handleEdit = useCallback((sequence: SequenceConfig) => {
    setSelectedSequence(sequence);
  }, []);

  const handleSave = useCallback((entityType: string, data: SequenceUpdateData) => {
    updateSequence.mutate({ entityType, data }, {
      onSuccess: () => setSelectedSequence(null)
    });
  }, [updateSequence]);

  const handleReset = useCallback((entityType: string) => {
    resetSequence.mutate(entityType, {
      onSuccess: () => setSelectedSequence(null)
    });
  }, [resetSequence]);

  const handleCloseModal = useCallback(() => {
    setSelectedSequence(null);
  }, []);

  const columns: TableColumn<SequenceConfig>[] = [
    {
      id: 'module',
      header: 'Module',
      accessor: 'module',
      render: (v) => (
        <Badge color={MODULE_COLORS[(v as string) || 'Autre'] || 'gray'}>
          {(v as string) || 'Autre'}
        </Badge>
      )
    },
    {
      id: 'description',
      header: 'Entite',
      accessor: 'description',
      render: (v, row) => (
        <div>
          <div className="font-medium">{v as string}</div>
          <div className="text-xs text-gray-500 font-mono">{(row as SequenceConfig).entity_type}</div>
        </div>
      )
    },
    {
      id: 'prefix',
      header: 'Prefixe',
      accessor: 'prefix',
      render: (v) => <code className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">{v as string}</code>
    },
    {
      id: 'format',
      header: 'Format',
      accessor: 'include_year',
      render: (v, row) => {
        const seq = row as SequenceConfig;
        const format = seq.include_year
          ? `${seq.prefix}${seq.separator}AAAA${seq.separator}${'X'.repeat(seq.padding)}`
          : `${seq.prefix}${seq.separator}${'X'.repeat(seq.padding)}`;
        return <code className="text-xs">{format}</code>;
      }
    },
    {
      id: 'example',
      header: 'Prochain',
      accessor: 'example',
      render: (v) => (
        <span className="font-mono text-blue-600 dark:text-blue-400 font-medium">
          {v as string}
        </span>
      )
    },
    {
      id: 'current_number',
      header: 'Compteur',
      accessor: 'current_number',
      render: (v, row) => (
        <span className="text-gray-600 dark:text-gray-400">
          {(v as number)} ({(row as SequenceConfig).current_year})
        </span>
      )
    },
    {
      id: 'configured',
      header: 'Statut',
      accessor: 'configured',
      render: (v) => (
        <Badge color={(v as boolean) ? 'green' : 'gray'}>
          {(v as boolean) ? 'Personnalise' : 'Par defaut'}
        </Badge>
      )
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'entity_type',
      render: (_, row) => (
        <div onClick={(e) => e.stopPropagation()}>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => handleEdit(row as SequenceConfig)}
          >
            <Settings size={14} className="mr-1" />
            Configurer
          </Button>
        </div>
      )
    }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Hash size={20} />
            Numerotation automatique
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Parametrez le format des references pour chaque type de document.
          </p>
        </div>
        <div className="flex gap-2">
          <Select
            value={filterModule}
            onChange={(v) => setFilterModule(v)}
            options={[
              { value: '', label: 'Tous les modules' },
              ...modules.map(m => ({ value: m as string, label: m as string }))
            ]}
            className="w-48"
          />
        </div>
      </div>

      <DataTable
        columns={columns}
        data={filteredSequences}
        isLoading={isLoading}
        keyField="entity_type"
          filterable
          onRowClick={handleEdit}
      />

      <EditModal
        sequence={selectedSequence}
        isOpen={!!selectedSequence}
        onClose={handleCloseModal}
        onSave={handleSave}
        onReset={handleReset}
        isLoading={updateSequence.isPending || resetSequence.isPending}
      />

      {/* Legende */}
      <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="text-xs text-gray-500 dark:text-gray-400">
          <strong>Legende du format:</strong> AAAA = Annee | X = Chiffres du compteur
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          <strong>Note:</strong> Le compteur n&apos;est pas modifiable manuellement pour garantir l&apos;integrite des sequences.
        </div>
      </div>
    </Card>
  );
};

export default SequencesView;
