/**
 * AZALSCORE Module - Country Packs France - FEC View
 * Vue Fichier des Ecritures Comptables
 */

import React, { useState } from 'react';
import { FileText, CheckCircle, Download, Play } from 'lucide-react';
import { Button, Modal } from '@ui/actions';
import { Select, Input } from '@ui/forms';
import { Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import { useFECExports, useGenerateFEC, useValidateFEC } from '../hooks';
import { FEC_STATUS } from '../constants';
import { Badge } from './LocalComponents';
import type { FECExport } from '../api';

export const FECView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [formData, setFormData] = useState({
    fiscal_year: new Date().getFullYear(),
    period_start: '',
    period_end: '',
    siren: ''
  });

  const { data: exports = [], isLoading, error, refetch } = useFECExports({
    status: filterStatus || undefined
  });
  const generateFEC = useGenerateFEC();
  const validateFEC = useValidateFEC();

  const handleGenerate = async () => {
    await generateFEC.mutateAsync(formData);
    setShowGenerateModal(false);
  };

  const columns: TableColumn<FECExport>[] = [
    { id: 'file_name', header: 'Reference', accessor: 'file_name', render: (v) => <code className="font-mono font-bold">{v as string}</code> },
    { id: 'fiscal_year', header: 'Exercice', accessor: 'fiscal_year', render: (v) => <Badge color="blue">{v as number}</Badge> },
    {
      id: 'period',
      header: 'Periode',
      accessor: 'period_start',
      render: (_, row) => `${formatDate(row.period_start)} - ${formatDate(row.period_end)}`
    },
    { id: 'entries_count', header: 'Ecritures', accessor: 'entries_count', align: 'right' },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v) => {
        const info = FEC_STATUS.find(s => s.value === v);
        return <Badge color={info?.color || 'gray'}>{info?.label || (v as string)}</Badge>;
      }
    },
    {
      id: 'validation_errors',
      header: 'Erreurs',
      accessor: 'validation_errors',
      render: (v) => {
        const errors = v as string[];
        return errors?.length > 0 ? (
          <Badge color="red">{errors.length} erreurs</Badge>
        ) : (
          <Badge color="green">OK</Badge>
        );
      }
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-1">
          {row.status === 'GENERATED' && (
            <Button size="sm" variant="primary" onClick={() => validateFEC.mutate(row.id)}>
              <CheckCircle size={14} className="mr-1" />
              Valider
            </Button>
          )}
          {(row.status === 'VALIDATED' || row.status === 'EXPORTED') && (
            <Button size="sm" variant="success">
              <Download size={14} className="mr-1" />
              Telecharger
            </Button>
          )}
        </div>
      )
    }
  ];

  return (
    <>
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Fichiers des Ecritures Comptables (FEC)</h3>
          <div className="flex gap-2">
            <Select
              value={filterStatus}
              onChange={(v) => setFilterStatus(v)}
              options={[{ value: '', label: 'Tous statuts' }, ...FEC_STATUS]}
              className="w-36"
            />
            <Button onClick={() => setShowGenerateModal(true)}>
              <FileText size={16} className="mr-1" />
              Generer FEC
            </Button>
          </div>
        </div>
        <DataTable
          columns={columns}
          data={exports}
          isLoading={isLoading}
          keyField="id"
          filterable
          error={error instanceof Error ? error : null}
          onRetry={() => refetch()}
        />
      </Card>

      <Modal isOpen={showGenerateModal} onClose={() => setShowGenerateModal(false)} title="Generer un FEC" size="md">
        <div className="space-y-4">
          <div className="azals-field">
            <label htmlFor="fec-fiscal-year" className="azals-field__label">Exercice fiscal</label>
            <Input
              id="fec-fiscal-year"
              type="number"
              value={String(formData.fiscal_year)}
              onChange={(v) => setFormData({ ...formData, fiscal_year: parseInt(v) })}
            />
          </div>
          <div className="azals-field">
            <label htmlFor="fec-siren" className="azals-field__label">SIREN</label>
            <Input
              id="fec-siren"
              type="text"
              value={formData.siren}
              onChange={(v) => setFormData({ ...formData, siren: v })}
              placeholder="123456789"
            />
          </div>
          <Grid cols={2}>
            <div className="azals-field">
              <label htmlFor="fec-period-start" className="azals-field__label">Date debut</label>
              <input
                id="fec-period-start"
                type="date"
                className="azals-input"
                value={formData.period_start}
                onChange={(e) => setFormData({ ...formData, period_start: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label htmlFor="fec-period-end" className="azals-field__label">Date fin</label>
              <input
                id="fec-period-end"
                type="date"
                className="azals-input"
                value={formData.period_end}
                onChange={(e) => setFormData({ ...formData, period_end: e.target.value })}
              />
            </div>
          </Grid>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowGenerateModal(false)}>Annuler</Button>
            <Button onClick={handleGenerate} isLoading={generateFEC.isPending}>
              <Play size={16} className="mr-1" />
              Generer
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};

export default FECView;
