/**
 * AZALSCORE Module - Audit - Compliance Page
 * Liste des controles de conformite
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, RefreshCw } from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button, ButtonGroup } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import { useComplianceChecks, useComplianceSummary } from '../hooks';
import { COMPLIANCE_STATUS_CONFIG, COMPLIANCE_FRAMEWORK_LABELS } from '../types';
import type { ComplianceCheck } from '../types';

export const CompliancePage: React.FC = () => {
  const navigate = useNavigate();
  const { data: checks, isLoading, error, refetch } = useComplianceChecks();
  const { data: summary } = useComplianceSummary();

  const columns: TableColumn<ComplianceCheck>[] = [
    {
      id: 'framework',
      header: 'Referentiel',
      accessor: 'framework',
      render: (value) => COMPLIANCE_FRAMEWORK_LABELS[value as keyof typeof COMPLIANCE_FRAMEWORK_LABELS] || String(value),
    },
    {
      id: 'control_id',
      header: 'Controle',
      accessor: 'control_id',
      render: (value) => <code className="azals-code">{value as string}</code>,
    },
    {
      id: 'control_name',
      header: 'Nom',
      accessor: 'control_name',
    },
    {
      id: 'category',
      header: 'Categorie',
      accessor: 'category',
      render: (value) => (value as string) || '-',
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => {
        const config = COMPLIANCE_STATUS_CONFIG[value as keyof typeof COMPLIANCE_STATUS_CONFIG];
        return <span className={`azals-badge azals-badge--${config?.color || 'gray'}`}>{config?.label || String(value)}</span>;
      },
    },
    {
      id: 'severity',
      header: 'Severite',
      accessor: 'severity',
    },
    {
      id: 'last_checked_at',
      header: 'Derniere verif',
      accessor: 'last_checked_at',
      render: (value) => (value ? formatDate(value as string) : 'Jamais'),
    },
  ];

  return (
    <PageWrapper
      title="Conformite"
      subtitle={summary ? `${Math.round(summary.compliance_rate * 100)}% de conformite` : ''}
      actions={
        <ButtonGroup>
          <Button variant="ghost" leftIcon={<RefreshCw size={16} />} onClick={() => { refetch(); }}>
            Actualiser
          </Button>
          <CapabilityGuard capability="audit.compliance.create">
            <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/audit/compliance/new')}>
              Nouveau
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      }
    >
      {/* Résumé */}
      {summary && (
        <section className="azals-section">
          <Grid cols={4} gap="md">
            <Card>
              <div className="azals-stat">
                <span className="azals-stat__value">{summary.total}</span>
                <span className="azals-stat__label">Total</span>
              </div>
            </Card>
            <Card>
              <div className="azals-stat azals-stat--success">
                <span className="azals-stat__value">{summary.compliant}</span>
                <span className="azals-stat__label">Conformes</span>
              </div>
            </Card>
            <Card>
              <div className="azals-stat azals-stat--danger">
                <span className="azals-stat__value">{summary.non_compliant}</span>
                <span className="azals-stat__label">Non conformes</span>
              </div>
            </Card>
            <Card>
              <div className="azals-stat azals-stat--primary">
                <span className="azals-stat__value">{Math.round(summary.compliance_rate * 100)}%</span>
                <span className="azals-stat__label">Taux de conformite</span>
              </div>
            </Card>
          </Grid>
        </section>
      )}

      <Card noPadding>
        <DataTable
          columns={columns}
          data={checks || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          emptyMessage="Aucun controle de conformite"
        />
      </Card>
    </PageWrapper>
  );
};

export default CompliancePage;
