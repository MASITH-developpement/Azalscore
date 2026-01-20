/**
 * AZALSCORE Module - Qualité
 * Contrôle qualité, non-conformités, audits
 */

import React from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { ClipboardCheck, AlertTriangle, FileSearch } from 'lucide-react';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import type { DashboardKPI } from '@/types';

export const QualityDashboard: React.FC = () => {
  const navigate = useNavigate();

  const kpis: DashboardKPI[] = [
    { id: 'controls', label: 'Contrôles (mois)', value: 0 },
    { id: 'nc', label: 'Non-conformités ouvertes', value: 0 },
    { id: 'rate', label: 'Taux conformité', value: '-' },
    { id: 'audits', label: 'Audits planifiés', value: 0 },
  ];

  return (
    <PageWrapper title="Qualité" subtitle="Contrôle et assurance qualité">
      <section className="azals-section">
        <Grid cols={4} gap="md">
          {kpis.map((kpi) => <KPICard key={kpi.id} kpi={kpi} />)}
        </Grid>
      </section>

      <section className="azals-section">
        <Grid cols={3} gap="md">
          <Card
            title="Contrôles"
            actions={<Button variant="ghost" size="sm" onClick={() => navigate('/quality/controls')}>Voir</Button>}
          >
            <ClipboardCheck size={32} className="azals-text--primary" />
            <p>Contrôles qualité</p>
          </Card>

          <Card
            title="Non-Conformités"
            actions={<Button variant="ghost" size="sm" onClick={() => navigate('/quality/nc')}>Gérer</Button>}
          >
            <AlertTriangle size={32} className="azals-text--primary" />
            <p>Gestion des NC</p>
          </Card>

          <Card
            title="Audits"
            actions={<Button variant="ghost" size="sm" onClick={() => navigate('/quality/audits')}>Planifier</Button>}
          >
            <FileSearch size={32} className="azals-text--primary" />
            <p>Audits internes</p>
          </Card>
        </Grid>
      </section>
    </PageWrapper>
  );
};

export const QualityRoutes: React.FC = () => (
  <Routes>
    <Route index element={<QualityDashboard />} />
    <Route path="controls" element={<QualityDashboard />} />
    <Route path="nc" element={<QualityDashboard />} />
    <Route path="audits" element={<QualityDashboard />} />
  </Routes>
);

export default QualityRoutes;
